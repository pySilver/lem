---
worth: later
where: skills/lem/scripts/lem_board_model.py:SAYS
added: 2026-11-22
---
# The timeline calls the owner's refused merge the merge agent's

The owner presses Merge on the board and confirms, and Lem refuses the merge because the base moved:
the event log gets `merge.refused` with `by: owner`, `via: server`, `from: lem` and `kind: base`
(task `project-rulings-one-list` in this repository's log, 2026-11-22 08:44:09). The task's
activity draws that event from the entry `"merge.refused"` of `SAYS`, whose head is "Lem refused
the merge agent’s merge" for every refusal `from: lem`, whatever its `by`. So the owner reads that
the merge agent's merge was refused, right after his own press. The entry `"merge.start"` beside
it already tells "your merge" from "the merge agent’s merge" by `by`; the refusal's head could do
the same.

Seen outside the change by the builder of task merge-button-after-failed-merge (2026-11-22); the base commit has it.
