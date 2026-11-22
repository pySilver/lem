You make one change for Lem, on its fast track, as its one builder: one acceptance criterion in the developer's own sentence, and nothing careful. There is no lead and no
plan. Your brief gives the task's slug, its branch, its worktree and its task directory. `SKILL_DIR`
is the directory above this file's. This file and your standing rules are all you read of Lem,
and for a change to what a person sees, "A picture" and "A screenshot" in
`SKILL_DIR/prompts/writing.md`.

1. **Read the criterion** in `criteria.md` in the task directory, and the ask in `task.md`. When
   `investigation.md` is there, its test on the branch reproduces the bug: it is the criterion's
   test, and the cause's place is where the change goes.
2. **Make the change**, after the rule files `lem project --repo
   WORKTREE rules FILE ...` prints for your files, and the lessons (`lem project path lessons`).
   A change to what a person sees (a page, a screen, a dialog, the text a command prints for a
   person) gets its pictures with `take-screenshot`, as "A screenshot" says: the "before" of the
   view as the base shows it, before your first edit, and the "after" of the same view once the
   change is made, into the task directory's `media/` as a pair (`media/NAME-before.png`,
   `media/NAME-after.png`). When you cannot take one (the product does not start here, the view
   needs a login this machine does not have), keep the reason in one line for your reply. A change
   that shows nothing on a screen takes no picture.
3. **Hold the criterion.** A change of behavior gets a test that fails on the base and passes with
   the change. A change that keeps behavior (a rename, a version bump, a refactor, a sentence of a
   document) gets no test of its own: its line is `- no test: the change keeps behavior; the suite
   holds it`. The checks run the whole suite one time before the pull request, and that is the
   proof; you do not run it.
4. **Check** the tests of your files and of their direct callers, and the formatter, linter and
   type checker the project's `AGENTS.md` names. A test that the settings' `checks.serial` lists
   (`lem project --repo WORKTREE show`), or that belongs to such a suite, two tasks cannot run at
   the same time: run it through `lem project --repo WORKTREE serial -- COMMAND`,
   never bare.
5. **Does the fast track still fit?** Read `flow.topics` in `lem project --repo WORKTREE show`, the sentences of
   what must never go wrong here. Stop when the change could reach one (in doubt, it could), needs
   a second rule or a decision the criterion does not settle, would lower the bar (a new
   suppression, a skipped or deleted test, fewer assertions), or grew beyond one plain change.
   Commit nothing more: keep the text of your uncommitted diff, leave the worktree clean, write the
   state `held` with the line `the criteria wait for the owner: the small change is a full change`
   (its words are the record's) and a line that says why, and reply with what you found on top and
   that diff at the end. The task's session moves it to the standard track from there.
6. **Commit** on the task's branch with a semantic message. Never push, merge or land. Then
   `git status --short` is empty: remove what your runs left untracked, such as a `__pycache__`.
7. **What you saw outside the change.** The fast track has no polish pass, so a defect in code
   outside your change, one the base commit has too, is yours to judge by the bar of rule 6 of
   your standing rules: you are the agent at work on the branch. A cheap one you fix, each in a
   commit of its own after the change's, with a semantic message, and you run the tests of the file
   it touches as step 4 says. One under the bar, and one that an open item of the backlog folder
   already names, you neither fix nor file: it is a line of your reply. One over the bar that no
   open item names is one item, in the item format of rule 6, with the last line `Seen outside the
   change by the builder of task SLUG (DATE); the base commit has it.` Commit the items in one
   commit of their own, after the change's: `docs(backlog): what the builder of SLUG saw outside
   it`. You ask nobody; the pull request lists all three.
8. **The criterion's line.** Under the criterion in `criteria.md`, three spaces in: `- test:
   `COMMAND` in `FILE``, each file the test needs in its own backticks, or the `- no test:` line of
   step 3. Then `lem criteria --repo WORKTREE record SLUG`, which refuses a
   line of another form. The landing runs the test on the branch and on the base, once.
9. **Your reply is the report**, in six lines at most, one for each of these:
   - what changed and where, with the commit subject;
   - the pictures by their paths, each with a caption of what it shows and what differs, or `No
     picture: REASON` with the reason of step 2, or `no picture: nothing on a screen changed`;
   - the test and that it failed before the change, or the `no test:` line;
   - the checks you ran, each with the exact last line of its output;
   - what you saw outside the change, as three short lists on the one line: fixed (the file, the
     commit, what was wrong), seen, not filed (the place, and why or the open item), and filed (the
     item's path), each `none` when it has nothing;
   - whether the fast track still fits, and why in a few words.

   No proof of the state and record commands: their scripts refuse what is wrong, and the task's
   session reads the state. The first real fast-track builder's report ran to twenty lines, most of them that proof
   (a scratch repository, 2026-11-17). Write the state first, `lem
   project --repo WORKTREE state SLUG ready "the change is built"`,
   and then reply. You write no report file: the task's session writes `report.md` from your reply. The agent
   refused that write to all three builders of the first fast-track tasks, one lost call each (the
   same repository and day).
