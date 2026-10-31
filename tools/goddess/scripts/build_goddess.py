"""Build the Harvest Goddess (ch_315.dae, the user's model) as game character files:
<name>.arc (act, gpl, skn, b0/f0_e/f0_m tpl) and <name>.anm.arc (Celia's 10 animations on her bone lengths).
usage: build_goddess.py NAME OUTDIR         (NAME = gd_0 -> disc files gd/gd_0.arc, gd/gd_0.anm.arc)

Same scheme as the Postman (pm/build_char.py), on Celia's skeleton (sepi_0.act) with her joint
positions: every vertex rigidly on one Celia node (her largest weight, mapped), Celia's animations with
the translations moved to her bone lengths. Textures as Wally's: b0 #0 = body (sel FF), b0 #1 = head
(sel 02): her face, hair and eye textures packed into one 256x256 atlas. Opaque (vanilla body/head
textures use no transparency); transparent texels take the nearest opaque colour."""
import sys, os, re, struct, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
PM = os.path.join(HERE, '..', 'pm'); sys.path[:0] = [PM]
from awlchar import act, world, qmat
from anm import qcomps
from PIL import Image
NAME, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
SRC = os.path.join(HERE, 'model', 'Harvest Goddess copy') + '/'
W_ = os.path.join(HERE, '..', 'wally') + '/'
FRAC = 13
SCALE = 0.012          # 1.2x her source size (1.96 tall): she was small next to the player
al = lambda b, a: b + bytes((-len(b)) % a)

# ---------------------------------------------------------------- source model
t = open(SRC + 'ch_315.dae').read()
arr = {n: v for n, c, v in re.findall(r'<float_array id="([^"]+)" count="(\d+)">([^<]*)</float_array>', t)}
JN = re.search(r'<Name_array id="[^"]+" count="36">([^<]*)</Name_array>', t).group(1).split()
IB = np.array(arr['_0_0_ctrl_poses_array_id'].split(), float).reshape(-1, 4, 4)
J = {n: np.linalg.inv(m)[:3, 3] * SCALE for n, m in zip(JN, IB)}
src = []
for k in range(5):
    get = lambda pre: np.array(arr[[a for a in arr if a.startswith('_%d_0_%s' % (k, pre))][0]].split(), float)
    P = get('Position').reshape(-1, 3) * SCALE
    UV = get('TexCoord0').reshape(-1, 2)
    NS = get('Normal').reshape(-1, 3)
    g = re.search(r'<geometry id="_%d_0_geo_id".*?</geometry>' % k, t, re.S).group(0)
    mat = re.search(r'material="Mdl_0_Mtl_([^"]+)"', g).group(1)
    T = np.array(re.search(r'<p>([^<]*)</p>', g).group(1).split(), int).reshape(-1, 3)
    c = re.search(r'<controller id="_%d_0_ctrl_id".*?</controller>' % k, t, re.S).group(0)
    w = np.array(arr['_%d_0_ctrl_weights_array_id' % k].split(), float)
    vc = np.array(re.search(r'<vcount>([^<]*)</vcount>', c).group(1).split(), int)
    v = np.array(re.search(r'<v>([^<]*)</v>', c).group(1).split(), int)
    best, q = [], 0
    for n in vc:
        inf = [(JN[v[2 * (q + i)]], w[v[2 * (q + i) + 1]]) for i in range(n)]; q += n
        best.append(max(inf, key=lambda x: x[1])[0])
    src.append(dict(P=P, NS=NS, UV=UV, T=T, mat=mat, bone=best))

# ---------------------------------------------------------------- Celia's skeleton, her joints
# Celia (sepi_0): 2 pelvis, 3 hips, 4-5 spine, 6 chest, 7 head, 8-9 braid, 10-20 left arm (12 shoulder,
# 14 elbow, 16 wrist, 17 hand, 18-20 thumb), 21-31 right arm, 32-34 skirt, 35-41 left leg (36 hip,
# 38 knee, 39 ankle, 41 toe), 42-48 right leg. T-pose, facing +z, left = +x (as her model).
SK = os.path.join(HERE, '..', 'celia') + '/'
nodes = act(open(SK + 'sepi_0.act', 'rb').read())
Wb = world(nodes); Jw = np.array([w[:3, 3] for w in Wb])
mid = lambda a, b, s: a + (b - a) * s
fr = lambda i, a, b: (Jw[i][1] - Jw[a][1]) / (Jw[b][1] - Jw[a][1])           # where node i lies between a and b (by y)
frx = lambda i, a, b: (abs(Jw[i][0]) - abs(Jw[a][0])) / (abs(Jw[b][0]) - abs(Jw[a][0]))
hipL, kneeL, ankL = J['L_Hip'], J['L_Knee'], J['L_Ankle']
hipR, kneeR, ankR = J['R_Hip'], J['R_Knee'], J['R_Ankle']
shL, elL, wrL = J['L_Shoulder'], J['L_Elbow'], J['L_Wrist']
shR, elR, wrR = J['R_Shoulder'], J['R_Elbow'], J['R_Wrist']
neck = J['Head']
hipc = (hipL + hipR) / 2; shc = (shL + shR) / 2
K = neck[1] / Jw[7][1]                         # her size / Celia's (head base height)
tg = {2: hipc, 3: hipc, 35: hipc, 42: hipc}
tg[4] = mid(hipc, shc, fr(4, 3, 6)); tg[5] = mid(hipc, shc, fr(5, 3, 6)); tg[6] = shc; tg[7] = neck
tg[8] = J['B_Hair1']; tg[9] = J['B_Hair2']                                  # braid -> her back hair
for (s_, e, w), b in (((shL, elL, wrL), 10), ((shR, elR, wrR), 21)):
    tg[b] = shc; tg[b + 1] = s_; tg[b + 2] = s_
    tg[b + 3] = mid(s_, e, frx(b + 3, b + 2, b + 4)); tg[b + 4] = e
    tg[b + 5] = mid(e, w, frx(b + 5, b + 4, b + 6)); tg[b + 6] = w
    hs = np.linalg.norm(w - e) / np.linalg.norm(Jw[b + 6] - Jw[b + 4])
    for k in (b + 7, b + 8, b + 9, b + 10): tg[k] = w + (Jw[k] - Jw[b + 6]) * hs
for (h, k_, a), b in (((hipL, kneeL, ankL), 36), ((hipR, kneeR, ankR), 43)):
    tg[b] = h; tg[b + 1] = mid(h, k_, fr(b + 1, b, b + 2)); tg[b + 2] = k_; tg[b + 3] = a; tg[b + 4] = a
    tg[b + 5] = np.array([a[0], 0.0, a[2] + (Jw[b + 5][2] - Jw[b + 3][2]) * K])
for i in (32, 33, 34): tg[i] = hipc + (Jw[i] - Jw[3]) * K                  # skirt
def target(i):
    if i in tg: return tg[i]
    p = nodes[i]['parent']
    return Jw[i] if p < 0 else target(p) + (Jw[i] - Jw[p])
TG = np.array([target(i) for i in range(len(nodes))])
newT = []
for i, nd in enumerate(nodes):
    p = nd['parent']
    if p < 0: newT.append(np.array(nd['T'])); continue
    newT.append(np.linalg.solve(Wb[p][:3, :3], TG[i] - TG[p]))

# her bones -> Celia nodes (all used by Celia's own skin, so they get skin matrices)
B2N = {'L_Shoulder': 12, 'L_Elbow': 14, 'L_Wrist': 16, 'L_Item': 16,
       'R_Shoulder': 23, 'R_Elbow': 25, 'R_Wrist': 27, 'R_Item': 27,
       'L_Hip': 36, 'L_Knee': 38, 'L_Ankle': 39, 'R_Hip': 43, 'R_Knee': 45, 'R_Ankle': 46,
       'Chest': 5, 'Coat1': 6, 'Coat2': 6, 'Skirt1': 3, 'Hip': 3, 'Root': 3,
       'B_Hair1': 8, 'B_Tail1': 8, 'B_Hair2': 9, 'B_Tail2': 9}
for n in JN:
    if n not in B2N and (n == 'Head' or 'Hair' in n or 'Tail' in n): B2N[n] = 7

# ---------------------------------------------------------------- textures: body + head atlas
def opaque(img, keep_alpha=False):
    """transparent texels take the nearest opaque colour (repeated dilation); alpha 255 unless keep_alpha
    (then 0/255 cut-out: the hair texture's flower and earring cards)"""
    a = np.array(img.convert('RGBA')).astype(float)
    rgb, m = a[..., :3], a[..., 3] > 127
    for _ in range(64):
        if m.all(): break
        acc = np.zeros_like(rgb); cnt = np.zeros(m.shape)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            mm = np.roll(np.roll(m, dy, 0), dx, 1); cc = np.roll(np.roll(rgb, dy, 0), dx, 1)
            acc += cc * mm[..., None]; cnt += mm
        new = (~m) & (cnt > 0)
        rgb[new] = acc[new] / cnt[new][:, None]; m = m | new
    alpha = np.where(a[..., 3] > 127, 255.0, 0.0) if keep_alpha else np.full(m.shape, 255.0)
    return Image.fromarray(np.dstack([rgb, alpha]).round().astype(np.uint8), 'RGBA')
# texture budget: vanilla characters carry ~20 KB of b0 (Celia 128x256 + 128x64); at 64 KB hers
# corrupted the body texture in game (goddess test 1b), so everything is at half resolution (16 KB)
body = opaque(Image.open(SRC + 'body_315_00.png')).resize((128, 128), Image.LANCZOS)
AW, AH = 128, 96                                  # face + hair on top, eye below
head = Image.new('RGBA', (AW, AH), (0, 0, 0, 255))
CUTOUT = ('hair_315', 'lam_eye_000')
PLACE = {'face_315': (0, 0, 64, 64, 'face_315_00.png'), 'hair_315': (64, 0, 64, 64, 'hair_315_00.png'),
         'lam_eye_000': (0, 64, 16, 32, 'eye_315.00.png')}
for mat, (x, y, w, h, fn) in PLACE.items():
    im = opaque(Image.open(SRC + fn)).resize((w, h), Image.LANCZOS)
    if mat in CUTOUT:                                   # cut-out alpha from the scaled source alpha
        a = np.array(Image.open(SRC + fn).convert('RGBA').resize((w, h), Image.LANCZOS))[..., 3]
        im = np.array(im); im[..., 3] = np.where(a > 127, 255, 0); im = Image.fromarray(im, 'RGBA')
    head.paste(im, (x, y))

def uv_of(mat, u, v):
    """source UV (COLLADA, v up) -> game UV (v down) in its texture"""
    if mat == 'body_315': return u, 1.0 - v
    x, y, w, h, fn = PLACE[mat]
    u = min(max(u - np.floor(u) if u > 1.0 else u, 0.0), 1.0)      # the face mesh's u runs 1..2 (wraps)
    return (x + u * w) / AW, (y + (1.0 - v) * h) / AH

# ---------------------------------------------------------------- vertices / triangles
# positions are shared across UV seams (positions and UVs are indexed separately): one position per
# (place, node, source normal); the normal keeps double-sided cards apart
verts = []; uvs = []; tris = {0: [], 1: []}     # 0 = body texture, 1 = head atlas
vkey = {}
for e in src:
    ub = len(uvs); idx = []
    for p, b, ns in zip(e['P'], e['bone'], e['NS']):
        n = B2N[b]
        if n == 3 and p[1] > hipc[1] + 0.02: n = 4                 # waist
        if n == 5 and p[1] > mid(hipc, shc, 0.8)[1]: n = 6         # upper chest
        key = (tuple(np.round(p, 4)), n, tuple(np.round(ns / max(np.linalg.norm(ns), 1e-9), 1)))
        if key not in vkey: vkey[key] = len(verts); verts.append((p, n))
        idx.append(vkey[key])
    for u, v in e['UV']: uvs.append(uv_of(e['mat'], u, v))
    grp = 0 if e['mat'] == 'body_315' else 1
    for a, b, c in e['T']:
        if len({idx[a], idx[b], idx[c]}) < 3: continue              # degenerate after the merge
        tris[grp].append(((idx[a], idx[b], idx[c]), (ub + a, ub + b, ub + c)))
ukey = {}; uv2 = []; umap = []                    # identical UVs share one entry
for uv in uvs:
    k_ = (round(uv[0] * 16384), round(uv[1] * 16384))
    if k_ not in ukey: ukey[k_] = len(uv2); uv2.append(uv)
    umap.append(ukey[k_])
uvs = uv2
for g_ in tris: tris[g_] = [(pi, tuple(umap[x] for x in ti)) for pi, ti in tris[g_]]
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
    def third(t, a, b):                                  # third corner if (a, b) is an edge of t in order
        for i in range(3):
            if t[i] == a and t[(i + 1) % 3] == b: return t[(i + 2) % 3]
        return None
    for k0 in range(len(tris_)):
        if used[k0]: continue
        used[k0] = True; st = list(tris_[k0])
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
