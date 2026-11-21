---
worth: yes
where: skills/lem/scripts/project.py
added: 2026-11-21
---
# GitHub Issues as a second tracker

On 2026-11-17 the owner picked "GitHub Issues as a second tracker" on a page: "Thats a real gap.
Github is most used by typical developers. We cannot expect adoption without GitHub support". The
code takes one kind: `TRACKERS` in `project.py` is `("linear",)`, and `/lem read`, `task-dir
--ticket` and the landing's comment reach a ticket only through `lem-linear`.

What the work needs:

- `kind = "github"` in `[tracker]`, with no other key: the repository is origin's.
- A skill for it beside `lem-linear`, with the same steps (`check`, `read`, `start`, `land`, `drop`,
  `answer`): an issue read by its number or its address, marked as started, and commented on at
  the landing, through `gh`.
- `/lem init` proposes `github` when the repository's issues are in use and no Linear key shows.
- A backlog item is still never mirrored to an issue, and Lem opens no issue unless the owner asks.
