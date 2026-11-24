---
worth: later
where: src/lem/board_model.py:stop_due
added: 2026-11-24
---
# A shell command keeps the row of a stopped session after a readable turn

`stop_due` returns None at once when the task's session runs a shell command (`shell` is not
false), before it looks at the session's turn. `session.guard_refusal` does the same and answers
`working`. The step `worked`, which logs a turn read after an unread status message and so ends
the stop (`stop_stands`), is never due while a shell command runs.

The run, read in the code at 3247d8fe (not run):

1. Lem cannot read the signs of `refund-rounding`'s session. The unread status message goes out
   at 11:39, and the unread stop is logged at 11:49. "Waits for you" shows the row of the stop.
2. At 11:55 the signs read again: a turn at 11:52, and `shell` true, since the agent runs the
   test suite, which takes 30 minutes.
3. Each look until the suite ends gives no step: `stop_due` returns at its first test of `shell`.
   The row stays, with "Open a session" on it.
4. The owner presses it. `guard_refusal` answers `working`, and the board says "Its session works
   again, so no session was opened", beside the row that says it stopped.
5. When the suite ends, the next look gives `worked` from the turn of 11:52, and the row goes.

Step 5 holds only once `WRITES_WORKED` in `board_model.py` is true. It is false at 3247d8fe, so
today no readable turn ends an unread stop, with a shell command or without: the row stays until
a work event or a `session.open` (the item
`a-session-that-answers-each-status-message-keeps-the-row-of-an-unread-stop.md`). So the
sentence "the row stays stopped while a shell command is still active" is the case of a switch
that is off; a reader who repairs it now changes nothing the owner sees.

- (a) Nothing now; decide when `WRITES_WORKED` is switched on. Cost: none before the switch; after
  it, the false row for as long as the shell command runs.
- (b) With the switch, `worked` is due while a shell command runs: the test of `shell` moves after
  the step `worked` in `stop_due`, and `guard_refusal` lets `worked` pass it. A turn read after
  the message is proof the session works, whatever runs in its shell. Cost: two conditions and a
  unit case of each, in the release that switches `WRITES_WORKED` on.
- (c) `stopped_of` shows no row while a shell command of the session runs, with no record. Cost:
  the row comes back each time the command ends with no turn after the message.

Recommendation: (b), in the same change as the switch of `WRITES_WORKED`.

Seen by a builder of 2026-11-24 in the guard of a stopped session; read again for this item the
same day.
