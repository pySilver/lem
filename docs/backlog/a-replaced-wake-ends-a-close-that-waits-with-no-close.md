---
worth: later
where: skills/lem/scripts/session.py:cmd_close
added: 2026-11-22
---
# A replaced wake ends a close that waits, with no close

cmd_close with --when-unselected counts the session.wake records of the session it waits on (wakes_of), and gives up with `closed: false, woken: true` when one more comes, since a wake means new work. The `replaced` wake that `lem session open SLUG --why stopped` logs for the old pane (tell_replaced) means the opposite: the pane is to close. tell_replaced sends `lem: SLUG replaced` first and logs the wake after it, so an old pane that starts `lem session close SLUG --session OLD --why handoff --when-unselected` between the two keeps its pane open. No run showed it: the line reaches the agent only when its turn ends, which is after the log in every case seen, so this is reasoning from the code (the builders of tasks 2 and 4 of dead-tasks-woken-or-shown). The fix is one condition: wakes_of leaves out why=replaced, with a unit case of the close that waits.

Seen by the builders of task dead-tasks-woken-or-shown (2026-11-22); the change of that task made the replaced wake.
