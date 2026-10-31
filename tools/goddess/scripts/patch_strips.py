s=open('build_goddess.py').read()
old_dl=s[s.index('def dl(trilist):'):s.index('def build_gpl():')]
new_dl='''def strips(trilist):
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
'''
s=s.replace(old_dl,new_dl)
a="    f0e, f0m = pm['files'][pn['pm_0_f0_e.tpl']], pm['files'][pn['pm_0_f0_m.tpl']]   # face frames (her face is painted)"
assert a in s
s=s.replace(a,'''    def blank_frames(t):          # same frame count, every frame 1x1 transparent: her face is painted and her
        n_ = struct.unpack_from('>I', t, 4)[0]          # gpl never draws the eye/mouth materials (sel 00/01)
        return tpl([Image.new('RGBA', (1, 1), (0, 0, 0, 0))] * n_)
    f0e = blank_frames(pm['files'][pn['pm_0_f0_e.tpl']]); f0m = blank_frames(pm['files'][pn['pm_0_f0_m.tpl']])
    check_strips(tris[0]); check_strips(tris[1])''')
b="    print(NAME + '.arc', len(arc), NAME + '.anm.arc', len(anm))"
assert b in s
s=s.replace(b,'''    print(NAME + '.arc', len(arc), NAME + '.anm.arc', len(anm))
    # archives over 64 KB loaded into slot 37 overlapped the game's scratch matrix buffer (tests 1b-3:
    # garbled texture, then a crash); the teddy (62,976) and the Postman (63,328) load fine
    assert len(arc) < 62976, 'larger than the teddy dar_0.arc (62,976 B)\'''')
open('build_goddess.py','w').write(s)
