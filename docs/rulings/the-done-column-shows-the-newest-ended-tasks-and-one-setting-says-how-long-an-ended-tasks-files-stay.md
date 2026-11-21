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

In a second session of the same day, after it measured `.lem/state` of Lem's own checkout at 75 MB
eight days after the first commit: "I think that `.lem/state` should not grow to gigabytes. Maybe
KEEP_DAYS should be configurable and one would configure it to let's say 7 days instead of 30 to
keep disk usage in control." And, when that session proposed this machine's file for the number:
"Why machines? I thought that those logs are per project and stored in project .lem dir".

The form is the session's: the setting is `state.keep_days` of `.lem/project.toml`, a whole number
of 1 or more, 30 by default, read as the base branch has it, so a task's branch cannot lower it,
and no key of `machine.toml` or of `.lem/project.local.toml`. `lem project prune` removes what is
older: the working files of a task that ended (the ones its map calls work, such as the review
tool's archive of a round), with its documents and records kept; and whole, a question to the
experts, a panel's folder, a nap and a copy of the cast. It replaces the two constants of 30 days,
the experts' and the naps', which were guesses. The board server runs it for each workspace each
hour, since it reaches across tasks, and `lem project prune --dry-run --days N` shows what a number
would remove before he sets it. All of it is Lem's untracked state, and nothing of it goes to git.
The backlog items `docs/backlog/the-board-s-done-column-has-no-limit.md` and
`docs/backlog/an-ended-task-s-events-and-records-stay-on-the-machine-for-ever.md` are the work
that is left: the Done column, the events of an old task in `events.jsonl`, and the small record
that is all an old task needs to keep.
