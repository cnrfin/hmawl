# Tools: glitched area tools + unused item slots (research)

## Tools in the game (user's list, wiki)
- Hoe: 4DE Heavy (start), 4DF Hoe (ledger 800 G), 4E0 Light (1000 G), 4E1 Strange (Tim + Ruby event; should till +,
  GC tills 1), 4E2 Weird (Vesta, ch2; 3x3).
- Sickle: 4E5 Heavy (start), 4E6 Sickle (600 G), 4E7 Light (750 G), 4E8 Strange (Gustafa; should cut -, GC cuts 1),
  4E9 Weird (Dr Hardy, ch2; +).
- Watering can: 4EC S (35), 4ED (70, 600 G), 4EE L (140, 750 G), 4EF W (Romana; 3x3, GC waters 1).
- 4F2/4F3 fishing poles, 4F4/4F5 lures, milkers 4F6/4F7, goat milkers 4F8/4F9, 4FA shears, 4FB clippers,
  4FC/4FD electric clippers, 4FE brush, 4FF shovel, 500/501 nursing bottles, 502 Cursed Axe.

## Unused duplicates (weapon slots)
- 4E3 "Hoe", 4E4 "Light Hoe", 4EA "Sickle", 4EB "Light Sickle", 4F0 "Watering Can", 4F1 "Watering Can L": not in
  the shed's 5 slots; each still has its own case in the tool switches (func_8004D1EC/4F0/6E0/8BC) and an item
  table entry. Plan: weapons go here, no real tool is removed.

## Code
- Item table lbl_80282DF8, 0x24 per item, +0 = category (1 hoe, 2 sickle, 3 can, 4 rod, 5 milker, 6 shears ...).
  Watering capacity at +0xC low half (S 35, 70, L 140, W 1).
- Per-tool usage counters: func_8004D4F0 (increment), func_8004D6E0 (read): 4DE-4E2 share one case indexed per tool
  (6-byte entries), 4E3 / 4E4 their own fields (+0x9E / +0xA4). func_8004D1EC / func_8004D8BC: per category.
- No literal +/3x3 offset tables in the data (scanned s8/s16/s32/f32): the area logic seems missing on GC.
- Field objects get a tool-hit message: func_8008EE80(obj, msg) (vtable lbl_802ADD58 slot +0x30) -> per type/state
  ptmf table lbl_802AFF08 +0x30 -> handlers (0x800964D4-0x80097F00) check msg+4 == 1 and item msg+0xC.
- func_80028988: per-tool text lookup (lbl_8029BECC), Strange/Weird hoes have their own entries.
