#!/usr/bin/env python3
"""Breeze (HMAWL) re-arranged as an OoT-style battle loop, on the game's own instruments (hmawl_music.sf2).
Melody and harmony from the Breeze MIDI (bars 4-35 = A + B); new parts in the battle idiom: C minor (E->Eb,
A->Ab, B kept over G), 200 bpm, octave-bouncing 8th bass with a semitone push, cello root/b2 rocking,
viola 16th tremolo on the chord's 3rd + 5th, soft continuous 16th snare with accents, trumpet melody.
usage: arrange_breeze_battle.py BREEZE.mid OUT.mid"""
import sys, mido
BPM = 200
CH = dict(mel=0, bass=1, cello=2, viola=3, snare=9)
PATCH = {0: (4, 3), 1: (20, 1), 2: (7, 5), 3: (18, 0), 9: (8, 5)}   # (bank, program), as the OoT render (game2.mid)
VOL = {0: 100, 1: 80, 2: 64, 3: 70, 9: 34}
def read(f):
    m = mido.MidiFile(f); tpb = m.ticks_per_beat; t = 0; on = {}; out = []
    for x in m.tracks[1]:
        t += x.time
        if x.type == 'note_on' and x.velocity > 0: on[x.note] = (t, x.velocity)
        elif x.type in ('note_off', 'note_on') and x.note in on:
            s, v = on.pop(x.note); out.append((s / tpb, (t - s) / tpb, x.note, v))
    return sorted(out)
def minor(n, root):
    pc = n % 12
    if pc == 4: return n - 1                       # E -> Eb
    if pc == 9: return n - 1                       # A -> Ab
    return n
CHORD = {0: (0, 3, 7), 7: (7, 11, 2), 5: (5, 8, 0), 3: (8, 0, 3), 4: (0, 3, 7)}   # pc of root -> chord pcs (C minor)
def main():
    src, dst = sys.argv[1:3]; notes = read(src)
    BAR0, BAR1, INTRO = 4, 36, 2
    # per bar: root from the lowest note, melody = notes >= F4 (bars 7/11 also have E4/G4 answers: >= E4 off-beat)
    ev = []                                        # (beat, dur, ch, note, vel)
    roots = {}
    for s, d, n, v in notes:
        b = int(s // 4)
        if BAR0 <= b < BAR1: roots[b] = min(roots.get(b, 200), n)
    def at(bar): return (bar - BAR0 + INTRO) * 4
    for s, d, n, v in notes:
        b = int(s // 4)
        if not (BAR0 <= b < BAR1) or n < 64 and not (n >= 63 and (s % 1) > 0.4): continue
        if n == roots.get(b): continue
        r = roots[b] % 12; beat = at(b) + s % 4
        dur = min(d, 1.5) * 0.85
        ev.append((beat, dur, CH['mel'], minor(n, r), min(127, 88 + (12 if s % 1 < 0.1 else 0))))
    # harmony layers, intro bars use the first bar's root (C)
    for bar in range(BAR0 - INTRO, BAR1):
        rn = roots.get(max(bar, BAR0), 48); r = rn % 12; base = at(bar)
        if r == 4: r = 0
        lo = 36 + r if r <= 7 else 24 + r          # bass root octave 2
        for k in range(8):                          # bass: root / octave bounce, b2 push on the last 8th
            n = lo + (12 if k % 2 else 0)
            if k == 7: n = lo + 1
            ev.append((base + k * 0.5, 0.42, CH['bass'], n, 96 if k % 2 == 0 else 78))
        for k in range(8):                          # cello: root / b2 rocking an octave up
            ev.append((base + k * 0.5, 0.45, CH['cello'], lo + 12 + (1 if k % 4 == 3 else 0), 70))
        c = CHORD.get(r, CHORD[0]); vt = [60 + c[1] if c[1] >= 5 else 72 + c[1], 60 + c[2] if c[2] >= 5 else 72 + c[2]]
        for k in range(16):                         # viola tremolo
            for n in vt: ev.append((base + k * 0.25, 0.22, CH['viola'], n, 52 + (10 if k % 4 == 0 else 0)))
        for k in range(16):                         # snare: soft 16ths, accents on the beats
            ev.append((base + k * 0.25, 0.1, CH['snare'], 40, 46 + (28 if k % 4 == 0 else 0) + (18 if k in (0, 8) else 0)))
    m = mido.MidiFile(ticks_per_beat=480); tr = mido.MidiTrack(); m.tracks.append(tr)
    tr.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(BPM)))
    for ch, (bank, prog) in PATCH.items():
        tr += [mido.Message('control_change', channel=ch, control=0, value=bank), mido.Message('program_change', channel=ch, program=prog),
               mido.Message('control_change', channel=ch, control=7, value=VOL[ch])]
    msgs = []
    for beat, dur, ch, n, v in ev:
        msgs.append((int(beat * 480), 1, mido.Message('note_on', channel=ch, note=n, velocity=v)))
        msgs.append((int((beat + dur) * 480), 0, mido.Message('note_off', channel=ch, note=n, velocity=0)))
    msgs.sort(key=lambda x: (x[0], x[1])); t = 0
    for tick, _, msg in msgs: msg.time = tick - t; t = tick; tr.append(msg)
    m.save(dst); print('%d notes, %d bars, %.1f s' % (len(ev), BAR1 - BAR0 + INTRO, (BAR1 - BAR0 + INTRO) * 4 * 60 / BPM))
if __name__ == '__main__': main()
