---
worth: yes
where: skills/lem/scripts/project.py
added: 2026-11-21
---
# An ended task's files stay on the machine for ever

No script of Lem removes `.lem/state/events.jsonl` or a folder of `.lem/state/tasks/`. Only the
naps (`cmd_may_nap`, `NAPS_KEEP_DAYS`) and the experts' folders (`experts.py:prune`, `KEEP_DAYS`)
leave, each after 30 days. On 2026-11-21 `.lem/state/tasks/` was 72 MB for 18 tasks, most of it in
`reviews/` (18 MB in `interview-in-a-companion`); a thousand tasks are about 4 GB (an unmeasured
estimate, from that ratio). The board's `derive` reads every event of every task, and the log of
those 18 tasks is 830 lines; copied to 1,003 ended tasks it is 47 MB (measured, see
`the-board-s-done-column-has-no-limit.md`).

The owner's ruling (2026-11-21, `docs/rulings/the-done-column-shows-the-newest-ended-tasks-and-one-setting-says-how-long-an-ended-tasks-files-stay.md`):
one key of the project's settings, a time, after which an ended task's files leave; and
`events.jsonl` keeps one summary event in place of the events of a task that is past it.

What the history holds elsewhere, so the local copy adds nothing after the time: the plan in
`docs/plans/`, the commits, the backlog items, and the pull request's text, which `land.py` writes
from `pr.md` (the owner's words, the criteria, the checks, the review rounds, the decisions of the
build and the breakers, what was not done).

What only the machine holds, and who reads it after the end:

- the retro reads the `review`, `proposed` and `careful.missed` events, `lem decisions list` and
  `report.md`, "since the last retro" (`stages/learn.md`); the naps read recent tasks
  (`stages/nap.md`). The time of the key must be longer than the gap between two retros.
- `/lem resume` of a dropped task reads `state.md`, `decisions.jsonl`, `handoff.md`,
  `breaker-*.md`, `ask.txt`, `brief.md` and the files of `RESUMED_FILES` (`cmd_resume`). Past the
  time, a dropped task cannot be resumed, and `cmd_resume` says so.
- three readers need a small record of each ended task with no limit, or they break:
  `cmd_may_start` and `session.py:queued_behind` read the end of the task a queued task waits for
  (with no `state.md`, `queued_refusal` says "no task" and the queued task never starts);
  `cmd_task_dir` keeps a new task from the name of an ended one; and the board's Done column and
  `bm.after_ended` read the end from the events.

The fix:

1. A key of `.lem/project.toml` for the time; its default and its table are the task's to choose,
   after reading "Opinionated and small", "Not every section of the settings stays" and
   "Four places are settings". 30 days matches the naps and the experts; it is a guess, not a
   measure. `docs/settings.md` gets its row (`tests/lem-settings.sh` holds the two one to one).
2. Past the time, an ended task's folder keeps only the record the three readers need: its name,
   its end, its day and its pull request. The rest of the folder leaves, `reviews/`, `talk.md`,
   `media/` and the transcripts' events among them.
3. `events.jsonl` keeps one summary event for such a task in place of its events, written so that
   a reader that tails the log (`Reader.read_log` reads from its last size while the inode stays)
   reads the new file whole.
4. What runs the cleanup is the task's to choose. A step that already runs often and for every
   repository fits, as `cmd_may_nap` removes the old naps.

Tracked files cite folders of `.lem/state/` as the source of a ruling or a plan
(`docs/plans/2026-11-21-agents-md-read-on-demand/map.json`, some files of `docs/rulings/`). Those
folders were never in git, so the cleanup takes nothing from another developer; on this machine the
citations point at folders that left.

Surfaced in the maintainer's session of 2026-11-21, on the owner's question of what 1,000 closed
plans do to the board.
