# Update and remove

## Update

An update brings the newest release of Lem, never a change that no release holds. Update the app
and the plugin together:

```bash
brew upgrade pySilver/tap/lem
claude plugin marketplace update lem
claude plugin update lem@lem --scope project
```

Then start a new session, which also replaces the board server. Update the plugin in each
repository: one board server serves them all. `lem doctor` shows each one you missed.

- **The app and the plugin must have the same release.** When they differ, a command of Lem stops with
  one line that names the part that is behind. `lem doctor`, `lem help` and `lem version` still
  answer.
- **Auto-update** of the plugin is off when you install Lem. To turn it on, type `/plugin`, open
  **Marketplaces**, select `lem`, and turn on auto-update. Then update the app too.
- **A session that runs keeps its Lem until it ends.** The next session loads the new release.
- **Your release**: `lem version` gives it. `claude plugin list` shows the plugin's, on the
  `Version` line of `lem@lem`.
- **A release older than a teammate's**: git does not share `.lem/state/`, so your tasks stay
  yours. When the teammate's release adds a key to `.lem/settings.toml`, your Lem stops at each
  command and names the key. Update, and Lem goes on.
- **A task begun two releases back** stops, and its message gives the way on
  ([below](#a-task-of-an-older-release)).
- **A bad release** is not taken back: a newer release repairs it.

## A task of an older release

Lem reads the tasks begun on its own release and on the release just before it. A task begun two
releases back or more stops at its first command, and the board shows it blocked, with no act on
it. Its message names the release it began on, and the way on: `/lem drop <task>`, then
`/lem resume <task>`. The resume starts a new request on your release, from the branch, its
commits and the notes of the task. Its session asks you again for your yes to the criteria.

## Remove

1. Merge or drop each open task.
2. Remove the cronn jobs of this repository.
3. If no other repository uses Lem, type `/lem serve tailscale off` and `/lem serve stop`.
4. Run `claude plugin uninstall lem@lem --scope project`.
5. Run `claude plugin marketplace remove lem --scope project`.
6. Remove Lem's allow rules from `.claude/settings.local.json`.
7. Run `git rm -r .lem`, and commit.
8. Delete the folder `.lem/`.
9. If no other repository uses Lem, run `brew uninstall lem`, and delete `~/.config/lem/` and
   `$TMPDIR/lem-ask/`.
