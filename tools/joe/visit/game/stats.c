/* Farmer level / EXP / stats (step 2 of notes/stats_design.md; pm.bin).
   Saved in event counters (game+0x12194 + 4i, saved with the game; 0-29 count up daily, 8/19/40-44/49/50/52/53/63 in use):
   54 'ST01' marker, 55 EXP into the current level, 56 level (from 1), 57 HP, 58 Pwr, 59 End, 60 Lck, 61 the level-up
   menu's answer (set by event 410: 1..4, raw or x128), 62 points not yet spent.
   EXP: stamina spent on tools (any stamina drop that is not an enemy hit: zt.c reports those), 1 EXP per 100 stamina;
   the day's wild animal on defeat (zt.c). Next level needs 500 + 750 x (level - 1) (stats2). Each level: "Level up!" (skill.c, SE 216)
   and one point, chosen in event 410 (Common.arc) once the player is free and not fighting.
   Effects: HP +10 % max stamina per point (max 20 -> 3 bars); End: tool HP cost -2 % and hunger -2.5 % per point;
   Pwr: weapon damage +5 % per point (zt.c); tool efficiency and Lck come later. Stats view: Z + D-pad Up (event 411,
   number slots set with func_80102300(msg mgr *0x803491C4, slot, value)). */
typedef unsigned int u32;
typedef int s32;
typedef unsigned char u8;
#define F(addr, ret, args) ((ret (*) args)(addr))
#define CNT(g, i)     (*(s32 *)((g) + 0x12194 + 4 * (i)))
#define EVMGR         (*(u8 **)0x803491BC)
#define CONTROL       (*(u8 *)(*(u8 **)0x80349218 + 8))
#define event_start   F(0x8010AAC4, s32, (u8 *, s32, s32, s32))
#define msg_num       F(0x80102300, void, (u8 *, s32, s32))
#define MSGMGR        (*(u8 **)0x803491C4)
#define OK(p)         ((u32)(p) >= 0x80000000u && (u32)(p) < 0x81800000u)
enum { C_MAGIC = 54, C_EXP, C_LV, C_HP, C_PWR, C_END, C_LCK, C_ANS, C_PTS };
#define ST_MAGIC  0x53543031u
#define EV_LVUP   410
#define EV_STATS  411
#define STAT_MAX  20
void skill_levelup(void);
struct { u32 magic; s32 ignore, acc, last, lastfull, menu, cool, gained, refund, wait; } ST;   /* 'STAT' (dump) */

static s32 need(s32 lv) { return 500 + 1250 * (lv - 1); }   /* stats3: 500, 1750, 3000 ... (farming EXP x3); stats2: 500, 1250, 2000 ... (was 1500 + 500 lv: Lv 2 took 2000) */
static s32 ready(u8 *g) { return OK(g) && CNT(g, C_MAGIC) == (s32)ST_MAGIC; }
s32 stats_pwr(void) { u8 *g = *(u8 **)0x803491CC; return ready(g) ? CNT(g, C_PWR) : 0; }
void stats_ignore(s32 dmg) { ST.ignore += dmg; }            /* zt.c: an enemy hit, not tool work */
void stats_exp(s32 n)                                        /* EXP gained (zt.c: a defeated animal) */
{
    u8 *g = *(u8 **)0x803491CC;
    if (!ready(g) || n <= 0) return;
    CNT(g, C_EXP) += n; ST.gained += n;
}
static s32 event_free(void)
{
    u8 *ev = EVMGR;
    return OK(ev) && *(s32 *)(ev + 0x680) == -1 && !*(s32 *)(ev + 0x58C) && CONTROL == 1;
}
void stats_frame(u8 *g, s32 map, volatile u32 *held, volatile u32 *press, s32 busy)
{
    s32 cur, d, *pts;
    ST.magic = 0x53544154u;
    if (!OK(g)) return;
    if (CNT(g, C_MAGIC) != (s32)ST_MAGIC) {                  /* a save without stats: start at Lv 1 */
        s32 i; for (i = C_EXP; i <= C_PTS; i++) CNT(g, i) = 0;
        CNT(g, C_LV) = 1; CNT(g, C_MAGIC) = (s32)ST_MAGIC; ST.last = -1; ST.lastfull = -1;
    }
    pts = &CNT(g, C_PTS);
    /* HP: max stamina */
    *(s32 *)(g + 0x11B88) = 100000 + 10000 * CNT(g, C_HP);
    /* tool work: stamina drops (not enemy hits) -> EXP, End refunds part of it */
    cur = *(s32 *)(g + 0x11B84);
    if (busy == 2) { ST.last = cur; ST.ignore = 0; ST.lastfull = *(s32 *)(g + 0x11B94); return; }   /* collapsing: zt.c owns stamina */
    if (ST.last >= 0) {
        d = ST.last - cur;
        if (d > 0 && ST.ignore > 0) { s32 k = d < ST.ignore ? d : ST.ignore; d -= k; ST.ignore -= k; }
        if (d > 0 && d < 30000) {
            s32 back = d * 2 * CNT(g, C_END) / 100;
            if (back > 0) { cur += back; *(s32 *)(g + 0x11B84) = cur; ST.refund += back; }
            {   /* work, not stamina: the game scales tool cost by its own tool level (func_8004BE3C: category ctrl+0x160 1 ->
                   level +0x2E, 2 -> +0x32, x (3450 - 650 L) / 400 = x7 at L1 .. x0.5 at L5); undo that, or EXP would fall 14x */
                u8 *c = g + 0x11B80; s32 cat = *(s32 *)(c + 0x160), lv = cat == 1 ? c[0x2E] : cat == 2 ? c[0x32] : 0;
                if (lv >= 1 && lv <= 5) ST.acc += d * 400 / (3450 - 650 * lv); else ST.acc += d;
            }
            if (ST.acc >= 33) { CNT(g, C_EXP) += ST.acc / 33; ST.gained += ST.acc / 33; ST.acc %= 33; }   /* stats3: x3 (~1 level per bar early) */
        }
    }
    ST.last = cur; ST.ignore = 0;
    /* End: hunger (fullness +0x11B94) drops slower */
    {
        s32 full = *(s32 *)(g + 0x11B94);
        if (ST.lastfull >= 0) {
            s32 df = ST.lastfull - full;
            if (df > 0 && df < 1000) { full += df * 25 * CNT(g, C_END) / 1000; *(s32 *)(g + 0x11B94) = full; }
        }
        ST.lastfull = full;
    }
    /* levels */
    if (CNT(g, C_LV) < 1) CNT(g, C_LV) = 1;
    while (CNT(g, C_EXP) >= need(CNT(g, C_LV))) {
        CNT(g, C_EXP) -= need(CNT(g, C_LV)); CNT(g, C_LV)++; (*pts)++;
        skill_levelup();
        ST.cool = 80;                                           /* the pop-up (75 frames), then the menu (stats5: was 150) */
    }
    if (ST.cool > 0) ST.cool--;
    /* the level-up menu (event 410) */
    if (ST.menu == 1) {                                     /* stats5: wait until it is really running (it starts a frame or more
                                                               later; stats4 took that for 'ended', so the answer was lost and the
                                                               menu came back for ever) */
        u8 *ev = EVMGR;
        if (OK(ev) && *(s32 *)(ev + 0x680) != -1) ST.menu = 2;
        else if (++ST.wait > 300) { ST.menu = 0; ST.wait = 0; }   /* never started: try again later */
        return;
    }
    if (ST.menu == 2) {
        u8 *ev = EVMGR;
        if (OK(ev) && *(s32 *)(ev + 0x680) == -1 && !*(s32 *)(ev + 0x58C)) {   /* the event has ended */
            s32 v = CNT(g, C_ANS), k = v > 4 ? v / 128 : v, *st = 0;
            if (k >= 1 && k <= 4) {
                st = &CNT(g, C_HP + k - 1);
                if (*st < STAT_MAX && *pts > 0) { (*st)++; (*pts)--; }
            }
            CNT(g, C_ANS) = 0; ST.menu = 0; ST.wait = 0; ST.cool = 30;
        }
        return;
    }
    if (CNT(g, C_ANS) && *pts > 0) {                       /* an answer stored but not applied yet (e.g. a reload) */
        s32 v = CNT(g, C_ANS), k = v > 4 ? v / 128 : v;
        if (k >= 1 && k <= 4 && CNT(g, C_HP + k - 1) < STAT_MAX) { CNT(g, C_HP + k - 1)++; (*pts)--; }
        CNT(g, C_ANS) = 0;
    }
    if (*pts > 0 && !busy && !ST.cool && map >= 0 && event_free()) {
        u8 *mm = MSGMGR;
        if (CNT(g, C_HP) >= STAT_MAX && CNT(g, C_PWR) >= STAT_MAX && CNT(g, C_END) >= STAT_MAX && CNT(g, C_LCK) >= STAT_MAX) { *pts = 0; return; }
        if (OK(mm)) msg_num(mm, 0, CNT(g, C_LV));
        CNT(g, C_ANS) = 0; ST.menu = 1; ST.wait = 0;
        event_start(EVMGR, EV_LVUP, 0, 0);
        return;
    }
    /* the stats view: Z + D-pad Up */
    if ((*held & 0x10u) && (*press & 0x08u) && !busy && map >= 0 && event_free()) {
        u8 *mm = MSGMGR;
        *press &= ~0x08u;
        if (OK(mm)) {
            msg_num(mm, 0, CNT(g, C_LV)); msg_num(mm, 1, CNT(g, C_EXP)); msg_num(mm, 2, need(CNT(g, C_LV)));
            msg_num(mm, 3, CNT(g, C_HP)); msg_num(mm, 4, CNT(g, C_PWR)); msg_num(mm, 5, CNT(g, C_END)); msg_num(mm, 6, CNT(g, C_LCK));
            event_start(EVMGR, EV_STATS, 0, 0);
        }
    }
}
