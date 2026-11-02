"""Joe's bench clips (sit down, sitting loop, stand up) as AWL .anm files for the 90% Joe.
usage: joe_sit.py OUTDIR   -> anm_sitdown.bin, anm_sitloop.bin, anm_standup.bin, cig.json

Poses were designed on the bench model (mapobj 136) in the preview scripts; Joe's geometry rides only on
nodes 13 (head), 18/39 (gloves), 8/48 (shoes) and 29 (cigarette, reused face node). Each keyed node gets its
world transform per key; every other node keeps its rest local. Root frames:
- sit down: the NPC stands ZS in front of the bench, facing it.
- sitting loop and stand up: same spot, facing away from the bench (the code turns Joe 180 degrees when the
  sit down ends; the poses match, so the turn isn't seen). Stand up ends on idle frame 0."""
import sys, os, json, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); SP = os.path.join(HERE, '..')
sys.path[:0] = [os.path.join(SP, 'pm'), HERE]
from awlchar import act, world, qmat
from anm import parse
import pose as P_
import joe_anm
from scipy.spatial.transform import Rotation as Rot, Slerp
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
VAN = os.path.join(SP, 'goddess', 'girls', 'ban_0') + '/'
JS = 0.9; FPS = 30; ZS = 0.75
nodes = act(open(VAN + 'ban_0.act', 'rb').read()); Wb = world(nodes); NN = len(nodes)
D = np.diag([JS] * 3 + [1])
CIG_NODE, CIG_PARENT = 29, 28
KEYED = [13, 18, 39, 8, 48, CIG_NODE]

def Rx(a): c, s = np.cos(a), np.sin(a); return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
def Ry(a): c, s = np.cos(a), np.sin(a); return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
def Rz(a): c, s = np.cos(a), np.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
def Ryh(a): M = np.eye(4); M[:3, :3] = Ry(a); return M
def Tr(p): M = np.eye(4); M[:3, 3] = p; return M
def ease(x): x = min(max(x, 0), 1); return x * x * (3 - 2 * x)
def seg(t, a, b): return ease((t - a) / (b - a))

# ---------------------------------------------------------------- sitting pose (preview units, bench frame)
RS = np.array([[-1, 0, 0], [0, 0, 1], [0, 1, 0]], float)                                   # hand sideways at the mouth
RK = Ry(0.25) @ Rx(0.5) @ np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]], float)             # hand draped over the knee
HY = 0.78
def place(n, t, R):
    out = np.eye(4); out[:3, :3] = R @ (Wb[n][:3, :3] * JS); out[:3, 3] = t; return out
def base_spec():
    return {13: ([0, HY, -0.06], Rx(-0.12)), 8: ([0.30, 0.148, 0.50], Ry(0.40)), 48: ([-0.30, 0.148, 0.48], Ry(-0.35)),
            18: ([0.50, 0.80, -0.30], Ry(0.35) @ np.array([[np.cos(-0.1), -np.sin(-0.1), 0], [np.sin(-0.1), np.cos(-0.1), 0], [0, 0, 1]]))}
P0 = np.array([-0.48, 0.44, 0.10]); P1 = np.array([-0.28, 0.70, 0.26])
SL = Slerp([0, 1], Rot.from_matrix([RK, RS]))
LOOP = 10.0
def spec_at(t):
    yaw = 0.45 * (seg(t, 0.4, 1.4) - seg(t, 2.0, 3.0)) - 0.45 * (seg(t, 5.8, 6.8) - seg(t, 7.4, 8.4))
    up = seg(t, 3.0, 3.8) - seg(t, 4.6, 5.5)
    pitch = -0.10 - 0.08 * (seg(t, 3.6, 4.1) - seg(t, 4.5, 5.0))
    bob = 0.008 * np.sin(2 * np.pi * t / (LOOP / 3))
    s = base_spec(); s[39] = (list(P0 + (P1 - P0) * up + [0, bob, 0]), SL([ease(up * 1.6)]).as_matrix()[0])
    s[13] = ([0, HY + bob, -0.06], Ry(yaw) @ Rx(pitch)); return s
def posedW(sp):
    W = [D @ w for w in Wb]
    for n, (t, R) in sp.items(): W[n] = place(n, np.array(t, float), R)
    return W

# ---------------------------------------------------------------- transitions (preview units, bench frame)
idle = parse(open(VAN + 'anm00.bin', 'rb').read())
WI = [D @ w for w in world(nodes, P_.locals_at(nodes, idle, 0))]
WS = posedW(spec_at(0))
def blend(A, B, w):
    r = Slerp([0, 1], Rot.from_matrix([A[:3, :3] / JS, B[:3, :3] / JS]))([w]).as_matrix()[0]
    M = np.eye(4); M[:3, :3] = r * JS; M[:3, 3] = A[:3, 3] * (1 - w) + B[:3, 3] * w; return M
def sitdown(t):          # t in design seconds (0..2.4)
    phi = np.pi * (1 - seg(t, 0.25, 1.3)); bz = ZS * (1 - seg(t, 0.95, 1.9)); W = {}
    for n in KEYED[:-1]:
        if n in (8, 48):
            a, b = (0.25, 0.75) if n == 8 else (0.65, 1.15)
            M = Tr([0, 0, bz]) @ Ryh(np.pi * (1 - seg(t, a, b))) @ blend(WI[n], WS[n], seg(t, 0.95, 1.9))
            M[1, 3] += 0.10 * np.sin(np.pi * min(max((t - a) / (b - a), 0), 1))
        elif n in (18, 39):
            w = seg(t, 1.0, 2.1) if n == 39 else seg(t, 1.2, 2.3); M = Tr([0, 0, bz]) @ Ryh(phi) @ blend(WI[n], WS[n], w)
        else:
            M = Tr([0, 0, bz]) @ Ryh(phi) @ blend(WI[n], WS[n], seg(t, 0.95, 1.9))
            M[:3, :3] = M[:3, :3] @ Rx(0.30 * np.sin(np.pi * min(max((t - 0.95) / 1.0, 0), 1)))
        W[n] = M
    return W
def standup(t):          # 0..1.6
    W = {}
    for n in KEYED[:-1]:
        w = seg(t, 0.0, 0.6) if n in (8, 48) else seg(t, 0.1, 1.1) if n in (18, 39) else seg(t, 0.35, 1.4)
        M = blend(WS[n], Tr([0, 0, ZS]) @ WI[n], w)
        if n == 13: M[:3, :3] = M[:3, :3] @ Rx(0.35 * np.sin(np.pi * min(max((t - 0.2) / 1.1, 0), 1)))
        W[n] = M
    return W
SPEED = 28 / 34          # matches the 1.2x walk

# ---------------------------------------------------------------- game skeleton (90%) and the cigarette
gn = [dict(v) for v in nodes]
for k in range(NN): gn[k]['T'] = tuple(np.array(gn[k]['T']) * JS)
gn[CIG_PARENT]['Q'] = (0, 0, 0, 1); gn[CIG_PARENT]['T'] = (0, 0, 0)
W23 = world(gn)[23]
park = W23[:3, :3].T @ (np.array([0, 1.16 * JS, -0.116 * JS]) - W23[:3, 3])     # head ball centre (measured on the mesh)
gn[CIG_NODE]['Q'] = (0, 0, 0, 1); gn[CIG_NODE]['T'] = tuple(park)
GL = [np.array(P_.locals_at(gn, [], 0)[k]) for k in range(NN)]                  # game rest locals
GW = world(gn, GL)
# cigarette: axis straight out of the lips in the puff pose, between index and middle finger
Mw = RS @ Wb[39][:3, :3]; AX = Mw.T @ np.array([0, 0, 1.0]); AT = np.array([-0.12, 0.0, -0.36])
BANDS = [(-0.10, -0.02, 0), (-0.02, 0.24, 1), (0.24, 0.265, 2), (0.265, 0.282, 3)]; RAD = 0.026; MIDY = (BANDS[0][0] + BANDS[-1][1]) / 2
u = np.cross(AX, [0, 0, 1.0]); u /= np.linalg.norm(u); w_ = np.cross(AX, u); RC = np.stack([AX, u, w_], 1)   # node frame x = cigarette axis
def cig_mesh(n=8):
    P = []; B = []; F = []
    ring = lambda x: [[x, RAD * JS * np.cos(2 * np.pi * k / n), RAD * JS * np.sin(2 * np.pi * k / n)] for k in range(n)]
    for y0, y1, b in BANDS:
        i0 = len(P); P += ring((y0 - MIDY) * JS) + ring((y1 - MIDY) * JS); B += [b] * 2 * n
        for k in range(n):
            a, c = i0 + k, i0 + (k + 1) % n; F += [[a, c, c + n], [a, c + n, a + n]]
    for x, b in ((BANDS[0][0], 0), (BANDS[-1][1], 3)):
        ci = len(P); P.append([(x - MIDY) * JS, 0, 0]); B.append(b); r0 = len(P); P += ring((x - MIDY) * JS); B += [b] * n
        F += [[ci, r0 + k, r0 + (k + 1) % n] for k in range(n)]
    P = np.array(P); F = np.array(F)
    cen = P[F].mean(1); nrm = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])
    outw = cen.copy(); outw[:, 0] = np.where(np.abs(cen[:, 1]) + np.abs(cen[:, 2]) < 1e-6, np.sign(cen[:, 0]), 0)   # caps point along the axis
    fl = (nrm * outw).sum(1) < 0; F[fl] = F[fl][:, ::-1]
    return P, B, F
def to_game(M):          # preview world (rotation x0.9) -> game world (rigid)
    G = M.copy(); G[:3, :3] = M[:3, :3] / JS; return G
def cig_world(G39):      # game world of the cigarette node held in the right glove
    out = np.eye(4); out[:3, :3] = G39[:3, :3] @ RC; out[:3, 3] = G39[:3, 3] + G39[:3, :3] @ (JS * (AT + AX * MIDY)); return out

def solve(Wk, root, cig):
    """keyed game worlds (root frame) -> locals for all 50 nodes"""
    W = [None] * NN; L = [None] * NN
    for n in range(NN):
        p = gn[n]['parent']; Wp = W[p] if p >= 0 else np.eye(4)
        W[n] = Wk[n] if n in Wk else Wp @ GL[n]
    if cig: W[CIG_NODE] = cig_world(W[39])          # node 29 comes before 39: placed once the glove is known
    else: W[CIG_NODE] = W[13] @ np.linalg.inv(GW[13]) @ GW[CIG_NODE]   # parked: follows the head ball
    for n in range(NN):
        p = gn[n]['parent']; L[n] = np.linalg.inv(W[p] if p >= 0 else np.eye(4)) @ W[n]
    return L
def clip(frames_fn, nfr, step, root, hold=0):
    """hold: extra frames repeating the last pose (the game loops clips; if one ends before the code switches
    to the next, it holds still instead of restarting)"""
    keys = {n: [] for n in range(NN)}; fr = list(range(0, nfr, step)) + [nfr] + ([nfr + hold] if hold else [])
    for f in fr:
        Wk, cig = frames_fn(min(f, nfr))
        Wk = {n: root @ to_game(M) for n, M in Wk.items()}
        L = solve(Wk, root, cig)
        for n in range(NN): keys[n].append((f, L[n]))
    tracks = []
    for n in range(NN):
        ks = keys[n]
        if all(np.allclose(ks[0][1], k[1], atol=1e-5) for k in ks):
            tracks.append((n, 'const', (joe_anm.mat2q(ks[0][1][:3, :3]), ks[0][1][:3, 3])))
        else:
            out = []; prev = None
            for f, M in ks:
                q = joe_anm.mat2q(M[:3, :3])
                if prev is not None and np.dot(q, prev) < 0: q = -q
                prev = q; out.append((f, q, M[:3, 3]))
            tracks.append((n, 'keys', out))
    return joe_anm.rebuild(open(VAN + 'anm00.bin', 'rb').read(), float(nfr + hold), tracks)

ROOT_FACE = np.linalg.inv(Tr([0, 0, ZS]) @ Ryh(np.pi))     # bench frame -> NPC facing the bench
ROOT_AWAY = np.linalg.inv(Tr([0, 0, ZS]))                   # bench frame -> NPC facing away
n_down = int(round(2.4 * SPEED * FPS)); n_up = int(round(1.6 * SPEED * FPS)); n_loop = int(LOOP * FPS)
CIG_ON = 2.15            # design seconds into the sit down: right hand settled on the knee
def f_down(f):
    t = f / FPS / SPEED; W = sitdown(t); return W, t >= CIG_ON
def f_loop(f):
    W = posedW(spec_at(f / FPS)); return {n: W[n] for n in KEYED[:-1]}, True
def f_up(f):
    t = f / FPS / SPEED; return standup(t), f == 0
HOLD = 90

# ---------------------------------------------------------------- talking and the gift (clips 9-11)
# 9 standing talk: Van's "explaining" clip 17 (both hands out in front), on the keyed nodes
v17 = parse(open(VAN + 'anm17.bin', 'rb').read()); n_talk = int(v17[0]['length'])
def f_talk(f):
    W = [D @ w for w in world(nodes, P_.locals_at(nodes, v17, f))]; return {n: W[n] for n in KEYED[:-1]}, False
# 10 sitting talk: the sitting pose, the cigarette hand comes up off the knee and gestures; head nods
TLOOP = 4.0
PG = np.array([-0.56, 0.60, 0.40])                       # hand out in front, at chest height
RG = Rx(-0.55) @ Ry(0.35) @ RK                           # wrist turned up: open hand
SLG = Slerp([0, 1], Rot.from_matrix([RK, RG]))
def sit_talk_spec(t):
    s = base_spec()
    up = seg(t, 0.15, 0.7) - seg(t, 3.0, 3.7)
    wave = up * np.array([0.05 * np.sin(2 * np.pi * (t - 0.7) / 1.15), 0.045 * np.sin(2 * np.pi * (t - 0.7) / 0.575), 0.03 * np.sin(2 * np.pi * (t - 0.7) / 1.15)])
    R = SLG([up]).as_matrix()[0] @ Rx(0.18 * up * np.sin(2 * np.pi * (t - 0.7) / 0.575))
    s[39] = (list(P0 + (PG - P0) * up + wave), R)
    nod = 0.07 * np.sin(2 * np.pi * t / 1.0) * (seg(t, 0.3, 0.8) - seg(t, 3.0, 3.5))
    s[13] = ([0, HY, -0.06], Ry(-0.12 * up) @ Rx(-0.10 + nod)); return s
def f_sittalk(f):
    W = posedW(sit_talk_spec(f / FPS)); return {n: W[n] for n in KEYED[:-1]}, True
# 11 gift: takes the coin with the right hand, looks at it, slips it into a back pocket, back to idle
def place_s(n, t, R):                                    # standing frame: R relative to the idle rotation
    out = np.eye(4); out[:3, :3] = R @ WI[n][:3, :3]; out[:3, 3] = t; return out
PI39 = WI[39][:3, 3]
KEYS39 = [(0.0, PI39, np.eye(3)),
          (0.45, np.array([-0.30, 0.66, 0.42]), Rz(-0.9) @ Rx(-0.4)),     # reach out, palm up
          (0.75, np.array([-0.30, 0.66, 0.42]), Rz(-0.9) @ Rx(-0.4)),
          (1.15, np.array([-0.40, 0.78, 0.30]), Rz(-0.6) @ Rx(-0.7)),     # bring it up to look at it
          (1.55, np.array([-0.40, 0.78, 0.30]), Rz(-0.6) @ Rx(-0.7)),
          (2.10, np.array([-0.42, 0.42, -0.42]), Ry(-0.9) @ Rz(0.3)),     # round to the back pocket
          (2.40, np.array([-0.40, 0.38, -0.46]), Ry(-0.9) @ Rz(0.3)),
          (3.00, PI39, np.eye(3))]
def key_at(K, t):
    for (t0, p0, r0), (t1, p1, r1) in zip(K, K[1:]):
        if t <= t1:
            w = ease((t - t0) / (t1 - t0)); return p0 + (p1 - p0) * w, Slerp([0, 1], Rot.from_matrix([r0, r1]))([w]).as_matrix()[0]
    return K[-1][1], K[-1][2]
def f_pocket(f):
    t = f / FPS; W = {n: WI[n].copy() for n in KEYED[:-1]}
    p, R = key_at(KEYS39, t); W[39] = place_s(39, p, R)
    look = seg(t, 0.2, 0.6) - seg(t, 1.6, 2.1); turn = seg(t, 1.6, 2.0) - seg(t, 2.3, 2.9)
    H = WI[13].copy(); H[:3, :3] = Ry(-0.35 * turn) @ Rx(0.22 * look) @ WI[13][:3, :3]; H[1, 3] += 0.02 * np.sin(np.pi * seg(t, 0.9, 1.5)); W[13] = H
    return W, False
n_stalk = int(TLOOP * FPS); n_pocket = int(3.0 * FPS)

clips = {'anm_sitdown.bin': clip(f_down, n_down, 2, ROOT_FACE, HOLD),
         'anm_sitloop.bin': clip(f_loop, n_loop, 3, ROOT_AWAY),
         'anm_standup.bin': clip(f_up, n_up, 2, ROOT_AWAY, HOLD),
         'anm_talk.bin': clip(f_talk, n_talk, 2, np.eye(4)),
         'anm_sittalk.bin': clip(f_sittalk, n_stalk, 2, ROOT_AWAY),
         'anm_pocket.bin': clip(f_pocket, n_pocket, 2, np.eye(4), HOLD)}
for k, v in clips.items(): open(os.path.join(OUT, k), 'wb').write(v); print(k, len(v))
P, B, F = cig_mesh()
json.dump(dict(park=list(park), mesh_P=P.tolist(), mesh_band=B, mesh_F=F.tolist(), clips=list(clips),
               frames=dict(sitdown=n_down, sitloop=n_loop, standup=n_up, talk=n_talk, sittalk=n_stalk, pocket=n_pocket), stand_spot=ZS), open(os.path.join(OUT, 'cig.json'), 'w'))
print('frames', n_down, n_loop, n_up, n_talk, n_stalk, n_pocket)
