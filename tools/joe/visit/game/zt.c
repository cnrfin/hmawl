/* Z targeting (lock-on), step 1: Z picks the nearest villager (or Joe) in front within range, Z again
   switches to the next one in front or lets go. While locked the player keeps facing the target: the
   stick still moves him (movement is computed from the stick and the camera yaw, not from the facing),
   so he strafes and backs up. Z's first-person look is no longer reachable in the field.
   - pm_frame (pad hook, before the game's update) calls zt_frame: Z press, target choice, release.
   - HOOK13 (0x800313C4, after the player's state update, before his position / facing are copied into
     event slot 0) calls zt_post: points the facing (+0x58, a unit vector) at the target.
   Behaviour after OoT's attention system (zeldaret/oot z_actor.c, behaviour only): front cone 60 degrees
   for a new lock, 90 degrees with distance x0.6-1.0 for switching, release a little past the lock range. */
typedef unsigned int u32;
typedef int s32;
typedef unsigned char u8;
#define F(addr, ret, args) ((ret (*) args)(addr))
#define sfx_play   F(0x8012A52C, s32, (u8 *, s32, s32))
#define CONTROL    (*(u8 *)(*(u8 **)0x80349218 + 8))      /* 1 = player free */
#define EVMGR      (*(u8 **)0x803491BC)
#define FADER      (*(u8 **)0x803491B8)
#define SLOT_POS(g, i) ((float *)((g) + 0x29C78 + 12 * (i)))   /* event character slots: 0 = player */
#define SLOT_DIR(g, i) ((float *)((g) + 0x29F84 + 12 * (i)))
#define SLOT_MAP(g, i) (*(s32 *)((g) + 0x2A290 + 4 * (i)))
#define PL_STATE   0x1364                               /* player state: 1 = free in the field */
#define PL_FACE    0x58
#define ZT_RANGE   10.0f                                /* lock-on range (OoT's 350 units at Link's height ~ 11) */
#define ZT_LEASH   13.5f                                /* let go past this */
#define ZT_COS60   0.5f
#define ZT_JOE     100                                  /* target id for Joe (not an event slot) */
#define SE_LOCK    3                                    /* cursor_ok */

s32 pm_joe_pos(float *p);                               /* pm.c: Joe's position if he is out on this map */

static struct { s32 target; float tx, tz; } Z;

static s32 no_event(void)
{
    u8 *m = EVMGR;
    return m && *(s32 *)(m + 0x680) == -1 && *(s32 *)(m + 0x58C) == 0;
}
static float rsq(float x)
{
    float r;
    __asm__("frsqrte %0, %1" : "=f"(r) : "f"(x));
    r = r * (1.5f - 0.5f * x * r * r);
    r = r * (1.5f - 0.5f * x * r * r);
    return r;
}
/* a candidate's position; 0 if it is not out on the player's map */
static s32 tpos(u8 *g, s32 id, s32 map, float *x, float *z)
{
    float p[3], *s;
    if (id == ZT_JOE) {
        if (map != 1 || !pm_joe_pos(p)) return 0;
        *x = p[0]; *z = p[2]; return 1;
    }
    if (SLOT_MAP(g, id) != map) return 0;
    s = SLOT_POS(g, id);
    if (s[0] == 0 && s[2] == 0) return 0;
    *x = s[0]; *z = s[2]; return 1;
}
/* best target in front: switching = 1 skips the current one, widens the cone to 90 degrees and favours
   targets straight ahead (distance x0.6 ahead .. x1.0 at the side) */
static s32 pick(u8 *g, s32 map, s32 switching)
{
    float *p = SLOT_POS(g, 0), *d = SLOT_DIR(g, 0), best = 1e30f, x, z;
    s32 id, found = 0, i;
    for (i = 0; i <= 0x26; i++) {
        float dx, dz, d2, inv, c, score;
        id = i == 0 ? ZT_JOE : i;
        if (switching && id == Z.target) continue;
        if (!tpos(g, id, map, &x, &z)) continue;
        dx = x - p[0]; dz = z - p[2]; d2 = dx * dx + dz * dz;
        if (d2 > ZT_RANGE * ZT_RANGE || d2 < 0.0001f) continue;
        inv = rsq(d2); c = (dx * d[0] + dz * d[2]) * inv;  /* cos of the angle from the facing */
        if (c < (switching ? 0.0f : ZT_COS60)) continue;
        score = d2 * (switching ? 1.0f - 0.4f * c : 1.0f);
        if (score < best) { best = score; found = id; }
    }
    return found;
}
static void release(void) { Z.target = 0; }

void zt_frame(u8 *g, s32 map, volatile u32 *held, volatile u32 *press)
{
    u8 *f = FADER;
    s32 free = map >= 0 && CONTROL == 1 && no_event() && !(f && *(u8 *)(f + 0x60));
    if (!free) { release(); return; }
    if (Z.target) {                                      /* let go when out of reach or gone */
        float *p = SLOT_POS(g, 0), dx, dz;
        if (!tpos(g, Z.target, map, &Z.tx, &Z.tz)) release();
        else {
            dx = Z.tx - p[0]; dz = Z.tz - p[2];
            if (dx * dx + dz * dz > ZT_LEASH * ZT_LEASH) release();
        }
    }
    if (*press & 0x10) {                                 /* Z: ours now (no first-person look) */
        *press &= ~0x10u; *held &= ~0x10u;
        if (!Z.target) {
            Z.target = pick(g, map, 0);
            if (Z.target) { tpos(g, Z.target, map, &Z.tx, &Z.tz); sfx_play(*(u8 **)0x803491E4, SE_LOCK, 0); }
        } else {
            s32 next = pick(g, map, 1);
            if (next) { Z.target = next; tpos(g, next, map, &Z.tx, &Z.tz); sfx_play(*(u8 **)0x803491E4, SE_LOCK, 0); }
            else release();             /* test 1's release sound (4) was a looping drone: none now */
        }
    }
    *held &= ~0x10u;                                     /* holding Z never reaches the game either */
}

/* atan2 (radians), polynomial: about 0.005 rad worst error, plenty for a camera */
static float zatan2(float y, float x)
{
    float ax = x < 0 ? -x : x, ay = y < 0 ? -y : y, a, s, r;
    if (ax < 1e-6f && ay < 1e-6f) return 0;
    a = ax < ay ? ax / ay : ay / ax; s = a * a;
    r = ((-0.0464964749f * s + 0.15931422f) * s - 0.327622764f) * s * a + a;
    if (ay > ax) r = 1.57079637f - r;
    if (x < 0) r = 3.14159274f - r;
    return y < 0 ? -r : r;
}
#define ZT_TURN    0.35f                                /* facing: share of the way to the target per frame */
#define ZT_CAMRATE 0.12f                                /* camera yaw: share of the way per frame */
#define CAM        (*(u8 **)0x8034922C)                 /* field camera: +0x1C yaw; it looks along (-sin, -cos) */

/* after the player's update (HOOK13): turn toward the target; swing the camera behind him, looking past him
   at the target (so stick-up also means toward the target, as in OoT) */
void zt_post(u8 *pl)
{
    float *pos, *face, dx, dz, d2, inv, fx, fz, want, *yaw, dy;
    u8 *c = CAM;
    if (!Z.target || !pl || *(s32 *)(pl + PL_STATE) != 1) return;
    pos = (float *)(pl + 0x4C); face = (float *)(pl + PL_FACE);
    dx = Z.tx - pos[0]; dz = Z.tz - pos[2]; d2 = dx * dx + dz * dz;
    if (d2 < 0.01f) return;
    inv = rsq(d2); dx *= inv; dz *= inv;
    fx = face[0] + (dx - face[0]) * ZT_TURN; fz = face[2] + (dz - face[2]) * ZT_TURN;
    d2 = fx * fx + fz * fz;
    if (d2 < 0.0001f) { fx = dx; fz = dz; d2 = 1; }          /* exactly opposite: go straight there */
    inv = rsq(d2); face[0] = fx * inv; face[1] = 0; face[2] = fz * inv;
    if ((u32)c >= 0x80000000u && (u32)c < 0x81800000u) {
        yaw = (float *)(c + 0x1C);
        want = zatan2(-dx, -dz);
        dy = want - *yaw;
        while (dy > 3.14159274f) dy -= 6.28318548f;
        while (dy < -3.14159274f) dy += 6.28318548f;
        *yaw += dy * ZT_CAMRATE;
    }
}
