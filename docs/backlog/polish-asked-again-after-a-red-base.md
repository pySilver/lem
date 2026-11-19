---
worth: yes
where: skills/lem/scripts/land.py:cmd_polish
added: 2026-11-19
---
# the polish pass is asked again after a red base held the task

`stages/polish.md` says the pass runs once for a task, and that the rebase of `base` keeps it. One
landing of status-boards-steady-look (2026-11-19) went another way:

1. `lem land polish --done` logged the pass on `00c2291` (four commits, three items filed).
2. `checks` was red by a test of the base, so the task went `blocked` with `the base is red` and
   `after:` a task for that test, and that task landed as `28d3c81`.
3. The task went `ready` again, and `lem land start`, then `base`, rebased it onto `28d3c81`.
4. `lem land polish` then printed `"done": false` and took the rebased tip, `58e5f1e`, as the
   start of a new pass.
5. `checks` refused: "the polish pass started at 58e5f1ecb and is not done". Lem closed the new
   pass with `--done` and no commits, so the record holds a second pass that no builder made.

What to look at: whether `start` of a task that comes back from `blocked` drops the pass that
`landing.json` holds, or whether `cmd_polish` compares the pass with the tip and not with the
range of the task's own commits. The fix keeps a pass across a rebase of `base` after any stop,
as `stages/polish.md` says.
