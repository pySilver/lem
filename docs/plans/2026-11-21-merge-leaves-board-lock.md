# A merge from the board holds no other act of the board

careful: no. The two locks a merge needs, the task's step lock and the repository's merge lock, are kernel locks (`fcntl.flock`) that `land.py` takes in whatever process runs the step, the same way a task's session already runs `lem land merge` in a process of its own beside the server; `land.py`'s merge and its rules do not change, so no topic of `flow.topics` is reached (checked against "Lem changes a developer's repository without his word", "The landing lets through a change that should not land" and "A pull request says green when it should not").

## Acceptance criteria

Size: full, because the board's server changes how it runs a merge, and its look at GitHub learns of a merge that runs.

1. While a merge from the board waits for GitHub, the owner's other acts on the board still answer:
   1. The board shows the repository `shop` with the task `word-in-file`, open as pull request 1.
   2. The owner confirms its merge, and GitHub answers `gh pr merge` slowly.
   3. Meanwhile he gives his yes to the criteria of the task `note-in-readme` of the repository `docs`, on the same board.
   4. While it waits, the board shows "Merging…" on `word-in-file`.
   5. His yes is on record, and its page comes back, while the merge of pull request 1 still waits.
   6. When GitHub answers, pull request 1 is merged and `word-in-file` is landed.
2. Two merges of one repository still take turns: while the merge of `first-move` holds the repository's merge lock, the merge of `second-move` waits for it, and the board shows on `second-move` that it waits for the merge of `first-move`.
3. The board says what came of a merge as it does today: a merge that went through says "Merged: pull request #1 is on main", and one that Lem refused says the refusal's own line, as `lem land merge` gives it.
4. While a merge from the board runs, the board's look at GitHub shows no false failure for that task: when GitHub already calls pull request 1 merged before the merge's step ends, the status bar shows no line that `lem land merged word-in-file` failed. A look that finds `lem land merged` failing for a task whose merge does not run still shows its line, as today.

## Tasks

1. **The board's merge runs as a process of its own, outside the server's one script lock**, and the look at GitHub leaves a task whose merge runs to that merge. Serves criteria 1 to 4. Files: `skills/lem/scripts/serve.py` (`merge_in_thread`, `forge_once`, and the module docstring's lines on `merge_in_thread` and SCRIPT_LOCK), `tests/lem-board-act.sh` (the checks of criteria 1 and 4, and of 2 and 3 where no check holds them yet), and `tests/unit/test_serve.py` when a rule there is a pure function.

## Decisions of the plan

- **The merge runs as `python3 -B land.py --repo MAIN merge ...` with `subprocess.run`, from `merge_in_thread`, and SCRIPT_LOCK is not taken around it.** The backlog item settles this option (`docs/backlog/one-slow-github-call-holds-every-act-of-the-board.md`). A child process takes the step lock and the merge lock itself, and its stdout and stderr are its own, so it does not mix with the server's in-process calls, which redirect the process's streams (`lem_sibling.run`). The child gets the server's environment as it is, so `gh`, the stand-ins of the tests and `LEM_*` reach it as they reach `lem_sibling.run`'s own process calls (`APART`). `after()` (`asked_from`, the `board.act` record) still runs through `lem_run`, under the lock. The backlog item is removed in the same commit (`git rm`), since the change does what it asks.
- **The look at GitHub skips a task whose merge runs in this process (`NOTES.running`).** Today the merge and the look take turns under SCRIPT_LOCK. With the merge outside it, the look can see pull request 1 merged while the merge's step still holds the task's step lock; `lem land merged` is then refused, and the status bar says for a few minutes that it failed. The merge's own step records the landing; a task whose merge ends with no landing (a refusal) is looked at again at the next look, as any open task is.
- **The forge look itself keeps SCRIPT_LOCK**, and `gh` gets no time limit: both as the backlog item settles.

## What this plan does not verify

- A real slow GitHub: the checks hold the stand-in for `gh` in its `pr merge` until the test lets it go. The length of a slow GitHub answer is not measured.
