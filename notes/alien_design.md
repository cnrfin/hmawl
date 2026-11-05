# The alien: agreed direction (user, in discussion)

Optional night enemy, unlocked by two events; replaces the owl's slot in the wild-animal roll only once unlocked.

## Unlock
1. **Crop circle.** The cow is left outside the barn and the player sleeps in the house bed. Whatever the time, they
   wake at 3 am. No music, odd sounds. In the pasture a circle of grass is cut short with the cow in the centre; the
   camera catches a glimpse of something leaving the farm.
2. **The glow.** After event 1, leaving the house after midnight (before sleeping): a cutscene, the farmer walks out
   and looks toward the graveyard past the bridge. A red glow, a woman screams, after a few seconds the glow is gone,
   the scene ends.
3. From then on the alien can be met roaming at night, plus random red glows, hums / strange sounds and HUD static.

## The alien
- Look (user references, 6 images in the user's Archive.zip; our own design from their shared traits, no copy of any
  one): not a grey - uncannily human. A huge pale dome of a head (mushroom / bulb shape) on a thin neck, with a small,
  ordinary, tired human face set low in it (droopy eyes, a slight frown, old-man creases); pale grey-pink skin; thin,
  human-proportioned body that is slightly too long. From behind (head turned away) it reads as a big pale dome on a
  thin figure; the small human face is the reveal.
- "Just a little off" (user): longer neck and limbs, a contorted posture, a wide face. Proposed set (few strong
  wrongs, the rest subtle): neck ~1.5x, forearms / shins ~1.2x, one extra knuckle-length on the fingers; face ~1.3x too
  wide with eyes set a touch too far apart and a slightly too-long philtrum; shoulders raised and rolled forward,
  head jutting, one shoulder lower; knees slightly bent and turned in; elbows bending a little the wrong way at rest.
  Motion: no bob, overly smooth glide, then sudden stiff jerks; the head lags the body, then snaps; blinks rarely and
  slowly; breathing too slow and too deep. Many of these are bone lengths / rest poses, so they can be tuned in game.
- Head always turned away from the player. On Z-lock: the head snaps round, black eyes glow red, it screams, the
  farmer is frozen in fear for about a second, then the fight starts.

- Body (user): built on our base human (blank body, tools/goddess/data/blank_v3 / small-bust variant, Celia's
  skeleton) so it matches the villagers; the off-ness is bone lengths, joint angles and head scale on that base.
  Candidates (tools/alien/body_candidates.py): A The Listener (neck 1.9x pushed forward, hunched, arms a little long,
  knees bent in), B The Tall One (taller, neck 2.2x, long limbs, stiff, head tilted), C The Contorted (bent and
  twisted, shoulder dropped, head cocked, one arm longer), D The Wide (head 1.4x wide and flatter, long neck, narrow
  sloping shoulders, elbows bent the wrong way).
  v2 (user: too feminine, too like the villagers), shared by all four: straight torso with no waist or hips, flat
  chest, gaunt arms and legs (0.72x thick), no ears, the skull swelling up and back into a dome above a normal-sized
  face, hands 1.5x long, pale cool grey skin.
  Chosen: B (user), with hypermobile forelimbs - elbows bent, forearms pointing up (forearms 3x long) - and a thinner
  neck (0.6x). Forelimb options (SET=fore): B1 mantis (folded up in front, hands limp), B2 reversed (elbows bent
  backwards, forearms up behind), B3 sideways (elbows bend outward, forearms up beside the head), B4 raised (upper
  arms level, forearms straight up, wrists bent over).

## After the first defeat: the well
- A red glow appears in the town well and beckons the player down. Below: a small new map (our own).
- Reward: a key that opens the unused shed on the player's farm (never used in vanilla).
- In the shed: the H.M Murasama (item 0x4EB). The weapons test build (toolfix.c -DWEAPONS_ALL) hands it out at
  the start; in the real build it should only come from the shed.

## Open questions
- Look and model (our own design).
- Graveyard spot (the area past the bridge) and which night hours.
- What the cow gets out of it, and whether the events repeat.
- Reward for a defeat (besides the well).
- The well map: layout, what is down there (a guardian? just the key?), how the player gets back up.
