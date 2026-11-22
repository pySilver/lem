---
worth: later
where: skills/lem/scripts/project.py:outcome_of
added: 2026-11-22
---
# The first line skips an outcome that opens with a short bold phrase

`outcome_of` tells a bold label (`**Today:**`) from a bold sentence by its length alone: a line whose
first bold run closes within three words is a label, and its paragraph is skipped. So an outcome
whose paragraph opens with a short bold phrase is never quoted. Run on a `task.md` whose `## Outcome`
holds "**Done** shows the 20 newest ended tasks, and one row leads to the rest." and then "The picker
keeps the same twenty tasks in its list.", it returned the second sentence, about the picker
(github-issues-tracker's polish pass, 2026-11-22). A label could be told by its form instead: a bold
run that ends in `:`, or one that is the whole line. The fix needs a case in `tests/unit/test_task.py`
for a short bold phrase beside the ones for `**Today:**` and a bold sentence.

The task bold-outcome-quoted-whole carries the same change of `outcome_of` as github-issues-tracker
(its commit 4efe7e3, unpushed), and its branch also edits
`docs/backlog/the-first-line-skips-a-bold-outcome.md`, the item that change ends. Change this one
after that task lands or is dropped, so that the two branches do not conflict, and remove that item
then.
