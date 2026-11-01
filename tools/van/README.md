# Van's visit days

- Van = villager id 0x23 (char table lbl_802C0450 index 32, record 31 at GAME+0x124C4).
- Per-villager day table lbl_802951C8 (8 B rows; villager id -> row via lbl_802551D8, chapter variants in
  func_80148490): +6 u16 = 10-bit day mask, bit = day of season 0-9 (func_80010034). func_801483E4 tests it;
  the schedule condition switch (0x801230C0) and the daily-plan code (0x8006075C, 0x80060F38) use it.
- Van's row (32) mask = 0x44 = the 3rd and 7th. Most villagers share 0x44 (shop days). So vanilla Van
  already comes on the 3rd and 7th; only his intro line (bahn.mes 0x46) said "3rd and the 8th".
- Van test 1: bahn.mes 0x46 "8th" -> "7th" (02890b7f -> ba87c3d2).
- Van's shop talk = event 366 (Common.arc 65), condition record in EventCondition_Cxx.arc member 8 (no day field).
