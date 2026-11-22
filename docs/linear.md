# Connect Linear

Lem moves a ticket when its work starts and when it lands. Lem adds a comment when the task ends.
For the issues of GitHub, read [Connect GitHub Issues](github-issues.md).

## Connect the server

Lem reads and writes tickets through Linear's MCP server, `https://mcp.linear.app/mcp`.

1. Add the server for your user, so that the worktree of each task gets it too:

   ```bash
   claude mcp add --transport http --scope user linear https://mcp.linear.app/mcp
   ```

2. Start a session, type `/mcp`, and select `linear`.
3. Sign in to Linear in the browser.

`claude mcp list` shows whether the server is connected. For a second workspace, add a second
server with a different name. Lem uses the server that has the team of the ticket.

## Fill the settings

When the branch names or commit subjects of your repository show Linear ticket keys, such as
`ABC-12`, `/lem init` adds this table. To add it yourself:

```toml
[tracker]
kind = "linear"
```

The table has no other setting. The key of a ticket names its team. Lem moves the ticket to the
team's status of the type `started` or `completed`. A ticket that is already there stays as it is.
An automation of Linear can also move the ticket, and Lem does not move it back.

## Start a task from a ticket

Type `/lem new` and the key or the address of the ticket: `/lem new ABC-12`. The ticket is the
request, and Lem uses the branch name from Linear. `/lem read ABC-12` only shows the ticket.

Lem writes through the connection of the person who signed in. The last line of each comment from
Lem names the task: `lem: <task> landed`.

## When it does not connect

[Linear's guide to its MCP server](https://linear.app/docs/mcp) has the steps for each problem.
