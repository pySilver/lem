# Connect GitHub Issues

Lem writes to the issue of a task at three times. When the build starts, the issue gets an
assignee. When the task lands, the issue gets one comment, and Lem closes it. When the task stops
with no merge, the issue gets one comment and stays open. All people who can see the repository
can see these changes.

## What Lem writes

1. The build of the task starts. An issue with no assignee gets the person who signed in to `gh`.
   An issue with an assignee keeps it, and Lem adds nobody. When that assignee is another person,
   Lem tells you who it is.
2. The pull request has the line `Issue: #42`, so GitHub links the issue and the pull request.
3. The pull request merges. The issue gets one comment: what changed, the address of the pull
   request, and green or not green. Then Lem closes the issue as completed. An issue that is
   closed already stays closed.

`gh` writes as the person who signed in, so GitHub shows that person as the author. The last line
of each comment from Lem names the task: `lem: <task> landed`. Lem writes only to the issue of the
task. Lem does not open an issue, and does not copy a backlog item to an issue.

## Prepare `gh`

Lem reads and writes issues through `gh`, the command of GitHub.

1. Install `gh` from [cli.github.com](https://cli.github.com).
2. Sign in:

   ```bash
   gh auth login
   ```

3. Turn on the issues of the repository on GitHub, under Settings, General, Features.

`gh auth status` shows the account that Lem writes as.

## Fill the settings

`/lem init` adds this table when the issues of your repository are on and hold at least one issue,
and no Linear ticket key shows in its branch names or commit subjects. To add it yourself:

```toml
[tracker]
kind = "github"
```

The table has no other setting. Lem uses the issues of the repository that `origin` names, at each
step. Lem refuses an issue of another repository, for example the upstream of a fork.

## Start a task from an issue

Type `/lem new` and the number or the address of the issue: `/lem new 42`, or
`/lem new https://github.com/OWNER/REPO/issues/42`. The text of the issue is the request. When the
text is empty, the title is the request. The comments under the issue are not part of the request.
`/lem read 42` only shows the issue, and writes nothing to it.

When the issue is closed, Lem asks you whether you want the work again. One issue goes to one task
at a time. A task that landed keeps its issue: for new work on a reopened issue, type the request
in your own words.

## When a task stops with no merge

A task stops with no merge when you drop it, or when someone closes its pull request on GitHub. A
task that investigates a question or a bug also stops with no merge when it gives its answer.

1. The issue gets one comment. For a drop, the comment says why in one line. For an answer, it
   holds the answer. Its last line is `lem: <task> dropped` or `lem: <task> answered`.
2. Lem removes the assignee that it added at the start. Other assignees stay.
3. The issue stays open, and Lem tells you so. You decide whether it closes.

Lem does each write one time. When a session stops after a comment, the next session finds the
last line of that comment, and posts no second comment. When Lem did not do a write yet,
`/lem status <task>` shows the line that does it, for example `lem issue drop <task>`.

## Check the connection

`/lem init` checks the connection before it adds the table. To check it again, ask in plain words:
"check the GitHub tracker". The check names the repository and says that its issues are on. Or it
names each missing part with its fix: `gh` is not installed, `gh` is not signed in, the issues are
off, or `origin` is not on GitHub. The check writes nothing, to the issues or to the settings.
