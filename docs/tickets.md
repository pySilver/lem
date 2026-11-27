# Start from a ticket

A ticket of Linear or an issue of GitHub can be the request of a task. Lem then writes to it when
the build starts, when the task lands, and when the task stops with no merge. A team shares the
settings in git, the tickets and the pull requests. Each developer has their own board, with the
tasks on their own computer.

`gh` and Linear write as the person who signed in. The last line of each comment from Lem names
the task, for example `lem: <task> landed`. Lem opens no ticket, and copies no backlog item to a
ticket.

## Linear

### Connect the server

Lem reads and writes tickets through Linear's MCP server, `https://mcp.linear.app/mcp`.

1. Add the server for your user, so that the worktree of each task gets it too:

    ```bash
    claude mcp add --transport http --scope user linear https://mcp.linear.app/mcp
    ```

2. Start a session, type `/mcp`, and select `linear`.
3. Sign in to Linear in the browser.

`claude mcp list` shows whether the server is connected. For a second Linear workspace, add a
second server with a different name. Lem uses the server that has the team of the ticket.

### Fill the settings

When the branch names or commit subjects of your repository show Linear ticket keys, such as
`ABC-12`, `/lem init` adds this table. To add it yourself:

```toml
[tracker]
kind = "linear"
```

The table has no other setting. The key of a ticket names its team. Lem moves the ticket to the
team's status of the type `started` when the build starts, and `completed` when the task lands. A
ticket that is already there stays as it is. An automation of Linear can also move the ticket, and
Lem does not move it back.

### Start a task from a ticket

Type `/lem new` and the key or the address of the ticket: `/lem new ABC-12`. The ticket is the
request, and Lem uses the branch name from Linear. `/lem read ABC-12` only shows the ticket.

### When Linear does not connect

[Linear's guide to its MCP server](https://linear.app/docs/mcp) has the steps for each problem.

## GitHub Issues

### Connect `gh`

Lem reads and writes issues through `gh`, the command of GitHub.

1. Install `gh` from [cli.github.com](https://cli.github.com).
2. Sign in:

    ```bash
    gh auth login
    ```

3. Turn on the issues of the repository on GitHub, under Settings, General, Features.

`gh auth status` shows the account that Lem writes as.

### Fill the issue settings

`/lem init` adds this table when the issues of your repository are on and hold at least one issue.
It does not add it when a Linear ticket key shows in the branch names or commit subjects. To add it
yourself:

```toml
[tracker]
kind = "github"
```

Lem uses the issues of the repository that `origin` names. It refuses an issue of another repository, for example the upstream of a fork.

### Start a task from an issue

Type `/lem new` and the number or the address of the issue: `/lem new 42`, or
`/lem new https://github.com/OWNER/REPO/issues/42`. The text of the issue is the request. When the
text is empty, the title is the request. The comments under the issue are not part of the request.
`/lem read 42` only shows the issue.

When the issue is closed, Lem asks you whether you want the work again. One issue goes to one task
at a time. A task that landed keeps its issue: for new work on a reopened issue, type the request
in your own words.

Lem writes to the issue at these steps:

1. The build starts. An issue with no assignee gets the person who signed in to `gh`. An issue with
   an assignee keeps it. When that assignee is another person, Lem tells you who it is.
2. The pull request has the line `Issue: #42`, so GitHub links the issue and the pull request.
3. The pull request merges. The issue gets one comment: what changed, the address of the pull
   request, and green or not green. Then Lem closes the issue as completed.
4. The task stops with no merge. You drop it, someone closes its pull request, or the task
   answers a question or a bug. The issue gets one comment, and Lem removes the assignee that
   it added. An open issue stays open and a closed issue stays closed.

### When GitHub Issues does not connect

`/lem init` checks the connection before it adds the table. To check it again, ask in plain words:
"check the GitHub tracker". The check looks for `gh`, a GitHub login and enabled issues, and for an
`origin` on GitHub. It names each problem with its fix, and writes nothing.
