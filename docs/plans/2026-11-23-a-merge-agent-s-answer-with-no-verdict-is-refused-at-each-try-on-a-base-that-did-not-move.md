# A merge agent's answer with no verdict is refused at each try on a base that did not move

careful: yes. "The landing lets through a change that should not land: one a person should merge" is in reach: the task changes what `lem land merge-review` records from the merge agent's answer, and that record decides whether the board's server merges with no person.

## Acceptance criteria

Size: full, because the rule is one, but it sits in the step that decides whether a pull request merges without a person, so it is careful and never the fast track.

1. On a base that did not move, a second answer of the merge agent with no verdict ends the tries and calls the owner, as an agent that gives no answer twice does:
   1. Task gift-note is `open`. The base has not moved since its checks ran.
   2. The merge agent answers with `## Review` as its first line and `Verdict: merge.` under it.
   3. `lem land merge-review gift-note --file ANSWER --tip TIP --base BASE` refuses it, and says that the merge agent is asked again.
   4. A fresh merge agent answers in the same form, with the same tip and base.
   5. The same command now writes the answer down as the merge review, which calls the owner and says why in plain words: the merge agent twice put another line above its verdict, and its answer says `Verdict: merge.` lower down.
   6. "Waits for you" shows "Read the merge review" for gift-note, and the board's server does not merge it.
2. On a base that moved, a second answer that cannot be recorded is still recorded as another round of the checks, and the owner is not asked.
   - no test: the change keeps behavior; the suite holds it
3. The landing's step of the merge agent, and the agent's own part of the harness, say what follows a second refused answer on a base that did not move.
   - no test: the change is two sentences of a stage file and of a harness file.

## How it works

```mermaid
flowchart TD
  A["The merge agent answers"] --> B{"The answer can be recorded?"}
  B -->|"yes"| C["The merge review is written: it merges or calls the owner"]
  B -->|"no"| D{"The first such answer for this tip and base?"}
  D -->|"yes"| E["Refused: a fresh merge agent is asked again"]
  D -->|"no"| F{"The base moved since the checks?"}
  F -->|"yes"| G["Recorded as another round: the checks run again"]
  F -->|"no"| H["Recorded as a review that calls the owner"]
```

## Tasks

1. **The second refused answer on a base that did not move calls the owner** (criteria 1, 2 and 3).
   In `skills/lem/scripts/land.py`, `cmd_merge_review`: on a base that did not move, the second answer
   for one tip and base that gives no verdict is written down as `merge-review.md` and as the kept
   `merge_review`, with `verdict` null, `calls` true and a `why` in plain words: the merge agent
   twice put another line above its verdict, and, when a line lower down in its answer gives
   `Verdict: merge.` or `Verdict: call.`, which verdict that line gives. That lower line never
   becomes the verdict: the owner decides. Its `next` is the one of a review that calls the owner. The first such answer is refused as today, and
   the moved base keeps its rule. A test in `tests/unit/test_land.py` for the rule where it can be a
   call of a function, and a check in `tests/lem-land-shop.sh` beside the check of the first refused
   answer (near line 127) for the journey: two answers with no verdict on a base that did not move,
   the second exits 0 with `calls` true, `lem project waiting` lists the task's merge review, and
   `lem land merge SLUG --by merger --via server` is refused. In `skills/lem/stages/land.md`, step 7
   (the paragraph that starts "A first line with no verdict is refused"), and in
   `skills/lem/harness/claude-code/ask-merger.md` (its last paragraph), one sentence each on what
   follows the second refused answer on a base that did not move, and names the "Read the merge
   review" row the owner then sees in "Waits for you".

## Decisions

- **The record is a merge review that calls the owner, with no verdict.** No new state, row or
  event: the board's `merge_wait` gives "owner" for a review of the proposed tip whose verdict is not
  `merge`, "Waits for you" shows its "Read the merge review" row while `calls` is true, the feed says
  "it calls you" for a `merge.review` with `calls` true, and `lem land merge --by merger` is refused
  with no merge review whose verdict is `merge`. Rests on `merge_wait` and `merge_review_said` in
  `skills/lem/scripts/lem_board_model.py` and on step 8 of `skills/lem/stages/land.md`.
- **The answer is still written down word for word as `merge-review.md`**, so the owner reads what
  the merge agent wrote, as for any answer that is recorded.
- **Out of scope: a merge agent that gives no answer twice on a base that did not move.** It leaves no
  record, so the board still says that the merge agent reads the task. That is a neighbor of this
  defect with another cause (no answer file, so nothing for `merge-review` to read); the builder
  files it as a backlog item when it confirms it in the code.

## What it will not verify

- No real merge agent is started: the answers are files the tests write, since the rule reads the
  text of the answer and nothing of the agent.
