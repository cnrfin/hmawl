# Harvest Goddess model

A custom Harvest Goddess character for the game, built on Celia's skeleton and shown in game through the
Postman/goddess test code (Z + X spawns her in character slot 37).

## What is here

| Path | Contents |
|---|---|
| `build/gd_0.arc`, `build/gd_0.anm.arc` | Game files (final test 4). 2,832 triangles, 152,192 B, 1.1x Celia. SHA-1: `gd_0.arc` `a6e1dccf`, `gd_0.anm.arc` `2407808f`. |
| `build_jiggle/gd_0.arc`, `build_jiggle/gd_0.anm.arc` | Jiggle test 6 (`GD_JIGGLE=fold GD_JIGGLE_GAIN=2 GD_JIGGLE_CLAMP=0.0175`, on top of test 4): 49 nodes, node 21 reused as the bust bone. SHA-1: `b608bff2`, `c0c522d6`. Not yet tried in game. |
| `build/b0_body.png`, `build/b0_head.png` | The two texture atlases inside `gd_0_b0.tpl`. |
| `data/goddess_FINAL_model2.pkl.gz` | The finished model as pieces (positions, UVs, triangles, texture per piece). |
| `data/celia_hands.pkl.gz` | Celia's hands (mesh, nodes, skin-tinted texture) used on the goddess. |
| `data/face_frames_lavender.pkl.gz` | Muffy's eye frames (lavender) and mouth frames (skin-matched), every frame. |
| `data/blank_v3.npz`, `data/body_sheet.png` | Base body mesh on Celia's joints, and the user's body texture sheet. |
| `scripts/` | Every script used to make the model (hair, outfit, veil, sash/bow, Muffy head reshaping, face, hands, sandals) and the game build. |
| `previews/` | Renders, including ones read back from the built game files and posed with Celia's animations. |

## The model

- Body: the original blank body (`blank_v3`), head reshaped onto Muffy's head shape (`reshape_head.py`),
  Muffy's face shell stitched into it as one surface (`stitch.py`), lowered 0.04 so the jaw meets the
  shoulders as before.
- Face: Muffy's face mesh, eye and mouth meshes; eyes recoloured lavender; forehead hairline band repainted
  to match the hair.
- Hair: Kate-style centre part, Samantha's tufts, loose strands, twist-textured egg buns, Flora's ponytail
  with a bow made from the red sash ribbon and cream flowers.
- Outfit from the user's sheet (126.png), veil over the shoulders, front sash, gold bracelets,
  Celia's hands, sandals.

## Game build (`scripts/build_final.py NAME OUTDIR`)

1. Hidden triangles removed by ray casting (`cull.py`): body under the clothes, scalp under the hair.
2. UV-aware decimation of dense pieces (`decim.py`): each UV chart decimated with fixed borders,
   new UVs from the closest point on the original.
3. Rigid skin on Celia's nodes: body by body part (as `build_blank.py`), skirt on Celia's skirt nodes
   32-34, ponytail and bow on her braid nodes 8/9, veil on the chest (6), hair/face on the head (7),
   hands on Celia's own hand nodes.
4. Skin pieces (body, face, eye, mouth, ears, hands, feet) share one smooth normal per position, so
   there are no shading seams where they meet. Stray hair paint is cleaned from the face texture.
5. Textures packed into two atlases (b0 #0 body, b0 #1 head). Eye and mouth use the animated
   frame textures (f0_e / f0_m). GPL materials laid out as Muffy's `mumu_0.gpl`: eye (sel 00),
   body (sel FF), mouth (sel 01), head (sel 02).
6. Skeleton and Celia's 10 animations scaled by `GD_SCALE` (default 1.1).
7. Skirt pushed by the feet (`skirtfollow.py`), walk and run: legs keep Celia's motion; per frame the front
   skirt node (34) swings forward when a toe would pass the gown's front hem angle (+26 deg from the hip),
   the back node (32) swings back when the ankle, toe or heel would pass the back hem angle (-22 deg),
   12 deg margin; sides (33) follow. Gown/overskirt/sash skinned front 34, back 32, sides 33, top band 3.
   Key controls are written equal to the key rotation (the control is a rotation, not a tangent: scaling
   it, as the earlier shorter-stride option `anmsoft.py` / `GD_WALK`/`GD_RUN` did, made the run jitter).
8. Optional jiggle (`GD_JIGGLE=1`, `jiggle.py`): two extra nodes under node 5 (BUST full motion, RING half
   motion) appended to the act (51 nodes); bust vertices skinned to them; per animation a damped spring
   (3.2 Hz, damping 0.22) driven by node 5's motion is baked into keyed-translation tracks (pelvis-style
   packed 0x3EE10100), clamped by `GD_JIGGLE_CLAMP`. Bust = y 0.665-0.78, |x| < 0.105, z > 0.055 (full);
   a band around it at half motion. BROKEN IN GAME: every 51-node build (jiggle tests 3-5) wrecked her
   model as soon as she spawned - the game evidently can't take more than Celia's 49 nodes.
   `GD_JIGGLE=fold` stays at 49: node 21 (right clavicle base; constant at its rest in all 10 animations,
   unused by the skin) is folded into its child 22 (22's rest and every key pre-multiplied by 21's fixed
   transform; verified: every other node matches test 4 in every frame) and reused as the bust node.
   One free node only, so no half-motion ring.
   `GD_JIGGLE_IDLE` adds a constant test bob to every animation (used only to check it in game).

It needs files extracted from the disc, which are not in git: Celia (`sepi_0.*`, `anm00-09.bin`) in
`$GD_GAME/celia`, Wally's `sua_0.gpl` in `$GD_GAME/wally`, and the model tools (`awlchar.py`, `anm.py`,
`wally.py`) in `$GD_PM`. `wally.py` reads `../menuf/tpl2png.py` relative to the current directory, so run
it from the tools folder. The output is byte-identical to `build/`.

## Putting it on the disc

As for the earlier goddess tests (only the two `gd/` files change; `pm.bin` is unchanged from goddess test 6):

```
python3 gcbuild.py --iso HM_AWL_blank1a.iso --out HM_AWL_final4a.iso \
  --replace gd/gd_0.arc=gd/gd_0.arc --replace gd/gd_0.anm.arc=gd/gd_0.anm.arc --allow-unreferenced
python3 postman_npc/make_pm_dol.py HM_AWL_final4a.iso HM_AWL_final4.iso
```

Runs in game (tests 1-2 in Dolphin: loads, animates, face shading fixed in test 2). The archive is larger
than the earlier goddess tests (test 6 was 61 KB) and relies on the 256 KB pool-B spacer from test 6.
