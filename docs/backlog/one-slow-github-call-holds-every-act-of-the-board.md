---
worth: yes
where: skills/lem/scripts/serve.py:merge_in_thread
added: 2026-11-21
---
# One slow GitHub call holds every act of the board

The board server runs each call into Lem's scripts in its own process, one at a time, under one
lock, `SCRIPT_LOCK` (`lem_run` and `session_run` in `serve.py`): the scripts run in-process through
`lem_sibling.run`, which redirects the process's stdout and stderr, so two at once would mix their
output. The board's merge (`merge_in_thread`) runs `land.py merge` through `lem_run`, and that call
holds the lock through `merge_lock`'s wait, `git fetch`, `gh pr merge` and `gh pr view`. The forge
look (`forge_once`) holds it through `land.forge_look`, another `gh` call. No `gh` call has a time
limit: `gh_in` in `land.py` runs `subprocess.run` with no `timeout`.

A run, from reading the code (not run, and the length of a slow GitHub answer is not measured):
the board shows two repositories, `shop` and `docs`. The owner taps the merge of `shop`'s pull
request on his phone, and GitHub answers `gh pr merge` slowly. While it waits, he taps his yes to
the criteria of a `docs` task, and the server's wake of a `docs` session for a conflict comes due.
Both wait for `SCRIPT_LOCK`, so his yes does not land and his page does not come back until the
`shop` merge ends. A `gh` call that hangs holds every act of the board on every repository for as
long as it hangs.

The options:

- **The board's merge as a child process outside the lock** (`subprocess.run([sys.executable,
  "-B", land.py, "merge", ...])`), keeping the task's step lock and the repository's `merge.lock`.
  Costs one local process for each merge and no act of the owner; the forge look keeps the lock.
  It also shrinks the window in which a confirmed merge can meet a newer proposal (the same
  review's finding 3).
- **A time limit on each `gh` call** in `gh_in`, with a refusal that names the retry. Bounds the
  wait, does not remove it; the limit would be a guess until a slow call is measured.
- **Both**: the merge leaves the lock, and the forge look and the merge are bounded.

Settled by the maintaining session on 2026-11-22 (the owner gave it the design on 2026-11-16): the
first option. The board's merge runs as a child process outside `SCRIPT_LOCK`, and keeps the task's
step lock and the repository's `merge.lock`. It removes the wait for every other act at the cost of
one local process for each merge. No time limit on `gh`: until a slow call is measured, its value
would be a guess, and the refusal it brings would be an act of the owner's.

Where it surfaced: the outside review of 2026-11-21 (Astra, tip 4, and its answer to finding 3;
the second reader's check of Sol's finding 1, which named the `gh` call with no time limit).
