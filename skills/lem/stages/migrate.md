# migrate

`/lem migrate` moves a repository's linked settings to their place under `.lem/`. Linking the
folders an older tool already reads (`init --existing link`) is the first step of an adoption: it
lets a project try Lem with nothing moved. It is not the end state. A project that stays with Lem
keeps its settings in one place, and this stage is how it gets there.

The move is a change like any other: it runs on a task's branch and lands through the gate.

1. **What is linked.** `project.py migrate plan` prints each setting that still points at an
   older tool's folder, and each file of the rules folder with whether it scopes itself to paths.
   With nothing linked, say so and end the stage.
2. **The owner splits the rules.** The rules folder holds two kinds of file, and only one kind
   moves: a file that says how code is written here is style guide and moves; a file about the
   agent's own conduct or about the workflow is not, and it stays where it is. Put the list to
   the owner through `ask-owner`, each file with your guess and the reason for it (a file that
   scopes itself to paths is about the code under them). Which file is which is the owner's
   call. The cast, the profile and the review folder move whole, and the owner is told that.
3. **Open the task** as `stages/new.md` does, with this ask in `task.md`: move the linked
   settings under `.lem`, with the one command the lead runs,
   `project.py migrate run --styleguide FILE ...` and the files the owner named (or `--styleguide`
   with no file when none moves), and "done when": every file the command lists under `mentions`
   names the new path or is left with a reason, and the project's checks pass. Then start its
   lead. The lead's plan is that command, the corrections and the checks.
4. **What the command leaves in place**, so the owner is not surprised by it in the diff:
   - a link for each moved rule in the rules folder, which stays a real folder. An agent that
     loads that folder by itself goes on loading the rule through its link;
   - a link from the review tool's fixed folder to `.lem/review`, because the review tool reads
     that one path;
   - the folder for worktrees, which holds live checkouts and is not moved.
   The harness file says what was checked about each link in your agent.
5. **After the landing**, `project.py migrate plan` shows nothing linked but the worktrees. Say
   in the report which rule files stayed and why.
