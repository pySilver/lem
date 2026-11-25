# Notes of the step `board-acts`

What the owner's acts on the board are, what the other steps of group 4 and later may count on,
and what this step needs in files it does not own.

## What is built

`src/lem/board/acts/`: one use case for each act, each over the records and the same `app`
functions a command calls, and `routes.py` with their addresses.

| Address (POST) | Module | It calls |
| --- | --- | --- |
| `/HOST/WS/start`, `/HOST/WS/tasks` | `start.py`, `starting.py`, `slugs.py` | `app.tasks.open.opened`, then `app.sessions.opening.open_session(..., "new")` |
| `/HOST/WS/backlog/drop` | `backlog.py`, `child.py` | `lem proposals drop PATH` as a process of its own (an add-on's command) |
| `/HOST/WS/agterm/SESSION` | `jump.py` | `Terminal.select` of the session Lem opened last for a task of the workspace |
| `.../tasks/SLUG/answer` | `answer.py`, `checking.py`, `recording.py`, `parking.py`, `approving.py` | `model.owner.answers.answer` in one write with the question and an `OwnerAct`; `app.tasks.park.parked`; `app.criteria.approve.approved` with `--shown`; then `app.sessions.waking.wake(..., "owner")` |
| `.../tasks/SLUG/session` | `session.py`, `restarting.py` | `opening.open_session(..., "dead" or "owner")`, or `guard_steps.stepped(..., "restart", None)` over a stop on record |
| `.../tasks/SLUG/merge` | `merge.py`, `approval.py`, `merging.py` | `app.landing.merge.run` with `Asked(by="owner", via="board", tip=...)`, in a thread of its own |

Every act on the main listener first passes `asker.refusal`: the loopback client, one `Origin`
that is the board's own, and no `Sec-Fetch-Site` but `same-origin`. A refusal of an act is its
note, never an error page.

## For `board-views`

- **The key of an answer's form** is `lem.board.acts.asking.standing(task).id`: the record's
  question for the exact hold key, or the hold key when the record has no question for it.
  The hold keys are
  `breaker:SLUG:N:STAMP`, `plan:SLUG:STAMP`, `skip:SLUG:STAMP` or `criterion:SLUG:STAMP` with
  STAMP `clock.compact(hold.since)` (the fixture's ids have this form). Resume and a new
  criteria question append a sequence number to the hold key. The act writes that
  question on the record with the answer when the record held none, so the view and the act
  never disagree on the id. `asking.OPTIONS` gives each topic's options in their order.
- **The criteria's `digest`** is `model.criteria.digest.shown` of `criteria.md`'s bytes: the act
  compares it with the file, and the approval approves those bytes or nothing.
- **Park and Drop** post to `.../answer` with `option` `park` or `drop` and the hidden field
  `confirm=yes` from their confirm steps. The Park step sends his line in `words`. There is no
  `.../park` or `.../approve` address.
- **Amendment A4**: the merge's confirm step says Approve. The button's label is "Approve" (its
  `busy` "Approving…"), not "Merge pull request #44" as `fixtures/board/panel.MERGE_STEP` has it;
  the form is the same (`confirm=yes`, `tip`).
- An answer on the board writes no `took_effect`: the task's session sets it
  (`notes/owner.md`). Park saves the answer and the breaker's hold in one write. Resume keeps
  that answer and stores a fresh question, including when the two acts fall in the same second.

## For `board-pages`

- **The note after an act**: the 303 names `?note=TOKEN`; `lem.board.acts.notes.NOTES.get(token)`
  gives a `Note` (`task`, `act`, `state`: `running`, `done`, `refused`, `stands` or
  `uncertain`, `said`), or None once it is an hour old. The page makes it the `Page.note` input
  (`board/inputs/parts.Note`). For `uncertain`, show the instruction to check GitHub.
- **The jump** is `POST {Head.jump}/{SESSION}` with no body, as the design names it, in the place
  of `main`'s `POST .../agterm/select` with `{"session": ...}`; it answers JSON `{"done": bool,
  "said": str}` as before. The `agterm` controller of `tools/board-kit` posts there.

## For `board-service`

- **The door**: the door listener's app sets `app.state.door = True`, and the door's own check
  (his login, the same origin, `board/door.py`) runs before the routes. The acts then skip the
  main listener's check and keep `via` `door`. The main listener's check reads
  `app.state.facts.port`.
- The row of the pages' `Referrer-Policy` header is moved to you; the act's refusal of the
  `Origin` `null` is this step's.

## For `addons-flow`

`lem proposals drop PATH` is run by the board as `lem --repo CHECKOUT proposals drop PATH`, with
`LEM_SERVE=off`. It prints the envelope with `result.proposals`, the names of the proposals whose
day's record keeps the drop, and removes the file; a refusal's why and fix are the board's note.
The board refuses an empty path, an item of `docs/backlog`, and an item an open task holds.
The board holds the workspace claim lock across the holder check and child call. When
`addons-flow` implements the drop, the command must hold that lock across its own holder check
and file removal. Move the lock to the command in the same change so both entry points use it.

The ledger row for file removal and the saved verdict moves to `addons-flow`. The board test
uses a stand-in for the command. The rebuilt add-on's test must prove both effects, as
`Drop.test_a_drop_removes_the_file_at_once_and_keeps_the_drop_in_the_retros_file` does on `main`.

## For `board-duties`

An approval that stands is `Landing.standing` with `by_act` `board`. Under amendment A4, the checks
run on the rebased task before it can merge on a moved base. A task red on its rebase leaves
the line. A task checked on the current base goes first. The server records how many approved
tasks wait at each merge. The merge duty carries out a standing approval with
`--standing --via server` when the landing permits it. For a fresh approval, the landing
checks the submitted tip again under the merge lock and the forge call uses that tip. Six rows of
`lem-board-act.sh` about the server's merges and its look at the forge are moved to you
(`tests/ledger/moves/board-acts.tsv`).

## For `core` (`pyproject.toml`)

Starlette's `request.form()` needs `python-multipart`, which is not a dependency. The acts read a
page's form, always `application/x-www-form-urlencoded`, with `urllib.parse.parse_qsl`, and need
nothing added. If a later act takes a file, `python-multipart` is the library to add.

## Where the brief and the code differed

- The stub and the design name the new task's address `POST .../tasks`; the board's inputs
  (`fixtures/board/shelves.py`) post to `.../start`, as `main` did. Both addresses take the form.
- The design names the jump `POST /HOST/WS/agterm/SESSION`; `main` and its script used
  `.../agterm/select`. The design's address is built; `board-pages` moves the script.

## For the owner of `tests/unit/board/test_slice.py` (`slice-board`'s file)

`test_an_address_not_built_answers_501_with_the_step_that_builds_it` holds two rows of this
step, `("POST", "/h/w/tasks/fix-the-login/merge", "board-acts")` and `("POST", "/h/w/tasks",
"board-acts")`. Both addresses are built now, and a form with no `Origin` gets 403 from the
main listener's check, so both cases fail after the join (seen in this worktree:
`T unit tests/unit/board/`, 545 collected, 2 failed, those two). Asked: remove the two rows.
This step did not edit the file, which it does not own.
