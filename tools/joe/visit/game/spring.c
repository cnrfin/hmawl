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
    W.last[W.n++ & 7] = item;
}

void spring_release(void)
{
    W.item = 0;
}

void spring_frame(u8 *g, s32 map, u32 pad_held, u32 pad_press)
{
    u8 *pl = pm_player;
    float pt[3];
    if (map != VALLEY || !pl) { W.item = 0; return; }

    if ((pad_press & 0x100) && !(pad_held & 0x10) && CONTROL == 1 && !W.item && can_toss(g, pl, pt)) {
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
