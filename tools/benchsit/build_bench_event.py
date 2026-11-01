"""Bench by the tree: "Sit until the evening?" (before 18:00) / "Sit until the morning?" (from 18:00, and
before 6:00). Yes -> fade out, the clock goes to 18:00 / 6:00 (script cmd_43 set today's time, cmd_44 add
hours+minutes, both through func_80109E00 like the game's own events), fade in.
Appends the script to Common.arc as entry 107 (event 407; the Postman's is 406) and puts the two lines in
debug.mes entries 9 and 10 (free 4-byte slots after the Postman's 0..8; file size kept).
usage: build_bench_event.py Common.arc debug.mes OUTDIR   (inputs: the Postman build, 95208117 / 16e98598)
needs scratchpad/event (scrasm, mesenc, clzc, loadarc) on the path."""
import sys, os, struct, hashlib
EV = os.environ.get('EVTOOLS', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'event'))
sys.path.insert(0, EV); sys.path.insert(0, os.path.dirname(EV))
from scrasm import Asm
from clzc import clz_compress
from clz import clz_decompress
from mesenc import enc, mes_entries, mes_build
from loadarc import load, parse

common_in, mes_in, outdir = sys.argv[1:4]
os.makedirs(outdir, exist_ok=True)
EVENT_FILE = 0x32                                            # debug.mes
EVE, MORN = 9, 10
TEXT = {EVE: "Sit until the\nevening?<yesno>", MORN: "Sit until the\nmorning?<yesno>"}

ev = open(mes_in, 'rb').read()
ents = mes_entries(ev)
assert mes_build(ents) == ev and ents[EVE] == ents[MORN] == b'\0\0\0\0', 'debug.mes slots 9/10 not free'
for k, t in TEXT.items(): ents[k] = enc(t)
grow = sum(len(x) for x in ents) - sum(len(x) for x in mes_entries(ev))
assert set(ents[-1]) == {0} and len(ents[-1]) > grow, 'no zero padding at the end of debug.mes'
ents[-1] = ents[-1][:len(ents[-1]) - grow]                   # the last entry is zero padding: keep the size
body = mes_build(ents)
assert len(body) <= len(ev), 'debug.mes grew'
new_mes = body + bytes(len(ev) - len(body))
assert mes_entries(new_mes)[EVE] == enc(TEXT[EVE])

V_ANS = 2
REST = 27                                                    # event counter 27 = 1 on Yes: pm.c refills stamina
a = Asm(); L = a.new
a.sys(0x10); a.sys(0x00)                                     # event start
def fade(cmd):
    a.num(0); a.raw(64); a.sys(cmd)                          # cmd_0B out / cmd_0C in: black, 0.5 s
    top = L('fade'); a.label(top); a.sys(0x00); a.sys(0x0D); a.jnz(top)
morning, early, go_eve, done = L('morn'), L('early'), L('eve'), L('done')
a.sys(0x4A); a.num(6); a.emit('cmp'); a.jlt(early)          # hour < 6  -> morning (today 6:00)
a.sys(0x4A); a.num(18); a.emit('cmp'); a.jlt(go_eve)        # hour < 18 -> evening
# 18:00-23:59: until tomorrow 6:00 = add (29 - hour) h + (60 - minute) min
a.wait_msg(EVENT_FILE, MORN, V_ANS)
a.load(V_ANS); a.num(1); a.emit('cmp'); a.jnz(done)
a.num(REST); a.num(1); a.sys(0x93)
fade(0x0B)
a.num(29); a.sys(0x4A); a.emit('sub'); a.num(60); a.sys(0x4B); a.emit('sub'); a.sys(0x44)
a.jmp(morning)
a.label(early)
a.wait_msg(EVENT_FILE, MORN, V_ANS)
a.load(V_ANS); a.num(1); a.emit('cmp'); a.jnz(done)
a.num(REST); a.num(1); a.sys(0x93)
fade(0x0B)
a.num(6); a.num(0); a.sys(0x43)                              # today 6:00
a.jmp(morning)
a.label(go_eve)
a.wait_msg(EVENT_FILE, EVE, V_ANS)
a.load(V_ANS); a.num(1); a.emit('cmp'); a.jnz(done)
a.num(REST); a.num(1); a.sys(0x93)
fade(0x0B)
a.num(18); a.num(0); a.sys(0x43)                             # today 18:00
a.label(morning)
for _ in range(30): a.sys(0x00)                             # a moment in the dark
fade(0x0C)
a.label(done)
a.emit('end'); a.emit('end')
script = a.build()
ins, ch = parse(script); assert len(ins) == len(a.ins)

u = open(common_in, 'rb').read()
be = lambda b, o: struct.unpack_from('>I', b, o)[0]
assert u[:4] == b'U\xaa8-'
root, hsize, dstart = be(u, 4), be(u, 8), be(u, 12)
n = be(u, root + 8); st = root + 12 * n
assert n == 107, 'expected the Postman Common.arc (106 entries)'
names = bytes(u[st:root + hsize])
nodes = [bytearray(u[root + 12 * i:root + 12 * i + 12]) for i in range(n)]
raws = [clz_decompress(u[be(u, root+12*i+4):be(u, root+12*i+4)+be(u, root+12*i+8)]) for i in range(1, n)]
raws.append(script)
al = lambda x: (x + 0x1F) & ~0x1F
name_off = len(names.rstrip(b'\0')) + 1
names2 = names[:name_off] + b'@\0'
nodes.append(bytearray(struct.pack('>III', name_off, 0, 0)))
struct.pack_into('>I', nodes[0], 8, n + 1)
hlen = 12 * (n + 1) + len(names2)
dstart = max(dstart, al(root + hlen))                      # room for the extra node
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
assert [b for _, b in fs] == raws and len(fs) == 107
print('script: %d instructions; Common.arc 0x%x -> 0x%x; node %d = event %d' % (len(a.ins), len(u), len(out), len(fs), 300 + len(fs)))
for f in ('Common.arc', 'debug.mes'):
    b = open(os.path.join(outdir, f), 'rb').read(); print(f, hex(len(b)), hashlib.sha1(b).hexdigest())
