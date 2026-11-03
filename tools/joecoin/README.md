# $JOE coin (stock-exchange feature for Joe)

`joe_market.html` is the price simulator (also published as an artifact). The formula there is the one to port.

## Locked settings (chosen by the user)
start 50 G, growth +75 %/year, volatility 60 %, daily jitter ±12 %, crypto-winter dip −50 %,
3 pumps/dumps per year, Joe's cut 0 %.

## TV report lines (channel 3)
- pump day: "We're JOE BACK!"
- dump day: "It's so Joever.."
- up > 8 %: "$JOE doing a lil something.."
- down > 8 %: "Just a dip. HODL."
- otherwise: "Crab market today."
- winter: "Crypto winter. Joe is hibernating. HODL."
- Joe's visit day: adds "Joe is in town today!"

## Game hooks found
- Channel 3 text: `func_8008E298` (main.dol) picks the program from `tv_vd0..4.mes` (message groups 0x36-0x3A)
  and copies it into the TV caption string; replace it with the $JOE report.
- Channel 3 picture: image 6 of `tv-console2.tpl` (192x144 CMPR), used for every channel-3 program.
- Old coin: item "Coin" 0x442 (`item.mes`), description `itemdoc03.mes` #55.
- Joe's days: early {1,2,4,5}, late {6,9,10} per season by hash(seed, year*4+season); none in winter.
  Van fixed to the 3rd and 7th, postman the 8th.

## TV test 1 (`game/`)
- `joetv.c`: replaces channel 3's caption builder (0x8008E298, hook `pm_tv_stub` at pm.bin +0x144 in
  `hook.s`); builds "$JOE Coin Daily" from the price formula (identical to the simulator for every day
  checked) and copies the day's screen (tv-console2.tpl images 14-20) over channel 3's pictures 1, 2, 3, 6.
  Seed fixed at 1890 for the test. Built together with the postman code (pm.c, logs.c, skill.c, spring.c).
- `make_pm_dol.py`: adds HOOK8 and moves the heap start 0x80364000 -> 0x80366000 (code is 23 KB now).
- `build_tvdata.py`: tv-console2.tpl + the 7 screens (`../screens/`, CMPR via `../cmpr.py`), image 9's
  singer animation pieces made transparent; font.tpl gets '$' (`dollar.npy`) at glyph 0x80FD (unused in
  the US text). Font: US glyph codes are 0x8000 digits, 0x800B A-Z, 0x80D8 a-z, '+' 0x80C6, '%' 0x80D7.
- Output SHA-1: tv-console2.tpl e9efc4ff, font.tpl e5c4b578 (test 2), pm.bin 16aec257.
- TV test 1 worked in game except the `$`: the US game draws text from font.tpl image 1 (Western font, 16x16 cells,
  same code order), where 0x80FD is "ä". Test 2 also draws `$` there (`dollar16.npy`).
- TV test 4: the game reads font.tpl from **preload.arc.clz** (loaded at boot), not the loose root copy, so
  the loose font edit did nothing. `build_preload.py` draws '$' into preload's own font.tpl (image 1, cell
  0x80FD; its image 0 differs from the loose copy, so the file isn't swapped) and recompresses (CLZ).
  preload.arc.clz 408,721 -> 403,276 B, SHA-1 65c38d8b. The loose font.tpl change is harmless and not needed.
- TV test 5: test 4 still showed 'ä'. The US preload font replaces unused kanji in image 0 (the 24x24 font
  the text boxes draw from) with European letters (0x80FB-0x8107, 0x8432-0x8463); 0x80FD there is 'ä'.
  `build_preload.py` now draws '$' into image 0 too. preload.arc.clz SHA-1 47f843f8. Confirmed in game: `$` shows.

## Per-save market (joeseed test 1)
The price formula is unchanged but its seed is now per save: event counter 52 (game+0x12194+4*52, saved with the
other event counters; unused by every script and by our code) gets a random value (time base x game rand) on day 1
of a new game (joetv.c joe_seed_frame, called from pm_frame). A save whose counter is 0 (made before this) keeps
seed 1890, so its price history doesn't change. Joe's visit days stay on 1890. joe_market.html previews seed 1890.
pm.bin 6454d5a3 (normal), 12b51625 (WEAPONS_ALL test).
Fix (enemy test 1c): a new file showed 37 G on day 1 and -42 % on day 2 (the seed had been re-rolled during day 1,
after the price was seen; dump 081dc2a6: seed 0x1C7114DF gives day 1 = 60, day 2 = 35). The session now keeps the
seed and restores it if counter 52 is cleared on day 1; newgame_extra (new game setup) clears both.
Enemy test 1d: the seed is mirrored in event counter 53; if 52 is lost or overwritten it is restored from 53,
and every change seen in 52/53 is logged (pm.bin symbol joe_seed_log, magic 'JSED': clock, c52, c53, act
0 seen changed / 1 mirrored / 2 restored / 3 new seed / 4 kept seed / 9 new game). The user saw 77 G then 62 G
reported as +19 % on 1c. A NO_TVPIC test build (TV picture copy off) separates the TV from the HUD crash.
