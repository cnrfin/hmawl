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
typedef short s16;
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
#define SH_DATA
#include "stat_hud.h"
struct { u32 magic; s32 ignore, acc, last, lastfull, menu, cool, gained, refund, wait, fish_set, r_exp, r_gold, r_wait, r_open, tl_seen, tl[2], tacc[2], twin, pend, page, lastmap, drift; } ST;   /* 'STAT' (dump) */

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
/* step 4: a defeated animal's reward (zt.c). Gold first, in the game's info box with the cash sound; its EXP is only
   added once that box has closed, so "Level up!" and the stat menu always come after it, never together.
   gold2: the box is opened by the game's own player state 0x2A (as the R item description: file player+0x14C0, msg
   +0x14C4; it opens func_801020E4 mode 1, holds the player and waits for A). gold1 opened the box directly from
   here: it showed, then closed by itself at once. */
#define pl_state  F(0x80031D7C, void, (u8 *, s32))
#define ST_MSG    0x2A
#define ST_FREE   1
extern u8 *pm_player;
#define gold_add  F(0x80113234, void, (u8 *, s32))
#define sfx_play  F(0x8012A52C, s32, (u8 *, s32, s32))
#define MES_DEBUG 0x32
#define M_GOLD    30                                          /* debug.mes "You found <n0> G!" (build_stats_events.py) */
#define SE_CASH   0xCD                                        /* script command 0xC1's sound */
#define REWARD_WAIT 90                                        /* the defeat animation first */
extern s32 skill_pop_on;
void stats_reward(s32 exp, s32 gold)
{
    if (exp > 0) ST.r_exp += exp;
    if (gold > 0) ST.r_gold += gold;
    ST.r_wait = REWARD_WAIT;
}
static s32 ev_running(void)                             /* lv4: a script event is on: +0x680 (talk events) or +0x58C (ours) */
{
    u8 *ev = EVMGR;
    return OK(ev) && (*(s32 *)(ev + 0x680) != -1 || *(s32 *)(ev + 0x58C));
}
static s32 menu_free(void)                              /* lv2: event_free without +0x58C, for the next level's menu */
{
    u8 *mm = MSGMGR;
    return !ev_running() && CONTROL == 1 && !(OK(mm) && *(s32 *)(mm + 0x48));
}
static s32 event_free(void)
{
    u8 *ev = EVMGR;
    u8 *mm = MSGMGR;
    return OK(ev) && *(s32 *)(ev + 0x680) == -1 && !*(s32 *)(ev + 0x58C) && CONTROL == 1 &&
           !(OK(mm) && *(s32 *)(mm + 0x48));                 /* gold3: and no message box up */
}

/* step 3: the stat HUD (tools/hud/build_stat_hud.py: quads appended to opguide.agc element 7, rewritten here) */
#define AGC (*(u8 **)0x80349110)
static void sq_set(u8 *q, s32 x0, s32 w, s32 h, const float *uv, float ufrac)
{
    *(s16 *)(q + 4) = x0; *(s16 *)(q + 8) = x0 + w;
    if (h >= 0) *(s16 *)(q + 10) = *(s16 *)(q + 6) + h;
    if (uv) {
        float *u = (float *)(q + 0x1C);
        u[0] = uv[0]; u[1] = uv[1]; u[2] = uv[0] + (uv[2] - uv[0]) * ufrac; u[3] = uv[3];
    }
}
static void sq_fill(u8 *q, s32 full_w, s32 num, s32 den, const float *uv)   /* a bar cropped to num / den */
{
    s32 w;
    if (num < 0) num = 0;
    if (num > den) num = den;
    w = full_w * num / den;
    sq_set(q, *(s16 *)(q + 4), w, -1, uv, (float)num / (float)den);
}
static s32 sq_number(u8 *q, s32 nq, s32 x, s32 v, s32 sc, s32 pct)          /* digits (+ '%'); the rest zero width */
{
    s32 d[4], n = 0, i, h = 21 * sc / 100;
    if (v < 0) v = 0;
    do { d[n++] = v % 10; v /= 10; } while (v && n < 3);
    for (i = 0; i < nq; i++) {
        u8 *qq = q + 0x2C * i;
        s32 k = i < n ? d[n - 1 - i] : (pct && i == n) ? 10 : -1;
        if (k < 0) { sq_set(qq, x, 0, -1, 0, 1); continue; }
        *(s16 *)(qq + 6) = *(s16 *)(q + 6);
        sq_set(qq, x, SH_DIG_W[k] * sc / 100, h, SH_DIG[k], 1.0f);
        x += SH_DIG_W[k] * sc / 100 - 1;
    }
    return x;
}
static void stats_hud(u8 *g)
{
    static const float UV_GREEN[4] = {0.0f, 0.1875f, 0.65625f, 0.3125f};
    static const float UV_YELLOW[4] = {0.0f, 0.333333f, 0.65625f, 0.458333f};
    static const float UV_RED[4] = {0.0f, 0.479167f, 0.65625f, 0.604167f};
    u8 *a = AGC;
    s32 cur, max, k;
    if (!OK(a) || *(u32 *)a != 0xC1C7C3C6u || *(u32 *)(a + 0xE88) != E7_TOTAL) return;   /* our opguide.agc */
    cur = *(s32 *)(g + 0x11B84); max = *(s32 *)(g + 0x11B88);
    /* HP: 100000 per layer (green, blue, purple); the top layer empties first. Green alone turns yellow / red when low (as v03) */
    sq_fill(a + SQ_GREEN, SH_BAR_W, cur, 100000, cur > 50000 ? UV_GREEN : cur > 25000 ? UV_YELLOW : UV_RED);
    for (k = 1; k <= 2; k++)
        sq_fill(a + (k == 1 ? SQ_BLUE : SQ_PURPLE), SH_BAR_W, max > 100000 * k ? cur - 100000 * k : 0, 100000, k == 1 ? SH_UV_BLUE : SH_UV_PURPLE);
    /* fullness % */
    sq_number(a + SQ_PCT, 4, SH_PCT_X, *(s32 *)(g + 0x11B94) / 13500, SH_PCT_SC, 1);
    /* EXP into the level, and the level */
    if (ready(g)) {
        sq_fill(a + SQ_CYAN, SH_EXP_W, CNT(g, C_EXP), need(CNT(g, C_LV)), SH_UV_CYAN);
        sq_number(a + SQ_LVNUM, 2, SH_LV_X, CNT(g, C_LV), SH_LV_SC, 0);
    }
}
/* step 4: Luck, +5 % per point (x2 at 20).
   Dig site (wlp2.rel, module id 3, loaded when needed; found through the OS module list at 0x800030C8): a dig at a
   spot finds something when 1 + rand % 100 < 30.0 / (digs at that spot + 1) (wlp2 0x2450; 30.0 = .rodata section 4
   +0x50, the roll's bounds 1 / 100 = .data section 5 +0xAD8 / +0xADC). The 30.0 becomes 30 x (1 + 0.05 Luck).
   Fishing (main.dol func_8017346C / func_80173504): species = cumulative weights 0x802C91F8 [species 0-7][water 0-3]
   (s16) against 0..100; the rare ones (weight 1-10) get x (1 + 0.05 Luck), taken from that water's most common
   species. Big vs small: the even fish (table +0x1A weight 1) when 0..lbl_8034895C (100) <= 100 / (w_even + w_odd);
   that bound becomes 100 / (1 + 0.05 Luck). */
#define FISH_W   ((short *)0x802C91F8)
#define FISH_BIG (*(s32 *)0x8034895C)
static const short fish_w0[32] = { 50, 0, 0, 0,  45, 0, 0, 0,  5, 0, 10, 0,  0, 50, 0, 50,
                                   0, 0, 5, 5,   0, 15, 0, 15,  0, 5, 0, 0,  0, 30, 85, 30 };
static void stats_luck(s32 lck)
{
    s32 w, sp, i;
    u32 m = *(u32 *)0x800030C8;
    for (i = 0; i < 16 && OK(m); i++, m = *(u32 *)(m + 4)) {        /* dig site */
        u32 st = *(u32 *)(m + 0x10), ro, da;
        if (*(u32 *)m != 3 || *(u32 *)(m + 0xC) != 21 || !OK(st)) continue;
        ro = *(u32 *)(st + 4 * 8) & ~1u; da = *(u32 *)(st + 5 * 8) & ~1u;
        if (OK(ro) && OK(da) && *(s32 *)(da + 0xAD8) == 1 && *(s32 *)(da + 0xADC) == 100 && *(u32 *)(ro + 0x54) == 0)
            *(float *)(ro + 0x50) = 30.0f + 1.5f * (float)lck;
        break;
    }
    for (i = 0; i < 32; i++) if (FISH_W[i] != fish_w0[i]) break;   /* fishing (once the table is ours, or untouched) */
    if (i < 32 && ST.fish_set != 1) return;
    for (w = 0; w < 4; w++) {
        s32 common = 0, add = 0;
        for (sp = 0; sp < 8; sp++) if (fish_w0[sp * 4 + w] > fish_w0[common * 4 + w]) common = sp;
        for (sp = 0; sp < 8; sp++) {
            s32 v = fish_w0[sp * 4 + w], b = v > 0 && v <= 10 ? (v * 5 * lck + 50) / 100 : 0;
            FISH_W[sp * 4 + w] = (short)(v + b); add += b;
        }
        FISH_W[common * 4 + w] = (short)(fish_w0[common * 4 + w] - add);
    }
    ST.fish_set = 1;
    FISH_BIG = 10000 / (100 + 5 * lck);
}

/* step 4: Attack on the farm - the tool skill pools (ctrl = game+0x11B80: +0x2C animal tools, +0x30 field tools; u16,
   level = pool / 500 + 1, max 5; the level cuts the tools' stamina cost and widens the charge) grow 5 % faster per
   Attack point (x2 at 20): each rise the game makes gets that much on top. */
static void stats_tools(u8 *g, s32 atk)
{
    s32 k;
    for (k = 0; k < 2; k++) {
        unsigned short *p = (unsigned short *)(g + 0x11B80 + (k ? 0x30 : 0x2C));
        s32 cur = *p, d = cur - ST.tl[k];
        if (ST.tl_seen && d > 0 && d < 5000) ST.twin = 40;   /* real tool use (EXP window) */
        if (ST.tl_seen && d > 0 && d < 5000 && atk > 0) {
            ST.tacc[k] += d * 5 * atk;
            if (ST.tacc[k] >= 100) {
                cur += ST.tacc[k] / 100; ST.tacc[k] %= 100;
                if (cur > 60000) cur = 60000;
                *p = (unsigned short)cur;
            }
        }
        ST.tl[k] = cur;
    }
    ST.tl_seen = 1;
}

void stats_frame(u8 *g, s32 map, volatile u32 *held, volatile u32 *press, s32 busy)
{
    s32 cur, d, *pts;
    ST.magic = 0x53544154u;
    if (!OK(g)) return;
    {   /* lv1 (user: Lv / EXP back to 1 after sleeping): the day change (func_8010BF58) adds 1 to every non-zero event
           counter 32..61 (func_8010C078(obj, 0x1F, 0x3E, 0); the game's dev list: 31..62 __COUNTER_COUNTUP_DAY), so 'ST01'
           became 'ST02' and the stats started over. The game itself uses only 32..34 there; ours are 40-62 (Joe 45-47,
           goddess quest 51, $JOE market 52 / 53, these stats 54-62). Now it counts 32..44 only (li r5, 0x3E -> 0x2D at
           0x8010BF8C). */
        /* lv2 (user: reset again after sleeping in the bed): the same call is also in func_8010BEB0 at 0x8010BEE4 (the
           bed's sleep, from a REL), which lv1 missed. Both now. */
        static u32 *const IP[2] = { (u32 *)0x8010BF8C, (u32 *)0x8010BEE4 };
        s32 k;
        for (k = 0; k < 2; k++) {
            u32 *ip = IP[k];
            if (*ip == 0x38A0003Eu) { *ip = 0x38A0002Du; __asm__ volatile("dcbst 0,%0\n\tsync\n\ticbi 0,%0\n\tisync" :: "r"(ip) : "memory"); }
        }
    }
    {   /* lv2: a save the old day change already touched: 'ST01' + k after k days, and every non-zero stat counter + k too
           (zero ones stay zero). Take the k days back instead of starting over. */
        u32 m = (u32)CNT(g, C_MAGIC);
        if (m > ST_MAGIC && m - ST_MAGIC < 2000u) {
            s32 i, dk = (s32)(m - ST_MAGIC);
            for (i = C_EXP; i <= C_PTS; i++) if (CNT(g, i) > 0) { CNT(g, i) -= dk; if (CNT(g, i) < 0) CNT(g, i) = 0; }
            if (CNT(g, C_LV) < 1) CNT(g, C_LV) = 1;
            CNT(g, C_MAGIC) = (s32)ST_MAGIC; ST.drift = dk;
        }
    }
    if (CNT(g, C_MAGIC) != (s32)ST_MAGIC) {                  /* a save without stats: start at Lv 1 */
        s32 i; for (i = C_EXP; i <= C_PTS; i++) CNT(g, i) = 0;
        CNT(g, C_LV) = 1; CNT(g, C_MAGIC) = (s32)ST_MAGIC; ST.last = -1; ST.lastfull = -1;
    }
    pts = &CNT(g, C_PTS);
    /* HP: max stamina */
    *(s32 *)(g + 0x11B88) = 100000 + 10000 * CNT(g, C_HP);
    stats_hud(g);
    if (map != ST.lastmap) { ST.tl_seen = 0; ST.lastmap = map; }     /* not across loads / scene changes */
    stats_tools(g, CNT(g, C_PWR));                                   /* everywhere (the barn too: milking) */
#ifdef LUCK_TEST
    stats_luck(STAT_MAX);                                   /* test build: Luck 20 effects */
#else
    stats_luck(CNT(g, C_LCK));
#endif
    /* tool work: stamina drops (not enemy hits) -> EXP, End refunds part of it */
    cur = *(s32 *)(g + 0x11B84);
    if (busy == 2) { ST.last = cur; ST.ignore = 0; ST.lastfull = *(s32 *)(g + 0x11B94); return; }   /* collapsing: zt.c owns stamina */
    if (ST.last >= 0) {
        d = ST.last - cur;
        if (d > 0 && ST.ignore > 0) { s32 k = d < ST.ignore ? d : ST.ignore; d -= k; ST.ignore -= k; }
        {   /* alien3 / alien4 (user: EXP rose just walking; then the milker gave none): only stamina spent on real tool use
               counts - the game also drains a little stamina from moving. Real use = the hidden tool-skill pools rise
               (stats_tools). A drop counts within 40 frames after a rise; a drop just before one waits up to 40 frames */
            if (d > 0 && !ST.twin) { ST.pend += d; ST.page = 40; d = 0; }
            if (ST.twin > 0 && ST.pend > 0) { d += ST.pend; ST.pend = 0; }
            if (ST.page > 0 && --ST.page == 0) ST.pend = 0;
            if (ST.twin > 0) ST.twin--;
        }
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
    /* a defeat's reward: gold box, then its EXP (levels and menus wait) */
    if (ST.r_open) {
        u8 *mm = MSGMGR, *pl = pm_player;
        s32 up = (OK(mm) && *(s32 *)(mm + 0x48)) || (OK(pl) && *(s32 *)(pl + 0x1364) == ST_MSG);
        if (ST.r_open == 1) {                                /* gold3: the box opens a frame or more after the state change; */
            if (up && OK(mm) && *(s32 *)(mm + 0x48)) ST.r_open = 2;   /* gold2 took that gap for 'closed' (dump 0c6bb71d) */
            else if (++ST.r_wait > 90) ST.r_open = 3;        /* never showed: go on */
            return;
        }
        if (up) return;                                      /* until A closes it */
        ST.r_open = 0; ST.r_wait = 0; ST.cool = 20;
    }
    if (ST.r_gold || ST.r_exp) {
        u8 *mm = MSGMGR;
        if (ST.r_wait > 0) { ST.r_wait--; return; }
        if (ST.r_gold > 0) {
            u8 *pl = pm_player;
            if (busy || map < 0 || skill_pop_on || !event_free() || !OK(mm) || *(s32 *)(mm + 0x48) ||
                !OK(pl) || *(s32 *)(pl + 0x1364) != ST_FREE) return;
            gold_add(g + 0x11A14, ST.r_gold);
            sfx_play(*(u8 **)0x803491E4, SE_CASH, 0);
            msg_num(mm, 0, ST.r_gold);
            *(s32 *)(pl + 0x14C0) = MES_DEBUG; *(s32 *)(pl + 0x14C4) = M_GOLD;
            pl_state(pl, ST_MSG);
            ST.r_gold = 0; ST.r_open = 1; ST.r_wait = 0;
            return;
        }
        CNT(g, C_EXP) += ST.r_exp; ST.gained += ST.r_exp; ST.r_exp = 0;
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
        if (ev_running() || CNT(g, C_ANS)) ST.menu = 2;   /* lv4: our events show as +0x58C, not +0x680 (lv2/lv3 timed out here: 5 s) */
        else if (++ST.wait > 300) { ST.menu = 0; ST.wait = 0; }   /* never started: try again later */
        return;
    }
    if (ST.menu == 2) {
        if (CNT(g, C_ANS)) {                                /* lv3: the menu loops in one event (patch_lvup_loop.py): apply
                                                               each answer now, set 61 back to 0 and the next level's number */
            s32 v = CNT(g, C_ANS), k = v > 4 ? v / 128 : v;
            if (k >= 1 && k <= 4 && CNT(g, C_HP + k - 1) < STAT_MAX && *pts > 0) { CNT(g, C_HP + k - 1)++; (*pts)--; }
            if (CNT(g, C_HP) >= STAT_MAX && CNT(g, C_PWR) >= STAT_MAX && CNT(g, C_END) >= STAT_MAX && CNT(g, C_LCK) >= STAT_MAX) *pts = 0;
            if (*pts > 0) { u8 *mm = MSGMGR; if (OK(mm)) msg_num(mm, 0, CNT(g, C_LV) - *pts + 1); }
            CNT(g, C_ANS) = 0;
        }
        if (!ev_running() && !CNT(g, C_ANS)) {              /* the event has ended */
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
    if (*pts > 0 && !busy && !ST.cool && map >= 0 && menu_free()) {
        u8 *mm = MSGMGR;
        if (CNT(g, C_HP) >= STAT_MAX && CNT(g, C_PWR) >= STAT_MAX && CNT(g, C_END) >= STAT_MAX && CNT(g, C_LCK) >= STAT_MAX) { *pts = 0; return; }
        if (OK(mm)) msg_num(mm, 0, CNT(g, C_LV) - *pts + 1);   /* lv1: two levels at once = 'Lvl 2', then 'Lvl 3' (was 3 twice) */
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
