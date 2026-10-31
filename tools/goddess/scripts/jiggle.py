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
def bust_nodes(P, n_bust, n_ring):
    """node override for body vertices (unscaled positions): -1 = keep. The whole bust volume in front of the
    chest (y 0.665-0.780, |x| < 0.105, z > 0.055) moves fully; a band around it moves half (blends the edge)."""
    x, y, z = np.abs(P[:, 0]), P[:, 1], P[:, 2]
    full = (y > 0.665) & (y < 0.780) & (x < 0.105) & (z > 0.055)
    ring = (y > 0.640) & (y < 0.805) & (x < 0.130) & (z > 0.025) & ~full
    out = np.full(len(P), -1); out[full] = n_bust; out[ring] = n_ring
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
def spring_offsets(nodes, raw_anm, center_local, f_hz=3.2, zeta=0.22, gain=1.6, clamp=0.010, sub=8, fps=30.0, idle_amp=0.0):
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
    if idle_amp > 0 and nf > 2:                      # test aid: a visible bob in every animation (in the chest frame's main axis)
        ax = np.argmax(np.abs(rot[0].T @ np.array([0, 1.0, 0])))
        cyc = max(1, round((nf - 1) / 12.0))
        local[:, ax] += idle_amp * np.sin(2 * np.pi * cyc * np.arange(nf) / (nf - 1))
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

# ---------------------------------------------------------------- 49-node variant: reuse node 21
# The game breaks with more than 49 nodes (jiggle tests 3-5). Node 21 (right clavicle base, child of 5)
# is constant at its rest pose in all 10 animations and unused by the skin: fold it into its child 22
# (22 hangs from 5 directly, its rest and every key pre-multiplied by 21's fixed transform) and use 21 as
# the bust node (parent 5).
FREE, FREE_CHILD = 21, 22
def qmul(a, b):
    ax, ay, az, aw = a; bx, by, bz, bw = b
    return np.array([aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
                     aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz])
def act_fold(d, bust_T):
    d = bytearray(d); n = struct.unpack_from('>I', d, 4)[0]
    e = lambda i: 0x20 + 0x1C * i
    rd = lambda i: list(struct.unpack_from('>7I', d, e(i)))
    x21 = rd(FREE)[0]; x22 = rd(FREE_CHILD)[0]
    v21 = struct.unpack_from('>I10f', d, x21); v22 = struct.unpack_from('>I10f', d, x22)
    q21, t21 = np.array(v21[4:8]), np.array(v21[8:11]); q22, t22 = np.array(v22[4:8]), np.array(v22[8:11])
    R21 = qmat(q21)
    struct.pack_into('>4f', d, x22 + 0x10, *qmul(q21, q22)); struct.pack_into('>3f', d, x22 + 0x20, *(t21 + R21 @ t22))
    struct.pack_into('>4f', d, x21 + 0x10, 0, 0, 0, 1.0); struct.pack_into('>3f', d, x21 + 0x20, *bust_T)
    # links: 22 becomes a child of 5 right after 21; 21 has no children
    r21 = rd(FREE); r22 = rd(FREE_CHILD)
    r22[3] = r21[3]                                  # parent = 5
    r22[2] = r21[2]; r22[1] = e(FREE)                # siblings: 21 -> 22 -> (21's old next)
    if r21[2]:
        rn = rd((r21[2] - 0x20) // 0x1C); rn[1] = e(FREE_CHILD); struct.pack_into('>7I', d, r21[2], *rn)
    r21[2] = e(FREE_CHILD); r21[4] = 0
    struct.pack_into('>7I', d, e(FREE), *r21); struct.pack_into('>7I', d, e(FREE_CHILD), *r22)
    return bytes(d), (q21, t21)
def anm_fold(raw, bust_keys, L):
    """22's track pre-multiplied by 21's (constant) local transform; 21's track = bust keyed translation"""
    d = bytearray(raw); n = struct.unpack_from('>H', d, 4)[0]
    tab = [list(struct.unpack_from('>fIHHI', d, 8 + 16 * i)) for i in range(n)]
    offs = sorted(set(t[1] for t in tab)) + [len(d)]
    get = lambda t: struct.unpack_from('>%dh' % ((offs[offs.index(t[1]) + 1] - t[1]) // 2), d, t[1])
    t21 = [t for t in tab if t[3] == FREE][0]; t22 = [t for t in tab if t[3] == FREE_CHILD][0]
    assert t21[4] == 0x3E000009, hex(t21[4])                 # constant rotation (all comps) + translation
    h = get(t21); q21 = np.array(h[0:4]) / 16384.; T21 = np.array(h[4:7]) / 16384.; R21 = qmat(q21 / np.linalg.norm(q21))
    p = t22[4]; b2, b3 = (p >> 8) & 0xFF, p & 0xFF; b1 = (p >> 16) & 0xFF
    assert b1 & 0xE0 == 0 and not (b2 & 0x01), hex(p)        # all four components stored, no keyed translation
    o = t22[1]; h = list(get(t22)); k = 0
    S = lambda v: [int(np.clip(round(c * 16384), -32768, 32767)) for c in v]
    if b3 & 0x08:
        h[k:k + 4] = S(qmul(q21, np.array(h[k:k + 4]) / 16384.)); k += 4
    if b3 & 0x01:
        h[k:k + 3] = S(T21 + R21 @ (np.array(h[k:k + 3]) / 16384.)); k += 3
    else:
        h_ins = S(T21)                                       # (no case in Celia's data: 22 always has a translation)
    if b2 & 0x70:
        while k + 9 <= len(h):
            h[k + 1:k + 5] = S(qmul(q21, np.array(h[k + 1:k + 5]) / 16384.))
            h[k + 5:k + 9] = S(qmul(q21, np.array(h[k + 5:k + 9]) / 16384.))
            k += 9
    struct.pack_into('>%dh' % len(h), d, o, *h)
    blob = b''.join(struct.pack('>4h', int(f), *S(xyz)) for f, xyz in bust_keys); blob += bytes((-len(blob)) % 4)
    t21[1] = len(d); t21[2] = len(bust_keys); t21[4] = 0x3EE10100; t21[0] = L
    for i, t in enumerate(tab): struct.pack_into('>fIHHI', d, 8 + 16 * i, *t)
    return bytes(d) + blob
