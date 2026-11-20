---
worth: later
where: skills/lem/assets/board.html:focusOf
added: 2026-11-20
---
# The large card skips a task whose choice was answered with no lead yet

On the board of all tasks, a task whose newest block is `held` with `choice 1 waits for the owner`,
and whose choice 1 the owner answered after it, has `t.answered` set and `t.forOwner` false: it
waits for Lem to start its lead again (`lem companion due`'s `start`), and the Building lane holds
its card "Answered" with Lem as the actor. `focusOf` reads `m.forOwner`, `m.blocked`, `m.landing`,
`m.building`, `m.approved`, `m.ready` and `m.queued`, and such a task is in none of them. With
`refund-late-orders` answered ("refund them") and no other task, the large card says "Nothing
runs" and "Every task has landed, was answered or was dropped.", while the title counts "1
answered, with no lead yet". The fix is the place that a task approved with no lead has in the
order of `focusOf`, for `t.answered` too, with a check of the large card in `tests/test-board.sh`.

Seen outside the change by the builder of task large-card-shows-an-approved-task (2026-11-20); the base commit has it.
