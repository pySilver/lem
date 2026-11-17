You make one small change for Lem, the coordinator of this repository, as its one builder: one
story in the developer's own sentence, and nothing careful. There is no lead and no plan. Your
brief gives the task's slug, its branch, its worktree and its task directory. `SKILL_DIR` is the
directory above this file's. This file and your standing rules are all you read of Lem.

1. **Read the story** in `stories.md` in the task directory, and the ask in `task.md`. When
   `investigation.md` is there, its test on the branch reproduces the bug: it is the story's test,
   and the cause's place is where the change goes.
2. **Make the change**, after the style guide files `python3 SKILL_DIR/scripts/project.py --repo
   WORKTREE rules FILE ...` prints for your files, and the lessons (`project.py path lessons`).
3. **Hold the story.** A change of behavior gets a test that fails on the base and passes with
   the change. A change that keeps behavior (a rename, a version bump, a refactor, a sentence of a
   document) gets no test of its own: its line is `- no test: the change keeps behavior; the suite
   holds it`, and you run every command of `gate.commands` (`project.py --repo WORKTREE show`)
   yourself, since the suite is the proof.
4. **Check** the tests of your files, and the formatter, linter and type checker the project's
   `AGENTS.md` names.
5. **Is it still small?** Read `flow.topics` in `project.py --repo WORKTREE show`, the sentences of
   what must never go wrong here. Stop when the change could reach one (in doubt, it could), needs
   a second rule or a decision the story does not settle, would lower the bar (a new suppression, a
   skipped or deleted test, fewer assertions), or grew beyond one plain change. Commit nothing more:
   write `report.md` in the task directory with what you found on top and your uncommitted diff at
   its end, leave the worktree clean, write the state `held` with the line `the stories wait for
   the owner: the small change is a feature` and a line that says why, and reply with the report's
   path. Lem takes the feature path from there.
6. **Commit** on the task's branch with a semantic message. Never push, merge or land.
7. **The story's line.** Under the story in `stories.md`, three spaces in: `- test: `COMMAND` in
   `FILE``, each file the test needs in its own backticks, or the `- no test:` line of step 3. Then
   `python3 SKILL_DIR/scripts/stories.py --repo WORKTREE record SLUG`, which refuses a line of
   another form. The landing runs the test on the branch and on the base, once.
8. **Report** in `report.md` in the task directory, in a few lines: what you changed; each command
   you ran with the exact last line of its output; the commit subject; each defect you saw outside
   the change, with its file. Then `python3 SKILL_DIR/scripts/project.py --repo WORKTREE state SLUG
   ready "the small change is built"`, and reply with the report's path only.
