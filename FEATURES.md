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
| $JOE Coin Daily on TV channel 3; per-save market (joeseed test 1): each new game picks a random seed on day 1, kept in event counter 52 (saved); older saves keep seed 1890 | joetv.c (HOOK8, mseed / joe_seed_frame from pm_frame) | price = f(seed, day), tools/joecoin; Joe's visit days stay on 1890 |
| $JOE coin: villagers hate it (HOOK9), never a wanted gift (HOOK10) | joetv.c | |
| $JOE dig-site share 10 % halving per chapter; x2 at full Joe friendship | joetv.c joe_dig_frame | |
| Lumber item (0x51C) | make_pm_dol.py data patch | |
| Van only on the 3rd and 7th | make_pm_dol.py (0x802952D4) | tools/van |
| Bench "sit until evening/morning" (time skip, shipping, rest; game's per-minute time skip so villagers keep their schedules (battle9, confirmed), screen held black, a new day re-rolls the wild animal, then a valley reload (battle10, untested)) | pm.c, Common.arc event 407 | tools/benchsit |
| Joe speaks as character 0x23 (Mukumuku's slot): name "Joe" in Message.arc people.mes, hearts from his gifts | events 408/409 speaker 0x23, pm.c joe_hearts | tools/joe/visit test 12 (HOOK12 stub unused, site restored) |
| Joe's visit, trade, talk, gifts | pm.c joe_* , events 408/409 | tools/joe (DESIGN.md, visit/README.md) |
| Joe's faces (blink, angry/happy/neutral per line), mouth flaps + talk gestures timed to the typing, gift take-and-pocket | pm.c joe_face / joe_talk_frame, joe_lines.h, counters 49/50 | visit/README.md test 13 |
| Zelda-style Z targeting (tests 1-16): lock-on to villagers/Joe, switching, yellow bracket reticle, lock on/off sounds 434/435, follow camera with zoom + upward tilt, face the target, strafe left/right + walk-back clips 126-128 | zt.c (HOOK13-16, motion picks 0x80042D44/D98/DD0), opguide.agc reticle quads, boy_0.anm.arc clips | tools/ztarget (NOTES.md), tools/sound, tools/hud |
| Field tile cursor in the Z-target bracket style, soft settle | tile.c (HOOK18 0x80091F58) | tools/ztarget NOTES.md |
| Z-target combo (tests 17-18b, confirmed working; test 19 sickles; weapons test 1: weapons 4E3/4E4/4EA/4EB only, held item game+0x11CC4): B while locked on = 3-hit one-handed combo (quick forehand, quick backhand, heavy overhead), consecutive B chains; upper body only (waist twist, legs keep walking/strafing) | zt.c zt_bone / sw_start / swing_frame (HOOK19 0x8019E5C4 -> pm_bone_stub +0x250), boy_0.anm.arc clips 129-131 | tools/ztarget/anim combo.py + make_attack_clips.py (authored from scratch: IK arm arcs, spine twist), NOTES.md; no weapon model or hits yet |
| Area tools fixed (toolfix 2 confirmed working; toolfix 1; toolfix 2 = neighbours really apply/redraw via the impact message, pasture grass, can W holds 10): Strange Hoe +, Weird Hoe 3x3, Strange Sickle - (across facing), Weird Sickle +, Watering Can W 3x3 | toolfix.c tool_area / tool_area_impact (HOOK20 0x8004390C -> pm_area_stub +0x258, HOOK22 0x800332C0 -> pm_impact_stub +0x2B0) | tools/toolfix/NOTES.md; centre tile must be a field tile hit by case 0xF |
| Weapons phase 1 (weapons test 1, confirmed working): Stick 4E3 (new game, rucksack), Wooden Sword 4E4, Farmer's Sword 4EA (3000 G), H.M Murasama 4EB; names/descriptions; chapter alt-look swap off; combo only with weapons | make_pm_dol.py (weapons patches, HOOK21), zt.c, tools/weapons/add_weapon_text.py | tools/weapons/README.md; models + ledger still to do |
| Weapon models (weapons test 2): Stick, Wooden Sword, Farmer's Sword, H.M Murasama in hand + rucksack | commonall.arc (real.gpl 27-30, symbol.gpl 196-199, textures in place), make_pm_dol.py item rows | tools/weapons (weapon_models.py, pack_weapons.py) |
| Player clips 126-131 served from pm.bin (weapons test 4): mainchapter archives back to vanilla size (fixes the chapter-block overflow behind the test 18 and weapons 3 crashes); arena start 0x80380000 | zt.c zt_arc_anim, clips.s, HOOK23 0x801A0A88, add_player_clips.py (strip) | tools/ztarget/NOTES.md |
| Combo voice (weapons test 6): Toan's voice (user's Dark Cloud disc) with each swing, 440/441/442 = hits 1/2/3; 443 hurt, 444 dies in the bank for later; tired sound 304 replaced with toan_06 (test 7); lock on/off now vanilla 238/239; impact sounds only on enemy hits (test 7b); the day's wild animal is a Z target and the enemy (enemy test 1); hits 1/2 swing = vanilla 196 trimmed, as 445 (test 8) | zt.c swing_sounds (SE_VOICE1 + hit), SE_LOCK/SE_FREE | tools/sound/README.md (audio not committed) |
| Breeze battle theme (v12): heroic arrangement at 184 bpm, 4-bar rise intro then a 32-bar loop from bar 5; flat level. In game (enemy3, testing): a DTK stream /battle/BATTLE.adp that starts when you lock onto a living enemy (field music fades out) and fades out on defeat or when you run more than 13.5 away | tools/sound/battle/breeze_heroic.py, tools/sound/stream (dtk.py), zt.c bm_frame | rendered with hmawl_music.sf2; .adp only in the user's zip |
| Enemy step 2 (enemy2b, testing): the day's wild animal has 120 HP; damage per hit Stick 10 / Wooden Sword 13 / Farmer's Sword 20 / H.M Murasama 40, hit 3 x1.5; each hit flashes it light red (4 frames) and knocks it back 0.35; at 0 HP it freezes, shakes side to side, turns red (15 frames) and flickers out (45 frames), then is hidden, moved off the map and untargetable for the rest of the day; defeat sound 222 (an animal cry, user pick) | zt.c en_hit / en_frame (ENMY record), the model's flat colour +0x3D / +0x3E | findings 7.44 |
| Battle AI test 1 (battle1): while you are locked onto the day's animal its own AI / movement are paused (HOOK28/29) and ours runs: circle at 3 units, wind up, lunge, recover, repeat; a hit staggers it; no damage to the player yet; existing clips: idle 0, moving clip measured per species (lizard / chihuahua "mouse" / turtle 1, tanuki 2 and 1 for the lunge, owl perched); ground-snapped moves, double lunge (battle4); circles facing its travel direction, all wild animals drawn 2x (root-bone scale in the pose since battle7; the skeleton instance scale only took on the chihuahua; collision unchanged), circling facing confirmed (battle5); head turns toward the player, up to ~70° (battle6, confirmed on all species); aggro (battle7): lock-on starts it, lock-off keeps it, ends past ZT_LEASH (or 25 units from home while unlocked), then walks home; battle music follows the aggro; per-species attack poses drawn on the bones (lizard leap + jaw snaps, chihuahua play bow + dart, tanuki butt wiggle + jump + hop gait, turtle shell spin / bite), flinch and hit-3 knockback (battle11, untested) | zt.c ai_frame, hook.s pm_aistep_stub / pm_move_stub | findings 7.46 |
| Memory fixes (memfix 1-19): Joe's archives freed on every scene change (stale model-entry 37 / set-71 pointers cleared); Joe's model + animations loaded into pool A while he is in the valley (op_new / op_delete hooks); duplicate-copy sweep; pool guard: any pool A/B overlap is recorded ('MGRD') and the first shows in Dolphin as an invalid read from 0x0BAD00A0 (A over B) / 0x0BAD00B0 (B over A); memory gauge 'MEMG' every 4 frames | pm.c (joe_free_now, pm_new_a, pm_del_a, dup_sweep, mg_after, mem_gauge), hook.s (pm_new_stub, pm_del_stub, pm_pool_stub), HOOK25-27 | notes/findings.md 7.43 |
| Chapter 1 slimmed: son's animations emptied, Grant / Kate / Samantha (chapter-2 newcomers) get 16 KB placeholder models (their animations / Grant's action tables kept: the load reads them) | tools/memory/strip_chapter.py --put, tools/goddess/scripts/build_stub.py (stubs only in the user's zip) | findings 7.43 |
| Test keys (Z+B, Z+D-Up, Z+X, Z+D-Left/Right/Down, Z+Y) and debug blocks: removed in Joe test 16; HOOK11 probe unhooked | pm.c, logs.c, skill.c, make_pm_dol.py | visit/README.md test 16 |

## Data files
| Feature | Files | Where |
|---|---|---|
| Joe model, 90 %, cigarette, bench clips, 1.2x walk, face 80 %, talk / sitting talk / pocket clips | gd/gd_0.arc, gd/gd_0.anm.arc | tools/joe/build/test8 (+ test9: mouth frames RGB5A3, soft edges; test10: face 90 %; test11: textures at half size, 387 -> 156 KB) |
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
| Zelda-style Z targeting (now built, see pm.bin) + light combat | Next: wildlife as targets/enemies (research done, findings 7.40: one wild animal per day, object at *(*(0x80305FBC)+0x44), position +0x4C), hit detection. Original idea: Replaces Z's first-person view. Use the OoT decompilation (zeldaret/oot) as a behaviour reference only. Plan: 1) Z locks the nearest villager or animal in range, with a marker, and the player keeps facing them while walking (existing walk animation); 2) a follow camera, which needs the field camera object found (RAM dumps); 3) new player clips for strafing left and right and walking backwards (to work on every chapter's look); 4) cycling targets, targetable objects, a release distance. Needs a hook in the player's movement update. |
