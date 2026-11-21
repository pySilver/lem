---
worth: later
where: skills/lem/scripts/lem_board_model.py:now_head
added: 2026-11-21
---
# The Overview's headline of a task queued after a dropped task says "Waits for another task"

`export-notes-in-order` is queued after `gift-note-in-export`, which is dropped. The task's Overview says "You act", then the headline "Waits for another task", then "Where you answer: It waited for gift-note-in-export, which was dropped ...". `now_head` reads only `t.waits_after`, not `t.dropped_after`, so the headline describes a wait on Lem's side under an eyebrow that says the owner acts. The fix is one branch in `now_head` for `t.dropped_after` (the row's verb from `wait_say`), and an assertion of `now_head` in `AfterDropped` of `tests/unit/test_board_model.py`.

A should finding of review round 2 of task owner-order-open-defects (2026-11-21), left open because both review rounds were used; the owner chose to merge pull request 15 and file it.
