"""Build the finished Harvest Goddess (goddess_FINAL_model2.pkl: Muffy-shaped head + face, our hair,
outfit, veil, sash/bow, Celia's hands, sandals) as game files on Celia's skeleton, scaled 1.1x:
<name>.arc (act, gpl, skn, b0 = body atlas + head atlas, f0_e = Muffy's eye frames in lavender,
f0_m = Muffy's mouth frames skin-matched) and <name>.anm.arc (Celia's 10 animations, scaled).

Pipeline: hidden triangles culled (body under the clothes, scalp under the hair), UV-aware decimation
of the dense pieces, every vertex rigidly on one Celia node (body by body part, skirt on Celia's skirt
nodes, ponytail on her braid nodes, veil on the chest, hair/face on the head), textures packed into two
atlases. GPL materials as Muffy's: eye (sel 00, material 0), body (sel FF), mouth (sel 01), head (sel 02).
usage: build_final.py NAME OUTDIR"""
import sys, os, ast, struct, pickle, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.environ.get('GD_PM', os.path.join(HERE, '..', 'game', 'pm'))]
from awlchar import act, world
from anm import qcomps
from PIL import Image
import blank as BL, gzip
def pload(path):
    return pickle.load(gzip.open(path + '.gz', 'rb') if not os.path.exists(path) and os.path.exists(path + '.gz') else open(path, 'rb'))
from cull import visible
from decim import decimate
from anmsoft import soften
import jiggle as JG
import skirtfollow as SF
JIGGLE = os.environ.get('GD_JIGGLE', '0') == '1'
NAME, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
SCALE = float(os.environ.get('GD_SCALE', '1.1'))
FRAC = 13
al = lambda b, a: b + bytes((-len(b)) % a)
DATA = os.environ.get('GD_DATA', os.path.join(HERE, '..', 'data'))
GAME = os.environ.get('GD_GAME', os.path.join(HERE, '..', 'game'))   # files extracted from the disc (not in git)
SK = os.path.join(GAME, 'celia') + '/'
W_ = os.path.join(GAME, 'wally') + '/'
nodes = act(open(SK + 'sepi_0.act', 'rb').read())
newT = [np.array(nd['T']) * SCALE for nd in nodes]; K = SCALE
Jw = np.array([w[:3, 3] for w in world(nodes)])
N_BUST, N_RING = len(nodes), len(nodes) + 1

# helper functions shared with the earlier builders (strips, display lists, skin, act, anims, TPL, U8)
src = open(os.path.join(HERE, 'build_blank.py')).read()
want = {'strips', 'dl', 'check_strips', 'build_skn', 'build_act', 'retarget_anim', 'c565', 'un565', 'cmpr', 'tpl', 'u8'}
for node in ast.parse(src).body:
    if isinstance(node, ast.FunctionDef) and node.name in want:
        exec(compile(ast.Module([node], []), 'build_blank.py', 'exec'), globals())

# ---------------------------------------------------------------- model
g = pload(os.path.join(DATA, 'goddess_FINAL_model2.pkl'))
HP, OT = list(g['headpieces']), list(g['other'])
NAMES = (['body', 'face', 'eye', 'mouth', 'earpatch', 'fill'][:len(HP)] +
         ['feet', 'sole', 'sole', 'gown', 'skirt', 'belt', 'veil', 'sashtail', 'sashtail', 'sashflower', 'sashflower',
          'sashflower', 'scalp', 'hair', 'loose', 'loose', 'loose', 'loose', 'bun', 'bun', 'pony',
          'bowlobe', 'bowlobe', 'bowtail', 'bowtail', 'bowflower', 'bowflower', 'bowflower', 'tuft', 'tuft',
          'band', 'band', 'hand', 'hand'])
PIECES = HP + OT
assert len(NAMES) == len(PIECES), (len(NAMES), len(PIECES))
# Celia's hands carry their own nodes (per corner, same order as their P)
hand_nodes = [h['node'] for h in pload(os.path.join(DATA, 'celia_hands.pkl'))['H']]

# 1. cull triangles nobody can see (T-pose, views from above down to 35 degrees below)
geo = [(np.asarray(p[0]), np.asarray(p[2])) for p in PIECES]
bc = geo[0][0][geo[0][1]].mean(1)
ib = NAMES.index('body'); isc = NAMES.index('scalp'); ift = NAMES.index('feet')
cand = {ib: ((bc[:, 1] < 0.60) & (bc[:, 1] > 0.10)) | (bc[:, 1] > 0.88),
        isc: np.ones(len(geo[isc][1]), bool), ift: np.ones(len(geo[ift][1]), bool)}
vis = visible(geo, cand)

# 2. decimation ratios (UV-aware); pieces not listed keep every triangle
RATIO = {'body': 0.48, 'scalp': 0.25, 'veil': 0.30, 'bun': 0.22, 'pony': 0.55, 'gown': 0.60, 'hand': 0.65,
         'bowlobe': 0.40, 'bowflower': 0.5, 'sashflower': 0.5, 'sashtail': 0.45, 'bowtail': 0.5, 'hair': 0.8}
def clean_face(t):
    t = t.copy(); H_, W_ = t.shape[:2]
    green = (t[..., 1] > t[..., 0] + 12)
    green[:22, :92] = False                                     # keep the hairline band
    skinpx = ~green
    for y, x in zip(*np.where(green)):
        for r in range(1, 6):
            ys, xs = slice(max(0, y - r), y + r + 1), slice(max(0, x - r), x + r + 1)
            m = skinpx[ys, xs]
            if m.any(): t[y, x, :3] = t[ys, xs, :3][m].mean(0); break
    return t
pieces = []
for k, (nm, p) in enumerate(zip(NAMES, PIECES)):
    P, Q, F, tex = np.asarray(p[0], float), np.asarray(p[1], float), np.asarray(p[2]), np.asarray(p[3], float)
    if k in vis: F = F[vis[k]]
    if nm in ('face', 'earpatch'): tex = clean_face(tex)
    nodes_k = None
    if nm == 'hand':
        nodes_k = hand_nodes[NAMES[:k].count('hand')]
    elif nm in RATIO and nm not in ('eye', 'mouth', 'face'):
        P, Q, F = decimate(P, Q, F, RATIO[nm], preserve_border=nm not in ('scalp', 'gown'))
        Q = np.nan_to_num(Q, nan=0.5)
    if nm == 'hand' and 'hand' in RATIO:
        pass                                   # hands: keep their per-vertex nodes (not decimated)
    pieces.append(dict(name=nm, P=P, Q=Q, F=np.asarray(F), tex=tex, hnode=nodes_k))

# 3. nodes
V0 = np.load(os.path.join(DATA, 'blank_v3.npz'))['V']
S_ = BL.S
def prim(P):
    m = lambda c, s: np.array(c) * [s, 1, 1]
    out = {}
    out['head'] = np.minimum.reduce([BL.ell(P, *S_['cran']), BL.ell(P, *S_['jaw']), BL.ell(P, *S_['chin']),
                                     BL.ell(P, m(S_['ear'][0], 1), S_['ear'][1]), BL.ell(P, m(S_['ear'][0], -1), S_['ear'][1])])
    out['neck'] = BL.cap(P, *S_['neck'])
    out['torso'] = np.minimum.reduce([BL.ell(P, *S_['chest']), BL.ell(P, *S_['waist']), BL.ell(P, *S_['hips'])] +
                                     [np.linalg.norm(P - m(S_['bust'][0], s), axis=-1) - S_['bust'][1] for s in (1, -1)])
    for s, sd in ((1, 'L'), (-1, 'R')):
        out['arm' + sd] = np.minimum.reduce([BL.cap(P, m(S_[k][0], s), m(S_[k][1], s), *S_[k][2:]) for k in ('shoulder', 'upper', 'fore')])
        out['hand' + sd] = np.minimum(BL.rbox(P, m(S_['palm'][0], s), S_['palm'][1], S_['palm'][2]), BL.rbox(P, m(S_['mitt'][0], s), S_['mitt'][1], S_['mitt'][2]))
        out['thumb' + sd] = BL.cap(P, m(S_['thumb'][0], s), m(S_['thumb'][1], s), *S_['thumb'][2:])
        out['leg' + sd] = np.minimum.reduce([BL.cap(P, m(S_['thigh'][0], s), m(S_['thigh'][1], s), *S_['thigh'][2:]),
                                            BL.cap(P, m(S_['shin'][0], s), m(S_['shin'][1], s), *S_['shin'][2:]), BL.ell(P, m(S_['calf'][0], s), S_['calf'][1])])
        out['foot' + sd] = BL.rbox(P, m(S_['foot'][0], s), S_['foot'][1], S_['foot'][2])
    return out
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
pr = prim(V0); pn = list(pr); lab = np.array(pn)[np.argmin(np.stack([pr[n] for n in pn]), 0)]
NODE0 = np.array([node_of(p, l) for p, l in zip(V0, lab)])
from scipy.spatial import cKDTree
kd0 = cKDTree(V0)
def body_node(P):
    n = NODE0[kd0.query(P)[1]]
    n[P[:, 1] > 0.86] = 7
    return n
# Celia's skirt vertices -> nodes 3 / 32 / 33 / 34
import awlmodel
CM = awlmodel.load(SK + 'sepi_0'); CV = CM['V']; cvb = CM['bones']
sk = [i for i in range(len(CV)) if cvb[i] and cvb[i][0] in (3, 32, 33, 34) and 0.12 < CV[i, 1] < 0.58]
kds = cKDTree(CV[sk]); skn_ = np.array([cvb[i][0] for i in sk])
def skirt_node(P):
    """front half -> 34, back half -> 32, sides -> 33 (their mean), top band -> hips"""
    n = np.where(P[:, 2] > 0.045, 34, np.where(P[:, 2] < -0.015, 32, 33))      # front / back / sides
    n[P[:, 1] > 0.57] = 3
    return n
HEAD = {'face', 'eye', 'mouth', 'earpatch', 'fill', 'scalp', 'hair', 'loose', 'bun', 'tuft'}
for pc in pieces:
    nm, P = pc['name'], pc['P']
    if nm in HEAD: n = np.full(len(P), 7)
    elif nm == 'body': n = body_node(P)
    elif nm == 'hand': n = np.array(pc['hnode'])
    elif nm in ('pony', 'bowlobe', 'bowtail', 'bowflower'): n = np.where(P[:, 1] > 0.84, 8, 9) if nm == 'pony' else np.full(len(P), 8)
    elif nm == 'veil': n = np.full(len(P), 6)
    elif nm in ('gown', 'skirt', 'sashtail'): n = skirt_node(P)
    elif nm in ('belt', 'sashflower'): n = np.full(len(P), 3)
    elif nm == 'band':
        allv = np.vstack([V0] + [p['P'] for p in pieces if p['name'] == 'hand'])
        alln = np.concatenate([NODE0] + [np.array(p['hnode']) for p in pieces if p['name'] == 'hand'])
        n = alln[cKDTree(allv).query(P)[1]]
    elif nm in ('feet', 'sole'): n = NODE0[kd0.query(P)[1]]
    else: raise SystemExit('no node rule for ' + nm)
    pc['node'] = np.asarray(n, int)

if JIGGLE:
    for pc in pieces:
        if pc['name'] == 'body':
            ov = JG.bust_nodes(pc['P'], N_BUST, N_RING)
            pc['node'] = np.where(ov >= 0, ov, pc['node'])
            print('jiggle: bust vertices', int((ov == N_BUST).sum()), 'ring', int((ov == N_RING).sum()))

# 4. textures -> atlases (each piece's used UV box baked, wrapping sampled, then shelf-packed)
def sample(tex, u, v):
    h, w = tex.shape[:2]
    return tex[(np.floor(v * h).astype(int)) % h, (np.floor(u * w).astype(int)) % w]
groups = {}
for pc in pieces:
    if pc['name'] in ('eye', 'mouth'): continue
    key = id(pc['tex'])
    for k2, gg in groups.items():
        if gg['tex'].shape != pc['tex'].shape: continue
        hh, ww = gg['tex'].shape[:2]; qq = pc['Q'][pc['F'].ravel()] if len(pc['F']) else pc['Q']
        px = lambda t: t[(np.floor(qq[:, 1] * hh).astype(int)) % hh, (np.floor(qq[:, 0] * ww).astype(int)) % ww]
        if np.array_equal(gg['tex'], pc['tex']) or np.abs(px(gg['tex']) - px(pc['tex'])).max() < 1.5: key = k2; break
    gg = groups.setdefault(key, dict(tex=pc['tex'], pcs=[]))
    gg['pcs'].append(pc); pc['gkey'] = key
BODY_ATL = {'body', 'fill', 'feet', 'sole', 'gown', 'skirt', 'belt', 'veil', 'sashtail', 'sashflower', 'bowlobe',
            'bowtail', 'bowflower', 'band', 'hand'}
RES = float(os.environ.get('GD_TEXRES', '1.0'))
for key, gg in groups.items():
    Qs = np.vstack([pc['Q'][pc['F'].ravel()] for pc in gg['pcs']])
    u0, v0 = Qs.min(0); u1, v1 = Qs.max(0)
    if u0 > -0.06 and u1 < 1.06 and v0 > -0.06 and v1 < 1.06 and (u1 - u0) > 0.8 and (v1 - v0) > 0.8:
        u0, v0, u1, v1 = 0.0, 0.0, 1.0, 1.0           # (nearly) the whole sheet: take it as is, clamp
    h, w = gg['tex'].shape[:2]
    if u1 - u0 < 1e-3: u0 -= 2.0 / w; u1 += 2.0 / w
    if v1 - v0 < 1e-3: v0 -= 2.0 / h; v1 += 2.0 / h
    atl = 'body' if gg['pcs'][0]['name'] in BODY_ATL else 'head'
    LOWRES = {'bun': 0.5, 'scalp': 0.5, 'pony': 0.75, 'veil': 0.75}
    res = RES * min(LOWRES.get(pc_['name'], 1.0) for pc_ in gg['pcs'])
    pw = max(4, int(np.ceil((u1 - u0) * w * res))); ph = max(4, int(np.ceil((v1 - v0) * h * res)))
    uu = u0 + (np.arange(pw) + 0.5) / pw * (u1 - u0); vv = v0 + (np.arange(ph) + 0.5) / ph * (v1 - v0)
    if (u0, v0, u1, v1) == (0.0, 0.0, 1.0, 1.0) and (pw, ph) == (w, h): img = gg['tex'].copy()
    else: img = sample(gg['tex'], uu[None, :].repeat(ph, 0), vv[:, None].repeat(pw, 1))
    gg.update(box=(u0, v0, u1, v1), img=img, atl=atl, size=(pw, ph))
    for pc in gg['pcs']: assert pc['name'] in BODY_ATL or atl == 'head', pc['name']
def pack(items, W):
    """skyline: each rect (largest first) at the lowest position where it fits, then leftmost"""
    sky = np.zeros(W, int)
    for g_ in sorted(items, key=lambda g_: -g_['size'][0] * g_['size'][1]):
        pw, ph = g_['size']; best = None
        for x in range(0, W - pw + 1, 4):
            y = sky[x:x + pw].max()
            if best is None or y < best[1]: best = (x, y)
        x, y = best; g_['at'] = (x, y); sky[x:x + pw] = y + ph
    return -(-sky.max() // 8) * 8
ATL = {}
for atl, W in (('body', 256), ('head', 256)):
    its = [gg for gg in groups.values() if gg['atl'] == atl]
    H = pack(its, W); A = np.zeros((H, W, 4)); A[..., 3] = 255
    for gg in its:
        x, y = gg['at']; pw, ph = gg['size']; A[y:y + ph, x:x + pw] = gg['img']
    ATL[atl] = (A, W, H)
for gg in groups.values():
    u0, v0, u1, v1 = gg['box']; x, y = gg['at']; pw, ph = gg['size']; _, W, H = ATL[gg['atl']]
    for pc in gg['pcs']:
        q = pc['Q']; uu = np.clip((q[:, 0] - u0) / (u1 - u0), 0, 1); vv = np.clip((q[:, 1] - v0) / (v1 - v0), 0, 1)
        pc['UVa'] = np.stack([(x + 0.5 + uu * (pw - 1)) / W, (y + 0.5 + vv * (ph - 1)) / H], 1)
        pc['mat'] = 1 if gg['atl'] == 'body' else 3
for pc in pieces:
    if pc['name'] == 'eye': pc['UVa'] = np.clip(pc['Q'], 0, 1); pc['mat'] = 0
    if pc['name'] == 'mouth': pc['UVa'] = np.clip(pc['Q'], 0, 1); pc['mat'] = 2
def to_img(A):
    a = A.copy(); a[..., 3] = np.where(a[..., 3] > 127, 255, 0)
    return Image.fromarray(a.clip(0, 255).round().astype(np.uint8), 'RGBA')
body_img, head_img = to_img(ATL['body'][0]), to_img(ATL['head'][0])

# 5. vertices (scaled), welded per (position, node, rough normal); smooth normals
verts = []; vkey = {}; uvs = []; ukey = {}; tris = {0: [], 1: [], 2: [], 3: []}
def piece_normals(P, F):
    key = {}; wid = np.array([key.setdefault(tuple(np.round(p, 4)), len(key)) for p in P])
    acc = np.zeros((len(key), 3))
    n = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])
    for k in range(3): np.add.at(acc, wid[F[:, k]], n)
    nn = acc[wid]; return nn / np.maximum(np.linalg.norm(nn, axis=1)[:, None], 1e-12)
# skin pieces share one smooth normal per position (no shading seams where face, eye, mouth, ears and
# the head/body meet, as on the vanilla models); other pieces are smoothed on their own
SKIN = ('body', 'face', 'eye', 'mouth', 'earpatch', 'fill', 'hand', 'feet')
skin_acc = {}
for pc in pieces:
    if pc['name'] not in SKIN or len(pc['F']) == 0: continue
    P, F = pc['P'], pc['F']; n = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])
    for t, nn in zip(F, n):
        for v in t: k = tuple(np.round(P[v], 4)); skin_acc[k] = skin_acc.get(k, 0) + nn
vnorm = []
for pc in pieces:
    P, F = pc['P'], pc['F']
    if len(F) == 0: continue
    if pc['name'] in SKIN:
        Nn = np.array([skin_acc.get(tuple(np.round(p, 4)), np.array([0, 1.0, 0])) for p in P], float)
        Nn /= np.maximum(np.linalg.norm(Nn, axis=1)[:, None], 1e-12)
    else:
        Nn = piece_normals(P, F)
    idx = []; uidx = []
    for i in range(len(P)):
        key = (tuple(np.round(P[i] * SCALE, 4)), int(pc['node'][i]), tuple(np.round(Nn[i], 1)))
        if key not in vkey: vkey[key] = len(verts); verts.append((P[i] * SCALE, int(pc['node'][i]))); vnorm.append(Nn[i].copy())
        idx.append(vkey[key])
        uk = (round(pc['UVa'][i][0] * 16384), round(pc['UVa'][i][1] * 16384))
        if uk not in ukey: ukey[uk] = len(uvs); uvs.append(tuple(pc['UVa'][i]))
        uidx.append(ukey[uk])
    for a, b_, c in F:
        if len({idx[a], idx[b_], idx[c]}) < 3: continue
        tris[pc['mat']].append(((idx[a], idx[b_], idx[c]), (uidx[a], uidx[b_], uidx[c])))
P = np.array([v[0] for v in verts]); B = np.array([v[1] for v in verts])
N = np.array(vnorm); N /= np.maximum(np.linalg.norm(N, axis=1)[:, None], 1e-9)
order = []; groups_s = []; slot = 0
for b in sorted(set(B)):
    idx = [i for i in range(len(P)) if B[i] == b]
    for c in range(0, len(idx), 128):
        ch = idx[c:c + 128]
        if groups_s:
            pb, ps, pcn = groups_s[-1]; need = ((ps + pcn) * 12 + 0x1F) & ~0x1F
            while (slot * 12) & ~0x1F < need: slot += 1
        n_ = max(len(ch), 2)
        groups_s.append((b, slot, n_))
        for k, i in enumerate(ch): order.append((slot + k, i))
        slot += n_
nbuf = slot
lb, ls_, lc = groups_s[-1]; a0 = (ls_ * 12) & ~0x1F
nbuf = max(nbuf, -(-(a0 + ((lc * 12 + ls_ * 12 % 32 + 0x1F) & ~0x1F)) // 12))
pos_of = {i: s_ for s_, i in order}
P2 = np.zeros((nbuf, 3)); N2 = np.zeros((nbuf, 3)); N2[:, 1] = 1.0
for s_, i in order: P2[s_] = P[i]; N2[s_] = N[i]
filled = set(s_ for s_, i in order)
for s_ in range(nbuf):
    if s_ not in filled: P2[s_] = P2[s_ - 1]; N2[s_] = N2[s_ - 1]
for gk in tris: tris[gk] = [(tuple(pos_of[i] for i in pi), ti) for pi, ti in tris[gk]]
q = lambda x: int(np.clip(np.round(x * (1 << FRAC)), -32768, 32767))
assert np.abs(P2).max() * (1 << FRAC) < 32767, 'positions overflow the fixed-point range'
vbuf = b''.join(struct.pack('>6h', *[q(c) for c in P2[i]], *[q(c) for c in N2[i]]) for i in range(len(P2)))
groups = groups_s          # build_skn reads 'groups'

def build_gpl():
    """materials as Muffy's mumu_0.gpl: eye (sel 00), body (sel FF), mouth (sel 01), head (sel 02)"""
    tgpl = open(W_ + 'sua_0.gpl', 'rb').read()[0x1C:]
    m = bytearray(0x24)
    m[0x1C:0x24] = struct.pack('>IHBB', 0x24, len(P2), 0x30 | FRAC, 6)
    m += vbuf; m = bytearray(al(bytes(m), 4))
    col_off = len(m); ch = bytearray(tgpl[0x3c44:0x3c50]); struct.pack_into('>I', ch, 0, col_off + 8); m += ch
    uv_off = len(m); m += bytes(0x10); uv_data = len(m)
    m += b''.join(struct.pack('>hh', int(np.clip(round(u * 16384), -32768, 32767)), int(np.clip(round(v * 16384), -32768, 32767))) for u, v in uvs)
    m = bytearray(al(bytes(m), 4))
    nrm_off = len(m); m += struct.pack('>IHBBI', 0x24 + 6, len(P2), 0x30 | FRAC, 6, 0x41C80000)
    mat_off = len(m); ncmd = 6
    m += bytes(0xC + 0x10 * ncmd)
    while (len(m) + 0x1C) % 0x20: m += b'\0'
    offs = {}
    for mat in (0, 1, 2, 3):
        offs[mat] = len(m); d_ = dl(tris[mat]); m += d_; offs[mat] = (offs[mat], len(d_))
    struct.pack_into('>III', m, mat_off, offs[0][0], mat_off + 0xC, ncmd << 16)
    cmds = [struct.pack('>IIII', 0x01000000, 0x11110000, 0, 0),                       # eye frame (f0_e)
            struct.pack('>IIII', 0x03000000, 1, 0, 0),
            struct.pack('>IIII', 0x02000000, 0xC3C, *offs[0]),
            struct.pack('>IIII', 0x01FF0000, 0x11110001, *offs[1]),                    # body atlas (b0 #0)
            struct.pack('>IIII', 0x01010000, 0x11110002, *offs[2]),                    # mouth frame (f0_m)
            struct.pack('>IIII', 0x01020000, 0x11110003, *offs[3])]                    # head atlas (b0 #1)
    for k, c in enumerate(cmds): m[mat_off + 0xC + 0x10 * k:mat_off + 0x1C + 0x10 * k] = c
    tail = len(m); m += (NAME + '.tpl').encode() + b'\0\0\0' + (NAME[0].upper() + NAME[1:] + '_L:Layer1').encode() + b'\0'
    struct.pack_into('>IHBBII', m, uv_off, uv_data, len(uvs), 0x3E, 2, tail, 0)
    struct.pack_into('>5I', m, 0, 0x1C, col_off, uv_off, nrm_off, mat_off)
    struct.pack_into('>II', m, 0x14, 0x01FF0000, 0)
    return struct.pack('>7I', 0x005BBC61, 0, 0, 1, 0x14, 0x1C, len(m)) + bytes(m)

def tpl_dedup(images):
    """as tpl(), identical images share one data block (as the vanilla frame files do)"""
    blobs = []; ref = []
    for im in images:
        bb = cmpr(im)
        k = next((i for i, (b2, s2) in enumerate(blobs) if b2 == bb and s2 == im.size), None)
        if k is None: blobs.append((bb, im.size)); k = len(blobs) - 1
        ref.append(k)
    n = len(images)
    out = bytearray(struct.pack('>III', 0x0020AF30, n, 0xC))
    for k in range(n): out += struct.pack('>II', 0xC + 8 * n + 0x24 * k, 0)
    pos = (0xC + 8 * n + 0x24 * n + 0x1F) & ~0x1F; dpos = []
    for bb, _ in blobs: dpos.append(pos); pos = (pos + len(bb) + 0x1F) & ~0x1F
    for im, k in zip(images, ref):
        out += struct.pack('>HHIIIIIIBBBB', im.height, im.width, 14, dpos[k], 1, 1, 1, 1, 0, 0, 0, 0)[:0x24].ljust(0x24, b'\0')
    out = bytearray(al(bytes(out), 0x20))
    for bb, _ in blobs: out += al(bb, 0x20)
    return bytes(out)
def frames_tpl(frames):
    ims = []
    for a in frames:
        if a.shape[0] == 1: ims.append(Image.new('RGBA', (1, 1), (0, 0, 0, 0)))
        else: ims.append(Image.fromarray(a.clip(0, 255).round().astype(np.uint8), 'RGBA'))
    return tpl_dedup(ims)

if __name__ == '__main__':
    fr = pload(os.path.join(DATA, 'face_frames_lavender.pkl'))
    f0e, f0m = frames_tpl(fr['eye']), frames_tpl(fr['mouth'])
    for gk in tris: check_strips(tris[gk])
    gpl, skn, actb = build_gpl(), build_skn(), build_act()
    if JIGGLE:
        from awlchar import act as act_parse
        sn = act_parse(actb); Wb5 = world(sn)[JG.PARENT]
        c_local = (np.linalg.inv(Wb5) @ np.r_[JG.CENTER * SCALE, 1])[:3]
        actb = JG.act_add(actb, [(JG.PARENT, c_local, (0, 0, 0, 1.0)), (JG.PARENT, c_local, (0, 0, 0, 1.0))])
        nodes_j = act_parse(actb); assert len(nodes_j) == N_RING + 1
    b0 = tpl([body_img, head_img])
    arc = u8([(NAME + '.act', actb), (NAME + '.gpl', gpl), (NAME + '.skn', skn), (NAME + '_b0.tpl', b0),
              (NAME + '_f0_e.tpl', f0e), (NAME + '_f0_m.tpl', f0m), ('_tmp.txt', b'')])
    # long gown: shorter strides in walk (1) and run (5), legs and Celia's skirt nodes together
    STRIDE = {1: float(os.environ.get('GD_WALK', '1.0')), 5: float(os.environ.get('GD_RUN', '1.0'))}
    LEGSKIRT = (32, 33, 34, 36, 37, 38, 39, 40, 41, 43, 44, 45, 46, 47, 48)
    rest = [nd['Q'] for nd in nodes]
    from awlchar import act as act_parse
    nodes_sf = act_parse(actb)
    SKIRT_FOLLOW = {1: float(os.environ.get('GD_SKIRT_MARGIN', '12')), 5: float(os.environ.get('GD_SKIRT_MARGIN', '12'))}   # margin (deg) inside the hem
    anims = []
    for a in range(10):
        raw = retarget_anim(open(SK + 'anm%02d.bin' % a, 'rb').read())
        if a in STRIDE and STRIDE[a] != 1.0: raw, nk = soften(raw, rest, {n_: STRIDE[a] for n_ in LEGSKIRT}); print('anim', a, 'stride', STRIDE[a], 'keys', nk)
        if a in SKIRT_FOLLOW:
            L_, keys, dF, dB = SF.skirt_push(nodes_sf, raw, margin=SKIRT_FOLLOW[a])
            raw = SF.replace_tracks(raw, L_, keys)
            print('anim', a, 'skirt pushed by the feet: front up to %.0f deg, back up to %.0f deg' % (dF.max(), dB.min()))
        if JIGGLE:
            L_, off = JG.spring_offsets(nodes_j, raw, c_local, gain=float(os.environ.get('GD_JIGGLE_GAIN', '1.6')))
            amp = np.linalg.norm(off, axis=1).max()
            if amp < 0.0008:
                raw = JG.anm_add_tracks(raw, [(N_BUST, L_, None, c_local), (N_RING, L_, None, c_local)])
            else:
                kb = [(f, c_local + o) for f, o in enumerate(off)]; kr = [(f, c_local + 0.5 * o) for f, o in enumerate(off)]
                raw = JG.anm_add_tracks(raw, [(N_BUST, L_, kb), (N_RING, L_, kr)])
            print('anim', a, 'jiggle max offset mm', round(amp * 1000, 1))
        anims.append(('@', raw))
    anm = u8(anims)
    open(os.path.join(OUT, NAME + '.arc'), 'wb').write(arc)
    open(os.path.join(OUT, NAME + '.anm.arc'), 'wb').write(anm)
    body_img.save(os.path.join(OUT, 'b0_body.png')); head_img.save(os.path.join(OUT, 'b0_head.png'))
    for n_, d_ in (('act', actb), ('gpl', gpl), ('skn', skn), ('b0', b0), ('f0e', f0e), ('f0m', f0m)):
        open(os.path.join(OUT, NAME + '.' + n_ + '.bin'), 'wb').write(d_)
    print('triangles', {k: len(v) for k, v in tris.items()}, 'total', sum(len(v) for v in tris.values()))
    print('vertices', len(P), 'buffer', len(P2), 'uvs', len(uvs), 'skin groups', len(groups), 'nodes', sorted(set(B)))
    print('atlases body', body_img.size, 'head', head_img.size)
    print('pieces', {nm: sum(len(p['F']) for p in pieces if p['name'] == nm) for nm in dict.fromkeys(NAMES)})
    print(NAME + '.arc', len(arc), NAME + '.anm.arc', len(anm))
    print('parts', {k: len(v) for k, v in (('act', actb), ('gpl', gpl), ('skn', skn), ('b0', b0), ('f0e', f0e), ('f0m', f0m))})
