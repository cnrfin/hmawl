# Findings: gold routine and script command table

Target: Harvest Moon: A Wonderful Life (US, GYWEE9).

Everything below is from **main.dol**. main.dol and the three rels are
separate builds, and each finding says which file it is in.

- "RAM" means the address while running. main.dol always loads at the same
  address, so its RAM addresses are fixed.
- "file" means the byte offset inside the original `main.dol`. This is the
  second column of every line in `asm/main/game/*.s`. That column was checked
  against the original binary.
- The bytes come from the original binaries, after they passed
  `sha1sum -c hmawl_us_r0.sha1`. These are static findings. Where something
  still needs Dolphin, it says so.

## 1. Verified addresses (main.dol)

All four claims from the earlier analysis hold.

### 1.1 `func_80113234`: add to a value, clamped to a min and max ("gold add")

`asm/main/game/code_800F3228.s`, lines 38606–38634.

| RAM | file | bytes | asm |
|---|---|---|---|
| 0x80113234 | 0x10FF74 | `2C 04 00 00` | `cmpwi r4, 0x0` (first instruction of the function) |
| 0x80113254 | 0x10FF94 | `90 03 00 04` | `stw r0, 0x4(r3)` (saves value + amount) |

```
80113234 2C040000  cmpwi r4, 0x0
80113238 4080002C  bge   lbl_80113264
8011323C 80C3000C  lwz   r6, 0xc(r3)     ; minimum
80113240 80030004  lwz   r0, 0x4(r3)     ; current value
80113244 7CA43050  subf  r5, r4, r6
80113248 7C050000  cmpw  r5, r0
8011324C 41810010  bgt   lbl_8011325C
80113250 7C002214  add   r0, r0, r4
80113254 90030004  stw   r0, 0x4(r3)
80113258 4E800020  blr
8011325C 90C30004  stw   r6, 0x4(r3)     ; set to minimum
80113260 4E800020  blr
80113264 80A30004  lwz   r5, 0x4(r3)
80113268 80C30008  lwz   r6, 0x8(r3)     ; maximum
8011326C 7C053050  subf  r0, r5, r6
80113270 7C040000  cmpw  r4, r0
80113274 41810010  bgt   lbl_80113284
80113278 7C052214  add   r0, r5, r4
8011327C 90030004  stw   r0, 0x4(r3)
80113280 4E800020  blr
80113284 90C30004  stw   r6, 0x4(r3)     ; set to maximum
80113288 4E800020  blr
```

What it does (r3 = object, r4 = signed amount): the value at +0x4 becomes
value + amount, kept between the minimum at +0xC and the maximum at +0x8.
All three are 32-bit signed words. The function has no stack frame, and
nothing branches to 0x80113234 except the one call in 1.2.

### 1.2 The only call: 0x801115F4

| RAM | file | bytes | asm |
|---|---|---|---|
| 0x801115F4 | 0x10E334 | `48 00 1C 41` | `bl func_80113234` (the offset 0x1C40 from 0x801115F4 lands on 0x80113234) |
| 0x801115F8 | 0x10E338 | `2C 19 00 00` | `cmpwi r25, 0x0` (the next instruction) |

The search for other callers covered the original binaries, not just the asm text:

- **main.dol**: every word in every text section was decoded as `b`, `bl` or
  `bc`. Every section was also checked for raw pointer words, and text was
  checked for `lis`/`addi` and `lis`/`ori` pairs, targeting 0x80113234–0x8011328B.
  The only result from outside the function is `bl` at 0x801115F4. The other
  three branches into that range are the function's own `bge`/`bgt`.
- **wlp0.rel, wlp1.rel, wlp2.rel**: parsed every relocation table entry
  (9715, 15170 and 7752 entries) and looked for module-0 (main.dol) targets in
  that range. **None found.** To check that the scanner works, it was run
  against `func_80012800`. It found wlp1 sec1+0x1C (file 0x118), which matches
  `bl func_80012800` in `asm/rels/wlp1.s` line 45.
- The asm text agrees: `grep -rn func_80113234 asm/` gives only the label and
  the one `bl`.

### 1.3 Command 0xC1 in the jump table `lbl_802C0078`

`func_8010C604` (RAM 0x8010C604, file 0x109344) is the script command
handler. It checks `cmplwi r25, 0xdd` and then jumps through `lbl_802C0078`,
so the table has **0xDE entries (commands 0x00–0xDD)**. The jump table is in
main.dol section data5. Entry address = 0x802C0078 + command × 4.

| command | RAM of entry | file | value |
|---|---|---|---|
| 0xC0 | 0x802C0378 | 0x2BD378 | `801115B4` |
| **0xC1** | **0x802C037C** | **0x2BD37C** | **`801115D8`** |
| 0xC2 | 0x802C0380 | 0x2BD380 | `80111614` |

The asm agrees: the 194th `.4byte` after `lbl_802C0078:` in
`code_800F3228.s` is `lbl_801115D8`.

Command 0xC1 (`lbl_801115D8`), RAM 0x801115D8–0x80111610:

```
801115D8 7F83E378  mr    r3, r28
801115DC 38800000  li    r4, 0x0
801115E0 48001755  bl    func_80112D34     ; script argument 0 = amount
801115E4 7C791B78  mr    r25, r3
801115E8 480019F5  bl    func_80112FDC     ; r3 = game-data pointer
801115EC 48001A15  bl    func_80113000     ; r3 += 0x11A14
801115F0 7F24CB78  mr    r4, r25
801115F4 48001C41  bl    func_80113234
801115F8 2C190000  cmpwi r25, 0x0
801115FC 418211C8  beq   func_801127C4     ; amount 0 → done
80111600 48001965  bl    func_80112F64     ; r3 = lbl_803491E4
80111604 388000CD  li    r4, 0xcd
80111608 38A00000  li    r5, 0x0
8011160C 48018F21  bl    func_8012A52C     ; runs only when amount != 0 (purpose unknown)
80111610 480011B4  b     func_801127C4
```

### 1.4 The getters

| RAM | file | bytes | asm |
|---|---|---|---|
| 0x80112FDC | 0x10FD1C | `80 6D A8 0C` | `lwz r3, lbl_803491CC@sda21(r13)` |
| 0x80112FE0 | 0x10FD20 | `4E 80 00 20` | `blr` |
| 0x80113000 | 0x10FD40 | `3C 63 00 01` | `addis r3, r3, 0x1` |
| 0x80113004 | 0x10FD44 | `38 63 1A 14` | `addi r3, r3, 0x1a14` |
| 0x80113008 | 0x10FD48 | `4E 80 00 20` | `blr` |

`addis 0x1` adds 0x10000 and `addi 0x1a14` adds 0x1A14, so
`func_80113000` returns r3 + 0x11A14.

**Gold value in RAM:** `*(u32*)0x803491CC + 0x11A14 + 0x4`. The maximum is
at +0x8 and the minimum at +0xC from the same base. You have confirmed this
in Dolphin.

**Gold limits, read in Dolphin:**

| field | offset | RAM (one Dolphin session) | value |
|---|---|---|---|
| gold object base | game-data + 0x11A14 | 0x81085894 (derived) | |
| current gold | +0x4 | 0x81085898 (derived) | |
| maximum | +0x8 | 0x8108589C | `0x05F5E0FF` = 99,999,999 |
| minimum | +0xC | 0x810858A0 | 0 |

The derived rows are worked out from the two read addresses, so in that
session the game-data pointer at 0x803491CC held 0x81073E80. The game-data
object is in the heap, so these RAM addresses may change between boots or
saves. The offsets don't change; use them, not the fixed addresses, in any
patch or cheat code. The limits are values in RAM. I haven't found where
they are set, so changing them would mean finding the code that writes +0x8.

### 1.5 Correction to my earlier report

I said the two 8-entry animal arrays (0x1B4 bytes each) were at
`lbl_803491CC + 0x4` and `+ 0xDA4`. **That was wrong.** Every caller of the
slot functions (`func_800D430C`, `func_800D3A38`, `func_800D4C54`,
`func_800D497C`, …) passes `game-data + 0x27E60` (`addis r3, rX, 0x2;
addi r3, r3, 0x7e60`). The getter `func_8011319C` returns the same pointer.
So, counting from the start of game-data:

- animal slot block: `game-data + 0x27E60`
- first 8-slot array: `game-data + 0x27E64`, second: `game-data + 0x28C04`
- each record is 0x1B4 bytes: +0x0 / +0x4 type codes (see command 0x89),
  +0xC a field read by command 0x8A, +0x1AC kind, +0x1B0 index.

## 2. Command table: cases that use the game-data object

Method: read the 0xDE table entries from the original main.dol. Each case
runs from its entry to the next case's start in address order. The
table points to 213 distinct cases, and **37** of them call `func_80112FDC`
(the game-data getter). That includes every case that calls
`func_80113000`. No case reads `lbl_803491CC` directly.

These names are for the game-data getters that the cases use. "+X" is the
offset from the game-data pointer:

| getter | returns | likely meaning |
|---|---|---|
| `func_801130BC` | +0x50 | item container A (`func_8004FD68` count, `func_8004FDA0` add/remove, `func_8004FCC0`) |
| `func_801130F0` | +0x14A8 | container, called through its function table |
| `func_801130E8` | +0x14D0 | container, called through its function table |
| `func_80113128` | +0x1550 | container (`func_8005774C`) |
| `func_80112FF4` | +0x118C8 | unknown |
| `func_801130D0` / `func_801130DC` | +0x1119C / +0x111BC | containers |
| `func_80113000` | +0x11A14 | **gold** {+0x4 value, +0x8 max, +0xC min} |
| `func_801130C4` | +0x11B80 | object with fields +0x144, +0x148 |
| `func_80113078` | +0x12078 | **flags/variables**: bitsets at +0x2C, +0xC4, +0x31C; int array at +0x11C |
| `func_80113178` | +0x123D0 | unknown (`func_8008878C`) |
| `func_8000DC24(id)` | +0x124C4 + (slot−1)×0x124 | per-character record (see 0x7F/0x80/0x84) |
| `func_80113084(i)` | +0x14AF0 + i×0x20 | small 0x20-byte records |
| `func_8011309C` | word at +0x27E54 | unknown |
| `func_8011319C` | +0x27E60 | animal slot block (1.5) |
| `func_801130F8(i)` / `func_80113110(i)` | +0x29F84 / +0x29C78 + i×0xC | lists of 3-float positions |
| `func_801130A8(i)` | word at +0x2A290 + i×4 | unknown int array |

All 37 cases. "a0", "a1" are script arguments (`func_80112D34(args, n)`).
"push" means the case returns a value to the script (`func_80112Bxx`/`Cxx`/`D08`).

| cmd | RAM | description |
|---|---|---|
| 0x03 | 0x8010C6E8 | Large case (247 instructions). Calls many systems, including the animal slot block and several game-data parts. Probably scene/day setup. **Unclear.** |
| 0x2C | 0x8010D5A8 | Takes a0. If a0 is −1..2 or 0x52 it calls `func_8017767C(g_system, 4, 0)`, otherwise `func_8017775C(g_system, 6, a0, 0)`. Then it copies position entry 0 from +0x29C78/+0x29F84. Probably a map change or warp. **Unclear.** |
| 0x4F | 0x8010E168 | Looks up item a0's category (`lbl_80282DF8`, 0x24 per entry) and adds it to the matching container (+0x14A8, +0x14D0, +0x111BC, +0x1119C, +0x1550). Push success. |
| 0x51 | 0x8010E35C | Push word +0x144 of +0x11B80. |
| 0x52 | 0x8010E378 | Push `func_8014674C(word +0x148 of +0x11B80)`. |
| 0x53 | 0x8010E398 | Push the count of item a0 in container +0x50. |
| 0x55 | 0x8010E3D8 | Find the first non-empty entry in container +0x14A8, remove it, push it. |
| 0x56 | 0x8010E468 | Uses +0x11B80 (+0x144/+0x148) and spawns or updates objects. **Unclear.** |
| 0x67 | 0x8010ECFC | Push word [+0x2A290 + a0×4]. |
| 0x7C | 0x8010F4C8 | Mostly `lbl_803491EC` calls. Ends by pushing word +0x27E54. **Unclear.** |
| 0x7F | 0x8010F650 | Character a0: add a1 to byte **+0xF**, clamped to **0–100**, then recalculate (`func_80078174`). |
| 0x80 | 0x8010F690 | Character a0: push `func_80077798(record, 0)`, a value calculated from the record. |
| 0x82 | 0x8010F6C8 | `func_80151FE0(+0x14AF0 record[map(a0)], clamp(a1, −128..127))`. |
| 0x83 | 0x8010F728 | Push byte +0x1D of +0x14AF0 record[map(a0)]. |
| 0x84 | 0x8010F760 | Character a0: push byte **+0x24** of the record. |
| 0x89 | 0x8010F9FC | Animal slot a0 (0x31–0x40): push a category code 0–9 from its type field, or −1 (see 2.1). |
| 0x8A | 0x8010FB18 | Animal slot a0: push field **+0xC** of the slot record. There is no null check. |
| 0x8B | 0x8010FB4C | Push `func_8008878C(+0x123D0, a0)`. |
| 0x93 | 0x8010FECC | Variable: `int[+0x12078+0x11C + a0×4] = a1`. |
| 0x94 | 0x8010FF08 | Flag a0 in bitset +0x12078+0xC4: set if a1 != 0, else clear. |
| 0x95 | 0x8010FF5C | Push variable `int[+0x12078+0x11C + a0×4]`. |
| 0x96 | 0x8010FF90 | Push whether flag a0 in bitset +0x12078+0xC4 is set. |
| 0xA0 | 0x80110164 | Large case (337 instructions): positions and vector math using +0x29C78/+0x29F84. Probably camera or player placement. **Unclear.** |
| **0xC1** | 0x801115D8 | **Gold += a0, clamped** (section 1). Calls `func_8012A52C(lbl_803491E4, 0xCD, 0)` when a0 != 0. |
| **0xC2** | 0x80111614 | **Push current gold** (word +0x11A14+0x4). |
| 0xC5 | 0x801116C4 | Large case (423 instructions): tests +0x12078 flags and reads byte +0x12 of many character records. **Unclear.** |
| 0xCA | 0x80111E70 | Flag a0 in bitset +0x12078+0x31C: set if a1 != 0, else clear. |
| 0xCB | 0x80111EC0 | Push whether flag a0 in bitset +0x12078+0x31C is set. |
| 0xCD | 0x80111F2C | Under conditions involving `lbl_803491BC`, sets flags in bitset +0x12078+0x2C. **Partly unclear.** |
| 0xCE | 0x80111FE4 | `lbl_8034916C` calls plus +0x11B80 and +0x27E54. **Unclear.** |
| 0xD2 | 0x80112464 | Push `func_8004FCC0(+0x50, a0, a1)`. Probably "has a1 of item a0". |
| 0xD3 | 0x801124B0 | Push `func_8004FDA0(+0x50, a0, a1, −1)`. Probably "add a1 of item a0". |
| 0xD4 | 0x80112500 | Add item a0 ×a1 to container +0x14D0, push result. |
| 0xD5 | 0x8011255C | Count of a0 in +0x50 plus count in +0x14D0. Shows 0xC6 − total (space left?). |
| 0xD8 | 0x80112654 | Push the count of item a0 in container +0x14D0. |
| 0xD9 | 0x80112690 | Shows (count of a0 in +0x50) + 1. |
| 0xDC | 0x80112764 | `func_8004FDA0(+0x50, a0, −a1, −1)`. Probably "remove a1 of item a0". |

### 2.1 Command 0x89 category codes

For slots 0x31–0x38, field +0x0 (0–0x1B) goes through the nested table
`lbl_802BFF88` (RAM 0x802BFF88). Field values 0–0x17 cycle through 0,0,1,1,2,2,…;
0x18 → 3, 0x19 and 0x1A → 4, 0x1B → 5. For slots 0x39–0x40, field +0x4:
0–1 → 6, 2 → 7, 3 → 8, 4 → 9. Anything else gives −1. I haven't matched these
codes to species. The model table suggests cow, sheep, goat and horse, but
the ID numbering may differ (see open questions).

### 2.2 Per-character records (0x7F / 0x80 / 0x84)

`func_8000DC24(game-data, id)` → `func_8007846C(id)` → `func_8007962C`
finds the id in the 33-pair table `lbl_8024F594` (RAM 0x8024F594). Ids
**0x01–0x1F, 0x23, 0x24** map to slots 1–33. Any other id returns 0, which
means no record.

Record = game-data + 0x124C4 + (slot−1) × 0x124.

- byte +0xF: a value from 0 to 100. Command 0x7F adds to it with clamping.
  This looks like friendship or hearts, but that isn't confirmed.
- `func_80077798(record, n)` looks up n among 63 selectors and calls the
  matching function. Command 0x80 uses n = 0.

## 3. Dog (feeding, playing) and cow milking

**I found no command in this table that handles the dog or milking.**

- No case calls the dog object's code (main.dol 0x800A5D5C–0x800A7CA0,
  method table `lbl_802B2F3C`).
- The only animal-specific commands are **0x89** (category) and **0x8A**
  (slot field +0xC). They work on any animal in slots 0x31–0x40 and read
  only. Nothing writes animal slot fields from a script command.
- The dog's model IDs (0x27/0x28) have no entry in the per-character table
  in 2.2. So 0x7F/0x80/0x84 can't change the dog through those ids. That's
  only if the model IDs and the character-table IDs are the same numbering,
  which isn't confirmed.
- So dog affection and milk are probably updated outside the script
  commands: by the dog object or another main.dol system, or by the rels.
  The rels reference `lbl_803491CC` 546 times (wlp0: 114, wlp1: 214,
  wlp2: 218). The rels never call the gold routine, but they could still
  change the game-data object some other way.

## 4. Open questions

Each one needs a Dolphin check unless it says otherwise.

1. ~~**Gold max and min.**~~ **Resolved:** maximum 99,999,999
   (`0x05F5E0FF`), minimum 0. See section 1.4. Still open: which code
   writes these limits. A Dolphin write breakpoint on +0x8, set while
   loading a save or starting a new game, would show it.
2. **Where else gold changes.** The script command is the only *call* to
   `func_80113234`, but shops, shipping and so on could write +0x4 directly.
   Set a write breakpoint on the gold value and sell, buy and ship. If it
   stops in a rel, note the module and its load address.
3. **What `func_8012A52C(lbl_803491E4, 0xCD, 0)` does.** It runs after a
   non-zero gold change. My guess is a sound effect or the money display.
4. **Dog affection.** Find the dog's value in RAM: feed or play, sleep, and
   search for the change. It may be inside the game-data object. A write
   breakpoint on it then shows which code updates it daily and which code
   checks feeding and playing.
5. **Cow milk.** Same method on a cow. Watch the slot record at game-data +
   0x27E64 + n×0x1B4 (and the second array at +0x28C04) across days,
   especially +0x0, +0x4 and +0xC.
6. **Animal type codes.** Match the 0x89 category codes (0–9) to species by
   checking a known cow, sheep, goat and so on in Dolphin.
7. **Are the ID numberings the same?** Do the model-loader IDs (dog 0x27/0x28,
   goat 0x19/0x1A), the character-table IDs (0x01–0x24) and the animal slot
   IDs (0x31–0x40) all number the same things? Statically they overlap, so
   they may be different lists.
8. **Per-character byte +0xF (0–100).** Change it in Dolphin for a known
   villager and see whether their heart level changes.
9. **The large cases (0x03, 0x2C, 0x56, 0x7C, 0xA0, 0xC5, 0xCD, 0xCE).**
   Their purpose is unclear. Static reading could narrow these down without
   Dolphin, but it would take a while.
10. **Which script files use command 0xC1.** The scripts are game data on
    the disc, not in this repo. Finding which events give or take gold means
    extracting the disc's script files.

## 5. How these were checked

The scripts are in `tools/analysis/`. See its README for setup, inputs and
example runs. They only read files, never write. Every result in this note
can be rerun from a clean clone with the four original binaries in `orig/`.

- `asmq.py`: searches the main.dol asm (`asm/main/game/*.s`) by label,
  prints a label's body, or lists callers. It handles the repo's CRLF line endings.
- `xref.py`: scans the original main.dol for branch, pointer and
  `lis`/`addi` references, and parses the relocation tables of the three
  rels (sections 1.2, 1.5).
- `dolread.py`: reads a 32-bit word by RAM address and gives its section
  and file offset (section 1.3).
- `cases.py`: splits `func_8010C604` into cases using the jump table in the
  original main.dol (section 2).

## 6. Item description moved to R (Gecko, tested)

Codes: `cheats/item-description-on-r.txt` (GYWEE9 US, main.dol sha1
1ccfd9df…2374). All addresses are in main.dol.

- **How the A press shows it.** In idle/walk, A looks up an action in
  `lbl_80292A78[heldClass*0xAC + targetType]` (`func_8004ED60`,
  0x8004EE3C). With an item held and no usable target, the action is 24.
  Case 24 (0x80043C24 in `func_80043120`, 0x8004919C in `func_80048A5C`)
  stores file 0x3B (`@itemdoc`) at controller +0x14C0 and the item ID at
  +0x14C4, then sets state 42. State 42's enter method (0x80034CAC) opens
  the message (`func_801020E4`, 0x80034D30).
- **R.** R is a half-press of the analog trigger, bit 0x02000000 in the
  pad word at `lbl_80341574`+8 (set at 0x8021369C). The R handlers
  (0x800430A8 in `func_80042DFC`, 0x800489DC in `func_800488B0`) whistle
  only with empty hands. With an item held they did nothing.
- **What the codes do.** Two 32-bit writes point jump-table entry 24
  (0x802A74D0, 0x802A7768) at the "no action" default, which turns off
  the description on A. Two C2 hooks replace the held-item `bne` at
  0x800430BC (was 4082004C) and 0x800489F0 (was 4082001C). With an item
  held they set up the same message and enter state 42.
- **Tested.** With an item held, R shows the item's description. With
  empty hands, R still whistles. A no longer shows the description.
- **Offset check.** The `beq +0x38` in each hook lands on the C2
  branch-back slot (word 15 of 16), which returns to hook+4 (0x800430C0 /
  0x800489F4). This matches the tested code. `+0x3C` would land past the
  end of the block.
- **Open issues.** The watering-can description may show the wrong water
  amount: the R hook skips the `func_80102300` call the A path made. Not
  checked in game. The `func_800310A4(this,1)` call and animation-rate
  reset are also skipped; no problems seen.

## 7. Input: A-button gate

All findings are in **main.dol** (sha1 matches `hmawl_us_r0.sha1`). File offsets
come from the second column of the asm. RELs are covered at the end.

### Pad struct and per-frame update

| Item | Address (file offset) | Confidence | Evidence |
|---|---|---|---|
| Pad control block | `lbl_80341430` | high | Base for both record sets below (sysdolphin.s) |
| Master records, 4 × 0x44 | 0x80341464 (= +0x34) | high | `func_80213B44` reads them from r4 = base+0x34 |
| **Copy records the game reads**, 4 × 0x44, pad 0 first | **0x80341574** (= +0x144) | high | `func_80213B44` writes them from r5 = base+0x144, ctr 4, stride 0x44; 48 game-code refs in main.dol |
| Field +0x00 | held buttons | high | Input to the xor/and in `func_802136C8` |
| Field +0x04 | previous held | high | Same |
| **Field +0x08** | **trigger (newly pressed) = held & (held ^ prev)** | high | `func_802136C8`, 0x80213A94–0x80213B08 |
| Field +0x0C | repeat | medium | Repeat counter logic beside it, +0x14 |
| Field +0x10 | release = prev & (prev ^ held) | high | Same block |
| **A mask** | **0x100** | high | Dolphin SDK `PAD_BUTTON_A`; most common mask tested on +0x08 (8 sites); `func_80044F70`'s 0x100 branch sets up the item-description message, matching section 6's A path |
| Other bits | B 0x200, Z 0x10, Start 0x1000, R-analog 0x02000000 (set at 0x8021369C), L-analog probably 0x01000000 | high / high / high / high / low | SDK values; section 6; 0x01000000 is assumed by symmetry |
| Frame loop | `func_8000AC34`, `bl func_80213CE4` at 0x8000AD38 | high | One call per loop pass, after the frame-buffer update |
| Pad update | `func_80213CE4` (0x80213CE4, file 0x210A24): `bl func_80212720` (hardware read, medium: calls func_802143A0/func_801C0824, not confirmed as PADRead) → `bl func_802136C8` (renew master) → `bl func_80213B44` (copy to 0x80341574) at 0x80213CF8 | high | asm/main/libraries/sysdolphin.s |

**Pad 0 A-pressed-this-frame** = `(*(u32*)0x8034157C & 0x100) != 0`. A is held
when `*(u32*)0x80341574 & 0x100`.

### Sites that test A (main.dol)

All sites load the pad pointer with `lis/addi lbl_80341574`, do an `lwz` on the
field, then `rlwinm.`/`andi.` and branch. "On A" lists the calls inside the
taken block. Blocks over 60 instructions were cut short, so those lists may be
incomplete.

| Test addr (file) | Function | Field & mask | Taken block | Calls on A | Confidence |
|---|---|---|---|---|---|
| 0x80033B00 (0x30840) | func_8003350C | +8 & 0x100 | 0x80033B08–0x80033B20 | func_80031D7C; then `stw 0x58(r5)`, `b` 0x80033BB4 | high (test); context unknown |
| 0x80033F48 (0x30C88) | func_80033E1C | +8 & 0x310 (A\|B\|Z) | 0x80033F50–0x80033FF4 | func_80085EB0, func_80085884, func_80085998, func_801B8048, func_801B8760, func_80030E18, func_80141028, func_8019E280 (list cut short) | high (test); fires on any of A/B/Z, not A alone |
| 0x8003743C (0x3417C) | func_800372AC | **+0 (held)** & 0x100 | 0x80037444–0x80037494 | func_80083378, func_800107A4; stores 0x128(r29), 0x14AC(r29) | high (test); true every frame A is **held** |
| 0x80043778 (0x404B8) | func_80043754 | +8 & 0x100 | 0x80043780–0x80044584 | jump table (`bctr`); func_8004579C, func_80011680 (×n); `stw 0x1388(r31)` | high (test); medium that this is the field action dispatch |
| 0x800450C8 (0x41E08) | func_80044F70 | +8 & 0x100 | 0x800450D0–0x80045248 | func_80031D7C, func_80011680; `stw 0x14C0/0x14C4(r29)` | high; item-description path (section 6) |
| 0x800474A8 (0x441E8) | func_8004748C | +8 & 0x100 | 0x800474B0–0x80047838 | func_80011680, func_800D6C98 | high (test); context unknown |
| 0x80048490 (0x451D0) | func_80048470 | +8 & 0x100 | 0x80048498–0x800484C4 | func_8017295C, func_80031D7C ×2 | high (test); context unknown |
| 0x80048D98 (0x45AD8) | func_80048D7C | +8 & 0x100 | 0x80048DA0–0x800496C8 | jump table (`bctr`); func_80011680 | high (test); context unknown |
| 0x8010553C (0x10227C) | func_80105530 | +8 & 0x100 | 0x80105544–0x80105564 | func_8012A52C; `stw 0x4(r30)` | high (test); code_800F3228.s, likely menu/UI (low) |
| 0x801060B0 (0x102DF0) | func_80106088 | +8 & 0x100 | 0x801060B8–0x801060D8 | func_8012A52C, func_80106EA8 | high (test); same file, likely menu/UI (low) |

No function here has a decomp name; all are `func_XXXXXXXX`.

### Per-frame vs A-only

- **Every frame, whatever the input:** `func_8000AC34` → `func_80213CE4` →
  `func_80212720`, `func_802136C8`, `func_80213B44`. High.
- **Only on A**, reached through the taken branch: the callees listed above.
  The same callees can also be reached from other paths. For example,
  func_80011680 and func_80031D7C have several callers, so they are
  **not** good A-only hook points by themselves. Medium.
- **The containing functions** (func_8003350C … func_80106088) are probably
  per-frame update handlers for one game state each, called while that state
  is active. Not confirmed: their callers were not traced. Low.
- **func_800372AC** tests *held*. Its block runs on every frame A is held,
  not once per press.

### Gaps

- **Indirect tests are not covered.** The pointer gets passed to helpers
  (func_8023DCE0 r3 ×3, func_8004EA50 r4 from 0x800450B0, func_80084BDC r4,
  func_8017A2FC). A tests inside those were not scanned. func_8004ED60's A
  action lookup at 0x8004EE3C (section 6) is reached this way.
- **RELs.**
  - wlp0.rel: 7 refs, all Start (+8 & 0x1000).
  - wlp1.rel: 34 refs that keep +8/+0xC in registers across calls. No direct
    A test matched; unresolved.
  - wlp2.rel: 1 ref, no A test.

### Dolphin checks

| Check | How | Confirms |
|---|---|---|
| Mask and field | Memory watch on 0x8034157C (u32) and press A | Bit 0x100 is set for exactly one frame per press |
| Writer | Write breakpoint on 0x8034157C | Hits inside func_80213B44 (copy loop, ~0x80213B60) once per frame |
| Readers | Read breakpoint on 0x8034157C | Lists live A/trigger readers, including indirect ones and wlp1 |
| Each site | Code breakpoint at the test addresses above, then look at r0 after the `lwz` | Which sites run in which game state |
| Logger gate | Hook after 0x80213CF8 (return of `bl func_80213B44`) or at 0x80213CFC, and test `lwz r0,0x8034157C; andi. r0,r0,0x100` | Gate fires once per A press, every game state |

### 7.1 Gecko C2: A-press counter (main.dol, not tested in Dolphin)

**Hook point.** 0x80213CFC, file offset 0x210A3C in main.dol (sha1
1ccfd9df…22374, matches `hmawl_us_r0.sha1`). Original word `80010014` =
`lwz r0, 0x14(r1)`. That is the first epilogue instruction of `func_80213CE4`,
right after `bl func_80213B44` at 0x80213CF8 (`4BFFFE4D`), so the pad copy at
0x80341574 is already filled for this frame. High.

- `func_80213CE4` has one caller: `bl` at 0x8000AD38 (`48208FAD`, file
  0x7A78) in the main loop, followed by `b func_8000AC34`. The caller does
  not read r3, CR0, r11 or r12 after the call. High.
- At the hook, r0 is dead (the original instruction overwrites it) and r3–r12
  and CR0 are volatile.

**Free RAM: 0x80000A00 (counter), 0x80000A04 (last LR).** This is the 0xA00
exception-vector slot (0x100 bytes), which the OS never installs. Medium-high.

- `OSExceptionInit` (0x801B11B8, asm/main/libraries/dolphin/os.s) copies the
  0x98-byte `OSExceptionVector` stub (0x801B1490–0x801B1528) to the 15 slots
  listed at 0x802DFDAC (`lbl_802DFC88`+0x124): 0x100–0x900, 0xC00, 0xD00,
  0xF00, 0x1300, 0x1400, 0x1700. The loop bound is `cmplwi r0, 0xf` at 0x801B13CC.
- 0xA00, 0xB00, 0xE00, 0x1000–0x1200, 0x1500 and 0x1600 are never written by it.
- The 0x900 stub ends at 0x80000997.
- No static reference to 0x80000A00–0x80000AFF exists in main.dol or
  wlp0/1/2.rel. The scan covered:
  - lis + any D-form load/store/addi/ori;
  - raw 32-bit words in every section;
  - REL relocations against module 0;
  - absolute `(r0)` D-form accesses (one hit, 0x8025E440, is in a data
    table, not code).
- Dolphin's Gecko handler uses 0x80001800–0x80003000, so it doesn't overlap.
- Not ruled out statically: a computed-pointer write, e.g. a memset of
  low memory. Dolphin check: write breakpoint on 0x80000A00–0x80000A07 with
  the code off; it should never hit.
- Ruled out: dead code. The DOL is dead-stripped; the only function
  with no reference outside extab is `__dt__26__partial_array_destructorFv`
  (C++ unwind), so no dead code is usable for storage.

**Code (11 lines, 21 instructions + Gecko return slot).**

```
$A press counter (pad 0)
C2213CFC 0000000B
9421FFE0 91610008
9181000C 7D800026
91810010 3D608034
818B157C 718C0100
4182001C 3D608000
818B0A00 398C0001
918B0A00 7D8802A6
918B0A04 81810010
7D8FF120 8181000C
81610008 38210020
80010014 00000000
```

```
stwu  r1,-0x20(r1)      ; save r11, r12, CR
stw   r11,0x8(r1)
stw   r12,0xC(r1)
mfcr  r12
stw   r12,0x10(r1)
lis   r11,0x8034
lwz   r12,0x157C(r11)   ; pad 0 newly pressed, 0x8034157C
andi. r12,r12,0x100     ; A
beq   skip
lis   r11,0x8000
lwz   r12,0xA00(r11)    ; counter += 1
addi  r12,r12,1
stw   r12,0xA00(r11)
mflr  r12
stw   r12,0xA04(r11)    ; last LR
skip:
lwz   r12,0x10(r1)
mtcrf 0xFF,r12
lwz   r12,0xC(r1)
lwz   r11,0x8(r1)
addi  r1,r1,0x20
lwz   r0,0x14(r1)       ; original instruction
                        ; Gecko appends b 0x80213D00
```

Assembled with `powerpc-linux-gnu-as -mregnames -mgekko` and checked with objdump.

- **Patch.** 0x80213CFC goes from `80010014` to a `b` into the Gecko code list.
  The target is set by the handler at run time.
- **Writes.** When A is not pressed, the only writes are to the code's own
  stack frame below r1. The counter and slot are written only on A.
- **Last-LR caveat.** The hook is entered by `b`, so LR there is always
  0x80213CFC (the return from `bl func_80213B44`). The function's own
  return address, 0x14(r1), is always 0x8000AD3C, since there is one caller.
  The slot proves the hook ran; it can't identify A handlers. To learn which
  functions run on A, the hook must sit inside those handlers, e.g. the
  section 7 test sites.

**Test plan (Dolphin).**

1. Code off: set a write breakpoint on 0x80000A00 (8 bytes), boot to the
   field, and play a minute. No hit means the slot is free.
2. Code on: Memory view at 0x80000A00. On the title screen and in the field,
   each A press adds exactly 1. Holding A adds only 1. B, Start and the stick
   add 0.
3. 0x80000A04 reads 80213CFC after the first press.
4. Code breakpoint at 0x80213CFC shows a `b` into 0x800018xx–0x80002FFF.
   Stepping through returns to 0x80213D00 with r0 = 8000AD3C and r1
   unchanged.
5. Normal play for a few minutes (menus, field, item use, a day change): no
   crash, no input lag, A acts as before.

### 7.2 Gecko C2: one A counter per test site (main.dol, not tested in Dolphin)

**Sites.** Each word was read from main.dol (sha1 1ccfd9df…22374, matches
`hmawl_us_r0.sha1`). Each is the site's test instruction, and the word after
it is `beq` (`4182xxxx`). High.

- **Safe to hook.** All 10 instructions are record-form `rlwinm.`/`andi.`
  on r0/r3/r4/r27, with no PC-relative forms and no use of r1, r11 or r12.
- **Not branch targets.** A scan of every `b`/`bc` in main.dol's text found
  none pointing at a site or at site+4.
- **Source register holds the pad word.** Each test register holds
  `lbl_80341574+8`. At 0x800450C8, r27 is loaded at 0x800450B4. At 0x80033B00,
  r4 is set to `lbl_80341574` at 0x80033AE8.
- **Correction to section 7.** The 0x80033B00 site is in the function
  starting at 0x80033AE0 (`lbl_80033AE0`, `stwu r1,-0x50(r1)`), not in
  `func_8003350C`.

| # | Site | File off | Original | Asm | Counter |
|---|---|---|---|---|---|
| 0 | 0x80033B00 | 0x30840 | `540005EF` | `rlwinm. r0,r0,0,23,23` | 0x80000A10 |
| 1 | 0x80033F48 | 0x30C88 | `70000310` | `andi. r0,r0,0x310` | 0x80000A14 |
| 2 | 0x8003743C | 0x3417C | `540005EF` | `rlwinm. r0,r0,0,23,23` (held word) | 0x80000A18 |
| 3 | 0x80043778 | 0x404B8 | `546005EF` | `rlwinm. r0,r3,0,23,23` | 0x80000A1C |
| 4 | 0x800450C8 | 0x41E08 | `576005EF` | `rlwinm. r0,r27,0,23,23` | 0x80000A20 |
| 5 | 0x800474A8 | 0x441E8 | `540005EF` | `rlwinm. r0,r0,0,23,23` | 0x80000A24 |
| 6 | 0x80048490 | 0x451D0 | `540005EF` | `rlwinm. r0,r0,0,23,23` | 0x80000A28 |
| 7 | 0x80048D98 | 0x45AD8 | `546005EF` | `rlwinm. r0,r3,0,23,23` | 0x80000A2C |
| 8 | 0x8010553C | 0x10227C | `546005EF` | `rlwinm. r0,r3,0,23,23` | 0x80000A30 |
| 9 | 0x801060B0 | 0x102DF0 | `548005EF` | `rlwinm. r0,r4,0,23,23` | 0x80000A34 |

**Counters.** 0x80000A10–0x80000A37 are in the unused 0xA00 vector slot from
7.1, the same slot as the working 0x80000A00 counter. 0x80000A08/0x0C are
left unused. Medium-high.

- Rescanned 0x80000A08–0x80000A3F with the 7.1 method. Every address had
  zero hits for:
  - lis + D-form;
  - raw words in every main.dol section;
  - REL relocations against module 0;
  - absolute `(r0)` D-form in main.dol and the RELs;
  - raw words in the RELs.
- The range is not in any OS-filled range. `OSExceptionInit` fills only
  the 15 listed slots; 0x900 ends at 0x80000997 and 0xA00 is never written.

**Hook body (same for every site; only the counter offset and the last
instruction change).** 19 instructions + Gecko return = 10 lines per site.

- The original instruction runs last, after r1, r11, r12 and all CR fields
  are restored. So r0 and CR0 come out exactly as the original would leave
  them.
- XER is untouched.
- The counter goes up when the **site runs in a frame where pad-0 A was
  newly pressed**, whatever the site's own test does:
  - site 1 also passes on B or Z, but only A is counted;
  - site 2 tests held, but only new-press frames are counted.
- A site that runs more than once per frame (e.g. once per object) would
  add more than 1 per press. That would itself be a finding.

```
stwu r1,-0x20(r1) ; stw r11,8(r1) ; stw r12,0xC(r1) ; mfcr r12 ; stw r12,0x10(r1)
lis r11,0x8034 ; lwz r12,0x157C(r11) ; andi. r12,r12,0x100 ; beq skip
lis r11,0x8000 ; lwz r12,CTR(r11) ; addi r12,r12,1 ; stw r12,CTR(r11)
skip: lwz r12,0x10(r1) ; mtcrf 0xFF,r12 ; lwz r12,0xC(r1) ; lwz r11,8(r1) ; addi r1,r1,0x20
<original instruction>                ; Gecko appends b site+4
```

Assembled per site with `powerpc-linux-gnu-as -mregnames -mgekko`. The
script asserts that each hook's last word equals the original word read from
main.dol.

- **Patch.** Each site goes from its original word to a `b` into the Gecko
  code list.
- **Size.** 110 lines (880 bytes). With 7.1 enabled too, the total is 976
  bytes, well inside Dolphin's code-list area.

```
$A site counters (pad 0, 10 sites) [hmawl notes 7.2]
C2033B00 0000000A
9421FFE0 91610008
9181000C 7D800026
91810010 3D608034
818B157C 718C0100
41820014 3D608000
818B0A10 398C0001
918B0A10 81810010
7D8FF120 8181000C
81610008 38210020
540005EF 00000000
C2033F48 0000000A
9421FFE0 91610008
9181000C 7D800026
91810010 3D608034
818B157C 718C0100
41820014 3D608000
818B0A14 398C0001
918B0A14 81810010
7D8FF120 8181000C
81610008 38210020
70000310 00000000
C203743C 0000000A
9421FFE0 91610008
9181000C 7D800026
91810010 3D608034
818B157C 718C0100
41820014 3D608000
818B0A18 398C0001
918B0A18 81810010
7D8FF120 8181000C
81610008 38210020
540005EF 00000000
C2043778 0000000A
9421FFE0 91610008
9181000C 7D800026
91810010 3D608034
818B157C 718C0100
41820014 3D608000
818B0A1C 398C0001
918B0A1C 81810010
7D8FF120 8181000C
81610008 38210020
546005EF 00000000
C20450C8 0000000A
9421FFE0 91610008
9181000C 7D800026
91810010 3D608034
818B157C 718C0100
41820014 3D608000
818B0A20 398C0001
918B0A20 81810010
7D8FF120 8181000C
81610008 38210020
576005EF 00000000
C20474A8 0000000A
9421FFE0 91610008
9181000C 7D800026
91810010 3D608034
818B157C 718C0100
41820014 3D608000
818B0A24 398C0001
918B0A24 81810010
7D8FF120 8181000C
81610008 38210020
540005EF 00000000
C2048490 0000000A
9421FFE0 91610008
9181000C 7D800026
91810010 3D608034
818B157C 718C0100
41820014 3D608000
818B0A28 398C0001
918B0A28 81810010
7D8FF120 8181000C
81610008 38210020
540005EF 00000000
C2048D98 0000000A
9421FFE0 91610008
9181000C 7D800026
91810010 3D608034
818B157C 718C0100
41820014 3D608000
818B0A2C 398C0001
918B0A2C 81810010
7D8FF120 8181000C
81610008 38210020
546005EF 00000000
C210553C 0000000A
9421FFE0 91610008
9181000C 7D800026
91810010 3D608034
818B157C 718C0100
41820014 3D608000
818B0A30 398C0001
918B0A30 81810010
7D8FF120 8181000C
81610008 38210020
546005EF 00000000
C21060B0 0000000A
9421FFE0 91610008
9181000C 7D800026
91810010 3D608034
818B157C 718C0100
41820014 3D608000
818B0A34 398C0001
918B0A34 81810010
7D8FF120 8181000C
81610008 38210020
548005EF 00000000
```

**Test plan (Dolphin).**

1. Code off: set a write breakpoint on 0x80000A10–0x80000A37 (0x28 bytes)
   and play the title screen, field, menus and item use for a few minutes. It
   should never hit, and the words should stay as they were.
2. Code on (7.1 can stay on as a reference): Memory view at 0x80000A00.
   - Press A once in each state: title, field idle, field next to an
     object or NPC, menu, item select.
   - After each press, the 0x80000A00 total should go up by 1. The site
     counters that changed show which sites ran in that state.
   - Without pressing anything, nothing should change. Holding A should not
     keep counting.
   - A site counter that rises by more than 1 per press means that site
     runs more than once per frame. Note it.
3. Breakpoint at each site address: you should see the `b` into the code
   list. Step to the site+4 `beq`. CR0 and r0 should match what the original
   instruction gives (compare with the code off).
4. Normal play for a few minutes with A-driven actions (talk, pick up, menus,
   item description): behaviour should be the same as with the code off.

### 7.3 Cow milking path (main.dol, static only, not tested in Dolphin)

All addresses are in main.dol (sha1 1ccfd9df…22374, matches
`hmawl_us_r0.sha1`). The file offsets come from `dolread.py`. "Msg" means
the 0x34-byte message built by `func_8004579C` and sent by
`func_80011680`:

| Offset | Field |
|---|---|
| +0x0 | sender id |
| +0x4 | type |
| +0x8 | arg |
| +0xC | held item |
| +0x10 | target id |

`func_80011680` looks the target up and calls its virtual +0xC, which
forwards to the current state's slot-4 handler.

**State tables are built at boot.** The player state table
`lbl_802A3AA8` (0x3C per state, five ptmfs: enter, +0xC update, +0x18,
+0x24 per-frame, +0x30 message) is zero in the DOL. The static
initializer `lbl_800388B4` fills it. The animal table `lbl_802B9008`
(filled by `lbl_800D0F9C`) and the field-item table `lbl_80297608`
(filled by `lbl_80009938`) work the same way. I recovered the
state→function lists by emulating those initializers (straight-line
`lwz`/`stw`; script in my scratchpad, not committed). High.

#### Chain on a milking press

| # | Address | What happens | Evidence | Conf. |
|---|---|---|---|---|
| 1 | `func_80043120` (state 1, slot +0x24) | Field A handler. Site 3 (0x80043778) tests A, then `bctr` through `lbl_802A7470[r24]`. | State-table emulation: state 1 slot 3 = 0x80043120. | High |
| 2 | `func_8004ED60` → 0x8004EE3C | r24 = `lbl_80292A78[heldClass*0xAC + targetType]`. Held class comes from `func_8004EFDC`: item 0x4F6/0x4F7 → class 9 (0x8004F140). Row 9, target 3 = **0x10** (0x80293087, file 0x290087). Row 0xA (items 0x4F8/0x4F9) gives 0x10 for target 0xF. | Table bytes. | High for the table; **medium** that 0x4F6/7 is the milker and target 3 a cow |
| 3 | 0x800439D4 (case 0x10) | `func_8004579C(msg, target, player, type=1, arg=0, item=r26)`, `func_80011680`. If accepted, `func_80030F7C` (only touches watering-can water). Player → **state 0x94**. | 0x800439E8 `38C00001`, 0x80043A1C `3BC00094`. | High |
| 4 | `lbl_800D04F8` | Animal message handler (slot 4 of animal states 0–9 and 0xD–0xF; 13 vtable copies). Type 1 → 0x800D06A4: held 0x4F6/0x4F7 → `func_800D0AC4` (0x800D06BC `cmpwi 0x4f6`). | Jump table `lbl_802B9DF8`. | Medium (cow vs other livestock unconfirmed) |
| 5 | `func_800D0AC4` | If arg == 0 (true here), the animal goes to **state 0x1E** (0x800D0AE4 `li r4,0x1e`). Other branches are refusals: emote via `func_800CB644` + state 0x2A. | | Medium |
| 6 | Player state 0x94 (enter 0x80036ADC, per-frame 0x80036BA0) | Plays anim 0x2E (0x80036B60). When it ends (`func_8017D7EC`), sends type 0x1C to the cow, then state+1 = 0x95. | | High |
| 7 | Animal state 0x1E (msg 0x800D0C64) → 0x1F (enter 0x800CF87C, per-frame 0x800CF8E0) | On 0x1C, advances to 0x1F, which plays the cow's milking anim. When it ends (0x800CF908 `beq`), it builds the payload {kind, count} and sends **type 0x1C, arg = &payload** to the player (0x800CF9CC). | | High (structure) |
| 8 | Player state 0x95 (msg 0x800385F8) | On 0x1C: kind → player+0x14A4, count → player+0x14A8. Sound 0x119 for category-5 tools (0x118 otherwise), then state 0x96. | 0x80038644/0x8003864C. | High |
| 9 | **Player state 0x96: the drop loop** (enter 0x80036C70, per-frame 0x80036CC8) | See below. | | High (structure) |

**State 0x96 in detail.**

- Enter plays anim **0x2F** (0x80036C78) and zeroes the drop index +0x1368.
- Each time anim 0x2F ends (0x80036CF0 `beq`), the per-frame handler
  decrements the count +0x14A8.
- **If the count is now 0 and the hands are empty:** the last item goes
  into the hand (`stw` kind → controller+0x144 at 0x80036D24).
- **Otherwise:** one item is dropped:
  - the position comes from `func_800320F8(player, &pos, +0x4C, +0x58, index)`;
  - the index is incremented;
  - **`func_8000743C(lbl_803491F4, kind, map=+0x64, &pos, rot)`** spawns
    it (call at 0x80036D78).
- **When the count reaches 0:** it sends type 0x1C to the cow, plays anim
  0x32, stops sounds 0x118/0x119 and sets state 0 (0x80036E4C).
- **Otherwise:** it re-enters state 0x96 for the next item.

So **the per-item delay is one full playback of player anim 0x2F**, and
each milk except the last is a separate field object.

#### Kind, count and the spawn routine

- **Kind: `func_800C7F48(ai)`.**
  - It returns item **6** when a vcall on ai+0x124 returns ≤ 3. This
    looks like a low-condition fallback.
  - Otherwise it returns `base + ai+0x164`, where base is one of
    `lbl_80347518`/`1C`/`20`/`24` (sdata), picked by `func_800CBEAC`.
    That is probably milk size by heart/health level.
  - If the kind is 6, the count is forced to 1.
  - Medium: the exact item IDs are not resolved, because the bases are
    sdata words set at runtime.
- **Count: `func_800C8018(ai)`.** It picks 0x32–0x64 by comparing ai+0x88
  against `lbl_80347528`–`lbl_80347538`, then computes
  `ai+0x14C * pct / 100` with a threshold at 0x50. I only read its first
  branch. Medium.
- **Count cap: `func_80006B14(gamedata+0x27E58)`** = `max(0, 0x50 - list->count)`.
  At most 80 field items exist at once. Constant `38000050` at
  0x80006B18 (file 0x3858) and `20040050` at 0x80006B24 (file 0x3864).
  High for the maths, medium for the meaning.
- **Spawn: `func_8000743C`.**
  1. `func_80006EA4(gamedata+0x27E58, …)` adds a record (kind, map, pos,
     rot) to the field-item list.
  2. It allocates a 0x62-byte object (`func_8017A200`).
  3. The ctor `func_800079EC` builds a field-item object pointing at the
     record.
  4. `func_8017CD5C` adds it to the scene.
  - **No count field anywhere.** Each record holds one item.
  - High.

#### Pickup path

1. Empty hands + a ground item → action **0x17** (row 1 of `lbl_80292A78`).
2. Case 0x80043BCC/0x80043BE8 sends **type 0xA** (0x80043BF4) to the
   item. The player enters **state 0x83** (0x80043C10).
3. **Field-item message handler `lbl_800090E8`** (item state 0):
   - 0xA → item state 2 (0x800091C4);
   - 3 → reply **0x1D** with arg+0xC = `*(item+0xD0)` (the record's kind)
     to the sender, then item state 1.
4. Player state 0x83 (enter 0x80035C6C, anim 0xA) sends 0x1C to the item
   after 1 frame (0x80035CF0), then state 0x84.
5. Item state 2 (msg 0x80008ED4) → state 3 on 0x1C. State 3 enter
   (0x80008FB0) opens a message window (`func_801020E4`, file 0x33,
   msg 0x1D6). Purpose unclear.
6. **What the player gets:** the player's top-level receiver
   (`func_80031758`) handles 0x1D at **0x80031B3C**. It stores arg+0xC
   into the held-item word controller+0x144 (0x80031B44 `90030144`) and
   attaches the model.

The player holds exactly one item ID; there is no count. So "one pickup
collects all" cannot come from a constant change. Medium: I didn't
trace who sends type 3 to the item (probably state 0x84).

#### Values for the two goals

| Goal | Address (file) | Current | Effect if changed | Conf. |
|---|---|---|---|---|
| (a) per-item delay | 0x80036CF0 (0x33A30) | `4182017C` `beq` (wait for anim 0x2F) | `60000000` should drop one item per frame instead of one per anim cycle. | Medium (untested; anim 0x2F restarts every frame) |
| (a) per-item anim | 0x80036C78 (0x339B8) | `3880002F` anim id | A shorter anim id would shorten each cycle. No anim table was read. | Low |
| (a) player pre-anim | 0x80036B60 (0x338A0) | `3880002E` | Anim before the cow reacts (state 0x94). | Medium |
| (a) cow milking anim wait | 0x800CF908 (0xCC648) | `418200DC` | `60000000` would send {kind, count} on the first frame of state 0x1F. | Medium (untested) |
| (b) drop vs hand | 0x80036D08 (0x33A48) | `40820034` `bne` (count≠0 → drop) | The decision point. Only the last item can go in the hand. | High |
| (b) spawn call | 0x80036D78 (0x33AB8) | `4BFD06C5` `bl func_8000743C` | Hook point to redirect the count−1 extra items, e.g. to the rucksack or shipping. Needs a target routine I haven't found. | High (site) / open (target) |
| (b) field-item cap | 0x80006B18 / 0x80006B24 (0x3858/0x3864) | `0x50` | Caps the milk count per milking. Leave as is. | High |

#### Dolphin checks

| What to confirm | How |
|---|---|
| 0x4F6/7 is the milker and target type 3 is a cow | Code BP 0x800439D4 while milking: r24 should be 0x10. Also check `*(*(player+0x135C)+0x144)` (held item). |
| The cow handler | BP 0x800D0AC4: it hits once per milking. |
| Kind and count | BP 0x80038644. r4 points at {kind, count}: read the words at r4+0 and r4+4. |
| One spawn per milk | BP 0x80036D78: it should hit count−1 times. r4 = kind; r6/r7 = pos/rot. |
| What pickup gives | BP 0x80031B44 while picking up a milk: r0 = the item ID put in hand. |
| Patch (a) | Write `60000000` to 0x80036CF0 in Memory view and milk. All milk should appear within a few frames, with no softlock. |

### 7.4 Item containers ("rucksack" add) and a milk-to-container hook (main.dol, not tested)

All addresses are in main.dol (sha1 1ccfd9df…22374, matches
`hmawl_us_r0.sha1`). The file offsets come from `dolread.py`.

#### The add routine

The game data `lbl_803491CC` holds several item containers, constructed
in order at 0x8000D310–0x8000D43C. Most share one class: the base vtable
is `lbl_802A837C` (ctor `func_80051320`). Each slot is 4 bytes:
`{s16 id, s8 count, pad}`. The object fields are:

| Offset | Field |
|---|---|
| +0x8 | max stack |
| +0xC | slot count |
| +0x10 | slot array |

| Function | Vtable slot | What it does | Conf. |
|---|---|---|---|
| `func_80051798(this, id)` | +0x28 | Linear search of `slots[0..+0xC)` for `id`. Returns the index, or −1. With id 0 it finds the first empty slot. | High |
| **`func_800515F4(this, id, count, slot)`** | +0x30 | **Add/remove.** See below. Returns **1** on success, **0** on failure. | High |
| `func_80057EF8` | +0x30 in subclass vtable `lbl_802A7D64` | Same logic. It also sets flag bytes +0x14..+0x17 for item IDs 0x459/0x45E–0x465/0x466/0x468. | High |

**How `func_800515F4` adds.**

- **ID already present:** adds `count` to that slot. It fails (returns 0)
  if the new count is above `+0x8` or below 0. A count of 0 clears the
  slot.
- **ID not present:** it uses `slot` if that is ≥ 0, else `find(0)`. If
  that slot's ID is non-zero or `count ≤ 0`, it fails. Otherwise it writes
  `sth id` and `stb count`.
- **Full container (not confirmed statically):** if no slot is free,
  `find(0)` returns −1, and the routine then reads `slots[-1]`, the 4
  bytes before the array. That is heap-block header data, not a slot. If
  that halfword happens to be 0, the routine would write into the header.
  Callers should check `find(id)`/`find(0)` first; the hook below does.

**Script command 0x4F ("give item a0", 0x8010E168) chooses the container
from the item table.** It reads `lbl_80282DF8[id*0x24 + 1]`, a bitmask,
and takes the first set bit:

| Bit | Container | Add slot | Size |
|---|---|---|---|
| 1 | +0x14A8 | vt+0x30 | 330 slots, stack 99 |
| 2 | +0x14D0 | vt+0x30 | 1080, stack 99 |
| 3 | +0x111BC | vt+0x1C | 510, stack 99 |
| 4 | +0x1119C | vt+0x1C | 50, stack 99 |
| 5 | +0x1550 | `func_8005774C` | 22 (tools) |
| 6 | +0x14D0 | vt+0x30 | |

Other containers by ctor: +0x118C8 holds 4 slots, stack 1 (subclass
above); +0x1188C holds 50, stack 99. Ctors and sizes are high
confidence; the slot counts come from the `li` constants in each ctor
before `__nwa`.

**Milk items.** The cow product base values are sdata
`lbl_80347518..24` = **7, 0xF, 0x13, 0xB**, plus ai+0x164. That gives IDs
0x7–0x16. Item 6 is the fallback. The table byte for 7–0x13 is **0x12**
(bits 1 and 4), so the game's own "give" path puts milk into
**+0x14A8**. Item 6 is 0x02 (bit 1). High for the bytes; medium that
0x7–0x16 are the milk sizes.

**Which container is the rucksack: not resolved.**

- No player-state code (0x80032000–0x80038800) calls a container's
  add slot.
- The only player-side add I found is 0x80047C30 (indoor state class).
  It adds `word[gamedata+0x14D28]` ×1 to +0x1188C, then sets held = 0x4FF.
- +0x14A8 (330 slots) looks more like storage or a shipping stock than
  the rucksack. **Low** that +0x14A8 is what the menu shows as
  "rucksack".
- Dolphin check:
  1. Put one milk into the rucksack through the game's own UI.
  2. Read each container's slot-array pointer (`*(gamedata+off+0x10)`;
     `gamedata = *(u32*)(r13-0x57F4)`), or memory-search for the
     halfword milk ID followed by a count byte.
  3. Or set a read breakpoint on each array while opening the rucksack
     menu.

#### Call site

At 0x80036D78 (file 0x33AB8, `4BFD06C5` = `bl func_8000743C`):

| Register | Value |
|---|---|
| r3 | `lbl_803491F4` (ignored: `func_8000743C` reloads `lbl_803491CC`) |
| r4 | **kind** = `lwz r4,0x14A4(r31)` at 0x80036D70 |
| r5 | map (+0x64) |
| r6 | &pos = r1+8 |
| r7 | rot (player+0x58) |

- After the call, 0x80036D7C only reloads `0x14A8(r31)`. The return value
  is **not used**.
- r31 (player) and r30 are non-volatile and are not touched by the hook.
- CR, CTR and LR are dead at a call site.
- High.

#### Proposed change (C2 at 0x80036D78, 45 instructions + return slot)

The hook replaces the `bl`. It tries `+0x14A8.add(id, 1, −1)`. It calls
the original `func_8000743C` with the saved r3–r7 only if:

- `find(id)` and `find(0)` both return −1, or
- `add` returns 0 (stack at 99).

So a full container falls back to the old ground drop. The last milk
still goes to the hand when the hands are empty (0x80036D08 path,
unchanged). Assembled with `powerpc-linux-gnu-as -mregnames -mgekko`;
branch targets were checked with objdump (`out` = the Gecko return slot
at +0xB4).

```
$Milk to container +0x14A8 (C2 at 0x80036D78)
C2036D78 00000017
9421FFD0 90610008
9081000C 90A10010
90C10014 90E10018
806DA80C 386314A8
9061001C 81830004
818C0028 7D8903A6
4E800421 2C030000
40800024 8061001C
38800000 81830004
818C0028 7D8903A6
4E800421 2C030000
4180002C 8061001C
8081000C 38A00001
38C0FFFF 81830004
818C0030 7D8903A6
4E800421 2C030000
40820030 80610008
8081000C 80A10010
80C10014 80E10018
38210030 3D808000
618C743C 7D8903A6
4E800421 48000008
38210030 00000000
$Instant milking (7.3)
04036CF0 60000000
```

- **Changing the container.** Word 10 of the code body, `386314A8`
  (`addi r3,r3,0x14A8`), is the only value to change if Dolphin shows a
  different container is the rucksack.
- **The +0x111xx containers are a different class.** cmd 0x4F calls
  their add through **vt+0x1C**, and their find slot is unverified. The
  `818C0028`/`818C0030` offsets would need checking before pointing the
  hook there.

#### Dolphin tests

1. With both codes on, milk a cow. No milk should appear on the ground,
   except the last one, which goes to the hand. A breakpoint at
   0x8000743C should not hit.
2. Read `*(gamedata+0x14A8+0x10)` and look for `{id, count}` with id
   0x7–0x16 and count = milk − 1. Then check where it shows in game
   (rucksack, storage or shipping).
3. Fill the container (or set slot count +0xC to 0 temporarily). The milk
   should drop on the ground as before, with no crash.

### 7.5 Message boxes and a milking summary (main.dol, static only, not tested)

All addresses are in main.dol (sha1 1ccfd9df…22374, matches
`hmawl_us_r0.sha1`). The file offsets come from `dolread.py`.

#### Message routine

| Function | Address (file) | Signature / behaviour | Conf. |
|---|---|---|---|
| **`func_801020E4`** | 0x801020E4 (0xFEE24) | See below. | High (args/return); medium (A handling) |
| `func_80102300(mgr, i, value)` | 0x80102300 (0xFF040) | `mgr+0x88+i*4 = value`. **Number parameter.** Used for watering-can water (0x80043C80, section 6) and at 0x800F3150. | High |
| `func_80102310(mgr, i, value)` | 0x80102310 (0xFF050) | `mgr+0xA8+i*4 = value`. **Name parameter.** Field items pass an item ID (0x80008FD4 → system 0x1D6). Animals pass slot−0x31 (0x800CF3F0). | High (store); medium (meaning) |
| `func_80102320` | 0x80102320 | Called by the opener. It gets the text with `func_800FB498(lbl_803491F0, file, msgId)`, then lays it out (`func_800FBCC0`, `func_800FC408`, `func_80102894`). | High |
| **`func_800FB498(textMgr, file, msgId)`** | 0x800FB498 (0xF81D8) | Returns a **pointer into the loaded `.mes` file**. `base = func_800FB540(file)`, `ptr = base + *(base + 8 + msgId*4)`. For file 0x3B it splits IDs over 0x3C–0x3E (>0x14E, >0x29D, >0x3EC). Return at 0x800FB528 (`7C030378`). | High |

**`func_801020E4(mgr = lbl_803491C4, mode, file, msgId, speaker, 0x70, r9, r10)`.**

- If a box is already open (`mgr+0x48 != 0`), it returns **0** and does
  nothing. Otherwise it sets `+0x48 = 1`, opens the box and returns **1**.
- **It does not block.** Callers wait in a player state until
  `lbl_803491C4+0x48 == 0`. Example: state 0x2A. Its enter, 0x80034CAC,
  opens `(file=+0x14C0, msg=+0x14C4)`; its per-frame handler, 0x80034D58,
  waits on +0x48 (`808DA804` at 0x80034D6C), then returns to idle.
- I assume the A press that closes the box is handled by the message
  window. I haven't traced its per-frame update. Medium.

**Text files.** The table `lbl_802517E0` holds 8-byte {label, filename}
entries; the index is the `file` argument.

| ID | File |
|---|---|
| 0x00–0x28 | NPC files |
| 0x31 | event |
| **0x33** | **system.mes** |
| 0x3B–0x3E | itemdoc*.mes |
| 0x41 | string.mes |
| 0x43 | phrase.mes |
| **0x44** | **item.mes** |

The `.mes` files are on the disc, not in the DOL or this repo. Their
encoding and control codes (newline, end, number and name insertion)
are **unknown statically**. Every message I found with a number or name
parameter is in **system.mes (0x33)**:

| Site | Parameter | msgId |
|---|---|---|
| field-item state 3, 0x80008FF8 | item name | 0x1D6 |
| animal reaction, 0x800CF428 | animal name | from `func_800CC328` |
| 0x800C2AE0 | name | 5 |
| 0x801739F4 | name | 0xE1 |
| 0x8008F2CC | name | 0xCF |
| 0x800F3180 (with file 0x29/0x3B) | number | |

#### Milk grade

- **kind = base[group] + grade.** This comes from `func_800C7F48`
  (0x800C7F48). The base is chosen by `func_800CBEAC(ai, *(ai+0))`
  (jump table `lbl_802B7F98`), which maps the animal type to a group:

  | Animal type | Group | Base (sdata) |
  |---|---|---|
  | 6, 7 | 1 | `lbl_8034751C` = 0xF |
  | 12, 13 | 2 | `lbl_80347520` = 0x13 |
  | 18, 19 | 3 | `lbl_80347524` = 0xB |
  | any other | 0 | `lbl_80347518` = 7 |

  High.
- **The grade is ai+0x164.** It is a clamped value: current +0x164,
  max +0x168 = 3, min +0x16C = 0. The init is at 0x800C6B30–0x800C6B54.
  So there are 4 grades, 0–3. High for the range; medium that it is the
  shop grade (S/M/L/G or similar).
- **Item IDs per group are consecutive:**

  | Group | IDs |
  |---|---|
  | 0 | 7–0xA |
  | 3 | 0xB–0xE |
  | 1 | 0xF–0x12 |
  | 2 | 0x13–0x16 |

  Which group is cow, goat or sheep is not confirmed.
- **One milking gives one kind.** The payload is a single {kind, count},
  so every milk from one milking has the same grade. The summary only
  needs: count, kind.
- Item 6 is the fallback when `func_800C7F48`'s vcall on ai+0x124 returns
  ≤ 3. The count is then forced to 1.

#### Where count and kind are known

| Location | Count | Kind |
|---|---|---|
| Player state 0x95, 0x80038644/0x8003864C | stored at **player+0x14A8** | stored at **player+0x14A4** |
| Drop loop, 0x80036CC8 | +0x14A8 is **decremented to 0**, so the total is lost | +0x14A4 stays valid until state 0 |
| 7.4 hook (C2 at 0x80036D78), success path | r4 = kind on entry | r4 = kind on entry |

- The drop index +0x1368 is reset by state 0x96's enter (0x80036CA8) on
  every re-entry, so it doesn't hold the total either.
- **Best counter:** in the 7.4 hook's success path (`bne done`), add 1 to
  a RAM word and save the kind. After the last milk, the loop reaches
  0x80036D7C with `+0x14A8 == 0` and falls through to the end block at
  0x80036D88: it sends 0x1C to the cow, plays anim 0x32, stops sounds,
  then `func_80031D7C(player, 0)` at 0x80036E4C (`li r4,0` at 0x80036E48,
  file 0x33B88).
- If the hands were empty, the last milk went to the hand, not to
  storage.

#### Existing summary box

I found none for milking. The closest is field-item state 3's
item-name message (system 0x1D6, 0x80008FB0). I didn't look for
shipping or day-end result screens beyond the `func_801020E4` caller
list.

#### Proposed approach (two codes; medium risk)

**1. Count.** Extend the 7.4 hook's `done:` path to:

```
lis r12,0x8000
lwz r0,0xB00(r12)   ; count
addi r0,r0,1
stw r0,0xB00(r12)
lwz r0,0x0C(r1)     ; saved kind
stw r0,0xB04(r12)
```

Put this before `addi r1,r1,0x30`. Free RAM: the 0xB00 vector slot
(0x80000B00–0x80000BFF). I checked it with the 7.1 method:

- no lis+D-form, raw-word or REL-relocation references in main.dol or
  wlp0/1/2.rel;
- no absolute `(r0)` accesses;
- not one of `OSExceptionInit`'s 15 slots.

**2. Show the box.** Hook 0x80036E48 (`li r4,0` before
`bl func_80031D7C`). If `*(0x80000B00) != 0`:

1. `func_80102300(lbl_803491C4, 0, count)`.
2. `func_80102310(lbl_803491C4, 0, kind)`.
3. `stw 0x33 → player+0x14C0`, `stw msgId → player+0x14C4`.
4. Clear 0x80000B00.
5. `li r4,0x2A`, so the game's own state 42 opens the box, waits for it
   to close, then returns to idle.

This reuses tested code (section 6 enters state 42 the same way). If
the count is 0, `li r4,0` stays as it was.

**Text.** This is the part that can't be done statically.

- **Option A (no text change):** use an existing system.mes message that
  already shows a number and an item name. That needs system.mes to find
  one.
- **Option B (custom text):** C2 at the entry of `func_800FB498`
  (0x800FB498, `9421FFE0`). If `r4 == 0x33 && r5 == <unused id>`, set
  `r3 = 0x80000B10` (a text buffer) and `blr` before the `stwu`;
  otherwise run `stwu` and continue. The buffer must use the `.mes`
  encoding and its end/newline codes. The count and grade can be written
  as ready-made digits, so no number control code is needed.

**Risk.**

- The state-42 path is medium.
- Option B is medium-high until the `.mes` format is known. A wrong
  terminator would run the layout off the end of the buffer.
- Showing the box while the cow is still in its post-milk state (0x20)
  is probably harmless. The cow only waits for 0x1C, and 0x1C is sent
  first at 0x80036DF4.

#### Open questions and Dolphin checks

| Question | Dolphin check |
|---|---|
| `.mes` format, and a usable system.mes message | Upload `system.mes` (it is on the disc). Or break at 0x800FB528 while an "obtained item" message opens and dump the bytes at r0/r3. |
| Does A close the box? | Watch `lbl_803491C4+0x48` (`*(r13-0x57FC)+0x48`) while the item description is open: it should go 1→0 on A. |
| Grade semantics | Read ai+0x164 at 0x800C7F94 (r31 = ai) while milking cows of known quality, and compare with the item name shown. |
| Group → species | At 0x800C7F94, read `*(ai+0)` (type) for a cow and a goat. |
| Param slot semantics for item names | Break at 0x80008FD4 and compare r5 (item ID) with the name shown in the 0x1D6 message. |

### 7.6 system.mes decoded (file 0x33)

**Input.** system.mes, sha1 `2f93f7c62ea2d5b8529f913cf40b82f52c2929e7`,
51,936 (0xCAE0) bytes. The sha1 matches. It was read from a scratchpad
copy; the file is not in the repo.

The reader is `mesread.py` (scratchpad, not committed). It writes
`system_decoded.txt`: one line per message, as
`IDX text`, with `\n` for a line break.

#### File format

| Offset | Content | Conf. |
|---|---|---|
| 0x0 | u32 magic `CDC3B0B0` | High |
| 0x4 | u32 count = **0x1F8 (504)**. The earlier "126" was wrong. | High |
| 0x8 | 504 × u32 file offsets. The table ends at 0x7E8 = message 0's offset. All offsets are inside the file, ascending and 4-aligned. This matches `func_800FB498`: `ptr = base + *(base + 8 + id*4)`. | High |

**Message bytes.**

- A byte ≥ 0x80 starts a **2-byte glyph** (`b0<<8 | b1`).
- A byte < 0x80 is a **control code** with a fixed number of argument
  bytes.
- **0x00 ends** the message. **0x40** (choice prompt) also ends it; its
  options are the following messages.
- High. The 2-byte vs 1-byte split is the copy loop at 0x800FB1C4
  (`rlwinm. r0,r3,0,24,24`; `lhz`/`sth` for ≥ 0x80, `stb` otherwise;
  stop on 0).
- All 504 messages decode to their own end with no unknown codes or
  glyphs.

**Glyphs (high).**

| Glyph | Character |
|---|---|
| `8000`–`8009` | `0`–`9` (also the number-to-text table `lbl_80251A10`, used at 0x800FC918) |
| `800B`–`8024` | `A`–`Z` |
| `80D8`–`80F1` | `a`–`z` |
| `80C8` | `.` |
| `80CA` | `?` |
| `80CB` | `!` |
| `80F2` | `'` |
| `8104` | `"` |
| `8105` | `,` |
| `8106` | `:` |
| `800A` | `-` |
| `80F5` / `80F6` | `(` / `)` |
| `80D2` | `/` |
| `80D6` | heart |
| `80D3`, `80D5`, `80CC`, `8452`, `81BE` | symbols (medium) |
| 0x02 | space |
| 0x01 | newline |

**Control codes.** The game dispatches them in `func_80186E28(this, p)`,
a jump table `lbl_802CA5E0` on `*p` 0x00–0x54. Each entry selects a
virtual-call ptmf from `lbl_802CA3B8`. I inferred the argument lengths
from the data; every message decodes cleanly with them.

| Code | Args | Meaning (evidence) | Conf. |
|---|---|---|---|
| 0x30 | 0 | Wait for A at the end of a box (595 uses; every message ends `30 00`) | High |
| 0x31 | 0 | Next page, after `30` | High |
| 0x13 … 0x17 | 0 | Highlight on/off around inserts and terms (`<13>A Button<17>`) | High |
| 0x14 | 0 | Highlight variant (`<14><2B:19><17>`) | Medium |
| **0x25 hi lo** | 2 | **Item name.** `8000` = name parameter slot 0 (`func_80102310(mgr,0,id)`, as used by the field-item message 0x1D6 `<hl><25:8000></hl>...`). Any other value is a literal item ID, e.g. `001E` fertilized egg (msg 0x009), `0003` fodder (0x0E0), `04FA` shears (0x1E4). | High (literal); medium (slot bit) |
| **0x2A 00 nn** | 2 | **Number.** Msg 0x0BD "`<2A:0000>` in stock."; 0x0C5 "Current stock: `<2A:0004>`". Probably number slot nn (`func_80102300(mgr,nn,v)`). | Medium |
| 0x21 8n | 1 | Animal/actor name, parameter slot n (`<21:80> is sick.`; 0x124–0x12B use slots 80–87) | High |
| 0x20 nn | 1 | NPC name by ID ("Sorry, `<20:0d>` is sleeping.") | High |
| 0x2B nn | 1 | Place/object name (`The <2B:15> is full.`) | Medium |
| 0x29 nn | 1 | String parameter slot nn (menu choices, toy-box list) | Medium |
| 0x26, 0x27, 0x34 | 2 | 0x26: thing name; 0x27: choice line; 0x34: speaker/portrait | Low |
| 0x40 a b | 2 | Choice prompt; ends the message | High |
| 0x12, 0x23, 0x33, 0x49 | 0 | Rare; purpose unknown | Low |

#### Search result: a number plus an item name

**No system.mes message inserts both a number and an item name from
parameters.**

- **0x0BD:** "Milk Storage / The red light blinks / when milk is in
  it.`<wait><page>` `<2A:0000>` in stock." Number only. It is about the
  barn milk tank, not food storage.
- **0x0C5:** literal item `0003` plus number `<2A:0004>`.
- **Item name only:** 0x1F2 "Put the `<25:8000>` in the Rucksack.",
  0x1D5 "A `<25:8000>`.", 0x0E1 "Caught a `<25:8000>`."

#### Proposed text (custom, built from the game's own codes; option B in 7.5)

`Sent <2A:0000> milk to\nfood storage:\n<hl><25:8000></hl><wait>`
encodes to 60 bytes:

```
801D80DC 80E580EB 022A0000 0280E480 E080E380 E20280EB 80E60180
DD80E680 E680DB02 80EA80EB 80E680E9 80D880DE 80DC8106 01132580
00173000
```

- **Where it goes.** Write it to 0x80000B10 (0xB00 slot, checked in 7.5)
  with a Gecko `06000B10 0000003C` string write.
- **How it is shown.** Return it from the `func_800FB498` hook in 7.5 for
  a reserved (file 0x33, ID) pair. The count goes in number slot 0 and
  the milk kind in name slot 0.
- **Grade.** It comes from the item name (`25:8000` shows the milk's own
  name).
- **Dolphin check:**
  1. With the text written and the hook on, open it once.
  2. Confirm the number appears. If it doesn't, try `2A 00 04` or check
     which `+0x88` slot 0x0BD reads, by breaking at `func_80102300`
     while checking the barn milk tank.
  3. Confirm the box closes on A.

#### 7.6.1 Milk, cow and storage messages (system.mes)

| Idx | Text (decoded) | Codes | Reuse for summary? |
|---|---|---|---|
| 0x0BD | "Milk Storage / The red light blinks / when milk is in it." `<wait><page>` "`<2A:0000>` in stock." | 2A (number), 30, 31 | Count only. The wording is the barn tank's. Medium |
| 0x1F2 | "Put the / `<25:8000>` / in the Rucksack." | 25 (item name, slot 0) | Name only. The wording (Rucksack) is wrong. High that it shows the name |
| 0x1D5 | "A `<hl><25:8000></hl>`." | 13/17, 25 | Name only, neutral wording. High |
| 0x1D6 | "`<hl><25:8000></hl>`..." | 13/17, 25 | Name only. Already used by the field item (0x80008FF8) |
| 0x0E1 | "Caught a / `<25:8000>`." | 25 | Fishing wording. No |
| 0x0C5 | "Push the A Button to get `<25:0003>` in and out." `<page>` "Current stock: `<2A:0004>`" | 25 (literal fodder), 2A | Number plus a literal (not parameter) item. No |
| 0x1D1 / 0x1D2 / 0x1D3 / 0x1D0 | Auto-Milker, tank and milking-spot descriptions | none | No |
| 0x1E1 | "…You can milk cows by hand or with the `<25:04f6>`. The quality and the quantity of milk depends on the breed and condition." | 25 (literal 0x4F6) | No. **Confirms item 0x4F6 is the Milker** (7.3 step 2, raising that to high). |
| 0x1E2 | "You can raise Normal Cows, Star Cows, Brown Cows and Marble Cows. Each breed produce unique milk." | none | No. **Matches the 4 product groups in 7.5** (base 7/0xB/0xF/0x13). The group is the **breed**, so ai+0x164 (0–3) is the **quality grade**. Medium. |
| 0x1CD / 0x1CE / 0x1EB, 0x107, 0x139 etc. | Cheese/butter makers, shipping, recipes | literal "Milk" text | No |

**Conclusion.** No existing message carries both a number parameter and
an item-name parameter.

- **Two-box option (no text change):** two boxes in a row.
  1. 0x0BD with `func_80102300(mgr, 0, count)`, which shows
     "Milk Storage … `<n>` in stock."
  2. 0x1D5 with `func_80102310(mgr, 0, kind)`, which shows "A `<milk>`."
  The wording is not a good fit, and it needs two state-42 passes.
- **Recommended: custom text** (7.6). It uses the same two parameter
  calls and one box.

### 7.7 Milk summary box: one Gecko code (main.dol, not tested in Dolphin)

All addresses are in main.dol (sha1 1ccfd9df…22374, matches
`hmawl_us_r0.sha1`). The file offsets come from `dolread.py`. Inputs:
system.mes sha1 2f93f7c6…29e7 and item.mes sha1 2fb00073…, both read
from scratchpad copies.

**What it does.**

- Every milk the 7.4 hook adds to food storage (+0x14A8) increments a
  counter and records the item ID.
- When the drop loop ends, the player enters state 0x2A instead of
  idle, which shows the box: "Sent `<n>` to food storage: `<milk name>`".
- State 0x2A waits for the box to close, then goes to idle.
- The text comes from a reserved system.mes ID that the text-lookup
  hook redirects to RAM.

**item.mes.** It has 0x52D entries; the index is the item ID, and the
reader is `mesread.py` with code 0x11 treated as a 0-byte code. Names:

| ID | Name |
|---|---|
| 0x06 | Mothers Milk |
| 0x07–0x0A | Normal Milk |
| 0x0B–0x0E | Marble Milk |
| 0x0F–0x12 | Star Milk |
| 0x13–0x16 | Brown Milk |
| 0x17 | Goat Milk |
| 0x18 | Good Goat Milk |
| 0x52A | Moomoo Milk |

So `<25:8000>` shows the breed name. High.

| Part | Address (file) | Original | Notes | Conf. |
|---|---|---|---|---|
| Text buffer | 0x80000B10–0x80000B40 | — | Gecko `06` string write, 0x31 bytes | High |
| Counter / milk ID | 0x80000B00 / 0x80000B04 | — | See the RAM check below | High (static) |
| Store + count (replaces the 7.4 code) | 0x80036D78 (0x33AB8) | `4BFD06C5` `bl func_8000743C` | 51 insns. The 7.4 hook plus, on `add` returning 1: `[B00] += 1`, `[B04] = id` | High |
| Trigger | 0x80036E48 (0x33B88) | `38800000` `li r4,0` | 34 insns. See below. | Medium (state-0x2A reuse is untested here) |
| Text hook | 0x800FB498 (0xF81D8) | `9421FFE0` `stwu r1,-0x20(r1)` | 9 insns. If `(r4&0xFF)==0x33 && r5==0x1F8`, return 0x80000B10 via `blr` before the frame is built; otherwise run `stwu` and continue. | High |
| Instant milking | 0x80036CF0 (0x33A30) | `4182017C` | `04036CF0 60000000`, unchanged from 7.3 | Tested by user |

**Trigger hook in detail.**

- **Counter is 0:** it runs `li r4,0`, the original instruction.
- **Otherwise:**
  1. `func_80102300(lbl_803491C4, 0, count)` (number slot 0).
  2. `func_80102310(lbl_803491C4, 0, id)` (name slot 0).
  3. player+0x14C0 = 0x33, player+0x14C4 = 0x1F8.
  4. Clear 0x80000B00.
  5. `li r4,0x2A`.
- **Registers.** r3 (player, from `mr r3,r31` at 0x80036E44) is saved in
  the hook's own 0x20-byte frame and restored before the frame is popped.
  r1 comes back to its value on entry. Only volatiles are changed
  (r0/r4/r5/r12/CTR/CR/LR), and the original
  `bl func_80031D7C` at 0x80036E4C clobbers those anyway.
- The two slot setters (0x80102300 `5480103A`, 0x80102310 `5480103A`)
  are leaf stores.

**Reserved ID 0x1F8.** system.mes has 504 messages (0x000–0x1F7), so
0x1F8 is one past the table and cannot collide with real text. Checks:

- no `li r6,0x1f8` anywhere in main.dol's asm;
- `func_800FB498` has no bounds check for file 0x33;
- the hook catches the ID before `func_800FB540`.

Medium: callers that compute the ID at runtime weren't traced, but none
can legitimately reach 0x1F8.

**RAM 0x80000B00–0x80000B4F.** Same method as 7.1. Zero hits for:

- `lowref.py`: lis + D-form/addi/ori, raw words in every main.dol
  section, REL relocations against module 0;
- absolute `(r0)` D-form in main.dol, wlp0, wlp1 and wlp2;
- raw words in the RELs.

The range is not in `OSExceptionInit`'s 15 slots (0xB00 is never
installed).

**Text.** `Sent <2A:0000> to food storage:\n<25:8000><wait>`, 49 bytes.
`mesread.py` decodes it back to exactly this string.

- **Width risk (medium).** The longest line in all of system.mes is 22
  characters; "Sent 3 to food storage:" is 23.
- **Fix if it wraps or overflows:** add `00000B21 00000001` after the
  `06` block. It turns the space after "to" into a newline: "Sent 3
  to / food storage: / Normal Milk".

**Known behaviour.** If the hands are empty, the last milk goes to the
hand (7.3), not to storage, so the box counts one fewer than milked.
The kind comes from the last add; one milking gives one kind.

**Gecko code** (replaces the 7.4 code; keep only one 0x80036D78 hook):

```
$Milk summary box (notes 7.7) - replaces the 7.4 code
06000B10 00000031
801D80DC 80E580EB
022A0000 0280EB80
E60280DD 80E680E6
80DB0280 EA80EB80
E680E980 D880DE80
DC810601 25800030
00000000 00000000
C2036D78 0000001A
9421FFD0 90610008
9081000C 90A10010
90C10014 90E10018
806DA80C 386314A8
9061001C 81830004
818C0028 7D8903A6
4E800421 2C030000
40800024 8061001C
38800000 81830004
818C0028 7D8903A6
4E800421 2C030000
4180002C 8061001C
8081000C 38A00001
38C0FFFF 81830004
818C0030 7D8903A6
4E800421 2C030000
40820030 80610008
8081000C 80A10010
80C10014 80E10018
38210030 3D808000
618C743C 7D8903A6
4E800421 48000020
3D808000 816C0B00
396B0001 916C0B00
8001000C 900C0B04
38210030 00000000
C2036E48 00000012
3D808000 800C0B00
2C000000 41820078
9421FFE0 90610008
9001000C 806DA804
38800000 80A1000C
3D808010 618C2300
7D8903A6 4E800421
806DA804 38800000
3D808000 80AC0B04
3D808010 618C2310
7D8903A6 4E800421
80610008 38000033
900314C0 380001F8
900314C4 3D808000
38000000 900C0B00
38210020 3880002A
48000008 38800000
60000000 00000000
C20FB498 00000005
5480063E 28000033
40820018 280501F8
40820010 3C608000
60630B10 4E800020
9421FFE0 00000000
04036CF0 60000000
```

**Dolphin tests.**

1. **Code off:** set a write breakpoint on 0x80000B00–0x80000B4F, play,
   and milk. It should never hit.
2. **Code on, milk a cow with full hands:**
   - 0x80000B00 counts up during the loop, then reads 0;
   - player state goes to 0x2A;
   - one box shows "Sent N to food storage: Normal Milk" (or the breed),
     with N = milk count;
   - A closes it and control returns.
3. **Breakpoint at 0x800FB498:** confirm it returns 0x80000B10 only for
   r4 = 0x33, r5 = 0x1F8. Other messages (NPC talk, item descriptions)
   should be unchanged.
4. **If the number shows blank or wrong:** the slot-0 guess for
   `2A 00 00` is wrong. Try `2A 00 04` with `00000B1B 00000004` (the slot byte of the `2A` code at 0x80000B19).
5. **If the line overflows:** add `00000B21 00000001`.
6. **Storage full (set +0x14A8 count +0xC to 0):** the milk drops on the
   ground and no box appears (counter stays 0).

### 7.8 Hand milking and the summary box (main.dol, static; disagrees with in-game report)

All addresses are in main.dol (sha1 1ccfd9df…22374, matches
`hmawl_us_r0.sha1`). The file offsets come from `dolread.py`.

#### Static trace of hand milking

| # | Address (file) | What happens | Conf. |
|---|---|---|---|
| 1 | `lbl_80292A78` row 1 (empty hands), target 3 → action **0x13** | Hand milking. The milker is row 9 → 0x10. | High (table) |
| 2 | 0x800442DC (0x4101C), case 0x13 | `func_8004579C(msg, target, player, type=0x16, arg=0, item=0)` (0x800442E8 `38C00016`, 0x800442F0 `38E00000`), `func_80011680`. Player → **state 0x94** (0x80044308 `3BC00094`), the same as the milker. | High |
| 3 | Cow handler `lbl_800D04F8`, type 0x16 → 0x800D09BC (0xCD6FC) | `bl func_800D0AC4`, the same routine as the milker (7.3 step 5). arg 0 → cow state 0x1E → 0x1F sends {kind, count}. | High |
| 4 | Player states 0x94 → 0x95 → 0x96 | **Same states.** The only differences are cosmetic: state 0x94 plays anim 0x13 instead of 0xF and skips the tool-use counters (category ≠ 5); state 0x95 plays sound 0x118 instead of 0x119. | High |
| 5 | Drop loop 0x80036CC8 | It **diverges only at 0x80036D08/0x80036D18**. When the count reaches 0 with empty hands (always true for hand milking), the last milk goes to the hand (`stw` kind → controller+0x144 at 0x80036D24, file 0x33A64) instead of `func_8000743C`. The other count−1 go through 0x80036D78, the 7.4 hook. | High |

**So, statically, hand milking reaches 0x80036D78 count−1 times** and
the 7.7 counter should rise. No other code adds to food storage on this
path.

- The only direct `+0x14A8` accesses are the ctor/dtor (0x8000D384,
  0x8000EB64), the condition evaluator (0x80026320–0x8002686C), cmd
  0x4F/0x55, and 0x80128B84 (a vtable +0x10 query).
- This conflicts with the in-game report (counter 0, no box). Possible
  causes, none confirmed:
  - **(a)** the cow gives count = 1 per hand milking, so the single milk
    goes to the hand and no add happens;
  - **(b)** the counter did rise, but the trigger cleared it and state
    0x2A's `func_801020E4` returned 0 (box busy), so nothing showed;
  - **(c)** hand milking in the barn uses another player class. Section
    6 noted the indoor handler `func_80048A5C`; that class's states were
    not traced.

#### Grade letter

- Each grade is its own item ID: **ID = breed base + grade (0–3)**
  (7.5; grade = ai+0x164 at milking).
- The item-table fields differ per grade. For Normal Milk 0x07–0x0A:

  | Field | Values |
  |---|---|
  | +0x6 | model 0x6E/0xE9/0xEA/0xEB |
  | +0xA | 0x14/0x2B/0x2C/0x2D |
  | +0xE (likely price) | 12/15/23/30 |
  | +0x12 | 0x28/0x32/0x46/0x5A |

- The R description opens itemdoc message ID = item ID (section 6: +0x14C4
  = held item, file 0x3B). item.mes names are identical across a breed
  (7.7), so **the letter in "Normal MilkB" is most likely literal text in
  that item's itemdoc.mes entry**. There is no runtime letter table:
  - the only A–Z glyph table in main.dol is `lbl_80293F50` (an
    alphabet, used only by 0x80136914/0x8013697C, likely name entry);
  - no code builds `0x800B+n`.
- Medium. Needs itemdoc.mes to confirm and to read the S/A/B/C… order.

#### Proposed hook (route-independent counter)

C2 at **0x800515F4** (file 0x4E334, `9421FFE0`). This is the entry of
the container add method `func_800515F4(this, id, count, slot)`, vtable
+0x30 of food storage.

- If `this == gamedata+0x14A8`, `count > 0` and id is in 0x06–0x18 or is
  0x52A: `[0x80000B00] += count`, `[0x80000B04] = id`.
- Then it runs `stwu`. r11, r12 and CR0 are volatile at function entry.
- It catches every add to food storage, whatever the route.
- Use it **with the original 7.4 store hook** (no counter), or the
  counts double.
- It counts at entry, so a rare failed add (stack already at 99) is still
  counted. Medium.
- The box still fires only at the drop-loop end (0x80036E48). If cause
  (c) is right, the indoor class needs its own trigger.

Combined code (`milk_summary_box_v2.txt` in the scratchpad):

```
$Milk summary box v2 (notes 7.8) - counts every milk added to food storage
06000B10 00000031
801D80DC 80E580EB
022A0000 0280EB80
E60280DD 80E680E6
80DB0280 EA80EB80
E680E980 D880DE80
DC810601 25800030
00000000 00000000
C2036D78 00000017
9421FFD0 90610008
9081000C 90A10010
90C10014 90E10018
806DA80C 386314A8
9061001C 81830004
818C0028 7D8903A6
4E800421 2C030000
40800024 8061001C
38800000 81830004
818C0028 7D8903A6
4E800421 2C030000
4180002C 8061001C
8081000C 38A00001
38C0FFFF 81830004
818C0030 7D8903A6
4E800421 2C030000
40820030 80610008
8081000C 80A10010
80C10014 80E10018
38210030 3D808000
618C743C 7D8903A6
4E800421 48000008
38210030 00000000
C20515F4 0000000A
818DA80C 398C14A8
7C036000 40820038
2C050000 40810030
28040006 41800028
28040018 4081000C
2804052A 40820018
3D808000 816C0B00
7D6B2A14 916C0B00
908C0B04 9421FFE0
60000000 00000000
C2036E48 00000012
3D808000 800C0B00
2C000000 41820078
9421FFE0 90610008
9001000C 806DA804
38800000 80A1000C
3D808010 618C2300
7D8903A6 4E800421
806DA804 38800000
3D808000 80AC0B04
3D808010 618C2310
7D8903A6 4E800421
80610008 38000033
900314C0 380001F8
900314C4 3D808000
38000000 900C0B00
38210020 3880002A
48000008 38800000
60000000 00000000
C20FB498 00000005
5480063E 28000033
40820018 280501F8
40820010 3C608000
60630B10 4E800020
9421FFE0 00000000
04036CF0 60000000
```

#### Dolphin checks

| Question | Check |
|---|---|
| (a) count per hand milking | Break at 0x80038644 (state 0x95) during hand milking. r4 → {kind, count}; read the word at r4+4. |
| Is 0x80036D78 reached? | Code breakpoint there while hand milking. |
| (b) box blocked? | Break at 0x80034D30 (state 0x2A's `bl func_801020E4`) and read r3 after it returns (0 = blocked). |
| (c) other player class? | Read player+0x1364 (state) during hand milking. 0x94/0x95/0x96 means the main class; anything else is another class. Section 6's `func_80048A5C` handles A presses indoors (site 7, 0x80048D98). |
| Grade letter | Upload itemdoc.mes, or break at 0x800FB528 with r4 = 0x3B while R-describing a milk, and decode the text at r3 with `mesread.py`. |

### 7.9 Summary box: highlight and grade letter (main.dol, static)

All addresses are in main.dol (sha1 1ccfd9df…22374, matches
`hmawl_us_r0.sha1`).

#### Highlighted text (replaces the 7.7 `06` block)

`Sent <2A:0000> to\nfood storage:\n<13><25:8000><17><30>`. This is 51
bytes, 0x80000B10–0x80000B42. `mesread.py` decodes it back exactly.

- The line break after "to" is built in (byte 0x80000B21 = `01`), so the
  separate `00000B21 00000001` write is no longer needed.
- Everything stays inside the checked range 0x80000B00–0x80000B4F.

```
06000B10 00000033
801D80DC 80E580EB
022A0000 0280EB80
E60180DD 80E680E6
80DB0280 EA80EB80
E680E980 D880DE80
DC810601 13258000
17300000 00000000
```

#### Where the R/A description's grade letter comes from

| Step | Address (file) | Evidence | Conf. |
|---|---|---|---|
| A path: action 0x18 case | 0x80043C24 (0x40964) | Writes **file 0x3B** to player+0x14C0 (`3800003B`). | High |
| | 0x80043C40 (0x40980) | Writes the **held item ID** (controller+0x144) to player+0x14C4 (`901F14C4`). | High |
| | 0x80043C54 / 0x80043C80 | Sets a number parameter (`func_80102300`) **only for category 3** (watering can water). No other parameter is set. | High |
| R path (section 6 Gecko) | 0x800430BC hook | Same message setup, with no parameters at all, and the letter still shows. | High (in game) |
| State 0x2A enter | 0x80034D18/0x80034D20/0x80034D30 (0x31A58/0x31A60/0x31A70) | `func_801020E4(mgr, 1, +0x14C0, +0x14C4, -1, 0x70, 0, 0)`. Message = **itemdoc entry number = item ID**. | High |
| Text lookup | 0x800FB4A8 (0xF81E8) | File 0x3B is split by ID into itemdoc01–03 above 0x14E/0x29D/0x3EC. Milk IDs are below 0x14E, so they live in itemdoc.mes itself. | High |

**Conclusion:**

- The name and letter ("Normal MilkB", highlighted) and "The quality is
  average." are **static text in itemdoc.mes, one entry per item ID**.
- **The grade is the item ID** (breed base + 0–3, from ai+0x164 at
  milking, 7.5). There is no per-instance field, and no runtime letter is
  added: no parameter is set, and main.dol has no letter table (7.8).
- High for "per item ID, no parameter". Medium that the letter is a
  literal glyph rather than an unknown control code; that needs
  itemdoc.mes.
- **The letter mapping itself (which grade is S/A/B/…) is not known
  statically.**

#### Ways to show the letter in the summary box

**Option A: copy the itemdoc name line (no mapping needed).** Medium
risk.

- In the trigger hook (0x80036E48), call
  `func_800FB498(lbl_803491F0 = *(r13-0x57D0), 0x3B, id)`.
- It returns the pointer to the item's doc text. Copy its first line,
  glyph-aware, up to the first `01`/`30`/`00`, into the box buffer in
  place of `<13><25:8000><17>`.
- This shows exactly what the R description shows, including the green
  highlight if the line has its own 13/17.
- Risk: control codes with arguments inside that line would need the
  `mesread.py` argument table in the copy loop, and the line length is
  unknown.
- `lbl_803491F0` is the text manager used by `func_80102320` at
  0x80102338.

**Option B: a letter glyph per grade.** Low risk, but needs the
mapping.

- Change the text to `<13><25:8000>?<17>`: 2 more bytes, a placeholder
  glyph before the `17` (currently at 0x80000B40).
- The trigger writes `table[grade]` into it, with
  `grade = (id - 7) & 3` for IDs 0x07–0x16.
- Mother's 0x06, goat 0x17/0x18 and Moomoo 0x52A need their own entries,
  or a blank.
- Needs the S/A/B… order from itemdoc.mes or from game testing.

#### Open questions and Dolphin checks

| Question | Check |
|---|---|
| Letter order per grade | Upload itemdoc.mes (`mesread.py` decodes it; IDs 0x07–0x0A, 0x0B–0x0E, …). Or R-describe one milk of each grade and note the letter against its ID (read the held ID at `*(player+0x135C)+0x144`). |
| Is the letter a literal glyph? | Break at 0x800FB528 with r4 = 0x3B during an R description and dump the bytes at r0 (the text pointer) up to the first `01`. |
| Option A pointer | Check that `*(r13-0x57D0)` equals the r3 passed to `func_800FB498` at 0x80102338. |

### 7.10 Summary box with grade letter (main.dol, not tested in Dolphin)

All addresses are in main.dol (sha1 1ccfd9df…22374, matches
`hmawl_us_r0.sha1`). Inputs: itemdoc.mes sha1 `a44f32f8…8d48`, 0x14F
entries, read from a scratchpad copy.

**itemdoc.mes check (high).**

- Each milk entry starts `13 25 00 <id>` (highlight, literal item name),
  then:
  - IDs 0x07–0x16: a letter glyph, then `01` (newline), `17`;
  - 0x06, 0x17, 0x18: `01` straight after the name (no letter).
- Grades from the text: C "not that good", B "average", A "good",
  S "excellent".
- **The hook's letter for all 19 IDs 0x06–0x18 matches the file
  byte-for-byte:**
  - C = `800D` for 0x07, 0x0B, 0x0F, 0x13;
  - B = `800C` for 0x08, 0x0C, 0x10, 0x14;
  - A = `800B` for 0x09, 0x0D, 0x11, 0x15;
  - S = `801D` for 0x0A, 0x0E, 0x12, 0x16;
  - blank for 0x06, 0x17, 0x18.
- The index `(id + 1) & 3` gives 0, 1, 2, 3 = C, B, A, S for every cow
  ID.
- 0x52A is not in itemdoc.mes (0x14F entries), so its blank letter is
  unconfirmed.

**Text (53 bytes, 0x80000B10–0x80000B44).**
`Sent <2A:0000> to\nfood storage:\n<13><25:8000>{8000}<17><30>`.

- The placeholder glyph `8000` ('0') is at **0x80000B40**, directly after
  `25 80 00` and before `17`.
- `mesread.py` decodes it back, and decodes correctly with each of the
  20 possible letter values written in.
- Still inside the checked RAM range 0x80000B00–0x80000B4F.

**Trigger (C2 at 0x80036E48, file 0x33B88, original `38800000`, 50
instructions).**

- Same as 7.7, plus a letter block right after `stw r0,0xC(r1)`:
  1. `r5 = [0x80000B04]` (kind).
  2. If `(kind - 7) > 0x0F` unsigned, write `0x0202`.
  3. Otherwise compute `i = (kind + 1) & 3`; i = 3 gives `0x801D`;
     anything else gives `0x8000 | (0x0D - i)`.
  4. `sth` at 0x80000B40.
- **No-letter case:** `0x0202` (two spaces) is used rather than `0x0200`.
  A `0x00` byte ends the message, so `0200` would cut off the `17` and
  the wait-for-A.
- **Registers and stack:**
  - The letter block uses only r5 and r11 (volatiles; r5 is reloaded
    before each slot call) and r12, which still holds 0x80000000 from
    the hook's first instruction.
  - It sits inside the hook's existing 0x20-byte frame, after the count
    is saved.
  - The zero-count path (`beq orig` → `li r4,0`) is unchanged.
  - Everything else in 7.7 is unchanged: both parameter calls, file
    0x33 / ID 0x1F8, counter clear, `li r4,0x2A`.
- Assembled with `powerpc-linux-gnu-as`. Branch targets checked:
  `blank` at +0x54, `gs` at +0x48, `put` at +0x58, `orig` at +0xC4.

**Gecko code.** It replaces the 7.9 `06` block and the 7.7 `C2036E48`
block. The 7.4 store hook, the text hook at 0x800FB498 and `04036CF0`
stay as they are.

```
$Milk summary box: text with grade letter + trigger (notes 7.10)
06000B10 00000035
801D80DC 80E580EB
022A0000 0280EB80
E60180DD 80E680E6
80DB0280 EA80EB80
E680E980 D880DE80
DC810601 13258000
80001730 00000000
C2036E48 0000001A
3D808000 800C0B00
2C000000 418200B8
9421FFE0 90610008
9001000C 80AC0B04
3965FFF9 280B000F
4181002C 39650001
556B07BE 2C0B0003
41820010 216B000D
616B8000 48000014
3960001D 616B8000
48000008 39600202
B16C0B40 806DA804
38800000 80A1000C
3D808010 618C2300
7D8903A6 4E800421
806DA804 38800000
3D808000 80AC0B04
3D808010 618C2310
7D8903A6 4E800421
80610008 38000033
900314C0 380001F8
900314C4 3D808000
38000000 900C0B00
38210020 3880002A
48000008 38800000
60000000 00000000
```

**Expected box (one milk of each grade, e.g. Normal).**

- "Sent N to / food storage: / **Normal MilkC**"
- "… **Normal MilkB**", "… **Normal MilkA**", "… **Normal MilkS**"
- Mother's/Goat: "… **Goat Milk**  " (two trailing spaces, invisible)

**Dolphin tests.**

1. Milk one cow of each grade, or set the cow's ai+0x164 to 0–3 before
   milking. The box shows the matching letter inside the green
   highlight. It matches the R description of the same milk.
2. A Goat or Mother's milking shows the name with no letter, and the box
   still waits for A.
3. Read 0x80000B40 after the box opens; it should be 800D/800C/800B/801D
   or 0202.
4. Regression: the count, the line break and A-to-close work as before.

### 7.11 Plot "description" on A (main.dol, static; the box itself is not identified yet)

> **Superseded in part by 7.11.1.** In-game screenshots show the box is
> "Cultivated land. / The soil is (not very / – / very) fertile." with the
> A label "Look". That is not the held-item description (0x18).

All addresses are in main.dol (sha1 1ccfd9df…22374, matches
`hmawl_us_r0.sha1`). The action table `lbl_80292A78` is at **file
0x28FA78**: 31 rows (held class) × 0xAC bytes, with the A action at
`[target]` and the second action at `[0x56 + target]`. The 7.3 cell for
row 9, target 3 is at file 0x290087.

**How the target type is chosen (high).**

- The ground under the player is **not** a target. The A handler
  (`func_80043120`) probes for objects in front of the player with
  `func_80010A94` (0x80043414 and three more probes). That fills the
  object category and subtype (0x24(r1)/0x28(r1) → action struct
  +0x1C/+0x20).
- `func_8004F2EC` maps category/subtype to a target type (jump table
  `lbl_802A7B84`, categories 0–0x32). With no object,
  `func_8004F8C4` returns **0x2A**.
- **The collision attribute (low byte 0x20) is not read anywhere on this
  path.** No code in `func_80043120`, `func_8004ED60` or `func_8004F2EC`
  reads a collision attribute. So the A action can't be switched by the
  attribute value.
- There is one field-specific rewrite: in `func_8004ED60` at 0x8004EDE8,
  **target 8 becomes target 0** when
  `func_8001F718(lbl_80349204, map, pos, …)` is true. `lbl_80349204` is
  the field/map manager. Medium: target 8's meaning (plot or crop) isn't
  confirmed.

**Two overrides before the table (high).**

| Override | Address | Condition | Result |
|---|---|---|---|
| Action **0x30** | 0x8004363C | Map 1 and `func_801728E4(lbl_80349164, pos, rot)` true and cell == 4. Independent of the held item. | State 0xE2 → `func_80172788` sets up a position/camera sequence. **No message.** |
| Action **0x31** | 0x80043688 | `func_8001CF3C(lbl_80349204, …)` true, empty hands | State 0xEB → system.mes **0x135** "Sell Items?" (the stand). Not a plot text. |

**Every A-path message opener in player code (0x80030000–0x80050000)
(high).**

| Caller | File/msg | Text |
|---|---|---|
| 0x80034D30 (state 0x2A) | from player+0x14C0/+0x14C4 | Set by action **0x18** (0x80043C24: itemdoc 0x3B, held item → **the held item's own description**), action **0x28** (0x8004435C: system.mes 2–4 random, "You can't throw that away" etc.), `func_80032348` (system 0/1, "No more space" / "Rucksack is full"), plus indoor-class copies |
| 0x800485A4/0x80048668/0x800486B8/0x80049AE0 | system 0x135–0x138 | Stand sell/close prompts |
| 0x80047B30 | system, ID from game data +0x14D2C | Indoor-class message, not traced |
| 0x800462D4 | file 0x31 (event.mes), msg 9 | Not traced |

**No soil, plot or field description exists in system.mes** (all 504
messages searched: soil/field/plow/till/seed/crop/land/dirt). A plot text
would have to be in another file (structure.mes 0x42, string.mes 0x41,
event.mes 0x31), and no A-path code opens those for the field.

**Held-item cases on a target-0/1 or no-object plot (from the table).**

| Held (row) | Target 0 or 1 | No object (0x2A) | Now shows | Conf. |
|---|---|---|---|---|
| Empty (1) | 0x00 / 0x00 | 0x16 (default: nothing) | nothing | High |
| Row 2 | 0x03 | 0x00 | msg type 6 → state 9 (an object action) | High (table) |
| Rows 3–4 (items 2/3/4) | 0x1D | 0x00 | 0x1D: object action | High (table) |
| Rows 5–0x1E (tools, seeds, watering can, fertilizer…) | **0x18** | 0x00 | **held item's itemdoc description** | High (table); medium that the plot is target 0/1 |

**Conclusion.** Statically, the only description that A can open on a
plot is **action 0x18 = the held item's own description**. It appears
for rows 5–0x1E at targets 0 and 1, for example after the target 8 → 0
rewrite at 0x8004EDE8. This is **not** a soil text. Section 6's tested
code already sends it to "no action":
`042A74D0 800444FC` / `042A7768 80049640`. Original words: `80043C24`
at 0x802A74D0 (file 0x2A44D0) and `8004919C` at 0x802A7768 (file
0x2A4768).

**Proposed change, two cases (pending one Dolphin check).**

- **If the box shows the held item's own description (file 0x3B):** use
  section 6's two `04` writes. It's tested; the description moves to R.
  - Narrower alternative: zero just the plot's cells. Set target 8 → 0
    no longer, by changing `li r31,0x0` at 0x8004EE28 to a target that
    has no 0x18 entry, for example 0x2A: `3BE0002A` in place of
    `3BE00000`.
  - That keeps 0x18 everywhere else, but it's only correct if the plot
    really is target 8. That is medium/low confidence until the check
    below.
- **If the box is from another file or ID:** the opener is not on this
  path. Patch the caller that the check finds instead.

**Dolphin checks (decisive).**

| Question | Check |
|---|---|
| Which box is it? | Code breakpoint at **0x801020E4** when the box opens on a plot. Record r5 (file: 0x3B = item description, 0x33 = system, 0x42 = structure) and r6 (msg ID), then LR (the caller). |
| Which action/target? | Breakpoint at **0x80043780** (after site 3) on the same press. r24 = action code. The target type is at `(r1+0x9B0 or 0x974)+0x30` (see 7.3). |
| Is target 8 rewritten? | Breakpoint at **0x8004EE28**: does it hit on a plot? |
| Tools on plots | Repeat with each tool held, to see whether tool use goes through A (action ≠ 0x18) or another button. |

#### 7.11.1 Correction from in-game screenshots (static; message ID still needs Dolphin)

The box reads "Cultivated land." then "The soil is not very fertile." /
"is fertile." / "is very fertile.", with A = "Look". So the conclusion
above (action 0x18, held-item itemdoc) is wrong for this box.

**What is now confirmed (high, main.dol).**

- The file argument (r5) of `func_801020E4` indexes the name table
  `lbl_802517E0` (file 0x24E7E0) in pairs: file N → names [2N] "@name"
  and [2N+1] "name.mes". Checked: 0x33 → system.mes, 0x3B → itemdoc.mes,
  0x31 → event.mes, **0x29 → console.mes**, 0x41 string, 0x42 structure,
  0x43 phrase, 0x44 item, 0x45 farmcrop.
- The text "Cultivated", "fertile" is **not** in system.mes, item.mes or
  itemdoc.mes (raw glyph search). Those are the only .mes files I have.
- No player-code opener (all `func_801020E4` callers and all
  +0x14C0/+0x14C4 writers in main.dol were checked) builds a message ID
  from fertility. The A handler's "pass" actions
  (0, 8, 9, 0xA, 0x11, 0x16, 0x19, 0x1E–0x21, 0x27, 0x2E, 0x2F →
  0x800444FC, `li r22,3`) do nothing in player code; something else acts
  on them.
- console.mes (0x29) is opened only through virtual "show console
  message (id)" methods: `func_800F30D0` (0x800F3180, file 0x29, or 0x3B
  when id bit 0x10000000 is set), `lbl_800F1428` (0x800F1464), and REL
  copies (wlp1 0x1BB94, 0x3C720). Script commands open messages through
  `func_80113864` with file and ID taken from script arguments. So the
  plot "Look" text is most likely console.mes, opened by an object or
  script with a data-driven ID. **Medium**; not confirmable without the
  ID or console.mes.
- Fertility bits: no code in main.dol or the RELs tests collision bits
  0x2000/0x4000 (the 0x0020/0x2020/0x4020 attributes in the viewer) with
  `andi.`/`rlwinm`. Whatever picks "not very / – / very" isn't a direct
  attribute test that I could find. **Low** that the attribute is read.
- HUD labels: `func_80083378(player+0xDC, slot, action)` sets the button
  labels from the byte table at `lbl_8024F638+0x5C` (file 0x24C694).
  Action 0x18 → label 0x01. Which label number is "Look" isn't known.

**Proposed change (does not touch the attribute, the action table, or
tool/seed/water/harvest paths).** Skip only this message at the
opener. A C2 hook at the entry of `func_801020E4` returns 0 ("not
opened", the same value as its own busy path at 0x8010228C) when
file = 0x29 and LO ≤ ID ≤ HI. Every other message opens as before.

Original at 0x801020E4 (file **0xFEE24**): `9421FFD0` (`stwu r1,-0x30(r1)`),
checked in main.dol.

```
C21020E4 00000005
2C050029 4082001C   # cmpwi r5,0x29 ; bne orig
2C061111 41800014   # cmpwi r6,LO   ; blt orig   (LO = 0x1111 placeholder)
2C062222 4181000C   # cmpwi r6,HI   ; bgt orig   (HI = 0x2222 placeholder)
38600000 4E800020   # li r3,0 ; blr  (LR is still the caller's)
9421FFD0 00000000   # orig: stwu r1,-0x30(r1)
```

**Don't use it until LO/HI (and the file, if it isn't 0x29) come from
the Dolphin check below.** Replace `1111` and `2222` with the IDs (and
`0029` with the file if it differs). If the three fertility texts
plus "Cultivated land." aren't consecutive, use one compare per ID.

Risk (medium): the callers I read ignore the return value and then wait
for the box flag `mgr+0x48`, which stays 0, so they should continue
at once. A script caller that waits on a different event could hang; the
test plan covers this.

**Dolphin checks (decisive).**

| Question | Check |
|---|---|
| File and ID | Code breakpoint at **0x801020E4**, press A on a plot with empty hands. Record r5 (expect 0x29), r6 (ID) and LR. Repeat on a fertile and a very fertile plot to get all IDs. |
| Who opens it | From LR, step back: is it `func_800F30D0`/`lbl_800F1428` (object vtable) or `func_80113864` (script)? |
| Are IDs shared | With the code on, Look at other objects (signs, bins, the stand). Nothing else should lose its text, unless it uses the same file and ID. |

**Test plan (after filling LO/HI).**

| Case | Expected after |
|---|---|
| Empty hands, A on plot (all three fertilities) | No box; player stays free to move (no hang) |
| Each tool (hoe, sickle, hammer, axe…) on plot | Same as before |
| Seeds on plot | Plants as before |
| Watering can on plot | Waters as before |
| Harvest a ripe crop | Harvests as before |
| Look at non-plot objects | Text as before |


#### 7.11.2 Look on plots: probe trace (main.dol, static only)

main.dol sha1 1ccfd9df…22374 (= `hmawl_us_r0.sha1`).

- **The "8 candidates" of `func_80010A94` are map blocks, not objects.**
  `lbl_8023DF88` (file 0x23AF88) is just 0..7. Each index goes through
  `func_80011634(block, i)` into `lbl_8023E138` (file 0x23B138, 16 rows
  × 0x24: key = block 1–16, then 8 neighbour blocks of a 4×4 grid,
  -1 = none). `func_80010C9C` walks each block's hit list
  (`mgr+0x2A0+block*0x2C`), takes the nearest hit in range and returns:
  out+0 = owner+0x04, out+4 = owner+0x08, out+8/+0xC = the pair written
  by the owner's virtual method **vtable+0x10** (`bctrl` at 0x80010E20).
- At the Look callers (`func_80048A5C`, 0x80048AE8): r4→0x20(r1),
  r5→0x1C(r1), **r6→0x2C(r1)/0x30(r1) = that virtual pair**. So 0x2C(r1)
  (struct +0x1C, the `lbl_802A7B84` index) is a runtime value from the
  plot owner's class, not a table constant.
- Base method `lbl_8000A560` returns (-1,-1) (→ kind 0). Category 0x20
  (→ kind 0x3F) is written by 0x800C7E20 / 0x800C88FC (object code at
  0x800C…, not the field). That's why `042A7C04 8004F350` did nothing.
- Category 0x1E (0x8004F644) decodes the subtype through
  `func_80023988` (records at `lbl_80299FB0`, stride 0x3C) and returns
  kinds 0x35–0x3A from bits of record +0x28. This looks like a
  living-thing record (animal or crop). Not confirmed as the plot.
- I couldn't find the plot owner's vtable+0x10 method statically. The
  overrides that write the pair through r4 (main.dol) return
  categories 0x0D, 0x17, 0x18, 0x1C, 0x2D–0x31, 0x33. Most REL ones
  return 0x00–0x12. **The plot's (category, kind) cell is not
  identified.**
- No main.dol or REL code opens file 0x3F with a constant. Its opener
  passes the file from data, for example through `func_80113864`
  (script) → `func_801020E4`.
- The "Look" on the A button is a label index, `lbl_8024F638+0x5C`
  (file 0x24C694) by action, used by `func_80083378`. It's probably a
  texture, not text.

**Fallback patch (not tested): stop only these line.mes boxes at the
opener.** C2 at 0x801020E4 (file 0xFEE24, original `9421FFD0`).
Returns 0, the opener's own "busy" result, for file 0x3F and msg 0x1D,
0x27 or 0x2F–0x31. 0x2A ("Water the plant.") and 0x32 (hoe hint) are
left alone.

```
C21020E4 00000007
2C05003F 4082002C
2C06001D 4182001C
2C060027 41820014
2806002F 41800014
28060031 4181000C
38600000 4E800020
9421FFD0 00000000
```

Risks: the Look action/animation itself may still play (only the box is
skipped). If a script waits for the box differently from the callers
read in 7.11.1, it could hang.

### 7.12 Skip Intro: title → game flow (main.dol + wlp1.rel, static only)

**CLZ.** Already ported in `tools/analysis/arclist.py` (`clz_decompress`).
Header "CLZ\0", +4 size. LZSS from +0x10, flags **LSB first**, bit
1 = reference: dist = 0x1000 − (b0 | (b1&0xF0)<<4), len = (b1&0xF)+3.
Checked on mainchapter1.arc.clz: the whole stream is consumed
(0x445138/0x445138) and the output is a valid U8. **mainchapterN.arc
holds only NPC models and animations** (boy_0.arc … *.anm.arc), not
scripts.

**Where the intro lives.** `func_8010A6D8` (script engine) loads
`ChapterN.arc` and `EventCondition_C0(N-1).arc` from the table at
0x802BDB68 for chapter `func_8000FEE8(lbl_80349218)`. The Chapter-1
opening script is in **Chapter1.arc** (+ EventCondition_C00.arc).

**Title → game (wlp1.rel, REL section offsets).**
- ConsoleTitle (vtable 0x4BB44, update 0x3D324): state +0x5AC, cursor
  +0x5B0 (2 items, wraps via 0x3E0D0). A (0x100) or Start (0x1000) →
  +0x5C8 = cursor, state 4 (0x3DFCC). Idle 0xA8C frames → +0x5C8 = 3
  (0x3DE00).
- After the fade, 0x3E0F0 sets +0x5B8 = 1 and calls
  `func_8017767C(g_system, scene, 0)`: cursor 0 (New Game) → **scene
  0x2B** (0x3E15C); 1 (Load) → 0x2C; 3 (demo) → 0x2E.
- Scene factory 0x45B8C (case = scene − 0x13): scenes 0x29–0x2E build
  class 0x2320 with a mode. 0x2B → mode 4 → **console 0x1B** (ctor
  0x3CCC0, SaveDataManager init 0x361E8, i.e. the memory-card new-game
  console). Console ids are dispatched at 0x2898: 0x18 = 0x3E2DC,
  0x19 = title 0x3CE98, 0x1A = load 0x3CB48, 0x1B = 0x3CCC0,
  0x1C = 0x410D8, 0x1D = 0x412C8.
- When a console returns next id **0x21**, 0x2840 calls
  `func_8017767C(g_system, 0, 0)`, the field scene. So the intro is
  not run by the title code. It's event script that starts in scene 0.

**Naming.** Script opcode **0x0E** (`lbl_8010CD7C`, table
`lbl_802C0078`) requests **scene 0x28** (0x8010CDF4; wlp1 class 0x2158,
the SceneConsoleNameEntry REL, `nameentry2.agc`), and resumes when it
returns. The dog, farm and player naming are therefore 0x0E commands
inside the intro script. Their arguments, and all the intro's flag,
money, animal, Takakura and day writes, are script data in
Chapter1.arc. **Not statically visible from main.dol.**

### 7.13 Skip Intro: opening-script patch (static; not tested in Dolphin)

Branch `skip-intro-script`. Builder: `tools/skipintro/build_skipintro.py`
(inputs: main.dol sha1 1ccfd9df…22374, Chapter1.arc 120708 bytes,
system.mes 51936 bytes).

**Files.** Chapter1.arc is an **uncompressed** U8 with 34 entries, each
CLZ (format as 7.12). Every entry decompresses to RIFF `SCR ` with
CODE / (STR) / OPT chunks. EventCondition_C00.arc is a plain U8 with 10
records (format not decoded). The loader pairs them (table 0x802BDB68).
Event ids below 300 are chapter×50 + entry (1-based) into ChapterN.arc
(0x8010AD80). **The opening is Chapter1.arc entry 1**, 0x14A5
instructions: it alone contains the naming calls (5 × command 0x0E).

**Script VM** (`func_80186208`, jump table 0x802CA310). Instruction =
op u8, flags u8 (bit 0: arg += frame base vm+0x4D8), pad u16, arg s32.
Stack vm+0x20 (sp byte vm+0x1B0, max 100), vars vm+0x1B8 (200 words).
Numbers are fixed point, shift 7 (OPT = 7).

| op | meaning | op | meaning |
|---|---|---|---|
| 01 | store via address (`v[a]=x`, leaves x) | 13 / 14 | push / pop var[arg] |
| 02–06 | `+= -= *= /= %=` via address | 15 / 16 | dup / pop |
| 07–0B | add sub mul div mod | 17 | push arg |
| 0C / 0D | logical and / or | 18 | jmp arg (instruction index) |
| 0E / 0F | top ± 1.0 | 19–1E | pop, jump if <0, ≤0, =0, ≠0, ≥0, >0 |
| 10 / 11 | neg / not | 1F / 20 | call / ret |
| 12 | compare: push 1, −1, 0 (a>b, a<b, equal) | 21–23 | frame base =, +=, −= |
| 24 | end | 25 | script command `arg` (`func_8010C604`) |

Command argument counts: first byte of the 0x24-byte entries at
0x802BDF00 (types: 1 int, 2 fixed→float). A command pushes a result if
its case calls one of the push helpers 0x80112B0C…0x80112D08. With these
rules the stack depth of all 5283 reachable instructions is consistent.

**Command 0x04** (message): args (file, msg, speaker). The first call
opens the box and returns 0. Later calls return 0 while it is open,
then choice+1, or −1 for a plain message.

**What the opening does** (commands in order; full trace in the builder
report). Setup: 0x42, 0x28, clock 11:00 (0x43), 0x2E, warp 1 (0x2C),
0x5A(74,0). Then Takakura's lines (takakura.mes 100–138). **Choice at
msg 113 sets v[8] = 39 or 40** and takes one of two branches with
0x03(13, v[8]) and naming 0x0E(v[8]). Then 0x2D(2,90,1,1), warp 7,
naming 0x0E(49) (animal slot 0x31) + 0x05(0,0), warp 1, naming 0x0E(72),
0x36, clock 13:10, naming 0x0E(0). Then the tour (warps, clock 15:30 and
next day 07:40), the morning scene, and closing other.mes 447/450 plus
0x27. **The script itself has no flag, var, gold or item commands**
(0x93/0x94/0xC1/0xCA/0x4F/0xD3/0xD4 are absent). The only game-data
commands are 0x03 and 0x2C. Starting money and the first animal are not
set here.

**Patch (v3, after the first Dolphin test).** v1/v2 skipped "cosmetic"
regions but kept wait loops on command 0x0D. Those loops also contain
character moves (for example 0x60 at 0x0674) whose characters are spawned
in skipped regions, so after the dog naming the script waited forever
(music still playing), and the kept fade pairs showed the static tree
shots. v3 drops the region approach:
- Instruction 0x001D (after the opening warp and SYS 10): `17 00 13 00
  00 00 2B 8C` → `18 00 00 00 00 00 14 A5` (jmp to appended code). It shows
  system.mes 0x1F9 "Skip the intro?" and sets v[150] = (answer == Yes).
- **No:** runs the original instruction and continues the original script
  (the simulation shows the same command sequence plus the prompt).
- **Yes (v5):** appended code (0x14A5–0x158B), on a black screen, with
  the original arguments where the original is used:
  1. new line system.mes 0x1FA "Which dog do you want?", then the dog
     choice (takakura.mes 113 → v[2]; v[8] = 39 for the first option,
     else 40);
  2. 0x03(13, v[8]) and 0x7D(75) / 0x7D(76), then naming v[8] (dog);
  3. black, 0x2D(2, 90, 1, 1), new line 0x1FB "Let's name your cow.",
     naming 49 (cow), 0x05(0, 0);
  4. black, new line 0x1FC "Now name your farm.", naming 72 (farm);
  5. black, new line 0x1FD "Finally, how should / I call you?", naming 0
     (player);
  6. black, then the clock 0x43 13:10, 15:30, 07:40, then warp 0x2C(1)
     + 0x10;
  7. black, then a jump to 0x148F, the "The Beginning" part of the
     ending: 0x27(120, 0), other.mes 450, 0x27(−120, 0), END.
  "Black" is the script's own instant setup `0x41(0|1|3, 0, 0)`. The new
  lines are only in system.mes, so the full intro (No) still shows
  Takakura's own lines. v4 used takakura.mes 114/122/124/126; v3 jumped
  to 0x1466, which showed the beach and line 447.
- Instruction bytes 2–3 are zeroed everywhere (never read; the compiler
  left junk). Entry 1: 8295 → 8194 bytes compressed (v5), so it fits its slot.
  The other 33 entries are byte-identical and Chapter1.arc stays 120708
  bytes.
- system.mes stays 51936 bytes. Space comes from five byte-identical
  duplicates sharing their first copy's text: 0x06=0x05, 0x10=0x0F,
  0x16=0x15, 0x17=0x11, 0x18=0x11 (`func_800FB498` is base + offset[id],
  with no length or order check). All 504 original ids decode identically.
  New: 0x1F8 and 0x1F9 "Skip the intro?" `40 00 00` (0x1F8 is left for the
  milk-summary Gecko), 0x1FA–0x1FD the four short lines ending `30 00`.

**Not confirmed.**
- Which EventCondition_C00 record starts event 1.
- Console 0x1B's last step before next-id 0x21 (the next id is the
  console result +0xB4, getter 0x40BC8).
- What 0x06/0x07/0x20/0x2D/0x36/0x76 do.
- Where the player stands after END on Yes: the original places the
  player and Takakura (0x85/0x58/0x59 at 0x1265–0x1278) before the morning
  scene, and v3 skips that. If the game does not move the player into the
  house itself after the event, the place to add is 0x1265–0x127C.
- What the naming screens show over (the field is still black from the
  prompt; there is no tree scene).


### 7.14 Faster scene transitions: one fade-duration hook (static; not tested in Dolphin)

Branch `faster-transitions`.

**The screen fader.** Every screen fade goes through
`func_80189128(fader, colour_from, colour_to, f1 = seconds, r6, r7)`
(fader `lbl_803491B8`). It stores `1000.0 × f1` (ms, constant
`lbl_8034BC00`) at +0x58, the start time (`func_8017A2FC`, ms) at +0x5C
and busy = 1 at +0x60. The update (0x80188D60) computes
progress = (now − start) / +0x58, and when progress > 1 sets +0x60 to 0 or 2;
duration 0 finishes at once. "Wait for fade" (script command 0x0D,
`func_80189338`) is just +0x60 == 1. Timing is real time, not frames.

**Callers (durations in seconds).** main.dol constants:

| call site | function | constant | value |
|---|---|---|---|
| 0x80012984 | func_80012900 (field/map load area) | lbl_80349F0C | 1.0 |
| 0x80014654 | func_80014604 | lbl_80349F2C | 1.0 |
| 0x80034638 / 0x80034904 | func_80034304 (player state code) | lbl_8034A208 / lbl_8034A210 | 0.5 / 1.0 |
| 0x80034EC8, 0x80034FC8, 0x800350C8, 0x80035358 | func_80034E3C… (player) | lbl_8034A218 | 0.2 |
| 0x80046668 | func_800463C8 | lbl_8034A2E0 | 2.0 |
| 0x80047D70, 0x80049C2C, 0x80049CF0 | indoor player code | lbl_8034A31C (9 refs) | 1.0 |
| 0x80048260, 0x80048314 | func_80048054 | lbl_8034A328 | 0.2 |
| 0x8004B0AC | func_8004A948 | lbl_8034A35C | 1.0 |
| 0x8008CED0 | func_8008CE58 | lbl_8034A76C | 0.8 |
| 0x800F1FF0, 0x800F2098, 0x800F6194, 0x800F62D4 | console/UI | lbl_8034ADD4 / lbl_8034AE54 | 0.25 |
| 0x801742C4, 0x8017453C, 0x8017475C, 0x80174954 | func_80174170… | lbl_8034B9D4 | 1.0 |
| 0x8010CCDC / 0x8010CD5C | script commands 0x0B / 0x0C | script argument | per script |

Plus about 40 calls in wlp0/wlp1/wlp2 with durations from data tables
(title, consoles, rooms). The "what is it" column is the containing
function only, not confirmed in game. Several constants are shared with
non-fade code (lbl_8034A31C has 9 references), so writing the constants
is not safe.

**Script command 0x41** (`func_8014FE20`, args level 0–127 and seconds)
is a **volume** tween timed with OSGetTime, not a screen fade, and nothing
waits on it. (The Skip Intro "black()" helper therefore sets volumes to 0;
the screen was already black from the opening.)

**v2 (after the first test showed no change).** There are three fade
starts, not one: `func_80189128` (26 + ~40 calls), `func_80189230` (fade
from the current colour, 18 calls, for example 0x80015E4C, 0x8008B9EC,
0x80120FBC and RELs) and `func_80188C48`. All three convert seconds to ms
with the same constant `lbl_8034BC00` = 1000.0 (sdata2, file 0x2EA1E0,
`447A0000`), and nothing else reads it. So one write scales every fade:

```
0434BC00 43FA0000    (500.0: every fade half as long)
0434BC00 43A6AAAB    (333.3: one third)
0434BC00 00000000    (diagnostic only: all fades instant, to see how much
                      of a transition is loading rather than fading)
```

Use it instead of the v1 C2 hook (both together would quarter the
`func_80189128` fades).

**v1 hook (superseded).** C2 at 0x80189154 (file 0x185E94, original `FFE00890`
`fmr f31, f1`): f31 = f1 × scale, using the free stack slot 0x10(r1)
(the frame is 0x30; GPRs are at 0x14–0x1C and colours at 0x8/0xC).
Scale ½:

```
C2189154 00000003
3D803F00 618C0000
91810010 C3E10010
EFE107F2 00000000
```

For ⅓ replace the first line with `3D803EAA 618CAAAB`. Every fade
(including menu and console fades) becomes ½ or ⅓ as long. No command is
skipped and every wait still waits for its fade to end. Script timed
waits (v[0] = timer + t loops on command 0x0A) and music fades are
unchanged.

### 7.15 Doors: skip the walk-up, open and knock animations (static; not tested)

Branch `faster-transitions`. The door actions in the A table go to player
states 09 (actions 0x01/0x03, own or open door, HUD label 0x0E) and 0x0C
(action 0x0B, someone else's door, label 0x10). The state advances with
`func_80031F78` (player+0x1364 += 1, then runs the new state's init from
`lbl_802A3AA8`, 0x3C per state), so a door is a fixed chain:

| state | handlers (init / per-frame / – / update) | what it does | gate |
|---|---|---|---|
| 09 / 0C | 0x8003549C / 0x800354FC / – / 0x80035544 | walk to the door along a path (`func_80175EC0`, door id +0x1388) | path done: +0x1450 == 0 (`bne` 0x8003555C) |
| 0A | 0x80035578 / 0x80035638 / – / 0x800356D8 | door animation 0x19 (`func_8007C19C`), slide to the door over 10 frames | anim done (`func_8017D7EC`, `beq` 0x80035738) and counter +0x1368 ≥ 10 (`blt` 0x80035744) |
| 0D | 0x800357E0 / same / – / same | knock animation 0x1C | same |
| 0B / 0E | 0x80035884 / 0x80035894 / – / 0x80035914 | walk in, then the room change (`func_8017775C`) | no event running (+0x680 == −1 and +0x58C == 0) |

0x800356D8 also guards on "no event running" and then calls
`func_80011680` (the door request) before advancing; that stays. None of
these states opens a message. "It's locked." / "No one must be home." /
"Closed..." (system.mes 0xAA–0xB1, 0xCC) come from elsewhere (the A
action or the door's script), so they are unaffected.

**Gecko** (main.dol; original words checked):

```
0403555C 60000000   # 0x8003555C (file 0x3229C) was 40820008: walk-up ends at once
04035738 60000000   # 0x80035738 (file 0x32478) was 41820094: don't wait for the door/knock animation
04035744 60000000   # 0x80035744 (file 0x32484) was 41800088: don't wait 10 frames
```

Both copies of the state table (outdoor and indoor) use these handlers,
so entering and leaving are both covered. The player is not moved to the
door first (the warp sets the position in the new room).

**Why the fade codes did nothing (open).** The door request
(`func_80011680` with `lbl_802971C8`) may drive a screen effect of its own
(ScreenEffect.cpp / ScreenEffectBase.cpp) rather than `func_80189128`. If
so, door fades are timed there, possibly per frame. Not traced yet.

#### 7.15.1 Door sequence, corrected (static; v1 codes failed in Dolphin)

- Kernel runs three phases every frame (0x8017CD7C/CDC0/CE04, ptmfs 0x802C9F38/44/50 → task vtable +0x10/+0x18/+0x14). For the player these are func_80031144 (slot +0xC, always), func_80031484 (slot +0x18) and func_80031504 (slot +0x24), the last two only when no event (0x680 == -1 && 0x58C == 0). Slot +0x30 is the message handler (0x800383A0 = ignore all; 0x8003872C = wait for msg 0x31).
- Runtime table lbl_802A3AA8 is zero in the DOL (filled at boot); its rows match the template at 0x802A01F0. Door states: 09→0A→0B (open), 0C→0D→0E (knock), and a second set D2→D3→D4, D5→D6→D7 using the same functions. lbl_802A7768 is not a player-state table.
- A-press (0x800437E8 open / 0x80043828 knock): sends msg 6 to the target object (+0x1388) and reads its reply. 0 or 2 → set state 09/0C. Any other reply → no door state. This reply is where closed/locked/nobody-home messages and some events come from.
- 09/0C: walk the path (+0x1434) until +0x1450 == 1.0 (0x80035544).
- 0A/0D init: start motion 0x19 (open, 0x80035614) or 0x1C (knock, 0x80035860) through func_8007C19C. These are the only two callers.
- 0A/0D slot +0x24 (0x800356D8): wait for motion end and 10 align frames, then send msg 0x1C to the door (room-change request, 0x800357B4) and go to 0B/0E. The game skips the motion and the waits when player+0x135C→+0x148 == 2.
- Why v1 failed: all three patched branches run every frame and are in the path. But the motion is started in 0A/0D init, which no code touched, and 0B/0E keep playing and aligning it. So the animation still played in full.
- v2: take the game's own +0x148 == 2 route everywhere, nop the knock start, keep the walk skip:
  `0403555C 60000000` `040355C4 48000054` `04035670 48000050` `04035724 48000024` `04035860 60000000` `040358D0 4800002C`

#### 7.15.2 Real door states, from Dolphin RAM dumps (supersedes 7.15/7.15.1)

- Dumps: player object at 0x80A8A600 (field) / 0x80C97AE0 (other map); its vptrs are at +0x10. v2 patches were present in RAM, so the codes do apply. 09–0E are not the field door path.
- A idle: state 0x01, motion 0. B own house: state 0x34, motion id 8. C knock: state 0x5E, motion id 9. No event (0x680 = -1).
- Motion IDs come from func_800288E8: u16 table 0x80249230[id*8 + variant*2] → ptr table 0x8029BECC → 0x18-byte descriptor.
- Shared state blocks (many door types; A-press jump tables at 0x80043CA0 and 0x80043DBC):
  - WALK 800457FC/8004590C/800459D0: motion 2 plus a path; ends when the path is done (0x800459F0).
  - ENTER 80045A3C: motion 8; 30 frames (0x80045AB8), then msg 0x1C to the door, then a wait state.
  - KNOCK 80045E18: motion 9; until the motion ends (0x80045E9C).
  - AFTER-KNOCK 80045F10/80045F6C: motion 0xA; 2 frames (0x80035D08), then msg 0x1C.
- v3: `040459F0 60000000` `04045A44 38800000` `04045AB8 2C000000` `04045E20 38800000` `04045E9C 60000000` `04045F18 38800000` `04045F74 38800000` `04035D08 2C00FFFF`

#### 7.15.3 Player control waits for the fade-in (static)

- lbl_80012844 is a scene state used by both SceneWorldMap (main.dol) and SceneRoom (wlp2 REL). While the fader is busy (func_80189338, fader+0x60 == 1) it returns. Once the fade-in ends it sets lbl_80349218+8 = 1 (player control on; door states clear it) unless lbl_80349194+0x49 != 0. It then moves to the idle state lbl_800128B8.
- Patch: `04012864 60000000` (was 40820040, file 0xF5A4). Control is enabled on the first frame of that state; the fade still plays.
- Dump D (paused mid fade-in after entering the house): player state 0x29, control flag lbl_80349218+8 = 1 (the 04012864 patch was active), fader busy. State 0x29 (map arrival) slot +0x18 (0x80034B44) returns while the fader is busy (0x80034B64). After that it picks the next state from g_system+0x60 (0 = normal control; 0xCC/0xCE/0xD9/0xE1/0x12/0xB0 for special cases).
- Patch: `04034B64 60000000` (was 40820130, file 0x318A4). Keep `04012864 60000000` as well.

#### 7.16 Run animation speed (static)

- Field state 01, slot +0xC (func_80042CA8): func_8003083C gives the stick level. 0 → motion 0 (idle), 1.0 → motion 3 (run), otherwise motion 2 (walk). Walk/run play rate = 30.0 × player+0x1370 (move speed) / 1.5. It is set through func_8007C100 → func_8017D74C (motion player +0x8 = rate). So the animation speed follows the movement speed.
- Run-only rate scale: C2 hook at 0x80042D90 (`fdivs f1,f1,f0` EC210024, file 0x3FAD0) multiplies f1 by a constant built with lis in r12 and staged at 0x8(r1) (free in this 0x10 frame).
  `C2042D90 00000003` `EC210024 3D803F40` `91810008 C0010008` `EC210032 00000000` (0x3F40 = ×0.75). The walk branch has the same fdivs at 0x80042DC8.

#### 7.17 Bridge footstep material (static)

- Collision triangle attr u16: the low nibble looks like the surface material. The vanilla bridge deck (X 182–192, Z 147–151, Y 10) is all 0x?004; the ground is 0x?008. The added bridge deck (X 183–193, Z 262.4–266.6, Y 19.28) is 6 copies of 0x0008.
- woodstep.py sets those 6 copies to 0x0004 in mapr1.arc / mapr2.arc, in place and at the same size. The deck-version sources are b0592293… / 20179e48…; the outputs are 2d95b533… / ce1e495e…. That 0x4 is the wood footstep sound is inferred from the vanilla bridge, not confirmed in code.

#### 7.18 Options in the bed menu: findings (static + dumps H/I)

- Choice window class (main.dol). It opens with func_80105110(win, style, r5 = item count, r6 = text, r7 = start cursor, r8 = cancellable, r9 out). The count is stored at win+0x2C and the cursor at win+0x28. The input step lbl_80105488 wraps Down/Up against the count; on A it puts the cursor in win+4, on B (if cancellable) -1. Dumps H/I: window 0x80AB8160, count 3, cursor 0→1, text buffer 0x809B7820.
- Bed menu in wlp1.rel: request switch (table at module 0x4B368), request 0x21 → msg 0x96, 0x22–0x25 → msg 0x97 (separate text with Alarm as line 4). Close switch at 0x4B41C. Which close case handles the bed menu is not settled.
- Text: newline 0x01, space 0x02, glyph 2 bytes. build_optmes.py adds "\nOptions" to 0x96/0x97 and points 0x95 (debug "Felicitations…") at 0x9E. The file stays 0xCAE0 with 48 bytes spare. RAM system.mes in dump H == skipintro out5 (sha1 3677d7b4…); output sha1 64278eae….
- BGM: .adp tracks are hardware DTK streams. Their volume is set via AISetStreamVolLeft/Right = func_801C1980 / func_801C19AC (AI 0xCC006C04), driven by the stream fader object at func_80129B1C (+0xE0/+0xF0). Farm/event music (BOKUJYO*/EVENT* .arc+.samp) is sequenced, not streamed: not covered yet.
- SFX master: not found. lbl_80349180 (SoundManager) fade +0x250/+0x254/+0x260 (func_8014FE20) feeds func_8014D308 per sound in a list; its scope is unknown.
- Test codes: count hook C2105110 (r5 = line count when the text starts "Sl" and has one more line than r5); BGM ×0.5 hooks at 0x801C1980 / 0x801C19AC.
- Test 1 result: Options shows; picking it opens the Diary save screen. So the room code treats choice 3 as Diary, and the choice has to be caught in the box.
- v1 hooks (sources in scratch opt/hooks):
  - 0x80105554 (A in a choice box; original `lwz r0,0x28(r30)` 801E0028). If the box text starts "Sl", count ≥ 4 and cursor = last: save text/count/window and reopen the same box with a 2-line BGM/SFX text (func_80105110, state reset to idle 0x802BD660). Then skip the result (jump to 0x80105598).
  - 0x80105488 (input step entry; original `stwu r1,-0x10(r1)` 9421FFF0). In options mode: B reopens the bed menu with the cursor on Options; Left/Right (guessed bits 0x40000/0x1 and 0x80000/0x2 in pad +0xC) change the attenuation of the cursor row and reopen.
  - 0x801C1980 / 0x801C19AC: stream volume × (10 − BGM atten) / 10.
  - Data at 0x80000E80 (zero in all dumps; trace/FP-assist vector tail): +0 mode, +1 BGM atten, +2 SFX atten, +4 text, +8 count, +C window, text buffer at 0x80000E90.
  - SFX is stored but not applied yet.
- v1 result (after the A-counter diagnostics were turned off to free Gecko space): the box opens and the numbers change. The music is unaffected, and B shows an empty box: win+0x18 is the box's own text buffer, which our text overwrote.
- MusyX: sndMasterVolume = func_801DABD8(vol u8 0..127, time, music, fx). It calls synthVolume func_801D9B48 with group 0x15 (music) / 0x16 (fx). Game wrappers: func_80189DD8 (music), func_80189D7C (fx).
- v2: h1 copies the bed text to 0x80000DA0 and sets mode 2; h2 opens the box on the next frame, handles Left/Right/B, and calls sndMasterVolume directly with the bypass flag DATA+3 set; h4 (0x801DABD8, original 9421FFE0, file 0x1D7918) records the game's last request per group (DATA+0x10/+0x11, |0x80) and scales it; the stream hooks stay.

### 7.16 Item models: real.gpl vs symbol.gpl, and the Ax (tested in Dolphin)

- Both files come from `commonall.arc` (RAM copies sit 0x95A20 apart, the same as in the archive).
- Item table 0x80282DF8 (0x24 per item): +2 = symbol.gpl model, +4/+6 = symbol.tpl textures;
  +3 = real.gpl model, +8/+A = real.tpl textures.
- `func_80011F68`: if item +3 == item 0's +3 (0x1A), draw the symbol.gpl model (held like an item);
  otherwise the real.gpl model (held like a tool). The rucksack grid icon uses symbol.gpl (+2) always.
- real.gpl model 2 (brush2) is used by no item. Ax (0x502) now: real model 2 (generated axe, appended
  after model 26), real texture 14; symbol model 122 'ono' replaced in place by a rotated copy.
- symbol kuwa models = real ones transformed: (x,y,z)_sym ≈ (-y,-x,-z)*0.907 + (6.3,4.3,2.1).
- Names: item.mes (file 0x44), entry = item id, plain glyphs ending 00. Descriptions: itemdocNN,
  itemdoc03 entry = item - 0x3ED.
- For a future "item get" animation: the rucksack description view spins the item's 3D model above
  the text box (dump RDesc.raw, description of the Ax open). That spinning-model view is the thing to
  find and reuse.
- Tool hits (static, 2026-10-29): A handler `func_80043120` actions 0x0F (0x800438A8) and 0x12
  (0x80043954) send a type-1 message {item = r26} to the probed object (`func_8004579C` +
  `func_80011680`), then enter the swing state (0x79 / 0xAD, enter 0x80032F7C). The object's own
  handler does the effect (tilling etc.); the swing state never does. Ax no-hit code: C2 hooks at
  0x800438F8 / 0x80043960 skip the send for item 0x502 and jump to 0x8004390C / 0x8004397C with r3 = 0.
- Tool stamina (static): swing state calls `func_8004D7AC(ctrl, 0xF, item, charge)` → `func_8004E330`
  picks a row of the s16 table 0x8024ED38 by item (hoes 0x4DE–0x4E0/0x4E3–4 → row 0x12 = 50;
  0x4E1/0x4E2 → row 0x13 = 200; unknown items → row 0x21, category 0 = no cost). The cost
  (row × charge × `func_8001216C(item)` % [0x4E1/0x4E8 120, 0x4E2/0x4E9 150, else 100] × condition)
  accumulates in ctrl+0x2C/+0x30 (u16 pool, u8 level = pool/1000+1, max 5). Heavy/normal/Light hoe
  costs are identical in this data. Ax code: row 0x12 at 0x8004E3B4, factor 120 at 0x8001216C.
- Stamina/fullness (RAM diff W1/W2/W3 + static): ctrl = game+0x11B80. +0x04 stamina (max +0x08 =
  100000, min +0x0C), +0x10 refill target; +0x14 fullness (max +0x18 = 1350000, min +0x1C).
  Hoe swings: stamina 99749 → 61949; idle: back to 100000. Fullness falls with time, faster with work.
  Drain `func_8004BE3C` (called 0x800320BC): base × skill scale [+0x160 category 1 → level +0x2E,
  2 → level +0x32; (3450 − 650·level)/400] × +0x154 × 400 / 3,000,000, subtracted at 0x8004BEF4.
  So the "skill" pools +0x2C/+0x30 are tool proficiency that cuts stamina drain (×7 at L1 … ×0.5 at L5).

### 7.17 HUD (opguide) and the stamina bar (static; first in-game test pending)

- HUD object built by `func_80082B94`; files `opguide.agc` / `opguide.tpl` (commonall.arc) loaded by
  `func_80082AB0`. Per-frame method `lbl_80082F94` → `func_80083814` (sprite updates, `func_800E2C58`) →
  `func_800838D8` (2D setup `func_800E111C/115C/11CC`, then each sprite's vtable+0x18 draw).
  Sprites (0x154 each): +0x74 ×4, +0x5C4 ×4 (flags +0x4C), +0xB14, +0xC68, +0xDBC, +0xF10; clock +0x1064.
  Set up in `func_80082FE0` with `func_800E23B4(sprite, layout +0x1278, group, entry, 0, &params)`.
- AGC format (magic C1C7C3C6 = "AGCF" in EBCDIC): u32 nGroups, u32 groupTable; group = (count, off);
  entry (0x14) = [nElements, elemPtr, ?, 0x10, ?]; element (12) = [nQuads, quadPtr, s16 x, s16 y]
  (screen offset from centre 320,240); quad (0x2C) = [u32 tex, s16 x0,y0,x1,y1, 4× u32 RGBA, f32 u0,v0,u1,v1].
  Group 4 entry 0 = the purple disc (+0xDBC), always drawn with the HUD.
- Stamina bar test 1: atlas 256×96 RGB5A3 added as opguide.tpl texture 2; six elements appended to
  group 4 entry 0 (frames, fills at 75 % / 60 %, apple, face). Tools: scratchpad hud/build_hud.py,
  pack_u8clz.py.
- Live fills work (in-game): writing quad x1 / v0 / v1 in the loaded agc ([0x80349110] + offset) takes
  effect the same frame (layout accessors `func_801812B4` read the raw file). Too many Gecko codes made
  the C0 codes silently not run; keep the list short.
- Player: HUD object = player + 0xDC (r3 in `lbl_80082F94`); player state id at +0x1364, position +0x4C.
  No stable global pointer to the player exists (checked 34 dumps). HUD v2 code: C2 hook at 0x80082F94
  does the fills and slides our six elements (y at agc +0xE4A … +0xE86) up when the position changed in
  the last 20 frames. State in 0x80005070..7F.
- v02 build (scratchpad v02/: v02.s, v02.ld, make_v02.py): caves in .init padding 0x800035B0, 0x800036F8,
  0x800037E0, 0x800038E0, 0x80003E00, 0x800040E0, 0x800048E0 (all zero in every dump; 0x80003DF0 is
  written at runtime, avoided). Whistle's second word lives in the boot-built player state table, so it is
  baked as the source constant 0x802A0C48 (80034F44 → 80034364; it alone feeds 0x802A4500).
- Name (v03b): farmer name = game + 0x11D08 (text of a name object at +0x11D00, vtable 802BCE04; "A" then "Connor" across two saves). game+0x11D35 (getter func_800FF358) stayed "A" in both saves, probably the farm name. game+0x2B284 is only string.mes's default "Pete". Glyph textures must be RGB5A3: IA4 renders garbled in the HUD.
  font.tpl tex 0 (1008×648 I4) = 24×24 cells, 42 per row, cell index = low byte of the glyph code.
  Glyph atlas (A–Z, a–z, 21×21 cells, white + 1 px outline) is opguide.tpl texture 3 (IA4). Layout gets
  a 7th element with 12 quads; hud_name (v03.s) writes x0/x1 and UVs per letter each frame.
  Watch for the PPC r0 trap: addi/subi with r0 as base reads 0 (caught twice in v03).

### 7.18 Postman event: groundwork (static)

- Seeds (item.mes `<26:crop>` + " Seed"; farmcrop.mes names): crops have 12 seed items each, trees 3.
  Gen1 crops 1–4, 32–35 (Tomato 0x11B …); gen2 5–18, 36–49; gen3 "Layer" 19–31, 50–60;
  trees gen1 61–65 (0x3EB …), gen2 66–75, gen3 76–84. Seed map: scratchpad event/seedmap.json.
- C/D reward pool: Coin 0x442, Fossil 0x446, Moon Ore 0x454, Sugar Ore 0x455.
- Ax already can't be dropped/shipped/sold/stored/gifted (tool flags) — tested.
- Disc has a dev folder test/: text lists of event flags (free slots 50–157, 171–189; resets at
  158 day / 159 month / 191 year), conditions, counters, OCC events; TSCR .sb scripts (RIFF, 8-byte
  ops; 0x17 push, 0x25 call) incl. 5000_getkuwa4 (get-item), 6100_bahnrun (bahn = Wally).
  No TSCR in RAM; real events likely in Chapter1–6.arc / EventCondition_C0x.arc / NPC_NormalTalk_n.arc.
  Correction: bahn/ban = Van (the travelling merchant, bahn.mes is his shop text); Wally = suary.mes /
  sua_0.arc (character order Sebastian, Wally, Chris, Hugh = seba, sua, kuri, hyu).
- Event scripts: ChapterN.arc (U8, entries unnamed "@", each CLZ) hold RIFF "SCR " scripts with chunks
  CODE (u32 count + 8-byte instructions [u8 op][u8 flags][u16 operand kind][u32 value]), OPT, STR, "PT".
  Same format as test/Script/*.sb (test.arc = the 46 dev scripts, compressed). 80 scripts parsed:
  ops 1,2,7–30,36,37; operand kinds 0x0000, 0x1200, 0x1300 (immediate), 0xF877 (frame-relative), …
  Interpreter step: func_80186208 (vm+8 code, vm+0xC pc, flag bit 0x80 of byte1 → add vm+0x4D8;
  jump table lbl_802CA310[op], op ≤ 0x25). Native commands: func_8010C604 (0xDE commands).
  NPC_NormalTalk_n.arc = per-NPC talk tables (different format). ban_0.arc (act, gpl, skn, 3 tpl, tam)
  + ban_0.anm.arc (22 animations) is Van, not Wally.
- Script VM ops (func_80186208, table 0x802CA310): 0 nop, 1–6 = += -= *= /= %=, 7–11 + - * / %, 12/13 && ||,
  14/15 ++ --, 16 neg, 17 not, 18 cmp (push -1/0/1), 19 load var, 20 store var, 21 dup, 22 pop, 23 push imm,
  24 jmp, 25–30 jlt/jle/jz/jnz/jge/jgt (pop), 31 call, 32 ret, 33–35 frame set/enter/leave, 36 end,
  37 native call (value = command, via vtable+0xC → lbl_8010B740 → func_8010C604). Stack vm+0x20 (100),
  vars vm+0x1B8, fixed-point shift vm+0x1B4 = 7 (#128 = 1.0). Operand flag bit0 = frame-relative.
- Native command signatures: lbl_802BDF00, 0x24 each: u8 nargs, then u32 arg types (1 int, 2 float).
  Per-command handler + callee list: scratchpad event/cmds.txt. Disassembler: scratchpad scrdis.py.
- Script numbers are fixed-point ×128 everywhere (cmd_4F(167808) = give item 0x51F). cmd_04(file, msg, c) =
  func_801020E4 message; polled: pushes -1 while open, then the result (choice). Message file IDs: table
  lbl_802517E0 (0 badog … 0x23 takakura, 0x31 event, 0x32 debug, 0x33 system, 0x44 item, 0x45 farmcrop).
- Event start: func_8010AAC4(mgr = [0x803491BC], eventNo, 0, 0). eventNo < 300 → current ChapterN.arc
  script (eventNo − chapter×50); eventNo ≥ 300 → Common.arc U8 node (eventNo − 300); node 0 is the root, so the first script is event 301 (in-game test: 405 ran the 'Chop the tree?' script, my index 104). Archives: mgr+0x450C
  chapter, +0x44E4 Common.arc, cond data +0x4538; names table lbl_802BDA88 (+0xF0 chapter/cond pairs,
  +0x1B0 NPC_NormalTalk_1–6, +0x1D4 "Common.arc").
- Script details (static, 2026-10-29): RIFF size field = whole file length; kind u16 is ignored by the VM.
  push of a variable address (kind 0x6500) + `assign` stores and leaves the value; cmp(a, b) pushes
  raw 1 / -1 / 0 for a>b / a<b / a==b (lbl_803489C0..C8); mul = (a·b)>>7, div = (a<<7)/b, mod = raw a%b;
  jumps test the popped value against 0. cmd_04 is polled while it returns 0; Yes/No answer 1.0 = first
  choice. Yes/No markup in a message = `40 00 00` (system.mes); `<25:8000>` = item name from message
  param 0, set by cmd_05(slot, value) (msgobj+0xA8). cmd_46–4C = chapter, year, season (0–3), day (0–9),
  hour, minute, second (time units of 1/10 s). cmd_51 = held item (ctrl+0x144), cmd_52 = +0x148,
  cmd_53(item) = rucksack count, cmd_56 = clear the hands (assumed), cmd_D3/DC(item, n) = add/remove,
  cmd_4F(item) = give, cmd_91 = spawn an object/prop (not the get-item display), cmd_94/96 = flag set/get.
- Postman test 1 (scratchpad event/build_postman.py, scrasm.py, mesenc.py, vmsim.py): script appended
  to Common.arc as node 106 (event 406), lines appended to event.mes entries 10–16. Trigger Gecko C2
  at 0x80213CFC: hold Z + press D-Up → func_8010AAC4(mgr, 406, 0, 0). Seed seasons come from the user's
  list (unverified); gen-3 "Rare Crop #N" mapped to LayerN (N≤9) / Layer(N+1) (N≥10); trees left out.
- Postman test results (Dolphin): event and text work. cmd_4F routes items by item-table byte +1 to
  storage containers (game+0x14A8 / +0x14D0 / …), not the rucksack; switched to cmd_D3(item, 1) =
  func_8004FDA0(game+0x50). Randomness: the game's rand() is func_8017D3E8 (LCG 0x41C64E6D, seed
  0x803494B8); no script command calls it, so the trigger writes rand() & 0x7FFF to event counter 29
  (game+0x12208; cmd_95(i) reads game+0x12194+4i, pushed <<7) and the script reads cmd_95(29).
- Disc is full (1,459,978,240 bytes). Common.arc must be rebuilt no larger than 0x3E16C: event/clzc.py
  (optimal-parse CLZ) recompresses the 105 scripts 3.8 KB smaller; Postman script 13.9 KB → 2.4 KB.
  Postman text lives in debug.mes entries 0–6 (file 0x32, size kept at 0x4C80).

### 7.19 Disc space and unused-event survey (static, 2026-10-30)

- Disc layout (gclist of the US disc): 1731 files, 528 MB. Free gap 0x00907460–0x379EB144 (~880 MB)
  between the low and high file blocks; gcbuild only uses it with --place. sound/ 105 MB, .thp movies
  125 MB, .tpl 176 MB. Unused-looking folders are tiny: test/ 0.7 MB, jp/ 1.2 MB, CVS 0.06 MB.
- Event numbering: eventNo − 300 (Common) or − chapter×50 is the U8 **node** index (ARCFastOpen
  func_80203BF0, node 0 = root), so archive file k is event base + k + 1.
- EventCondition_C0n.arc: 10 files of 32-byte bit-packed records; event number = (b0 | b1<<8) & 0x1FF
  (checked: poultry-birth records → 328 = Common file 27 "2012a_BIRTHANIMAL_POULTRY"). 104 events.
  test/text/EventCondition.txt names the 72 condition types (dead/birth animals, trades, dig site…).
- Message file IDs: table lbl_802517E0, pairs (@name, name.mes): 0 badog … 35 takakura, 36 tsurutan,
  37 vesta, 38–40 *_wife, 41 console, 42 other, 43–48 son_*, 49 event, 50 debug, 51 system, 52 minigame,
  53–58 tv*, 59–62 itemdoc*, 63 line … 68 item, 69 farmcrop.
- Script STR chunks hold developer debug strings (Shift-JIS) naming events, e.g. Chapter1 file 12
  "Nami oshikake (visit) events 1–5", 13 "Nami omiai events", 2 "chapter 1 end event", Common 24
  "Script/Common/2008_DEADANIMAL.gcs". Dump: scratchpad chap/str_all.txt.
- Native callers of func_8010AAC4 with constant events: 7, 12, 20, 28, 304, 323, 331, 333, 353, 354,
  388, 394, 396, 397, 399–401, 403–405. Others pass computed numbers (talk tables, chapter changes).
- Text survey (US .mes, 71 files, 17,469 messages; decoder in scratchpad chap/, dump chap/mesUS_all.txt):
  references collected from all scripts (cmd_04/A4–A6 with constant file/msg) and NPC_NormalTalk_1–6
  (u16 file, u16 msg pairs). Many "unreferenced" lines are native-driven (gifts, tools, rumours), so
  unreferenced ≠ unused.
- Harvest Sprites = david.mes / ebony.mes / flat.mes (US names Nic, Nak, Flak). Lines 5–43 of each form a
  "find Wonderfuls so the Harvest Goddess comes to the Spring" activity (searching, befriending Mukumuku
  and an animal, dancing for crops, a singing voice, star wishes, a yearly Goddess test that fails).
  No script or talk table uses them; Common file 75 (sprite intro) uses only 0–4. Native callers of
  func_801020E4 with file 6 are only ebony 70–74 (GBA link). Not proven unused: sprite AI may compute ids.
  kris.mes 171–172: Kris throwing offerings into the lake, "the Goddess hasn't appeared". item 0x43E
  "Goddess Drop" exists.
- tai.mes is a byte-identical copy of tay.mes and is not in the message table (never loaded).
- JP and US .mes have the same message counts (except string/structure, US larger): no JP-only text.
- other.mes 295–349: untranslated Japanese developer menu text (choice lists), unreferenced.
- dreaming_normal/good/bad.thp = 0.9 / 1.2 / 2.1 MB.
- gcbuild (scratchpad gc/gcbuild.py, sha1 c9b4ecaf…): a grown replacement with no room after the last
  file now goes to the lowest 0x8000-aligned all-zero gap outside every file, system area and other
  replacement (--iso). Tested on a synthetic full disc (junk in a gap is skipped; two grown files don't
  overlap); output identical to the previous version when the disc end has room.
- other.mes 295–349 (rendered with font.tpl texture 0: 42×27 cells of 24 px, index = glyph − 0x8000):
  a developer "condition branch" (条件ぶんき) menu for Takakura's shipping / animal-trade / tool-purchase
  events: branches 0 (player), 1 (shipping + tool purchase flags), A (shipments), B (animals),
  C (Takakura memo flags 1·2 / 3·4), D (seed/item purchase flags); questions such as "Where is the
  cow for memo flag 3·4?", "Who is the fiancée?", "Did he buy a hoe / sickle / watering can / clippers?";
  results "Event end A–H"; and "Sorry, this event doesn't happen under this condition, bye-bye!".
  Many scripts pass message ids from variables, so "unreferenced" text is only a candidate list.

### 7.20 Character model format (ban_0.arc = **Van**, not Wally; Wally = sua_0.arc; static, in progress)

- ban_0.arc: ban_0.act (skeleton), .gpl (mesh), .skn (skin), _b0.tpl (body), _f0_e / _f0_m.tpl
  (eyes / mouth), .tam (texture animation, magic F4E1EEED; face frames). ban_0.anm.arc: 22 animations
  (header 00AC7472, 0x32 = 50 tracks = one per skeleton node).
- .act: magic 007B7960, u32 node count (50), u32 0xC, u32 node table (0x20), u32 name (→ "ban_0.gpl").
  Node 0x1C: [xform off, prev sibling, next sibling, parent, first child, u16 FFFF + u16 index, flags].
  Transform 0x34: u32 flags, scale xyz, quaternion xyzw, translation xyz, pad. Root at y ≈ 1.005.
- .gpl: magic 005BBC61, 1 model at 0x1C; same block layout as real.gpl but positions are s16
  (pos hdr count 0x703 = 1795 vertices, fmt byte 0x3D). .skn header 00190025 001D0D00 + offsets.
- .gpl (character) model block at file 0x1C: [pos hdr 0x1C, colour 0x5464, uv 0x5470, normal 0x61A4,
  material 0x61B0]. Positions+normals interleaved s16, frac 13 (fmt 0x3D, 6 comps, 1795 vertices, stride
  12); the normal header points 6 bytes into the same data. UV s16 (841). Four display lists (mat list:
  [u8 01, u8 n, …, 1111000k tex, dl offset, dl size]); prims 0x90 triangles, per vertex u16 pos, u16
  normal, u16 uv. The pos buffer holds the bind pose in model space (T-pose, y 0…1.61, x ±1.17).
- .skn (CPU skinning, func_8019C080, locked-cache DMA): header u16 n1 (1-bone, 0x40 each), n2 (2-bone,
  0x74), n3 (3+-bone additive, 0x44), u8 frac (13); u32 table offsets t1 0x24, t2 0x664, t3 0x1728,
  then flush range (+0x14 start, +0x18 size) and an index list (+0x1C, count +0x20) for type 3.
  1-bone entry: mtx 0x30 (runtime), +0x30 src, +0x34 dst (byte offset in the gpl pos buffer), u16 bone,
  u16 count, u8 src misalignment. 2-bone: 2 mtx, +0x60 src, +0x64 weights, +0x68 dst, u16 b1, b2, count,
  u8 align. 3+: mtx, src, weights, dst, index list, u16 bone, u16 count. Sources are model-space bind
  positions (same vertex for both bones), so the engine's bone matrices are world × inverse bind.
  Data area starts at 0x1EE0 (after the three tables). Rigid skin = n1 groups only.
- Skeleton rest pose (act) is a T-pose matching the mesh (picture: scratchpad pm/wally_bind.png).
  Bones: 0 root, 1 ground, 2 pelvis, 4–9 / 43–49 legs, 10–12 spine, 13–21 / 34–42 arms (shoulder,
  elbow, wrist, hand, thumb), 22 neck, 23 head, 24 head top, 25 back of head, 26–33 face.
- .anm (anm.arc file): magic 00AC7472, u16 track count (50); tracks of 16 bytes [f32 length (59),
  u32 data offset, u16 kind (1 constant, 3 keyed), u16 node, u32 packed]. Constant tracks: packed
  byte 3 bit 0x08 = rotation, 0x01 = translation; byte 1 bits 7/6/5 = quaternion z/y/x omitted (zero);
  values s16 /16384, quaternion comps then translation xyz, padded to 4 bytes. The translations equal
  the act's bone offsets, so animations carry Wally's bone lengths.
- postman.dae: 615-vertex body + 13-vertex part, 15 joints "runningman", scale 0.001, height 6.69 →
  arm half-span / height = 0.51 (Wally 0.64).
- Wally = sua_0.arc (act 46 nodes, gpl 1282 vertices, skn, b0/f0_e/f0_m tpl; no .tam) + sua_0.anm.arc
  (8 animations, 0x2E tracks). sua_1 / sua_2.arc = same mesh with outfit textures b1 / b2.
  Material record [u8 1, u8 sel, u16 0][1111000k][dl][size]; sel FF = body tex (b0 #0), 02 = head tex
  (b0 #1), 00 = eye tpl frame, 01 = mouth tpl frame. Display lists mix 0x90 triangles and 0x80 quads;
  a vcd 0x3C list has 4-byte vertices (pos, normal; no UV). Renderer: scratchpad pm/wally.py + raster.py.
- Wally proportions (height 1.65): hips 35 %, shoulders/neck 51 % (head + hair = top half), hand tip
  ±39 %. Postman reshape test (pm/chibi.py, CH4: hip 2400, torso_y 0.62, torso_w 1.2, leg_w 1.35,
  arm_l 0.75, arm_w 1.35, head 2.05 wide / 1.6 tall, head raised 380): pm/cmp4.png.
- Postman source (full zip): postman.dae (body + 13-vertex mouth patch on bone_14), postman_00.png,
  Mouth/pm_mouth01 (closed) / pm_mouth02 (open) 32×32 half-face tiles.
- Postman shape chosen by the user: head 1.55× (rounded: jaw_y 0.8, jaw_w 0.88, crown 1.08, depth 0.85,
  ears 0.7, head_y 1.27, raised 260). Body candidates: current (torso_w 1.2, legs/arms ×1.35 thick) or
  slimmer (1.08 / 1.1 / 1.08), saved as scratchpad pm/postman_shape.json; renders pm/cmp6.png, cmp7.png.
- .anm fully decoded (scratchpad pm/anm.py; every Wally track accounted for): the u16 I called "kind"
  is the key count. Constant rotation, then constant translation, then keys. Rotation-only key: frame,
  q (comps per mask), q control; translation-only key: frame, xyz; both: frame, q, xyz, q control.
  Wally anims (sua_0.anm.arc): 0 idle (69 f), 1 walk (31), 2 arms-crossed idle (59), 3/4 talking
  gestures (80/89), 5 run (31), 6 jog (20), 7 bow (79). Node 3 = whistle. 2/3-bone skin groups are
  approximated in the preview renderer (spikes at the hands in pm/wally_anims.png are preview-only).
- Postman retarget (pm/retarget.py): joints moved to the reshaped Postman's positions (height 1.60),
  Wally's rest rotations kept; new local T = parent rest rotation⁻¹ × (target − parent target).
  Animation translations = new rest T + (anim T − Wally rest T) × 1.60/1.65. Rigid skin: each vertex
  → one Wally node (bone_0→4/20, 7→21/22, legs 7/8/10 and 14/15/17, arms 24/25/27 and 35/36/38,
  head 45). Nodes 6/13 and 9/16 never rotate (fixed offsets): thighs swing at 7/14 (up to 120° in the
  run), knees 8/15, toe roll 10/11 and 17/18, hands 27/38 in gestures.
  Preview: pm/pm_run.gif, pm/pm_anims.png. Not yet written to game files.

### 7.21 Character slots (static)

- Model table 0x80249A6C (base 0x80249A10 + 0x5C): 132 entries × 0x18 = [name ptr, f32 ×3 (size /
  collision / talk height?), u32 0, u8 animation-set index]. 0–109 people, 110+ animals (other layout).
- Character → model: u8 table at 0x8024A6E0 (base + 0xCD0), model = [charID×6 + chapter]
  (func_8002E634 / func_8002E7F0, chapter from func_8000FEE8). Character IDs = people.mes order
  (0 Pete … 11 Wally … 32–34 Nak/Nic/Flak, 35 Mukumuku, 36 Van, 37 DUMMY, 38 Tartan); 39 entries.
  37 DUMMY → dar_0.arc (model 74, sizes 1.0/0.79/0.62, anim set 0x1C) in all chapters;
  38 Tartan → hi.arc (model 75).
- Characters exist as objects in a list at event manager +0x630 (func_8010927C finds by ID at obj+0xD0).
  cmd_5A(id, show) shows/hides one character, id 74 = all 65 (0..0x40). cmd_85(actor, …, x, y, rot)
  places an existing actor (message 0x1F).
- DUMMY (37) is used as an actor in two events: Common file 53 (event 354, Van delivering a child's
  present: "Any child would love that") and Chapter4 file 2 (event 153).
- DUMMY = dar_0.arc is a **teddy bear** (orange bandana; 31 bones, 1089 vertices; anims: sit, stand ×2)
  — the present Van delivers (Common event 354) and a prop in Chapter4 event 153. Render pm/dar.png.
- Model load: func_8002D128 reads char→model→entry name at load time and opens the .arc by name
  (func_80190E94), unpacking act/gpl/skn/tpl into a 0x44-byte slot (table 0x802EB4D4), so changing
  the RAM model entry (name ptr / sizes) before a load swaps the model. func_8002C284(?, n) loads the
  special models 88+n (lbl_8024A2AC) into slots at 0x802ECE3C.
- Animation sets: table 0x80248B40, 73 records × 0x14 = [anm.arc name, subact, subanm, motion list ptr,
  u8 chapter preload mask (0x3F all, 0 = on demand)]. 14 = sua_0 (Wally), 57 = hi (Tartan), 71 = dar_0.
  Loaded by func_80027FAC(set, …) from main.dol and the .rel modules per area. Motion list = array of
  ptrs to 0x18-byte motion entries [u8 set ref (Wally 0x1C/0x1D, 0x0E, 0x88, 0x5C…; teddy 0x8E, 0x34,
  0x82), u8, u16 anim no/flags, u32 mask, u32 flags, …] — meaning of the set-ref byte not yet confirmed.
- Character file builder: scratchpad pm/build_char.py NAME OUTDIR → NAME.arc (act from Wally with new
  bone offsets, gpl rebuilt: 628 vertices s16/13, 2 display lists [body sel FF tex 0, mouth sel 01],
  4 material commands [01 sel FF tex, 03 1, 02 vcd C3C draw, 01 sel 01 draw]; rigid skn 18 groups of
  ≤128 vertices; CMPR tpls: b0 = body 128×128 + 1×1, f0_e = teddy's 58 frames (unused), f0_m = 36
  frames, open/closed chosen from Wally's mouth set) and NAME.anm.arc (Wally anims in order idle, run,
  walk, arms-crossed, talk, talk 2, jog, bow; translations retargeted in place).
  gpl material command list: 01 = [01 sel 00 00][1111000k tex][dl][size] set texture (+draw if dl),
  02 = [02][vcd][dl][size] set format + draw, 03 = [03][n] mode. Skin src/dst share the misalignment
  byte: real offset = off + al.
- First in-game test (pm/deliver_model1): Postman files under the teddy's names (dar_0.arc 62,976 B,
  fits; dar_0.anm.arc 28,608 B, goes to the gap) + Gecko: Z+D-Up → event 354 (Van brings the present),
  and model entry 74 sizes set to Wally's (0x8024A160 = 0.95, 1.58, 1.2).
- Model test 1 (Dolphin): event 354 showed the original teddy, so the disc dar_0.arc was not read.
  func_80190E94(name) first searches every mounted archive (list at [0x80349210], func_8019A3C8) and
  only opens the DVD file if the name is not found: map archives carry the character models used on
  that map (the house map has the teddy). A model name not in the current map's archive is read from
  the disc. Event 354 played out of context warps the player to odd spots afterwards.
- Model test 2: Common.arc gains file 107 = event 407 (scratchpad event/build_test407.py: data shifted
  by 0x20 for the bigger header): fade, warp map 1 (farm), hide all, player at (167.9, 119.6) facing
  0, character 37 cmd_72(37,0) + cmd_58 (167.9, 122.6) + cmd_59 180 + cmd_5A(37,1) + cmd_6C(37,0),
  camera cmd_14 (167.9, 2.6, 116) / cmd_15 (167.9, 1.0, 122), fade in, debug.mes 2, end.
  Map 1 = farm (Common file 1 places the player at 167.9/119.6 and Takakura at 167.4/136.8).
- Model test 2 (Dolphin): crash "invalid read from 0, PC 0x801A0A9C" (func_801A0A88 reads a U8 header
  through a null archive pointer: character 37's model/anim archives were never loaded), map 1 is not
  the field, and the player ended out of bounds. Characters are not loaded when shown.
- Only 33 characters have daily-routine records (game+0x124C4 + (k−1)×0x124, +0x24 = schedule id;
  k from the pair table 0x8024F594 via func_8007962C): 1–31, 35 Mukumuku → 32, 36 Van → 33.
  DUMMY (37) has none, so the schedule system never places it. cmd_84(char) returns the schedule id.
- Room code (wlp REL) loads DUMMY before its scenes with func_8002D128(37) (model; arg = character
  id), func_80027FAC(71, 0) (anim set), func_8007DECC([0x803491DC] character manager, 37) (creates
  the character, 0x17C-byte slot at mgr+0x4C+id×0x17C); Tartan the same with 38 / set 57.
  func_80109A90(event mgr, id) returns a character object (player = 0); position vector at +0x4C.
- Model test 3: trigger Z+D-Left = those three calls for 37; Z+D-Up = player x/z ×128 into counters
  27/28 (game+0x12200/0x12204), rand into 29, start event 408 (Common file 108: place 37 at player
  x+1.5, show, idle, line, motion 1, line).
- Model test 3 (Dolphin): crash at 0x80109AD0 (func_80109A90 walking the event's character list,
  null node): the list at event mgr +0x630 is only filled while an event runs. Fix (test 3b): the
  script reads the player's position with cmd_64(actor) = x, cmd_66(actor) = z (cmd_65 = y?,
  cmd_67 = facing), as Common files 1 and 53 do at their start; the trigger only loads 37 (D-Left)
  and starts 408 (D-Up).
- Model test 3b (Dolphin): works — character 37 loaded by the trigger and placed by event 408 next to
  the player, in the house and in the field — but it was the teddy both times: dar_0.arc is in an
  always-mounted archive. Test 4: the Postman as new disc files pm/pm_0.arc and pm/pm_0.anm.arc
  (gcbuild --add-dir); Gecko writes the names at 0x80000B00 / 0x80000B20 and points model entry 74
  (0x8024A15C) and animation set 71 (0x802490CC) at them (the loader's DVD path goes through
  DVDConvertPathToEntrynum, so a folder path works). Trigger moved to hold L+R (Z is the first-person
  camera).
- Model fix (model7, pm_0.arc 63,328 B, sha1 2d21709a…): the flat panel came from the skin write-back.
  func_8019C080 skins each 1-bone group in the locked cache and DMAs it back to the gpl vertex buffer
  (in place) in whole 32-byte blocks, so tightly packed groups overwrote the next group's first
  vertices. The builder now leaves spare vertices between groups (as Wally's file does), pads the
  buffer for the last group's write, and keeps to nodes Wally's skin uses (hips on 5/12, not 4).
  Skin matrix = world × inverse(rest world from the act) (func_8019E848). Earlier tests 5b/6 had
  still used the first build (62,976 B), so the panel persisted until model7.

### 7.22 Postman NPC outside events (static; stage 1 built, not tested)

- NPC slots: the NPC manager has 34 fixed slots (k 1–33 = routine characters, pair table 0x8024F550/
  0x8024F594); DUMMY (37) has none. Event characters are a separate actor class (ctor func_8007F328(obj,
  1, id), 0x2A8 bytes from heap 0x802F320C via func_8017A200; +0xD0 id, +0xD4 character slot, position
  +0x4C, direction +0x58), registered with the actor manager [0x8034923C] by func_8017CD5C(mgr,
  obj+0x70, 0xC000+id) (func_801092D0 = event "add character"); the manager updates and draws them.
  Methods: func_8007F994 set position (no state change), func_8007F9B8 set direction vector,
  func_8007F9D4 position + state 1, func_80080238 play motion (state 4), func_8007F910 show,
  func_8007F8EC hide, func_80081DEC set state. Character 37 motions (set 71 list): 0 idle, 1 run.
- Character slot draw: slot vtable+0x10 (lbl_8007BBA0) sets rotation/translation, culls and skins;
  func_8007BD48(slot) draws with the camera matrix.
- Player state each frame (func_80031144): position → game+0x29C78 (per character id×12), direction
  → game+0x29F84, current map → game+0x2A290 (id×4). Valley = map 1 (mapr1 collision; map 1 is the id
  compared most often). No event running: [0x803491BC]+0x680 == −1 and +0x58C == 0 (as func_8010AAC4).
- Clock: [[0x80349218]] in tenths of a second: hour = T/36000 % 24, day = T/864000 % 10 (0-based),
  season = T/8640000 & 3. Ground height: func_8001CB54([0x80349204], vec) → f1.
- Route (user's drawing, scratchpad viewer/route.png, route.json): 20 waypoints from the road end
  (144.9, 331) to Romana's gate (216, 51), 353 units, all on walkable ground.
- Stage 1 (scratchpad event/npc/build_npc.py → npc1/postman_npc1_gecko.txt): C2 at the pad update;
  Z+D-Left spawns the actor on map 1, it runs the route (0.12 units/frame), idles 10 s at the gate,
  runs back and hides; A within 2 units starts event 406 once (A cleared from the pad words); during the
  event it stands still facing the player; off map 1 it is hidden. State at 0x80000B40 ('PMAN' at +0x3C).
- Stage 1 test (Dolphin): spawn, run animation, drawing and the A-talk event all work. Faults: he faced
  the wrong way (event actors draw their facing from the rotator at +0x1C8: pitch +0x1F4, yaw +0x1F8 =
  atan2(dx, dz), set by func_80108094(rot, pitch, yaw); target yaw +0x20C), Stage 1b swapped the route axes on the
  assumption that viewer/route.json is (Z, X); in Dolphin he then never appeared, while the stage 1 route
  was right, so route.json is game (X, Z) for mapr1. Stage 1c: original axes + the rotator facing fix. No player collision
  yet (NPCs use a collider at NPC+0xC0: func_801520F8 init, func_80152218(col, id), owner at +0x34,
  registered through its vtable +0xC).

### 7.23 Postman NPC in main.dol (static; built, not yet tested in Dolphin)

- Stage 1x Gecko faults explained: the event-actor pool (func_8017A200, 0x802F320C, 0x2A8 blocks) is
  reused by the event system — a MEM1 dump showed the Postman's block holding the player's event actor
  (id 0) — so our actor was freed under us (crash / odd facing). Event actors: dtor func_8007F648(obj,
  flags) unlinks every node (func_80009904) and returns the block to the pool when flags > 0.
  State table lbl_802AADF8 (filled at boot from ptmf constants): 1 standing, 2 walk (path +0xF4),
  3 turn (rotator → +0x58), 4 motion (to state 1 when a non-looping motion ends); only states 2/3
  write +0x58. Draw step func_80081CD4: slot vtable+0x10 (lbl_8007BBA0) with dir = actor+0x58,
  yaw = deg(atan2(dir.x, dir.z)); model fronts are +Z (Wally and the Postman alike).
- Motion entry word 0: bits 31–25 = animation set, low 10 bits = animation; word 1 packs eye/mouth,
  sub-actor and sub-animation indices. Anim sets reload by name on every func_80027FAC call.
- Collider class (NPC+0xC0, 0x38 bytes): func_801520F8 init, vtable 0x802C5720, owner at +0x34
  (reads owner +0x4C pos, +0x58 dir, +0x64 map), func_80152218(col, id) size, vtable [3] register /
  [4] unregister with [0x80349204], [2] dtor (deletes when flags > 0).
- Flags: game+0x12078; func_801129A0 get, func_801129E0 set, func_80112A30 clear (cmd_96/94).
  operator new 0x80178E88 (size, file, line), delete 0x80179168.
- Arena: OSInit sets ArenaLo from BootInfo->arenaLo, else __ArenaLo 0x8035EFA0, or on the bi2 debug
  path _stack_addr (0x8035CFA0). main.dol text sections 2–6 are free.
- Build (scratchpad event/dol: pm.c, route.h, hook.s, pm.ld; make_pm_dol.py; package postman_npc/):
  C compiled with clang --target=powerpc-unknown-eabi -mcpu=750, linked at 0x8035EFA0 (3352 bytes),
  added as text section 2; OSInit patched so ArenaLo = 0x80360000 on both paths (0x801B0EE4/E8,
  0x801B0F2C); pad update end 0x80213CFC branches to it. make_pm_dol.py checks every site, writes the
  larger DOL in place or into an unreferenced disc area (boot.bin 0x420), tested on synthetic discs
  built from the original main.dol. Common.arc rebuilt from vanilla + event 406 that sets flag 61 once
  the player answers with milk (VM-simulated: no milk → no flag; Yes/No → flag 61).
- Behaviour: 8th, 9:00–11:00 on map 1 (and g_system map 1): model/anims of character 37 swapped to
  pm/pm_0 (names + sizes patched, restored when the visit ends outdoors); actor from operator new,
  registered with the actor manager (0xC025), NPC collider; place from the clock (in 9–10, wait
  10:00–10:15, back 10:15–11:00); A within 2 units → event 406 unless flag 61 (A swallowed near him);
  removed when the player leaves map 1 (model kept until the visit ends). Test: Z+D-Left starts a
  visit now, Z+D-Right stops it.

### 7.24 Postman: winding, menu lock, talk camera (static; pm10, not yet tested in Dolphin)

- Inside-out model: GameCube front faces wind opposite to the builder's. Wally's sua_0.gpl triangles
  disagree with their vertex normals (10 agree / 2298 disagree); the old pm_0 agreed (808 / 0), so
  the back faces were drawn (face seen from behind). build_char.py dl() now emits each triangle
  reversed (0 / 808); only the display lists change. pm_0.arc 63,328 B, sha1 d068193f….
- Item menu: X in player state 1 (func_80043000 area, 0x8004300C) goes to player state 3; state 3's
  enter (0x80034010) stores 0 to [0x80349218]+8 at 0x80034098, and its exit path stores 1
  (0x800341AC). pm.c only takes A when that byte is 1 (player free), and leaves the A press alone
  otherwise.
- Talk camera: event counters live at game+0x12194+4i; the script VM's counter get (sys 0x95,
  func_801129D0) pushes value×128, and VM div is fixed-point ((a<<7)/b, 64-bit). A scan of all
  163 scripts (Common, Chapter1–6, EventCondition, NormalTalk archives) found counters 0–3, 32–34,
  64–71 used; 4–31 untouched by scripts, and code reaches counters only through the VM. pm.c writes
  eye/target ×128 into counters 20–25 before starting event 406; the script starts with
  cmd_14(c20/128, c21/128, c22/128) and cmd_15(c23/128, …). Framing copied from Common event 35
  (eye ~1.8 in front at head height, aimed through the head): eye 2.3 in front + 0.7 to the side,
  1.5 up; target 2.0 behind him, 1.3 up. Not confirmed: that the field camera returns by itself
  when the event ends (original events end with fades).

### 7.25 Postman pm11 (after the pm10 test)

- pm10 in Dolphin: talk close-up and menu lock work; face winding fixed. Remaining: mouth too bright,
  camera too close / off-centre / level, crash "invalid write to 0x380a3db8, PC 0x8019FED8" walking
  into a building while he was out.
- 0x8019FED8 is in func_8019FECC (copies an animation key struct; callers in the animation player
  0x801A68xx and func_80156590). Likely cause (not confirmed): the room scene loads character 37 and
  reloads animation set 71 itself (7.21 notes), freeing animations our still-registered actor was
  playing, and with our names still patched. Fix: while the fader ([0x803491B8]+0x60 == 1, as
  func_80189338) is busy and we are not talking, despawn and unload the model and restore the names;
  if the map changes without a fade, only restore the names.
- Mouth: its vertices were a separate flat patch with normals straight ahead (mean (0, 0.05, 0.94));
  Wally's mouth normals tilt down ((0, -0.4, 0.65)). Builder now copies the nearest face vertex's
  normal ((0, -0.49, 0.47)) and tints the mouth frames by body-skin / mouth-skin (the tile was
  ~5-15 % lighter). pm_0.arc sha1 25b9000d….
- Camera: eye 3.4 in front, 2.1 above his feet, no side offset; aimed at him 1.1 up (≈16° down).
- pm.bin now built with -Os (3,840 B; -O2 was 4,176 B, leaving only 16 bytes below 0x80360000).

### 7.26 Postman pm12: door crash, "thanks" line (static; not yet tested)

- pm11 still crashed entering a building (PC 0x8019FED8/0x8019FEE0, writes to 0x93E1000C/10). The
  writer is func_8019FECC called from the animation player func_801A6878 (via Motion func_8017DB28 /
  func_8017D7FC, char-slot update 0x8007BAAC): it writes through a channel's +0xC target in freed
  memory. The fader check never fired: field doors don't use the fader (7.15).
- Scene change: doors call func_8017775C(g_system, 6, …), which stores the next scene at
  g_system+0x58 (and sets byte 0x80349011). g_system's update func_8017755C (one caller,
  0x8000AC70) switches as soon as +0x58 != -1 (-2 = back to the previous scene): func_80177D30
  builds the next scene in the same call, then +0x58 = -1. A per-frame poll can miss it.
- Fix: second hook at 0x8017755C (was 9421FFF0 stwu r1,-0x10(r1)) → pm_hook2 (pm.bin +0x14): if
  +0x58 != -1, pm_scene_change() despawns and unloads him (unless talking), then the original stwu
  and back to 0x80177560. make_pm_dol.py checks and patches both hooks.
- "Thanks": flag 62 (unused by every script and by code; code only uses flags 0, 1, 0x135,
  0x13D–0x142) set by event 406 when he takes the milk; the script starts with "flag 62 → debug.mes
  entry 7 'That hit the spot, thanks!' and end". pm.c talks when flag 61 is clear or 62 is set,
  and clears both on other days (not during a Z+D-Left test visit). debug.mes now goes on the disc
  too (sha1 39108c40…). pm.bin 4,124 B, ends 0x8035FFBC.
- pm13: refusing now has a follow-up too. Event 406 order: flag 62 → "That hit the spot, thanks!"
  (debug.mes 7); else flag 61 → "Can't you see I'm busy? Out of the way!" (debug.mes 8); else the
  milk talk. pm.c starts the event on every A next to him. debug.mes sha1 16e98598…, Common.arc
  4380af8c…, pm.bin 4,068 B.

### 7.27 Postman pm14: house crash root cause, run cycle speed (static)

- pm13 dump (user, after one crash entering a house; player map 20): our state fully released
  (actor 0, loaded 0, names back to dar_0), slot 37 set up by the room (teddy) — but set 71's loaded
  entry (0x802EA714 + 71×0x30, +0 = archive) still pointed at 0x80999460, which no longer held a
  U8 archive (now code: 91030264…). The room sets the teddy up from set 71 without reloading it,
  so its motion read channels from freed memory (bad write target 0x38210040 = `addi r1,r1,0x40`).
- load_animset (func_80027FAC) → func_801A06B8: entry+0 = func_801A632C(name), func_801A0734
  relocates the U8 in place; no free of the old one. Unload = func_800282A0(set) (func_801A06F4 →
  func_801A65C0 → func_80190944, clears +0/+0x2C/+4). release_model now unloads set 71 and puts
  back the 0x30-byte entry saved before our load.
- Animation step: anim state = {f32 time, f32 step, u32 loop, f32 length, …}; func_8019FF08 adds
  step to time each frame. Char slot motion at +0x54, its player at +0x94 with state pointers at
  slot+0x9C / +0xA0 (all characters 1.0 in the dump). pm.c writes 1.3 while he runs (route speed
  is from the clock, unchanged).
- pm.bin grew to 4,300 B (S ends 0x8036006C): arena low moved to 0x80361000 (0x801B0EE4 lis
  0x8036, 0x801B0EE8 addi 0x1000 (was 28030000), 0x801B0EEC b 0x801B0EFC (was 40820010);
  debug path 0x801B0F2C addi 0x1000).

### 7.28 Item-get scene (static; pm15, not yet tested)

- The spinning model: event command **cmd_91(slot, item, x, y, z, angle°)** (handler 0x8010FDF0 →
  func_80109CD4: item model via func_80011F68 into the event item slot evmgr+0x538+slot×4,
  PSMTXRotRad 'Y' (func_801B8048, angle × deg→rad), translate (func_801B82E4), func_801A2B48 sets the
  instance matrix; pushes 1). cmd_92(slot) hides it (func_80109D80, no push). World coordinates.
  Chapter1 script 30 (proposal, item 1311 Blue Feather) shows it next to the player with motion 7.
- func_80011F68(&itemrow, holder) binds the symbol/real model (func_80012030 → instance at
  holder+0, func_801A2A4C model, func_801A2B74 textures); something else draws the instance.
  The wlp2 caller at 0x15CA4 (+text base 0x80980F94 in the dump) is a room display, not the menu.
- Fades: cmd_0B(color, s) fade out (hold), cmd_0C(color, s) fade in, cmd_0D = fader busy.
  Both → func_80189128(fader, &from, &to, hold, 0, seconds); colours are palette lbl_8034AFB8[idx]
  with the alpha replaced (index 0 = black 000000).
- Sounds: cmd_30(id) plays SFXList entry id (214 door_close, 215 door_open in scripts; pushes a
  value). 224 = "fanfare". sys 0x0A = time in seconds (waits: v = t + d; loop until t >= v).
- Player motions used in scripts (cmd_72(0, m)): 0, 1, 2, 3 run, 7, 8, 9 knock, 10, 12, 19, 20,
  26–28, 30, 31, 34.
- Event 406 item_get(): fade out; cmd_14/15 from counters 10–15; cmd_72(0, 7); item spins via
  cmd_91 each frame (6°/frame) at counters 16–18; fade in; cmd_30(224); "You got" box polled each
  frame; fade out; cmd_92; cmd_72(0, 0); counter 19 = 1. pm.c fills counters 10–18 at the talk's start
  from game+0x29C78 / +0x29F84 (eye 2.6 in front, 1.35 up; aim 1.1 up; item 0.6 in front, 1.3 up)
  and, when the event has ended with counter 19 set, fades in itself (from 000000FF to 0, 0.5 s).
- The fader check in pm_frame is gone (the scene hook covers doors; it would have unloaded him on
  the item-get fade-in). pm.bin 4,848 B, Common.arc 21bfae39….

### 7.29 Item-get scene, pass 2 (pm15 feedback; static)

- pm14 test: scene works; the Postman sometimes covered the player/item, the player looked tired with
  arms down. Cause: **cmd_72(char, n) is the facial expression** (func_8007FE30 → slot face +0x124,
  func_8002F3E8), not a motion; 7 = tired. **cmd_6C(char, m) plays an event motion** (func_80080238,
  as our actor), cmd_6D(char, m, loop) the same with a loop flag.
- Expressions: face table per character lbl_8029F818[char×0x18 + chapter×4] → 8-byte entries
  {eye frame, mouth frame}; eye ≥ 0x3A / mouth ≥ 0x24 are animated sequences. Player table 0x8024CFD8:
  0 = 67/47, 3 = 9/6, 7 = 69/36 (tired), 19 = 9/19, 33 = 9/19. Face TPLs in RAM hold 1×1 placeholders
  (58 eye / 36 mouth entries), so frames could not be rendered. Using 3 (the player's face before
  minigame "Wonderful!!").
- Hold pose: Chapter1 script 30 (proposal) plays cmd_6D(0, 95, 1) before showing the Blue Feather;
  Common 83/84/86 (items shown) use cmd_6D(0, 16, 0). Using 95 looped.
- Facing: cmd_59(char, deg), 0 = +Z (Common 35). pm.c computes deg(atan2(dx, dz)) of (player −
  Postman) into counter 9; the camera sits on that side (Postman behind the player).
- Postman jog: set 71's own motions are entries 0–2 of the list at 0x8029C4D4 (0x8E000400 idle,
  0x8E000401 run, 0x8E004C02 anim 2); the rest belong to set 26. pm.c points entry 2 (0x80241EC8) at
  anim 6 (jog, 0x8E000406) while loaded, restores it on release, and plays it while counter 8 is set.
- Audio (for later): music is MusyX sequences (BOKUJYO*/EVENT* .arc + .samp; SNGList has 31 songs),
  BGM streams are DTK .adp; sounds are MusyX SFX (cmd_30 id = SFXList index).

### 7.30 MusyX sound banks: SoundFont out, fanfare in (static; demo not yet tested in game)

- sound/*.arc = U8 with pool, proj, sdir (+ song for music groups); *.samp = DSP-ADPCM sample data.
  GAME_ALL (group 0x2B, SFX type 1): 246 samples; proj SFX table (hdr+0x14 → u16 count, 10-byte
  entries {define id, macro id, prio, voices, vel, pan, key}); define ids start at 181 = SFXList
  numbering, so cmd_30(id) → define id. Sound 224 "fanfare" → macro 89 → sample 89 (5.40 s, 44.1 kHz,
  slot 0x1474A0–0x168800 = 136,032 B in GAME_ALL.samp). No event script plays 224.
- sdir entry (0x20): id, -, offset, -, pitch(60), -, rate @+0xE, samples @+0x10 (fmt in top byte),
  loop start, loop length, info offset; info: u16, ps, loop ps, hist2, hist1, 16 coefs.
- Macro commands are 8 bytes stored byte-reversed; StartSample = byte 3 0x10, sample id in bytes 1–2.
  Music pools have layer objects (pool+0xC offset): {macro, key lo, key hi, transpose, vol, prio,
  span, pan}; the sample sounds at its recorded pitch at key 60 − transpose.
- Tools (scratchpad snd/): musyx.py (U8/sdir/DSP decode), build_sf2.py + sf2.py (layers →
  SoundFont instruments, verified in FluidSynth), dspenc.py (k-means predictors + per-frame search;
  re-encoding the original fanfare: 40.9 dB SNR, same size), fanfare_patch.py (WAV → sample in
  place, sdir updated, read-back checked). Demo fanfare test_build: GAME_ALL.arc sha1 5ee3d41f…,
  GAME_ALL.samp 11cf4f05….
- All music groups (27, user upload): every program is a layer object (proj normal page: {u16 object,
  prio, voices, program, pad}, 6 B). hmawl_music.sf2: 165 presets (bank = song index, program = the
  song's own), kits also in bank 128; 645 unique samples (deduplicated), 50 MB. build_sf2_all.py.
- User MIDI "Get Big Item" (GM: drums 38/52, glock, choir, piano, strings; 3 s): GM parts matched to
  game presets by spectrum + envelope of one rendered note (timbre.py), remapped (remap_mid.py),
  rendered with FluidSynth, put in sound 224: 3.61 s at 44.1 kHz, 91,080 B, 37.7 dB SNR.
  GAME_ALL.arc 9045e9c7…, GAME_ALL.samp 524f2252….
- pm16 test: fanfare works in game; pose wrong: event motion 95 (Chapter1 script 30) is the
  Blue Feather pose — bending down to a Harvest Sprite. Removed: the player keeps the pose he talked
  in (holding the milk), which stays after cmd_56 takes it. Common.arc 495cf96d….
- Old test Gecko (C2 at 0x80213CFC, user's copy): Z+D-Up started event 406, Z+D-Down added items
  7–10 ×1 via func_8004FDA0(game+0x50, id, 1, −1). It hooks the same address as pm.bin, so it must
  stay off; Z+D-Down is now in pm.c (pm.bin 5,464 B, sha1 2de96425…). Held item = game+0x11CC4.
- Item-get axe: cmd_91 binds through func_80011F68, which picks real.gpl (in-hand model, pivot at
  the grip; our axe = 1.1-unit pole along Y) for items whose table +3 differs from item 0's — the
  user's build changed the Ax to real model 2 (7.16). The rucksack view binds with func_80011F2C
  (symbol.gpl always; symbol axe lies along X, centred). make_pm_dol now also patches 0x80109D24
  bl func_80011F68 → bl func_80011F2C (4BF08245 → 4BF08209). No original cmd_91 script shows an item
  that uses the real model, so their scenes are unchanged. Pose: the user's milk came from the
  held-item Gecko write (game+0x11CC4), so the player was never in the holding state; real milk
  keeps it.
- Holding pose (baked in): the player's event motions (actor vt+0xB0 → func_8007C7E8 with slot+8 =
  −1 → func_80028394(0, m) = set 0's motion list[m]) and the field's func_800288E8(motion, …, item)
  (u16 0x80249230[motion×4 + variant] into the same list 0x8029BECC) share descriptors; variant
  (func_80029138) = 1 for a held normal item. So event motion 1 = idle holding, 0 idle, 8–11 walk,
  16–19 run. Player set = 0 in every chapter (lbl_80249108). Event 406 item_get plays cmd_6D(0, 1, 1).

### 7.31 Skip Intro v6: the dog choice without Takakura (static)

- takakura.mes 113 = `35 02 "Go ahead and pick one." 35 00 01 41 02 00 "Pointy Ears" 01 "Long Ears" 00`.
  Option lists in .mes: text, `01 41 <count> 00`, options split by `01`, end `00` (badog.mes 5,
  bahn.mes 33–37 the same). Yes/No prompts end `40 00 00`.
- build_skipintro.py: 0x1FA is now "Which dog do you want?" + that option block; the Yes path's
  choice loop reads system.mes 0x1FA instead of showing 0x1FA as a line and then takakura 113.
  Space: one more duplicate shared (0x19 = 0x14). Chapter1.arc / system.mes keep their sizes
  (entry 1 8172 B compressed).

### 7.32 Choppable logs: map objects (static; placement test built, not yet run)

- Existing field log = placement id 198 in map1-p-other.oqt (5 copies: (71.2, 90.6), (75.3, 150.1),
  (85.1, 156.1), (93.9, 159.5), (103.6, 156.5)); model mapobj.gpl #198 "obj04-L" (48 verts, 73 tris,
  ~3.56 x 0.61 x 0.73, hollow: no end triangles).
- mapobj.gpl: u32 magic 005BBC61, bbox-table size (24 x count), bbox-table offset, count (285), model
  table offset 0x14; table = (data offset, name offset); bbox table = 6 f32 per model. Model: +0 pos hdr
  (s16, 14 frac), +4 colour hdr, +8 uv hdr (s16, 14 frac; name offset -> "mapobj.tpl"), +0xC normal
  hdr (global table: data 0, 0xF3 entries, fmt 0x40), +0x10 material (first DL, cmd list, count<<16),
  commands 16 B: 01 texture (low byte = image.mapobj_sNbM.tpl index), 03 mode, 02 draw (format,
  DL, size); format 0x8A8 = pos, normal, colour, uv (u8); 0x828 = pos, normal, uv. DLs 0x20-aligned in
  the file. The log uses texture 19 (mossy bark), the prop atlas is texture 0 (1024x1024); the tree
  stump (#143 kilikabu1-L) uses atlas uv 0.471-0.500 / 0.739-0.763 for its ring top.
- image.mapobj_s<1-20>b<1-6>.tpl: 26 textures each; s1 looks like summer, s4 spring (pink blossom);
  winter set not identified yet. mapobj.lod: 353 slots of 4 bytes (room for a model 285).
- Runtime: each placement becomes a 0x60-byte instance {model ptr, 3x4 matrix, ..., +0x38 2,
  +0x3C 01000000, +0x44 ptr}; valley "other" array of 283 at 0x809D1AA0 in the dump (no static root
  found; heap records at 0x80308Bxx are allocation bookkeeping). Map-object collision is precomputed
  per map (mapobj.col), so dynamic logs need their own colliders.
- .oqt quadtree: node = 6 f32 bbox, 4 absolute child offsets, u32 count (subtree total for inner
  nodes), leaf records at +0x2C (0x34 B: u16 id, u16 flags, 3x4 matrix), depth-first from 8. Reader/
  writer round-trips all map1-5 files byte-identically.
- Tools (tools/logs/): build_log_model.py (model 285 "obj04c-L" = obj04-L + capped ends using the
  stump rings, 2 materials; existing models kept at their offsets mod 0x20), oqt_insert.py,
  build_log_maps.py (3 records of model 285 in map1-5-p-other.oqt; x/z + 0.0123 marker for finding
  the instances at runtime). Spots (player position, facing): (182.00, 13.91, 177.00, 99°),
  (283.98, 21.62, 122.37, 149°), (75.44, 0.47, 117.60, −160°); logs lie across the facing.
- Axe: the baked no-till code is a cave at 0x800038E0 (both A paths: cmpwi r26,0x502 → li r3,0 →
  b back); the `li r3,0` at 0x800038E8 / 0x80003900 is the place to call a hit counter.
- Correction: the game reads the valley placements from **mapc1..5.arc** (U8: mapN-p-house/obst/
  obstBB/other/plant/ptcl.oqt + mapobj[N].col; a 154,588-byte archive in RAM = mapc1.arc) and the
  map-object models from **mapcommon.arc.clz** (CLZ U8, 90 files: mapobj.gpl, mapobj--N.act,
  mapobj.lod, jimen-*.gpl, ...). The loose copies on the disc are identical but unused, so the
  first test (loose files) showed no logs. build_log_archives.py rebuilds those six archives
  (U8 re-layout reproduces the originals byte-identically; CLZ re-encoded greedily with lookahead,
  1,326,656 B vs 1,329,201 original, round trip checked).
- Map-object models are actually loaded from **commonall.arc.clz** (its own mapobj.gpl, mapobj.lod,
  mapobj--N.act, map env files); mapcommon.arc.clz's copy was not what RAM held (test 2 dump: old
  285-model gpl at 0x81251280, three new placements loaded but not instanced). The user's commonall
  (3,824,947 B, with the axe work) rebuilt with model 285: 3,815,470 B, all other files identical.
- Test 4 (user): logs appear at the three spots, mossy, ends still open, no collision. Probable cause
  of the missing caps: the caps' display list size was 93 B; every original DL size is a multiple of
  0x20 (GXCallDisplayList takes whole 32-byte blocks). Six models have a second draw group (e.g.
  house04-L: 01010000 11110014 … / 03 mode 5 / 02 fmt 0xA8), so two groups are supported. Test 5:
  cap DL padded to 0xC0, caps in both windings, sides remapped to texture 16 (tree3L-wood bark,
  uv 0.51–0.998 / 0.01–0.998). commonall.arc.clz 3,815,522 B (sha1 1f6f4597…).
- Test 5: caps showed only as small triangles: obj04-L is open along a top seam too (23 boundary
  edges, loops of 10/3/8, one vertex of degree 4), so its rims can't be capped. Model 285 is now a
  closed 8-sided trunk (r 0.32, x ±1.75, 18 verts) with bark = left half of texture 16's tree3 area
  (u 0.515–0.745; the area's two halves differ, seam in the middle), wrapped twice; ring caps from the
  atlas; normals = global-table indices of obj04-L vertices pointing the closest way; both windings.
- Weather: func_80015640([0x803491D4]) = [+0x20], 0–5 (6+ panics in 0x80013FC0). func_8001263C sets
  one condition bit for 3 or 5 and another for 4: rain/storm = 3/5, snow = 4 (inferred). +0x20 differs
  between dumps of the same day, so it is the weather now, not a daily value.
- logs.c (in pm.bin): finds the three instances by the marker x/z bits (instance: model ptr at −0x10
  from x; file copies have 0x011D0000 there) in 0x80700000–0x81800000 after the valley loads; hides a
  log by y − 100; three body colliders per log (op_new 0x40, col_init, vtable 0x802C5720, stand-in
  owner with +0x4C pos / +0x58 dir / +0x64 map, col_config(37)). Counter 4: bits 0–2 present, bit 3 wet
  today, bits 8–23 last day + 1; counters 5–7 hits. pm_axe_hit: point 1.1 in front of the player
  within 0.9 of a log's axis = a hit; 10 = gone. make_pm_dol patches the baked axe cave's li r3,0 at
  0x800038E8 / 0x80003900 to bl pm_axe_stub (pm.bin +0x54), after checking the cave words; arena low
  0x80362000.

### 7.33 Logs: swing, prompt, sound, collision, stamina (pm.bin; tested in Dolphin, logs test 15)

- A prompt: hook 0x8004368C (field A handler stores its action at player+0x128, then the A label from
  lbl_8024F638+0x5C[action]): action 0x0F (tool swing, label 0x08 "Use") while the axe faces a log.
  Player pointer captured at the handler start (0x80043120, r3).
- Hits: one per entry into player state 0x79 with the axe facing a present log (game- or code-started).
- Swing state 0x79 (state table lbl_802A3AA8, 0x3C/state, filled at boot): enter 0x80032F7C (motion 0x39
  at the proficiency rate func_8004DAE0), end check 0x80033130: tool category lbl_80282DF8[item*0x24]
  3 → 60 frames, 6 → motion done (motion+0x20, never set for 0x39), else 30 frames. Axe/hoes = 1.
  An earlier mod had 60→40 / 30→10 (A could be mashed). Now 0x80033170 → category 1 ends after
  30 / motion speed (motion = [player+0xBC]+0x54, speed at +0x8); the mod's words are put back.
- Proficiency: pool u16 + level u8 at ctrl+0x2C/0x30 (ctrl = game+0x11B80); level = pool/1000+1 (max 5)
  at 0x8004D9BC, now /500. The axe mod skips func_8004D7AC (no points) and uses the hoe row/pool.
- Stamina game+0x11B84 (max +0x11B88, min +0x11B8C), refills when idle. Log hit: extra 3000; swing speed
  ×1 down to 80 % stamina, then linear to ×0.4 at empty.
- Sound: every SFX start passes 0x8018B224 (lhz r3,0x14(r31) → func_801DA9F8); cmd_30 → func_8012A52C.
  New sound 432 (wood_hit1) added to GAME_ALL (macro/sample 917, copied from 305 knock; proj id lists
  are ranges, SFX table at proj+0x74; add_sfx.py). The first non-ambient sound in a log swing → 432.
- Collision: map-object colliders list lbl_802E92D4; player check 0x8001E170 uses owner map vs
  g_system+0x68 and pushes out of circles (radius + 0.3). Logs: 7 circles r 0.4 every 0.45.
- Map objects are instanced only near the player; placement records (0x011D0000 at x−0x10) stay in the
  loaded mapc arc. Hiding writes y on records and instances (scan 0x40000 B/frame).
- HUD bars (v02 cave 0x800035B0): show after 65 still frames (was 20) at 0x80003628.

### 7.34 Lumber item, log rules, stall, Look (tested in Dolphin, logs test 22)

- Item 0x51C (was "<12>Record13"; <12> = red text with no reset) = Lumber. Row as Golden Wool: category
  0x1C, +1 tab bits 0x40 ("etc."; bit 0x01 = hidden from the rucksack, bit k = tab k), price 120
  (ships x5 = 600G), symbol model 11 (brush2, unused), texture 554 (symbol.tpl, appended RGB5A3).
- Menu/description model size: lbl_8028E84C, 0xE per symbol model (196 entries): s16 bbox min/max
  xyz + radius, /16384; read by func_800121C4. A model index >= 196 reads past it (huge in menus).
- Menu item names come from Message.arc/item.mes (not the loose item.mes); descriptions itemdoc03.mes.
- Rucksack slots: game+0x58 + 4i {u16 id, s8 count, u8}; func_8004FDA0(game+0x50, id, n, -1) adds
  (1 ok, 0 full/>99). Equipping a tool takes it out of the rucksack.
- Pick-up: motion 0xA with empty hands (state 0x84 does nothing), then item bind func_80011F2C(&row,
  player+0x1454) + func_8007C934 attach; pick-up sound 261 'syukaku'.
- Event counters 0-29 count up every day (EventCounter.txt markers 30/31/62/63); log state now in
  counter 63 (game+0x12290): present, wet today, spot used this season, day % 255 + 1, hits x3.
- Stall: villager item pick func_8011811C (held item first, then rucksack); hook at its end 0x8011886C
  turns 0x502 into 0. The pick lands in lbl_8034935C.
- Look: A action 0x18 has the "Look" label; message box = state 0x2A with player+0x14C0 file
  (0x33 system.mes, 0x3B itemdoc) and +0x14C4 message. system.mes 0x1FE "A humble log." appended.
- Arena low now 0x80364000 (pm.bin 0x323C B).

### 7.35 Goddess pond: cut content, fishing water, unused Toss (static; spring test 1 built, not yet run)

- Cut goddess quest text: david/flat/ebony.mes 0x00-0x2D (Harvest Sprites collect "wonderful things"
  so the Harvest Goddess comes to the Spring, `<2B:26>` = structure.mes 0x26 "Spring"); kris.mes 0xAB/0xAC
  (Ruby, JP only, US blanked): tossing things into the spring per an oracle, goddess doesn't appear.
  JP .mes kana: glyph 0x8025+i = hiragana gojuon, small kana, dakuten, then katakana (scratchpad jpkana.py).
- Fishing: fish table 0x802C9238 (0x1C per fish, 0x46F-0x47E), bite weights 0x802C91F8 [species 0-7][water 0-3]
  s16; big vs small = 100/(w_big+w_small) vs rand. Water type = func_8001DBA0(_, pos) (fishing.col,
  collision layer 8; raw attr 0->0, 1->1, 2->3, 3->2, none 5). Regions: 0 upper river, 1 lower river,
  2 pond A (x76-86 z104-112), 3 pool B (x265-275 z133-145, y~20) = goddess pond.
- A labels: opguide.agc group 1 entry = label (texture 0 word sheet); label 7 "Toss", 8 "Use".
- Unused Toss: action 0x28 (label 7) for every class at target 0x42 (never produced in game); needs item
  flag 0x8 (row +0x1C). States 0x9B (motion 0x21, frame 10: hands empty + sfx 263), 0x9C (projectile
  player+0x1460: pos, vel +0xC, gravity +0x18; func_800DFD24 init, func_800DFE88 aim -> frames; ends at
  frames >= +0x1494 by messaging target +0x1388), 0x9D (motion end -> field).
- spring.c: Toss label at pool B, own throw (pl_prep, motion rate 1, state 0x9B, +0x1494 = 9999), lands
  when the item falls below the player's feet - 0.4 -> unbind hand model, sfx 300, state 0x9D.
- Tested (spring test 6, OK): quick vanish at the visible surface (ground_y at the landing point; the
  pond's ground check is ~0.66 above the fishing-water height) + lure splash: func_800DD3BC(*(0x80349234),
  0x18, &pos, &facing, 0, 0, 0.0f). The effect keeps the pos/facing POINTERS (must outlive it; facing =
  cast direction). Sinking tried and dropped (water has no colour; the hand model is only drawn in 0x9C).

### 7.36 Harvest Goddess model in game (goddess test 1 built, not yet run)

- Source: ch_315.dae (5 meshes, 866 verts, 1052 tris, 36 joints, T-pose, height 163 = 1.63 at 0.01,
  faces +z, left = +x) + body 256², face/hair 128², eye 32x64 PNGs (hair/eye use cut-out alpha).
- Celia (sepi_0.arc / .anm.arc): 49-node act (2 pelvis, 3 hips, 4-5 spine, 6 chest, 7 head, 8-9 braid,
  10-20 / 21-31 arms: 12 shoulder 14 elbow 16 wrist, 32-34 skirt, 35-41 / 42-48 legs: 36 hip 38 knee
  39 ankle), skin uses every node but 0,1,11,22,35,37,42,44. 10 anims (MotionList2.dbg spb_00-09):
  idle, walk, holding idle, put away, explain, run, plead, dizzy, crouch, kitchen work.
- goddess/build_goddess.py: her joints on Celia's skeleton (rest rotations kept), rigid skin (largest
  weight -> mapped node; back hair -> braid 8/9), Celia's anims with translations x (her/Celia head
  height 1.27); b0 = body (sel FF) + 256² head atlas (sel 02: face, hair, eye; hair/eye CMPR 1-bit
  alpha). gd_0.arc 124,000 B (vanilla villagers up to 154 KB), gd_0.anm.arc 36,736 B.
- pm.c goddess_test: Z+X = slot 37 with gd names, spawn at Pool B (270.3, ground, 139.0) facing the
  player; next Z+X = next anim via set-71 motion entry 2 word 0x8E0004nn.
- Goddess test 1 crash (read 0xE0040000, PC 0x8019C80C): func_8019C734 (1-bone skin loop) sets
  ctr = count - 1 with the first vertex pipelined, so a group of count 1 loops 2^32 times through the
  locked cache. Every skin group needs >= 2 vertices (builder pads with an unused copy). Test 1b.
- Goddess tests 2-3 crash (PC 0x801A3684 in func_801A3668 via the skinning draw 0x8019E694): her act
  from node 23 on and her gpl head were overwritten by a 114-matrix scratch array (pointers at
  0x802FC93C and on the stack) lying inside her loaded archive. Her gd_0.arc was 74,848 B (test 1b
  124,000 B: garbled body texture instead); the teddy (62,976) and Postman (63,328) are fine. Working
  rule: keep slot-37 archives under 62,976 B. Test 4 build = 61,216 B (shared positions, merged UVs,
  strips 0x98, 1x1 face frames, head atlas 128x96). Not yet run.
- In-place act conversion (normal, seen in Celia's RAM): each node's 0x34 transform slot becomes a 3x4
  matrix + 4 bytes at runtime.
- Correction (test 4 dump): 0x802FC8C4 is the heap's allocation record list (arena 0x80364000 + 0x61FEA0;
  records {tag, ptr, size, next, ...}); 0x80983F00 was an ordinary 0x420 block. Her DVD-loaded archive
  was treated as free memory while still in use -> other allocations landed on it (inconsistent crashes;
  test 4 crashed after 5 anims, then before she appeared). The 64 KB rule was wrong.
- Every villager model/anm lives in mainchapterN.arc.clz (169 files: *_0.arc, *.anm.arc, subact/subanm),
  found by bare name in the mounted archives (func_8019A3C8) and used in place. Test 5: gd_0.arc and
  gd_0.anm.arc appended to mainchapter0-5 (goddess/add_to_mainchapter.py, standalone), pm.c names bare.
- Memory model (tests 4-5 dumps): Memory::InitializeWithArena makes pool A (0x802FD4D0, records
  0x802FC8C4, func_8017860C: mainchapter + per-frame scratch, grows up from arena lo) and pool B
  (0x80315508, operator new __nw__FUl 0x80178E88, first-fit: lowest free block first). In the valley
  pool B's lowest used block sat 2-3 KB above pool A's top (vanilla dump: 276 KB), so new pool-B blocks
  (our actor, models) were overwritten by pool A's per-frame matrices -> random crashes at
  0x8019E5EC / 0x801A3684. Putting gd_0 in mainchapter (test 5) just moved pool A up. Test 6: 256 KB
  pool-B spacer taken before our model loads (freed in restore_names). The arena-lo move for pm.bin
  (0x8035EFA0 -> 0x80364000, 20 KB) also eats into this margin.
- Goddess test 6 (Dolphin): OK - she appears, all 10 Celia animations cycle repeatedly, no crash.
  Working pipeline: build_goddess.py -> gd/gd_0.arc (61 KB) + gd/gd_0.anm.arc on the disc, slot 37,
  own set-71 motion list, 256 KB pool-B spacer.

### 7.40 Wildlife (static + 4 RAM dumps; research for enemies)

- Five wild species, character ids 0x2C lizard, 0x2D mouse, 0x2E tanu (tanuki), 0x2F kame (turtle), 0x30 owl.
  Model table lbl_8024A534: 24-byte rows {name, scale 1.0, f, f, 0, byte} for lizard.arc, mouse.arc, tanu.arc,
  owl.arc (string at 0x80346A38), kame.arc (then cow0..cat rows of 8 bytes); anims: <name>.anm.arc,
  <name>_subact.arc, <name>_subanm.arc. Each is a file of its own on the disc (not part of the map).
- **One wild animal at a time.** g_system (lbl_80349194) +0x3F8 = today's species = 0x2C + rand() % 5
  (lbl_803469D0 / lbl_803469D8 = 4; set at 0x800132CC and 0x80013B88). func_80159560 loads that species' model
  (func_8002C74C → slot lbl_802ECA70 + i*0x44, 5 slots; the heap block is sized for the biggest, 0x8002BAC4).
- **The object.** The field scene setup (func_80013F60 → 0x8001434C) allocates 0x2B0 bytes and builds it with
  func_80159A28(obj, 1, species, func_801595E0(species) = 0x3D..0x41 → the base's character id); stored at
  scene+0x44 (and in the manager at scene+0x40, its +0x4C). Base class func_80010904 (the villagers' base),
  own vtable at +0x10 = lbl_802C618C (methods func_80159FF0, func_8015A22C..4AC, lbl_8015C7EC..850; class code
  0x80159A28-0x8015C850).
- **Runtime:** field scene = *(u32 *)0x80305FBC (same in all 4 dumps); animal = *(scene + 0x44);
  +0x4C x, +0x50 y, +0x54 z (copy at +0xFC), +0x58 / +0x60 facing (sin, cos), +0x128 species. Not in the event
  character slots (game+0x29C78), which is why Z targeting never saw it.
- Dumps: turtle (Z2) at (77.5, -, 112.7), (75.0, -, 113.5); owl (winter) at (279, 27, 116); lizard (263, 19.6, 179).
- Enemies plan: 1) zt.c: add the animal as a Z candidate (position above); 2) target_is_enemy = it; impacts +
  a hit reaction (flinch/knockback via its position, HP in our own state); 3) more than one animal needs more
  objects of this class (constructor above) or our own actor.

### 7.41 HUD clock garbage / crash (user dump 93470d41): the $JOE TV picture copy
- Crash: PC 0x80187F64 (stw r0,4(r3), r3 = 0x02F0F140) in a ptmf dispatch (0x80187370); the HUD clock area showed
  texture garbage, once blue clock text. joetv.c show_picture cached the tv-console2.tpl address; the house (wlp2)
  loads that file with the house and frees it on leaving (0x1D420 zeroes its bss lbl_10000050 handle and
  lbl_10000074 tpl pointer), but the freed copy keeps a valid header, so a later channel 3 copied 4 x 13.8 KB of
  picture into reused memory. Fix: no cache; a tpl counts only if a word holds its address with a live handle
  0x24 before it (the wlp2 bss pair; seen at 0x809C0574 in 7 house dumps, none outside).

### 7.42 Session dump dca3cabd (enemy 1d, NO_TVPIC): $JOE seed counts up; the crash is a runaway recursion
- $JOE: the seed log showed counters 52 / 53 going ..64D0, D1, D2, D3 on days 1-4: they are count-up counters (+1
  every new day), so each day's "since yesterday" compared two markets. Fix (enemy 1e): the seed is kept in the top
  halves (52 high 16 bits, 53 low 16 bits); the daily +1 only reaches the low halves. Existing seeds stay readable.
- Crash with the TV picture copy OFF (so not the TV): "Invalid write to 0xBCD1D7B9, PC 0x80144348". 0x800020C4-
  0x8046D84C is covered by 0x30-byte stack frames of func_8019D534 (return 0x8019D700): it walks a node tree
  (+0x10 first child, +0x8 next sibling) and recursed forever on a node whose links point at itself.
- Outer frames (still intact above 0x8035CE0C): player state lbl_800343EC (take the held item out: held_attach
  func_8007C934, then motion 0x48 / 0x35 with item 4EB = H.M Murasama, row 0x8028DF04) -> func_8007C0C0 ->
  func_8017DB28 -> sub-clip r31 = (desc word1 >> 11) & 0x7F = 6 from the player's sub-anim arc (*0x802EA718,
  0x808326E0 in a healthy dump) -> func_80199F5C returned 0x808326DF (= the arc - 1: the file lookup failed) ->
  func_8019CD50 / func_8019D330 instanced it -> the recursion. So at that moment the sub-anim archive's entry 6
  was gone or corrupt. Lag in the field built up before it (the user: extreme lag, gone indoors).
- Dump e996fcfb (enemy 1e NO_TVPIC; only running in and out of the house): "Unknown pointer 0x114000E0, PC 0x80188AB0,
  LR 0x80187378", the same dispatcher as the first crash (0x80187F64): func_80186E28 is the message-text control
  code interpreter (opcode byte 0..0x54, handlers call the text object's vtable +0xBC/+0xC0). Suspect: opguide.agc
  element 7 (the farmer's name, 12 glyph quads in vanilla) was grown to 37 quads for the skill row / pop-up /
  reticle; the game re-renders the name on HUD rebuilds (every map change). Test hudtest1: weapons3 commonall with
  element 7's count back to 12 (our HUD extras then switch themselves off: E7_COUNT check), commonall 96ffdad7.

### 7.43 Memory: the two pools overlap (the cause of the random corruption, T-poses, slowdowns, crashes)
- Pool A (0x802FD4D0, records {start, size, next, flag 2 used / 1 free}) grows up from the arena start:
  the mainchapter (6.27 MB) + per-frame scratch. Pool B (0x80315508, operator new; records hold the block's
  TOP address and size) fills down from the arena top. Nothing keeps them apart: when B reaches A's top it
  hands out memory inside the mainchapter (villager animations: T-poses, corrupt textures, crashes).
- Gap = B lowest used (top - size) - A top: Oct 28 dump (near vanilla) +276 KB; joeprice +480 KB;
  targetanimal / field crash / HUD crash -50 KB; T-pose and Joe dumps -1219 KB.
- Costs: our arena reservation 0x8035CFA0 -> 0x80380000 (141 KB); commonall +175 KB since Oct 28 (HUD,
  weapons, symbol/real tpl, mapobj); with Joe: 256 KB spacer + a SECOND copy of his archives (377 KB model
  + 73 KB anims, unreferenced: leaked when names were restored without unloading, or the next scene loaded
  them again as character 37).
- memfix 1: arena start 0x80377000 (pm.bin ends 0x80375884); the spacer is freed once Joe is spawned; on a
  scene change during a talk the character-37 names go back at once; archives no longer referenced by the
  model entry (0x802EB4D4 + 37*0x44 + 0x10) or any set (0x802EA714 + n*0x30) are freed (free_orphans);
  pm.bin symbol mem_g ('MEMG'): gap now / lowest seen / when, every 32 frames.
- New-game crash on memfix 1 (dump 102e6cca, naming screen): PC 0x8001F9F4 = collider-list unlink with a garbage
  node; our state empty; gauge: gap -12 KB already at the naming screen (A top 0x80996EE0, B low 0x80993E60,
  B 14.7 MB). So the game needs memory back beyond our own additions. Pool A's block is exactly the unpacked
  chapter archive (0x61FEA0 here), so a smaller archive frees memory 1:1.
- Chapter 1 = mainchapter0 (has hyu_0; mainchapter1 has hyu_1). The son's animations (son_0.anm.arc 384 KB +
  subact/subanm = 392 KB) are in it although he is born at the start of chapter 2. tools/memory/strip_chapter.py
  (run on the user's ISO) empties them: -382 KB. Next candidates: characters that never appear in a chapter.
- memfix 2 dump abdbf0cb (son stripped: pool A block 0x5C03A0, -382 KB OK) still crashed (rucksack, Joe on the
  map): pool B is top-down over the WHOLE arena (header: top 0x817F40A0, size = the arena); its lowest record is a
  free block from the arena start up to its lowest used block, so B never "knows" about A: once B's usage reaches
  down past A's top they overlap (here B reached 0x80882F40, A top 0x80937E40: -339 KB).
- Joe's model archive (377 KB, 0x5E6A0) was in memory twice again: load_model(37) then slot_setup(slot, 37, -1)
  loads it a second time and the character-37 model entry (0x802EB4D4 + 37*0x44, ARC handle: +0 = archive start;
  memfix 1 wrongly read +0x10) keeps only the second. memfix 3: the first copy is freed once nothing in RAM points
  at it (full-RAM scan, skipping the pools' records and pm.bin). Next: Joe's model is huge (377 KB) - shrink it.
- memfix 3 dump 055b67cc: still two copies (0x808E3040 orphan, 0x808849A0 live = model entry 37 +0); orphan list
  empty, so the two loads are not load_model / slot_setup in that order (setup order top-down: guard, anims,
  copy 1, copy 2). memfix 4: dup_sweep 60/180/300 frames after setup_model: any pool-B block with the live
  archive's size and header (+4..+0x40) that no RAM word points at (skipping only the record arrays
  0x802FC8C4-0x803154FC and pm.bin) is freed. Checked offline on the dump: finds exactly the orphan.
- memfix 4 dumps joe1 / joe2 (rucksack opened and closed repeatedly with Joe around): 3, then 9 copies of Joe's
  377 KB model (anims stay 1), dup_freed 0. Source: the event-actor constructor (0x8007F53C..0x8007F590) loads
  character id < 0x27's model (func_8002D128) and sets the slot up (func_8007B8F8) whenever slot +0xC is 0,
  without freeing the copy in the model entry; Joe's actor is made again after every menu. memfix 5: spawn()
  unloads the old model first when the slot is torn down; dup_sweep runs every 60 frames while Joe is loaded as a
  net; debug dup_dbg ('DUPS': sweeps, candidates, kept, freed, last reference address).
- memfix 5 dumps joe3-5: copies 3 -> 5 -> 11 (one per rucksack close). dup_dbg: 37 sweeps, 13 candidates, all kept
  as referenced (last reference 0x8031887C, a game static that held the copy at sweep time; 0 in the dumps).
  unload_model (func_8002D3B4 -> func_8019A1CC) only closes the ARC handle: the memory stays. memfix 6: spawn()
  remembers the old copy when slot 37 is torn down, lets the actor constructor load the new one, then
  op_delete()s the old one at once; dup_dbg.spawns / reloads count respawns. (The file registry at 0x80318608
  only lists the live copy.)
- memfix 6 dumps joe6 / joe7: copies 3 -> 11 again; dup_dbg spawns 11, reloads 0: the respawn path never hit (slot
  +0xC set). Real path: each menu runs restore_names (map changes) -> S.loaded 0 with our model still in the model
  entry -> after the menu setup_model -> load_model replaces it unfreed; the orphan was then dropped by
  free_orphans because 0x8031887C (the last file read) pointed at it. memfix 7: setup_model frees our previous
  archive right after load_model replaces it (the slot was torn down just before); referenced() ignores
  0x8031887C. Offline on joe7: the 10 old copies have no other references.
- memfix 7 dump 0601e020 (right build): 5 copies, freed 0, 31 sweeps saw 1 candidate: two old copies' headers
  (+4..+0x40) differ from the live one (rewritten in place after loading), and the sweep only ran while S.loaded.
  None of the old copies is referenced. The reloads come from yet another loader (func_8019A0EC has 19 callers).
  memfix 8: dup_sweep every 60 frames always; learns our archives' block sizes once; any other U8 block of
  exactly that size that is not the live one and is unreferenced in two sweeps in a row is freed.
- memfix 8 dumps 6ffbeaab / fb1422d9: 9 / 10 extra copies of Joe's model (377 KB); no other character's model is
  duplicated (only pair besides: the two 560 KB VI framebuffers, vanilla). 58 / 142 candidates all "referenced",
  last from 0x803188B4: SDK driver data (0x80318838 render mode, 0x80318868 XFB, 0x803188A0 12-byte request table),
  zero in the dumps, so a transient copy of the scanned pointer. memfix 9: referenced() skips 0x80318700-0x80318900.
- memfix 9 dump 483b2b7c: still 9 old copies, 121/121 candidates "referenced", last from 0x80317FB0 (a stack).
  In the dump the old copies are referenced only by pool-B block records (the next block's top); the live one by
  model entry 37 (+0/+0x1C/+0x24) and pm.bin. Whole-RAM scans see the scanned pointer left on stacks/SDK data by
  interrupts. memfix 10: referenced() checks only the game's static tables 0x802E0000-0x802F0000 (owners).
- memfix 10 dumps 1527a09c / 302c2cef: leak fixed (no duplicate models; dup_dbg freed 1 / 11). Still gap -715 KB:
  pool B uses 15.2 MB, pool A (chapter 1 archive, every villager's model and anims) 5.9 MB. Joe's model is the lowest
  B block, inside A. Joe's textures 314 KB vs a villager's ~33 KB (body 128x256+128x64 CMPR, 32x32 CMPR face frames).
  Joe test 11: JOE_TEX=0.5 -> gd_0.arc 156,128 B (-230 KB). Remaining deficit ~485 KB: next, strip characters
  absent from chapter 1 / Murrey, compress the HUD additions in commonall.
- memfix 11 dumps joe_3 (0a7466aa, error + garbled mouth texture as Joe loaded) / joe_4 (7afae3c4): joe_3 no leak but
  gap -120 KB: Joe's model (0x8091B320..) lies above pool A's top 0x80937400, in A's per-frame scratch -> his mouth
  texture overwritten. joe_4: 4 old copies kept: set 10 +0x2C (0x802EA920) = the END of set 10's 0x260-byte block,
  which equals the next block's start. memfix 12: referenced() looks for start + 0x20 (an ARC handle holds the node
  table pointer too: model entry +4); offline on joe_4 only the live copy is owned. dup_sweep frees every
  confirmed copy in one sweep (8-entry seen list, restart after each free).
- Chapter 1 also carries Grant (gura), Kate (keit), Samantha (san), Dr. Hardy (pado; ch-1 anims already empty on
  the original disc), who move in in chapter 2 (body textures checked: villager_bodies.png). strip_chapter.py
  default now empties them too: 573 KB more (pool A 5.75 MB -> ~5.2 MB). Risk: the chapter 1 -> 2 transition.
- Correction (user): Dr. Hardy (pado) is in the valley from the start (his ch-1 anims are pado_1.anm.arc, 16 KB).
  Removed from the strip list: Grant / Kate / Samantha only, 414 KB.
- memfix 12 dumps 2c2d8dea (invalid read from 0, PC 0x801A04F4, loading the save) / 42d0ffea (crash entering the
  mansion): the game OPENS every chapter character's model at load (model entries 0-31 + 35-37 filled; 14-16 =
  Grant / Kate / Samantha, empty with their emptied archives). Memory itself was fine: gap +324 KB in the mansion dump.
  memfix 13: their models are replaced by a 16 KB placeholder (tools/goddess/scripts/build_stub.py: 72 faces of the
  blank body on Celia's skeleton, blank face frames; built from disc data, so only in the user's zip); their
  anims / subact / subanm stay empty (as pado_0.anm.arc on the original disc, whose model is opened too).
  strip_chapter.py --put name=file. Expected: ~364 KB freed for the three (instead of 414).
- memfix 13 dumps fadefd5d / c232212a: models 14-16 now open (placeholders), but invalid read from 0x14 at 0x801A40B4
  on load (and the mansion crash): their 0-byte .anm.arc. On the original disc an animation-less character has a
  64-byte EMPTY U8 archive (pado_0.anm.arc, tei_0.anm.arc), not 0 bytes. memfix 14: strip_chapter.py writes that
  64-byte archive for every dropped .anm.arc (subact / subanm stay 0 bytes, as keit / san / kuri on the original).
- memfix 14: mansion OK; still an invalid read on load (0x01F110AC at 0x801A0AF4): Grant's subact / subanm (644 / 192 B
  on the disc, unlike Kate's / Samantha's 0 B) were emptied; the load indexes them (func_801A0A88 -> 801A0AF4).
  memfix 15: they are kept.
- memfix 15 dump a62a3006: same read at 0x801A0AF4. Path (traced): func_801A0A88(anim archive, 0, n) opens file n via
  ARCInitHandle / func_80203BF0; when the archive has no such file the result is uninitialised stack (0x01F110A8, found
  at an anim player's +0x10 in the dump: 0x80EF2BCC, 0x80FE66B0) -> func_8019FE08 -> func_801A0AF4. The load asks the
  newcomers' animation archives for clips, so the 64-byte empty ones fail. memfix 16: their .anm.arc are kept (33 KB);
  only the models are replaced (about 330 KB freed).
- memfix 16 dumps d1239f81 (inn, ignorable error at 0x801A3630) / cb8aea64 (Celia's house, hang): no error on load.
  Root cause of the building crashes, traced in both dumps:
  1. Pool A, besides the chapter archive, takes a 239 KB block (0x3A660 at 0x808E3D80, + 0x320) when a building
     loads. MEMG (every 32 frames) missed it: real A top 0x8091E700, B low 0x8091A540 -> overlap ~17-20 KB.
     Vanilla's 276 KB gap is what keeps this block clear.
  2. The B blocks it overlapped are Joe's model (156,128 B, its U8 header overwritten by A data) and animations
     (74,464 B), still allocated INSIDE the building. S: loaded 0, own_* 0, orphan[] = model + anims; entry 37 +0 /
     set 71 +0 still point at them (unload only closes handles), so free_orphans never freed them.
  3. setup_model re-captured orig_set after a menu while set 71 still held our animations.
  memfix 17: pm_scene_change -> joe_free_now(): entry 37 back to the unused state (zeros, vtable word +0x20 kept),
  set 71 back to orig_set, then op_delete model + anims + orphans before the next scene loads; orig_set never
  captured from our own archive (S.last_anims); MEMG every 4 frames.
- memfix 17 dump 92afe3f3 (inn, read from 0x5 at 0x8001025C): Joe now freed (B free from 0x8091C140, 2.6 MB), but 3 game
  blocks (6528 / 608 / 32 B, owned by a live object at 0x80FE9F0C and set 10) stay at 0x8091A540..0x8091C140, inside
  the inn's pool-A block. They were allocated (slot set-up) while Joe's archives held B's bottom down.
- Pool A is the game's module heap: SystemTask (0x80177B98..) loads each area's REL with DvdFile + allocA
  (func_8017860C(size, file, line)) + OSLink; the inn's 0x3A660 block is its REL (header word 3 = module id). Both
  pools span the whole arena (A hdr 80377000 / 0147D0A0), A bottom-up, B top-down, each blind to the other.
  Invariant: B's lowest LIVE block must stay above chapter archive + the biggest area REL (+bss).
  A alloc / free: func_8017860C / func_80178660; B: func_801786D4 / func_80178728 (op_new 0x80178E88 / op_delete
  0x80179168 also B).
- Original commonall (24c1e6b7, 5,410,544 B unpacked) vs ours: +182 KB (opguide.tpl +123 KB: three RGB5A3 HUD
  textures, which must stay RGB5A3; symbol.tpl +27 KB, real.* +12 KB, mapobj.gpl +9 KB, symbol.gpl +6 KB).
- memfix 18: Joe's archives go to POOL A while he is in the valley (no REL above the chapter archive there) and are
  freed at every scene change before the next REL loads. op_new / op_delete hooked (HOOK25 0x80178E88 -> pm_new_stub
  +0x2F0, HOOK26 0x80179168 -> pm_del_stub +0x358): with joe_to_a set (load_animset / load_model / slot_setup in
  setup_model, actor_ctor in spawn) a request >= 64 KB goes to allocA if it ends >= 64 KB below B's lowest block
  (else B as before); pm_del_a frees only blocks we put in A (8-entry list). No 256 KB spacer any more. A model
  copy replaced by slot_setup is freed at once. make_pm_dol.py must be the new one (two more patch sites).
- memfix 18: user: "silky smooth, no breaks".
- memfix 19 pool guard: HOOK27 func_80178A44 (pool alloc, every pool-A allocation and pool-B ones outside op_new)
  -> pm_pool_stub (+0x3D4), and op_new's normal path (pm_new_stub) now calls mg_after too. mg_after checks the new
  block against the other pool's USED blocks (B check: A's few records; A check: B's ~1600 only when the block
  reaches below a cached B bottom, refreshed by MEMG every 4 frames). Overlap -> 'MGRD' record {magic, n_a, n_b,
  overlaps, signalled, b_low, b_low_min, b_low_min_lr, pool, p, size, lr, lr2, other_p, other_size, frame}; the
  first one reads 0x0BAD00A0 (A over B) / 0x0BAD00B0 (B over A): Dolphin's invalid-read box names it. Detection
  only (no memory to give back at that point). pm.bin now ends 0x8037693C (arena 0x80377000: 1.7 KB left).
- memfix 19 dumps: 941a25d8 (m19t) MGRD n_a 69,443 / n_b 17,043, overlaps 0, B lowest ever 0x80959580 (470 KB above
  the chapter archive's end 0x808E3D80; lowest-B caller 0x800FD0E8); MEMG gap min 237 KB (a building's REL loaded).
  7eb2f3b2 (GUARD_TEST: Joe in pool B): overlaps 0, B lowest 0x809585C0 too: without the 256 KB spacer (gone in
  memfix 18) Joe's archives fit in B's holes, so the spacer was the main reason B reached into the REL area.
  GUARD_TEST now instead asks pool A, 600 frames in, for a block reaching 64 KB into B's lowest block and frees it
  at once (records only): must give 0x0BAD00A0.
- memfix 19 guard test 2 (dump 5356376c): fired as designed: MGRD overlaps 1, pool A, p 0x8091E760 (A top), size 0x164E80
  (to 64 KB inside B), lr 0x80178650 (allocA wrapper), lr2 0x8035FDF4 (the test), other = B block 0x80A736E0
  (0x23000), frame 600; freed at once, pools apart afterwards (gap 1363 KB at the title).
- memfix 20: arena start 0x80377000 -> 0x8037C000 (lis 0x8038 / addi -0x4000): pm.bin room 118 KB (was 1.7 KB
  free above its end 0x8037693C); costs the pools 20 KB (tightest gap 237 -> ~217 KB). PREV accepts the 0x7000 words.
- TV "To be continued": not in tv-console2.tpl (21 pictures decoded from dump dfd76891: 0 vignette, 1-3 drama couple,
  4-5 angel, 6 singer, 7 news, 8-13 weather / effects, 14-20 ours) nor in its agc; probably a drama caption line
  (game text encoding). Waiting for a screenshot.
- memfix 20 dump 08c13861 (m20t, buildings + rucksack with Joe): arena / pool A start 0x8037C000 (OK), MGRD n_a 42,255 /
  n_b 15,357, overlaps 0; chapter archive ends 0x808E8D80, B lowest ever 445 KB above it; MEMG gap min 214 KB.
  m20t = the user's base from now on.

### 7.44 Enemy step 2: HP, hit flash and an FF7-style defeat (enemy2, static)
- Model instance draw func_801A2CFC(inst): +0 gpl, +4 3x4 matrix, +0x3C visible, +0x3D flat colour (lighting off via
  func_801A7BA4(.., 0), then GXSetChanMatColor(GX_COLOR0A0, *(u32 *)(inst + 0x3E)) at 0x801A2E70), +0x44 texture pair.
  Normal drawing has GXSetBlendMode(BLEND, SRCALPHA, INVSRCALPHA) on (0x80182868 / 0x80184B24 / 0x80191344).
- The wild animal's instance (dump 60ea3264, tanuki): animal +0x168 = skeleton instance 0x80A39420 (+0 act,
  +8 37 nodes, +0x14 mesh instance); +0x14 = 0x80A3A020: +0 its gpl, matrix with the animal's position, +0x3C 1,
  +0x3D 0. Characters are skinned on the CPU (func_8019C080) and then drawn by the same instance path.
- zt.c: EN {hp, day, state 0 alive / 1 dying / 2 gone, t, flash, ...} ('ENMY'); en_hit on each impact (weapon
  damage table, hit 3 x1.5, knockback), en_frame every field frame (flash, shake + tint + alpha fade, then
  +0x3C = 0); tpos(ZT_WILD) refuses unless alive (no lock on a defeated animal). Reset each new day.
  Unknowns for the test: whether the channel takes the material colour from the register (tint visible) and
  whether TEV passes its alpha (fade), and whether the game rewrites +0x3C every frame.
- enemy2 test (user, tanuki; dump 6eeeb7cb): HP right; no visible white flash (flat colour MULTIPLIES the texture:
  white = just unlit); no shake (the animal moves itself from its +0xFC position copy, overwriting +0x4C); red tint
  works; no fade (the colour's alpha is ignored), then hidden (+0x3C = 0 works); still solid after (collider).
  enemy2b: flash = light red (255,120,120); positions written to +0x4C and +0xFC; fade = flicker out (shown on
  fewer of each 16 frames); defeated = hidden and moved to (-5000, y, -5000).
- The invisible Z target in the dump: event slot 5 at (274.9, 126.1) = moi_0.arc = MURREY (grass skirt, bare feet;
  body texture decoded): his actor has the 0x2000 "out on this map" flag but his model is not drawn.

### 7.45 Battle music: the DTK stream player (enemy3, static)
- Valley music = MusyX songs; the DTK stream is free there. Stream player (audio = *0x803491E4, player at +0x80):
  func_80129928(player, f1, len1, off1, f2, len2, off2): DVDChangeDir("sound"), DVDOpen both, DVDPrepareStreamAsync
  (func_801BACD0) for f1 then f2 queued (the drive loops the second). Busy (+0xDC) -> the request waits in
  lbl_802FBE60 and the update retries. func_8012A880(audio, track): names lbl_802C1000, {len1, off1, len2, off2}
  << 15 from lbl_802545B8 (all vanilla tracks: whole file, then loop from N x 32 KB). Stop: func_8012A8E4(audio).
  Faders audio+0x160 / +0x170: func_8018A08C(fader, u8 target, u16 ms) (func_8018A0FC = current value).
  Music master: func_80189DD8(*(audio+0x4C), 0..127, ms) (sndMasterVolume music group).
- zt.c bm_frame ('BTLM'): lock on a living enemy -> field music to 0 in 0.8 s, stream /battle/BATTLE.adp (loop at
  9 << 15), faders 0 -> 255 in 1 s; defeat or > ZT_LEASH from the enemy -> faders to 0 + music back to 127 over
  1.5 s, stream stopped after 100 frames; leaving the valley stops it at once. Defeat sound SE_DEFEAT = 222.

### 7.46 Wild animal update / motion (research for battle AI, static + dump 60ea3264)
- Update = func_8015A22C(obj) (vtable thunk 0x8015C830): timers +0xE4 / +0xE8; **AI step bl func_8015A6D4 at
  0x8015A2B4**, **movement bl func_8015C398 at 0x8015A2BC**, then func_800107A4(obj+0x30, obj+0xFC) (the +0xFC
  position copy -> +0x4C), facing +0xF0.. -> +0x58... Animation player at obj+0x1A8 (func_8017D7FC advance,
  func_8017D7EC done?); a motion request obj+0xD8 != current +0xDC starts a clip: kind obj+0xD4 (0..4) picks
  func_8002B4B8 (+0x278) / 8002B114 (+0x279) / 8002B62C (+0x27A) / 8002B358 (+0x27B) / 8002B258 (+0x27C) for the clip,
  then func_8017D610(obj+0x1A8, skel obj+0x168, set, clip, 0) and +0xDC = +0xD8. Tanuki: kind 2, motion 8.
- Motion table per species (func_8002F8CC, 0x8029FBF0 + 4*id): lizard {0,2,4,6,8,10,0,0,0,0,0,2}, mouse {0,2,0,6,0,0,
  0,0,0,0,21,2}, tanu {21,2,0,6,8,0,0,0,0,0,21,2}, kame {21,2,22,6,8,10,0,14,0,0,21,0}, owl {21,0,0,0,8,0,0,0,0,0,21,0}
  (>= 0x14: sub-animation archive clip - 0x14). The motion state +0x280 ({slot, table, sub-player +8}).
- Tanuki animations = animation set 10 (obj+0x1E8 = 10): 11 clips, 1.4-5.9 KB each. AI uses rand() (func_8017D3E8).
- Battle plan: patch the two bl's (AI step / movement) to pm.bin stubs that skip them while we drive the animal
  (position via +0x4C/+0xFC, facing, motion via +0xD8); new attack clips appended to tanu.anm.arc (clips 11+) and
  mapped through the species table.
- battle test 1: HOOK28 0x8015A2B4 (bl func_8015A6D4, AI step) / HOOK29 0x8015A2BC (bl func_8015C398, movement)
  -> pm_aistep_stub +0x42C / pm_move_stub +0x440: return at once when r3 == en_ctl (zt.c), else the original.
  zt.c ai_frame ('ENAI'): while locked on and alive: circle at 3.0 (walk, 75-150 frames, direction alternating),
  wind up 30 frames (idle, facing), lunge 14 frames at 0.28/frame toward where the player was (run), recover 45
  (idle; a hit = 30-frame stagger). Motion request +0xD8 = clip (idle 0 / walk 1 / run 2 assumed); facing via
  +0xF0 / +0xF8. Lock let go -> en_ctl 0 (its own AI again); dying / gone -> still held.
