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
