# Notes of the step `board-duties` for other steps

What the step `board-duties` gives, what the other steps of group 4 and after may count on, and
what it needs in files it does not own.

## What the duties are

`board/duties/runner.py` runs the seven duty paths of the design's part 2 in this order at each
tick (20 s), for each workspace on the list but one whose state folder holds `demo`: `forge`,
`merge`, `conflict`, `queue`, `guard`, `prune`. Each is `tick(duty)` over a
`context.Duty` (the workspace's name, a `Here` with its ports bound for the server's environment,
the moment, and `memory.Kept`). A duty calls the `app` function of its command in this process;
no `lem` subprocess runs. One failure costs no other (`seams.py`): the forge's is the board's
problem "the board's look at GitHub failed: ...", another duty's "the board's duty NAME failed:
...", the prune's one line of the server's log.

The end wake (`wake … merged`) is part of `conflict.py`, so that the runner keeps the seven paths
that `tests/unit/board/test_slice.py` counts.

## For `board-views` and `board-pages`

- **The board's problems.** `lem.board.duties.memory.MEMORY.problems_of(checkout)`: the lines of
  `Statusbar.problems` (a look at the forge the forge did not answer, a bookkeeping that failed,
  the sessions that do not read, a duty that failed). They live in the server's memory, as on
  `main` (`Workspace.forge["problem"]`, `session_problem`).
- **The forge's last look.** `.lem/state/forge.json` in the form of `lem.app.owner.forge.Look`
  (`looked`, `seen` by task with `head` and GitHub's `mergeable` in capitals), written whole at
  each look. `forge` and `forge_title` of the status bar read `looked`.
- **A server merge's line.** `MEMORY.of(checkout).said[slug]`: "Lem merges ...", then "Merged:
  ...", "The merge did not go: WHY; FIX", or "The owner's merge still stands for TIP ...".
  `MEMORY.of(checkout).running()` names the tasks whose merge the server runs now.

## For `board-acts`

- The owner's press of Merge runs `app/landing/merge.run` itself. When it runs in a thread of
  the server, put the thread in `MEMORY.of(checkout).merging[slug]`: the forge duty then leaves
  the pull request's bookkeeping to the merge, and the merge duty starts no second merge.
- Amendment A4 counts approved tasks when the forge call goes. For his press too, pass
  `before_call=partial(merge_count.at_call, duty, slug)` to `app.landing.merge.run`.
  The callback reads the current records under both landing locks.
- Four rows of his press moved to you (`tests/ledger/moves/board-duties.tsv`): a press after a
  moved base, a press whose request read the task before his refusal, a second press while his
  merge stands, and the note of his own press that a moved base refused.

## For `board-service`

- The Push watcher in `board/life.py` handles each new wait (`duty:push-new-waits`).
- `runner.tick(home, now=None)` and `runner.loop(home, stopping)` keep their places in
  `board/life.py`.

## For `addons-outside`

`duty:wake-inbox-question` moved to you: after the Inbox took a question, the add-on wakes the
live session with `lem.app.sessions.waking.wake(here, slug, "inbox", None, now)`, which opens
none when no session lives. The board imports no add-on.

## For `core` (`records/`)

- **A4's record.** At each forge call to merge, the server appends one framed line `{at, task, tip,
  by, waiting, behind}` to `.lem/state/merge-line.jsonl` (`board/duties/merge_line.py`,
  `Waited`): `waiting` is how many approved tasks waited besides the one that merged. It is the
  server's record, as `forge.json` is. Asked, when a journal entry suits better: `waiting` and
  `behind` on `MergeIntent`, which the merge writes before its call.
- **Retention.** `Summary` and `Total` fit as they are. The fold clears the record's citations
  of the files that go: the landing's evidence (checks, reviews, filed items, the resolution,
  the merge reads' briefs, Jev's reads, the proposal's text and notes, the polish pass's files),
  the decisions (amendment A2 puts them in the merge commit's text) and the investigation's
  report path. Of the criteria only their size stays. The dates in the two session logs count
  toward the task's age.

## For `sessions`

A wake of a task with no session on record, from the server, fails: "no workspace of agterm is
known for SLUG: no session of it or of this repository is on record, and this runs in no
session of agterm" (`app/sessions/placing.py`). Seen in `tests/journeys/test_duties.py` for the
end wake of a task landed by the skeleton's commands, which opened no session. The duty logs it
and tries again after five minutes. On `main` the server's `lem session open` opened such a
session. Asked: a workspace for an open from no session (the first of the terminal's, or the
one of the repository's newest session of any task).

## For the plan

- `store/retention.py` is the package `store/retention/` (`rules`, `fold`, `totals`, `files`,
  `trees`, `folders`, `old`, `answer`, `run`, `said`): one module held more than wemake's seven
  members and twelve imports.
- `app/retention_days.py` reads `state.keep_days` and its source for `lem prune` and the hourly run.
- The small record keeps `session-acts.jsonl` beside `sessions.jsonl`: Lem's acts on the
  sessions are the stand-in of journal entries (notes/sessions.md), and without them the end
  wake would wake a pruned task whose worktree stays.
