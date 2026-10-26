#!/usr/bin/env python3
"""List the contents of a game archive (.arc, .arc.clz) without extracting it.

usage: arclist.py ARCHIVE [--nested]

Formats handled:
  U8   magic 55 AA 38 2D. Header: +0x04 root node offset, +0x08 size of
       the node table plus string table, +0x0C data offset. Nodes are 12
       bytes: u8 type (0 file, 1 dir), u24 name offset into the shared
       string table, u32 data offset (dir: parent index), u32 size
       (dir: index after its last child). Root node +0x08 = node count.
  CLZ  magic "CLZ\\0". +0x04 u32 decompressed size, +0x08 u32 0,
       +0x0C u32 decompressed size again. LZSS stream from +0x10: one
       flag byte per 8 items, read LSB first, bit 0 = literal byte,
       bit 1 = 2-byte reference b0 b1 with distance
       0x1000 - (b0 | (b1 & 0xF0) << 4) and length (b1 & 0x0F) + 3.
       The output is a U8 archive.
  Yaz0 / RARC are recognised and reported, not parsed (not seen in this
  game's files so far).

--nested also lists U8 or CLZ archives found inside the archive.
Reads only; writes nothing.
"""
import argparse, signal, struct

# Exit quietly when output is piped into head etc.
if hasattr(signal, "SIGPIPE"):
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

U8_MAGIC = b'\x55\xaa\x38\x2d'


def be32(b, o):
    return struct.unpack_from('>I', b, o)[0]


def clz_decompress(b):
    size = be32(b, 4)
    out = bytearray()
    i = 0x10
    while len(out) < size:
        flags = b[i]
        i += 1
        for k in range(8):
            if len(out) >= size:
                break
            if not (flags >> k) & 1:
                out.append(b[i])
                i += 1
            else:
                b0, b1 = b[i], b[i + 1]
                i += 2
                dist = 0x1000 - (b0 | ((b1 & 0xF0) << 4))
                if dist > len(out):
                    raise ValueError(f'reference before start at input 0x{i - 2:X}')
                for _ in range((b1 & 0x0F) + 3):
                    out.append(out[-dist])
    return bytes(out), i


def u8_entries(b):
    root = be32(b, 4)
    count = be32(b, root + 8)
    strings = root + count * 12
    nodes = []
    for n in range(count):
        o = root + n * 12
        name_off = be32(b, o) & 0xFFFFFF
        end = b.index(b'\0', strings + name_off)
        nodes.append((b[o], b[strings + name_off:end].decode('latin-1'),
                      be32(b, o + 4), be32(b, o + 8)))
    # Rebuild paths: a dir's children run from its index + 1 up to its "next" index.
    paths, stack = [], []
    for n, (typ, name, a, nxt) in enumerate(nodes):
        while stack and n >= stack[-1][1]:
            stack.pop()
        path = '/'.join([s[0] for s in stack] + [name]) if n else '/'
        paths.append(path)
        if typ == 1 and n:
            stack.append((name, nxt))
    return root, count, strings, nodes, paths


def describe(b, label, nested, indent=''):
    magic = b[:4]
    if magic == b'CLZ\0':
        raw, used = clz_decompress(b)
        print(f'{indent}{label}: CLZ, decompressed 0x{be32(b, 4):X} bytes, '
              f'stream used 0x{used:X} of 0x{len(b):X}')
        b, label = raw, label + ' (decompressed)'
        magic = b[:4]
    if magic == b'Yaz0':
        print(f'{indent}{label}: Yaz0, decompressed size 0x{be32(b, 4):X} (not parsed)')
        return
    if magic == b'RARC':
        print(f'{indent}{label}: RARC (not parsed)')
        return
    if magic != U8_MAGIC:
        print(f'{indent}{label}: unknown magic {magic.hex()}')
        return
    root, count, strings, nodes, paths = u8_entries(b)
    files = [n for n in nodes if n[0] == 0]
    print(f'{indent}{label}: U8, root 0x{root:X}, header size 0x{be32(b, 8):X}, '
          f'data offset 0x{be32(b, 12):X}, {count} nodes '
          f'({count - len(files)} dirs, {len(files)} files), string table at 0x{strings:X}')
    for (typ, name, a, size), path in zip(nodes, paths):
        if typ == 1:
            print(f'{indent}  DIR                        {path}')
            continue
        inner = b[a:a + 4]
        tag = {U8_MAGIC: 'U8', b'CLZ\0': 'CLZ', b'Yaz0': 'Yaz0', b'RARC': 'RARC'}.get(inner, '')
        ok = '' if a + size <= len(b) else '  OUT OF RANGE'
        print(f'{indent}  0x{a:08X} 0x{size:08X} {tag:4} {path}{ok}')
        if nested and tag in ('U8', 'CLZ'):
            describe(b[a:a + size], path, nested, indent + '    ')


ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
ap.add_argument('archive')
ap.add_argument('--nested', action='store_true')
args = ap.parse_args()
describe(open(args.archive, 'rb').read(), args.archive, args.nested)
