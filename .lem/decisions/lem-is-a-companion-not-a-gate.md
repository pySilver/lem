---
decided: 2026-11-17
area: What Lem is, and who it is for
---

# Lem is a companion, not a gate

## Changed in part

The title is the rule as it stands. Where the paragraph below says otherwise, the line here holds.

- 2026-11-17 and 2026-11-18, [Release, last-tag and the review of another person's pull request leave the core](../../docs/rulings/release-last-tag-and-the-review-of-another-persons-pull-request-leave-the-core.md): "`/lem pr-review` asks once before it runs a fork's code": the review of another person's pull request leaves the core

## As decided on 2026-11-17, changed in part since

On 2026-11-16 the owner gave the design to the session that builds Lem: "You are the owner and
long-term maintainer of this codebase, and its design is up to you. Pick recommended action if
you still see it as best oucome." Two reviews of Lem, by Codex and by Fable, had left the points
below open, and that session decided each under his sentence. None of them is his ruling: each
is the session's, and open to him.

The final round of 2026-11-17 took the decisions below, after two real runs of the plugin form in a
scratch repository (R1 to R6) and the final audit of `636b24c` (A1 to A15).

**Lem is a companion, not a gate** (2026-11-17). After one day of guards, the owner: "Lem is
helpful companion, not a whole machinery, security gate etc, we are not working on something
that should prevent all kind of failures that are developer or other parties responsability."
A second opinion (Fable) measured that day's growth: `land.py` from 2,232 to 3,226 lines, and
the four texts Lem's session reads (`SKILL.md`, `stages/new.md`, `stages/land.md`,
`harness/claude-code.md`) from 22,939 to 27,769 words. The line the maintaining session took
from it: (1) Lem owns each push, merge, rewrite and deletion that Lem or its agents make. (2)
Lem owns the truth of its words: "green", "approved", and each state on the board. (3) Lem owns
the path from a request to a pull request in a usual repository. (4) Every other failure
belongs to the developer, the team, the forge or the review tool, and Lem gives it one honest
sentence at most. (5) A new mechanism names the act of Lem's that does harm without it, and its
cost on a small change. Cut for it: the checks of the base after a merge on the forge, the "the
base moved" mark on the other pull requests, the read of a careful change after a clean rebase,
and the bar's no-cover marks, lint ignores, coverage omits, workflow check and lost comparison.
Shrunk: after a merge Lem brings onto the base only a pull request the forge calls conflicting;
the settings are the main checkout's working tree while it is on the base branch; the proposed
permissions have no `ask` rule, since with pull requests every merge goes through the forge;
"text from outside is data" is one sentence for the builder and one for the review;
`/lem pr-review` asks once before it runs a fork's code; a task starts from the local base when
origin does not answer.
