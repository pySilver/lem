---
worth: later
where: skills/lem/scripts/lem_board_model.py:answer_of
added: 2026-11-22
---
# The "where" of a blocked task tells the owner to have it built

A task in `blocked` ("the migration needs the owner") with a live session has one row of Waits for you, of kind blocked, whose "where" says "The task’s session stopped on something it cannot settle alone: “the migration needs the owner”. Tell it what to do in the task’s session, or type /lem drop gift-note there to end the task." `answer_of` has no line for `blocked` and falls through to its last one, so `waits_for` gives "Tell the task’s session to build it, or type /lem drop gift-note to end it." as the tooltip of the card's Waits for fact: the session stopped and waits for his word, and the tooltip asks him to have it build.

Seen outside the change by the builder of task no-session-row-names-open (2026-11-22); the base commit has it.
