---
ruled: 2026-11-15
area: A request: its type, its track and its commands
---

# What must not go wrong is named by topic, and an agent says whether a task is careful

His ruling of 2026-11-15. It is reopened only by asking him. A quote is his words.

**What must not go wrong is named by topic, and an agent says whether a task is careful**: "we
analyze the project, then we suggest what are the dangerous zones or topics and let user
provide more ... Later at a plan time we can understand if it touches anything whats dangerous
and needs to be taken carefully. Works better than just code path", and "it would be nice to
get a suggestion from Agent whether its should be safe run or not, human can overlook real
danger" (2026-11-15). On 2026-11-16, after an audit showed a branch that set `careful = []` in
its own `.lem/project.toml`, a landing that read the branch's settings and an agent that merged
it, he asked: "`careful = []` should we have this kind of thing in evolving app? why don't we
infere whether changes are dangerous from context of the task/plan?" The form is the
maintaining session's decision, below ("Whether a change is careful is inferred"), not his.
