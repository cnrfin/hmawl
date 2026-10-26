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
