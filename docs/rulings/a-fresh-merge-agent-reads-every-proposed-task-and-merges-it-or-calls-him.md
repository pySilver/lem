---
ruled: 2026-11-20
area: The review, the pull request and the merge
---

# A fresh merge agent reads every proposed task, and merges it or calls him

His rulings of 2026-11-20 and 2026-11-21, while his interview redesigned how a task runs and the
board became a served app; a quote is his words. His answers Q7 to Q11 and notes P1 to P9 are in
`.lem/state/tasks/one-lem-parallel-landings/`, which git ignores. Where a note replaces an earlier
ruling, this is the ruling now.

The first three tasks of the redesign, in the order he agreed to (Q9, "Yes I agree"):

**A fresh merge agent reads every proposed task, and merges it or calls him**: an "additional
Agent with fresh context" with a "settings configurable model" (P6). On a question page he picked,
against both recommendations, "The merge agent reads each task, the fast track too" and "Each
not-green pull request calls you"; a careful change always calls him ("It calls you"). Its seat:
"this should be set on most generic level, not in code (`~/.config/lem` ?)", so `seats.merger`
comes from the repository, else from `machine.toml`. `branch.land` stays the switch: "developer
can configure `lem` the say he always needs to review before merge. Merge review still applies."
The form is the session's: `prompts/merge.md`, the default `"agent"`, and `merge-review.md` in
place of the owner's page of a task.
