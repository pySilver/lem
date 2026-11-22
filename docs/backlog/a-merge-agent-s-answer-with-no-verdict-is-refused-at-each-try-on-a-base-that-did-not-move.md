---
worth: later
where: skills/lem/scripts/land.py:cmd_merge_review
added: 2026-11-22
---
# A merge agent's answer with no verdict is refused at each try on a base that did not move

`lem land merge-review SLUG --file ANSWER --tip TIP --base BASE` counts the answers it could not
record for one tip and one base (`merge_unread` in `landing.json`). On a moved base the second such
answer is recorded as `another round`. On a base that did not move (BASE is the checks' own base),
every answer whose first line gives no `Verdict: merge.` or `Verdict: call.` exits 1 with "the
merge agent is asked again", the third and the tenth as the first, and the count only grows.
`skills/lem/stages/land.md`, step 7, says "A first line with no verdict is refused: start the agent
once more", and nothing in the step or in `skills/lem/harness/claude-code/ask-merger.md` says what
follows a second refused answer on a base that did not move. `ask-merger.md` bounds only an agent
that gives no answer at all (two ends, then the owner reads the task).

So a merge agent whose seat keeps answering in a form the step refuses (a model that puts a
heading above the verdict line, for one) is started again by each session that follows the text,
with no end. The same rule as for no answer would fit: after a second refused answer on a base
that did not move, the owner is told in one line that the task waits for his read.

Seen by the lead of moved-base-merge-agent-call (2026-11-22) beside its change, which bounded the
moved-base case alone; the base commit has the unbounded case.
