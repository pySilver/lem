---
worth: later
where: src/lem/board_model.py:merge_wait
added: 2026-11-23
---
# A merge agent that gives no answer twice on a base that did not move leaves the board saying it reads

Task gift-note is `open`, and its base has not moved since the checks ran. The task's session starts
the merge agent on the brief `lem land merge-review gift-note` printed. The agent ends with a
non-zero exit and no answer file, and a second start ends the same way.
`skills/lem/harness/claude-code/ask-merger.md` then says only "tell the owner in one line that the
task waits for his read". Nothing runs `lem land merge-review gift-note --file ...`, so no
`merge.review` event and no `merge_review` in `landing.json` is written for the tip.

`merge_wait` in `src/lem/board_model.py` gives "reads" for an open task with no
merge review of its proposed tip, so the board still says that the merge agent reads gift-note.
"Waits for you" shows no row for it, since only "owner" is a row there. The owner has the one line
in the session and nothing on the board or the phone.

An answer with no verdict, twice, on the same kind of base is recorded as a review that calls the
owner (`unread_next` in `src/lem/land.py`), so "Read the merge review" waits for him. An
agent that gives no answer twice has no answer file to record and needs a record of its own. Seen
by the task a-merge-agent-s-answer-with-no-verdict-is-refused-at-each-try-on-a-base-that-did-not-move
(2026-11-23), whose plan kept this case out of its scope.
