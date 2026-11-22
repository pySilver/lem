---
worth: later
where: skills/lem/scripts/lem_board_pages.py:card_chips
added: 2026-11-22
---
# A stopped task's card on the kanban has no chip of its own

A task in landing whose stop the guard of a stopped session logged (session.stopped, after the status message at 11:39 and the restart at 11:49 in the unit cases of #37) has the row "Its session stopped: open a fresh one" in "Waits for you", but its card stays in the column "Checks and review" with no chip that says so. The card of a task with no session gets the chip "no session" or "session does not answer" from session_need (lem_board_pages.py:card_chips, and lem_board_task.py for the task's page); stopped_of has no such chip. The owner who looks at the Tasks view alone does not see the stop.

Seen by the builder of task 3 of dead-tasks-woken-or-shown (2026-11-22).
