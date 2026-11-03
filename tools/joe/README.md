# Joe (EmotiGuy)

A new optional character: Joe, the EmotiGuy emoji (a floating round head with gloves and shoes). He is meant
to take Mukumuku's place in the game data; his role is still to be designed. For now he is tested in the
goddess test slot (`gd/gd_0`, Z + X spawns him).

## What is here

| Path | Contents |
|---|---|
| `build/gd_0.arc`, `build/gd_0.anm.arc` | Joe test 4 (test 3 + skin 22% brighter, `JOE_SKIN`). 2,380 triangles, 273,088 B (sharper face frames and gloves/shoes textures); Van's first 6 animations (26,848 B). Test 2 ran in game with face, gloves and shoes correct. |
| `data/joe_pieces.pkl.gz` | Gloves, shoes (decimated, with UVs) and the plain head (eyes/mouth removed), exported from the user's Blender file. |
| `data/parts_lib.json.gz` | Expression parts library (brows, eyes, mouth for 57 shape keys), rendered from the full-quality model; used by the face editor and the frame builder. |
| `data/final_set.json` | The chosen eye/brow and mouth frames. |
| `data/user_expressions*.` | The user's expressions from the Joe Face Maker (PDF export, parsed). |
| `data/tex_*.png`, `data/face_cam.pkl` | Joe's textures and the front camera the parts were rendered with. |
| `editor/joe_face_maker_template.html` | The Joe Face Maker page (`__LIB__` is replaced by `parts_lib.json`). |
| `scripts/` | `joe_export.py` / `parts.py` / `joe_build.py` (Blender 5.2 via the `bpy` module), `compose.py` + `frames.py` (face frames), `joe_game.py` (game files). |
| `previews/` | Renders read back from the built files. |

## Build

- Source: the user's `The Emotis.blend` (not in git, 121 MB). `joe_export.py` and `parts.py` read it.
- Skeleton and animations: Van's (`ban_0`, 50 nodes, 22 animations, unchanged). Joe fits Van's rig at 1.07x
  with no joint moved: head and face patches on node 13, gloves on 18/39, shoes on 8/48.
- Head: lat-long sphere shrunk onto Joe's head, front mirrored from the back (a clean dome); eye/brow and mouth
  patches laid on it (brows above y 120 on the canvas pulled 28% down off the rim) use the animated frame textures.
- Face frames at the vanilla numbers: eyes 0-2 normal, 6-8 angry, 9-11 happy, 12-14 blushing, 18-20 sad/crying,
  30 sleeping, 54-56 surprised, 57 wink; mouth 0/1 neutral, 2 surprised, 4/5 smile, 7/8 angry, 9/10 sad.
  Eye frames 80x64, mouth 80x56, 1-bit alpha.
- GPL materials as Muffy's: eye frame (sel 00), body atlas gloves+shoes (sel FF), mouth frame (sel 01), head skin (sel 02).

## Putting test 1 on the disc

`gcbuild.py` currently refuses to replace both files in one pass (its plan grows `gd_0.arc` in place into the
gap it also picks for `gd_0.anm.arc`), so do it in two passes:

```
python3 gcbuild.py --iso HM_AWL_blank1a.iso --out HM_AWL_joe1x.iso --replace gd/gd_0.arc=gd/gd_0.arc --allow-unreferenced
python3 gcbuild.py --iso HM_AWL_joe1x.iso --out HM_AWL_joe1a.iso --replace gd/gd_0.anm.arc=gd/gd_0.anm.arc --allow-unreferenced
python3 postman_npc/make_pm_dol.py HM_AWL_joe1a.iso HM_AWL_joe1.iso
```

## Test 5: 90% Joe, faster walk, bench clips (`build/test5/`)

```
# run from the joeexpr/ work folder (frames.py reads final_set.json there)
python3 joe_sit.py ../joegame/sit_out                       # anm_sitdown/sitloop/standup.bin + cig.json
JOE_SCALE=0.9 JOE_CIG=$PWD/../joegame/sit_out/cig.json JOE_WALK=28 python3 ../joegame/joe_game.py gd_0 OUT
```
- `JOE_SCALE=0.9`: mesh, skeleton translations and every animation translation x0.9 (`joe_anm.scale_T`).
- `JOE_WALK=28`: Van's walk (clip 1) retimed 34 -> 28 frames (1.2x). Ground speed to match: ~1.17x Van's.
- Cigarette: 42-vertex mesh on node 29 (an unused face node). Nodes 28/29 get identity rest locals, 29 parked
  at the head ball's centre; clips 0-5 get constant 28/29 tracks (checked: the cigarette stays inside the
  head in every frame). Colours: four 8x8 cells in a free corner of the body atlas.
- New clips (`joe_sit.py`, all 50 tracks, 30 fps, squad control = key -> slerp):
  - 6 sit down, 59 frames, NPC standing 0.75 in front of the bench facing it; twists round and sits.
  - 7 sitting loop, 300 frames, NPC on the same spot facing away (turn the NPC 180 degrees when 6 ends).
  - 8 stand up, 40 frames, same frame as 7; ends on idle frame 0.
- Read back from the built files: `previews/test5_readback.png`. Sizes: gd_0.arc 275,104 B, gd_0.anm.arc 47,712 B.

## Test 6 (`build/test6/`): shoe insides
Test 5 + black caps over every open boundary loop of the shoes (sole seam, ankle opening, small gaps), both
windings (130 triangles); black is a fifth 8x8 cell next to the cigarette colours. gd_0.arc 278,080 B;
gd_0.anm.arc unchanged. Preview `previews/test6_shoes.png`.

## Test 7 (`build/test7/gd_0.anm.arc`): no restart at the end of sit down / stand up
The game loops every clip, and in game the sit down / stand up ended before the code switched to the next
clip (visible jump back). Clips 6 and 8 now end with 90 frames holding their last pose (lengths 149 / 130).
gd_0.arc unchanged from test 6.

## Test 11 (`build/test11/gd_0.arc`): textures at half size (memory)
Joe's textures were 314 KB (body 512x256 CMPR 72 KB, 18 eye frames 112x96 CMPR 97 KB, 9 mouth frames 112x72
RGB5A3 145 KB) against a villager's ~33 KB (body 128x256 + 128x64, 32x32 face frames). `JOE_TEX=0.5` halves the
body atlas (UVs unchanged) and the eye / mouth frames (56x48 CMPR, 56x36 RGB5A3): gd_0.arc 386,720 -> 156,128 B.
```
JOE_TEX=0.5 JOE_SOFTMOUTH=1 JOE_SCALE=0.9 JOE_CIG=$PWD/../joegame/sit_out/cig.json JOE_WALK=28 JOE_FACE=0.9 python3 ../joegame/joe_game.py gd_0 OUT
```
(`JOE_TEX` unset rebuilds test 10 byte for byte.) gd_0.anm.arc unchanged (test 10).
