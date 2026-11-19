---
worth: later
where: skills/lem/assets/board.html:ring
added: 2026-11-19
---
# The label inside the ring of the phases touches the ring's stroke

On the board of one task, the card of the phases draws a ring of 116 px with a stroke of 10 px,
and a count and a label inside it (`.ring-center span`: 12 px, upper case, spaced .05em). In both
pictures `assets/screens/task-light.png` and `task-dark.png`, made by `tests/board-showcase.py` at
the commit that made them on `feat/status-boards-steady-look`, the label "PLAN TASKS" touches the
ring's stroke on the left and on the right. The builder of that task saw it and left it.

A smaller label, less spacing, or a ring with more room inside would give it air. The pictures
are then made again with `python3 -B tests/board-showcase.py DIR` and looked at in light and in
dark, since no check measures the label against the ring.
