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
typedef short s16;
#include "skill_hud.h"                                  /* AGC_RET_Q, UV_TRI, element 7 (the HUD quads) */
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

static struct { s32 target; float tx, ty, tz; float r; s32 alpha; float *apos[0x27]; } Z;
#define ACTMGR     (*(u8 **)0x8034923C)
#define CAM        (*(u8 **)0x8034922C)                 /* field camera: +0x1C yaw; it looks along (-sin, -cos) */
/* villager actors (actor manager id 0xB000; one per character, out or not): +0x4C character id, +0x2C flags
   (0x2000 set while the character is out on the current map), position at -0x24 (from valley dumps) */
static void scan_actors(void)
{
    u8 *m = ACTMGR, *n, *c;
    s32 k = 0, id;
    for (id = 0; id < 0x27; id++) Z.apos[id] = 0;
    if ((u32)m < 0x80000000u || (u32)m >= 0x81800000u) return;
    for (n = *(u8 **)(m + 4); n != m + 0x14 && (u32)n >= 0x80000000u && (u32)n < 0x81800000u && k < 600; n = *(u8 **)(n + 4), k++) {
        c = *(u8 **)(n + 0xC);
        if ((u32)c < 0x80000000u || (u32)c >= 0x81800000u || *(u32 *)(c + 0x14) != 0xB000) continue;
        id = *(s32 *)(c + 0x4C);
        if (id >= 1 && id < 0x27 && (*(u32 *)(c + 0x2C) & 0x2000)) Z.apos[id] = (float *)(c - 0x24);
    }
}

static float rsq(float x)
{
    float r;
    __asm__("frsqrte %0, %1" : "=f"(r) : "f"(x));
    r = r * (1.5f - 0.5f * x * r * r);
    r = r * (1.5f - 0.5f * x * r * r);
    return r;
}
static float zsin(float x)                              /* x in -pi..pi */
{
    float x2;
    while (x > 3.14159274f) x -= 6.28318548f;
    while (x < -3.14159274f) x += 6.28318548f;
    x2 = x * x;
    return x * (1 - x2 / 6 * (1 - x2 / 20 * (1 - x2 / 42)));
}
/* a candidate's position; 0 if it is not out on the player's map */
static s32 tpos(u8 *g, s32 id, s32 map, float *x, float *z)
{
    float p[3], *s;
    if (id == ZT_JOE) {
        if (map != 1 || !pm_joe_pos(p)) return 0;
        *x = p[0]; *z = p[2]; return 1;
    }
    s = Z.apos[id];                                      /* only characters that are out here */
    if (!s || SLOT_MAP(g, id) != map) return 0;
    *x = s[0]; *z = s[2]; return 1;
}
static float ztan_half_fov(u8 *c)
{
    float f = *(float *)(c + 0x38) * (3.14159274f / 360.0f);
    return zsin(f) / zsin(f + 1.57079637f);
}
static float theight(u8 *g, s32 id)
{
    float p[3];
    if (id == ZT_JOE) { pm_joe_pos(p); return p[1]; }
    return Z.apos[id] ? Z.apos[id][1] : SLOT_POS(g, 0)[1];
}
/* best target in front: switching = 1 skips the current one, widens the cone to 90 degrees and favours
   targets straight ahead (distance x0.6 ahead .. x1.0 at the side) */
/* debug block for RAM dumps (magic 'ZTDB') */
struct { u32 magic; s32 target, alpha, free, map, control, noev, fade, presses, picks, cands, last_pick, agc_ok, cx, cy, frames, nfree; float w, ndx, ndy; } zt_dbg;
static float ztan_half_fov(u8 *c);
/* project a world point with the field camera: returns depth (<= 0: behind), ndc x / y in -1..1 */
static float proj(float x, float y, float z, float *nx, float *ny)
{
    u8 *c = CAM;
    float *M, sx, sy, w, f;
    if ((u32)c < 0x80000000u || (u32)c >= 0x81800000u) return 0;
    M = (float *)(c + 0x50);
    sx = M[0] * x + M[1] * y + M[2] * z + M[3];
    sy = M[4] * x + M[5] * y + M[6] * z + M[7];
    w = -(M[8] * x + M[9] * y + M[10] * z + M[11]);
    if (w < 0.3f) return 0;
    f = ztan_half_fov(c);
    *nx = sx / w / (f * *(float *)(c + 0x34)); *ny = sy / w / f;
    return w;
}
/* OoT-like choice: anyone out here within range whose chest is on screen; nearest and most central wins.
   switching = 1 skips the current target. */
static float theight(u8 *g, s32 id);
static s32 pick(u8 *g, s32 map, s32 switching)
{
    float *p = SLOT_POS(g, 0), best = 1e30f, x, z, nx, ny;
    s32 id, found = 0, i, n = 0;
    for (i = 0; i <= 0x26; i++) {
        float dx, dz, d2, score, ax;
        id = i == 0 ? ZT_JOE : i;
        if (switching && id == Z.target) continue;
        if (!tpos(g, id, map, &x, &z)) continue;
        dx = x - p[0]; dz = z - p[2]; d2 = dx * dx + dz * dz;
        if (d2 > ZT_RANGE * ZT_RANGE || d2 < 0.0001f) continue;
        if (proj(x, theight(g, id) + 0.85f, z, &nx, &ny) <= 0) continue;
        if (nx < -0.95f || nx > 0.95f || ny < -0.95f || ny > 0.95f) continue;
        n++;
        ax = nx < 0 ? -nx : nx;
        score = d2 * (1.0f + ax);
        if (score < best) { best = score; found = id; }
    }
    zt_dbg.cands = n; zt_dbg.last_pick = found; zt_dbg.picks++;
    return found;
}
static void release(void) { Z.target = 0; }
static void reticle(u8 *g);

/* ---- the reticle: 4 HUD quads (opguide.agc element 7, AGC_RET_Q) around the target's projected chest.
   Camera *(0x8034922C): +0x50 view matrix (3 x 4 rows), +0x34 aspect, +0x38 vertical FOV in degrees (30.2;
   checked against a screenshot). HUD units: 640 x 480, origin at the centre, y down. Closes in from 60 px
   to 20 px, then breathes; light blue like OoT's people reticle; fades out on release. */
#define AGC        (*(u8 **)0x80349110)
#define RET_COL    0x9696FF00u
#define RET_Y      0.85f                                /* aim this far above the target's feet */
static s32 rframe;
static void quad(u8 *a, s32 k, s32 x0, s32 y0, s32 x1, s32 y1, const float *uv, u32 rgba)
{
    u8 *q = a + AGC_RET_Q + 0x2C * k;
    s32 i;
    *(u32 *)q = 4;
    *(s16 *)(q + 4) = x0; *(s16 *)(q + 6) = y0; *(s16 *)(q + 8) = x1; *(s16 *)(q + 10) = y1;
    for (i = 0; i < 4; i++) { *(u32 *)(q + 0xC + 4 * i) = rgba; *(float *)(q + 0x1C + 4 * i) = uv[i]; }
}
static void reticle(u8 *g)
{
    u8 *a = AGC, *c = CAM;
    float x, y, z, w, sx, sy, r;
    s32 cx, cy, e7y, h = TRI_W / 2, k, ri;
    u32 col;
    zt_dbg.agc_ok = 0;
    if ((u32)a < 0x80000000u || (u32)a >= 0x81800000u) return;
    zt_dbg.agc_ok = 1;
    if (*(u32 *)a != 0xC1C7C3C6u) return;
    zt_dbg.agc_ok = 2;
    if (*(u32 *)(a + AGC_E7_COUNT) != E7_COUNT) return;   /* our opguide.agc */
    zt_dbg.agc_ok = 3;
    if (Z.target) { if (Z.alpha < 255) Z.alpha += 51; if (Z.alpha > 255) Z.alpha = 255; }
    else { Z.alpha -= 64; if (Z.alpha < 0) Z.alpha = 0; Z.r = 60; }
    if (!Z.alpha || (u32)c < 0x80000000u || (u32)c >= 0x81800000u) {
        for (k = 0; k < 4; k++) quad(a, k, 0, 0, 0, 0, UV_TRI[k], 0xFFFFFF00u);
        return;
    }
    x = Z.tx; y = Z.ty + RET_Y; z = Z.tz;
    w = proj(x, y, z, &sx, &sy);
    zt_dbg.w = w; zt_dbg.ndx = sx; zt_dbg.ndy = sy;
    if (w <= 0) { for (k = 0; k < 4; k++) quad(a, k, 0, 0, 0, 0, UV_TRI[k], 0xFFFFFF00u); return; }
    cx = (s32)(sx * 320.0f);
    cy = (s32)(-sy * 240.0f);
    zt_dbg.cx = cx; zt_dbg.cy = cy;
    if (Z.r < 20.5f) Z.r = 20 + 2.0f * zsin((float)(rframe++ % 60) * (6.28318548f / 60.0f));
    else Z.r += (20 - Z.r) * 0.3f;
    r = Z.r; ri = (s32)r;
    e7y = *(s16 *)(a + AGC_E7_Y); cx -= E7_X; cy -= e7y;
    col = RET_COL | (u32)Z.alpha;
    quad(a, 0, cx - h, cy - ri - TRI_W, cx + h, cy - ri, UV_TRI[0], col);        /* top, pointing down */
    quad(a, 1, cx - h, cy + ri, cx + h, cy + ri + TRI_W, UV_TRI[1], col);        /* bottom, pointing up */
    quad(a, 2, cx - ri - TRI_W, cy - h, cx - ri, cy + h, UV_TRI[3], col);        /* left, pointing right */
    quad(a, 3, cx + ri, cy - h, cx + ri + TRI_W, cy + h, UV_TRI[2], col);        /* right, pointing left */
}

void zt_frame(u8 *g, s32 map, volatile u32 *held, volatile u32 *press)
{
    u8 *f = FADER;
    u8 *ev = EVMGR;
    /* free: no script event running (+0x680 == -1). Not +0x58C: test 3 lost the lock near several villagers,
       which looks like their own goings-on setting it (see zt_dbg.noev in a dump) */
    s32 free = map >= 0 && CONTROL == 1 && ev && *(s32 *)(ev + 0x680) == -1 && !(f && *(u8 *)(f + 0x60));
    static s32 notfree;
    zt_dbg.magic = 0x5A544442u; zt_dbg.frames++; zt_dbg.map = map; zt_dbg.control = CONTROL; zt_dbg.noev = ev ? *(s32 *)(ev + 0x58C) : -2;
    zt_dbg.fade = f ? *(u8 *)(f + 0x60) : -1; zt_dbg.free = free;
    if (!free) {                                         /* let go only if it lasts (events, menus, fades) */
        zt_dbg.nfree++;
        if (++notfree > 8) release();
        reticle(g); return;
    }
    notfree = 0;
    scan_actors();
    if (Z.target) {                                      /* let go when out of reach or gone */
        float *p = SLOT_POS(g, 0), dx, dz;
        if (!tpos(g, Z.target, map, &Z.tx, &Z.tz)) release();
        else {
            dx = Z.tx - p[0]; dz = Z.tz - p[2];
            if (dx * dx + dz * dz > ZT_LEASH * ZT_LEASH) release();
        }
    }
    if (*press & 0x10) {                                 /* Z: ours now (no first-person look) */
        *press &= ~0x10u; *held &= ~0x10u; zt_dbg.presses++;
        if (!Z.target) {
            Z.target = pick(g, map, 0);
            if (Z.target) { tpos(g, Z.target, map, &Z.tx, &Z.tz); Z.r = 60; sfx_play(*(u8 **)0x803491E4, SE_LOCK, 0); }
        } else {
            s32 next = pick(g, map, 1);
            if (next) { Z.target = next; tpos(g, next, map, &Z.tx, &Z.tz); Z.r = 60; sfx_play(*(u8 **)0x803491E4, SE_LOCK, 0); }
            else release();             /* test 1's release sound (4) was a looping drone: none now */
        }
    }
    *held &= ~0x10u;                                     /* holding Z never reaches the game either */
    if (Z.target) Z.ty = theight(g, Z.target);
    reticle(g);
    zt_dbg.target = Z.target; zt_dbg.alpha = Z.alpha;
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
