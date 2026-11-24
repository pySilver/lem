---
worth: later
where: src/lem/project.py:outcome_of
added: 2026-11-22
---
# The first line skips a bold outcome

`outcome_of` quotes the first sentence of prose under `## Outcome` in a task's `task.md`, and skips
a paragraph that opens with a bold label, such as `**Today:**`. A bold sentence, on one line or
wrapped over more, is quoted whole (f48009ee, d1d7880c, 8bda2ea1). But the label is still told by its
length too: a line whose first bold run closes within three words is a label, whatever follows it on
the line, and its paragraph is skipped. `prompts/writing.md` asks for bold on the one phrase of a
paragraph that carries the outcome, so an outcome that opens with a short bold phrase is never quoted,
and the first line to the owner quotes the next paragraph in its place.

Run at 9b1eddb8 on a `task.md` whose `## Outcome` holds "**Done** shows the 20 newest ended tasks, and
one row leads to the rest." and then "The picker keeps the same twenty tasks in its list.":
`project.outcome_of` returns `'The picker keeps the same twenty tasks in its list'`, the second
paragraph (github-issues-tracker's polish pass met the same on 2026-11-22). A label could be told by
its form alone: a bold run that ends in `:`, inside the bold or right after it, or one of a few words
alone on its line. The fix needs a case in `tests/unit/test_task.py` for a short bold phrase beside the ones
for `**Today:**` and a bold sentence.

The rule above was built (3ede70f1) and reverted (cb8f211d) after a review of 2026-11-24: it quotes a
label that has no colon. `prompts/writing.md` names the two labels of a story `**Today**` and
`**After**`, with no colon, and a label of a few bold words with text after it on its line is no
outcome. Over the five inputs below, each the first paragraph under `## Outcome` with "The picker
keeps the same twenty tasks in its list." after it, the rule above gives:

- "**Done** shows the 20 newest ended tasks, and one row leads to the rest.": "Done shows the 20
  newest ended tasks, and one row leads to the rest", right.
- "**Today** - the footer says 2025.": "Today - the footer says 2025", a label quoted.
- "**Before.** The invoice shows 100 EUR after the refund.": "Before".
- "**1.** The owner opens the board.": "1".
- "**Today:** the footer says 2025.": the next paragraph, right.

Over the 97 `task.md` files of this repository's state folder (2026-11-24, `outcome_of` run under
each rule and compared with today's), the rule above changes one result and makes none right: `dead-tasks-woken-or-shown` opens with "**Today**, the landing of
merge-leaves-board-lock:", which it quotes as "Today, the landing of merge-leaves-board-lock".

The question is the owner's: what makes a bold run at the start of the outcome a label?

1. Today's rule: a bold run of three words or fewer, or one that ends in `:`. "**Done** shows ..."
   is a label and is skipped; "**Today** - ...", "**Before.** ..." and "**Today:** ..." are
   labels. Only the first is wrong, and it is the case `prompts/writing.md` asks for.
2. The rule above: a bold run that ends in `:`, inside the bold or right after it, or a few bold
   words alone on their line. "**Done** shows ..." is quoted; "**Today** - ..." is quoted as
   "Today - the footer says 2025" and "**Before.** ..." as "Before"; "**Today:** ..." is a label.
3. Today's rule, except that a run of three words or fewer that ends in a letter or a digit, with a
   letter, a digit or a code span next on its line, opens the sentence. "**Done** shows ..." is
   quoted; "**Today** - ...", "**Before.** ..." (it ends in `.`), "**1.** ..." and "**Today:** ..."
   are labels, and so is "**Today**, the landing of ...". Over the 97 files it changes no result:
none of them opens its outcome with a short bold phrase.

Recommendation: 3. It quotes the phrase `prompts/writing.md` asks for, keeps every label the
files hold, and its case in `tests/unit/test_task.py` sits beside the ones for `**Today:**` and a
bold sentence. A label in the form "**Today** the footer says 2025." (no mark after the bold) would
then be quoted; none of the 97 files has one.
