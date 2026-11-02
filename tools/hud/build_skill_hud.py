#!/usr/bin/env python3
"""Tool skill on the HUD: a row under the food bar (tool-type icon + 5 gems) and a "Field up!" /
"Animal up!" pop-up. Art: the rucksack's tools / milk-can tab icons, the HUD's B-button gem recoloured
(yellow = earned, grey = not yet) and the HUD font (opguide.tpl texture 3) for the letters.

usage: build_skill_hud.py commonall.arc.clz rucksack2.tpl OUTDIR
Writes OUTDIR/commonall.arc.clz (opguide.tpl + texture 4, opguide.agc + 17 quads) and OUTDIR/skill_hud.h
(the offsets and texture coordinates the runtime code in pm.bin uses).

opguide.agc: group 4 entry 0 is the purple disc + our HUD elements; element 7 (the farmer's name, 12 glyph
quads) has its quads at the end of the file, and the HUD code writes element y values and quad fields at
fixed offsets, so the new quads are appended to element 7 (count 12 -> 29) and nothing else moves.
Quad (0x2C): u32 texture, s16 x0 y0 x1 y1 (relative to the element), 4 x u32 RGBA, f32 u0 v0 u1 v1."""
import os, sys, struct, json, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, '..', 'logs'), '/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/lumber']
import u8arc, tpltool
from build_log_archives import clz_decompress, clz_compress

GLYPH = '/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/font/glyph_meta.json'
ELEM7, NAME_Q = 7, 12
ROW_Q, POP_Q, RET_Q = 6, 11, 4      # RET_Q: the Z-target reticle (4 triangles, zt.c)
AW, AH = 128, 64
be = lambda b, o: struct.unpack_from('>I', b, o)[0]

def blob(im, seed):
    """the connected opaque area around seed (drops the neighbouring tab icons' edges)"""
    a = np.array(im); m = a[..., 3] > 16; keep = np.zeros(m.shape, bool)
    ys, xs = np.where(m); k = np.argmin((ys - seed[0]) ** 2 + (xs - seed[1]) ** 2); st = [(ys[k], xs[k])]
    while st:
        y, x = st.pop()
        if 0 <= y < m.shape[0] and 0 <= x < m.shape[1] and m[y, x] and not keep[y, x]:
            keep[y, x] = True; st += [(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)]
    a[~keep, 3] = 0
    ys, xs = np.where(keep); return Image.fromarray(a).crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))

def art(opg_tpl, ruck_tpl):
    T = tpltool.read(opg_tpl); op0 = Image.fromarray(tpltool.decode(opg_tpl, T[0]))
    R = tpltool.read(ruck_tpl); rk = Image.fromarray(tpltool.decode(ruck_tpl, R[0]))
    hoe = blob(rk.crop((186, 40, 230, 90)), (22, 22)); can = blob(rk.crop((154, 40, 198, 90)), (22, 22))
    b = np.array(op0.crop((343, 2, 375, 35))).astype(float); r, g, bl, al = b[..., 0], b[..., 1], b[..., 2], b[..., 3]
    yel = np.stack([np.clip(r * 1.05, 0, 255), np.clip(r * 0.86 + g * 0.4, 0, 255), np.clip(bl * 0.35 + g * 0.2, 0, 255), al], -1)
    lum = r * 0.4 + g * 0.4 + bl * 0.2; gry = np.stack([lum * 0.55 + 20, lum * 0.55 + 22, lum * 0.6 + 30, al * 0.95], -1)
    def gem(arr):                                       # blur the "B" away, then 16x16
        im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)); c = im.filter(ImageFilter.GaussianBlur(2.4))
        m = Image.new('L', im.size, 0); ImageDraw.Draw(m).ellipse((7, 6, 25, 27), fill=255)
        return Image.composite(c, im, m).resize((16, 16), Image.LANCZOS)
    ex = Image.new('RGBA', (10, 21), (0, 0, 0, 0)); d = ImageDraw.Draw(ex)       # "!" in the HUD font's style
    d.rounded_rectangle((1, 0, 8, 13), radius=3, fill=(0, 0, 0, 255)); d.rounded_rectangle((3, 2, 6, 11), radius=1, fill=(255, 255, 255, 255))
    d.ellipse((1, 14, 8, 20), fill=(0, 0, 0, 255)); d.ellipse((3, 16, 6, 18), fill=(255, 255, 255, 255))
    return {'hoe': hoe.resize((28, 32), Image.LANCZOS), 'can': can.resize((28, 32), Image.LANCZOS),
            'gemY': gem(yel), 'gemE': gem(gry), 'excl': ex}

def triangles(n=12):
    """white triangle pointing down (1 px grey rim, tinted by the quad colour); the others are rotations"""
    big = Image.new('RGBA', (n * 8, n * 8), (0, 0, 0, 0)); d = ImageDraw.Draw(big); m = n * 8
    d.polygon([(4, 6), (m - 4, 6), (m / 2, m - 6)], fill=(150, 150, 150, 255))
    d.polygon([(16, 14), (m - 16, 14), (m / 2, m - 22)], fill=(255, 255, 255, 255))
    down = big.resize((n, n), Image.LANCZOS)
    return {'triD': down, 'triU': down.rotate(180), 'triL': down.rotate(-90), 'triR': down.rotate(90)}

def main():
    a = sys.argv[1:]; onto = None
    if '--onto' in a: i = a.index('--onto'); onto = a[i + 1]; del a[i:i + 2]
    clz, ruck, out = a[:3]
    u = clz_decompress(open(clz, 'rb').read()); arc = u8arc.read(u); nm = u8arc.names(arc)
    kt, ka = nm['opguide.tpl'], nm['opguide.agc']
    tpl, agc = arc['files'][kt], bytearray(arc['files'][ka])
    T = tpltool.read(tpl); assert len(T) == 4, 'expected the HUD build with textures 0-3'
    parts = art(tpl, open(ruck, 'rb').read()); parts.update(triangles())
    place = {'hoe': (0, 0), 'can': (32, 0), 'gemY': (64, 0), 'gemE': (84, 0), 'excl': (104, 0),
             'triD': (0, 40), 'triU': (16, 40), 'triL': (32, 40), 'triR': (48, 40)}
    atlas = Image.new('RGBA', (AW, AH), (0, 0, 0, 0)); rect = {}
    for k, (x, y) in place.items():
        atlas.alpha_composite(parts[k].convert('RGBA'), (x, y)); rect[k] = (x, y, parts[k].width, parts[k].height)
    tpl2, tex = tpltool.append(tpl, np.array(atlas)); assert tex == 4
    uv = lambda k: (rect[k][0] / AW, rect[k][1] / AH, (rect[k][0] + rect[k][2]) / AW, (rect[k][1] + rect[k][3]) / AH)

    # agc: element 7's quads are the file's last bytes
    gt = be(agc, 8); cnt, off = be(agc, gt + 32), be(agc, gt + 36); ne, ep = be(agc, off), be(agc, off + 4)
    assert ne == 8
    nq, qp, ex7, ey7 = struct.unpack_from('>IIhh', agc, ep + 12 * ELEM7)
    assert nq == NAME_Q and qp + 0x2C * nq == len(agc), 'element 7 is not at the end of opguide.agc'
    quad = lambda tex, x0, y0, x1, y1, col, u: struct.pack('>Ihhhh', tex, x0, y0, x1, y1) + struct.pack('>4I', *[col] * 4) + struct.pack('>4f', *u)
    # the row (screen offsets from the centre): icon under the apple, gems along the food bar's line
    ICON = (-243, -129); GEM0, GEM_DX, GEM_Y = -210, 15, -121          # 40 px in from the apple
    rel = lambda x, y: (x - ex7, y - ey7)
    ix, iy = rel(*ICON)
    row = [quad(4, ix, iy, ix + 28, iy + 32, 0xFFFFFF00, uv('hoe'))]
    for k in range(5):
        gx, gy = rel(GEM0 + GEM_DX * k, GEM_Y); row.append(quad(4, gx, gy, gx + 16, gy + 16, 0xFFFFFF00, uv('gemE')))
    pop = [quad(3, 0, 0, 0, 0, 0xFFFFFF00, (0, 0, 0, 0))] * POP_Q
    ret = [quad(4, 0, 0, 0, 0, 0xFFFFFF00, uv('triD'))] * RET_Q
    q0 = len(agc); agc += b''.join(row + pop + ret)
    struct.pack_into('>I', agc, ep + 12 * ELEM7, NAME_Q + ROW_Q + POP_Q + RET_Q)
    agc = bytes(agc)

    if onto:   # put the new HUD files into a later commonall (e.g. the $JOE coin build) that only differs elsewhere
        base = u8arc.read(clz_decompress(open(onto, 'rb').read())); bn = u8arc.names(base)
        assert bn['opguide.tpl'] == kt and bn['opguide.agc'] == ka
        built = u8arc.read(clz_decompress(open(clz, 'rb').read()))     # (the input's own files, for the check below)
        arc = base
    nu = u8arc.build(arc, {kt: tpl2, ka: agc}); a2 = u8arc.read(nu)
    for j in arc['files']:
        if j not in (kt, ka): assert a2['files'][j] == arc['files'][j]
    c = clz_compress(nu); assert clz_decompress(c) == nu
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, 'commonall.arc.clz'), 'wb').write(c)
    atlas.resize((AW * 4, AH * 4), Image.NEAREST).save(os.path.join(out, 'skill_atlas.png'))

    # header for the runtime code
    G = json.load(open(GLYPH)); code = {cd: i for i, cd in enumerate(G['codes'])}
    def gl(ch):
        cd = 0x0B + ord(ch) - 65 if ch.isupper() else 0xD8 + ord(ch) - 97
        i = code[cd]; cx, cy = G['cells'][i]; lft, w = G['adv'][i]; C = G['cell']
        return ((cx + lft) / G['aw'], cy / G['ah'], (cx + lft + w) / G['aw'], (cy + C) / G['ah'], w, C)
    words = ['Field up', 'Animal up']
    h = ['/* generated by build_skill_hud.py */',
         '#define AGC_ELEMENTS   0x%X   /* element table (12 bytes each) */' % ep,
         '#define AGC_E7_Y       0x%X   /* element 7 y (s16), the HUD slide moves it */' % (ep + 12 * ELEM7 + 10),
         '#define AGC_E7_COUNT   0x%X' % (ep + 12 * ELEM7), '#define E7_COUNT       %d' % (NAME_Q + ROW_Q + POP_Q + RET_Q),
         '#define E7_X           %d' % ex7, '#define AGC_ROW_Q      0x%X   /* icon, then 5 gems */' % q0,
         '#define AGC_POP_Q      0x%X   /* %d letter quads */' % (q0 + 0x2C * ROW_Q, POP_Q), '#define POP_QUADS      %d' % POP_Q,
         '#define AGC_RET_Q      0x%X   /* %d Z-target reticle quads (zt.c) */' % (q0 + 0x2C * (ROW_Q + POP_Q), RET_Q),
         'static const float UV_TRI[4][4] = {%s};  /* down, up, left, right */' % ', '.join('{%ff, %ff, %ff, %ff}' % uv(k) for k in ('triD', 'triU', 'triL', 'triR')),
         '#define TRI_W %d' % rect['triD'][2],
         'static const float UV_HOE[4] = {%ff, %ff, %ff, %ff};' % uv('hoe'),
         'static const float UV_CAN[4] = {%ff, %ff, %ff, %ff};' % uv('can'),
         'static const float UV_GEMY[4] = {%ff, %ff, %ff, %ff};' % uv('gemY'),
         'static const float UV_GEME[4] = {%ff, %ff, %ff, %ff};' % uv('gemE'),
         'static const float UV_EXCL[4] = {%ff, %ff, %ff, %ff};' % uv('excl'),
         '#define EXCL_W %d' % rect['excl'][2], '#define EXCL_H %d' % rect['excl'][3],
         'struct glyph { float u0, v0, u1, v1; short w, h; };']
    for n, wd in enumerate(words):
        h.append('static const struct glyph WORD%d[] = {  /* "%s" (0 w = space) */' % (n, wd))
        for ch in wd:
            if ch == ' ': h.append('    {0, 0, 0, 0, 0, 0},')
            else: h.append('    {%ff, %ff, %ff, %ff, %d, %d},  /* %s */' % (gl(ch) + (ch,)))
        h.append('};')
    h.append('#define WORD0_N %d\n#define WORD1_N %d' % (len(words[0]), len(words[1])))
    open(os.path.join(out, 'skill_hud.h'), 'w').write('\n'.join(h) + '\n')
    print('opguide.tpl +texture 4 (%dx%d), opguide.agc %d -> %d B (element 7: %d quads), commonall %d B sha1 %s'
          % (AW, AH, len(arc['files'][ka]), len(agc), NAME_Q + ROW_Q + POP_Q + RET_Q, len(c), hashlib.sha1(c).hexdigest()[:12]))

if __name__ == '__main__':
    main()
