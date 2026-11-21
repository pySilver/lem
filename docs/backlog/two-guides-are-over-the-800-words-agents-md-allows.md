---
worth: yes
where: docs/board.md
added: 2026-11-21
---
# Two guides are over the 800 words AGENTS.md allows

`AGENTS.md`, "Layout", says each guide the README links stays under 800 words. On 2026-11-21, `wc -w`
gives 920 for `docs/board.md` (911 on `main` at `74bd242`, 920 after the task
`owner-order-open-defects` added "task that waits for a task that you dropped" to the row of
"Waits for you") and 835 for `docs/flow.md`. A cut of 121 and 36 words is an edit of a text in STE
that a reader reads, so it is a task of its own and not a polish pass's.

On 2026-11-22 at `f96e87b` the two guides were longer still: 932 and 868 words. Settled: each
guide that `AGENTS.md` bounds is under 800 words again, still in STE and with no fact a reader
needs taken out; a fact that only a maintainer needs moves to `AGENTS.md` or the skill. The rule
stays as it is.
