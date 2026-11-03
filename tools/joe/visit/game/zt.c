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
#define SE_LOCK    238                                  /* lock on: vanilla sound 238 (user pick; 434 = our OoT-style flutter, still in the bank) */
#define SE_FREE    239                                  /* lock off: vanilla 239 (435 = ours) */

s32 pm_joe_pos(float *p);                               /* pm.c: Joe's position if he is out on this map */

static struct { s32 target; float tx, ty, tz; float r; s32 alpha; float *apos[0x27]; u32 seen[0x27], now; float fx, fz, mx, mz; u32 movf; s32 fvalid; } Z;
#define ZT_PRESENT 30                                   /* frames a character counts as out after its flag was last seen */
#define ACTMGR     (*(u8 **)0x8034923C)
#define CAM        (*(u8 **)0x8034922C)                 /* field camera: +0x1C yaw; it looks along (-sin, -cos) */
/* villager actors (actor manager id 0xB000; one per character, out or not): +0x4C character id, +0x2C flags
   (0x2000 set while the character is out on the current map), position at -0x24 (from valley dumps) */
static void scan_actors(void)
{
    u8 *m = ACTMGR, *n, *c;
    s32 k = 0, id;
    Z.now++;
    if ((u32)m < 0x80000000u || (u32)m >= 0x81800000u) return;
    for (n = *(u8 **)(m + 4); n != m + 0x14 && (u32)n >= 0x80000000u && (u32)n < 0x81800000u && k < 600; n = *(u8 **)(n + 4), k++) {
        c = *(u8 **)(n + 0xC);
        if ((u32)c < 0x80000000u || (u32)c >= 0x81800000u || *(u32 *)(c + 0x14) != 0xB000) continue;
        id = *(s32 *)(c + 0x4C);
        /* 0x2000 flickers (test 6: locks dropped a frame after locking, with both sounds): it looks like a
           drawn-this-frame flag, so a character counts as out for ZT_PRESENT frames after it was last set */
        if (id >= 1 && id < 0x27 && (*(u32 *)(c + 0x2C) & 0x2000)) { Z.apos[id] = (float *)(c - 0x24); Z.seen[id] = Z.now; }
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
    if (!Z.apos[id] || Z.now - Z.seen[id] > ZT_PRESENT || SLOT_MAP(g, id) != map) return 0;   /* out here, lately */
    s = SLOT_POS(g, id);                                 /* the live position (event slot, every frame) */
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
    return SLOT_POS(g, id)[1];
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
/* event log for RAM dumps (magic 'ZLOG'): the last 32 events with the game clock (+20 a frame) and our call
   counter (two calls on one clock = the pad hook ran twice in a frame).
   kinds: 1 Z press (a = master held, b = copy pressed bit), 2 lock (a id, b candidates), 3 switch (a id),
   4 let go: Z, 5 let go: out of range, 6 let go: target gone, 7 release: not free, 8 Z with nothing to lock */
struct { u32 magic, n, calls; struct { u32 clock, call; s16 kind, a, b, pad; } e[32]; } zt_log;
static void zlog(s32 kind, s32 a, s32 b)
{
    u32 i = zt_log.n++ & 31;
    zt_log.magic = 0x5A4C4F47u;
    zt_log.e[i].clock = *(u32 *)*(u8 **)0x80349218; zt_log.e[i].call = zt_log.calls;
    zt_log.e[i].kind = (s16)kind; zt_log.e[i].a = (s16)a; zt_log.e[i].b = (s16)b;
}
static void release(void) { if (Z.target) zlog(7, Z.target, 0); Z.target = 0; Z.fvalid = 0; }
static void let_go_why(s32 why) { if (Z.target) { zlog(why, Z.target, 0); sfx_play(*(u8 **)0x803491E4, SE_FREE, 0); } Z.target = 0; Z.fvalid = 0; }
static void reticle(u8 *g);

/* ---- the reticle: 4 HUD quads (opguide.agc element 7, AGC_RET_Q) around the target's projected chest.
   Camera *(0x8034922C): +0x50 view matrix (3 x 4 rows), +0x34 aspect, +0x38 vertical FOV in degrees (30.2;
   checked against a screenshot). HUD units: 640 x 480, origin at the centre, y down. Closes in from 60 px
   to 20 px, then breathes; light blue like OoT's people reticle; fades out on release. */
#define AGC        (*(u8 **)0x80349110)
#define RET_COL    0xFFCE2E00u                          /* flat yellow (255, 206, 46) */
#define RET_Y      0.85f                                /* aim this far above the target's feet */
#define RET_H      30.0f                                /* bracket box half-width at RET_DEPTH (HUD px, 640 x 480) */
#define RET_DEPTH  12.0f                                /* ... and it scales with 1 / depth (clamped) */
#define RET_ARM    12                                   /* bracket arm length */
#define RET_W      4                                    /* bracket thickness */
#define RET_SNAP   9.0f                                 /* frames to snap in (ease-out-back, overshoot 2) */
static void quad(u8 *a, s32 k, s32 x0, s32 y0, s32 x1, s32 y1, const float *uv, u32 rgba)
{
    u8 *q = a + AGC_RET_Q + 0x2C * k;
    s32 i, t;
    if (x0 > x1) { t = x0; x0 = x1; x1 = t; }
    if (y0 > y1) { t = y0; y0 = y1; y1 = t; }
    *(u32 *)q = 4;
    *(s16 *)(q + 4) = x0; *(s16 *)(q + 6) = y0; *(s16 *)(q + 8) = x1; *(s16 *)(q + 10) = y1;
    for (i = 0; i < 4; i++) { *(u32 *)(q + 0xC + 4 * i) = rgba; *(float *)(q + 0x1C + 4 * i) = uv[i]; }
}
static void ret_hide(u8 *a)
{
    s32 k;
    for (k = 0; k < 8; k++) quad(a, k, 0, 0, 0, 0, UV_WHITE, 0xFFFFFF00u);
}
/* reticle B (chosen from four mock-ups, tools/ztarget/reticle): four flat yellow corner brackets round the
   target's body; they snap in from twice the size with a little overshoot, then pulse gently */
static void reticle(u8 *g)
{
    u8 *a = AGC, *c = CAM;
    float x, y, z, w, sx, sy, t, k, h, sc;
    s32 cx, cy, e7y, hx, hy, sxn, syn, n = 0;
    u32 col;
    zt_dbg.agc_ok = 0;
    if ((u32)a < 0x80000000u || (u32)a >= 0x81800000u) return;
    zt_dbg.agc_ok = 1;
    if (*(u32 *)a != 0xC1C7C3C6u) return;
    zt_dbg.agc_ok = 2;
    if (*(u32 *)(a + AGC_E7_COUNT) != E7_COUNT) return;   /* our opguide.agc */
    zt_dbg.agc_ok = 3;
    if (Z.target) { if (Z.alpha < 255) Z.alpha += 51; if (Z.alpha > 255) Z.alpha = 255; }
    else { Z.alpha -= 64; if (Z.alpha < 0) Z.alpha = 0; Z.r = -1; }
    if (!Z.alpha || (u32)c < 0x80000000u || (u32)c >= 0x81800000u) { ret_hide(a); return; }
    x = Z.tx; y = Z.ty + RET_Y; z = Z.tz;
    w = proj(x, y, z, &sx, &sy);
    zt_dbg.w = w; zt_dbg.ndx = sx; zt_dbg.ndy = sy;
    if (w <= 0) { ret_hide(a); return; }
    cx = (s32)(sx * 320.0f);
    cy = (s32)(-sy * 240.0f);
    zt_dbg.cx = cx; zt_dbg.cy = cy;
    if (Z.r < 0) Z.r = 0;
    t = Z.r; if (Z.r < 100000) Z.r += 1;
    if (t < RET_SNAP) {                                  /* ease-out-back: 2x size -> 1x, overshooting a little */
        float u = t / RET_SNAP - 1;
        k = 1 + 3.0f * u * u * u + 2.0f * u * u;
        h = 2.0f + (1.0f - 2.0f) * k;
    } else h = 1.0f + 0.05f * zsin((t - RET_SNAP) * (6.28318548f / 42.0f));   /* gentle pulse, 1.4 s */
    sc = RET_DEPTH / w; if (sc < 0.6f) sc = 0.6f; if (sc > 1.6f) sc = 1.6f;
    hx = (s32)(RET_H * sc * h); hy = (s32)(RET_H * 1.15f * sc * h);
    e7y = *(s16 *)(a + AGC_E7_Y); cx -= E7_X; cy -= e7y;
    col = RET_COL | (u32)Z.alpha;
    for (sxn = -1; sxn <= 1; sxn += 2)
        for (syn = -1; syn <= 1; syn += 2) {
            s32 x0 = cx + sxn * hx, y0 = cy + syn * hy;
            quad(a, n++, x0, y0, x0 - sxn * RET_ARM, y0 - syn * RET_W, UV_WHITE, col);   /* horizontal arm */
            quad(a, n++, x0, y0, x0 - sxn * RET_W, y0 - syn * RET_ARM, UV_WHITE, col);   /* vertical arm */
        }
}

static void swing_frame(s32 bpress, s32 free);
static s32 sw_item; static u8 *sw_g;
struct { u32 magic, n, lastm, bpress, tries, fail, starts, bones, slot, arc, anim; float w, frame, len; u32 ring[8][4]; u32 item, kids[4], kbone[4]; } sw_dbg;   /* 'SWDB' (dump) */
void zt_frame(u8 *g, s32 map, volatile u32 *held, volatile u32 *press)
{
    u8 *f = FADER;
    u8 *ev = EVMGR;
    s32 zpress;
    /* free: no script event running (+0x680 == -1). Not +0x58C: test 3 lost the lock near several villagers,
       which looks like their own goings-on setting it (see zt_dbg.noev in a dump) */
    s32 free = map >= 0 && CONTROL == 1 && ev && *(s32 *)(ev + 0x680) == -1 && !(f && *(u8 *)(f + 0x60));
    static s32 notfree;
    zt_log.calls++;
    zt_dbg.magic = 0x5A544442u; zt_dbg.frames++; zt_dbg.map = map; zt_dbg.control = CONTROL; zt_dbg.noev = ev ? *(s32 *)(ev + 0x58C) : -2;
    zt_dbg.fade = f ? *(u8 *)(f + 0x60) : -1; zt_dbg.free = free;
    if (!free) {                                         /* let go only if it lasts (events, menus, fades) */
        zt_dbg.nfree++;
        if (++notfree > 8) release();
        swing_frame(0, 0); reticle(g); return;
    }
    notfree = 0;
    scan_actors();
    if (Z.target) {                                      /* let go when out of reach or gone */
        float *p = SLOT_POS(g, 0), dx, dz;
        if (!tpos(g, Z.target, map, &Z.tx, &Z.tz)) let_go_why(6);
        else {
            dx = Z.tx - p[0]; dz = Z.tz - p[2];
            if (dx * dx + dz * dz > ZT_LEASH * ZT_LEASH) let_go_why(5);
        }
    }
    {   /* Z press from our own record of the last frame: the game's "pressed" compares with a held word we
           clear, so a Z held 2+ frames looked like a second press (test 7: lock + lock-off sounds together) */
        /* from the pad's master record (0x80341464, pad 0 held), which nothing of ours writes: if the hook runs
           twice in a frame, the copy's held Z we cleared on the first call can't fake a new press later */
        static u32 zlast;
        u32 zdown = *(volatile u32 *)0x80341464 & 0x10;
        zpress = zdown && !zlast; zlast = zdown;
        if (zpress) zlog(1, (s32)(*(volatile u32 *)0x80341464 & 0xFFFF), (s32)(*press & 0x10));
    }
    *press &= ~0x10u;
    if (zpress) {                                        /* Z: ours now (no first-person look) */
        zt_dbg.presses++;
        if (!Z.target) {
            Z.target = pick(g, map, 0);
            if (Z.target) { zlog(2, Z.target, zt_dbg.cands); tpos(g, Z.target, map, &Z.tx, &Z.tz); Z.r = -1; sfx_play(*(u8 **)0x803491E4, SE_LOCK, 0); }
            else zlog(8, 0, zt_dbg.cands);
        } else {
            s32 next = pick(g, map, 1);
            if (next) { zlog(3, next, zt_dbg.cands); Z.target = next; tpos(g, next, map, &Z.tx, &Z.tz); Z.r = -1; sfx_play(*(u8 **)0x803491E4, SE_LOCK, 0); }
            else let_go_why(4);
        }
    }
    *held &= ~0x10u;                                     /* holding Z never reaches the game either */
    {   /* B while locked on: the tool swing (ours; B does not reach the game while locked) */
        static u32 blast;
        u32 bdown = *(volatile u32 *)0x80341464 & 0x200;
        s32 bpress = bdown && !blast; blast = bdown;
        u32 mw = *(volatile u32 *)0x80341464;
        if (mw != sw_dbg.lastm) { sw_dbg.lastm = mw; sw_dbg.ring[sw_dbg.n & 7][0] = mw; sw_dbg.ring[sw_dbg.n & 7][1] = *held;
                                  sw_dbg.ring[sw_dbg.n & 7][2] = *press; sw_dbg.ring[sw_dbg.n & 7][3] = (u32)Z.target; sw_dbg.n++; }
        if (bpress) sw_dbg.bpress++;
        s32 item = *(s32 *)(g + 0x11CC4), sickle = item == 0x4E3 || item == 0x4E4 || item == 0x4EA || item == 0x4EB;   /* the weapons: Stick, Wooden Sword, Farmer's Sword, H.M Murasama (tools/weapons) */
        sw_dbg.item = (u32)item;
        if (Z.target && sickle) { *press &= ~0x200u; *held &= ~0x200u; }     /* else B is the game's (put the tool away) */
        sw_item = item; sw_g = g;
        swing_frame(bpress && Z.target && sickle, 1);
    }
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
#define ZT_DIST    9.5f                                 /* lock-on zoom: camera distance (+0x30, normally 12) */
#define ZT_HEIGHT  1.0f                                 /* lock-on: camera height (+0x10, normally 1.5; added to both the eye,
                                                           which sits at the ground behind, and the aim point): lower = nearer the ground */
#define ZT_ZRATE   0.10f
static struct { s32 on; float dist0, h0, tilt; } ZC;
#define ZT_UP      0.07f                                /* lock-on: view pitched up this much (radians, ~4 degrees) */      /* the camera's own values while we change them */

/* after the player's update (HOOK13): turn toward the target; swing the camera behind him, looking past him
   at the target (so stick-up also means toward the target, as in OoT) */
static void zoom(u8 *c, s32 locked)
{
    float *dist = (float *)(c + 0x30), *ht = (float *)(c + 0x10), wd, wh;
    ZC.tilt += ((locked ? ZT_UP : 0) - ZC.tilt) * ZT_ZRATE;
    if (!locked && ZC.tilt < 0.0005f) ZC.tilt = 0;
    if (locked && !ZC.on) { ZC.on = 1; ZC.dist0 = *dist; ZC.h0 = *ht; }
    if (!ZC.on) return;
    wd = locked ? ZT_DIST : ZC.dist0; wh = locked ? ZT_HEIGHT : ZC.h0;
    *dist += (wd - *dist) * ZT_ZRATE; *ht += (wh - *ht) * ZT_ZRATE;
    if (!locked && (*dist - wd) * (*dist - wd) < 0.0004f && (*ht - wh) * (*ht - wh) < 0.0001f) {
        *dist = ZC.dist0; *ht = ZC.h0; ZC.on = 0;         /* back to the game's own values */
    }
}
void zt_post(u8 *pl)
{
    float *pos, *face, dx, dz, d2, inv, fx, fz, want, *yaw, dy;
    u8 *c = CAM;
    s32 cam_ok = (u32)c >= 0x80000000u && (u32)c < 0x81800000u;
    if (cam_ok) zoom(c, Z.target && pl && *(s32 *)(pl + PL_STATE) == 1);
    if (!Z.target || !pl || *(s32 *)(pl + PL_STATE) != 1) return;
    pos = (float *)(pl + 0x4C); face = (float *)(pl + PL_FACE);
    dx = Z.tx - pos[0]; dz = Z.tz - pos[2]; d2 = dx * dx + dz * dz;
    if (d2 < 0.01f) return;
    inv = rsq(d2); dx *= inv; dz *= inv;
    if (!Z.fvalid) { Z.fx = face[0]; Z.fz = face[2]; Z.fvalid = 1; }   /* start from where he faces */
    fx = Z.fx + (dx - Z.fx) * ZT_TURN; fz = Z.fz + (dz - Z.fz) * ZT_TURN;
    d2 = fx * fx + fz * fz;
    if (d2 < 0.0001f) { fx = dx; fz = dz; d2 = 1; }          /* exactly opposite: go straight there */
    inv = rsq(d2); Z.fx = fx * inv; Z.fz = fz * inv;
    face[0] = Z.fx; face[1] = 0; face[2] = Z.fz;
    if (cam_ok) {
        yaw = (float *)(c + 0x1C);
        want = zatan2(-dx, -dz);
        dy = want - *yaw;
        while (dy > 3.14159274f) dy -= 6.28318548f;
        while (dy < -3.14159274f) dy += 6.28318548f;
        *yaw += dy * ZT_CAMRATE;
        while (*yaw > 3.14159274f) *yaw -= 6.28318548f;      /* keep it in -pi..pi (it counted on: -6.95 in a dump) */
        while (*yaw < -3.14159274f) *yaw += 6.28318548f;
    }
}

/* after the camera's look-at (HOOK14/15): pitch the field camera's view up by ZC.tilt. V' = Rx(-t) V on the
   3 x 4 view matrix at +0x50: rows 1 and 2 turn about the camera's x axis (camera looks down -z). */
void zt_tilt(u8 *c)
{
    float *M, s, k, r1, r2;
    s32 i;
    if (c != CAM || ZC.tilt <= 0) return;
    M = (float *)(c + 0x50);
    s = zsin(ZC.tilt); k = zsin(ZC.tilt + 1.57079637f);
    for (i = 0; i < 4; i++) {
        r1 = M[4 + i]; r2 = M[8 + i];
        M[4 + i] = k * r1 + s * r2;
        M[8 + i] = -s * r1 + k * r2;
    }
}

/* ---- moving while locked on (HOOK16 facing, the three motion picks).
   zt_face: func_8003083C has just pointed the facing along the stick (camera-relative) = where he walks;
   keep that as the move direction, then turn him back to our facing toward the target (the model uses the
   facing later in the frame; the step itself comes from the stick and the camera yaw). */
void zt_face(u8 *pl)
{
    float *face = (float *)(pl + PL_FACE);
    Z.mx = face[0]; Z.mz = face[2]; Z.movf = Z.now;
    if (!Z.target || !Z.fvalid || *(s32 *)(pl + PL_STATE) != 1) return;
    face[0] = Z.fx; face[1] = 0; face[2] = Z.fz;
}
/* zt_motion: the free-roaming state picks idle / walk / run every frame with func_8007C100(slot, variant 0 / 3 /
   2, group 0x35, item, item, 4, rate). Locked on and moving: the stick direction against the facing picks
   forward (keep the game's walk / run), back, or a side (left = his +x). The motion player takes a motion entry
   pointer (func_8017D660 keeps it while it is the same one): entries copied from the game's own (its blend
   and flags), pointing at boy_0.anm.arc clips 126 (strafe left), 127 (strafe right), 128 (walk back). */
#define mot_pick   F(0x8007C100, void, (u8 *, s32, s32, s32, s32, s32, float))
#define mot_entry  F(0x800288E8, u32 *, (u32 *, s32, s32, s32, s32, s32, s32))
#define mot_play   F(0x8007C894, void, (u8 *, u32 *, float))
#define CLIP_LEFT  126
#define CLIP_RIGHT 127
#define CLIP_BACK  128
static u32 zt_ent[3][6];
static u8 *sw_slot;                                      /* the player's model slot (from his motion picks) */
void zt_motion(u8 *slot, s32 var, s32 grp, s32 i1, s32 i2, s32 e, float rate)
{
    u32 buf[4], *src;
    s32 k, which;
    float dot, crs;
    sw_slot = slot;
    if (!Z.target || !Z.fvalid || var == 0 || Z.now - Z.movf > 1) { mot_pick(slot, var, grp, i1, i2, e, rate); return; }
    dot = Z.mx * Z.fx + Z.mz * Z.fz; crs = Z.fx * Z.mz - Z.fz * Z.mx;
    if (dot > 0.70710678f) { mot_pick(slot, var, grp, i1, i2, e, rate); return; }   /* forward: the game's own */
    which = dot < -0.70710678f ? 2 : crs < 0 ? 0 : 1;
    src = mot_entry(buf, var, grp, i1, i2, e, 0);           /* the entry the game would play */
    if ((u32)src < 0x80000000u || (u32)src >= 0x81800000u) { mot_pick(slot, var, grp, i1, i2, e, rate); return; }
    for (k = 0; k < 6; k++) zt_ent[which][k] = src[k];
    zt_ent[which][0] = (src[0] & ~0x3FFu) | (u32)(which == 0 ? CLIP_LEFT : which == 1 ? CLIP_RIGHT : CLIP_BACK);
    mot_play(slot, zt_ent[which], rate);
}

/* Tool swing while locked on, as an upper-body layer: the legs keep walking / strafing.
   The pose build (func_8019E438) evaluates every bone with func_801A01F8(ctl, bone, trs); pm_bone_stub sends that
   call here with the model instance. For the player we then blend our own anim controller (the game's 0x1C-byte
   layout: frame, rate, loop, length, anim, next, weight) into the spine, arms and head with the game's own
   blend (func_8019FF8C, the one its motion crossfades use). The clip comes from boy_0.anm.arc (set 0, at
   slot +0x88 -> +0) through func_801A0A88; we advance its frame ourselves, at our own speed. */
#define anim_eval  F(0x801A01F8, s32, (u8 *, s32, u8 *))
#define anim_blend F(0x8019FF8C, void, (u8 *, s32, u8 *, float))
#define arc_anim   F(0x801A0A88, u8 *, (u8 *, s32, s32))
#define ctl_init   F(0x8019FE08, void, (u8 *, u8 *, float))
#define SW_CLIP    129                                  /* combo hits 1-3 = boy_0.anm.arc 129 / 130 / 131 (tools/ztarget/anim combo.py) */
#define SW_IN      2.0f                                 /* hit 1: weight fade in from the walk (frames) */
#define SW_OUT     6.0f                                 /* last hit: fade out over its recovery */
#define SW_XF      3.0f                                 /* chained hit: crossfade from the previous one */
static const float sw_chain[2] = { 11.0f, 9.0f };       /* hit 1 / 2 frame from which a queued B starts the next */
struct swctl { float frame, rate; u32 loop; float len; u8 *anim; struct swctl *next; float w; u32 pad; };
static struct swctl SWC[2];
static struct { s32 on, hit, queued, cur; float w, xf; u32 swings; } SW;
static float smooth01(float x) { if (x <= 0.0f) return 0.0f; if (x >= 1.0f) return 1.0f; return x * x * (3.0f - 2.0f * x); }
/* Combo sounds (Dark Cloud battle sounds from the user's disc, sound bank 436-439, tools/sound): the swing as the
   strike snaps, the impact on the strike frame if the locked-on target is within the weapon's reach in front. */
#define SE_SWING_L 445                                  /* hits 1 / 2: the game's own swoosh 196, lead-in silence trimmed (user pick; 436 unused) */
#define SE_SWING_H 437                                  /* hit 3 */
#define SE_HIT_L   438
#define SE_HIT_H   439
#define SE_VOICE1  440                                  /* Toan's voice (Dark Cloud): hit 1, hit 2, hit 3; 443 hurt / 444 dies for later */
static const float sw_snap[3] = { 5.0f, 3.0f, 10.0f }, sw_strike[3] = { 8.0f, 6.0f, 13.0f };
static float weapon_reach(s32 item)
{
    switch (item) { case 0x4E3: return 1.4f; case 0x4E4: return 1.5f; case 0x4EA: return 1.6f; case 0x4EB: return 2.1f; }
    return 1.4f;
}
/* Impacts only on enemies. There are none yet (villagers / Joe can be locked onto but are never hit), so this is 0
   until enemies exist; then it checks the target's type. */
static s32 target_is_enemy(void *t) { (void)t; return 0; }
static void swing_sounds(float f0, float f1)
{
    s32 h = SW.hit;
    if (f0 < sw_snap[h] && f1 >= sw_snap[h]) {
        sfx_play(*(u8 **)0x803491E4, h == 2 ? SE_SWING_H : SE_SWING_L, 0);
        sfx_play(*(u8 **)0x803491E4, SE_VOICE1 + h, 0);
    }
    if (f0 < sw_strike[h] && f1 >= sw_strike[h] && Z.target && sw_g && target_is_enemy((void *)Z.target)) {
        float *p = SLOT_POS(sw_g, 0), dx = Z.tx - p[0], dz = Z.tz - p[2], r = weapon_reach(sw_item) + 0.4f;
        if (dx * dx + dz * dz < r * r && dx * Z.fx + dz * Z.fz > 0.0f) {
            sfx_play(*(u8 **)0x803491E4, h == 2 ? SE_HIT_H : SE_HIT_L, 0); sw_dbg.n++;
        }
    }
}
static s32 sw_start(s32 hit, s32 chained)
{
    u8 *tab, *arc, *a;
    sw_dbg.tries++;
    if (!sw_slot) { sw_dbg.fail = 1; return 0; }
    tab = *(u8 **)(sw_slot + 0x88); arc = tab ? *(u8 **)tab : 0; sw_dbg.arc = (u32)arc;
    if (!arc) { sw_dbg.fail = 2; return 0; }
    if (*(u32 *)arc != 0x55AA382Du) { sw_dbg.fail = 3; return 0; }
    if ((a = arc_anim(arc, 0, SW_CLIP + hit)) == 0) { sw_dbg.fail = 4; return 0; }
    sw_dbg.anim = (u32)a; sw_dbg.fail = 0; sw_dbg.starts++;
    if (chained) SW.cur ^= 1;
    ctl_init((u8 *)&SWC[SW.cur], a, 0.0f); SWC[SW.cur].rate = 1.0f; SWC[SW.cur].next = 0;
    SW.hit = hit; SW.queued = 0; SW.xf = chained ? SW_XF : 0.0f; SW.on = 1; SW.swings++;
    return 1;
}
static void swing_frame(s32 bpress, s32 free)
{
    struct swctl *c, *p;
    sw_dbg.magic = 0x53574442u; sw_dbg.slot = (u32)sw_slot;
    if (sw_slot) {                                       /* the held tool's model: child instances +0x15C, bone u16 +0x16C */
        u8 *in = *(u8 **)(sw_slot + 0x14); s32 k;
        if ((u32)in >= 0x80000000u && (u32)in < 0x81800000u)
            for (k = 0; k < 4; k++) { sw_dbg.kids[k] = *(u32 *)(in + 0x15C + 4 * k); sw_dbg.kbone[k] = *(unsigned short *)(in + 0x16C + 2 * k); }
    }
    if (!free) { SW.on = 0; SW.w = 0.0f; return; }
    if (bpress) { if (!SW.on) sw_start(0, 0); else if (SW.hit < 2) SW.queued = 1; }
    if (!SW.on) { SW.w = 0.0f; return; }
    c = &SWC[SW.cur];
    if (SW.queued && SW.hit < 2 && c->frame >= sw_chain[SW.hit]) { sw_start(SW.hit + 1, 1); c = &SWC[SW.cur]; }
    p = &SWC[SW.cur ^ 1];
    if (SW.xf > 0.0f) { c->next = p; c->w = smooth01(SW.xf / SW_XF); SW.xf -= 1.0f; } else c->next = 0;
    SW.w = (SW.hit == 0 ? smooth01((c->frame + 1.0f) / SW_IN) : 1.0f) * smooth01((c->len - c->frame) / SW_OUT);
    sw_dbg.w = SW.w; sw_dbg.frame = c->frame; sw_dbg.len = c->len;
    if (p->frame + 1.0f < p->len) p->frame += 1.0f;
    if (c->frame + 1.0f >= c->len) { SW.on = 0; SW.w = 0.0f; return; }
    swing_sounds(c->frame, c->frame + 1.0f);
    c->frame += 1.0f;
}
s32 zt_bone(u8 *ctl, s32 n, u8 *trs, u8 *inst)
{
    s32 r = anim_eval(ctl, n, trs);
    if (r && SW.w > 0.0f && n >= 18 && sw_slot && inst == *(u8 **)(sw_slot + 0x14)) {
        anim_blend((u8 *)&SWC[SW.cur], n, trs, SW.w); sw_dbg.bones++;   /* the clips own the whole spine: full weight */
    }
    return r;
}

/* Player clips 126-131 live in pm.bin (clips.s), not in boy_0.anm.arc: the chapter archive is decompressed into a
   fixed-size heap block (0x8036A000.. +0x62A820 in the dumps) and grew past it with the clips (tools/ztarget/NOTES.md).
   func_801A0A88(arc, 0, clip), the game's clip lookup (motion player, our swing), is hooked: for the player's
   animation archive (set 0 of his set table, 0x802EA714) and clip >= 126 it returns our copy. The game relocates
   every clip of an archive at load (+0 0x00AC7472 -> -1, each track's data offset += clip address); ours are
   relocated the first time they are asked for. */
extern u8 zt_clip126[], zt_clip127[], zt_clip128[], zt_clip129[], zt_clip130[], zt_clip131[];
static u8 *const zt_clips[6] = { zt_clip126, zt_clip127, zt_clip128, zt_clip129, zt_clip130, zt_clip131 };
u8 *arc_anim_orig(u8 *arc, s32 z, s32 clip);            /* hook.s: the original, past the replaced first instruction */
u8 *zt_arc_anim(u8 *arc, s32 z, s32 clip)
{
    if (clip >= 126 && clip < 132 && arc && arc == *(u8 **)0x802EA714) {
        u8 *p = zt_clips[clip - 126];
        if (*(u32 *)p != 0xFFFFFFFFu) {
            s32 n = *(unsigned short *)(p + 4), k;
            for (k = 0; k < n; k++) *(u32 *)(p + 8 + 16 * k + 4) += (u32)p;
            *(u32 *)p = 0xFFFFFFFFu;
        }
        return p;
    }
    return arc_anim_orig(arc, z, clip);
}
