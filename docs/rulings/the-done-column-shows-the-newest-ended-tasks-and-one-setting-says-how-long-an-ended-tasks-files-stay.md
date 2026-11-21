---
ruled: 2026-11-21
area: The settings, the seats and the tracker
---

# The Done column shows the newest ended tasks, and one setting says how long an ended task's files stay

His answers in the maintainer's session of 2026-11-21, on what 1,000 closed tasks do to the board
and to the state folder; a quote is his words.

**The Done column shows the newest ended tasks**: "I belive we should either keep `last N` done
items or make `ttl` limits. First works better for project that are not in constant development
phase."

**One setting says how long an ended task's files stay**: "We don't need to preserve whole
development history locally, thats for sure (or keep it for others in git)." To the session's
proposal that a landed task's large files leave after a time and a dropped task's folder stays as
long, so that `/lem resume` still works: "Agree, configurable ttl per project" and "I think we need
a single ttl setting to avoid complexity". To the proposal that `events.jsonl` keeps one summary
event in place of an old ended task's events: "OK".

The form is the session's: the setting is one key of `.lem/project.toml`; a small record of each
ended task (its name, its end, its day and its pull request) stays on the machine with no limit,
because a task queued after it, the guard on a task's name and the board read it; all of it is
Lem's untracked state, and nothing of it goes to git. The backlog items
`docs/backlog/the-board-s-done-column-has-no-limit.md` and
`docs/backlog/an-ended-task-s-files-stay-on-the-machine-for-ever.md` are the work.
