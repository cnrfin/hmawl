#!/usr/bin/env python3
"""Split the script-command switch in func_8010C604 (main.dol) into its cases.

usage: cases.py MAIN_DOL [--asm FILE] [--gd | --all | --dump]

  --gd    (default) only cases that call func_80112FDC or read lbl_803491CC
          (the game-data object)
  --all   every case, with its calls
  --dump  every case, with its disassembly

The jump table lbl_802C0078 (0xDE entries) is read from the original
main.dol. Instruction text comes from the asm file, which defaults to
asm/main/game/code_800F3228.s in this repo (CRLF is handled). A case runs
from its table entry to the next distinct entry in address order.
Reads only; writes nothing.
"""
import argparse, os, re, struct

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
ap.add_argument('main_dol')
ap.add_argument('--asm', default=os.path.join(REPO, 'asm', 'main', 'game', 'code_800F3228.s'))
g = ap.add_mutually_exclusive_group()
g.add_argument('--gd', dest='mode', action='store_const', const='gd')
g.add_argument('--all', dest='mode', action='store_const', const='all')
g.add_argument('--dump', dest='mode', action='store_const', const='dump')
a = ap.parse_args()
mode = a.mode or 'gd'

dol = open(a.main_dol, 'rb').read()
be32 = lambda o: struct.unpack_from('>I', dol, o)[0]
secs = [(be32(i*4), be32(0x48 + i*4), be32(0x90 + i*4)) for i in range(18)]

def rd(addr):
    for off, base, size in secs:
        if size and base <= addr < base + size:
            return be32(off + addr - base)
    raise KeyError(hex(addr))

# Addresses from the analysis in notes/findings.md (main.dol, US r0).
TABLE, NCASES = 0x802C0078, 0xDE
FUNC_START, FUNC_END = 0x8010C604, 0x801127C4   # FUNC_END = shared exit
targets = [rd(TABLE + 4*i) for i in range(NCASES)]

LINE = re.compile(r'^/\* ([0-9A-F]{8}) [0-9A-F]{8}  ((?:[0-9A-F]{2} ){4})\*/\t(.*)$')
ins = {}
with open(a.asm, encoding='latin-1') as f:
    for raw in f:
        m = LINE.match(raw.rstrip('\r\n'))
        if m:
            ad = int(m.group(1), 16)
            if FUNC_START <= ad < FUNC_END + 0x40:
                ins[ad] = (m.group(2).replace(' ', ''), m.group(3))

bounds = sorted(set(targets) | {FUNC_END})
def body(t):
    end = bounds[bounds.index(t) + 1]
    return [(ad, *ins[ad]) for ad in range(t, end, 4)]

opsby = {}
for op, t in enumerate(targets):
    opsby.setdefault(t, []).append(op)

shown = 0
for t in sorted(opsby):
    if t == FUNC_END:
        continue
    b = body(t)
    calls = [re.search(r'\bbl (\S+)', tx).group(1) for _, _, tx in b if tx.startswith('bl ')]
    sda = sorted({m for _, _, tx in b for m in re.findall(r'(lbl_\w+)@sda21', tx)})
    gd = 'func_80112FDC' in calls or 'lbl_803491CC' in sda
    if mode == 'gd' and not gd:
        continue
    shown += 1
    ops = ','.join(f'0x{o:02X}' for o in opsby[t])
    print(f'== cmd {ops}  @ {t:08X}  ({len(b)} insns)  gamedata={"Y" if gd else "n"}')
    print('   calls: ' + ' '.join(calls))
    if sda:
        print('   sda:   ' + ' '.join(sda))
    if mode == 'dump':
        for ad, h, tx in b:
            print(f'   {ad:08X} {h}  {tx}')
print(f'# {shown} cases shown ({len([t for t in opsby if t != FUNC_END])} distinct case bodies, {NCASES} table entries)')
