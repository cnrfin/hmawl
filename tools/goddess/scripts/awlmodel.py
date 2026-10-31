"""Read an AWL character (NAME.gpl/.skn/.act/_b0.tpl) for editing previews: positions, UVs, triangles per
material, and the bone(s) each vertex follows (from the skin groups)."""
import sys, struct, numpy as np
HERE = '/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/'
sys.path[:0] = [HERE + 'pm']
import wally
from awlchar import act, world

def skin_bones(skn, nverts):
    """vertex index -> list of bones (first = strongest for 1-bone; for multi: listed bones)"""
    n1, n2, n3 = struct.unpack_from('>HHH', skn, 0)
    t1, t2, t3 = struct.unpack_from('>III', skn, 8)
    vb = [[] for _ in range(nverts)]
    for k in range(n1):
        e = t1 + 0x40 * k
        src, dst, b, c, al = struct.unpack_from('>IIHHB', skn, e + 0x30)
        s = (dst + al) // 12
        for i in range(c): vb[s + i].append(b)
    for k in range(n2):
        e = t2 + 0x74 * k
        src, wts, dst, b1, b2, c, al = struct.unpack_from('>IIIHHHB', skn, e + 0x60)
        s = (dst + al) // 12
        for i in range(c):
            if s + i < nverts: vb[s + i] += [b1, b2]
    for k in range(n3):
        e = t3 + 0x44 * k
        src, wts, dst, idx, b, c = struct.unpack_from('>IIIIHH', skn, e + 0x30)
        # 3+-bone: additive passes over an index list; record the bone on each listed vertex
        for i in range(c):
            v = struct.unpack_from('>H', skn, idx + 2 * i)[0] if idx + 2 * i + 2 <= len(skn) else None
            if v is not None and v < nverts: vb[v].append(b)
    return vb

def load(prefix):
    V, UV, fmt, groups, dls = wally.load(prefix + '.gpl')
    UVn = UV / (16384.0 if np.abs(UV).max() > 4 else 1.0)
    skn = open(prefix + '.skn', 'rb').read()
    vb = skin_bones(skn, len(V))
    nodes = act(open(prefix + '.act', 'rb').read())
    return dict(V=V, UV=UVn, groups=groups, bones=vb, nodes=nodes, prefix=prefix)
