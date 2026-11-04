#!/usr/bin/env python3
"""GameCube DTK stream audio (.adp, the format of the game's streamed BGM: sound/*.adp) - encoder and decoder.
Frame = 32 bytes = 28 stereo samples: byte 0 / 1 = left / right header (high nibble filter 0-3, low nibble shift),
bytes 2 / 3 = copies, bytes 4..31 = one byte per sample pair, low nibble left, high nibble right. The decoder is
the hardware's (as Dolphin's StreamADPCM): history in 6-bit fixed point, filters 0, 60/64, 115/64 -52/64, 98/64 -55/64.
usage: dtk.py encode IN.wav OUT.adp      (16-bit stereo; any rate, the file holds no rate: the game plays 48 kHz)
       dtk.py decode IN.adp OUT.wav [rate]"""
import sys, wave, numpy as np

K = {0: (0, 0), 1: (0x3C, 0), 2: (0x73, -0x34), 3: (0x62, -0x37)}

def dec_sample(nib, q, h):
    f1, f2 = K[q >> 4]
    hist = (h[0] * f1 + h[1] * f2 + 0x20) >> 6
    hist = max(-0x200000, min(0x1FFFFF, hist))
    s = ((nib << 12) & 0xFFFF); s = s - 0x10000 if s & 0x8000 else s
    cur = ((s >> (q & 0xF)) << 6) + hist
    h[1] = h[0]; h[0] = cur
    return max(-32768, min(32767, cur >> 6))

def decode(data):
    out = np.zeros((len(data) // 32 * 28, 2), np.int16); hl = [0, 0]; hr = [0, 0]; k = 0
    for o in range(0, len(data) - 31, 32):
        ql, qr = data[o], data[o + 1]
        for i in range(28):
            b = data[o + 4 + i]
            out[k, 0] = dec_sample(b & 0xF, ql, hl); out[k, 1] = dec_sample(b >> 4, qr, hr); k += 1
    return out

def enc_channel(x):
    """x: int array (28 * n). Returns (headers[n], nibbles[n, 28]) choosing, per frame, the filter / shift with
    the least squared error, simulating the decoder exactly (so the history stays in step)."""
    n = len(x) // 28; heads = np.zeros(n, np.uint8); nibs = np.zeros((n, 28), np.uint8)
    cand = [(f, s) for f in range(4) for s in range(13)]
    F1 = np.array([K[f][0] for f, s in cand], np.int64); F2 = np.array([K[f][1] for f, s in cand], np.int64)
    SH = np.array([s for f, s in cand], np.int64)
    h1 = 0; h2 = 0
    for fr in range(n):
        t = x[fr * 28:(fr + 1) * 28].astype(np.int64)
        a1 = np.full(len(cand), h1, np.int64); a2 = np.full(len(cand), h2, np.int64)
        err = np.zeros(len(cand), np.int64); ns = np.zeros((len(cand), 28), np.int64)
        for i in range(28):
            hist = np.clip((a1 * F1 + a2 * F2 + 0x20) >> 6, -0x200000, 0x1FFFFF)
            # want ((nib << 12) >> sh) << 6 + hist ~ t << 6  ->  nib ~ (t*64 - hist) / 64 * 2^sh / 4096
            want = (t[i] * 64 - hist).astype(np.float64) / 64.0 * (2.0 ** SH) / 4096.0
            nib = np.clip(np.round(want), -8, 7).astype(np.int64)
            cur = (((nib << 12) >> SH) << 6) + hist
            out = np.clip(cur >> 6, -32768, 32767)
            err += (out - t[i]) ** 2
            a2 = a1; a1 = cur; ns[:, i] = nib & 0xF
        b = int(np.argmin(err)); f, s = cand[b]
        heads[fr] = (f << 4) | s; nibs[fr] = ns[b]; h1 = int(a1[b]); h2 = int(a2[b])
    return heads, nibs

def encode(pcm):
    n = len(pcm) // 28 * 28; pcm = pcm[:n]
    hl, nl = enc_channel(pcm[:, 0]); hr, nr = enc_channel(pcm[:, 1])
    out = bytearray(len(hl) * 32)
    for fr in range(len(hl)):
        o = fr * 32; out[o] = hl[fr]; out[o + 1] = hr[fr]; out[o + 2] = hl[fr]; out[o + 3] = hr[fr]
        out[o + 4:o + 32] = bytes((nl[fr] | (nr[fr] << 4)).astype(np.uint8))
    return bytes(out)

def read_wav(p):
    w = wave.open(p); assert w.getnchannels() == 2 and w.getsampwidth() == 2, 'need 16-bit stereo'
    return np.frombuffer(w.readframes(w.getnframes()), '<i2').reshape(-1, 2), w.getframerate()

if __name__ == '__main__':
    if sys.argv[1] == 'encode':
        x, sr = read_wav(sys.argv[2]); open(sys.argv[3], 'wb').write(encode(x))
    else:
        y = decode(open(sys.argv[2], 'rb').read()); sr = int(sys.argv[4]) if len(sys.argv) > 4 else 48000
        w = wave.open(sys.argv[3], 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(y.tobytes()); w.close()
