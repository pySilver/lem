---
worth: later
where: skills/lem/stages/plan.md
added: 2026-11-21
---
# A design choice's kept decision has two readings after a repair

Step 5 of `skills/lem/stages/plan.md` says of a design choice that the plan talk left: "one option
is the kept decision with each mechanism that guards it, the other the reversed decision", and
"the pick of level 1 is the kept decision: the plan stands until a level settles otherwise".

After a repair of the talk that changed a decision, "kept" can mean the decision as the plan had it
before the talk, or the plan as the talk left it. In `owner-task-order-stays` (2026-11-21) the two
readings gave different answers. The talk's first repair (commit `037d3d4`) changed where a queued
task goes on, to "where it stopped"; the ladder's file for design choice A
(`.lem/state/tasks/owner-task-order-stays/ladder-A.md`) still named as "Kept" the decision before
the repair, "it resumes at the build, as today". The defender's report named the doubt.

The sentence should say which of the two is the kept decision, so that level 1 of the ladder has
one pick.
