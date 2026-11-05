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
  Picked: the mantis (user: arms lower, shoulders more hunched, neck thinner -> neck 0.42x). SET=mantis: M1 forearms up
  at chest height, M2 forearms lower reaching forward, M3 very hunched with forearms low and hands dangling.
  Then (user): the neck a round tube of one radius (0.016) all along; a rounded upper back (bulge + more spine curve);
  the head upright, facing straight ahead whatever the lean.
  Picked: M3's strong hunch with T-rex arms (user): upper arms hang (set in world space, so the spine's lean does not
  swing them back), forearms point up from the elbow, wrists bent so the hands hang down. SET=trex: T1 forearms up and
  forward, T2 steeper, T3 elbows tucked back. In the blockout the base's mitten forearm / hand is replaced by a round
  forearm, a palm and three long fingers (the final mesh needs a real forearm and hand).
  Picked: T2 (user). Head: a wide hinged jaw for the scream (user) - the lower front of the head below the mouth line,
  flaring wider toward the chin, hinged under the ears; at the reveal it drops 45-65 degrees and the whole lower head
  gapes. Rig: Celia's braid nodes 8 / 9 (children of the head, unused - no hair) give a jaw bone for the pose layer
  (as the lizard gape). SET=jaw: J1 closed, J2 open 45, J3 wider jaw open 65.
  Picked: J3 with the bell (user, from the first jaw render): the whole lower head flares smoothly, widest at the
  bottom (1.6x), and the scream swings it down ~70 degrees from under the ears (jaw_bell). Option: dark mouth where
  the skin stretches.
  Then (user): a normal face when closed (no jaw, no flare); the bell flares only as the jaw opens. Mock-up: width
  1.0 closed -> 1.3 at 35 degrees -> 1.6 at 70. In game: jaw bone (Celia's braid node 8) rotation + x scale together
  (pose records have a scale flag; root-bone scale already works), lower head weighted to it, more toward the bottom
  (two-bone skin groups), node 9 for an extra flare at the rim if one bone is not enough.
- Red eyes at the scream (user): characters have eye texture frames (f0_e.tpl, ~58 frames; expressions pick an
  {eye, mouth} frame, face slot +0x124) - paint a red-eye frame and switch to it, as blinking does. The hit flash
  tints the whole model, so it can't do eyes alone. Glow: unknown how the blue flowers by the spring glow (map
  material, effect or particles: to look up); fallbacks: full-bright red eye texture (reads as lit at night) plus a
  soft red halo drawn at the projected eye positions with HUD quads (as the Z-target reticle), or a particle.
- Decided (user): eyes full-bright red even at night. Plan: the red eyes as a small separate model attached to the
  head bone the way held items are attached to the hand (logs.c item_bind / held_attach), so it has its own draw
  instance with the flat-colour switch on (+0x3D = 1, colour white: lighting off - findings 7.44, enemy2 test: white =
  the texture unlit). Hidden (+0x3C = 0) until the scream, then shown over the normal eyes. Optional halo with HUD
  quads on top.
- Face (user: original, like the references, not anime): painted procedurally (tools/alien/face.py ->
  alien_face.png / alien_face_red.png, our own art): heavy half-closed lids in shadowed sockets, bags, no eyebrows,
  low creased forehead, long thin nose, thin down-turned mouth, nose-to-mouth folds, sagging lines below the corners,
  hollow cheeks. Small and low on the dome (eyes at y 0.962 on the base head, mouth 0.906). The jaw now splits at the
  painted mouth line (jaw_bell top 0.909, hinge 0.93) so the scream opens below the nose and the eyes stay.
  Then (user): no features at all, just big black empty eyes - the fear is the mouth; aliens have bigger eyes.
  face.py (FACE=eyes): E1 round, E2 big tilted ovals, E3 huge and far apart; black, red with a glow at the scream.
  Picked: E3 (huge black eyes, far apart).

## Behaviour notes (user's reference: a scream-and-freeze enemy from another game - mechanics only; our own model,
## look and sounds, nothing taken from that game's files)
- The freeze also triggers by distance: walk up close without locking on and it turns and screams anyway.
- While the farmer is frozen it closes in and grabs; mashing buttons breaks free sooner (shorter freeze with Endurance?).
- A grab drains (HP or fullness) until the player breaks free; then it reels back, open to hits.
- Roaming: it hardly moves while watched, shuffles closer when the player looks away.
- Applied from the user's model reference (ideas only, nothing from its files): ribs, breastbone, collarbones and a
  sunken belly painted on the torso (tools/alien/alien_ribs.png, our own) with the belly pulled in and the waist
  narrowed under a slightly wider ribcage (face.py gaunt); oversized T-rex hands (longer palm, four long jointed
  fingers: forelimbs_big). Walk: a shuffle (knees bent, feet barely lifting) when we animate it. FACE=v2 renders it.
- Eyes at the scream (user): the eyes stay black with a small glowing red dot in each (about a third of the eye),
  readable at lock-on range. In game the dots are the separate full-bright model (two small discs on the head bone).
- Sockets (user): the eyes set into the head - each eye area pushed in (up to 0.055, deepest at its centre) under a
  small brow, plus a soft socket shadow painted round each eye (face.py sockets). The final mesh needs more vertices
  round the eyes for real sockets (the base head has ~10 per eye).

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
