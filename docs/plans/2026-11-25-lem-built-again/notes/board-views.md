# Notes of the step `board-views`

What the step `board-views` gives, what the other steps may count on, and what it needs in files
it does not own.

## What is built

`src/lem/board/views/`: the board's views, pure functions from one value, `world.World` (the
records of a workspace and what lies beside each, `world.Seen`), to the inputs of
`board/inputs/`. Only `gather.py`, `folder.py`, `branch.py`, `inbox_read.py` and
`backlog/read.py` read anything; every other module is a pure function of the world.

- `gather.gather(checkout, ask.Ask) -> World`: the records through the store, Lem's acts on each
  task's sessions (`app/sessions/log.py`), the files and the prose of each task's folder, the
  newest commit of each branch and the backlog items it adds (`branch.Branches`, a part of the
  `Git` port), the backlog (`backlog/read.py`), the owner's presence, the Inbox's record, and the
  mark of example tasks. A demo takes each session from the acts alone; any other board takes the
  terminal's list (`Ask.listed`, what `app/owner/sessions.sessions_of` gives), or says that the
  sessions are not known.
- `pages.page(world, want, note) -> Page`: a page whole, the frame and the one view of its
  address (`Viewer.view`), and the panel of the task it opens (`Viewer.task`, `Viewer.tab`).
- The views one by one: `tasks.tasks`, `waits.view.waits`, `backlog.view.backlog`,
  `frame.page.frame`, the panel (`panel/`), the tabs (`criteria/`, `checks/`, `artifacts/`,
  `timeline/`), `activity/`, `older.py`.
- The rules they share: `owed.py` (the rows of `model/owner/waiting.py` from the world),
  `standing.py` (where a task stands: its column, look, who acts, its state's words, since when),
  `telling.py` (a card's line), `words.py` (a stage's line in the board's words), `offers.py`
  (the acts the board offers: `acts_of` on `main`), `answering.py` (the answer to a question),
  `reasons.py` (the reasons a pull request is not green), `where.py` (where the owner answers).

## For `board-pages`

- A route reads the world with `gather.gather(checkout, ask.Ask(...))` and renders
  `pages.page(world, want, note)`. `want` is `backlog.wanted.wanted(parse_qs(query))`. Every
  fixture of `tests/fixtures/board/` is what `pages.page` gives of the afternoon
  (`tests/unit/board/views/afternoon.py`).
- `views/kanban.py` (the walking skeleton's) stays for `pages/kanban.py` until that page renders
  `pages.page(...).tasks`; then both, and `inputs/kanban.py`, go.
- `Added.said` of a backlog item that names its task ends with ", in task"; the template puts a
  space before the task's link.

## For `core`

1. **The `Git` port's facts of the backlog.** The board says who added each item and whether git
   has it. `backlog/ledger.Ledger` names the two facts it needs: `adds(where, folder)` (the
   commits that added files under the folder, the newest first: `git log --diff-filter=A
   --no-renames --date=short --name-only -- FOLDER`, with author, day, subject and body) and
   `unsaved(where, folder)` (each path git has no commit of or a change to, file by file:
   `git status --porcelain --untracked-files=all -- FOLDER`). Asked: both on `GitFacts`, with
   the `git` adapter; until then the board's read takes `Ask.ledger`, which the server leaves None
   (git cannot tell: no item says who added it).
2. **`branch.Branches`** is the part of `GitFacts` a task's board reads (`tip`, `merge_base`,
   `commits`, `changed_paths`, `show`): no change asked.
3. **`types-PyYAML`.** `backlog/head.py` catches `yaml.YAMLError` of a bad front matter;
   `pyyaml` comes with `python-frontmatter` and has no types (one pyrefly warning). Asked: the dev
   dependency `types-PyYAML`.

## For `sessions`

Lem's acts on a task's sessions are still `session-acts.jsonl` (`app/sessions/acts.py`), which
the views read beside the record; once they are journal entries (`notes/sessions.md`), the
gather reads them from the record and `Seen.acts` goes.

## Facts no `World` field holds yet

`state.keep_days`, the `?key=` and `?words=` of a step and a card's page come in through
`panel/opened.Opened`; the branch's history (the merge step says "one commit"), the server's
running merges (`HeadActs.merging`), the act's note on a tab, and Lem's first line of a task
(`Now.opening`) are not shown.

## For `board-duties` and `board-service`

- The forge's last look is `world.Forge` (`looked`, `problem`, `conflicts`): the server fills it
  from `forge.json` (`app/owner/forge.read`, `forge.conflicts`) when it gathers a page.
- The machine's other workspaces are the switcher's (`frame.page.Beside.switcher`); with none,
  the frame shows this workspace alone.
- What did not read is `Beside.problems` (the status bar's and the beacon's).

## Ledger rows given on

`tests/ledger/moves/board-views.tsv` (19 rows, each with why):

- The rulings of the board's group that another step builds: the served app, Tailscale and the
  server's start (`board-service`); the board's look and its icons (`board-pages`); the question
  page (`ask`); what reaches across tasks (`board-duties`); the refusal of a note with no option
  (`board-acts`); and the duty that watches the owner's mark (the stream's refresh,
  `board-pages`).
- Rules a record or a model of another step lacks, which the board then shows:
  - `owner`: `model/owner/looks.Session` has no `unheard` case (`Listed` has it), so a session
    that does not answer says one text for every case; `model/owner/turns.GOES_ON` has no
    `request`, so a request's one answer stays his row while he is away.
  - `land-merge`: `model/landing/merge_standing.standing_of` says his merge stands after a review
    calls him with no verdict, and after GitHub refused the server's carrying it out, so the
    board offers no Merge.
  - `land-checks`: no record holds a command that ended in a run that still runs, nor the total
    of a stopped run's commands (`notes/board-inputs.md`, "A run that runs"); two cases of the
    polish pass's live line and the count of a stopped run wait for it.
  - `board-duties`: the forge list of a blocked merge seat; the transcripts a pruned task keeps.
  - `ask`: a card of an earlier session (`Question` has no session field: `notes/owner.md`).
  - `addons-outside`: the task's own session finding its row while its turn runs
    (`app/owner/scope.py`).
