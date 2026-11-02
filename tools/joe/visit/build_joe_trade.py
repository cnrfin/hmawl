"""Joe's bench trade: event 408 (Common.arc node 108, after the bench's 407) + its lines in debug.mes 11-21.
The picker is the game's own (script commands D5/D6/D7 buy, D9/DA/DB sell = the global number picker at
0x802F3D70 that Vesta's and Van's shops use). pm.c does the money and the coins (counters 41-44):
  41 request: script 1 = buy, 4 = sell; pm.c answers 2 = bought, 3 = not enough gold, 5 = sold
  42 count picked; 44 $JOE held (set by pm.c before the event); message number slot 0 = today's price.
usage: build_joe_trade.py Common.arc debug.mes OUTDIR   (inputs: the bench build, Common.arc 700e4ae4 /
debug.mes 4dd04c6d); needs scratchpad/event (scrasm, mesenc, clzc, clz, loadarc) via EVTOOLS."""
import sys, os, struct, hashlib
EV = os.environ.get('EVTOOLS', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'event'))
sys.path.insert(0, EV); sys.path.insert(0, os.path.dirname(EV))
from scrasm import Asm
from clzc import clz_compress
from clz import clz_decompress
import mesenc
from mesenc import mes_entries, mes_build
from loadarc import load, parse
mesenc.P['$'] = 0x80FD                                       # drawn into the fonts for the TV report
mesenc.TAGS['<price>'] = b'\x2a\x00\x00'                     # number slot 0
enc = mesenc.enc

common_in, mes_in, outdir = sys.argv[1:4]
os.makedirs(outdir, exist_ok=True)
FILE = 0x32                                                  # debug.mes
TEXT = {
    11: "I'm selling $JOE for\n<price>G today.<wait>",
    12: "Wanna buy some?<yesno>",
    13: "You don't have\nenough G for that,\nkid.<wait>",
    14: "Pleasure doing\nbusiness. HODL!<wait>",
    15: "Wanna sell some\n$JOE?<yesno>",
    16: "What!? You're selling\nyour $JOE?<wait>",
    17: "Hm, ok, I'll buy\nyour $JOE bags for\n<price>G. How does that\nsound?<yesno>",
    18: "You don't have any\n$JOE, kid.<wait>",
    19: "Later, kid.<wait>",
    20: "Done. Don't come\ncrying when it moons.<wait>",
}
ev = open(mes_in, 'rb').read()
ents = mes_entries(ev)
assert mes_build(ents) == ev and all(ents[k] == b'\0\0\0\0' for k in TEXT), 'debug.mes slots 11-20 not free'
for k, t in TEXT.items(): ents[k] = enc(t)
grow = sum(len(x) for x in ents) - sum(len(x) for x in mes_entries(ev))
assert set(ents[-1]) == {0} and len(ents[-1]) > grow
ents[-1] = ents[-1][:len(ents[-1]) - grow]
body = mes_build(ents); assert len(body) <= len(ev)
new_mes = body + bytes(len(ev) - len(body))

JOE = 0x442
REQ, CNT, HELD = 41, 42, 44
V_ANS, V_N = 2, 3
a = Asm(); L = a.new
a.sys(0x10)                                                  # event start
for base, cmd in ((20, 0x14), (23, 0x15)):                   # first-person camera: counters 20-25 = eye / target x128 (pm.c)
    for k in range(3): a.num(base + k); a.sys(0x95); a.num(128); a.emit('div')
    a.sys(cmd)
a.num(0); a.num(0); a.sys(0x5A)                              # cmd_5A(0, 0): hide the player (first person, as cmd_A0 does)
a.num(1); a.sys(0xDD); a.sys(0x00)                           # cmd_DD(1): the money window (as the shops)
done = L('done')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_joe_mes import FILE as MFILE, LINES, BASE as LBASE
MSG = {11: 'sell_intro', 12: 'buy_q', 13: 'poor', 14: 'bought', 15: 'sell_q', 16: 'what', 17: 'offer', 18: 'none', 19: 'later', 20: 'sold'}   # old debug.mes slot -> Joe's line in mukumuku.mes
def wait_msg(m, var=None):
    """cmd_04(mukumuku.mes, line, speaker 0x23 = Joe's character): the talk window shows his name and heart"""
    a.num(49); a.num(LINES[MSG[m]] - LBASE + 1); a.sys(0x93)   # counter 49 = the line (+1): pm.c's face and talk animation
    top = a.new('msg'); a.label(top); a.sys(0x00)
    if var is not None: a.addr(var)
    a.num(MFILE); a.num(LINES[MSG[m]]); a.num(0x23); a.sys(0x04)
    if var is not None: a.emit('assign')
    a.num(0); a.emit('cmp'); a.jz(top)
def say(m): wait_msg(m)
def ask(m, no):                                              # yes/no: answer 0 = yes; anything else -> no
    wait_msg(m, V_ANS); a.load(V_ANS); a.num(1); a.emit('cmp'); a.jnz(no)
def setc(c, v): a.num(c); a.num(v); a.sys(0x93)
def setc_var(c, var): a.num(c); a.load(var); a.sys(0x93)
def getc(c): a.num(c); a.sys(0x95)
def picker(open_cmd, wait_cmd, get_cmd):
    a.num(JOE); a.sys(open_cmd)
    top = L('pick'); a.label(top); a.sys(0x00); a.sys(wait_cmd); a.num(0); a.emit('cmp'); a.jz(top)
    a.addr(V_N); a.sys(get_cmd); a.emit('assign'); a.emit('pop')
def wait_while(c, v):
    top = L('wait'); a.label(top); a.sys(0x00); getc(c); a.num(v); a.emit('cmp'); a.jz(top)
bye, sell, no_coins, poor = L('bye'), L('sell'), L('none'), L('poor')
say(11)
ask(12, sell)
# ---- buy
picker(0xD5, 0xD6, 0xD7)
a.load(V_N); a.num(0); a.emit('cmp'); a.jz(bye)
setc_var(CNT, V_N); setc(REQ, 1); wait_while(REQ, 1)
getc(REQ); a.num(3); a.emit('cmp'); a.jz(poor)
say(14); a.jmp(done)
a.label(poor); say(13); a.jmp(done)
# ---- sell
a.label(sell)
ask(15, bye)
getc(HELD); a.num(0); a.emit('cmp'); a.jz(no_coins)
say(16)
ask(17, bye)
picker(0xD9, 0xDA, 0xDB)
a.load(V_N); a.num(0); a.emit('cmp'); a.jz(bye)
setc_var(CNT, V_N); setc(REQ, 4); wait_while(REQ, 4)
say(20); a.jmp(done)
a.label(no_coins); say(18); a.jmp(done)
a.label(bye); say(19)
a.label(done)
setc(REQ, 0)
setc(49, 0)
a.num(0); a.sys(0xDD)                                         # money window off
a.num(0); a.num(1); a.sys(0x5A)                              # player shown again
a.emit('end'); a.emit('end')
script = a.build()
ins, ch = parse(script); assert len(ins) == len(a.ins)

u = open(common_in, 'rb').read()
be = lambda b, o: struct.unpack_from('>I', b, o)[0]
root, hsize, dstart = be(u, 4), be(u, 8), be(u, 12)
n = be(u, root + 8); st = root + 12 * n
assert n == 108, 'expected the bench Common.arc (107 entries)'
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
assert [b for _, b in fs] == raws and len(fs) == 108
print('script: %d instructions; node %d = event %d' % (len(a.ins), len(fs), 300 + len(fs)))
for f in ('Common.arc', 'debug.mes'):
    b = open(os.path.join(outdir, f), 'rb').read(); print(f, hex(len(b)), hashlib.sha1(b).hexdigest()[:8])
