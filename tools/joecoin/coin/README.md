# $JOE coin item (coin test 1)

The old "Coin" (item 0x442; item table lbl_80282DF8 row: category 0x1E, symbol model 33, texture 30,
price 2) becomes the $JOE coin. Silver/Gold Coin share model 33 with textures 259/199 and are unchanged.
- `build_coin_tex.py`: commonall.arc.clz symbol.tpl image 30 (32x64 CMPR: front 28x28 at y 0, back at
  y 28, rim strip y 56-63; model 33 maps z- face to the top square, z+ to the second) -> `coin_tex_new.png`
  (an emblem of Joe's grin; the photo coin is unreadable at 28 px). Base: skill build 41286e03 -> 39f513b8.
- Message.arc item.mes 0x442 "Coin" -> "$JOE Coin" (base f84995a0 -> 3205b29b).
- itemdoc03.mes #0x55: "Joe's memecoin, dug / up at the dig site. / Only Joe buys it. / HODL!"
  (base 8d35606e -> 4b5f1d11). `mesedit.enc` encodes ASCII ('$' = 0x80FD, needs the TV test 5 preload font).
Still to do: dig-site rarity, sell price/buyers, villager reactions.

## Coin test 2
The emblem didn't look like Joe. Test 2 gives image 30 a 128x256 texture made from the user's coin art
(`coin_tex_x4.png`, face 112 px): appended to symbol.tpl (32-aligned) with image 30's header pointed at it
(the model's UVs are 0-1, so they scale). commonall.arc.clz a970336f (3,839,604 B).
Confirmed in game (rucksack menu: icon, name with $, description, 3D coin with Joe's face).

## Coin test 3: dig-site halving
Dig table lbl_802928C8 (18 rows: item u32, group u16, weight u16, chapter mask u8, repeatable u8): the
dig scene (wlp2 lbl_00001D20, chapter from func_8000FEE8(clock), 0-5) gives each row open in the chapter
weight / sum. `joe_dig_frame` (joetv.c, called from pm_frame) rewrites the weights every frame: others x100,
the coin the weight for exactly 10 / 5 / 2.5 / 1.25 / 0.625 / 0.3125 % of dig-site finds in chapters 1-6.
pm.bin a9929cdd (23,532 B).

## Coin test 4: price 0
Item table +0xC = price: shops charge price x 10, the shipping bin pays price x 5 (func_80055454 sums
price*5*count over 0x211 items); Van's code (func_80134E38) checks price*10 == 0. make_pm_dol.py sets the
coin's price word 0x8028C74C 0x00020000 -> 0 so only Joe (TV price) pays for it. Untested: whether the bin
still takes it (for 0 G) and whether Van refuses it. pm.bin unchanged (a9929cdd).

## Coin test 5: villagers never ask to buy it
Test 4 in game: Van says "You can't sell that to me." and the shipping bin refuses it.
Villagers' show-item lines are chosen by item category (0x1E = every dig-site item, e.g. Hugh 0x85 "I'll
take a look at it, if they're old coins..."), so the coin can't get its own line by data alone. The
"villager asks to buy the held item" pick (func_8011811C end, pm_nosell_stub) now also returns "nothing"
for 0x442. hook.s grew 8 bytes: pm_tv_stub is now at pm.bin +0x14C (make_pm_dol HOOK8_OFF). pm.bin 9c... see zip.
Still to do: a hate reaction + affection drop (needs the show/gift reaction code).

## Coin test 6: villagers hate it (how villager item talk works)
- Villager talk tables: `NPC_NormalTalk_1..6.arc` (one per chapter), 36 CLZ members (one per villager,
  member = func_80118940(villager)), each 158 records x 78 bytes: 3 pages of 4 (group, line) pairs + u32,
  then 3 (group, line, flag) extras. Decompressed at talk start into lbl_802F3F44 (func_8017837C).
- func_80113FBC picks the record: for a held item, func_80012134(item, K) tests bit K-1 of item flags
  (+0x1C) >> 5; the coin's flags give K = 20 -> record 0x3E (shared by every dig-site find).
- func_80117B10(villager, record, &group, &line) picks the page (by times shown) or an extra.
- Villager records: game + 0x124C4 + 0x124 x (func_8007846C(id) - 1); affection = s16 at +0x28 (setter
  func_800782D8), gift-today byte +0x25. Hugh's coin gift: 50 -> 131.
- Test 6 hooks func_80117B10 (pm_talk_stub, pm.bin +0x150): record 0x3E with the coin held -> the
  villager's own dislike line (table in joetv.c by message group, else other.mes 0x43 / 0x42), gift flag
  0x80349348 cleared, affection -10 once a day per villager. `talktab.py` reads the tables.
