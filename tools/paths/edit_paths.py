#!/usr/bin/env python3
"""Villager paths (PathData.arc -> path_WorldMap.pth, the valley).
.pth layout (big-endian): header 7 x u32 = magic F0E1F4E8, node count, link count, spot count, node table off,
link table off, spot table off. Node (20 B) = f32 x, f32 z, u32 0, u32 link count, u32 first link (byte offset
into the link table). Link (8 B) = u32 target node (byte offset into the node table, i.e. index*20), f32 length.
Links are stored both ways. Spot (8 B) = u32 id, u32 node byte offset: the named places scripts send villagers to.

Edits:
1. New bridge (x 262.5-266.5, z 182.9-193.0): two waypoints at the deck ends, linked to each other, to 175 on the
   north bank and to 354 / 178 on the south road. Nodes are appended, so spots and old offsets are unchanged.
2. Bench test 2: spot 2 (node 285, in front of the kept bench's old seat) moves to the turned bench's seat, east
   of it at (138.30, 176.60). Its link to 162 would cross the bench, so it goes 285-286 instead (286-162 passes
   north of the bench). Spot 3 (node 286, the removed bench) is left as a plain waypoint.
usage: edit_paths.py PathData.arc OUT.arc"""
import sys, os, struct, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import u8arc
NAME = 'path_WorldMap.pth'
def read(p):
    mg, nn, nl, n3, on, ol, o3 = struct.unpack_from('>7I', p, 0); assert mg == 0xF0E1F4E8
    N = [list(struct.unpack_from('>ff', p, on + 20 * i)) for i in range(nn)]
    L = [[struct.unpack_from('>I', p, ol + struct.unpack_from('>I', p, on + 20 * i + 16)[0] + 8 * k)[0] // 20
          for k in range(struct.unpack_from('>I', p, on + 20 * i + 12)[0])] for i in range(nn)]
    S = [struct.unpack_from('>II', p, o3 + 8 * k) for k in range(n3)]
    return N, L, S
def write(N, L, S):
    on = 0x1C; ol = on + 20 * len(N); nl = sum(map(len, L)); o3 = ol + 8 * nl
    out = bytearray(struct.pack('>7I', 0xF0E1F4E8, len(N), nl, len(S), on, ol, o3)); lo = 0; links = b''
    for (x, z), nb in zip(N, L):
        out += struct.pack('>ffIII', x, z, 0, len(nb), lo); lo += 8 * len(nb)
        for j in nb: links += struct.pack('>If', 20 * j, math.hypot(N[j][0] - x, N[j][1] - z))
    return bytes(out + links + b''.join(struct.pack('>II', *s) for s in S))
def link(L, a, b):
    if b not in L[a]: L[a].append(b)
    if a not in L[b]: L[b].append(a)
def unlink(L, a, b):
    L[a].remove(b); L[b].remove(a)
def main(src, dst):
    d = open(src, 'rb').read(); a = u8arc.read(d); assert u8arc.build(a, {}) == d
    k = u8arc.names(a)[NAME]; p = a['files'][k]
    N, L, S = read(p); assert write(N, L, S) == p                     # exact round trip
    # 1. bridge
    assert [round(v, 2) for v in N[175]] == [264.67, 181.33] and [round(v, 2) for v in N[354]] == [260.89, 197.14]
    b1 = len(N); N.append([264.5, 182.6]); L.append([])
    b2 = len(N); N.append([264.5, 193.6]); L.append([])
    link(L, b1, 175); link(L, b1, b2); link(L, b2, 354); link(L, b2, 178)
    # 2. bench seat
    assert (2, 285 * 20) in S and [round(v, 2) for v in N[285]] == [137.56, 177.88]
    N[285] = [138.30, 176.60]; unlink(L, 285, 162); link(L, 285, 286)
    new = write(N, L, S); chk = read(new); assert chk[1] == L and chk[2] == S
    o = u8arc.build(a, {k: new}); assert u8arc.read(o)['files'][k] == new
    open(dst, 'wb').write(o)
    print('%s: %d -> %d waypoints, %d -> %d links; PathData.arc %d -> %d bytes' %
          (NAME, len(N) - 2, len(N), len(read(p)[1]) and sum(map(len, read(p)[1])), sum(map(len, L)), len(d), len(o)))
    for i in (b1, b2, 175, 354, 178, 285, 286, 162):
        print('  node %d (%.2f, %.2f) -> %s' % (i, N[i][0], N[i][1], L[i]))
if __name__ == '__main__': main(*sys.argv[1:3])
