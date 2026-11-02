import numpy as np, math
def root_key(pcm, sr):
    """MIDI key of the fundamental (harmonic product spectrum over the first 0.2 s after the attack); None if unpitched."""
    a = np.array(pcm, float)
    if len(a) < 2048: return None
    st = min(len(a) // 8, int(0.02 * sr)); seg = a[st:st + min(len(a) - st, 16384)]
    if len(seg) < 2048: return None
    seg = seg * np.hanning(len(seg)); N = 1 << 17
    sp = np.abs(np.fft.rfft(seg, N)); fr = np.fft.rfftfreq(N, 1 / sr)
    hps = sp.copy()
    for h in (2, 3, 4):
        d = sp[::h]; hps[:len(d)] *= d; hps[len(d):] = 0
    band = (fr > 40) & (fr < 4000)
    k = np.argmax(hps * band); f0 = fr[k]
    flat = np.exp(np.mean(np.log(sp[band] + 1e-9))) / (np.mean(sp[band]) + 1e-9)   # spectral flatness
    if flat > 0.35 or f0 <= 0: return None
    return int(round(69 + 12 * math.log2(f0 / 440)))
