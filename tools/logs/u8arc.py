"""Flat/nested U8 archive read and rebuild (same node order and names; data re-laid 0x20-aligned
from the original data start, as the game's own archives are)."""
import struct
def read(d):
    assert d[:4] == b'U\xaa8-'
    root, hs, ds = struct.unpack_from('>III', d, 4); n = struct.unpack_from('>I', d, root + 8)[0]
    nodes = [list(struct.unpack_from('>III', d, root + 12 * k)) for k in range(n)]
    strtab = d[root + 12 * n:root + hs]
    files = {k: d[o:o + s] for k, (w0, o, s) in enumerate(nodes) if not w0 >> 24}
    name = lambda k: strtab[nodes[k][0] & 0xFFFFFF:strtab.index(b'\0', nodes[k][0] & 0xFFFFFF)].decode('latin1')
    return dict(head=d[:ds], root=root, ds=ds, nodes=nodes, files=files, name=name, n=n)
def names(a):
    return {a['name'](k): k for k in a['files']}
def build(a, replace):
    """replace: {node index: new bytes}"""
    out = bytearray(a['head']); nodes = [list(x) for x in a['nodes']]
    order = sorted(a['files'], key=lambda k: a['nodes'][k][1])          # original data order
    for k in order:
        data = replace.get(k, a['files'][k])
        out += bytes((-len(out)) % 0x20)
        nodes[k][1] = len(out); nodes[k][2] = len(data); out += data
    for k, w in enumerate(nodes): struct.pack_into('>III', out, a['root'] + 12 * k, *w)
    return bytes(out)
