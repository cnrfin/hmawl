# Joe's visit (test 1: walking and sitting, no talk yet)

`game/` = the pm.bin sources (copies of the postman_npc code) with Joe's visit added (`joe_frame` in pm.c),
`gen_route.py` = `game/joe_route.h` from the valley path network (path_WorldMap.pth after paths test 1; run in
a folder holding `N.npy` / `net.json` exported from it).

- Days: `joe_visit_day` (joetv.c) = the TV's `joe_today`: one early day {1,2,4,5}, one late {6,9,10}, not winter.
- Route (61 path nodes): east road (463) round Celia's farm to the dig-site end of the bridge (469, 230.6 u),
  over the bridge and down the west corridor to the bench (285, 158.4 u), south road back to 463 (174.3 u).
- Clock: +20 tenths of a game second per frame (func_800102F0), so 1 game hour = 1800 frames (~1 real minute).
  Speed = his 1.2x walk clip's stride, 0.0406 u/frame = 0.00203 u per clock unit.
- Times: in 6:20, dig site 9:30-9:50 (faces east, idle), bench 12:00: sit down (clip 6, facing the bench = -x),
  59 frames later the sitting loop (clip 7, turned to +x), 18:00 stand up (clip 8, 40 frames), walk out, gone 20:24.
- While he sits, A at the bench doesn't open the sit prompt (`joe_here`); trading comes next.
- Slot 37 with `S.who = 2` (Joe's model, gd_0); the goddess test (Z + X) stays `S.who = 1`.
- Test key: Z + D-Up = today is Joe's day, clock forward to his next stage (6:20, 9:25, 11:55, 17:58, 20:14).
- Bench sit test 11 probe removed (plan_log is an empty function, its hook kept). pm.bin 28,624 B, ends 0x80365F70.

Build: on top of HM_AWL_joe5.iso (sit14 code + Joe test 5): gd_0.arc (test 6), then make_pm_dol.py, which now
replaces an existing Postman section (update mode). pm.bin SHA-1 95a81d22, make_pm_dol.py see below.
make_pm_dol.py with update mode: SHA-1 aeeb6c11.

## Test 2: no second sit down
The game cross-fades clips (in local space). Sit down -> sitting flips his facing 180 degrees, so the fade
started from the sit down's last pose under the new facing and looked like a second sit down. `joe_motion`
starts clip 7 twice in that frame, so the fade runs from clip 7 into itself. pm.bin SHA-1 cd29a76b
(ends 0x80365F94). Stand up (no turn) was already fixed by test 7's held last pose.

## Test 3: no cross-fade into the sitting loop
Test 2's double start didn't help (the fade source is kept). The fade length is in the motion entry:
func_8017DB28 reads word 1 bits 6-10 as cross-fade frames (31 = default 10) for func_801A6878. Joe's entry 7
(sitting loop) now has 0 (word 1 0x07FBF83F); the others keep the default. Double start removed.
pm.bin SHA-1 c54eae7b (ends 0x80365F90).
(actor_motion passes f1 through unset to func_8017D74C, which stores it as the playback-rate factor:
worth checking if a clip ever plays at the wrong speed.)

## Test 4: trading at the bench
- The number picker: the game's global script picker at 0x802F3D70 (class 0x802BD754, ctor func_80106504;
  the one Vesta's and Van's shops show), driven by script commands D5 (open, buy: max = 198 - held), D6 (poll,
  1 when done), D7 (value, 0 on cancel), D9/DA/DB (sell: max from the held count). Found by diffing two dumps
  of Vesta's picker at 3 and 4. CC(slot, n) sets message number slots (<2A 00 nn>), C1/C2 gold, D3/DC add/remove.
- `build_joe_trade.py`: event 408 (Common.arc node 108) + debug.mes 11-20 ("I'm selling $JOE for <price>G
  today", buy yes/no, picker, sell yes/no, "What!? You're selling your $JOE?", "Hm, ok, I'll buy your $JOE
  bags for <price>G", ...). Inputs: the bench build (Common 700e4ae4, debug 4dd04c6d) -> `trade/` (Common
  0cb841e9, debug 6c1b2dbc).
- pm.c: A next to Joe while he sits starts event 408 (counter 44 = $JOE held, number slot 0 = today's price,
  `joe_price_today` = the TV's price); the script asks via counter 41 (1 buy / 4 sell, count in 42) and pm.c
  does the gold and coins (the script VM's x128 multiply would overflow). Same price both ways.
- pm.bin grew past 0x80366000: arena start moved to 0x8036A000 (OSInit main and debug paths);
  make_pm_dol.py's update mode accepts the earlier arena words. Checked on a mock disc (fresh then update).
- No expressions yet (the angry "What!?" line is plain).
pm.bin cca2dccd, make_pm_dol.py ce24f38c.

## Test 5: talk camera, cash chime, bench camera test
- Trade event: `cmd_10` then `cmd_A0(37)` = the game's NPC talk camera (as Common script 88 does with
  character 5). cmd_A0 reads the character's position/direction from the event system's per-character
  slots, game+0x29C78 / +0x29F84 + 12 x id (id 0 = the player); pm.c writes Joe's seat (bench centre,
  facing +x) into slot 37 before and during the event.
- Cash chime: sound 0xCD (what script cmd_C1 plays on a gold change) after a buy or a sale.
- Bench (event 407): built without `cmd_10` (`BENCH_NOCAM=1`) to test whether that is the camera jump.
- Common.arc a4646e86 (bench without cmd_10 + trade), debug.mes unchanged (6c1b2dbc). pm.bin 84f171ce.
- Money window: not found yet (the shops draw it from their own REL code).

## Test 6: money window, Joe stays seated, camera a little further
- Money window: script cmd_DD(flag) = func_80109048(evmgr, flag), shows/hides the event system's gold
  window (object 0x802F3A1C, drawn by func_80106D08 from the game's gold). Found by diffing two dumps
  (window shown / closed). The trade turns it on after cmd_A0 and off at the end. Common.arc 411f77e3.
- The event start stands character 37 up (actor +0x214 leaves state 4): during the trade pm.c restarts the
  sitting loop when that happens.
- Talk camera a little further: character 37's slot point is 0.4 behind the seat centre.
- Test 5 results: first-person camera works (slightly too close), the bench jump is gone (cmd_10 removed),
  the cash chime plays. pm.bin 1e2b5c33.

## Test 7: own first-person camera (no cmd_A0)
cmd_A0(37) also moves character 37 to its slot point and turns it to the player in the talk idle (test 6:
Joe stood up, behind the bench). Dropped: pm.c writes counters 20-25 (eye at the player's head 1.4 up,
0.2 toward Joe; target Joe's face, bench centre 0.95 up) and the script feeds them to cmd_14/cmd_15, as the
Postman's talk does. Re-sit check and slot writes removed. Common.arc 8d2db2a8, pm.bin b2b5effb.

## Test 8: camera distance, player hidden
Test 7 (eye at the player's head) was far too close: the player stands right by the bench. The eye is now
2.6 from Joe toward the player, 1.35 up, aimed at his face (0.95 up); cmd_5A(0, 0) hides the player during
the trade (cmd_A0 did that), cmd_5A(0, 1) shows him again. Common.arc e3022926, pm.bin 5ded727e.

## Test 9: talking while he walks, secret $JOE gifts, friendship
- `build_joe_talk.py`: event 409 (Common.arc node 109) + debug.mes 21-27 (input: the trade build ->
  `talk/`, Common 44d710f7, debug 52b153f1). Camera from counters 20-25 (aimed at his face, 1.1 up), player
  hidden. Line chosen by pm.c in counter 48: 1 intro + bench hint (first meeting), 2 bench hint, 3 dig site
  (9:30-9:50), 4 fall (crypto winter), 5 gift, 6 tenth gift, 7 second gift the same day.
- pm.c: A next to Joe while he walks or waits (not at the bench): he stops, turns to the player, idles
  until the event ends, then carries on along the route. Holding a $JOE coin = a gift: once a visit
  (counter 47 = day + 1), counter 46 counts them (10 = full friendship); the script takes the coin from the
  hands (cmd_56). Counter 45 = met. Other held items: just his normal line.
- joetv.c: full friendship (counter 46 >= 10) doubles the dig site's $JOE share.
- pm.bin b9968e36 (ends 0x80366834).

## Test 10: Joe's name and heart in the window, new lines
- `build_joe_mes.py`: Joe's lines appended to mukumuku.mes (entries 38+, Mukumuku's 38 kept) and
  people.mes 35 "Mukumuku" -> "Joe". cmd_04(file, msg, speaker): speaker != -1 maps the file to a character
  (table 0x80251A38: file 0x15 mukumuku.mes -> character 0x23) and shows that character's name
  (people.mes[character]) and heart. Both events now use cmd_04(0x15, line, 0).
- Lines: gift "Woah, a $JOE for me? My yigga!" (every gift; still counted quietly for the dig bonus),
  second gift the same visit "You keep a hold of that for now my yigga. $JOE finna boutta.", fall "Hey,
  my yigga. Crypto winter is coming, so I won't be around until spring. So figure out what you wanna do
  with your $JOE before then."
- data/: Common.arc d0f89ea4, mukumuku.mes 5dfdab5d, people.mes 22b9572a (debug.mes as test 9). pm.bin c721c54c.
- The heart shows character 0x23's friendship (not yet tied to the gifts).

## Test 11: name plate for Joe's lines (HOOK12)
Test 10 showed no name: every script message goes through func_80113864, which calls func_801020E4 with
mode 0 (window without name plate; the speaker is ignored). Villager talk uses mode 1 (name + heart:
+0x5C layout +0x314, speaker -> character via table 0x80251A38). HOOK12 = that bl at 0x80113894 ->
pm_msg_stub (pm.bin +0x1E4): file 0x15 (Joe's lines in mukumuku.mes) opens in mode 1, everything else as
before. make_pm_dol.py: new 'blhook' patch type. Checked on the mock disc (update mode). pm.bin ab37596e,
make_pm_dol.py 17653839.

## Test 11b: Joe's hearts
pm.c joe_hearts: before a talk or trade, character 0x23's villager record (func_8000DC24) +0xF =
40 + 6 x gifts (cap 100), so the name-plate hearts (v03 hearts v7) follow his $JOE gifts: 0 gifts 1 grey,
2 green, 4 blue, 6 red, 8 2 red, 10 3 red. pm.bin c019bebd (pm_msg_stub still at +0x1E4).

## Test 12: the real fix for name and heart
func_801020E4(mgr, mode, file, msg, speaker): mode 0 = the talk window (layout +0x314, white text), any
other mode = the sign-post board (layout +0x34C, dark text). With mode 0: speaker -1 -> character from the
file (table 0x80251A38), else the speaker is the character id itself; the name is drawn only if the
character is in table 0x80251A90 (1..0x26). Test 10 passed speaker 0 (no such character -> no name); test 11's
hook forced mode 1 (board). Now: speaker 0x23 in both events, HOOK12 site restored to the original bl
(make_pm_dol.py update mode accepts the test 11 word). The name plate reads people.mes inside Message.arc
(loaded at boot): `build_joe_message_arc.py` sets entry 35 to "Joe" (input: the $JOE coin build 3205b29b).
data/: Common.arc d40c7e13, Message.arc 70a46b73. pm.bin c019bebd, make_pm_dol.py dff40754.

## Test 13: faces, talking, the gift pocket, smaller face
- Face: Joe's character slot has a face object at slot +0x124 (func_8002F39C / F3E8 set, F548 draws):
  +0 eye, +4 mouth; eye >= 58 / mouth >= 36 = animation (value - 58 / - 36) of the common
  char_com_eye.tam / char_com_mouth.tam (commonall.arc; pointers 0x803490F0 / F4, played with
  func_8017E11C into +0x14 / +0x24), else a still frame. +8 >= 0 = a motion's own face animation.
  The common animations fit Joe's frames: eye 9 blink 0-2, 3 angry 6-8, 11 sad 18-20; mouth 11 flaps 0/1,
  9 angry 7/8, 0 smile 4/5, 6 sad 9/10. (The 0x1AC chara class has a second face at +0x17C with
  chanml_com_*.tam = animals.)
- Talking: both events set counter 49 = line + 1 before each line (`gen_joe_lines.py` -> game/joe_lines.h:
  face and letters per page). pm.c follows the typing (JT_FRAMES = 2 frames a letter; A finishes a page or
  turns it): mouth flaps and the talk clip while typing, still mouth and idle / sitting loop after.
  Faces: angry on "What!?", happy (smile) on intro, bought, gifts; neutral otherwise. Blinks all the time.
- Gift: the talk event sets counter 50 = 1 after taking the coin (cmd_56) and waits; pm.c plays the
  take-and-pocket clip (90 frames) and sets 0, then the line.
- Clips (joe_sit.py): 9 standing talk (Van's clip 17 "explaining", 155 frames), 10 sitting talk (cigarette
  hand comes off the knee and gestures, head nods, left hand stays on the backrest, 120), 11 gift (reach,
  look, back pocket, 90 + 90 hold); motion 12 = the sitting loop with the cross-fade (after talking).
- Face 20 % smaller: `JOE_FACE=0.8` (joe_game.py scales the eye and mouth patches about the canvas
  centre 256, 269). Build: `JOE_SCALE=0.9 JOE_CIG=.../cig.json JOE_WALK=28 JOE_FACE=0.8 joe_game.py`;
  with JOE_FACE unset the build reproduces test 6 / test 7 exactly.
- Files: data/Common.arc f8cdeca9, build/test8 gd_0.arc d0d845f6, gd_0.anm.arc 406beace; pm.bin ed25ecff.

## Test 14: cleaner mouth edges
Same mouth art. The mouth frames were CMPR (2 colours per 4x4 block, 1-bit alpha): the teeth / gums / skin
mix turned into blocky specks and jagged outlines. Now (`JOE_SOFTMOUTH=1`, frames.py `soft`): the hard mask
blurred at full size and area-averaged down (smooth edge, creases kept), stored as RGB5A3. gd_0.arc grows
278 -> 387 KB (mouth tpl 38 -> 147 KB). build/test9 gd_0.arc (gd_0.anm.arc as test 13).

## Test 15: face through the expression table, debug block, face 90 %
Test 14 showed no face or talk animation. The face writes went straight into the slot's face (+0x124);
the game's own expression calls (func_8002F3E8 via the character's table) can override that. Now
character 37's six expression-table pointers (0x8029F818 + 0x18 x 37) point at Joe's table while he is
loaded (restored in restore_names); every entry = the wanted (eye, mouth) and pm.c calls func_8002F3E8(face, 0)
each frame. Debug block `joe_dbg` at 0x803660F8 (magic 'JOED'): raw counter 49, line, page, timer, motion,
face eye/mouth now, wanted eye/mouth, frames, pocket, in_event, slot. Face 90 % (`JOE_FACE=0.9`), soft mouth.
build/test10 gd_0.arc a18dc9b5; pm.bin 25407471.

## Test 16: test leftovers removed
- Test keys gone: Z+B (clock to 22:00), Z+D-Up (Joe's next stage; and logs.c's "today counts as rainy" on the
  same keys), Z+X (Goddess test, goddess_test removed), Z+D-Left/Right/Down (Postman visit / stop / milk),
  Z+Y (skill.c +250 points).
- Debug blocks gone: joe_dbg, bench_dbg.
- HOOK11 (villager daily plan -> pm_van_stub -> plan_log, the bench-sit test 11 probe) restored to the
  original instruction; make_pm_dol.py update mode accepts the old branch word (0x482FE260). The stubs stay
  in hook.s (their offsets are checked) but nothing calls them. Same main.dol from a fresh and an update patch.
- pm.bin bb159d80 (0x7740 bytes), make_pm_dol.py 79640674.
