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

Build (from HM_AWL_sit5b.iso): gd_0.arc (test 6), gd_0.anm.arc (test 5), then make_pm_dol.py.
pm.bin SHA-1 95a81d22, make_pm_dol.py 7aa233f6.
