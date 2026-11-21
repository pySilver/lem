---
worth: yes
where: skills/lem/scripts/lem_board_pages.py:kanban
added: 2026-11-21
---
# The board's Done column has no limit

`kanban` draws one card for each task in the column, and Done holds every task that ever landed,
was dropped or was answered (`lanes_sorted` in `lem_board_model.py`, newest first). Each event in
`events.jsonl` sends a `refresh` to each open page (`serve.py`), and the page comes again whole.

Measured on 2026-11-21 at 74bd242: the real log of this repository, then its 17 ended tasks copied
59 times, through `derive` and `kanban_page` in one process.

| | 17 in Done | 1,003 in Done |
| --- | --- | --- |
| `events.jsonl` | 830 lines, 0.85 MB | 46,766 lines, 47 MB |
| `derive` | 3 ms | 149 ms |
| the Tasks page | 4 ms, 93 KB | 120 ms, 3.3 MB |

A month of tasks on a phone over the tailnet gets 3.3 MB at each event of a landing, and a Done tab
of a thousand cards.

The owner's ruling (2026-11-21, `docs/rulings/the-done-column-shows-the-newest-ended-tasks-and-one-setting-says-how-long-an-ended-tasks-files-stay.md`):
keep the last N ended tasks, or a time limit; the last N works better for a project that is not in
constant development. A time limit alone empties Done on a
quiet project: a repository that landed three tasks a month ago shows none. The last N shows the
same three, and on a busy project it still bounds the page.

The fix: Done shows the newest N ended tasks, with a row at its foot that counts the rest
("212 older") and links a list of them; the count in the column's head stays the whole count.
N is a constant of the board, not a key of the settings (read "Opinionated and small" and "Not
every section of the settings stays" before making it one). 20 is an unmeasured estimate of a
column that fits one screen of the large board.

`picker.py` keeps ended tasks by time (`ENDED_DAYS = 7`), so on a quiet project its list of ended
tasks is empty too. The same rule there keeps the picker and the board alike.

Not in this item: the event log and the task folders grow without end
(`an-ended-task-s-files-stay-on-the-machine-for-ever.md`). The small record that item keeps of
each ended task is what the list of older tasks reads.

Surfaced in the maintainer's session of 2026-11-21, on the owner's question of what 1,000 closed
plans do to the board.
