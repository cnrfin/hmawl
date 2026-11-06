#!/usr/bin/env python3
"""The goddess's first summoning (gq5): event 412 appended to Common.arc + her lines (batch 1, A1-A10, as the user
edited them) in free debug.mes entries. pm.c (gd_frame) loads her into character 37, raises her out of Pool B, plays
her motions and works out each camera shot; the script and pm.c talk through event counters (x128 in the script):
  26 cue (script -> pm.c): 1 rise, 2 close-up, 3 side two-shot, 4 bow, 5 talking two-shot, 6 sink
  27 done (pm.c -> script): 1 risen, 2 sunk
  28 year 1 (pm.c -> script): 1 = say A9 (the year-1 line)
  20-25 camera eye / target x 128 (pm.c, every frame, for the current cue)
usage: build_gq_scene.py Common.arc debug.mes OUTDIR   (inputs: stats1 Common.arc (events to 411), the gq4 debug.mes);
needs scratchpad/event (scrasm, mesenc, clzc, clz, loadarc) via EVTOOLS. Writes Common.arc, debug.mes, gq_scene.h."""
import sys, os, struct, json, hashlib
HERE = os.path.dirname(os.path.abspath(__file__))
EV = os.environ.get('EVTOOLS', '/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/event')
sys.path.insert(0, EV); sys.path.insert(0, os.path.dirname(EV))
from scrasm import Asm
from clzc import clz_compress
from clz import clz_decompress
import mesenc
from mesenc import mes_entries, mes_build
from loadarc import load, parse
mesenc.TAGS['<name>'] = b'\x20\x00'                          # the farmer's name (as <20:00> in the game's text)

common_in, mes_in, outdir = sys.argv[1:4]
os.makedirs(outdir, exist_ok=True)
FILE = 0x32
LINES = json.load(open(os.path.join(HERE, '..', 'dialogue', 'goddess_lines_batch1.json')))
A = ['A%d' % i for i in range(1, 11)]
def text(s):                                                 # blank line = new box (wait + page), ends with wait
    boxes = [b.strip('\n') for b in s.replace('\r', '').split('\n\n') if b.strip()]
    return '<wait><page>'.join(boxes) + '<wait>'

ev = open(mes_in, 'rb').read(); ents = mes_entries(ev)
assert mes_build(ents) == ev
free = [i for i, e in enumerate(ents) if e == b'\0\0\0\0' and i < len(ents) - 1]
ids = {}
for k, i in zip(A, free):
    ents[i] = mesenc.enc(text(LINES[k])); ids[k] = i
BUSY = free[len(A)]                                          # state-0x2A box: 2 lines at most
ents[BUSY] = mesenc.enc("The water is restless.\nCome back later.<wait>")
grow = sum(map(len, ents)) - sum(map(len, mes_entries(ev)))
assert set(ents[-1]) == {0} and len(ents[-1]) > grow
ents[-1] = ents[-1][:len(ents[-1]) - grow]
body = mes_build(ents); new_mes = body + bytes(len(ev) - len(body)); assert len(new_mes) == len(ev)

CUE, DONE, YEAR1 = 26, 27, 28
a = Asm(); L = a.new
a.sys(0x10); a.sys(0x00)                                     # event start
def getc(c): a.num(c); a.sys(0x95)
def setc(c, v): a.num(c); a.num(v); a.sys(0x93)
def frame(): a.sys(0x00)
def shot():                                                  # camera from counters 20-25 (x128), as Joe's trade
    for base, cmd in ((20, 0x14), (23, 0x15)):
        for k in range(3): a.num(base + k); a.sys(0x95); a.num(128); a.emit('div')
        a.sys(cmd)
    a.num(0); a.sys(0x13)
def cue(k): setc(CUE, k); frame(); frame(); shot()
def wait_done(v):
    top = L('wait'); a.label(top); frame(); getc(DONE); a.num(v); a.emit('cmp'); a.jnz(top)
def say(k): a.wait_msg(FILE, ids[k])
cue(1); wait_done(1)                                         # she rises out of the pool
say('A1')
cue(2); say('A2')                                            # close-up: eyes open
cue(3); say('A3'); say('A4')                                 # side two-shot: the turnips
cue(5); say('A5'); say('A6')                                 # talking: the lore, "you brought her home"
cue(4); say('A7')                                            # "I am the Harvest Goddess" (a little bow)
cue(5); say('A8')                                            # the hook
skip = L('noy1'); getc(YEAR1); a.num(1); a.emit('cmp'); a.jnz(skip)
say('A9')
a.label(skip)
cue(2); say('A10')
cue(6); wait_done(2)                                         # she sinks back
setc(CUE, 0); setc(DONE, 0)
a.emit('end'); a.emit('end')
script = a.build()
ins, ch = parse(script); assert len(ins) == len(a.ins)

u = open(common_in, 'rb').read()
be = lambda b, o: struct.unpack_from('>I', b, o)[0]
root, hsize, dstart = be(u, 4), be(u, 8), be(u, 12)
n = be(u, root + 8); st = root + 12 * n
assert n == 112, 'expected the stats Common.arc (events up to 411)'
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
out = bytes(out)
open(os.path.join(outdir, 'Common.arc'), 'wb').write(out)
open(os.path.join(outdir, 'debug.mes'), 'wb').write(new_mes)
_, fs = load(os.path.join(outdir, 'Common.arc'))
assert [b for _, b in fs] == raws
EVENT = 300 + len(fs)
h = ['/* generated by tools/goddess/quest/build_gq_scene.py: the first summoning */',
     '#define GQ_SCENE_EVENT %d' % EVENT, '#define GQ_MSG_BUSY 0x%X' % BUSY, '#define GQ_C_CUE  %d' % CUE, '#define GQ_C_DONE %d' % DONE, '#define GQ_C_YEAR1 %d' % YEAR1]
open(os.path.join(outdir, 'gq_scene.h'), 'w').write('\n'.join(h) + '\n')
print('event %d, %d instructions; lines' % (EVENT, len(a.ins)), ids)
for f in ('Common.arc', 'debug.mes'):
    b = open(os.path.join(outdir, f), 'rb').read(); print(f, len(b), hashlib.sha1(b).hexdigest()[:8])
