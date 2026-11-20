---
worth: later
where: skills/lem/scripts/project.py:runs_without_owner
added: 2026-11-20
---
# A back in the second a task opens leaves a span of no length

The owner types `/lem im-away` at 2026-11-19T15:10:00Z, and `/lem im-back` at 15:30:00Z. In the
same second, 15:30:00Z, Lem opens a task: its first `task.state` event has that `ts`. Then `lem
project tasks` gives the task a `without_owner` span `{"from": "2026-11-19T15:30:00Z", "to":
"2026-11-19T15:30:00Z"}`, and its pull request says it ran without him "from 15:30 to 15:30",
though the task never ran without him.

The span starts at `max(start["ts"], first)`, the task's opening, and the back ends it there,
because the test that drops an away and a back that came before the opening is `record["ts"] <
first`, which a back in the same second does not pass. The comparison is the same before the task
`away-for-the-whole-machine`, but since that task `merged` puts the repository's events and the
records of the machine's mark in one list, the repository's events first on a shared second, so
the tie now has two sources. A fix: drop a span whose `to` equals its `from` when the back is the
record that ends it, as the code already drops a span that ended before the opening.
