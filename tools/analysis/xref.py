#!/usr/bin/env python3
"""Find every reference to a main.dol address range in the original binaries.

usage: xref.py BINDIR START END        (START/END in hex, END exclusive)

BINDIR must contain main.dol, wlp0.rel, wlp1.rel and wlp2.rel (the originals).
  main.dol: decodes every word in the text sections as b/bl/bc, finds
            lis+addi / lis+ori pairs, and scans all sections for raw
            32-bit pointers (vtables, jump tables, data).
  wlp*.rel: parses the relocation tables and reports every relocation
            against module 0 (main.dol) whose target is in [START, END).
Reads only; writes nothing.
"""
import os, signal, struct, sys

# Exit quietly when output is piped into head etc.
if hasattr(signal, "SIGPIPE"):
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

if len(sys.argv) != 4:
    raise SystemExit(__doc__)
bindir, start, end = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3], 16)
inr = lambda a: start <= a < end
be32 = lambda b, o: struct.unpack_from('>I', b, o)[0]
sx = lambda v, bits: v - (1 << bits) if v & (1 << (bits - 1)) else v

def read(name):
    path = os.path.join(bindir, name)
    if not os.path.exists(path):
        raise SystemExit(f'missing {path}')
    return open(path, 'rb').read()

dol = read('main.dol')
secs = []
for i in range(18):
    off, addr, size = be32(dol, i*4), be32(dol, 0x48 + i*4), be32(dol, 0x90 + i*4)
    if size:
        secs.append(('text' if i < 7 else 'data', i, off, addr, size))

hits = []
for kind, i, off, addr, size in secs:
    lis = {}
    for k in range(0, size, 4):
        w, pc = be32(dol, off + k), addr + k
        op = w >> 26
        if kind == 'text' and op == 18:                      # b / bl / ba / bla
            t = (sx(w & 0x03FFFFFC, 26) + (0 if w & 2 else pc)) & 0xFFFFFFFF
            if inr(t):
                hits.append(f'main.dol {kind}{i} {pc:08X} (file 0x{off+k:X}) {"bl" if w & 1 else "b"} -> {t:08X}  raw {w:08X}')
        if kind == 'text' and op == 16:                      # bc
            t = (sx(w & 0xFFFC, 16) + (0 if w & 2 else pc)) & 0xFFFFFFFF
            if inr(t):
                hits.append(f'main.dol {kind}{i} {pc:08X} bc -> {t:08X}  raw {w:08X}')
        if kind == 'text' and op == 15 and ((w >> 16) & 31) == 0:   # lis rD, hi
            lis[(w >> 21) & 31] = (w & 0xFFFF) << 16
        elif kind == 'text' and op in (14, 24):              # addi / ori on a lis'd reg
            ra = (w >> 16) & 31
            if ra in lis:
                v = (lis[ra] + sx(w & 0xFFFF, 16)) if op == 14 else (lis[ra] | (w & 0xFFFF))
                if inr(v & 0xFFFFFFFF):
                    hits.append(f'main.dol {kind}{i} {pc:08X} lis/{"addi" if op == 14 else "ori"} -> {v & 0xFFFFFFFF:08X}')
        if inr(w):
            hits.append(f'main.dol {kind}{i} {pc:08X} (file 0x{off+k:X}) raw word {w:08X}')

RELTYPES = {1: 'ADDR32', 4: 'ADDR16_LO', 5: 'ADDR16_HI', 6: 'ADDR16_HA', 10: 'REL24', 11: 'REL14'}
for name in ('wlp0.rel', 'wlp1.rel', 'wlp2.rel'):
    rel = read(name)
    imp_off, imp_size = be32(rel, 0x28), be32(rel, 0x2C)
    n = 0
    for e in range(imp_off, imp_off + imp_size, 8):
        mod, pos = be32(rel, e), be32(rel, e + 4)
        sec = cur = 0
        while True:
            off, typ, s, addend = struct.unpack_from('>HBBI', rel, pos); pos += 8
            if typ == 203:                                   # R_DOLPHIN_END
                break
            if typ == 202:                                   # R_DOLPHIN_SECTION
                sec, cur = s, 0
                continue
            cur += off
            if typ == 201:                                   # R_DOLPHIN_NOP
                continue
            n += 1
            if mod == 0 and inr(addend):
                hits.append(f'{name} sec{sec}+0x{cur:X} {RELTYPES.get(typ, typ)} -> {addend:08X}')
    print(f'# {name}: scanned {n} relocations')

print(f'# main.dol: scanned {len(secs)} sections')
print('\n'.join(hits) if hits else '# no references found')
