---
worth: later
where: skills/lem/scripts/project.py:outcome_of
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
