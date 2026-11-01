"""AWL .anm helpers for Joe: scale translations, retime, constant tracks, and an encoder for keyed clips.

Format (see scratchpad pm/anm.py): header 8 bytes (n tracks at +4), then n entries '>fIHHI'
(length in frames, data offset, key count, node, packed). packed: byte1 bits 0x80/0x40/0x20 = quaternion
z/y/x omitted, 0x08 = rotation keyed, 0x01 = translation keyed; byte2 0x70 = rotation keys, 0x01 =
translation keys; byte3 0x08 = constant rotation, 0x01 = constant translation. Values s16/16384.
Keys: rotation+translation 'frame, q, T, q control' (control = squad point; set to q -> slerp)."""
import struct, numpy as np

def _comps(packed):
    b1 = (packed >> 16) & 0xFF
    return [c for c, bit in (('x', 0x20), ('y', 0x40), ('z', 0x80)) if not b1 & bit] + ['w']

def _walk(d):
    """yield (entry index, entry, data offset, layout) for every track's halfwords"""
    n = struct.unpack_from('>H', d, 4)[0]
    tr = [struct.unpack_from('>fIHHI', d, 8 + 16 * i) for i in range(n)]
    offs = sorted(set(t[1] for t in tr)) + [len(d)]
    for i, (length, off, nk, node, packed) in enumerate(tr):
        end = offs[offs.index(off) + 1]; nh = (end - off) // 2
        nc = len(_comps(packed)); b2, b3 = (packed >> 8) & 0xFF, packed & 0xFF
        lay = dict(nc=nc, constR=bool(b3 & 8), constT=bool(b3 & 1), keyR=bool(b2 & 0x70), keyT=bool(b2 & 1), nh=nh)
        yield i, (length, off, nk, node, packed), lay

def _keysize(l):
    nc = l['nc']
    if l['keyR'] and l['keyT']: return 1 + 2 * nc + 3, 1 + nc        # T after frame + q
    if l['keyR']: return 1 + 2 * nc, None
    if l['keyT']: return 4, 1
    return 0, None

def scale_T(d, k):
    """multiply every translation (constant and keyed) by k"""
    d = bytearray(d); done = set()
    for i, (length, off, nk, node, packed), l in _walk(d):
        if off in done: continue
        done.add(off); p = 0
        def sc(a):
            v = struct.unpack_from('>h', d, a)[0]; struct.pack_into('>h', d, a, int(np.clip(round(v * k), -32768, 32767)))
        if l['constR']: p += l['nc']
        if l['constT']:
            for j in range(3): sc(off + 2 * (p + j))
            p += 3
        ks, tpos = _keysize(l)
        if ks and tpos is not None:
            for j in range((l['nh'] - p) // ks):
                for c in range(3): sc(off + 2 * (p + j * ks + tpos + c))
    return bytes(d)

def retime(d, newlen):
    """scale every key frame and track length so the clip lasts newlen frames"""
    d = bytearray(d); done = set(); oldlen = None
    for i, (length, off, nk, node, packed), l in _walk(d):
        oldlen = oldlen or length; k = newlen / oldlen
        struct.pack_into('>f', d, 8 + 16 * i, length * k)
        if off in done: continue
        done.add(off); p = (l['nc'] if l['constR'] else 0) + (3 if l['constT'] else 0)
        ks, _ = _keysize(l)
        if ks:
            for j in range((l['nh'] - p) // ks):
                a = off + 2 * (p + j * ks); f = struct.unpack_from('>h', d, a)[0]
                struct.pack_into('>h', d, a, int(round(f * k)))
    return bytes(d)

def _q16(v): return [int(np.clip(round(c * 16384), -32768, 32767)) for c in v]

def rebuild(header, length, tracks):
    """tracks: list of (node, kind, payload). kind 'const': payload (q xyzw, T);
    kind 'keys': payload list of (frame, q xyzw, T). Every track gets its own data block."""
    n = len(tracks); tab = []; data = b''; base = 8 + 16 * n
    for node, kind, pl in tracks:
        off = base + len(data)
        if kind == 'const':
            q, T = pl; blob = struct.pack('>7h', *_q16(q), *_q16(T)); tab.append((length, off, 1, node, 0x3E000009))
        else:
            blob = b''.join(struct.pack('>12h', int(f), *_q16(q), *_q16(T), *_q16(q)) for f, q, T in pl)
            tab.append((length, off, len(pl), node, 0x3E097100))
        data += blob + bytes((-len(blob)) % 4)
    out = bytearray(header[:8]); struct.pack_into('>H', out, 4, n)
    for t in tab: out += struct.pack('>fIHHI', *t)
    return bytes(out) + data

def replace_tracks(d, const):
    """const: {node: (q, T)} -> those nodes' tracks become constant (other tracks copied as they are)"""
    n = struct.unpack_from('>H', d, 4)[0]
    tr = [struct.unpack_from('>fIHHI', d, 8 + 16 * i) for i in range(n)]
    offs = sorted(set(t[1] for t in tr)) + [len(d)]
    out_tab = []; data = b''; base = 8 + 16 * n
    for length, off, nk, node, packed in tr:
        o = base + len(data)
        if node in const:
            q, T = const[node]; blob = struct.pack('>7h', *_q16(q), *_q16(T)); out_tab.append((length, o, 1, node, 0x3E000009))
        else:
            blob = d[off:offs[offs.index(off) + 1]]; out_tab.append((length, o, nk, node, packed))
        data += blob + bytes((-len(blob)) % 4)
    out = bytearray(d[:8])
    for t in out_tab: out += struct.pack('>fIHHI', *t)
    return bytes(out) + data

def mat2q(R):
    """rotation matrix -> (x,y,z,w) in awlchar.qmat's convention"""
    from scipy.spatial.transform import Rotation
    q = Rotation.from_matrix(R).as_quat()      # scipy (x,y,z,w), same convention as qmat (checked by round trip)
    return q if q[3] >= 0 else -q
