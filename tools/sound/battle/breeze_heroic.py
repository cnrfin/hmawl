#!/usr/bin/env python3
"""Breeze, heroic / epic arrangement (battle theme take 4): the Breeze melody (bars 4-35 of the MIDI, = the
user's recording from 0:05) in C major at 184 bpm on EVENT07 p0 (bank 10 prog 0), doubled an octave down;
strings in a heroic gallop (8th + two 16ths) on the chord tones, march bass (root / octave), horn pads with rising
runs into each phrase, snare march (2 and 4, rolls into phrase ends), toms on downbeats, a cymbal on big arrivals;
the B section's Ab/Eb turn lifted to bVI - bVII - I (Ab - Bb - C).
usage: breeze_heroic.py BREEZE.mid OUT.mid"""
import sys, mido
BPM = 184
LEAD = (10, 0)
PATCH = {0: LEAD, 4: LEAD, 1: (20, 1), 2: (7, 5), 3: (18, 0), 9: (8, 5)}
VOL = {0: 108, 4: 74, 1: 86, 2: 66, 3: 70, 9: 46}
CH = {0: (0, 4, 7), 7: (7, 11, 2), 5: (5, 9, 0), 9: (9, 0, 4), 8: (8, 0, 3), 10: (10, 2, 5), 2: (2, 5, 9), 4: (4, 7, 11), 3: (3, 7, 10)}
def read(f):
    m = mido.MidiFile(f); tpb = m.ticks_per_beat; t = 0; on = {}; out = []
    for x in m.tracks[1]:
        t += x.time
        if x.type == 'note_on' and x.velocity > 0: on[x.note] = (t, x.velocity)
        elif x.type in ('note_off', 'note_on') and x.note in on:
            s, v = on.pop(x.note); out.append((s / tpb, (t - s) / tpb, x.note, v))
    return sorted(out)
def main():
    src, dst = sys.argv[1:3]; notes = read(src); B0, B1, INTRO = 4, 36, 2
    lows = {}
    for s, d, n, v in notes:
        b = int(s // 4)
        if B0 <= b < B1: lows[b] = min(lows.get(b, 200), n)
    def root(b):
        r = lows.get(b, 48) % 12
        return 0 if r == 4 else r                  # C/E -> C
    roots = {b: root(b) for b in range(B0, B1)}
    roots[31] = 10                                 # bVII (Bb) after the Ab/Eb bars -> lift into the return
    def at(b): return (b - B0 + INTRO) * 4
    ev = []
    for s, d, n, v in notes:                       # melody (as the v1 pick: top line), legato-ish, accented downbeats
        b = int(s // 4)
        if not (B0 <= b < B1) or n < 64 and not (n >= 63 and (s % 1) > 0.4) or n == lows.get(b): continue
        beat = at(b) + s % 4; dur = min(d, 2.0) * 0.95; vel = 112 if s % 1 < 0.1 else 96
        ev.append((beat, dur, 0, n, vel)); ev.append((beat, dur, 4, n - 12, vel - 24))
    for bar in range(B0 - INTRO, B1):
        r = roots.get(max(bar, B0), 0); base = at(bar); t = CH.get(r, CH[0])
        lo = 36 + r if r <= 7 else 24 + r
        for k, (o, d) in enumerate(((0, 1.5), (12, 0.5), (0, 1.5), (12, 0.5))):     # march bass
            ev.append((base + k * 1.0, 0.9 if k % 2 == 0 else 0.45, 1, lo + o, 104 if k == 0 else 88))
        tones = [60 + (p if p >= 4 else p + 12) for p in t]
        for beat in range(4):                                                     # gallop: 8th + 16th + 16th
            for off, dd in ((0, 0.45), (0.5, 0.22), (0.75, 0.22)):
                for n in tones[1:]: ev.append((base + beat + off, dd, 3, n, 70 + (14 if off == 0 else 0)))
        for n in tones: ev.append((base, 3.9, 2, n - 12, 62))                    # horn pad
        if bar >= B0 and (bar - B0) % 4 == 3:                                     # rising run into the next phrase
            nxt = CH.get(roots.get(bar + 1, 0), CH[0]); tgt = 60 + nxt[0] + 12
            for k in range(8): ev.append((base + 2 + k * 0.25, 0.24, 2, tgt - 8 + [0, 2, 4, 5, 7, 9, 11, 12][k] - 4, 80))
        for k in range(4):                                                        # snare march
            if k in (1, 3): ev.append((base + k, 0.15, 9, 40, 92))
            ev.append((base + k + 0.5, 0.1, 9, 40, 40))
        if bar >= B0 and (bar - B0) % 4 == 3:
            for k in range(8): ev.append((base + 2 + k * 0.25, 0.1, 9, 40, 60 + k * 7))   # roll into the phrase
        ev.append((base, 0.3, 9, 45, 100)); ev.append((base + 2, 0.3, 9, 43, 80))         # toms
        if bar >= B0 and (bar - B0) % 8 == 0: ev.append((base, 1.0, 9, 49, 96))           # cymbal on arrivals
    m = mido.MidiFile(ticks_per_beat=480); tr = mido.MidiTrack(); m.tracks.append(tr)
    tr.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(BPM)))
    for ch, (bank, prog) in PATCH.items():
        tr += [mido.Message('control_change', channel=ch, control=0, value=bank), mido.Message('program_change', channel=ch, program=prog),
               mido.Message('control_change', channel=ch, control=7, value=VOL[ch])]
    msgs = []
    for beat, dur, ch, n, v in ev:
        msgs.append((int(beat * 480), 1, mido.Message('note_on', channel=ch, note=n, velocity=max(1, min(127, v)))))
        msgs.append((int((beat + dur) * 480), 0, mido.Message('note_off', channel=ch, note=n, velocity=0)))
    msgs.sort(key=lambda x: (x[0], x[1])); tt = 0
    for tick, _, msg in msgs: msg.time = tick - tt; tt = tick; tr.append(msg)
    nb = B1 - B0 + INTRO; m.save(dst); print('%d bars, %.1f s' % (nb, nb * 4 * 60 / BPM))
if __name__ == '__main__': main()
