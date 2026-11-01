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
