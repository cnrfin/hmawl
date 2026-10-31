"""Build the blank body (blank/blank_v3.npz: clean all-quad mesh on Celia's joints) as game character
files on Celia's skeleton, same scheme as build_goddess.py: <name>.arc + <name>.anm.arc (Celia's 10
animations, unchanged: the body is built on her joints). Every vertex rigidly on one Celia node,
chosen by body part (nearest shape of the SDF) and position along the limb. Plain skin textures:
b0 #0 = body, b0 #1 = head (cylindrical UVs, face at the centre: ready for painting features).
usage: build_blank.py NAME OUTDIR"""
import sys, os, re, struct, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
PM = os.path.join(HERE, '..', 'pm'); sys.path[:0] = [PM, os.path.join(HERE, 'blank')]
from awlchar import act, world, qmat
from anm import qcomps
from PIL import Image
import blank as BL
NAME, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
W_ = os.path.join(HERE, '..', 'wally') + '/'
FRAC = 13
al = lambda b, a: b + bytes((-len(b)) % a)
SK = os.path.join(HERE, '..', 'celia') + '/'
nodes = act(open(SK + 'sepi_0.act', 'rb').read())
newT = [np.array(nd['T']) for nd in nodes]; K = 1.0          # her own joints

SKIN = (246, 214, 182)
body = Image.new('RGBA', (32, 32), SKIN + (255,))          # plain for now (small: slot-37 archive budget)
head = Image.new('RGBA', (32, 32), SKIN + (255,))

d = np.load(os.path.join(HERE, 'blank', 'blank_v3.npz')); PV, TF = d['V'], d['F']
# ---- body part per vertex: the SDF primitive nearest to it
S = BL.S; X = PV
def prim(P):
    m = lambda c, s: np.array(c) * [s, 1, 1]
    out = {}
    out['head'] = np.minimum.reduce([BL.ell(P, *S['cran']), BL.ell(P, *S['jaw']), BL.ell(P, *S['chin']),
                                     BL.ell(P, m(S['ear'][0], 1), S['ear'][1]), BL.ell(P, m(S['ear'][0], -1), S['ear'][1])])
    out['neck'] = BL.cap(P, *S['neck'])
    out['torso'] = np.minimum.reduce([BL.ell(P, *S['chest']), BL.ell(P, *S['waist']), BL.ell(P, *S['hips'])] +
                                     [np.linalg.norm(P - m(S['bust'][0], s), axis=-1) - S['bust'][1] for s in (1, -1)])
    for s, sd in ((1, 'L'), (-1, 'R')):
        out['arm' + sd] = np.minimum.reduce([BL.cap(P, m(S[k][0], s), m(S[k][1], s), *S[k][2:]) for k in ('shoulder', 'upper', 'fore')])
        out['hand' + sd] = np.minimum(BL.rbox(P, m(S['palm'][0], s), S['palm'][1], S['palm'][2]), BL.rbox(P, m(S['mitt'][0], s), S['mitt'][1], S['mitt'][2]))
        out['thumb' + sd] = BL.cap(P, m(S['thumb'][0], s), m(S['thumb'][1], s), *S['thumb'][2:])
        out['leg' + sd] = np.minimum.reduce([BL.cap(P, m(S['thigh'][0], s), m(S['thigh'][1], s), *S['thigh'][2:]),
                                            BL.cap(P, m(S['shin'][0], s), m(S['shin'][1], s), *S['shin'][2:]), BL.ell(P, m(S['calf'][0], s), S['calf'][1])])
        out['foot' + sd] = BL.rbox(P, m(S['foot'][0], s), S['foot'][1], S['foot'][2])
    return out
pr = prim(X); names = list(pr); lab = np.array(names)[np.argmin(np.stack([pr[n] for n in names]), 0)]
def node_of(p, part):
    x, y, z = p; ax = abs(x); o = 0 if x >= 0 else 11; ol = 0 if x >= 0 else 7     # left = +x (Celia)
    if part == 'head': return 7
    if part == 'neck': return 7 if y > 0.875 else 6
    if part == 'torso':
        if ax > 0.115 and y > 0.70: return 12 + o
        return 3 if y < 0.60 else (4 if y < 0.70 else 5)
    if part.startswith('arm'): return 5 if ax < 0.10 else (12 + o if ax < 0.255 else 13 + o)
    if part.startswith('hand'): return 13 + o if ax < 0.38 else (15 + o if ax < 0.475 else 17 + o)
    if part.startswith('thumb'): return 19 + o if ax < 0.44 else 20 + o
    if part.startswith('leg'): return 3 if y > 0.47 else (37 + ol if y > 0.355 else (38 + ol if y > 0.16 else 40 + ol))
    if part.startswith('foot'): return 41 + ol if z > 0.10 else (38 + ol if y > 0.16 else 40 + ol)
NODE = np.array([node_of(p, l) for p, l in zip(X, lab)])
# ---- UVs: body = centre of the plain body texture; head = cylinder around the head, face at u = 0.5
def head_uv(p):
    u = 0.5 + np.arctan2(p[0], p[2]) / (2 * np.pi); v = np.clip((1.34 - p[1]) / 0.52, 0, 1)
    return (u, v)
verts = [(PV[i], int(NODE[i])) for i in range(len(PV))]
uvs = [(0.5, 0.5)] + [head_uv(p) for p in PV]          # 0 = body; 1 + i = head uv of vertex i
tris = {0: [], 1: []}
for a, b, c in TF:
    if NODE[a] == NODE[b] == NODE[c] == 7: tris[1].append(((a, b, c), (1 + a, 1 + b, 1 + c)))
    else: tris[0].append(((a, b, c), (0, 0, 0)))
P = np.array([v[0] for v in verts]); B = np.array([v[1] for v in verts])
N = np.zeros_like(P)
for g in tris.values():
    for (a, b, c), _ in g:
        n = np.cross(P[b] - P[a], P[c] - P[a]); N[a] += n; N[b] += n; N[c] += n
N /= np.maximum(np.linalg.norm(N, axis=1)[:, None], 1e-9)
# skin groups: per node, <= 128 vertices, never sharing a 32-byte block (see pm/build_char.py)
order = []; groups = []; slot = 0
for b in sorted(set(B)):
    idx = [i for i in range(len(P)) if B[i] == b]
    for c in range(0, len(idx), 128):
        ch = idx[c:c + 128]
        if groups:
            pb, ps, pc = groups[-1]; need = ((ps + pc) * 12 + 0x1F) & ~0x1F
            while (slot * 12) & ~0x1F < need: slot += 1
        n_ = max(len(ch), 2)                      # the game's 1-bone skin loop needs >= 2 vertices (count 1 loops
        groups.append((b, slot, n_))              # through memory): pad with an unused copy (filled below)
        for k, i in enumerate(ch): order.append((slot + k, i))
        slot += n_
nbuf = slot
lb, ls_, lc = groups[-1]; a0 = (ls_ * 12) & ~0x1F
nbuf = max(nbuf, -(-(a0 + ((lc * 12 + ls_ * 12 % 32 + 0x1F) & ~0x1F)) // 12))
pos_of = {i: s_ for s_, i in order}
P2 = np.zeros((nbuf, 3)); N2 = np.zeros((nbuf, 3)); N2[:, 1] = 1.0
for s_, i in order: P2[s_] = P[i]; N2[s_] = N[i]
filled = set(s_ for s_, i in order)
for s_ in range(nbuf):
    if s_ not in filled: P2[s_] = P2[s_ - 1]; N2[s_] = N2[s_ - 1]
for g in tris: tris[g] = [(tuple(pos_of[i] for i in pi), ti) for pi, ti in tris[g]]
q = lambda x: int(np.clip(np.round(x * (1 << FRAC)), -32768, 32767))
vbuf = b''.join(struct.pack('>6h', *[q(c) for c in P2[i]], *[q(c) for c in N2[i]]) for i in range(len(P2)))

# ---------------------------------------------------------------- gpl
def strips(trilist):
    """greedy triangle strips. A corner is (position, uv); in the emitted (GC) order a strip v0..vn draws
    (v_j, v_j+1, v_j+2) for even j and (v_j+1, v_j, v_j+2) for odd j"""
    tris_ = [tuple(zip(pi[::-1], ti[::-1])) for pi, ti in trilist]          # GC front face order
    by_edge = {}
    for k, (a, b, c) in enumerate(tris_):
        for e in ((a, b), (b, c), (c, a)): by_edge.setdefault(e, []).append(k)
    used = [False] * len(tris_); out = []
    nbr = [set() for _ in tris_]
    for e, ks in by_edge.items():
        for k in ks:
            for k2 in by_edge.get((e[1], e[0]), []): nbr[k].add(k2)
    def free(k): return sum(1 for j in nbr[k] if not used[j])
    def third(t, a, b):                                  # third corner if (a, b) is an edge of t in order
        for i in range(3):
            if t[i] == a and t[(i + 1) % 3] == b: return t[(i + 2) % 3]
        return None
    while not all(used):
        k0 = min((k for k in range(len(tris_)) if not used[k]), key=free)
        used[k0] = True
        st = list(tris_[k0])
        for r in range(3):                               # rotation whose strip continues furthest from the seed
            a_, b_ = tris_[k0][(r + 1) % 3], tris_[k0][(r + 2) % 3]
            if any(not used[k] for k in by_edge.get((b_, a_), [])): st = [tris_[k0][r], a_, b_]; break
        while True:
            j = len(st) - 2
            a, b = (st[-2], st[-1]) if j % 2 == 0 else (st[-1], st[-2])
            nxt = None
            for k in by_edge.get((a, b), []):
                if not used[k]:
                    x = third(tris_[k], a, b)
                    if x is not None: nxt = (k, x); break
            if nxt is None: break
            used[nxt[0]] = True; st.append(nxt[1])
        out.append(st)
    return out
def dl(trilist):
    out = b''
    for st in strips(trilist):
        out += bytes([0x90 if len(st) == 3 else 0x98]) + struct.pack('>H', len(st))
        for p, t_ in st: out += struct.pack('>HHH', p, p, t_)
    return al(out, 0x20)
def check_strips(trilist):
    """the strips draw exactly the input triangles with the same facing"""
    norm = lambda t: min(t[i:] + t[:i] for i in range(3))
    want = sorted(norm(tuple(zip(pi[::-1], ti[::-1]))) for pi, ti in trilist)
    got = []
    for st in strips(trilist):
        for j in range(len(st) - 2):
            got.append(norm((st[j], st[j + 1], st[j + 2]) if j % 2 == 0 else (st[j + 1], st[j], st[j + 2])))
    assert sorted(got) == want, 'strips do not match the triangles'
def build_gpl():
    tgpl = open(W_ + 'sua_0.gpl', 'rb').read()[0x1C:]
    m = bytearray(0x24)
    m[0x1C:0x24] = struct.pack('>IHBB', 0x24, len(P2), 0x30 | FRAC, 6)
    m += vbuf; m = bytearray(al(bytes(m), 4))
    col_off = len(m); ch = bytearray(tgpl[0x3c44:0x3c50]); struct.pack_into('>I', ch, 0, col_off + 8); m += ch
    uv_off = len(m); m += bytes(0x10); uv_data = len(m)
    m += b''.join(struct.pack('>hh', int(np.clip(round(u * 16384), -32768, 32767)), int(np.clip(round(v * 16384), -32768, 32767))) for u, v in uvs)
    m = bytearray(al(bytes(m), 4))
    nrm_off = len(m); m += struct.pack('>IHBBI', 0x24 + 6, len(P2), 0x30 | FRAC, 6, 0x41C80000)
    mat_off = len(m); ncmd = 4
    m += bytes(0xC + 0x10 * ncmd)
    while (len(m) + 0x1C) % 0x20: m += b'\0'
    o_body = len(m); d_body = dl(tris[0]); m += d_body
    o_head = len(m); d_head = dl(tris[1]); m += d_head
    struct.pack_into('>III', m, mat_off, o_body, mat_off + 0xC, ncmd << 16)
    cmds = [struct.pack('>IIII', 0x01FF0000, 0x11110000, 0, 0),                 # body texture (b0 #0)
            struct.pack('>IIII', 0x03000000, 1, 0, 0),
            struct.pack('>IIII', 0x02000000, 0xC3C, o_body, len(d_body)),
            struct.pack('>IIII', 0x01020000, 0x11110001, o_head, len(d_head))]   # head texture (sel 02 = b0 #1), draw
    for k, c in enumerate(cmds): m[mat_off + 0xC + 0x10 * k:mat_off + 0x1C + 0x10 * k] = c
    tail = len(m); m += (NAME + '.tpl').encode() + b'\0\0\0' + (NAME[0].upper() + NAME[1:] + '_L:Layer1').encode() + b'\0'
    struct.pack_into('>IHBBII', m, uv_off, uv_data, len(uvs), 0x3E, 2, tail, 0)
    struct.pack_into('>5I', m, 0, 0x1C, col_off, uv_off, nrm_off, mat_off)
    struct.pack_into('>II', m, 0x14, 0x01FF0000, 0)
    return struct.pack('>7I', 0x005BBC61, 0, 0, 1, 0x14, 0x1C, len(m)) + bytes(m)

def build_skn():
    n1 = len(groups); t1 = 0x24
    data_start = (t1 + 0x40 * n1 + 0x1F) & ~0x1F
    ents = bytearray(0x40 * n1); data = bytearray()
    for k, (b, start, cnt) in enumerate(groups):
        dst_byte = start * 12; algn = dst_byte % 0x20; dst = dst_byte - algn
        while (data_start + len(data)) % 0x20: data += b'\0'
        srco = data_start + len(data)
        data += bytes(algn) + vbuf[start * 12:(start + cnt) * 12]
        struct.pack_into('>IIHHB', ents, 0x40 * k + 0x30, srco, dst, b, cnt, algn)
    body_ = bytes(ents) + bytes(data_start - t1 - len(ents)) + bytes(data)
    end = t1 + len(body_)
    hdr = struct.pack('>HHHBB', n1, 0, 0, FRAC, 0) + struct.pack('>7I', t1, end, end, 0, 0, end, 0)
    return al(hdr + body_, 0x20)

def build_act():
    d = bytearray(open(SK + 'sepi_0.act', 'rb').read())
    n = struct.unpack_from('>I', d, 4)[0]
    for i in range(n):
        x = struct.unpack_from('>I', d, 0x20 + 0x1C * i)[0]
        struct.pack_into('>3f', d, x + 0x20, *[float(v) for v in newT[i]])
    i = d.find(b'sepi_0.gpl'); d[i:i + 10] = (NAME + '.gpl').encode()[:10].ljust(10, b'\0')
    return bytes(d)

def retarget_anim(raw):
    d = bytearray(raw)
    n = struct.unpack_from('>H', d, 4)[0]
    for length, off, nkeys, node, packed in [struct.unpack_from('>fIHHI', d, 0x8 + 16 * i) for i in range(n)]:
        comps = qcomps(packed); nc = len(comps); b2, b3 = (packed >> 8) & 0xFF, packed & 0xFF
        restT = np.array(nodes[node]['T']); nT = newT[node]
        def fix(p):
            v = np.array(struct.unpack_from('>3h', d, off + 2 * p)) / 16384.
            struct.pack_into('>3h', d, off + 2 * p, *[int(np.clip(round(c * 16384), -32768, 32767)) for c in nT + (v - restT) * K])
        p = 0
        if b3 & 0x08: p += nc
        if b3 & 0x01: fix(p); p += 3
        if b2 & 0x70 and b2 & 0x01:
            for k in range(nkeys): fix(p + 1 + nc); p += 1 + 2 * nc + 3
        elif b2 & 0x01:
            for k in range(nkeys): fix(p + 1); p += 4
    return bytes(d)
ANIMS = 10      # Celia's: 0 idle, 1 walk, 2 holding idle, 3 put away, 4 explain, 5 run, 6 plead, 7 dizzy, 8 crouch, 9 kitchen

def c565(c): return (int(c[0]) >> 3) << 11 | (int(c[1]) >> 2) << 5 | (int(c[2]) >> 3)
def un565(v): return np.array([(v >> 11 & 31) * 255 // 31, (v >> 5 & 63) * 255 // 63, (v & 31) * 255 // 31], float)
def cmpr(img):
    a = np.array(img.convert('RGBA')).astype(float)
    a = np.pad(a, ((0, (-a.shape[0]) % 8), (0, (-a.shape[1]) % 8), (0, 0)), mode='edge')   # whole 8x8 tiles
    h, w = a.shape[:2]; out = bytearray()
    for ty in range(0, h, 8):
        for tx in range(0, w, 8):
            for sb in range(4):
                bx, by = tx + (sb & 1) * 4, ty + (sb >> 1) * 4
                rgb = a[by:by + 4, bx:bx + 4, :3].reshape(-1, 3); al_ = a[by:by + 4, bx:bx + 4, 3].reshape(-1)
                if (al_ < 128).any():                          # 3-colour mode + transparent (index 3)
                    op = al_ >= 128
                    if not op.any(): out += struct.pack('>HHI', 0, 0xFFFF, 0xFFFFFFFF); continue
                    o = rgb[op]; c = o - o.mean(0)
                    ax = np.linalg.svd(c, full_matrices=False)[2][0] if np.abs(c).sum() > 0 else np.array([1, 1, 1.])
                    pr = c @ ax; c0, c1 = c565(o[pr.argmax()]), c565(o[pr.argmin()])
                    if c0 > c1: c0, c1 = c1, c0                  # c0 <= c1 selects this mode
                    p0, p1 = un565(c0), un565(c1); pal = np.array([p0, p1, (p0 + p1) / 2])
                    best = ((rgb[:, None, :] - pal[None]) ** 2).sum(2).argmin(1); idx = 0
                    for k in range(16): idx = idx << 2 | (int(best[k]) if op[k] else 3)
                    out += struct.pack('>HHI', c0, c1, idx); continue
                # endpoints: the two most distant colours along the block's main axis
                c = rgb - rgb.mean(0); ax = np.linalg.svd(c, full_matrices=False)[2][0] if np.abs(c).sum() > 0 else np.array([1, 1, 1.])
                pr = c @ ax
                c0, c1 = c565(rgb[pr.argmax()]), c565(rgb[pr.argmin()])
                if c0 == c1: c0 = c0 | 0x20 if c0 & 0x20 == 0 else c0 & ~0x20
                if c0 < c1: c0, c1 = c1, c0
                p0, p1 = un565(c0), un565(c1); pal = np.array([p0, p1, (2 * p0 + p1) / 3, (p0 + 2 * p1) / 3])
                best = ((rgb[:, None, :] - pal[None]) ** 2).sum(2).argmin(1); idx = 0
                for k in range(16): idx = idx << 2 | int(best[k])
                out += struct.pack('>HHI', c0, c1, idx)
    return bytes(out)
def tpl(images):
    n = len(images); blobs = [cmpr(im) for im in images]
    out = bytearray(struct.pack('>III', 0x0020AF30, n, 0xC))
    for k in range(n): out += struct.pack('>II', 0xC + 8 * n + 0x24 * k, 0)
    pos = (0xC + 8 * n + 0x24 * n + 0x1F) & ~0x1F
    for im, b in zip(images, blobs):
        out += struct.pack('>HHIIIIIIBBBB', im.height, im.width, 14, pos, 1, 1, 1, 1, 0, 0, 0, 0)[:0x24].ljust(0x24, b'\0')
        pos = (pos + len(b) + 0x1F) & ~0x1F
    out = bytearray(al(bytes(out), 0x20))
    for b in blobs: out += al(b, 0x20)
    return bytes(out)

def u8(files):
    names = b'\0' + b''.join(n.encode() + b'\0' for n, _ in files)
    nn = len(files) + 1; hdr_size = 12 * nn + len(names)
    data_off = (0x20 + hdr_size + 0x1F) & ~0x1F
    nodes_ = [struct.pack('>III', 0x01000000, 0, nn)]; blob = b''; no = 1
    for n, d in files:
        nodes_.append(struct.pack('>III', no, data_off + len(blob), len(d))); no += len(n) + 1
        blob += al(d, 0x20)
    head_ = struct.pack('>IIII', 0x55AA382D, 0x20, hdr_size, data_off) + bytes(0x10)
    out = head_ + b''.join(nodes_) + names
    return out + bytes(data_off - len(out)) + blob

if __name__ == '__main__':
    sys.path.insert(0, '/home/user/hmawl/tools/logs')
    import u8arc
    pm = u8arc.read(open(os.path.join(HERE, '..', 'pkg36', 'postman_npc', 'pm_0.arc'), 'rb').read()); pn = u8arc.names(pm)
    def blank_frames(t):          # same frame count, every frame 1x1 transparent: her face is painted and her
        n_ = struct.unpack_from('>I', t, 4)[0]          # gpl never draws the eye/mouth materials (sel 00/01)
        return tpl([Image.new('RGBA', (1, 1), (0, 0, 0, 0))] * n_)
    f0e = blank_frames(pm['files'][pn['pm_0_f0_e.tpl']]); f0m = blank_frames(pm['files'][pn['pm_0_f0_m.tpl']])
    check_strips(tris[0]); check_strips(tris[1])
    gpl, skn, actb = build_gpl(), build_skn(), build_act()
    b0 = tpl([body, head])
    arc = u8([(NAME + '.act', actb), (NAME + '.gpl', gpl), (NAME + '.skn', skn), (NAME + '_b0.tpl', b0),
              (NAME + '_f0_e.tpl', f0e), (NAME + '_f0_m.tpl', f0m), ('_tmp.txt', b'')])
    anm = u8([('@', retarget_anim(open(SK + 'anm%02d.bin' % a, 'rb').read())) for a in range(ANIMS)])
    open(os.path.join(OUT, NAME + '.arc'), 'wb').write(arc)
    open(os.path.join(OUT, NAME + '.anm.arc'), 'wb').write(anm)
    body.save(os.path.join(OUT, 'b0_body.png')); head.save(os.path.join(OUT, 'b0_head.png'))
    print('vertices', len(P), 'buffer', len(P2), 'uvs', len(uvs), 'tris body/head', len(tris[0]), len(tris[1]),
          'skin groups', len(groups), 'nodes', sorted(set(B)))
    print(NAME + '.arc', len(arc), NAME + '.anm.arc', len(anm))
    # archives over 64 KB loaded into slot 37 overlapped the game's scratch matrix buffer (tests 1b-3:
    # garbled texture, then a crash); the teddy (62,976) and the Postman (63,328) load fine
    print('parts', {k: len(v) for k, v in (('act', actb), ('gpl', gpl), ('skn', skn), ('b0', b0), ('f0e', f0e), ('f0m', f0m))})
    assert len(arc) < 62976, 'larger than the teddy dar_0.arc (62,976 B)'
