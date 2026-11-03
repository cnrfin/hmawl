"""GameCube TPL read (decode to RGBA numpy) and write (append/replace images, RGB5A3 or CMPR).
TPL: magic 0020AF30, u32 count, u32 table offset (0xC); table entries {u32 image hdr, u32 palette hdr};
image hdr {u16 h, u16 w, u32 fmt, u32 data, wrapS, wrapT, minF, magF, f32 lodBias, u8 edgeLod, minLod, maxLod, 0}."""
import struct, numpy as np
BLK = {0: (8, 8, 4), 1: (8, 4, 8), 2: (8, 8, 4), 3: (4, 4, 16), 4: (4, 4, 16), 5: (4, 4, 16), 6: (4, 4, 32), 14: (8, 8, 4)}

def read(d):
    assert struct.unpack_from('>I', d, 0)[0] == 0x0020AF30
    n, to = struct.unpack_from('>II', d, 4)
    out = []
    for i in range(n):
        ih, ph = struct.unpack_from('>II', d, to + 8 * i)
        h, w, fmt, data = struct.unpack_from('>HHII', d, ih)
        out.append(dict(i=i, hdr=ih, pal=ph, w=w, h=h, fmt=fmt, data=data, rest=d[ih + 12:ih + 0x24]))
    return out

def size(fmt, w, h):
    bw, bh, bpp = BLK[fmt]
    return ((w + bw - 1) // bw) * ((h + bh - 1) // bh) * bw * bh * bpp // 8

def c5a3(v):
    if v & 0x8000:
        return ((v >> 10 & 31) * 255 // 31, (v >> 5 & 31) * 255 // 31, (v & 31) * 255 // 31, 255)
    return ((v >> 8 & 15) * 17, (v >> 4 & 15) * 17, (v & 15) * 17, (v >> 12 & 7) * 255 // 7)

def c565(v):
    return ((v >> 11 & 31) * 255 // 31, (v >> 5 & 63) * 255 // 63, (v & 31) * 255 // 31)

def decode(d, t):
    w, h, fmt, o = t['w'], t['h'], t['fmt'], t['data']
    bw, bh, bpp = BLK[fmt]
    W = (w + bw - 1) // bw * bw; H = (h + bh - 1) // bh * bh
    img = np.zeros((H, W, 4), np.uint8)
    if fmt == 14:
        for by in range(0, H, 8):
            for bx in range(0, W, 8):
                for sy in (0, 4):
                    for sx in (0, 4):
                        c0, c1, bits = struct.unpack_from('>HHI', d, o); o += 8
                        a, b = c565(c0), c565(c1)
                        if c0 > c1:
                            pal = [a + (255,), b + (255,), tuple((2 * x + y) // 3 for x, y in zip(a, b)) + (255,),
                                   tuple((x + 2 * y) // 3 for x, y in zip(a, b)) + (255,)]
                        else:
                            pal = [a + (255,), b + (255,), tuple((x + y) // 2 for x, y in zip(a, b)) + (255,), (0, 0, 0, 0)]
                        for k in range(16):
                            img[by + sy + k // 4, bx + sx + k % 4] = pal[bits >> (30 - 2 * k) & 3]
        return img[:h, :w]
    for by in range(0, H, bh):
        for bx in range(0, W, bw):
            if fmt == 6:
                ar = d[o:o + 32]; gb = d[o + 32:o + 64]; o += 64
                for k in range(16):
                    img[by + k // 4, bx + k % 4] = (ar[2 * k + 1], gb[2 * k], gb[2 * k + 1], ar[2 * k])
                continue
            for k in range(bw * bh):
                y, x = by + k // bw, bx + k % bw
                if fmt == 5:
                    img[y, x] = c5a3(struct.unpack_from('>H', d, o)[0]); o += 2
                elif fmt == 4:
                    img[y, x] = c565(struct.unpack_from('>H', d, o)[0]) + (255,); o += 2
                elif fmt == 3:
                    a, i = d[o], d[o + 1]; img[y, x] = (i, i, i, a); o += 2
                elif fmt == 1:
                    i = d[o]; img[y, x] = (i, i, i, 255); o += 1
                elif fmt == 2:
                    v = d[o]; o += 1; i = (v & 15) * 17; img[y, x] = (i, i, i, (v >> 4) * 17)
                elif fmt == 0:
                    v = d[o + k // 2]; i = ((v >> 4) if k % 2 == 0 else (v & 15)) * 17; img[y, x] = (i, i, i, 255)
            if fmt == 0: o += 32
    return img[:h, :w]

def enc_rgb5a3(img):
    h, w = img.shape[:2]; out = bytearray()
    for by in range(0, h, 4):
        for bx in range(0, w, 4):
            for k in range(16):
                r, g, b, a = [int(v) for v in img[by + k // 4, bx + k % 4]]
                v = 0x8000 | (r >> 3) << 10 | (g >> 3) << 5 | (b >> 3) if a >= 0xE0 else (a >> 5) << 12 | (r >> 4) << 8 | (g >> 4) << 4 | (b >> 4)
                out += struct.pack('>H', v)
    return bytes(out)

def append(d, img, fmt=5, like=None):
    """Return a new TPL with img appended (RGB5A3); the existing image data stays where it is."""
    texs = read(d); n = len(texs)
    to = struct.unpack_from('>I', d, 8)[0]
    h, w = img.shape[:2]
    data = enc_rgb5a3(img)
    # new layout: header + table (n+1) + headers + old data (shifted) + new data
    old_hdr_lo = min(t['hdr'] for t in texs)
    old_data_lo = min(t['data'] for t in texs)
    head = 0xC + 8 * (n + 1)
    hdrs = [d[t['hdr']:t['hdr'] + 0x24] for t in texs]
    rest = like['rest'] if like else texs[-1]['rest']
    hdrs.append(struct.pack('>HHII', h, w, fmt, 0) + rest)
    hdr_base = (head + 0x1F) & ~0x1F
    data_base = (hdr_base + 0x24 * (n + 1) + 0x1F) & ~0x1F
    shift = data_base - old_data_lo
    out = bytearray(struct.pack('>III', 0x0020AF30, n + 1, 0xC))
    for i in range(n + 1): out += struct.pack('>II', hdr_base + 0x24 * i, 0)
    out += bytes(hdr_base - len(out))
    for i, hd in enumerate(hdrs):
        hd = bytearray(hd)
        if i < n: struct.pack_into('>I', hd, 8, texs[i]['data'] + shift)
        out += hd
    out += bytes(data_base - len(out))
    out += d[old_data_lo:]
    out += bytes((-len(out)) % 0x20)
    struct.pack_into('>I', out, hdr_base + 0x24 * n + 8, len(out))
    out += data
    return bytes(out), n
