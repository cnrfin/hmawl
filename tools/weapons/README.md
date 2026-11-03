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
