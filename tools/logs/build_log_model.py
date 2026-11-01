#!/usr/bin/env python3
"""Choppable log for the valley (GYWEE9 US): mapobj.gpl model 285 = obj04-L (the hollow log, model 198)
rebuilt as a closed 8-sided trunk (obj04-L's own mesh is open along a top seam as well as at the
ends, so its rims can't be capped). Sides: the tree bark of texture #16 (tree3L-wood's area of it);
ends: the tree stump's ring region of the prop atlas (#0, kilikabu1-L's cut top). Display-list
sizes are padded to 32 bytes; every triangle is drawn in both windings.

usage: build_log_model.py mapobj.gpl OUTDIR
Writes OUTDIR/mapobj.gpl (286 models) and OUTDIR/log_model_report.txt. Reads only its input.

mapobj.gpl: u32 magic 005BBC61, bbox-table size, bbox-table offset, model count, model-table offset (0x14);
table: (model data offset, name offset) per model; model data; names; bbox table (6 f32 per model).
Model: +0 pos hdr (data, u16 count, fmt 0x3E = s16/14 frac, 3), +4 colour hdr, +8 uv hdr (data, count,
fmt, 2, name offset of 'mapobj.tpl', 0), +0xC normal hdr (global table: 0, 0xF3, 0x40, 3, 41C80000),
+0x10 material (first DL, command list, count<<16), +0x14 01FF0000; commands are 16 bytes:
01 = texture (low byte = mapobj.tpl index), 03 = mode, 02 = draw (vertex format, DL, size).
Vertex formats: 0x8A8 = pos, normal, colour, uv (u8 each); 0x828 = pos, normal, uv."""
import math, os, struct, sys

BASE, STUMP, NEW = 198, 143, 285
TEX_BARK, TEX_ATLAS = 16, 0
BARK_RECT = (0.515, 0.01, 0.745, 0.998)  # u0, v0, u1, v1: the left half of tree3L-wood's bark in texture 16
BARK_WRAPS = 2                            # (its two halves differ, with a seam: one half, twice round)

def be32(d, o): return struct.unpack_from('>I', d, o)[0]

def read_gpl(g):
    magic, bsize, boff, n, toff = struct.unpack_from('>5I', g, 0)
    assert magic == 0x005BBC61 and toff == 0x14
    ents = [struct.unpack_from('>II', g, toff + 8 * k) for k in range(n)]
    ends = [ents[k + 1][0] for k in range(n - 1)] + [min(e[1] for e in ents)]
    models = [g[ents[k][0]:ends[k]] for k in range(n)]
    names = [g[o:g.index(b'\0', o)] for _, o in ents]
    boxes = [g[boff + 24 * k:boff + 24 * k + 24] for k in range(n)]
    return models, names, boxes

def tris_of(m, dl, size, per):
    i = dl; out = []
    while i < dl + size and m[i] in (0x80, 0x90, 0x98, 0xA0):
        op = m[i]; k = struct.unpack_from('>H', m, i + 1)[0]
        v = [tuple(m[i + 3 + per * q:i + 3 + per * (q + 1)]) for q in range(k)]; i += 3 + per * k
        if op == 0x90: out += [v[j:j + 3] for j in range(0, k, 3)]
        elif op == 0x98: out += [(v[j], v[j + 1], v[j + 2]) if j % 2 == 0 else (v[j + 1], v[j], v[j + 2]) for j in range(k - 2)]
        elif op == 0x80: out += [t for j in range(0, k, 4) for t in ((v[j], v[j + 1], v[j + 2]), (v[j], v[j + 2], v[j + 3]))]
    return out

def model_parts(m):
    po, pc = struct.unpack_from('>IH', m, 0x1C)
    P = [struct.unpack_from('>3h', m, po + 6 * k) for k in range(pc)]
    ch = be32(m, 4); cd, cc = struct.unpack_from('>IH', m, ch); C = m[cd:cd + 3 * cc]
    uh = be32(m, 8); ud, uc = struct.unpack_from('>IH', m, uh)
    UV = [struct.unpack_from('>2h', m, ud + 4 * k) for k in range(uc)]
    mat = be32(m, 0x10); _, cp, nc = struct.unpack_from('>III', m, mat)
    cmds = [struct.unpack_from('>4I', m, cp + 16 * c) for c in range(nc >> 16)]
    return P, C, UV, cmds

SIDES, RADIUS, HALF_LEN = 8, 0.32, 1.75

def build_model(base, stump):
    """a closed 8-sided trunk lying along x on the ground: bark (texture 16) around it, the stump's
    rings (atlas #0) on both ends. Normals are global-table indices taken from obj04-L's vertices
    whose directions are closest (that table has no data in the file to compute from)."""
    P0, C0, UV0, cmds0 = model_parts(base)
    d0 = [c for c in cmds0 if c[0] >> 24 == 2][0]
    tris0 = tris_of(base, d0[2], d0[3], 4)
    Pf = [(x / 16384, y / 16384, z / 16384) for x, y, z in P0]
    cy0 = sum(p[1] for p in Pf) / len(Pf); cz0 = sum(p[2] for p in Pf) / len(Pf)
    nidx = {}
    for t in tris0:
        for v in t: nidx.setdefault(v[0], v[1])
    dirs = []                                              # (direction in the y-z plane, normal index)
    for k, n in nidx.items():
        dy, dz = Pf[k][1] - cy0, Pf[k][2] - cz0; l = math.hypot(dy, dz)
        if l > 0.1: dirs.append((dy / l, dz / l, n))
    def normal_for(dy, dz):
        return max(dirs, key=lambda d: d[0] * dy + d[1] * dz)[2]
    # the stump's ring rectangle in the atlas
    sP, _, sUV, scmds = model_parts(stump)
    sd = [c for c in scmds if c[0] >> 24 == 2][0]
    top = []
    for t in tris_of(stump, sd[2], sd[3], 3):
        a, b, c = [sP[v[0]] for v in t]
        n = [(b[1]-a[1])*(c[2]-a[2])-(b[2]-a[2])*(c[1]-a[1]), (b[2]-a[2])*(c[0]-a[0])-(b[0]-a[0])*(c[2]-a[2]),
             (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])]
        if abs(n[1]) > 0.8 * math.sqrt(sum(x * x for x in n)): top += [(sUV[v[-1]][0] / 16384, sUV[v[-1]][1] / 16384) for v in t]
    u0 = min(u for u, v in top); u1 = max(u for u, v in top); v0 = min(v for u, v in top); v1 = max(v for u, v in top)
    uc, vc, ru, rv = (u0 + u1) / 2, (v0 + v1) / 2, (u1 - u0) / 2 * 0.92, (v1 - v0) / 2 * 0.92
    bu0, bv0, bu1, bv1 = BARK_RECT
    q = lambda f: int(round(f * 16384))
    P, UV = [], []
    ang = [2 * math.pi * i / SIDES for i in range(SIDES)]
    ring = {}
    for e, x in ((0, -HALF_LEN), (1, HALF_LEN)):
        for i, a in enumerate(ang):
            ring[e, i] = len(P); P.append((q(x), q(RADIUS + RADIUS * math.cos(a)), q(RADIUS * math.sin(a))))
    centre = {0: len(P), 1: len(P) + 1}
    P += [(q(-HALF_LEN), q(RADIUS), 0), (q(HALF_LEN), q(RADIUS), 0)]
    side_uv = {}; per = SIDES // BARK_WRAPS
    for e in (0, 1):
        for i in range(per + 1):                              # one wrap's columns; faces reuse them
            side_uv[e, i] = len(UV); UV.append((q(bu0 + (bu1 - bu0) * i / per), q(bv0 + (bv1 - bv0) * e)))
    cap_uv = {}
    for i, a in enumerate(ang):
        cap_uv[i] = len(UV); UV.append((q(uc + ru * math.cos(a)), q(vc + rv * math.sin(a))))
    cap_c = len(UV); UV.append((q(uc), q(vc)))
    side, caps = [], []
    for i in range(SIDES):
        j = (i + 1) % SIDES
        na, nb = normal_for(math.cos(ang[i]), math.sin(ang[i])), normal_for(math.cos(ang[j]), math.sin(ang[j]))
        c0 = i % per
        a0, a1 = (ring[0, i], na, side_uv[0, c0]), (ring[1, i], na, side_uv[1, c0])
        b0, b1 = (ring[0, j], nb, side_uv[0, c0 + 1]), (ring[1, j], nb, side_uv[1, c0 + 1])
        for t in ((a0, b0, b1), (a0, b1, a1)):
            side.append(t); side.append((t[0], t[2], t[1]))          # both windings
        nend = normal_for(math.cos(ang[i]), math.sin(ang[i]))        # (no +-x normal known: the rim's)
        for e in (0, 1):
            t = ((centre[e], nend, cap_c), (ring[e, i], nend, cap_uv[i]), (ring[e, j], nend, cap_uv[j]))
            caps.append(t); caps.append((t[0], t[2], t[1]))
    dl = lambda ts: bytes([0x90]) + struct.pack('>H', 3 * len(ts)) + b''.join(bytes(v) for t in ts for v in t)
    al = lambda b, a: b + bytes((-len(b)) % a)
    dlA, dlB = al(dl(side), 0x20), al(dl(caps), 0x20)       # display list sizes are whole 32-byte blocks
    m = bytearray(0x1C)
    pos_h = len(m); m += bytes(8); pos_d = len(m)
    m += b''.join(struct.pack('>3h', *p) for p in P); m = bytearray(al(bytes(m), 4))
    col_h = len(m); m += bytes(8); col_d = len(m); m += C0; m = bytearray(al(bytes(m), 4))
    uv_h = len(m); m += bytes(16); uv_d = len(m)
    m += b''.join(struct.pack('>2h', *t) for t in UV); m = bytearray(al(bytes(m), 4))
    nrm_h = len(m); m += struct.pack('>IHBBI', 0, 0xF3, 0x40, 3, 0x41C80000)
    mat = len(m); m += bytes(12 + 16 * 6)
    m = bytearray(al(bytes(m), 0x20))
    oA = len(m); m += dlA
    oB = len(m); m += dlB
    name = len(m) + 12; m += bytes(12) + b'mapobj.tpl\0\0'
    struct.pack_into('>5I', m, 0, pos_h, col_h, uv_h, nrm_h, mat); struct.pack_into('>I', m, 0x14, 0x01FF0000)
    struct.pack_into('>IHBB', m, pos_h, pos_d, len(P), 0x3E, 3)
    struct.pack_into('>IHBB', m, col_h, col_d, len(C0) // 3, 0, 3)
    struct.pack_into('>IHBBII', m, uv_h, uv_d, len(UV), 0x3E, 2, name, 0)
    cmds = [(0x01FF0000, 0x11110000 | TEX_BARK, 0, 0), (0x03000000, 1, 0, 0), (0x02000000, 0x828, oA, len(dlA)),
            (0x01FF0000, 0x11110000 | TEX_ATLAS, 0, 0), (0x03000000, 1, 0, 0), (0x02000000, 0x828, oB, len(dlB))]
    struct.pack_into('>III', m, mat, oA, mat + 12, len(cmds) << 16)
    for k, c in enumerate(cmds): struct.pack_into('>4I', m, mat + 12 + 16 * k, *c)
    box = [min(p[i] for p in P) / 16384 for i in range(3)] + [max(p[i] for p in P) / 16384 for i in range(3)]
    info = dict(verts=len(P), uvs=len(UV), side_tris=len(side), cap_tris=len(caps), ring_uv=(round(uc, 4), round(vc, 4)), size=len(m))
    return bytes(m), box, info

def main():
    src, outdir = sys.argv[1:3]
    g = open(src, 'rb').read()
    models, names, boxes = read_gpl(g)
    assert len(models) == 285 and names[BASE] == b'obj04-L' and names[STUMP] == b'kilikabu1-L', 'unexpected mapobj.gpl'
    new, box, info = build_model(models[BASE], models[STUMP])
    models.append(new); names.append(b'obj04c-L'); boxes.append(struct.pack('>6f', *box))
    n = len(models); toff = 0x14
    first = toff + 8 * n
    first += (0x1C - first) % 0x20                      # keep each model at its original offset mod 0x20
    out = bytearray(first); offs = []
    orig_first = struct.unpack_from('>I', g, toff)[0]
    for k, m in enumerate(models):
        if k < 285:
            want = struct.unpack_from('>I', g, toff + 8 * k)[0] - orig_first + first
            assert want >= len(out); out += bytes(want - len(out))
        else:
            out += bytes((-len(out)) % 0x20)            # the new model's display lists are 0x20-aligned
        offs.append(len(out)); out += m
    name_offs = []
    for nm in names: name_offs.append(len(out)); out += nm + b'\0'
    out += bytes((-len(out)) % 0x20)
    boff = len(out); out += b''.join(boxes)
    struct.pack_into('>5I', out, 0, 0x005BBC61, 24 * n, boff, n, toff)
    for k in range(n): struct.pack_into('>II', out, toff + 8 * k, offs[k], name_offs[k])
    # self-check: every original model byte-identical at an offset with the same alignment
    for k in range(285):
        assert out[offs[k]:offs[k] + len(models[k])] == models[k]
        assert (offs[k] - struct.unpack_from('>I', g, toff + 8 * k)[0]) % 0x20 == 0
    os.makedirs(outdir, exist_ok=True)
    open(os.path.join(outdir, 'mapobj.gpl'), 'wb').write(out)
    with open(os.path.join(outdir, 'log_model_report.txt'), 'w') as f:
        f.write('mapobj.gpl %d -> %d bytes, %d models; model %d "obj04c-L" at %#x\n' % (len(g), len(out), n, NEW, offs[NEW]))
        f.write('%r\nbbox %s\n' % (info, [round(x, 3) for x in box]))
    print(open(os.path.join(outdir, 'log_model_report.txt')).read())

if __name__ == '__main__':
    main()
