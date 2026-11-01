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
