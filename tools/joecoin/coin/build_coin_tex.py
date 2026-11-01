"""commonall.arc.clz: symbol.tpl image 30 (the Coin's own 32x64 texture: front, back, rim) -> the $JOE coin.
usage: build_coin_tex.py commonall.arc.clz coin_tex.png OUT.clz"""
import sys, os, struct, hashlib
H = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [H, '/home/user/hmawl/tools/logs', '/home/user/hmawl-goddess/tools/joecoin']
import u8arc, cmpr
from build_log_archives import clz_decompress, clz_compress
from PIL import Image
src, png, out = sys.argv[1:4]
c = open(src, 'rb').read(); u = clz_decompress(c); a = u8arc.read(u); nm = u8arc.names(a)
k = nm['symbol.tpl']; t = bytearray(a['files'][k])
io, _ = struct.unpack_from('>II', t, 12 + 8 * 30); h, w, f, do = struct.unpack_from('>HHII', t, io); assert (w, h, f) == (32, 64, 14)
b = cmpr.encode(Image.open(png).convert('RGB')); assert len(b) == 1024
t[do:do + 1024] = b
u2 = u8arc.build(a, {k: bytes(t)}); b2 = u8arc.read(u2)
for j in a['files']:
    if j != k: assert b2['files'][j] == a['files'][j]
c2 = clz_compress(u2); assert clz_decompress(c2) == u2
open(out, 'wb').write(c2); print('commonall.arc.clz', len(c), '->', len(c2), hashlib.sha1(c2).hexdigest()[:8])
