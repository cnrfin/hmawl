#!/usr/bin/env python3
"""Slim the goddess's face on the BUILT model (user: keep the current model; less of Muffy's baby face - a narrower
jaw and a slightly more pointed chin, like Flora's), and recolour her eye frames: eyebrows in her hair's green, a faint
eyeshadow on the upper lid.
Geometry: one smooth warp of model-space positions (+Y up, +Z forward, x 0 = the face's centre line), applied to every
skin source vertex (.skn group 1 sources: s16 / 8192, 6 shorts per vertex = position + normal, from src + align) and
every .gpl position, so shared seams stay joined. Below the eyes the face narrows toward the jaw (front half of the head
only: buns, back hair and neck untouched); the chin's middle moves a little down and forward.
Texture: the 58 eye frames (gd_0_f0_e.tpl, 32x32 CMPR, shared data) decoded, brows (dark brown strokes above the eye)
recoloured to the hair green, a soft tint over the upper lid, re-encoded in place (same size).
usage: slim_face.py IN_gd_0.arc OUT_gd_0.arc [--slim 0.14] [--chin 0.02] [--shadow R,G,B] [--no-texture]"""
import sys, os, struct, argparse, ast, numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument('src'); ap.add_argument('dst')
ap.add_argument('--slim', type=float, default=0.20)          # lateral squeeze at the jaw
ap.add_argument('--chin', type=float, default=0.03)          # chin point: down by this, forward by 0.6 x this
ap.add_argument('--brow', default='70,120,80')               # her hair's mid green
ap.add_argument('--shadow', default='100,170,175')           # faint teal
ap.add_argument('--shadow-a', type=float, default=0.5)
ap.add_argument('--no-texture', action='store_true')
A = ap.parse_args()
EYE_LO, JAW, CHIN, NECK, MOUTH = 1.06, 0.96, 0.925, 0.86, 0.975            # built heights (1.1 x the source model)

def sm(x): x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)
def warp(P):
    P = P.copy(); x, y, z = P[:, 0], P[:, 1], P[:, 2]
    w = sm((EYE_LO - y) / (EYE_LO - JAW)) * sm((y - NECK) / (CHIN - NECK))   # 0 at the eyes -> 1 at the jaw, off at the neck
    f = sm((z + 0.05) / 0.15)                                               # front of the head only
    c = w * f * np.exp(-(x / 0.09) ** 2) * sm((MOUTH - y) / 0.04)          # the chin's middle, below the mouth
    P[:, 0] = x * (1 - A.slim * w * f)
    P[:, 1] = y - A.chin * c
    P[:, 2] = z + 0.6 * A.chin * c
    return P

def u8_entries(d):
    be = lambda o: struct.unpack_from('>I', d, o)[0]
    root = be(4); n = be(root + 8); st = root + 12 * n; out = []
    for i in range(1, n):
        w0, o, s = struct.unpack_from('>III', d, root + 12 * i)
        if not w0 >> 24:
            nm = d[st + (w0 & 0xFFFFFF):d.index(b'\0', st + (w0 & 0xFFFFFF))].decode()
            out.append((nm, o, s))
    return out
d = bytearray(open(A.src, 'rb').read())
F = {n: (o, s) for n, o, s in u8_entries(d)}
pre = [n for n in F if n.endswith('.gpl')][0][:-4]

# ---- skin sources
so, ss = F[pre + '.skn']; S = bytearray(d[so:so + ss])
n1 = struct.unpack_from('>H', S, 0)[0]; g1o = struct.unpack_from('>I', S, 8)[0]
moved = 0
for k in range(n1):
    o = g1o + 0x40 * k; src, dst, bone, cnt = struct.unpack_from('>IIHH', S, o + 0x30); al = S[o + 0x3C]
    a = np.array(struct.unpack_from('>%dh' % (6 * cnt), S, src + al), float).reshape(-1, 6)
    P = a[:, :3] / 8192; Q = warp(P); moved += int((abs(Q - P).max(1) > 1e-4).sum())
    a[:, :3] = np.round(Q * 8192)
    struct.pack_into('>%dh' % (6 * cnt), S, src + al, *a.astype(int).ravel())
d[so:so + ss] = S
# ---- gpl positions (the bind copy)
go, gs = F[pre + '.gpl']; G = bytearray(d[go:go + gs]); m0 = 0x1C
po = struct.unpack_from('>I', G, m0)[0]; off, cnt, fmt, comp = struct.unpack_from('>IHBB', G, m0 + po)
frac = fmt & 0xF; raw = np.array(struct.unpack_from('>%dh' % (6 * cnt), G, m0 + off), float).reshape(-1, 6)
raw[:, :3] = np.round(warp(raw[:, :3] / (1 << frac)) * (1 << frac))
struct.pack_into('>%dh' % (6 * cnt), G, m0 + off, *raw.astype(int).ravel())
d[go:go + gs] = G
print('skin vertices moved:', moved)

# ---- eye frames: brows to the hair green, faint eyeshadow
if not A.no_texture:
    src = open(os.path.join(HERE, 'build_blank.py')).read(); ns = {'np': np, 'struct': struct}
    for node in ast.parse(src).body:
        if isinstance(node, ast.FunctionDef) and node.name in ('c565', 'un565', 'cmpr'):
            exec(compile(ast.Module([node], []), 'build_blank.py', 'exec'), ns)
    def decmpr(b):                                           # 32x32 CMPR -> RGBA
        img = np.zeros((32, 32, 4)); i = 0
        for by in range(0, 32, 8):
            for bx in range(0, 32, 8):
                for sy in (0, 4):
                    for sx in (0, 4):
                        c0, c1 = struct.unpack_from('>HH', b, i); bits = struct.unpack_from('>I', b, i + 4)[0]; i += 8
                        p0, p1 = ns['un565'](c0), ns['un565'](c1)
                        pal = [np.r_[p0, 255], np.r_[p1, 255]]
                        pal += [np.r_[(2 * p0 + p1) / 3, 255], np.r_[(p0 + 2 * p1) / 3, 255]] if c0 > c1 else [np.r_[(p0 + p1) / 2, 255], np.zeros(4)]
                        for q in range(16):
                            img[by + sy + q // 4, bx + sx + q % 4] = pal[(bits >> (30 - 2 * q)) & 3]
        return img
    eo, es = F[pre + '_f0_e.tpl']; T = bytearray(d[eo:eo + es])
    n, tab = struct.unpack_from('>II', T, 4); seen = set()
    brow = np.array([int(v) for v in A.brow.split(',')], float); sh = np.array([int(v) for v in A.shadow.split(',')], float)
    for i in range(n):
        io = struct.unpack_from('>I', T, tab + 8 * i)[0]; h, w, f_, do = struct.unpack_from('>HHII', T, io)
        if w != 32 or f_ != 14 or do in seen: continue
        seen.add(do)
        img = decmpr(bytes(T[do:do + 512])); rgb = img[:, :, :3]; op = img[:, :, 3] > 0
        lum = rgb.mean(2); skin_l = np.median(lum[:2][op[:2]]) if op[:2].any() else 215.0
        ys = np.arange(32)[:, None] * np.ones((1, 32))
        dark = op & (lum < skin_l - 40)                               # lashes / pupil / brow strokes
        lash = np.full(32, -1)
        for x in range(32):                                          # the lash line: first dark pixel from row 10 down
            col = np.where(dark[10:24, x])[0]
            if len(col): lash[x] = 10 + col[0]
        # brows: everything clearly darker than the skin above the lash line (rows < 10, or above an open eye)
        k = np.clip((skin_l - lum) / (skin_l - 70), 0, 1)
        is_brow = op & (ys < 10) & (lum < skin_l - 10)
        kb = k[..., None]
        rgb[is_brow] = (rgb * (1 - kb) + brow * kb)[is_brow]
        # eyeshadow: skin just above each column's lash line, fading upward and toward the eye's ends
        xs = np.where(lash >= 0)[0]
        if len(xs) > 2:
            x0, x1 = xs.min(), xs.max(); mid = (x0 + x1) / 2; half = max(1.0, (x1 - x0) / 2)
            for x in xs:
                ex = np.clip(1.15 - abs(x - mid) / half, 0, 1)
                for dy in range(1, 6):
                    y = lash[x] - dy
                    if y < 0 or not op[y, x] or dark[y, x] or is_brow[y, x]: continue
                    a = A.shadow_a * ex * (1 - (dy - 1) / 5)
                    rgb[y, x] = rgb[y, x] * (1 - a) + sh * a
        img[:, :, :3] = rgb.clip(0, 255)
        T[do:do + 512] = ns['cmpr'](Image.fromarray(img.astype(np.uint8), 'RGBA'))
    d[eo:eo + es] = T
    print('eye frames recoloured:', len(seen))
open(A.dst, 'wb').write(bytes(d)); print(A.dst, len(d))
