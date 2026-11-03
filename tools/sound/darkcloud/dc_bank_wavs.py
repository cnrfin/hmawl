#!/usr/bin/env python3
"""Decode Sony PS2 sound banks (.hd header + .bd body, as in Dark Cloud) to WAV: one file per VAG sample.
HD: 'IECS'-tagged chunks; Vagi (sample list) = {tag 8, u32 size, u32 max index, u32 offsets[max+1] (from the
chunk start)} -> entries {u32 offset in .bd, u16 sample rate, u8 loop, u8 -}. BD: PS-ADPCM, 16-byte frames
{shift|filter, flags, 14 data bytes}, flag bit 0 = end.
A .snd (e.g. sound/voice/voiceN.snd) is a 0x50-byte header {name, ..., at 0x40: u32 hd offset, hd size, bd offset}
followed by the .hd and a .bd that has its own 0x50 header (at 0x40: u32 body offset, body size); it is split here.
usage: dc_bank_wavs.py BANK.hd|BANK.snd OUT_DIR"""
import sys, os, struct, wave
K = [(0, 0), (60, 0), (115, -52), (98, -55), (122, -60)]
def adpcm(bd, off):
    out = []; s1 = s2 = 0; i = off
    while i + 16 <= len(bd):
        sh, fl = bd[i] & 15, bd[i] >> 4; flags = bd[i + 1]; k0, k1 = K[fl if fl < 5 else 0]
        for b in bd[i + 2:i + 16]:
            for nib in (b & 15, b >> 4):
                v = (nib - 16 if nib >= 8 else nib) << 12 >> sh
                v = v + ((s1 * k0 + s2 * k1 + 32) >> 6); v = max(-32768, min(32767, v)); out.append(v); s2, s1 = s1, v
        i += 16
        if flags & 1: break
    return out
def chunks(d):
    i = 0; res = {}
    while i + 16 <= len(d):
        if d[i:i + 4] == b'IECS': res[d[i + 4:i + 8][::-1].decode('latin1')] = i
        i += 4
    return res
def main():
    hd, out = sys.argv[1:3]
    if hd.endswith('.snd'):
        f = open(hd, 'rb').read(); ho, hs, bo = struct.unpack_from('<3I', f, 0x40); b = f[bo:]; o2, s2 = struct.unpack_from('<2I', b, 0x40)
        d, bd = f[ho:ho + hs], b[o2:o2 + s2]; hd = hd[:-4] + '.hd'
    else: d = open(hd, 'rb').read(); bd = open(hd[:-3] + '.bd', 'rb').read()
    c = chunks(d)['Vagi']; mx = struct.unpack_from('<I', d, c + 12)[0]; os.makedirs(out, exist_ok=True); n = 0
    for k in range(mx + 1):
        eo = struct.unpack_from('<I', d, c + 16 + 4 * k)[0]
        if eo == 0xFFFFFFFF: continue
        off, rate, loop = struct.unpack_from('<IHB', d, c + eo)
        pcm = adpcm(bd, off)
        w = wave.open(os.path.join(out, '%s_%02d.wav' % (os.path.basename(hd)[:-3], k)), 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate or 22050)
        w.writeframes(struct.pack('<%dh' % len(pcm), *pcm)); w.close(); n += 1
    print(os.path.basename(hd), n, 'samples')
if __name__ == '__main__': main()
