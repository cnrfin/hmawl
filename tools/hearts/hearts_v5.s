# Name-plate hearts. C2 hook at 0x80102598 (was: addi r4,r31,0x384) in the name-plate draw.
# r31 = message object, r3 = draw context (kept). +0x384 = speaker name, +0x60 = speaker = villager id.
# Draws "<name> <colour>hearts<17>" from BUF instead of +0x384.
# Colour codes: 10 white, 11 black, 12 red, 13 green, 14 blue, 15 dark grey, 16 custom, 17 back to default.
#   villagers, friendship (record +7, 1..100): <=50 1 dark grey, 51-60 1 green, 61-70 1 blue,
#     71-80 1 red, 81-90 2 red, 91-100 3 red
#   Celia/Muffy/Nami, love only (love byte +0x1D): 0-9 1 dark grey, 10-19 1 green,
#     20+ 1-5 red (game's love level, thresholds 20/40/60/80/90 at 0x8034B624)
.set BUF, 0x80005000            # 64 bytes, unused .init (0x80004F70-0x800050AC is zero)
    stwu  r1, -0x20(r1)
    mflr  r0
    stw   r0, 0x24(r1)
    stw   r3, 0x08(r1)
    stw   r30, 0x0C(r1)
    stw   r29, 0x10(r1)
    addi  r30, r31, 0x384        # default: the game's own name
    lbz   r0, 0(r30)
    cmpwi r0, 0
    beq   9f
    lwz   r4, 0x60(r31)
    cmpwi r4, 1
    blt   9f
    lis   r3, 0x8035
    lwz   r3, -0x6E34(r3)        # game (0x803491CC)
    lis   r12, 0x8000
    ori   r12, r12, 0xDC24       # func_8000DC24(game, id): villager record or 0
    mtctr r12
    bctrl
    cmpwi r3, 0
    beq   9f
    lbz   r29, 7(r3)             # friendship
    lis   r4, BUF@h
    ori   r4, r4, BUF@l
    addi  r5, r31, 0x384
    subi  r6, r4, 1              # r6 = last byte written
    addi  r7, r4, 24             # name copy limit
1:  lbz   r0, 0(r5)              # copy the name, whole glyphs only
    cmpwi r0, 0
    beq   2f
    cmplw r6, r7
    bge   2f
    stbu  r0, 1(r6)
    addi  r5, r5, 1
    cmplwi r0, 0x80
    blt   1b
    lbz   r0, 0(r5)
    stbu  r0, 1(r6)
    addi  r5, r5, 1
    b     1b
2:  lwz   r4, 0x60(r31)
    subi  r4, r4, 2              # Celia 2, Muffy 3, Nami 4 -> love record 0..2
    cmplwi r4, 2
    bgt   10f
    lis   r3, 0x8035             # --- marriage candidates: love only
    lwz   r3, -0x6E34(r3)
    slwi  r4, r4, 5
    add   r3, r3, r4
    addis r3, r3, 1
    lbz   r5, 0x4B0D(r3)         # love: +0x14AF0 + 0x1D
    li    r7, 1
    li    r8, 0x15               # 0-9: 1 dark grey
    cmplwi r5, 10
    blt   4f
    li    r8, 0x13               # 10-19: 1 green
    cmplwi r5, 20
    blt   4f
    lis   r8, 0x8035
    subi  r8, r8, 0x49DC         # 20+: game's love level 1-5 (thresholds 0x8034B624), red
    li    r7, 0
3:  lbz   r0, 0(r8)
    cmplw r5, r0
    blt   5f
    addi  r7, r7, 1
    addi  r8, r8, 1
    cmpwi r7, 5
    blt   3b
5:  li    r8, 0x12
4:  bl    7f
    b     8f
10: subi  r0, r29, 41            # --- everyone else: friendship
    li    r7, 10
    divw  r7, r0, r7             # band: <=50 0, 51-60 1, 61-70 2, 71-80 3, 81-90 4, 91-100 5
    cmpwi r7, 0
    bge   2f
    li    r7, 0
2:  li    r8, 0x15               # band 0: 1 dark grey
    cmpwi r7, 1
    blt   2f
    li    r8, 0x13               # band 1: 1 green
    beq   2f
    li    r8, 0x14               # band 2: 1 blue
    cmpwi r7, 2
    beq   2f
    li    r8, 0x12               # band 3-5: 1-3 red
    subi  r7, r7, 2
    b     3f
2:  li    r7, 1
3:  bl    7f
8:  li    r0, 0
    stb   r0, 1(r6)
    lis   r30, BUF@h
    ori   r30, r30, BUF@l
    b     9f
# put " <r8>" + r7 hearts (max 5) + "<17>" after r6; nothing if r7 <= 0
7:  cmpwi r7, 0
    blelr
    cmpwi r7, 5
    ble   5f
    li    r7, 5
5:  li    r0, 2
    stbu  r0, 1(r6)
    stbu  r8, 1(r6)
    mtctr r7
6:  li    r0, 0x80
    stbu  r0, 1(r6)
    li    r0, 0xD6
    stbu  r0, 1(r6)
    bdnz  6b
    li    r0, 0x17
    stbu  r0, 1(r6)
    blr
9:  mr    r4, r30
    lwz   r3, 0x08(r1)
    lwz   r30, 0x0C(r1)
    lwz   r29, 0x10(r1)
    lwz   r0, 0x24(r1)
    mtlr  r0
    addi  r1, r1, 0x20
