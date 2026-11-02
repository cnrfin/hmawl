"""GameCube DSP-ADPCM encoder: 8 predictor pairs fitted to the sound (k-means on per-frame
least-squares predictors), then each 14-sample frame picks the predictor and scale with the least
error, tracking the decoder's own history so errors don't accumulate."""
import numpy as np

def _frame_lsq(x, h1, h2):
    # predict x[n] from x[n-1], x[n-2]
    X = np.stack([np.concatenate(([h1, ], x[:-1])), np.concatenate(([h2, h1], x[:-2]))], 1)
    c, *_ = np.linalg.lstsq(X, x, rcond=None)
    return c

def fit_coefs(pcm, k=8, iters=12):
    x = np.asarray(pcm, float); n = len(x) // 14
    if n == 0: return [(0, 0)] * k
    cs, ws = [], []
    for i in range(n):
        f = x[i * 14:(i + 1) * 14]
        h1 = x[i * 14 - 1] if i else 0.0; h2 = x[i * 14 - 2] if i else 0.0
        e = float(np.dot(f, f))
        if e < 1: continue
        c = _frame_lsq(f, h1, h2); c = np.clip(c, -1.99, 1.99)
        cs.append(c); ws.append(e)
    cs = np.array(cs) if cs else np.zeros((1, 2)); ws = np.array(ws) if ws else np.ones(1)
    cent = [np.array([0.0, 0.0]), np.array([1.0, 0.0]), np.array([1.9, -0.92])]
    rng = np.random.default_rng(1)
    while len(cent) < k: cent.append(cs[rng.integers(len(cs))])
    cent = np.array(cent)
    for _ in range(iters):
        d = ((cs[:, None, :] - cent[None]) ** 2).sum(2); lab = d.argmin(1)
        for j in range(3, k):                       # keep the 3 fixed predictors (silence / 1st / 2nd order)
            m = lab == j
            if m.any(): cent[j] = (cs[m] * ws[m, None]).sum(0) / ws[m].sum()
    return [(int(round(a * 2048)), int(round(b * 2048))) for a, b in cent]

def encode(pcm, coefs):
    x = np.asarray(pcm, np.int64); n = len(x); out = bytearray(); h1 = h2 = 0
    for i in range(0, n, 14):
        f = x[i:i + 14]
        if len(f) < 14: f = np.concatenate([f, np.zeros(14 - len(f), np.int64)])
        best = None
        for p, (c1, c2) in enumerate(coefs):
            for sc in range(12):
                a, b = h1, h2; err = 0; nibs = []
                for s in f:
                    pred = (c1 * a + c2 * b + 1024) >> 11
                    q = int(np.floor((s - pred) / (1 << sc) + 0.5)); q = max(-8, min(7, q))
                    v = ((q * (1 << sc)) << 11) + 1024 + c1 * a + c2 * b; v >>= 11; v = max(-32768, min(32767, v))
                    err += (s - v) * (s - v); nibs.append(q & 0xF); b, a = a, v
                    if best and err >= best[0]: break
                else:
                    if best is None or err < best[0]: best = (err, p, sc, nibs, a, b)
        _, p, sc, nibs, h1, h2 = best
        out.append((p << 4) | sc)
        for k in range(0, 14, 2): out.append((nibs[k] << 4) | nibs[k + 1])
    return bytes(out)
