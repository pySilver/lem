---
decided: 2026-11-17
area: A request: its type, its track and its commands
---

# An ask waits for another task only when it needs that task's result

On 2026-11-16 the owner gave the design to the session that builds Lem: "You are the owner and
long-term maintainer of this codebase, and its design is up to you. Pick recommended action if
you still see it as best oucome." Two reviews of Lem, by Codex and by Fable, had left the points
below open, and that session decided each under his sentence. None of them is his ruling: each
is the session's, and open to him.

The final round of 2026-11-17 took the decisions below, after two real runs of the plugin form in a
scratch repository (R1 to R6) and the final audit of `636b24c` (A1 to A15).

**An ask waits for another task only when it needs that task's result** (2026-11-17). The rule
of `aeaa577` stays, as the maintaining session's and not the owner's: two asks that only name
the same file or function each start at once, each in a worktree of its own, and the landing
line settles an overlap. In the second real run a bug waited behind a one-day task for that
reason, and a developer who types a bug wants it started.
