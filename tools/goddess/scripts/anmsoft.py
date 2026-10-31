"""Shorter strides for a long gown: scale the keyed rotations of the leg and skirt nodes part-way back
to their rest rotation (slerp), in place in an AWL .anm. Each track's stored components stay the same
(the rest rotation lies in the same plane), key controls are scaled with it."""
import struct, numpy as np
from anm import qcomps, fullq
def slerp(a, b, t):
    if np.dot(a, b) < 0: b = -b
    d = np.clip(np.dot(a, b), -1, 1); th = np.arccos(d)
    if th < 1e-6: return b
    return (np.sin((1 - t) * th) * a + np.sin(t * th) * b) / np.sin(th)
def soften(raw, rest, nodes_scale):
    d = bytearray(raw); n = struct.unpack_from('>H', d, 4)[0]
    tr = [struct.unpack_from('>fIHHI', d, 0x8 + 16 * i) for i in range(n)]
    changed = 0
    for length, off, kind, node, packed in tr:
        if node not in nodes_scale: continue
        s = nodes_scale[node]; comps = qcomps(packed); nc = len(comps); b2, b3 = (packed >> 8) & 0xFF, packed & 0xFF
        if not (b2 & 0x70): continue                       # only keyed rotations
        r = np.array(rest[node], float); r /= np.linalg.norm(r)
        p = off
        if b3 & 0x08: p += 2 * nc
        if b3 & 0x01: p += 6
        withT = bool(b2 & 0x01)
        ks = 2 * (1 + 2 * nc + (3 if withT else 0))
        end = [o for o in sorted(set(t[1] for t in tr)) + [len(d)] if o > off][0]
        while p + ks <= end:
            vals = np.array(struct.unpack_from('>%dh' % nc, d, p + 2)) / 16384.
            q = fullq(vals, comps); qn = q / max(np.linalg.norm(q), 1e-9)
            rr = r if np.dot(r, qn) >= 0 else -r
            q2 = slerp(rr, qn, s) * np.linalg.norm(q)
            idx = {'x': 0, 'y': 1, 'z': 2, 'w': 3}
            struct.pack_into('>%dh' % nc, d, p + 2, *[int(np.clip(round(q2[idx[c]] * 16384), -32768, 32767)) for c in comps])
            co = p + 2 + 2 * nc + (6 if withT else 0)
            cv = np.array(struct.unpack_from('>%dh' % nc, d, co)) * s
            struct.pack_into('>%dh' % nc, d, co, *[int(np.clip(round(c), -32768, 32767)) for c in cv])
            p += ks; changed += 1
    return bytes(d), changed
