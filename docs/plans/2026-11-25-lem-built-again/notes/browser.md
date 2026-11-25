# The browser level

The production board routes serve the typed demo records on a kernel-assigned loopback port.
The test entry gives the server its own home. The forge and terminal are the port fakes.
Playwright uses its Chromium headless shell, a temporary profile and the mock keychain.

Run the level from the browser worktree in a session that permits loopback. After it passes, run
the showcase capture to write the eight demo pictures. Inspect the pictures before their commit.

```sh
.venv/bin/python -I -B tests --level browser
UPDATE_LEM_SCREENS=1 .venv/bin/python -I -B tests --level browser tests/browser/test_showcase.py::test_the_demo_afternoon_draws_the_documented_pictures
```

Keep the full result lines and check them against `tests/ledger/fates/browser.tsv`. The ledger
lists the exact test name for every row. The chart, board kit, screenshot smoke test and
showcase each have a case beyond those proofs.

## The criteria comparison on the desktop

The approval template `src/lem/board/templates/task/approve.html` uses `cf-pair` for
changed, added and removed criteria. The stylesheet uses this class for the desktop grid and
the phone breakpoint. The side and label classes keep the two texts distinct and wrap each
one inside its column. The template unit case checks those classes for all three change types.
The browser case checks the stacked phone view and the side-by-side desktop view.
