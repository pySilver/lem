# new

`/task new <what>` opens one task. `<what>` is the owner's words, an issue link or a backlog item.

1. **The slug and the branch.** A slug of two to five plain words that say what the owner gets
   ("report-dates-stay-whole"), never a code. The branch is `<type>/<slug>` with a semantic type
   (`feat`, `fix`, `chore`, `docs`), unless the project's `AGENTS.md` gives its own scheme.
2. **The worktree.** One worktree per task, from the settings' base branch. Use the project's own
   worktree script when `AGENTS.md` names one, since it sets up what a plain worktree lacks (a test
   database, an environment). Otherwise `git worktree add` in the folder the project's other
   worktrees are in. Every later path in this task is inside that worktree.
3. **The task directory.** `project.py task-dir SLUG`, then write `task.md`:
   - the ask, verbatim;
   - the outcome in one or two sentences, as the person it is for would see it;
   - done when: the evidence that shows the outcome, each line something a command or a look at
     the product can show;
   - out of scope, when the ask has an obvious neighbor this task leaves alone.
4. **Is the ask clear?** If you cannot write the outcome without choosing between two readings
   that give the owner different things, ask once through `ask-owner`, each reading as what the
   owner would get. Anything else you read from the code and the rulings, and log.
5. **Go on to `plan`.** Write the first block of `state.md`.

Several tasks run at once, each in its own worktree with its own builder. Before a second task
starts, name the files each will change: two tasks on the same files run one after the other, or
the later one is briefed with the earlier one's branch.
