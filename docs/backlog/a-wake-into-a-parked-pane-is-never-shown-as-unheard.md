---
worth: later
where: src/lem/board_model.py:session_need
added: 2026-11-22
---
# A wake into a parked pane is never shown as unheard

session_need gives `deaf` from `unanswered` of lem session list, which is true only while the line `lem: SLUG WHY` still waits in agterm's mailbox of the session (`agtermctl msg read`). A parked Claude Code process runs its own Stop hook, which takes the line out of the mailbox with no turn of the agent: the session of merge-leaves-board-lock (#37) was parked (`63868.json`, `status: idle` since 10:45:48, `parkedJobId: 6fe214ec`), and a wake sent to it left the queue-operation `enqueue` at 15:53:31Z in its transcript and no turn. So the row "Its session does not answer" never shows for such a pane. The guard of a stopped session now catches a task in building, ready or landing after 45 and 10 minutes; a task in another status that needs its session gets nothing.

Seen by the investigator of task dead-tasks-woken-or-shown (its outside.md, 2026-11-22); the base commit has it.
