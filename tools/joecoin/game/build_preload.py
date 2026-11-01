"""preload.arc.clz with '$' drawn into font.tpl (image 1, the Western font, glyph 0x80FD = a-umlaut).
The game reads font.tpl from preload.arc (loaded at boot), not the loose copy at the disc root.
usage: build_preload.py preload.arc.clz OUT.clz"""
import sys, os, struct, hashlib, numpy as np
H = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, H)
from clzlib import clz_decompress, clz_compress
import u8arc
def dollar(f):
    f = bytearray(f); n, tab = struct.unpack_from('>II', f, 4)
    ih = struct.unpack_from('>I', f, tab + 8)[0]; h, w, fmt, do = struct.unpack_from('>HHII', f, ih); assert (w, h, fmt) == (672, 112, 0)
    D = np.load(os.path.join(H, 'dollar16.npy')); r, c = divmod(0xFD, 42); x0, y0 = c * 16, r * 16; tx = w // 8
    for yy in range(16):
        for xx in range(16):
            x, y = x0 + xx, y0 + yy; v = int(D[yy, xx]) // 17
            p = do + ((y // 8) * tx + x // 8) * 32 + (y % 8) * 4 + (x % 8) // 2
            f[p] = (f[p] & 0x0F) | (v << 4) if x % 2 == 0 else (f[p] & 0xF0) | v
    return bytes(f)
def main(src, out):
    u = clz_decompress(open(src, 'rb').read()); a = u8arc.read(u); nm = u8arc.names(a); assert u8arc.build(a, {}) == u
    k = nm['font.tpl']; new = dollar(a['files'][k])
    u2 = u8arc.build(a, {k: new}); assert len(u2) == len(u)
    c = clz_compress(u2); assert clz_decompress(c) == u2
    open(out, 'wb').write(c); print('preload.arc.clz', len(c), hashlib.sha1(c).hexdigest()[:8])
if __name__ == '__main__': main(*sys.argv[1:3])
