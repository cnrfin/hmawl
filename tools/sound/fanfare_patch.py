"""Put a WAV in place of a MusyX sample (default: GAME_ALL sample 89 = sound 224 "fanfare").
usage: fanfare_patch.py IN.wav GAME_ALL.arc GAME_ALL.samp OUTDIR [--sample 89] [--rate 44100|32000|22050] [--gain 0.89]
The WAV is mixed to mono, resampled (ffmpeg) to the highest rate that fits the sample's slot in the
.samp (sizes don't change, so both files go back on the disc in place), normalised to -1 dBFS and
DSP-ADPCM encoded; the sample's sdir entry (length, rate, loop off, coefficients) is updated."""
import sys, os, struct, subprocess, wave, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from musyx import be16, be32, sdir, dsp_decode
import dspenc

def main():
    a = sys.argv[1:]; sid = 89; force = None; gain = 0.89
    if '--gain' in a: i = a.index('--gain'); gain = float(a[i + 1]); del a[i:i + 2]
    if '--sample' in a: i = a.index('--sample'); sid = int(a[i + 1]); del a[i:i + 2]
    if '--rate' in a: i = a.index('--rate'); force = int(a[i + 1]); del a[i:i + 2]
    wav_in, arc_in, samp_in, out = a
    arc = bytearray(open(arc_in, 'rb').read()); samp = bytearray(open(samp_in, 'rb').read())
    root = be32(arc, 4); nn = be32(arc, root + 8)
    files = [struct.unpack_from('>III', arc, root + 12 * i) for i in range(1, nn)]
    sd_off, sd_len = files[2][1], files[2][2]                       # pool, proj, sdir
    sd = arc[sd_off:sd_off + sd_len]
    ents = sdir(bytes(sd)); e = next(x for x in ents if x['id'] == sid)
    k = ents.index(e)
    nxt = min([x['off'] for x in ents if x['off'] > e['off']] + [len(samp)])
    slot = nxt - e['off']; max_n = slot // 8 * 14
    src = wave.open(wav_in); src_rate = src.getframerate(); src_n = src.getnframes(); src.close()
    dur = src_n / src_rate
    rates = [force] if force else [44100, 32000, 24000, 22050, 16000]
    rate = next((r for r in rates if dur * r <= max_n), None)
    if rate is None: sys.exit('%.2f s is too long: the slot holds %.2f s at %d Hz' % (dur, max_n / rates[-1], rates[-1]))
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', wav_in, '-ac', '1', '-ar', str(rate), '-f', 's16le', '-'],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.int16).astype(float)[:max_n]
    x *= (32767 * gain) / max(1.0, np.abs(x).max())                 # peak = gain x full scale (default -1 dBFS)
    pcm = np.round(x).astype(int)
    co = dspenc.fit_coefs(pcm); enc = dspenc.encode(pcm, co)
    assert len(enc) <= slot
    dec = np.array(dsp_decode(enc, len(pcm), [v for p in co for v in p]), float)
    snr = 10 * np.log10((x ** 2).sum() / max(1.0, ((x - dec) ** 2).sum()))
    samp[e['off']:e['off'] + slot] = enc + bytes(slot - len(enc))
    base = sd_off + 0x20 * k                                        # sdir entry
    struct.pack_into('>H', arc, base + 0xE, rate)                  # entry: id, -, offset, -, pitch, -, rate,
    struct.pack_into('>I', arc, base + 0x10, (e['fmt'] << 24) | len(pcm))   # samples, loop start, loop length, info
    struct.pack_into('>II', arc, base + 0x14, 0, 0)                 # no loop
    info = sd_off + e['info']
    struct.pack_into('>BBhh', arc, info + 2, enc[0], 0, 0, 0)        # first frame header, loop ps, history
    struct.pack_into('>16h', arc, info + 8, *[v for p in co for v in p])
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, os.path.basename(arc_in)), 'wb').write(arc)
    open(os.path.join(out, os.path.basename(samp_in)), 'wb').write(samp)
    # read back with the decoder used for the game files
    chk = next(x for x in sdir(bytes(arc[sd_off:sd_off + sd_len])) if x['id'] == sid)
    back = dsp_decode(bytes(samp[chk['off']:chk['off'] + (chk['n'] + 13) // 14 * 8]), chk['n'], chk['coefs'])
    assert back == dec.astype(int).tolist()
    print('sample %d: %.2f s at %d Hz, %d of %d bytes, SNR %.1f dB -> %s' % (sid, len(pcm) / rate, rate, len(enc), slot, snr, out))

if __name__ == '__main__':
    main()
