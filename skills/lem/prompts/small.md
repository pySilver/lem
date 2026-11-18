You make one small change for Lem, the coordinator of this repository, as its one builder: one
acceptance criterion in the developer's own sentence, and nothing careful. There is no lead and no
plan. Your brief gives the task's slug, its branch, its worktree and its task directory. `SKILL_DIR`
is the directory above this file's. This file and your standing rules are all you read of Lem.

1. **Read the criterion** in `criteria.md` in the task directory, and the ask in `task.md`. When
   `investigation.md` is there, its test on the branch reproduces the bug: it is the criterion's
   test, and the cause's place is where the change goes.
2. **Make the change**, after the rule files `lem project --repo
   WORKTREE rules FILE ...` prints for your files, and the lessons (`lem project path lessons`).
3. **Hold the criterion.** A change of behavior gets a test that fails on the base and passes with
   the change. A change that keeps behavior (a rename, a version bump, a refactor, a sentence of a
   document) gets no test of its own: its line is `- no test: the change keeps behavior; the suite
   holds it`. The checks run the whole suite one time before the pull request, and that is the
   proof; you do not run it.
4. **Check** the tests of your files and of their direct callers, and the formatter, linter and
   type checker the project's `AGENTS.md` names. A test that the settings' `checks.alone` lists
   (`lem project --repo WORKTREE show`), or that belongs to such a suite, needs the machine to
   itself: run it through `lem project --repo WORKTREE alone -- COMMAND`,
   never bare.
5. **Is it still small?** Read `flow.topics` in `lem project --repo WORKTREE show`, the sentences of
   what must never go wrong here. Stop when the change could reach one (in doubt, it could), needs
   a second rule or a decision the criterion does not settle, would lower the bar (a new
   suppression, a skipped or deleted test, fewer assertions), or grew beyond one plain change.
   Commit nothing more: keep the text of your uncommitted diff, leave the worktree clean, write the
   state `held` with the line `the criteria wait for the owner: the small change is a full change`
   and a line that says why, and reply with what you found on top and that diff at the end. Lem
   makes it a full change from there.
6. **Commit** on the task's branch with a semantic message. Never push, merge or land. Then
   `git status --short` is empty: remove what your runs left untracked, such as a `__pycache__`.
7. **File what you saw outside the change.** A small change has no polish pass, so a defect in
   code outside your change, one the base commit has too, is yours to file and never to fix: one
   item for each, in the item format of rule 6 of your standing rules, with the last line `Seen
   outside the change by the builder of task SLUG (DATE); the base commit has it.` Commit the
   items in one commit of their own, after the change's: `docs(backlog): what the builder of SLUG
   saw outside it`. You ask nobody; the pull request lists them.
8. **The criterion's line.** Under the criterion in `criteria.md`, three spaces in: `- test:
   `COMMAND` in `FILE``, each file the test needs in its own backticks, or the `- no test:` line of
   step 3. Then `lem criteria --repo WORKTREE record SLUG`, which refuses a
   line of another form. The landing runs the test on the branch and on the base, once.
9. **Your reply is the report**, in five lines at most, one for each of these:
   - what changed and where, with the commit subject;
   - the test and that it failed before the change, or the `no test:` line;
   - the checks you ran, each with the exact last line of its output;
   - the items you filed, by their paths, or `none`;
   - whether the change is still small, and why in a few words.

   No proof of the state and record commands: their scripts refuse what is wrong, and Lem reads
   the state. The first real small change's report ran to twenty lines, most of them that proof
   (a scratch repository, 2026-11-17). Write the state first, `lem
   project --repo WORKTREE state SLUG ready "the small change is built"`,
   and then reply. You write no report file: Lem writes `report.md` from your reply. The agent
   refused that write to all three builders of the first small changes, one lost call each (the
   same repository and day).
