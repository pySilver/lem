---
worth: later
where: skills/lem/scripts/lem_board_pages.py:backlog_item
added: 2026-11-23
---
# A backlog item never shows that it has a task

The Backlog view draws each item with its "Start a task" button whatever the tasks are:
`backlog_item` reads the item and never the board's model. On 2026-11-23 at 11:00 the live board
still offered "Start a task" on `an-ignored-pycache-a-builder-left-makes-the-checks-red`, whose task
was building in its own session. A second press posts the item again, and `act_start` in `serve.py`
refuses it with "is a task already, and it is ...: say the new one in other words", a text written
for the words of a new task, not for an item. A fix reads the task of the item's slug from the model
and shows its state and a link to its page in place of the button.

Seen outside the change by the builder of task start-shows-the-started-task (2026-11-23); the base commit has it.
