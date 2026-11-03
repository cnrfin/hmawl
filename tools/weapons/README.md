# Weapons

| Weapon | Item | Get it | Model (phase 1) |
|---|---|---|---|
| Stick | 0x4E3 | rucksack at a new game (pm_newgame_stub, HOOK21 0x800136D8) | Hoe mesh (real.gpl 0x10) |
| Wooden Sword | 0x4E4 | ledger 1000 G (phase 3) | Light Hoe mesh |
| Farmer's Sword | 0x4EA | ledger 3000 G (phase 3) | Sickle mesh |
| H.M Murasama | 0x4EB | event (later) | Light Sickle mesh |

Phase 1 (weapons test 1): these ids were the chapter-start "alternate look" of Hoe / Light Hoe / Sickle / Light
Sickle (tools/toolfix/NOTES.md). make_pm_dol.py switches that swap off (item pool li r5 in func_80050DF4, held item
switch at 0x80013D68.., shed alt table lbl_8024EDFC), maps them to themselves in func_800124FC, makes 4E3 / 4E4
sickle-type (category 2, flags 0xA001), moves their usage counters off the hoes', and prices the Farmer's Sword
3000 G. zt.c: the Z-target combo only with these four. add_weapon_text.py: names (Message.arc item.mes) and
descriptions (itemdoc03.mes) on the disc's own files.
Next: phase 2 models (commonall.arc real.gpl / symbol.gpl), phase 3 ledger (10-entry list, first 8 unowned shown,
swords delivered to the tool-shed cupboard: game+0x14D0 vtable +0x30, like the new game's Tomato Seed B).

## Phase 2: models (weapons test 2)
- weapon_models.py: procedural meshes in real.gpl units (1/64, grip at 0, handle +y, edge +z) and swatch textures:
  Stick (plain octagonal handle), Wooden Sword (Kokiri-style practice sword), Farmer's Sword (iron guard + pommel,
  leather grip, steel blade with fuller), H.M Murasama (H.F. Murasama look: slightly curved katana, red edge, gold
  habaki, black round tsuba, red/black diamond-wrapped tsuka). enc_cmpr: CMPR encoder (inverse of tpltool.decode).
- pack_weapons.py commonall.arc.clz OUT: real.gpl models 27-30 and symbol.gpl 196-199 (4 table entries = 0x20, so
  all models keep their 0x20 alignment), textures redrawn in place in real.tpl 0x1F/0x20/0x1C/0x1D and symbol.tpl
  0xDB/0xDC/0xD8/0xD9 (only the old duplicate ids used them). Base 5d7ab970 -> cdc4172d (+9.6 KB unpacked).
- make_pm_dol.py: item rows 4E3/4E4/4EA/4EB bytes +2 / +3 -> the new models.
- preview.py (scratchpad renderer): front / 3/4 / side previews with the decoded CMPR textures.

## Weapons test 3 (user feedback on test 2)
- H.M Murasama rebuilt with Masamune proportions: blade y 9.5..118.5 (1.7 units), gentle curve toward the spine,
  all red with a pink wavy hamon, black square tsuba and habaki, black tsuka with grey segments.
- Farmer's Sword: crossguard curving up at the ends (Mesh.guard_z).
- Textures 32x64 (Stick, Wooden Sword) / 64x64 (swords), appended to real.tpl / symbol.tpl with the image headers
  repointed (tpl_set). commonall 5d7ab970 -> 0a6ed437 (+23 KB unpacked). make_pm_dol.py as test 2.

## Weapons test 4b: menu size
- The rucksack / item views fit a symbol model with a per-model display box (func_800121C4: table lbl_8028E84C, 7 s16
  per model in 1/16384: xmin ymin zmin xmax ymax zmax radius; only as long as the vanilla model list, so models
  196+ read the data after it and came out huge; Lumber was fixed by editing model 11's box). HOOK24 0x80012200
  (add r7,r5,r6, r6 = model * 14) -> pm_box_stub: models >= 196 use zt_sym_boxes (toolfix.c, from the icon meshes).
