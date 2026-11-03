#!/usr/bin/env python3
"""Breeze battle theme v2: an original 16-bar battle loop that only quotes Breeze (its opening arpeggio
C-G-C-E as a brass call, sequenced onto each chord, and the B section's D-Eb rub), built on the dark turn the
user liked (B section bars 27-31: G -> Ab/Eb -> G -> F) as Cm Cm Ab Ab Fm Fm G G / Cm Cm Ab Ab Eb Eb G G.
OoT-style texture (200 bpm): octave-bouncing 8th bass with a b2 push, cello root/b2 rocking, viola 16th tremolo,
soft 16th snare, string stabs on the chord changes; brass lead doubled an octave down.
usage: breeze_battle_v2.py OUT.mid [lead_bank lead_prog] [loops]"""
import sys, mido
BPM = 200
CHORDS = [0, 0, 8, 8, 5, 5, 7, 7, 0, 0, 8, 8, 3, 3, 7, 7]          # root pcs (C minor)
TONES = {0: (0, 3, 7), 8: (8, 0, 3), 5: (5, 8, 0), 7: (7, 11, 2), 3: (3, 7, 10)}
C4 = 60
def lead_phrase(var):
    """(bar, beat, dur, note) for 8 bars; var 0/1 = first / second phrase"""
    L = []
    def call(bar, r):                       # the Breeze arpeggio cell on chord root r: 1-5-1-3
        t = TONES[r]; root = C4 + 12 + r if r < 7 else C4 + r
        third = root + (t[1] - t[0]) % 12; fifth = root - 12 + (t[2] - t[0]) % 12
        L.extend([(bar, 0, 0.7, root), (bar, 1, 0.45, fifth), (bar, 1.5, 0.45, root), (bar, 2, 1.8, third)])
    call(0, 0); L += [(1, 3.5, 0.2, 74), (1, 3.75, 0.25, 75)]                 # D-Eb pickup
    L += [(2, 0, 2.6, 72), (2, 3, 0.9, 70), (3, 0, 1.8, 68), (3, 2, 0.9, 67), (3, 3, 0.9, 68)]
    if var == 0:
        call(4, 5); L += [(5, 2, 1.4, 79), (5, 3.5, 0.45, 77)]
        L += [(6, 0, 1.8, 74), (6, 2, 0.9, 75), (6, 3, 0.9, 74), (7, 0, 3.0, 71)]          # D-Eb rub, B held
    else:
        call(4, 3); L += [(5, 2, 1.4, 79), (5, 3.5, 0.45, 82)]
        L += [(6, 0, 0.9, 79), (6, 1, 0.9, 74), (6, 2, 0.9, 75), (6, 3, 0.9, 77), (7, 0, 3.5, 79)]   # up to G
    return L
def main():
    dst = sys.argv[1]; lb, lp = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (25, 2)
    loops = int(sys.argv[4]) if len(sys.argv) > 4 else 2
    PATCH = {0: (lb, lp), 4: (lb, lp), 1: (20, 1), 2: (7, 5), 3: (18, 0), 5: (18, 0), 9: (8, 5)}
    VOL = {0: 104, 4: 70, 1: 82, 2: 60, 3: 62, 5: 78, 9: 32}
    ev = []; INTRO = 2
    def bar_of(i): return i % 16
    total = INTRO + 16 * loops
    for i in range(total):
        r = CHORDS[0] if i < INTRO else CHORDS[bar_of(i - INTRO)]; base = i * 4
        lo = 36 + r if r <= 7 else 24 + r
        for k in range(8):
            ev.append((base + k * 0.5, 0.42, 1, lo + (12 if k % 2 else 0) + (1 if k == 7 else 0) - (12 if k == 7 else 0), 96 if k % 2 == 0 else 76))
            ev.append((base + k * 0.5, 0.45, 2, lo + 12 + (1 if k % 4 == 3 else 0), 68))
        t = TONES[r]; vt = [60 + (p if p >= 5 else p + 12) for p in t[1:]]
        for k in range(16):
            for n in vt: ev.append((base + k * 0.25, 0.22, 3, n, 50 + (10 if k % 4 == 0 else 0)))
            ev.append((base + k * 0.25, 0.1, 9, 40, 44 + (26 if k % 4 == 0 else 0) + (18 if k in (0, 8) else 0)))
        if i >= INTRO and (i - INTRO) % 2 == 0:                      # string stab on each chord change
            for n in (48 + t[0] % 12, 55 + (t[2] - 7) % 12 if t[2] >= 7 else 55 + t[2] + 5, 60 + t[1] % 12):
                ev.append((base, 0.3, 5, n, 100))
    for lp_ in range(loops):
        for half in (0, 1):
            off = (INTRO + 16 * lp_ + 8 * half) * 4
            for bar, beat, dur, n in lead_phrase(half):
                v = 112 if beat == 0 else 96
                ev.append((off + bar * 4 + beat, dur, 0, n, v)); ev.append((off + bar * 4 + beat, dur, 4, n - 12, v - 20))
    m = mido.MidiFile(ticks_per_beat=480); tr = mido.MidiTrack(); m.tracks.append(tr)
    tr.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(BPM)))
    for ch, (bank, prog) in PATCH.items():
        tr += [mido.Message('control_change', channel=ch, control=0, value=bank), mido.Message('program_change', channel=ch, program=prog),
               mido.Message('control_change', channel=ch, control=7, value=VOL[ch])]
    msgs = []
    for beat, dur, ch, n, v in ev:
        msgs.append((int(beat * 480), 1, mido.Message('note_on', channel=ch, note=n, velocity=min(127, v))))
        msgs.append((int((beat + dur) * 480), 0, mido.Message('note_off', channel=ch, note=n, velocity=0)))
    msgs.sort(key=lambda x: (x[0], x[1])); tt = 0
    for tick, _, msg in msgs: msg.time = tick - tt; tt = tick; tr.append(msg)
    m.save(dst); print('%s: %d bars, %.1f s, lead bank %d prog %d' % (dst, total, total * 4 * 60 / BPM, lb, lp))
if __name__ == '__main__': main()
