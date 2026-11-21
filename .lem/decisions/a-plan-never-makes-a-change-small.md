---
decided: 2026-11-17
area: The plan, the build and the tests
---

# A plan never makes a change small

## Changed in part

The title is the rule as it stands. Where the paragraph below says otherwise, the line here holds.

- 2026-11-18, [A night ends as pull requests, and a task without the owner covers what a night was](a-night-ends-as-pull-requests-and-a-task-without-the-owner-covers-what-a-night-was.md): "a night that meets an item that is one plain change drafts no plan and names it in the night report": the night's own path is gone

## As decided on 2026-11-17, changed in part since

On 2026-11-16 the owner gave the design to the session that builds Lem: "You are the owner and
long-term maintainer of this codebase, and its design is up to you. Pick recommended action if
you still see it as best oucome." Two reviews of Lem, by Codex and by Fable, had left the points
below open, and that session decided each under his sentence. None of them is his ruling: each
is the session's, and open to him.

The final round of 2026-11-17 took the decisions below, after two real runs of the plugin form in a
scratch repository (R1 to R6) and the final audit of `636b24c` (A1 to A15).

**A plan never makes a change small** (A3). A lead could write a small change's size line in a
plan, for a full change from a complete request or at night, and then no approval, no read of
the criteria and no polish pass was asked: the probe's plan went through the gate, the read and
`propose` green, and `land --by agent` landed it. A one-rule ask is a small change, with its
criterion in the task directory, approved by Lem with `--small`. `criteria.py` and `land.py` refuse a
plan file that says `Size: small`, and a night that meets an item that is one plain change drafts no plan and
names it in the night report as ready to start as a small change.
