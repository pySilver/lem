---
worth: later
where: skills/lem/prompts/session.md
added: 2026-11-23
---
# A task's session says its question before mark-waiting, and the owner never sees it

"While the owner is needed" in `skills/lem/prompts/session.md` tells a task's session to say the
question in one line, then mark the session as waiting (`mark-waiting`), then wait. In Claude Code
the text a turn writes before a tool call did not reach the owner's view: only the last line after
the call did. In the interview of the task `seat-defaults-and-fallback` on
2026-11-23 the owner wrote: "You keep saying that some question is opened above but I never saw
one!!!". The question has to be the last text of the turn, after the mark.

The same order, say then mark, is also in the lines that `seat-defaults-and-fallback` added for a
seat that failed: `stages/plan.md` step 4.3 (`blocked`), `harness/claude-code/ask-merger.md` (a
block of the merge agent's seat) and the landing's line for `the seat that failed: merger` in
`prompts/session.md`.

Seen outside the change by the interview of `seat-defaults-and-fallback` (its `outside.md`), and
filed by its polish pass; the base commit has it.
