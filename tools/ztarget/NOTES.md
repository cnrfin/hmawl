# Z targeting: research notes

Goal (FEATURES.md, Ideas): Z locks on to a nearby villager or animal. The player keeps facing the target while
moving, and the camera follows. The OoT decompilation is used as a behaviour reference only.

## Found so far (static reading of main.dol; not yet checked in game)

**Z today (first-person look)**
- The player's button routine is func_80042FB4 (r30 = player object). Its Z test is at 0x80043058:
  `rlwinm. r0, r4, 0, 27, 27` on the pad's newly-pressed word (0x8034157C, Z = 0x10).
- If g_system +0x68 == 1 (field) and player +0x64 == 1, it calls func_80031D7C(player, 2): the player state
  setter, state 2 = first-person look.
- The look state's update (around 0x80033F10) leaves on A, B or Z (`andi. 0x310` on the pressed word).
- That code works on the camera object at *(0x8034922C). The calls are func_80085EB0, func_80085884 and
  func_80085998.
- **Plan:** keep the Z test, but send it to our lock-on instead of state 2. Or, with less patching, catch Z
  in pm.c's pad hook and clear the bit, as the bench and Joe already do with A.

**Camera object** (*(0x8034922C)), confidence medium
- +0x00/+0x04 and +0x13C/+0x140 are written together in func_80085EB0. Probably the eye and look-at copies.
- +0x1C and +0x48/+0x4C are angles or distances used by the look code (+0x48 - +0x1C feeds sin/cos via
  func_801B8048).
- +0x154/+0x15C and +0x170 are a mode flag and values for the look state.
- func_80085884 / func_80085998: the camera per-frame from the player position (func_8017BBA4 = actor
  position). func_80085998 reads lbl_80349204 (probably the field camera settings).
- **Next:** dumps 1 and 2 confirm which fields are the eye, the look-at and the yaw. A follow camera then
  overrides them each frame after the game's own update.

**Player**
- Player object: field A handler hook (pm_player). Event slot 0 = game +0x29C78 (position), +0x29F84 (direction).
- State setter func_80031D7C(player, state). Facing and speed fields still to find (dumps 3 and 4).

## Dumps asked for
1. Standing still (A), then after rotating the camera with the C-stick (B): field camera fields.
2. Standing still (A), then holding Z in first person (B): the camera mode / state values.
3. Facing one way (A), then turned on the spot (B): the player's facing.
4. Standing (A), then mid-walk with the stick held (B): speed and walk state.
5. Standing next to a named villager: the villager actor list and positions.

## OoT reference (zeldaret/oot, main): behaviour only, not code to copy
How sure each item is: **[read]** = read in the source text; **[lead]** = from a summary of a part not read
line by line, so check it before relying on it.

**Target selection** (z_actor.c: Attention_FindActor, Attention_Update, Attention_Draw, sAttentionRanges)
- [lead] Search order by category: boss, enemy, ..., NPC, item, chest, ..., door. A candidate must have
  attention enabled, be in range, be roughly on screen (leeway 20 px sideways, 160 px vertically) and be in
  line of sight.
- [lead] Not locked: only actors within ~60 degrees of the player's facing count, scored by squared
  distance. Locked (looking for the next target): within 90 degrees, with distance x 0.6 straight ahead
  rising to x 1.0 at 90 degrees, so targets in front are preferred.
- [lead] Ranges by type (range / release): 70/140, 170/255, 280, 350/525 (the default, type 3), 700/1050,
  1000/1500, ... Release happens at roughly sqrt(range x leash), about 428 units for type 3.
  OoT units: Link is about 50 tall, so convert by scale (AWL's player is about 1.6 units tall: OoT 350 ~
  AWL 11).
- [read] Holding back on the stick while locked stops it cycling to another target. The second-Z-press
  cycling itself is in player code, not yet read.

**Reticle and arrow** [read]
- Colours: enemy yellow (255,255,0); NPC light blue (150,150,255); anything else green (0,255,0).
- The reticle is 4 triangles rotated 90 degrees apart. It starts at radius 500, closes toward 80 with
  step clamp((500 - r) x 3, 30, 100), then spins (3 steps/frame of 128 per turn) at radius 120. Faded
  motion-blur copies show while it closes in. On release it fades (alpha -120/frame) and opens up
  (+80/frame).
- The arrow over the target sits 17 units above its focus point and spins about Y by 3000/65536 of a turn
  per frame.
- Sounds: a lock-on sound for enemies, a gentler one for people.
- **For AWL:** the reticle can be a HUD sprite at the target's projected screen position (skill.c already
  draws HUD art); the arrow could be a small spinning model (as the cmd_91 item model).

**Player while locked** (z_player.c, z_player_lib.c)
- [read] Locking on to an NPC = "friendly" focus, and the camera goes into its Z-target-friendly mode.
- [lead] Stick: world direction = camera yaw + stick angle; a dead zone below 55 (of about 60); the
  direction relative to the facing is sorted into 4 (forward / back / left / right), which picks walk,
  backwalk, sidestep left or sidestep right. Animations: side_walk, side_walkL/R, back_walk.
- [lead] Parallel Z (no target): keep the current facing, camera snaps behind.
- Not yet read: speeds while locked, and the code that keeps him turned toward the target.

**Camera** (z_camera.c)
- [read] Smoothing is "step = difference x rate", snapping when close: offsets 0.05 a frame, look-at step
  0.12 to 1.1 x, distance 1/20 and pitch 1/16 of the difference per frame. Pitch limits about +80 /
  -30 to -50 degrees.
- [read] Wall check: the eye is kept 8 units off walls and 1 unit above the floor.
- [lead] KeepOn1 (people): look-at placed between player and target, pitch kept within about +-70 degrees,
  a short swing in (~4 frames + extra). Battle1 (enemies): the closer the target, the more the yaw
  swings to keep both in frame; FOV narrows slightly. Parallel1 (no target): turns behind the player over
  4 frames.
- **For AWL:** a simple version of KeepOn1. The eye sits behind the player on the line from the target
  through the player, raised and a little to the side, looking at a point between the two, all eased
  with the rates above.
