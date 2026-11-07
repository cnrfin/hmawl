#!/usr/bin/env python3
"""gq5: the goddess's disc files under their own names (gd/ now holds Joe): hg/hg_0.arc = build/gd_0.arc with every
'gd_0' renamed 'hg_0' (same length: the archive's file names and the two name strings inside her act / gpl, nothing
else contains it), hg/hg_0.anm.arc = build/gd_0.anm.arc unchanged.
gq8: --jiggle takes build_jiggle/ (jiggle test 6: 49 nodes, node 21 folded into 22 and reused as the bust bone).
fm1/fm2: --slim takes build_slim/ (build_jiggle + slim_face.py: rounder, narrower jaw to a small chin point, green brows, teal eyeshadow).
usage: make_hg.py OUTDIR [--jiggle | --slim]   (writes OUTDIR/hg_0.arc, OUTDIR/hg_0.anm.arc; install with gcbuild --add-dir hg=OUTDIR)"""
import sys, os, hashlib
B = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build_slim' if '--slim' in sys.argv else 'build_jiggle' if '--jiggle' in sys.argv else 'build')
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
m = open(os.path.join(B, 'gd_0.arc'), 'rb').read()
assert m.count(b'gd_0') == 8, m.count(b'gd_0')
m = m.replace(b'gd_0', b'hg_0')
a = open(os.path.join(B, 'gd_0.anm.arc'), 'rb').read()
for n, d in (('hg_0.arc', m), ('hg_0.anm.arc', a)):
    open(os.path.join(out, n), 'wb').write(d); print(n, len(d), hashlib.sha1(d).hexdigest()[:8])
