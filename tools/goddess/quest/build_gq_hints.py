#!/usr/bin/env python3
"""Goddess quest hints (gh1; the user's lines: tools/goddess/dialogue/goddess_hints.json).
 - Villager hints V1-V12 and the Harvest Sprites' progress lines P1-P8 go into free debug.mes entries (file 0x32 =
   message group 50). spring.c gq_talk (from the villager talk hook, joetv.c joe_talk_post) points an everyday chat
   line (talk records 4-6, func_80113B80) at them, so the villager's own name plate stays. <n> = number slot 0
   (2A 00 00; spring.c fills it with func_80102300 before the line shows).
 - The opening: the cut Sprite scene at the Spring, Common event 376 (Nak / Nic / Flak placed by Pool B, 13 lines from
   david.mes 1-4 / 0x31, ebony.mes 0-3, flat.mes 0-3), rewritten with the user's O1-O4 and new joining lines, its
   speakers set to 32 / 33 / 34 (name plates; was -1). spring.c starts it on the first visit to the Spring from Day 2.
usage: build_gq_hints.py Common.arc debug.mes david.mes ebony.mes flat.mes OUTDIR
  (Common.arc / debug.mes: the current build (lv3 / gq scene); the three Sprite files from the US disc)
needs scratchpad/event (scrasm-era tools: mesenc, clzc, clz, loadarc, scrdis) via EVTOOLS. Writes the five files and gq_hints.h."""
import sys, os, json, struct, hashlib
HERE = os.path.dirname(os.path.abspath(__file__))
EV = os.environ.get('EVTOOLS', '/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/event')
sys.path.insert(0, EV); sys.path.insert(0, os.path.dirname(EV))
from clzc import clz_compress
from clz import clz_decompress
import mesenc
from mesenc import mes_entries, mes_build
from loadarc import load, parse
mesenc.TAGS['<name>'] = b'\x20\x00'                      # the farmer's name
mesenc.TAGS['<n>'] = b'\x2a\x00\x00'                     # number slot 0
common_in, debug_in, david_in, ebony_in, flat_in, outdir = sys.argv[1:7]
os.makedirs(outdir, exist_ok=True)
H = json.load(open(os.path.join(HERE, '..', 'dialogue', 'goddess_hints.json')))
def text(s):                                             # blank line = new box (wait + page), ends with wait
    boxes = [b.strip('\n') for b in s.replace('\r', '').split('\n\n') if b.strip()]
    return '<wait><page>'.join(boxes) + '<wait>'

# ---- debug.mes: V1-V12, P1-P8
d = open(debug_in, 'rb').read(); ents = mes_entries(d); assert mes_build(ents) == d
free = [i for i, e in enumerate(ents) if e == b'\0\0\0\0' and i < len(ents) - 1]
keys = ['V%d' % i for i in range(1, 13)] + ['P%d' % i for i in range(1, 9)]
ids = {}
for k, i in zip(keys, free):
    ents[i] = mesenc.enc(text(H[k]['line'])); ids[k] = i
grow = sum(map(len, ents)) - sum(map(len, mes_entries(d)))
assert set(ents[-1]) == {0} and len(ents[-1]) > grow
ents[-1] = ents[-1][:len(ents[-1]) - grow]
nd = mes_build(ents); nd += bytes(len(d) - len(nd)); assert len(nd) == len(d)
open(os.path.join(outdir, 'debug.mes'), 'wb').write(nd)

# ---- the opening scene's 13 lines (event 376's order: Nak 1, Nic 0, Flak 0, Nak 2, Nak 0x31, Nic 1, Flak 1, Nak 3,
#      Nic 2, Flak 2, Nak 4, Nic 3, Flak 3). O1-O4 are the user's; the rest are new joining lines (gh1 draft).
O = {k: H[k]['line'] for k in ('O1', 'O2', 'O3', 'O4')}
SCENE = {
    ('david', 1): O['O1'] + '\n\n' + O['O2'],
    ('ebony', 0): "She's been asleep for\nages and ages~",
    ('flat', 0): "Such a sleepyhead\ngoddess!",
    ('david', 2): "She won't wake up on\nher own, you know.",
    ('david', 0x31): "The old folks of the\nvalley used to bring\nher gifts.",
    ('ebony', 1): "And the Spring would\nshimmer and shine~",
    ('flat', 1): O['O3'],
    ('david', 3): "Ask around the valley\ntoo. Some folks still\nknow the old ways.",
    ('ebony', 2): O['O4'],
    ('flat', 2): "But what IS a\nwonderful thing?",
    ('david', 4): "Let's go and find out!",
    ('ebony', 3): "Time to go!\nTime to go!",
    ('flat', 3): "H-hey! Wait for me!",
}
for name, src in (('david', david_in), ('ebony', ebony_in), ('flat', flat_in)):
    b = open(src, 'rb').read(); e = mes_entries(b); assert mes_build(e) == b
    for (n, i), s in SCENE.items():
        if n == name: e[i] = mesenc.enc(text(s))
    open(os.path.join(outdir, name + '.mes'), 'wb').write(mes_build(e))

# ---- Common.arc: event 376's speakers -1 -> 32 Nak (david) / 33 Nic (ebony) / 34 Flak (flat)
u = open(common_in, 'rb').read()
be = lambda b, o: struct.unpack_from('>I', b, o)[0]
root, hsize, dstart = be(u, 4), be(u, 8), be(u, 12)
n = be(u, root + 8)
nodes = [bytearray(u[root + 12 * i:root + 12 * i + 12]) for i in range(n)]
raws = [clz_decompress(u[be(u, root + 12 * i + 4):be(u, root + 12 * i + 4) + be(u, root + 12 * i + 8)]) for i in range(1, n)]
NODE = 76                                                   # Common event 376 (node 76; 'file 75' in the loader's list)
scr = bytearray(raws[NODE - 1]); ins, ch = parse(bytes(scr))
code_at = bytes(scr).find(b'CODE') + 8 + 4                  # first instruction (u32 count first)
SPK = {5: 32, 6: 33, 7: 34}
done = 0
for j, (op, fl, kind, v) in enumerate(ins):
    if op == 37 and v == 0x04:                              # ... push file, push msg, push #128, neg, sys 04
        f = ins[j - 4][3] >> 7
        assert ins[j - 1][0] == 16 and ins[j - 2][0] == 23 and ins[j - 2][3] == 128, ins[j - 4:j + 1]
        o = code_at + 8 * (j - 2); struct.pack_into('>BBHI', scr, o, 23, ins[j - 2][1], ins[j - 2][2], SPK[f] << 7)
        o = code_at + 8 * (j - 1); struct.pack_into('>BBHI', scr, o, 0, 0, 0, 0)          # neg -> nop
        done += 1
assert done == 13, done
raws[NODE - 1] = bytes(scr)
al = lambda x: (x + 0x1F) & ~0x1F
data = bytearray(); offs = []
for r in raws:
    c = clz_compress(r); offs.append((dstart + len(data), len(c))); data += c + bytes(al(len(c)) - len(c))
for i, (o, sz) in enumerate(offs, 1): struct.pack_into('>II', nodes[i], 4, o, sz)
out = bytearray(u[:root]) + b''.join(nodes) + u[root + 12 * n:root + hsize]
out += bytes(dstart - len(out)); out += data
open(os.path.join(outdir, 'Common.arc'), 'wb').write(bytes(out))
_, fs = load(os.path.join(outdir, 'Common.arc')); assert [b for _, b in fs] == raws

h = ['/* generated by tools/goddess/quest/build_gq_hints.py: goddess quest hints (debug.mes entries) */',
     '#define GQ_EV_SPRITES 376']
h += ['#define GH_%s 0x%X' % (k, v) for k, v in ids.items()]
open(os.path.join(outdir, 'gq_hints.h'), 'w').write('\n'.join(h) + '\n')
for f in ('Common.arc', 'debug.mes', 'david.mes', 'ebony.mes', 'flat.mes'):
    b = open(os.path.join(outdir, f), 'rb').read(); print(f, len(b), hashlib.sha1(b).hexdigest()[:8])
print(ids)
