#!/usr/bin/env python3
"""The game loads the valley's placements from mapc1..5.arc and the map-object models from
mapcommon.arc.clz (the loose .oqt/mapobj.gpl files on the disc are not read). This rebuilds them:
  mapcN.arc          mapN-p-other.oqt + the three log placements (build_log_maps.py)
  mapcommon.arc.clz  mapobj.gpl + model 285 (build_log_model.py), CLZ re-encoded
usage: build_log_archives.py SRC_DIR OUTDIR   (SRC_DIR holds mapc1..5.arc and mapcommon.arc.clz)"""
import os, sys, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import u8arc, oqt_insert as Q, build_log_maps as M, build_log_model as B
SP = os.path.join(HERE, '..', '..')

def clz_decompress(c):
    assert c[:4] == b'CLZ\0'; n = struct.unpack_from('>I', c, 4)[0]; out = bytearray(); i = 0x10
    while len(out) < n:
        f = c[i]; i += 1
        for k in range(8):
            if len(out) >= n: break
            if f >> k & 1:
                b0, b1 = c[i], c[i + 1]; i += 2
                d = 0x1000 - (b0 | (b1 & 0xF0) << 4); l = (b1 & 0xF) + 3
                for _ in range(l): out.append(out[-d])
            else: out.append(c[i]); i += 1
    return bytes(out)

def clz_compress(b):
    """greedy-with-lookahead LZSS (4 KB window, length 3..18), hash chains"""
    n = len(b); W = 0x1000; out = bytearray(b'CLZ\0' + struct.pack('>III', n, 0, n)); heads = {}; prev = [0] * n
    def best(i):
        if i + 3 > n: return 0, 0
        j = heads.get(b[i:i + 3], -1); bl, bd, tries = 0, 0, 0
        while j >= 0 and i - j <= W and tries < 48:
            l = 0
            while l < 18 and i + l < n and b[j + l] == b[i + l]: l += 1
            if l > bl: bl, bd = l, i - j
            if l == 18: break
            j = prev[j]; tries += 1
        return bl, bd
    def add(i):
        if i + 3 <= n:
            k = b[i:i + 3]; prev[i] = heads.get(k, -1); heads[k] = i
    i = 0
    while i < n:
        fpos = len(out); out.append(0); f = 0
        for k in range(8):
            if i >= n: break
            l, d = best(i)
            if l >= 3 and i + 1 < n:
                add(i); l2, _ = best(i + 1)
                if l2 > l + 1: l = 0
                prev_added = True
            else: prev_added = False
            if l >= 3:
                v = 0x1000 - d; out += bytes([v & 0xFF, ((v >> 4) & 0xF0) | (l - 3)]); f |= 1 << k
                for q in range(i + (1 if prev_added else 0), i + l): add(q)
                i += l
            else:
                if not prev_added: add(i)
                out.append(b[i]); i += 1
        out[fpos] = f
    return bytes(out)

def main():
    src, outdir = sys.argv[1:3]; os.makedirs(outdir, exist_ok=True)
    for c in range(1, 6):
        d = open(os.path.join(src, 'mapc%d.arc' % c), 'rb').read(); a = u8arc.read(d)
        assert u8arc.build(a, {}) == d
        k = u8arc.names(a)['map%d-p-other.oqt' % c]
        root = Q.read(a['files'][k]); before = root.count
        for x, y, z, yaw in M.spots(): Q.insert(root, Q.record(M.MODEL, x, y, z, yaw), M.HALF)
        new = Q.write(root); out = u8arc.build(a, {k: new})
        chk = u8arc.read(out); assert Q.read(chk['files'][k]).count == before + 3
        for kk in a['files']:
            if kk != k: assert chk['files'][kk] == a['files'][kk]
        open(os.path.join(outdir, 'mapc%d.arc' % c), 'wb').write(out)
        print('mapc%d.arc %d -> %d bytes (map%d-p-other.oqt %d -> %d records)' % (c, len(d), len(out), c, before, before + 3))
    c = open(os.path.join(src, 'mapcommon.arc.clz'), 'rb').read(); u = clz_decompress(c); a = u8arc.read(u)
    assert u8arc.build(a, {}) == u
    k = u8arc.names(a)['mapobj.gpl']; g = a['files'][k]
    models, names, boxes = B.read_gpl(g)
    newm, box, info = B.build_model(models[B.BASE], models[B.STUMP])
    import tempfile
    with tempfile.TemporaryDirectory() as t:
        open(os.path.join(t, 'in.gpl'), 'wb').write(g)
        sys.argv = ['x', os.path.join(t, 'in.gpl'), t]; B.main()
        ng = open(os.path.join(t, 'mapobj.gpl'), 'rb').read()
    nu = u8arc.build(a, {k: ng})
    nc = clz_compress(nu)
    assert clz_decompress(nc) == nu, 'CLZ round trip failed'
    open(os.path.join(outdir, 'mapcommon.arc.clz'), 'wb').write(nc)
    print('mapcommon.arc %d -> %d bytes; mapcommon.arc.clz %d -> %d bytes (round trip checked)' % (len(u), len(nu), len(c), len(nc)))

if __name__ == '__main__':
    main()
