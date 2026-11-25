# Notes of the step `board-inputs`

What the board's typed inputs are, what the five board steps of group 4 may count on, and what
the step needs in files it does not own.

## What is built

- `src/lem/board/inputs/`: one frozen msgspec struct for each section of each page, on one base
  (`parts.Input`: keyword fields, an unknown key refused, defaults left out of the JSON). The
  frame: `layout.py` (`Viewer`, `Head`, `Phonebar`, `Topbar`, `Statusbar`, `Keys`),
  `sidebar.py`, `switcher.py` (and the page `/`, `Workspaces`, and `Failure`), `search.py`. The
  views: `tasks.py` (Tasks and the page of older ended tasks), `waits.py` (with `Reasons`, which
  four places list), `backlog.py`, `activity.py` (and the page of a new task). The panel:
  `task/head.py`, `task/cards.py` and `task/now.py` (the Overview's cards), `task/overview.py`,
  `task/criteria.py`, `task/decisions.py` (the tab Criteria and decisions), `task/checks.py`,
  `task/timeline.py`, `task/artifacts.py`, `task/steps.py` (merge, park, drop, card),
  `task/panel.py`. A whole page: `page.py` (`Frame`, `Page`).
- The pure functions that make an input's part from a record's fact, and no rule of a view:
  `clock.py` (a length, a time since, a clock time with its date on another day, each as a
  `When`, with the moment of the page and the zone as arguments) and `names.py` (a title from a
  slug, a task's address, a pull request's link and chip).
- `tests/fixtures/board/`: the showcase afternoon of `main`'s `tests/board-showcase.py` at the
  fixed minute `2026-11-25T16:00Z`, as the records of the rebuild (`ended.py`, `held.py`,
  `working.py`, `receipt.py`), what no record holds (`beside.py`: Lem's acts on the sessions,
  the tasks' files, the backlog's items, the Inbox's record; `lay(folder)` writes the whole
  afternoon into a workspace through the store), and the inputs today's board draws of it.

The brief asked for "the pure functions that make it from the records"; the plan gives that rule
to `board-views` ("records and model outputs -> inputs"). This step builds only the functions
above, which turn one fact into one part; every rule (which column, what waits, the words of a
state) stays with `board-views`.

## The expected inputs, and how they were had

`main`'s own code drew today's pages of the afternoon (its showcase run with `LEM_SERVE=off` and a
throwaway home, then `board_pages` and `board_task` with `TZ=UTC`), and each value of the
fixtures is the value those pages print, where a record of the rebuild holds its fact. The ids of
every markdown block are today's (`md-KEY-` and the SHA-256 of `KEY|TEXT`); the fixtures' texts
gave today's ids for all ten.

| Fixture | Section | Of |
| --- | --- | --- |
| `frame.FRAME` | the frame of the page Tasks | `Frame` |
| `columns.TASKS` | the four columns | `Tasks` |
| `waiting.WAITS`, `waiting.KEYS` | Waits for you | `Waits` |
| `shelves.BACKLOG`, `shelves.KEYS` | Backlog | `Backlog` |
| `panel.OPEN`, `CRITERIA_TAB`, `CHECKS_TAB`, `MERGE_STEP` | the panel of `refund-line-on-receipt` | `Panel` |

No fixture holds Activity, the Timeline, Artifacts, the page of older tasks (Done holds all three
ended tasks), the page of a new task, `/`, or the panel of another task: their structs are
built, and their first cases are the views' own.

## What each step of group 4 may count on

- **`board-views`.** Its case: `lay(tmp_path)` and the facts beside the records (`shown.VIEWER`,
  the zone `UTC`, `moments.NOW`, `shown.VERSION`, the live sessions of `beside.ACTS` taken as a
  demo takes them, from the acts alone, the Inbox of `beside.INBOX`, no look at the forge, demo
  data) give each fixture above, equal. The rules the fixtures hold, besides today's words:
  a card of a task the owner's answer or a breaker holds counts from the hold's `since`, every
  other from the task's (`test_a_card_counts_from_its_hold...`); a held task's state reads
  "Waits for you", and the search's chip names the status of the record (`Waits for you ·
  building`); the status bar counts the journals' entries (`118 entries`), in the place of
  today's events; the tab Artifacts counts 7 documents by today's map (`main`'s
  `artifacts.arrange` over the laid folder; today's 9 had `ask.txt`, `state.md` and the plan in
  the worktree, which the afternoon has not).
- **`board-pages`.** Each template prints one input, with no rule: `Plain` escaped; `Inline`
  through markdown-it's inline rule, escaped; a `Document` as today's markdown block under its
  `id`, with its media address; a `When` as its `shown`, with `data-since` or `data-ago` from
  its `ticks` and `at`; an `Icon` is a symbol of `board-icons.json` (`triangle-exclamation`, not
  `alert`); a `Link` with `frame` gets the panel's frame attributes unless `Viewer.native`, and
  with `out` a tab of its own; a `Choice` with `confirm` is a button of `formaction` with GET; a
  `Stack` of one thing is drawn as that thing's row alone; `Reasons` gives the ids
  `{id}-reasons` and `{id}-r{n}`; the `…` of a label is in the label. A page renders from the
  fixtures with no view: import `fixtures.board.frame`, `columns`, `waiting`, `shelves`,
  `panel`.
- **`board-acts`.** Every form's action and fields: `key` is a `Question.id` of the record, and
  `digest`, `tab`, `in`, `option`, `confirm`, `tip`, `item`, `words` as `main`'s acts read them.
- **`board-duties`.** The status bar's `forge` and `forge_title` are the words of the server's
  look; a duty that failed is one of `Statusbar.problems`.
- **`board-service`.** `Viewer` is what a request says (the listener, the client, the door, the
  cookie); `Head.stream` and `Head.version` are the stream's; `Workspaces`, `Box` and `Failure`
  are the pages outside a workspace.

`kanban.py` is the walking skeleton's form, which `views/kanban.py` and `pages/kanban.py` still
use; the step that moves them to `tasks.py` removes it (`test_shapes.py` skips it by name).

## For `core`

1. **The inputs' base among ruff's runtime bases.** msgspec reads the annotations of every
   `parts.Input`, as it does a record's; ruff's TC rules see only the root's three bases, so
   `src/lem/board/inputs/ruff.toml` repeats the root's list with `lem.board.inputs.parts.Input`
   beside it. Asked: that name in `[tool.ruff.lint.flake8-type-checking]` of `pyproject.toml`;
   then the nested file goes.
2. **`ItemHead.worth`.** Today's backlog has `worth: yes` (the polish pass's item of the
   afternoon, the group Worth doing) and items with no worth (the group No verdict in the item);
   `records/items.py` takes `later` and `no` only. Asked: `yes` and an unset worth.
3. **A command's moment.** Checks and review prints when each command ended (`08:05`, `08:06`);
   `Outcome` and `CommandEnd` have no moment, so the fixture prints the run's end for both.
   Asked: `at` on each.
4. **A run that runs.** `coupon-has-a-slug` is in its checks: `make test` passed, `make lint`
   runs. The journal has `CheckWait` and `CheckEnd` and nothing between, so no record holds a
   command that ended in a run that has not; today's board shows it. Asked, with `land-checks`:
   a journal entry for each command as it ends, or the run's live file the board may read.

## Values of today's board that no record of the rebuild holds

| Value | Where it is now | Its owner |
| --- | --- | --- |
| Lem's acts on a task's sessions (open, close, the agterm id) | `session-acts.jsonl` (`app/sessions/acts.py`, asked as journal entries in `notes/sessions.md`) | `sessions` |
| Which agterm sessions live | `Terminal.sessions()`; a demo takes the acts alone | `board-duties`, `board-views` |
| A `lem-ask` card that waits | the fixture holds it as a `Question` of topic `card`; the card's own files are `ask`'s | `ask` |
| The Inbox's record (thread, why) | `inbox.json`, today's form | `addons-outside` |
| The look at the forge (`forge.json`, when, what stops it) | the server's file | `board-duties` |
| Demo data | the file `demo` in the state folder | `board-service` |
| Who added a backlog item, the items filed on a branch | git (`log`, `diff --diff-filter=A`) | `board-views`, through the `Git` port |
| The last commit's head and subject (Last commit, the merge step's commit) | git, on the task's branch | `board-views`, through the `Git` port |
| The tasks' prose (`task.md`'s outcome, a breaker's document, the merge review, the report) | files of the task's folder, read as they are (part 3) | the stages that write them |
| Lem's first line of a task (`t.opening`) | `Shape` has none (`notes/sessions.md` asks for `say`) | `task`, `core` |
| The plan's `## How it works` with its chart | `Criteria.how`, which the fixture fills with the whole section | `criteria` |
