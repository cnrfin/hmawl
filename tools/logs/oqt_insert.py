#!/usr/bin/env python3
"""Placement quadtree (.oqt, magic EDEFF1F4) reader/writer, and record insertion.
Node at an absolute offset: 6 f32 bbox (min x,y,z, max x,y,z), 4 u32 child offsets (0 = none),
u32 count (leaf: its records; inner node: records in the subtree); a leaf's records follow at +0x2C,
0x34 bytes each: u16 model id, u16 flags, 3x4 f32 matrix (rows; translation in m[3], m[7], m[11]).
Nodes are stored depth-first from 8; the header is magic + u32 1."""
import struct

class Node:
    def __init__(s, bbox, kids, count, recs): s.bbox, s.kids, s.count, s.recs = list(bbox), kids, count, recs

def read(d):
    assert d[:8] == b'\xed\xef\xf1\xf4\x00\x00\x00\x01', d[:8].hex()
    def rd(o):
        bbox = struct.unpack_from('>6f', d, o); ch = struct.unpack_from('>4I', d, o + 0x18); n = struct.unpack_from('>I', d, o + 0x28)[0]
        if any(ch):
            return Node(bbox, [rd(c) if c else None for c in ch], n, [])
        return Node(bbox, [None] * 4, n, [d[o + 0x2C + 0x34 * k:o + 0x2C + 0x34 * (k + 1)] for k in range(n)])
    return rd(8)

def write(root):
    out = bytearray(b'\xed\xef\xf1\xf4\x00\x00\x00\x01')
    def wr(nd):
        o = len(out); out.extend(bytes(0x2C))
        if nd.recs: out.extend(b''.join(nd.recs))
        offs = [wr(k) if k else 0 for k in nd.kids]
        struct.pack_into('>6f4II', out, o, *nd.bbox, *offs, nd.count)
        return o
    wr(root)
    return bytes(out)

def record(model, x, y, z, yaw_deg, flags=0):
    import math
    c, s = math.cos(math.radians(yaw_deg)), math.sin(math.radians(yaw_deg))
    return struct.pack('>HH12f', model, flags, c, 0, s, x, 0, 1, 0, y, -s, 0, c, z)

def insert(root, rec, half_extent):
    """add rec to the leaf whose box holds its x/z (else the nearest), growing the boxes on the way"""
    x, y, z = struct.unpack_from('>f', rec, 16)[0], struct.unpack_from('>f', rec, 32)[0], struct.unpack_from('>f', rec, 48)[0]
    lo = (x - half_extent, y - 0.5, z - half_extent); hi = (x + half_extent, y + 1.5, z + half_extent)
    nd = root
    while True:
        for i in range(3):
            nd.bbox[i] = min(nd.bbox[i], lo[i]); nd.bbox[3 + i] = max(nd.bbox[3 + i], hi[i])
        nd.count += 1
        kids = [k for k in nd.kids if k]
        if not kids:
            nd.recs.append(rec); return nd
        inside = [k for k in kids if k.bbox[0] <= x <= k.bbox[3] and k.bbox[2] <= z <= k.bbox[5]]
        if inside: nd = inside[0]
        else: nd = min(kids, key=lambda k: ((k.bbox[0] + k.bbox[3]) / 2 - x) ** 2 + ((k.bbox[2] + k.bbox[5]) / 2 - z) ** 2)
