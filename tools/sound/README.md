# Sound bank (sound/GAME_ALL.arc + GAME_ALL.samp)

Final bank: `build/GAME_ALL.arc` (863651c4) + `build/GAME_ALL.samp` (924c681e), as shipped in logs test 29.

| Sound | What |
|---|---|
| 224 | item-get fanfare: your "Get Big Item" MIDI played on the game's own instruments (replaces sample 89 in place) |
| 305 | knock (vanilla, unchanged) |
| 432 | new: wood hit (`src/wood_hit1.mp3`), the log chop (logs.c `SFX_WOOD`); settings copied from 305 |
| 433 | new: the "Breeze" level-up jingle, version G (piano melody an octave up) (skill.c `SFX_LEVEL_UP`, the Field/Animal up chime); settings copied from 224 |

Rebuild from the vanilla bank (byte-identical; ffmpeg needed):
```
python3 fanfare_patch.py src/item_get_game.wav VANILLA/GAME_ALL.arc VANILLA/GAME_ALL.samp out1
python3 add_sfx.py src/wood_hit1.mp3 out1/GAME_ALL.arc out1/GAME_ALL.samp out2 --id 432 --template 305
python3 add_sfx.py src/breeze_up_G.wav out2/GAME_ALL.arc out2/GAME_ALL.samp out3 --id 433 --template 224 --gain 0.80
```
Vanilla GAME_ALL: arc 1c1e37e9, samp 9e4d0949. Intermediate: out1 9045e9c7 / 524f2252, out2 88f280d5 / b433835d.
Install: `gcbuild.py --replace sound/GAME_ALL.arc=... --replace sound/GAME_ALL.samp=... --allow-unreferenced`.

Tools:
- `fanfare_patch.py`: a WAV over an existing sample, in place (resampled to fit its slot).
- `add_sfx.py`: a new sound id: sample appended, macro copied from a template sound and pointed at the new
  sample (the test-28 bug: copies kept pointing at the template's sample; now checked), SFX entry added.
- `musyx.py`, `dspenc.py` (DSP ADPCM), `sf2.py`, `pitch.py`, `timbre.py`, `remap_mid.py`.
- `build_sf2.py` / `build_sf2_all.py`: the game's music instruments as a SoundFont (`hmawl_music.sf2`, 51 MB,
  not committed: rebuild with `SND_IN=<folder with the disc's sound/*.arc + *.samp>`); presets list in
  `hmawl_music_presets.txt`. Used to render `src/item_get_game.wav` from `src/item_get_game.mid`.
- `jingles/`: the level-up / field-up candidates (MIDI); G was picked.
