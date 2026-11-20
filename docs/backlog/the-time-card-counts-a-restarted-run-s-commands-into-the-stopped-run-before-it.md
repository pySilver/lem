---
worth: later
where: skills/lem/assets/board.html:timeOf
added: 2026-11-20
---
# the time card counts a restarted run's commands into the stopped run before it

a landing's checks run 2 commands, the first ends (gate command=make test exit:=0), then lem land checks SLUG --stop (gate.end result=stopped); /lem land runs them again on the same tip (gate.start, gate command=make test exit:=0). landing() continues the object run on the same tip, since neither gate.start nor gate.end resets it, so run.count is 2 and run.done true, and the open piece says "The tests of the criteria run" while the new run's second command has not started. The base commit has it: gate.start there does not touch run either.

Seen outside the change by review round 2 of task board-ends-checks-at-their-end (2026-11-20); the base commit has it.
