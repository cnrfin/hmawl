#!/usr/bin/env python3
"""Add the Z-targeting player clips to boy_0.anm.arc inside a mainchapterN.arc.clz (the always-loaded archive
with every character's model and animations; the farmer's 126 clips are shared by all his chapter models).
usage: add_player_clips.py mainchapterN.arc.clz OUT.arc.clz [anm126.bin ... anm131.bin]
Clips 126 strafe left, 127 strafe right, 128 walk back, 129-131 combo hits 1-3 (zt.c CLIP_* / SW_CLIP). Every other file keeps its bytes and
order; run again on its own output and the three are replaced, not added twice."""
import sys, os, struct, hashlib, types
# bundled (no other files needed): CLZ from hmawl tools/logs/build_log_archives.py, U8 from u8arc.py
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


u8arc = types.ModuleType('u8arc')
exec(compile('"""Flat/nested U8 archive read and rebuild (same node order and names; data re-laid 0x20-aligned\nfrom the original data start, as the game\'s own archives are)."""\nimport struct\ndef read(d):\n    assert d[:4] == b\'U\\xaa8-\'\n    root, hs, ds = struct.unpack_from(\'>III\', d, 4); n = struct.unpack_from(\'>I\', d, root + 8)[0]\n    nodes = [list(struct.unpack_from(\'>III\', d, root + 12 * k)) for k in range(n)]\n    strtab = d[root + 12 * n:root + hs]\n    files = {k: d[o:o + s] for k, (w0, o, s) in enumerate(nodes) if not w0 >> 24}\n    name = lambda k: strtab[nodes[k][0] & 0xFFFFFF:strtab.index(b\'\\0\', nodes[k][0] & 0xFFFFFF)].decode(\'latin1\')\n    return dict(head=d[:ds], root=root, ds=ds, nodes=nodes, files=files, name=name, n=n)\ndef names(a):\n    return {a[\'name\'](k): k for k in a[\'files\']}\ndef build(a, replace):\n    """replace: {node index: new bytes}"""\n    out = bytearray(a[\'head\']); nodes = [list(x) for x in a[\'nodes\']]\n    order = sorted(a[\'files\'], key=lambda k: a[\'nodes\'][k][1])          # original data order\n    for k in order:\n        data = replace.get(k, a[\'files\'][k])\n        out += bytes((-len(out)) % 0x20)\n        nodes[k][1] = len(out); nodes[k][2] = len(data); out += data\n    for k, w in enumerate(nodes): struct.pack_into(\'>III\', out, a[\'root\'] + 12 * k, *w)\n    return bytes(out)\n', 'u8arc', 'exec'), u8arc.__dict__)
al = lambda b, a: b + bytes((-len(b)) % a)

def u8(files):
    names = b'\0' + b''.join(n.encode() + b'\0' for n, _ in files)
    nn = len(files) + 1; hdr_size = 12 * nn + len(names)
    data_off = (0x20 + hdr_size + 0x1F) & ~0x1F
    nodes = [struct.pack('>III', 0x01000000, 0, nn)]; blob = b''; no = 1
    for n, d in files:
        nodes.append(struct.pack('>III', no, data_off + len(blob), len(d))); no += len(n) + 1
        blob += al(d, 0x20)
    head = struct.pack('>IIII', 0x55AA382D, 0x20, hdr_size, data_off) + bytes(0x10)
    out = head + b''.join(nodes) + names
    return out + bytes(data_off - len(out)) + blob


CLIPS = 126
NEW = 6                                     # our clips 126..131 (replaced, not added twice, on a re-run)

def main():
    a = sys.argv[1:]
    if len(a) not in (2, 2 + NEW): sys.exit(__doc__)
    here = os.path.dirname(os.path.abspath(__file__))
    clips = [open(p, 'rb').read() for p in (a[2:] if len(a) > 2 else [os.path.join(here, 'anm%d.bin' % k) for k in range(126, 126 + NEW)])]
    d = clz_decompress(open(a[0], 'rb').read()); arc = u8arc.read(d); nm = u8arc.names(arc)
    if 'boy_0.anm.arc' not in nm:
        open(a[1], 'wb').write(open(a[0], 'rb').read()); print('%s: no boy_0.anm.arc, copied unchanged' % os.path.basename(a[0])); return
    k = nm['boy_0.anm.arc']; inner = arc['files'][k]
    ia = u8arc.read(inner); order = sorted(ia['files'], key=lambda j: ia['nodes'][j][1])
    files = [('@', ia['files'][j]) for j in order]
    assert CLIPS <= len(files) <= CLIPS + NEW, 'boy_0.anm.arc has %d clips (expected 126..%d)' % (len(files), CLIPS + NEW)
    files = files[:CLIPS] + [('@', c) for c in clips]
    nu_inner = u8(files); ib = u8arc.read(nu_inner)
    assert [ib['files'][j] for j in sorted(ib['files'], key=lambda j: ib['nodes'][j][1])] == [f for _, f in files]
    nu = u8arc.build(arc, {k: nu_inner}); b = u8arc.read(nu); bn = u8arc.names(b)
    for n, j in nm.items(): assert n == 'boy_0.anm.arc' or b['files'][bn[n]] == arc['files'][j], n
    c = clz_compress(nu); assert clz_decompress(c) == nu
    open(a[1], 'wb').write(c)
    print('%s: boy_0.anm.arc %d -> %d clips (%d -> %d bytes), archive %d packed, sha1 %s'
          % (os.path.basename(a[0]), len(order), len(files), len(inner), len(nu_inner), len(c), hashlib.sha1(c).hexdigest()[:12]))

if __name__ == '__main__':
    main()
