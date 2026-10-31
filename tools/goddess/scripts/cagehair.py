"""Goddess hair as planned quad geometry (AWL-style, from measurements of Celia/Muffy/Lumina/Flora):
crown+back sheet in columns (strand direction = column), D-shaped back slab closed against the neck with
a hem of V points, 5 wedge fringe spikes, 2 flattened S tendrils."""
import sys, numpy as np
sys.path[:0] = ['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess',
                '/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/blank']
import gd2
HC = np.array([0.0, 1.08, -0.01])
def head(P): return gd2.head_sdf(np.atleast_2d(P), ears=False)
def surf(d):
    d = d / np.linalg.norm(d); r = 0.2
    for _ in range(40): r -= head(HC + d * r)[0] * 0.9
    return HC + d * r
def hdir(th, e):
    th, e = np.radians(th), np.radians(e); return np.array([np.cos(e) * np.sin(th), np.sin(e), -np.cos(e) * np.cos(th)])

C = dict(top_e=80.0, crown_off=0.032, back_extra=0.035, bump_th=62.0, bump_e=50.0, bump_h=0.0, bump_w=21.0,
         nape_y=0.99, hem_y=0.60, hem_amp=0.0, tips=(0.0, 36.0, 72.0), groove=0.008, n_locks=14, rows=13, rows_head=8, temple_vol=0.03, part=0.012, top_dip=0.0, curls=(-77, -51, -26, 0, 26, 51, 77), curl_r=0.046, hem_flat=0.68)
def zf(y): return np.interp(y, [0.55, 0.95, 1.02], [-0.08, -0.08, -0.05])
def zb(y): return np.interp(y, [0.55, 0.70, 0.85, 1.00], [-0.215, -0.24, -0.255, -0.27])
def rx(y): return np.interp(y, [0.55, 0.70, 0.82, 1.00], [0.20, 0.225, 0.245, 0.25])
def offset(th, e, c=C):
    o = c['crown_off'] + c['back_extra'] * max(0, np.cos(np.radians(th))) * np.exp(-((e - 5) / 30) ** 2)
    for s in (1, -1):
        da = np.hypot((th - s * c['bump_th']) * np.cos(np.radians(e)), e - c['bump_e'])
        o += c['bump_h'] * np.exp(-(da / c['bump_w']) ** 2)
    o -= c['top_dip'] * np.exp(-((e - 90) / 22) ** 2)                      # dip between the two bumps
    a = abs(((th + 180) % 360) - 180)                                   # 180 = front centre
    o += c['temple_vol'] * np.exp(-((a - 145) / 18) ** 2) * np.exp(-((e - 15) / 22) ** 2)   # swept volume over the temples
    o -= c['part'] * np.exp(-((a - 180) / 5) ** 2) * (e > 15)          # centre parting
    return o
def head_pt(th, e, c=C):
    d = hdir(th, e); return surf(d) + d * offset(th, e, c)
def slab_pt(beta, y, c=C, groove=True):
    b = np.radians(beta); r_z = zf(y) - zb(y)
    p = np.array([rx(y) * np.sin(b), y, zf(y) - r_z * np.cos(b)])
    if groove:
        g = c['groove'] * (0.5 - 0.5 * np.cos(np.radians(beta) * c['n_locks']))
        n = np.array([np.sin(b) / rx(y), 0, -np.cos(b) / r_z]); n /= np.linalg.norm(n); p -= n * g
    return p
def hem_y(beta, c=C):
    if c.get('curls'):          # notch between curls so each lock tapers into its own curl
        cs = c['curls']; d = min(abs(beta - x) for x in cs); gap = (cs[1] - cs[0]) / 2
        return c['hem_flat'] + 0.05 * np.clip((d - gap * 0.45) / (gap * 0.55), 0, 1)
    dist = min(abs(beta - t) for t in [x * s for x in c['tips'] for s in (1, -1)])
    return c['hem_y'] + c['hem_amp'] * min(1.0, dist / 18.0)
FRONT_END = ([80, 92.5, 105, 117.5, 130, 142.5, 155, 167.5, 180], [None, 1.085, 1.07, 1.06, 1.08, 1.13, 1.19, 1.25, 1.28])   # centre-parted arch (Celia/Flora)
def column(th, c=C):
    """dense polyline of one column from the crown down to its end, and whether it is a back (slab) column"""
    a = abs(((th + 180) % 360) - 180)
    pts = []
    if a <= 80.0001:                       # back: head then slab
        beta = np.clip(th * 90 / 80, -90, 90)
        e = c['top_e']
        while True:
            p = head_pt(th, e, c)
            if p[1] < c['nape_y'] + 0.06 or e < -60: break
            pts.append(p); e -= 2.0
        n_head = len(pts); y0 = pts[-1][1]; ye = hem_y(beta, c)
        for y in np.linspace(min(y0 - 0.02, c['nape_y']), ye, 30):
            q = slab_pt(beta, y, c); w = np.clip((y0 - y) / 0.10, 0, 1)
            pts.append(pts[-1] * (1 - w) + q * w if w < 1 else q)
        return np.array(pts), True, (beta, n_head)
    ye = np.interp(a, FRONT_END[0][1:], FRONT_END[1][1:])
    e = c['top_e']
    while True:
        p = head_pt(th, e, c)
        if p[1] < ye: break
        pts.append(p); e -= 1.5
    return np.array(pts), False, None
def resample(poly, n):
    L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(poly, axis=0), axis=1))]
    t = np.linspace(0, L[-1], n); return np.stack([np.interp(t, L, poly[:, k]) for k in range(3)], 1)

class Mesh:
    def __init__(s): s.V = []; s.F = []; s.UV = []; s.part = []
    def v(s, p, uv=(0, 0)): s.V.append(np.asarray(p, float)); s.UV.append(uv); return len(s.V) - 1
    def quad(s, a, b, c_, d, part):
        s.F.append((a, b, c_)); s.F.append((a, c_, d)); s.part += [part, part]
    def tri(s, a, b, c_, part): s.F.append((a, b, c_)); s.part.append(part)

def build(c=C):
    M = Mesh(); R = c['rows']
    ths = [b * 80 / 90 for b in range(-90, 91, 9)] + [80 + 12.5 * k for k in range(1, 16)]   # 21 back + 15 front
    cols = []
    for th in ths:
        poly, back, info = column(th, c)
        if back:
            beta, nh = info; RH = c['rows_head']
            P = np.vstack([resample(poly[:nh], RH), resample(poly[nh - 1:], R - RH + 1)[1:]])
            cols.append((P, back, beta, th))
        else: cols.append((resample(poly, R), back, None, th))
    nC = len(cols)
    G = [[M.v(cols[j][0][i], (((cols[j][3] + 180) % 360) / 360, i / (R - 1))) for i in range(R)] for j in range(nC)]
    pole = M.v(head_pt(0, 90, c), (0.5, 0.0))
    for j in range(nC):
        k = (j + 1) % nC
        M.tri(pole, G[k][0], G[j][0], 'crown')
        for i in range(R - 1): M.quad(G[j][i], G[k][i], G[k][i + 1], G[j][i + 1], 'crown')
    # lip under the hairline (front/side columns): the edge folds into the skull -> reads as thick
    back_idx = [j for j in range(nC) if cols[j][1]]
    for j in range(nC):
        k = (j + 1) % nC
        if cols[j][1] and cols[k][1]: continue
        for jj in (j, k):
            if not hasattr(M, 'lip'): M.lip = {}
            if jj not in M.lip:
                p = M.V[G[jj][-1]]; M.lip[jj] = M.v(p + (HC - p) / np.linalg.norm(HC - p) * 0.025, (M.UV[G[jj][-1]][0], 1.0))
        M.quad(G[j][-1], G[k][-1], M.lip[k], M.lip[j], 'lip')
    # slab inner face (flat, against the neck/back), rows below the nape, closing the hem and the side edges
    nb = len(back_idx); rows_in = []
    ys_top = c['nape_y'] + 0.02
    inner = {}
    for j in back_idx:
        beta = cols[j][2]; col = M.V
        bottom = M.V[G[j][-1]]
        ys = np.linspace(ys_top, bottom[1], 6)
        inner[j] = []
        for y in ys:
            x = rx(y) * np.sin(np.radians(beta)) * 0.96
            inner[j].append(M.v((x, y, zf(y) + 0.004), (M.UV[G[j][0]][0], 1.0)))
        inner[j][-1] = G[j][-1]                        # hem: inner bottom = outer bottom (closed, pointed)
    for a, b in zip(back_idx, back_idx[1:]):
        for i in range(5): M.quad(inner[b][i], inner[a][i], inner[a][i + 1], inner[b][i + 1], 'inner')
    # side edges: inner edge columns joined to the outer edge column (beta = +-90 lies on the front plane)
    for j, sgn in ((back_idx[0], -1), (back_idx[-1], 1)):
        outer = [G[j][i] for i in range(R) if M.V[G[j][i]][1] <= ys_top]
        top_o = outer[0]
        for i in range(5):
            # pair the inner edge vertices with outer ones at similar heights
            yi = M.V[inner[j][i]][1]; yi2 = M.V[inner[j][i + 1]][1]
            oa = min(outer, key=lambda q: abs(M.V[q][1] - yi)); ob = min(outer, key=lambda q: abs(M.V[q][1] - yi2))
            if oa != ob:
                if sgn > 0: M.quad(oa, inner[j][i], inner[j][i + 1], ob, 'inner')
                else: M.quad(inner[j][i], oa, ob, inner[j][i + 1], 'inner')
    return M, cols, G

# ---------------------------------------------------------------- wedge spikes and tendrils
def prism(M, path, widths, thick, normals, sides=3, part='lock', cap_root=True):
    """closed lock along path: cross-section triangle (sides 3, base on the surface) or diamond (4), tip pointed"""
    rings = []
    n_ = len(path)
    for i in range(n_ - 1):
        t = path[min(i + 1, n_ - 1)] - path[max(i - 1, 0)]; t /= np.linalg.norm(t)
        nrm = normals[i] - t * (normals[i] @ t); nrm /= np.linalg.norm(nrm); sd = np.cross(t, nrm)
        w, h = widths[i] / 2, thick[i]
        if sides == 3: sec = [path[i] - sd * w, path[i] + nrm * h, path[i] + sd * w]
        else: sec = [path[i] - sd * w, path[i] + nrm * h / 2, path[i] + sd * w, path[i] - nrm * h / 2]
        rings.append([M.v(p, (0.1 + 0.15 * k / sides, i / (n_ - 1))) for k, p in enumerate(sec)])
    tip = M.v(path[-1], (0.17, 1.0))
    for a, b in zip(rings, rings[1:]):
        for k in range(sides): M.quad(a[k], a[(k + 1) % sides], b[(k + 1) % sides], b[k], part)
    for k in range(sides): M.tri(rings[-1][k], rings[-1][(k + 1) % sides], tip, part)
    if cap_root:
        r = rings[0]
        for k in range(1, sides - 1): M.tri(r[0], r[k + 1], r[k], part)
def add_fringe(M, c=C):
    for th, tip_y, w in ((-150, 1.105, 0.075), (-165, 1.15, 0.07), (180, 1.125, 0.08), (165, 1.155, 0.07), (150, 1.10, 0.075)):
        path = []; nr = []
        for e in np.linspace(62, 20, 7):
            d = hdir(th + (0 if th == 180 else np.sign(th) * -4 * (62 - e) / 42), e); p = surf(d)
            path.append(p + d * 0.004); nr.append(d)
        path = np.array(path)
        # pull down onto the forehead to tip_y
        k = np.linspace(0, 1, len(path)) ** 1.5
        for i in range(len(path)):
            if path[i][1] > tip_y or i == 0: continue
        last = path[-1]; tgt = last.copy(); tgt[1] = tip_y; d_ = tgt - HC; tgt = surf(d_) + d_ / np.linalg.norm(d_) * 0.004
        path[-1] = tgt
        widths = w * (1 - 0.85 * np.linspace(0, 1, len(path)) ** 1.2); thick = 0.030 * (1 - 0.8 * np.linspace(0, 1, len(path)))
        prism(M, path, widths, thick, nr, 3, 'fringe')
def add_tendrils(M, c=C):
    """curtain bangs (measured on Celia/Flora): a thick lock from the parting sweeps out over the
    forehead edge, standing off the hairline (volume), and falls beside the face to the chin, waving gently"""
    for s in (1, -1):
        path = []; nr = []; wid = []; thk = []
        for th, e, lift, w, tk in ((175, 62, 0.010, 0.08, 0.035), (167, 48, 0.022, 0.11, 0.045), (157, 34, 0.034, 0.12, 0.055), (147, 21, 0.040, 0.12, 0.062)):
            d = hdir(s * th, e); p = surf(d) + d * (offset(s * th, e, c) + lift)
            path.append(p); nr.append(d); wid.append(w); thk.append(tk)
        p0 = path[-1]; n = 12
        for t in np.linspace(0, 1, n)[1:]:
            y = p0[1] - t * 0.36
            x = s * (abs(p0[0]) + 0.005 * t + 0.014 * np.sin(t * 1.5 * 2 * np.pi) + 0.03 * max(0, t - 0.85) / 0.15)
            z = p0[2] - 0.03 * t + 0.015 * np.sin(t * 1.5 * 2 * np.pi + 1.0)
            path.append((x, y, z)); nr.append(np.array([s, 0, 0.9]))
            wid.append(0.12 * (1 - 0.6 * t ** 1.4)); thk.append(0.062 * (1 - 0.5 * t))
        nr = [v / np.linalg.norm(v) for v in nr]
        for k in (3, 4): nr[k] = (nr[k - 1] + nr[k + 1]) / 2; nr[k] /= np.linalg.norm(nr[k])
        prism(M, np.array(path, float), np.array(wid), np.array(thk), nr, 4, 'tendril')
def full(c=C):
    M, cols, G = build(c); add_tendrils(M, c); add_buns(M, c); add_curls(M, c)
    return np.array(M.V), np.array(M.F), np.array(M.UV), np.array(M.part)

def add_buns(M, c=C, center=(0.195, 1.36, -0.07), r=(0.125, 0.118, 0.125), rings=6, segs=10):
    """original goddess's buns: two round buns high on the back corners of the head (strands swirl round)"""
    for s_ in (1, -1):
        cen = np.array(center) * [s_, 1, 1]; ids = []
        for i in range(1, rings):
            th = np.pi * i / rings; row = []
            for j in range(segs):
                ph = 2 * np.pi * j / segs
                d = np.array([np.sin(th) * np.cos(ph), np.cos(th), np.sin(th) * np.sin(ph)])
                row.append(M.v(cen + d * r, (0.1 + 0.2 * ((j / segs + 0.35 * i / rings) % 1), i / rings)))
            ids.append(row)
        top = M.v(cen + [0, r[1], 0], (0.2, 0.0)); bot = M.v(cen - [0, r[1], 0], (0.2, 1.0))
        for j in range(segs):
            k = (j + 1) % segs
            M.tri(top, ids[0][j], ids[0][k], 'bun'); M.tri(bot, ids[-1][k], ids[-1][j], 'bun')
            for i in range(rings - 2): M.quad(ids[i][j], ids[i + 1][j], ids[i + 1][k], ids[i][k], 'bun')
def add_curls(M, c=C, segs=8):
    """Chris-style barrel curls rolled under the hem, one per lock, axis along the hem"""
    y = c['hem_flat'] + 0.012; r0 = c['curl_r']
    for b in c['curls']:
        r = r0 * (1.25 if abs(b) > 70 else 1.0)
        p = slab_pt(b, y, c, groove=False); p2 = slab_pt(b + 2, y, c, groove=False)
        ax = p2 - p; ax /= np.linalg.norm(ax)
        out = np.array([np.sin(np.radians(b)), 0, -np.cos(np.radians(b))]); out -= ax * (out @ ax); out /= np.linalg.norm(out)
        cen = p + out * r * 0.35 - np.array([0, r * 0.05, 0])
        half = rx(y) * np.sin(np.radians(13)) * 0.80
        up = np.cross(ax, out)
        rings = []
        for t, sc in ((-1, 0.72), (-0.4, 1.0), (0.4, 1.0), (1, 0.72)):
            rings.append([M.v(cen + ax * half * t + (out * np.cos(2 * np.pi * k / segs) + up * np.sin(2 * np.pi * k / segs)) * r * sc,
                              (0.1 + 0.2 * (t + 1) / 2, k / segs)) for k in range(segs)])
        for a_, b_ in zip(rings, rings[1:]):
            for k in range(segs):
                k2 = (k + 1) % segs; M.quad(a_[k], a_[k2], b_[k2], b_[k], 'curl')
        rings = [rings[0], rings[-1]]
        cA = M.v(cen - ax * half, (0.15, 0.5)); cB = M.v(cen + ax * half, (0.15, 0.5))
        for k in range(segs):
            k2 = (k + 1) % segs; M.tri(cA, rings[0][k2], rings[0][k], 'curl'); M.tri(cB, rings[1][k], rings[1][k2], 'curl')
