# Bench: sit until evening / morning (bench sit test 1)

- `build_bench_event.py Common.arc debug.mes OUT` (inputs = the Postman build: Common.arc 95208117,
  debug.mes 16e98598; needs scratchpad/event tools via EVTOOLS): appends event 407 (Common.arc entry 107)
  and puts "Sit until the evening?" / "Sit until the morning?" (with Yes/No) in debug.mes entries 9 / 10.
  Out: Common.arc a0d491f5, debug.mes 4dd04c6d.
- Script: hour < 6 -> morning prompt, Yes = cmd_43(6, 0) (today 6:00); hour < 18 -> evening prompt, Yes =
  cmd_43(18, 0); else morning prompt, Yes = cmd_44(29 - hour, 60 - minute) (to tomorrow 6:00). Both time
  commands go through func_80109E00 (the game's event time skip). Fade out 0.5 s before, ~0.5 s dark, fade in.
- pm.c: on the valley, A within 1.6 of the turned bench's seat (137.65, 176.60, from its collision box) while
  facing it (cos > 0.5), player free, not Z -> event_start(EVMGR, 407, 0, 0).
- Untested: whether jumping past midnight this way runs the overnight update like the bed does.

## Bench sit test 1 result / test 2
Works once: time, crops, logs and villager positions are right after the skip. But afterwards A at the bench
gave the vanilla "Newly painted... Not really..." until a scene change, and repeated sits ran the stamina out
(the player passed out outside). Test 2: the trigger uses the player's map (game+0x2A290 == 1) and "no event
running" (event manager +0x680 == -1, +0x58C == 0, CONTROL != 3) instead of the field check / CONTROL == 1;
bench_dbg (pm.c) records presses/started/rested and the checked values. On Yes the script sets event counter 27;
pm.c then refills stamina (game+0x11B84 = max +0x11B88). Common.arc e03a8b1f, debug.mes 4dd04c6d (same).

## Bench sit test 3
Sleepy dump (day 7 9:04, stamina full) vs 4 rested dumps: game+0x11BB0 high u16 14 (low u16 0x121 always),
+0x11BB8 17, +0x11BD0 140; all 0 when rested. On Yes pm.c also zeroes these (sleepiness).

## Bench sit test 4 (stepped time skip)
Dumps before/after a nap (day 8 11:32 -> 17:34): uncollected earnings game+0x11A50 0 -> 115; timed jobs at
game+0x11B10..0x11B30 (+ pending flags 0x11B48..0x11B4D) with the shipping pickup at 12:00 (flag 0x11B4C) and a
12:30 job both pending before, done after. The pickup only fires inside the 12:00-12:30 window (0x801335DC checks
start 0x11B28 / end 0x11B30), which a single clock jump skips. Test 4: the script only asks, sets counter 27
(1 evening / 2 morning), fades out and ends on black; pm.c steps the clock 5 game minutes per frame (+ the copy at
lbl_80349194+0x404) to 18:00 / next 6:00 with pad input held off, then refills stamina, clears the sleepy values
and fades back in. Common.arc 60ff57c7, debug.mes 4dd04c6d.
