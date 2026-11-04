# Streamed music (DTK .adp)

The game's streamed BGM (sound/*.adp) is GameCube DTK audio: 48 kHz stereo, 32-byte frames of 28 samples (see dtk.py).
Tracks play through the stream player func_80129928(audio + 0x80, file1, len1, off1, file2, len2, off2): file1 whole
(len 0 = to the end), then file2 from off2 looping (the drive repeats it). The game's table lbl_802545B8 holds
{len1, off1, len2, off2} in 32 KB units (e.g. KORO.adp loops from 26 x 32 KB). Volume: stream faders audio + 0x160 /
0x170 (func_8018A08C(fader, 0..255, ms)); field (MusyX) music master: func_80189DD8(*(audio + 0x4C), 0..127, ms).

## Battle theme (enemy3): /battle/BATTLE.adp
Breeze battle v12 (battle/breeze_heroic.py, 3 cycles -> h13.mid) rendered at 48 kHz (fluidsynth -g 0.5 on
hmawl_music.sf2), 0.159 s of silence + the 4-bar rise = 9 x 32 KB (258,048 samples), then loop cycle 2 resampled
(periodic FFT, +0.178 %) to 70 x 32 KB; normalized to -18.8 dBFS RMS / -1 dBFS peak; `dtk.py encode`. 79 x 32 KB =
2,588,672 B; round-trip SNR 35.6 dB. Not committed (rendered with the game's own instruments).
Disc: `gcbuild.py --add-dir battle=DIR_WITH_BATTLE.adp`; played as "/battle/BATTLE.adp", loop at 9 << 15.
