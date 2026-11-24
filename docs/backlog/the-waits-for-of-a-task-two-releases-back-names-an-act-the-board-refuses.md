---
worth: yes
where: src/lem/board_model.py:answer_of
added: 2026-11-24
---
# The "Waits for" of a task two releases back names an act the board refuses

A task that a release stopped has one row in "Waits for you", whose "where" is the stop's message.
Its page's "Waits for" fact takes `answer_of(t)`, which has no line for `t.release_stop`, while
`acts_of` offers nothing. Run at c674b18d on the `ReleaseStop` case of
`tests/unit/test_board_model.py`: for `open` the fact says "Merge the pull request on GitHub or on
this board."; for `building`, "Tell the task’s session to build it, ..."; for `planned`, "Read the
plan, then build it or drop the task on this board, ...". It should say the stop's message, as the
row does.

Seen on the way by a backlog worker of 2026-11-24, with a probe on the same case.
