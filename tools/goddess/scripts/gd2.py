"""Custom goddess v2 on the blank body: princess (ch_205) hair fitted to the blank head, recoloured
to the goddess green (AWL-desaturated)."""
import sys, numpy as np
sys.path[:0] = ['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/model',
                '/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/pm',
                '/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess',
                '/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/blank']
import loaddae, restyle
from PIL import Image
PD = '/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/princess_in/Witch Princess/'
GD = '/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/model/Harvest Goddess copy/'
def princess():
    return loaddae.load(PD + 'ch_205.dae', {'body_205': 'body_205_00.png', 'face_205': 'face_205_00.png',
                                            'hair_205': 'hair_205_00.png', 'lam_eye_000': 'eye_205.00.png'})
def goddess():
    return loaddae.load(GD + 'ch_315.dae', {'body_315': 'body_315_00.png', 'face_315': 'face_315_00.png',
                                           'hair_315': 'hair_315_00.png', 'lam_eye_000': 'eye_315.00.png'})
# princess head (face mesh, Head bone): x +-24, chin y 114.1, face front z 19.2 -> blank head
S = 0.464 / 48.0
OFF = np.array([0.0, 0.871 - 114.1 * S, 0.201 - 19.2 * S])
def fit(P, s=S, off=OFF, dy=0.0, dz=0.0): return P * s + off + [0, dy, dz]

def desat(rgb, k):
    l = (rgb * [0.3, 0.59, 0.11]).sum(-1, keepdims=True); return l + (rgb - l) * k
def green_hair_tex(sat=0.72):
    """princess hair texture, luminance mapped onto the goddess hair's green ramp, then desaturated (AWL)"""
    h = [m for m in princess()[0] if m['mat'] == 'hair_205'][0]; tex = h['tex'].copy()
    ramp = restyle.ramp_from(GD + 'hair_315_00.png', sel=lambda a: (a[:, 1] > a[:, 0] + 10) & (a[:, 1] > a[:, 2]))
    op = tex[..., 3] > 0; L = restyle.lum(tex[..., :3])
    lo, hi = np.percentile(L[op], 1), np.percentile(L[op], 99.5)
    tex[op] = restyle.recolour(tex[op], ramp, lo, hi)
    tex[..., :3] = desat(tex[..., :3], sat).clip(0, 255)
    return tex

def loop_subdiv(P, UV, T, smooth=1.0):
    """one Loop subdivision of a triangle mesh whose positions and UVs share indices (UV seams =
    duplicated vertices). Smoothing works on welded positions so seams stay closed; open edges use
    the boundary (crease) rules. smooth=0 is plain midpoint subdivision."""
    key = {}; wid = np.array([key.setdefault(tuple(np.round(p, 4)), len(key)) for p in P])
    nW = len(key); WP = np.zeros((nW, 3)); WP[wid] = P
    from collections import defaultdict
    ef = defaultdict(list)                      # welded edge -> opposite welded vertices
    for a, b, c in T:
        for x, y, z in ((a, b, c), (b, c, a), (c, a, b)):
            e = tuple(sorted((wid[x], wid[y]))); ef[e].append(wid[z])
    nb = defaultdict(set); bnb = defaultdict(set)
    for (x, y), opp in ef.items():
        nb[x].add(y); nb[y].add(x)
        if len(opp) == 1: bnb[x].add(y); bnb[y].add(x)
    NW = WP.copy()
    for v in range(nW):
        if bnb[v]:
            if len(bnb[v]) == 2: q = list(bnb[v]); NW[v] = 0.75 * WP[v] + 0.125 * (WP[q[0]] + WP[q[1]])
        else:
            n = len(nb[v]); 
            if n < 3: continue
            beta = (5 / 8 - (3 / 8 + np.cos(2 * np.pi / n) / 4) ** 2) / n
            NW[v] = (1 - n * beta) * WP[v] + beta * WP[list(nb[v])].sum(0)
    def epos(x, y):
        e = tuple(sorted((x, y))); opp = ef[e]
        if len(opp) == 2: return 0.375 * (WP[x] + WP[y]) + 0.125 * (WP[opp[0]] + WP[opp[1]])
        return 0.5 * (WP[x] + WP[y])
    NP = list(P + (NW[wid] - P) * smooth); NUV = list(UV); emap = {}
    def mid(a, b):
        k = (min(a, b), max(a, b))
        if k not in emap:
            p = 0.5 * (P[a] + P[b]); p = p + (epos(wid[a], wid[b]) - p) * smooth
            emap[k] = len(NP); NP.append(p); NUV.append(0.5 * (UV[a] + UV[b]))
        return emap[k]
    NT = []
    for a, b, c in T:
        ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
        NT += [(a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)]
    return np.array(NP), np.array(NUV), np.array(NT)

import blank as BL
def head_sdf(P, ear_grow=1.0, ears=True):
    S = BL.S; m = lambda c, s: np.array(c) * [s, 1, 1]
    d = BL.ell(P, *S['cran']); d = BL.smin(d, BL.ell(P, *S['jaw']), 0.05); d = BL.smin(d, BL.ell(P, *S['chin']), 0.04)
    for s in (1, -1):
        if ears: d = BL.smin(d, BL.ell(P, m(S['ear'][0], s), np.array(S['ear'][1]) * ear_grow), 0.012)
    return d
def head_grad(P, e=1e-3, ears=True):
    g = np.zeros_like(P)
    for k in range(3):
        dd = np.zeros(3); dd[k] = e; g[:, k] = (head_sdf(P + dd, ears=ears) - head_sdf(P - dd, ears=ears)) / (2 * e)
    return g / np.maximum(np.linalg.norm(g, axis=1, keepdims=True), 1e-9)

def weld(P):
    key = {}; return np.array([key.setdefault(tuple(np.round(p, 4)), len(key)) for p in P]), len(key)
def conform(P, T, margin=0.014, iters=30, ear_grow=1.25, ears=True):
    """push hair vertices out of the head (incl. ears) to >= margin; the push spreads to neighbours"""
    wid, n = weld(P); WP = np.zeros((n, 3)); WP[wid] = P
    nb = [set() for _ in range(n)]
    for a, b, c in T:
        for x, y in ((a, b), (b, c), (c, a)): nb[wid[x]].add(wid[y]); nb[wid[y]].add(wid[x])
    D = np.zeros_like(WP)
    for it in range(iters):
        Q = WP + D; d = head_sdf(Q, ear_grow, ears); g = head_grad(Q, ears=ears)
        need = np.maximum(margin - d, 0)
        D += g * need[:, None]
        if it < iters - 1:
            D = 0.5 * D + 0.5 * np.array([D[list(s)].mean(0) if s else D[i] for i, s in enumerate(nb)])
    Q = WP + D
    for _ in range(10):                                   # exact constraint at the end
        d = head_sdf(Q, ear_grow, ears); g = head_grad(Q, ears=ears); Q += g * np.maximum(margin - d, 0)[:, None]
    return Q[wid]

def hairline(theta_deg):
    t = np.abs(theta_deg)
    return np.interp(t, [0, 35, 75, 105, 140, 180], [1.165, 1.15, 1.0, 0.93, 0.89, 0.89])
def cap(BV, BF, off=0.006, uvrect=(0.62, 0.05, 0.86, 0.38)):
    """hair cap: the blank head's faces above the hairline, lifted off the skull, crown texture"""
    th = np.degrees(np.arctan2(BV[:, 0], BV[:, 2]))
    ear = (np.abs(BV[:, 0]) > 0.222) & (np.abs(BV[:, 1] - 1.025) < 0.06)
    inside = (BV[:, 1] > hairline(th)) & ~ear & (BV[:, 1] > 0.87)
    F = [f for f in BF if inside[f].all()]
    used = sorted({i for f in F for i in f}); idx = {v: k for k, v in enumerate(used)}
    P = BV[used] + head_grad(BV[used]) * off
    u0, v0, u1, v1 = uvrect
    UV = np.c_[u0 + (u1 - u0) * (th[used] + 180) / 360, v0 + (v1 - v0) * np.clip((1.33 - BV[used, 1]) / 0.43, 0, 1)]
    return P, UV, np.array([[idx[i] for i in f] for f in F])

def plump(P, T, sharpen=0.8, edge_in=0.007, mid_out=0.006, r=0.035, ear_r=0.09):
    """3D-ify the hair: amplify its folds (unsharp mask on the surface), roll the open edges in towards
    the head and lift lock middles a little, so locks read as rounded clumps instead of cards"""
    import heapq
    wid, n = weld(P); WP = np.zeros((n, 3)); WP[wid] = P
    from collections import defaultdict
    nb = [set() for _ in range(n)]; ef = defaultdict(int); N = np.zeros((n, 3))
    for a, b, c in T:
        fn = np.cross(WP[wid[b]] - WP[wid[a]], WP[wid[c]] - WP[wid[a]])
        for x in (a, b, c): N[wid[x]] += fn
        for x, y in ((a, b), (b, c), (c, a)):
            nb[wid[x]].add(wid[y]); nb[wid[y]].add(wid[x]); ef[tuple(sorted((wid[x], wid[y])))] += 1
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
    g = head_grad(WP, ears=False); N *= np.sign((N * g).sum(1) + 1e-9)[:, None]      # outward
    L = WP.copy()
    for _ in range(2): L = np.array([L[list(s_)].mean(0) if s_ else L[i] for i, s_ in enumerate(nb)])
    det = WP - L; det -= N * 0                                              # keep full detail vector
    S_ = BL.S; ec = np.array(S_['ear'][0]); de = np.minimum(np.linalg.norm(WP - ec, axis=1), np.linalg.norm(WP - ec * [-1, 1, 1], axis=1))
    we = np.clip((de - ear_r * 0.5) / (ear_r * 0.5), 0, 1)[:, None]          # 0 near the ears: hair left as is there
    Q = WP + sharpen * det * we
    bnd = {v for e, c in ef.items() if c == 1 for v in e}
    dist = np.full(n, np.inf); h = []
    for v in bnd: dist[v] = 0; heapq.heappush(h, (0.0, v))
    while h:
        dv, v = heapq.heappop(h)
        if dv > dist[v]: continue
        for u in nb[v]:
            nd = dv + np.linalg.norm(WP[u] - WP[v])
            if nd < dist[u]: dist[u] = nd; heapq.heappush(h, (nd, u))
    t = np.clip(dist / r, 0, 1); t = t * t * (3 - 2 * t)
    Q += N * (-edge_in + (edge_in + mid_out) * t)[:, None] * we
    return Q[wid]

TONE_SPREAD = 0.85
MUFFY = '/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/girls/mumu_0/mumu_0'
def muffy_hair(keep=lambda c: True, swirls=True):
    """Muffy's hair triangles (body sheet: swirl block u<75,v<27; strand block u>=75,v<60), as a plain
    triangle mesh with its own vertices/UVs; texture recoloured to the goddess green (AWL-desaturated)"""
    import awlmodel, wally
    M = awlmodel.load(MUFFY); T = wally.textures(MUFFY + '_b0.tpl', MUFFY + '_f0_e.tpl', MUFFY + '_f0_m.tpl')
    tex = T[255].copy(); H, W = tex.shape[:2]; UV = M['UV']; V = M['V']
    hair = np.zeros((H, W), bool); hair[:27, :75] = True; hair[:60, 75:] = True
    ramp = restyle.ramp_from(GD + 'hair_315_00.png', sel=lambda a: (a[:, 1] > a[:, 0] + 10) & (a[:, 1] > a[:, 2]))
    L = restyle.lum(tex[..., :3]); lo, hi = np.percentile(L[hair], 1), np.percentile(L[hair], 99.5)
    # match the princess hair's tone distribution (position along the ramp: mean and spread)
    ph = [m for m in princess()[0] if m['mat'] == 'hair_205'][0]['tex']; op = ph[..., 3] > 0; PL = restyle.lum(ph[..., :3])[op]
    plo, phi = np.percentile(PL, 1), np.percentile(PL, 99.5); pt = np.clip((PL - plo) / (phi - plo), 0, 1)
    mt = np.clip((L[hair] - lo) / (hi - lo), 0, 1); mt = np.clip((mt - mt.mean()) / mt.std() * pt.std() * TONE_SPREAD + pt.mean(), 0, 1)
    px = tex[hair].copy(); px[:, :3] = (lo + mt * (hi - lo))[:, None]       # grey of the matched tone
    tex[hair] = restyle.recolour(px, ramp, lo, hi); tex[..., :3] = np.where(hair[..., None], desat(tex[..., :3], 0.72), tex[..., :3]).clip(0, 255)
    P, UVo, Tr, key = [], [], [], {}
    for tid, tris, _ in M['groups']:
        if tid != 255: continue
        for pi, ti in tris:
            u = np.mean([UV[t][0] % 1 for t in ti]) * W; v = np.mean([UV[t][1] % 1 for t in ti]) * H
            sw = u < 75 and v < 27; st = u >= 75 and v < 60
            if not (sw or st) or (sw and not swirls): continue
            if not keep(V[list(pi)].mean(0)): continue
            idx = []
            for p, t in zip(pi, ti):
                k = (p, t)
                if k not in key: key[k] = len(P); P.append(V[p]); UVo.append((UV[t][0] % 1 if UV[t][0] != 1 else 1, UV[t][1]))
                idx.append(key[k])
            Tr.append(idx)
    return np.array(P), np.array(UVo), np.array(Tr), tex

BACK_RECT = (0.67, 0.30, 0.85, 0.80)            # princess texture: long back strands (u0, v0, u1, v1)
def fill_rect_opaque(tex, rect=BACK_RECT):
    """transparent texels inside rect take the nearest opaque colour (so a solid shell shows no holes)"""
    t = tex.copy(); H, W = t.shape[:2]; u0, v0, u1, v1 = rect
    y0, y1, x0, x1 = int(v0 * H) - 1, int(v1 * H) + 2, int(u0 * W) - 1, int(u1 * W) + 2
    sub = t[y0:y1, x0:x1]; m = sub[..., 3] > 127; rgb = sub[..., :3].copy()
    for _ in range(40):
        if m.all(): break
        acc = np.zeros_like(rgb); cnt = np.zeros(m.shape)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            mm = np.roll(np.roll(m, dy, 0), dx, 1); acc += np.roll(np.roll(rgb, dy, 0), dx, 1) * mm[..., None]; cnt += mm
        new = (~m) & (cnt > 0); rgb[new] = acc[new] / cnt[new][:, None]; m |= new
    sub[..., :3] = rgb; sub[..., 3] = 255; t[y0:y1, x0:x1] = sub
    return t
def wrap_uv(P, rect=BACK_RECT, ytop=1.16, ybot=0.72):
    """mirror-symmetric wrap: angle from the back of the head -> u, height -> v"""
    u0, v0, u1, v1 = rect
    tb = np.abs(np.degrees(np.arctan2(P[:, 0], -P[:, 2])))                 # 0 at the back, 180 at the front
    u = u0 + (u1 - u0) * np.clip(tb / 180, 0, 1)
    v = v0 + (v1 - v0) * np.clip((ytop - P[:, 1]) / (ytop - ybot), 0, 1)
    return np.c_[u, v]

def hair_atlas():
    """princess hair texture (128x128, recoloured) + below it a 128x64 strip of her back strands, mirror-tiled
    across so it repeats seamlessly (for the Muffy-shaped lower hair). Returns texture, and v-scale for old UVs"""
    t = fill_rect_opaque(green_hair_tex()); H, W = t.shape[:2]; u0, v0, u1, v1 = BACK_RECT
    R = t[int(v0 * H):int(v0 * H) + 64, int(u0 * W):int(u1 * W)]
    w = R.shape[1]; x = np.arange(w); wgt = (1 - np.abs((x + 0.5) / w * 2 - 1))[None, :, None]   # 1 mid, 0 edges
    Rt = R * wgt + np.roll(R, w // 2, 1) * (1 - wgt)                     # seamless when repeated side by side
    strip = np.concatenate([Rt] * (W // w + 1), 1)[:, :W]
    return np.concatenate([t, strip], 0), H / (H + 64)
def strip_uv(P, vscale, ytop=1.16, ybot=0.72):
    tb = np.abs(np.degrees(np.arctan2(P[:, 0], -P[:, 2])))
    u = np.clip(tb / 180, 0, 0.999)
    v = vscale + (1 - vscale) * np.clip((ytop - P[:, 1]) / (ytop - ybot), 0.004, 0.996)
    return np.c_[u, v]

def _param(P, ytop, ybot):
    th = np.degrees(np.arctan2(P[:, 0], -P[:, 2])); h = (ytop - P[:, 1]) / (ytop - ybot)
    return np.c_[th, h * 180.0]                                  # h scaled to degrees-ish so the grid is isotropic
def transfer_uv(MP, MT, PP, PUV, PT, ytop=1.16, ybot_m=0.60, ybot_p=0.42, res=1.0):
    """per-corner UVs for the Muffy-shaped hair, taken from the princess back hair's own layout:
    (angle around the head, relative height) on both; each Muffy triangle uses the affine map of the
    outermost princess triangle under its centre (so it never spans two texture islands)"""
    qp = _param(PP, ytop, ybot_p); qm = _param(MP, ytop, ybot_m)
    nx, ny = int(360 / res), int(200 / res); grid = -np.ones((ny, nx), int); rad = np.full((ny, nx), -1.0)
    R = np.hypot(PP[:, 0], PP[:, 2])
    for k, t in enumerate(PT):
        q = qp[t]
        if q[:, 0].max() - q[:, 0].min() > 90: continue          # across the front seam
        x0, x1 = int(np.floor((q[:, 0].min() + 180) / res)), int(np.ceil((q[:, 0].max() + 180) / res))
        y0, y1 = int(np.floor(q[:, 1].min() / res)), int(np.ceil(q[:, 1].max() / res))
        A = np.c_[q, np.ones(3)].T
        if abs(np.linalg.det(A)) < 1e-9: continue
        Ai = np.linalg.inv(A); r = R[t].mean()
        for yy in range(max(y0, 0), min(y1 + 1, ny)):
            for xx in range(max(x0, 0), min(x1 + 1, nx)):
                b = Ai @ np.array([xx * res - 180 + res / 2, yy * res + res / 2, 1])
                if (b >= -0.02).all() and r > rad[yy, xx]: rad[yy, xx] = r; grid[yy, xx] = k
    # fill empty cells from neighbours
    for _ in range(200):
        e = grid < 0
        if not e.any(): break
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            sh = np.roll(np.roll(grid, dy, 0), dx, 1); m = e & (sh >= 0); grid[m] = sh[m]; e = grid < 0
    cu = []
    for t in MT:
        c = qm[t].mean(0); xx = int(np.clip((c[0] + 180) / res, 0, nx - 1)); yy = int(np.clip(c[1] / res, 0, ny - 1))
        k = grid[yy, xx]; q = qp[PT[k]]; A = np.c_[q, np.ones(3)].T; Ai = np.linalg.inv(A)
        cu.append([PUV[PT[k]].T @ (Ai @ np.array([qm[i][0], qm[i][1], 1])) for i in t])
    return np.array(cu)                                           # (ntri, 3, 2)
def fill_used(tex, tri_uvs, keep_alpha_uvs):
    """make the texels under tri_uvs opaque (nearest opaque colour), except texels other parts rely on for cut-outs"""
    from PIL import Image, ImageDraw
    H, W = tex.shape[:2]
    def mask(uvs):
        m = Image.new('L', (W, H), 0); d = ImageDraw.Draw(m)
        for tr in uvs: d.polygon([(u * W, v * H) for u, v in tr], fill=255, outline=255)
        return np.array(m) > 0
    want = mask(tri_uvs) & ~mask(keep_alpha_uvs)
    t = tex.copy(); m = t[..., 3] > 127; rgb = t[..., :3].copy()
    for _ in range(40):
        todo = want & ~m
        if not todo.any(): break
        acc = np.zeros_like(rgb); cnt = np.zeros(m.shape)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            mm = np.roll(np.roll(m, dy, 0), dx, 1); acc += np.roll(np.roll(rgb, dy, 0), dx, 1) * mm[..., None]; cnt += mm
        new = todo & (cnt > 0); rgb[new] = acc[new] / cnt[new][:, None]; m = m | new
    t[..., :3] = rgb; t[want, 3] = 255
    return t

def radius_grid(P, T, ytop, ybot, nth=180, nh=60):
    """outermost radius (about the vertical axis) per (angle from the back, relative height) cell"""
    th = np.degrees(np.arctan2(P[:, 0], -P[:, 2])); h = (ytop - P[:, 1]) / (ytop - ybot); r = np.hypot(P[:, 0], P[:, 2])
    G = np.full((nh, nth), np.nan)
    # sample triangles densely (barycentric points) so the grid has no gaps
    bs = np.array([(a, b, 1 - a - b) for a in np.linspace(0, 1, 7) for b in np.linspace(0, 1, 7) if a + b <= 1])
    for t in T:
        if th[t].max() - th[t].min() > 90: continue
        q = bs @ np.c_[th[t], h[t], r[t]]
        ix = np.clip(((q[:, 0] + 180) / 360 * nth).astype(int), 0, nth - 1); iy = np.clip((q[:, 1] * nh).astype(int), 0, nh - 1)
        ok = (q[:, 1] >= 0) & (q[:, 1] < 1)
        for x, y, rr in zip(ix[ok], iy[ok], q[ok, 2]):
            if not (G[y, x] >= rr): G[y, x] = rr
    for _ in range(300):                                          # fill gaps from neighbours
        e = np.isnan(G)
        if not e.any(): break
        acc = np.zeros_like(G); cnt = np.zeros_like(G)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            sh = np.roll(np.roll(G, dy, 0), dx, 1); m = ~np.isnan(sh); acc[m] += sh[m]; cnt += m
        n = e & (cnt > 0); G[n] = acc[n] / cnt[n]
    return G
def sample(G, th, h):
    nh, nth = G.shape; x = np.clip((th + 180) / 360 * nth - 0.5, 0, nth - 1.001); y = np.clip(h * nh - 0.5, 0, nh - 1.001)
    x0, y0 = x.astype(int), y.astype(int); fx, fy = x - x0, y - y0
    return (G[y0, x0] * (1 - fx) * (1 - fy) + G[y0, x0 + 1] * fx * (1 - fy) + G[y0 + 1, x0] * (1 - fx) * fy + G[y0 + 1, x0 + 1] * fx * fy)
def reshape_lower(PP, PT, MP, MT, ytop=1.16, ybot_p=0.30, ybot_m=0.60, blend=0.12, keep=None):
    """princess hair keeps its mesh and UVs; below ytop it takes Muffy's silhouette: heights rescaled to her
    length, outer radius to hers, inner layers keep their depth under the outer layer"""
    Gm = radius_grid(MP, MT, ytop, ybot_m); Gp = radius_grid(PP, PT, ytop, ybot_p)
    th = np.degrees(np.arctan2(PP[:, 0], -PP[:, 2])); hp = np.clip((ytop - PP[:, 1]) / (ytop - ybot_p), 0, 1)
    r = np.hypot(PP[:, 0], PP[:, 2])
    rn = sample(Gm, th, hp) + (r - sample(Gp, th, hp)); yn = ytop - hp * (ytop - ybot_m)
    w = np.clip((ytop - PP[:, 1]) / blend, 0, 1); w = w * w * (3 - 2 * w)
    if keep is not None: w = w * (1 - keep)
    rr = r + (rn - r) * w; yy = PP[:, 1] + (yn - PP[:, 1]) * w
    s = rr / np.maximum(r, 1e-6)
    return np.c_[PP[:, 0] * s, yy, PP[:, 2] * s]

def falling_shape(G, sigma=(2.5, 4.0), hem=0.10, hem_in=0.025):
    """smooth Muffy's outer radius grid into one clean shape that only widens or stays as it goes down
    (hanging hair), with a soft rounded hem in the last part"""
    from scipy.ndimage import median_filter, gaussian_filter
    g = np.pad(G, ((0, 0), (5, 5)), mode='wrap'); g = median_filter(g, size=(3, 5), mode='nearest')[:, 5:-5]
    g = gaussian_filter(g, sigma, mode=('nearest', 'wrap'))
    g = np.maximum.accumulate(g, axis=0)                          # never curves back in going down
    nh = g.shape[0]; h = (np.arange(nh) + 0.5) / nh
    t = np.clip((h - (1 - hem)) / hem, 0, 1); g = g - hem_in * (t ** 2)[:, None]
    return g
def reshape_lower2(PP, PT, MP, MT, ytop=1.16, ybot_p=0.30, ybot_m=0.60, blend=0.12, keep=None, depth=0.012):
    Gm = falling_shape(radius_grid(MP, MT, ytop, ybot_m))
    from scipy.ndimage import gaussian_filter
    Gp = gaussian_filter(radius_grid(PP, PT, ytop, ybot_p), (1.5, 3), mode=('nearest', 'wrap'))
    th = np.degrees(np.arctan2(PP[:, 0], -PP[:, 2])); hp = np.clip((ytop - PP[:, 1]) / (ytop - ybot_p), 0, 1)
    r = np.hypot(PP[:, 0], PP[:, 2])
    lay = np.clip(r - sample(Gp, th, hp), -depth, 0)               # inner layers stay a little underneath
    rn = sample(Gm, th, hp) + lay; yn = ytop - hp * (ytop - ybot_m)
    w = np.clip((ytop - PP[:, 1]) / blend, 0, 1); w = w * w * (3 - 2 * w)
    if keep is not None: w = w * (1 - keep)
    rr = r + (rn - r) * w; yy = PP[:, 1] + (yn - PP[:, 1]) * w
    s = rr / np.maximum(r, 1e-6)
    return np.c_[PP[:, 0] * s, yy, PP[:, 2] * s]

PATCHES = [(85, 54, 110, 100), (0, 25, 32, 72), (18, 74, 46, 104), (52, 32, 80, 70)]   # texel boxes (x0,y0,x1,y1)
def filled(tex):
    t = tex.copy(); m = t[..., 3] > 127; rgb = t[..., :3].copy()
    for _ in range(60):
        if m.all(): break
        acc = np.zeros_like(rgb); cnt = np.zeros(m.shape)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            mm = np.roll(np.roll(m, dy, 0), dx, 1); acc += np.roll(np.roll(rgb, dy, 0), dx, 1) * mm[..., None]; cnt += mm
        new = (~m) & (cnt > 0); rgb[new] = acc[new] / cnt[new][:, None]; m |= new
    t[..., :3] = rgb; t[..., 3] = 255; return t
def varied_strip(tex, W=128, H=64, ov=8, patches=PATCHES):
    """non-repeating strip: different strand patches of the hair texture, each scaled to H tall, cross-faded
    into each other and around the wrap (u 0 = u 1)"""
    from PIL import Image
    f = filled(tex); n = len(patches); pw = W // n + ov
    tiles = []
    for x0, y0, x1, y1 in patches:
        im = Image.fromarray(f[y0:y1, x0:x1].astype(np.uint8)).resize((pw, H), Image.BICUBIC)
        tiles.append(np.array(im).astype(float))
    out = np.zeros((H, W + ov, 4)); wsum = np.zeros((1, W + ov, 1)); step = W // n
    ramp = np.ones(pw); ramp[:ov] = np.linspace(0, 1, ov + 2)[1:-1]; ramp[-ov:] = np.linspace(1, 0, ov + 2)[1:-1]
    for k, t in enumerate(tiles):
        out[:, k * step:k * step + pw] += t * ramp[None, :, None]; wsum[:, k * step:k * step + pw] += ramp[None, :, None]
    out = out / np.maximum(wsum, 1e-6)
    # wrap: the overhang past W blends into the start
    tail = out[:, W:W + ov]; wv = np.linspace(1, 0, ov + 2)[1:-1][None, :, None]
    head = out[:, :ov].copy(); out[:, :ov] = tail * wv + head * (1 - wv)
    s = out[:, :W]; s[..., 3] = 255
    return s
def hair_atlas2():
    t = green_hair_tex(); s = varied_strip(t)
    return np.concatenate([t, s], 0), t.shape[0] / (t.shape[0] + s.shape[0])
def strip_uv_corners(P, T, vscale, ytop=1.16, ybot=0.72):
    """per-corner UVs, full wrap: back centre at u 0.5, seam at the front (u 0/1) fixed per triangle"""
    th = np.degrees(np.arctan2(P[:, 0], -P[:, 2]))
    u = (th + 180) / 360; v = vscale + (1 - vscale) * np.clip((ytop - P[:, 1]) / (ytop - ybot), 0.004, 0.996)
    U = u[T]; V = v[T]
    wrap = U.max(1) - U.min(1) > 0.5
    U[wrap] = np.where(U[wrap] < 0.5, U[wrap] + 1, U[wrap])
    return np.stack([U, V], -1)

def varied_strip2(tex, W=128, H=64, ov=4, box=(84, 50, 111, 104), upright=False):
    """crisp non-repeating strip from the long back strands: the block in 4 orientations + a shifted
    copy, nearest-sampled, short cross-fades"""
    from PIL import Image
    f = filled(tex); x0, y0, x1, y1 = box; B = f[y0:y1, x0:x1]
    w = B.shape[1]
    vs = ([B, np.roll(B, w // 3, 1)[:, ::-1], np.roll(B, 2 * w // 3, 1), B[:, ::-1], np.roll(B, w // 2, 1)] if upright else
          [B, B[:, ::-1], B[::-1], B[::-1, ::-1], np.roll(B, w // 2, 1)[:, ::-1]])
    n = len(vs); step = int(np.ceil(W / n)); pw = step + ov
    out = np.zeros((H, step * n + ov, 4)); wsum = np.zeros((1, step * n + ov, 1))
    ramp = np.ones(pw); ramp[:ov] = np.linspace(0, 1, ov + 2)[1:-1]; ramp[-ov:] = np.linspace(1, 0, ov + 2)[1:-1]
    for k, t in enumerate(vs):
        im = np.array(Image.fromarray(t.astype(np.uint8)).resize((pw, H), Image.NEAREST)).astype(float)
        out[:, k * step:k * step + pw] += im * ramp[None, :, None]; wsum[:, k * step:k * step + pw] += ramp[None, :, None]
    out = out / np.maximum(wsum, 1e-6)
    out = out[:, :W + ov]; tail = out[:, W:W + ov]; wv = np.linspace(1, 0, ov + 2)[1:-1][None, :, None]
    out[:, :ov] = tail * wv + out[:, :ov] * (1 - wv)
    s = out[:, :W].copy(); s[..., 3] = 255
    return s
def hair_atlas3(upright=True):
    t = green_hair_tex(); s = varied_strip2(t, upright=upright)
    return np.concatenate([t, s], 0), t.shape[0] / (t.shape[0] + s.shape[0])

def drape_over(PP, PT, MP, MT, ytop=1.16, ybot_p=0.30, ytip=0.90, ybot_m=0.60, gap=0.012, depth=0.010, blend=0.10, keep=None):
    """princess hair (one piece, own texture) shortened so its wavy tips end at ytip, lying just outside
    Muffy's smoothed, falling outline (the fuller under-layer)"""
    from scipy.ndimage import gaussian_filter
    Gm = falling_shape(radius_grid(MP, MT, ytop, ybot_m), hem_in=0.0)
    Gp = gaussian_filter(radius_grid(PP, PT, ytop, ybot_p), (1.5, 3), mode=('nearest', 'wrap'))
    th = np.degrees(np.arctan2(PP[:, 0], -PP[:, 2])); hp = np.clip((ytop - PP[:, 1]) / (ytop - ybot_p), 0, 1)
    r = np.hypot(PP[:, 0], PP[:, 2])
    yn = ytop - hp * (ytop - ytip); hm = np.clip((ytop - yn) / (ytop - ybot_m), 0, 1)
    lay = np.clip(r - sample(Gp, th, hp), -depth, 0)
    rn = sample(Gm, th, hm) + gap + lay
    w = np.clip((ytop - PP[:, 1]) / blend, 0, 1); w = w * w * (3 - 2 * w)
    if keep is not None: w = w * (1 - keep)
    rr = r + (rn - r) * w; yy = PP[:, 1] + (yn - PP[:, 1]) * w
    s = rr / np.maximum(r, 1e-6)
    return np.c_[PP[:, 0] * s, yy, PP[:, 2] * s]
def varied_strip3(tex, W=128, H=128, ov=6, box=(84, 50, 111, 104)):
    """upright variants of the back strands, smooth (bicubic) upscale + light sharpening, 128x128"""
    from PIL import Image, ImageFilter
    f = filled(tex); x0, y0, x1, y1 = box; B = f[y0:y1, x0:x1]; w = B.shape[1]
    vs = [B, np.roll(B, w // 3, 1)[:, ::-1], np.roll(B, 2 * w // 3, 1), B[:, ::-1], np.roll(B, w // 2, 1)]
    n = len(vs); step = int(np.ceil(W / n)); pw = step + ov
    out = np.zeros((H, step * n + ov, 4)); wsum = np.zeros((1, step * n + ov, 1))
    ramp = np.ones(pw); ramp[:ov] = np.linspace(0, 1, ov + 2)[1:-1]; ramp[-ov:] = np.linspace(1, 0, ov + 2)[1:-1]
    for k, t in enumerate(vs):
        im = Image.fromarray(t[..., :3].astype(np.uint8)).resize((pw, H), Image.BICUBIC).filter(ImageFilter.UnsharpMask(1.2, 60, 2))
        im = np.dstack([np.array(im).astype(float), np.full((H, pw), 255.0)])
        out[:, k * step:k * step + pw] += im * ramp[None, :, None]; wsum[:, k * step:k * step + pw] += ramp[None, :, None]
    out = out / np.maximum(wsum, 1e-6); out = out[:, :W + ov]
    tail = out[:, W:W + ov]; wv = np.linspace(1, 0, ov + 2)[1:-1][None, :, None]; out[:, :ov] = tail * wv + out[:, :ov] * (1 - wv)
    s = out[:, :W].copy(); s[..., 3] = 255
    return s
def hair_atlas4():
    t = green_hair_tex(); s = varied_strip3(t)
    return np.concatenate([t, s], 0), t.shape[0] / (t.shape[0] + s.shape[0])

def body_sdf(P): return BL.sdf(P)
def body_grad(P, e=1e-3):
    g = np.zeros_like(P)
    for k in range(3):
        dd = np.zeros(3); dd[k] = e; g[:, k] = (BL.sdf(P + dd) - BL.sdf(P - dd)) / (2 * e)
    return g / np.maximum(np.linalg.norm(g, axis=1, keepdims=True), 1e-9)
def thicken(P, UV, T, sel, t_top=0.05, t_tip=0.025, y_full=1.02, y_start=1.12, ytip=0.30, margin=0.010):
    """give the selected (back) part of a sheet real volume: an inner surface offset towards the body
    (thick near the top, thinner at the tips, none on the crown), kept clear of the body, and its open
    edges closed. Returns new P, UV, T (inner triangles reversed, rim quads added)."""
    from collections import defaultdict
    wid, n = weld(P); WP = np.zeros((n, 3)); WP[wid] = P
    ST = T[sel]
    N = np.zeros((n, 3))
    for a, b, c in ST:
        fn = np.cross(WP[wid[b]] - WP[wid[a]], WP[wid[c]] - WP[wid[a]])
        for x in (a, b, c): N[wid[x]] += fn
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
    out = WP - np.array([0, 1.0, -0.02]) * [1, 0, 1]; out[:, 1] = 0          # horizontal outward from the body axis
    N *= np.sign((N * out).sum(1) + 1e-9)[:, None]
    for _ in range(3):                                                         # smooth the offset direction
        acc = N.copy(); cnt = np.ones(n)
        for a, b, c in ST:
            for x, y in ((a, b), (b, c), (c, a)): acc[wid[x]] += N[wid[y]]; cnt[wid[x]] += 1
        N = acc / cnt[:, None]; N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
    y = WP[:, 1]
    th = np.where(y > y_full, np.clip((y_start - y) / (y_start - y_full), 0, 1) * t_top,
                  t_top + (t_tip - t_top) * np.clip((y_full - y) / (y_full - ytip), 0, 1))
    IW = WP - N * th[:, None]
    for _ in range(8):                                                         # keep the inner surface out of the body
        d = body_sdf(IW); g = body_grad(IW); IW += g * np.maximum(margin - d, 0)[:, None]
    used = sorted({wid[i] for t in ST for i in t})
    # inner copies: one per original corner index used (keeps UVs), positions from IW
    corners = sorted({i for t in ST for i in t}); cmap = {i: len(P) + k for k, i in enumerate(corners)}
    NP = np.vstack([P, IW[wid[corners]]]); NUV = np.vstack([UV, UV[corners]])
    inner = [(cmap[a], cmap[c], cmap[b]) for a, b, c in ST]
    # open edges of the whole sheet that belong to the selected part: close them with a rim
    ec = defaultdict(list)
    for k, (a, b, c) in enumerate(T):
        for x, y_ in ((a, b), (b, c), (c, a)): ec[tuple(sorted((wid[x], wid[y_])))].append((k, x, y_))
    rim = []
    for e, lst in ec.items():
        if len(lst) != 1: continue
        k, x, y_ = lst[0]
        if not sel[k] or th[wid[x]] < 0.004 or th[wid[y_]] < 0.004: continue
        rim += [(y_, x, cmap[x]), (y_, cmap[x], cmap[y_])]
    return NP, NUV, np.vstack([T, np.array(inner), np.array(rim).reshape(-1, 3)])

def wrap_back(P, T, sel, k=2.0, y0=1.10, ramp=0.18, squeeze=0.12):
    """curve the flat back sheet around the body: the sides come forward (dz = k x^2) and in a little,
    blended in below the head"""
    wid, n = weld(P); WP = np.zeros((n, 3)); WP[wid] = P
    vs = np.zeros(n, bool)
    for t in T[sel]: vs[wid[t]] = True
    w = np.clip((y0 - WP[:, 1]) / ramp, 0, 1); w = w * w * (3 - 2 * w) * vs
    Q = WP.copy(); Q[:, 2] += k * WP[:, 0] ** 2 * w; Q[:, 0] *= 1 - squeeze * w
    return Q[wid]

def taubin(P, T, sel, iters=8, lam=0.5, mu=-0.53):
    """non-shrinking smoothing of the selected part (open edges and vertices shared with the rest stay put)"""
    from collections import defaultdict
    wid, n = weld(P); WP = np.zeros((n, 3)); WP[wid] = P
    nb = [set() for _ in range(n)]; ec = defaultdict(int); insel = np.zeros(n, bool); inrest = np.zeros(n, bool)
    for k, (a, b, c) in enumerate(T):
        for x in (a, b, c): (insel if sel[k] else inrest)[wid[x]] = True
        if not sel[k]: continue
        for x, y in ((a, b), (b, c), (c, a)):
            nb[wid[x]].add(wid[y]); nb[wid[y]].add(wid[x]); ec[tuple(sorted((wid[x], wid[y])))] += 1
    bnd = {v for e, c in ec.items() if c == 1 for v in e}
    free = insel & ~inrest; free[list(bnd)] = False
    idx = np.where(free)[0]; nbl = [list(nb[i]) for i in idx]
    for _ in range(iters):
        for f in (lam, mu):
            C = np.array([WP[l].mean(0) for l in nbl]); WP[idx] += f * (C - WP[idx])
    return WP[wid]
def thicken2(P, UV, T, sel, tex, t_top=0.05, t_tip=0.025, y_full=1.02, y_start=1.12, ytip=0.30, margin=0.010, min_th=0.004):
    """as thicken(), but: the inner layer never passes the outer one, and edges are only closed where the
    texture is solid (no rims along see-through strand tips)"""
    from collections import defaultdict
    wid, n = weld(P); WP = np.zeros((n, 3)); WP[wid] = P
    ST = T[sel]; N = np.zeros((n, 3))
    for a, b, c in ST:
        fn = np.cross(WP[wid[b]] - WP[wid[a]], WP[wid[c]] - WP[wid[a]])
        for x in (a, b, c): N[wid[x]] += fn
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
    out = WP.copy(); out[:, 1] = 0; out[:, 2] += 0.02
    N *= np.sign((N * out).sum(1) + 1e-9)[:, None]
    for _ in range(4):
        acc = N.copy(); cnt = np.ones(n)
        for a, b, c in ST:
            for x, y in ((a, b), (b, c), (c, a)): acc[wid[x]] += N[wid[y]]; cnt[wid[x]] += 1
        N = acc / cnt[:, None]; N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
    y = WP[:, 1]
    th = np.where(y > y_full, np.clip((y_start - y) / (y_start - y_full), 0, 1) * t_top,
                  t_top + (t_tip - t_top) * np.clip((y_full - y) / (y_full - ytip), 0, 1))
    IW = WP - N * th[:, None]
    for _ in range(8):
        d = body_sdf(IW); g = body_grad(IW); IW += g * np.maximum(margin - d, 0)[:, None]
    depth = ((WP - IW) * N).sum(1)                                     # keep the inner layer under the outer one
    IW = np.where((depth < min_th)[:, None], WP - N * np.minimum(th, min_th)[:, None], IW)
    corners = sorted({i for t in ST for i in t}); cmap = {i: len(P) + k for k, i in enumerate(corners)}
    NP = np.vstack([P, IW[wid[corners]]]); NUV = np.vstack([UV, UV[corners]])
    inner = [(cmap[a], cmap[c], cmap[b]) for a, b, c in ST]
    H, W = tex.shape[:2]
    solid = lambda i: tex[min(int(UV[i][1] % 1 * H), H - 1), min(int(UV[i][0] % 1 * W), W - 1), 3] > 127
    ec = defaultdict(list)
    for k, (a, b, c) in enumerate(T):
        for x, y_ in ((a, b), (b, c), (c, a)): ec[tuple(sorted((wid[x], wid[y_])))].append((k, x, y_))
    rim = []
    for e, lst in ec.items():
        if len(lst) != 1: continue
        k, x, y_ = lst[0]
        if not sel[k] or th[wid[x]] < 0.004 or th[wid[y_]] < 0.004: continue
        if not (solid(x) and solid(y_)): continue
        rim += [(y_, x, cmap[x]), (y_, cmap[x], cmap[y_])]
    return NP, NUV, np.vstack([T, np.array(inner), np.array(rim).reshape(-1, 3)]) if rim else np.vstack([T, np.array(inner)])

def coverage(tex, UV, T, n=6):
    """fraction of opaque texels under each triangle (barycentric samples)"""
    H, W = tex.shape[:2]; A = tex[..., 3] > 127
    bs = np.array([(a, b, 1 - a - b) for a in np.linspace(0, 1, n) for b in np.linspace(0, 1, n) if a + b <= 1 + 1e-9])
    out = np.zeros(len(T))
    for k, t in enumerate(T):
        q = bs @ UV[t]; x = np.clip((q[:, 0] % 1) * W, 0, W - 1).astype(int); y = np.clip((q[:, 1] % 1) * H, 0, H - 1).astype(int)
        out[k] = A[y, x].mean()
    return out
