# HM AWL v02: codes moved from Gecko into main.dol caves (unused .init padding, zero in every RAM dump).
# Each routine has its own section; v02.ld places them. Hook sites get "b <routine>" (make_v02.py).
.set GAME,   0x803491CC         # game data pointer
.set AGC,    0x80349110         # loaded opguide.agc
.set FLAG,   0x80005064         # Ax give: 2 = given this boot
.set LAST,   0x80005060         # dog bowl: last day seen
.set STATE,  0x80005070
.include "hudoffs.inc"         # HUD: +0 x, +4 z, +8 still frames, +C slide offset

# ---------- name-plate hearts (hook 0x80102598, was addi r4,r31,0x384) ----------
.section .hearts,"ax"
.global hearts
hearts:
    .incbin "hearts_v7_code.bin"
    b     R_8010259C

# ---------- HUD per-frame hook (0x80082F94, was stwu r1,-0x10(r1)); r3 = HUD = player+0xDC ----------
.section .hud,"ax"
.global hud_hook
hud_hook:
    stwu  r1, -0x90(r1)
    stw   r0, 0x08(r1)
    mflr  r0
    stw   r0, 0x0C(r1)
    mfcr  r0
    stw   r0, 0x10(r1)
    mfctr r0
    stw   r0, 0x14(r1)
    stmw  r3, 0x18(r1)          # r3..r31 -> 0x18..0x8B
    bl    hud_fill
    lwz   r3, 0x18(r1)
    bl    hud_slide
    bl    dogbowl
    bl    axgive
    lwz   r3, 0x18(r1)
    bl    hud_name
    lmw   r3, 0x18(r1)
    lwz   r0, 0x14(r1)
    mtctr r0
    lwz   r0, 0x10(r1)
    mtcr  r0
    lwz   r0, 0x0C(r1)
    mtlr  r0
    lwz   r0, 0x08(r1)
    addi  r1, r1, 0x90
    stwu  r1, -0x10(r1)         # original instruction
    b     R_80082F98

# r9 = agc (or 0), r4 = ctrl (or 0)
hud_ptrs:
    li    r9, 0
    li    r4, 0
    lis   r6, 0x8000
    lis   r7, 0x8180
    lis   r5, AGC@ha
    lwz   r5, AGC@l(r5)
    cmplw r5, r6
    bltlr
    cmplw r5, r7
    bgelr
    lwz   r8, SFILL(r5)         # our fill quad uses texture 2
    cmpwi r8, 2
    bnelr
    lis   r8, GAME@ha
    lwz   r8, GAME@l(r8)
    cmplw r8, r6
    bltlr
    cmplw r8, r7
    bgelr
    mr    r9, r5
    addis r4, r8, 1
    addi  r4, r4, 0x1B80        # ctrl = game + 0x11B80
    blr

hud_fill:
    mflr  r10
    bl    hud_ptrs
    mtlr  r10
    cmpwi r9, 0
    beqlr
    lwz   r5, 4(r4)             # stamina 0..100000
    cmpwi r5, 0
    bge   1f
    li    r5, 0
1:  lis   r6, 1
    ori   r6, r6, 0x86A0
    cmpw  r5, r6
    ble   2f
    mr    r5, r6
2:  mr    r7, r5
    mulli r5, r5, 168
    divwu r5, r5, r6
    sth   r5, SFILL+8(r9)         # stamina fill x1
    li    r6, 0
    ori   r6, r6, 50000
    cmpw  r7, r6
    ble   3f
    lis   r5, 0x3E40            # green rows
    lis   r6, 0x3EA0
    b     5f
3:  li    r6, 0
    ori   r6, r6, 25000
    cmpw  r7, r6
    ble   4f
    lis   r5, 0x3EAA            # yellow
    ori   r5, r5, 0xAAAB
    lis   r6, 0x3EEA
    ori   r6, r6, 0xAAAB
    b     5f
4:  lis   r5, 0x3EF5            # red
    ori   r5, r5, 0x5555
    lis   r6, 0x3F1A
    ori   r6, r6, 0xAAAB
5:  stw   r5, SFILL+0x20(r9)
    stw   r6, SFILL+0x28(r9)
    lwz   r5, 0x14(r4)          # fullness 0..1350000
    cmpwi r5, 0
    bge   6f
    li    r5, 0
6:  lis   r6, 0x14
    ori   r6, r6, 0x9970
    cmpw  r5, r6
    ble   7f
    mr    r5, r6
7:  mulli r5, r5, 110
    divwu r5, r5, r6
    sth   r5, FFILL+8(r9)         # fullness fill x1
    blr

.section .hud2,"ax"
.global hud_slide
hud_slide:                      # r3 = HUD
    mflr  r10
    bl    hud_ptrs
    mtlr  r10
    cmpwi r9, 0
    beqlr
    lis   r10, STATE@ha
    addi  r10, r10, STATE@l
    addi  r8, r3, -0xDC         # player
    lwz   r6, 0x135C(r8)
    cmpw  r6, r4
    bne   3f
    lwz   r5, 0x4C(r8)          # x
    lwz   r6, 0x54(r8)          # z
    lwz   r7, 0(r10)
    lwz   r11, 4(r10)
    stw   r5, 0(r10)
    stw   r6, 4(r10)
    lwz   r12, 8(r10)
    cmpw  r5, r7
    bne   1f
    cmpw  r6, r11
    bne   1f
    cmpwi r12, 255
    bge   2f
    addi  r12, r12, 1
    b     2f
1:  li    r12, 0
2:  stw   r12, 8(r10)
3:  lwz   r12, 8(r10)
    lwz   r5, 0xC(r10)
    cmpwi r12, 20               # frames standing still before it shows
    blt   5f
    li    r6, 5                 # show: ease in
    divwu r7, r5, r6
    cmpwi r7, 1
    bge   4f
    li    r7, 1
4:  subf  r5, r7, r5
    cmpwi r5, 0
    bge   6f
    li    r5, 0
    b     6f
5:  addi  r5, r5, 8             # hide
    cmpwi r5, 110
    ble   6f
    li    r5, 110
6:  stw   r5, 0xC(r10)
    b     hud_apply

.section .hud3,"ax"
hud_apply:                      # y = base - offset for our elements
    li    r6, -178
    subf  r6, r5, r6
    sth   r6, 0xE4A(r9)
    li    r6, -176
    subf  r6, r5, r6
    sth   r6, 0xE56(r9)
    li    r6, -153
    subf  r6, r5, r6
    sth   r6, 0xE62(r9)
    li    r6, -151
    subf  r6, r5, r6
    sth   r6, 0xE6E(r9)
    li    r6, -164
    subf  r6, r5, r6
    sth   r6, 0xE7A(r9)
    li    r6, -204
    subf  r6, r5, r6
    sth   r6, 0xE86(r9)
    li    r6, -204
    subf  r6, r5, r6
    sth   r6, 0xE92(r9)
    blr

# ---------- dog bowl filled each new day ----------
.section .dog,"ax"
.global dogbowl
dogbowl:
    lis   r3, 0x8035
    lwz   r4, -0x6DE8(r3)       # clock (0x80349218)
    lwz   r5, -0x6E34(r3)       # game
    lis   r0, 0x8000
    cmplw r4, r0
    bltlr
    cmplw r5, r0
    bltlr
    lis   r0, 0x8180
    cmplw r4, r0
    bgelr
    cmplw r5, r0
    bgelr
    lwz   r6, 0(r4)
    lis   r7, 1
    ori   r7, r7, 0x5180        # 86400
    divwu r6, r6, r7
    lis   r8, LAST@ha
    lwz   r9, LAST@l(r8)
    cmpw  r6, r9
    beqlr
    stw   r6, LAST@l(r8)
    addis r5, r5, 3
    li    r0, 1
    stb   r0, -0x6656(r5)       # game+0x299AA = bowl full
    blr

# ---------- give the Ax once per boot if it is neither in the rucksack nor in the hands ----------
.section .axgive,"ax"
.global axgive
axgive:
    lis   r3, FLAG@ha
    lwz   r0, FLAG@l(r3)
    cmpwi r0, 2
    beqlr
    lis   r3, GAME@ha
    lwz   r31, GAME@l(r3)
    lis   r0, 0x8000
    cmplw r31, r0
    bltlr
    lis   r0, 0x8180
    cmplw r31, r0
    bgelr
    lwz   r0, 0x54(r31)         # container vtable must be the item box's
    lis   r3, 0x802B
    ori   r3, r3, 0xC070
    cmplw r0, r3
    bnelr
    addis r3, r31, 1
    lwz   r0, 0x1CC4(r3)        # ctrl+0x144 = held item (game+0x11CC4)
    cmpwi r0, 0x502
    beq   9f
    addi  r30, r31, 0x50        # container
    li    r29, 0
    li    r28, 0                # non-empty slots seen
1:  slwi  r3, r29, 2
    add   r3, r3, r30
    lhz   r0, 8(r3)
    cmplwi r0, 0x502
    beq   9f                    # already there
    cmplwi r0, 0
    beq   2f
    addi  r28, r28, 1
2:  addi  r29, r29, 1
    cmpwi r29, 350
    blt   1b
    cmpwi r28, 0
    beqlr                       # save not loaded yet
    mflr  r27
    mr    r3, r30
    li    r4, 0x502
    li    r5, 1
    li    r6, -1
    lis   r12, 0x8004
    ori   r12, r12, 0xFDA0
    mtctr r12
    bctrl                       # func_8004FDA0: add 1 Ax the game's way
    mtlr  r27
9:  lis   r3, FLAG@ha
    li    r0, 2
    stw   r0, FLAG@l(r3)
    blr

# ---------- Ax: swing without hitting ----------
.section .ax,"ax"
.global notill1, notill2, stamA, stamB, stamC
notill1:                        # 0x800438F8 (addi r3,r1,0x778)
    cmpwi r26, 0x502
    bne   1f
    li    r3, 0
    b     R_8004390C
1:  addi  r3, r1, 0x778
    b     R_800438FC
notill2:                        # 0x80043960 (addi r3,r1,0x744)
    cmpwi r26, 0x502
    bne   1f
    li    r3, 0
    b     R_8004397C
1:  addi  r3, r1, 0x744
    b     R_80043964
# ---------- Ax stamina: hoe row, 120 % drain, no hoe skill gain ----------
stamA:                          # 0x8004E3B4 (cmpwi r8,0x4ec)
    cmpwi r8, 0x502
    bne   1f
    li    r31, 0x12
    lfs   f31, -0x7A90(r2)      # lbl_8034A3B0 (2.0)
    b     R_8004E5B8
1:  cmpwi r8, 0x4EC
    b     R_8004E3B8
stamB:                          # 0x8004BEF4 (subf r0,r3,r0)
    lwz   r12, 0x144(r31)
    cmpwi r12, 0x502
    bne   1f
    mulli r3, r3, 6
    li    r12, 5
    divwu r3, r3, r12
1:  subf  r0, r3, r0
    b     R_8004BEF8
stamC:                          # 0x8004D7AC (stwu r1,-0x40(r1))
    cmpwi r5, 0x502
    bne   1f
    blr
1:  stwu  r1, -0x40(r1)
    b     R_8004D7B0

# ---------- farmer's name under the face: 12 glyph quads (texture 3) at NAMEQ ----------
.section .name,"ax"
.global hud_name
hud_name:
    mflr  r10
    bl    hud_ptrs
    mtlr  r10
    cmpwi r9, 0
    beqlr
    addis r6, r4, -1
    addi  r6, r6, -0x1B80       # game = ctrl - 0x11B80
    addis r6, r6, 1
    addi  r6, r6, 0x1D08        # farmer's name = game + 0x11D08 (text of the name object at +0x11D00)
    addi  r11, r9, NAMEQ        # quad pointer
    li    r5, 0                 # pen x
    li    r12, 12               # quads left
    lis   r8, ntab@ha
    addi  r8, r8, ntab@l
1:  lbz   r0, 0(r6)
    cmpwi r0, 0x80
    beq   3f
    cmpwi r0, 2                 # space
    bne   name_hide             # end (0) or anything else: hide the rest
    addi  r6, r6, 1
    addi  r5, r5, 7
    b     7f
3:  lbz   r7, 1(r6)
    addi  r6, r6, 2
    subi  r0, r7, 0x0B          # A-Z -> 0..25
    cmplwi r0, 26
    blt   4f
    subi  r3, r7, 0xD8          # a-z -> 26..51
    cmplwi r3, 26
    addi  r0, r3, 26
    blt   4f
    addi  r5, r5, 8             # other glyph: leave a gap
    b     7f
4:  slwi  r7, r0, 1
    add   r7, r7, r8
    lbz   r3, 0(r7)             # left bearing
    lbz   r7, 1(r7)             # width
    subf  r3, r3, r5            # x0 = pen - bearing
    sth   r3, 4(r11)
    addi  r3, r3, NCELL
    sth   r3, 8(r11)
    add   r5, r5, r7
    subi  r5, r5, 1
    b     uvset
7:  li    r0, 0                 # hidden quad
    sth   r0, 4(r11)
    sth   r0, 8(r11)
name_next:
    addi  r11, r11, 0x2C
    subic. r12, r12, 1
    bgt   1b
    blr

.section .name2,"ax"
name_hide:                      # zero-width the remaining quads
    li    r0, 0
    sth   r0, 4(r11)
    sth   r0, 8(r11)
    addi  r11, r11, 0x2C
    subic. r12, r12, 1
    bgt   name_hide
    blr
uvset:                          # r0 = glyph index: copy the cell's UVs, then back to the loop
    li    r3, NCOLS
    divwu r7, r0, r3            # row
    mullw r3, r7, r3
    subf  r3, r3, r0            # col
    slwi  r3, r3, 2
    lis   r10, ucol@ha
    addi  r10, r10, ucol@l
    add   r3, r3, r10
    lwz   r0, 0(r3)
    stw   r0, 0x1C(r11)         # u0
    lwz   r0, 4(r3)
    stw   r0, 0x24(r11)         # u1
    slwi  r7, r7, 2
    lis   r10, vrow@ha
    addi  r10, r10, vrow@l
    add   r7, r7, r10
    lwz   r0, 0(r7)
    stw   r0, 0x20(r11)         # v0
    lwz   r0, 4(r7)
    stw   r0, 0x28(r11)         # v1
    b     name_next

.section .namedata,"a"
.global ntab, ucol, vrow
ntab:
    .byte 0, 20
    .byte 2, 17
    .byte 2, 17
    .byte 1, 18
    .byte 2, 18
    .byte 2, 17
    .byte 1, 19
    .byte 1, 18
    .byte 7, 7
    .byte 3, 15
    .byte 1, 18
    .byte 2, 17
    .byte 0, 20
    .byte 0, 20
    .byte 1, 19
    .byte 2, 17
    .byte 0, 20
    .byte 1, 19
    .byte 2, 17
    .byte 1, 18
    .byte 1, 19
    .byte 1, 18
    .byte 0, 20
    .byte 2, 18
    .byte 1, 19
    .byte 1, 19
    .byte 3, 14
    .byte 4, 14
    .byte 4, 13
    .byte 3, 15
    .byte 3, 14
    .byte 3, 14
    .byte 4, 12
    .byte 3, 14
    .byte 8, 7
    .byte 5, 9
    .byte 4, 13
    .byte 7, 7
    .byte 1, 19
    .byte 3, 14
    .byte 3, 14
    .byte 4, 13
    .byte 4, 12
    .byte 5, 11
    .byte 4, 12
    .byte 2, 14
    .byte 2, 15
    .byte 4, 13
    .byte 2, 15
    .byte 4, 13
    .byte 4, 14
    .byte 3, 14
    .balign 4
ucol:
    .float 0.0
    .float 0.08203125
    .float 0.1640625
    .float 0.24609375
    .float 0.328125
    .float 0.41015625
    .float 0.4921875
    .float 0.57421875
    .float 0.65625
    .float 0.73828125
    .float 0.8203125
    .float 0.90234375
    .float 0.984375
vrow:
    .float 0.0
    .float 0.1875
    .float 0.375
    .float 0.5625
    .float 0.75
    .float 0.9375
