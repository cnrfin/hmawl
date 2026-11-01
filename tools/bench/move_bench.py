#!/usr/bin/env python3
"""Valley benches by the bridge field: remove the bench at x 140.265 and turn the one at x 137.575 to
face east (seat towards the spot the player stands on, x 140.45 z 176.58), beside the tree at (138.06, 173.90).
Edits map{N}-p-other.oqt inside mapc1..5.arc. Benches have no collision in mapobj{N}.col (checked: no
collision polygon within the benches' area), so only the placement changes.
usage: move_bench.py SRC_DIR OUTDIR    (SRC_DIR holds mapc1..5.arc)"""
import sys, os, struct, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oqt_insert as Q, u8arc
BENCH = 136
KEEP, DROP = (137.575, 177.24), (140.265, 177.24)
NEW_X, NEW_Z, YAW = 137.60, 176.60, 90.0          # yaw 90: model +z (seat side) -> world +x
def find(n, xz, path=()):
    for i, r in enumerate(n.recs):
        mid = struct.unpack_from('>H', r, 0)[0]; M = struct.unpack_from('>12f', r, 4)
        if mid == BENCH and abs(M[3] - xz[0]) < 0.01 and abs(M[11] - xz[1]) < 0.01: return path + (n,), i
    for k in n.kids:
        if k:
            f = find(k, xz, path + (n,))
            if f: return f
    return None
def main(src, out):
    os.makedirs(out, exist_ok=True)
    for c in range(1, 6):
        d = open(os.path.join(src, 'mapc%d.arc' % c), 'rb').read(); a = u8arc.read(d); assert u8arc.build(a, {}) == d
        k = u8arc.names(a)['map%d-p-other.oqt' % c]; root = Q.read(a['files'][k]); before = root.count
        path, i = find(root, KEEP); leaf = path[-1]; r = bytearray(leaf.recs[i])
        y = struct.unpack_from('>f', r, 32)[0]; fl = struct.unpack_from('>H', r, 2)[0]
        leaf.recs[i] = Q.record(BENCH, NEW_X, y, NEW_Z, YAW, fl)
        for nd in path:                                   # grow boxes for the turned bench (1.12 x 0.32)
            nd.bbox[0] = min(nd.bbox[0], NEW_X - 1.2); nd.bbox[2] = min(nd.bbox[2], NEW_Z - 1.2)
            nd.bbox[3] = max(nd.bbox[3], NEW_X + 1.2); nd.bbox[5] = max(nd.bbox[5], NEW_Z + 1.2)
        path, i = find(root, DROP); del path[-1].recs[i]
        for nd in path: nd.count -= 1
        new = Q.write(root); o = u8arc.build(a, {k: new})
        chk = Q.read(u8arc.read(o)['files'][k]); assert chk.count == before - 1 and not find(chk, DROP)
        open(os.path.join(out, 'mapc%d.arc' % c), 'wb').write(o)
        print('mapc%d.arc %d -> %d bytes, placements %d -> %d' % (c, len(d), len(o), before, chk.count))
if __name__ == '__main__': main(*sys.argv[1:3])
