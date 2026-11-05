#!/usr/bin/env python3
"""Stage 1 of the alien (notes/alien_design.md): the model as game files, on Celia's skeleton (49 nodes).
The bind pose is the T-pose on a skeleton whose bone lengths are the design's (B: long neck, legs, 3x forearms...);
the hunch, the T-rex arms, the head and the jaw are poses applied at run time (zt.c pose layer), so they are NOT in
the mesh. Rigid skin (one node per vertex, as the goddess); the jaw (below the mouth line) is a separate piece on
Celia's braid node 8 moved to the jaw hinge; a dark mouth cavity inside the head shows when it opens.
usage: build_alien.py NAME OUTDIR      -> NAME.arc, NAME.anm.arc (Celia's 10 animations, retargeted), loose parts,
                                          the textures, and readback renders (bind pose and posed) from the files."""
import sys, os, struct, numpy as np
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
NAME, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
SCR = '/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/'
os.environ['SET'] = 'none'; os.environ['FACE'] = 'none'
_argv = sys.argv; sys.argv = ['x', OUT]
exec(open(os.path.join(HERE, 'face.py')).read())          # the design: body_candidates + face (no renders)
sys.argv = _argv
sys.path[:0] = [SCR + 'pm']
from anm import qcomps
FRAC = 13
al = lambda b, a: b + bytes((-len(b)) % a)
SK = SCR + 'celia/'; W_ = SCR + 'wally/'

# ------------------------------------------------------------------ the design in the bind pose
E3 = EYES['E3 huge, far apart']
VR = sockets(gaunt(smooth_face(VA)), E3)                   # rest shape on Celia's own joints
BIND = dict(len=merge(B['len'], {16: 3.0, 27: 3.0}), scl=dict(B['scl']))
VBIND = pose(BIND, VR); Rb, tb = pose.last                 # T-pose on the lengthened skeleton (R = identity)
newT = []
for n, nd in enumerate(nodes):                              # local translations: Celia's, scaled like the bones
    newT.append(np.array(nd['T']) * BIND['len'].get(n, 1.0))
JW_TOP, HINGE_R = 0.909, np.array([0, 0.93, -0.04])        # jaw: below the painted mouth line; hinge under the ears
hc = np.array([0, 1.08, 0.0]); hs = np.array(B['scl'][7][1])
def head_bind(p):                                           # a rest-space head point -> bind space (node 7 rigid)
    q = (np.asarray(p) - hc) * hs + hc
    return q - P[7] + tb[7]
HINGE_B = head_bind(HINGE_R)
R7 = Wr[7][:3, :3]                                          # Celia's rest world rotation of the head node
newT[8] = R7.T @ (HINGE_B - tb[7]) / np.linalg.norm(R7[:, 0])   # node 8 (braid, child of 7) at the hinge

keep = ~np.isin(NODE, FORE_NODES)
PV = []; NODEV = []; KIND = []                              # positions, node, kind ('b' body, 'h' head, 'j' jaw, 'c' cavity)
idx_map = {}
for i in np.where(keep)[0]:
    idx_map[i] = len(PV); PV.append(VBIND[i]); NODEV.append(int(NODE[i]))
    KIND.append('h' if LAB[i] == 'head' else 'b')
TRI = []
JAWV = (LAB == 'head') & (VR[:, 1] < JW_TOP) & (VR[:, 2] > -0.01)
dup = {}; dupH = {}
for a, b, c in F:
    if not (keep[a] and keep[b] and keep[c]): continue
    if all(LAB[x] == 'head' for x in (a, b, c)) and sum(JAWV[x] for x in (a, b, c)) >= 2:   # a jaw face
        tri = []
        for x in (a, b, c):
            if JAWV[x]: v = idx_map[x]
            else:
                if x not in dup:
                    dup[x] = len(PV); PV.append(VBIND[x]); NODEV.append(8); KIND.append('j')
                v = dup[x]
            tri.append(v)
        TRI.append(tri)
    else:                                                   # head / body faces: a jaw vertex here gets a head copy
        tri = []
        for x in (a, b, c):
            if JAWV[x]:
                if x not in dupH:
                    dupH[x] = len(PV); PV.append(VBIND[x]); NODEV.append(7); KIND.append('h')
                tri.append(dupH[x])
            else: tri.append(idx_map[x])
        TRI.append(tri)
for i in np.where(JAWV & keep)[0]: NODEV[idx_map[i]] = 8; KIND[idx_map[i]] = 'j'

REST_Y = {}
for i, v in idx_map.items(): REST_Y[v] = VR[i, 1]
for x, v in list(dup.items()) + list(dupH.items()): REST_Y[v] = VR[x, 1]
def add_mesh(vt, ft, node, kind):
    o = len(PV)
    for v in vt: PV.append(v); NODEV.append(node); KIND.append(kind)
    for f in ft: TRI.append([o + int(f[0]), o + int(f[1]), o + int(f[2])])
# forelimbs in the bind pose (arm along +-x, palm down): forearm on the elbow node, palm and fingers on the wrist
for e, w, sx in ((15, 16, 1), (26, 27, -1)):
    ax_ = np.array([sx, 0.0, 0.0]); side = np.array([0, 0, 1.0])
    add_mesh(*tube(tb[e], tb[w], 0.017, 0.012, 6), e, 'b')
    pe = tb[w] + ax_ * 0.1
    add_mesh(*tube(tb[w], pe, 0.016, 0.026, 6), w, 'b')
    for f in (-1.5, -0.5, 0.5, 1.5):
        k0 = pe + side * 0.012 * f; k1 = k0 + ax_ * 0.077 + side * 0.006 * f
        add_mesh(*tube(k0, k1, 0.007, 0.0065, 4), w, 'b'); add_mesh(*tube(k1, k1 + ax_ * 0.063 + side * 0.004 * f, 0.0065, 0.003, 4), w, 'b')
# the mouth's inside: dark linings - shrunk copies of the lower head (node 7) and of the jaw (node 8) with the
# winding reversed, so only their inner sides show, and only through the open mouth (they never poke out)
LC = head_bind(np.array([0, 0.96, -0.02]))
def lining(faces, node):
    cp = {}
    for t in faces:
        ids = []
        for v in t:
            if v not in cp: cp[v] = len(PV); PV.append(LC + (PV[v] - LC) * 0.92); NODEV.append(node); KIND.append('c')
            ids.append(cp[v])
        TRI.append([ids[0], ids[2], ids[1]])
jaw_f = [t for t in TRI if all(NODEV[v] == 8 for v in t)]
low_f = [t for t in TRI if all(NODEV[v] == 7 and KIND[v] == 'h' for v in t) and min(REST_Y[v] for v in t) < 0.96]
lining(jaw_f, 8); lining(low_f, 7)
PV = np.array(PV); NODEV = np.array(NODEV); KIND = np.array(KIND); TRI = np.array(TRI)

# ------------------------------------------------------------------ UVs and baked textures
HEAD_MASK = np.isin(KIND, ['h', 'j'])
hy = PV[HEAD_MASK, 1]; HY0, HY1 = hy.min() - 0.005, hy.max() + 0.005
def uv_head(p): return np.stack([0.5 + np.arctan2(p[:, 0], p[:, 2]) / (2 * np.pi), (HY1 - p[:, 1]) / (HY1 - HY0)], 1)
def uv_body(p): return np.stack([0.5 + np.arctan2(p[:, 0], p[:, 2] + 1e-9) / (2 * np.pi), np.clip((1.30 - p[:, 1]) / 1.30, 0, 1)], 1)
# rest-space positions for painting (each output vertex -> its rest point, so the paint follows the design)
REST = np.zeros_like(PV)
inv = {v: k for k, v in idx_map.items()}
for v in range(len(PV)):
    if v in inv: REST[v] = VR[inv[v]]
for x, v in list(dup.items()) + list(dupH.items()): REST[v] = VR[x]
eyes_img = np.asarray(paint_eyes(E3, False)).astype(float)         # planar face paint (face coords)
ribs_img = np.asarray(paint_ribs()).astype(float)
def face_col(r):                                                    # colour at a rest-space head point
    u = (r[0] - X0) / (X1 - X0); v = (Y1 - r[1]) / (Y1 - Y0)
    if r[2] > 0 and 0 <= u < 1 and 0 <= v < 1: return eyes_img[int(v * TH), int(u * TW)]
    return SKIN_RGB
def body_col(r):
    u = (r[0] - BX0) / (BX1 - BX0); v = (BY1 - r[1]) / (BY1 - BY0)
    if r[2] > -0.01 and 0 <= u < 1 and 0 <= v < 1: return ribs_img[int(v * ribs_img.shape[0]), int(u * ribs_img.shape[1])]
    return SKIN_RGB
DARK = np.array([30, 10, 12.0])

UVL = []; TUV = []; GROUP = []; UVIX = {}; UV_GROUP = []
for t in TRI:
    k = KIND[t]; kind = 'c' if 'c' in k else ('h' if all(np.isin(k, ['h', 'j'])) else 'b')
    uv = uv_head(PV[t]) if kind == 'h' else uv_body(PV[t])
    if kind == 'c': uv = np.array([[0.97, 0.97]] * 3)              # the dark patch of the body texture
    if uv[:, 0].max() - uv[:, 0].min() > 0.5: uv[uv[:, 0] < 0.5, 0] = 0.999   # across the back seam (plain skin): no wrap in the atlas
    ids = []
    for x in uv:
        key = (round(float(x[0]), 5), round(float(x[1]), 5))   # shared texture coordinates
        key = key + (1 if kind == 'h' else 0,)
        if key not in UVIX: UVIX[key] = len(UVL); UVL.append(key[:2]); UV_GROUP.append(key[2])
        ids.append(UVIX[key])
    TUV.append(tuple(ids)); GROUP.append(1 if kind == 'h' else 0)

def bake(size, group, colfn, extra=None):
    """paint each triangle of the group into its UV area from its rest-space points"""
    W, H = size; img = np.tile(SKIN_RGB, (H, W, 1)); filled = np.zeros((H, W), bool)
    for t, tu, g in zip(TRI, TUV, GROUP):
        if g != group or 'c' in KIND[t]: continue
        uv = np.array([UVL[i] for i in tu]) * [W, H]
        if np.ptp(uv[:, 0]) > W / 2: continue                       # wrapped seam triangles: plain skin there anyway
        x0, x1 = int(uv[:, 0].min()), int(np.ceil(uv[:, 0].max())); y0, y1 = int(uv[:, 1].min()), int(np.ceil(uv[:, 1].max()))
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        (ax, ay), (bx, by), (cx, cy) = uv
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-9: continue
        l0 = ((by - cy) * (gx - cx) + (cx - bx) * (gy - cy)) / den; l1 = ((cy - ay) * (gx - cx) + (ax - cx) * (gy - cy)) / den; l2 = 1 - l0 - l1
        m = (l0 >= -0.02) & (l1 >= -0.02) & (l2 >= -0.02)
        r = REST[t]
        for yy, xx, a_, b_, c_ in zip(gy[m].astype(int), gx[m].astype(int), l0[m], l1[m], l2[m]):
            if 0 <= yy < H and 0 <= xx < W:
                img[yy, xx] = colfn(a_ * r[0] + b_ * r[1] + c_ * r[2]); filled[yy, xx] = True
    if extra is not None: extra(img)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
def dark_patch(img):
    H, W = img.shape[:2]; img[int(H * 0.94):, int(W * 0.94):] = DARK
head_tex = bake((128, 128), 1, face_col)
body_tex = bake((64, 128), 0, body_col, dark_patch)
# alien3 (user: no eyes in game - the animal slot seems to draw everything with b0 image 0): one atlas, body at
# u 0..0.25, head at u 0.5..1.0, stored as both b0 images; the UVs are remapped into it
atlas = Image.new('RGB', (256, 128), tuple(int(c) for c in SKIN_RGB))
atlas.paste(body_tex, (0, 0)); atlas.paste(head_tex, (128, 0))
UVL = [((u * 0.25 if g == 0 else 0.5 + u * 0.5), v) for (u, v), g in zip(UVL, UV_GROUP)]

# ------------------------------------------------------------------ the game files (as tools/goddess build_blank.py)
P = PV; B = NODEV
N = np.zeros_like(P)
for a, b, c in TRI:
    n = np.cross(P[b] - P[a], P[c] - P[a]); N[a] += n; N[b] += n; N[c] += n
N /= np.maximum(np.linalg.norm(N, axis=1)[:, None], 1e-9)
order = []; groups = []; slot = 0
for b in sorted(set(B)):
    idx = [i for i in range(len(P)) if B[i] == b]
    for c in range(0, len(idx), 128):
        ch = idx[c:c + 128]
        if groups:
            pb, ps, pc = groups[-1]; need = ((ps + pc) * 12 + 0x1F) & ~0x1F
            while (slot * 12) & ~0x1F < need: slot += 1
        n_ = max(len(ch), 2)
        groups.append((int(b), slot, n_))
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
tris = {0: [], 1: []}
for t, tu, g in zip(TRI, TUV, GROUP): tris[g].append((tuple(pos_of[int(i)] for i in t)[::-1], tuple(tu)[::-1]))   # the readback (game culling) wants this winding
uvs = UVL
q = lambda x: int(np.clip(np.round(x * (1 << FRAC)), -32768, 32767))
vbuf = b''.join(struct.pack('>6h', *[q(c) for c in P2[i]], *[q(c) for c in N2[i]]) for i in range(len(P2)))
src = open('/home/user/hmawl-goddess/tools/goddess/scripts/build_blank.py').read()
def grab(name):                                             # reuse build_blank.py's writers verbatim
    s = src.index('\ndef ' + name + '(') + 1; lines = src[s:].split('\n'); out = [lines[0]]
    for l in lines[1:]:
        if l and not l[0].isspace(): break                  # the next top-level statement ends the function
        out.append(l)
    return '\n'.join(out)
for fn in ('strips', 'dl', 'check_strips', 'build_gpl', 'build_skn', 'build_act', 'retarget_anim', 'c565', 'un565',
           'cmpr', 'tpl', 'u8'):
    exec(grab(fn))
ANIMS = 10
K = 1.0

if __name__ == '__main__':
    sys.path.insert(0, '/home/user/hmawl/tools/logs')
    import u8arc
    pm = u8arc.read(open(SCR + 'pkg36/postman_npc/pm_0.arc', 'rb').read()); pn = u8arc.names(pm)
    def blank_frames(t):
        n_ = struct.unpack_from('>I', t, 4)[0]
        return tpl([Image.new('RGBA', (1, 1), (0, 0, 0, 0))] * n_)
    f0e = blank_frames(pm['files'][pn['pm_0_f0_e.tpl']]); f0m = blank_frames(pm['files'][pn['pm_0_f0_m.tpl']])
    check_strips(tris[0]); check_strips(tris[1])
    gpl, skn, actb = build_gpl(), build_skn(), build_act()
    b0 = tpl([atlas, atlas])
    files = [(NAME + '.act', actb), (NAME + '.gpl', gpl), (NAME + '.skn', skn), (NAME + '_b0.tpl', b0),
             (NAME + '_f0_e.tpl', f0e), (NAME + '_f0_m.tpl', f0m)]
    if NAME == 'owl':                                       # the owl's archive also has owl_f0.tpl (one face texture)
        files.append(('owl_f0.tpl', tpl([Image.new('RGBA', (1, 1), (0, 0, 0, 0))])))
    arc = u8(files + [('_tmp.txt', b'')])
    clips = [retarget_anim(open(SK + 'anm%02d.bin' % a, 'rb').read()) for a in range(ANIMS)]
    if NAME == 'owl':                                       # the owl's code may ask for more clips; the pose layer sets
        small = min(clips, key=len)                         # every rotation anyway: idle first, the rest the smallest clip
        anm = u8([('@', clips[0] if a == 0 else small) for a in range(24)])
    else: anm = u8([('@', c) for c in clips])
    open(os.path.join(OUT, NAME + '.arc'), 'wb').write(arc)
    open(os.path.join(OUT, NAME + '.anm.arc'), 'wb').write(anm)
    for nm_, d_ in ((NAME + '.act', actb), (NAME + '.gpl', gpl), (NAME + '.skn', skn), (NAME + '_b0.tpl', b0),
                    (NAME + '_f0_e.tpl', f0e), (NAME + '_f0_m.tpl', f0m)):
        open(os.path.join(OUT, nm_), 'wb').write(d_)
    body_tex.save(os.path.join(OUT, 'b0_body.png')); head_tex.save(os.path.join(OUT, 'b0_head.png')); atlas.save(os.path.join(OUT, 'b0_atlas.png'))
    print('vertices', len(P), 'buffer', len(P2), 'uvs', len(uvs), 'tris body/head', len(tris[0]), len(tris[1]),
          'skin groups', len(groups), 'nodes', sorted(set(int(b) for b in B)))
    print(NAME + '.arc', len(arc), NAME + '.anm.arc', len(anm))
    print('parts', {k: len(v) for k, v in (('act', actb), ('gpl', gpl), ('skn', skn), ('b0', b0), ('f0e', f0e), ('f0m', f0m))})
