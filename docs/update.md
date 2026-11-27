# Update and remove

## Update

An update brings the newest release of Lem. Update the app and the plugin together:

```bash
brew upgrade pySilver/tap/lem
claude plugin marketplace update lem
claude plugin update lem@lem --scope project
```

Then start a new session, which also replaces the board server. The first board page that you
open then shows one note with the new release and the release that it replaced. Update the plugin
in each repository: one board server serves them all. `lem doctor` shows each one you missed.

- **The app and the plugin must have the same release.** When they differ, a command of Lem stops with
  one line that names the part that is behind. `lem doctor`, `lem help` and `lem version` still
  answer.
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
