"""Weapon models (weapons phase 2): geometry + textures for the in-hand (real.gpl) and menu (symbol.gpl) models.
Units are real.gpl's: s8 with 6 fraction bits (1 = 1/64), the hand grip at the origin, handle along +y, the
striking edge toward +z (where the hoe and sickle blades point). Textures are drawn into the four real.tpl /
symbol.tpl images only the old duplicate ids used (16x32 or 32x16 CMPR), in place."""
import math, struct, numpy as np
import gplmodel

class Mesh:
    def __init__(s): s.P = []; s.N = []; s.UV = []; s.faces = []
    def vid(s, p):
        p = tuple(int(round(c)) for c in p)
        assert all(-128 <= c <= 127 for c in p), p
        if p not in s.P: s.P.append(p)
        return s.P.index(p)
    def nid(s, n):
        l = math.sqrt(sum(c * c for c in n)) or 1; q = tuple(int(round(64 * c / l)) for c in n)
        if q not in s.N: s.N.append(q)
        return s.N.index(q)
    def uid(s, u, v):
        q = (max(0, min(255, int(round(u * 128)))), max(0, min(255, int(round(v * 128)))))
        if q not in s.UV: s.UV.append(q)
        return s.UV.index(q)
    def face(s, pts, uvs, center):
        a, b, c = pts[0], pts[1], pts[2]
        u = [b[i] - a[i] for i in range(3)]; w = [c[i] - a[i] for i in range(3)]
        n = [u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0]]
        if math.sqrt(sum(x * x for x in n)) < 1e-6: return
        fc = [sum(p[i] for p in pts) / len(pts) for i in range(3)]
        out = [fc[i] - center[i] for i in range(3)]
        if sum(n[i] * out[i] for i in range(3)) > 0:       # game convention: clockwise from outside
            pts = pts[::-1]; uvs = uvs[::-1]; n = [-x for x in n]
        ni = s.nid([-x for x in n])
        s.faces.append([(s.vid(p), ni, s.uid(*t)) for p, t in zip(pts, uvs)])
    def loft(s, secs, cap0=True, cap1=True):
        """secs: list of (y, [(x, z, u)...], v) rings with the same point count; side quads + end caps"""
        for i in range(len(secs) - 1):
            ya, ra, va = secs[i]; yb, rb, vb = secs[i + 1]; n = len(ra)
            cy = (ya + yb) / 2; cx = sum(p[0] for p in ra + rb) / (2 * n); cz = sum(p[1] for p in ra + rb) / (2 * n)
            for k in range(n):
                a0, a1, b0, b1 = ra[k], ra[(k + 1) % n], rb[k], rb[(k + 1) % n]
                s.face([(a0[0], ya, a0[1]), (a1[0], ya, a1[1]), (b1[0], yb, b1[1]), (b0[0], yb, b0[1])],
                       [(a0[2], va), (a1[2], va), (b1[2], vb), (b0[2], vb)], (cx, cy, cz))
        for (y, r, v), on, d in ((secs[0], cap0, -1), (secs[-1], cap1, 1)):
            if not on: continue
            cx = sum(p[0] for p in r) / len(r); cz = sum(p[1] for p in r) / len(r)
            if len(set((round(p[0]), round(p[1])) for p in r)) < 3: continue
            s.face([(p[0], y, p[1]) for p in r], [(p[2], v) for p in r], (cx, y - d * 5, cz))
    def gpl(s, tex, like, base, tail=b'real.tpl\0\0\0\0'):
        tris = [f for f in s.faces if len(f) == 3]; quads = [f for f in s.faces if len(f) == 4]; ng = [f for f in s.faces if len(f) > 4]
        prims = []
        if tris: prims.append((0x90, [v for f in tris for v in f]))
        if quads: prims.append((0x80, [v for f in quads for v in f]))
        for f in ng: prims.append((0xA0, f))
        assert len(s.P) < 256 and len(s.N) < 256 and len(s.UV) < 256
        return gplmodel.build(dict(P=s.P, N=s.N, UV=s.UV, prims=prims, tex=tex, col=like['col'], nhdr=like['nhdr']), base, tail)

def ring(n, rx, rz, u0, u1, ox=0, oz=0, ph=0.5):
    return [(ox + rx * math.cos(2 * math.pi * (k + ph) / n), oz + rz * math.sin(2 * math.pi * (k + ph) / n),
             u0 + (u1 - u0) * k / max(n - 1, 1)) for k in range(n)]
def blade_ring(T, Wf, Wb, uspine, uflat, uedge, oz=0):
    """diamond-ish blade section: edge at +z (Wf), back at -z (Wb), thickness x +-T"""
    return [(0, oz + Wf, uedge), (T, oz, uflat), (0, oz - Wb, uspine), (-T, oz, uflat)]

def stick():
    """a plain tool handle (the hoe's octagonal handle, a bit longer, rounded ends)"""
    m = Mesh(); r = ring(8, 2.2, 2.2, 0.1, 0.9)
    secs = [(-28, ring(8, 1.6, 1.6, 0.1, 0.9), 0.02), (-26, r, 0.08)] + [(y, r, 0.1 + 0.8 * (y + 26) / 72) for y in (0, 22)] + [(46, r, 0.92), (48, ring(8, 1.6, 1.6, 0.1, 0.9), 0.98)]
    m.loft(secs); return m
def wooden_sword():
    """OoT Kokiri-style practice sword: light wood blade with a rounded tip, simple crossguard, wrapped grip
    texture 16x32: v 0-0.5 blade wood, 0.5-0.75 guard (darker wood), 0.75-1 grip wrap"""
    m = Mesh(); BL = (0.05, 0.5, 0.95)
    g = ring(8, 2.3, 2.3, 0.1, 0.9)
    m.loft([(-12, ring(8, 3.2, 3.2, 0.1, 0.9), 0.97), (-9, ring(8, 3.2, 3.2, 0.1, 0.9), 0.97), (-9, g, 0.78), (7, g, 0.99)])  # pommel + grip
    gd = [(-2.6, -8, 0.2), (2.6, -8, 0.8), (2.6, 8, 0.8), (-2.6, 8, 0.2)]
    m.loft([(7, gd, 0.55), (11, gd, 0.7)])                                            # crossguard
    sec = lambda w, t: blade_ring(t, w, w, BL[0], BL[1], BL[2])
    m.loft([(11, sec(4.2, 1.9), 0.05), (50, sec(4.2, 1.9), 0.35), (55, sec(3.4, 1.6), 0.42), (58, sec(2.0, 1.1), 0.46), (60, sec(0.6, 0.5), 0.48)])
    return m
def farmers_sword():
    """iron hilt (guard + pommel), leather grip, steel blade with a fuller
    texture 32x16: u 0-0.5 blade (spine..edge), 0.5-0.75 iron, 0.75-1 leather"""
    m = Mesh(); IRON = (0.55, 0.7); LEA = (0.78, 0.97)
    m.loft([(-13, ring(6, 3.3, 3.3, *IRON), 0.5), (-10, ring(6, 3.6, 3.6, *IRON), 0.5), (-8, ring(6, 2.6, 2.6, *IRON), 0.5)])   # pommel
    g = ring(8, 2.3, 2.3, *LEA); m.loft([(-8, g, 0.2), (7, g, 0.8)])                    # leather grip
    gd = [(-2.8, -10, 0.55), (2.8, -10, 0.7), (2.8, 10, 0.7), (-2.8, 10, 0.55)]
    m.loft([(7, gd, 0.3), (10, gd, 0.7)])                                             # iron crossguard
    sec = lambda w, t: blade_ring(t, w, w, 0.03, 0.25, 0.47)
    m.loft([(10, sec(4.4, 1.2), 0.5), (55, sec(4.0, 1.1), 0.5), (62, sec(2.2, 0.8), 0.5), (66, sec(0.3, 0.3), 0.5)])
    return m
def murasama():
    """H.F. Murasama look: long slightly curved katana, steel blade with a red edge, gold habaki, black round
    tsuba, long red-and-black wrapped tsuka with a black kashira.
    texture 32x16: u 0-0.5 blade (spine 0 .. red edge 0.5), 0.5-0.625 gold, 0.625-0.75 black, 0.75-1 wrap"""
    m = Mesh(); BLK = (0.66, 0.72); WRAP = (0.77, 0.98)
    m.loft([(-20, ring(8, 2.3, 2.6, *BLK), 0.5), (-17, ring(8, 2.3, 2.6, *BLK), 0.5)])                # kashira
    w = ring(8, 2.0, 2.4, *WRAP); m.loft([(-17, w, 0.0), (5, w, 1.0)])                                    # tsuka
    m.loft([(5, ring(12, 6.0, 6.0, *BLK), 0.5), (7, ring(12, 6.0, 6.0, *BLK), 0.5)])                     # tsuba
    m.loft([(7, ring(6, 1.6, 3.4, 0.52, 0.6), 0.5), (10, ring(6, 1.5, 3.2, 0.52, 0.6), 0.5)])              # habaki
    curve = lambda y: -0.0006 * (y - 10) ** 2
    secs = []
    for y in (10, 25, 40, 55, 66, 72):
        f = 1 - max(0, y - 64) / 8 * 0.9
        secs.append((y, blade_ring(1.1 * f + 0.15, 3.2 * f, 1.3 * f, 0.02, 0.22, 0.49, curve(y)), 0.5))
    secs.append((75, blade_ring(0.15, 0.3, 0.2, 0.02, 0.22, 0.49, curve(75) - 1.5), 0.5))
    m.loft(secs)
    return m

def texture(name, w, h):
    t = np.zeros((h, w, 3), float)
    yy, xx = np.mgrid[0:h, 0:w]
    if name == 'stick':
        t[:] = (150, 104, 62); t += ((np.sin(yy * 1.3 + xx * 0.2) * 10)[..., None]) ; t[:, ::5] *= 0.92
    elif name == 'wood':
        t[:h // 2] = (214, 172, 112); t[:h // 2] += (np.sin(yy[:h // 2] * 0.9) * 8)[..., None]       # light wood blade
        t[h // 2:3 * h // 4] = (150, 100, 58)                                                    # guard
        wrap = ((xx + yy) // 3) % 2; t[3 * h // 4:] = np.where(wrap[3 * h // 4:, :, None], (120, 80, 48), (205, 180, 140))
    elif name == 'farmer':
        bl = t[:, :w // 2]; u = xx[:, :w // 2] / (w // 2)
        bl[:] = (178, 184, 192); bl[(u > 0.42) & (u < 0.6)] = (140, 146, 156); bl[u > 0.85] = (226, 230, 236)
        t[:, w // 2:3 * w // 4] = (78, 80, 86)
        lea = ((yy + xx) // 3) % 2; t[:, 3 * w // 4:] = np.where(lea[:, 3 * w // 4:, None], (104, 62, 30), (138, 86, 44))
    elif name == 'murasama':
        bl = t[:, :w // 2]; u = xx[:, :w // 2] / (w // 2)
        bl[:] = (200, 204, 212); bl[u < 0.2] = (150, 152, 160); bl[u > 0.72] = (200, 30, 36)           # red edge
        t[:, w // 2:5 * w // 8] = (214, 170, 60)                                                    # gold habaki
        t[:, 5 * w // 8:3 * w // 4] = (22, 20, 22)                                                  # black tsuba / kashira
        d = (((xx + yy) // 3) % 2) ^ (((xx - yy) // 3) % 2)
        t[:, 3 * w // 4:] = np.where(d[:, 3 * w // 4:, None], (176, 18, 26), (26, 22, 24))            # red / black wrap
    return np.clip(t, 0, 255).astype(np.uint8)

def c565(rgb): r, g, b = [int(x) for x in rgb]; return (r >> 3) << 11 | (g >> 2) << 5 | (b >> 3)
def d565(v): return np.array(((v >> 11 & 31) * 255 // 31, (v >> 5 & 63) * 255 // 63, (v & 31) * 255 // 31), float)
def enc_cmpr(img):
    """RGB image (h, w multiples of 8) -> CMPR (opaque blocks, c0 > c1 four-colour mode)"""
    h, w = img.shape[:2]; out = bytearray()
    for by in range(0, h, 8):
        for bx in range(0, w, 8):
            for sy in (0, 4):
                for sx in (0, 4):
                    blk = img[by + sy:by + sy + 4, bx + sx:bx + sx + 4].reshape(16, 3).astype(float)
                    lum = blk @ (0.3, 0.59, 0.11); a, b = blk[lum.argmax()], blk[lum.argmin()]
                    c0, c1 = c565(a), c565(b)
                    if c0 == c1: c0 = c0 | 1 if c0 < 0xFFFF else c0; c1 = c0 - 1 if c0 else 0
                    if c0 < c1: c0, c1 = c1, c0
                    A, B = d565(c0), d565(c1); pal = [A, B, (2 * A + B) // 3, (A + 2 * B) // 3]
                    bits = 0
                    for k in range(16):
                        q = min(range(4), key=lambda j: ((blk[k] - pal[j]) ** 2).sum()); bits |= q << (30 - 2 * k)
                    out += struct.pack('>HHI', c0, c1, bits)
    return bytes(out)
WEAPONS = [  # id, name, builder, texture style, real.tpl / symbol.tpl image (only the old duplicate used them)
    (0x4E3, 'Stick', stick, 'stick', 0x1F, 0xDB),
    (0x4E4, 'Wooden Sword', wooden_sword, 'wood', 0x20, 0xDC),
    (0x4EA, "Farmer's Sword", farmers_sword, 'farmer', 0x1C, 0xD8),
    (0x4EB, 'H.M Murasama', murasama, 'murasama', 0x1D, 0xD9),
]
