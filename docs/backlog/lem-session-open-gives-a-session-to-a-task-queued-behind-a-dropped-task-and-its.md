---
worth: later
where: skills/lem/scripts/session.py:cmd_open
added: 2026-11-21
---
# lem session open gives a session to a task queued behind a dropped task, and its refusal says the task gets one when the other is dropped

queued_behind returns None when the after: task is in project.ENDED, which includes dropped, so for a task queued after a dropped task `lem session open SLUG` opens a session although the rule since c28ca79 keeps it queued for the owner's word; for a task queued after an open one, the refusal says "it gets its session when OTHER is landed, answered or dropped". Read in the code at 877d52b, where queued_behind and the refusal are the same.

Seen outside the change by review round 2 of task owner-task-order-stays (2026-11-21); the base commit has it.
