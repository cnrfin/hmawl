"""$JOE TV data: tv-console2.tpl + 7 screens (images 14-20, CMPR 192x144) and font.tpl with '$' at 0x80FD.
usage: build_tvdata.py TV_TPL FONT_TPL SCREENS_DIR OUTDIR"""
import sys, os, struct, numpy as np
from PIL import Image
sys.path.insert(0, '/home/user/hmawl-goddess/tools/joecoin'); import cmpr
SCREENS = ['were-joe-back', 'its-so-joever', 'joe-doing-something', 'HODL', 'crab-market', 'crypto-winter', 'joe-in-town']
al = lambda n, a=32: (n + a - 1) // a * a
def tpl_read(t):
    magic, n, tab = struct.unpack_from('>III', t, 0); assert magic == 0x0020AF30
    out = []
    for i in range(n):
        ih, ph = struct.unpack_from('>II', t, tab + 8 * i); assert ph == 0
        hdr = bytearray(t[ih:ih + 0x24]); h, w, fmt, do = struct.unpack_from('>HHII', hdr, 0)
        size = {14: w * h // 2, 0: w * h // 2, 5: w * h * 2}[fmt] if fmt in (0, 5, 14) else None
        # size from the next data start for safety
        out.append([hdr, do])
    starts = sorted(set(o for _, o in out)) + [len(t)]
    return [(hdr, t[do:starts[starts.index(do) + 1]]) for hdr, do in out]
def tpl_write(imgs):
    n = len(imgs); tab = 0xC; hdrs = al(tab + 8 * n, 4); data0 = al(hdrs + 0x24 * n)
    out = bytearray(struct.pack('>III', 0x0020AF30, n, tab)); body = bytearray(); pos = data0
    for i, (hdr, data) in enumerate(imgs):
        out += struct.pack('>II', hdrs + 0x24 * i, 0)
    out += bytes(hdrs - len(out))
    for hdr, data in imgs:
        h2 = bytearray(hdr); struct.pack_into('>I', h2, 8, pos); out += h2
        body += data + bytes(al(len(data)) - len(data)); pos += al(len(data))
    out += bytes(data0 - len(out)); return bytes(out + body)
def main(tv, font, sdir, od):
    t = open(tv, 'rb').read(); imgs = tpl_read(t); assert len(imgs) == 14
    assert tpl_write(imgs) == t, 'tpl round trip'
    hdr6 = imgs[6][0]
    for nm in SCREENS:
        im = Image.open(os.path.join(sdir, nm + '.png')).convert('RGB')
        if im.size != (192, 144): im = im.resize((192, 144), Image.LANCZOS)
        imgs.append((hdr6, cmpr.encode(im)))
    # image 9 (320x248 CMPR) holds the singer's animation pieces (light streaks, arm, mic) that are
    # pasted over channel 3's picture: make them transparent (x 128-319 for y 0-63, x 152-319 for y 64-79)
    hdr9, d9 = imgs[9]; h9, w9, f9 = struct.unpack_from('>HHI', hdr9, 0); assert (w9, h9, f9) == (320, 248, 14)
    d9 = bytearray(d9); tw = w9 // 8
    for by in range(0, 80, 4):
        for bx in range(152 if by >= 64 else 128, 320, 4):
            tile = (by // 8) * tw + bx // 8; sub = ((by % 8) // 4) * 2 + (bx % 8) // 4
            struct.pack_into('>HHI', d9, (tile * 4 + sub) * 8, 0x0000, 0xFFFF, 0xFFFFFFFF)
    imgs[9] = (hdr9, bytes(d9))
    new = tpl_write(imgs); open(os.path.join(od, 'tv-console2.tpl'), 'wb').write(new)
    chk = tpl_read(new); assert len(chk) == 21 and all(chk[i][1][:len(imgs[i][1])] == imgs[i][1] for i in range(21))
    print('tv-console2.tpl', len(t), '->', len(new))
    # font: '$' into glyph 0x80FD (image 0, I4 1008x648, 42 glyphs of 24x24 per row)
    f = bytearray(open(font, 'rb').read()); n, tab = struct.unpack_from('>II', f, 4)
    ih = struct.unpack_from('>I', f, tab)[0]; h, w, fmt, do = struct.unpack_from('>HHII', f, ih); assert (w, h, fmt) == (1008, 648, 0)
    D = np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dollar.npy'))
    r, c = divmod(0xFD, 42); x0, y0 = c * 24, r * 24
    tiles_x = w // 8
    for yy in range(24):
        for xx in range(24):
            x, y = x0 + xx, y0 + yy; v = int(D[yy, xx]) // 17
            tile = (y // 8) * tiles_x + x // 8; p = do + tile * 32 + (y % 8) * 4 + (x % 8) // 2
            f[p] = (f[p] & 0x0F) | (v << 4) if x % 2 == 0 else (f[p] & 0xF0) | v
    # the US game draws text with image 1 (the Western font, 672x112, 42 cells of 16x16 per row, same
    # code order): 0x80FD there is 'a-umlaut', unused in the US text
    ih = struct.unpack_from('>I', f, tab + 8)[0]; h, w, fmt, do = struct.unpack_from('>HHII', f, ih); assert (w, h, fmt) == (672, 112, 0)
    D = np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dollar16.npy'))
    r, c = divmod(0xFD, 42); x0, y0 = c * 16, r * 16; tiles_x = w // 8
    for yy in range(16):
        for xx in range(16):
            x, y = x0 + xx, y0 + yy; v = int(D[yy, xx]) // 17
            tile = (y // 8) * tiles_x + x // 8; p = do + tile * 32 + (y % 8) * 4 + (x % 8) // 2
            f[p] = (f[p] & 0x0F) | (v << 4) if x % 2 == 0 else (f[p] & 0xF0) | v
    open(os.path.join(od, 'font.tpl'), 'wb').write(f); print('font.tpl', len(f), 'glyph 0x80FD = $ (both fonts)')
if __name__ == '__main__': main(*sys.argv[1:5])
