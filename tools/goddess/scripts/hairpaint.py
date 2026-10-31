"""Procedural hair texture for the goddess hairstyle (crown + bumps + Muffy-shaped lower hair):
wavy rounded locks, fine strands, a broken sheen band, darker underside. u = angle from the back centre
(mirrored, 0 = back, 1 = front), v = angle down from the crown. Colours: the goddess hair ramp, AWL-desaturated,
tone-matched to the fringe (princess texture)."""
import numpy as np
from PIL import Image
import gd2, restyle
def smooth(x): x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)
def paint(W=128, H=128, ss=4, n_locks=11, seed=7, sheen_v=0.24):
    rng = np.random.RandomState(seed)
    X, Y = np.meshgrid((np.arange(W * ss) + 0.5) / (W * ss), (np.arange(H * ss) + 0.5) / (H * ss))
    edge = smooth(X / 0.10) * smooth((1 - X) / 0.10)                 # waves fade at the mirror lines
    wave = (0.32 * np.sin(2 * np.pi * (2.1 * Y + 0.15 * np.sin(2 * np.pi * 1.3 * X))) +
            0.12 * np.sin(2 * np.pi * (4.3 * Y + 0.7 * X))) * smooth(Y / 0.18) * edge
    s = X * n_locks + 0.5 + wave                                      # lock coordinate (lock centre at the back centre)
    k = np.floor(s).astype(int); t = s - k
    prof = np.sin(np.pi * t) ** 0.7                                   # rounded lock: light middle, dark grooves
    lk = rng.uniform(-0.07, 0.07, 64)[np.mod(k, 64)]
    fine = np.zeros_like(X)
    for f, a in ((7.0, 0.05), (13.0, 0.035), (23.0, 0.025)):
        fine += a * np.sin(2 * np.pi * (s * f + rng.uniform(0, 1)) + 0.6 * np.sin(2 * np.pi * (Y * 3 + rng.uniform(0, 1))))
    L = 0.30 + 0.42 * prof + lk + fine
    sv = sheen_v + 0.025 * np.sin(2 * np.pi * (X * 5.0 + 0.3)) + 0.015 * np.sin(2 * np.pi * s)
    streak = np.clip(0.5 + 0.5 * np.sin(2 * np.pi * (s * 3.0 + 0.2)), 0, 1) ** 2
    L += 0.32 * np.exp(-((Y - sv) / 0.035) ** 2) * prof * (0.4 + 0.6 * streak)
    L -= 0.18 * smooth((Y - 0.86) / 0.14)                            # darker towards the hem / underside
    L -= 0.10 * smooth((0.06 - Y) / 0.06)                            # crown centre a touch darker (parting)
    L = np.clip(L, 0, 1)
    im = Image.fromarray((L * 255).astype(np.uint8)).resize((W, H), Image.LANCZOS)
    return np.array(im) / 255.0
def colourise(L, sat=0.72):
    """luminance -> goddess hair ramp, matched to the princess texture's tone spread"""
    ramp = restyle.ramp_from(gd2.GD + 'hair_315_00.png', sel=lambda a: (a[:, 1] > a[:, 0] + 10) & (a[:, 1] > a[:, 2]))
    ph = [m for m in gd2.princess()[0] if m['mat'] == 'hair_205'][0]['tex']; op = ph[..., 3] > 0
    PL = restyle.lum(ph[..., :3])[op]; plo, phi = np.percentile(PL, 1), np.percentile(PL, 99.5)
    pt = np.clip((PL - plo) / (phi - plo), 0, 1)
    t = (L - L.mean()) / L.std() * pt.std() + pt.mean()
    rgb = ramp[(np.clip(t, 0, 1) * 255).astype(int)]
    rgb = gd2.desat(rgb.astype(float), sat).clip(0, 255)
    return np.dstack([rgb, np.full(L.shape, 255.0)])
CEN = np.array([0.0, 1.08, -0.02])
def uv(P, phimax=150.0):
    th = np.degrees(np.arctan2(P[:, 0], -(P[:, 2] - CEN[2])))
    phi = np.degrees(np.arctan2(np.hypot(P[:, 0], P[:, 2] - CEN[2]), P[:, 1] - CEN[1]))
    return np.c_[np.abs(th) / 180.0, np.clip(phi / phimax, 0, 1)]

def paint2(W=128, H=128, ss=4, n_locks=17, seed=11, sheen_v=0.22):
    """softer, painterly version: varied lock widths, irregular waves, low lock contrast, fine strands
    and broken light streaks (like the princess texture's painted look)"""
    rng = np.random.RandomState(seed)
    X, Y = np.meshgrid((np.arange(W * ss) + 0.5) / (W * ss), (np.arange(H * ss) + 0.5) / (H * ss))
    edge = smooth(X / 0.08) * smooth((1 - X) / 0.08)
    def n1(x, f, ph): return np.sin(2 * np.pi * (x * f + ph))
    wave = (0.30 * n1(Y, 1.7, 0.1 + 0.25 * n1(X, 1.1, 0.3)) + 0.16 * n1(Y, 3.3, 0.6 + 0.4 * n1(X, 2.3, 0.1)) +
            0.08 * n1(Y, 6.1, 0.2 + X * 1.7)) * smooth(Y / 0.15) * edge
    warp = 0.25 * n1(X, 3.0, 0.2) + 0.12 * n1(X, 7.0, 0.5)              # uneven lock widths
    s = (X + warp / n_locks) * n_locks + 0.5 + wave
    k = np.floor(s).astype(int); t = s - k
    prof = np.sin(np.pi * t) ** 0.5
    lk = rng.uniform(-0.06, 0.06, 64)[np.mod(k, 64)]
    fine = np.zeros_like(X)
    for f, a in ((5.0, 0.045), (9.0, 0.04), (17.0, 0.03), (31.0, 0.02)):
        fine += a * n1(s, f, rng.uniform()) * (0.6 + 0.4 * n1(Y, rng.uniform(1, 3), rng.uniform()))
    L = 0.40 + 0.20 * prof + lk + fine
    # broken light streaks along the strands (painted highlights), stronger around the sheen band
    streaks = np.clip(n1(s, 2.0, 0.15) * n1(s, 5.0, 0.4) + 0.2 * n1(Y, 4.0, 0.3), 0, 1) ** 3
    sv = sheen_v + 0.03 * n1(X, 4.0, 0.3) + 0.02 * n1(s, 1.0, 0.0)
    band = np.exp(-((Y - sv) / 0.05) ** 2)
    L += streaks * (0.10 + 0.28 * band) + 0.10 * band * prof
    L -= 0.16 * smooth((Y - 0.84) / 0.16)
    L -= 0.08 * smooth((0.05 - Y) / 0.05)
    L = np.clip(L, 0, 1)
    return np.array(Image.fromarray((L * 255).astype(np.uint8)).resize((W, H), Image.LANCZOS)) / 255.0

def value_noise(W, H, gx, gy, rng):
    """smooth 2D noise, mirror-symmetric at x = 0 and x = 1 (the texture's mirror lines)"""
    g = rng.uniform(-1, 1, (gy + 3, gx + 1)); g = np.concatenate([g[:, ::-1], g[:, 1:]], 1)       # symmetric at the left
    im = Image.fromarray(((g + 1) * 127.5).astype(np.uint8)).resize((W * 2, H), Image.BICUBIC)
    a = np.array(im) / 127.5 - 1; return a[:, W:W * 2] if a.shape[1] >= 2 * W else a[:, -W:]
def paint3(W=128, H=128, ss=4, n_locks=7, seed=5, sheen_v=0.22, contrast=1.0, streaky=False, fine_amp=0.012, mott_amp=0.07, crown=0.0, sheen_amp=0.22, wave_amp=1.0):
    """natural soft shading: broad clumps, uneven soft shadows between some of them, large mottling,
    faint strands, soft broken sheen"""
    rng = np.random.RandomState(seed)
    X, Y0 = np.meshgrid((np.arange(W * ss) + 0.5) / (W * ss), (np.arange(H * ss) + 0.5) / (H * ss))
    Y = np.maximum(Y0 - crown, 0) / (1 - crown)          # above 'crown' nothing varies with height (no rings over the bumps)
    edge = smooth(X / 0.1) * smooth((1 - X) / 0.1)
    n1 = lambda x, f, ph: np.sin(2 * np.pi * (x * f + ph))
    wave = (0.22 * n1(Y, 1.6, 0.1 + 0.2 * n1(X, 1.1, 0.3)) + 0.10 * n1(Y, 3.1, 0.6 + 0.3 * n1(X, 2.1, 0.1))) * smooth(Y / 0.15) * edge * wave_amp
    warp = 0.30 * n1(X, 2.0, 0.1) + 0.15 * n1(X, 5.0, 0.4)
    s = (X + warp / n_locks) * n_locks + 0.5 + wave
    k = np.floor(s).astype(int); t = s - k
    depth = rng.uniform(0.15, 1.0, 64)[np.mod(k, 64)]                 # how deep the shadow before this clump is
    depth2 = rng.uniform(0.15, 1.0, 64)[np.mod(k + 1, 64)]
    groove = np.exp(-(t / 0.13) ** 2) * depth + np.exp(-((1 - t) / 0.13) ** 2) * depth2
    body = np.sin(np.pi * t) ** 1.5                                     # soft roundness of each clump
    if streaky:      # variation stretched along the strands: sample noise in (lock coordinate, height)
        def strand_noise(fs, fy, ph):
            g = rng.uniform(-1, 1, (fy + 3, 64)); xs = np.mod(s * fs + ph, 64); ys = Y * fy
            x0 = np.floor(xs).astype(int); y0 = np.floor(ys).astype(int); fx = smooth(xs - x0); fyy = smooth(ys - y0)
            a = g[y0, x0 % 64] * (1 - fx) + g[y0, (x0 + 1) % 64] * fx; b = g[y0 + 1, x0 % 64] * (1 - fx) + g[y0 + 1, (x0 + 1) % 64] * fx
            return a * (1 - fyy) + b * fyy
        mott = 0.6 * strand_noise(2.0, 2, 0.0) + 0.4 * strand_noise(5.0, 3, 7.0)
        fine_n = 0.6 * strand_noise(14.0, 4, 3.0) + 0.4 * strand_noise(29.0, 6, 11.0)
    else:
        mott = value_noise(W * ss, H * ss, 5, 4, rng) * 0.6 + value_noise(W * ss, H * ss, 11, 9, rng) * 0.4
        fine_n = 0
    fine = fine_amp * (n1(s, 9.0, 0.2) + 0.8 * n1(s, 19.0, 0.7)) + (fine_amp * 3.0) * fine_n
    L = 0.50 + 0.10 * body - 0.22 * groove + mott_amp * mott + fine
    sv = sheen_v + 0.03 * n1(X, 3.0, 0.3)
    sheen = np.exp(-((Y - sv) / 0.06) ** 2) * np.clip(body * (0.5 + 0.5 * mott), 0, 1)
    L += sheen_amp * sheen
    L -= 0.14 * smooth((Y - 0.82) / 0.18) + 0.06 * smooth((0.05 - Y0) / 0.05)
    L = 0.5 + (np.clip(L, 0, 1) - 0.5) * contrast
    return np.array(Image.fromarray((L * 255).astype(np.uint8)).resize((W, H), Image.LANCZOS)) / 255.0
def colourise2(L, spread=0.75, sat=0.72):
    ramp = restyle.ramp_from(gd2.GD + 'hair_315_00.png', sel=lambda a: (a[:, 1] > a[:, 0] + 10) & (a[:, 1] > a[:, 2]))
    ph = [m for m in gd2.princess()[0] if m['mat'] == 'hair_205'][0]['tex']; op = ph[..., 3] > 0
    PL = restyle.lum(ph[..., :3])[op]; plo, phi = np.percentile(PL, 1), np.percentile(PL, 99.5)
    pt = np.clip((PL - plo) / (phi - plo), 0, 1)
    t = (L - L.mean()) / L.std() * pt.std() * spread + pt.mean()
    rgb = gd2.desat(ramp[(np.clip(t, 0, 1) * 255).astype(int)].astype(float), sat).clip(0, 255)
    return np.dstack([rgb, np.full(L.shape, 255.0)])

def smooth_ramp():
    """the goddess hair ramp without its flat dark plateau: its smooth part, with a darker tone below"""
    ramp = restyle.ramp_from(gd2.GD + 'hair_315_00.png', sel=lambda a: (a[:, 1] > a[:, 0] + 10) & (a[:, 1] > a[:, 2]))
    keys = [ramp[100] * 0.72, ramp[100], ramp[150], ramp[200], ramp[240]]
    xs = np.linspace(0, 1, len(keys)); t = np.linspace(0, 1, 256)
    return np.stack([np.interp(t, xs, [k[c] for k in keys]) for c in range(3)], 1)
def colourise3(L, spread=0.75, sat=0.72, mean_shift=0.0):
    ramp = smooth_ramp()
    ph = [m for m in gd2.princess()[0] if m['mat'] == 'hair_205'][0]['tex']; op = ph[..., 3] > 0
    PL = restyle.lum(ph[..., :3])[op]; plo, phi = np.percentile(PL, 1), np.percentile(PL, 99.5)
    pt = np.clip((PL - plo) / (phi - plo), 0, 1)
    t = (L - L.mean()) / L.std() * pt.std() * spread + pt.mean() + mean_shift
    rgb = gd2.desat(ramp[(np.clip(t, 0, 1) * 255).astype(int)].astype(float), sat).clip(0, 255)
    return np.dstack([rgb, np.full(L.shape, 255.0)])
