#!/usr/bin/env python3
"""lv3: one level-up menu event for every pending level. Event 410 (build_stats_events.py) asked once and ended; the next
level's menu had to wait for the game's after-event flag (EVMGR + 0x58C, several seconds) before event_start would take
it. Now the script loops: menu -> counter 61 = the answer -> waits until pm.bin (stats.c) has applied it and set 61 back
to 0 (and the menu's level number for the next one) -> again while counter 62 (points) is not 0.
usage: patch_lvup_loop.py Common.arc OUT.arc   (any Common.arc with event 410 from build_stats_events.py; the menu's
debug.mes entry is read from the old script)"""
import sys, os, struct, hashlib
EV = os.environ.get('EVTOOLS', '/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/event')
sys.path.insert(0, EV); sys.path.insert(0, os.path.dirname(EV))
from scrasm import Asm
from clzc import clz_compress
from clz import clz_decompress
from loadarc import load, parse
src, dst = sys.argv[1:3]
DEBUG, ANS, PTS, NODE = 0x32, 61, 62, 110                     # event 410 = node 110
u = open(src, 'rb').read()
be = lambda b, o: struct.unpack_from('>I', b, o)[0]
root, hsize, dstart = be(u, 4), be(u, 8), be(u, 12)
n = be(u, root + 8)
nodes = [bytearray(u[root + 12 * i:root + 12 * i + 12]) for i in range(n)]
raws = [clz_decompress(u[be(u, root + 12 * i + 4):be(u, root + 12 * i + 4) + be(u, root + 12 * i + 8)]) for i in range(1, n)]
old = raws[NODE - 1]; ins, _ = parse(old)
msgs = [ins[j - 2][3] >> 7 for j, x in enumerate(ins) if x[0] == 37 and x[3] == 0x04]
assert msgs and len(set(msgs)) == 1 and any(x[0] == 37 and x[3] == 0x93 for x in ins), 'event 410 is not the level-up menu'
M_LV = msgs[0]
a = Asm(); L = a.new; V = 2
def getc(c): a.num(c); a.sys(0x95)
def setc(c, v): a.num(c); a.num(v); a.sys(0x93)
a.sys(0x00)
top = L('menu'); a.label(top)
a.wait_msg(DEBUG, M_LV, V)
done = L('set')
for k in range(1, 5):
    nxt = L('n%d' % k)
    a.load(V); a.num(k); a.emit('cmp'); a.jnz(nxt)
    setc(ANS, k); a.jmp(done)
    a.label(nxt)
setc(ANS, 1)                                                    # no answer (cancelled): HP
a.label(done)
w = L('applied'); a.label(w); a.sys(0x00); getc(ANS); a.num(0); a.emit('cmp'); a.jnz(w)   # until stats.c has applied it
getc(PTS); a.num(0); a.emit('cmp'); a.jnz(top)                 # points left: the next level's menu
a.emit('end'); a.emit('end')
raws[NODE - 1] = a.build()
al = lambda x: (x + 0x1F) & ~0x1F
data = bytearray(); offs = []
for r in raws:
    c = clz_compress(r); offs.append((dstart + len(data), len(c))); data += c + bytes(al(len(c)) - len(c))
for i, (o, sz) in enumerate(offs, 1): struct.pack_into('>II', nodes[i], 4, o, sz)
out = bytearray(u[:root]) + b''.join(nodes) + u[root + 12 * n:root + hsize]
out += bytes(dstart - len(out)); out += data
open(dst, 'wb').write(bytes(out))
_, fs = load(dst); assert [b for _, b in fs] == raws
print('event 410: menu entry 0x%X, %d instructions;' % (M_LV, len(a.ins)), dst, len(out), hashlib.sha1(out).hexdigest()[:8])
