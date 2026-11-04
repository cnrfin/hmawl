# HP / EXP / level system: agreed design (user, in progress)

## HP = stamina
- The game's stamina (game+0x11B84, max +0x11B88 = 100000, min +0x11B8C) is the player's HP.
- Farm work keeps draining it (as vanilla). Enemy attacks take it away (battle21).
- At 0: the vanilla collapse animation, fade, wake inside the house with half HP.

## Recovery and food
- Fullness (game+0x11B94, max +0x11B98 = 1350000) is shown as a percentage next to an apple icon.
- Recovery while resting is fastest at 90-100 % fullness, a step slower at 80-90 %, and so on down;
  at 50 % or below there is no recovery (the cue to eat).

## Levels
- One EXP pool. EXP from farm and animal tool use (measured from the game's hidden tool pools) and,
  in a large amount, from defeating the day's wild animal (plus some gold, told in a dialogue line
  with the cash sound).
- "Level up!" pop-up replaces "Field up!" / "Animal up!", with sound 216 (instead of our sting).
- 1 point per level, chosen right away in a new menu; a new screen to view the stats. Both built
  from scratch (the game has nothing like them).
- Stats, max 20 points each:
  - **HP**: more max HP. Extra HP shows as a second layer over the green bar: blue, then purple at
    max (3 bars in all). Damage empties the top layer first.
  - **Attack** (was "Pwr"): extra weapon damage, and tool efficiency on the farm (field and animal tools).
  - **Endurance**: slows hunger (fullness drain) and reduces how much HP tool use takes.
  - **Luck**: raises the chance that digging at the dig site finds an item, and the chance of rare
    fish (for the planned goddess quest).
- Balance must carry through all chapters (levels mostly gained over the whole game).

## HUD (after the level system)
- Like the current HUD: "HP" in the game's own lettering replaces the face, the HP bar beside it,
  a thinner EXP bar with the level under it; next to the HP bar the apple and the fullness %.

## Order (step 3 HUD: hud1; no name, "EXP" under "HP", cyan EXP bar, small "Lvl N" at its end)
1. Player damage, collapse -> wake at home with half HP, food-based recovery (battle21, in progress).
2. EXP / levels, level-up pop-up and sound, stat choice and view menus, Pwr / End effects.
3. The new HUD.
4. Lck effects, gold drops.
