---
decided: 2026-11-17
area: The plan, the build and the tests
---

# The checks remove what their own commands leave

On 2026-11-16 the owner gave the design to the session that builds Lem: "You are the owner and
long-term maintainer of this codebase, and its design is up to you. Pick recommended action if
you still see it as best oucome." Two reviews of Lem, by Codex and by Fable, had left the points
below open, and that session decided each under his sentence. None of them is his ruling: each
is the session's, and open to him.

The final round of 2026-11-17 took the decisions below, after two real runs of the plugin form in a
scratch repository (R1 to R6) and the final audit of `636b24c` (A1 to A15).

**The checks remove what their own commands leave** (R3, the first run). `python3 -m unittest`
left two `__pycache__` folders in a repository with no `.gitignore`, the gate refused the tree,
and the first small change ended in a second task for the ignore rule. The guard serves
"nothing lands that the checks did not pass on", which is about the committed tree. So the
checks note the untracked files before they run, remove the ones their commands created, name
them, and refuse only a changed tracked file; onboarding proposes the ignore lines for what
the commands leave, in its own commit. In the second run the same gate passed.
