---
decided: 2026-11-17
area: The review, the pull request and the merge
---

# A small change never gets a polish pass

On 2026-11-16 the owner gave the design to the session that builds Lem: "You are the owner and
long-term maintainer of this codebase, and its design is up to you. Pick recommended action if
you still see it as best oucome." Two reviews of Lem, by Codex and by Fable, had left the points
below open, and that session decided each under his sentence. None of them is his ruling: each
is the session's, and open to him.

The final round of 2026-11-17 took the decisions below, after two real runs of the plugin form in a
scratch repository (R1 to R6) and the final audit of `636b24c` (A1 to A15).

**A small change never gets a polish pass** (R1, the first run). Its builder reported one
defect outside the change, and Lem started a polish builder (73 s) only to file one backlog
item. The small change's own builder files such an item, in a commit of its own, and never
fixes it; the pull request lists it. Its report is its reply, five lines, and Lem writes
`report.md` from it: Claude Code refused the write of that file to all three builders of the
first small changes, as the retro of that repository counted (2026-11-17).
