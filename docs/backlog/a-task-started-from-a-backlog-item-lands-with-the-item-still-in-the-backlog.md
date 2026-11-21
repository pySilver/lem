---
worth: later
where: skills/lem/prompts/small.md
added: 2026-11-22
---
# A task started from a backlog item lands with the item still in the backlog

The task `guides-under-800-words` was opened from the backlog item
`docs/backlog/two-guides-are-over-the-800-words-agents-md-allows.md`: its `task.md` gives that
path as the ask. Its fast-track builder followed `skills/lem/prompts/small.md` step by step, made
the change in commit 84b9896 (`docs/board.md` 932 to 795 words, `docs/flow.md` 868 to 798), wrote
the state `ready`, and the item was still in `docs/backlog/` on the branch. The item left only
because the task's session then asked the builder to `git rm` it, in commit 0ee385b.

No text of Lem names that step. `skills/lem/prompts/small.md` names the backlog only for the
items its builder files (step 7). `agents/lem-builder.md` names it only in rule 6, the item format
for a defect outside the task. `skills/lem/stages/land.md` names it only for the items
`lem land file` writes for a review and for the items of the polish pass, and says an item the
owner does not want is never deleted. `skills/lem/scripts/land.py` reads the backlog folder for the
items the branch adds (`branch_items`, `builder_filed`) and never for the item the task came
from. So a task opened from an item, by the board's "Start a task" or by `/lem night`, lands with
its item still open unless its builder happens to remove it; earlier tasks did so by hand, as
337993c did in its fix commit.

Seen outside the change by the builder of task guides-under-800-words (2026-11-22); the base commit has it.
