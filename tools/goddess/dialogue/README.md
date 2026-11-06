# Harvest Goddess dialogue (our own writing)

Only the goddess's new lines live here. Nami's original lines are game text: they stay in the review pages in the
session scratchpad and are never committed.

- `goddess_lines_batch1.json`: batch 1 as the user approved it (id -> text; a blank line = a new box, `<name>` /
  `<nick>` / `<son>` placeholders). A = the first summoning, B = calling her at the spring, the hex ids = Nami's wife
  file (nami_wife.mes) entries she replaces when married to the goddess.
- Lore (user): her people lived in the valley long ago and left "when the land rose"; the Mermaid Fossil is one of them
  ("you brought her home"). They loved eating fish, so fish are a favourite gift.
- Voice (user): cheerful, a little bossy, knows she is a princess and expects to be treated like one, flirty; not too
  formal (no "you may").

- `goddess_lines_batch2.json`: the rest of nami_wife.mes as approved (user edits 017, 006, 044, 055, 06E, 0A2, 0A3);
  0A4 / 0AB / 0D2 rewritten without villager names (user: she does not know the villagers personally).
- `goddess_lines_batch3_married.json` (written by Claude, user delegated the rest): `married_<id>` = her version of
  each married-life line in nami.mes (bedtime, bar, ducks, the son's talents and late nights, the grandfather story,
  the chapter-5 advice, chapter 6 old age and farewell, engagement, baby). Nami's courtship / unmarried lines in
  nami.mes stay hers (023 = batch 1 'bar'; 164-166 are Nami's inn lines). Villagers are named by role (the doctor,
  the singer, the professor, the artist), except Takakura (he lives on the farm). Game control codes are kept in place
  (<41> choice, <32><03>{E80x} face, <21:80> typed name, <2B:xx> place, <52>, <50><04> face, {80D4}).
- `goddess_lines_batch4_extra.json`: lines no Nami file covers - W1-W4 her wedding day, M1-M4 at the spring when you
  married another bride, N1-N2 Nami's farewell when you marry the goddess.
