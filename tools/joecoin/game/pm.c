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
#define fade_start    F(0x80189128, void, (u8 *, u32 *, u32 *, s32, s32, float))  /* fader, from, to, hold, 0, seconds */
#define flag_get      F(0x801129A0, s32, (u8 *, s32))
#define flag_clear    F(0x80112A30, void, (u8 *, s32))
#define rucksack_add  F(0x8004FDA0, s32, (u8 *, s32, s32, s32))   /* container game+0x50: id, count, slot (-1 = any) */
#define vcall(obj, vt_off, idx) (*(void (**)(u8 *, s32))(*(u32 *)((obj) + (vt_off)) + 4 * (idx)))

#define CHAR_ID   37
#define ANIMSET   71
#define VALLEY    1
#define EVENT     406
struct { u32 presses, started, rested; s32 map, ev680, ev58c; u32 control; } bench_dbg;   /* bench sit test 2 debug */
static u32 bench_target, bench_start, bench_cool;       /* bench time skip: clock target (0 = idle), clock at the start */
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

#include "route.h"               /* ROUTE_N, route[ROUTE_N][3] (x, z, y), ROUTE_LEN */

static const char pm_model[] = "pm/pm_0.arc";
static const char pm_anims[] = "pm/pm_0.anm.arc";
static const float pm_size[3] = { 0.95f, 1.58f, 1.2f };
/* test: the Harvest Goddess in the same slot (Z + X at Pool B; see goddess_test) */
static const char gd_model[] = "gd/gd_0.arc";
static const char gd_anims[] = "gd/gd_0.anm.arc";
static const float gd_size[3] = { 0.95f, 1.96f, 1.2f };
#define GD_X 270.3f                       /* Pool B, the goddess pond (centre) */
#define GD_Z 139.0f
#define GD_AHEAD 2.4f                     /* test spawn: this far in front of the player */
#define GD_ANIMS 10                       /* Celia's: idle, walk, holding idle, put away, explain, run, plead, dizzy, crouch, kitchen */
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
static void setup_model(void)
{
    u8 *slot = char_slot(CHARMGR, CHAR_ID, 0);
    s32 i;
    if (!S.guard) S.guard = op_new(GUARD_SIZE, pm_model, 1);
    if (slot[0xC]) {                         /* the teddy (or an old copy) is set up: clear it */
        vcall(slot, 0, 2)(slot, 0);
        unload_model(CHAR_ID);
    }
    S.orig_model = MODEL74_NAME; S.orig_anims = SET71_NAME;
    S.orig_size[0] = MODEL74_SIZE[0]; S.orig_size[1] = MODEL74_SIZE[1]; S.orig_size[2] = MODEL74_SIZE[2];
    {   const float *sz = S.who ? gd_size : pm_size;
        MODEL74_NAME = S.who ? gd_model : pm_model; SET71_NAME = S.who ? gd_anims : pm_anims;
        MODEL74_SIZE[0] = sz[0]; MODEL74_SIZE[1] = sz[1]; MODEL74_SIZE[2] = sz[2];
    }
    for (i = 0; i < 12; i++) S.orig_set[i] = SET71_DATA[i];
    S.orig_mot2 = MOT2_WORD; MOT2_WORD = MOT2_JOG;
    S.orig_list = SET71_LIST;
    if (S.who) {                              /* the goddess: motion n = Celia's animation n */
        for (i = 0; i < GD_ANIMS; i++) {
            gd_mot[i][0] = 0x8E000400u | (u32)i; gd_mot[i][1] = 0x07FBFFFFu; gd_mot[i][2] = 0;
            gd_mot[i][3] = 0xFFFFFFFFu; gd_mot[i][4] = 0xFFFFFFFFu; gd_mot[i][5] = 0;
            gd_list[i] = gd_mot[i];
        }
        SET71_LIST = gd_list;
    }
    load_animset(ANIMSET, 0);
    load_model(CHAR_ID);
    slot_setup(slot, CHAR_ID, -1);
    S.loaded = 1;
}

static void restore_names(void)
{
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
    if (slot[0xC]) {
        vcall(slot, 0, 2)(slot, 0);
        unload_model(CHAR_ID);
    }
    unload_animset(ANIMSET);
    for (i = 0; i < 12; i++) SET71_DATA[i] = S.orig_set[i];
    MOT2_WORD = S.orig_mot2;
    SET71_LIST = S.orig_list;
    restore_names();
}

static void spawn(void)
{
    u8 *a = op_new(0x2A8, pm_model, 1), *c;
    if (!a) return;
    actor_ctor(a, 1, CHAR_ID);
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
/* test: Z + X on the valley = the Harvest Goddess standing just in front of the player, facing them; each further
   Z + X plays her next animation (motion entry 2 pointed at it, as the Postman's jog). Leaving the
   valley removes her. The Postman's visit is held off while she is out. */
static void goddess_test(u8 *g, s32 map)
{
    float *p = (float *)(g + 0x29C78), dx, dz, l2, inv;
    if (map != VALLEY) {
        if (S.actor && !S.talking) despawn();
        if (S.loaded && !S.actor) restore_names();
        S.who = 0;
        return;
    }
    if (!(PAD_HELD & 0x10) || !(PAD_PRESS & 0x400)) return;
    PAD_PRESS &= ~0x400u;
    if (!no_event()) return;
    if (S.who != 1 || !S.actor) {                        /* bring her out in front of the player */
        float *d = (float *)(g + 0x29F84), fl = d[0] * d[0] + d[2] * d[2], r = fl > 0.0001f ? rsqrt(fl) : 0;
        if (S.actor) despawn();
        if (S.loaded) release_model();
        S.who = 1;
        setup_model();
        spawn();
        if (!S.actor) { S.who = 0; return; }
        S.pos.x = p[0] + d[0] * r * GD_AHEAD; S.pos.z = p[2] + d[2] * r * GD_AHEAD;
        S.pos.y = p[1] + 2.0f;
        S.pos.y = ground_y(COLLMAP, &S.pos);
        S.gd_anim = 0;
    } else S.gd_anim = (S.gd_anim + 1) % GD_ANIMS;
    dx = p[0] - S.pos.x; dz = p[2] - S.pos.z; l2 = dx * dx + dz * dz;
    if (l2 > 0.0001f) { inv = rsqrt(l2); S.dir.x = dx * inv; S.dir.y = 0; S.dir.z = dz * inv; }
    actor_setpos(S.actor, &S.pos);
    actor_setdir(S.actor, &S.dir);
    S.motion = -1;
    motion(S.gd_anim);
}

void logs_release(void);
void logs_frame(u8 *g, s32 map, u32 pad_held, u32 pad_press);
void skill_frame(u8 *g, u32 pad_held, u32 pad_press);
void spring_release(void);
void spring_frame(u8 *g, s32 map, u32 pad_held, u32 pad_press);
void joe_dig_frame(void);
void van_frame(u8 *g);

void pm_scene_change(void)
{
    logs_release();
    spring_release();
    if (S.talking) return;
    if (S.actor) despawn();
    if (S.loaded) release_model();
}

void pm_frame(void)
{
    u8 *g = GAME;
    u32 t, tod;
    s32 day, map, mode, active;
    float s;

    if ((u32)g < 0x80000000u || (u32)g >= 0x81800000u || !*(u32 **)0x80349218) return;
    t = CLOCK;
    day = (t / T_DAY) % 10;
    tod = t % T_DAY;
    map = *(s32 *)(g + 0x2A290);              /* the player's current map */
    if (!*(u8 **)0x80349208 || *(s32 *)(*(u8 **)0x80349208 + 0x68) != map) map = -1;  /* g_system: in the field */
    logs_frame(g, map, PAD_HELD, PAD_PRESS);  /* choppable logs (logs.c) */
    skill_frame(g, PAD_HELD, PAD_PRESS);      /* tool skill on the HUD (skill.c) */
    spring_frame(g, map, PAD_HELD, PAD_PRESS);  /* offerings at the goddess pond (spring.c) */
    joe_dig_frame();                          /* $JOE coin dig-site halving (joetv.c) */
    van_frame(g);                             /* van test 5: log the stall Van's daily plan (joetv.c) */
    if ((PAD_HELD & 0x10) && (PAD_PRESS & 0x200)) {   /* test: Z + B = clock to 22:00 today (then bed = next morning) */
        u32 *clk = *(u32 **)0x80349218, old = *clk, *copy = 0;
        u8 *tm = *(u8 **)0x80349194;                 /* holds a second copy of the clock at +0x404 */
        if ((u32)tm >= 0x80000000u && (u32)tm < 0x81800000u && *(u32 *)(tm + 0x404) == old) copy = (u32 *)(tm + 0x404);
        if (old % T_DAY < 792000u) {
            *clk = old / T_DAY * T_DAY + 792000u;
            if (copy) *copy = *clk;
        }
        PAD_PRESS &= ~0x200u;
    }
    /* Bench by the tree (valley): A within 1.6 of the seat, facing it, no event running -> event 407
       ("Sit until the evening?" / "Sit until the morning?", Common.arc entry 107, debug.mes 9/10).
       The player's own map (game+0x2A290) is used, not the field check: after the event the latter can differ. */
    if (bench_cool) bench_cool--;
    if ((PAD_PRESS & 0x100) && !(PAD_HELD & 0x10) && *(s32 *)(g + 0x2A290) == 1 && !S.talking
        && !bench_target && !bench_cool && !*(s32 *)(g + 0x12194 + BENCH_CNT * 4)
        && !(FADER && *(u8 *)(FADER + 0x60))) {   /* not during a skip, a pending request, a fade, or just after */
        float *p = (float *)(g + 0x29C78), *d = (float *)(g + 0x29F84);
        float dx = BENCH_X - p[0], dz = BENCH_Z - p[2], d2 = dx * dx + dz * dz;
        if (d2 < 1.6f * 1.6f && d2 > 0.0001f && (dx * d[0] + dz * d[2]) * rsqrt(d2) > 0.5f) {
            u8 *ev = EVMGR;
            bench_dbg.presses++; bench_dbg.map = map; bench_dbg.control = CONTROL;
            bench_dbg.ev680 = ev ? *(s32 *)(ev + 0x680) : -2; bench_dbg.ev58c = ev ? *(s32 *)(ev + 0x58C) : -2;
            if (ev && *(s32 *)(ev + 0x680) == -1 && !*(s32 *)(ev + 0x58C) && CONTROL != 3) {
                PAD_PRESS &= ~0x100u; PAD_HELD &= ~0x100u;   /* the player does not act on this A */
                bench_dbg.started += event_start(ev, BENCH_EVENT, 0, 0) & 0xFF ? 1 : 0;
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
            bench_dbg.rested++;
        }
        if (bench_target) {
            u32 *clk = *(u32 **)0x80349218, old = *clk, step;
            u8 *tm = *(u8 **)0x80349194;
            PAD_PRESS = 0; PAD_HELD = 0;
            step = bench_target - old > 3000u ? 3000u : bench_target - old;
            *clk = old + step;
            ship_check(*(u8 **)0x803491CC);                  /* farm-side timed checks (shipping pickup 5:10-5:40, payout 12:00-12:30): only the farm/house module (wlp2) calls this, so the valley never would */
            if ((u32)tm >= 0x80000000u && (u32)tm < 0x81800000u && *(u32 *)(tm + 0x404) == old) *(u32 *)(tm + 0x404) = *clk;
            if (*clk >= bench_target) {
                bench_target = 0;
                *(s32 *)(g + 0x11B84) = *(s32 *)(g + 0x11B88);   /* stamina full */
                *(unsigned short *)(g + 0x11BB0) = 0;            /* sleepiness, as in rested dumps */
                *(s32 *)(g + 0x11BB8) = 0;
                *(s32 *)(g + 0x11BD0) = 0;
                *(u32 *)(g + 0x11CA4) = bench_start;            /* last time in bed (the sit's start), as the bed sets it */
                *(u32 *)(g + 0x11C9C) = *clk;                   /* last time woken up: now - tiredness counts from here */
                *(u32 *)(g + 0x11CB4) = *clk + 16 * 36000u;     /* sleepy from: woke + 16 h (as the bed sets it) */
                *(u32 *)(g + 0x11CAC) = *clk + 60 * 36000u;     /* the later limit: woke + 60 h (as the bed sets it) */
                if (FADER) { u32 from = 0x000000FF, to = 0x00000000; fade_start(FADER, &from, &to, 0, 0, 0.5f); }
                bench_cool = 60;                                 /* ~1 s after the fade-in: no new prompt */
            }
        }
    }
    if (day != 7 && !S.forced && flag_get(g + 0x12078, FLAG_MET)) flag_clear(g + 0x12078, FLAG_MET);
    if (day != 7 && !S.forced && flag_get(g + 0x12078, FLAG_FED)) flag_clear(g + 0x12078, FLAG_FED);
    active = day == 7 && tod >= T_START && tod < T_END;
    if (PAD_HELD & 0x10) {                    /* test: Z + D-Left = a visit now, Z + D-Right = stop, Z + D-Down = milk */
        if (PAD_PRESS & 0x1) { S.forced = 1; S.force_t0 = t; }
        if (PAD_PRESS & 0x2) S.forced = 0;
        if (PAD_PRESS & 0x4) {                /* test: Z + D-Down = one milk of each grade into the rucksack */
            s32 id;
            for (id = 7; id <= 10; id++) rucksack_add(g + 0x50, id, 1, -1);
        }
    }
    if (S.who == 1 || ((PAD_HELD & 0x10) && (PAD_PRESS & 0x400))) {   /* goddess test (Z + X) */
        goddess_test(g, map);
        if (S.who == 1) return;
    }
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
