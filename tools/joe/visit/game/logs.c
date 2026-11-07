/* Choppable logs on the valley map (map 1). The three logs are map objects (mapobj.gpl model 285,
   placed in mapc1..5.arc at the spots below with a +0.0123 marker on x/z). After the valley loads
   their placement records (in the loaded mapc arc) and runtime instances (made only near the player)
   are found by that translation; a log that is not there is dropped
   100 units under the ground. Present logs get three body colliders along their length.
   Saved state: event counter 63 (game+0x12290; counters 0-29 count up every day, 63 is free):
     bits 0-2 log present, bit 3 rain/snow seen today, bits 4-6 spot used this season,
     bits 8-15 last day seen (day % 255 + 1), bits 16-27 axe hits on each log (4 bits each)
   Rules: the morning after a day with rain or snow in the daytime (6:00-18:00, weather 3/5 rain,
   4 snow, for about 20 s), one log appears at a random spot that has not had one this season, so at
   most three logs (15 lumber) a season; uncut logs stay until the season ends. Ten Cursed Axe hits on
   a log (counted at each swing's impact) remove it: the axe goes back into the rucksack, one lumber
   into the hands with the pick-up motion and sound, four into the rucksack. */

typedef unsigned int u32;
typedef int s32;
typedef unsigned char u8;

#define F(addr, ret, args) ((ret (*) args)(addr))
#define op_new        F(0x80178E88, void *, (u32, const char *, s32))
#define col_init      F(0x801520F8, void, (u8 *))
#define col_config    F(0x80152218, void, (u8 *, s32))
#define game_rand     F(0x8017D3E8, s32, (void))
#define pl_prep       F(0x800310A4, void, (u8 *, s32))           /* as the tool swing does before its state */
#define mot_rate      F(0x8017D74C, void, (u8 *, float))
#define pl_state      F(0x80031D7C, void, (u8 *, s32))
#define tool_rate     F(0x8004DAE0, float, (u8 *, s32, s32))  /* swing motion speed from proficiency */
#define ruck_add      F(0x8004FDA0, s32, (u8 *, s32, s32, s32))  /* rucksack (game+0x50): 1 = added */
#define item_bind     F(0x80011F2C, void, (u8 **, u8 **))         /* bind an item's symbol model: (&row, &holder) */
#define item_unbind   F(0x801A2AD8, void, (u8 *))                 /* empty the hand model */
#define held_attach   F(0x8007C934, void, (u8 *, u8 *))
#define sfx_play      F(0x8012A52C, s32, (u8 *, s32, s32))      /* as cmd_30 */
#define SFX_PICKUP    261        /* 'syukaku', the harvest/pick-up sound */
#define motion_play   F(0x8007C0C0, void, (u8 *, s32, s32, s32, s32, s32))
#define LUMBER        0x51C      /* item (was the unused "Record13") */
#define LUMBER_N      5          /* per log: 1 in hand, the rest to the rucksack */
#define ST_PICKUP     0x84       /* the pick-up wait state (does nothing by itself) */
#define MOT_PICKUP    0xA        /* the pick-up motion (state 0x83's) */
#define PICKUP_FRAMES 36
#define ATTACH_AT     10         /* frame of the pick-up when the lumber is in the hands */
#define ITEMS         ((u8 *)0x80282DF8)   /* item table, 0x24 per item */
#define CONTROL       (*(u8 *)(*(u8 **)0x80349218 + 8))
#define PAD_PRESS_W   (*(volatile u32 *)0x8034157C)
#define AXE           0x502
#define ST_FIELD      1          /* player state: free in the field */
#define ST_SWING      0x79       /* tool swing (what action 0x0F enters) */
#define ST_MESSAGE    0x2A       /* a message box: file at player+0x14C0, message at +0x14C4 */
#define MES_SYSTEM    0x33       /* system.mes */
#define MSG_LOG_LOOK  0x1FE      /* "A humble log." (added at the end of system.mes) */
#define ACT_LOOK      0x18       /* an A action whose label is "Look" */
#define vcall(obj, vt_off, idx) (*(void (**)(u8 *, s32))(*(u32 *)((obj) + (vt_off)) + 4 * (idx)))
#define COL_VTABLE    0x802C5720
#define GAME          (*(u8 **)0x803491CC)
#define CLOCK         (**(u32 **)0x80349218)
#define WEATHER       (*(s32 *)(*(u8 **)0x803491D4 + 0x20))
#define CNT(g, i)     (*(s32 *)((g) + 0x12194 + 4 * (i)))
#define LOGST(g)      (*(u32 *)((g) + 0x12194 + 4 * 63))   /* event counter 63 (__COUNTER_COUNTUP_NO_START):
                                                              counters 0-29 count up every day; 63 is never
                                                              touched by the game and is saved */
#define HITS_OF(st, i) (((st) >> (16 + 4 * (i))) & 15)
#define HITS_CLR(i)    (15u << (16 + 4 * (i)))

#define LOGS      3
#define PRESENT   0x07       /* counter 4 bits 0-2: log present */
#define WET       0x08       /* bit 3: rain or snow seen today (daytime, for WET_FRAMES) */
#define USED_BIT0 0x10       /* bits 4-6: the spot has had its log this season */
#define USED      0x70
#define SEASON_DAYS 10
#define WET_FROM  (6 * 36000u)          /* 6:00 (clock in 1/10 s) */
#define WET_TO    (18 * 36000u)         /* 18:00 */
#define WET_FRAMES 600                  /* about 20 s of rain/snow in the daytime */
#define HITS      10
#define VALLEY    1
#define T_DAY     864000u
#define HIDE_DY   100.0f
#define COLS      7          /* colliders per log, along its length (player radius 0.3: no gaps) */
#define COL_STEP  0.45f
#define COL_R     0.4f       /* collider radius (log radius 0.32) */
#define PTRS      4          /* copies per log: placement records + instance */
#define COL_CHAR  37         /* collider size from character 37's entry (as the Postman's) */
#define REACH     1.1f       /* axe: point this far in front of the player ... */
#define HIT_R     0.9f       /* ... within this of the log's axis */
#define HALF_LEN  1.8f

static const float LX[LOGS] = { 182.0123f, 283.9923f, 75.4523f };
static const float LY[LOGS] = { 13.91f, 21.62f, 0.47f };
static const float LZ[LOGS] = { 177.0123f, 122.3823f, 117.6123f };
/* x of each log's snow (mapobj model 286, placed at the log's spot with x marker +0.0246) */
static const float SX[LOGS] = { 182.0246f, 284.0046f, 75.4646f };
#define SETS      (2 * LOGS)  /* 0-2 the logs, 3-5 their snow */
#define SET_X(i)  ((i) < LOGS ? LX[i] : SX[(i) - LOGS])
#define WINTER(g) ((CLOCK / T_DAY / SEASON_DAYS) % 4 == 3)    /* spring, summer, autumn, winter */
/* log axis (cos yaw, -sin yaw) for yaw 99, 149, -160 degrees */
static const float AX[LOGS] = { -0.156434f, -0.857167f, -0.939693f };
static const float AZ[LOGS] = { -0.987688f, -0.515038f, 0.342020f };

static struct {
    float *inst[SETS][PTRS];          /* x translation of a record / instance (y at +4 words, z at +8), 0 = free */
    u32 scan;                         /* next address of the incremental instance scan */
    s32 active;                       /* on the valley: pointers / colliders may be held */
    s32 prev_state;                   /* player state last frame: a hit is counted on entering the swing */
    s32 reward;                       /* a log was finished: give the lumber when the swing is over */
    s32 pickup;                       /* frames left of the pick-up motion (control locked) */
    s32 wood;                         /* this swing hit a log: 1 = its impact sound not swapped yet, 2 = done */
    s32 tlog;                         /* the log this swing is at */
    s32 wet_frames;                   /* daytime frames of rain/snow today */
    u32 sfx_n;                        /* sounds started (debug ring below) */
    unsigned short sfx_log[16];       /* ids of the last sounds started, for RAM dumps */
    u8 *col[LOGS][COLS];
    float owner[LOGS][COLS][0x70 / 4];   /* stand-in owners: position +0x4C, direction +0x58, map +0x64 */
} L;

u8 *pm_player;                            /* set by the hook at the start of the field A handler (0x80043120) */

static u32 fbits(float f) { union { float f; u32 u; } v; v.f = f; return v.u; }

#define SCAN_LO   0x80700000u
#define SCAN_HI   0x817FFF00u
#define SCAN_STEP 0x40000u                /* bytes per frame: the whole range in about a second */

static s32 near_bits(u32 a, u32 b) { return a - b + 64 < 128; }

static s32 still_there(float *p, s32 i)
{
    return near_bits(fbits(p[0]), fbits(SET_X(i))) && near_bits(fbits(p[8]), fbits(LZ[i % LOGS]));
}

/* look through the next SCAN_STEP bytes for copies of the logs' translations: placement records
   (id 0x011D at x - 0x10) and instances (model pointer at x - 0x10) */
static void scan_step(void)
{
    u32 a, hi, i, k;
    if (L.scan < SCAN_LO || L.scan >= SCAN_HI) L.scan = SCAN_LO;
    hi = L.scan + SCAN_STEP; if (hi > SCAN_HI) hi = SCAN_HI;
    for (a = L.scan; a < hi; a += 4) {
        u32 w = *(u32 *)a;
        for (i = 0; i < SETS; i++) {
            u32 p;
            if (!near_bits(w, fbits(SET_X(i))) || !near_bits(*(u32 *)(a + 0x20), fbits(LZ[i % LOGS]))) continue;
            p = *(u32 *)(a - 0x10);                          /* record: model 285 (log) / 286 (snow) */
            if ((p >> 16) != 0x011D && (p >> 16) != 0x011E && (p < 0x80000000u || p >= 0x81800000u)) continue;
            for (k = 0; k < PTRS; k++) if (L.inst[i][k] == (float *)a) break;
            if (k < PTRS) continue;
            for (k = 0; k < PTRS; k++) if (!L.inst[i][k]) { L.inst[i][k] = (float *)a; break; }
        }
    }
    L.scan = hi;
}

static void colliders(s32 i, s32 on)
{
    s32 k;
    for (k = 0; k < COLS; k++) {
        u8 *c = L.col[i][k];
        if (on && !c) {
            float *o = L.owner[i][k], d = (k - (COLS - 1) / 2) * COL_STEP;
            c = op_new(0x40, "logs", 1);
            if (!c) return;
            { s32 j; for (j = 0; j < 0x40; j += 4) *(u32 *)(c + j) = 0; }
            o[0x4C / 4] = LX[i] + AX[i] * d; o[0x50 / 4] = LY[i]; o[0x54 / 4] = LZ[i] + AZ[i] * d;
            o[0x58 / 4] = 0; o[0x5C / 4] = 0; o[0x60 / 4] = 1;
            *(s32 *)&o[0x64 / 4] = VALLEY;
            col_init(c);
            *(u32 *)(c + 0x10) = COL_VTABLE;
            *(float **)(c + 0x34) = o;
            col_config(c, COL_CHAR);
            *(float *)(c + 0x24) = COL_R;
            vcall(c, 0x10, 3)(c, 0);
            L.col[i][k] = c;
        } else if (!on && c) {
            vcall(c, 0x10, 4)(c, 0);
            vcall(c, 0x10, 2)(c, 1);
            L.col[i][k] = 0;
        }
    }
}

void logs_release(void)                   /* scene change / leaving the valley */
{
    s32 i;
    pm_player = 0;
    for (i = 0; i < SETS; i++) { s32 k; if (i < LOGS) colliders(i, 0); for (k = 0; k < PTRS; k++) L.inst[i][k] = 0; }
    L.scan = 0; L.active = 0;
    if (L.pickup) { L.pickup = 0; CONTROL = 1; }
}

static void day_rules(u8 *g)
{
    u32 st = LOGST(g), day = CLOCK / T_DAY, tod = CLOCK % T_DAY;
    u32 last = (st >> 8) & 0xFF, now = day % 255 + 1;                 /* 1..255 (0 = never seen) */
    s32 w = WEATHER, i;
    if (tod >= WET_FROM && tod < WET_TO && w >= 3 && w <= 5) {          /* rain/snow in the daytime */
        if (++L.wet_frames >= WET_FRAMES) st |= WET;
    }
    if (last != now) {
        L.wet_frames = 0;
        if (last) {
            u32 gone = (now + 255 - last) % 255, prev = day - (gone ? gone : 255);    /* the last day seen */
            if (day / SEASON_DAYS != prev / SEASON_DAYS)                 /* a new season: all cleared */
                st &= ~(PRESENT | USED);
            if (st & WET) {                                              /* yesterday was wet: one new log */
                s32 free[LOGS], n = 0;                                   /* at a spot not used this season */
                for (i = 0; i < LOGS; i++) if (!(st & (USED_BIT0 << i))) free[n++] = i;
                if (n) { i = free[(game_rand() & 0x7FFF) % n]; st |= (1 << i) | (USED_BIT0 << i); }
            }
        }
        st = (st & ~(WET | 0xFF00u)) | (now << 8);
    }
    for (i = 0; i < LOGS; i++) if (!(st & (1 << i))) st &= ~HITS_CLR(i);   /* no log, no hits */
    LOGST(g) = st;
}

static void axe_swing(u8 *g, u32 pad_held, u32 pad_press);
static void give_lumber(u8 *g, u8 *pl);
static void count_swing(u8 *g);

void logs_frame(u8 *g, s32 map, u32 pad_held, u32 pad_press)
{
    s32 i, st;
    day_rules(g);
    if (map != VALLEY) {
        if (L.active) logs_release();
        return;
    }
    L.active = 1;
    st = LOGST(g);
    for (i = 0; i < SETS; i++) {
        s32 j = i % LOGS, on = (st >> j) & 1 && (i < LOGS || WINTER(g));   /* snow: winter only */
        s32 k;
        for (k = 0; k < PTRS; k++) {
            float *p = L.inst[i][k];
            if (p && !still_there(p, i)) p = L.inst[i][k] = 0;                    /* freed */
            if (p) p[4] = on ? LY[j] : LY[j] - HIDE_DY;
        }
        if (i < LOGS) colliders(i, on);                      /* independent of finding the model */
    }
    scan_step();                                             /* instances come and go with distance */
    axe_swing(g, pad_held, pad_press);
    count_swing(g);
    if (L.reward && pm_player) { L.reward = 0; give_lumber(g, pm_player); }
    if (L.pickup > 0 && pm_player) {
        if (--L.pickup == PICKUP_FRAMES - ATTACH_AT) {                    /* the lumber is in the hands */
            u8 *ctrl = *(u8 **)(pm_player + 0x135C), *row = ITEMS + LUMBER * 0x24;
            *(s32 *)(ctrl + 0x144) = LUMBER;
            item_bind(&row, (u8 **)(pm_player + 0x1454));
            held_attach(*(u8 **)(pm_player + 0xBC), *(u8 **)(pm_player + 0x1454));
            ruck_add(g + 0x50, LUMBER, LUMBER_N - 1, -1);
            sfx_play(*(u8 **)0x803491E4, SFX_PICKUP, 0);
        }
        if (L.pickup == 0) { pl_state(pm_player, ST_FIELD); CONTROL = 1; }
    }
}

/* the present log in front of the player (a point REACH ahead within HIT_R of its axis), or -1 */
static s32 log_in_front(u8 *g)
{
    float *p = (float *)(g + 0x29C78), *d = (float *)(g + 0x29F84);
    float dx = d[0], dz = d[2], l2 = dx * dx + dz * dz, px, pz, r = 1.0f;
    s32 i, st = LOGST(g);
    if (l2 < 0.0001f) return -1;
    r = r * (1.5f - 0.5f * l2 * r * r); r = r * (1.5f - 0.5f * l2 * r * r); r = r * (1.5f - 0.5f * l2 * r * r);
    dx *= r; dz *= r;
    px = p[0] + dx * REACH; pz = p[2] + dz * REACH;
    for (i = 0; i < LOGS; i++) {
        float rx, rz, t, ex, ez;
        if (!((st >> i) & 1)) continue;
        rx = px - LX[i]; rz = pz - LZ[i];
        t = rx * AX[i] + rz * AZ[i];
        if (t > HALF_LEN) t = HALF_LEN;
        if (t < -HALF_LEN) t = -HALF_LEN;
        ex = rx - AX[i] * t; ez = rz - AZ[i] * t;
        if (ex * ex + ez * ez <= HIT_R * HIT_R) return i;
    }
    return -1;
}

static void hit(u8 *g, s32 i)
{
    u32 st = LOGST(g), n = HITS_OF(st, i) + 1;
    LOGST(g) = (st & ~HITS_CLR(i)) | (n << (16 + 4 * i));
    if (n >= HITS) {                                                    /* chopped: the log goes */
        LOGST(g) = st & ~HITS_CLR(i) & ~(1u << i);                      /* (its spot stays used) */
        { s32 k; for (k = 0; k < PTRS; k++) {
            if (L.inst[i][k]) L.inst[i][k][4] = LY[i] - HIDE_DY;
            if (L.inst[i + LOGS][k]) L.inst[i + LOGS][k][4] = LY[i] - HIDE_DY; } }
        colliders(i, 0);
        L.reward = 1;
    }
}

/* the log is done: the Cursed Axe goes back into the rucksack, one Lumber into the hands with the
   pick-up motion (as picking up a field item, state 0x83), the rest into the rucksack */
static void give_lumber(u8 *g, u8 *pl)
{
    u8 *ctrl = *(u8 **)(pl + 0x135C);
    s32 held = *(s32 *)(ctrl + 0x144);
    if (held && (held != AXE || !ruck_add(g + 0x50, AXE, 1, -1))) {     /* hands can't be freed */
        ruck_add(g + 0x50, LUMBER, LUMBER_N, -1);
        return;
    }
    *(s32 *)(ctrl + 0x144) = 0;                                       /* empty hands, as a pick-up starts */
    item_unbind(*(u8 **)(pl + 0x1454));
    pl_state(pl, ST_PICKUP);
    motion_play(*(u8 **)(pl + 0xBC), MOT_PICKUP, *(s32 *)(pl + 0x138C), 0, *(s32 *)(ctrl + 0x148), 4);
    CONTROL = 0;
    L.pickup = PICKUP_FRAMES;
}

/* A with the Cursed Axe at a log: the field's tool actions only swing at plots, so start the
   swing here (as the A handler does for action 0x0F: func_800310A4(p, 1), motion rate 1.0,
   state 0x79) and count the hit; the A press is consumed so the handler does nothing else */
static void axe_swing(u8 *g, u32 pad_held, u32 pad_press)
{
    u8 *pl = pm_player;
    s32 i;
    if (!(pad_press & 0x100) || (pad_held & 0x10) || !pl || CONTROL != 1) return;
    if (*(s32 *)(pl + 0x1364) != ST_FIELD) return;
    i = log_in_front(g);
    if (i < 0) return;
    PAD_PRESS_W &= ~0x100u;
    if (*(s32 *)(g + 0x11CC4) != AXE) {                                 /* no axe: "A humble log." */
        *(s32 *)(pl + 0x14C0) = MES_SYSTEM;
        *(s32 *)(pl + 0x14C4) = MSG_LOG_LOOK;
        pl_state(pl, ST_MESSAGE);
        return;
    }
    pl_prep(pl, 1);
    mot_rate(*(u8 **)(pl + 0xBC) + 0x54, 1.0f);
    pl_state(pl, ST_SWING);
}

/* one hit per swing, whoever started it (axe_swing or the game's own action 0x0F): the frame the
   player enters the swing state with the Cursed Axe in hand, facing a present log */
/* swing speed from stamina (game+0x11B84, max +0x11B88): full speed down to TIRED_AT of the bar,
   then slower in a straight line to SLOW_RATE at empty */
#define TIRED_AT  0.8f
#define LOG_COST  3000       /* extra stamina per hit on a log (bar = 100000; the game's own is ~1000) */
#define SLOW_RATE 0.4f
static float swing_rate(u8 *g)
{
    s32 st = *(s32 *)(g + 0x11B84), mx = *(s32 *)(g + 0x11B88);
    float f;
    if (mx <= 0) return 1.0f;
    f = (float)st / (float)mx;
    if (f >= TIRED_AT) return 1.0f;
    if (f < 0) f = 0;
    return SLOW_RATE + (1.0f - SLOW_RATE) * f / TIRED_AT;
}

static void count_swing(u8 *g)
{
    u8 *pl = pm_player;
    s32 st, i;
    if (!pl) return;
    st = *(s32 *)(pl + 0x1364);
    if (st != ST_SWING) { if (L.wood == 1) hit(g, L.tlog); L.wood = 0; }   /* no impact sound: count it now */
    else if (L.prev_state != ST_SWING && *(s32 *)(g + 0x11CC4) == AXE) {
        i = log_in_front(g);
        if (i >= 0) {
            s32 *stam = (s32 *)(g + 0x11B84), lo = *(s32 *)(g + 0x11B8C);
            mot_rate(*(u8 **)(pl + 0xBC) + 0x54,                         /* the game's speed (proficiency) */
                     tool_rate(*(u8 **)(pl + 0x135C), 0xF, AXE) * swing_rate(g));   /* x stamina */
            *stam = *stam - LOG_COST < lo ? lo : *stam - LOG_COST;        /* on top of the game's own cost */
            L.wood = 1; L.tlog = i;                                         /* the hit lands with the impact */
        }
    }
    L.prev_state = st;
}

/* called from the baked Cursed Axe code on every plot swing; returns 0 (the swing tills nothing).
   Hits are counted in count_swing. */
s32 pm_axe_hit(void)
{
    return 0;
}

/* the field A handler's action for this frame (0x8004368C): the tool swing (0x0F) when the Cursed Axe
   faces a present log, so the A button shows the swing label */
s32 spring_label(s32 action, u8 *pl);
s32 gd_label(s32 action, u8 *pl);
s32 pm_label(s32 action, u8 *pl)
{
    u8 *g = GAME;
    action = spring_label(action, pl);                               /* Toss at the goddess pond */
    action = gd_label(action, pl);                                   /* gd1: Talk to call / talk to the goddess */
    if ((u32)g < 0x80000000u || (u32)g >= 0x81800000u) return action;
    if (*(s32 *)(pl + 0x64) != VALLEY || log_in_front(g) < 0) return action;
    return *(s32 *)(g + 0x11CC4) == AXE ? 0x0F : ACT_LOOK;          /* swing, or "Look" without the axe */
}

/* every sound start (0x8018B224) passes its id here. During a swing that hit a log, the first
   field/tool sound (the impact on the ground) becomes the wood hit; ambient, animal, menu and
   voice sounds are left alone. */
#define SFX_WOOD 432
static s32 ambient(s32 id)
{
    return id < 181 || id == 182 || (id >= 185 && id <= 213) || id == 216 || (id >= 219 && id <= 222) ||
           (id >= 225 && id <= 227) || (id >= 254 && id <= 256) || id == 259 || id == 260 || id == 264 ||
           (id >= 282 && id <= 290) || (id >= 301 && id <= 303) || id >= 305;
}
s32 pm_sfx(s32 id)
{
    u8 *pl = pm_player;
    L.sfx_log[L.sfx_n++ & 15] = (unsigned short)id;
    if (L.wood == 1 && pl && *(s32 *)(pl + 0x1364) == ST_SWING && !ambient(id)) { L.wood = 2; hit(GAME, L.tlog); return SFX_WOOD; }
    return id;
}

/* swing end for hoes and the Cursed Axe (0x80033170): the vanilla 30 frames at motion speed 1,
   shorter when proficiency speeds the swing up, longer when stamina slows it down */
#define SWING_FRAMES 30.0f
s32 pm_swing_done(u8 *pl)
{
    s32 n = *(s32 *)(pl + 0x1368);
    float r = *(float *)(*(u8 **)(pl + 0xBC) + 0x54 + 0x8);      /* motion speed (func_8017D74C) */
    if (!(r > 0.25f)) r = 0.25f;
    return n >= SWING_FRAMES / r;
}
