/* Tool skill on the HUD (pm.bin). While the player holds a tool with a proficiency pool, a row under
   the food bar shows the pool's icon (tools-tab hoe = field tools, milk-can tab = animal tools) and its
   level as 5 gems; when a level goes up, "Field up" / "Animal up" pops up above the player for a
   moment with a chime. Everything is quads appended to opguide.agc element 7 (see skill_hud.h); they
   are rewritten here every frame in the loaded agc ([0x80349110]).
   Pools (ctrl = game+0x11B80): animal tools +0x2C (milkers, shears, clippers), field tools +0x30
   (hoes, sickles, watering cans, the Cursed Axe); u16 points, level = points / 500 + 1, max 5 (the
   game's own level byte only updates when a tool is used). */

typedef unsigned int u32;
typedef int s32;
typedef short s16;
typedef unsigned short u16;
typedef unsigned char u8;

#include "skill_hud.h"

#define F(addr, ret, args) ((ret (*) args)(addr))
#define sfx_play      F(0x8012A52C, s32, (u8 *, s32, s32))
#define music_volume  F(0x80189DD8, void, (u8 *, s32, s32))   /* (obj, 0..127, ms): sequenced music only */
#define MUSIC_OBJ     (*(u8 **)(*(u8 **)0x803491E4 + 0x4C))
#define MUSIC_TARGET(o) (*((o) + 0x3D8 + 0xA))     /* its fader: the last requested volume */
#define DUCK_VOL      0
#define DUCK_MS       400
#define DUCK_FRAMES   96                         /* the jingle is 3.7 s; come back as its last note rings */
#define BACK_MS       1200
#define AGC           (*(u8 **)0x80349110)
#define SLIDE         (*(s32 *)0x8000507C)        /* HUD slide (0 shown .. 110 hidden), from the HUD code */
#define QUAD(a, off, k) ((a) + (off) + 0x2C * (k))
#define POINTS_PER_LV 500
#define POP_FRAMES    75
#define POP_IN        8
#define POP_OUT       14
#define POP_Y         (-30)                      /* screen offset from the centre: just above the player */
#define POP_SCALE     1.5f
#define SFX_LEVEL_UP  433                        /* the "Breeze" sting (added to GAME_ALL) */
#define YELLOW        0xFFE25A00u

static struct {
    s32 lv[2];                                   /* last level seen per pool (0 = not yet seen) */
    s32 pop, pop_pool;                           /* frames left of the pop-up, and which pool */
    s32 duck, saved;                             /* frames until the music comes back, its volume before */
} K;

static s32 pool_of(s32 item)                     /* 0 field, 1 animal, -1 none */
{
    if ((item >= 0x4DE && item <= 0x4F1) || item == 0x502) return 0;
    if (item >= 0x4F6 && item <= 0x4FD) return 1;
    return -1;
}

static s32 level_of(u8 *g, s32 pool)
{
    s32 lv = *(u16 *)(g + 0x11B80 + (pool ? 0x2C : 0x30)) / POINTS_PER_LV + 1;
    return lv > 5 ? 5 : lv;
}

static void set_quad(u8 *q, s32 tex, s32 x0, s32 y0, s32 x1, s32 y1, const float *uv, u32 rgba)
{
    s32 k;
    *(u32 *)q = tex;
    *(s16 *)(q + 4) = x0; *(s16 *)(q + 6) = y0; *(s16 *)(q + 8) = x1; *(s16 *)(q + 10) = y1;
    for (k = 0; k < 4; k++) *(u32 *)(q + 0xC + 4 * k) = rgba;
    if (uv) for (k = 0; k < 4; k++) *(float *)(q + 0x1C + 4 * k) = uv[k];
}

static void set_alpha(u8 *q, u32 rgba)
{
    s32 k;
    for (k = 0; k < 4; k++) *(u32 *)(q + 0xC + 4 * k) = rgba;
}

static void pop_layout(u8 *a, s32 alpha, s32 rise)
{
    const struct glyph *w = K.pop_pool ? WORD1 : WORD0;
    s32 n = K.pop_pool ? WORD1_N : WORD0_N, i, x, total = 0, e7y = *(s16 *)(a + AGC_E7_Y);
    s32 h = (s32)(21 * POP_SCALE), y;
    u32 col = YELLOW | (u32)alpha;
    for (i = 0; i < n; i++) total += w[i].w ? (s32)(w[i].w * POP_SCALE) + 1 : 8;
    x = -total / 2 - E7_X;                                   /* element 7 coordinates */
    y = POP_Y - rise - e7y;
    for (i = 0; i < POP_QUADS; i++) {
        u8 *q = QUAD(a, AGC_POP_Q, i);
        if (i < n && w[i].w) {
            float uv[4]; s32 gw = (s32)(w[i].w * POP_SCALE);
            uv[0] = w[i].u0; uv[1] = w[i].v0; uv[2] = w[i].u1; uv[3] = w[i].v1;
            set_quad(q, 3, x, y, x + gw, y + h, uv, col);
            x += gw + 1;
        } else if (i < n) {                                   /* space */
            set_alpha(q, 0xFFFFFF00u); x += 8;
        } else set_alpha(q, 0xFFFFFF00u);
    }
}

void skill_frame(u8 *g, u32 pad_held, u32 pad_press)
{
    u8 *a = AGC;
    s32 item, pool, lv, k, alpha, slide;
    if ((u32)a < 0x80000000u || (u32)a >= 0x81800000u) return;
    if (*(u32 *)a != 0xC1C7C3C6u || *(u32 *)(a + AGC_E7_COUNT) != E7_COUNT) return;   /* our opguide.agc */

    if ((pad_held & 0x10) && (pad_press & 0x800)) {          /* test: Z + Y = +250 field-tool points */
        u16 *p = (u16 *)(g + 0x11B80 + 0x30);
        *p = *p > 65535 - 250 ? 65535 : *p + 250;
    }
    for (k = 0; k < 2; k++) {                                /* level-ups (no pop-up for the first look) */
        lv = level_of(g, k);
        if (K.lv[k] && lv > K.lv[k]) {
            K.pop = POP_FRAMES; K.pop_pool = k;
            sfx_play(*(u8 **)0x803491E4, SFX_LEVEL_UP, 0);
            {
                u8 *m = MUSIC_OBJ;                       /* fade the music out under the jingle */
                if ((u32)m >= 0x80000000u && (u32)m < 0x81800000u) {
                    if (!K.duck) K.saved = MUSIC_TARGET(m);
                    music_volume(m, DUCK_VOL, DUCK_MS);
                    K.duck = DUCK_FRAMES;
                }
            }
        }
        K.lv[k] = lv;
    }

    if (K.duck > 0 && --K.duck == 0) {                   /* bring the music back, unless the game */
        u8 *m = MUSIC_OBJ;                               /* has asked for a volume of its own since */
        if ((u32)m >= 0x80000000u && (u32)m < 0x81800000u && MUSIC_TARGET(m) == DUCK_VOL)
            music_volume(m, K.saved, BACK_MS);
    }
    item = *(s32 *)(g + 0x11CC4); pool = pool_of(item);
    slide = SLIDE; if (slide < 0) slide = 0;
    alpha = slide >= 90 ? 0 : 0xF0 - slide * 0xF0 / 90;     /* fades as the bars slide away */
    if (pool < 0) alpha = 0;
    lv = pool < 0 ? 0 : level_of(g, pool);
    {
        u8 *q = QUAD(a, AGC_ROW_Q, 0);
        float *uv = (float *)(q + 0x1C); const float *src = pool == 1 ? UV_CAN : UV_HOE;
        for (k = 0; k < 4; k++) uv[k] = src[k];
        set_alpha(q, 0xFFFFFF00u | (u32)alpha);
        for (k = 0; k < 5; k++) {
            u8 *gq = QUAD(a, AGC_ROW_Q, 1 + k);
            float *gu = (float *)(gq + 0x1C); const float *gs = k < lv ? UV_GEMY : UV_GEME; s32 j;
            for (j = 0; j < 4; j++) gu[j] = gs[j];
            set_alpha(gq, 0xFFFFFF00u | (u32)alpha);
        }
    }

    if (K.pop > 0) {
        s32 t = POP_FRAMES - K.pop, al = 0xF0;
        if (t < POP_IN) al = 0xF0 * t / POP_IN;
        if (K.pop < POP_OUT) al = 0xF0 * K.pop / POP_OUT;
        pop_layout(a, al, t / 4);
        K.pop--;
    } else {
        for (k = 0; k < POP_QUADS; k++) set_alpha(QUAD(a, AGC_POP_Q, k), 0xFFFFFF00u);
    }
}
