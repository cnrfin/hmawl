/* Offerings at the goddess pond (Pool B, the small pool on the high ground by the cliff log).
   The game has an unused "Toss" A action (0x28, label 7): throw motion (player state 0x9B, motion
   0x21; at frame 10 the item leaves the hands with sound 263 "throw"), flight (0x9C, a projectile at
   player+0x1460 moving the hand model player+0x1454), then 0x9D (waits for the motion, back to the
   field). Nothing in the released game ever offers it. Here, holding a tossable item (item flag 0x8,
   the game's own rule: not tools, toys, records or the Blue Feather) while the point in front of the
   player is Pool B water gives the Toss label; A starts the throw at the water, and when the item
   comes down to the surface it is gone with a splash (sound 300 "water").
   Pool B is water type 3 in fishing.col (func_8001DBA0, the lookup fishing uses), x 265..275,
   z 133..145. */

typedef unsigned int u32;
typedef int s32;
typedef unsigned char u8;

#define F(addr, ret, args) ((ret (*) args)(addr))
#define water_type    F(0x8001DBA0, s32, (void *, float *))   /* 0-3 fishing water, 5 none */
#define water_height  F(0x8001DC70, float, (void *, float *))  /* surface y of the fishing water there */
#define ground_y      F(0x8001CB54, float, (void *, float *))  /* the ground the projectile stops on */
#define effect_spawn  F(0x800DD3BC, void, (u8 *, s32, float *, float *, void *, void *, float))
#define EFFECTS       (*(u8 **)0x80349234)
#define FX_SPLASH     0x18       /* the lure's splash (fishing: cast landing, bites) */
#define proj_init     F(0x800DFD24, void, (u8 *, float *))    /* projectile: position, gravity */
#define proj_aim      F(0x800DFE88, float, (u8 *, float))     /* up speed for a distance; returns frames */
#define pl_prep       F(0x800310A4, void, (u8 *, s32))           /* as the A handler does before an action's state */
#define mot_rate      F(0x8017D74C, void, (u8 *, float))
#define pl_state      F(0x80031D7C, void, (u8 *, s32))
#define item_unbind   F(0x801A2AD8, void, (u8 *))
#define sfx_play      F(0x8012A52C, s32, (u8 *, s32, s32))
#define GAME          (*(u8 **)0x803491CC)
#define COLLMAP       (*(void **)0x80349204)
#define CONTROL       (*(u8 *)(*(u8 **)0x80349218 + 8))
#define PAD_PRESS_W   (*(volatile u32 *)0x8034157C)
#define ITEMS         ((u8 *)0x80282DF8)
#define HELD(g)       (*(s32 *)((g) + 0x11CC4))
#define VALLEY        1
#define ST_FIELD      1
#define ST_THROW      0x9B
#define ST_FLY        0x9C
#define ST_DONE       0x9D
#define ACT_TOSS      0x28       /* label 7 "Toss" */
#define POOL_B        3
#define POOL_X0 262.0f
#define POOL_X1 278.0f
#define POOL_Z0 130.0f
#define POOL_Z1 148.0f
#define REACH         1.6f       /* the water must be this far in front */
#define START_UP      0.9f       /* the item leaves from about hand height */
#define SPEED         0.2f       /* the game's own toss speed (lbl_8034A294) */
#define SURFACE_DY    0.4f       /* fallback water surface: this far below the player's feet */
#define FX_COUNTER    (*(s32 *)0x80349280)   /* effect object ids handed out (one per effect made) */
#define SFX_SPLASH    300

extern u8 *pm_player;

/* ---- the goddess quest (gq1, user design; notes/findings 7.62) ----
   Saved in event counter 51 (game+0x12194 + 4 x 51; unused by the game; gq1 had 45 = Joe's 'met' counter): bits 0-14 the 15 offerings made, bit 16 the
   goddess summoned, bit 17 a Mermaid Fossil was ever fished up (debug). Offerings: the 8 basic crops (any quality),
   Goddess Drop / Mist Moon / Trick Blue / Amorous, any milk, any egg, any wool; a new one: "The water shimmers...", the
   15th: "The spring glows softly...". The Mermaid Fossil (item 0x448, the dig table's Strange Fossil renamed; off the dig
   table now) is fished up at Pond A (water 2), ~1.2 % of catches (x(1 + Lck / 20)), until she is summoned. Tossed with
   all 15 done: she is summoned (placeholder: fade to white and back, a line); before that the water pushes it back
   (no throw, so it is never lost). */
#include "gq_mes.h"
#include "gq_scene.h"
extern s32 gq_scene_req;                 /* pm.c gd_frame: the first summoning (1 asked, 0 done, -1 busy) */
s32 gq_slot_busy(void);
#define GQ_HEARTS(c)  (((u32)(c) >> 24) & 0xFF)   /* her affection, bits 24-31 (gq5: full at the summoning, user) */
#define CNT(g, i)     (*(s32 *)((g) + 0x12194 + 4 * (i)))
#define GQ            51
#define GQ_ALL        0x7FFF
#define GQ_SUMMONED   0x10000
#define GQ_FISHED     0x20000
#define FOSSIL        0x448
#define MES_DEBUG     0x32
#define ST_MESSAGE    0x2A
#define POND_A        2
#define OK(p)         ((u32)(p) >= 0x80000000u && (u32)(p) < 0x81800000u)
#define rand_         F(0x8017D3E8, u32, (void))
#define rucksack_add  F(0x8004FDA0, s32, (u8 *, s32, s32, s32))
#define fade_to       F(0x80189128, void, (u8 *, u32 *, u32 *, s32, s32, float))
#define FADER         (*(u8 **)0x803491B8)
#define MSGMGR        (*(u8 **)0x803491C4)
#define fish_size     F(0x80173504, s32, (u8 *, s32))       /* fish index (2 x kind + 0 big / 1 small) */
#define fish_item     F(0x80173A0C, s32, (u8 *))            /* the caught item: table 0x802C9238[index] */
#define fish_msg      F(0x801739A4, void, (u8 *))           /* "You caught <item>!" (system.mes 0xE1) */
#define msg_item      F(0x80102310, void, (u8 *, s32, s32))
#define msg_open      F(0x801020E4, void, (u8 *, s32, s32, s32, s32, s32, s32, s32))
static s32 gq_bit(s32 i)
{
    if (i >= 0x1F && i <= 0x36) return 1 << ((i - 0x1F) / 3);          /* Tomato .. Sweet Potato, 3 qualities each */
    if (i == 0x43E) return 1 << 8;                                      /* Goddess Drop (spring) */
    if (i >= 0x43B && i <= 0x43D) return 1 << (9 + i - 0x43B);           /* Mist Moon, Trick Blue, Amorous */
    if (i >= 0x007 && i <= 0x018) return 1 << 12;                       /* any cow / goat milk */
    if (i >= 0x01C && i <= 0x01E) return 1 << 13;                       /* any egg */
    if (i >= 0x019 && i <= 0x01B) return 1 << 14;                       /* any wool */
    return 0;
}
struct { u32 magic; s32 pending, bitwas, rolls, hits, msg, sum, t; } GQD;   /* 'GQST' (dump) */
s32 gq_fish_size(u8 *fm, s32 kind)                    /* replaces the call at 0x8017343C */
{
    s32 idx = fish_size(fm, kind), lck = 0;
    u8 *g = GAME;
    GQD.magic = 0x47515354u; GQD.pending = 0; GQD.rolls++;
    if (!OK(g) || kind < 0 || kind > 7 || *(s32 *)(fm + 0x68) != POND_A || (CNT(g, GQ) & GQ_SUMMONED)) return idx;
    if (CNT(g, 54) == 0x53543031) lck = CNT(g, 60);   /* stats.c Lck */
#ifdef GQ_TEST
    lck = 1640;                                        /* test: half the Pond A catches */
#endif
    if ((s32)(rand_() % 10000u) < 120 * (20 + lck) / 20) {
        GQD.pending = 1; GQD.hits++; idx = 7;          /* on the line it is the smallest fish (Snelt) */
        GQD.bitwas = (*(u32 *)(g + 0x299FC) >> 7) & 1; /* its fishing-record bit, put back when caught */
    }
    return idx;
}
s32 gq_fish_item(u8 *fm)                              /* replaces the call at 0x800483A0 */
{
    s32 it = fish_item(fm);
    u8 *g = GAME;
    if (!GQD.pending || !OK(g)) return it;
    if (!GQD.bitwas) *(u32 *)(g + 0x299FC) &= ~(1u << 7);
    CNT(g, GQ) |= GQ_FISHED;
    return FOSSIL;
}
void gq_fish_msg(u8 *fm)                              /* replaces the call at 0x800483F4 */
{
    if (!GQD.pending) { fish_msg(fm); return; }
    GQD.pending = 0;
    msg_item(MSGMGR, 0, FOSSIL);
    msg_open(MSGMGR, 1, 0x33, 0xE1, -1, 0x70, 0, 0);
}
static void poke(u32 a, u32 want, u32 other)
{
    u32 *p = (u32 *)a;
    if (*p != other) return;
    *p = want;
    __asm__ volatile("dcbst 0,%0\n\tsync\n\ticbi 0,%0\n\tisync" :: "r"(p) : "memory");
}
#define BL(at, to)  (0x48000001u | (((u32)(to) - (u32)(at)) & 0x03FFFFFCu))
static void gq_hooks(void)
{
    poke(0x8017343C, BL(0x8017343C, gq_fish_size), BL(0x8017343C, 0x80173504));
    poke(0x800483A0, BL(0x800483A0, gq_fish_item), BL(0x800483A0, 0x80173A0C));
    poke(0x800483F4, BL(0x800483F4, gq_fish_msg), BL(0x800483F4, 0x801739A4));
    if (*(volatile unsigned short *)0x80292916 == 0xC8) *(volatile unsigned short *)0x80292916 = 0;   /* dig table: no Strange Fossil */
}

static struct {
    s32 item;                    /* in flight (0 = none) */
    s32 fly, frames;             /* frames flown, frames of the arc */
    float surface;
    float fx_at[3], fx_dir[3];   /* the splash keeps pointers to these (position, facing): must outlive it */
    s32 fx_made;                 /* debug: effect ids handed out by the last splash (0 = none made) */
    s32 n;                       /* offerings made (debug) */
    s32 last[8];                 /* last items tossed (debug, for RAM dumps) */
} W;

static float rsqrt(float x)               /* frsqrte + two Newton steps */
{
    float r;
    __asm__("frsqrte %0, %1" : "=f"(r) : "f"(x));
    r = r * (1.5f - 0.5f * x * r * r);
    r = r * (1.5f - 0.5f * x * r * r);
    return r;
}

static s32 tossable(s32 item)
{
    return item > 0 && item < 0x52C && (*(u32 *)(ITEMS + item * 0x24 + 0x1C) & 8);
}

/* the point REACH in front of the player is Pool B water; pt gets that point */
static s32 facing_pool(u8 *g, float *pt)
{
    float *p = (float *)(g + 0x29C78), *d = (float *)(g + 0x29F84);
    float dx = d[0], dz = d[2], l2 = dx * dx + dz * dz, r;
    if (l2 < 0.0001f) return 0;
    r = rsqrt(l2);
    pt[0] = p[0] + dx * r * REACH; pt[1] = p[1] + 1.0f; pt[2] = p[2] + dz * r * REACH;
    if (pt[0] < POOL_X0 || pt[0] > POOL_X1 || pt[2] < POOL_Z0 || pt[2] > POOL_Z1) return 0;
    return water_type(COLLMAP, pt) == POOL_B;
}

static s32 can_toss(u8 *g, u8 *pl, float *pt)
{
    return pl && *(s32 *)(pl + 0x64) == VALLEY && *(s32 *)(pl + 0x1364) == ST_FIELD &&
           tossable(HELD(g)) && facing_pool(g, pt);
}

/* the field A handler's action (via pm_label): Toss at Pool B */
s32 spring_label(s32 action, u8 *pl)
{
    u8 *g = GAME;
    float pt[3];
    if ((u32)g < 0x80000000u || (u32)g >= 0x81800000u) return action;
    return can_toss(g, pl, pt) ? ACT_TOSS : action;
}

static void offering(u8 *g, s32 item)
{
    s32 b = gq_bit(item), c = CNT(g, GQ);
    W.last[W.n++ & 7] = item;
    if (item == FOSSIL && (c & GQ_ALL) == GQ_ALL && !(c & GQ_SUMMONED)) {   /* the summoning */
        u8 *fd = FADER;
        CNT(g, GQ) = (c | GQ_SUMMONED | 0xFF000000u);         /* gq5: her affection starts full (a year of offerings) */
        gq_scene_req = 1;                                        /* pm.c raises her and runs event GQ_SCENE_EVENT */
        if (OK(fd)) { u32 from = 0xFFFFFFFFu, to = 0xFFFFFF00u; fade_to(fd, &from, &to, 0, 0, 1.6f); }   /* gq4: one flash (white -> clear;
                                                           gq1-3's white-in, hold, white-out read as two) */
        GQD.sum = 1; GQD.t = 0;
        return;
    }
    if (b && !(c & b)) { CNT(g, GQ) = c | b; GQD.msg = ((c | b) & GQ_ALL) == GQ_ALL ? GQ_MSG_GLOW : GQ_MSG_SHIMMER; }
}

void spring_release(void)
{
    W.item = 0;
}

void spring_frame(u8 *g, s32 map, u32 pad_held, u32 pad_press)
{
    u8 *pl = pm_player;
    float pt[3];
    gq_hooks();
    if (map != VALLEY || !pl) { W.item = 0; return; }
#ifdef GQ_TEST
    {   /* test (gq2): Z + D-Down fills the rucksack's free slots with offerings not yet made (and not already
           carried); with all 15 made, the Mermaid Fossil. Z from the pad's own record (zt.c takes Z out of the held word before we see it). */
        static const short need[15] = { 0x1F, 0x22, 0x25, 0x28, 0x2B, 0x2E, 0x31, 0x34, 0x43E, 0x43B, 0x43C, 0x43D, 0x07, 0x1C, 0x19 };
        if ((*(volatile u32 *)0x80341464 & 0x10) && (pad_press & 0x4)) {
            s32 k, n = 0, c = CNT(g, GQ);
            s32 room = 0, have, j;
            for (j = 0; j < 18; j++) if (!(*(u32 *)(g + 0x58 + 4 * j) >> 16)) room++;   /* rucksack: 18 slots {item, count, ff} */
            for (k = 0; k < 15 && n < room; k++) {
                if (c & (1 << k)) continue;
                for (have = 0, j = 0; j < 18; j++) if ((s32)(*(u32 *)(g + 0x58 + 4 * j) >> 16) == need[k]) have = 1;
                if (!have) { rucksack_add(g + 0x50, need[k], 1, -1); n++; }
            }
            if ((c & GQ_SUMMONED) && room) CNT(g, GQ) = c & ~(GQ_SUMMONED | 0xFF000000u);   /* gq5: replay the scene */
            if ((c & GQ_ALL) == GQ_ALL && room) rucksack_add(g + 0x50, FOSSIL, 1, -1);
            sfx_play(*(u8 **)0x803491E4, 261, 0);       /* the pick-up sound */
        }
    }
#endif
    if (GQD.sum) {                                       /* placeholder summon: white, hold, back */
        u8 *fd = FADER;
        (void)fd;
        if (++GQD.t >= 100) GQD.sum = 0;                        /* gq5: the scene follows the flash (no line) */
    }
    if (GQD.msg && !W.item && *(s32 *)(pl + 0x1364) == ST_FIELD && CONTROL == 1) {
        *(s32 *)(pl + 0x14C0) = MES_DEBUG; *(s32 *)(pl + 0x14C4) = GQD.msg; GQD.msg = 0;
        pl_state(pl, ST_MESSAGE);
        return;
    }

    if ((pad_press & 0x100) && !(pad_held & 0x10) && CONTROL == 1 && !W.item && !GQD.sum && can_toss(g, pl, pt) &&
        HELD(g) == FOSSIL && !(CNT(g, GQ) & GQ_SUMMONED) && ((CNT(g, GQ) & GQ_ALL) != GQ_ALL || gq_slot_busy())) {
        PAD_PRESS_W &= ~0x100u;                          /* not time yet (or the Postman / Joe is out): no throw */
        *(s32 *)(pl + 0x14C0) = MES_DEBUG;
        *(s32 *)(pl + 0x14C4) = (CNT(g, GQ) & GQ_ALL) != GQ_ALL ? GQ_MSG_NOTYET : GQ_MSG_BUSY;
        pl_state(pl, ST_MESSAGE);
        return;
    }
    if ((pad_press & 0x100) && !(pad_held & 0x10) && CONTROL == 1 && !W.item && !GQD.sum && can_toss(g, pl, pt)) {
        float *p = (float *)(g + 0x29C78), *pr = (float *)(pl + 0x1460), st[3], dx, dz, l2, r, dist;
        PAD_PRESS_W &= ~0x100u;                          /* the A handler does nothing else */
        st[0] = p[0]; st[1] = p[1] + START_UP; st[2] = p[2];
        dx = pt[0] - st[0]; dz = pt[2] - st[2]; l2 = dx * dx + dz * dz;
        r = rsqrt(l2); dist = l2 * r;
        proj_init((u8 *)pr, st);
        pr[3] = dx * r * SPEED; pr[4] = 0; pr[5] = dz * r * SPEED;
        W.frames = (s32)proj_aim((u8 *)pr, dist);
        *(float *)(pl + 0x1494) = 9999.0f;               /* the flight state never ends by itself (no target) */
        W.item = HELD(g); W.fly = 0;
        W.fx_dir[0] = dx; W.fx_dir[1] = 0; W.fx_dir[2] = dz;
        W.surface = water_height(COLLMAP, pt);               /* fishing water (below the visible surface) */
        {   float gy = ground_y(COLLMAP, pt);                 /* the visible surface: the ground check stops */
            if (gy > W.surface && gy < W.surface + 1.5f) W.surface = gy;   /* thrown things on it */
        }
        if (!(W.surface < p[1] + 0.5f && W.surface > p[1] - 3.0f)) W.surface = p[1] - SURFACE_DY;
        pl_prep(pl, 1);
        mot_rate(*(u8 **)(pl + 0xBC) + 0x54, 1.0f);
        pl_state(pl, ST_THROW);
        return;
    }

    if (W.item) {
        s32 st = *(s32 *)(pl + 0x1364);
        float *pr = (float *)(pl + 0x1460);
        if (st == ST_FLY) {
            ++W.fly;
            if ((W.fly > W.frames / 2 && pr[1] <= W.surface + 0.05f) || W.fly > W.frames + 30) {   /* down at the water */
                W.fx_at[0] = pr[0]; W.fx_at[1] = W.surface; W.fx_at[2] = pr[2];
                {   s32 c0 = FX_COUNTER;
                    if (EFFECTS) effect_spawn(EFFECTS, FX_SPLASH, W.fx_at, W.fx_dir, 0, 0, 0.0f);
                    W.fx_made = FX_COUNTER - c0;
                }
                item_unbind(*(u8 **)(pl + 0x1454));
                sfx_play(*(u8 **)0x803491E4, SFX_SPLASH, 0);
                offering(g, W.item);
                W.item = 0;
                pl_state(pl, ST_DONE);
            }
        } else if (st != ST_THROW) W.item = 0;          /* interrupted */
    }
}
