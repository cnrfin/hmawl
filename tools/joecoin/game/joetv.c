/* $JOE Coin Daily: TV channel 3 shows the day's $JOE price instead of the entertainment programs.
   func_8008E298 (channel 3's caption builder, called only by the TV scene in wlp2) is replaced by
   joe_tv (hook: b pm_tv_stub at its first instruction). The price is a pure function of a seed and
   the day number (clock / 864000), so it never changes on reload; the formula and settings match
   tools/joecoin/joe_market.html. The day's picture (tv-console2.tpl images 14-20, appended to the
   file) is copied over channel 3's pictures (1, 2, 3, 6), so whichever one the program uses shows it. */
typedef unsigned int u32;
typedef int s32;
typedef unsigned short u16;
typedef unsigned char u8;

#define F(addr, ret, args) ((ret (*) args)(addr))
#define str_set        F(0x800FCBB8, void, (void *, const u8 *))
#define DCFlushRange   F(0x801B23C8, void, (void *, u32))
#define GXInvalidateTexAll F(0x801D03B4, void, (void))
#define CLOCK       (**(u32 **)0x80349218)        /* tenths of a second since the start */
#define T_DAY       864000u

#define SEED     1890u
#define BASE_LN  3.91202300543f    /* ln 50 G */
#define GROW_LN  0.55961578794f    /* ln 1.75 per year */
#define VOL      0.60f
#define DAILY    0.12f
#define DIP      0.50f
#define PUMP_P   (3.0f / 40.0f)

__attribute__((noinline)) static u32 h32(u32 a, u32 b)
{
    u32 x = (a * 0x9E3779B1u) ^ ((b + 0x7F4A7C15u) * 0x85EBCA77u);
    x ^= x >> 15; x *= 0x2C1B3C6Du; x ^= x >> 12; x *= 0x297A2D39u; x ^= x >> 15;
    return x;
}
__attribute__((noinline)) static float uni(u32 n, u32 k) { return (float)h32(SEED ^ (k * 0x632BE5ABu), n) * (1.0f / 4294967296.0f); }
__attribute__((noinline)) static float vnoise(float x, u32 k)
{
    u32 i = (u32)x; float f = x - (float)i, w = f * f * (3.0f - 2.0f * f);
    return (uni(i, k) * (1.0f - w) + uni(i + 1, k) * w) * 2.0f - 1.0f;
}
typedef union { float f; u32 u; } FU;
__attribute__((noinline)) static float flog(float x)
{
    FU v; v.f = x; s32 e = (s32)((v.u >> 23) & 255) - 127;
    v.u = (v.u & 0x007FFFFFu) | 0x3F800000u;                      /* mantissa in [1, 2) */
    float t = (v.f - 1.0f) / (v.f + 1.0f), t2 = t * t;
    return (float)e * 0.69314718f + 2.0f * t * (1.0f + t2 * (1.0f / 3 + t2 * (1.0f / 5 + t2 * (1.0f / 7 + t2 * (1.0f / 9)))));
}
__attribute__((noinline)) static float fexp(float x)
{
    float k = x * 1.44269504f; s32 n = (s32)(k + (k >= 0 ? 0.5f : -0.5f));
    float r = x - (float)n * 0.69314718f, s = 1.0f, term = 1.0f;
    for (s32 i = 1; i < 9; i++) { term *= r / (float)i; s += term; }
    FU v; v.u = (u32)(n + 127) << 23;
    return s * v.f;
}
static const float SIN11[10] = { 0.28173256f, 0.54064082f, 0.75574957f, 0.90963200f, 0.98982144f,
                                 0.98982144f, 0.90963200f, 0.75574957f, 0.54064082f, 0.28173256f };
static s32 event(u32 t)                                 /* 1 pump, -1 dump, 0 none */
{
    float r = uni(t, 4);
    return r < PUMP_P / 2 ? 1 : r < PUMP_P ? -1 : 0;
}
__attribute__((noinline)) static s32 price(u32 t)
{
    u32 season = (t / 10) % 4, d = t % 10;
    float lg = BASE_LN + GROW_LN * (float)t / 40.0f;
    lg += VOL * (0.65f * vnoise((float)t / 12.0f, 1) + 0.35f * vnoise((float)t / 4.0f, 2));
    lg += DAILY * (uni(t, 3) * 2.0f - 1.0f);
    if (season == 3) lg += flog(1.0f - DIP * (0.5f + 0.5f * SIN11[d]));
    if (season == 0 && t >= 40) lg += flog(1.0f - DIP * 0.5f * (1.0f - (float)d / 9.0f));
    s32 ev = event(t);
    if (ev > 0) lg += flog(2.0f + uni(t, 5));
    else if (ev < 0) lg += flog(0.3f + 0.2f * uni(t, 5));
    s32 p = (s32)(fexp(lg) + 0.5f);
    return p < 5 ? 5 : p > 9999 ? 9999 : p;
}
static s32 joe_today(u32 t)
{
    u32 year = t / 40, season = (t / 10) % 4, day = t % 10 + 1, k = year * 4 + season;
    static const u8 early[4] = { 1, 2, 4, 5 }, late[3] = { 6, 9, 10 };
    if (season == 3) return 0;
    return day == early[h32(SEED ^ 0xA5A5u, k) % 4] || day == late[h32(SEED ^ 0x5A5Au, k) % 3];
}

/* ---- text: ASCII -> the game's message bytes ('|' = wait for A) */
static u8 msg[400];
static u32 mlen;
__attribute__((noinline)) static void put2(u32 g) { msg[mlen++] = (u8)(g >> 8); msg[mlen++] = (u8)g; }
static void puts_(const char *s)
{
    for (; *s; s++) {
        char c = *s;
        if (c >= 'A' && c <= 'Z') put2(0x800B + c - 'A');
        else if (c >= 'a' && c <= 'z') put2(0x80D8 + c - 'a');
        else if (c >= '0' && c <= '9') put2(0x8000 + c - '0');
        else if (c == ' ') msg[mlen++] = 0x02;
        else if (c == '\n') msg[mlen++] = 0x01;
        else if (c == '|') msg[mlen++] = 0x30;
        else if (c == '.') put2(0x80C8);
        else if (c == '!') put2(0x80CB);
        else if (c == '\'') put2(0x80F2);
        else if (c == '+') put2(0x80C6);
        else if (c == '%') put2(0x80D7);
        else if (c == '$') put2(0x80FD);
        else if (c == '-') put2(0x800A);
    }
}
static void putn(s32 n)
{
    char b[12]; s32 i = 11; b[i] = 0;
    if (n == 0) b[--i] = '0';
    while (n > 0) { b[--i] = '0' + n % 10; n /= 10; }
    puts_(b + i);
}

/* ---- picture */
#define TPL_N      21
#define PIC_BYTES  (192 * 144 / 2)
static u8 *tpl;
__attribute__((noinline)) static u8 *pic(u8 *t, s32 i)
{
    u8 *h = *(u8 **)(t + 12 + 8 * i);
    if ((u32)h < 0x80000000u || (u32)h >= 0x817FFFE0u || ((u32)h & 3)) return 0;
    return *(u16 *)h == 144 && *(u16 *)(h + 2) == 192 && *(u32 *)(h + 4) == 14 && *(u32 *)(h + 8) >= 0x80000000u && *(u32 *)(h + 8) < 0x817F0000u ? *(u8 **)(h + 8) : 0;
}
static s32 is_tv_tpl(u8 *t)
{
    return *(u32 *)t == 0xFFFFFFFFu && *(u32 *)(t + 4) == TPL_N && *(u32 *)(t + 8) == (u32)(t + 12)
        && pic(t, 6) && pic(t, 14) && pic(t, 20);
}
static void show_picture(s32 k)
{
    static const u8 dst[4] = { 1, 2, 3, 6 };
    if (!tpl || !is_tv_tpl(tpl)) {                  /* the bound file: magic -> 0xFFFFFFFF, offsets -> pointers */
        tpl = 0;
        for (u8 *p = (u8 *)0x80364000; p < (u8 *)0x81800000; p += 32)
            if (is_tv_tpl(p)) { tpl = p; break; }
        if (!tpl) return;
    }
    /* copy every time: turning the TV off and on reloads the original pictures, often at the same address */
    u8 *src = pic(tpl, 14 + k);
    for (s32 j = 0; j < 4; j++) {
        u8 *d = pic(tpl, dst[j]); u32 *a = (u32 *)d, *b = (u32 *)src;
        for (u32 i = 0; i < PIC_BYTES / 4; i++) a[i] = b[i];
        DCFlushRange(d, PIC_BYTES);
    }
    GXInvalidateTexAll();
}

enum { P_BACK, P_JOEVER, P_LIL, P_HODL, P_CRAB, P_WINTER, P_TOWN };
void *joe_tv(void *prog, void *str)
{
    u32 t = CLOCK / T_DAY, season = (t / 10) % 4;
    s32 p = price(t), y = t ? price(t - 1) : p, ev = event(t), joe = joe_today(t);
    s32 chg = (s32)((float)(p - y) * 100.0f / (float)y + (p >= y ? 0.5f : -0.5f));
    s32 k;
    mlen = 0;
    puts_("$JOE Coin Daily\n....................|\n1 $JOE is worth\n"); putn(p); puts_("G today.\n");
    if (chg >= 0) puts_("+"); else { puts_("-"); chg = -chg; }
    putn(chg); puts_("% since yesterday|\n");
    if (season == 3)      { puts_("Crypto winter. Joe\nis hibernating.\nHODL."); k = P_WINTER; }
    else if (ev > 0)      { puts_("We're JOE BACK!"); k = P_BACK; }
    else if (ev < 0)      { puts_("It's so Joever.."); k = P_JOEVER; }
    else if (chg >= 8 && p > y) { puts_("$JOE doing a lil\nsomething.."); k = P_LIL; }
    else if (chg >= 8)    { puts_("Just a dip. HODL."); k = P_HODL; }
    else                  { puts_("Crab market today."); k = P_CRAB; }
    if (joe) { puts_("|\nJoe is in town today!"); if (ev == 0) k = P_TOWN; }
    msg[mlen++] = 0;
    show_picture(k);
    str_set(str, msg);
    (void)prog;
    return str;
}

/* ---- dig site: the $JOE coin halves every chapter (10%, 5%, 2.5%, 1.25%, ...)
   The dig table (lbl_802928C8: 18 rows of item u32, group u16, weight u16, chapter mask u8, repeatable u8)
   is read when the dig site is set up: each row open in this chapter (mask bit) gets weight / sum.
   Every frame the other rows get their original weight x 100 and the coin (row 0, item 0x442) the weight
   that makes its share exactly the chapter's target among the rows open in that chapter. */
#define DIG_TAB   ((u8 *)0x802928C8)
#define chapter_of F(0x8000FEE8, s32, (void *))
static u16 dig_base[18];
void joe_dig_frame(void)
{
    static const float share[6] = { 0.10f, 0.05f, 0.025f, 0.0125f, 0.00625f, 0.003125f };
    void *clk = *(void **)0x80349218;
    if (!clk || *(u32 *)DIG_TAB != 0x442) return;
    if (!dig_base[1]) for (s32 i = 0; i < 18; i++) dig_base[i] = *(u16 *)(DIG_TAB + 12 * i + 6);
    s32 ch = chapter_of(clk); if (ch < 0) ch = 0; if (ch > 5) ch = 5;
    u32 others = 0;
    for (s32 i = 1; i < 18; i++) {
        u8 *r = DIG_TAB + 12 * i;
        *(u16 *)(r + 6) = (u16)(dig_base[i] * 100);
        if (r[8] >> ch & 1) others += dig_base[i] * 100;
    }
    float p = share[ch];
    *(u16 *)(DIG_TAB + 6) = (u16)((float)others * p / (1.0f - p) + 0.5f);
}

/* ---- villagers hate the $JOE coin
   func_80117B10(villager, record, &group, &line) picks a villager's talk line for a talk record (the
   villager's NPC_NormalTalk table, 78-byte records); the held-item chain sends the coin's talk class
   (item flags bit 20) to record 0x3E, shared with every dig-site find. pm_talk_stub wraps it: when the
   record is 0x3E and the player holds the coin (0x442), the line becomes that villager's own dislike
   line (no give-it-to-me prompt), the "may offer a gift" flag 0x80349348 is cleared, and the villager
   loses JOE_HATE affection (record +0x28, via the game's setter), once a day per villager. */
#define HELD_ITEM   (*(volatile u16 *)(*(u8 **)0x803491CC + 0x11CC6))
#define GIFT_FLAG   (*(volatile u8 *)0x80349348)
#define villager_rec F(0x8000DC24, u8 *, (u8 *, s32))
#define set_affection F(0x800782D8, s32, (u8 *, s32))
#define JOE_HATE    10
#define G_OTHER     42
static const u16 hate_line[46] = {   /* by message group: that villager's own dislike line; 0 = shared line */
    [0] = 0x3C,  /* badog:   I really hate that. Please try and remember that. */
    [1] = 0x55,  /* bahn:    I don't like that at all. */
    [3] = 0x61,  /* carter:  What's that?? Throw that away. */
    [4] = 0x91,  /* daryl:   I don't want that. */
    [10] = 0x2E, /* ghali:   No matter how much I look at it, I still don't like it. */
    [11] = 0x39, /* godey:   I can't stand that junk. */
    [13] = 0x45, /* gustafa: Get that away from me. */
    [15] = 0x4A, /* kate:    I don't want that. */
    [17] = 0x31, /* kris:    I really don't like that at all. */
    [19] = 0x87, /* mash:    That's unusual... I'm not interested in it, though. */
    [20] = 0x49, /* moi:     I don't want t-that... */
    [23] = 0x1A3,/* nami:    Okay, okay. You keep it for yourself, okay? */
    [24] = 0x23, /* nina:    No matter which way I look at it, I don't like it. Sorry dear. */
    [25] = 0x2A, /* pasaran: Can you please get rid of that? Throw it into the Sun or something... */
    [27] = 0x2E, /* romana:  I don't want that. */
    [35] = 0xB0, /* takakura: Sorry, I don't like that very much. */
    [37] = 0x78, /* vesta:   I'm not interested. */
};
static u8 hate_day_seen[64];
static u32 hate_day = 0xFFFFFFFFu;
s32 joe_talk_post(s32 who, s32 rec, s32 *grp, s32 *msg, s32 ret)
{
    if (rec != 0x3E || HELD_ITEM != 0x442) return ret;
    s32 g = *grp;
    if (g >= 0 && g < 46 && hate_line[g]) *msg = hate_line[g];
    else { *msg = (g == 14 || g == 18) ? 0x42 : 0x43; *grp = G_OTHER; }   /* Yuck... Go away. / What is that?? Throw it away. */
    GIFT_FLAG = 0;
    u32 day = CLOCK / T_DAY;
    if (day != hate_day) { for (s32 i = 0; i < 64; i++) hate_day_seen[i] = 0; hate_day = day; }
    if (who >= 0 && who < 64 && !hate_day_seen[who]) {
        u8 *r = villager_rec(*(u8 **)0x803491CC, who);
        if (r) {
            s32 a = *(short *)(r + 0x28) - JOE_HATE;
            set_affection(r, a < 0 ? 0 : a);
        }
        hate_day_seen[who] = 1;
    }
    return ret;
}

/* Van day log (van test 5): every frame, the stall Van's daily plan byte (villager 0x24 record +0x24:
   1/2 = works the stall, 4/5 = away) is logged when the day or the byte changes:
   van_log = {magic 'VANL', n, then 64 rows of (day, tenths of the day, plan, record +0x25..+0x27)}. */
struct van_row { u32 day, tod; u8 plan, b25, b26, b27; };
struct { u32 magic, n; struct van_row row[64]; } van_log;
s32 pick_log(u8 *obj, s32 res) { return res; }
void van_frame(u8 *g)
{
    static u32 last_day = 0xFFFFFFFFu; static u8 last_plan = 0xFF;
    u8 *r = villager_rec(g, 0x24);
    u32 day = CLOCK / T_DAY;
    if (!r || *(u16 *)(r + 4) != 0x24) return;
    if (day != last_day || r[0x24] != last_plan) {
        struct van_row *w = &van_log.row[van_log.n & 63];
        w->day = day; w->tod = CLOCK % T_DAY; w->plan = r[0x24]; w->b25 = r[0x25]; w->b26 = r[0x26]; w->b27 = r[0x27];
        van_log.magic = 0x56414E4C; van_log.n++;
        last_day = day; last_plan = r[0x24];
    }
}

/* bench sit test 11 probe: every villager daily plan (func_80060EF8) is logged:
   plan_log_buf = {magic 'PLAN', n, 64 rows of (day, tenths of the day, villager id, Takakura only: shipping
   containers game+0x111BC / +0x1119C non-empty (func_80053234), job flags game+0x11B48..0x11B4F before planning)} */
#define ship_has F(0x80053234, s32, (u8 *))
struct plan_row { u32 day, tod; short id; u8 c1, c2; u8 jobs[8]; };
struct { u32 magic, n; struct plan_row row[64]; } plan_log_buf;
void plan_log(u8 *st)
{
    u8 *g = *(u8 **)0x803491CC, *v = *(u8 **)(st + 8);
    struct plan_row *r = &plan_log_buf.row[plan_log_buf.n & 63];
    s32 k;
    r->day = CLOCK / T_DAY; r->tod = CLOCK % T_DAY;
    r->id = v ? *(s32 *)(v + 0xBC) : -1;
    r->c1 = r->c2 = 0xEE;
    if (r->id == 7) { r->c1 = ship_has(g + 0x111BC) & 0xFF; r->c2 = ship_has(g + 0x1119C) & 0xFF; }
    for (k = 0; k < 8; k++) r->jobs[k] = g[0x11B48 + k];
    plan_log_buf.magic = 0x504C414E; plan_log_buf.n++;
}
