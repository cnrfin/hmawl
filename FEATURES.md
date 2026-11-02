# Feature ledger (read this before saying something doesn't exist)

Everything built for the mod so far, where it lives, and its state. Long chat sessions get summarised and
lose detail; this file is the record. Update it with every feature change. "Scratchpad" items were built in
a session's temporary folder; the ones still only there are marked.

## In main.dol (patched builds v01 -> v02 -> v03, code in unused .init padding)
| Feature | Where | Notes |
|---|---|---|
| Name-plate hearts v7 | `tools/hearts/`, `tools/maindol_v03/` (hook 0x80102598, BUF 0x80005000) | Villagers: long-term friendship record +0xF (0..100): <=50 1 grey, 51-60 green, 61-70 blue, 71-80 red, 81-90 2 red, 91-100 3 red. Celia/Muffy/Nami: love byte +0x1D, 1-5 red from love 20. Joe uses character 0x23's record (pm.c `joe_hearts`). |
| HUD stamina/fullness bars v2 + farmer's name under the face | `tools/maindol_v03/v03.s` (hook 0x80082F94, state 0x80005070..7F) | opguide.agc elements |
| Dog bowl refilled every morning | `tools/maindol_v03/v03.s` | last day at 0x80005060 |
| Ax: given once per boot, swings as a tool (no hit), hoe-row stamina 120 %, no hoe skill | `tools/maindol_v03/v03.s` | |
| Cursed Axe code baked in | checked by make_pm_dol.py (0x800038E0..) | |
| Bed menu Options (v1-v9) | scratchpad `opt/` (Gecko codes) | being scrapped: no audio/language options needed |
| Item description on R | `cheats/item-description-on-r.txt` (hmawl repo, options-menu branch) | Gecko codes |

## pm.bin (custom code, main.dol text section 2 at 0x8035EFA0; arena now 0x8036A000) — `tools/joe/visit/game/`
| Feature | File | Notes |
|---|---|---|
| Postman NPC (8th, 9:00-11:00, milk event 406, Cursed Axe gift) | pm.c, route.h | Common.arc event 406 |
| Choppable logs (appear the day after rain) | logs.c | snow mapc build |
| Tool skill on the HUD (gems, "Field/Animal up" chime) | skill.c, skill_hud.h | level every 500 points |
| Goddess pond offerings | spring.c | |
| $JOE Coin Daily on TV channel 3 | joetv.c (HOOK8) | price = f(seed 1890, day), tools/joecoin |
| $JOE coin: villagers hate it (HOOK9), never a wanted gift (HOOK10) | joetv.c | |
| $JOE dig-site share 10 % halving per chapter; x2 at full Joe friendship | joetv.c joe_dig_frame | |
| Lumber item (0x51C) | make_pm_dol.py data patch | |
| Van only on the 3rd and 7th | make_pm_dol.py (0x802952D4) | tools/van |
| Bench "sit until evening/morning" (time skip, shipping, rest) | pm.c, Common.arc event 407 | tools/benchsit |
| Joe speaks as character 0x23 (Mukumuku's slot): name "Joe" in Message.arc people.mes, hearts from his gifts | events 408/409 speaker 0x23, pm.c joe_hearts | tools/joe/visit test 12 (HOOK12 stub unused, site restored) |
| Joe's visit, trade, talk, gifts | pm.c joe_* , events 408/409 | tools/joe (DESIGN.md, visit/README.md) |
| Joe's faces (blink, angry/happy/neutral per line), mouth flaps + talk gestures timed to the typing, gift take-and-pocket | pm.c joe_face / joe_talk_frame, joe_lines.h, counters 49/50 | visit/README.md test 13 |
| Test keys (Z+B, Z+D-Up, Z+X, Z+D-Left/Right/Down, Z+Y) and debug blocks: removed in Joe test 16; HOOK11 probe unhooked | pm.c, logs.c, skill.c, make_pm_dol.py | visit/README.md test 16 |

## Data files
| Feature | Files | Where |
|---|---|---|
| Joe model, 90 %, cigarette, bench clips, 1.2x walk, face 80 %, talk / sitting talk / pocket clips | gd/gd_0.arc, gd/gd_0.anm.arc | tools/joe/build/test8 (+ test9: mouth frames RGB5A3, soft edges; test10: face 90 %) |
| Joe's lines (mukumuku.mes 38+), people.mes 35 = "Joe" | mukumuku.mes, people.mes | tools/joe/visit/data |
| Trade/talk events 408/409, bench 407 (no cmd_10) | Common.arc | tools/joe/visit/data |
| Villager paths: dig-site bridge, bench spot | PathData.arc | tools/paths |
| Bench turned + collision, bridge walkway (wood footsteps) | mapobj/map files | tools/bench, hmawl repo |
| $JOE coin item (model, texture, docs) | item/itemdoc03 etc. | tools/joecoin/coin |
| Harvest Goddess model (+ jiggle tests) | gd files (earlier) | tools/goddess |
| Sound bank: item-get fanfare (224), wood hit (432), Breeze level-up jingle G (433) | sound/GAME_ALL.arc + .samp | tools/sound (README: rebuild chain from vanilla; SoundFont script, not the 51 MB .sf2) |
| Muffy recolour (pink hair, black dress, orange eyes): textures only, not built into her files yet | mumu_0.arc (future) | tools/muffy |
| Skip intro | Chapter1.arc etc. | tools/skipintro |

## Ideas (not started)
| Idea | Notes |
|---|---|
| Zelda-style Z targeting | Replaces Z's first-person view. Use the OoT decompilation (zeldaret/oot) as a behaviour reference only. Plan: 1) Z locks the nearest villager or animal in range, with a marker, and the player keeps facing them while walking (existing walk animation); 2) a follow camera, which needs the field camera object found (RAM dumps); 3) new player clips for strafing left and right and walking backwards (to work on every chapter's look); 4) cycling targets, targetable objects, a release distance. Needs a hook in the player's movement update. |
