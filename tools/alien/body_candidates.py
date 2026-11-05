"""Alien candidates on our base human (tools/goddess/data/blank_v3: the blank body on Celia's skeleton, same proportions
as the game's villagers). Per vertex: its Celia node (build_blank.py's body-part rule), softly blended with the parent
node near each joint; each candidate = bone length scales, joint rotations (world, about the joint) and local scales.
usage: onbase.py OUTDIR"""
import sys, numpy as np
from PIL import Image, ImageDraw, ImageFont
S = '/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/'
sys.path[:0] = [S + 'pm', S + 'goddess/blank']
from awlchar import act, world
import blank as BL
OUT = sys.argv[1]

nodes = act(open(S + 'celia/sepi_0.act', 'rb').read()); Wr = world(nodes)
P = np.array([w[:3, 3] for w in Wr]); PAR = [nd['parent'] for nd in nodes]
d = np.load(S + 'goddess/blank/blank_v3_smallbust.npz'); V0, F = d['V'], d['F']   # blank_v3 with a flat chest

# ---- node per vertex (as build_blank.py)
Sd = BL.S
def prim(X):
    m = lambda c, s: np.array(c) * [s, 1, 1]; out = {}
    out['head'] = np.minimum.reduce([BL.ell(X, *Sd['cran']), BL.ell(X, *Sd['jaw']), BL.ell(X, *Sd['chin']),
                                     BL.ell(X, m(Sd['ear'][0], 1), Sd['ear'][1]), BL.ell(X, m(Sd['ear'][0], -1), Sd['ear'][1])])
    out['neck'] = BL.cap(X, *Sd['neck'])
    out['torso'] = np.minimum.reduce([BL.ell(X, *Sd['chest']), BL.ell(X, *Sd['waist']), BL.ell(X, *Sd['hips'])] +
                                     [np.linalg.norm(X - m(Sd['bust'][0], s), axis=-1) - Sd['bust'][1] for s in (1, -1)])
    for s, sd in ((1, 'L'), (-1, 'R')):
        out['arm' + sd] = np.minimum.reduce([BL.cap(X, m(Sd[k][0], s), m(Sd[k][1], s), *Sd[k][2:]) for k in ('shoulder', 'upper', 'fore')])
        out['hand' + sd] = np.minimum(BL.rbox(X, m(Sd['palm'][0], s), Sd['palm'][1], Sd['palm'][2]), BL.rbox(X, m(Sd['mitt'][0], s), Sd['mitt'][1], Sd['mitt'][2]))
        out['thumb' + sd] = BL.cap(X, m(Sd['thumb'][0], s), m(Sd['thumb'][1], s), *Sd['thumb'][2:])
        out['leg' + sd] = np.minimum.reduce([BL.cap(X, m(Sd['thigh'][0], s), m(Sd['thigh'][1], s), *Sd['thigh'][2:]),
                                            BL.cap(X, m(Sd['shin'][0], s), m(Sd['shin'][1], s), *Sd['shin'][2:]), BL.ell(X, m(Sd['calf'][0], s), Sd['calf'][1])])
        out['foot' + sd] = BL.rbox(X, m(Sd['foot'][0], s), Sd['foot'][1], Sd['foot'][2])
    return out
pr = prim(V0); names = list(pr); LAB = np.array(names)[np.argmin(np.stack([pr[n] for n in names]), 0)]
def node_of(p, part):
    x, y, z = p; ax = abs(x); o = 0 if x >= 0 else 11; ol = 0 if x >= 0 else 7
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
NODE = np.array([node_of(p, l) for p, l in zip(V0, LAB)])

def eff_parent(n):                                  # nearest ancestor at a different place (the joint we bend about)
    p = PAR[n]
    while p >= 0 and np.linalg.norm(P[p] - P[n]) < 0.01: p = PAR[p]
    return p

def rot(axis, deg):
    a = np.asarray(axis, float); a /= np.linalg.norm(a); t = np.radians(deg); c, s = np.cos(t), np.sin(t); x, y, z = a
    return np.array([[c + x * x * (1 - c), x * y * (1 - c) - z * s, x * z * (1 - c) + y * s],
                     [y * x * (1 - c) + z * s, c + y * y * (1 - c), y * z * (1 - c) - x * s],
                     [z * x * (1 - c) - y * s, z * y * (1 - c) + x * s, c + z * z * (1 - c)]])

def alien_rest(V):
    """v2 (user: too feminine, too like the villagers): rest-shape changes shared by every candidate."""
    V = V.copy(); x, y, z = V[:, 0], V[:, 1], V[:, 2]
    head = LAB == 'head'; ax = np.abs(x)
    # straight, sexless torso: no waist, narrow hips, flat chest
    tor = LAB == 'torso'
    hip = tor & (y < 0.6); V[hip, 0] *= 0.8; V[hip, 2] = -0.005 + (z[hip] + 0.005) * 0.85
    wst = tor & (y >= 0.6) & (y < 0.7); V[wst, 0] *= 1.08
    chs = tor & (y >= 0.68) & (z > 0.03); V[chs, 2] = 0.03 + (z[chs] - 0.03) * 0.35
    # gaunt limbs
    arm = np.isin(NODE, [13, 24]) | ((NODE == 12) & (ax > 0.2)) | ((NODE == 23) & (ax > 0.2))
    V[arm, 1] = 0.795 + (y[arm] - 0.795) * 0.72; V[arm, 2] = -0.005 + (z[arm] + 0.005) * 0.72
    leg = np.isin(NODE, [37, 38, 44, 45]) | ((LAB == 'legL') | (LAB == 'legR')) & (y < 0.5)
    cx = np.sign(x[leg]) * 0.06
    V[leg, 0] = cx + (x[leg] - cx) * 0.72; V[leg, 2] = 0.005 + (z[leg] - 0.005) * 0.72
    # a thin neck (user)
    # a thin neck (user): a round tube of one radius all the way along
    nk = LAB == 'neck'; cz = np.median(z[nk]); dx, dz = x[nk], z[nk] - cz; rr = np.hypot(dx, dz) + 1e-9
    V[nk, 0] = dx / rr * 0.016; V[nk, 2] = cz + dz / rr * 0.016
    # forearms: round tubes (the base's forearm is part of its flat mitten hand); hands bigger, fingers longer
    for fn, sx in ((15, 1), (26, -1)):
        fa = NODE == fn; dy, dz = y[fa] - 0.795, z[fa] + 0.005; rr = np.hypot(dy, dz) + 1e-9
        V[fa, 1] = 0.795 + dy / rr * 0.014; V[fa, 2] = -0.005 + dz / rr * 0.014
    for hn, wn in ((17, 16), (28, 27)):
        hd = np.isin(NODE, [hn, hn + 2, hn + 3]); c = P[wn]
        V[hd] = c + (V[hd] - c) * np.array([1.5, 1.15, 1.35])
    # a rounded upper back (user): the back of the chest bulges out
    bk = (LAB == 'torso') & (z < 0) & (y > 0.62) & (y < 0.84)
    V[bk, 2] -= 0.035 * np.sin(np.clip((y[bk] - 0.62) / 0.22, 0, 1) * np.pi)
    # no ears
    e = head & (ax > 0.19) & (np.abs(y - 1.025) < 0.07) & (np.abs(z - 0.015) < 0.06)
    V[e, 0] = np.sign(x[e]) * np.minimum(ax[e], 0.2)
    # the skull swells up and back into a dome above a face of normal size
    dm = head & (y > 1.0); t = y[dm] - 1.0
    V[dm, 1] = 1.0 + t * 1.32; V[dm, 2] = np.where(z[dm] < 0, z[dm] * (1 + 1.6 * t), z[dm])
    return V
VA = alien_rest(V0)

def pose(spec, V0=V0):
    """spec: len {node: k} (scales the bone from its effective parent), rot {node: R} (world rotation at the joint),
       scl {node: (centre, (sx, sy, sz))} (non-uniform scale of that node's own vertices, rest space)."""
    L, Rd, Sc = spec.get('len', {}), spec.get('rot', {}), spec.get('scl', {})
    R = [None] * len(nodes); t = [None] * len(nodes)
    for n in range(len(nodes)):
        p = PAR[n]
        if p < 0: R[n] = np.eye(3); t[n] = P[n].copy(); continue
        off = (P[n] - P[p]) * L.get(n, 1.0)
        t[n] = R[p] @ off + t[p]
        R[n] = R[p] @ Rd.get(n, np.eye(3))
    def F(n, X):
        X = X - P[n]
        if n in Sc:
            c, s = Sc[n]; X = (X + P[n] - c) * s + c - P[n]
        return X @ R[n].T + t[n]
    pose.last = (R, t)
    out = np.zeros_like(V0)
    for n in np.unique(NODE):
        idx = np.where(NODE == n)[0]; X = V0[idx]
        q = eff_parent(n)
        if q < 0: out[idx] = F(n, X); continue
        dvec = P[n] - P[q]; ln = np.linalg.norm(dvec); dvec /= ln
        s = (X - P[n]) @ dvec / 0.035                     # blend across ~7 cm around the joint
        w = np.clip(0.5 + 0.5 * s, 0, 1); w = w * w * (3 - 2 * w)
        if n == 7:                                        # the neck stretches smoothly; the head itself stays rigid
            w = np.where(LAB[idx] == 'head', 1.0, np.clip((X[:, 1] - 0.80) / 0.12, 0, 1))
        out[idx] = w[:, None] * F(n, X) + (1 - w[:, None]) * F(q, X)
    return out

# arms down at the sides: the T-pose shoulder (node 12 / 23) turned ~78 degrees
def arms_down(deg=78, elbow=8, sw=0):
    return {12: rot((0, 0, 1), -deg + sw), 23: rot((0, 0, 1), deg - sw), 15: rot((0, 1, 0), elbow), 26: rot((0, 1, 0), -elbow)}

HEADC = np.array([0, 1.08, 0.0])
def merge(*ds):
    o = {}
    for dct in ds: o.update(dct)
    return o

human = dict(rot=arms_down())

HANDS = {17: 1.5, 28: 1.5}
A = dict(   # The Listener: long neck pushed forward, head jutting and tipped down, shoulders hunched up and rolled in,
            # arms a little too long, knees slightly bent and in
    len=merge(HANDS, {7: 1.9, 13: 1.15, 15: 1.2, 16: 1.15, 24: 1.15, 26: 1.2, 27: 1.15}),
    rot=merge(arms_down(70, 14), {6: rot((1, 0, 0), 38), 7: rot((1, 0, 0), -12), 5: rot((1, 0, 0), 10),
              11: rot((0, 0, 1), 10) @ rot((0, 1, 0), -14), 22: rot((0, 0, 1), -10) @ rot((0, 1, 0), 14),
              37: rot((1, 0, 0), -10) @ rot((0, 0, 1), 3), 44: rot((1, 0, 0), -10) @ rot((0, 0, 1), -3),
              38: rot((1, 0, 0), 18), 45: rot((1, 0, 0), 18)}),
    scl={7: (HEADC, (1.05, 1.08, 1.05))})

B = dict(   # The Tall One: 1.3x, neck twice as long, long thin limbs, stiff and straight, head tilted to one side
    len=merge(HANDS, {7: 2.2, 4: 1.25, 5: 1.25, 6: 1.2, 13: 1.3, 15: 1.35, 16: 1.2, 24: 1.3, 26: 1.35, 27: 1.2,
         38: 1.35, 39: 1.35, 45: 1.35, 46: 1.35}),
    rot=merge(arms_down(84, 2), {7: rot((0, 0, 1), 16)}),
    scl={7: (HEADC, (0.95, 1.06, 0.98)), 3: (P[3], (0.85, 1, 0.9)), 4: (P[4], (0.85, 1, 0.9)), 5: (P[5], (0.85, 1, 0.9))})

C = dict(   # The Contorted: bent at the waist and twisted, one shoulder dropped, head cocked far over, one arm longer,
            # knees bent, feet turned in
    len=merge(HANDS, {7: 1.6, 24: 1.25, 26: 1.35, 27: 1.2, 13: 1.05, 15: 1.05}),
    rot=merge(arms_down(64, 25, 0), {4: rot((1, 0, 0), 22) @ rot((0, 1, 0), 18), 5: rot((0, 0, 1), -12),
              6: rot((1, 0, 0), 20), 7: rot((0, 0, 1), -55) @ rot((1, 0, 0), 10),
              23: rot((0, 0, 1), 84), 26: rot((0, 1, 0), -4),
              37: rot((1, 0, 0), -30) @ rot((0, 1, 0), 15), 44: rot((1, 0, 0), -25) @ rot((0, 1, 0), -15),
              38: rot((1, 0, 0), 40), 45: rot((1, 0, 0), 32)}),
    scl={7: (HEADC, (1.02, 1.04, 1.02))})

D = dict(   # The Wide: head and face far too wide and a little flat, long thin neck, narrow sloping shoulders,
            # elbows bent the wrong way, long forearms
    len=merge(HANDS, {7: 1.6, 11: 0.75, 22: 0.75, 15: 1.25, 26: 1.25}),
    rot=merge(arms_down(80, -14), {11: rot((0, 0, 1), -12), 22: rot((0, 0, 1), 12)}),
    scl={7: (HEADC, (1.4, 0.88, 1.08)), 6: (P[6], (0.8, 1, 0.8))})

def fore(elbow_axis, deg, wrist=None, sh=84, out=0, fwd=0, flen=3.0, extra=None):
    """B with the forelimbs folded up at the elbow (user): elbow turned deg about elbow_axis (rest frame, left arm;
       mirrored for the right), optional wrist turn, shoulder angle sh, upper arm out sideways by 'out' degrees."""
    ax = np.array(elbow_axis, float); axR = ax * [-1, 1, 1] * -1     # mirror: x stays, rotation sense flips
    r = {12: rot((1, 0, 0), -fwd) @ rot((0, 0, 1), -sh + out), 23: rot((1, 0, 0), -fwd) @ rot((0, 0, 1), sh - out), 7: rot((0, 0, 1), 16),
         15: rot(ax, deg), 26: rot(ax * [1, -1, -1], deg)}
    if wrist is not None: r[16] = rot(wrist[0], wrist[1]); r[27] = rot(np.array(wrist[0]) * [1, -1, -1], wrist[1])
    if extra:
        r.update(extra)
        # the arm angles above are meant in the world, not on top of the spine's lean: undo the parents' rotation
        def acc(n):
            Rn = np.eye(3); chain = []
            while n >= 0: chain.append(n); n = PAR[n]
            for c in reversed(chain): Rn = Rn @ r.get(c, np.eye(3))
            return Rn
        for sh_n in (12, 23):
            r[sh_n] = acc(PAR[sh_n]).T @ r[sh_n]
    sc = dict(B['scl']); sc[15] = (P[15], (flen, 1, 1)); sc[26] = (P[26], (flen, 1, 1))   # the forearm mesh itself
    return dict(len=merge(B['len'], {16: flen, 27: flen}), rot=r, scl=sc)

def hunch(k):
    """shoulders up and rolled forward, upper back rounded, neck leaning out (strength k); the head is turned back
       up so it faces straight ahead (user), whatever the lean"""
    a4, a5, a6 = 14 * k, 20 * k, 34 * k
    return {4: rot((1, 0, 0), a4), 5: rot((1, 0, 0), a5), 6: rot((1, 0, 0), a6), 7: rot((1, 0, 0), -(a4 + a5 + a6)),
            11: rot((0, 0, 1), 14 * k) @ rot((0, 1, 0), -18 * k), 22: rot((0, 0, 1), -14 * k) @ rot((0, 1, 0), 18 * k)}

SKIN = np.array([214, 210, 212]) / 255; HUM = np.array([150, 158, 170]) / 255; BG = np.array([30, 30, 36]) / 255

def render(V, ang, col, W=280, H=470, sc=240, oy=None, F=F, fcol=None):
    c, s = np.cos(ang), np.sin(ang)
    X = V @ np.array([[c, 0, -s], [0, 1, 0], [s, 0, c]]).T
    sx = W / 2 + X[:, 0] * sc; sy = (H - 14 if oy is None else oy) - X[:, 1] * sc; z = X[:, 2]
    img = np.tile(BG, (H, W, 1)); zb = np.full((H, W), -1e9)
    N = np.cross(X[F[:, 1]] - X[F[:, 0]], X[F[:, 2]] - X[F[:, 0]]); N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-12
    Lt = np.array([0.35, 0.55, 0.75]); Lt /= np.linalg.norm(Lt)
    shade = 0.28 + 0.72 * np.clip(N @ Lt, 0, 1) + 0.18 * (1 - np.abs(N[:, 2])) ** 3
    for i, (a, b, cc) in enumerate(F):
        inside = N[i, 2] <= 0
        if inside and not render.insides: continue
        xs = np.array([sx[a], sx[b], sx[cc]]); ys = np.array([sy[a], sy[b], sy[cc]])
        x0, x1 = int(max(0, xs.min())), int(min(W - 1, xs.max() + 1)); y0, y1 = int(max(0, ys.min())), int(min(H - 1, ys.max() + 1))
        if x0 > x1 or y0 > y1: continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        den = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(den) < 1e-9: continue
        l0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / den
        l1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / den; l2 = 1 - l0 - l1
        m = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
        zz = l0 * z[a] + l1 * z[b] + l2 * z[cc]
        sub = zb[y0:y1 + 1, x0:x1 + 1]; m &= zz > sub
        c_ = np.array([0.16, 0.05, 0.06]) if inside or (fcol is not None and i < len(fcol) and fcol[i]) else col * shade[i]
        sub[m] = zz[m]; img[y0:y1 + 1, x0:x1 + 1][m] = c_
    return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))

render.insides = False
def tube(a, b, ra, rb, k=8):
    """a closed cylinder a -> b (radii ra, rb): vertices, faces"""
    a, b = np.asarray(a, float), np.asarray(b, float); d = b - a; L = np.linalg.norm(d) + 1e-9; d /= L
    u = np.cross(d, [0, 0, 1]) if abs(d[2]) < 0.9 else np.cross(d, [1, 0, 0]); u /= np.linalg.norm(u); w = np.cross(d, u)
    ang = np.linspace(0, 2 * np.pi, k, endpoint=False)
    ring = lambda c, r: c + r * (np.cos(ang)[:, None] * u + np.sin(ang)[:, None] * w)
    Vt = np.vstack([ring(a, ra), ring(b, rb), a, b]); Ft = []
    for i in range(k):
        j = (i + 1) % k
        Ft += [(i, j, k + j), (i, k + j, k + i), (2 * k, j, i), (2 * k + 1, k + i, k + j)]
    return Vt, np.array(Ft)

HINGE = np.array([0, 0.95, -0.02])
def jaw(V, width=1.35, open_deg=0.0, mouth=0.905):
    """a wide jaw (user): the lower front of the head below the mouth line, flaring out wider than the face toward
       the chin (jowls), hinged under the ears; open_deg drops it for the scream. Rest space (head rigid on node 7)."""
    V = V.copy(); hd = LAB == 'head'
    # the bell (user, from the first jaw render): the whole lower head flares out, widest at the bottom
    b = np.clip((0.965 - V[:, 1]) / 0.03, 0, 1) * (V[:, 2] > -0.09) * hd; b = b * b * (3 - 2 * b)
    V[:, 0] *= 1 + (width - 1) * b * np.clip((0.975 - V[:, 1]) / 0.05, 0, 1)
    w = ((V[:, 1] < mouth) & (V[:, 2] > -0.01) & hd).astype(float)     # a clean cut at the mouth line
    if open_deg:
        q = V - HINGE; Rj = rot((1, 0, 0), open_deg)
        V = V * (1 - w[:, None]) + (q @ Rj.T + HINGE) * w[:, None]
    return V

def jaw_bell(V, width=1.6, open_deg=0.0, top=0.965, soft=0.03, hinge=(0, 0.975, -0.03)):
    """the first jaw render (user's pick, J3): the whole lower head flares smoothly into a bell, widest at the bottom,
       and opening swings that whole lower head down from a hinge under the ears (the skin stretches, no cut)."""
    V = V.copy(); hd = LAB == 'head'
    w = np.clip((top - V[:, 1]) / soft, 0, 1) * (V[:, 2] > -0.09) * hd; w = w * w * (3 - 2 * w)
    V[:, 0] *= 1 + (width - 1) * w * np.clip((top + 0.01 - V[:, 1]) / 0.05, 0, 1)
    if open_deg:
        hg = np.array(hinge); q = V - hg; Rj = rot((1, 0, 0), open_deg)
        V = V * (1 - w[:, None]) + (q @ Rj.T + hg) * w[:, None]
    return V

FORE_NODES = [15, 16, 17, 19, 20, 26, 27, 28, 30, 31]
def forelimbs(V):
    """replace the base's mitten forearm / hand with a round forearm, a palm and three long fingers (blockout)"""
    R, t = pose.last
    keep = ~np.isin(NODE, FORE_NODES)
    Fk = F[keep[F].all(1)]
    Vs, Fs = [V], [Fk]; base = len(V)
    def add(vt, ft):
        nonlocal base
        Vs.append(vt); Fs.append(ft + base); base += len(vt)
    for e, w, sx in ((15, 16, 1), (26, 27, -1)):
        add(*tube(t[e], t[w], 0.017, 0.012))
        hd = R[w] @ np.array([sx, 0, 0]); side = R[w] @ np.array([0, 0, 1])
        palm_end = t[w] + hd * 0.07
        add(*tube(t[w], palm_end, 0.016, 0.02))
        for f in (-1, 0, 1):
            add(*tube(palm_end + side * 0.012 * f, palm_end + hd * 0.09 + side * 0.02 * f, 0.006, 0.004, 6))
    return np.vstack(Vs), np.vstack(Fs)

try: font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 20); small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
except Exception: font = small = ImageFont.load_default()
VH = pose(human)
views = [(0, 'front'), (np.radians(40), '3/4'), (np.radians(90), 'side'), (np.pi, 'back')]
rows = []
import os
SET = os.environ.get('SET', 'all')
LIST = (('A', 'The Listener', A), ('B', 'The Tall One', B), ('C', 'The Contorted', C), ('D', 'The Wide', D))
if SET == 'mantis':
    LIST = (('M1', 'Mantis, hunched: forearms up at chest height', fore((0, 1, 0), -105, ((0, 1, 0), -85), fwd=18, out=10, extra=hunch(1.0))),
            ('M2', 'Mantis, hunched: forearms lower, reaching forward', fore((0, 1, 0), -80, ((0, 1, 0), -80), fwd=10, out=8, extra=hunch(1.0))),
            ('M3', 'Mantis, very hunched: forearms low, hands dangling', fore((0, 1, 0), -70, ((0, 1, 0), -90), fwd=5, out=6, extra=hunch(1.5))))
if SET == 'jaw':
    T2 = fore((0, 1, 0), -150, ((0, 1, 0), 145), fwd=0, out=4, extra=hunch(1.5))
    render.insides = True
    rows = []
    for tag, nm, wd, op, dark in (('J3', 'closed: a normal face, no jaw showing', 1.0, 0, 0), ('J3', 'opening: the bell starts to flare', 1.3, 35, 1),
                                  ('J3', 'the scream: full bell', 1.6, 70, 1)):
        Vc = pose(T2, jaw_bell(VA, wd, 0)); Vj = pose(T2, jaw_bell(VA, wd, op))
        ar = lambda X: np.linalg.norm(np.cross(X[F[:, 1]] - X[F[:, 0]], X[F[:, 2]] - X[F[:, 0]]), axis=1)
        mouthF = (ar(Vj) > 1.8 * ar(Vc) + 1e-7) & bool(dark)          # skin stretched across the opening: the mouth
        Vj, FF = forelimbs(Vj); keep = ~np.isin(NODE, FORE_NODES); mouthF = mouthF[keep[F].all(1)]
        hc = Vj[LAB == 'head'].mean(0) if False else None
        cells = [render(Vj, a, SKIN, F=FF, fcol=mouthF) for a, _ in views[:3]]
        # close-ups of the head: front and 3/4, zoomed on the face
        Hc = Vj[LAB == 'head'].mean(0) if len(Vj) == len(LAB) else Vj[:len(LAB)][LAB == 'head'].mean(0)
        for a in (0, np.radians(40)):
            cells.append(render(Vj - Hc, a, SKIN, F=FF, sc=380, oy=250, fcol=mouthF))
        sheet = Image.new('RGB', (280 * len(cells), 470 + 34), (30, 30, 36)); dr = ImageDraw.Draw(sheet)
        for k, cimg in enumerate(cells):
            sheet.paste(cimg, (280 * k, 34)); dr.text((280 * k + 6, 38), (['front', '3/4', 'side'] + ['face front', 'face 3/4'])[k], fill=(160, 160, 170), font=small)
        dr.text((8, 6), '%s  %s' % (tag, nm), fill=(235, 225, 220), font=font); rows.append(sheet); print(tag)
    out = Image.new('RGB', (rows[0].width, sum(r.height for r in rows))); y = 0
    for r in rows: out.paste(r, (0, y)); y += r.height
    out.save(OUT + '/alien_jaw.png'); sys.exit(0)
if SET == 'trex':   # M3's hunch, forearms up from the elbow, wrists bent so the hands hang down (user: like a T-rex)
    LIST = (('T1', 'T-rex arms: forearms up and forward, hands hanging down', fore((0, 1, 0), -130, ((0, 1, 0), 128), fwd=-5, out=4, extra=hunch(1.5))),
            ('T2', 'T-rex arms: forearms steeper, hands hanging down', fore((0, 1, 0), -150, ((0, 1, 0), 145), fwd=0, out=4, extra=hunch(1.5))),
            ('T3', 'T-rex arms: elbows tucked back, forearms up, hands down', fore((0, 1, 0), -140, ((0, 1, 0), 135), fwd=-20, out=4, extra=hunch(1.5))))
if SET == 'fore':
    LIST = (('B1', 'Mantis: long forearms folded up in front, hands hanging limp', fore((0, 1, 0), -120, ((0, 1, 0), -85), fwd=40, out=12)),
            ('B2', 'Reversed: elbows bent backwards, forearms up behind the shoulders', fore((0, 1, 0), 125, ((0, 1, 0), 70), fwd=-35, out=14)),
            ('B3', 'Sideways: elbows bend outward, forearms up beside the head', fore((0, 0, 1), 135, ((0, 0, 1), -70), out=25)),
            ('B4', 'Raised: upper arms out level, forearms straight up, wrists bent over', fore((0, 0, 1), 90, ((0, 0, 1), 80), sh=8)))
for tag, nm, spec in LIST:
    V = pose(spec, VA)
    if SET in ('trex', 'mantis', 'fore'): V, FF = forelimbs(V)
    else: FF = F
    cells = [render(VH, np.radians(25), HUM)] + [render(V, a, SKIN, F=FF) for a, _ in views]
    sheet = Image.new('RGB', (280 * len(cells), 470 + 34), (30, 30, 36)); dr = ImageDraw.Draw(sheet)
    for k, cimg in enumerate(cells):
        sheet.paste(cimg, (280 * k, 34)); dr.text((280 * k + 6, 38), 'base human' if k == 0 else views[k - 1][1], fill=(160, 160, 170), font=small)
    dr.text((8, 6), '%s  %s' % (tag, nm), fill=(235, 225, 220), font=font)
    sheet.save('%s/base_%s.png' % (OUT, tag)); rows.append(sheet); print(tag)
out = Image.new('RGB', (rows[0].width, sum(r.height for r in rows)))
y = 0
for r in rows: out.paste(r, (0, y)); y += r.height
out.save(OUT + {'fore': '/alien_forelimbs.png', 'mantis': '/alien_mantis.png', 'trex': '/alien_trex.png'}.get(SET, '/alien_bodies_base.png'))
