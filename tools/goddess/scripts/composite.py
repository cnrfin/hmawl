"""Hair composite: Celia (hair removed) + Flora's hair (fringe/cap), fitted to Celia's face, + generated
buns, all in the goddess's green (luminance -> her hair texture's colour ramp)."""
import sys, numpy as np
sys.path[:0] = ['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess',
                '/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/model',
                '/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/pm']
import restyle, awlmodel, wally, hairswap
from PIL import Image
G = '/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/girls/'
lum = restyle.lum

def face_box(M, head_bones, face_sel=(2,)):
    B = M['bones']
    vs = sorted({i for tid, tris, _ in M['groups'] if tid in face_sel for t in tris for i in t[0]
                 if B[i] and set(B[i]) <= set(head_bones)})
    F = M['V'][vs]; return F.min(0), F.max(0)

def goddess_ramp():
    r = restyle.ramp_from(restyle.SRC + 'hair_315_00.png', sel=lambda a: (a[:, 1] > a[:, 0] + 10) & (a[:, 1] > a[:, 2]))
    return r

HR = (11, 84, 61, 191)               # Flora's hair swatch in her body sheet (x0, y0, x1, y1)
def flora_hair(cel_box, ramp):
    F = awlmodel.load(G + 'flora_0/flora_0'); B = F['bones']
    tex = wally.tpl(G + 'flora_0/flora_0_b0.tpl', 0); H, W = tex.shape[:2]
    inside = lambda u, v: HR[0] <= u <= HR[2] and HR[1] <= v <= HR[3]
    fmin0, fmax0 = face_box(F, (42,))
    tris = []
    for tid, ts, vst in F['groups']:
        if tid != 255: continue
        for pi, ti in ts:
            if not all(B[v] == [42] for v in pi): continue
            u = np.mean([F['UV'][t][0] % 1 for t in ti]) * W; v = np.mean([F['UV'][t][1] % 1 for t in ti]) * H
            if inside(u, v) and max(F['V'][x][1] for x in pi) > fmin0[1] + 0.05: tris.append((pi, ti))
    used = np.zeros((H, W), bool); used[HR[1]:HR[3] + 1, HR[0]:HR[2] + 1] = True
    rgb = tex[..., :3]; L = lum(rgb); lo, hi = np.percentile(L[used], 1), np.percentile(L[used], 99.5)
    soft = ramp[np.linspace(90, 245, 256).astype(int)]          # softer than Flora's contrast
    tex2 = tex.copy(); tex2[used] = restyle.recolour(tex[used], soft, lo, hi)
    cmin, cmax = cel_box
    s = (cmax - cmin) / (fmax0 - fmin0); s[2] = (s[0] + s[1]) / 2
    P = (F['V'] - (fmin0 + fmax0) / 2) * s + (cmin + cmax) / 2
    return dict(P=P, UV=F['UV'], tris=tris, tex=tex2)

def bun(center, radii, tex, rings=8, segs=14):
    """ellipsoid bun; strands (horizontal in Flora's swatch) run pole to pole: latitude -> texture x,
    longitude -> texture y, inside the left half of the swatch (away from the parting line)"""
    H, W = tex.shape[:2]
    x0, x1, y0, y1 = (HR[0] + 2) / W, (HR[0] + 22) / W, (HR[1] + 4) / H, (HR[3] - 4) / H
    P, UV, tris = [], [], []
    for i in range(rings + 1):
        th = np.pi * i / rings
        for j in range(segs + 1):
            ph = 2 * np.pi * j / segs
            d = np.array([np.sin(th) * np.cos(ph), np.cos(th), np.sin(th) * np.sin(ph)])
            P.append(center + d * radii)
            UV.append((x0 + (x1 - x0) * i / rings, y0 + (y1 - y0) * j / segs))
    for i in range(rings):
        for j in range(segs):
            a = i * (segs + 1) + j; b = a + 1; c = a + segs + 1; d = c + 1
            tris += [((a, c, b), (a, c, b)), ((b, c, d), (b, c, d))]
    return np.array(P), np.array(UV), tris
