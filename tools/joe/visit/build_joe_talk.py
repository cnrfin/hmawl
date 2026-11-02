"""Joe's talk while he walks or waits at the dig site: event 409 (Common.arc node 109, after the trade's 408)
+ lines in debug.mes 21-34. pm.c picks the line (counter 48) and does the friendship bookkeeping:
  1 first meeting (intro + bench hint), 2 bench hint, 3 at the dig site, 4 fall (crypto winter),
  5 a $JOE gift, 6 the 10th gift (full friendship), 7 a second gift on the same visit.
Gifts (5/6): the script takes the coin out of the player's hands (cmd_56).
usage: build_joe_talk.py Common.arc debug.mes OUTDIR   (inputs: the trade build)"""
import sys, os, struct, hashlib
EV = os.environ.get('EVTOOLS', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'event'))
sys.path.insert(0, EV); sys.path.insert(0, os.path.dirname(EV))
from scrasm import Asm
from clzc import clz_compress
from clz import clz_decompress
import mesenc
from mesenc import mes_entries, mes_build
from loadarc import load, parse
mesenc.P['$'] = 0x80FD
enc = mesenc.enc

common_in, mes_in, outdir = sys.argv[1:4]
os.makedirs(outdir, exist_ok=True)
FILE = 0x32
TEXT = {
    21: "Hey, I'm Joe.<wait><page>Ever heard of the\nEthereum blockchain?<wait><page>You can find some\ncrazy stuff on there.<wait>",
    22: "Come meet me by the\nbench by the bridge<wait><page>if you wanna trade\nsome memecoins.<wait>",
    23: "Y'know, I've heard\npeople mining $JOE\ncoin around here.<wait><page>That's why I came to\ncheck it out.<wait>",
    24: "Look kid, crypto\nwinter is coming and\nbears will be in full<wait><page>force. I won't be\naround until spring,<wait><page>so think about what\nyou wanna do with\nyour $JOE.<wait>",
    25: "Woah, a $JOE for me?\nYou get it, kid.<wait><page>HODL!<wait>",
    26: "Another $JOE? You're\na real one, kid.<wait><page>We're homies now.\nWAGMI.<wait>",
    27: "You already gave me\none today, kid.<wait><page>HODL the rest.<wait>",
}
ev = open(mes_in, 'rb').read()
ents = mes_entries(ev)
assert mes_build(ents) == ev and all(ents[k] == b'\0\0\0\0' for k in TEXT), 'debug.mes slots 21-27 not free'
for k, t in TEXT.items(): ents[k] = enc(t)
grow = sum(len(x) for x in ents) - sum(len(x) for x in mes_entries(ev))
assert set(ents[-1]) == {0} and len(ents[-1]) > grow
ents[-1] = ents[-1][:len(ents[-1]) - grow]
body = mes_build(ents); assert len(body) <= len(ev)
new_mes = body + bytes(len(ev) - len(body))

KIND = 48
a = Asm(); L = a.new
a.sys(0x10)
for base, cmd in ((20, 0x14), (23, 0x15)):                   # camera from counters 20-25 (pm.c), as the trade
    for k in range(3): a.num(base + k); a.sys(0x95); a.num(128); a.emit('div')
    a.sys(cmd)
a.num(0); a.num(0); a.sys(0x5A); a.sys(0x00)                 # player hidden (first person)
done = L('done')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_joe_mes import FILE as MFILE, LINES, BASE as LBASE
MSG = {21: 'intro', 22: 'hint', 23: 'dig', 24: 'winter', 25: 'gift', 26: 'gift', 27: 'gift_again'}   # old debug.mes slot -> Joe's line in mukumuku.mes
def wait_msg(m, var=None):
    """cmd_04(mukumuku.mes, line, speaker 0x23 = Joe's character): the talk window shows his name and heart"""
    a.num(49); a.num(LINES[MSG[m]] - LBASE + 1); a.sys(0x93)   # counter 49 = the line (+1): pm.c's face and talk animation
    top = a.new('msg'); a.label(top); a.sys(0x00)
    if var is not None: a.addr(var)
    a.num(MFILE); a.num(LINES[MSG[m]]); a.num(0x23); a.sys(0x04)
    if var is not None: a.emit('assign')
    a.num(0); a.emit('cmp'); a.jz(top)
def say(m): wait_msg(m)
def kind_is(k, target): a.num(KIND); a.sys(0x95); a.num(k); a.emit('cmp'); a.jz(target)
labels = {k: L('k%d' % k) for k in range(1, 8)}
for k in range(1, 8): kind_is(k, labels[k])
a.jmp(done)
a.label(labels[1]); say(21); say(22); a.jmp(done)
a.label(labels[2]); say(22); a.jmp(done)
a.label(labels[3]); say(23); a.jmp(done)
a.label(labels[4]); say(24); a.jmp(done)
def pocket():                                                 # counter 50 = 1: pm.c plays Joe's take-and-pocket, then sets 0
    a.num(50); a.num(1); a.sys(0x93)
    top = L('pk'); a.label(top); a.sys(0x00); a.num(50); a.sys(0x95); a.num(1); a.emit('cmp'); a.jz(top)
a.label(labels[5]); a.sys(0x56); pocket(); say(25); a.jmp(done)        # cmd_56: take the coin out of the hands
a.label(labels[6]); a.sys(0x56); pocket(); say(26); a.jmp(done)
a.label(labels[7]); say(27); a.jmp(done)
a.label(done)
a.num(KIND); a.num(0); a.sys(0x93)
a.num(49); a.num(0); a.sys(0x93)
a.num(0); a.num(1); a.sys(0x5A)                              # player shown again
a.emit('end'); a.emit('end')
script = a.build()
ins, ch = parse(script); assert len(ins) == len(a.ins)

u = open(common_in, 'rb').read()
be = lambda b, o: struct.unpack_from('>I', b, o)[0]
root, hsize, dstart = be(u, 4), be(u, 8), be(u, 12)
n = be(u, root + 8); st = root + 12 * n
assert n == 109, 'expected the trade Common.arc (108 entries)'
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
assert [b for _, b in fs] == raws and len(fs) == 109
print('script: %d instructions; node %d = event %d' % (len(a.ins), len(fs), 300 + len(fs)))
for f in ('Common.arc', 'debug.mes'):
    b = open(os.path.join(outdir, f), 'rb').read(); print(f, hex(len(b)), hashlib.sha1(b).hexdigest()[:8])
