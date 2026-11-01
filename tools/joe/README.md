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
