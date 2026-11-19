---
worth: later
where: skills/lem/assets/board.html:focusOf
added: 2026-11-19
---
# The large card skips a task approved with no lead

On the board of all tasks, the large card shows the first task of `m.forOwner`, `m.blocked`,
`m.landing`, `m.building`, `m.ready` or `m.queued`. A task whose newest block is `held` with
`the interview waits for the owner`, and whose criteria the owner approved after it, has
`t.approved` set and `t.forOwner` false: it waits for Lem to start its lead (`lem companion due`'s
`start`). `derive` puts no `held` list in the model, so that task is in none of the lists
`focusOf` reads. With `gift-note-in-export` approved at 14:20 and no other task, the large card
says "Nothing runs" and "Every task has landed, was answered or was dropped.", while the Building lane holds the card "Approved" with Lem as the actor
and the title counts "1 approved, with no lead yet". The fix is a place for such a task in the
order of `focusOf`, after `m.building`; `tests/test-board.sh` holds the board's rows for it, so the
fix comes with a check of the large card there.
