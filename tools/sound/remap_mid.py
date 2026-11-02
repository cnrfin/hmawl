"""Rewrite a GM MIDI to play game instruments from hmawl_music.sf2.
Per channel: (bank, program); drum notes (channel 10) go to their own channels with a key remap."""
import struct, sys
def vlq_r(d, o):
    v = 0
    while True:
        b = d[o]; o += 1; v = (v << 7) | (b & 0x7F)
        if not b & 0x80: return v, o
def vlq_w(n):
    b = [n & 0x7F]; n >>= 7
    while n: b.insert(0, 0x80 | (n & 0x7F)); n >>= 7
    return bytes(b)
def read(path):
    d = open(path, 'rb').read(); fmt, ntr, div = struct.unpack_from('>HHH', d, 8); o = 14; tracks = []
    for _ in range(ntr):
        ln = struct.unpack_from('>I', d, o + 4)[0]; p = o + 8; end = p + ln; t = 0; run = 0; ev = []
        while p < end:
            dt, p = vlq_r(d, p); t += dt; st = d[p]
            if st == 0xFF:
                l, q = vlq_r(d, p + 2); ev.append((t, d[p:q + l])); p = q + l; continue
            if st in (0xF0, 0xF7):
                l, q = vlq_r(d, p + 1); ev.append((t, d[p:q + l])); p = q + l; continue
            if st & 0x80: run = st; p += 1
            n = 1 if run & 0xF0 in (0xC0, 0xD0) else 2
            ev.append((t, bytes([run]) + d[p:p + n])); p += n
        tracks.append(ev); o = end
    return fmt, div, tracks
def write(path, fmt, div, tracks):
    out = b'MThd' + struct.pack('>IHHH', 6, fmt, len(tracks), div)
    for ev in tracks:
        ev = sorted(ev, key=lambda e: e[0]); data = b''; last = 0
        for t, m in ev:
            data += vlq_w(t - last) + m; last = t
        if not ev or ev[-1][1][:2] != b'\xff\x2f': data += b'\x00\xff\x2f\x00'
        out += b'MTrk' + struct.pack('>I', len(data)) + data
    open(path, 'wb').write(out)
def remap(src, dst, chan_map, drum_map):
    """chan_map {ch: (bank, prog)}; drum_map {key: (new_ch, bank, prog, new_key)}"""
    fmt, div, tracks = read(src); new = []
    setup = []
    for ch, (b, p) in chan_map.items(): setup += [(0, bytes([0xB0 | ch, 0, b])), (0, bytes([0xC0 | ch, p]))]
    for ch, b, p, _ in set(drum_map.values()): setup += [(0, bytes([0xB0 | ch, 0, b])), (0, bytes([0xC0 | ch, p]))]
    for ev in tracks:
        ne = []
        for t, m in ev:
            st = m[0]
            if st < 0xF0:
                ch, c = st & 0xF, st & 0xF0
                if c in (0xC0,) or (c == 0xB0 and m[1] in (0, 32)): continue     # our own bank/program instead
                if ch == 9 and c in (0x80, 0x90):
                    if m[1] not in drum_map: continue
                    nch, _, _, nk = drum_map[m[1]]; m = bytes([c | nch, nk, m[2]])
                elif ch not in chan_map and c in (0x80, 0x90): continue
            ne.append((t, m))
        new.append(ne)
    new[0] = setup + new[0]
    write(dst, fmt, div, new)
