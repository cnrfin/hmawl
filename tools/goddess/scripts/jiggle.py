"""Experimental 'jiggle': two extra nodes under the upper spine (node 5): BUST (full motion) and RING
(half motion, blends the edge). Their motion is baked per animation from a damped spring driven by the
spine's own movement in that animation, stored as keyed-translation tracks (the pelvis track layout:
packed 0x3EE10100, key = frame, x, y, z / 16384)."""
import struct, numpy as np
from awlchar import world, qmat
import pose
from anm import parse

PARENT = 5
CENTER = np.array([0.0, 0.728, 0.085])        # between the two bust shapes of the blank body (unscaled)
L_C, R_C = np.array([0.05, 0.728, 0.072]), np.array([-0.05, 0.728, 0.072])

L_TIP, R_TIP = np.array([0.038, 0.728, 0.115]), np.array([-0.038, 0.728, 0.115])   # front of the enlarged bust
def bust_nodes(P, n_bust, n_ring, inner=0.042, outer=0.060):
    """node override for body vertices (unscaled positions): -1 = keep. By distance from the bust front."""
    d = np.minimum(np.linalg.norm(P - L_TIP, axis=1), np.linalg.norm(P - R_TIP, axis=1))
    out = np.full(len(P), -1)
    front = P[:, 2] > 0.025
    out[front & (d < inner)] = n_bust
    out[front & (d >= inner) & (d < outer)] = n_ring
    return out

# ---------------------------------------------------------------- act with extra nodes
def act_add(d, specs):
    """specs: list of (parent index, T, Q). Returns the new act bytes (table, node data, name rebuilt)."""
    n = struct.unpack_from('>I', d, 4)[0]
    off2i = lambda o: (o - 0x20) // 0x1C if o else -1
    ent = []
    for i in range(n):
        x, prv, nxt, par, ch, idx, fl = struct.unpack_from('>7I', d, 0x20 + 0x1C * i)
        ent.append(dict(prv=off2i(prv), nxt=off2i(nxt), par=off2i(par), ch=off2i(ch), fl=fl, data=d[x:x + 0x34]))
    name_off = struct.unpack_from('>I', d, 0x10)[0]; name = d[name_off:]
    for par, T, Q in specs:
        k = len(ent)
        e = dict(prv=-1, nxt=-1, par=par, ch=-1, fl=0x01000000,
                 data=struct.pack('>I10f', 0x0C000000, 1, 1, 1, *Q, *T) + bytes(8))      # 0x34 per node (last 8 bytes 0)
        if ent[par]['ch'] < 0: ent[par]['ch'] = k
        else:
            c = ent[par]['ch']
            while ent[c]['nxt'] >= 0: c = ent[c]['nxt']
            ent[c]['nxt'] = k; e['prv'] = c
        ent.append(e)
    N = len(ent); tab = 0x20; data0 = tab + 0x1C * N; name_new = data0 + 0x34 * N
    i2off = lambda i: tab + 0x1C * i if i >= 0 else 0
    out = bytearray(d[:0x20])
    struct.pack_into('>I', out, 4, N); struct.pack_into('>I', out, 0x10, name_new)
    for i, e in enumerate(ent):
        out += struct.pack('>7I', data0 + 0x34 * i, i2off(e['prv']), i2off(e['nxt']), i2off(e['par']), i2off(e['ch']),
                           0xFFFF0000 | i, e['fl'])
    for e in ent: out += e['data']
    out += name
    return bytes(out)

# ---------------------------------------------------------------- spring, baked per animation
def spring_offsets(nodes, raw_anm, center_local, f_hz=3.2, zeta=0.22, gain=1.6, clamp=0.010, sub=8, fps=30.0):
    """local (parent-frame) offsets of the bust per integer frame 0..L over one loop"""
    tr = parse(raw_anm); L = tr[0]['length']; nf = int(round(L)) + 1
    W = [world(nodes, pose.locals_at(nodes, tr, f)) for f in range(nf)]
    anchor = np.array([(w[PARENT] @ np.r_[center_local, 1])[:3] for w in W])
    rot = [w[PARENT][:3, :3] for w in W]
    w0 = 2 * np.pi * f_hz; dt = 1.0 / fps / sub
    p = anchor[0].copy(); v = np.zeros(3); rec = []
    for loop in range(4):
        for f in range(nf - 1 if nf > 1 else 1):
            a0, a1 = anchor[f], anchor[min(f + 1, nf - 1)]
            for s in range(sub):
                a = a0 + (a1 - a0) * (s + 1) / sub
                acc = -w0 * w0 * (p - a) - 2 * zeta * w0 * v
                v += acc * dt; p += v * dt
            if loop == 3: rec.append((f, (p - a1).copy()))
    offs = np.zeros((nf, 3))
    for f, o in rec:
        offs[(f + 1) % nf if nf > 1 else 0] = o
    if nf > 1: offs[0] = offs[-1]          # the loop's last frame = its first (seamless wrap)
    local = np.array([rot[f].T @ (offs[f] * gain) for f in range(nf)])
    n_ = np.linalg.norm(local, axis=1); k = np.minimum(1.0, clamp / np.maximum(n_, 1e-9))
    return L, local * k[:, None]

def anm_add_tracks(raw, tracks):
    """tracks: list of (node, length, keys[(frame, xyz)]) or (node, length, None, T) constant.
    Rebuilds the table (one 16-byte entry per track) and appends the data."""
    d = bytes(raw); n = struct.unpack_from('>H', d, 4)[0]
    tab = [list(struct.unpack_from('>fIHHI', d, 8 + 16 * i)) for i in range(n)]
    data_start = 8 + 16 * n; body = d[data_start:]
    N = n + len(tracks); shift = 16 * len(tracks)
    for t in tab: t[1] += shift
    extra = b''; base = 8 + 16 * N + len(body)
    for tk in tracks:
        node, length = tk[0], tk[1]
        off = base + len(extra)
        if tk[2] is None:
            T = tk[3]; blob = struct.pack('>3h', *[int(round(c * 16384)) for c in T]) + b'\0\0'
            tab.append([length, off, 1, node, 0x3EE00001])
        else:
            blob = b''.join(struct.pack('>4h', int(f), *[int(np.clip(round(c * 16384), -32768, 32767)) for c in xyz]) for f, xyz in tk[2])
            tab.append([length, off, len(tk[2]), node, 0x3EE10100])
        extra += blob + bytes((-len(blob)) % 4)
    out = bytearray(d[:8]); struct.pack_into('>H', out, 4, N)
    for t in tab: out += struct.pack('>fIHHI', *t)
    return bytes(out) + body + extra
