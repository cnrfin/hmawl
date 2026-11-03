#!/usr/bin/env python3
"""Free memory: empty files that a chapter never uses from its chapter archive (mainchapterN.arc.clz).
The chapter archive is unpacked whole into the bottom of the game's memory and kept for the whole chapter
(pool A, findings 7.43); every byte removed from it widens the gap to the general pool 1:1.
Default: chapter 1 (mainchapter0) without the son's animations (son_0.anm.arc 384 KB + subact/subanm:
392 KB) - the son is born at the start of chapter 2 - and Grant (gura), Kate (keit) and Samantha (san),
who move in in chapter 2 (414 KB). (Dr. Hardy, pado, is in the valley from the start: kept.) The files stay in the archive's directory, empty.
Their MODELS cannot be emptied: the game opens every chapter character's model when a save loads (memfix 12:
empty gura/keit/san_0.arc -> invalid read from 0 on load, crash entering the mansion). --put replaces a file
with a small placeholder model (tools/goddess/scripts/build_stub.py NAME OUTDIR, 16 KB).
usage: strip_chapter.py GAME.iso OUTDIR [--chapter 0] [--drop a,b,...] [--put name=file,...]
Writes OUTDIR/mainchapterN.arc.clz; put it on the disc with gcbuild.py --replace mainchapterN.arc.clz=..."""
import sys, os, struct

def clz_decompress(c):
    assert c[:4] == b'CLZ\0'; n = struct.unpack_from('>I', c, 4)[0]; out = bytearray(); i = 0x10
    while len(out) < n:
        f = c[i]; i += 1
        for k in range(8):
            if len(out) >= n: break
            if f >> k & 1:
                b0, b1 = c[i], c[i + 1]; i += 2
                d = 0x1000 - (b0 | (b1 & 0xF0) << 4); l = (b1 & 0xF) + 3
                for _ in range(l): out.append(out[-d])
            else: out.append(c[i]); i += 1
    return bytes(out)

def clz_compress(b):
    """greedy-with-lookahead LZSS (4 KB window, length 3..18), hash chains"""
    n = len(b); W = 0x1000; out = bytearray(b'CLZ\0' + struct.pack('>III', n, 0, n)); heads = {}; prev = [0] * n
    def best(i):
        if i + 3 > n: return 0, 0
        j = heads.get(b[i:i + 3], -1); bl, bd, tries = 0, 0, 0
        while j >= 0 and i - j <= W and tries < 48:
            l = 0
            while l < 18 and i + l < n and b[j + l] == b[i + l]: l += 1
            if l > bl: bl, bd = l, i - j
            if l == 18: break
            j = prev[j]; tries += 1
        return bl, bd
    def add(i):
        if i + 3 <= n:
            k = b[i:i + 3]; prev[i] = heads.get(k, -1); heads[k] = i
    i = 0
    while i < n:
        fpos = len(out); out.append(0); f = 0
        for k in range(8):
            if i >= n: break
            l, d = best(i)
            if l >= 3 and i + 1 < n:
                add(i); l2, _ = best(i + 1)
                if l2 > l + 1: l = 0
                prev_added = True
            else: prev_added = False
            if l >= 3:
                v = 0x1000 - d; out += bytes([v & 0xFF, ((v >> 4) & 0xF0) | (l - 3)]); f |= 1 << k
                for q in range(i + (1 if prev_added else 0), i + l): add(q)
                i += l
            else:
                if not prev_added: add(i)
                out.append(b[i]); i += 1
        out[fpos] = f
    return bytes(out)

def u8_read(d):
    assert d[:4] == b'U\xaa8-'
    root, hs, ds = struct.unpack_from('>III', d, 4); n = struct.unpack_from('>I', d, root + 8)[0]
    nodes = [list(struct.unpack_from('>III', d, root + 12 * k)) for k in range(n)]
    strtab = d[root + 12 * n:root + hs]
    files = {k: d[o:o + s] for k, (w0, o, s) in enumerate(nodes) if not w0 >> 24}
    name = lambda k: strtab[nodes[k][0] & 0xFFFFFF:strtab.index(b'\0', nodes[k][0] & 0xFFFFFF)].decode('latin1')
    return dict(head=d[:ds], root=root, ds=ds, nodes=nodes, files=files, name=name, n=n)
def u8_names(a):
    return {a['name'](k): k for k in a['files']}
def u8_build(a, replace):
    """replace: {node index: new bytes}"""
    out = bytearray(a['head']); nodes = [list(x) for x in a['nodes']]
    order = sorted(a['files'], key=lambda k: a['nodes'][k][1])          # original data order
    for k in order:
        data = replace.get(k, a['files'][k])
        out += bytes((-len(out)) % 0x20)
        nodes[k][1] = len(out); nodes[k][2] = len(data); out += data
    for k, w in enumerate(nodes): struct.pack_into('>III', out, a['root'] + 12 * k, *w)
    return bytes(out)


def iso_file(iso, path):
    with open(iso, 'rb') as f:
        h = f.read(0x440); fst_off, fst_size = struct.unpack_from('>II', h, 0x424)
        f.seek(fst_off); fst = f.read(fst_size)
        n = struct.unpack_from('>I', fst, 8)[0]; st = 12 * n
        name = lambda i: fst[st + (struct.unpack_from('>I', fst, 12 * i)[0] & 0xFFFFFF):].split(b'\0')[0].decode('latin1')
        for i in range(1, n):
            w0, off, sz = struct.unpack_from('>III', fst, 12 * i)
            if not (w0 >> 24) and name(i).lower() == path.lower():
                f.seek(off); return f.read(sz)
    sys.exit('%s not found on the disc' % path)

# An animation archive with no animations, as on the original disc (pado_0.anm.arc, tei_0.anm.arc: 64 bytes):
# a U8 header, the root node, an empty name. A 0-byte .anm.arc for a character whose model is opened crashes
# the load (memfix 13: invalid read from 0x14 at 0x801A40B4). Never empty a subact / subanm that is not already
# empty on the disc (memfix 14: Grant's 644 / 192 B ones emptied -> invalid read at 0x801A0AF4 on load: the game
# indexes them at load; func_801A0A88 returns the raw pointer when the file is not a U8 archive).
# Nor the animations of a character whose model is opened: the load asks for animation n (func_801A0A88(arc, 0, n)
# -> func_8019FE08); with no such file it returns stack garbage (memfix 15 dump: anim player +0x10 = 0x01F110A8)
# and func_801A0AF4 reads through it. So Grant / Kate / Samantha keep their (small) original animations.
EMPTY_U8 = struct.pack('>IIII', 0x55AA382D, 0x20, 13, 0x40) + bytes(0x10) + struct.pack(">III", 0x01000000, 0, 1) + bytes(0x14)
assert len(EMPTY_U8) == 64

def main():
    a = sys.argv[1:]; ch = 0; drop = 'son_0.anm.arc,son_0_subact.arc,son_0_subanm.arc,keit_0_subact.arc,keit_0_subanm.arc,san_0_subact.arc,san_0_subanm.arc'
    if '--chapter' in a: i = a.index('--chapter'); ch = int(a[i + 1]); del a[i:i + 2]
    if '--drop' in a: i = a.index('--drop'); drop = a[i + 1]; del a[i:i + 2]
    put = {}
    if '--put' in a:
        i = a.index('--put')
        for x in a[i + 1].split(','): n_, f_ = x.split('=', 1); put[n_] = open(f_, 'rb').read()
        del a[i:i + 2]
    iso, out = a
    nm = 'mainchapter%d.arc.clz' % ch
    c = iso_file(iso, nm); u = clz_decompress(c); arc = u8_read(u); names = u8_names(arc)
    rep = {}; freed = 0
    for f in drop.split(','):
        if f not in names: sys.exit('%s: no %s' % (nm, f))
        k = names[f]
        if not arc['files'][k]: continue                  # already empty (e.g. the son on an earlier stripped disc): as is
        rep[k] = EMPTY_U8 if f.endswith('.anm.arc') else b''
        freed += len(arc['files'][k]) - len(rep[k])
    for f, data in put.items():
        if f not in names: sys.exit('%s: no %s' % (nm, f))
        rep[names[f]] = data
    nu = u8_build(arc, rep); back = u8_read(nu)
    for f, k in names.items():
        if k not in rep: assert back['files'][k] == arc['files'][k], f
    cc = clz_compress(nu); assert clz_decompress(cc) == nu
    os.makedirs(out, exist_ok=True); open(os.path.join(out, nm), 'wb').write(cc)
    print('%s: %d -> %d bytes unpacked (%d KB freed), %d bytes packed' % (nm, len(u), len(nu), (len(u) - len(nu)) // 1024, len(cc)))

if __name__ == '__main__':
    main()
