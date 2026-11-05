#!/usr/bin/env python3
"""Read the built alien back from its own game files (gpl / skn / act / tpl) and render it: the bind pose, and
posed the way zt.c will pose it (T2 arms, the hunch, the head forward) closed and screaming (jaw node 8 turned and
widened). Positions, UVs, textures and the node per vertex all come from the files.
usage: readback.py PREFIX OUT.png       (PREFIX = OUTDIR/NAME of build_alien.py)"""
import sys, os, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
SCR = '/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/'
PRE, OUTP = os.path.abspath(sys.argv[1]), sys.argv[2]
os.environ['SET'] = 'none'; os.environ['FACE'] = 'none'
_argv = sys.argv; sys.argv = ['x', os.path.dirname(OUTP) or '.']
exec(open(os.path.join(HERE, 'body_candidates.py')).read().split("try: font")[0])   # rot, fore, hunch
sys.argv = _argv
os.chdir(SCR + 'goddess'); sys.path[:0] = ['.', 'blank', '../pm']
import awlmodel, wally, view, raster
from awlchar import world
from PIL import Image, ImageDraw

M = awlmodel.load(PRE); V = M['V']; UV = M['UV']
nd = M['nodes']; Wb = world(nd); Pb = np.array([w[:3, 3] for w in Wb]); PARb = [x['parent'] for x in nd]
bone = np.array([b[0] if b else 0 for b in M['bones']])
T = wally.textures(PRE + '_b0.tpl', PRE + '_f0_e.tpl', PRE + '_f0_m.tpl')

def posed(rots, jaw_deg=0.0, jaw_wide=1.0):
    R = [None] * len(nd); t = [None] * len(nd)
    for n in range(len(nd)):
        p = PARb[n]
        if p < 0: R[n] = np.eye(3); t[n] = Pb[n].copy(); continue
        t[n] = R[p] @ (Pb[n] - Pb[p]) + t[p]; R[n] = R[p] @ rots.get(n, np.eye(3))
    if jaw_deg: R[8] = R[8] @ rot((1, 0, 0), jaw_deg)
    out = np.zeros_like(V)
    for n in np.unique(bone):
        i = bone == n; q = V[i] - Pb[n]
        if n == 8: q = q * [jaw_wide, 1, 1]
        out[i] = q @ R[n].T + t[n]
    return out

def parts(VV):
    ps = []
    for tid, ts, _ in M['groups']:
        P = np.array([VV[list(pi)] for pi, _ in ts]).reshape(-1, 3); Q = np.array([UV[list(ti)] for _, ti in ts]).reshape(-1, 2)
        F = np.arange(len(P)).reshape(-1, 3)
        n = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
        ps.append((P, Q, F, T[tid], np.repeat(n, 3, 0)))
    return ps

def draw(ps, angs, zm, yc, W=250, H=360, lab=''):
    ims = []
    for ang in angs:
        img = np.zeros((H, W, 3)) + [40, 42, 50]; zb = np.full((H, W), -1e9); sc = H / 1.6 * zm; oy = H / 2 + yc * sc
        Rv = raster.rotY(ang)
        for P, Q, F, t, Nn in ps: view.smooth_tex(img, zb, P, F, Q, t, Rv, sc, W / 2, oy, normals=Nn, weld_key=False)
        ims.append(Image.fromarray(img.clip(0, 255).astype(np.uint8)))
    o = Image.new('RGB', (W * len(ims), H + 20), (30, 30, 36))
    for i, im in enumerate(ims): o.paste(im, (W * i, 20))
    ImageDraw.Draw(o).text((6, 4), lab, fill=(230, 225, 220)); return o

T2 = fore((0, 1, 0), -150, ((0, 1, 0), 145), fwd=0, out=4, extra=hunch(1.5))['rot']
angs = (0, 0.6, 1.57, 3.14)
rows = [draw(parts(V), angs, 0.85, 0.75, lab='read back from the files: bind pose (T-pose on the lengthened skeleton)'),
        draw(parts(posed(T2)), angs, 1.0, 0.62, lab='posed as zt.c will: T2 arms, hunch, head forward'),
        draw(parts(posed(T2, 70, 1.6)), angs, 1.0, 0.62, lab='the scream: jaw node 8 turned 70 degrees and 1.6x wide')]
out = Image.new('RGB', (rows[0].width, sum(r.height for r in rows))); y = 0
for r in rows: out.paste(r, (0, y)); y += r.height
out.save(OUTP); print('saved', OUTP, 'vertices', len(V), 'nodes', sorted(set(bone.tolist())))
