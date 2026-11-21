---
ruled: 2026-11-21
area: The settings, the seats and the tracker
---

# One number of days in the project's settings keeps the state folder small

His words of 2026-11-21, in the maintaining session, after it measured `.lem/state` of Lem's own
checkout at 75 MB eight days after the first commit; a quote is his words.

**One number of days in the project's settings keeps the state folder small**: "I think that
`.lem/state` should not grow to gigabytes. Maybe KEEP_DAYS should be configurable and one would
configure it to let's say 7 days instead of 30 to keep disk usage in control." And, when the
session proposed this machine's file for the number: "Why machines? I thought that those logs are
per project and stored in project .lem dir". So the number is a key of `.lem/project.toml`, 30 by
default, and no key of `machine.toml` or of `.lem/project.local.toml`.

The form is the session's: the key is `state.keep_days`, a whole number of 1 or more, read as the
base branch has it, so a task's branch cannot lower it. `lem project prune` removes what is older:
the working files of a task that ended (the ones its map calls work, such as the review tool's
archive of a round), with its documents and records kept; and whole, a question to the experts, a
panel's folder, a nap and a copy of the cast. It replaces the two constants of 30 days, the
experts' and the naps', which were guesses. The board server runs it for each workspace each hour,
since it reaches across tasks, and `lem project prune --dry-run --days N` shows what a number would
remove before he sets it.
