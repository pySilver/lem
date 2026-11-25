# Notes of the step `land-text`

What the landing's texts need in files `land-text` does not own, and what the texts say until
then. Each item names the file, what to change, and why.

## For `task` (`skills/lem/stages/new.md`, "The fast track"): the review hint (amendment A3)

The session that shapes a fast-track task may write one line, a review hint, beside its criterion:
what in the change could need more than one read, and which lens, only when it sees a reason (the
owner's words of 2026-11-25: "even better both decisions can be done by Agent itself"). Its place
is a section of its own after the criterion in the task's `criteria.md`:

```markdown
## Review hint

The change reads the session cookie in two places; the security lens should read both.
```

It cannot be a line under the criterion: `model/criteria/lines.py` refuses a list line of another
form (`criteria-form`), and a line of words there would change the criterion's text and its
digest. The section after `## Acceptance criteria` is outside both (`model/criteria/section.py`
ends the section at the next `## `). `prompts/review.md` step 3 reads it as an input and
`prompts/small.md` step 1 leaves it as it is; `stages/new.md` should say when the shape writes it.

## For `task`: the hold of a red base, and the hold after two repair builders

`landing.md` E, "Red base" and "Repair limit", and `notes/land-checks.md` item 16: no command of
the tree sets `blocked: the base is red, after: SLUG` on a task in `landing`, or `blocked` after a
second builder on one failure (`lem task move SLUG ready` from `landing` is refused without
`--start-over`). Until one does, `stages/land.md` step 4 has the session tell the owner in one
line, wait for the repair task with `lem session wait REPAIR --until landed,dropped,answered`, and
go on with what `lem land next SLUG` names once the repair landed; the task stays in `landing`
meanwhile, so the board shows no hold and the load line does not start its repair first
(`checks_wanted.BASE_RED` reads the hold). A command such as `lem task hold SLUG blocked --why
"the base is red" --after REPAIR`, and its lift when REPAIR lands, closes it; the stage then names
it.

## For `task`: a start over keeps the review files of the landing before

`main` moved `reviews/` of the landing before into `reviews/landing-N/` at a start over, and
`app/landing/review_files.py` refuses a record kept there (`landing-before`). The start over of
`model/task/ending.py` moves the reviews into `Landing.archived` and starts the attempts at 1,
but moves no file, so the new review's `reviews/review-1.json` is written over the old one's.
The record keeps the old review whole; the file the board links does not. `stages/land.md` step 1
no longer promises the folder.

## For `land-propose` (`app/landing/propose_made.py`): what `propose` prints

`main`'s `propose` printed `merge_review` (`carried` or null) with `merge_review_why`,
`owner_merge` (`stands: ...` or `ended: WHY`) and `synced` (the line of what bringing the task
onto a moved base did). `Made` has none of them. The stage now reads the merge read's carry from
`lem land next SLUG` (it names the merge, not `merge-review`), and says "Your merge ended" from the
board's line; a session that wants to tell the owner WHY his merge ended reads it nowhere in a
command's output. Asked: `Made.merge_review`, `merge_review_why` and `owner_merge`, copied from the
proposal (`notes/land-merge.md` item 13 asks `propose` to write them).

## For `land-merge` (`app/landing/merge_facts.py`): four facts of `main`'s brief

The merge agent's brief has no `time`, no `tokens`, no `bar` and no plan (`main`'s `criteria`:
the plan, or `criteria.md`). `prompts/merge.md` now names the bar file by its rule (the project's
`.claude/agents/lem-builder.md`, else Lem's), reads the criteria with their tests from the pull
request's text, and reads `time` and `tokens` only when the brief gives them. A test in
`tests/unit/texts/test_landing_texts.py` holds the prompt to every key `Facts` and `Moved` have, so
a key added there fails until the prompt names it.

## For `land-merge` (`records/landing/merge.py`, `Cleaned.rebased`)

`main`'s `clean` printed `rebased` as the sentence `merge_lines.after_push(same=True)` makes ("X
was rebased after its push: its tip ... holds the same change as ..., the head Lem pushed, which
the forge merged"), which the session gave the owner as it was. `Cleaned.rebased` is a bool; the
stage has the session say its own sentence. The sentence on the record (or in clean's `say`)
brings `main`'s words back.

## For `land-merge` (`app/landing/following.py`): the merge agent's merge is the server's

After a read whose verdict is `merge`, `lem land next` gives `act: run` with `lem land merge SLUG
--by merger --message SUBJECT`. That merge is the board server's duty (`board-duties`), never the
session's; `stages/land.md` step 7 says so. A `next` of `wait`, with a why that names the server's
merge, would say it without the stage.

## Amendment A2, as built

The body of a squash lists the task's decisions from its record before the moved line and `Lem
task: SLUG` (`model/landing/merge_decided.py`, `merge_lines.squash_body`'s third part,
`merge_call.merging`; `tests/unit/landing/test_merge_decided.py`). With `branch.history = "keep"`
the branch's own commits land with no body of Lem's, so the decisions reach the base's history
only through the pull request's text. `main`'s squash body also copied the lines under `## Fixed
on the way` (`notes/land-merge.md` item 6), which is still open.

## For `close`: one rule in two places

`notes/land-review.md` item 16e: `model/landing/careful.py` and `propose_careful.py` both judge an
edit of Lem's settings. No text of `land-text` holds either; left for `close`.
