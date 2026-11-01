# Skip Intro patch builder (GYWEE9 US)

`build_skipintro.py MAIN_DOL CHAPTER1_ARC SYSTEM_MES OUTDIR` reads the
original `main.dol`, `files/Chapter1.arc` and `system.mes` and writes a
patched `Chapter1.arc`, a patched `system.mes` and `patch_report.txt`
into OUTDIR. It never writes to its inputs. Keep the outputs out of the
repo.

- `Chapter1.arc` entry 1 (the opening script) gets a "Skip the intro?"
  Yes/No prompt. No plays the intro unchanged. Yes goes straight to the dog
  choice and the four naming screens, then to the intro's ending (see
  notes/findings.md 7.13).
- `system.mes` gets ids 0x1F8 and 0x1F9, both pointing at "Skip the
  intro?" with choice code 0x40. The prompt uses 0x1F9; 0x1F8 stays free
  for the milk-summary Gecko's hook. Space comes from sharing message
  0x10's text with its identical twin 0x0F.

Both outputs are exactly the size of the originals (the disc is full), so
they can be replaced in place. Entry 1 is re-encoded with an optimal-parse
CLZ, and it already fits its slot, so every other entry is byte-identical.
If a future change made it too big, the builder would re-encode other
entries, largest saving first.

The script checks itself: stack balance of the patched script, CLZ and U8
round trips, that re-encoded entries decompress to their original bytes,
that untouched entries are byte-identical, and that both output sizes
equal the originals.
Replace both files in the disc image (for example with Dolphin's
"Extract/Replace" in a file system view, or by rebuilding the disc from
the extracted folder).
