---
worth: yes
where: skills/lem/scripts/lem_board_model.py:answer_of
added: 2026-11-21
---
# The "where" of a task whose only row is "no session" sends the owner to a session that is gone

A building task ("task 2 of 3") with no session in lem session list has one row of Waits for you, of kind session, whose words say "Open a session here or on the task's header"; waits_for gives answer_of's last line, "Tell the task's session to build it, or type /lem drop gift-note to end it.", as the tooltip of the card's Waits for fact. The same text on the base 473cd9d.

Settled: the "where" of that row says what the row itself says, to open a session here or on the
task's header (or to drop the task), and never names a session that is gone. Read on 2026-11-22 at
f96e87b: `answer_of` still falls through to its last line for such a task.

Seen outside the change by review round 2 of task owner-order-open-defects (2026-11-21); the base commit has it.
