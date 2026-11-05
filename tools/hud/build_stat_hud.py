#!/usr/bin/env python3
"""Step 3 of notes/stats_design.md: the stat HUD. "HP" (HUD font) where the face was, the HP bar (green, then blue and
purple layers for extra max HP), the apple and the fullness in %, "EXP" under "HP" with a thinner cyan EXP bar and a
small "Lvl N" at its end. The farmer's name, the face, the old bars and the tool-skill row go.

usage: build_stat_hud.py commonall.arc.clz OUTDIR      (input: the HUD build with opguide.tpl textures 0-4 and
                                                       element 7 = 37 quads, i.e. build_skill_hud.py's output)
Writes OUTDIR/commonall.arc.clz and OUTDIR/stat_hud.h (offsets and texture coordinates for stats.c).

opguide.tpl: + texture 5 (RGB5A3 256 x 80): digits 0-9 and '%' drawn like the HUD font (the dialogue font at 0.75,
1 px black outline), and the green fill recoloured blue / purple, the thin orange fill recoloured cyan.
opguide.agc: elements 1-6 (v03 bars, apple, face) get 0 quads (v03's main.dol code still writes them: harmless; its
pointer check reads the fill quad's texture 2, which stays); the 12 name quads become transparent (v03 writes only
their x and UVs); STAT_Q new quads are appended to element 7 (its quads are the file's last bytes), so every
existing offset (AGC_ROW_Q / POP / RET) stays. Element 7 coordinates: x from E7_X, y from its base -204 (the slide
moves the element)."""
import os, sys, struct, json, hashlib
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
SCR = '/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/'
sys.path[:0] = [os.path.join(HERE, '..', 'logs'), SCR + 'lumber', SCR + 'font']
import u8arc, tpltool
from build_log_archives import clz_decompress, clz_compress
from i4 import load as font_load
GLYPH = SCR + 'font/glyph_meta.json'
FONT = SCR + 'font/font.tpl'
E7, E7_BASE_Y, NAME_Q, OLD_Q = 7, -204, 12, 37
AW, AH = 256, 80
be = lambda b, o: struct.unpack_from('>I', b, o)[0]

# layout, in HUD coordinates (x -320..320, y -224..224), as agreed in the preview (scratchpad hud3/preview.py)
BX, BY = -254, -200          # HP bar back
EY = BY + 25                 # EXP bar back
HP_X, HP_Y, HP_SC = -291, BY - 4, 0.85
EXP_X, EXP_Y, EXP_SC = -292, EY - 4, 0.54
APPLE = (-77, BY - 6, 26, 26)
PCT_X, PCT_Y, PCT_SC = -50, BY - 2, 0.75
LV_X, LV_Y, LV_SC = BX + 132, EY - 5, 0.55
FONT_SC = 0.75               # tex3 and our digits are drawn at 0.75 (21 px cells)

def glyph(F, code):          # same recipe as the HUD font (scratchpad font/glyphs.py)
    r, c = divmod(code, 42); g = F[r * 24:r * 24 + 24, c * 24:c * 24 + 24]
    g = np.array(Image.fromarray(g).resize((18, 18), Image.LANCZOS)).astype(float) / 255
    pad = np.zeros((21, 21)); pad[1:19, 1:19] = g
    out = np.zeros_like(pad)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            out = np.maximum(out, np.roll(np.roll(pad, dy, 0), dx, 1))
    al = np.clip(np.maximum(out, pad), 0, 1); it = np.clip(pad / np.maximum(al, 1e-6), 0, 1)
    cols = np.where(al.max(0) > 0.15)[0]
    im = Image.fromarray(np.dstack([it * 255] * 3 + [al * 255]).astype(np.uint8), 'RGBA')
    return im.crop((cols.min(), 0, cols.max() + 1, 21))

def rehue(im, hue):
    a = np.array(im); hsv = np.array(Image.fromarray(a[..., :3]).convert('HSV')); hsv[..., 0] = hue
    rgb = np.array(Image.fromarray(hsv, 'HSV').convert('RGB'))
    return Image.fromarray(np.dstack([rgb, a[..., 3]]), 'RGBA')

def main():
    clz, out = sys.argv[1:3]
    u = clz_decompress(open(clz, 'rb').read()); arc = u8arc.read(u); nm = u8arc.names(arc)
    kt, ka = nm['opguide.tpl'], nm['opguide.agc']
    tpl, agc = arc['files'][kt], bytearray(arc['files'][ka])
    T = tpltool.read(tpl); assert len(T) == 5, 'expected the HUD build with textures 0-4'
    t2 = Image.fromarray(tpltool.decode(tpl, T[2])).convert('RGBA')
    crop = lambda im, u0, v0, u1, v1: im.crop((round(u0 * im.width), round(v0 * im.height), round(u1 * im.width), round(v1 * im.height)))

    # texture 5
    F = font_load(FONT)[0]
    atlas = Image.new('RGBA', (AW, AH), (0, 0, 0, 0)); rect = {}
    x = 0
    for ch in '0123456789%':
        g = glyph(F, ord(ch) - 48 if ch.isdigit() else 215)
        atlas.alpha_composite(g, (x, 0)); rect[ch] = (x, 0, g.width, g.height); x += g.width + 2
    assert x <= AW
    green = crop(t2, 0.0, 0.188, 0.656, 0.312)                     # 168 x 12 (v03's fill)
    orange = crop(t2, 0.0, 0.771, 0.43, 0.844)                     # 110 x 7
    for k, (im, y) in {'blue': (rehue(green, 150), 24), 'purple': (rehue(green, 196), 40), 'cyan': (rehue(orange, 128), 58)}.items():
        atlas.alpha_composite(im, (0, y)); rect[k] = (0, y, im.width, im.height)
    tpl2, tex = tpltool.append(tpl, np.array(atlas)); assert tex == 5
    uv5 = lambda k: (rect[k][0] / AW, rect[k][1] / AH, (rect[k][0] + rect[k][2]) / AW, (rect[k][1] + rect[k][3]) / AH)
    G = json.load(open(GLYPH)); code = {cd: i for i, cd in enumerate(G['codes'])}
    def gl3(ch):                                                    # a letter in texture 3: uv, width
        cd = 0x0B + ord(ch) - 65 if ch.isupper() else 0xD8 + ord(ch) - 97
        i = code[cd]; cx, cy = G['cells'][i]; lft, w = G['adv'][i]; C = G['cell']
        return ((cx + lft) / G['aw'], cy / G['ah'], (cx + lft + w) / G['aw'], (cy + C) / G['ah']), w

    # agc
    gt = be(agc, 8); off = be(agc, gt + 36); ne, ep = be(agc, off), be(agc, off + 4)
    assert ne == 8
    nq, qp, ex7, ey7 = struct.unpack_from('>IIhh', agc, ep + 12 * E7)
    assert nq == OLD_Q and qp + 0x2C * nq == len(agc), 'element 7 is not the 37-quad HUD build at the end of opguide.agc'
    for e in range(1, 7): struct.pack_into('>I', agc, ep + 12 * e, 0)
    for k in range(NAME_Q):
        for j in range(4): struct.pack_into('>I', agc, qp + 0x2C * k + 12 + 4 * j, 0xFFFFFF00)
    W = 0xFFFFFFF0
    rel = lambda hx, hy: (hx - ex7, hy - E7_BASE_Y)
    def quad(tex, hx, hy, w, h, u, col=W):
        x0, y0 = rel(hx, hy)
        return struct.pack('>Ihhhh', tex, x0, y0, x0 + w, y0 + h) + struct.pack('>4I', *[col] * 4) + struct.pack('>4f', *u)
    Q, names = [], {}
    def add(name, q): names[name] = len(Q); Q.append(q)
    add('hpback', quad(2, BX, BY, 172, 16, (0.0, 0.0, 0.672, 0.167)))
    add('green', quad(2, BX + 2, BY + 2, 168, 12, (0.0, 0.188, 0.656, 0.312)))
    add('blue', quad(5, BX + 2, BY + 2, 168, 12, uv5('blue')))
    add('purple', quad(5, BX + 2, BY + 2, 168, 12, uv5('purple')))
    add('apple', quad(2, *APPLE, (0.703, 0.542, 0.836, 0.896)))
    add('pct', quad(5, PCT_X, PCT_Y, 0, 0, uv5('0')))
    for k in range(3): Q.append(quad(5, PCT_X, PCT_Y, 0, 0, uv5('0')))   # 4 quads: up to "100%"
    add('expback', quad(2, BX, EY, 128, 9, (0.0, 0.625, 0.445, 0.74)))
    add('cyan', quad(5, BX + 2, EY + 1, 124, 6, uv5('cyan')))
    def word(name, s, hx, hy, sc):
        names[name] = len(Q)
        for ch in s:
            u, w = gl3(ch); gw = round(w * sc / FONT_SC); Q.append(quad(3, hx, hy, gw, round(21 * sc / FONT_SC), u)); hx += gw - 1
        return hx
    word('hp', 'HP', HP_X, HP_Y, HP_SC)
    word('exp', 'EXP', EXP_X, EXP_Y, EXP_SC)
    lvx = word('lvl', 'Lvl', LV_X, LV_Y, LV_SC)
    add('lvnum', quad(5, lvx, LV_Y, 0, 0, uv5('0')))
    Q.append(quad(5, lvx, LV_Y, 0, 0, uv5('0')))                       # 2 quads: up to Lvl 99
    q0 = len(agc); agc += b''.join(Q)
    total = OLD_Q + len(Q)
    struct.pack_into('>I', agc, ep + 12 * E7, total)
    agc = bytes(agc)

    nu = u8arc.build(arc, {kt: tpl2, ka: agc}); a2 = u8arc.read(nu)
    for j in arc['files']:
        if j not in (kt, ka): assert a2['files'][j] == arc['files'][j]
    c = clz_compress(nu); assert clz_decompress(c) == nu
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, 'commonall.arc.clz'), 'wb').write(c)
    atlas.resize((AW * 3, AH * 3), Image.NEAREST).save(os.path.join(out, 'stat_atlas.png'))

    fl = lambda u: '{%ff, %ff, %ff, %ff}' % tuple(u)
    h = ['/* generated by tools/hud/build_stat_hud.py */',
         '#define E7_TOTAL      %d   /* element 7 quads with the stat HUD (skill.c / zt.c check it) */' % total,
         '#define STAT_Q        %d' % len(Q)]
    for k, i in names.items(): h.append('#define SQ_%-8s 0x%X' % (k.upper(), q0 + 0x2C * i))
    h += ['#define SH_BAR_W   168   /* HP fill width */', '#define SH_EXP_W   124',
          '#define SH_PCT_X   %d    /* element 7 x of the first fullness digit */' % rel(PCT_X, 0)[0],
          '#define SH_PCT_Y   %d' % rel(0, PCT_Y)[1], '#define SH_PCT_SC  %d   /* x 100 */' % round(PCT_SC / FONT_SC * 100),
          '#define SH_LV_X    %d' % rel(lvx + 5, 0)[0], '#define SH_LV_Y    %d' % rel(0, LV_Y)[1],
          '#define SH_LV_SC   %d' % round(LV_SC / FONT_SC * 100),
          '#ifdef SH_DATA', 'static const float SH_DIG[11][4] = {%s};  /* 0-9, %% (texture 5) */' % ', '.join(fl(uv5(ch)) for ch in '0123456789%'),
          'static const unsigned char SH_DIG_W[11] = {%s};' % ', '.join(str(rect[ch][2]) for ch in '0123456789%'),
          'static const float SH_UV_BLUE[4] = %s, SH_UV_PURPLE[4] = %s, SH_UV_CYAN[4] = %s;' % (fl(uv5('blue')), fl(uv5('purple')), fl(uv5('cyan'))), '#endif']
    open(os.path.join(out, 'stat_hud.h'), 'w').write('\n'.join(h) + '\n')
    print('opguide.tpl +texture 5 (%dx%d), opguide.agc %d -> %d B (element 7: %d quads), commonall %d B sha1 %s'
          % (AW, AH, len(arc['files'][ka]), len(agc), total, len(c), hashlib.sha1(c).hexdigest()[:12]))

if __name__ == '__main__':
    main()
