# Sound bank (sound/GAME_ALL.arc + GAME_ALL.samp)

Final bank: `build/GAME_ALL.arc` (b8d163da) + `build/GAME_ALL.samp` (18982d7e), Z-targeting test 13. (Logs test 29's bank, without 434/435: 863651c4 / 924c681e.)

| Sound | What |
|---|---|
| 224 | item-get fanfare: your "Get Big Item" MIDI played on the game's own instruments (replaces sample 89 in place) |
| 305 | knock (vanilla, unchanged) |
| 432 | new: wood hit (`src/wood_hit1.mp3`), the log chop (logs.c `SFX_WOOD`); settings copied from 305 |
| 434 | new: Z-target lock on (`src/z_lock_on.mid/.wav`): D3 then G3 fluttering x4, after OoT's (`src/oot_z_target_reference.mp3`), on RECORD07 p4 (pizzicato strings), low-passed at 1.2 kHz; quiet on purpose (gain 0.40: ~1.6 dB under the wood hit); zt.c `SE_LOCK` |
| 435 | new: Z-target lock off (`src/z_lock_off.*`): the same notes reversed, quicker (G x2, then D), gain 0.30; zt.c `SE_FREE` |
| 433 | new: the "Breeze" level-up jingle, version G (piano melody an octave up) (skill.c `SFX_LEVEL_UP`, the Field/Animal up chime); settings copied from 224 |

Rebuild from the vanilla bank (byte-identical; ffmpeg needed):
```
python3 fanfare_patch.py src/item_get_game.wav VANILLA/GAME_ALL.arc VANILLA/GAME_ALL.samp out1
python3 add_sfx.py src/wood_hit1.mp3 out1/GAME_ALL.arc out1/GAME_ALL.samp out2 --id 432 --template 305
python3 add_sfx.py src/breeze_up_G.wav out2/GAME_ALL.arc out2/GAME_ALL.samp out3 --id 433 --template 224 --gain 0.80
python3 add_sfx.py src/z_lock_on.wav out3/GAME_ALL.arc out3/GAME_ALL.samp out4 --id 434 --template 305 --gain 0.40
python3 add_sfx.py src/z_lock_off.wav out4/GAME_ALL.arc out4/GAME_ALL.samp out5 --id 435 --template 305 --gain 0.30
```
The lock .wav files are fluidsynth renders of the .mid files on hmawl_music.sf2 (bank 18 prog 4), low-passed (z_lock_render.py).
Note: add_sfx.py scales every new sample to `--gain` x full scale (peak), so the gain sets the in-game level: the
first lock sounds (gain 0.89) played louder than the wood hit.
Vanilla GAME_ALL: arc 1c1e37e9, samp 9e4d0949. Intermediate: out1 9045e9c7 / 524f2252, out2 88f280d5 / b433835d.
Install: `gcbuild.py --replace sound/GAME_ALL.arc=... --replace sound/GAME_ALL.samp=... --allow-unreferenced`.

## Combo sounds (weapons test 5): Dark Cloud battle sounds from the user's own disc
Not committed (the audio is the user's game data): darkcloud/extract_dc_sound.py pulls sound\battle out of the
disc's DATA.DAT with DATA.HD2, darkcloud/dc_bank_wavs.py decodes the .hd/.bd banks to WAV. Picks (dan01bg):
| Sound | Clip | Use |
|---|---|---|
| 436 | dan01bg_10, its loudest 0.45 s (fades 20 / 120 ms), gain 0.55 | swing, combo hits 1 / 2 |
| 437 | dan01bg_30, gain 0.65 | swing, hit 3 |
| 438 | dan01bg_22, gain 0.70 | impact, hits 1 / 2 |
| 439 | dan01bg_07, gain 0.80 | impact, hit 3 |
```
python3 add_sfx.py swing_light.wav build/GAME_ALL.arc build/GAME_ALL.samp o1 --id 436 --template 305 --gain 0.55
python3 add_sfx.py swing_heavy.wav o1/GAME_ALL.arc o1/GAME_ALL.samp o2 --id 437 --template 305 --gain 0.65
python3 add_sfx.py impact_light.wav o2/GAME_ALL.arc o2/GAME_ALL.samp o3 --id 438 --template 305 --gain 0.70
python3 add_sfx.py impact_heavy.wav o3/GAME_ALL.arc o3/GAME_ALL.samp o4 --id 439 --template 305 --gain 0.80
```
-> GAME_ALL.arc 8015d59b / .samp b3baa3e3 (on top of the Z-target bank b8d163da / 18982d7e).

Tools:
- `fanfare_patch.py`: a WAV over an existing sample, in place (resampled to fit its slot).
- `add_sfx.py`: a new sound id: sample appended, macro copied from a template sound and pointed at the new
  sample (the test-28 bug: copies kept pointing at the template's sample; now checked), SFX entry added.
- `musyx.py`, `dspenc.py` (DSP ADPCM), `sf2.py`, `pitch.py`, `timbre.py`, `remap_mid.py`.
- `build_sf2.py` / `build_sf2_all.py`: the game's music instruments as a SoundFont (`hmawl_music.sf2`, 51 MB,
  not committed: rebuild with `SND_IN=<folder with the disc's sound/*.arc + *.samp>`); presets list in
  `hmawl_music_presets.txt`. Used to render `src/item_get_game.wav` from `src/item_get_game.mid`.
- `jingles/`: the level-up / field-up candidates (MIDI); G was picked.

## Voice (weapons test 6): Toan's voice from the user's Dark Cloud disc (sound\voice\voice0.snd = toan_s)
Not committed. darkcloud/dc_bank_wavs.py decodes the .snd (voice0..6 = toan, syao, goro, ruby, unga, ozmd, turi).
| Sound | Clip | Use |
|---|---|---|
| 440 | toan_01, gain 0.60 | voice, hit 1 (with the swing, zt.c SE_VOICE1 + hit) |
| 441 | toan_02, gain 0.60 | voice, hit 2 |
| 442 | toan_07, gain 0.70 | voice, hit 3 |
| 443 | toan_03, gain 0.70 | hurt (not used yet) |
| 444 | toan_04, gain 0.75 | dies (not used yet) |
Tired (weapons test 7): sound 304 (user-identified; macro 916, sample 878, used by 304 only) replaced in place with
toan_06 trimmed to 0.62 s (5 ms fade) at the old level (gain 0.45: RMS -19.6 dB like the original):
`fanfare_patch.py tired.wav v5/GAME_ALL.arc v5/GAME_ALL.samp v6 --sample 878 --gain 0.45` -> arc 4fd3b62f / samp cc2efc2c.
Z-target lock on / off now use the game's own 238 / 239 (user pick); 434 / 435 stay in the bank, unused.
Duplicates (vanilla): 250 samples, 228 distinct; 10 groups stored more than once (22 extra copies, 214 KB), e.g.
376/377/378, 397/398/399, 332/333/335/336, and 10 copies under 307/326/327/347/348/410/411/415/416/417.
```
python3 add_sfx.py 0_toan_01.wav o4/GAME_ALL.arc o4/GAME_ALL.samp v1 --id 440 --template 305 --gain 0.60
python3 add_sfx.py 0_toan_02.wav v1/GAME_ALL.arc v1/GAME_ALL.samp v2 --id 441 --template 305 --gain 0.60
python3 add_sfx.py 0_toan_07.wav v2/GAME_ALL.arc v2/GAME_ALL.samp v3 --id 442 --template 305 --gain 0.70
python3 add_sfx.py 0_toan_03.wav v3/GAME_ALL.arc v3/GAME_ALL.samp v4 --id 443 --template 305 --gain 0.70
python3 add_sfx.py 0_toan_04.wav v4/GAME_ALL.arc v4/GAME_ALL.samp v5 --id 444 --template 305 --gain 0.75
```
-> GAME_ALL.arc b201d0de / .samp 587c5656 (test 6). Test 7 pm.bin c4840574 (normal), 8960024c (WEAPONS_ALL test).
