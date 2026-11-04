# Per-frame hook: 0x80213CFC (end of the pad update wrapper, was lwz r0,0x14(r1)) branches here.
    .section .text.hook, "ax"
    .globl pm_hook
pm_hook:
    stwu  r1, -0x10(r1)
    bl    pm_frame
    addi  r1, r1, 0x10
    lwz   r0, 0x14(r1)              # original instruction
    b     pad_hook_return

# Scene hook: 0x8017755C (start of g_system's update, was stwu r1,-0x10(r1)) branches here.
    .globl pm_hook2
pm_hook2:
    stwu  r1, -0x20(r1)
    mflr  r0
    stw   r0, 0x24(r1)
    stw   r3, 0x8(r1)
    stw   r4, 0xc(r1)
    lwz   r0, 0x58(r3)              # requested scene, -1 = none
    cmpwi r0, -1
    beq   1f
    bl    pm_scene_change
1:  lwz   r0, 0x24(r1)
    mtlr  r0
    lwz   r3, 0x8(r1)
    lwz   r4, 0xc(r1)
    addi  r1, r1, 0x20
    stwu  r1, -0x10(r1)             # original instruction
    b     scene_hook_return

# Axe stub: the baked Cursed Axe code (0x800038E8 / 0x80003900, was li r3,0) calls here on every swing.
    .globl pm_axe_stub
pm_axe_stub:
    b     pm_axe_hit                # returns 0 in r3, as the li did

# Player hook: 0x80043120 (start of the field A handler, was stwu r1,-0xa30(r1)); r3 = the player.
    .globl pm_player_stub
pm_player_stub:
    lis   r12, pm_player@ha
    stw   r3, pm_player@l(r12)
    stwu  r1, -0xa30(r1)             # original instruction
    b     player_hook_return

# Label hook: 0x8004368C (field A handler, was stw r24,0x128(r31)); r24 = the A action it chose, r31 = the player.
# pm_label may swap the action (0x0F, tool swing, at a log) so the HUD shows the swing label.
    .globl pm_label_stub
pm_label_stub:
    stwu  r1, -0x10(r1)
    mflr  r0
    stw   r0, 0x14(r1)
    mr    r3, r24
    mr    r4, r31
    bl    pm_label
    mr    r24, r3
    lwz   r0, 0x14(r1)
    mtlr  r0
    addi  r1, r1, 0x10
    stw   r24, 0x128(r31)            # original instruction
    b     label_hook_return

# Sound hook: 0x8018B224 (sound start, was lhz r3,0x14(r31)): r3 = sound id; pm_sfx may swap it.
# r4-r10 carry the caller's volume/pan arguments to the next call, so they are kept.
    .globl pm_sfx_stub
pm_sfx_stub:
    stwu  r1, -0x30(r1)
    mflr  r0
    stw   r0, 0x34(r1)
    stw   r4, 0x8(r1)
    stw   r5, 0xc(r1)
    stw   r6, 0x10(r1)
    stw   r7, 0x14(r1)
    stw   r8, 0x18(r1)
    stw   r9, 0x1c(r1)
    stw   r10, 0x20(r1)
    lhz   r3, 0x14(r31)            # original instruction
    bl    pm_sfx
    lwz   r4, 0x8(r1)
    lwz   r5, 0xc(r1)
    lwz   r6, 0x10(r1)
    lwz   r7, 0x14(r1)
    lwz   r8, 0x18(r1)
    lwz   r9, 0x1c(r1)
    lwz   r10, 0x20(r1)
    lwz   r0, 0x34(r1)
    mtlr  r0
    addi  r1, r1, 0x30
    b     sfx_hook_return

# Swing-end hook: 0x80033170 (swing state's end check, was b 0x8003319C = "end after N frames").
# r0 = the held tool's category, r31 = the player. Category 1 (hoes, the Cursed Axe) asks pm_swing_done,
# which scales the vanilla 30 frames by the swing's motion speed (proficiency, stamina).
    .globl pm_exit_stub
pm_exit_stub:
    cmpwi r0, 1
    bne   1f
    stwu  r1, -0x10(r1)
    mflr  r0
    stw   r0, 0x14(r1)
    mr    r3, r31
    bl    pm_swing_done
    lwz   r0, 0x14(r1)
    mtlr  r0
    addi  r1, r1, 0x10
    cmpwi r3, 0
    beq   2f
    b     exit_now                  # 0x800331A8: end the swing
2:  b     exit_wait                 # 0x800332E8: not yet
1:  b     exit_frames               # 0x8003319C: the original frame count

# Villager-asks-for-an-item pick: 0x8011886C (end of func_8011811C, was lwz r3,0x20(r1)); the
# Cursed Axe (0x502) and the $JOE coin (0x442) are never offered for sale: they come back as 0, the callers' "nothing" case.
    .globl pm_nosell_stub
pm_nosell_stub:
    lwz   r3, 0x20(r1)              # original instruction
    cmpwi r3, 0x502                 # the Cursed Axe
    beq   2f
    cmpwi r3, 0x442                 # the $JOE coin: only Joe buys it
    bne   1f
2:  li    r3, 0
1:  b     nosell_return

# TV channel 3 caption: 0x8008E298 (func_8008E298, was stwu r1,-0x20(r1)) -> joe_tv(prog, str), returns str.
    .globl pm_tv_stub
pm_tv_stub:
    b     joe_tv

# Villager talk line: 0x80117B10 (func_80117B10(villager, record, &group, &line), was stwu r1,-0x40(r1)).
# Runs the original, then joe_talk_post(villager, record, &group, &line, result) may swap the line.
    .globl pm_talk_stub
pm_talk_stub:
    stwu  r1, -0x20(r1)
    mflr  r0
    stw   r0, 0x24(r1)
    stw   r3, 0x8(r1)
    stw   r4, 0xc(r1)
    stw   r5, 0x10(r1)
    stw   r6, 0x14(r1)
    bl    1f
    mr    r7, r3
    lwz   r3, 0x8(r1)
    lwz   r4, 0xc(r1)
    lwz   r5, 0x10(r1)
    lwz   r6, 0x14(r1)
    bl    joe_talk_post
    lwz   r0, 0x24(r1)
    mtlr  r0
    addi  r1, r1, 0x20
    blr
1:  stwu  r1, -0x40(r1)             # original first instruction
    b     talk_hook_return          # 0x80117B14

# Villager liked/wanted-item list check: 0x80148A4C (func_80148A4C(list, item), was stwu r1,-0x30(r1)).
# The $JOE coin (0x442) is in no villager's lists: no "can I have it?", no gift acceptance.
    .globl pm_want_stub
pm_want_stub:
    cmpwi r5, 0x442
    bne   1f
    li    r3, 0
    blr
1:  stwu  r1, -0x30(r1)             # original first instruction
    b     want_hook_return          # 0x80148A50

# Villager daily plan: 0x80060EF8 (func_80060EF8(state), was stwu r1,-0x140(r1)). plan_log(state) records who
# planned and when (bench sit test 11 probe: does Takakura, villager 7, plan the trade jobs after a bench skip).
    .globl pm_van_stub
pm_van_stub:
    stwu  r1, -0x20(r1)
    mflr  r0
    stw   r0, 0x24(r1)
    stw   r3, 0x8(r1)
    bl    plan_log
    lwz   r3, 0x8(r1)
    lwz   r0, 0x24(r1)
    mtlr  r0
    addi  r1, r1, 0x20
    stwu  r1, -0x140(r1)            # original first instruction
    b     van_hook_return           # 0x80060EFC

# Script messages: func_80113864 (every script message command) opens the window with mode 0, which never
# shows the speaker's name and heart. HOOK12 (its bl func_801020E4 at 0x80113894) comes here: Joe's lines
# (file 0x15, mukumuku.mes) open in mode 1, the villager talk window with name and heart.
    .globl pm_msg_stub
pm_msg_stub:
    cmpwi r5, 0x15
    bne   1f
    li    r4, 1
1:  b     msg_open                  # 0x801020E4

# Z targeting: 0x800313C4, in the player's update right after his state handler (r30 = player), before his
# position and facing are copied into event slot 0. zt_post(player) turns him toward the lock-on target.
    .globl pm_zt_stub
pm_zt_stub:
    stwu  r1, -0x10(r1)
    mflr  r0
    stw   r0, 0x14(r1)
    mr    r3, r30
    bl    zt_post
    lwz   r0, 0x14(r1)
    mtlr  r0
    addi  r1, r1, 0x10
    lwz   r3, -0x57F4(r13)          # original instruction (lwz r3, lbl_803491CC@sda21(r13))
    b     zt_hook_return            # 0x800313C8

# Z targeting tilt: the camera base's look-at (func_8017B834 / func_8017B89C: C_MTXLookAt into camera +0x50, r31 =
# camera) -> zt_tilt(camera) pitches the field camera's view up a little while locked on. Hooked at the
# instruction after each look-at (lwz r0, 0x34(r1)), replayed here.
    .globl pm_tilt_stub
pm_tilt_stub:
    mr    r3, r31
    bl    zt_tilt
    lwz   r0, 0x34(r1)
    b     tilt_return1              # 0x8017B88C
    .globl pm_tilt2_stub
pm_tilt2_stub:
    mr    r3, r31
    bl    zt_tilt
    lwz   r0, 0x34(r1)
    b     tilt_return2              # 0x8017B8F8

# Z targeting moves: the free-roaming state's three motion picks (idle / walk / run: bl func_8007C100 at
# 0x80042D44 / D98 / DD0) come here instead; zt_motion has func_8007C100's arguments (slot, r4-r8, f1 rate)
# and plays the strafe / walk-back clips while locked on, else calls func_8007C100 itself.
    .globl pm_mot_stub
pm_mot_stub:
    b     zt_motion
# Z targeting facing: func_8003083C has just set the player's facing from the stick (+0x58, r25 = player),
# before the model uses it this frame; zt_face keeps him turned to the target while locked on.
    .globl pm_face_stub
pm_face_stub:
    mr    r3, r25
    bl    zt_face
    b     face_return               # 0x80030A5C (the replaced instruction was b 0x80030A5C)

# Field tile cursor: func_80091F58(pos, view mtx) (the thin yellow square) -> zt_tile_cursor (tile.c), the
# Z-target bracket style. b (not bl): it returns straight to the game's caller.
    .globl pm_tile_stub
pm_tile_stub:
    b     zt_tile_cursor

# Upper-body layer: func_8019E438 (every model's pose build, r24 = model instance) evaluates each bone with
# bl func_801A01F8(anim ctl, bone, trs) at 0x8019E5C4; that bl comes here. zt_bone(ctl, bone, trs, inst) calls it,
# then blends the Z-target tool swing into the player's spine / arms / head (tools/ztarget/NOTES.md).
    .globl pm_bone_stub
pm_bone_stub:
    mr    r6, r24
    b     zt_bone

# Area tools: right after func_80043120 case 0xF sends its one tool-hit message (bl func_80011680 at 0x80043908;
# message at r1+0x778, r26 = item, r31 = player). The function saved LR in its prologue, so bl is free here.
# tool_area (toolfix.c) re-sends it to the neighbouring field tiles; the send's result (r3) is kept in r22, which
# the game sets from r3 at 0x80043918 anyway.
    .globl pm_area_stub
pm_area_stub:
    mr    r22, r3
    addi  r3, r1, 0x778
    mr    r4, r26
    mr    r5, r31
    mr    r6, r22                   # the main send's result (0 = accepted)
    bl    tool_area
    mr    r3, r22
    lwz   r0, 0x1c(r1)              # the replaced instruction
    b     area_return               # 0x80043910

# New game: the start-up code gives the Milker with bl func_8004FDA0(game+0x50, 0x4F6, 1, -1) at 0x800136D8 (r28 =
# game). That bl comes here: the Milker, then the Stick (0x4E3) the same way, so it starts in the rucksack too.
    .globl pm_newgame_stub
pm_newgame_stub:
    stwu  r1, -0x10(r1)
    mflr  r0
    stw   r0, 0x14(r1)
    bl    item_pool_add             # the replaced call (Milker)
    mr    r3, r28
    bl    newgame_extra             # toolfix.c: the Stick (all four weapons in a WEAPONS_ALL test build)
    nop                             # (kept at 13 instructions so the stubs after it stay where they are)
    nop
    nop
    lwz   r0, 0x14(r1)
    mtlr  r0
    addi  r1, r1, 0x10
    blr

# Area tools, part 2: tool state 0x79's impact frame (lbl_80033130) sends the type-0x1C "apply" message to the
# target (pl+0x1388) at 0x800332BC (message at r1+0x8, r31 = player; LR saved in the prologue). tool_area_impact
# sends it to the neighbours that took the hit too, so they really change and redraw.
    .globl pm_impact_stub
pm_impact_stub:
    addi  r3, r1, 0x8
    mr    r4, r31
    bl    tool_area_impact
    lis   r3, 0x8029                # the replaced instruction (lis r3, lbl_802971C8@ha)
    b     impact_return             # 0x800332C4

# Clip lookup: func_801A0A88(arc, 0, clip) entry (stwu r1,-0x40(r1)) -> pm_arcanim_stub -> zt_arc_anim (zt.c), which
# serves the player's clips 126-131 from pm.bin and otherwise calls arc_anim_orig (the replaced instruction, then
# the rest of the original at 0x801A0A8C).
    .globl pm_arcanim_stub
pm_arcanim_stub:
    b     zt_arc_anim
    .globl arc_anim_orig
arc_anim_orig:
    stwu  r1, -0x40(r1)
    b     arcanim_return            # 0x801A0A8C

# Menu display boxes: func_800121C4 fits a symbol model in the rucksack / item views with a 7-halfword box per
# model (table lbl_8028E84C, 14 bytes each, only as long as the vanilla model list). At 0x80012200 (add r7,r5,r6:
# r6 = model * 14) this bl picks zt_sym_boxes (toolfix.c) for the weapon models 196+. Uses only r7 (r0 holds the
# loop count); LR is saved by the function.
    .globl pm_box_stub
pm_box_stub:
    cmplwi r6, 196 * 14
    blt   1f
    lis   r7, (zt_sym_boxes - 196 * 14)@ha
    addi  r7, r7, (zt_sym_boxes - 196 * 14)@l
    add   r7, r7, r6
    blr
1:  add   r7, r5, r6                # the replaced instruction
    blr

# operator new (0x80178E88 entry, stwu r1,-0x20(r1)) -> pm_new_stub: while joe_to_a is set, requests of 64 KB or
# more (Joe's model / animations) go to pool A via pm_new_a (pm.c), which returns 0 when they do not fit there.
    .globl pm_new_stub
pm_new_stub:
    lis   r12, joe_to_a@ha
    lwz   r12, joe_to_a@l(r12)
    cmpwi r12, 0
    beq   1f
    srwi  r12, r3, 16               # < 64 KB: as before
    cmpwi r12, 0
    beq   1f
    stwu  r1, -0x20(r1)
    mflr  r0
    stw   r0, 0x24(r1)
    stw   r3, 0x8(r1)
    stw   r4, 0xc(r1)
    stw   r5, 0x10(r1)
    bl    pm_new_a
    lwz   r0, 0x24(r1)
    mtlr  r0
    cmpwi r3, 0
    bne   2f
    lwz   r3, 0x8(r1)
    lwz   r4, 0xc(r1)
    lwz   r5, 0x10(r1)
    addi  r1, r1, 0x20
1:  stwu  r1, -0x20(r1)             # normal path: the original operator new, then the pool guard (mg_after)
    mflr  r0
    stw   r0, 0x24(r1)
    stw   r3, 0x8(r1)
    bl    new_orig
    stw   r3, 0x14(r1)
    mr    r4, r3
    lis   r3, 0x8031
    ori   r3, r3, 0x5508            # pool B
    lwz   r5, 0x8(r1)
    lwz   r6, 0x24(r1)
    li    r7, 0
    bl    mg_after
    lwz   r3, 0x14(r1)
    lwz   r0, 0x24(r1)
    mtlr  r0
2:  addi  r1, r1, 0x20
    blr
new_orig:
    stwu  r1, -0x20(r1)             # the replaced instruction
    b     new_return                # 0x80178E8C

# operator delete (0x80179168 entry, stwu r1,-0x20(r1)) -> pm_del_stub: our pool-A blocks go back to pool A.
    .globl pm_del_stub
pm_del_stub:
    cmpwi r3, 0
    beq   1f
    stwu  r1, -0x20(r1)
    mflr  r0
    stw   r0, 0x24(r1)
    stw   r3, 0x8(r1)
    bl    pm_del_a
    lwz   r0, 0x24(r1)
    mtlr  r0
    cmpwi r3, 0
    lwz   r3, 0x8(r1)
    addi  r1, r1, 0x20
    bnelr
1:  stwu  r1, -0x20(r1)             # the replaced instruction
    b     del_return                # 0x8017916C

# Pool allocation func_80178A44(pool, size, file, line) (entry stwu r1,-0x30(r1)): every pool-A allocation and the
# pool-B ones that do not go through operator new. After it, mg_after (pm.c) checks the new block against the
# other pool's used blocks (memfix 19 pool guard).
    .globl pm_pool_stub
pm_pool_stub:
    stwu  r1, -0x20(r1)
    mflr  r0
    stw   r0, 0x24(r1)
    stw   r3, 0x8(r1)
    stw   r4, 0xc(r1)
    lwz   r0, 0x34(r1)              # the wrapper's caller (wrappers keep LR at +0x14 of a 0x10 frame)
    stw   r0, 0x10(r1)
    bl    pool_orig
    stw   r3, 0x14(r1)
    mr    r4, r3
    lwz   r3, 0x8(r1)
    lwz   r5, 0xc(r1)
    lwz   r6, 0x24(r1)
    lwz   r7, 0x10(r1)
    bl    mg_after
    lwz   r3, 0x14(r1)
    lwz   r0, 0x24(r1)
    mtlr  r0
    addi  r1, r1, 0x20
    blr
pool_orig:
    stwu  r1, -0x30(r1)             # the replaced instruction
    b     pool_return               # 0x80178A48

# Wild animal update (func_8015A22C): its AI step (bl func_8015A6D4 at 0x8015A2B4) and movement (bl func_8015C398 at
# 0x8015A2BC) -> these stubs: skipped while zt.c's battle AI drives this animal (en_ctl == r3), else the originals.
    .globl pm_aistep_stub
pm_aistep_stub:
    lis   r12, en_ctl@ha
    lwz   r12, en_ctl@l(r12)
    cmpw  r12, r3
    beqlr
    b     ai_step_orig              # 0x8015A6D4
    .globl pm_move_stub
pm_move_stub:
    lis   r12, en_ctl@ha
    lwz   r12, en_ctl@l(r12)
    cmpw  r12, r3
    beqlr
    b     ai_move_orig              # 0x8015C398
