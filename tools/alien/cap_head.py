#!/usr/bin/env python3
"""Head redesign (user): a wide, FLAT mushroom-cap head (not a dome) with huge black eyes, no jaw. The head is our own
mesh: a surface of revolution (elliptical rings) from a profile r(y), the face low on the front of the cap, a narrow chin
running down into the thin neck. Rendered on the T2 body; the eyes are painted on a planar front texture.
usage: cap_head.py OUTDIR"""
import sys, os, numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
OUTD = sys.argv[1]
os.environ['FACE'] = 'none'
_a = sys.argv; sys.argv = ['x', OUTD]; __file__ = os.path.join(HERE, 'face.py'); exec(open(__file__).read()); sys.argv = _a
__file__ = os.path.join(HERE, 'cap_head.py')

def resample(c, M):
    c = np.array(c, float); d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))]
    t = np.linspace(0, d[-1], M); return np.stack([np.interp(t, d, c[:, 0]), np.interp(t, d, c[:, 1])], 1)

def head_mesh(k, seg=48, M=40):
    """a mushroom cap (thin rim, low flat-ish top) over a face lobe hanging below its front. Per azimuth phi a profile
       curve (r, y) from the neck up to the crown, blended from the front curve (face lobe) to the back curve (straight
       up under the cap) by w = max(cos phi, 0) ** k['fw']; rings are slightly elliptical (z * zr)."""
    R, top, rim, fw, zr = k['R'], k['top'], k['rim'], k['fw'], k.get('zr', 0.85)
    ey, my, ch = k['eyey'], k['mouth'], k['chin']
    crown = [(R, rim), (R * 0.99, rim + 0.2 * (top - rim)), (R * 0.93, rim + 0.45 * (top - rim)), (R * 0.8, rim + 0.7 * (top - rim)),
             (R * 0.55, rim + 0.9 * (top - rim)), (R * 0.25, top - 0.004), (0.0, top)]
    L = k.get('lobe', 1.0)
    front = [(0.0, ch), (0.035 * L, ch + 0.008), (0.065 * L, my - 0.035 * L), (0.085 * L, my), (0.13 * L, my + 0.04), (R * 0.75, ey - 0.03),
             (R * 0.93, ey + 0.005), (R, rim)] + crown[1:]
    back = [(0.0, k['nape']), (0.04, k['nape'] + 0.004), (0.12, k['nape'] + 0.012), (R * 0.75, ey - 0.03), (R * 0.93, ey + 0.005),
            (R, rim)] + crown[1:]
    Fc, Bc = resample(front, M), resample(back, M)
    V = []; Fs = []
    for kk in range(seg):
        ph = 2 * np.pi * kk / seg; w = max(np.cos(ph), 0) ** fw
        C = Bc + (Fc - Bc) * w
        for r, y in C:                                     # flat front to back (user): depth zr on the cap, the neck
            z_ = zr if y > ey else 0.9 + (zr - 0.9) * min(r / (0.6 * R), 1.0)   # and chin stay round
            V.append((r * np.sin(ph), y, r * z_ * np.cos(ph)))
    for kk in range(seg):
        k2 = (kk + 1) % seg
        for i in range(M - 1):
            a, b, c, d = kk * M + i, k2 * M + i, kk * M + i + 1, k2 * M + i + 1
            Fs += [(a, b, c), (b, d, c)]
    return np.array(V), np.array(Fs)

def jaw_open(Hv, k, deg):
    """the lower face lobe (below the mouth line, front) swings down about a hinge behind it"""
    if not deg: return Hv.copy(), np.zeros(len(Hv), bool)
    my = k['mouth'] + 0.02; hz = -0.04; V = Hv.copy()
    wz = np.clip((Hv[:, 2] - 0.0) / 0.05, 0, 1); wy = np.clip((my - Hv[:, 1]) / 0.012, 0, 1); wgt = wz * wy
    a = -np.radians(deg) * wgt; c, s_ = np.cos(a), np.sin(a)
    y, z = Hv[:, 1] - my, Hv[:, 2] - hz
    V[:, 1] = my + y * c - z * s_; V[:, 2] = hz + y * s_ + z * c
    V[:, 0] *= 1 + 0.45 * wgt * deg / 60
    return V, wgt > 0

def paint(eye, red=False, TWc=512):
    """front texture over x -0.5..0.5, y -0.1..0.5 (head-local); eye = (rx, ry, ex, ey, tilt)"""
    X0c, X1c, Y0c, Y1c = -0.5, 0.5, -0.1, 0.5
    pxc = lambda x, y: ((x - X0c) / (X1c - X0c) * TWc, (Y1c - y) / (Y1c - Y0c) * TWc * 0.6)
    W, Hh = TWc, int(TWc * 0.6)
    img = np.tile(SKIN_RGB, (Hh, W, 1)).astype(float)
    mask = Image.new('L', (W, Hh), 0); d = ImageDraw.Draw(mask)
    rx, ry, ex, ey, tilt = eye
    for sx in (-1, 1):
        pts = []
        for t in np.linspace(0, 2 * np.pi, 72, endpoint=False):
            x, y = rx * np.cos(t), ry * np.sin(t)
            x, y = x * np.cos(sx * tilt) - y * np.sin(sx * tilt), x * np.sin(sx * tilt) + y * np.cos(sx * tilt)
            pts.append(pxc(sx * ex + x, ey + y))
        d.polygon(pts, fill=255)
    m = np.array(mask.filter(ImageFilter.GaussianBlur(1.2))).astype(float)[..., None] / 255
    rim = np.array(mask.filter(ImageFilter.GaussianBlur(14))).astype(float)[..., None] / 255
    img = img * (1 - 0.6 * np.clip(rim * 1.5, 0, 1))
    img = img * (1 - m) + np.array([6, 5, 7]) * m
    gl = Image.new('L', (W, Hh), 0); dg = ImageDraw.Draw(gl)               # a faint wet highlight in each eye
    for sx in (-1, 1):
        cx, cy = pxc(sx * ex - sx * rx * 0.35, ey + ry * 0.4); r = rx * 0.12 / (X1c - X0c) * W
        dg.ellipse((cx - r, cy - r * 0.7, cx + r, cy + r * 0.7), fill=120)
    g = np.array(gl.filter(ImageFilter.GaussianBlur(2))).astype(float)[..., None] / 255
    img = img * (1 - g) + 230 * g
    if red:
        dot = Image.new('L', (W, Hh), 0); dd = ImageDraw.Draw(dot)
        for sx in (-1, 1):
            cx, cy = pxc(sx * ex, ey); r = min(rx, ry) * 0.3 / (X1c - X0c) * W
            dd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
        core = np.array(dot.filter(ImageFilter.GaussianBlur(1.5))).astype(float)[..., None] / 255
        halo = np.array(dot.filter(ImageFilter.GaussianBlur(10))).astype(float)[..., None] / 255 * m
        img = img * (1 - halo) + np.array([230, 25, 15]) * halo
        hot = np.array(dot.filter(ImageFilter.GaussianBlur(0.5)).resize((W, Hh))).astype(float)[..., None] / 255
        img = img * (1 - core) + np.array([255, 60, 40]) * core
    uvf = lambda P: np.stack([(P[:, 0] - X0c) / (X1c - X0c), (Y1c - P[:, 1]) / (Y1c - Y0c)], 1)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)), uvf

T2 = fore((0, 1, 0), -150, ((0, 1, 0), 145), fwd=0, out=4, extra=hunch(1.5))
VS = gaunt(smooth_face(VA))
VP = pose(T2, VS); R_, t_ = pose.last
CHIN = np.array([0, 0.835, 0.0])                     # head-local origin: just above the neck top (rest space)
def place(Hv):
    return (R_[7] @ (Hv + CHIN - P[7]).T).T + t_[7]

CANDS = [
    ('F1 flat plate head (thin front to back)', dict(R=0.30, top=0.46, rim=0.2, fw=1.6, eyey=0.17, mouth=0.07, chin=-0.02, nape=0.12, zr=0.38),
     (0.06, 0.045, 0.09, 0.17, 0.2), 0),
    ('F2 flatter still, wider', dict(R=0.34, top=0.44, rim=0.19, fw=2.0, eyey=0.165, mouth=0.07, chin=-0.02, nape=0.125, zr=0.26),
     (0.065, 0.045, 0.1, 0.165, 0.25), 0),
    ('F3 flat, with a jaw (closed / open)', dict(R=0.31, top=0.48, rim=0.23, fw=1.1, eyey=0.205, mouth=0.1, chin=-0.1, nape=0.13, lobe=1.45, zr=0.36),
     (0.056, 0.046, 0.088, 0.2, 0.2), 65),
]
try: font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 20); small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
except Exception: font = small = ImageFont.load_default()
Vf, FF = forelimbs_big(VP); keep = ~np.isin(NODE, FORE_NODES)
fb = keep[F].all(1) & ~(LAB[F] == 'head').any(1)          # the body without its old head
body_F = np.vstack([F[fb], FF[fmask_n:]]) if False else None
nb = len(F); FFbody = np.vstack([F[fb], FF[keep[F].all(1).sum():]])
UVb = np.stack([(VS[:, 0] - BX0) / (BX1 - BX0), (BY1 - VS[:, 1]) / (BY1 - BY0)], 1); ONb = (LAB == 'torso') & (VS[:, 2] > -0.01)
ribs = Image.open(os.path.join(HERE, 'alien_ribs.png'))
rows = []
for nm, pr, eye, jdeg in CANDS:
    for red in (False, True):
        Hv0, Hf = head_mesh(pr)
        Hv, jm = jaw_open(Hv0, pr, jdeg if red else 0)
        Hp = place(Hv)
        tex, uvf = paint(eye, red); UVh = uvf(Hv0); ONh = Hv0[:, 2] > -0.02
        ar = lambda X: np.linalg.norm(np.cross(X[Hf[:, 1]] - X[Hf[:, 0]], X[Hf[:, 2]] - X[Hf[:, 0]]), axis=1)
        mouthF = (ar(Hv) > 1.6 * ar(Hv0) + 1e-9) if (jdeg and red) else np.zeros(len(Hf), bool)
        o = len(Vf); Vall = np.vstack([Vf, Hp]); Fall = np.vstack([FFbody, Hf + o])
        fc = np.concatenate([np.zeros(len(FFbody), bool), mouthF])
        ext = len(Vall) - len(UVb)
        L2 = (np.vstack([UVb, np.zeros((ext, 2))]), np.concatenate([ONb, np.zeros(ext, bool)]), ribs)
        L1 = (np.vstack([np.zeros((o, 2)), UVh]), np.concatenate([np.zeros(o, bool), ONh]), tex)
        cells = [render_layers(Vall, [L1, L2], a, Fall, sc=190, oy=445, fcol=fc) for a in (0, np.radians(35), np.radians(90))]
        Hc = Hp.mean(0) + np.array([0, -0.02, 0])
        for ang in (np.radians(0), np.radians(-30)):
            cells.append(render_layers(Vall - Hc, [L1, L2], ang, Fall, sc=380, oy=235, fcol=fc))
        sheet = Image.new('RGB', (280 * len(cells), 470 + 30), (30, 30, 36)); dr = ImageDraw.Draw(sheet)
        for kk, ci in enumerate(cells): sheet.paste(ci, (280 * kk, 30))
        lab = nm + ((' - the scream, jaw open %d deg' % jdeg if jdeg else ' - the scream (red dots)') if red else '')
        dr.text((8, 5), lab, fill=(235, 225, 220), font=font); rows.append(sheet); print(lab)
out = Image.new('RGB', (rows[0].width, sum(r.height for r in rows))); y = 0
for r in rows: out.paste(r, (0, y)); y += r.height
out.save(os.path.join(OUTD, 'cap_heads.png')); print('saved')
