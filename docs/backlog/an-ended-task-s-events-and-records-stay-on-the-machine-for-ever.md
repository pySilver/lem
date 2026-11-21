---
worth: yes
where: skills/lem/scripts/project.py:cmd_prune
added: 2026-11-21
---
# An ended task's events and records stay on the machine for ever

`lem project prune` removes the working files of a task that ended more than `state.keep_days`
ago, and the old folders of the experts, the panels, the naps and the cast's copies (the owner's
ruling of 2026-11-21, "The Done column shows the newest ended tasks, and one setting says how long
an ended task's files stay", `docs/rulings/rulings.md`).
Two parts of that ruling are not built.

**The events.** No script shortens `.lem/state/events.jsonl`. The board's `derive` reads every
event of every task at each refresh. On 2026-11-21 the log of 18 tasks was 830 lines; copied to
1,003 ended tasks it is 46,766 lines and 47 MB, and `derive` takes 149 ms in place of 3 ms
(measured, see `the-board-s-done-column-has-no-limit.md`). The owner said "OK" to one summary event
in place of the events of a task that is past the time.

**The records.** `prune` keeps each document and each record of an old task
(`lem_artifacts.working` gives only the working files). On 2026-11-21 a dry run over the 17 ended
tasks of this repository (`lem project prune --dry-run --days 0`) removed 67.7 MB and kept 2.6 MB,
at most 0.6 MB for one task. A thousand tasks at that size are about 150 MB (an unmeasured
estimate, from that ratio). The ruling's form asks for less: past the time, an ended task keeps
only a small record, its name, its end, its day and its pull request.

Who reads what after the end, so a fix does not break them:

- the retro reads the `review`, `proposed` and `careful.missed` events, `lem decisions list` and
  `report.md`, "since the last retro" (`stages/learn.md`); the naps read recent tasks
  (`stages/nap.md`). The time of the key must be longer than the gap between two retros.
- `/lem resume` of a dropped task reads `state.md`, `decisions.jsonl`, `handoff.md`,
  `breaker-*.md`, `ask.txt`, `brief.md` and the files of `RESUMED_FILES` (`cmd_resume`). If the
  records leave, a dropped task past the time cannot be resumed, and `cmd_resume` must say so.
- three readers need the small record of each ended task with no limit, or they break:
  `cmd_may_start` and `session.py:queued_behind` read the end of the task a queued task waits for
  (with no `state.md`, `queued_refusal` says "no task" and the queued task never starts);
  `cmd_task_dir` keeps a new task from the name of an ended one; and the board's Done column and
  `bm.after_ended` read the end from the events.
- `prune` itself dates an ended task by its last event in the log, so a summary event must carry
  that time.

Options: (a) the summary event alone: it bounds the log, which every refresh of the board reads,
and leaves the records, which nothing reads at a refresh; (b) the summary event and the small
record, as the ruling's form says: it bounds both, and ends `/lem resume` of an old dropped task;
(c) leave both until a repository has some hundred ended tasks. Recommendation: (a), written so
that a reader that tails the log (`Reader.read_log` reads from its last size while the inode
stays) reads the new file whole. The unknown that would move it to (b): the size of the records on
a repository with long reports.

Surfaced in the maintainer's session of 2026-11-21, on the owner's question of what 1,000 closed
plans do to the board; rewritten the same day to what `lem project prune` left.
