---
worth: later
where: skills/lem/scripts/land.py:cmd_base
added: 2026-11-22
---
# A second run of base with no new base or tip clears rebase_carried, so an owner's merge that should stand ends

The updates in cmd_base set rebase_carried and rebase_uncovered to None on every run, and set rebase_carried again only when tip != origin and the review carries (review_carries). lem land base SLUG rebases a reviewed change onto a moved base with no conflict and keeps rebase_carried; a second lem land base SLUG after a cut-off finds the branch already on the base, tip == origin, and sets rebase_carried to None; propose then finds no carry in tip_carry, ends the owner's merge with 'a commit came after the tip proposed before', and gives the merge review the same reason, so a fresh merge agent reads the task, where both should carry. Read in the code at 8bda2ea1, and again after task merge-without-review-rerun; not run.

Seen outside the change by review round 1 of task ended-merge-names-its-cause (2026-11-22); the base commit has it.
