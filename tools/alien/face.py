"""The alien's face (user: an original face like the references - small, tired, uncannily human; no anime features).
Painted procedurally as a texture in face coordinates (rest-space metres on the base head: x -0.15..0.15, y 0.84..1.06),
then shown on the T2 body with the bell jaw closed and screaming, with normal and red eyes.
usage: face.py OUTDIR"""
import sys, os, numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1]
os.environ['SET'] = 'none'
_argv = sys.argv; sys.argv = ['x', OUT]
exec(open(os.path.join(HERE, 'body_candidates.py')).read().split("try: font")[0])
sys.argv = _argv

# ---------------- painting
TW = TH = 512
X0, X1, Y0, Y1 = -0.15, 0.15, 0.84, 1.06
def px(x, y): return ((x - X0) / (X1 - X0) * TW, (Y1 - y) / (Y1 - Y0) * TH)
SKIN_RGB = np.array([206, 198, 197], float)

class Paint:
    def __init__(s):
        s.dark = Image.new('L', (TW, TH), 0); s.light = Image.new('L', (TW, TH), 0)
        s.tint = np.zeros((TH, TW, 3)); s.tintA = np.zeros((TH, TW))
    def stroke(s, layer, pts, w, val, blur):
        im = Image.new('L', (TW, TH), 0); d = ImageDraw.Draw(im)
        d.line([px(*p) for p in pts], fill=val, width=max(1, int(w)), joint='curve')
        im = im.filter(ImageFilter.GaussianBlur(blur))
        L = s.dark if layer == 'd' else s.light
        L.paste(Image.fromarray(np.maximum(np.array(L), np.array(im)).astype(np.uint8)))
    def blob(s, layer, c, rx, ry, val, blur):
        im = Image.new('L', (TW, TH), 0); d = ImageDraw.Draw(im)
        (cx, cy) = px(*c); sx = rx / (X1 - X0) * TW; sy = ry / (Y1 - Y0) * TH
        d.ellipse((cx - sx, cy - sy, cx + sx, cy + sy), fill=val)
        im = im.filter(ImageFilter.GaussianBlur(blur))
        L = s.dark if layer == 'd' else s.light
        L.paste(Image.fromarray(np.maximum(np.array(L), np.array(im)).astype(np.uint8)))
    def colour(s, mask, rgb, a):
        m = np.array(mask).astype(float) / 255 * a
        s.tint = s.tint * (1 - m[..., None]) + np.array(rgb) * m[..., None]; s.tintA = np.maximum(s.tintA, m)

def curve(f, x0, x1, n=24): return [(x, f(x)) for x in np.linspace(x0, x1, n)]

def paint_face(red=False):
    P = Paint()
    EY, EX = 0.962, 0.043                                             # eyes: low on the dome, a little too far apart
    for sx in (-1, 1):
        cx = sx * EX
        P.blob('d', (cx, EY + 0.002), 0.03, 0.017, 95, 9)             # deep, shadowed socket
        P.blob('d', (cx + sx * 0.004, EY - 0.012), 0.024, 0.008, 70, 6)   # bags under the eyes
        P.stroke('d', curve(lambda x: EY - 0.017 - 9 * (x - cx) ** 2, cx - 0.02, cx + 0.018), 3, 110, 2)   # bag crease
        # heavy upper lid: a fold above the eye, the lid itself drooping over half the eye
        P.stroke('d', curve(lambda x: EY + 0.009 - 14 * (x - cx - sx * 0.003) ** 2, cx - 0.02, cx + 0.02), 4, 150, 1.5)
        P.blob('l', (cx, EY + 0.0045), 0.017, 0.0035, 60, 3)           # lid catching light
        # the eye opening: a low, narrow almond (half closed)
        im = Image.new('L', (TW, TH), 0); d = ImageDraw.Draw(im)
        top = [px(x, EY + 0.0015 - 3.2 * (x - cx) ** 2 * 0 - 0.0) for x in np.linspace(cx - 0.016, cx + 0.016, 20)]
        bot = [px(x, EY - 0.004 + 10 * (x - cx) ** 2) for x in np.linspace(cx + 0.016, cx - 0.016, 20)]
        d.polygon(top + bot, fill=255); eye = im.filter(ImageFilter.GaussianBlur(1.2))
        if red:
            P.colour(eye, (255, 24, 18), 1.0)
            P.colour(eye.filter(ImageFilter.GaussianBlur(7)), (255, 40, 30), 0.55)   # bleed: reads as glowing
        else:
            P.colour(eye, (62, 52, 54), 0.95)                          # sclera barely shows: dull, dark
            P.blob('d', (cx + sx * 0.002, EY - 0.001), 0.0062, 0.0042, 255, 1)     # iris / pupil under the lid
            P.blob('l', (cx + sx * 0.0035, EY + 0.0002), 0.0012, 0.0010, 150, 0.6)  # a small wet highlight
        P.stroke('d', curve(lambda x: EY + 0.0015, cx - 0.016, cx + 0.016), 3, 200, 1)   # lid edge (lashless)
        # crow's feet
        for k in range(3):
            P.stroke('d', [(cx + sx * 0.022, EY + 0.002 - 0.004 * k), (cx + sx * 0.033, EY + 0.004 - 0.007 * k)], 2, 70, 1.2)
    # no eyebrows: only a faint brow ridge shadow, and creases on a low forehead
    for sx in (-1, 1):
        P.stroke('l', curve(lambda x: EY + 0.026 - 6 * (x - sx * 0.04) ** 2, sx * 0.02, sx * 0.065), 7, 55, 5)
    for k, yy in enumerate((1.0, 1.012, 1.024)):
        P.stroke('d', curve(lambda x: yy + 3 * x * x, -0.05 + 0.01 * k, 0.05 - 0.01 * k), 2, 55 - 10 * k, 1.5)
    P.stroke('d', [(-0.004, EY + 0.02), (-0.002, EY + 0.006)], 2, 70, 1.2)          # a frown line between the brows
    P.stroke('d', [(0.005, EY + 0.018), (0.003, EY + 0.006)], 2, 55, 1.2)
    # nose: long and thin, a soft shadow down one side, small nostrils
    P.stroke('l', [(0, EY + 0.006), (0.001, 0.938)], 6, 60, 4)
    P.stroke('d', [(0.011, EY - 0.004), (0.012, 0.938)], 5, 60, 4)
    P.blob('d', (0, 0.931), 0.012, 0.004, 90, 4)                       # under the tip
    for sx in (-1, 1): P.blob('d', (sx * 0.0075, 0.9325), 0.0035, 0.0018, 210, 1.2)
    P.blob('l', (0.002, 0.937), 0.005, 0.003, 70, 2)                   # tip highlight
    # mouth: thin, wide-ish, the corners pulled down
    MY = 0.906
    mouth = curve(lambda x: MY - 2.2 * x * x - 0.0 * x, -0.027, 0.027)
    P.stroke('d', mouth, 4, 230, 1.0)
    P.stroke('d', curve(lambda x: MY - 0.006 - 2.0 * x * x, -0.018, 0.018), 6, 70, 3)   # under the lower lip
    lips = Image.new('L', (TW, TH), 0); d = ImageDraw.Draw(lips)
    d.line([px(*p) for p in curve(lambda x: MY + 0.002 - 2.2 * x * x, -0.024, 0.024)], fill=255, width=6)
    P.colour(lips.filter(ImageFilter.GaussianBlur(2)), (168, 140, 142), 0.5)
    P.stroke('d', curve(lambda x: MY + 0.0095 - 1.0 * x * x, -0.006, 0.006, 6), 3, 70, 1.5)   # philtrum dip
    # the creases that make it old and tired: nose-to-mouth folds, sagging lines below the corners
    for sx in (-1, 1):
        P.stroke('d', curve(lambda t: 0, 0, 1, 2), 1, 0, 1)
        fold = [(sx * (0.014 + 0.016 * t ** 0.8), 0.935 - 0.034 * t) for t in np.linspace(0, 1, 16)]
        P.stroke('d', fold, 4, 150, 1.6)
        P.stroke('l', [(sx * (0.018 + 0.016 * t ** 0.8), 0.935 - 0.034 * t) for t in np.linspace(0, 1, 16)], 6, 60, 3)
        P.stroke('d', [(sx * (0.028 + 0.004 * t), MY - 0.003 - 0.025 * t) for t in np.linspace(0, 1, 10)], 3, 110, 1.6)
        P.blob('d', (sx * 0.05, 0.925), 0.02, 0.025, 45, 12)          # hollow cheeks
    P.blob('d', (0, 0.876), 0.03, 0.01, 60, 8)                         # under the chin
    P.blob('l', (0, 0.888), 0.02, 0.008, 45, 6)                        # chin
    # compose: skin, darkening (multiply), light, colour
    dk = np.array(P.dark).astype(float) / 255; lt = np.array(P.light).astype(float) / 255
    img = np.tile(SKIN_RGB, (TH, TW, 1))
    img = img * (1 - 0.62 * dk[..., None]) * np.array([1.0, 0.97, 0.98]) ** (dk[..., None] * 3)
    img = img + (255 - img) * 0.35 * lt[..., None]
    img = img * (1 - P.tintA[..., None]) + P.tint * P.tintA[..., None]
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))

def paint_eyes(kind, red=False):
    """user: just big black empty eyes, no other features (the fear is in the mouth). kind: (rx, ry, ey, ex, tilt)"""
    rx, ry, ey, ex, tilt = kind
    img = Image.fromarray(np.tile(SKIN_RGB, (TH, TW, 1)).astype(np.uint8))
    mask = Image.new('L', (TW, TH), 0); d = ImageDraw.Draw(mask)
    for sx in (-1, 1):
        cx = sx * ex
        pts = []
        for t in np.linspace(0, 2 * np.pi, 64, endpoint=False):
            x, y = rx * np.cos(t), ry * np.sin(t)
            if tilt: x, y = x * np.cos(sx * tilt) - y * np.sin(sx * tilt), x * np.sin(sx * tilt) + y * np.cos(sx * tilt)
            pts.append(px(cx + x, ey + y))
        d.polygon(pts, fill=255)
    m = np.array(mask.filter(ImageFilter.GaussianBlur(1.5))).astype(float)[..., None] / 255
    a = np.array(img).astype(float)
    rim = np.array(mask.filter(ImageFilter.GaussianBlur(16))).astype(float)[..., None] / 255
    a = a * (1 - 0.75 * np.clip(rim * 1.6, 0, 1))                     # a deep socket shadow round each eye
    a = a * (1 - m) + np.array([8, 6, 8]) * m                          # the black eye stays
    if red:                                                           # user: a small red dot in each black eye
        dot = Image.new('L', (TW, TH), 0); dd = ImageDraw.Draw(dot)
        for sx in (-1, 1):
            cx, cy = px(sx * ex, ey); r = min(rx, ry) * 0.32 / (X1 - X0) * TW
            dd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
        core = np.array(dot.filter(ImageFilter.GaussianBlur(1.2))).astype(float)[..., None] / 255
        halo = np.array(dot.filter(ImageFilter.GaussianBlur(6))).astype(float)[..., None] / 255 * m
        a = a * (1 - 0.8 * halo) + np.array([200, 20, 15]) * 0.8 * halo
        a = a * (1 - core) + np.array([255, 40, 30]) * core
    if False:
        rim = np.array(mask.filter(ImageFilter.GaussianBlur(6))).astype(float)[..., None] / 255
        a = a * (1 - 0.35 * rim)                                       # a faint socket shadow round the edge
        a = a * (1 - m) + np.array([8, 6, 8]) * m
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

EYES = {'E1 round': (0.024, 0.024, 0.968, 0.045, 0), 'E2 big ovals, tilted': (0.026, 0.034, 0.972, 0.046, 0.35),
        'E3 huge, far apart': (0.034, 0.036, 0.97, 0.058, 0.15)}

# ---------------- head: smooth the base's face dent (its sculpted nose / sockets) before painting on it
def smooth_face(V, it=12):
    V = V.copy(); fr = (LAB == 'head') & (V[:, 2] > 0.04) & (V[:, 1] > 0.88) & (V[:, 1] < 1.08)
    nb = [set() for _ in range(len(V))]
    for a, b, c in F: nb[a] |= {b, c}; nb[b] |= {a, c}; nb[c] |= {a, b}
    idx = np.where(fr)[0]
    for _ in range(it):
        V[idx] = 0.5 * V[idx] + 0.5 * np.array([V[list(nb[i])].mean(0) for i in idx])
    return V

def face_uv(V):
    u = (V[:, 0] - X0) / (X1 - X0); v = (Y1 - V[:, 1]) / (Y1 - Y0)
    on = (LAB == 'head') & (V[:, 2] > -0.02)
    return np.stack([u, v], 1), on

def render_tex(V, UV, ON, tex, ang, Fz, W=280, H=470, sc=240, oy=None, fcol=None):
    T = np.asarray(tex).astype(float) / 255; th, tw = T.shape[:2]
    c, s = np.cos(ang), np.sin(ang)
    X = V @ np.array([[c, 0, -s], [0, 1, 0], [s, 0, c]]).T
    sx = W / 2 + X[:, 0] * sc; sy = (H - 14 if oy is None else oy) - X[:, 1] * sc; z = X[:, 2]
    img = np.tile(BG, (H, W, 1)); zb = np.full((H, W), -1e9)
    N = np.cross(X[Fz[:, 1]] - X[Fz[:, 0]], X[Fz[:, 2]] - X[Fz[:, 0]]); N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-12
    Lt = np.array([0.35, 0.55, 0.75]); Lt /= np.linalg.norm(Lt)
    shade = 0.32 + 0.68 * np.clip(N @ Lt, 0, 1) + 0.15 * (1 - np.abs(N[:, 2])) ** 3
    skin = SKIN_RGB / 255
    for i, (a, b, cc) in enumerate(Fz):
        inside = N[i, 2] <= 0
        xs = np.array([sx[a], sx[b], sx[cc]]); ys = np.array([sy[a], sy[b], sy[cc]])
        x0, x1 = int(max(0, xs.min())), int(min(W - 1, xs.max() + 1)); y0, y1 = int(max(0, ys.min())), int(min(H - 1, ys.max() + 1))
        if x0 > x1 or y0 > y1: continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        den = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(den) < 1e-9: continue
        l0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / den
        l1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / den; l2 = 1 - l0 - l1
        m = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
        zz = l0 * z[a] + l1 * z[b] + l2 * z[cc]
        sub = zb[y0:y1 + 1, x0:x1 + 1]; m &= zz > sub
        if not m.any(): continue
        sub[m] = zz[m]
        if inside or (fcol is not None and fcol[i]): col = np.array([0.14, 0.04, 0.05]); img[y0:y1 + 1, x0:x1 + 1][m] = col; continue
        if ON[a] and ON[b] and ON[cc]:
            uu = l0 * UV[a, 0] + l1 * UV[b, 0] + l2 * UV[cc, 0]; vv = l0 * UV[a, 1] + l1 * UV[b, 1] + l2 * UV[cc, 1]
            ti = np.clip((vv * th).astype(int), 0, th - 1); tj = np.clip((uu * tw).astype(int), 0, tw - 1)
            img[y0:y1 + 1, x0:x1 + 1][m] = (T[ti, tj] * shade[i])[m]
        else:
            img[y0:y1 + 1, x0:x1 + 1][m] = skin * shade[i]
    return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))

if __name__ == '__main__' and os.environ.get('FACE', 'eyes') == 'painted':
    texN = paint_face(False); texR = paint_face(True)
    texN.save(OUT + '/alien_face.png'); texR.save(OUT + '/alien_face_red.png')
    T2 = fore((0, 1, 0), -150, ((0, 1, 0), 145), fwd=0, out=4, extra=hunch(1.5))
    VS = smooth_face(VA)
    UV, ON = face_uv(VS)
    try: font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 20); small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
    except Exception: font = small = ImageFont.load_default()
    rows = []
    for nm, wd, op, tex in (('normal: jaw closed', 1.0, 0, texN), ('the scream: jaw open, eyes red', 1.6, 70, texR)):
        JW = dict(top=0.909, soft=0.008, hinge=(0, 0.93, -0.04))       # the split is the painted mouth line
        Vc = pose(T2, jaw_bell(VS, wd, 0, **JW)); Vj = pose(T2, jaw_bell(VS, wd, op, **JW))
        ar = lambda X: np.linalg.norm(np.cross(X[F[:, 1]] - X[F[:, 0]], X[F[:, 2]] - X[F[:, 0]]), axis=1)
        mouthF = ar(Vj) > 1.8 * ar(Vc) + 1e-7
        Vf, FF = forelimbs(Vj); keep = ~np.isin(NODE, FORE_NODES); fmask = keep[F].all(1)
        UVf = np.vstack([UV, np.zeros((len(Vf) - len(UV), 2))]); ONf = np.concatenate([ON, np.zeros(len(Vf) - len(ON), bool)])
        mF = np.concatenate([mouthF[fmask], np.zeros(len(FF) - fmask.sum(), bool)])
        Hc = Vj[LAB == 'head'].mean(0) + np.array([0, -0.07, 0])
        cells = [render_tex(Vf, UVf, ONf, tex, a, FF, fcol=mF) for a in (0, np.radians(35))]
        for a in (0, np.radians(30)):
            cells.append(render_tex(Vf - Hc, UVf, ONf, tex, a, FF, sc=900, oy=235, fcol=mF))
        sheet = Image.new('RGB', (280 * len(cells), 470 + 34), (30, 30, 36)); dr = ImageDraw.Draw(sheet)
        for k, ci in enumerate(cells):
            sheet.paste(ci, (280 * k, 34)); dr.text((280 * k + 6, 38), ['front', '3/4', 'face', 'face 3/4'][k], fill=(160, 160, 170), font=small)
        dr.text((8, 6), nm, fill=(235, 225, 220), font=font); rows.append(sheet); print(nm)
    out = Image.new('RGB', (rows[0].width, sum(r.height for r in rows))); y = 0
    for r in rows: out.paste(r, (0, y)); y += r.height
    out.save(OUT + '/alien_face_sheet.png')

if __name__ == '__main__' and os.environ.get('FACE', 'eyes') == 'eyes':
    T2 = fore((0, 1, 0), -150, ((0, 1, 0), 145), fwd=0, out=4, extra=hunch(1.5))
    VS = smooth_face(VA); UV, ON = face_uv(VS)
    try: font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 20); small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
    except Exception: font = small = ImageFont.load_default()
    JW = dict(top=0.909, soft=0.008, hinge=(0, 0.93, -0.04))
    rows = []
    for nm, kind in EYES.items():
        cells = []
        for wd, op, red in ((1.0, 0, False), (1.6, 70, True)):
            tex = paint_eyes(kind, red)
            Vc = pose(T2, jaw_bell(VS, wd, 0, **JW)); Vj = pose(T2, jaw_bell(VS, wd, op, **JW))
            ar = lambda X: np.linalg.norm(np.cross(X[F[:, 1]] - X[F[:, 0]], X[F[:, 2]] - X[F[:, 0]]), axis=1)
            mouthF = ar(Vj) > 1.8 * ar(Vc) + 1e-7
            Vf, FF = forelimbs(Vj); keep = ~np.isin(NODE, FORE_NODES); fmask = keep[F].all(1)
            UVf = np.vstack([UV, np.zeros((len(Vf) - len(UV), 2))]); ONf = np.concatenate([ON, np.zeros(len(Vf) - len(ON), bool)])
            mF = np.concatenate([mouthF[fmask], np.zeros(len(FF) - fmask.sum(), bool)])
            Hc = Vj[LAB == 'head'].mean(0) + np.array([0, -0.05, 0])
            cells.append(render_tex(Vf, UVf, ONf, tex, np.radians(20), FF, fcol=mF))
            cells.append(render_tex(Vf - Hc, UVf, ONf, tex, 0, FF, sc=700, oy=235, fcol=mF))
        sheet = Image.new('RGB', (280 * len(cells), 470 + 34), (30, 30, 36)); dr = ImageDraw.Draw(sheet)
        for k, ci in enumerate(cells):
            sheet.paste(ci, (280 * k, 34)); dr.text((280 * k + 6, 38), ['closed', 'face', 'scream', 'face'][k], fill=(160, 160, 170), font=small)
        dr.text((8, 6), nm, fill=(235, 225, 220), font=font); rows.append(sheet); print(nm)
    out = Image.new('RGB', (rows[0].width, sum(r.height for r in rows))); y = 0
    for r in rows: out.paste(r, (0, y)); y += r.height
    out.save(OUT + '/alien_eyes_sheet.png')


# ---------------- v2 (user's reference, ideas only): ribs and a sunken belly, bigger hands
BX0, BX1, BY0, BY1 = -0.13, 0.13, 0.48, 0.86
def paint_ribs():
    W, H = 256, 384
    dk = Image.new('L', (W, H), 0); lt = Image.new('L', (W, H), 0)
    P = lambda x, y: ((x - BX0) / (BX1 - BX0) * W, (BY1 - y) / (BY1 - BY0) * H)
    d1 = ImageDraw.Draw(dk); d2 = ImageDraw.Draw(lt)
    for k in range(7):                                             # ribs: arcs down and out from the breastbone
        y0 = 0.80 - 0.028 * k
        for sx in (-1, 1):
            pts = [P(sx * (0.012 + 0.09 * t), y0 - 0.035 * t ** 1.6 - 0.002 * k * t) for t in np.linspace(0, 1, 14)]
            d1.line([(a, b + 5) for a, b in pts], fill=150, width=5)   # the shadow under each rib
            d2.line(pts, fill=110, width=4)                             # the rib catching light
    d1.line([P(0, 0.82), P(0, 0.70)], fill=120, width=4)              # breastbone
    d1.ellipse([*P(-0.06, 0.66), *P(0.06, 0.55)], fill=120)           # sunken belly under the ribcage
    for sx in (-1, 1): d1.line([P(sx * 0.07, 0.83), P(sx * 0.11, 0.78)], fill=110, width=6)   # collarbones
    dk = np.array(dk.filter(ImageFilter.GaussianBlur(3))).astype(float) / 255
    lt = np.array(lt.filter(ImageFilter.GaussianBlur(2))).astype(float) / 255
    img = np.tile(SKIN_RGB, (H, W, 1)) * (1 - 0.75 * dk[..., None]); img = img + (255 - img) * 0.45 * lt[..., None]
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))

def gaunt(V):
    """sunken belly, narrow waist under a slightly flared ribcage"""
    V = V.copy(); tor = LAB == 'torso'; y = V[:, 1]
    belly = tor & (y > 0.53) & (y < 0.68) & (V[:, 2] > 0)
    V[belly, 2] *= 0.55 + 0.45 * np.abs(y[belly] - 0.605) / 0.075
    waist = tor & (y > 0.56) & (y < 0.66); V[waist, 0] *= 0.85
    cage = tor & (y >= 0.68) & (y < 0.80); V[cage, 0] *= 1.06
    return V

def forelimbs_big(V, palm=0.1, finger=0.14):
    """the T-rex hands, oversized: longer palm, four long fingers, knuckles"""
    R, t = pose.last
    keep = ~np.isin(NODE, FORE_NODES); Fk = F[keep[F].all(1)]
    Vs, Fs = [V], [Fk]; base = [len(V)]
    def add(vt, ft): Vs.append(vt); Fs.append(ft + base[0]); base[0] += len(vt)
    for e, w, sx in ((15, 16, 1), (26, 27, -1)):
        add(*tube(t[e], t[w], 0.017, 0.012))
        hd = R[w] @ np.array([sx, 0, 0]); side = R[w] @ np.array([0, 0, 1])
        pe = t[w] + hd * palm
        add(*tube(t[w], pe, 0.016, 0.026))
        for f in (-1.5, -0.5, 0.5, 1.5):
            k0 = pe + side * 0.012 * f; k1 = k0 + hd * finger * 0.55 + side * 0.006 * f
            add(*tube(k0, k1, 0.007, 0.0065, 6)); add(*tube(k1, k1 + hd * finger * 0.45 + side * 0.004 * f, 0.0065, 0.003, 6))
    return np.vstack(Vs), np.vstack(Fs)

def render_layers(V, layers, ang, Fz, W=280, H=470, sc=240, oy=None, fcol=None):
    """as render_tex, with several planar texture layers: [(UV, ON, tex), ...] (a face takes the first whose 3 vertices are ON)"""
    Ts = [np.asarray(tx).astype(float) / 255 for _, _, tx in layers]
    c, s = np.cos(ang), np.sin(ang)
    X = V @ np.array([[c, 0, -s], [0, 1, 0], [s, 0, c]]).T
    sx = W / 2 + X[:, 0] * sc; sy = (H - 14 if oy is None else oy) - X[:, 1] * sc; z = X[:, 2]
    img = np.tile(BG, (H, W, 1)); zb = np.full((H, W), -1e9)
    N = np.cross(X[Fz[:, 1]] - X[Fz[:, 0]], X[Fz[:, 2]] - X[Fz[:, 0]]); N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-12
    Lt = np.array([0.35, 0.55, 0.75]); Lt /= np.linalg.norm(Lt)
    shade = 0.32 + 0.68 * np.clip(N @ Lt, 0, 1) + 0.15 * (1 - np.abs(N[:, 2])) ** 3
    skin = SKIN_RGB / 255
    for i, (a, b, cc) in enumerate(Fz):
        inside = N[i, 2] <= 0
        xs = np.array([sx[a], sx[b], sx[cc]]); ys = np.array([sy[a], sy[b], sy[cc]])
        x0, x1 = int(max(0, xs.min())), int(min(W - 1, xs.max() + 1)); y0, y1 = int(max(0, ys.min())), int(min(H - 1, ys.max() + 1))
        if x0 > x1 or y0 > y1: continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        den = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(den) < 1e-9: continue
        l0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / den
        l1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / den; l2 = 1 - l0 - l1
        m = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
        zz = l0 * z[a] + l1 * z[b] + l2 * z[cc]
        sub = zb[y0:y1 + 1, x0:x1 + 1]; m &= zz > sub
        if not m.any(): continue
        sub[m] = zz[m]
        if inside or (fcol is not None and fcol[i]): img[y0:y1 + 1, x0:x1 + 1][m] = np.array([0.14, 0.04, 0.05]); continue
        col = None
        for (UV, ON, _), T in zip(layers, Ts):
            if ON[a] and ON[b] and ON[cc]:
                th, tw = T.shape[:2]
                uu = l0 * UV[a, 0] + l1 * UV[b, 0] + l2 * UV[cc, 0]; vv = l0 * UV[a, 1] + l1 * UV[b, 1] + l2 * UV[cc, 1]
                col = T[np.clip((vv * th).astype(int), 0, th - 1), np.clip((uu * tw).astype(int), 0, tw - 1)] * shade[i]; break
        img[y0:y1 + 1, x0:x1 + 1][m] = col[m] if col is not None else skin * shade[i]
    return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))

def sockets(V, kind, depth=0.055, brow=0.014):
    """user: the eyes set deeper in the head - each eye's area pushed in (deepest at its centre), the skin just above
       pushed out a little into a brow that shades it"""
    rx, ry, ey, ex, tilt = kind; V = V.copy(); hd = (LAB == 'head') & (V[:, 2] > 0)
    for sx in (-1, 1):
        dx = (V[:, 0] - sx * ex) / (rx * 1.25); dy = (V[:, 1] - ey) / (ry * 1.25); r2 = dx * dx + dy * dy
        inner = hd & (r2 < 1); k = (1 - r2[inner]) ** 1.5
        cen = np.array([sx * ex * 0.6, ey, 0.0]); dirn = V[inner] - cen; dirn /= np.linalg.norm(dirn, axis=1, keepdims=True)
        V[inner] -= dirn * (depth * k)[:, None]
        bw = hd & (dy > 0.6) & (dy < 1.6) & (np.abs(dx) < 1.0)
        V[bw, 2] += brow * (1 - np.abs(dx[bw])) * np.sin((dy[bw] - 0.6) / 1.0 * np.pi)
    return V

if __name__ == '__main__' and os.environ.get('FACE', 'eyes') == 'v2':
    T2 = fore((0, 1, 0), -150, ((0, 1, 0), 145), fwd=0, out=4, extra=hunch(1.5))
    VS = gaunt(smooth_face(VA)); UV, ON = face_uv(VS)          # texture placed before the sockets are pushed in
    VS = sockets(VS, EYES['E3 huge, far apart'])
    UVb = np.stack([(VS[:, 0] - BX0) / (BX1 - BX0), (BY1 - VS[:, 1]) / (BY1 - BY0)], 1)
    ONb = (LAB == 'torso') & (VS[:, 2] > -0.01)
    ribs = paint_ribs(); ribs.save(OUT + '/alien_ribs.png')
    try: font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 20); small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
    except Exception: font = small = ImageFont.load_default()
    JW = dict(top=0.909, soft=0.008, hinge=(0, 0.93, -0.04)); kind = EYES['E3 huge, far apart']
    rows = []
    for nm, wd, op, red in (('the design: T2, E3 eyes, ribs, sunken belly, big hands', 1.0, 0, False), ('the scream', 1.6, 70, True)):
        tex = paint_eyes(kind, red)
        Vc = pose(T2, jaw_bell(VS, wd, 0, **JW)); Vj = pose(T2, jaw_bell(VS, wd, op, **JW))
        ar = lambda X: np.linalg.norm(np.cross(X[F[:, 1]] - X[F[:, 0]], X[F[:, 2]] - X[F[:, 0]]), axis=1)
        mouthF = ar(Vj) > 1.8 * ar(Vc) + 1e-7
        Vf, FF = forelimbs_big(Vj); keep = ~np.isin(NODE, FORE_NODES); fmask = keep[F].all(1)
        ext = len(Vf) - len(UV)
        L1 = (np.vstack([UV, np.zeros((ext, 2))]), np.concatenate([ON, np.zeros(ext, bool)]), tex)
        L2 = (np.vstack([UVb, np.zeros((ext, 2))]), np.concatenate([ONb, np.zeros(ext, bool)]), ribs)
        mF = np.concatenate([mouthF[fmask], np.zeros(len(FF) - fmask.sum(), bool)])
        cells = [render_layers(Vf, [L1, L2], a, FF, fcol=mF) for a in (0, np.radians(35), np.radians(90))]
        for ang in (np.radians(-30), np.radians(25)):
            Hc = Vj[LAB == 'head'].mean(0) + np.array([0, -0.06, 0])
            cells.append(render_layers(Vf - Hc, [L1, L2], ang, FF, sc=700, oy=235, fcol=mF))
        sheet = Image.new('RGB', (280 * len(cells), 470 + 34), (30, 30, 36)); dr = ImageDraw.Draw(sheet)
        for k, ci in enumerate(cells):
            sheet.paste(ci, (280 * k, 34)); dr.text((280 * k + 6, 38), ['front', '3/4', 'side', 'face', 'face'][k], fill=(160, 160, 170), font=small)
        dr.text((8, 6), nm, fill=(235, 225, 220), font=font); rows.append(sheet); print(nm)
    out = Image.new('RGB', (rows[0].width, sum(r.height for r in rows))); y = 0
    for r in rows: out.paste(r, (0, y)); y += r.height
    out.save(OUT + '/alien_v2.png')
