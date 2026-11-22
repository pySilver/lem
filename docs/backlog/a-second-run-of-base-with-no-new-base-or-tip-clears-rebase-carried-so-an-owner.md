---
worth: later
where: skills/lem/scripts/land.py:cmd_base
added: 2026-11-22
---
# A second run of base with no new base or tip clears rebase_carried, so an owner's merge that should stand ends

At the base commit, updates in cmd_base sets rebase_carried to None on every run and sets it again only when tip != origin and the change is covered. lem land base SLUG rebases a covered change onto a moved base with no conflict and keeps rebase_carried; a second lem land base SLUG after a cut-off finds the branch already on the base, tip == origin, and sets rebase_carried to None; propose then finds carried_over false and ends the owner's merge with 'a commit came after the rebase, or the rebase met a conflict', where his merge should stand. Read in the code at 8bda2ea1; not run.

Seen outside the change by review round 1 of task ended-merge-names-its-cause (2026-11-22); the base commit has it.
