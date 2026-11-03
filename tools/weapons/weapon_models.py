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
    def guard_z(s, zs, ybot, hgt, hx, uv):
        """a bar along z: box section (x +-hx, y ybot(z) .. +hgt) at each z, ends capped"""
        secs = [[(-hx, ybot(z), z), (hx, ybot(z), z), (hx, ybot(z) + hgt, z), (-hx, ybot(z) + hgt, z)] for z in zs]
        us = [uv[0], uv[1], uv[1], uv[0]]
        for i in range(len(secs) - 1):
            A, B = secs[i], secs[i + 1]; va, vb = i / (len(secs) - 1), (i + 1) / (len(secs) - 1)
            c = (0, (A[0][1] + B[0][1]) / 2 + hgt / 2, (A[0][2] + B[0][2]) / 2)        # local centre of this piece
            for e in range(4):
                s.face([A[e], A[(e + 1) % 4], B[(e + 1) % 4], B[e]], [(us[e], va), (us[(e + 1) % 4], va), (us[(e + 1) % 4], vb), (us[e], vb)], c)
        for S_, d in ((secs[0], -1), (secs[-1], 1)):
            s.face(S_, [(u, 0.5) for u in us], (0, S_[0][1] + hgt / 2, S_[0][2] - d * 4))
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
    m.guard_z([z for z in range(-12, 13, 3)], lambda z: 7 + 0.028 * z * z, 3.0, 2.8, IRON)   # iron crossguard, ends curving up
    sec = lambda w, t: blade_ring(t, w, w, 0.03, 0.25, 0.47)
    m.loft([(10, sec(4.4, 1.2), 0.5), (55, sec(4.0, 1.1), 0.5), (62, sec(2.2, 0.8), 0.5), (66, sec(0.3, 0.3), 0.5)])
    return m
def murasama():
    """H.F. Murasama look, Masamune proportions: a long thin katana with a gentle even curve, all-red blade with a
    pink hamon (texture), black square tsuba, black habaki, black tsuka with grey segments, black kashira.
    texture 64x64: u 0-0.5 blade (spine 0 .. edge 0.5), v along the blade; 0.5-0.75 black metal; 0.75-1 tsuka"""
    m = Mesh(); BLK = (0.55, 0.7); TS = (0.77, 0.98)
    m.loft([(-24, ring(8, 2.1, 2.5, *BLK), 0.5), (-21, ring(8, 2.3, 2.7, *BLK), 0.5)])               # kashira
    w = ring(8, 2.0, 2.4, *TS); m.loft([(-21, w, 0.0), (5, w, 1.0)])                                   # tsuka
    sq = [(-5.2, -5.2, 0.55), (5.2, -5.2, 0.7), (5.2, 5.2, 0.55), (-5.2, 5.2, 0.7)]
    m.loft([(5, sq, 0.3), (7, sq, 0.7)])                                                              # square tsuba
    m.loft([(7, ring(6, 1.3, 2.4, *BLK), 0.5), (9.5, ring(6, 1.2, 2.2, *BLK), 0.5)])                  # habaki
    curve = lambda y: -0.00075 * (y - 9.5) ** 2                                                         # toward the spine
    secs = []
    for y in (9.5, 30, 50, 70, 90, 104, 112):
        secs.append((y, blade_ring(0.9, 2.6, 1.5, 0.03, 0.24, 0.48, curve(y)), (y - 9.5) / 108))
    secs.append((116, blade_ring(0.6, 1.4, 1.4, 0.03, 0.24, 0.48, curve(116)), 0.98))              # kissaki: edge sweeps
    secs.append((118.5, blade_ring(0.15, 0.2, 0.2, 0.03, 0.24, 0.48, curve(118.5) - 0.6), 1.0))      # up to the point
    m.loft(secs)
    return m

TEX_SIZE = {'stick': (32, 64), 'wood': (32, 64), 'farmer': (64, 64), 'murasama': (64, 64)}   # (w, h)
def texture(name, w=None, h=None):
    """UV layout in fractions (u across / v along), so any size works"""
    w, h = (w, h) if w else TEX_SIZE[name]
    rng = np.random.RandomState(7)
    yy, xx = np.mgrid[0:h, 0:w]; U = (xx + 0.5) / w; V = (yy + 0.5) / h
    noise = rng.uniform(-1, 1, (h, w))
    t = np.zeros((h, w, 3), float)
    def put(mask, rgb): t[mask] = rgb if np.ndim(rgb) == 1 or len(np.shape(rgb)) == 1 else rgb[mask]
    def wood(base, scale=1.0):
        grain = np.sin(U * 40 * scale + np.sin(V * 9) * 2.2) * 0.5 + 0.5
        return np.array(base)[None, None] * (0.86 + 0.16 * grain[..., None]) + noise[..., None] * 5
    if name == 'stick':
        t[:] = wood((150, 104, 62), 0.6)
    elif name == 'wood':
        t[:] = wood((214, 172, 112))
        edge = (np.abs(U - 0.5) > 0.42) & (V < 0.5); t[edge] *= 1.06                      # worn blade edges
        g = (V >= 0.5) & (V < 0.75); t[g] = wood((146, 98, 56))[g]                            # guard
        wr = V >= 0.75; band = ((xx + yy * 0.8) / 5).astype(int) % 2
        c = np.where(band[..., None], (112, 74, 44), (198, 172, 132)); sh = 0.8 + 0.2 * np.cos((U - 0.5) * 3)[..., None]
        t[wr] = (c * sh)[wr]
    elif name == 'farmer':
        bl = U < 0.5; k = U / 0.5                                                           # spine 0 .. edge 1
        steel = 150 + 60 * np.clip(1 - np.abs(k - 0.5) * 1.6, 0, 1) + noise * 4 + np.sin(V * 90) * 2
        steel = np.where((k > 0.42) & (k < 0.58), steel - 45, steel)                      # fuller
        steel = np.where(k > 0.86, 236, steel)                                              # bevel highlight
        t[bl] = np.stack([steel * 0.97, steel, steel * 1.04], -1)[bl]
        ir = (U >= 0.5) & (U < 0.75); g = 70 + 18 * np.sin(V * 6) + noise * 5
        t[ir] = np.stack([g, g * 1.02, g * 1.08], -1)[ir]
        le = U >= 0.75; band = ((yy * 1.0 + xx * 0.6) / 4).astype(int) % 3
        c = np.where(band[..., None] == 0, (70, 40, 20), (128, 78, 40)) * (0.85 + 0.15 * np.cos((U - 0.875) * 25))[..., None]
        t[le] = c[le]
    elif name == 'murasama':
        bl = U < 0.5; k = U / 0.5
        hamon = 0.62 + 0.07 * np.sin(V * 38) + 0.03 * np.sin(V * 97 + 1)                 # wavy temper line
        red = np.where((k < hamon)[..., None], np.array((196, 22, 38)), np.array((240, 120, 150)))
        red = np.where((k < 0.16)[..., None], np.array((120, 10, 22)), red)              # dark spine
        red = red * (0.92 + 0.08 * np.sin(V * 140))[..., None] + noise[..., None] * 6
        line = np.abs(k - hamon) < 0.035; red[line] = (255, 170, 190)
        t[bl] = red[bl]
        bk = (U >= 0.5) & (U < 0.75); g = 26 + 10 * (np.abs(U - 0.625) < 0.02) + noise * 3
        t[bk] = np.stack([g, g, g * 1.05], -1)[bk]
        ts = U >= 0.75; seg = (V * 9) % 1
        g = np.where((seg < 0.18), 120, 32) + noise * 4
        g = np.where((np.abs(U - 0.875) < 0.03) & (seg > 0.4) & (seg < 0.6), 190, g)       # silver detail
        t[ts] = np.stack([g, g, g * 1.06], -1)[ts]
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
