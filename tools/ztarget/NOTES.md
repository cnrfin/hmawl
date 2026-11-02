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
