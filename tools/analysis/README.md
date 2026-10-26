# Analysis scripts

These are the helper scripts used for `notes/findings.md`. They only read
files and never write anything. Nothing game-specific is built into them
except a few addresses; all game bytes are read from your own copy of the
originals.

Requirements: Python 3, standard library only.

## Setup

Put the original US binaries (GYWEE9) in a folder in the repo, for example
`orig/`. `.gitignore` already excludes `*.dol` and `*.rel`, so they won't be
committed. Then check them against the repo's hash list:

```sh
mkdir -p orig   # copy main.dol, wlp0.rel, wlp1.rel, wlp2.rel into it
(cd orig && sed 's#build/hmawl_us_r0/##' ../hmawl_us_r0.sha1 | sha1sum -c)
```

All four should say `OK`. On macOS, use `shasum -a 1 -c` in place of `sha1sum -c`.

Run every command below from the repo root. Hex addresses are written without `0x`.

## asmq.py: search the main.dol asm by function

Searches `asm/main/game/*.s` grouped by label, prints one label's body,
or lists the callers of a label. It doesn't need the binaries. The repo's
`.s` files have CRLF line endings, and the script handles that.

**Inputs:** the asm folder (default `asm/main/game`; change it with `--asm-dir DIR`).

The splitter also puts `func_` labels on branch targets, so a label isn't
always where a function really starts. Check for a `stwu r1` / `mflr`
prologue.

```sh
python3 tools/analysis/asmq.py func func_80113234        # body of the gold add routine
python3 tools/analysis/asmq.py callers func_80113234     # who calls it
python3 tools/analysis/asmq.py grep 'cmpwi r\d+, 0x27$'  # instruction search
```

Example (`callers func_80113234`):

```
func_80110908 801115F4
```

`func_80110908` is a branch-target label inside `func_8010C604`, which is
the real function (see notes section 1.3).

## xref.py: find every reference to an address in the original binaries

**Inputs:** a folder holding the original `main.dol`, `wlp0.rel`,
`wlp1.rel` and `wlp2.rel`, plus a start and end address (end not included).

- **main.dol:** decodes every `b`, `bl` and `bc` instruction, finds
  `lis` + `addi`/`ori` pairs, and looks for raw 32-bit pointers in every section.
- **rels:** parses the relocation tables. It reports relocations pointing
  into main.dol (module 0) in that range, as `wlpN.rel secS+offset TYPE -> target`.

```sh
python3 tools/analysis/xref.py orig 80113234 8011328C
```

Example output:

```
# wlp0.rel: scanned 9715 relocations
# wlp1.rel: scanned 15170 relocations
# wlp2.rel: scanned 7752 relocations
# main.dol: scanned 10 sections
main.dol text1 801115F4 (file 0x10E334) bl -> 80113234  raw 48001C41
main.dol text1 80113238 bc -> 80113264  raw 4080002C
main.dol text1 8011324C bc -> 8011325C  raw 41810010
main.dol text1 80113274 bc -> 80113284  raw 41810010
```

The last three lines are branches inside the function. To check that the
rel scan is working, try `xref.py orig 80012800 80012804`. It should list
`wlp1.rel sec1+0x1C REL24 -> 80012800`, which matches `bl func_80012800` at
file offset 0x118 in `asm/rels/wlp1.s`.

## dolread.py: read main.dol words by RAM address

**Inputs:** the path to the original `main.dol`, a RAM address, and
optionally how many words to read. It prints each word with its file
offset and DOL section.

```sh
python3 tools/analysis/dolread.py orig/main.dol 802C0378 3
```

Example output (command table entries 0xC0–0xC2):

```
802C0378  file 0x2BD378 (data5)  801115B4
802C037C  file 0x2BD37C (data5)  801115D8
802C0380  file 0x2BD380 (data5)  80111614
```

## cases.py: split the script command table into cases

Reads the 0xDE-entry jump table `lbl_802C0078` from the original main.dol.
It splits `func_8010C604` into one block per command and lists each
block's calls. Modes:

- `--gd` (default): only cases that use the game-data object (`func_80112FDC` / `lbl_803491CC`)
- `--all`: every case
- `--dump`: every case with its disassembly

**Inputs:** the path to the original `main.dol`, and the asm file (default
`asm/main/game/code_800F3228.s`; change it with `--asm FILE`).

```sh
python3 tools/analysis/cases.py orig/main.dol            # the 37 game-data cases
python3 tools/analysis/cases.py orig/main.dol --dump | grep -A16 '^== cmd 0xC1 '
```

Example output (start of the default mode):

```
== cmd 0x03  @ 8010C6E8  (247 insns)  gamedata=Y
   calls: func_80112D34 func_80112FDC func_80112FD4 ...
...
# 37 cases shown (213 distinct case bodies, 222 table entries)
```

## arclist.py: list the contents of a .arc or .arc.clz archive

The game's `.arc` files are U8 archives (magic `55 AA 38 2D`). The
`.arc.clz` files are U8 archives in a custom LZSS wrapper (magic `CLZ\0`),
which the script decompresses in memory. The format notes are in the
script's docstring. It reads only and writes nothing; it never extracts.

**Inputs:** an archive from the extracted disc (keep these out of the repo).

```sh
python3 tools/analysis/arclist.py path/to/maps1.arc
python3 tools/analysis/arclist.py path/to/mainchapter1.arc.clz --nested
```

`--nested` also lists the U8 and CLZ archives found inside the archive.

## Limits

- The addresses in `cases.py` (`lbl_802C0078`, `func_8010C604`, and the end at
  0x801127C4) are for the US release (GYWEE9, rev 0) only.
- `xref.py` finds direct references only. It misses addresses built some
  other way at run time, such as from a table plus an index, or from a
  function pointer kept in RAM.
- The rel results are section offsets, not RAM addresses. The rels load at a
  different address each time, so use the module's load base in Dolphin to
  convert them.
