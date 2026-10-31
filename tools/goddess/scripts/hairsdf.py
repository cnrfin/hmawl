"""Solid AWL-style hair for the goddess: crown shell + twintail bumps + full back (Celia's length) +
thick fringe spikes + Flora-like S-curved tendrils, one smooth closed surface (SDF, marching cubes)."""
import sys, numpy as np
sys.path[:0] = ['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess',
                '/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/blank']
import blank as BL, gd2
from skimage import measure
import pyfqmr
smin, cap, ell = BL.smin, BL.cap, BL.ell
def smax(a, b, k): return -smin(-a, -b, k)
HC = np.array([0.0, 1.08, -0.01])

def head(P): return gd2.head_sdf(P, ears=False)
def surface_point(d, off):
    """point on the head along direction d from the head centre, pushed out by off"""
    d = d / np.linalg.norm(d); r = 0.2
    for _ in range(30): r -= head((HC + d * r)[None])[0] * 0.9
    return HC + d * (r + off)
def path_sdf(P, pts, radii, k=0.012):
    d = None
    for i in range(len(pts) - 1):
        c = cap(P, pts[i], pts[i + 1], radii[i], radii[i + 1]); d = c if d is None else smin(d, c, k)
    return d

PRM = dict(shell=0.032, bump_c=(0.175, 1.275, -0.11), bump_r=(0.11, 0.09, 0.11),
           ybot=0.60, groove=0.008, n_locks=9, hem_pts=6, hem_amp=0.10)
def hairline_cut(P):
    """>0 below the hairline (no crown hair there); front hairline high, sides lower, back to the nape"""
    th = np.degrees(np.arctan2(P[..., 0], P[..., 2] - HC[2]))           # 0 = front
    a = np.abs(th)
    yl = np.interp(a, [0, 30, 60, 80, 100, 130, 180], [1.20, 1.19, 1.12, 1.07, 1.02, 0.95, 0.90])
    return (yl - P[..., 1]) * 1.0
def fringe_paths():
    out = []
    for az, tip, w in ((-48, 1.105, 0.030), (-24, 1.150, 0.030), (0, 1.125, 0.032), (22, 1.155, 0.030), (46, 1.100, 0.030)):
        pts = []; rad = []
        for t in np.linspace(0, 1, 7):
            el = np.radians(55 - t * 55) ; a = np.radians(az + 6 * np.sin(t * np.pi) * np.sign(az + 1e-3))
            d = np.array([np.sin(a) * np.cos(el), np.sin(el), np.cos(a) * np.cos(el)])
            p = surface_point(d, w * (1 - t) * 0.45 + 0.004)
            pts.append(p); rad.append(w * (1 - 0.82 * t ** 1.3))
        # pull the tip down to its tip height along the forehead
        out.append((np.array(pts), np.array(rad), tip))
    return out
def tendril_path(s):
    """Flora-like S-curved lock from the temple (in front of the ear) down past the chin"""
    pts = []; rad = []
    for t in np.linspace(0, 1, 16):
        y = 1.12 - t * 0.30
        x = s * (0.215 + 0.030 * np.sin(t * 2.0 * np.pi) + 0.02 * t)
        z = 0.05 + 0.025 * np.cos(t * 2.0 * np.pi) - 0.04 * t
        pts.append((x, y, z)); rad.append(0.034 * (1 - 0.65 * t ** 1.2) + 0.006)
    return np.array(pts), np.array(rad)
def back_sdf(P, prm):
    """measured on Celia/Lumina/Flora: below the head the hair is a D-shaped slab, flat against the neck
    (z ~ -0.08), rounded at the back (z ~ -0.25..-0.27), half-width ~0.25 narrowing a little at the hem,
    hanging almost straight down from the back of the head; hem of sharp V points"""
    y = P[..., 1]
    zf = np.interp(y, [0.55, 0.95, 1.05, 1.16], [-0.08, -0.08, -0.04, -0.03])
    zb = np.interp(y, [0.55, 0.70, 0.85, 1.00, 1.16], [-0.215, -0.24, -0.255, -0.275, -0.29])
    rx = np.interp(y, [0.55, 0.70, 0.82, 1.00, 1.16], [0.20, 0.225, 0.245, 0.255, 0.255])
    rz = zf - zb
    q = np.stack([P[..., 0] / rx, (P[..., 2] - zf) / rz], -1)
    d = (np.linalg.norm(q, axis=-1) - 1) * np.minimum(rx, rz)
    th = np.arctan2(P[..., 0], -(P[..., 2] - zf))
    d = d + prm['groove'] * np.cos(th * prm['n_locks']) * np.clip((1.10 - y) / 0.15, 0, 1)
    d = smax(d, P[..., 2] - zf, 0.02)
    hem = prm['ybot'] + prm['hem_amp'] * np.abs(np.sin(th * prm['hem_pts'] / 2))       # sharp V tips pointing down
    d = smax(d, hem - y, 0.012)
    return smax(d, y - 1.16, 0.04)
def body_clear(P):
    """the body below the head (neck, shoulders, back, arms): hair stays 1 cm away"""
    d = BL.sdf(P); return np.where(P[..., 1] < 0.93, d, 1.0)
def hair_sdf(P, prm=PRM, parts=None):
    hd = head(P)
    crown = smax(hd - prm['shell'], hairline_cut(P), 0.03)
    for s in (1, -1):
        c = np.array(prm['bump_c']) * [s, 1, 1]; crown = smin(crown, ell(P, c, np.array(prm['bump_r'])), 0.05)
    d = smin(crown, back_sdf(P, prm), 0.05)
    for pts, rad, tip in parts['fringe']: d = smin(d, path_sdf(P, pts, rad), 0.015)
    for pts, rad in parts['tendrils']:
        t = None
        for p, r in zip(pts, rad):
            e = ell(P, p, np.array([r * 0.62, r * 1.5, r * 1.15])); t = e if t is None else smin(t, e, 0.012)
        d = smin(d, t, 0.03)
    d = smax(d, -(body_clear(P) - 0.012), 0.015)
    return d
def build(step=0.005, target=1300, prm=PRM):
    parts = dict(fringe=fringe_paths(), tendrils=[tendril_path(1), tendril_path(-1)])
    lo = np.array([-0.40, 0.52, -0.36]); hi = np.array([0.40, 1.46, 0.30])
    n = np.ceil((hi - lo) / step).astype(int) + 1
    xs, ys, zs = [lo[i] + np.arange(n[i]) * step for i in range(3)]
    D = np.empty(n, np.float32)
    Y, Z = np.meshgrid(ys, zs, indexing='ij')
    for i, x in enumerate(xs):
        D[i] = hair_sdf(np.stack([np.full_like(Y, x), Y, Z], -1), prm, parts)
    V, F, _, _ = measure.marching_cubes(D, 0.0, spacing=(step,) * 3); V += lo
    hidden = (head(V) < -0.004) | (BL.sdf(V) < -0.004)                 # inside the head/body: never seen
    F = F[~hidden[F].all(1)]
    used = np.unique(F); remap = -np.ones(len(V), int); remap[used] = np.arange(len(used)); V = V[used]; F = remap[F]
    s = pyfqmr.Simplify(); s.setMesh(V, F); s.simplify_mesh(target_count=target, aggressiveness=5, preserve_border=True, verbose=False)
    V2, F2, _ = s.getMesh()
    return V2, F2
