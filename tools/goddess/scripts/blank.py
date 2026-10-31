"""Blank AWL young-woman body on Celia's skeleton (family A: Celia/Muffy/Karen/Sabrina share it exactly):
one closed surface (signed-distance shapes smooth-unioned, marching cubes), decimated to AWL density."""
import sys, numpy as np
from skimage import measure
import pyfqmr

def ell(P, c, r):                      # approx sdf of ellipsoid
    q = (P - c) / r; k0 = np.linalg.norm(q, axis=-1); k1 = np.linalg.norm(q / r, axis=-1)
    return k0 * (k0 - 1) / np.maximum(k1, 1e-9)
def cap(P, a, b, ra, rb):              # tapered capsule
    a = np.array(a, float); b = np.array(b, float); ba = b - a
    h = np.clip(((P - a) @ ba) / (ba @ ba), 0, 1)
    return np.linalg.norm(P - (a + h[..., None] * ba), axis=-1) - (ra + (rb - ra) * h)
def rbox(P, c, half, r):
    q = np.abs(P - c) - (np.array(half) - r)
    return np.linalg.norm(np.maximum(q, 0), axis=-1) + np.minimum(q.max(-1), 0) - r
def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1); return b * (1 - h) + a * h - k * h * (1 - h)

S = dict(  # shape parameters (metres in model space; Celia's bind pose, arms out)
    cran=((0, 1.10, -0.01), (0.232, 0.228, 0.212)), jaw=((0, 0.955, 0.055), (0.165, 0.125, 0.135)), chin=((0, 0.89, 0.085), (0.075, 0.05, 0.06)),
    ear=((0.226, 1.025, 0.015), (0.022, 0.05, 0.034)),
    neck=((0, 0.78, 0.0), (0, 0.97, 0.0), 0.036, 0.036),
    chest=((0, 0.745, 0.005), (0.108, 0.075, 0.072)), bust=((0.05, 0.728, 0.072), 0.055),
    waist=((0, 0.645, 0.0), (0.082, 0.07, 0.062)), hips=((0, 0.53, -0.005), (0.12, 0.08, 0.085)),
    shoulder=((0.06, 0.79, 0.0), (0.14, 0.79, 0.0), 0.042, 0.036),
    upper=((0.14, 0.79, 0.0), (0.255, 0.79, 0.0), 0.036, 0.031),
    fore=((0.255, 0.79, 0.0), (0.375, 0.79, 0.0), 0.031, 0.025),
    palm=((0.43, 0.786, 0.0), (0.05, 0.021, 0.04), 0.016), mitt=((0.505, 0.788, -0.004), (0.04, 0.016, 0.036), 0.014),
    thumb=((0.405, 0.777, 0.03), (0.46, 0.768, 0.075), 0.016, 0.013),
    thigh=((0.062, 0.50, 0.0), (0.07, 0.355, 0.0), 0.056, 0.042), calf=((0.072, 0.265, -0.012), (0.04, 0.065, 0.042)),
    shin=((0.07, 0.355, 0.0), (0.073, 0.12, -0.012), 0.038, 0.028),
    foot=((0.073, 0.042, 0.05), (0.042, 0.04, 0.098), 0.036),
)
def sdf(P, S=S):
    m = lambda c: np.array(c) * [-1, 1, 1]          # mirror to the other side
    d = ell(P, S['cran'][0], S['cran'][1]); d = smin(d, ell(P, *S['jaw']), 0.05); d = smin(d, ell(P, *S['chin']), 0.04)
    for s in (1, -1):
        c = np.array(S['ear'][0]) * [s, 1, 1]; d = smin(d, ell(P, c, S['ear'][1]), 0.012)
    d = smin(d, cap(P, *S['neck']), 0.03)
    t = ell(P, *S['chest']); t = smin(t, ell(P, *S['waist']), 0.05); t = smin(t, ell(P, *S['hips']), 0.05)
    for s in (1, -1):
        f = (lambda c: np.array(c) * [s, 1, 1])
        t = smin(t, np.linalg.norm(P - f(S['bust'][0]), axis=-1) - S['bust'][1], 0.025)
        a = cap(P, f(S['shoulder'][0]), f(S['shoulder'][1]), *S['shoulder'][2:])
        a = smin(a, cap(P, f(S['upper'][0]), f(S['upper'][1]), *S['upper'][2:]), 0.02)
        a = smin(a, cap(P, f(S['fore'][0]), f(S['fore'][1]), *S['fore'][2:]), 0.015)
        h = rbox(P, f(S['palm'][0]), S['palm'][1], S['palm'][2]); h = smin(h, rbox(P, f(S['mitt'][0]), S['mitt'][1], S['mitt'][2]), 0.012)
        h = smin(h, cap(P, f(S['thumb'][0]), f(S['thumb'][1]), *S['thumb'][2:]), 0.01)
        a = smin(a, h, 0.015); t = smin(t, a, 0.03)
        l = cap(P, f(S['thigh'][0]), f(S['thigh'][1]), *S['thigh'][2:]); l = smin(l, cap(P, f(S['shin'][0]), f(S['shin'][1]), *S['shin'][2:]), 0.02); l = smin(l, ell(P, f(S['calf'][0]), S['calf'][1]), 0.03)
        l = smin(l, rbox(P, f(S['foot'][0]), S['foot'][1], S['foot'][2]), 0.03)
        t = smin(t, l, 0.035)
    return smin(d, t, 0.03)

def build(step=0.006, target=1500):
    lo = np.array([-0.62, -0.01, -0.27]); hi = np.array([0.62, 1.36, 0.28])
    n = np.ceil((hi - lo) / step).astype(int) + 1
    xs, ys, zs = [lo[i] + np.arange(n[i]) * step for i in range(3)]
    D = np.empty(n, np.float32)
    for i, x in enumerate(xs):                         # slab by slab (memory)
        Y, Z = np.meshgrid(ys, zs, indexing='ij'); P = np.stack([np.full_like(Y, x), Y, Z], -1)
        D[i] = sdf(P)
    V, F, _, _ = measure.marching_cubes(D, 0.0, spacing=(step,) * 3); V += lo
    s = pyfqmr.Simplify(); s.setMesh(V, F); s.simplify_mesh(target_count=target, aggressiveness=5, preserve_border=True, verbose=False)
    V2, F2, _ = s.getMesh()
    return V, F, V2, F2
