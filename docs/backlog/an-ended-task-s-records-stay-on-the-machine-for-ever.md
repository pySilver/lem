---
worth: yes
where: skills/lem/scripts/lem_artifacts.py:working
added: 2026-11-21
---
# An ended task's records stay on the machine for ever

`lem project prune` removes the working files of a task that ended more than `state.keep_days`
ago, replaces all its events in `.lem/state/events.jsonl` with one `task.summary` event, and
removes the old folders of the experts, the panels, the naps and the cast's copies (the owner's
ruling of 2026-11-21, "The Done column shows the newest ended tasks, and one setting says how long
an ended task's files stay", `docs/rulings/rulings.md`). One part of that ruling's form is not
built: past the time, an ended task keeps only a small record, its name, its end, its day and its
pull request.

`prune` keeps each document and each record of an old task: `lem_artifacts.working` gives only
the working files. On 2026-11-21 a dry run over the 17 ended tasks of this repository
(`lem project prune --dry-run --days 0`) removed 67.7 MB and kept 2.6 MB, at most 0.6 MB for one
task. A thousand tasks at that size are about 150 MB (an unmeasured estimate, from that ratio).
Nothing reads these records at a refresh of the board, which reads the event log.

Who reads what of an ended task's folder after the end, so a fix does not break them:

- the retro reads `lem decisions list` (`decisions.jsonl`) and `report.md` "since the last retro"
  (`stages/learn.md`); the naps read recent tasks (`stages/nap.md`). Its events past the time are
  already one summary, so the time must stay longer than the gap between two retros.
- `/lem resume` of a dropped task reads `state.md`, `decisions.jsonl`, `handoff.md`,
  `breaker-*.md`, `ask.txt`, `brief.md` and the files of `RESUMED_FILES` (`cmd_resume`). It already
  refuses a dropped task whose events became its summary, and its refusal ends with `/lem` and the
  text of `ask.txt`: a small record that drops `ask.txt` leaves that line with the first line of
  `task.md`, or with the slug alone.
- `cmd_may_start` and `session.py:queued_behind` read the end of the task a queued task waits for
  from its `state.md` (`read_tasks`; with no `state.md`, `queued_refusal` says "no task" and the
  queued task never starts); `cmd_task_dir` keeps a new task from the name of an ended one; and
  `prune` itself (`task_calls`) touches only a task whose `state.md` says it ended and agrees with
  the log. A small record keeps `state.md`, or these move to the summary event.

Options: (a) keep the records, as `prune` does today; (b) past the time, remove every file of the
task folder but a small record that the readers above read, as the ruling's form says: it bounds
the folder, and takes `report.md` and `decisions.jsonl` from a retro that reads after the time.
Recommendation: (a), until a repository shows records that matter. The unknown that would move it
to (b): the size of the records on a repository with long reports.

Surfaced in the maintainer's session of 2026-11-21, on the owner's question of what 1,000 closed
plans do to the board; the task `old-task-events-summarized` built its events part, the summary
event, and left this item the records.
