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

## Test 1 (pm.bin, HOOK13): lock-on and strafe, no marker yet
Found for it (static reading plus earlier RAM dumps):
- Player object (r30 in his update func_800312xx): position +0x4C, facing +0x58 (unit vector), map +0x64,
  state +0x1364 (state table 0x802A3AA8, 0x3C per state, filled at runtime: state 1 = free in the field,
  its update 0x80042CA8, A/Z routine 0x80042DFC..0x80043120). Target speed +0x136C, current speed +0x1370,
  stick direction (stick space) +0x1374.
- func_8003083C: stick (pad +0x18/+0x19) -> speed class, facing = stick angle + camera yaw (camera
  *(0x8034922C) +0x1C). The position step (0x80030AEC) uses the stick vector and the camera yaw again, not
  the facing. So rewriting the facing after the update leaves movement to the stick: a strafe.
- Villagers keep their live position / direction / map in the event slots (game +0x29C78 / +0x29F84 /
  +0x2A290, 12 / 12 / 4 bytes x character id), same as slot 0 = the player (copied at 0x800313D0).
Code: zt.c. zt_frame (pad hook) takes Z (press and hold) whenever the player is free in the field. Z picks
the nearest villager (ids 1..0x26, same map) or Joe within 10 units and 60 degrees of the facing; Z again
switches (90 degrees, ahead favoured) or lets go; out past 13.5 units = let go. HOOK13 (0x800313C4, original
lwz r3,-0x57F4(r13) replayed in pm_zt_stub at pm.bin +0x1F4) calls zt_post(player): facing -> target.
Sounds: 3 on lock, 4 on release (4 is a guess).

## Test 1 results -> test 2
Test 1 in game: locks on, turns him toward the villager while standing and walking, lets go when far: all
right. Problems: a loud drone (release sound 4 is a looping sound: removed), jitter near several villagers
(cause not found yet; the facing now turns 35 % of the way per frame instead of snapping), and the camera
did not follow.
Camera object *(0x8034922C) (from two valley dumps): +0x00 = the point it follows (player position), +0x1C =
yaw, +0x30 = distance 12, +0x80 = the eye. It looks along (-sin yaw, -cos yaw): checked on both dumps (eye to
player direction). Test 2 eases +0x1C 12 % a frame toward atan2(-dx, -dz) (dx, dz = player to target), so the
camera swings behind him looking past him at the target, and stick-up walks toward the target (movement uses
the camera yaw). pm.bin 7a3830ac.

## Test 2 results -> test 3
Test 2: much better, camera turns, but locking is hit and miss and there is no marker.
- Hit and miss: the event slots also hold parked positions for characters that are not out (e.g. slots
  35/36 at fixed points on map 1). Targets now come from the villager actors: actor manager
  (*(0x8034923C), list via +4, end at mgr+0x14, node +0xC = component, component +0x14 = class id) class
  0xB000, one per character whether out or not; component +0x4C = character id, +0x2C flags (0x2000 while the
  character is out on this map), position at component -0x24. Checked on two valley dumps (29 matches).
- Marker: 4 HUD quads appended to opguide.agc element 7 (now 33 quads; build_skill_hud.py RET_Q, with
  `--onto` to put the new HUD files into the $JOE coin commonall a970336f; only opguide.tpl / opguide.agc
  differ). Projection from the camera's view matrix (+0x50, 3x4), aspect +0x34, FOV +0x38 = 30.2 degrees:
  the dump's player feet project 110 px below the centre, as in the user's screenshot. OoT-style close-in
  (60 -> 20 px) then a slow breathe, light blue (150,150,255), fade out on release.
- data/commonall.arc.clz 982dfad1, pm.bin 970bd3b5 (code ends 0x80367770; 10 KB left below the arena).

## Test 3 results -> test 4
Test 3: no reticle seen; with one villager smooth, with several it breaks (switching only works from some
spots, sometimes Z stops working while walking).
- Choice is now OoT-like and independent of the player's facing (which the stick and the lock keep
  changing): any present villager / Joe within 10 whose chest projects on screen (ndc within 0.95);
  score = distance^2 x (1 + |ndc x|). Switching uses the same rule without the current target.
- "Free" now ignores EVMGR +0x58C (suspected: set by villagers' own goings-on when several are near) and
  only needs +0x680 == -1 (no script event), CONTROL 1, no fade; a not-free spell must last 8+ frames to
  drop the lock.
- Debug block zt_dbg at 0x80367944 (magic 'ZTDB'): target, alpha, free, map, control, +0x58C, fade, Z
  presses, picks, candidates at the last pick, last pick, agc_ok (3 = HUD file found), reticle cx/cy, frames,
  not-free frames, depth w, ndc x/y. pm.bin 88366ec6.

## Test 5: lock sounds
Sound 434 (lock on, also on switching) and 435 (lock off: Z with nothing to switch to, target gone, or
walked past 13.5) in GAME_ALL (tools/sound README). No sound when an event or menu ends the lock.
pm.bin 44853104; zt_dbg moved to 0x8036799C.

## Test 4 dumps (Z1-Z3) -> test 6
Dumps: locked on villagers 21 / 6, alpha 255, agc_ok 3, 1 candidate per pick, no not-free frames during the
session (nfree stayed 1058, all from before). Camera yaw had counted on to -6.95: now wrapped.
Camera +0x10 = 1.5 (aim height over the player, also added to the ground height under the eye in
func_800859xx, so it cancels in the pitch there), +0x18 = -0.148 (not yet confirmed: copied with the others in
func_80085E40's save; test 6 doubles it while locked to see if it is the tilt), +0x30 = 12 (distance),
+0x38 = 30.2 FOV, +0x3C 0.3. Eye in the dump: 0.92 above the aim point at 12 (4.4 degrees).
Test 6: while locked, distance eases to 9.5 and +0x18 to 2x its value (10 % a frame); both ease back on
release and then hand back the game's exact values. pm.bin 46246320, zt_dbg 0x80367B58.

## Test 6 results -> test 7
Test 6: locking got worse (sometimes 3 presses), both sounds heard on a lock. Reading: the lock was made,
then let go a frame later (lock-off sound): the actor flag 0x2000 flickers, more with the camera moving
(zoom), so it looks like a drawn-this-frame flag rather than "out here". Now a character counts as out for 30
frames after the flag was last seen, and the target's position comes from its event slot (live every frame).
pm.bin 5e1ca972, zt_dbg 0x80367B3C.

## Test 7 results -> test 8
- Still both sounds sometimes. Cause: zt_frame cleared Z from the pad copy's held word every frame, and the
  pad update's "pressed" compares with the previous held, so Z held 2+ frames came back as a new press
  (second press = switch or let go). Now the press is our own edge on the held bit (previous frame kept
  in zt.c); press and held Z are still cleared for the game.
- Tilt: +0x18 does nothing visible. From five dumps the eye sits at the ground height behind the player
  (pitch varies 0.04-0.23 with the terrain) and +0x10 (1.5) is added to both eye and aim: test 8 eases +0x10
  to 1.0 while locked (camera nearer the ground), with the zoom to 9.5.
- pm.bin f91f513d, zt_dbg 0x80367B60.

## Test 8 results -> test 9
Test 8 worse. Likely: the pad hook runs more than once per game frame, so the "Z down last time" kept in
zt.c saw the copy's held Z we had just cleared on the first call, and a held Z turned into presses over and
over. Test 9 reads Z from the pad master record (0x80341464, pad 0 held: nothing of ours writes it).
Event log zt_log at 0x80367D28 (magic 'ZLOG', n, calls, 32 x {clock, call, kind, a, b}): 1 Z press (master
held, copy pressed bit), 2 lock (id, candidates), 3 switch, 4 let go by Z, 5 out of range, 6 target gone,
7 not free, 8 Z with nothing to lock. zt_dbg 0x80367F34. pm.bin 44129705.

## Test 9 dump -> test 10
Test 9 worked. Its log: one press = one event, lock/switch/let-go as expected, 98 calls in 98 frames (the hook
runs once a frame after all; reading the master record was still the fix that stuck).
Upward tilt: the camera base (func_8017B834 / func_8017B89C) builds the eye (+0x80), a target from the angles
(+0x18 + +0x8C pitch, +0x1C + +0x90 yaw) and C_MTXLookAt (func_801B8454) into +0x50. The angles orbit the eye
around the player (still looking at him), which is why changing +0x18 showed no tilt. HOOK14 (0x8017B888) /
HOOK15 (0x8017B8F4), the instruction after each look-at, call zt_tilt(camera): for the field camera,
V' = Rx(-t) V with t eased to 0.07 rad while locked. pm_tilt_stub +0x21C, pm_tilt2_stub +0x22C.
pm.bin 685a508e; zt_log 0x80367E24, zt_dbg 0x80368030.

## Test 11: softer lock sounds
434/435 rebuilt on RECORD07 p4 (pizzicato), D3/G3, low-passed at 1.2 kHz, and quiet: add_sfx.py peak-normalises
to --gain, so the first versions (0.89) played louder than the wood hit. Now gains 0.196 / 0.146: loudest 100 ms
at -25 / -26 dBFS vs the wood hit's -17. Bank 5b73a9b6 / 9ed747af. (Velocity changes nothing in these
presets: no velocity-to-filter in the bank.)

## Test 12: strafe / walk-back clips, facing while moving
- Player animation set 0 (boy_0.anm.arc, list 0x8029BECC, 200 motions). The free-roam update picks idle /
  walk / run with func_8007C100(slot, variant 0/3/2, group 0x35, held item +0x144/+0x148, 4, rate):
  func_800288E8 turns that into a motion ENTRY pointer, func_8007C894(slot, entry, rate) plays it
  (func_8017D660 keeps it while the pointer is the same). So no list change: zt_motion (the three bl
  sites -> pm_mot_stub +0x23C, 'blhook') copies the entry the game would play, points word 0's anim (low
  10 bits) at clip 126/127/128, and plays that.
- Facing: func_8003083C sets the facing from the stick (camera yaw + stick angle) and the model uses it
  later in the same frame, so test 1-11's after-update facing only showed when standing. HOOK16 at
  0x80030A3C (pm_face_stub +0x240) records that as the move direction and puts our facing back.
  Movement itself comes from the stick vector, not the facing.
- Direction: move . facing > cos 45 = forward (the game's walk / run), < -cos 45 = back, else the side
  (cross < 0 = his left, +x).
- Clips (anim/make_clips.py from strafe.py, encoded with joe_anm.rebuild on clip 1's header, read back
  and checked): 126 strafe left, 127 strafe right, 128 walk back, 21 frames like his walk.
  anim/add_player_clips.py appends them to boy_0.anm.arc in a mainchapterN.arc.clz (+52 KB unpacked;
  idempotent; mainchapter1 checked).
- pm.bin 346b1401 (code ends 0x80368588).

## Test 13: lock sounds louder
Gains 0.40 / 0.30 (test 11: 0.196 / 0.146 too quiet, test 5: 0.89 too loud): loudest 100 ms -18.8 / -19.8 dBFS (wood hit -17.2). Bank b8d163da / 18982d7e.
Reticle concepts (reticle/mockups.py): A petals, B brackets, C spinner, D arrow + ring; flat yellow (255,206,46), no outline.

## Test 14: reticle B (brackets)
Chosen from the four mock-ups: four flat yellow (255,206,46) corner brackets, 8 HUD quads (RET_Q 8, element 7
now 37 quads) drawn from a 6x6 white patch added to the HUD atlas (UV_WHITE, inner part) and tinted. Box
half-size 30 x 34.5 px at depth 12, scaled by 12 / depth (0.6-1.6); snaps in from 2x over 9 frames
(ease-out-back, overshoot 2), then pulses +-5 % every 42 frames. commonall 5d7ab970 (on the $JOE coin build),
pm.bin c0e945fc.

## Test 15: field tile cursor in the bracket style
Found from the user's dump on a field plot (tile centre 175.5, 114.5 one tile ahead): func_80091F58(pos, view
mtx), called once from 0x800922F0, draws the highlighted tile as a GX line strip (GXBegin = func_801CE2CC,
0xB0, 5 vertices) with indexed u8 corners 0x8024FBE0 (unit square) and colour 0x8024FC00 (F1F50F, alpha F3),
translated to (x - 0.5, y + 0.05, z - 0.5). HOOK18 (its first instruction) -> pm_tile_stub +0x24C ->
zt_tile_cursor (tile.c): the same GX set-up with direct f32 / RGBA8 vertices, four flat yellow corner
brackets as ground quads (both windings), half-size 0.46, arm 0.26, bar 0.07; snap in from 1.6x over 7
frames on a new tile, pulse 4 %. pm.bin deae3820.

## Test 16: tile cursor settle softened
No overshoot: from 1.15x to 1x over 6 frames (ease-out cubic), then the 4 % pulse. pm.bin 4e0cc987.
