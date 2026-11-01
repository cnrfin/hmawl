# Van's visit days

- Van = villager id 0x23 (char table lbl_802C0450 index 32, record 31 at GAME+0x124C4).
- Per-villager day table lbl_802951C8 (8 B rows; villager id -> row via lbl_802551D8, chapter variants in
  func_80148490): +6 u16 = 10-bit day mask, bit = day of season 0-9 (func_80010034). func_801483E4 tests it;
  the schedule condition switch (0x801230C0) and the daily-plan code (0x8006075C, 0x80060F38) use it.
- Van's row (32) mask = 0x44 = the 3rd and 7th. Most villagers share 0x44 (shop days). So vanilla Van
  already comes on the 3rd and 7th; only his intro line (bahn.mes 0x46) said "3rd and the 8th".
- Van test 1: bahn.mes 0x46 "8th" -> "7th" (02890b7f -> ba87c3d2).
- Van's shop talk = event 366 (Common.arc 65), condition record in EventCondition_Cxx.arc member 8 (no day field).

## Van test 1 result / test 2
Test 1 showed Van in town on days 1, 3, 7, 8, 9 (and 6 on another run): the 0x44 mask days are guaranteed,
other days are random. Dumps of day 2 (away) and day 6 (there) differ only in his current action (a small
object holding the villager pointer, made by the action factory func_80070AF4(type, slot, villager, x)):
day 6 action 0x10 (class 802A99E4), day 2 action 0 (none, class 802A92C0). His record, state object and
villager object (except position) are the same.
Test 2: hook at 0x80070AF4 -> pm_van_stub (+0x1B8) -> van_action (joetv.c): for villager 0x23 every action
becomes 0 unless it is the 3rd or 7th of the season (or day 0, the intro).

## Van test 2 result / test 3 (probe)
Day 5 dump with test 2: action 0 (hook worked) but Van still at his stall. The only state that differs
between away and present days is his position: path spot 0x000C0001 (281.9, 128.1: away, hidden) vs
0x000C0002 (280.0, 122.6: at the stall). His schedule (lbl_80295340 row 32: villager -> 0x28-byte row)
has one entry (type 6) and a weight table at 0x802DD4E4: 25 25 50 25 45 30 100 0 0 20 80 0, used by the
weighted pick func_80147F60 (callers 0x80067B4C, 0x80068D40).
Test 3 drops the action hook and logs Van's weighted picks (pm_van_stub at 0x80147F60 -> pick_log,
buffer van_log: 'VANL', n, 64 x {day, tod, weight offset, count, result}).

## Van test 3 result / test 4 (fix)
The probe logged nothing: Van's day isn't a weighted pick. Run 3 had him on days 1, 2, 3, 8 (not the 7th).
Comparing present dumps (days 5, 6) with away dumps (days 2, 10): the stall Van is villager **0x24**
(record 32, object with +0xBC = 36), not 0x23 (record 31, never plans). Record 0x24 +0x24 (daily plan,
func_80078228) = 1 on present days, 4 on away days; present position = path spot 0x0000000A (141.2, 106.9).
Day table row 33 (id 36 via lbl_802551D8) = 08 37 3C 23 50 00 03 7B: mask 0x37B = every day except the 3rd
and 8th. In the daily planner (0x80060EF8): mask bit clear -> option 2 (works the stall); set -> option 4
(away), plus option 1 (stall anyway) when rand(1..100) <= byte 4 (80) and rand(50..100) <= record +7.
Test 4 (make_pm_dol.py data patch, word 0x802952D4): 0x5000037B -> 0x000003BB = chance 0, mask clear only on
the 3rd (bit 2) and 7th (bit 6). Probe hook removed (its code stays in pm.bin, unhooked).
