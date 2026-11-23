---
worth: later
where: skills/lem/prompts/nap.md
added: 2026-11-23
---
# The nap brief says every task holds its report and its decisions

"Falling asleep" in `skills/lem/prompts/nap.md` tells the napping agent that under `tasks/` each
task has `ask.txt`, `task.md`, `state.md`, `report.md` and `decisions.jsonl`. Since
`an-ended-task-s-records-stay-on-the-machine-for-ever`, `lem project prune` leaves an ended task
that nothing happened in for `state.keep_days` days (30 by default) only its small record
(`lem_artifacts.SMALL_RECORD`: `state.md`, `ask.txt`, `task.md`, `landing.json` and the ticket's
and the resume's files). So in a state folder older than a month, most folders under `tasks/` hold
no `report.md` and no `decisions.jsonl`: in this repository a dry run with `--days 0` on
2026-11-23 found 65 ended tasks it would reduce so. The sentence was not changed by that task,
since `AGENTS.md` says a change to `prompts/nap.md` keeps the owner's voice and is tried with one
real nap.
