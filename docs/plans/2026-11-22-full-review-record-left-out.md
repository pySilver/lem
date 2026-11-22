# A full review's record leaves no profile out, as its brief says

careful: no, because the record check of `land.py` keeps its refusal as it is and only its message gets the words of the fix; the brief of the review moves the reasons for the profiles a full review does not run from the record to `review-N.md`, and the full set still runs whole (checked against each of the thirteen topics of `.lem/project.toml`; the nearest, "The landing lets through a change that should not land", is not reached, since no record that the landing refuses today is taken after the change).

## Acceptance criteria

Size: full, because the review's brief, the help of `lem land` and the refusal of its record check each change.

1. A review of a careful change writes its record as its brief says, and the landing takes it the first time:
   1. A careful task lands, and its review runs comprehensive, the project's full set.
   2. Its `review-1.md` gives the reason for each other profile of the review tool: focused, final, claude-only, codex-only, grill-me, expert and triage.
   3. Its record `review-1.json` says `"kind": "full"` and `"left_out": []`.
   4. `lem land read --record` takes the record.
   - no test: the change is the sentences of the review's brief, `skills/lem/prompts/review.md`, and of the help of `lem land`; the landing already takes a full record with an empty `left_out`, which the suite holds.
2. A full review's record that still lists a profile under `left_out` is refused, and the refusal names the fix:
   1. A record says `"kind": "full"` and `"left_out": [{"name": "focused", "why": "the change is careful"}]`.
   2. `lem land read --record` refuses it.
   3. Its message says that the full set leaves no profile out, that `left_out` is `[]` on a full review, and that the reason for each profile it did not run goes in `review-N.md`.

## Tasks

1. **The brief, the help and the refusal say the same thing.** Serves criteria 1 and 2.
   - `skills/lem/prompts/review.md`, step 3: the paragraph "Write one reason for each profile you
     run and each you leave out" gets the rule for `full`: the full set is run whole, so the record's
     `left_out` is `[]`, and the reason for each other profile of the tool goes in `review-N.md`.
     Step 8, the record's fields: `left_out` with a `why` each, and `[]` when `kind` is `full`.
   - `skills/lem/scripts/land.py`, the module docstring's "The record of a review" (the text of
     `lem land --help`): one sentence that `left_out` is `[]` when `kind` is `full`.
   - `skills/lem/scripts/land.py`, the refusal `if kind == "full" and left_out:` in the record
     check: keep its first words, "the project's full set leaves no profile out", and add the fix:
     `left_out` is `[]` on a full review, and the reason for each profile it did not run goes in
     `review-N.md`. The check itself stays as it is.
   - `tests/lem-land-shop.sh`: the check whose pass line is "a request the owner called careful
     gets the project's full set: ..." greps the refusal `dropped` for the new words of the fix too.
     Keep that pass line's words: `docs/rulings/history.md` names it, and
     `tests/unit/test_agents_md.py` finds it by them.

## Decisions

- Decision 1 of the task: the brief changes, and the check keeps its refusal. `land.py` cannot
  tell a profile of the full set from another profile, since the set is a profile of the review
  tool's own configuration, which `land.py` does not read; a check that takes `left_out` on a full
  review would take a record that drops a lens of the full set, and the pull request's text lists
  each `left_out` entry as "left out", which on a full review reads as a partial one.

## What it will not verify

- That the next real review of a careful task writes `left_out: []`: the brief is a prompt, and
  only a real careful task shows it.
