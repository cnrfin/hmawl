"""Skirt follows the legs: per frame, Celia's skirt nodes (32 left, 33 right, 34 front) are swung (about
their own x axis, as her keys do) so each skirt half points where that leg's hip->ankle direction points
(pitch, relative to rest, times K). 34 takes the average of 32 and 33. Legs keep Celia's motion.
Tracks are rewritten with a key every frame (frame, quaternion, control = the same quaternion)."""
import struct, numpy as np
from awlchar import world, qmat
import pose
from anm import parse

SK_L, SK_R, SK_C = 32, 33, 34
HIP_L, ANK_L, HIP_R, ANK_R = 36, 39, 43, 46
def qx(phi): return np.array([np.sin(phi / 2), 0, 0, np.cos(phi / 2)])
def pitch(v): return np.arctan2(v[2], -v[1])            # forward (+z) swing of a downward vector
def skirt_tracks(nodes, raw, K=1.0, extra=0.0):
    tr = parse(raw); L = tr[0]['length']; nf = int(round(L)) + 1
    rest = {n: np.array(nodes[n]['Q'], float) for n in (SK_L, SK_R, SK_C)}
    phi0 = {n: 2 * np.arctan2(rest[n][0], rest[n][3]) for n in rest}
    W0 = world(nodes)
    # the skirt node's local axis that points down at rest
    down = {n: W0[n][:3, :3].T @ np.array([0, -1.0, 0]) for n in rest}
    leg0 = {SK_L: pitch(W0[ANK_L][:3, 3] - W0[HIP_L][:3, 3]), SK_R: pitch(W0[ANK_R][:3, 3] - W0[HIP_R][:3, 3])}
    grid = np.radians(np.linspace(-80, 80, 321))
    out = {n: [] for n in rest}
    for f in range(nf):
        W = world(nodes, pose.locals_at(nodes, tr, f))
        par = nodes[SK_L]['parent']; Rp = W[par][:3, :3]
        ang = {}
        for n, (h, a) in ((SK_L, (HIP_L, ANK_L)), (SK_R, (HIP_R, ANK_R))):
            want = pitch(W0[n][:3, :3] @ down[n]) + K * (pitch(W[a][:3, 3] - W[h][:3, 3]) - leg0[n])
            want += extra * np.sign(want - pitch(W0[n][:3, :3] @ down[n]))
            # skirt angle phi whose world down-vector pitch is closest to 'want'
            best = min(grid, key=lambda g: abs(pitch(Rp @ qmat(qx(phi0[n] + g)) @ down[n]) - want))
            ang[n] = best
        ang[SK_C] = 0.5 * (ang[SK_L] + ang[SK_R])
        for n in rest:
            q = qx(phi0[n] + ang[n])
            if out[n] and np.dot(out[n][-1][1], q) < 0: q = -q
            out[n].append((f, q))
    return L, out

def replace_tracks(raw, L, keys_by_node):
    """swap each node's track for keyed rotation (all 4 comps, control = value) + its constant translation"""
    d = bytes(raw); n = struct.unpack_from('>H', d, 4)[0]
    tab = [list(struct.unpack_from('>fIHHI', d, 8 + 16 * i)) for i in range(n)]
    offs = sorted(set(t[1] for t in tab)) + [len(d)]
    extra = b''
    for t in tab:
        node = t[3]
        if node not in keys_by_node: continue
        packed = t[4]; b3 = packed & 0xFF; b1 = (packed >> 16) & 0xFF
        comps = [c for c, bit in (('x', 0x20), ('y', 0x40), ('z', 0x80)) if not b1 & bit] + ['w']
        h = struct.unpack_from('>%dh' % ((offs[offs.index(t[1]) + 1] - t[1]) // 2), d, t[1])
        p = len(comps) if b3 & 0x08 else 0
        T = h[p:p + 3] if b3 & 0x01 else (0, 0, 0)
        blob = struct.pack('>3h', *T)
        for f, q in keys_by_node[node]:
            qi = [int(np.clip(round(c * 16384), -32768, 32767)) for c in q]
            blob += struct.pack('>9h', f, *qi, *qi)
        blob += bytes((-len(blob)) % 4)
        t[1] = len(d) + len(extra); t[2] = len(keys_by_node[node]); t[4] = 0x3E087001; t[0] = L
        extra += blob
    out = bytearray(d)
    for i, t in enumerate(tab): struct.pack_into('>fIHHI', out, 8 + 16 * i, *t)
    return bytes(out) + extra

# ---------------------------------------------------------------- skirt pushed by the feet (cloth-like)
FRONT, BACK, SIDE = 34, 32, 33
TOE_L, TOE_R = 41, 48
def skirt_push(nodes, raw, front_rest=26.2, back_rest=-21.6, margin=7.0, heel=0.35, scale=1.1, smooth=0.5):
    """front half (34) swings forward only when a toe would pass the gown's front hem angle, back half (32)
    swings back only when a heel would pass the back hem angle; sides (33) take the mean. Angles in degrees
    from the hip pivot, measured on the gown (rest pose)."""
    tr = parse(raw); L = tr[0]['length']; nf = int(round(L)) + 1
    rest = {n: np.array(nodes[n]['Q'], float) for n in (FRONT, BACK, SIDE)}
    phi0 = {n: 2 * np.arctan2(rest[n][0], rest[n][3]) for n in rest}
    W0 = world(nodes)
    down = {n: W0[n][:3, :3].T @ np.array([0, -1.0, 0]) for n in rest}
    grid = np.radians(np.linspace(-80, 80, 641))
    fr, br = np.radians(front_rest - margin), np.radians(back_rest + margin)
    dF = []; dB = []
    for f in range(nf):
        W = world(nodes, pose.locals_at(nodes, tr, f))
        piv = W[FRONT][:3, 3].copy(); piv[2] = W[2][:3, 3][2] if False else W[3][:3, 3][2]
        Rh = W[3][:3, :3]; R0 = W0[3][:3, :3]
        def pit(p):                     # pitch from the hip pivot, in the hips' own frame (follows her lean)
            v = R0 @ Rh.T @ (p - piv); return np.arctan2(v[2], -v[1])
        pts = []
        for a, t in ((ANK_L, TOE_L), (ANK_R, TOE_R)):
            A, Tt = W[a][:3, 3], W[t][:3, 3]
            pts += [pit(A), pit(Tt), pit(A + (A - Tt) * heel)]          # ankle, toe, heel (whichever sticks out)
        dF.append(max(0.0, max(pts) - fr)); dB.append(min(0.0, min(pts) - br))
    dF = np.array(dF); dB = np.array(dB)
    if smooth:                          # a little cloth lag/softness: circular smoothing over the loop
        for arr in (dF, dB):
            a = arr[:-1].copy(); k = np.array([0.25, 0.5, 0.25])
            orig = a.copy()
            for _ in range(int(smooth * 4)): a = k[0] * np.roll(a, 1) + k[1] * a + k[2] * np.roll(a, -1)
            a = np.where(np.abs(orig) > np.abs(a), orig, a)        # soften the edges, never lower a peak
            arr[:-1] = a; arr[-1] = a[0]
    out = {n: [] for n in rest}
    for f in range(nf):
        W = world(nodes, pose.locals_at(nodes, tr, f)); Rp = W[nodes[FRONT]['parent']][:3, :3]
        for n, d in ((FRONT, dF[f]), (BACK, dB[f]), (SIDE, 0.5 * dF[f] + 0.8 * dB[f])):
            base = pitch(Rp @ qmat(qx(phi0[n])) @ down[n])
            best = min(grid, key=lambda g: abs(pitch(Rp @ qmat(qx(phi0[n] + g)) @ down[n]) - (base + d)))
            q = qx(phi0[n] + best)
            if out[n] and np.dot(out[n][-1][1], q) < 0: q = -q
            out[n].append((f, q))
    return L, out, np.degrees(dF), np.degrees(dB)
