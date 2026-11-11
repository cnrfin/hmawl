#!/usr/bin/env python3
"""The goddess's daily visits at the Spring (gd1): her lines into free debug.mes entries and the talk / gift event
(appended to Common.arc after the summoning scene, event 413). pm.c (gd_daily) raises her where the farmer pressed A at
Pool B, keeps her up until a scene change, picks the lines and the affection (tools/goddess/dialogue/goddess_daily.json
'rules'), sets the counters and starts the event:
  20-25 camera eye / target x 128 (cmd_14 / cmd_15)
  26 first line, 27 second line (0 = none): debug.mes ids
  28 = 1: take the held item first (cmd_56: a gift)
Lines: goddess_daily.json (D / G / R, drafts) + approved batch 1 (B1-B9) and batch 2 (B14b, B16, 060, seasonal 0C9..0D5).
usage: build_gd_daily.py Common.arc debug.mes OUTDIR   (inputs: the gh1 build - events to 412, hints in debug.mes)
needs scratchpad/event (scrasm, mesenc, clzc, clz, loadarc) via EVTOOLS. Writes Common.arc, debug.mes, gd_daily.h."""
import sys, os, struct, json, hashlib, re
HERE = os.path.dirname(os.path.abspath(__file__))
EV = os.environ.get('EVTOOLS', '/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/event')
sys.path.insert(0, EV); sys.path.insert(0, os.path.dirname(EV))
from scrasm import Asm
from clzc import clz_compress
from clz import clz_decompress
import mesenc
from mesenc import mes_entries, mes_build
from loadarc import load, parse
mesenc.TAGS['<name>'] = b'\x20\x00'                          # the farmer's name
common_in, mes_in, outdir = sys.argv[1:4]
os.makedirs(outdir, exist_ok=True)
DLG = os.path.join(HERE, '..', 'dialogue')
B1J = json.load(open(os.path.join(DLG, 'goddess_lines_batch1.json')))
B2J = json.load(open(os.path.join(DLG, 'goddess_lines_batch2.json')))
DJ = json.load(open(os.path.join(DLG, 'goddess_daily.json')))['lines']
USE = ['B%d' % i for i in range(1, 10)] + ['B14b', 'B16', '060', '0C9', '0CB', '0CC', '0CF', '0D0', '0D1', '0D4', '0D5']
TEXT = {}
for k in USE: TEXT[k] = B1J[k] if k in B1J else B2J[k]
TEXT.update(DJ)
for k, s in TEXT.items():
    bad = set(re.findall(r'<[^>]*>', s)) - {'<name>'}
    assert not bad, (k, bad)
def text(s):                                                 # blank line = new box (wait + page), ends with wait
    boxes = [b.strip('\n') for b in s.replace('\r', '').split('\n\n') if b.strip()]
    return '<wait><page>'.join(boxes) + '<wait>'
FILE = 0x32
d = open(mes_in, 'rb').read(); ents = mes_entries(d); assert mes_build(ents) == d
free = [i for i, e in enumerate(ents) if e == b'\0\0\0\0' and i < len(ents) - 1]
ids = {}
for k, i in zip(TEXT, free): ents[i] = mesenc.enc(text(TEXT[k])); ids[k] = i
grow = sum(map(len, ents)) - sum(map(len, mes_entries(d)))
assert set(ents[-1]) == {0} and len(ents[-1]) > grow
ents[-1] = ents[-1][:len(ents[-1]) - grow]
nd = mes_build(ents); nd += bytes(len(d) - len(nd)); assert len(nd) == len(d)

L1, L2, TAKE = 26, 27, 28
a = Asm(); L = a.new
a.sys(0x10)
for base, cmd in ((20, 0x14), (23, 0x15)):                   # camera from counters 20-25 (pm.c), as Joe's talk
    for k in range(3): a.num(base + k); a.sys(0x95); a.num(128); a.emit('div')
    a.sys(cmd)
a.sys(0x00)
def getc(c): a.num(c); a.sys(0x95)
def say(c):                                                  # cmd_04(debug.mes, counter c, speaker 0x25: her plate)
    top = L('msg'); a.label(top); a.sys(0x00)
    a.num(FILE); getc(c); a.num(0x25); a.sys(0x04); a.num(0); a.emit('cmp'); a.jz(top)
notake = L('notake'); getc(TAKE); a.num(1); a.emit('cmp'); a.jnz(notake)
a.sys(0x56)                                                  # the gift: out of the farmer's hands
a.label(notake)
say(L1)
no2 = L('no2'); getc(L2); a.num(0); a.emit('cmp'); a.jz(no2)
say(L2)
a.label(no2)
for c in (L1, L2, TAKE): a.num(c); a.num(0); a.sys(0x93)
a.emit('end'); a.emit('end')
script = a.build()
ins, ch = parse(script); assert len(ins) == len(a.ins)

u = open(common_in, 'rb').read()
be = lambda b, o: struct.unpack_from('>I', b, o)[0]
root, hsize, dstart = be(u, 4), be(u, 8), be(u, 12)
n = be(u, root + 8); st = root + 12 * n
assert n == 113, 'expected the gh1 Common.arc (events to 412): %d nodes' % n
names = bytes(u[st:root + hsize])
nodes = [bytearray(u[root + 12 * i:root + 12 * i + 12]) for i in range(n)]
raws = [clz_decompress(u[be(u, root + 12 * i + 4):be(u, root + 12 * i + 4) + be(u, root + 12 * i + 8)]) for i in range(1, n)]
raws.append(script)
al = lambda x: (x + 0x1F) & ~0x1F
name_off = len(names.rstrip(b'\0')) + 1
names2 = names[:name_off] + b'@\0'
nodes.append(bytearray(struct.pack('>III', name_off, 0, 0)))
struct.pack_into('>I', nodes[0], 8, n + 1)
hlen = 12 * (n + 1) + len(names2)
dstart = max(dstart, al(root + hlen))
data = bytearray(); offs = []
for r in raws:
    c = clz_compress(r); offs.append((dstart + len(data), len(c))); data += c + bytes(al(len(c)) - len(c))
for i, (o, sz) in enumerate(offs, 1): struct.pack_into('>II', nodes[i], 4, o, sz)
hdr = b''.join(nodes) + names2
out = bytearray(u[:root]) + hdr
struct.pack_into('>I', out, 8, len(hdr)); struct.pack_into('>I', out, 12, dstart)
out += bytes(dstart - len(out)); out += data
open(os.path.join(outdir, 'Common.arc'), 'wb').write(bytes(out))
open(os.path.join(outdir, 'debug.mes'), 'wb').write(nd)
_, fs = load(os.path.join(outdir, 'Common.arc')); assert [b for _, b in fs] == raws
EVENT = 300 + len(fs)
h = ['/* generated by tools/goddess/quest/build_gd_daily.py: the goddess\'s daily visits (debug.mes ids, event) */',
     '#define GD_EVENT %d' % EVENT, '#define GD_C_L1 %d' % L1, '#define GD_C_L2 %d' % L2, '#define GD_C_TAKE %d' % TAKE]
h += ['#define GDL_%s 0x%X' % (k, v) for k, v in ids.items()]
# gd3: letters per page (box) of each line, for pm.c's mouth flaps (as Joe's joe_lines.h); <name> counts as 6
lo, hi = min(ids.values()), max(ids.values())
rows = []
for i in range(lo, hi + 1):
    k = next((k for k, v in ids.items() if v == i), None)
    boxes = [b.strip('\n') for b in TEXT[k].replace('\r', '').split('\n\n') if b.strip()] if k else []
    lens = [min(255, len(b.replace('<name>', 'xxxxxx').replace('\n', ''))) for b in boxes][:4]
    rows.append('    { %d, { %s } },   /* %s */' % (len(lens), ', '.join(map(str, lens + [0] * (4 - len(lens)))), k))
h += ['#define GDT_FIRST 0x%X' % lo, '#define GDT_N %d' % (hi - lo + 1),
      'static const struct { unsigned char pages, len[4]; } gd_text[GDT_N] = {'] + rows + ['};']
open(os.path.join(outdir, 'gd_daily.h'), 'w').write('\n'.join(h) + '\n')
print('event %d, %d lines' % (EVENT, len(ids)))
for f in ('Common.arc', 'debug.mes'):
    b = open(os.path.join(outdir, f), 'rb').read(); print(f, len(b), hashlib.sha1(b).hexdigest()[:8])
