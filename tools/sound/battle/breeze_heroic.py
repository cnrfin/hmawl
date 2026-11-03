#!/usr/bin/env python3
"""Breeze, heroic / epic arrangement (battle theme take 6: OoT 16th snare drive in A, half-time drums in B, per-bar calibrated level so the loop seam is smooth): the Breeze melody (bars 4-35 of the MIDI, = the
user's recording from 0:05) in C major at 184 bpm on EVENT07 p0 (bank 10 prog 0), doubled an octave down;
strings in a heroic gallop (8th + two 16ths) on the chord tones, march bass (root / octave), horn pads with rising
runs into each phrase, snare march (2 and 4, rolls into phrase ends), toms on downbeats, a cymbal on big arrivals;
the B section's Ab/Eb turn lifted to bVI - bVII - I (Ab - Bb - C).
usage: breeze_heroic.py BREEZE.mid OUT.mid [cycles]"""
import sys, mido, math, random
BPM = 184
LEAD = (10, 0)
PATCH = {0: LEAD, 4: LEAD, 1: (20, 1), 2: (7, 5), 3: (18, 0), 9: (8, 5)}
VOL = {0: 108, 4: 74, 1: 86, 2: 66, 3: 70, 9: 74}
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
    src, dst = sys.argv[1:3]; cycles = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    notes = read(src); B0, B1, INTRO = 4, 36, 2; BSEC = 20; rnd = random.Random(5)
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
    def sec(b, frac=0.0):                         # section dynamics, continuous and periodic over the loop
        x = (b - B0) + frac                         # bars into the loop (0..32); intro = the loop's start level
        if x < 0: return 0.93
        pts = [(0, 0.93), (16, 0.97), (28, 1.0), (32, 1.0)]                        # gentle build, no drop at the seam
        if x >= 30: pts = [(30, 1.0), (32, 0.93)]                                  # ease home over the last 2 bars
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            if x0 <= x <= x1:
                u = (x - x0) / (x1 - x0); u = u * u * (3 - 2 * u); return y0 + (y1 - y0) * u
        return pts[-1][1]
    TRIM = [3.3, 0.3, -0.7, 0.9, 0.2, 0.1, -0.2, -0.2, 0.1, 3.6, 4.6, 1.1, 0.5, 3.8, 5.2, 0.7, 0.8, 1.0, 0.7, 0.5, 0.1, 0.1, 0.4, 0.2, -0.3, -1.1, -0.4, -1.2, -0.8, -1.2, -0.9, 0.2]   # per-bar dB, calibrated: smooth level across the seam
    def trim(b): return 10 ** (TRIM[(b - B0) % 32] / 40) if b >= B0 else 10 ** (TRIM[0] / 40)
    ev = []
    for s, d, n, v in notes:                       # melody (as the v1 pick: top line), legato-ish, accented downbeats
        b = int(s // 4)
        if not (B0 <= b < B1) or n < 64 and not (n >= 63 and (s % 1) > 0.4) or n == lows.get(b): continue
        beat = at(b) + s % 4; dur = min(d, 2.0) * 0.95
        vel = (100 if s % 1 < 0.1 else 88) + (n - 72) * 1.2 + min(d, 2) * 6      # contour: high and long notes speak up
        vel = vel * sec(b, (s % 4) / 4) + rnd.uniform(-5, 5)
        ev.append((beat, dur, 0, n, vel)); ev.append((beat, dur, 4, n - 12, vel - 22))
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
        sb = max(bar, B0); dyn = sec(sb)
        if bar >= BSEC:                                                           # B: half time
            ev.append((base + 2, 0.2, 9, 40, 116))
            for k in range(8):
                if k != 4: ev.append((base + k * 0.5, 0.1, 9, 40, 44 + (8 if k % 2 else 0)))
        else:                                                                     # A (and intro): OoT-style 16th drive
            for k in range(16):
                ev.append((base + k * 0.25, 0.08, 9, 40, (100 if k % 4 == 0 else 64 + (8 if k % 2 else 0)) * (0.92 + 0.08 * (k in (4, 12)))))
        if bar >= B0 and (bar - B0) % 4 == 3:
            for k in range(8): ev.append((base + 2 + k * 0.25, 0.1, 9, 40, 60 + k * 7))   # roll into the phrase
        if bar >= BSEC: ev.append((base, 0.3, 9, 45, 108)); ev.append((base + 1.5, 0.3, 9, 45, 84))   # half-time toms: 1, and of 2
        else: ev.append((base, 0.3, 9, 45, 100)); ev.append((base + 2, 0.3, 9, 43, 80))
        if bar >= B0 and (bar - B0) % 8 == 0: ev.append((base, 1.0, 9, 49, 96))           # cymbal on arrivals
    # bar -> source bar for the section shape; scale accompaniment velocities, humanize everything
    def src_bar(beat): return int(beat // 4) - INTRO + B0
    out = []
    for beat, dur, ch, n, v in ev:
        if ch not in (0, 4, 9): v = v * sec(src_bar(beat), (beat % 4) / 4)
        v = v * trim(src_bar(beat))
        out.append((max(0, beat + rnd.uniform(-0.012, 0.012) * (0 if ch == 9 and n == 40 and v > 100 else 1)), dur, ch, n, v + rnd.uniform(-4, 4)))
    ev = out
    LOOP = (B1 - B0) * 4; L0 = INTRO * 4
    if cycles > 1: ev = ev + [(b + LOOP * c, d, ch, n, v) for c in range(1, cycles) for b, d, ch, n, v in ev if b >= L0]
    END = L0 + LOOP * cycles
    def expr(ch, beat):                           # CC11: the smooth section curve + a gentle 8-bar phrase swell
        lb = beat if beat < L0 else L0 + (beat - L0) % LOOP
        b = src_bar(lb); fr = (lb % 4) / 4; x = ((lb - L0) % 32) / 32
        base = {0: 0.80, 4: 0.74, 1: 0.84, 2: 0.66, 3: 0.74}.get(ch, 1.0)
        sw = 0.05 * (math.sin(math.pi * x) ** 2) if ch in (2, 3, 0, 4) else 0.0
        return max(0.3, min(1.0, (base * sec(b, fr) + sw) * trim(b)))
    m = mido.MidiFile(ticks_per_beat=480); tr = mido.MidiTrack(); m.tracks.append(tr)
    tr.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(BPM)))
    for ch, (bank, prog) in PATCH.items():
        tr += [mido.Message('control_change', channel=ch, control=0, value=bank), mido.Message('program_change', channel=ch, program=prog),
               mido.Message('control_change', channel=ch, control=7, value=VOL[ch])]
    msgs = []
    for ch in (0, 4, 1, 2, 3):
        beat = 0.0
        while beat < END:
            msgs.append((int(beat * 480), 0, mido.Message('control_change', channel=ch, control=11, value=int(127 * expr(ch, beat)))))
            beat += 0.25
    for beat, dur, ch, n, v in ev:
        msgs.append((int(beat * 480), 1, mido.Message('note_on', channel=ch, note=n, velocity=int(max(1, min(127, v))))))
        msgs.append((int((beat + dur) * 480), 0, mido.Message('note_off', channel=ch, note=n, velocity=0)))
    msgs.sort(key=lambda x: (x[0], x[1])); tt = 0
    for tick, _, msg in msgs: msg.time = tick - tt; tt = tick; tr.append(msg)
    m.save(dst); print('intro %.3f s, loop %.3f s (%d bars), %d cycles' % (L0 * 60 / BPM, LOOP * 60 / BPM, LOOP // 4, cycles))
if __name__ == '__main__': main()
