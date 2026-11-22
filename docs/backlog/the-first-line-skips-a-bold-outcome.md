---
worth: later
where: skills/lem/scripts/project.py:outcome_of
added: 2026-11-22
---
# The first line skips a bold outcome

`outcome_of` quotes the first sentence of prose under `## Outcome` in a task's `task.md`, and skips
each paragraph whose line opens with `**` (its pattern `(\d+\.|[-*+>|!]|\*\*)`). The skip is there for
a bold label such as `**Today:**`, which `tests/unit/test_task.py` holds. But `prompts/writing.md`
asks for **bold** on the one phrase of a paragraph that carries the outcome, so an outcome written
that way opens with `**` and is never quoted. The task `done-column-shows-newest` (2026-11-21) opened
its outcome with "**The board's Done column shows the 20 tasks that ended last, and one row under them
leads to a page of the rest.**", and its first line quoted the next sentence, about the picker, in
its place. A label of a few words is already skipped by the rule of more than three words, so a fix
may strip the `**` marks from a line in place of skipping it; it needs a case in
`tests/unit/test_task.py` for a bold outcome beside the one for `**Today:**`.
