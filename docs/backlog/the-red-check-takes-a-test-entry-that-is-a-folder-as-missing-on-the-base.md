---
worth: later
where: src/lem/app/landing/checks_red_run.py:lacking
added: 2026-11-27
---
# The red check takes a test entry that is a folder as missing on the base

`lem criteria red` takes a criterion's test as one that does not start on the base commit when its
command runs Python on a folder. This repository's `AGENTS.md` gives the test entry under
"Checks" as `.venv/bin/python -I -B tests --level unit [PATHS]`, so a plan's test line in that
form reads `.venv/bin/python -I -B tests --level unit
tests/unit/ask/test_card.py::test_a_board_answer_closes_the_page_when_no_wait_runs`.
`checks_red.Command.script` returns `tests` as the script it starts, and `lacking` tests
`(place / name).is_file()`, which is false for the folder `tests`. Python runs a folder that holds
`__main__.py`, so the test starts on both sides, and the check still reports that it does not
start on the base commit.

The task `board-answered-question-closes` (2026-11-27) met it: its lead wrote its test lines with
`tests/__main__.py` in place of `tests` to pass the check (c3bc4479).
