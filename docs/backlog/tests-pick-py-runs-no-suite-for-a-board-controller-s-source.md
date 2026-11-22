---
worth: later
where: tests/pick.py:MAP
added: 2026-11-22
---
# tests/pick.py runs no suite for a board controller's source

`python3 tests/pick.py tools/board-kit/controllers/panel.js` prints "tools/board-kit/controllers/panel.js:
nothing reads it" and "nothing to run". The map puts `tools/*` in its row of what no suite reads, and only
the built `skills/lem/assets/vendor/board-app.js` reaches the board's suites (lem-serve, lem-board-act,
lem-board-keys). So a branch that changes a controller in `tools/board-kit/controllers/` and forgets to
rebuild `board-app.js` gets no suite from `python3 tests/pick.py --base main`, and nothing says that the
committed bundle no longer matches its source. Seen in the task board-cards-keyboard, whose builders
changed `cursor.js` and `panel.js` and rebuilt by hand. A fix maps the controllers to the board's suites,
or checks that the bundle is the build of its sources.
