---
worth: later
where: skills/lem/scripts/lem_board_model.py:waits_for
added: 2026-11-22
---
# A task with a second row beside "no session" is still answered in the session that is gone

A task in held ("the migration needs the owner") with no session in lem session list has two rows of Waits for you, session and held, and its "where" is "It waits on what its state says: “the migration needs the owner”. The task’s session says what to do."; a task in planned ("plan written, the owner reads it") with no session has the rows session and plan, and its "where" is "Read the plan, then build it or drop the task on this board, or tell the task’s session.". waits_for takes the row's words only when "no session" is the task's one row, so both fall to answer_of. The base commit gives the same two texts.

Seen outside the change by review round 1 of task no-session-row-names-open (2026-11-22); the base commit has it.
