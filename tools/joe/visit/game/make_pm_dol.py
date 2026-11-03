#!/usr/bin/env python3
"""Add the Postman NPC to a Harvest Moon: A Wonderful Life (US) disc image.

usage: python3 make_pm_dol.py IN.iso OUT.iso

main.dol gets one new text section (slot 2) at 0x8035EFA0 holding the Postman code (pm.bin), the
heap arena start moves from 0x8035EFA0 (or the stack top 0x8035CFA0 on the debug path) to
0x80366000 so nothing else uses that memory, the end of the pad update (0x80213CFC) branches
into the code once per frame, and the start of g_system's update (0x8017755C) branches to a check
that unloads the Postman before a scene change (doors). Every patched instruction is compared with the original first; on
any mismatch nothing is written. The larger main.dol is written back in place when the space
after it is free, otherwise into the lowest unreferenced disc area that fits (boot.bin 0x420 is
updated; the old copy is left as it was). Needs the pm/pm_0.arc + pm/pm_0.anm.arc files and the
Common.arc with event 406 that are already on the model7 disc. Turn off every Postman Gecko code."""
import os, struct, sys, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
CODE_ADDR = 0x8035EFA0
ARENA_LO = 0x8037C000                                 # pm.bin room: 0x8035EFA0-0x8037C000 (118 KB; was 0x80377000, 20 KB more for code)
AXE_STUB_OFF = 0x54                                    # pm_axe_stub in pm.bin (after pm_hook2)
HOOK = 0x80213CFC
HOOK2 = 0x8017755C
HOOK2_OFF = 0x14                                      # pm_hook2 in pm.bin (after pm_hook's 5 instructions)
HOOK3 = 0x80043120
HOOK3_OFF = 0x58                                      # pm_player_stub in pm.bin (after pm_axe_stub)
HOOK4 = 0x8004368C
HOOK4_OFF = 0x68                                      # pm_label_stub in pm.bin (after pm_player_stub)
HOOK5 = 0x8018B224
HOOK5_OFF = 0x98                                      # pm_sfx_stub in pm.bin (after pm_label_stub)
HOOK6 = 0x80033170
HOOK7 = 0x8011886C
HOOK7_OFF = 0x130                                     # pm_nosell_stub in pm.bin (after pm_exit_stub)
HOOK6_OFF = 0xF4                                      # pm_exit_stub in pm.bin (after pm_sfx_stub)
HOOK8 = 0x8008E298
HOOK8_OFF = 0x14C                                     # pm_tv_stub in pm.bin (after pm_nosell_stub)
HOOK9 = 0x80117B10
HOOK9_OFF = 0x150                                     # pm_talk_stub in pm.bin (after pm_tv_stub)
HOOK10 = 0x80148A4C
HOOK10_OFF = 0x1A0                                    # pm_want_stub in pm.bin (after pm_talk_stub)
HOOK11 = 0x80060EF8
HOOK11_OFF = 0x1B8                                    # pm_van_stub in pm.bin (after pm_want_stub)
HOOK12 = 0x80113894                                   # func_80113864's bl func_801020E4 (script messages)
HOOK12_OFF = 0x1E4                                    # pm_msg_stub in pm.bin (after pm_van_stub)
HOOK13 = 0x800313C4                                   # player update, after the state handler (Z targeting)
HOOK13_OFF = 0x1F4                                    # pm_zt_stub in pm.bin (after pm_msg_stub)
HOOK14 = 0x8017B888                                   # camera look-at (func_8017B834), after C_MTXLookAt: Z-target tilt
HOOK14_OFF = 0x21C                                    # pm_tilt_stub in pm.bin (after pm_zt_stub)
HOOK15 = 0x8017B8F4                                   # the same in func_8017B89C
HOOK15_OFF = 0x22C                                    # pm_tilt2_stub
MOT_SITES = (0x80042D44, 0x80042D98, 0x80042DD0)      # free-roam motion picks (bl func_8007C100) -> pm_mot_stub
MOT_OFF = 0x23C                                       # pm_mot_stub (b zt_motion)
HOOK16 = 0x80030A3C                                   # func_8003083C after the stick sets the facing
HOOK16_OFF = 0x240                                    # pm_face_stub
HOOK18 = 0x80091F58                                   # field tile cursor draw (func_80091F58 entry)
HOOK18_OFF = 0x24C                                    # pm_tile_stub (b zt_tile_cursor)
HOOK19 = 0x8019E5C4                                   # pose build (func_8019E438): bl func_801A01F8, per-bone anim eval
HOOK19_OFF = 0x250                                    # pm_bone_stub (mr r6,r24; b zt_bone)
HOOK20 = 0x8004390C                                   # A-action case 0xF, after the tool-hit send (area tools)
HOOK20_OFF = 0x258                                    # pm_area_stub (toolfix.c)
HOOK21 = 0x800136D8                                   # new game: bl func_8004FDA0 (Milker) -> + the Stick
HOOK21_OFF = 0x27C                                    # pm_newgame_stub
HOOK22 = 0x800332C0                                   # tool state 0x79 impact, after the 0x1C send (area tools)
HOOK22_OFF = 0x2B0                                    # pm_impact_stub
HOOK23 = 0x801A0A88                                   # clip lookup func_801A0A88 entry -> player clips 126-131 from pm.bin
HOOK23_OFF = 0x2C4                                    # pm_arcanim_stub (b zt_arc_anim)
HOOK24 = 0x80012200                                   # menu display box lookup (func_800121C4): add r7,r5,r6
HOOK24_OFF = 0x2D0                                    # pm_box_stub (weapon icon models 196+)
HOOK25 = 0x80178E88                                   # operator new entry (stwu r1,-0x20(r1))
HOOK25_OFF = 0x2F0                                    # pm_new_stub: Joe's archives into pool A (memfix 18)
HOOK26 = 0x80179168                                   # operator delete entry (stwu r1,-0x20(r1))
HOOK26_OFF = 0x398                                    # pm_del_stub: our pool-A blocks back to pool A
HOOK27 = 0x80178A44                                   # pool allocation func_80178A44 entry (stwu r1,-0x30(r1))
HOOK27_OFF = 0x3D4                                    # pm_pool_stub: pool guard (memfix 19)
PREV = {0x8028DDE4: (0x02206E10,), 0x8028DE08: (0x02206F11,), 0x80113894: (0x4824B8F1,), 0x80060EF8: (0x482FE260,), 0x801B0EE4: (0x3C608036, 0x3C608037, 0x3C608038), 0x801B0EE8: (0x38636000, 0x3863A000, 0x38630000, 0x38637000), 0x801B0F28: (0x3C608037, 0x3C608038), 0x801B0F2C: (0x38636000, 0x3863A000, 0x38630000, 0x38637000)}   # earlier builds' words (update mode)
PATCHES = [  # (RAM address, original word, new word, why)
    (0x801B0EE4, 0x80630030, 0x3C608038, 'OSInit: arena low = 0x8037C000 (was BootInfo->arenaLo or __ArenaLo) ...'),
    (0x801B0EE8, 0x28030000, 0x3863C000, '... - 0x4000'),
    (0x801B0EEC, 0x40820010, 0x48000010, '... then OSSetArenaLo'),
    (0x801B0F28, 0x3C608036, 0x3C608038, 'OSInit debug path: arena low = 0x8037C000 (was _stack_addr) ...'),
    (0x801B0F2C, 0x3863CFA0, 0x3863C000, '... - 0x4000'),
    (HOOK, 0x80010014, None, 'pad update end -> Postman code'),
    (HOOK2, 0x9421FFF0, None, 'g_system update start -> scene-change check'),
    (HOOK3, 0x9421F5D0, None, 'field A handler start -> pm_player_stub (remember the player)'),
    (HOOK4, 0x931F0128, None, 'field A handler, chosen A action -> pm_label_stub (swing label at a log)'),
    (HOOK5, 0xA07F0014, None, 'sound start, id -> pm_sfx_stub (wood hit at a log)'),
    (HOOK6, 0x4800002C, None, 'swing end check -> pm_exit_stub (hoes/axe: 30 frames / motion speed)'),
    (0x8004D9BC, 0x380003E8, 0x380001F4, 'tool proficiency: a level every 500 points (was 1000)'),
    (0x8028E5E8, 0x1501761A, 0x1C400B1A, 'Lumber (item 0x51C, was Record13), row as Golden Wool: category 0x1C, rucksack tab 0x40, symbol model 11'),
    (0x8028E5EC, 0x0071003F, 0x022A003F, '... symbol texture 554 (0x22A)'),
    (0x8028E5F4, 0x00000000, 0x00780000, '... price 120 (ships for 600G)'),
    (0x8028E5FC, 0x0A002710, 0x01002710, '... menu byte 1 (as wool)'),
    (0x8028E604, 0x00000001, 0x00000019, '... flags as wool'),
    (0x8028E608, 0x00124924, 0x00092492, '... as wool'),
    (0x8028E8E4, 0x0E00F59B, 0x0E00F200, 'symbol model 11 display box (menus): Lumber, x +-0.22, y 0..0.25, z +-0.125, r 0.28'),
    (0x8028E8E8, 0x0000F1B9, 0x0000F800, '...'),
    (0x8028E8EC, 0x09EF0600, 0x0E001000, '...'),
    (0x8028E8F0, 0x0DFF11AB, 0x08001200, '...'),
    (HOOK25, 0x9421FFE0, None, 'operator new -> pm_new_stub: Joe\'s model / animations (>= 64 KB) into pool A while he loads'),
    (HOOK26, 0x9421FFE0, None, 'operator delete -> pm_del_stub: frees of those pool-A blocks go to pool A'),
    (HOOK27, 0x9421FFD0, None, 'pool allocation (func_80178A44) -> pm_pool_stub: pool guard, an A/B overlap shows as an invalid read from 0x0BAD00A0 / 0x0BAD00B0'),
    (HOOK7, 0x80610020, None, 'villager item pick (func_8011811C end) -> pm_nosell_stub: never the Cursed Axe'),
    (HOOK8, 0x9421FFE0, None, 'TV channel 3 caption (func_8008E298) -> pm_tv_stub: $JOE Coin Daily'),
    (HOOK9, 0x9421FFC0, None, 'villager talk line (func_80117B10) -> pm_talk_stub: villagers hate the $JOE coin'),
    (HOOK10, 0x9421FFD0, None, 'villager liked/wanted-item lists (func_80148A4C) -> pm_want_stub: never the $JOE coin'),
    (HOOK12, 0x4BFEE851, 0x4BFEE851, 'script message window: original bl func_801020E4 kept (test 11 hook removed: mode 1 = sign-post box)'),
    (HOOK11, 0x9421FEC0, 0x9421FEC0, 'villager daily plan: original code kept (bench-sit probe hook removed)'),
    (HOOK13, 0x806DA80C, None, 'player update after the state handler -> pm_zt_stub: face the Z-target'),
    (HOOK14, 0x80010034, None, 'camera look-at (func_8017B834) -> pm_tilt_stub: Z-target tilt up'),
    (HOOK15, 0x80010034, None, 'camera look-at (func_8017B89C) -> pm_tilt2_stub: Z-target tilt up'),
    (0x80042D44, 0x480393BD, 'blhook', 'free-roam idle motion pick -> pm_mot_stub (Z-target strafe / walk-back clips)'),
    (0x80042D98, 0x48039369, 'blhook', 'free-roam walk motion pick -> pm_mot_stub'),
    (0x80042DD0, 0x48039331, 'blhook', 'free-roam run motion pick -> pm_mot_stub'),
    # weapons phase 1 (tools/weapons): the duplicate ids 4E3 / 4E4 / 4EA / 4EB become Stick / Wooden Sword /
    # Farmer's Sword / H.M Murasama. The chapter-start "alternate look" swap of Hoe / Light Hoe / Sickle /
    # Light Sickle into them is switched off, they map to themselves, and they are sickle-type tools.
    (HOOK21, 0x4803C6C9, 'blhook', 'new game: Milker + Stick (0x4E3) into the item pool -> pm_newgame_stub'),
    (0x80050F74, 0x38A004EA, 0x38A004E6, 'chapter start, item pool swap Sickle -> 4EA: keep 4E6'),
    (0x80050FF8, 0x38A004EB, 0x38A004E7, 'chapter start, item pool swap Light Sickle -> 4EB: keep 4E7'),
    (0x8005107C, 0x38A004E3, 0x38A004DF, 'chapter start, item pool swap Hoe -> 4E3: keep 4DF'),
    (0x80051100, 0x38A004E4, 0x38A004E0, 'chapter start, item pool swap Light Hoe -> 4E4: keep 4E0'),
    (0x80013D68, 0x380004EA, 0x380004E6, 'chapter start, held Sickle -> 4EA: keep 4E6'),
    (0x80013D74, 0x380004EB, 0x380004E7, 'chapter start, held Light Sickle -> 4EB: keep 4E7'),
    (0x80013D80, 0x380004E3, 0x380004DF, 'chapter start, held Hoe -> 4E3: keep 4DF'),
    (0x80013D8C, 0x380004E4, 0x380004E0, 'chapter start, held Light Hoe -> 4E4: keep 4E0'),
    (0x8024EE0C, 0x000004EA, 0x000004E6, 'shed alt id slot 4 (Sickle): 4E6'),
    (0x8024EE14, 0x000004EB, 0x000004E7, 'shed alt id slot 6 (Light Sickle): 4E7'),
    (0x8024EE1C, 0x000004E3, 0x000004DF, 'shed alt id slot 8 (Hoe): 4DF'),
    (0x8024EE20, 0x000004E4, 0x000004E0, 'shed alt id slot 9 (Light Hoe): 4E0'),
    (0x80298068, 0x80012540, 0x80012564, 'func_800124FC: 4E3 maps to itself (was Hoe)'),
    (0x8029806C, 0x80012548, 0x80012564, 'func_800124FC: 4E4 maps to itself (was Light Hoe)'),
    (0x80298084, 0x80012530, 0x80012564, 'func_800124FC: 4EA maps to itself (was Sickle)'),
    (0x80298088, 0x80012538, 0x80012564, 'func_800124FC: 4EB maps to itself (was Light Sickle)'),
    (0x8028DDE4, 0x01206E10, 0x0220C41B, 'item 4E3 Stick: category 2 (sickle-type), models symbol 196 / real 27 (weapons phase 2)'),
    (0x8028DE00, 0x00006001, 0x0000A001, 'item 4E3 Stick: sickle flags'),
    (0x8028DE08, 0x01206F11, 0x0220C51C, 'item 4E4 Wooden Sword: category 2, models symbol 197 / real 28'),
    (0x8028DEE0, 0x02206108, 0x0220C61D, "item 4EA Farmer's Sword: models symbol 198 / real 29"),
    (0x8028DF04, 0x02204609, 0x0220C71E, 'item 4EB H.M Murasama: models symbol 199 / real 30'),
    (0x8028DE24, 0x00006001, 0x0000A001, 'item 4E4 Wooden Sword: sickle flags'),
    (0x8028DEEC, 0x003C0000, 0x012C0000, "item 4EA Farmer's Sword: price 300 (3000 G)"),
    (0x802A7874, 0x8004D210, 0x8004D26C, 'usage counter (func_8004D1EC): 4E3 sickle case'),
    (0x802A7878, 0x8004D210, 0x8004D26C, 'usage counter (func_8004D1EC): 4E4 sickle case'),
    (0x802A78F4, 0x8004D538, 0x8004D594, 'usage counter (func_8004D4F0): 4E3 off the Hoe counter'),
    (0x802A78F8, 0x8004D554, 0x8004D5B0, 'usage counter (func_8004D4F0): 4E4 off the Light Hoe counter'),
    (0x802A7978, 0x8004D714, 0x8004D734, 'usage counter read (func_8004D6E0): 4E3'),
    (0x802A797C, 0x8004D71C, 0x8004D73C, 'usage counter read (func_8004D6E0): 4E4'),
    (0x802A79FC, 0x8004D8E0, 0x8004D8E8, 'usage (func_8004D8BC): 4E3 sickle case'),
    (0x802A7A00, 0x8004D8E0, 0x8004D8E8, 'usage (func_8004D8BC): 4E4 sickle case'),
    (HOOK24, 0x7CE53214, 'blhook', 'menu display box (func_800121C4) -> pm_box_stub: boxes for the weapon icon models 196-199'),
    (HOOK23, 0x9421FFC0, None, 'clip lookup (func_801A0A88) -> pm_arcanim_stub: player clips 126-131 served from pm.bin'),
    (HOOK22, 0x3C608029, None, 'tool impact (0x1C send) -> pm_impact_stub: area tools apply to the neighbours too'),
    (0x8028DFA8, 0x0A000001, 0x0A00000A, 'Watering Can W: holds 10 (was 1)'),
    (HOOK20, 0x8001001C, None, 'tool hit (func_80043120 case 0xF) -> pm_area_stub: Strange/Weird hoe + sickle, Watering Can W area shapes'),
    (HOOK19, 0x48001C35, 'blhook', 'pose build per-bone anim eval (bl func_801A01F8) -> pm_bone_stub: Z-target swing upper-body layer'),
    (HOOK18, 0x9421FFC0, None, 'field tile cursor (func_80091F58) -> pm_tile_stub: bracket style (tile.c)'),
    (HOOK16, 0x48000020, None, 'stick facing set (func_8003083C) -> pm_face_stub: face the Z-target while moving'),
    (0x802952D4, 0x5000037B, 0x000003BB, 'day table row 33 = Van (villager 0x24): chance of an extra visit 80 -> 0, day mask 0x37B -> 0x3BB (comes on the 3rd and 7th only)'),
    (0x8028C74C, 0x00020000, 0x00000000, '$JOE coin (item 0x442): price 0 (was 2; ships for 0 G, shops/Van see no value)'),
    (0x80109D24, 0x4BF08245, 0x4BF08209, 'cmd_91 item model: symbol (rucksack) model for every item, centred spin'),
    (0x800038E8, 0x38600000, 'axe', 'baked Cursed Axe code, A path 1 (li r3,0) -> bl pm_axe_stub: log hits'),
    (0x80003900, 0x38600000, 'axe', 'baked Cursed Axe code, A path 2 (li r3,0) -> bl pm_axe_stub: log hits'),
]
be32 = lambda b, o: struct.unpack_from('>I', b, o)[0]
OPTIONAL = [  # (RAM address, word expected, new word, why): changed only when the expected word is there
    (0x80033178, 0x2C000028, 0x2C00003C, 'swing end, category 3: 60 frames again (a mod had 40)'),
    (0x800331A0, 0x2C00000A, 0x2C00001E, 'swing end, other tools: 30 frames again (a mod had 10)'),
    (0x80003628, 0x2C0C0014, 0x2C0C0041, 'HUD stamina/food bars: show after 65 still frames (was 20)'),
]


def die(msg):
    sys.exit('stopping, nothing written: ' + msg)


def fst_files(fst):
    n = be32(fst, 8); st = 12 * n; out = []
    for i in range(1, n):
        w0, off, size = struct.unpack_from('>III', fst, 12 * i)
        if not (w0 >> 24):
            out.append((off, size))
    return out


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, out = sys.argv[1:]
    if os.path.exists(out): die(f'{out} exists')
    if os.path.realpath(src) == os.path.realpath(out): die('output equals input')
    code = open(os.path.join(HERE, 'pm.bin'), 'rb').read()
    if CODE_ADDR + len(code) > ARENA_LO: die('code does not fit below the new arena start')
    entry = CODE_ADDR                                   # pm_hook is the first thing in pm.bin
    if be32(code, HOOK2_OFF) != 0x9421FFE0: die('pm.bin does not have pm_hook2 at +0x14')
    targets = {HOOK: entry, HOOK2: entry + HOOK2_OFF, HOOK3: entry + HOOK3_OFF, HOOK4: entry + HOOK4_OFF, HOOK5: entry + HOOK5_OFF, HOOK6: entry + HOOK6_OFF, HOOK7: entry + HOOK7_OFF, HOOK8: entry + HOOK8_OFF, HOOK9: entry + HOOK9_OFF, HOOK10: entry + HOOK10_OFF, HOOK11: entry + HOOK11_OFF, HOOK12: entry + HOOK12_OFF, HOOK13: entry + HOOK13_OFF, HOOK14: entry + HOOK14_OFF, HOOK15: entry + HOOK15_OFF, HOOK16: entry + HOOK16_OFF, HOOK18: entry + HOOK18_OFF, HOOK19: entry + HOOK19_OFF, HOOK20: entry + HOOK20_OFF, HOOK21: entry + HOOK21_OFF, HOOK22: entry + HOOK22_OFF, HOOK23: entry + HOOK23_OFF, HOOK24: entry + HOOK24_OFF, HOOK25: entry + HOOK25_OFF, HOOK26: entry + HOOK26_OFF, HOOK27: entry + HOOK27_OFF}
    for a_ in MOT_SITES: targets[a_] = entry + MOT_OFF
    if be32(code, HOOK3_OFF) >> 16 != 0x3D80: die('pm.bin does not have pm_player_stub at +0x58')
    if be32(code, HOOK4_OFF) != 0x9421FFF0: die('pm.bin does not have pm_label_stub at +0x68')
    if be32(code, HOOK5_OFF) != 0x9421FFD0: die('pm.bin does not have pm_sfx_stub at +0x98')
    if be32(code, HOOK6_OFF) != 0x2C000001: die('pm.bin does not have pm_exit_stub at +0xF4')
    if be32(code, HOOK7_OFF) != 0x80610020: die('pm.bin does not have pm_nosell_stub at +0x130')
    if be32(code, HOOK8_OFF) >> 26 != 18: die('pm.bin does not have pm_tv_stub at +0x14C')
    if be32(code, HOOK9_OFF) != 0x9421FFE0: die('pm.bin does not have pm_talk_stub at +0x150')
    if be32(code, HOOK10_OFF) != 0x2C050442: die('pm.bin does not have pm_want_stub at +0x1A0')
    if be32(code, HOOK11_OFF) != 0x9421FFE0: die('pm.bin does not have pm_van_stub at +0x1B8')
    if be32(code, HOOK12_OFF) != 0x2C050015: die('pm.bin does not have pm_msg_stub at +0x1E4')
    if be32(code, HOOK13_OFF) != 0x9421FFF0: die('pm.bin does not have pm_zt_stub at +0x1F4')
    if be32(code, HOOK24_OFF) != 0x28060AB8: die('pm.bin does not have pm_box_stub at +0x2D0')
    if be32(code, HOOK25_OFF) >> 16 != 0x3D80: die('pm.bin does not have pm_new_stub at +0x2F0')
    if be32(code, HOOK26_OFF) != 0x2C030000: die('pm.bin does not have pm_del_stub at +0x398')
    if be32(code, HOOK27_OFF) != 0x9421FFE0: die('pm.bin does not have pm_pool_stub at +0x3D4')
    if be32(code, HOOK23_OFF) >> 26 != 18: die('pm.bin does not have pm_arcanim_stub at +0x2C4')
    if be32(code, HOOK22_OFF) != 0x38610008: die('pm.bin does not have pm_impact_stub at +0x2B0')
    if be32(code, HOOK21_OFF) != 0x9421FFF0: die('pm.bin does not have pm_newgame_stub at +0x27C')
    if be32(code, HOOK20_OFF) != 0x7C761B78: die('pm.bin does not have pm_area_stub at +0x258')
    if be32(code, HOOK19_OFF) != 0x7F06C378: die('pm.bin does not have pm_bone_stub at +0x250')
    if be32(code, HOOK18_OFF) >> 26 != 18: die('pm.bin does not have pm_tile_stub at +0x24C')
    if be32(code, MOT_OFF) >> 26 != 18 or be32(code, HOOK16_OFF) != 0x7F23CB78: die('pm.bin does not have pm_mot_stub / pm_face_stub at +0x23C / +0x240')
    if be32(code, HOOK14_OFF) != 0x7FE3FB78 or be32(code, HOOK15_OFF) != 0x7FE3FB78: die('pm.bin does not have pm_tilt_stub / pm_tilt2_stub at +0x21C / +0x22C')
    if be32(code, AXE_STUB_OFF) >> 26 != 18: die('pm.bin does not have pm_axe_stub at +0x54')
    with open(src, 'rb') as f:
        hdr = f.read(0x440)
        if hdr[:4] != b'GYWE': die(f'not the US disc (game id {hdr[:6]!r})')
        dol_off, fst_off, fst_size = struct.unpack_from('>III', hdr, 0x420)
        f.seek(0x2440); hdr_app = f.read(0x20)
        f.seek(dol_off); dh = f.read(0x100)
        offs = list(struct.unpack_from('>18I', dh, 0)); addrs = list(struct.unpack_from('>18I', dh, 0x48))
        sizes = list(struct.unpack_from('>18I', dh, 0x90))
        dol_size = max(o + s for o, s in zip(offs, sizes) if s)
        f.seek(dol_off); dol = bytearray(f.read(dol_size))
        f.seek(fst_off); fst = f.read(fst_size)
        f.seek(0, 2); disc_size = f.tell()

    update = False
    if sizes[2] or offs[2]:
        if addrs[2] != CODE_ADDR: die('text section slot 2 is in use')
        # update mode: the disc already has an earlier Postman build. Drop its code section (the last thing
        # in main.dol) and re-apply everything; patch sites may already hold this build's words.
        if offs[2] + sizes[2] != dol_size: die('the old Postman section is not at the end of main.dol')
        update = True
        dol = dol[:offs[2]]; offs[2] = sizes[2] = addrs[2] = 0
        print('main.dol already has a Postman section: replacing it')
    for o, a, s in zip(offs, addrs, sizes):
        if s and a < ARENA_LO and CODE_ADDR < a + s:
            die(f'a section at {a:#x} overlaps the code area')

    def at(addr):
        for o, a, s in zip(offs, addrs, sizes):
            if s and a <= addr < a + s: return o + addr - a
        die(f'{addr:#x} is not in main.dol')
    for addr, want in ((0x800038E0, 0x2C1A0502), (0x800038EC, 0x48040020), (0x800038F8, 0x2C1A0502), (0x80003904, 0x48040078)):
        if be32(dol, at(addr)) != want: die(f'{addr:#010x}: the baked Cursed Axe code is not there (has {be32(dol, at(addr)):08x})')
    def final(addr, new):
        if new is None: return 0x48000000 | ((targets[addr] - addr) & 0x03FFFFFC)
        if new == 'blhook': return 0x48000001 | ((targets[addr] - addr) & 0x03FFFFFC)
        if new == 'axe': return 0x48000001 | ((entry + AXE_STUB_OFF - addr) & 0x03FFFFFC)
        return new
    for addr, old, new, why in PATCHES:
        cur = be32(dol, at(addr))
        old_hook = update and new in (None, 'blhook') and cur >> 26 == 18 and \
            CODE_ADDR <= (addr + ((cur & 0x03FFFFFC) - (0x04000000 if cur & 0x02000000 else 0))) < ARENA_LO
        if cur != old and not old_hook and not (update and (cur == final(addr, new) or cur in PREV.get(addr, ()))):
            die(f'{addr:#010x} ({why}): main.dol has {cur:08x}, expected {old:08x}')
    print('all patch sites match the original code')

    # new main.dol: original bytes + the code section
    for addr, old, new, why in PATCHES:
        new = final(addr, new)                           # b / bl into pm.bin for the hooks
        struct.pack_into('>I', dol, at(addr), new)
        print(f'  {addr:#010x}: {old:08x} -> {new:08x}  {why}')
    for addr, want, new, why in OPTIONAL:
        if be32(dol, at(addr)) == want:
            struct.pack_into('>I', dol, at(addr), new); print(f'  {addr:#010x}: {want:08x} -> {new:08x}  {why}')
        else:
            print(f'  {addr:#010x}: left as {be32(dol, at(addr)):08x} (not the expected {want:08x})  {why}')
    sec_off = (len(dol) + 0x1F) & ~0x1F
    body = code + bytes((-len(code)) % 0x20)
    dol += bytes(sec_off - len(dol)) + body
    struct.pack_into('>I', dol, 0x00 + 4 * 2, sec_off)
    struct.pack_into('>I', dol, 0x48 + 4 * 2, CODE_ADDR)
    struct.pack_into('>I', dol, 0x90 + 4 * 2, len(body))
    print(f'  text section 2: file {sec_off:#x}, RAM {CODE_ADDR:#x}, {len(body):#x} bytes')

    # where the new main.dol goes on the disc
    app_end = 0x2440 + 0x20 + be32(hdr_app, 0x14) + be32(hdr_app, 0x18)
    used = [(0, app_end), (dol_off, dol_off + dol_size), (fst_off, fst_off + fst_size)] + [(o, o + s) for o, s in fst_files(fst)]
    used.sort()
    nxt = min([s for s, e in used if s >= dol_off + dol_size] + [disc_size])
    if dol_off + len(dol) <= nxt:
        new_off = dol_off
        print(f'main.dol stays at {dol_off:#x} (free space after it up to {nxt:#x})')
    else:
        new_off = None; cur = 0
        for s, e in used + [(disc_size, disc_size)]:
            start = (max(cur, 0x10000) + 0x7FFF) & ~0x7FFF
            if start + len(dol) <= s:
                new_off = start; break
            cur = max(cur, e)
        if new_off is None: die('no free disc area for the larger main.dol')
        print(f'main.dol moves from {dol_off:#x} to {new_off:#x} (unreferenced area; old copy left in place)')

    print(f'copying {src} -> {out} ...')
    with open(src, 'rb') as f, open(out, 'xb') as o:
        while True:
            chunk = f.read(1 << 22)
            if not chunk: break
            o.write(chunk)
        o.seek(new_off); o.write(dol)
        if new_off != dol_off:
            o.seek(0x420); o.write(struct.pack('>I', new_off))
    with open(out, 'rb') as o:
        o.seek(0x420); assert be32(o.read(4), 0) == new_off
        o.seek(new_off); assert o.read(len(dol)) == bytes(dol)
    print('done; main.dol sha1', hashlib.sha1(dol).hexdigest())


if __name__ == '__main__':
    main()
