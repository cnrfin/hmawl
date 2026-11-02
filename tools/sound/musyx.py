"""MusyX (GameCube) group archive reader: U8 .arc with pool / proj / sdir (/ song) + .samp."""
import struct
be16 = lambda d, o: struct.unpack_from('>H', d, o)[0]
be32 = lambda d, o: struct.unpack_from('>I', d, o)[0]

def u8(d):
    root = be32(d, 4); n = be32(d, root + 8); out = []
    for i in range(1, n):
        w0, o, s = struct.unpack_from('>III', d, root + 12 * i)
        if not w0 >> 24: out.append(d[o:o + s])
    return out

def sdir(d):
    """entries: id, sample offset in .samp, pitch (base MIDI key), rate, num samples, loop start, loop len, ADPCM info"""
    ents = []; o = 0
    while be16(d, o) != 0xFFFF:
        sid, _, off, _, pitch, _, rate, nsmp, lst, llen, info = struct.unpack_from('>HHIIBBHIIII', d, o)
        ents.append(dict(id=sid, off=off, pitch=pitch, rate=rate, n=nsmp & 0xFFFFFF, fmt=nsmp >> 24,
                         loop_start=lst, loop_len=llen, info=info))
        o += 0x20
    for e in ents:
        i = e['info']
        e['bytes'], e['ps'], e['lps'], e['hist2'], e['hist1'] = struct.unpack_from('>HBBhh', d, i)
        e['coefs'] = struct.unpack_from('>16h', d, i + 8)
    return ents

def dsp_decode(buf, n, coefs, hist1=0, hist2=0):
    """GameCube DSP-ADPCM: 8-byte frames, 14 samples each."""
    out = []; i = 0
    while len(out) < n:
        ps = buf[i]; i += 1
        scale = 1 << (ps & 0xF); c1, c2 = coefs[(ps >> 4) * 2], coefs[(ps >> 4) * 2 + 1]
        for k in range(14):
            if len(out) >= n: break
            b = buf[i + k // 2]; nib = (b >> 4) if k % 2 == 0 else (b & 0xF)
            if nib >= 8: nib -= 16
            s = ((nib * scale) << 11) + 1024 + c1 * hist1 + c2 * hist2
            s >>= 11; s = max(-32768, min(32767, s))
            out.append(s); hist2, hist1 = hist1, s
        i += 7
    return out
