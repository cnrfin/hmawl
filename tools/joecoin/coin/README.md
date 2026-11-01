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
