---
worth: later
where: src/lem/board_model.py:stop_stands
added: 2026-11-24
---
# A session that answers each status message keeps the row of an unread stop

The run, on the events of `StoppedSession` in `tests/unit/test_board_model.py` (#37 of
2026-11-22), with `stop_due`, `waits_of` and `session.guard_refusal` called at each minute from
11:50 to 18:00 at c674b18d:

1. Lem cannot read the session's signs. The unread status message goes out at 11:39, and the
   unread stop is logged at 11:49.
2. From 11:50 the signs read again. The session takes a turn at 11:55 and writes no state block.
3. The readable clock sends a status message at 12:40, 13:26, 14:12, 14:58, 15:44, 16:30 and
   17:16, and the session answers each with a turn a minute later and no state block.
4. No stop is logged after 11:49. The row "Its session stopped, and Lem cannot read it: open a
   fresh one" stays all the time, though the signs read and show turns: `stop_stands` ends a stop
   only at a work event or a `session.open`, and a turn is neither.
5. From 11:55, the owner's "Open a session" gives `working` (`guard_refusal`: the turn is newer
   than the stop).

So the board tells the owner to open a session that works, refuses the open, and the session gets
a message, and spends a turn, every 46 minutes. be719e8c fixed the case where the session does not
answer the readable message; this is the case where it does.

The same gap has a second run. The unread clock never uses a session's `sign` (Decision 3 of
`docs/plans/2026-11-23-guard-sees-unreadable-sessions.md`). The unread message goes out at 11:39; a
look at 11:45 reads the signs and sees a turn at 11:40, and gives no step; a look at 11:49 whose
signs do not read gives `stopped` from the 11:39 message (`stop_due` at c674b18d). The unread stop
is logged over a session that answered. A failed `ps` is one cause (`session.process_table` gives
None on a time-out or an exit that is not 0); how often it fails is not measured.

Both need what the log does not keep: the sign a readable look saw.

- (a) Nothing now. Cost: the false row and a turn every 46 minutes, for as long as the session
  answers.
- (b) A readable look that sees a turn after a standing unread stop, or after an unread status
  message, logs one event with that turn's time. `stop_stands` ends at it, so the row and the
  refused open go, and the unread clock counts from it. Decision 3 stays: it refuses a sign read
  beside signs that do not read, and this one was read when they did. Cost: a new event, which the
  release before must read without harm (a change of form, `AGENTS.md`), and a test for each clock.
- (c) The owner changes Decision 3, so that the unread clock uses a `sign` it reads beside signs
  that do not read. Cost: a turn with no live process behind it counts as work; it fixes only the
  second run.
- (d) `stop_stands` ends while the signs read and show a turn newer than the stop, read at each
  look with no record. Cost: the row comes back each time the signs stop reading.

Recommendation: (b). The unknown that settles it: how often a real session's signs stop reading
and come back, for which the log has no count.

Seen in the review of be719e8c, 2026-11-24, with a run of 11:39 to 18:00; the base before
be719e8c has the first run too.

The owner chose (b) on 2026-11-24, and its reader is built: `fold`, `worked_turn`, `stop_stands`
and the timeline read `session.worked`, and a turn ends only the stop whose status message came
before it. Its writer is built and off: `stop_due`'s step `worked`, which `lem session worked`
and the server's duty act on, waits behind `WRITES_WORKED` in `src/lem/board_model.py`, false
until the release after the one that reads the record. The reader of 0.3.1 folds an event it
does not know as a step of the landing, so its card "Waits for the load: 12, starts below 5"
says "It starts its landing" after the record; the one kind it reads without that,
`session.transcript`, makes its timeline say that Claude Code started in the task's session.
