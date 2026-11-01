#!/usr/bin/env python3
"""Snow on the valley logs (winter): mapobj.gpl model 286 "obj04snow-L", a thin snow pillow over the top
of the log (model 285), and three placements of it at the log spots (x marker +0.0246, the log's +0.0123
twice, so the code can tell them apart). The code shows a log's snow only in winter while the log is there.

usage: build_snow.py commonall.arc.clz mapc_dir OUTDIR
  commonall.arc.clz  the current one (mapobj.gpl with 286 models, 0-285)
  mapc_dir           mapc1..5.arc with the logs already placed
Writes OUTDIR/commonall.arc.clz and OUTDIR/mapc1..5.arc. Everything else keeps its bytes.

The pillow: 15 rows along the log x 11 columns round its top, a ragged lower edge (50-72 degrees
from the top, per row), lumpy thickness (0.075 * cos^1.5 on the ridge x 0.7-1.3) tapering at the ends,
and mottled blue-white vertex colours (format 0x8A8: pos, normal, colour, uv). Texture: mapobj.tpl #22
(a white tree silhouette, solid white in its trunk, the same in the spring and winter sets), every
vertex at one white texel; the colours do the shading. No snow texture exists in the map-object sets."""
import math, os, random, struct, sys, hashlib
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import u8arc, oqt_insert as Q
from build_log_archives import clz_decompress, clz_compress
from build_log_model import read_gpl, model_parts, tris_of, RADIUS, HALF_LEN
from build_log_maps import SPOTS, HALF

NEW, BASE, LOG = 286, 198, 285
TEX_WHITE, WHITE_UV = 22, (0.5, 0.74)
MARK2 = 0.0246
ROWS, COLS, SPAN = 14, 11, math.radians(72)
T_TOP, T_MIN, END_TAPER = 0.075, 0.006, 0.30

def snow_model(base):
    P0, _, UV0, cmds0 = model_parts(base)
    d0 = [c for c in cmds0 if c[0] >> 24 == 2][0]
    tris0 = tris_of(base, d0[2], d0[3], 4)
    Pf = [(x / 16384, y / 16384, z / 16384) for x, y, z in P0]
    cy0 = sum(p[1] for p in Pf) / len(Pf); cz0 = sum(p[2] for p in Pf) / len(Pf)
    nidx = {}
    for t in tris0:
        for v in t: nidx.setdefault(v[0], v[1])
    dirs = []
    for k, n in nidx.items():
        dy, dz = Pf[k][1] - cy0, Pf[k][2] - cz0; l = math.hypot(dy, dz)
        if l > 0.1: dirs.append((dy / l, dz / l, n))
    normal_for = lambda dy, dz: max(dirs, key=lambda d: d[0] * dy + d[1] * dz)[2]
    q = lambda f: int(round(f * 16384))
    rnd = random.Random(286)                                             # fixed: the same snow every build
    X0 = HALF_LEN * 0.95
    edge = [SPAN * (0.65 + 0.35 * rnd.random()) for r in range(ROWS + 1)]   # ragged lower edge per row
    lump = [[0.7 + 0.6 * rnd.random() for c in range(COLS)] for r in range(ROWS + 1)]
    P, C, idx, nrm = [], [], {}, {}
    for r in range(ROWS + 1):
        x = -X0 + 2 * X0 * r / ROWS + (rnd.random() - 0.5) * 0.06 * (0 < r < ROWS)
        taper = min(1.0, (X0 - abs(x)) / END_TAPER) ** 0.7
        for c in range(COLS):
            f = -1 + 2 * c / (COLS - 1)                                  # -1..1 across the top
            a = f * edge[r]
            t = T_MIN + T_TOP * (max(0.0, math.cos(a)) ** 1.5) * taper * lump[r][c]
            if abs(f) == 1: t = T_MIN                                    # the edge sits on the bark
            rr = RADIUS + t
            idx[r, c] = len(P); P.append((q(x), q(RADIUS + rr * math.cos(a)), q(rr * math.sin(a))))
            nrm[r, c] = normal_for(math.cos(a), math.sin(a))
            k = 0.86 + 0.14 * rnd.random() - 0.06 * abs(f)               # mottled, a little darker at the edge
            r8, g8, b8 = int(232 * k), int(238 * k), int(250 * k)        # blue-white, as RGB565 (format 0)
            C.append(struct.pack('>H', (r8 >> 3) << 11 | (g8 >> 2) << 5 | (b8 >> 3)))
    UV = [(q(WHITE_UV[0]), q(WHITE_UV[1]))]
    tris = []
    for r in range(ROWS):
        for c in range(COLS - 1):
            a, b, cc, d = [(idx[k], nrm[k], idx[k], 0) for k in ((r, c), (r, c + 1), (r + 1, c + 1), (r + 1, c))]
            for t in ((a, b, cc), (a, cc, d)):
                tris.append(t); tris.append((t[0], t[2], t[1]))          # both windings
    C0 = b''.join(C)
    assert len(P) < 256
    al = lambda b, n: b + bytes((-len(b)) % n)
    dlA = al(bytes([0x90]) + struct.pack('>H', 3 * len(tris)) + b''.join(bytes(v) for t in tris for v in t), 0x20)
    m = bytearray(0x1C)
    pos_h = len(m); m += bytes(8); pos_d = len(m)
    m += b''.join(struct.pack('>3h', *p) for p in P); m = bytearray(al(bytes(m), 4))
    col_h = len(m); m += bytes(8); col_d = len(m); m += C0; m = bytearray(al(bytes(m), 4))
    uv_h = len(m); m += bytes(16); uv_d = len(m)
    m += b''.join(struct.pack('>2h', *t) for t in UV); m = bytearray(al(bytes(m), 4))
    nrm_h = len(m); m += struct.pack('>IHBBI', 0, 0xF3, 0x40, 3, 0x41C80000)
    mat = len(m); m += bytes(12 + 16 * 3)
    m = bytearray(al(bytes(m), 0x20))
    oA = len(m); m += dlA
    name = len(m) + 12; m += bytes(12) + b'mapobj.tpl\0\0'
    struct.pack_into('>5I', m, 0, pos_h, col_h, uv_h, nrm_h, mat); struct.pack_into('>I', m, 0x14, 0x01FF0000)
    struct.pack_into('>IHBB', m, pos_h, pos_d, len(P), 0x3E, 3)
    struct.pack_into('>IHBB', m, col_h, col_d, len(C0) // 2, 0, 3)          # RGB565 entries
    struct.pack_into('>IHBBII', m, uv_h, uv_d, len(UV), 0x3E, 2, name, 0)
    cmds = [(0x01FF0000, 0x11110000 | TEX_WHITE, 0, 0), (0x03000000, 1, 0, 0), (0x02000000, 0x8A8, oA, len(dlA))]
    struct.pack_into('>III', m, mat, oA, mat + 12, len(cmds) << 16)
    for k, c in enumerate(cmds): struct.pack_into('>4I', m, mat + 12 + 16 * k, *c)
    box = [min(p[i] for p in P) / 16384 for i in range(3)] + [max(p[i] for p in P) / 16384 for i in range(3)]
    return bytes(m), box, len(P), len(tris)

def append_model(g, new, box, name):
    models, names, boxes = read_gpl(g)
    n0 = len(models); toff = 0x14
    models.append(new); names.append(name); boxes.append(struct.pack('>6f', *box))
    n = len(models)
    first0 = struct.unpack_from('>I', g, toff)[0]
    first = toff + 8 * n; first += (first0 - first) % 0x20             # each model keeps its offset mod 0x20
    out = bytearray(first); offs = []
    for k, m in enumerate(models):
        if k < n0:
            want = struct.unpack_from('>I', g, toff + 8 * k)[0] - first0 + first
            assert want >= len(out); out += bytes(want - len(out))
        else:
            out += bytes((-len(out)) % 0x20)
        offs.append(len(out)); out += m
    name_offs = []
    for nm in names: name_offs.append(len(out)); out += nm + b'\0'
    out += bytes((-len(out)) % 0x20)
    boff = len(out); out += b''.join(boxes)
    struct.pack_into('>5I', out, 0, 0x005BBC61, 24 * n, boff, n, toff)
    for k in range(n): struct.pack_into('>II', out, toff + 8 * k, offs[k], name_offs[k])
    for k in range(n0):
        assert out[offs[k]:offs[k] + len(models[k])] == models[k]
        assert (offs[k] - struct.unpack_from('>I', g, toff + 8 * k)[0]) % 0x20 == 0
    return bytes(out), offs[n0]

def main():
    clz, mapc_dir, out = sys.argv[1:4]
    os.makedirs(out, exist_ok=True)
    u = clz_decompress(open(clz, 'rb').read()); arc = u8arc.read(u); nm = u8arc.names(arc)
    k = nm['mapobj.gpl']; g = arc['files'][k]
    models, names, _ = read_gpl(g)
    assert len(models) == NEW and names[LOG] == b'obj04c-L' and names[BASE] == b'obj04-L', 'unexpected mapobj.gpl'
    new, box, nv, nt = snow_model(models[BASE])
    g2, at = append_model(g, new, box, b'obj04snow-L')
    nu = u8arc.build(arc, {k: g2})
    a2 = u8arc.read(nu)
    for j in arc['files']:
        if j != k: assert a2['files'][j] == arc['files'][j]
    c = clz_compress(nu); assert clz_decompress(c) == nu
    open(os.path.join(out, 'commonall.arc.clz'), 'wb').write(c)
    print('mapobj.gpl %d -> %d B: model %d at %#x, %d verts, %d tris, bbox %s; commonall %d B sha1 %s'
          % (len(g), len(g2), NEW, at, nv, nt, [round(v, 3) for v in box], len(c), hashlib.sha1(c).hexdigest()[:12]))
    for i in range(1, 6):
        fn = 'mapc%d.arc' % i
        a = u8arc.read(open(os.path.join(mapc_dir, fn), 'rb').read()); n2 = u8arc.names(a)
        ko = [j for name, j in n2.items() if name.endswith('-p-other.oqt')]; assert len(ko) == 1, fn
        d = a['files'][ko[0]]; root = Q.read(d); assert Q.write(root) == d
        before = root.count
        for x, y, z, yaw in SPOTS:
            Q.insert(root, Q.record(NEW, round(x, 2) + MARK2, y, round(z, 2) + 0.0123, yaw), HALF)
        d2 = Q.write(root); assert Q.read(d2).count == before + 3
        nb = u8arc.build(a, {ko[0]: d2})
        open(os.path.join(out, fn), 'wb').write(nb)
        print('%s: other.oqt %d -> %d records, arc %d B sha1 %s' % (fn, before, before + 3, len(nb), hashlib.sha1(nb).hexdigest()[:12]))

if __name__ == '__main__':
    main()
