# Notes of the step `owner` for other steps

What the step `owner` gives, what the board's steps (group 4) may count on, and what it needs in
files it does not own.

## For the board's steps (group 4): what you may count on

- **The rows of "Waits for you".** `lem.model.owner.waiting.rows(looks, away=..., now=...) ->
  tuple[Row, ...]`, pure, in the board's order (kind, then moment), and `waiting.stacks(rows)`,
  the rows grouped by task in the place of each task's first row. The count of the board (the
  sidebar, the title, the phone's icon) is `len(waiting.stacks(rows))`. A `Row`
  (`model/owner/looks.py`) has `kind` (`breaker`, `session`, `stopped`, `criteria`, `held`,
  `card`, `after_dropped`, `blocked`, `plan`, `review`, `merge`), `key` (main's keys:
  `breaker:SLUG:N`, `session:SLUG`, `deaf:SLUG`, `stopped:SLUG`, `held:SLUG`, `plan:SLUG`,
  `card:SLUG:QUESTION-ID`, `after_dropped:SLUG`, `blocked:SLUG`, `review:SLUG`, `merge:SLUG`),
  `task`, `since`, and the facts of its kind (`deaf`, `unread`, `restarted`, `after`, `say` for the
  release stop, `card` and `prompt`, `why` and `tip` of a review, `conflict`).
- **The look a row needs.** `Look(record, session, stop, worktree, conflict)`. The board server
  gathers it as `lem waiting` does: `lem.app.owner.looking.looked(here, now) -> Looked` (`looks`,
  `presence`, `unknown`: why the sessions are not known, `forge`). `here` is
  `lem.app.sessions.here.bound(folder)`. The terminal is asked only when a task has a session on
  record. A known missing session has `live=False`. An unreadable list gives no session facts.
  The look applies release stops to open tasks without a write.
- **The verb of a row**, in the board's words: `lem.model.owner.verbs.verb(row, task, landing)`.
  Where he acts, the icon and how the time reads stay `board-views`'s (`board_model.wait_say` on
  `main`). An unresolved merge intent says "Check the pull request on GitHub."
- **His presence.** `lem.store.owner.read(home)` (`Presence`: `away`, `since`, `words`, `seen`,
  `changes`); whether a task runs without him now is `lem.model.owner.presence.alone(task,
  presence)`, and the spans it ran without him `lem.model.owner.spans.spans(task, presence)`.
- **The merge's wait.** `lem.model.owner.merging.merge_wait(record)`: `owner`, `reads`, `merges`,
  `relands`, or None for a task that is not open (`board_model.merge_wait` on `main`), from the
  record alone. An unresolved merge intent waits for the owner to check GitHub. The kanban's
  "You" column and the merge page may read it.
- **His answer to a question.** `lem.model.owner.answers.answer(task, question_id, digest,
  answer) -> Task` refuses `answered` (answered already, asked again, or a text that changed) and
  `question` (no such question). A row whose question he answered on the board is no row until
  the task's session sets the question's `took_effect` (`answers.answered_hold`): the act that
  takes his answer (the session's command) sets it, and the board's act must not. A live session
  whose turn runs also holds back the breaker or the owner's hold until the turn ends.
- **`lem waiting`** prints the same rows (`rows`, `tasks` with each thing's `verb`, `count`) and
  the groups, so that the terminal, the phone and the Inbox list the same.

## For `board-duties`: the form of `forge.json`

`lem waiting` reads the server's last look at the forge as `lem.app.owner.forge.Look`:
`{"looked": MOMENT, "seen": {"SLUG": {"head": SHA, "mergeable": "CONFLICTING" | ...}}}`
in `.lem/state/forge.json`. The forge duty writes it in that form (with `store`'s whole write),
or moves the struct to `records/` and tells this step's owner; a conflict counts only at the head
Lem proposed last (`forge.conflicts`).

## For `ask`: the cards

A card is a `Question` of topic `card` on the task's record, open while it has no `answer`; it is
a row only while the task's newest session lives (main kept the card's session on the card and
showed only the live session's: `Question` has no session field, so a card of an earlier session
shows while the newest one lives). Asked: a `session` field on the card's question, or a card
closed when its session ends; then `held.card_rows` compares it.

## For `land-propose` (`app/landing/pr_head.py`): each span without him

`pr_head.alone` names only the time since the task's `mode` became `alone`, so a day task that ran
without the owner from his away to his back gets no line. `lem.model.owner.spans.spans(task,
presence)` gives each span with the words that began and ended it (`project.runs_without_owner`
on `main`); `pr_head` reads the presence with `store.owner.read(paths.home(environ))` in `app/`.
The ledger row `check:tests/lem-state.sh:a-task-of-one-repository-ran-without-the-own-...` is
fated `changed` by this step until then.

## For `core` (`records/owner.py`)

`Change` keeps no repository he typed his word in (`repo` on `main`, which no script acted on).
`store.owner.change` writes an away with new words over an away; `lem owner away` does not call it
then, since a word that changes nothing writes nothing (`main`).

## One choice of this step, open to the owner

- `lem owner watch` reads only the machine's mark, so it is no longer refused outside a
  repository; it refuses a missing `--seen` (`seen`) and turns a stop into the refusal `stopped`.
