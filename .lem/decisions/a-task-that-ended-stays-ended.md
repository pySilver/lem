---
decided: 2026-11-17
area: A task's session, and whether he is there
---

# A task that ended stays ended

## Changed in part

The title is the rule as it stands. Where the paragraph below says otherwise, the line here holds.

- 2026-11-20, [Each task lives in a session of its own, from its shape to its merge, and there is no Lem session.](../../docs/rulings/each-task-lives-in-a-session-of-its-own-from-its-shape-to-its-merge-and-there-is-no-lem-session.md): "`stages/stopped.md`": `prompts/session.md` takes its place (the note at line 924)

## As decided on 2026-11-17, changed in part since

On 2026-11-16 the owner gave the design to the session that builds Lem: "You are the owner and
long-term maintainer of this codebase, and its design is up to you. Pick recommended action if
you still see it as best oucome." Two reviews of Lem, by Codex and by Fable, had left the points
below open, and that session decided each under his sentence. None of them is his ruling: each
is the session's, and open to him.

The final round of 2026-11-17 took the decisions below, after two real runs of the plugin form in a
scratch repository (R1 to R6) and the final audit of `636b24c` (A1 to A15).

**A task that ended stays ended** (A2). A stale wake-up wrote `building` over a landed task, and
in the audit's probe `landing.json` lost `merged`, `pr` and `gated`. So `project.py state`
refuses a move out of `landed`, `answered` or `dropped`, `may-start` refuses a task that is
`landing`, `open` or ended, and `stages/stopped.md` starts a lead only for a task that is `building`
or has no new state block. New work on an ended task is a new ask.
