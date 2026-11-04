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

## Bench sit test 5
Test 4: shipping paid, but loading a 5:00 save ran the clock to 6:00 - event counters 0-29 count up every day
(all 1 in the dump), so counter 27 turned "on" at each day change. Test 5 uses counter 40 (no Chapter/Common
script touches it) and pm.c only acts on the values 7771 (evening) / 7772 (morning). Tiredness: still not
found (the three cleared values are already 0 in the tired session). Common.arc 700e4ae4, pm.bin aa6b8002.

## Bench sit test 6
Bed dumps (day 4 18:53 -> day 5 1:44): game+0x11C9C (last woke up) day 3 21:00 -> day 5 1:38, game+0x11CA4
(last went to bed) day 1 5:20 -> day 4 18:35 (the session had only bench sits since the start). Test 6 sets
these at the end of a sit: +0x11CA4 = the sit's start, +0x11C9C = now. Shipping: the pickup is the 12:00-12:30
job (not 5:00); days 1-3 had no pickup in the user's run (to check against vanilla).

## Bench sit test 7
Bed run: milk picked up at 5:00 day 2, paid by 12:30. The checks that flag the pickup (func_801331DC: window
game+0x11B38..0x11B40 = 5:10-5:40, event flag 0x3A) and the payout (func_801335DC: 12:00-12:30, flags 0x3B/0x3C)
run from func_80136260 -> func_801331A4(game+0x11B58), which only wlp2 (farm/house) calls - on the valley the
bench skip passes the windows with nobody checking. Test 7 calls func_80136260 on every step of the bench skip.

## Bench sit test 8
Tired dump with test 6 (now day 5 18:03): last woke/bed set by the sit (5/18:00, 5/9:04) but game+0x11CB4 =
day 4 19:00 (passed) and +0x11CAC = day 6 15:00. After a bed sleep (woke 5/1:39) they are 5/17:39 (+16 h) and
7/13:39 (+60 h): "sleepy from" and a later limit. Test 8 sets them the same at the end of a sit.

## Bench sit test 9
Test 8: no more sleepiness. Still: the pickup isn't done properly, and spamming A could reopen a prompt right
after a sit. The A trigger is now blocked during a skip, while counter 40 still holds a request, while the fader
is busy (FADER+0x60), and for 60 frames after the fade-in.
Shipping notes: EventCondition record field 183/7 is the condition id (EventCondition.txt); condition 58 =
CONDITION_TRADE_SHIPMENT = event flag 0x3A set by func_801331DC. Event 311 (Common.arc 10, Takakura, 1035
instructions) is listed for it with field 10/8 = 1 or 11 and 18/8 = 10.

## Bench sit test 10
Pickup has two paths: in the storage room (map 10) at 5:10 Takakura's cutscene (event 311), elsewhere the trade
manager's 5:10 job starts event 310 (Common.arc 9, ~12k instructions, the morning trade script) unless the player is
/ was just on map 10. The trade manager (*0x803491EC, vtable 0x802C1940 at +0x10, update slot 0x10 = 0x80134104,
skipped when the flag arg has 0x4) keeps its job times/flags at game+0x11B10..0x11B4F and queues each day's jobs
itself (job 0x11B4B -> func_8013477C -> func_80132F00). In every bench-session dump its times are stuck on the last
day spent on the farm: its update only runs while wlp2 is loaded. Test 10 calls update(obj, 0) on every bench step.

## Bench sit test 10 result / test 11 (probe)
Test 10 dump (day 2 6:05 after a bench night): the trade job table (object at game+0x11B00, vtable 0x802C1860;
times +0x10..+0x48, flags +0x48..) holds only day 1's 5:10/5:40 entries, the rest -1: nothing was scheduled.
The schedulers (job table methods 0x80133D54 / DA4 / DB8 / E08: set time pairs and job flags) are only called
from the villager daily plan func_80060EF8, in the branch for villager 7 = Takakura (0x80061168..0x80061298),
after checking the shipping containers game+0x111BC / +0x1119C (addis 1 + 0x11BC) (func_80053234). Test 11 logs every daily plan
(hook 0x80060EF8 -> pm_van_stub -> plan_log, buffer plan_log_buf at 0x80365990).

## Bench sit test 11 result / test 12
Plan log: every villager plans its day at its wake time (day 1: Takakura 7 at 5:01, others 6:00-13:06). After a
bench night, day 2 shows only 10/18/17 at 6:00 (just after the skip) - Takakura's 5:00 plan never ran, so no trade
jobs were scheduled. His wake check only fires in a short window that the 5-minute steps jump over. Test 12 steps
1 game minute per frame for 4:50-6:10 (5 minutes elsewhere). Probe log kept.

## Bench sit test 12 result / test 13
Still no Takakura plan on day 2 with 1-minute steps: his wake-up isn't processed while the player is off the farm.
The NPC manager (*0x8034916C) holds the villager objects at +4*id (Takakura = +0x1C). func_80060EF8 only reads
state+8, so test 13 calls it with a stand-in state {0, 0, Takakura} once per day of a bench skip at 5:00-5:10;
the 1-minute steps, trade_update and ship_check then run the 5:10 pickup. Code ends at 0x80365F88 (arena 0x80366000).

## Bench sit test 14
Stepping the whole skip left villagers where they stood (test 1's single jump placed them right). Test 14 jumps
the clock except through two stepped windows (1 game minute per frame): 4:58-5:45 (Takakura's plan + pickup) and
11:58-12:35 (payout). The van test 5 day logger is removed (space: code now ends 0x80365BC4; plan log at 0x803656B8).

## Bench sit test 12 (battle8): reload the valley at the end
User: after a bench night the animals did not respawn and villagers stay where they were; the bed's morning
reloads the field when the player walks out. The event warp (cmd 0x2C, func_8010D5A8) for maps -1..2 / 0x52 calls
func_8017767C(g_system, 4, 0) (g_system+0x58 = next scene 4 = field, +0x64 = 1, +0x78 = flag) and then sends
message 0x1F (func_8004579C(msg, receiver 1, 0, 0x1F, record, 0) + func_80011680) to place the player; without it
the player spawns at position entry 0 (game+0x29C78 / +0x29F84 = where he stands). pm.c: at the end of the skip,
on the valley, scene_req(g_system, 4, 0) instead of our fade-in. The field load fades in itself (func_80012900,
0x80012984, 1 s); fallback: 60-600 frames later, valley up and fader idle with its last target black
(fader +0x50 = to colour, alpha +0x53) -> fade in. bench_reloads counts reloads. pm test 237a4738, normal 5b76ae08.

## Bench sit test 12 result / test 13 (battle9)
Test 12 (user): times right, fade clean, shipping OK; but villagers stay where they were (e.g. still walking out of
the valley the next morning), Joe (ours, time-driven) right; after defeating the day's animal the bench brings the
same species back every day; and the prompt opened while the X item menu was up (CONTROL 0), leaving a second menu.
Cause of the villagers: writing the clock does not simulate them. The game's event time skip (func_80109E00 while an
event runs adds to lbl_80349334; at event end func_8000CC94(lbl_80109E44) registers the callback) runs, per minute:
f = func_80012568() | 0x400 (sda2 lbl_8034AFC8); func_8017CD7C / CDC0 / CE04(lbl_8034923C, f); func_8017CFD4(+0x74);
func_8017CF2C(+0x48); func_800101FC(clock obj *0x80349218, 1); func_80015760(lbl_803491D4, f); clock obj +8 (control)
held 1 meanwhile (func_80010158 first rounds the clock up to a whole minute). Villager objects are rebuilt on every
scene load (func_80079974) from that persistent state. Test 13: the bench runs this per-minute body itself, 60 minutes
a frame (1 through the farm windows), with Takakura's plan / ship_check / trade_update every minute; the prompt needs
CONTROL == 1. The wild-animal pick is not traced yet (loader func_80154604 -> func_8002B9F8, species table
lbl_8024A534); to check whether the simulated day change fixes it. pm test fd1f132f, normal e308c4d9.

## Bench sit test 13 result / test 14 (battle10)
Test 13 (user): villagers now where their schedules put them. The sky showed through the skip, changing at 2-4 fps;
the day's wild animal never changed over bench nights (the bed's morning changed it). The species lives at
lbl_80349194 +0x3F8 (read by the valley set-up at 0x80014358 -> func_80159A28) and is rolled 0x2C + rand() %
(lbl_803469D8 + 1) (= 4: lizard, mouse, tanuki, owl, turtle) at 0x80013B64..B88 (the morning after the bed) and at
0x800132AC..CC (another scene set-up). Test 14: a bench skip that crosses midnight rolls it the same way before the
reload (bench_rolls); each skip frame snaps the fader to black (0 s, black -> black) if its target is not black.
pm test ee451861, normal 09c4273e.
