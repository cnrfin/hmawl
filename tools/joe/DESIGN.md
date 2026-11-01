# Joe: visit design (from the user, not built yet)

## Visit days (decided earlier, see tools/joecoin/README.md)
- 2 days a season, never on Van's days (3rd, 7th) or the postman's (8th): early one of {1,2,4,5}, late one of
  {6,9,10}, picked per season by hash(seed, year*4+season). No visits in winter (crypto winter); the fall visit
  warns he won't be back until spring.
- Comes in any weather (default, not discussed).

## $JOE at the dig site (decided earlier)
- The old "Coin" item becomes the stackable $JOE coin, dug up at the dig site, rarer than other finds.

## Route (visit days)
- 10:00 enters the valley from the east road, walks round Celia's farm and north to the dig site.
- 11:00 at the dig site; waits a little.
- Crosses the new dig-site bridge (paths test 1, waypoints 468/469), walks south to the bench by the bridge.
- ~12:00 at the bench (bench spot 2, waypoint 285): sit-down animation, then the sitting loop.
- 18:00 stands up, leaves east along the south road.

## Trading and talk
- Trades $JOE only while sitting at the bench; while walking he only talks.
- Lines (draft):
  - Intro: "Hey, I'm Joe. Ever heard of the Ethereum blockchain? You can find some crazy stuff on there"
  - Walking: "Come meet me by the bench by the bridge if you wanna trade some memecoins"
  - At the dig site: "Y'know, I've heard people mining $JOE coin around here, that's why I came to check it out"
  - Fall: talks about crypto winter.

## Friendship
- Joe accepts only $JOE coin as a gift; one gift per visit.
- Full friendship after 10 $JOE gifts.
- Full friendship doubles the rate of finding $JOE at the dig site.

## Animations (approved previews)
- Model and skeleton at 90%; cigarette on its own bone, hidden in the head outside the sit animations.
- Walk: Van's walk retimed 34 -> 28 frames (1.2x); ground speed ~1.17x Van's.
- Sit down 2.0 s (faces the bench, twists round, sits), sitting loop 10 s, stand up 1.3 s (no twist).
