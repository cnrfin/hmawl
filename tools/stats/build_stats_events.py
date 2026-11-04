"""Level-up choice and stats view (step 2 of notes/stats_design.md).
Appends two scripts to Common.arc - event N (level-up choice) and N+1 (stats view), N = 300 + node count - and their texts
to free (4-byte) debug.mes entries.
usage: build_stats_events.py Common.arc debug.mes OUTDIR   (inputs: tools/joe/visit/data/Common.arc f8cdeca9, debug.mes
52b153f1 = the Joe talk build); needs scratchpad/event (scrasm, mesenc, clzc, clz, loadarc) via EVTOOLS.
Level-up: message "Level up! Lv <n0>" + an option list (01 41 04 00, options split by 01, end 00; as takakura.mes 113)
-> the answer (1..4) -> event counter 61 = 1..4 (pm.bin applies it). Stats: a message with number slots <2A:000n>
(0x2A nn 00 = slot nn, no padding; pm.bin fills them with func_80102300(*0x803491C4, n, v) before starting the event)."""
import sys, os, struct, hashlib
EV = os.environ.get('EVTOOLS', '/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/event')
sys.path.insert(0, EV); sys.path.insert(0, os.path.dirname(EV))
from scrasm import Asm
from clzc import clz_compress
from clz import clz_decompress
from mesenc import enc, mes_entries, mes_build
from loadarc import load, parse

common_in, mes_in, outdir = sys.argv[1:4]
os.makedirs(outdir, exist_ok=True)
DEBUG = 0x32
CHOICE_CNT = 61
OPTS = ['HP', 'Attack', 'Endurance', 'Luck']           # user: names only (the guide explains them)

from mesenc import P as PUNCT
def body(s):                                   # text -> glyph bytes, no terminator (mesenc.enc's rules)
    out = bytearray()
    for c in s:
        if c == '\n': out.append(0x01)
        elif c == ' ': out.append(0x02)
        elif 'A' <= c <= 'Z': out += struct.pack('>H', 0x800B + ord(c) - 65)
        elif 'a' <= c <= 'z': out += struct.pack('>H', 0x80D8 + ord(c) - 97)
        elif '0' <= c <= '9': out += struct.pack('>H', 0x8000 + ord(c) - 48)
        else: out += struct.pack('>H', PUNCT[c])
    return bytes(out)
def num(n): return bytes([0x2A, n, 0x00])           # 2A <slot> <pad width> (stats1 had them swapped: every number read slot 0)
def pad(b):
    b = bytearray(b) + b'\x00'
    while len(b) % 4: b.append(0)
    return bytes(b)
LVUP = pad(body('Level up!\nYou are now Lvl ') + num(0) + body('.\nWhich will you raise?') +
           b'\x01\x41\x04\x00' + b'\x01'.join(body(o) for o in OPTS))
STATS = pad(body('Lvl ') + num(0) + body('    EXP ') + num(1) + body(' / ') + num(2) + b'\x01' +
            body('HP ') + num(3) + body('    Attack ') + num(4) + b'\x01' +
            body('Endurance ') + num(5) + body('    Luck ') + num(6) + b'\x30')

ev = open(mes_in, 'rb').read(); ents = mes_entries(ev)
assert mes_build(ents) == ev
free = [i for i, e in enumerate(ents) if e == b'\0\0\0\0' and i < len(ents) - 1]
assert len(free) >= 2, 'no free debug.mes entries'
M_LV, M_ST = free[0], free[1]
ents[M_LV] = LVUP; ents[M_ST] = STATS
grow = sum(len(x) for x in ents) - sum(len(x) for x in mes_entries(ev))
assert set(ents[-1]) == {0} and len(ents[-1]) > grow, 'no zero padding at the end of debug.mes'
ents[-1] = ents[-1][:len(ents[-1]) - grow]
new_mes = mes_build(ents); new_mes += bytes(len(ev) - len(new_mes))
assert len(new_mes) == len(ev) and mes_entries(new_mes)[M_LV] == LVUP

def script_levelup():
    a = Asm(); L = a.new; V = 2
    a.sys(0x00)
    a.wait_msg(DEBUG, M_LV, V)
    done = L('done')
    for k in range(1, 5):
        nxt = L('n%d' % k)
        a.load(V); a.num(k); a.emit('cmp'); a.jnz(nxt)
        a.num(CHOICE_CNT); a.num(k); a.sys(0x93); a.jmp(done)
        a.label(nxt)
    a.num(CHOICE_CNT); a.num(1); a.sys(0x93)          # no answer (cancelled): HP
    a.label(done); a.emit('end'); a.emit('end')
    return a.build()
def script_stats():
    a = Asm(); V = 2
    a.sys(0x00); a.wait_msg(DEBUG, M_ST, V); a.emit('end'); a.emit('end')
    return a.build()
scripts = [script_levelup(), script_stats()]

u = open(common_in, 'rb').read()
be = lambda b, o: struct.unpack_from('>I', b, o)[0]
assert u[:4] == b'U\xaa8-'
root, hsize, dstart = be(u, 4), be(u, 8), be(u, 12)
n = be(u, root + 8); st = root + 12 * n
names = bytes(u[st:root + hsize])
nodes = [bytearray(u[root + 12 * i:root + 12 * i + 12]) for i in range(n)]
raws = [clz_decompress(u[be(u, root+12*i+4):be(u, root+12*i+4)+be(u, root+12*i+8)]) for i in range(1, n)]
first_event = 300 + n
al = lambda x: (x + 0x1F) & ~0x1F
name_off = len(names.rstrip(b'\0')) + 1
names2 = names[:name_off] + b'@\0'
for s in scripts:
    raws.append(s); nodes.append(bytearray(struct.pack('>III', name_off, 0, 0)))
struct.pack_into('>I', nodes[0], 8, len(nodes))
hlen = 12 * len(nodes) + len(names2)
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
for s in scripts: ins, ch = parse(s)
print('events: level-up %d, stats %d; debug.mes entries %d, %d' % (first_event, first_event + 1, M_LV, M_ST))
for f in ('Common.arc', 'debug.mes'):
    b = open(os.path.join(outdir, f), 'rb').read(); print(f, hex(len(b)), hashlib.sha1(b).hexdigest()[:8])
