# land

Machines gate a landing; people and models review it after.

1. **Bring the base in.** Merge or rebase the settings' base branch into the task's branch, as
   the project's `AGENTS.md` says it lands (a squash, a merge, a rebase). A conflict goes to a
   builder with both sides named.
2. **Run the gate.** Every command of the settings' `gate.commands`, at the root of the task's
   worktree, on the tip that will land. Keep the exact last line of each. A project with no gate
   command cannot land through this skill: say so and stop, because "nothing failed" would then
   mean "nothing ran".
3. **A red gate is work.** A failure the change caused goes to a builder. A failure the base
   already has is shown with the same command on the base, logged, and reported; it does not
   block this task and it is never hidden by editing the gate. Skipping or changing a gate command
   is the owner's decision only.
4. **The base moved during the run.** When the commits that arrived touch none of the files the
   gate reads for this change (documents only, another package), the result stands; say which
   commits they were. Otherwise run again on the new tip. Several green branches may be carried
   on one run as a joint candidate.
5. **Land, or hand over.** With `branch.land = "agent"`, land the branch the way the project's
   `AGENTS.md` describes, with its own landing script when it has one, and push only the branch
   the project names. With `"owner"`, change nothing and report that the branch is ready, with the
   gate's last lines.
6. **Queue the review.** `review_queue.py add` with the task's slug, the landed range and its
   risk: `high` when the task was careful, or touches authentication, money, a migration, a
   security boundary or the gate's own tooling; `normal` otherwise.
7. **Report to the owner**, once, in plain words: what they get, how to see it, the gate's last
   lines, the decisions taken without them (from `decisions.md`), what was not verified, and the
   review item's risk. Then remove the worktree the way the project does, and write the last block
   of `state.md`.
