---
worth: later
where: skills/lem/assets/board.html:timeOf
added: 2026-11-19
---
# the board shows the checks as running after a stop

`lem land checks SLUG` writes `gate.start`, a `gate` for each command that ended, and one
`gate.end` with its `result` (`passed`, `red`, `refused` or `stopped`). The board does not read
`gate.end`: it is in neither `CHECKS` nor `LANDING_STARTS`, so `landing()` in `timeOf` cuts the
landing at the `gate.start` or the last `gate` before it.

The run: a task in `landing` whose checks run one command of two, then `lem land checks SLUG
--stop`. The log holds `gate.start tip=... commands:=2`, no `gate`, and `gate.end result=stopped`.
The task stays in `landing`, and its time card and lane say "The checks run: 0 of 2 commands
done" as a live span, while nothing runs and the landing waits for the owner's word. The same
holds for a run that ends `refused` by an error of the step before its first `gate`.

What it needs: `gate.end` as the end of the checks' span on the board, with its `result` as the
head ("The checks were stopped", "the checks refused the change"), and the state after a stopped
run drawn as Lem's wait for the owner; a case in `tests/test-board.sh` with a stopped run.
