#!/usr/bin/env python3
"""Adds the three choppable-log placements (mapobj.gpl model 285) to the valley's object files.
usage: build_log_maps.py OUTDIR map1-p-other.oqt [map2-p-other.oqt ...]
Each log lies across the direction the player faced at that spot (from RAM dumps). x/z carry a small
marker offset so the code can find each log's runtime instance by its exact translation. The files
grow by 3 x 0x34 bytes; everything else is rewritten byte-identically (checked by a round trip)."""
import os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oqt_insert as Q

MODEL = 285
HALF = 1.9                                            # half the log's length (bbox x -1.80..1.76)
# (x, y, z, facing yaw in degrees) where the player stood, game coordinates on the valley map
SPOTS = [(182.0, 13.91, 177.0, 99.0),                # 1: dirt road by the waterfall fence
         (283.98, 21.62, 122.37, 149.0),             # 2: clearing under the cliff
         (75.44, 0.47, 117.60, -160.0)]              # 3: orchard path
MARK = 0.0123                                         # added to x and z of every log (runtime lookup key)

def spots():
    return [(round(x, 2) + MARK, y, round(z, 2) + MARK, yaw) for x, y, z, yaw in SPOTS]

def main():
    outdir, files = sys.argv[1], sys.argv[2:]
    os.makedirs(outdir, exist_ok=True)
    for f in files:
        d = open(f, 'rb').read(); root = Q.read(d)
        assert Q.write(root) == d, f + ': round trip differs'
        before = root.count
        for x, y, z, yaw in spots():
            Q.insert(root, Q.record(MODEL, x, y, z, yaw), HALF)
        out = Q.write(root)
        chk = Q.read(out)
        assert chk.count == before + 3
        open(os.path.join(outdir, os.path.basename(f)), 'wb').write(out)
        print('%s: %d -> %d bytes, %d -> %d records' % (os.path.basename(f), len(d), len(out), before, chk.count))
    for i, (x, y, z, yaw) in enumerate(spots(), 1):
        print('log %d at (%.4f, %.2f, %.4f) yaw %.0f' % (i, x, y, z, yaw))

if __name__ == '__main__':
    main()
