# Update and remove

## Update

An update brings the newest release of Lem. Update the app and the plugin together:

```bash
brew upgrade pySilver/tap/lem
claude plugin marketplace update lem
claude plugin update lem@lem --scope project
```

Then start a new session, which loads the new plugin and replaces the board server. The first
board page that you open then shows one note with the new release and the release that it
replaced. Update the plugin in each repository: one board server serves them all. `lem doctor`
shows each one you missed.

From the release after 0.4.2, the board server also replaces itself a few seconds after an
update removes or changes its files. This occurs when:

- `brew upgrade` removes or replaces the keg of the server's release.
- `brew upgrade python@3.14` removes the Python that the server runs on.
- An upgrade of a uv tool writes a new release into the server's folder.

The server starts `lem serve ensure` of the installed Lem. If it finds no installed Lem, it
writes the cause in `serve.log` and continues to serve what it can.

- **The app and the plugin must have the same release.** When they differ, a command of Lem stops with
  one line that names the part that is behind. `lem doctor`, `lem help`, `lem version` and
  `lem uninstall` still answer.
- **Auto-update** of the plugin is off by default. To turn it on, type `/plugin`, open
  **Marketplaces**, select `lem`, and turn on auto-update. Then update the app too.
- **A live session keeps its old plugin loaded.** If the app has a different release, Lem refuses
  task commands in that session. Start a new session with the matching plugin.
- **Your release**: `lem version` gives it. `claude plugin list` shows the plugin's, on the
  `Version` line of `lem@lem`.
- **A release older than a teammate's**: git does not share `.lem/state/`, so your tasks stay
  yours. When the teammate's release adds a key to `.lem/settings.toml`, your Lem stops at each
  command and names the key. Update, and Lem goes on.

## A task of an older release

These steps apply to tasks that use the current record format. Lem reads such tasks from its
own release and the release just before it. A task begun two releases back or more stops at its
first command. The board shows it as blocked.

The message names the release and tells you how to continue. Type `/lem drop <task>`. Then type
`/lem resume <task>`. Lem starts a new request from the branch, its commits and the task notes.
The new session asks for your yes to the criteria.

## Remove

`lem uninstall` removes what Lem put on this computer. First close each Claude Code session of a
repository that uses Lem: a session that runs Lem after the uninstall starts the board server
again. Then run it in a terminal:

```bash
lem uninstall
```

1. Lem reads the repositories of the board, their tasks, the Claude Code settings and the cronn
   jobs. It shows what it will remove.
2. Type `yes` or `all`.
    - `yes` keeps `.lem/state/` and `.lem/worktrees/` of each repository.
    - `all` also removes them. Lem removes each worktree with `git worktree remove`.
3. Lem does the steps in this order, and it shows each step:
    1. It stops the board server and closes the tailnet door.
    2. It removes the plugin `lem@lem` and the marketplace `lem` from each Claude Code scope.
    3. It removes `Bash(lem *)` and the `Read` rule of `lem doctor` from the Claude Code settings.
    4. It removes the home folder of Lem, `~/.config/lem/`, and `$TMPDIR/lem-ask/`.
4. Do the steps that Lem gives at the end:
    - Commit each `.claude/settings.json` that Lem names.
    - Delete the cronn jobs that Lem names from the `crontab.yml` of cronn.
    - Run `brew uninstall pySilver/tap/lem`.

An open task stops `lem uninstall`. Merge or drop each open task first. With `--force`, Lem
continues and keeps the worktree, the branch and the `.lem/state/` of each open task.

`lem uninstall --yes` asks no question and keeps `.lem/state/` and `.lem/worktrees/`. Without a
terminal, `lem uninstall` stops if you do not add `--yes`.

The task branches stay. The other files of `.lem/` also stay: the settings, the profile and the
cast are the team's files in git.

When a step fails, Lem does the other steps and gives the fix. Lem then keeps its home folder. Do
the fix, and run `lem uninstall` again.
