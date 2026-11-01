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
