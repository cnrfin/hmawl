/* Postman NPC for Harvest Moon: A Wonderful Life (US). Runs once per frame from the end of the
   pad update (hook at 0x80213CFC). On the 8th of every season, 9:00-11:00, while the player is on
   the valley map (map 1), the Postman (character 37 with the pm/pm_0 model) runs the route from the
   east road to Romana's gate (arriving at 10:00), waits, and runs back (gone at 11:00). His place on
   the route follows the game clock. Pressing A next to him starts the milk event (406) once per
   visit (event 406 sets flag 61 once you answer, with milk in hand). He is an event-style actor (ObjectEventCharacter) allocated with operator
   new, registered with the actor manager, and given an NPC body collider. */

typedef unsigned int u32;
typedef int s32;
typedef unsigned char u8;
typedef struct { float x, y, z; } Vec;

/* ---- game data */
#define GAME        (*(u8 **)0x803491CC)
#define EVMGR       (*(u8 **)0x803491BC)
#define FADER       (*(u8 **)0x803491B8)          /* screen fader; +0x60 == 1 while fading */
#define CHARMGR     (*(u8 **)0x803491DC)
#define ACTMGR      (*(u8 **)0x8034923C)
#define COLLMAP     (*(void **)0x80349204)
#define CLOCK       (**(u32 **)0x80349218)        /* tenths of a second since the start */
#define CONTROL     (*(u8 *)(*(u8 **)0x80349218 + 8))   /* 1 = player free; 0 in menus (X menu: state 3 enter) */
#define PAD_HELD    (*(volatile u32 *)0x80341574)
#define PAD_PRESS   (*(volatile u32 *)0x8034157C)
#define MODEL74_NAME (*(const char **)0x8024A15C)  /* model entry 74 (character 37) */
#define MODEL74_SIZE ((float *)0x8024A160)
#define SET71_NAME  (*(const char **)0x802490CC)  /* animation set 71 */
#define SET71_DATA  ((u32 *)(0x802EA714 + 71 * 0x30))   /* loaded set 71 (archive pointer at +0) */
#define MODEL37_ARC (*(u8 **)(0x802EB4D4 + 37 * 0x44))   /* character 37's loaded model archive: the entry's ARC handle +0 (func_8002D3B4 frees it) */

/* ---- game functions */
#define F(addr, ret, args) ((ret (*) args)(addr))
#define op_new        F(0x80178E88, void *, (u32, const char *, s32))
#define op_delete     F(0x80179168, void, (void *))
#define load_model    F(0x8002D128, void, (s32))
#define unload_model  F(0x8002D3B4, void, (s32))
#define load_animset  F(0x80027FAC, void, (s32, s32))
#define unload_animset F(0x800282A0, void, (s32))
#define char_slot     F(0x8007E248, u8 *, (u8 *, s32, s32))
#define slot_setup    F(0x8007B8F8, void, (u8 *, s32, s32))
#define actor_ctor    F(0x8007F328, u8 *, (u8 *, short, s32))
#define actor_dtor    F(0x8007F648, void, (u8 *, short))
#define actor_add     F(0x8017CD5C, void, (u8 *, u8 *, u32))
#define actor_setpos  F(0x8007F994, void, (u8 *, Vec *))
#define actor_setdir  F(0x8007F9B8, void, (u8 *, Vec *))
#define actor_show    F(0x8007F910, void, (u8 *))
#define actor_hide    F(0x8007F8EC, void, (u8 *))
#define actor_motion  F(0x80080238, void, (u8 *, s32))
#define ground_y      F(0x8001CB54, float, (void *, Vec *))
#define col_init      F(0x801520F8, void, (u8 *))
#define col_config    F(0x80152218, void, (u8 *, s32))
#define game_rand     F(0x8017D3E8, s32, (void))
#define event_start   F(0x8010AAC4, s32, (u8 *, s32, s32, s32))
#define ship_check    F(0x80136260, void, (u8 *))   /* func_80136260: farm daily checks -> func_801331A4(game+0x11B58) */
#define day_plan      F(0x80060EF8, void, (u8 *))     /* a villager's daily plan (reads state+8 only) */
#define trade_update  F(0x80134104, s32, (u8 *, s32))
#define fade_start    F(0x80189128, void, (u8 *, u32 *, u32 *, s32, s32, float))  /* fader, from, to, hold, 0, seconds */
#define flag_get      F(0x801129A0, s32, (u8 *, s32))
#define flag_clear    F(0x80112A30, void, (u8 *, s32))
#define rucksack_add  F(0x8004FDA0, s32, (u8 *, s32, s32, s32))   /* container game+0x50: id, count, slot (-1 = any) */
#define vcall(obj, vt_off, idx) (*(void (**)(u8 *, s32))(*(u32 *)((obj) + (vt_off)) + 4 * (idx)))

#define CHAR_ID   37
#define ANIMSET   71
#define VALLEY    1
#define EVENT     406
#define scene_req F(0x8017767C, void, (u8 *, s32, s32))
#define tsk_flags F(0x80012568, u32, (void))                /* the game's time skip, one minute (lbl_80109E44) */
#define w_upd1    F(0x8017CD7C, void, (u8 *, u32))
#define w_upd2    F(0x8017CDC0, void, (u8 *, u32))
#define w_upd3    F(0x8017CE04, void, (u8 *, u32))
#define w_upd4    F(0x8017CFD4, void, (u8 *))
#define w_upd5    F(0x8017CF2C, void, (u8 *))
#define clk_add   F(0x800101FC, void, (u8 *, s32))          /* clock object (*0x80349218) += minutes */
#define clk_align F(0x80010158, s32, (u8 *))                /* clock up to the next whole minute */
#define tsk_after F(0x80015760, void, (u8 *, u32))
u32 bench_minutes, bench_rolls;   /* g_system, scene (4 = field), flag */
u32 bench_reloads; static s32 bench_wait;   /* frames left to check that the reloaded valley faded in */
static u32 bench_target, bench_start, bench_cool, bench_taka_day = 0xFFFFFFFFu;       /* bench time skip: clock target (0 = idle), clock at the start */
#define BENCH_CNT 40                        /* event counter 40: set by the bench script on Yes (0-29 count up daily) */
#define BENCH_EVENT 407                     /* bench: sit until evening / morning */
#define BENCH_X   137.65f                   /* turned bench by the tree: seat centre (mapobj col box) */
#define BENCH_Z   176.60f
#define FLAG_MET  61             /* set by event 406 when you answer him (milk chance used) */
#define FLAG_FED  62             /* set by event 406 when he got the milk: later talks say thanks */
#define MOT_IDLE  0
#define MOT_RUN   1
#define MOT_JOG   2              /* set 71 motion entry 2, pointed at our jog (anim 6) while he is loaded */
#define MOT2_WORD (*(u32 *)0x80241EC8)  /* set 71 motion entry 2, word 0 (set 71, anim 2 = 0x8E004C02) */
#define MOT2_JOG  0x8E000406u   /* set 71, anim 6, the run entry's flags */
#define RUN_RATE  1.3f           /* run cycle plays this much faster (his speed comes from the clock) */
#define T_DAY     864000u
#define T_START   324000u        /* 9:00 */
#define T_DOOR    360000u        /* 10:00 arrives */
#define T_BACK    369000u        /* 10:15 leaves */
#define T_END     396000u        /* 11:00 gone */
#define TALK_R2   4.0f
#define CAM_D       3.4f   /* talk camera: eye distance in front of him */
#define CAM_SIDE    0.0f   /*   to the side */
#define CAM_EYE_Y   2.1f   /*   eye height above his feet (a little above his head: looks down) */
#define CAM_BEHIND  0.0f   /*   aim point behind him */
#define CAM_AIM_Y   1.1f   /*   aim height (upper chest: head above the text box) */
#define COL_VTABLE 0x802C5720
#define GET_D       2.6f   /* item-get close-up: eye distance in front of the player */
#define GET_EYE_Y   1.35f
#define GET_AIM_Y   1.1f
#define GET_ITEM_D  0.6f   /*   the spinning item: in front of him, chest height (above the text box) */
#define GET_ITEM_Y  1.3f
#define CNT_FADEBACK 19    /* set by event 406 when it ends on black: fade back in */
#define CNT_JOG      8     /* set by event 406 during the item-get close-up: he jogs on the spot */

#include "route.h"
#include "joe_route.h"               /* ROUTE_N, route[ROUTE_N][3] (x, z, y), ROUTE_LEN */

static const char pm_model[] = "pm/pm_0.arc";
static const char pm_anims[] = "pm/pm_0.anm.arc";
static const float pm_size[3] = { 0.95f, 1.58f, 1.2f };
/* Joe's model and animations (gd_0: first used for the Harvest Goddess test in this slot) */
static const char gd_model[] = "gd/gd_0.arc";
static const char gd_anims[] = "gd/gd_0.anm.arc";
static const float gd_size[3] = { 0.95f, 1.96f, 1.2f };
/* the Harvest Goddess (gq5): her own disc files (tools/goddess/build gd_0.* under new names: gd/ is Joe's now);
   Celia's skeleton and Celia's 10 animations (0 idle, 1 walk, 2 holding, 3 put away, 4 explain, 5 run, 6 plead,
   7 dizzy, 8 crouch, 9 kitchen work) */
static const char hg_model[] = "hg/hg_0.arc";
static const char hg_anims[] = "hg/hg_0.anm.arc";
static const float hg_size[3] = { 0.95f, 1.70f, 1.2f };
#define HG_ANIMS 10
#define WHO_HG   3
#define GD_X 270.3f                       /* Pool B, the goddess pond (centre) */
#define GD_Z 139.0f
#define GD_AHEAD 2.4f                     /* test spawn: this far in front of the player */
#define GD_ANIMS 13                       /* Joe (gd_0 test 13+): idle, walk, Van's 2-5, sit down, sitting, stand up,
                                             talk (Van's 17), sitting talk, gift (take + pocket),
                                             12 = the sitting loop again, with the cross-fade (after talking) */
#define SET71_LIST (*(u32 ***)(0x80248B40 + 71 * 0x14 + 0xC))   /* set 71's motion list (motion n -> entry) */
static u32 gd_mot[GD_ANIMS][6];           /* her motion entries: [set*2, flags, anim], mask, ... (as the teddy's) */
static u32 *gd_list[GD_ANIMS];

static struct {
    u8 *actor, *col;
    s32 loaded;                 /* our model/animations are set up in character slot 37 */
    s32 talking, motion;
    s32 forced; u32 force_t0;     /* test visit started with Z + D-Left */
    s32 who;                      /* the slot's model: 0 Postman, 1 Goddess (test) */
    s32 gd_anim;                  /* goddess test: animation shown */
    const char *orig_model, *orig_anims;
    float orig_size[3];
    u32 orig_set[12];            /* set 71's loaded entry before ours */
    u32 orig_mot2;
    u32 **orig_list;
    void *guard;                  /* spacer while our model is loaded (see setup_model) */
    u8 *own_model, *own_anims;    /* our two archives in memory (character 37's model entry +0x10, set 71 +0) */
    u8 *orphan[4];                /* our archives left behind by a scene change: freed once nothing uses them */
    s32 sweep;                    /* frames since the last duplicate sweep */
    u8 *last_anims;               /* the animation archive we loaded last (set 71 +0) */
    Vec pos, dir;
} S;

static float rsqrt(float x)               /* Gekko has no fsqrt: estimate + two Newton steps */
{
    float r;
    __asm__("frsqrte %0, %1" : "=f"(r) : "f"(x));
    r = r * (1.5f - 0.5f * x * r * r);
    r = r * (1.5f - 0.5f * x * r * r);
    return r;
}

static s32 no_event(void)
{
    u8 *m = EVMGR;
    return m && *(s32 *)(m + 0x680) == -1 && *(s32 *)(m + 0x58C) == 0;
}

static void motion(s32 m)
{
    if (S.motion == m && *(s32 *)(S.actor + 0x214) == 4) return;   /* still playing (state 4) */
    S.motion = m;
    actor_motion(S.actor, m);
}

/* distance along the route for time of day t (inside the visit) */
static float route_s(u32 t, s32 *mode)
{
    if (t < T_DOOR) { *mode = 0; return ROUTE_LEN * (float)(t - T_START) / (float)(T_DOOR - T_START); }
    if (t < T_BACK) { *mode = 1; return ROUTE_LEN; }
    *mode = 2; return ROUTE_LEN * (float)(T_END - t) / (float)(T_END - T_BACK);
}

static void place(float s, s32 back)
{
    s32 i = 0;
    float dx = 0, dz = 0, len = 1, t;
    for (;;) {
        dx = route[i + 1][0] - route[i][0];
        dz = route[i + 1][1] - route[i][1];
        len = seglen[i];
        if (s < len || i == ROUTE_N - 2) break;
        s -= len; i++;
    }
    if (s < 0) s = 0;
    if (s > len) s = len;
    t = s / len;
    S.pos.x = route[i][0] + dx * t;
    S.pos.z = route[i][1] + dz * t;
    S.pos.y = route[i][2] + (route[i + 1][2] - route[i][2]) * t + 2.0f;
    S.pos.y = ground_y(COLLMAP, &S.pos);
    S.dir.x = back ? -dx / len : dx / len;
    S.dir.y = 0;
    S.dir.z = back ? -dz / len : dz / len;
    actor_setpos(S.actor, &S.pos);
    actor_setdir(S.actor, &S.dir);
}

/* model + animations of character 37 = the Postman (names patched while he is around) */
/* Memory: the general pool (operator new) hands out its lowest free blocks first, and the valley
   leaves them right on top of the mainchapter archive, where the per-frame pool (func_8017860C:
   bone matrices etc.) grows upward. Our model, animations and actor landed there and were written
   over (goddess tests 4-5: 2-3 KB between the pools, vanilla 276 KB). A spacer taken first keeps
   them clear of it while they are loaded. */
#define GUARD_SIZE 0x40000
/* Pool A for Joe (memfix 18). The game runs two allocators over the same arena: pool A (0x802FD4D0) from the bottom
   up - the chapter archive, then each area's code module (a building's REL: the inn's is 239 KB) - and pool B
   (0x80315508, operator new) from the top down. Neither knows the other, so B must never put anything below
   "chapter archive + the largest area module". Joe's model + animations (230 KB) in B, loaded last, pushed B's
   bottom down by 230 KB, and every block the game allocated after him (never moved again) stayed that low: in a
   building the module was loaded over them (memfix 17 dump 92afe3f3: 3 game blocks, 7 KB, inside the inn's
   module). In the valley no module sits above the chapter archive, so Joe's archives go there, into pool A, and
   are freed at every scene change (joe_free_now) before the next area's module is loaded. op_new / op_delete
   are hooked (pm_new_stub / pm_del_stub in hook.s): while joe_to_a is set, a request of 64 KB or more goes to
   pool A if it ends at least 64 KB below B's lowest block; otherwise to B as before. */
s32 joe_to_a;
/* Pool guard (memfix 19, 'MGRD'): after every allocation the new block is checked against the other pool's used
   blocks. An overlap is the corruption behind the T-poses / garbled textures / crashes; it is recorded here and the
   first one makes Dolphin say "Invalid read from 0x0bad00a0" (a pool-A block over pool B, e.g. an area module) or
   "0x0bad00b0" (a pool-B block over pool A). Ignore it and play on; a RAM dump then shows who (lr = caller). */
struct { u32 magic, n_a, n_b, overlaps, signalled, b_low, b_low_min, b_low_min_lr;
         u32 pool, p, size, lr, lr2, other_p, other_size, frame; } mg;
static u32 mg_frames;
void mg_after(u32 pool, u8 *p, u32 size, u32 lr, u32 lr2)
{
    u8 *r; s32 k; u32 lo = (u32)p, hi;
    if (!p) return;
    mg.magic = 0x4D475244u;
    hi = lo + ((size + 0x1F) & ~0x1Fu);
    if (pool == 0x80315508u) {
        mg.n_b++;
        if (!mg.b_low || lo < mg.b_low) mg.b_low = lo;
        if (!mg.b_low_min || lo < mg.b_low_min) { mg.b_low_min = lo; mg.b_low_min_lr = lr2 ? lr2 : lr; }
        for (r = *(u8 **)(0x802FD4D0 + 0x10), k = 0; r && k < 300; r = *(u8 **)(r + 8), k++) {
            u32 a = *(u32 *)r, e = a + *(u32 *)(r + 4);
            if (*(u32 *)(r + 0xC) == 2 && lo < e && a < hi) { r = (u8 *)a; size = e - a; goto hit; }
        }
        return;
    }
    if (pool != 0x802FD4D0u) return;
    mg.n_a++;
    if (mg.b_low && hi <= mg.b_low) return;             /* below B's lowest block (cached): fine */
    for (r = *(u8 **)(0x80315508 + 0x10), k = 0; r && k < 6000; r = *(u8 **)(r + 8), k++) {
        u32 e = *(u32 *)r, a = e - *(u32 *)(r + 4);
        if (*(u32 *)(r + 0xC) == 2 && lo < e && a < hi) { r = (u8 *)a; size = e - a; goto hit; }
    }
    return;
hit:
    mg.overlaps++;
    mg.pool = pool; mg.p = lo; mg.size = hi - lo; mg.lr = lr; mg.lr2 = lr2; mg.other_p = (u32)r; mg.other_size = size;
    mg.frame = mg_frames;
    if (!mg.signalled) { mg.signalled = 1; (void)*(volatile u32 *)(pool == 0x802FD4D0u ? 0x0BAD00A0u : 0x0BAD00B0u); }
}
static u8 *a_blk[8]; static u32 a_len[8];
#define allocA  F(0x8017860C, void *, (u32, const char *, s32))
#define freeA   F(0x80178660, void, (void *))
static u32 pool_a_top(void)
{
    u8 *r; s32 k; u32 t = 0;
    for (r = *(u8 **)(0x802FD4D0 + 0x10), k = 0; r && k < 300; r = *(u8 **)(r + 8), k++)
        if (*(u32 *)(r + 0xC) == 2 && *(u32 *)r + *(u32 *)(r + 4) > t) t = *(u32 *)r + *(u32 *)(r + 4);
    return t;
}
static u32 pool_b_low(void)
{
    u8 *r; s32 k; u32 lo = 0xFFFFFFFFu;
    for (r = *(u8 **)(0x80315508 + 0x10), k = 0; r && k < 6000; r = *(u8 **)(r + 8), k++)
        if (*(u32 *)(r + 0xC) == 2 && *(u32 *)r - *(u32 *)(r + 4) < lo) lo = *(u32 *)r - *(u32 *)(r + 4);
    return lo;
}
u8 *pm_new_a(u32 size, const char *tag, s32 line)
{
    u8 *p; s32 i;
    size = (size + 0x1F) & ~0x1Fu;
    for (i = 0; i < 8 && a_blk[i]; i++) ;
    if (i == 8 || pool_b_low() < pool_a_top() + size + 0x10000) return 0;
    p = allocA(size, tag, line);
    if (!p) return 0;
    if ((u32)p + size + 0x10000 > pool_b_low()) { freeA(p); return 0; }   /* (placed higher than expected) */
    a_blk[i] = p; a_len[i] = size;
    return p;
}
s32 pm_del_a(u8 *p)
{
    s32 i;
    for (i = 0; i < 8; i++) if (a_blk[i] == p) { freeA(p); a_blk[i] = 0; a_len[i] = 0; return 1; }
    return 0;
}
static u32 a_size(u8 *p)
{
    s32 i;
    for (i = 0; i < 8; i++) if (p && a_blk[i] == p) return a_len[i];
    return 0;
}
static void orphan(u8 *p);
struct dupdbg { u32 magic, sweeps, cands, refd, freed, last_ref, spawns, reloads; };
extern struct dupdbg dup_dbg;
static void setup_model(void)
{
    u8 *slot = char_slot(CHARMGR, CHAR_ID, 0);
    s32 i;
    /* (no spacer any more: our archives go to pool A, see pm_new_a) */
    if (slot[0xC]) {                         /* the teddy (or an old copy) is set up: clear it */
        vcall(slot, 0, 2)(slot, 0);
        unload_model(CHAR_ID);
    }
    S.orig_model = MODEL74_NAME; S.orig_anims = SET71_NAME;
    S.orig_size[0] = MODEL74_SIZE[0]; S.orig_size[1] = MODEL74_SIZE[1]; S.orig_size[2] = MODEL74_SIZE[2];
    {   const float *sz = S.who == WHO_HG ? hg_size : S.who ? gd_size : pm_size;
        MODEL74_NAME = S.who == WHO_HG ? hg_model : S.who ? gd_model : pm_model;
        SET71_NAME = S.who == WHO_HG ? hg_anims : S.who ? gd_anims : pm_anims;
        MODEL74_SIZE[0] = sz[0]; MODEL74_SIZE[1] = sz[1]; MODEL74_SIZE[2] = sz[2];
    }
    {   u8 *cur = (u8 *)SET71_DATA[0]; s32 ours = cur && (cur == S.own_anims || cur == S.last_anims);
        for (i = 0; i < 4; i++) if (cur && S.orphan[i] == cur) ours = 1;
        if (!ours) for (i = 0; i < 12; i++) S.orig_set[i] = SET71_DATA[i];   /* (after a menu it still holds ours) */
    }
    S.orig_mot2 = MOT2_WORD; MOT2_WORD = MOT2_JOG;
    S.orig_list = SET71_LIST;
    if (S.who) {                              /* the goddess: motion n = Celia's animation n */
        for (i = 0; i < (S.who == WHO_HG ? HG_ANIMS : GD_ANIMS); i++) {
            gd_mot[i][0] = 0x8E000400u | (u32)(i == 12 && S.who != WHO_HG ? 7 : i); gd_mot[i][2] = 0;
            /* word 1 bits 6-10 = cross-fade frames into this motion (31 = the default 10, func_8017DB28).
               Joe's sitting loop (7) starts with no fade: it begins right as he turns 180 degrees, and a
               fade from the sit down's pose under the new facing looked like a second sit down. */
            gd_mot[i][1] = i == 7 && S.who != WHO_HG ? 0x07FBF83Fu : 0x07FBFFFFu;
            gd_mot[i][3] = 0xFFFFFFFFu; gd_mot[i][4] = 0xFFFFFFFFu; gd_mot[i][5] = 0;
            gd_list[i] = gd_mot[i];
        }
        SET71_LIST = gd_list;
    }
    joe_to_a = 1;
    load_animset(ANIMSET, 0);
    S.last_anims = (u8 *)SET71_DATA[0];
    {   /* Our previous model archive can still be in the model entry (restore_names after a menu only puts the names
           back): the load below replaces it without freeing it (+377 KB per menu, 11 copies in a user dump). The
           slot was torn down above, so nothing draws it: free it as soon as the new copy is in. */
        u8 *prev = MODEL37_ARC; s32 i, ours = 0;
        for (i = 0; i < 4; i++) if (prev && S.orphan[i] == prev) { ours = 1; S.orphan[i] = 0; }
        load_model(CHAR_ID);
        if (ours && MODEL37_ARC != prev && *(u32 *)prev == 0x55AA382Du) { op_delete(prev); dup_dbg.freed++; }
        else if (ours) orphan(prev);
    }
    {   u8 *first = MODEL37_ARC;
        slot_setup(slot, CHAR_ID, -1);           /* (this loads the model again: user dumps had two copies, 377 KB each) */
        if (first && first != MODEL37_ARC) {
            if (a_size(first)) { op_delete(first); dup_dbg.freed++; }   /* replaced, nothing draws it: free now */
            else orphan(first);
        }
    }
    joe_to_a = 0;
    S.loaded = 1;
    S.own_model = MODEL37_ARC; S.own_anims = (u8 *)SET71_DATA[0];
    S.sweep = 0;
}

static void joe_expr_patch(s32 on);
static void orphan(u8 *p)
{
    s32 i;
    if ((u32)p < 0x80000000u || (u32)p >= 0x81800000u) return;
    for (i = 0; i < 4; i++) if (S.orphan[i] == p) return;
    for (i = 0; i < 4; i++) if (!S.orphan[i]) { S.orphan[i] = p; return; }
}
/* Our archives left in memory when slot 37 had to be left to the new scene (a talk across a scene change,
   or leaving the valley without the scene hook): each one is about 450 KB (model 377 KB + animations 73 KB)
   and they used to stay for the rest of the session (user dumps: two copies of each with Joe around). Free
   one as soon as neither character 37's model entry nor any animation set points at it. */
/* any word in RAM pointing at p, other than the pools' own block records (0x802FC000-0x80320000) and pm.bin */
struct dupdbg dup_dbg;   /* debug ('DUPS'): sweeps run, duplicates seen, kept (referenced), freed, where the last reference was */
static u32 ref_at;
static s32 referenced(u8 *p)
{   /* Owners only: the game's static character/animation tables (model entries 0x802EB4D4, animation sets
       0x802EA714, actor tables) and our own data. A whole-RAM scan kept every copy (memfix 8/9: 121 of 121
       "referenced"): while it runs, interrupts and callbacks leave the scanned pointer on stacks and in SDK
       data (0x803188B4, 0x80317FB0), and the dumps show nothing else points at the old copies. */
    u32 *w;
    /* An owner (ARC handle) holds the archive start AND its node table (start + 0x20); a word equal to the start
       alone can be the END pointer of the block just below it (memfix 10 dump joe_4: set 10's +0x2C). */
    for (w = (u32 *)0x802E0000; w < (u32 *)0x802F0000; w++) if (*w == (u32)p + 0x20) { ref_at = (u32)w; return 1; }
    return 0;
}
static void free_orphans(void)
{
    s32 i, k, used;
    for (i = 0; i < 4; i++) {
        u8 *p = S.orphan[i];
        if (!p) continue;
        used = MODEL37_ARC == p || p == S.own_model || p == S.own_anims;
        for (k = 0; k < 0x60 && !used; k++) if (*(u8 **)(0x802EA714 + k * 0x30) == p) used = 1;
        if (used) continue;                                   /* still the live one: wait */
        if (!referenced(p) && *(u32 *)p == 0x55AA382Du) op_delete(p);   /* else something else owns it: leave it */
        S.orphan[i] = 0;
    }
}
/* Joe's model archive (377 KB) ends up in memory more than once: twice after setup and once more every time a
   menu (the rucksack) closes - the game reloads character 37's model and keeps only the new copy (user dumps:
   2, then 3 copies; the slowdown and T-pose followed). Once loading has settled, any other pool-B block that is a copy of our live model or
   animation archive (same size, same header) and that nothing in RAM points at is freed. */
static u32 model_size, anims_size;          /* block sizes of our two archives (pool-B records), learnt once */
static u32 block_size(u8 *p)
{
    u8 *r; s32 k;
    if (a_size(p)) return a_size(p);
    for (r = *(u8 **)(0x80315508 + 0x10), k = 0; r && k < 6000; r = *(u8 **)(r + 8), k++)
        if (*(u32 *)(r + 0xC) == 2 && *(u32 *)r - *(u32 *)(r + 4) == (u32)p) return *(u32 *)(r + 4);
    return 0;
}
static void dup_sweep(void)
{
    static u8 *seen[8];                                   /* candidates of the previous sweep */
    u8 *r, *live_m = MODEL37_ARC, *live_a = (u8 *)SET71_DATA[0], *now[8], *p; s32 k, i, n = 0, again;
    dup_dbg.magic = 0x44555053u; dup_dbg.sweeps++;
    if (S.loaded) {                                       /* learn the sizes while ours are the live ones */
        if (!model_size && live_m == S.own_model && live_m) model_size = block_size(live_m);
        if (!anims_size && live_a == S.own_anims && live_a) anims_size = block_size(live_a);
    }
    if (!model_size && !anims_size) return;
    do {                                                  /* restart the record walk after each free */
        again = 0;
        for (r = *(u8 **)(0x80315508 + 0x10), k = 0; r && k < 6000; r = *(u8 **)(r + 8), k++) {
            u32 sz = *(u32 *)(r + 4);
            if (*(u32 *)(r + 0xC) != 2 || (sz != model_size && sz != anims_size)) continue;
            p = (u8 *)(*(u32 *)r - sz);
            if (p == live_m || p == live_a || p == S.own_model || p == S.own_anims || *(u32 *)p != 0x55AA382Du) continue;
            for (i = 0; i < n; i++) if (now[i] == p) break;
            if (i < n) continue;                          /* already handled this sweep */
            dup_dbg.cands++;
            if (referenced(p)) { dup_dbg.refd++; dup_dbg.last_ref = ref_at; continue; }
            for (i = 0; i < 8; i++) if (seen[i] == p) break;
            if (i < 8) { seen[i] = 0; op_delete(p); dup_dbg.freed++; again = 1; break; }   /* orphaned two sweeps running */
            if (n < 8) now[n++] = p;                      /* (a copy just loaded may not be linked in yet) */
        }
    } while (again);
    for (k = 0; k < 8; k++) {                             /* the same for our blocks in pool A */
        p = a_blk[k];
        if (!p || (a_len[k] != model_size && a_len[k] != anims_size)) continue;
        if (p == live_m || p == live_a || p == S.own_model || p == S.own_anims || *(u32 *)p != 0x55AA382Du) continue;
        dup_dbg.cands++;
        if (referenced(p)) { dup_dbg.refd++; dup_dbg.last_ref = ref_at; continue; }
        for (i = 0; i < 8; i++) if (seen[i] == p) break;
        if (i < 8) { seen[i] = 0; op_delete(p); dup_dbg.freed++; continue; }
        if (n < 8) now[n++] = p;
    }
    for (i = 0; i < 8; i++) seen[i] = i < n ? now[i] : 0;
}
static void restore_names(void)
{
    if (S.own_model || S.own_anims) {        /* not freed by release_model: hand them to free_orphans */
        orphan(S.own_model); orphan(S.own_anims); S.own_model = S.own_anims = 0;
    }
    joe_expr_patch(0);                       /* character 37's expression tables back */
    if (S.orig_list) SET71_LIST = S.orig_list;
    MODEL74_NAME = S.orig_model; SET71_NAME = S.orig_anims;
    MODEL74_SIZE[0] = S.orig_size[0]; MODEL74_SIZE[1] = S.orig_size[1]; MODEL74_SIZE[2] = S.orig_size[2];
    S.loaded = 0;
    if (S.guard) { op_delete(S.guard); S.guard = 0; }
}

/* also unloads our animation archive and puts set 71's entry back: the next scene (a house) sets up
   the teddy from set 71 without reloading it, so a left-over pointer to our archive (freed with the
   field's memory, now holding the room's code) crashed in func_8019FECC (dump of pm13) */
static void release_model(void)
{
    u8 *slot = char_slot(CHARMGR, CHAR_ID, 0);
    s32 i;
    if (slot[0xC] && (!S.own_model || MODEL37_ARC == S.own_model)) {   /* still ours (or not known): the game frees it */
        vcall(slot, 0, 2)(slot, 0);
        unload_model(CHAR_ID);
        S.own_model = 0;
    }
    if (!S.own_anims || (u8 *)SET71_DATA[0] == S.own_anims) { unload_animset(ANIMSET); S.own_anims = 0; }
    /* anything not freed above stays in own_* and goes to free_orphans via restore_names */
    for (i = 0; i < 12; i++) SET71_DATA[i] = S.orig_set[i];
    MOT2_WORD = S.orig_mot2;
    SET71_LIST = S.orig_list;
    restore_names();
}

static void spawn(void)
{
    u8 *a, *c, *slot = char_slot(CHARMGR, CHAR_ID, 0);
    /* the actor constructor (0x8007F57C) loads character 37's model whenever its slot is not set up, without
       freeing the copy already in the model entry: after every menu (the rucksack) Joe is made again and one
       more 377 KB copy stayed (9 copies in a user dump). With the slot torn down nothing draws the old copy,
       so free it first and let the constructor's load replace it. */
    u8 *old = !slot[0xC] && MODEL37_ARC && *(u32 *)MODEL37_ARC == 0x55AA382Du ? MODEL37_ARC : 0;
    if (old) { unload_model(CHAR_ID); S.own_model = 0; }   /* (only closes the handle: the memory stays) */
    a = op_new(0x2A8, pm_model, 1);
    if (!a) return;
    joe_to_a = 1; actor_ctor(a, 1, CHAR_ID); joe_to_a = 0;
    if (MODEL37_ARC) S.own_model = MODEL37_ARC;
    dup_dbg.spawns++; if (old) dup_dbg.reloads++;
    if (old && MODEL37_ARC != old) { op_delete(old); dup_dbg.freed++; }   /* the new copy replaced it: free the old one now */
    *(s32 *)(a + 0x64) = VALLEY;            /* map of the actor (read by the collider) */
    actor_add(ACTMGR, a + 0x70, 0xC000 + CHAR_ID);
    S.actor = a; S.talking = 0; S.motion = -1;
    c = op_new(0x40, pm_model, 2);                        /* body collider, as the NPCs have (NPC +0xC0) */
    if (c) {
        col_init(c);
        *(u32 *)(c + 0x10) = COL_VTABLE;
        *(u8 **)(c + 0x34) = a;
        col_config(c, CHAR_ID);
        vcall(c, 0x10, 3)(c, 0);             /* register with the collision map */
    }
    S.col = c;
    actor_show(a);
    if (S.guard) { op_delete(S.guard); S.guard = 0; }   /* placed: give the 256 KB back (the pools were overlapping) */
}

static void despawn(void)
{
    if (S.col) {
        vcall(S.col, 0x10, 4)(S.col, 0);     /* unregister */
        vcall(S.col, 0x10, 2)(S.col, 1);     /* destructor + delete */
        S.col = 0;
    }
    if (S.actor) {
        actor_dtor(S.actor, 0);              /* unlinks it; slot 37 stays loaded (flag +0xF2 = 0) */
        op_delete(S.actor);
        S.actor = 0;
    }
}

/* atan2 in degrees (|error| < 0.3 deg): octant reduction + a 3-term polynomial */
static float atan2_deg(float y, float x)
{
    float ax = x < 0 ? -x : x, ay = y < 0 ? -y : y, a, s, r;
    if (ax < 1e-6f && ay < 1e-6f) return 0;
    a = (ax < ay ? ax : ay) / (ax < ay ? ay : ax);
    s = a * a;
    r = ((-0.0464964749f * s + 0.15931422f) * s - 0.327622764f) * s * a + a;   /* radians, 0..pi/4 */
    if (ay > ax) r = 1.57079637f - r;
    if (x < 0) r = 3.14159274f - r;
    if (y < 0) r = -r;
    return r * 57.2957795f;
}

/* item-get close-up (event 406 uses it after he hands something over). The player turns away from
   the Postman to face the camera, so he is behind the player and can't cover him or the item.
   Counters (x128): 8 = 0 (jog flag), 9 = player facing in degrees, 10-12 eye, 13-15 target,
   16-18 the item's position, 19 = 0 (fade-back flag). */
static void set_get_camera(u8 *g)
{
    s32 *c = (s32 *)(g + 0x12194 + 10 * 4);
    float *p = (float *)(g + 0x29C78), *d = (float *)(g + 0x29F84);
    float fx = p[0] - S.pos.x, fz = p[2] - S.pos.z, l2 = fx * fx + fz * fz, inv;   /* away from him */
    if (l2 < 0.0001f) { fx = d[0]; fz = d[2]; l2 = fx * fx + fz * fz; }
    if (l2 < 0.0001f) { fx = 0; fz = 1; l2 = 1; }
    inv = rsqrt(l2); fx *= inv; fz *= inv;
    c[-2] = 0;
    c[-1] = (s32)(atan2_deg(fx, fz) * 128.0f);
    c[0] = (s32)((p[0] + fx * GET_D) * 128.0f);
    c[1] = (s32)((p[1] + GET_EYE_Y) * 128.0f);
    c[2] = (s32)((p[2] + fz * GET_D) * 128.0f);
    c[3] = (s32)(p[0] * 128.0f);
    c[4] = (s32)((p[1] + GET_AIM_Y) * 128.0f);
    c[5] = (s32)(p[2] * 128.0f);
    c[6] = (s32)((p[0] + fx * GET_ITEM_D) * 128.0f);
    c[7] = (s32)((p[1] + GET_ITEM_Y) * 128.0f);
    c[8] = (s32)((p[2] + fz * GET_ITEM_D) * 128.0f);
    c[9] = 0;                                 /* counter 19 */
}

/* close-up for the talk, framed like the game's own (Common event 35): eye in front of him and
   a little to the side at head height, aimed through his head. Event counters 20-25 (unused by
   every script and only touched by the script VM) carry eye x,y,z and target x,y,z x128; the
   script divides them back and feeds cmd_14 / cmd_15. */
static void set_camera(u8 *g)
{
    s32 *c = (s32 *)(g + 0x12194 + 20 * 4);
    float dx = S.dir.x, dz = S.dir.z, y = S.pos.y;
    c[0] = (s32)((S.pos.x + dx * CAM_D + dz * CAM_SIDE) * 128.0f);
    c[1] = (s32)((y + CAM_EYE_Y) * 128.0f);
    c[2] = (s32)((S.pos.z + dz * CAM_D - dx * CAM_SIDE) * 128.0f);
    c[3] = (s32)((S.pos.x - dx * CAM_BEHIND) * 128.0f);
    c[4] = (s32)((y + CAM_AIM_Y) * 128.0f);
    c[5] = (s32)((S.pos.z - dz * CAM_BEHIND) * 128.0f);
}

/* second hook, at the start of g_system's per-frame update (func_8017755C, was stwu r1,-0x10(r1)):
   a pending scene change (+0x58 != -1) builds the next scene in this same call, and rooms load
   character 37 and animation set 71 themselves (door crash at 0x8019FED8). Doors use their own
   screen effect, not the fader, so this is the only reliable point to unload him first. */


/* ---- Joe's visit (on his days, see joe_visit_day in joetv.c). His place follows the clock, as the
   Postman's: 6:20 in from the east road, round Celia's farm to the dig-site end of the bridge (9:30),
   waits there, crosses and walks down to the bench (12:00), sits until 18:00, then leaves along the
   south road (gone 20:24). Walking speed matches his walk clip (0.0406 units a frame = per 20 clock
   units). At the bench: sit down (clip 6, facing the bench), then the sitting loop (clip 7, turned to
   face away), stand up at 18:00 (clip 8). */
s32 joe_visit_day(u32 day);
#define J_SPD     0.00203f                 /* units per clock unit (tenth of a game second) */
#define J_IN      228370u                  /* 6:20 */
#define J_DIG     (J_IN + (u32)(JR_DIG / J_SPD))
#define J_DIGEND  (J_BENCH - (u32)((JR_BENCH - JR_DIG) / J_SPD))
#define J_BENCH   432000u                  /* 12:00 */
#define J_SIT     (J_BENCH + 59u * 20u)    /* sit down done (59 frames, 20 clock units a frame) */
#define J_UP      648000u                  /* 18:00 */
#define J_GO      (J_UP + 40u * 20u)       /* stand up done */
#define J_GONE    (J_GO + (u32)((JR_LEN - JR_BENCH) / J_SPD))
#define JM_IDLE 0
#define JM_WALK 1
#define JM_SITDOWN 6
#define JM_SIT 7
#define JM_STANDUP 8
#define JM_TALK 9
#define JM_SITTALK 10
#define JM_POCKET 11
#define JM_SIT2 12                         /* sitting loop faded into (from the sitting talk) */
static s32 joe_forced, joe_here, joe_trading, joe_talking;
#define JOE_TALK_EVENT 409                 /* Common.arc node 109: talk while walking (build_joe_talk.py) */
#define HELD_ITEM  (*(volatile unsigned short *)(g + 0x11CC6))
/* Joe's hearts: the name-plate hearts code (v03 main.dol, hook 0x80102598, hearts v7) shows a villager's
   long-term friendship, record +0xF (0..100): <=50 1 grey, 51-60 green, 61-70 blue, 71-80 red, 81-90 2 red,
   91-100 3 red. Joe speaks as character 0x23 (Mukumuku's slot): its record's +0xF follows his $JOE gifts. */
#define villager_rec F(0x8000DC24, u8 *, (u8 *, s32))
static void joe_hearts(u8 *g)
{
    u8 *r = villager_rec(g, 0x23);
    s32 f = 40 + 6 * *(s32 *)(g + 0x12194 + 46 * 4);
    if (r) r[0xF] = (u8)(f > 100 ? 100 : f);
}
/* event counters kept in the save: 45 met, 46 $JOE gifts (10 = full friendship), 47 day of the last gift + 1;
   48 = the line for event 409 */
#define JOE_ITEM   0x442
#define JOE_EVENT  408                     /* Common.arc node 108: the bench trade (build_joe_trade.py) */
#define JCNT(i)    (*(s32 *)(g + 0x12194 + (i) * 4))   /* event counters 41 request, 42 count, 44 held */
#define GOLD       (*(u32 *)(g + 0x11A14 + 4))
#define GOLD_MAX   99999999u
#define item_count F(0x8004FD68, s32, (u8 *, s32))
#define msg_number F(0x80102300, void, (u8 *, s32, s32))
#define MSGMGR     (*(u8 **)0x803491C4)
s32 joe_price_today(void);
#define sfx_play   F(0x8012A52C, s32, (u8 *, s32, s32))
#define SE_CASH    0xCD                    /* the gold-change chime (script cmd_C1 plays it) */
/* first-person talk camera for the trade (the script reads counters 20-25 x128: eye, target; as the
   Postman's): eye on the player's side of Joe at a fixed distance, aimed at his face on the bench */
#define JCAM_D     2.6f                    /* trade camera: eye this far from Joe, toward the player */
#define JCAM_EYE_Y 1.35f                   /*   eye height above the ground (his face is ~0.95 up) */
static void joe_cam(u8 *g, float tx, float tz, float ty)
{
    s32 *c = (s32 *)(g + 0x12194 + 20 * 4);
    float *p = (float *)(g + 0x29C78);
    float dx = p[0] - tx, dz = p[2] - tz, l2 = dx * dx + dz * dz, inv;
    if (l2 < 0.0001f) { dx = 1; dz = 0; l2 = 1; }       /* fallback: in front of the bench (+x) */
    inv = rsqrt(l2);
    c[0] = (s32)((tx + dx * inv * JCAM_D) * 128.0f);    /* from Joe toward the player, a fixed distance */
    c[1] = (s32)((S.pos.y + JCAM_EYE_Y) * 128.0f);
    c[2] = (s32)((tz + dz * inv * JCAM_D) * 128.0f);
    c[3] = (s32)(tx * 128.0f); c[4] = (s32)(ty * 128.0f); c[5] = (s32)(tz * 128.0f);
}
/* the trade event asks through counter 41: 1 buy / 4 sell (count in 42); answer 2 bought, 3 short of gold, 5 sold */
static void joe_trade(u8 *g)
{
    s32 req = JCNT(41), n = JCNT(42);
    u32 p = (u32)joe_price_today(), total;
    if (req >= 128 && !(req & 127)) req >>= 7;
    if (n >= 128 && !(n & 127)) n >>= 7;
    if (MSGMGR) msg_number(MSGMGR, 0, (s32)p);
    if (n < 0) n = 0;
    total = p * (u32)n;
    if (req == 1) {
        if (GOLD < total) JCNT(41) = 3;
        else { GOLD -= total; rucksack_add(g + 0x50, JOE_ITEM, n, -1); JCNT(41) = 2; sfx_play(*(u8 **)0x803491E4, SE_CASH, 0); }
    } else if (req == 4) {
        s32 have = item_count(g + 0x50, JOE_ITEM);
        if (n > have) n = have;
        rucksack_add(g + 0x50, JOE_ITEM, -n, -1);
        total = p * (u32)n;
        GOLD = GOLD + total > GOLD_MAX ? GOLD_MAX : GOLD + total;
        JCNT(41) = 5;
        sfx_play(*(u8 **)0x803491E4, SE_CASH, 0);
    }
}
static void joe_motion(s32 m)               /* start a clip once (sit down / stand up must not restart) */
{
    if (S.motion == m) return;
    S.motion = m;
    actor_motion(S.actor, m);
}

/* ---- The Harvest Goddess's first summoning (gq6; tools/goddess/quest/build_gq_scene.py = event GQ_SCENE_EVENT, the
   shots from the Spring Scene Director's spring_scene.json, GSHOT in gq_scene.h). spring.c sets gq_scene_req when the
   Mermaid Fossil lands with all 15 offerings made. With slot 37 free (no Postman / Joe out), she is loaded as its third
   tenant (WHO_HG), placed 1.8 under Pool B's surface (hidden), facing the player, and the event starts.
   The script sets counter 26 to n when shot n starts and to 32 + n for shot n's after-the-lines action (the sink); we
   set counter 27 to the cue once its timed part is over (GSHOT hold / action frames) and the script waits on that where
   a shot has no lines or a pause. Every frame we move the event camera ourselves: its record (EVMGR + 0x5FC: eye +0,
   look-at pointer +0xC -> own target +0x10, target offset +0x1C, func_80108BEC works out distance / angles) gets the
   shot's eye / target, eased from its start to its end over the shot's glide frames. Placement is the editor's: the
   axis runs from her to the player, yaw turns it, the eye sits dist along it from the subject, height / aim are above
   the water. Music is the script's (vanilla cmd_2F / cmd_32 / cmd_41:
   Marin Jazz on slot 3). Shot fx: a white flash at its start, her eyes closed (frame 2) while it shows. The plead
   clip (the bow) plays once (func_80080294, no loop), then idle. After the sink: fade to white, then (event over)
   bars off and white -> clear. Letterbox bars: zt.c draws gq_lbox (HUD quads). Counter 28 = 1 in year 1. gq_scene_req: 1 asked, 0 done, -1 busy (spring.c tries again on the next toss). */
#define SPK_PAIRS ((u8 *)0x80251A90)                 /* message window: speaker -> name plate pairs (37: 1-36, 38) */
static void gs_plate(s32 on)                         /* gq10: her plate (37) borrows Tartan's (38) last pair while she speaks */
{
    if (SPK_PAIRS[72] != (on ? 38 : 37)) return;
    SPK_PAIRS[72] = SPK_PAIRS[73] = on ? 37 : 38;
}
#define GQ_SHOTS
#include "gq_scene.h"
s32 gq_scene_req;
s32 gq_lbox;                                 /* letterbox bar height (HUD px), zt.c draws it */
s32 gq_slot_busy(void) { return S.actor != 0 && S.who != WHO_HG; }
struct { u32 magic; s32 st, t, at, cue, lastcue, shot, act, waited, camok /* look-at retakes */, bow, eyes, white, face, ground; float surf;
         float eye[3], tgt[3]; } GS;      /* 'GSCN' (dump) */
#define GD_SINK 1.8f
#define GS_CAM       (EVMGR + 0x5FC)
#define cam_update   F(0x80108BEC, void, (u8 *))
#define motion_once  F(0x80080294, void, (u8 *, s32, s32))           /* (actor, clip, loop) - cmd_6D */
static const short GS_CLIP[10] = { 119, 25, 60, 120, 105, 36, 60, 90, 59, 100 };   /* hg_0.anm.arc clip frames (30 / s) */
/* her faces (gq8): {eye, mouth}; eye >= 58 / mouth >= 36 = the game's animated sets (blink / talk), from Muffy's own
   expression table (her frames are Muffy's); static frames: eye 2 closed, 7 half-lidded, 9 happy-closed, 12 blush;
   mouth 4 still */
static const unsigned char GS_FACE[9][2] = {
    { 67, 47 },  /* 0 her own (unused: the table is restored) */
    {  2,  4 },  /* 1 closed */
    { 67, 47 },  /* 2 neutral */
    { 67, 36 },  /* 3 smile */
    {  9, 36 },  /* 4 joy (eyes shut happy) */
    { 61, 45 },  /* 5 pout */
    {  7, 36 },  /* 6 smug (half-lidded) */
    { 12, 36 },  /* 7 blush */
    { 69, 42 },  /* 8 soft */
};
static void gs_face(s32 f);
static void gs_fade(u32 from, u32 to, float secs) { u8 *fd = FADER; if (fd) fade_start(fd, &from, &to, 0, 0, secs); }
static void gs_motion(s32 m)
{
    if (m == 4 || m == 6) { S.motion = m; motion_once(S.actor, m, 0); GS.bow = GS_CLIP[m] * 2 - 6; }   /* explain / plead once */
    else { GS.bow = 0; joe_motion(m); }
}
#define SE_WATER     300
static float smooth(float x) { return x <= 0 ? 0 : x >= 1 ? 1 : x * x * (3 - 2 * x); }
static float gsin(float x)                   /* radians */
{
    float x2;
    while (x > 3.14159274f) x -= 6.28318548f;
    while (x < -3.14159274f) x += 6.28318548f;
    if (x > 1.57079637f) x = 3.14159274f - x; else if (x < -1.57079637f) x = -3.14159274f - x;
    x2 = x * x;
    return x * (1 - x2 / 6 * (1 - x2 / 20 * (1 - x2 / 42 * (1 - x2 / 72))));
}
static void gs_pt(s32 who, float *p, float *o)  /* 0 her, 1 him, 2 between */
{
    if (who == 1) { o[0] = p[0]; o[1] = p[2]; }
    else if (who == 2) { o[0] = (p[0] + S.pos.x) * 0.5f; o[1] = (p[2] + S.pos.z) * 0.5f; }
    else { o[0] = S.pos.x; o[1] = S.pos.z; }
}
static void gs_cam(u8 *g, const struct gshot *sh, float f)
{
    s32 *c = (s32 *)(g + 0x12194 + 20 * 4), i;
    float *p = (float *)(g + 0x29C78), dx = p[0] - S.pos.x, dz = p[2] - S.pos.z, l2 = dx * dx + dz * dz, inv;
    float e = sh->smooth ? smooth(f) : (f < 0 ? 0 : f > 1 ? 1 : f), k[4], a, cs, sn, ux, uz, sp[2], tp[2];
    u8 *cam;
    for (i = 0; i < 4; i++) k[i] = sh->k[i] + (sh->k[4 + i] - sh->k[i]) * e;
    if (l2 < 0.0001f) { dx = 0; dz = 1; l2 = 1; }
    inv = rsqrt(l2); dx *= inv; dz *= inv;                         /* axis: her -> him */
    a = k[0] * 0.0174532924f; sn = gsin(a); cs = gsin(a + 1.57079637f);
    ux = dx * cs - dz * sn; uz = dx * sn + dz * cs;
    gs_pt(sh->subj, p, sp); gs_pt(sh->look, p, tp);
    GS.eye[0] = sp[0] + ux * k[1]; GS.eye[1] = GS.surf + k[2]; GS.eye[2] = sp[1] + uz * k[1];
    GS.tgt[0] = tp[0]; GS.tgt[1] = GS.surf + k[3]; GS.tgt[2] = tp[1];
    {   /* gq10 (dump ceb0de6f, A8): the grass rim round the pool stands above the water and hid both of them from
           low eyes outside it. Sample the ground along eye -> target and lift the eye until the line clears it. */
        Vec v; float gy, up = 0, f, need;
        s32 j;
        for (j = 0; j <= 7; j++) {
            f = (float)j * 0.125f;
            v.x = GS.eye[0] + (GS.tgt[0] - GS.eye[0]) * f; v.z = GS.eye[2] + (GS.tgt[2] - GS.eye[2]) * f;
            v.y = (GS.eye[1] > GS.tgt[1] ? GS.eye[1] : GS.tgt[1]) + 6.0f;
            gy = ground_y(COLLMAP, &v);
            if (gy != gy || gy > v.y - 0.01f) continue;
            need = gy + (j ? 0.25f : 0.6f) - (GS.eye[1] + (GS.tgt[1] - GS.eye[1]) * f);
            if (need > 0) { need /= 1.0f - f; if (need > up) up = need; }
        }
        if (up > 3.0f) up = 3.0f;
        if (up > 0) { GS.eye[1] += up; GS.ground++; }
    }
    for (i = 0; i < 3; i++) { c[i] = (s32)(GS.eye[i] * 128.0f); c[3 + i] = (s32)(GS.tgt[i] * 128.0f); }
    cam = EVMGR ? GS_CAM : 0;
    if (!cam || GS.t + GS.shot == 0) return;                   /* (the script's cmd_14 / 15 have not run yet) */
    if (*(u32 *)(cam + 0xC) != (u32)(cam + 0x10)) {            /* gq9: something re-pointed the look-at (the 3 odd shots?): */
        *(u32 *)(cam + 0xC) = (u32)(cam + 0x10); GS.camok++;   /* take it back, and count it */
    }
    for (i = 0; i < 3; i++) { ((float *)cam)[i] = GS.eye[i]; ((float *)(cam + 0x10))[i] = GS.tgt[i]; ((float *)(cam + 0x1C))[i] = 0; }
    cam_update(cam);
}
static s32 gs_get(u8 *g, s32 i) { s32 v = *(s32 *)(g + 0x12194 + i * 4); if (v >= 128 && !(v & 127)) v >>= 7; return v; }
static s32 gd_frame(u8 *g, s32 map, u32 t)
{
    s32 *cn = (s32 *)(g + 0x12194);
    u8 *au = *(u8 **)0x803491E4;
    GS.magic = 0x4753434Eu;
    if (!GS.st) {
        Vec v;
        float *p = (float *)(g + 0x29C78);
        if (gq_scene_req != 1) return 0;
        if (map != VALLEY || !no_event()) return 0;            /* (after the toss's own state has ended) */
        if (S.actor) { gq_scene_req = -1; return 0; }          /* the Postman / Joe is out: not now */
        if (S.loaded) release_model();
        S.who = WHO_HG;
        setup_model();
        spawn();
        if (!S.actor) { release_model(); S.who = 0; gq_scene_req = -1; return 0; }
        v.x = GD_X; v.y = 40.0f; v.z = GD_Z; GS.surf = ground_y(COLLMAP, &v);
        if (GS.surf != GS.surf || GS.surf < p[1] - 3.0f || GS.surf > p[1] + 1.0f) GS.surf = p[1] - 0.4f;
        S.pos.x = GD_X; S.pos.z = GD_Z; S.pos.y = GS.surf - GD_SINK;
        {   float dx = p[0] - GD_X, dz = p[2] - GD_Z, l2 = dx * dx + dz * dz, inv = l2 > 0.0001f ? rsqrt(l2) : 0;
            S.dir.x = dx * inv; S.dir.y = 0; S.dir.z = l2 > 0.0001f ? dz * inv : 1;
            {   float *pd = (float *)(g + 0x29F84); pd[0] = -S.dir.x; pd[1] = 0; pd[2] = -S.dir.z; }   /* he faces her */
        }
        actor_setpos(S.actor, &S.pos); actor_setdir(S.actor, &S.dir); actor_hide(S.actor);
        joe_motion(0);
        cn[GQ_C_CUE] = 0; cn[GQ_C_DONE] = 0; cn[GQ_C_FACE] = 0;
        cn[GQ_C_YEAR1] = t / (T_DAY * 40u) == 0;                /* 4 seasons x 10 days */
        gs_cam(g, &GSHOT[0], 0);
        GS.st = 1; GS.t = 0; GS.at = -1; GS.cue = 0; GS.lastcue = 0; GS.shot = 0; GS.act = -1; GS.waited = 0;
        GS.bow = 0; GS.eyes = 0; GS.white = 0; GS.face = -1; GS.ground = 0;
        /* gq9: her own face (the user found the gq8 set overdone); only lines the JSON names get another */
        gq_scene_req = 0;
        gs_plate(1);
        event_start(EVMGR, GQ_SCENE_EVENT, 0, 0);
        return 1;
    }
    if (GS.st == 1) {                                           /* the event is running */
        const struct gshot *sh;
        if (no_event()) { if (++GS.waited > 30 && GS.t > 30) GS.st = 2; }   /* (it starts a frame or more later) */
        else GS.waited = 0;
        if (!S.actor) { GS.st = 2; return 1; }
        if (GS_LETTERBOX && gq_lbox < 36) gq_lbox += 2;
        GS.cue = gs_get(g, GQ_C_CUE);
        if (GS.cue != GS.lastcue && GS.cue > 0) {
            s32 n = GS.cue >= 32 ? GS.cue - 32 : GS.cue;
            if (n >= 1 && n <= GS_N) {
                sh = &GSHOT[n - 1];
                if (GS.cue < 32) {                              /* shot n starts */
                    GS.shot = n - 1; GS.t = 0;
                    gs_motion(sh->motion);
                    if (sh->fx & 4) gs_face(1);                         /* eyes closed (the rise) */
                    if (sh->fx & 2) gs_fade(0xFFFFFFFFu, 0xFFFFFF00u, 1.2f);      /* white flash */
                    if (sh->act == 0) { S.pos.y = GS.surf - GD_SINK; actor_hide(S.actor); GS.act = -1; }
                    else if (sh->act == 1) { if (S.pos.y < GS.surf) S.pos.y = GS.surf; actor_show(S.actor); GS.act = -1; }
                    else if (!sh->after) { GS.act = sh->act; GS.at = 0; }
                } else { GS.act = sh->act; GS.at = 0; }          /* the after-the-lines action */
                if (GS.act >= 2) {
                    actor_show(S.actor);
                    if (sh->fx & 1) sfx_play(au, SE_WATER, 0);
                }
            }
            GS.lastcue = GS.cue;
        }
        {   s32 f = gs_get(g, GQ_C_FACE);                       /* the script's face for this line */
            if (f > 0 && f <= 9 && f != GS.eyes) { GS.eyes = f; gs_face(f); }
        }
        sh = &GSHOT[GS.shot];
        if (GS.act >= 2 && GS.at >= 0) {                       /* rising / sinking */
            float k = smooth((float)GS.at / (float)(sh->actf > 0 ? sh->actf : 1));
            S.pos.y = GS.surf - GD_SINK * (GS.act == 2 ? 1.0f - k : k);
            if (GS.at >= sh->actf) {
                if (GS.act == 3) {
                    actor_hide(S.actor);
                    if (GS_END_WHITE && GS.cue >= 32) { gs_fade(0xFFFFFF00u, 0xFFFFFFFFu, 0.6f); GS.white = 1; }   /* gq9: after the sink */
                }
                GS.act = -1;
                if (GS.cue >= 32 && !GS.white) cn[GQ_C_DONE] = GS.cue;
            } else GS.at++;
        }
        if (GS.white && ++GS.white > 36) cn[GQ_C_DONE] = GS.cue;   /* fully white: the script ends at once (gq8: the white
                                                                    cleared before the end and showed the sink again) */
        if (GS.bow && --GS.bow == 0) joe_motion(0);                      /* one bow, then idle */
        if (GS.cue > 0 && GS.cue < 32 && GS.t >= sh->hold && (GS.act < 2 || sh->after)) cn[GQ_C_DONE] = GS.cue;
        actor_setpos(S.actor, &S.pos); actor_setdir(S.actor, &S.dir);
        gs_cam(g, sh, sh->glide > 0 ? (float)GS.t / (float)sh->glide : 1.0f);
        GS.t++;
        return 1;
    }
    if (no_event()) {                                           /* over: give slot 37 back, the music too */
        if (S.actor) despawn();
        if (S.loaded) release_model();
        S.who = 0; GS.st = 0;
        GS.eyes = 0; joe_expr_patch(0); gs_plate(0);
        gq_lbox = 0;
        GS.white = 0;                                           /* (the event's end clears the white itself: gq7 flashed twice) */
        return 0;
    }
    return 1;
}
static void joe_place(float s)
{
    s32 i = 0;
    float len, t, dx, dz;
    while (i < JR_N - 2 && s > jr_seg[i]) { s -= jr_seg[i]; i++; }
    len = jr_seg[i]; t = s < 0 ? 0 : s > len ? 1 : s / len;
    dx = jr_pt[i + 1][0] - jr_pt[i][0]; dz = jr_pt[i + 1][1] - jr_pt[i][1];
    S.pos.x = jr_pt[i][0] + dx * t; S.pos.z = jr_pt[i][1] + dz * t;
    S.dir.x = dx / len; S.dir.y = 0; S.dir.z = dz / len;
}
/* ---- Joe's face and talking. His character slot's face (slot +0x124, func_8002F3E8's object): +0 eye,
   +4 mouth; a value >= 58 (eye) / 36 (mouth) plays animation (value - 58 / - 36) of char_com_eye.tam /
   char_com_mouth.tam (pointers 0x803490F0 / F4) into the players at +0x14 / +0x24, else it is a still frame.
   Those common animations match Joe's frame numbering: eye 9 = blink 0-2, 3 = angry blink 6-8, 11 = sad
   blink 18-20; mouth 11 = flaps 0/1, 9 = angry 7/8, 0 = smile 4/5, 6 = sad 9/10.
   The events set counter 49 = line + 1 (joe_lines.h) right before each line; pm.c follows the typing (letters
   per page x JT_FRAMES; A finishes a page early or turns it) to flap the mouth and play the talk gesture. */
#include "joe_lines.h"
#define tam_play   F(0x8017E11C, void, (u8 *, void *, s32, s32))
#define JT_FRAMES  2                       /* frames per letter (the message window's typing speed) */
#define JC_LINE    49                      /* counter: the line being said (+1) */
#define JC_POCKET  50                      /* counter: the gift event asks for the take-and-pocket (1 -> pm.c 0) */
#define JT_POCKET  90                      /* frames of the pocket clip (it holds after) */
static const unsigned char joe_faces[4][3] = {    /* eye, mouth still, mouth talking */
    { 58 + 9, 0, 36 + 11 },                /* neutral */
    { 58 + 3, 7, 36 + 9 },                 /* angry */
    { 58 + 9, 4, 36 + 0 },                 /* happy: smile */
    { 58 + 11, 9, 36 + 6 },                /* sad */
};
static struct { s32 line, page, timer, face, pocket; } jt;
static s32 jcnt(u8 *g, s32 i)
{
    s32 v = *(s32 *)(g + 0x12194 + i * 4);
    if (v >= 128 && !(v & 127)) v >>= 7;   /* script numbers come x128 */
    return v;
}
/* The game picks a face through the character's expression table (func_8002F748: 0x8029F818 + 0x18 x
   character + 4 x season -> (eye, mouth) pairs, func_8002F3E8 applies one; the game calls it itself, e.g.
   in events). Writing the face directly fought those calls, so character 37's six table pointers now point
   at Joe's table while he is loaded (restored after), every expression in it = the face we want. */
#define EXPR_TABS  ((u32 **)0x8029F818)
#define face_set   F(0x8002F3E8, void, (u8 *, s32))
static u32 joe_expr[11][2];
static u32 *orig_expr[6];
static s32 expr_patched;
static void joe_expr_patch(s32 on)
{
    s32 k;
    if (on == expr_patched) return;
    for (k = 0; k < 6; k++) {
        if (on) { orig_expr[k] = EXPR_TABS[CHAR_ID * 6 + k]; EXPR_TABS[CHAR_ID * 6 + k] = &joe_expr[0][0]; }
        else EXPR_TABS[CHAR_ID * 6 + k] = orig_expr[k];
    }
    expr_patched = on;
}
static void joe_face(s32 eye, s32 mouth)
{
    u8 *slot;
    s32 k;
    if (!S.actor) return;
    slot = *(u8 **)(S.actor + 0xD4);
    if ((u32)slot < 0x80000000u || (u32)slot >= 0x81800000u) return;
    joe_expr_patch(1);
    for (k = 0; k < 11; k++) { joe_expr[k][0] = (u32)eye; joe_expr[k][1] = (u32)mouth; }
    face_set(slot + 0x124, 0);             /* applies only what changed (restarts the blink / flap there) */
}
/* the goddess's face (gq8): the slot's expression table patched as Joe's, every entry = the face (GS_FACE) */
static void gs_face(s32 f)
{
    u8 *slot;
    if (f == 9) {                                         /* her own table back */
        joe_expr_patch(0);
        if (!S.actor) return;
        slot = *(u8 **)(S.actor + 0xD4);
        if ((u32)slot >= 0x80000000u && (u32)slot < 0x81800000u) face_set(slot + 0x124, 0);
        return;
    }
    if (f < 1 || f > 8) return;
    joe_face(GS_FACE[f][0], GS_FACE[f][1]);
}
/* every frame Joe is out; in_event: our talk (1) or trade (2) event is running */
static void joe_talk_frame(u8 *g, s32 in_event)
{
    s32 line = in_event ? jcnt(g, JC_LINE) : 0, talking;
    if (line != jt.line) {                 /* a new line: page 1 starts typing */
        jt.line = line; jt.page = 0; jt.timer = 0;
        if (line > 0 && line <= JL_N) { jt.face = joe_lines[line - 1].face; jt.timer = joe_lines[line - 1].len[0] * JT_FRAMES; }
        else if (!line) jt.face = 0;
    }
    if (line > 0 && line <= JL_N && (PAD_PRESS & 0x100)) {
        if (jt.timer > 0) jt.timer = 0;    /* A: the page shows at once */
        else if (jt.page + 1 < joe_lines[line - 1].pages) { jt.page++; jt.timer = joe_lines[line - 1].len[jt.page] * JT_FRAMES; }
    }
    if (jt.timer > 0) jt.timer--;
    talking = jt.timer > 0;
    if (in_event == 1 && jcnt(g, JC_POCKET) == 1 && !jt.pocket) jt.pocket = JT_POCKET;
    if (jt.pocket) {
        joe_motion(JM_POCKET);
        if (!--jt.pocket) *(s32 *)(g + 0x12194 + JC_POCKET * 4) = 0;
    } else if (in_event == 1) joe_motion(talking ? JM_TALK : JM_IDLE);
    else if (in_event == 2) joe_motion(talking ? JM_SITTALK : JM_SIT2);
    joe_face(joe_faces[jt.face][0], joe_faces[jt.face][talking ? 2 : 1]);
}
static s32 joe_frame(u8 *g, s32 map, u32 t)
{
    u32 tod = t % T_DAY;
    s32 m;
    float y0;
    if (joe_forced && joe_forced != (s32)(t / T_DAY) + 1) joe_forced = 0;
    joe_here = 0;
    if ((!joe_forced && !joe_visit_day(t / T_DAY)) || tod < J_IN || tod >= J_GONE) {
        if (S.who == 2 && no_event()) { if (S.actor) despawn(); if (S.loaded) release_model(); S.who = 0; }
        return 0;
    }
    if (map != VALLEY) {
        if (S.actor && !S.talking) despawn();
        if (S.loaded && !S.actor) restore_names();
        return 1;
    }
    if (joe_talking) {                        /* talking while walking: he waits, then carries on */
        if (no_event()) { joe_talking = 0; JCNT(JC_LINE) = 0; JCNT(JC_POCKET) = 0; jt.pocket = 0; }
        else { joe_talk_frame(g, 1); return 1; }
    }
    if (joe_trading) {                        /* our trade event: settle its requests */
        if (no_event()) { joe_trading = 0; JCNT(41) = 0; JCNT(JC_LINE) = 0; }
        else { joe_trade(g); joe_talk_frame(g, 2); return 1; }
    }
    if (!no_event()) return 1;
    if (S.loaded && S.who != 2) { if (S.actor) despawn(); release_model(); }
    if (!S.actor) {
        S.who = 2;
        if (!S.loaded) setup_model();
        spawn();
        if (!S.actor) return 1;
        S.pos.y = 60.0f;                      /* first fix: drop onto the ground from above */
    }
    y0 = S.pos.y;
    if (tod < J_DIG) { joe_place((float)(tod - J_IN) * J_SPD); m = JM_WALK; }
    else if (tod < J_DIGEND) { joe_place(JR_DIG); S.dir.x = 1; S.dir.z = 0; m = JM_IDLE; }      /* looks over the dig site */
    else if (tod < J_BENCH) { joe_place(JR_DIG + (float)(tod - J_DIGEND) * J_SPD); m = JM_WALK; }
    else if (tod < J_GO) {
        joe_place(JR_BENCH); S.dir.z = 0;
        if (tod < J_SIT) { S.dir.x = -1; m = JM_SITDOWN; }                                    /* faces the bench */
        else { S.dir.x = 1; m = tod < J_UP ? JM_SIT : JM_STANDUP; }                           /* turned: faces away */
        joe_here = tod >= J_SIT && tod < J_UP;
    } else { joe_place(JR_BENCH + (float)(tod - J_GO) * J_SPD); m = JM_WALK; }
    S.pos.y = y0 + 3.0f;
    S.pos.y = ground_y(COLLMAP, &S.pos);
    actor_setpos(S.actor, &S.pos);
    actor_setdir(S.actor, &S.dir);
    if (m == JM_SIT && (S.motion == JM_SIT2 || S.motion == JM_SITTALK)) m = JM_SIT2;
    joe_motion(m);
    joe_talk_frame(g, 0);                     /* blinking, neutral face */
    /* A next to Joe on the bench (player free, facing him): the trade */
    if (joe_here && (PAD_PRESS & 0x100) && !(PAD_HELD & 0x10) && CONTROL == 1 && !(FADER && *(u8 *)(FADER + 0x60))) {
        float *p = (float *)(g + 0x29C78), *d = (float *)(g + 0x29F84);
        float dx = (BENCH_X - 0.3f) - p[0], dz = BENCH_Z - p[2], d2 = dx * dx + dz * dz;
        if (d2 < 2.2f * 2.2f && d2 > 0.0001f && (dx * d[0] + dz * d[2]) * rsqrt(d2) > 0.3f) {
            PAD_PRESS &= ~0x100u; PAD_HELD &= ~0x100u;
            JCNT(41) = 0; JCNT(42) = 0; JCNT(44) = item_count(g + 0x50, JOE_ITEM);
            if (MSGMGR) msg_number(MSGMGR, 0, joe_price_today());
            joe_trading = 1;
            joe_hearts(g);
            joe_cam(g, BENCH_X, BENCH_Z, S.pos.y + 0.95f);
            event_start(EVMGR, JOE_EVENT, 0, 0);
        }
    }
    /* A next to Joe while he walks or waits at the dig site: a line, or a $JOE gift (secret: never hinted at) */
    else if (!joe_here && (tod < J_BENCH || tod >= J_GO) && (PAD_PRESS & 0x100) && !(PAD_HELD & 0x10) && CONTROL == 1
             && !(FADER && *(u8 *)(FADER + 0x60))) {
        float *p = (float *)(g + 0x29C78), *d = (float *)(g + 0x29F84);
        float dx = S.pos.x - p[0], dz = S.pos.z - p[2], d2 = dx * dx + dz * dz;
        if (d2 < 2.0f * 2.0f && d2 > 0.0001f && (dx * d[0] + dz * d[2]) * rsqrt(d2) > 0.3f) {
            s32 kind, day1 = (s32)(t / T_DAY) + 1, season = (s32)(t / T_DAY / 10) % 4;
            float inv = rsqrt(d2);
            PAD_PRESS &= ~0x100u; PAD_HELD &= ~0x100u;
            if (HELD_ITEM == JOE_ITEM) {
                if (JCNT(47) == day1) kind = 7;
                else { JCNT(47) = day1; if (JCNT(46) < 10) JCNT(46)++; kind = 5; }   /* counted quietly (10 = full friendship) */
            } else if (!JCNT(45)) { JCNT(45) = 1; kind = 1; }
            else if (season == 2) kind = 4;
            else if (tod >= J_DIG && tod < J_DIGEND) kind = 3;
            else kind = 2;
            JCNT(48) = kind;
            S.dir.x = -dx * inv; S.dir.y = 0; S.dir.z = -dz * inv;   /* turns to the player */
            actor_setdir(S.actor, &S.dir);
            joe_motion(JM_IDLE);
            joe_cam(g, S.pos.x, S.pos.z, S.pos.y + 1.1f);
            joe_hearts(g);
            joe_talking = 1;
            event_start(EVMGR, JOE_TALK_EVENT, 0, 0);
        }
    }
    return 1;
}

void logs_release(void);
void logs_frame(u8 *g, s32 map, u32 pad_held, u32 pad_press);
void skill_frame(u8 *g, u32 pad_held, u32 pad_press);
void spring_release(void);
void spring_frame(u8 *g, s32 map, u32 pad_held, u32 pad_press);
void joe_dig_frame(void);
void joe_seed_frame(void);


/* debug for RAM dumps (magic 'MEMG'): the gap between the per-frame pool A (0x802FD4D0, grows up from the arena
   start: mainchapter + scratch) and the general pool B (0x80315508, operator new, fills down from the top; its
   records hold the block's top address). When the gap goes negative they overlap: random corruption (findings
   7.43). Measured every 32 frames: now, the lowest seen, and when. */
struct { u32 magic, n; s32 gap, gap_min; u32 a_top, b_low, clock_min, b_used_kb; } mem_g;
static void mem_gauge(void)
{
    u8 *r; s32 k; u32 atop = 0, blow = 0xFFFFFFFFu, used = 0;
    if (mem_g.n++ & 3) return;                /* every 4 frames (every 32 missed a building's load block) */
    for (r = *(u8 **)(0x802FD4D0 + 0x10), k = 0; r && k < 300; r = *(u8 **)(r + 8), k++)
        if (*(u32 *)(r + 0xC) == 2 && *(u32 *)r + *(u32 *)(r + 4) > atop) atop = *(u32 *)r + *(u32 *)(r + 4);
    for (r = *(u8 **)(0x80315508 + 0x10), k = 0; r && k < 6000; r = *(u8 **)(r + 8), k++)
        if (*(u32 *)(r + 0xC) == 2) { u32 lo = *(u32 *)r - *(u32 *)(r + 4); used += *(u32 *)(r + 4); if (lo < blow) blow = lo; }
    mem_g.magic = 0x4D454D47u; mem_g.a_top = atop; mem_g.b_low = blow; mem_g.b_used_kb = used >> 10;
    mg.b_low = blow;                          /* the pool guard's cached B bottom, exact again */
    mem_g.gap = (s32)(blow - atop);
    if (mem_g.n <= 5 || mem_g.gap < mem_g.gap_min) { mem_g.gap_min = mem_g.gap; mem_g.clock_min = CLOCK; }
}
/* Scene change (a menu counts too): Joe's actor is gone, so free his archives now, before the next scene loads.
   The game's unload only closes the handles: character 37's model entry and animation set 71 kept pointing at
   our archives, so free_orphans waited for ever and 230 KB of Joe (model 152 KB + animations 73 KB) stayed at
   the bottom of the general pool in every building, right where a building's load puts its 239 KB pool-A block
   (memfix 16 dumps d1239f81 / cb8aea64: the inn's block overwrote Joe's model; orphans = model + anims, both
   still in entry 37 +0 / set 71 +0). Entry 37 goes back to an unused character's state (all zero but the
   handle's vtable word at +0x20), set 71 to what it held before Joe. */
static void joe_free_now(void)
{
    u8 *list[6]; s32 i, k;
    list[0] = S.own_model; list[1] = S.own_anims;
    for (i = 0; i < 4; i++) list[2 + i] = S.orphan[i];
    for (i = 0; i < 6; i++) {
        u8 *p = list[i];
        if (!p) continue;
        if (MODEL37_ARC == p) {
            u32 *e = (u32 *)(0x802EB4D4 + CHAR_ID * 0x44);
            for (k = 0; k < 17; k++) if (k != 8) e[k] = 0;
        }
        if ((u8 *)SET71_DATA[0] == p) {
            for (k = 0; k < 12; k++) SET71_DATA[k] = S.orig_set[k];
            for (k = 0; k < 6; k++) if (list[k] && (u8 *)SET71_DATA[0] == list[k]) SET71_DATA[0] = 0;   /* (never ours) */
        }
        if (block_size(p)) { op_delete(p); dup_dbg.freed++; }
        for (k = i + 1; k < 6; k++) if (list[k] == p) list[k] = 0;
    }
    S.own_model = S.own_anims = 0;
    for (i = 0; i < 4; i++) S.orphan[i] = 0;
}
void pm_scene_change(void)
{
    logs_release();
    spring_release();
    if (S.talking) {                         /* the talk keeps him, but the next scene must not load our files as 37 */
        if (S.loaded) { MODEL74_NAME = S.orig_model; SET71_NAME = S.orig_anims; }
        return;
    }
    if (S.actor) despawn();
    if (S.loaded) release_model();
    joe_free_now();
}

void zt_frame(u8 *g, s32 map, volatile u32 *held, volatile u32 *press);
/* Z targeting (zt.c): Joe's position while he is out (who 2 = Joe) */
s32 pm_joe_pos(float *p)
{
    if (S.who != 2 || !S.actor) return 0;
    p[0] = S.pos.x; p[1] = S.pos.y; p[2] = S.pos.z;
    return 1;
}
void pm_frame(void)
{
    u8 *g = GAME;
    u32 t, tod;
    s32 day, map, mode, active;
    float s;

    if ((u32)g < 0x80000000u || (u32)g >= 0x81800000u || !*(u32 **)0x80349218) return;
    mg_frames++;
#ifdef GUARD_TEST
    if (mg_frames == 600) {                   /* guard test: 10 s in, ask pool A for a block reaching 64 KB into B's
                                                 lowest block, release it at once (pool records live apart from the
                                                 memory, nothing is written there): the guard must say 0x0BAD00A0 */
        u32 at = pool_a_top(), lo = pool_b_low();
        if (lo > at) { u8 *t = allocA(lo - at + 0x10000, pm_model, 9); if (t) freeA(t); }
    }
#endif
    joe_seed_frame();                         /* joetv.c: the save's own $JOE market seed (first day of a new game) */
    free_orphans();                           /* our archives a scene change left behind */
    if (++S.sweep >= 60) { S.sweep = 0; dup_sweep(); }   /* every second: the game reloads 37's model after menus */
    mem_gauge();                              /* debug: the gap between the two memory pools */
    t = CLOCK;
    day = (t / T_DAY) % 10;
    tod = t % T_DAY;
    map = *(s32 *)(g + 0x2A290);              /* the player's current map */
    if (!*(u8 **)0x80349208 || *(s32 *)(*(u8 **)0x80349208 + 0x68) != map) map = -1;  /* g_system: in the field */
    zt_frame(g, map, &PAD_HELD, &PAD_PRESS);  /* Z targeting (zt.c): takes Z before anything else reads it */
    logs_frame(g, map, PAD_HELD, PAD_PRESS);  /* choppable logs (logs.c) */
    skill_frame(g, PAD_HELD, PAD_PRESS);      /* tool skill on the HUD (skill.c) */
    spring_frame(g, map, PAD_HELD, PAD_PRESS);  /* offerings at the goddess pond (spring.c) */
    joe_dig_frame();                          /* $JOE coin dig-site halving (joetv.c) */
    /* Bench by the tree (valley): A within 1.6 of the seat, facing it, no event running -> event 407
       ("Sit until the evening?" / "Sit until the morning?", Common.arc entry 107, debug.mes 9/10).
       The player's own map (game+0x2A290) is used, not the field check: after the event the latter can differ. */
    if (bench_cool) bench_cool--;
    if (bench_wait && --bench_wait < 540 && map == 1 && FADER && *(u8 *)(FADER + 0x60) != 1) {
        bench_wait = 0;                       /* the valley is back and nothing is fading: if the last fade ended on black */
        if (*(u8 *)(FADER + 0x53) == 0xFF) {  /* (to colour +0x50, alpha +0x53), fade in ourselves */
            u32 from = 0x000000FF, to = 0x00000000; fade_start(FADER, &from, &to, 0, 0, 0.5f);
        }
    }
    if ((PAD_PRESS & 0x100) && !(PAD_HELD & 0x10) && *(s32 *)(g + 0x2A290) == 1 && !S.talking && !joe_here
        && !bench_target && !bench_cool && !*(s32 *)(g + 0x12194 + BENCH_CNT * 4)
        && !(FADER && *(u8 *)(FADER + 0x60))) {   /* not during a skip, a pending request, a fade, or just after */
        float *p = (float *)(g + 0x29C78), *d = (float *)(g + 0x29F84);
        float dx = BENCH_X - p[0], dz = BENCH_Z - p[2], d2 = dx * dx + dz * dz;
        if (d2 < 1.6f * 1.6f && d2 > 0.0001f && (dx * d[0] + dz * d[2]) * rsqrt(d2) > 0.5f) {
            u8 *ev = EVMGR;
            if (ev && *(s32 *)(ev + 0x680) == -1 && !*(s32 *)(ev + 0x58C) && CONTROL == 1) {   /* free: not in the X menu (CONTROL 0) */
                PAD_PRESS &= ~0x100u; PAD_HELD &= ~0x100u;   /* the player does not act on this A */
                event_start(ev, BENCH_EVENT, 0, 0);
            }
        }
    }
    /* Yes on the bench: the script sets counter 27 (1 = until 18:00, 2 = until 6:00), fades to black and ends.
       Then the clock steps 5 game minutes a frame (like the bed's time skip, so timed jobs such as the
       12:00-12:30 shipping pickup still see their window), pad input held off; at the target: rest
       (stamina full, sleepiness cleared) and fade back in. */
    {
        s32 *req = (s32 *)(g + 0x12194 + BENCH_CNT * 4);
        u8 *ev = EVMGR;
        s32 want = *req == 7771 * 128 || *req == 7771 ? 1 : *req == 7772 * 128 || *req == 7772 ? 2 : 0;
        if (want && !bench_target && ev && *(s32 *)(ev + 0x680) == -1) {
            u32 c = CLOCK, base = c / T_DAY * T_DAY, h = c % T_DAY;
            if (want == 1) bench_target = base + 18 * 36000u;
            else bench_target = h < 6 * 36000u ? base + 6 * 36000u : base + T_DAY + 6 * 36000u;
            if (bench_target <= c) bench_target = c + 1;
            bench_start = c;
            *req = 0;
        }
        if (bench_target) {
            u32 *clk = *(u32 **)0x80349218, old = *clk, step;
            u8 *tm = *(u8 **)0x80349194;
            PAD_PRESS = 0; PAD_HELD = 0;
            {   /* battle9: run the game's own time skip, minute by minute (the event skip lbl_80109E44: per minute the
                   world updates func_8017CD7C / CDC0 / CE04 (lbl_8034923C, flags func_80012568() | 0x400), +0x74
                   func_8017CFD4, +0x48 func_8017CF2C, clock + 1 minute, func_80015760(lbl_803491D4, flags)); that moves
                   every villager through its schedule (writing the clock only left them where they stood). 60 minutes a
                   frame, 1 a frame through the farm's windows 4:58-5:45 (Takakura's plan, pickup 5:10-5:40) and
                   11:58-12:35 (payout 12:00-12:30), with our farm-side extras every minute. */
                u8 *ck = *(u8 **)0x80349218, *w = *(u8 **)0x8034923C, ctl = ck[8];
                u32 tod = old % T_DAY, n, k;
                n = ((tod >= 178800u && tod < 207000u) || (tod >= 430800u && tod < 453000u)) ? 1 : 60;
                if (old % 600u) { clk_align(ck); n--; }        /* onto a whole minute first (counts as one) */
                ck[8] = 1;                                     /* as the game's skip */
                if (FADER && *(u8 *)(FADER + 0x53) != 0xFF) {  /* keep the screen black through the skip (user: the sky
                                                                  showed, changing at a few frames a second) */
                    u32 bk = 0x000000FF; fade_start(FADER, &bk, &bk, 0, 0, 0.0f);
                }
                for (k = 0; k < n && *clk < bench_target; k++) {
                    u32 f = tsk_flags() | 0x400u;
                    w_upd1(w, f); w_upd2(w, f); w_upd3(w, f); w_upd4(w + 0x74); w_upd5(w + 0x48);
                    clk_add(ck, 1);
                    tsk_after(*(u8 **)0x803491D4, f);
                    bench_minutes++;
                    {   /* Takakura (villager 7) plans the day's trade jobs (pickup 5:10, payout 12:00) when he wakes at
                           ~5:00, but not while the player is off the farm: once per day of the skip, at 5:00+, his daily
                           plan (func_80060EF8 only reads state+8 = the villager object; NPC manager *0x8034916C +4 per id) */
                        u32 now = *clk, d = now / T_DAY, td = now % T_DAY;
                        u8 *npc = *(u8 **)0x8034916C, *tk;
                        if (td >= 180000u && td < 186000u && d != bench_taka_day && (u32)npc >= 0x80000000u && (u32)npc < 0x81800000u) {
                            tk = *(u8 **)(npc + 4 * 7);
                            bench_taka_day = d;
                            if ((u32)tk >= 0x80000000u && (u32)tk < 0x81800000u && *(s32 *)(tk + 0xBC) == 7) {
                                u8 *st[3]; st[0] = 0; st[1] = 0; st[2] = tk;
                                day_plan((u8 *)st);
                            }
                        }
                    }
                    ship_check(*(u8 **)0x803491CC);          /* farm-side timed checks (pickup 5:10-5:40, payout 12:00-12:30): only wlp2 calls it */
                    {   /* the trade manager (*0x803491EC, vtable 0x802C1940 at +0x10): its update runs the day's timed trade
                           jobs and queues the next day's; it only runs on the farm */
                        u8 *tr = *(u8 **)0x803491EC;
                        if ((u32)tr >= 0x80000000u && (u32)tr < 0x81800000u && *(u32 *)(tr + 0x10) == 0x802C1940u) trade_update(tr, 0);
                    }
                }
                ck[8] = ctl;
                (void)step;
            }
            if ((u32)tm >= 0x80000000u && (u32)tm < 0x81800000u && *(u32 *)(tm + 0x404) == old) *(u32 *)(tm + 0x404) = *clk;
            if (*clk >= bench_target) {
                bench_target = 0;
                if (*clk / T_DAY != bench_start / T_DAY && (u32)tm >= 0x80000000u && (u32)tm < 0x81800000u) {
                    /* a new day: roll the day's wild animal as the morning after the bed does (0x80013B64..B88:
                       lbl_80349194 +0x3F8 = 0x2C + rand() % (lbl_803469D8 + 1)); the valley reload builds it from that */
                    *(s32 *)(tm + 0x3F8) = 0x2C + (s32)(F(0x8017D3E8, u32, (void))() % (u32)(*(s32 *)0x803469D8 + 1));
                    bench_rolls++;
                }
                *(s32 *)(g + 0x11B84) = *(s32 *)(g + 0x11B88);   /* stamina full */
                *(unsigned short *)(g + 0x11BB0) = 0;            /* sleepiness, as in rested dumps */
                *(s32 *)(g + 0x11BB8) = 0;
                *(s32 *)(g + 0x11BD0) = 0;
                *(u32 *)(g + 0x11CA4) = bench_start;            /* last time in bed (the sit's start), as the bed sets it */
                *(u32 *)(g + 0x11C9C) = *clk;                   /* last time woken up: now - tiredness counts from here */
                *(u32 *)(g + 0x11CB4) = *clk + 16 * 36000u;     /* sleepy from: woke + 16 h (as the bed sets it) */
                *(u32 *)(g + 0x11CAC) = *clk + 60 * 36000u;     /* the later limit: woke + 60 h (as the bed sets it) */
                {   /* user: wake up as from the bed: reload the valley scene (the event warp 0x2C's path for map 1,
                       func_8010D5A8 -> func_8017767C(g_system, 4, 0): next scene 4 = the field, map 1). The new scene
                       places every villager for the time, picks the day's wild animal and fades in itself; the player
                       comes back where he stands (position entry 0, game+0x29C78 / +0x29F84). */
                    u8 *gs = *(u8 **)0x80349208;
                    if ((u32)gs >= 0x80000000u && (u32)gs < 0x81800000u && *(s32 *)(g + 0x2A290) == 1) {
                        scene_req(gs, 4, 0); bench_reloads++; bench_wait = 600;
                    } else if (FADER) { u32 from = 0x000000FF, to = 0x00000000; fade_start(FADER, &from, &to, 0, 0, 0.5f); }
                }
                bench_cool = 60;                                 /* ~1 s after the fade-in: no new prompt */
            }
        }
    }
    if (gd_frame(g, map, t)) return;           /* the goddess's scene owns slot 37 (spring.c asks for it) */
    if (S.who != 1 && joe_frame(g, map, t)) return;   /* Joe's visit owns slot 37 today */
    if (day != 7 && !S.forced && flag_get(g + 0x12078, FLAG_MET)) flag_clear(g + 0x12078, FLAG_MET);
    if (day != 7 && !S.forced && flag_get(g + 0x12078, FLAG_FED)) flag_clear(g + 0x12078, FLAG_FED);
    active = day == 7 && tod >= T_START && tod < T_END;
    if (S.forced) {
        if (t - S.force_t0 < T_END - T_START) { active = 1; tod = T_START + (t - S.force_t0); }
        else S.forced = 0;
    }

    if (map != VALLEY) {                      /* left the valley without a fade */
        if (S.actor && !S.talking) despawn();
        if (S.loaded && !S.actor) restore_names();    /* slot 37 may already be the new scene's */
        return;
    }
    if (!active) {
        if (S.actor && no_event()) despawn();
        if (!S.actor && S.loaded && no_event()) release_model();
        return;
    }
    if (!no_event()) {                        /* events (and our talk) freeze him */
        if (S.actor && S.talking && *(s32 *)(g + 0x12194 + CNT_JOG * 4)) motion(MOT_JOG);
        return;
    }
    if (S.talking) {                          /* the talk has ended */
        s32 *back = (s32 *)(g + 0x12194 + CNT_FADEBACK * 4);
        if (*back && FADER) {                 /* the item-get scene ended on black: fade back in */
            u32 from = 0x000000FF, to = 0x00000000;
            *back = 0;
            fade_start(FADER, &from, &to, 0, 0, 0.5f);
        }
        *(s32 *)(g + 0x12194 + CNT_JOG * 4) = 0;
        S.talking = 0;
        S.motion = -1;
    }
    if (!S.actor) {
        if (!S.loaded) setup_model();
        spawn();
        if (!S.actor) return;
    }
    s = route_s(tod, &mode);
    place(s, mode == 2);
    motion(mode == 1 ? MOT_IDLE : MOT_RUN);
    if (mode != 1) {                          /* faster run cycle: step of the slot's animation states */
        u8 *slot = *(u8 **)(S.actor + 0xD4);  /* motion slot+0x54, its player +0x40: states at +8 / +0xC */
        float *st;
        if (slot) {
            st = *(float **)(slot + 0x9C); if (st) st[1] = RUN_RATE;
            st = *(float **)(slot + 0xA0); if (st) st[1] = RUN_RATE;
        }
    }

    /* A next to him (not holding Z, player free): event 406 - the milk talk once per visit, then
       "thanks" (flag 62, got the milk) or a brush-off (flag 61 only, refused) */
    if ((PAD_PRESS & 0x100) && !(PAD_HELD & 0x10) && CONTROL == 1) {
        float px = *(float *)(g + 0x29C78), pz = *(float *)(g + 0x29C80);
        float dx = px - S.pos.x, dz = pz - S.pos.z, d2 = dx * dx + dz * dz;
        if (d2 < TALK_R2) PAD_PRESS &= ~0x100u;
        if (d2 < TALK_R2 && d2 > 0.0001f) {
            float inv = rsqrt(d2);
            S.dir.x = dx * inv; S.dir.y = 0; S.dir.z = dz * inv;
            actor_setdir(S.actor, &S.dir);
            motion(MOT_IDLE);
            PAD_PRESS &= ~0x100u; PAD_HELD &= ~0x100u;   /* the player does not act on this A */
            *(s32 *)(g + 0x12208) = game_rand() & 0x7FFF;  /* event counter 29: the script's random */
            set_camera(g);
            set_get_camera(g);
            S.talking = 1;
            event_start(EVMGR, EVENT, 0, 0);
        }
    }
}
