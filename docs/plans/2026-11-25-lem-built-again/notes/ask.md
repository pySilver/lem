# The question card's seams

## For the join

The overlay adapter can move to
`adapters/terminal_agterm` when its port has typed operations for open, result and close.
Move the trusted script hash and page marker from `board/ask/csp.py` to `app/asking/`.
Keep the HTTP policy in `board/ask/`.

The ask step changed `src/lem/model/owner/answers.py` (`refused`) so the session can close or
dismiss its card after the task is parked or ends. It changed `src/lem/app/owner/sessions.py`
(`session_of`, `agent_is_live`) so the board's answer route and the owner's wait list use the
same rule for a live agent. At the join, run `.venv/bin/python -I -B tests --level unit tests/unit/owner/`.

The task's card key starts with `card:` and ends with the page id, as the views expect. It
puts the question, HTML digest and first end in `task.json`. The same write appends the
card's journal line. The HTML and the metadata live in `cards/PAGE/`. The answer's full
wire value is an immutable file there, keyed by the answer's exact timestamp. Publish it
before the task cites it. An uncited attempt is an unused artifact.

## For the owner model and board views

The card metadata holds the exact agterm session id. The POST route checks the latest
session that the task opened, the terminal's list and the overlay result before it takes an
answer. `model/owner/held.py:card_rows` can still show an earlier session's card when a later
session of the task is live. Give the card's `Question` its session id and
`model/owner/looks.Session` the live session id. Fill the latter from
`app/owner/sessions.py:session_of` and compare them in `card_rows`. The current card id and
the board's page path stay the same. The stale row belongs to trial A3. Also render a
`closed` or `dismissed` card as a closed card in `views/panel/card.py`.

## For sessions

The Stop hook can use the pending overlay's file in `TMPDIR/lem-ask/`. File names with
`.no-status.html` give the opening command's choice. If `PAGEID.wait.html` is present,
its contents (`status` or `no-status`) give the more recent choice. The hook remains in
`hooks/stop.py` and uses the standard library only. The CLI tests prove that the wait word
follows the latest call. The hook itself remains a stub on this base.

The sessions ledger already moved four `AskStopHook` rows to `ask`. Returning them in a
second move forms a cycle. Their fates name A5 until the join removes their original move.
