#!/usr/bin/env python3
"""Breeze battle theme v3: dissonant / urgent. A C pedal with clashing upper harmony (Db/C Phrygian, F#dim/C,
Ab+/C, G7b9), chromatic bass neighbours, cello tritone rocking, viola minor-2nd clusters, off-beat cluster stabs,
toms + snare swells; brass lead on a warped Breeze cell (1 #4 1 b3 = C F# C Eb), chromatic answers, b9 shrieks.
usage: breeze_battle_v3.py OUT.mid [lead_bank lead_prog] [loops]"""
import sys, mido
BPM = 210
# 16 bars: upper harmony over the C pedal (pcs), bass pedal pc
HARM = [((0, 3, 7), 0), ((0, 3, 7), 0), ((1, 5, 8), 0), ((1, 5, 8), 0), ((0, 3, 7), 0), ((6, 9, 0), 0),
        ((8, 0, 4), 0), ((8, 0, 4), 0), ((0, 3, 7), 0), ((1, 5, 8), 0), ((6, 9, 0), 0), ((6, 9, 0), 0),
        ((7, 11, 2, 5, 8), 7), ((7, 11, 2, 5, 8), 7), ((1, 5, 8), 1), ((7, 11, 2, 5, 8), 7)]
CLUSTER = {0: (67, 68), 1: (68, 69), 6: (69, 70), 8: (71, 72), 7: (71, 72)}    # viola minor 2nds per harmony root
def lead():
    """(bar, beat, dur, note, accent) over 16 bars"""
    L = []
    def cell(bar, r, up=0):                           # warped Breeze arpeggio: 1 #4 1 b3
        b = 72 + r + up; L.extend([(bar, 0, 0.6, b, 1), (bar, 1, 0.4, b - 6, 0), (bar, 1.5, 0.4, b, 0), (bar, 2, 1.4, b + 3, 1)])
    cell(0, 0); L += [(1, 0.5, 0.4, 75, 0), (1, 1, 0.4, 74, 0), (1, 1.5, 0.4, 73, 0), (1, 2, 1.8, 72, 1)]   # chromatic fall
    L += [(2, 0, 0.3, 85, 1), (2, 0.5, 2.0, 73, 1), (3, 0, 0.5, 72, 0), (3, 1, 0.5, 73, 0), (3, 2, 1.6, 77, 1)]  # b9 shriek, Db colour
    cell(4, 0); L += [(5, 0, 0.6, 78, 1), (5, 1, 0.6, 75, 0), (5, 2, 1.8, 72, 1)]                        # F# dim
    L += [(6, 0, 1.4, 76, 1), (6, 1.5, 0.4, 75, 0), (6, 2, 1.4, 72, 1), (7, 0, 0.5, 68, 0), (7, 0.5, 0.5, 72, 0), (7, 1, 2.6, 76, 1)]  # Ab+
    cell(8, 0, 12 - 12); L += [(9, 0, 0.4, 77, 0), (9, 0.5, 0.4, 78, 0), (9, 1, 0.4, 79, 0), (9, 1.5, 2.2, 80, 1)]   # chromatic rise
    L += [(10, 0, 0.6, 78, 1), (10, 1, 0.6, 81, 1), (10, 2, 1.8, 84, 1), (11, 0, 0.5, 83, 0), (11, 1, 2.6, 78, 1)]
    L += [(12, 0, 0.6, 79, 1), (12, 1, 0.4, 80, 1), (12, 1.5, 2.2, 83, 1), (13, 0, 0.3, 92, 1), (13, 0.5, 3.0, 80, 1)]   # G7b9, Ab shriek
    L += [(14, 0, 0.6, 77, 1), (14, 1, 0.6, 73, 0), (14, 2, 1.8, 68, 1), (15, 0, 0.5, 71, 1), (15, 0.5, 0.5, 74, 1), (15, 1, 0.5, 77, 1), (15, 1.5, 2.3, 80, 1)]
    return L
def main():
    dst = sys.argv[1]; lb, lp = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (25, 2)
    loops = int(sys.argv[4]) if len(sys.argv) > 4 else 2
    PATCH = {0: (lb, lp), 4: (lb, lp), 1: (20, 1), 2: (7, 5), 3: (18, 0), 5: (18, 0), 9: (8, 5)}
    VOL = {0: 104, 4: 72, 1: 84, 2: 62, 3: 60, 5: 82, 9: 34}
    ev = []; INTRO = 2; total = INTRO + 16 * loops
    for i in range(total):
        h, ped = HARM[0] if i < INTRO else HARM[(i - INTRO) % 16]; base = i * 4; lo = 36 + ped
        for k, d in enumerate((0, 0, 0, 1, 0, 0, -1, 0)):           # bass: pedal with chromatic neighbours
            ev.append((base + k * 0.5, 0.4, 1, lo + d + (12 if k in (2, 5) else 0), 100 if k % 2 == 0 else 80))
        for k in range(8):                                          # cello: tritone rocking
            ev.append((base + k * 0.5, 0.42, 2, lo + 12 + (6 if k % 2 else 0), 72))
        cl = CLUSTER.get(h[0], (67, 68))
        for k in range(16):
            for n in cl: ev.append((base + k * 0.25, 0.22, 3, n, 48 + (12 if k % 4 == 0 else 0)))
            swell = 1.0 if (i - INTRO) % 4 != 3 else 1 + k / 16                  # snare swell into each 4th bar line
            ev.append((base + k * 0.25, 0.1, 9, 40, int((42 + (22 if k % 4 == 0 else 0)) * swell)))
        if i >= INTRO:                                              # off-beat cluster stabs + toms
            stab = sorted(set(60 + p for p in h[:3])) + [61 if h[0] != 1 else 62]
            for at in (1.5, 3.0) if (i - INTRO) % 2 == 0 else (0.5, 2.5, 3.5):
                for n in stab: ev.append((base + at, 0.22, 5, n, 108))
            for at, n in ((0, 45), (1.5, 43), (3.0, 41)):
                ev.append((base + at, 0.2, 9, n, 90 if at == 0 else 76))
    for lp_ in range(loops):
        off = (INTRO + 16 * lp_) * 4
        for bar, beat, dur, n, acc in lead():
            v = 118 if acc else 98
            ev.append((off + bar * 4 + beat, dur, 0, n, v)); ev.append((off + bar * 4 + beat, dur, 4, n - 12, v - 22))
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
    m.save(dst); print('%s: %d bars, %.1f s, lead bank %d prog %d' % (dst, total, total * 4 * 60 / BPM, lb, lp))
if __name__ == '__main__': main()
