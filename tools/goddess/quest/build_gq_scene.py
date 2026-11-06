#!/usr/bin/env python3
"""The goddess's first summoning (gq6): event 412 appended to Common.arc + her lines (batch 1, A1-A10, as the user
edited them) in free debug.mes entries, and the shot table (gq_scene.h) from tools/goddess/scene/spring_scene.json
(the Spring Scene Director's export). pm.c (gd_frame) raises / sinks her, plays her motions, moves the event camera
every frame along each shot's start -> end, flashes, sets her face per line; the field slot (Pool B's wind) is left alone;
plays Marin Jazz on the event slot 3 the way vanilla events do (cmd_2F(song) loads its group, cmd_32(song, 3) plays it,
cmd_41(slot, vol, seconds) fades). Script and pm.c talk through event counters (x128 in the script):
  26 cue (script -> pm.c): n = shot n starts; 32 + n = shot n's after-the-lines action (the sink)
  27 done (pm.c -> script): = the cue, once its timed part (min seconds / pause / action) is over
  28 year 1 (pm.c -> script): 1 = say A9 (the year-1 line)
  29 face (script -> pm.c): her expression for the next line (FACES; settings.faces in the JSON); 0 = her own
  20-25 camera eye / target x 128 (pm.c, for the script's first cmd_14 / cmd_15; no cmd_13: it pins the look-at
        on a character - the gq5 angle bug)
usage: build_gq_scene.py Common.arc debug.mes OUTDIR [scene.json]  (inputs: stats1 Common.arc (events to 411), the gq4
debug.mes); needs scratchpad/event (scrasm, mesenc, clzc, clz, loadarc) via EVTOOLS. Writes Common.arc, debug.mes,
gq_scene.h."""
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
SCENE = json.load(open(sys.argv[4] if len(sys.argv) > 4 else os.path.join(HERE, '..', 'scene', 'spring_scene.json')))
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

CUE, DONE, YEAR1, FACE = 26, 27, 28, 29
FACES = {'neutral': 2, 'closed': 1, 'smile': 3, 'joy': 4, 'pout': 5, 'smug': 6, 'blush': 7, 'soft': 8}   # pm.c GS_FACE[]
FPS = 60
SHOTS = SCENE['shots']; ST = SCENE['settings']
assert len(SHOTS) <= 31
def box_t(b): return 1.2 + len(''.join(b.split())) * 0.055          # the editor's reading-time guess
def line_t(k): return sum(box_t(b) for b in LINES[k].replace('\r', '').split('\n\n') if b.strip())
def parts(sh):                                                      # as the editor's shotParts()
    lt = sum(line_t(k) for k in sh['lines'])
    act = float(sh['actionSeconds'] or 3) if sh['action'] in ('rise', 'sink') else 0
    after = sh['actionWhen'] == 'afterLines'
    body = float(sh['pause'] or 0) + lt + (act if after else 0)
    return max(float(sh['seconds'] or 0), body, 0 if after else act, 0.5), act, after
a = Asm(); L = a.new
a.sys(0x10); a.sys(0x00)                                     # event start
def getc(c): a.num(c); a.sys(0x95)
def setc(c, v): a.num(c); a.num(v); a.sys(0x93)
def frame(): a.sys(0x00)
def shot():                                                  # camera from counters 20-25 (x128), once: pm.c moves it
    for base, cmd in ((20, 0x14), (23, 0x15)):
        for k in range(3): a.num(base + k); a.sys(0x95); a.num(128); a.emit('div')
        a.sys(cmd)
SONGS = {'Marin Jazz': 1}                                  # SNGList / the record table: Marin Jazz = song 1 (RECORD05)
SONG = SONGS[ST.get('music', 'Marin Jazz')]
def fx(v): a.emit('push', int(round(v * 128)) & 0xFFFFFFFF, 0x1300)   # '#' constants, as vanilla scripts push them
def fade(slot, vol, secs): a.num(slot); fx(vol); fx(secs); a.sys(0x41)
def song_load(n): fx(n); a.sys(0x2F); a.emit('pop')
def song_play(n): fx(n); a.num(3); a.sys(0x32); a.emit('pop')
def wait_done(v):
    top = L('wait'); a.label(top); frame(); getc(DONE); a.num(v); a.emit('cmp'); a.jnz(top)
def line(k):                                                 # her face for the line, its voice, the line
    setc(FACE, FACES[ST.get('faces', {}).get(k, 'neutral')])
    if k in ST.get('voices', {}): fx(ST['voices'][k]); a.sys(0x30); a.emit('pop')     # cmd_30: SFXList sound
    a.wait_msg(FILE, ids[k])
def say(k):
    if k == 'A9':                                            # year 1 only
        skip = L('noy1'); getc(YEAR1); a.num(1); a.emit('cmp'); a.jnz(skip); line(k); a.label(skip)
    else: line(k)
MUSIC = ST.get('musicFade') and ST.get('musicShot')
if MUSIC: fade(3, 0, 0); song_load(SONG)                     # (vanilla: slot 3 silent, then the group loaded)
for n, sh in enumerate(SHOTS, 1):
    dur, act, after = parts(sh)
    setc(CUE, n); frame(); frame()
    if n == 1: shot()
    if MUSIC and n == ST['musicShot']: song_play(SONG); fade(3, 127, 0.5)
    if not sh['lines'] or float(sh['pause'] or 0) > 0 or (act and not after): wait_done(n)
    for k in sh['lines']: say(k)
    if act and after:
        if MUSIC and sh['action'] == 'sink': fade(3, 0, 2.5)
        setc(CUE, 32 + n); wait_done(32 + n)
setc(CUE, 0); setc(DONE, 0); setc(FACE, 0)
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
CODE = {'goddess': 0, 'farmer': 1, 'pair': 2}
MOT = {'idle': 0, 'walk': 1, 'holding': 2, 'explain': 4, 'plead (bow)': 6, 'crouch': 8}   # Celia's clips (hg_0.anm.arc)
ACT = {'under': 0, 'stand': 1, 'rise': 2, 'sink': 3}
rows = []
for n, sh in enumerate(SHOTS, 1):
    dur, act, after = parts(sh)
    if sh['lines']: hold = float(sh['pause'] or 0) + (act if act and not after else 0)
    else: hold = max(float(sh['seconds'] or 0), act if not after else 0, 0.5)
    look = sh['subject'] if sh['look'] == 'subject' else sh['look']
    k = [sh['start'][x] for x in ('yaw', 'dist', 'height', 'aim')] + [sh['end'][x] for x in ('yaw', 'dist', 'height', 'aim')]
    rows.append('    { %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, { %s } },   /* %d %s */' % (CODE[sh['subject']], CODE[look],
        sh['ease'] != 'linear', MOT.get(sh['motion'], 0), ACT[sh['action']], after, int(bool(sh.get('splash'))) | int(bool(sh.get('flash'))) << 1 | int(sh.get('eyes') == 'closed') << 2,
        round(dur * FPS), round(hold * FPS), round(act * FPS), ', '.join(repr(float(v)) + 'f' for v in k), n, sh['name']))
h = ['/* generated by tools/goddess/quest/build_gq_scene.py from tools/goddess/scene/spring_scene.json: the first summoning */',
     '#define GQ_SCENE_EVENT %d' % EVENT, '#define GQ_MSG_BUSY 0x%X' % BUSY, '#define GQ_C_CUE  %d' % CUE, '#define GQ_C_DONE %d' % DONE,
     '#define GQ_C_YEAR1 %d' % YEAR1, '#define GQ_C_FACE %d' % FACE, '#define GS_N %d' % len(SHOTS), '#define GS_LETTERBOX %d' % int(bool(ST.get('letterbox'))),
     '#define GS_MUSIC_FADE %d' % int(bool(ST.get('musicFade'))), '#define GS_MUSIC_SHOT %d' % int(ST.get('musicShot') or 0),
     '#define GS_END_WHITE %d' % int(ST.get('endFade') == 'white'),
     '/* subject, look (0 her, 1 him, 2 midpoint), smooth, motion, action (0 under, 1 stand, 2 rise, 3 sink), after the lines,',
     '   fx (1 splash, 2 white flash at the start, 4 eyes closed), glide frames, hold frames (pm.c sets "done" then), action frames; start yaw dist height aim, end ... */',
     '#ifdef GQ_SHOTS', 'static const struct gshot { signed char subj, look, smooth, motion, act, after, fx; short glide, hold, actf; float k[8]; } GSHOT[GS_N] = {']
h += rows + ['};', '#endif']
open(os.path.join(outdir, 'gq_scene.h'), 'w').write('\n'.join(h) + '\n')
print('event %d, %d instructions; lines' % (EVENT, len(a.ins)), ids)
for f in ('Common.arc', 'debug.mes'):
    b = open(os.path.join(outdir, f), 'rb').read(); print(f, len(b), hashlib.sha1(b).hexdigest()[:8])
