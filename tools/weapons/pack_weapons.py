#!/usr/bin/env python3
"""Weapons phase 2: add the four weapon models to commonall.arc and draw their textures.
usage: pack_weapons.py commonall.arc.clz OUT_commonall.arc.clz
- real.gpl (in hand) gets models 27-30, symbol.gpl (rucksack / menus) models 196-199: 4 more table entries (8 bytes
  each = 0x20, so every model keeps its 0x20 alignment), the new models after the old ones, the names last.
- real.tpl images 0x1F / 0x20 / 0x1C / 0x1D and symbol.tpl 0xDB / 0xDC / 0xD8 / 0xD9 (used only by the old duplicate
  ids): new 32x64 / 64x64 CMPR textures appended to the .tpl, those image headers pointed at them.
- item rows: make_pm_dol.py points bytes +2 / +3 of 4E3 / 4E4 / 4EA / 4EB at the new models.
Every other file in the archive is checked byte for byte."""
import sys, os, struct, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gplmodel, weapon_models as W, tpltool
REAL_NEW, SYM_NEW = 27, 196
be = lambda b, o: struct.unpack_from('>I', b, o)[0]
# CLZ + U8 from the Z-target clip tool (same archive helpers)
_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ztarget', 'anim', 'add_player_clips.py')).read()
_g = {}; exec(_src.replace("if __name__ == '__main__':\n    main()", ''), _g)
clz_decompress, clz_compress, u8arc = _g['clz_decompress'], _g['clz_compress'], _g['u8arc']

def gpl_models(d):
    cnt, tb = be(d, 0xC), be(d, 0x10); ents = [struct.unpack_from('>II', d, tb + 8 * k) for k in range(cnt)]
    names0 = min(e[1] for e in ents); offs = sorted(set(e[0] for e in ents)) + [names0]
    return cnt, tb, ents, names0, {o: d[o:offs[offs.index(o) + 1]] for o in offs[:-1]}
def gpl_add(d, models, names, tail):
    """models: list of builder(base) -> bytes (base = file offset % 0x20 where it goes)"""
    cnt, tb, ents, names0, _ = gpl_models(d)
    assert tb == 0x14 and tb + 8 * cnt == min(e[0] for e in ents), 'table not right before the models'
    sh = 8 * len(models); assert sh % 0x20 == 0
    body = bytearray(d[tb + 8 * cnt:names0])            # old models, moved by sh
    new_off = []
    for mk in models:
        o = tb + 8 * (cnt + len(models)) + len(body); blob = mk(o % 0x20); assert len(blob) % 0x20 == 0
        new_off.append(o); body += blob
    namesb = d[names0:]; nmo = tb + 8 * (cnt + len(models)) + len(body)
    extra = b''; new_names = []
    for nm in names: new_names.append(nmo + len(namesb) + len(extra)); extra += nm.encode() + b'\0'
    total = namesb + extra
    out = bytearray(d[:tb]); struct.pack_into('>I', out, 0xC, cnt + len(models))
    delta_names = nmo - names0
    for o, no in ents: out += struct.pack('>II', o + sh, no + delta_names)
    for o, no in zip(new_off, new_names): out += struct.pack('>II', o, no)
    out += body + total; out += bytes((-len(out)) % 0x20)
    # checks: old models byte-identical at their new places, names intact
    for k, (o, no) in enumerate(ents):
        o2, no2 = struct.unpack_from('>II', out, tb + 8 * k); assert out[no2:].split(b'\0')[0] == d[no:].split(b'\0')[0]
    for o in sorted(set(e[0] for e in ents)): assert out[o + sh:o + sh + 0x40] == d[o:o + 0x40]
    assert bytes(out[tb + 8 * (cnt + len(models)):tb + 8 * (cnt + len(models)) + (names0 - tb - 8 * cnt)]) == d[tb + 8 * cnt:names0]
    return bytes(out)
def tpl_set(d, idx, img):
    """same size: in place; bigger: appended (0x20-aligned) and the image header pointed at it with the new size,
    as the $JOE coin's texture (the models' UVs are 0-1, so they scale)"""
    t = [x for x in tpltool.read(d) if x['i'] == idx][0]; assert t['fmt'] == 14, (idx, t)
    h, w = img.shape[:2]; data = W.enc_cmpr(img); assert len(data) == tpltool.size(14, w, h)
    out = bytearray(d)
    if (t['h'], t['w']) == (h, w): out[t['data']:t['data'] + len(data)] = data; return bytes(out)
    out += bytes((-len(out)) % 0x20); o = len(out); out += data
    struct.pack_into('>HHII', out, t['hdr'], h, w, 14, o); return bytes(out)
def symbolize(m, like):
    """real -> symbol space, as make_axe_symbol.py: (x,y,z)_sym = (-y,-x,-z)*0.907 + (6.3,4.3,2.1), turned 90 deg
    about the handle so the blade lies flat to the menu camera; long ones scaled to the hoe icon's length"""
    import copy
    ys = [p[1] for p in m.P]; k = 0.907 * min(1.0, 73.0 / (max(ys) - min(ys)))
    c = lambda v: max(-128, min(127, int(round(v))))
    P = [(c(-y * k + 6.3), c(-x * k + 4.3), c(-z * k + 2.1)) for x, y, z in m.P]
    N = [(-y, -x, -z) for x, y, z in m.N]
    y0, z0 = 4, 2
    P = [(x, c(y0 + (z - z0)), c(z0 - (y - y0))) for x, y, z in P]; N = [(x, z, -y) for x, y, z in N]
    s = copy.copy(m); s.P = P; s.N = N; return s
def main():
    if len(sys.argv) != 3: sys.exit(__doc__)
    raw = open(sys.argv[1], 'rb').read(); u = clz_decompress(raw); arc = u8arc.read(u); nm = u8arc.names(arc)
    real, sym, rtpl, stpl = (arc['files'][nm[f]] for f in ('real.gpl', 'symbol.gpl', 'real.tpl', 'symbol.tpl'))
    assert be(real, 0xC) == REAL_NEW and be(sym, 0xC) == SYM_NEW, 'not the expected real.gpl / symbol.gpl (already packed?)'
    _, _, rents, _, rmods = gpl_models(real); _, _, sents, _, smods = gpl_models(sym)
    like_r = gplmodel.parse(rmods[rents[15][0]])           # kuwa1: colour / normal headers
    like_s = gplmodel.parse(smods[sents[122][0]])          # ono
    rm, sm, rn, sn = [], [], [], []
    for wid, name, f, style, rt, st in W.WEAPONS:
        m = f(); sy = symbolize(f(), like_s)
        rm.append(lambda base, m=m, rt=rt: m.gpl(rt, like_r, base))
        sm.append(lambda base, sy=sy, st=st: sy.gpl(st, like_s, base, b'symbol.tpl\0\0'))
        tag = {0x4E3: 'stick', 0x4E4: 'ken_w', 0x4EA: 'ken_f', 0x4EB: 'ken_m'}[wid]; rn.append(tag); sn.append(tag)
    real2 = gpl_add(real, rm, rn, b''); sym2 = gpl_add(sym, sm, sn, b'')
    for wid, name, f, style, rt, st in W.WEAPONS:
        img = W.texture(style)
        rtpl = tpl_set(rtpl, rt, img); stpl = tpl_set(stpl, st, img)
    rep = {nm['real.gpl']: real2, nm['symbol.gpl']: sym2, nm['real.tpl']: rtpl, nm['symbol.tpl']: stpl}
    nu = u8arc.build(arc, rep); b = u8arc.read(nu); bn = u8arc.names(b)
    for n, j in nm.items():
        assert b['files'][bn[n]] == (rep[j] if j in rep else arc['files'][j]), n
    for k, (wid, *_r) in enumerate(W.WEAPONS):                # the new models parse back
        for g, base in ((real2, REAL_NEW), (sym2, SYM_NEW)):
            cnt, tb, ents, n0, mods = gpl_models(g); gplmodel.parse(mods[ents[base + k][0]])
    c = clz_compress(nu); assert clz_decompress(c) == nu
    open(sys.argv[2], 'wb').write(c)
    print('real.gpl %d -> %d, symbol.gpl %d -> %d, arc %d -> %d, clz %d, sha1 %s' % (len(real), len(real2), len(sym), len(sym2),
          len(u), len(nu), len(c), hashlib.sha1(c).hexdigest()[:8]))
if __name__ == '__main__': main()
