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
6. **Commit** on the task's branch with a semantic message. Never push, merge or land. Then
   `git status --short` is empty: remove what your runs left untracked, such as a `__pycache__`.
7. **File what you saw outside the change.** A small change has no polish pass, so a defect in
   code outside your change, one the base commit has too, is yours to file and never to fix: one
   item for each in the backlog folder (`paths.backlog` in `project.py --repo WORKTREE show`), in
   the item format of the `lem-backlog` skill: between two `---` lines `worth: later`, `where:
   PATH` or `PATH:SYMBOL` (never a line number) and `added: YYYY-MM-DD`, today; then `# TITLE` on
   one line; then the concrete run, with real values; last the line `Seen outside the change by
   the builder of task SLUG (DATE); the base commit has it.` The file name is the
   title's words joined by `-`; when a file of that name holds another defect, add the stem of
   the `where`. Commit the items in one commit of their own, after the change's: `docs(backlog):
   what the builder of SLUG saw outside it`. You ask nobody; the pull request lists them.
8. **The story's line.** Under the story in `stories.md`, three spaces in: `- test: `COMMAND` in
   `FILE``, each file the test needs in its own backticks, or the `- no test:` line of step 3. Then
   `python3 SKILL_DIR/scripts/stories.py --repo WORKTREE record SLUG`, which refuses a line of
   another form. The landing runs the test on the branch and on the base, once.
9. **Report** in `report.md` in the task directory, in five lines at most, one for each of these:
   - what changed and where, with the commit subject;
   - the test and that it failed before the change, or the `no test:` line;
   - the checks you ran, each with the exact last line of its output;
   - the items you filed, by their paths, or `none`;
   - whether the change is still small, and why in a few words.

   No proof of the state and record commands: their scripts refuse what is wrong, and Lem reads
   the state. The first real small change's report ran to twenty lines, most of them that proof
   (a scratch repository, 2026-11-17). Then `python3 SKILL_DIR/scripts/project.py --repo WORKTREE
   state SLUG ready "the small change is built"`, and reply with the report's path only. When
   the write of `report.md` is refused to you, your reply is the report's five lines instead, and
   Lem writes the file from it.
