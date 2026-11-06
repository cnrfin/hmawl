#!/usr/bin/env python3
"""Breeze, battle take 13: a triplet (12/8-feel) drive, after the user's reference (the FFX battle MIDI's devices, not
its notes): every beat in three, a hemiola cross-rhythm (strings and the snare backbeat every 2 triplets = 3 against 2),
a churning triplet bass with octave skips, a running triplet arpeggio under the A section, brass hits on the dotted
"every 4 triplets" grid in B. The harmony is breeze_heroic.py's chord plan unchanged (bars 5-36: the user-approved
v12 loop; intro C - C - Ab - Bb), the melody the same Breeze line with its offbeat 8ths swung onto the last triplet.
Same game instruments (EVENT07 lead, bank-10/20/7/18/8 presets in hmawl_music.sf2). 4-bar intro, then a 32-bar loop.
usage: breeze_triplet.py BREEZE.mid OUT.mid [bpm]"""
import sys, mido, random
LEAD = (10, 0)
PATCH = {0: LEAD, 4: LEAD, 1: (20, 1), 2: (7, 5), 3: (18, 0), 9: (8, 5)}
VOL = {0: 84, 4: 58, 1: 92, 2: 78, 3: 80, 9: 82}
CH = {0: (0, 4, 7), 7: (7, 11, 2), 5: (5, 9, 0), 9: (9, 0, 4), 8: (8, 0, 3), 10: (10, 2, 5), 2: (2, 5, 9), 4: (4, 7, 11), 3: (3, 7, 10)}
T = 1 / 3                                                   # one triplet 8th, in beats
def read(f):
    m = mido.MidiFile(f); tpb = m.ticks_per_beat; t = 0; on = {}; out = []
    for x in m.tracks[1]:
        t += x.time
        if x.type == 'note_on' and x.velocity > 0: on[x.note] = (t, x.velocity)
        elif x.type in ('note_off', 'note_on') and x.note in on:
            s, v = on.pop(x.note); out.append((s / tpb, (t - s) / tpb, x.note, v))
    return sorted(out)
def swing(s):                                               # straight grid -> triplet grid
    b = int(s); f = s - b
    q = min((0, 0.25, 0.5, 0.75, 1.0), key=lambda x: abs(x - f))
    return b + {0: 0, 0.25: T, 0.5: 2 * T, 0.75: 2.5 * T, 1.0: 1}[q]
def main():
    src, dst = sys.argv[1:3]; BPM = int(sys.argv[3]) if len(sys.argv) > 3 else 132
    notes = read(src); B0, B1, INTRO, BSEC = 4, 36, 4, 20; rnd = random.Random(13)
    lows = {}
    for s, d, n, v in notes:
        b = int(s // 4)
        if B0 <= b < B1: lows[b] = min(lows.get(b, 200), n)
    roots = {b: (0 if lows.get(b, 48) % 12 == 4 else lows.get(b, 48) % 12) for b in range(B0, B1)}
    roots[31] = 10
    H = lambda r, t, b=None: (r, t, r if b is None else b)
    HARM = {6: [H(0, CH[0]), H(7, CH[7], 11)], 7: [H(9, CH[9]), H(0, (0, 4, 10), 10)], 8: [H(5, CH[5], 9), H(5, CH[5])],
            28: [H(5, CH[5], 9), H(7, CH[7], 11)], 29: [H(0, CH[0]), H(2, (2, 6, 9))],
            30: [H(0, CH[0], 4), H(8, CH[8])], 31: [H(10, CH[10]), H(7, (7, 11, 5))]}
    IROOT = [0, 0, 8, 10]
    def at(b): return (b - B0 + INTRO) * 4
    ev = []
    for s, d, n, v in notes:                                # melody, swung; doubled an octave down
        b = int(s // 4)
        if not (B0 <= b < B1) or n < 64 and not (n >= 63 and (s % 1) > 0.4) or n == lows.get(b): continue
        beat = at(b) + swing(s % 4); end = at(b) + swing(min(s % 4 + d, 4.0)) if s % 4 + d <= 4 else at(b) + s % 4 + d
        dur = max(T * 0.8, min(end - beat, 2.0) * 0.94)
        vel = 106 if (s % 1) < 0.1 else 96
        ev.append((beat, dur, 0, n, vel)); ev.append((beat, dur, 4, n - 12, vel - 24))
    for bar in range(B0 - INTRO, B1):
        intro = bar < B0; B = bar >= BSEC; base = at(bar); lb = bar - B0
        r = IROOT[bar - (B0 - INTRO)] if intro else roots.get(bar, 0); t = CH.get(r, CH[0])
        halves = (HARM.get(lb) if not intro else None) or [H(r, t), H(r, t)]
        def half(k): return halves[0 if k < 6 else 1]                      # k = triplet 0..11
        def lo_of(p): return 36 + p if p <= 7 else 24 + p
        # bass: churning triplets (FFX-style onsets 0 .67 1 1.33 2 2.67 3 3.33), octave skips, fifth before the bar line
        for k in (0, 2, 3, 4, 6, 8, 9, 10):
            hr, ht, hb = half(k); lo = lo_of(hb)
            n = lo + (12 if k in (2, 8) else 7 if k == 10 and hb == hr else 0)
            ev.append((base + k * T, T * 0.9, 1, n, 110 if k in (0, 6) else 92 if k in (3, 9) else 84))
        # strings: hemiola stabs every 2 triplets (A: soft, under the arpeggio; B and intro: the main drive)
        for k in range(0, 12, 2):
            hr, ht, hb = half(k); vv = (96 if k in (0, 6) else 84) if (B or intro) else 70
            for p in ht: ev.append((base + k * T, T * 1.5, 3, 60 + (p if p >= 4 else p + 12), vv))
        if intro:                                            # rising triplet arpeggio climb, a step higher each bar
            for k in range(12):
                hr, ht, hb = half(k); tones = sorted(60 + (p if p >= 4 else p + 12) for p in ht)
                n = tones[k % 3] + 12 * (k // 6) + (bar - (B0 - INTRO)) * 2
                ev.append((base + k * T, T * 0.9, 2, n, 70 + k * 3 + (bar - (B0 - INTRO)) * 4))
        elif not B:                                          # A: running triplet arpeggio (horns, light), up and back
            for k in range(12):
                hr, ht, hb = half(k); tones = sorted(72 + (p if p >= 4 else p + 12) - 12 for p in ht)
                seq = tones + [tones[0] + 12] + tones[::-1][1:]       # 1 3 5 8 5 3
                ev.append((base + k * T, T * 0.85, 2, seq[k % 6], 66 + (10 if k % 3 == 0 else 0)))
        else:                                                # B: brass hits on the dotted grid (every 4 triplets) + held top
            for k, dd, vv in ((0, 4 * T * 0.9, 104), (4, 4 * T * 0.9, 94), (8, 4 * T * 0.9, 98)):
                hr, ht, hb = half(k)
                for p in ht: ev.append((base + k * T, dd, 2, 60 + (p if p >= 4 else p + 12) - 12, vv * 0.74))
        # drums: triplet snare ghosts, the hemiola backbeat (0.67 / 2 / 3.33), tom 'kick' on 1 and 3
        for k in range(12):
            if k in (2, 6, 10): continue
            ev.append((base + k * T, 0.08, 9, 40, 50 + (10 if k % 3 == 0 else 0)))
        for k in (2, 6, 10): ev.append((base + k * T, 0.12, 9, 40, 112 if B or intro else 104))
        ev.append((base, 0.3, 9, 41, 106)); ev.append((base + 6 * T, 0.3, 9, 41, 96))
        if B: ev.append((base + 9 * T, 0.3, 9, 41, 88))
        if (not intro and lb % 4 == 3) or bar == B0 - 1:     # triplet tom fill into the next phrase
            for j, n in enumerate((45, 45, 43, 43, 41, 41)): ev.append((base + (6 + j) * T, 0.1, 9, n, 84 + j * 5))
        if bar >= B0 and lb % 8 == 0: ev.append((base, 1.0, 9, 49, 100))
    for bar in range(B1 - 4, B1):                            # build-up: snare on every beat over the last 4 bars
        for k in range(4): ev.append((at(bar) + k, 0.15, 9, 40, 100 + 3 * (bar - (B1 - 4))))
    ev = [(max(0, b + (0 if ch == 9 else rnd.uniform(-0.01, 0.01))), d, ch, n, v) for b, d, ch, n, v in ev]
    L0 = INTRO * 4; LOOP = (B1 - B0) * 4; END = L0 + LOOP
    m = mido.MidiFile(ticks_per_beat=480); tr = mido.MidiTrack(); m.tracks.append(tr)
    tr.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(BPM)))
    for ch, (bank, prog) in PATCH.items():
        tr += [mido.Message('control_change', channel=ch, control=0, value=bank), mido.Message('program_change', channel=ch, program=prog),
               mido.Message('control_change', channel=ch, control=7, value=VOL[ch]),
               mido.Message('control_change', channel=ch, control=11, value=110)]
    msgs = []
    for beat, dur, ch, n, v in ev:
        msgs.append((int(beat * 480), 1, mido.Message('note_on', channel=ch, note=n, velocity=int(max(1, min(127, v))))))
        msgs.append((int((beat + dur) * 480), 0, mido.Message('note_off', channel=ch, note=n, velocity=0)))
    msgs.sort(key=lambda x: (x[0], x[1])); tt = 0
    for tick, _, msg in msgs: msg.time = tick - tt; tt = tick; tr.append(msg)
    m.save(dst); print('%d bpm: intro %.3f s, loop %.3f s (%d bars)' % (BPM, L0 * 60 / BPM, LOOP * 60 / BPM, LOOP // 4))
if __name__ == '__main__': main()
