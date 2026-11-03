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

## The send and the fix (toolfix 1)
- func_80043120 (A action): target = cone search func_80010A94 (pos player+0x4C, dir +0x58); action from table
  lbl_80292A78[itemKind*0xAC + targetKind]; switch lbl_802A7470. Case 0xF (0x800438A8) = hoe / sickle / can on a
  field tile: func_8004579C builds the message at r1+0x778 (+0 sender, +4 type 1, +8 water flag, +0xC item,
  +0x10 target id), func_80011680 sends it (-> func_800116F8 -> object by id -> func_8008EE80). Handlers only set
  a pending action (func_8008F6E8: +0x77 = 3, +0x76 = 1); the tile's update applies it. Stamina / skill / water
  are charged by the player's tool state, once.
- Tiles: 210 permanent objects, id 0x1A5 + g, array *(0x80349200)+0x4C stride 0x308; +0x70 descriptor {w, h, flag,
  first}, +0x74 g, +0x75 l; a = l / h (x), b = l % h (z), pos = base + (a + 0.5, b + 0.5). Fields: 7x5 (g 0-34),
  5x7 (35-69), 10x14 (70-209).
- HOOK20 0x8004390C (lwz r0,0x1c(r1) after the send) -> pm_area_stub -> tool_area(msg, item, player): neighbours by
  shape, target id rewritten and re-sent, then restored. Not yet covered: sickle with a bare-soil centre tile
  (case 0x17 at 0x80043BCC sends nothing), hoe on target kind 0x24 (case 0x12, message at r1+0x744).
- No per-tool area logic exists anywhere (dead or alive); the Strange/Weird compares elsewhere are skill gain
  (func_8001216C), stamina (func_8004E3B4), text (func_80028988), dialogue, inventory swaps.

## Weapons plan (user's design)
| Weapon | Slot | Source |
|---|---|---|
| Stick | 0x4E3 | tool shed from a new game (like Heavy Hoe / Heavy Sickle / Watering Can S) |
| Wooden Sword | 0x4E4 | ledger, 1000 G |
| Farmer's Sword (iron) | 0x4EA | ledger, 3000 G |
| H.M Murasama (pun on H.F. Murasama) | 0x4EB | special event (later) |
Models: Stick can reuse a tool handle; the three swords need new models. 0x4F0 / 0x4F1 stay spare.
Combo (zt.c) to accept these ids as well as the sickles.

## Research round 2 (models, shed, ledger, new game) — correction: the "duplicate" ids are LIVE
- Duplicates are alternate looks of the same tool: 4DF<->4E3, 4E0<->4E4, 4E6<->4EA, 4E7<->4EB, 4ED<->4F0, 4EE<->4F1,
  4F6<->4F7, 4F8<->4F9, 4FC<->4FD. func_80013CEC (chapter start, lbl_8001307C, chapter < 5) converts real -> dup:
  shed flag 0x10 (func_80057970), item pool (func_80050DF4, li r5 at 0x80050F74/FF8/0x8005107C/0x80051100), held item
  (jump table lbl_802981C8). Back: func_800124FC (table lbl_80298068; blr stub 0x80012564), used by tool code.
  Repurposing them needs those patched, and saves past a chapter change already hold them as real tools.
- Models: item row +2 symbol.gpl model, +3 real.gpl model (0x1A none), +4/+6 symbol.tpl, +8/+A real.tpl
  (commonall.arc real.gpl / real.tpl / symbol.gpl / symbol.tpl). func_80011F68 picks real if +3 != 0x1A.
  Carry pose holder player+0x1454 uses the real model only for categories 1, 2, 4 and item 0x4FF (checks at
  0x80031058 / 0x80031B80 / 0x80031C20). Hand attach func_8007C934 (right) / func_8007C958 (left). Existing pipeline
  for appending models: scratchpad/commonall/gplmodel.py, make_axe.py, pack_axe*.py (findings 7.16).
- Price = row +0xC x 10 (shipping x 5). 0x4E4 +0xC = 0x64 (1000 G); 0x4EA = 0x3C.
- Shed: flags game+0x1558[22] (0x80 owned, 0x01 on shelf, 0x10 alt), ids lbl_8024EDA4 / alt lbl_8024EDFC, screen in
  wlp1.rel (toolshelf.agc / .tpl, 22 slot positions, nav lbl_0004A240 23 nodes). No spare slots; a new row means
  ~46 main.dol + 15 wlp1 bounds, new tables, save bytes (pm.bin reimplementation).
- New game: lbl_8001361C: func_8004FDA0(game+0x50, 0x4F6, 1, -1) (pool), func_8005774C(game+0x1550, id) for
  4DE / 4E5 / 4EC (shelf).
- Ledger: tool list lbl_8024ED84 (8 u32: 4DF 4E0 4E6 4E7 4ED 4EE 4FA 4FC), getter func_80053EE0, 8 rows max on the
  ledger screen (wlp1 0x26908), order bits u16 record+0x36, delivery 0x801348DC puts tools on the shelf.
- Names: item.mes[id]; descriptions itemdocNN.mes (blocks of 0x14F: >= 0x3ED -> itemdoc03, index id - 0x3ED).

## Toolfix 2 (with weapons test 1): the apply message, pasture grass, can W capacity
- A tool use is two messages: the type-1 hit (A press) only sets the target pending (field tile state 3 sub 1,
  lbl_8008F018 then refuses anything but 0x1C, which is why the neighbours looked "already tilled"); the tool state
  0x79 impact frame (lbl_80033130, frame 30 / 60 for the can) sends type 0x1C to pl+0x1388 at 0x800332BC, which
  applies the change (e.g. 8008F350 hoe: func_8009EBB8(record, 2) and the new kind's init rebuilds the look).
- HOOK22 0x800332C0 -> pm_impact_stub -> tool_area_impact: the same 0x1C to the neighbours that accepted the hit.
  tool_area now skips everything when the main hit was refused (no swing would follow).
- Pasture grass: type-4 objects, ids 0x278..0x4B3 = 26 x 22 grid (id = 0x278 + ix*22 + iz, x 181.5+ix, z 128.5+iz);
  record via func_8001075C(*0x80349230, id), obj = ifc + *(ifc+0x10) - 0xA8; +0x70 state, +0x72 grass index ->
  game+0x14E84 + idx*8 (+4 growth, cuttable at >= 450). Same two phases (state 0 -> 1 on the hit, cut on 0x1C, +1
  fodder each). tool_area checks type / position / ripeness for each neighbour.
- Watering Can W capacity: item row +0x14 low half (0x8028DFA8) 1 -> 10.
- Still not covered: case 0x12 (hoe on target kind 0x24, state 0xAD, per-frame 0x80037F04).
