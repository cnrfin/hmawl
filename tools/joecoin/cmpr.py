"""GameCube CMPR (DXT1 in 8x8 tiles of four 4x4 sub-blocks) encoder/decoder, opaque images.
Endpoints: principal axis of each 4x4 block, then a few rounds of least-squares refinement."""
import struct
import numpy as np
from PIL import Image

def _q565(c):
    c = np.clip(np.round(c), 0, 255).astype(int)
    return (c[..., 0] >> 3) << 11 | (c[..., 1] >> 2) << 5 | (c[..., 2] >> 3)

def _un565(v):
    v = np.asarray(v)
    return np.stack([(v >> 11 & 31) * 255 // 31, (v >> 5 & 63) * 255 // 63, (v & 31) * 255 // 31], -1).astype(float)

def _palette(c0, c1):
    p0, p1 = _un565(c0), _un565(c1)
    return np.stack([p0, p1, (2 * p0 + p1) / 3, (p0 + 2 * p1) / 3], -2)       # (...,4,3)

def _blocks(a):
    """(H,W,3) -> (N,16,3) in CMPR order (8x8 tiles row-major, 2x2 sub-blocks inside)."""
    h, w = a.shape[:2]
    t = a.reshape(h // 8, 2, 4, w // 8, 2, 4, 3).transpose(0, 3, 1, 4, 2, 5, 6)
    return t.reshape(-1, 16, 3)

def encode(img):
    a = np.array(img.convert('RGB')).astype(float)
    assert a.shape[0] % 8 == 0 and a.shape[1] % 8 == 0
    B = _blocks(a)
    mean = B.mean(1, keepdims=True); X = B - mean
    cov = np.einsum('nki,nkj->nij', X, X)
    v = np.ones((len(B), 3))
    for _ in range(8):
        v = np.einsum('nij,nj->ni', cov, v); v /= np.linalg.norm(v, axis=1, keepdims=True) + 1e-9
    t = np.einsum('nki,ni->nk', X, v)
    e0 = mean[:, 0] + v * t.max(1, keepdims=True); e1 = mean[:, 0] + v * t.min(1, keepdims=True)
    W = np.array([[1, 0], [0, 1], [2 / 3, 1 / 3], [1 / 3, 2 / 3]])
    for it in range(3):
        c0, c1 = _q565(e0), _q565(e1)
        pal = _palette(c0, c1)
        idx = ((B[:, :, None, :] - pal[:, None, :, :]) ** 2).sum(-1).argmin(-1)   # (N,16)
        if it == 2: break
        A = W[idx]                                                              # (N,16,2)
        AtA = np.einsum('nki,nkj->nij', A, A) + np.eye(2) * 1e-6
        AtB = np.einsum('nki,nkc->nic', A, B)
        E = np.linalg.solve(AtA, AtB)                                           # (N,2,3)
        e0, e1 = E[:, 0], E[:, 1]
    # 4-colour mode needs c0 > c1; swap (and remap indices) where needed, nudge equal ones
    c0, c1 = _q565(e0), _q565(e1)
    eq = c0 == c1
    c0 = np.where(eq & (c0 < 0xFFFF), c0 + 1, c0); c1 = np.where(eq & (c0 == 0xFFFF), c1 - 1, c1)
    pal = _palette(c0, c1)
    idx = ((B[:, :, None, :] - pal[:, None, :, :]) ** 2).sum(-1).argmin(-1)
    sw = c0 < c1
    c0, c1 = np.where(sw, c1, c0), np.where(sw, c0, c1)
    idx = np.where(sw[:, None], np.array([1, 0, 3, 2])[idx], idx)
    out = bytearray()
    for n in range(len(B)):
        bits = 0
        for k in range(16): bits = bits << 2 | int(idx[n, k])
        out += struct.pack('>HHI', int(c0[n]), int(c1[n]), bits)
    return bytes(out)

def decode(data, w, h):
    n = (w // 4) * (h // 4); out = np.zeros((n, 16, 3))
    for i in range(n):
        c0, c1, bits = struct.unpack_from('>HHI', data, 8 * i)
        p0, p1 = _un565(c0), _un565(c1)
        pal = [p0, p1, (2 * p0 + p1) / 3, (p0 + 2 * p1) / 3] if c0 > c1 else [p0, p1, (p0 + p1) / 2, np.zeros(3)]
        for k in range(16): out[i, k] = pal[(bits >> (30 - 2 * k)) & 3]
    t = out.reshape(h // 8, w // 8, 2, 2, 4, 4, 3).transpose(0, 2, 4, 1, 3, 5, 6).reshape(h, w, 3)
    return Image.fromarray(np.clip(t, 0, 255).astype(np.uint8))
