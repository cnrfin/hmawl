#!/usr/bin/env python3
"""Read 32-bit words from main.dol by RAM address.

usage: dolread.py MAIN_DOL ADDR [COUNT]       (ADDR in hex)

Prints each word with its file offset and DOL section. Reads only.
"""
import struct, sys

if len(sys.argv) not in (3, 4):
    raise SystemExit(__doc__)
dol = open(sys.argv[1], 'rb').read()
addr, count = int(sys.argv[2], 16), int(sys.argv[3]) if len(sys.argv) > 3 else 1
be32 = lambda o: struct.unpack_from('>I', dol, o)[0]
secs = [(be32(i*4), be32(0x48 + i*4), be32(0x90 + i*4), i) for i in range(18)]

def file_off(a):
    for off, base, size, i in secs:
        if size and base <= a < base + size:
            return off + (a - base), ('text%d' % i if i < 7 else 'data%d' % (i - 7))
    raise SystemExit(f'{a:08X} is not in any main.dol section (bss or outside)')

for k in range(count):
    a = addr + 4*k
    o, s = file_off(a)
    print(f'{a:08X}  file 0x{o:06X} ({s})  {be32(o):08X}')
