---
worth: later
where: src/lem/board_model.py:task_files_look
added: 2026-11-24
---
# The board offers its acts on a task begun on a newer Lem

`task_files_look` applies the release rule (`lem_release.stop`) to each open task at each look,
and puts a stop on the task only for the kind "old" (3fdd5d1d). A mark newer than the board's own
release, the kind "new", changes nothing on the board: `acts_of` offers approve, merge and park as
on any task.

The run, read in the code at 3247d8fe and with `lem_release.stop` called once:

1. The board server runs Lem 0.3.1. A session of the project loads 0.4.0 and opens
   `refund-rounding`, whose `release.txt` says `0.4.0`.
2. `lem_release.stop("refund-rounding", "0.4.0", "0.3.1", "0.3.0")` gives the kind "new":
   "refund-rounding began on Lem 0.4.0, which is newer than this Lem, 0.3.1, so this Lem does
   nothing with it. /plugin marketplace update lem in Claude Code brings the newer release, and a
   new session of the project loads it".
3. The board shows the task in its lane with its buttons. A press of Merge, Park or the yes on
   the criteria runs a command of 0.3.1 (`lem_run`), which stops with exit 1 and that message;
   the board shows it as the act's answer. Park and the yes link the owner's answer first and
   take it back when the command refuses.
4. The answer of a row (`act_answer`) and of a card (`act_card`) run no such command: 0.3.1
   writes the record, and the session of 0.4.0 reads it.

The sentence "the task still gets the owner's acts" is right for the offer, not for the effect:
no act that runs a command does anything, and each says why.

The case needs a board server older than the session that opened the task. The SessionStart hook
replaces a server whose code is older (`serve.outdated`), so the window is from an update of Lem
to the next hook or `lem serve --ensure`. Whether `/reload-plugins` runs the hook was not tried.

A reader could take the case for the "old" one and put the task in the blocked lane. The task is
not blocked: its own sessions run it. The board is behind, and the way on is the board's restart.

- (a) Nothing now. Each refused act names the update. Cost: a press that does nothing, once for
  each act, in the window only.
- (b) A task of kind "new" gets no acts (`acts_of`) and one line on its card: "This board runs Lem
  0.3.1, and this task began on 0.4.0: `lem serve --ensure` in a session of the project brings the
  board to it". It stays in its lane and is not in "Waits for you". Cost: one field of the model
  beside `release_stop`, the line in the task's page, and a unit case.
- (c) The board server restarts itself when it sees a mark newer than its release. Cost: a server
  that replaces its own code in the middle of a look, which only `--ensure` does today.

Recommendation: (a), until a task of kind "new" is seen on a real board. The run needs a board
that missed an update, and each act already refuses with the fix.

Seen by a builder of 2026-11-24 beside 3fdd5d1d; the run above is of this item.
