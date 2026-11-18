# Connect Linear

Lem, or an automation of Linear, moves a ticket when its work starts and when it lands. Lem adds a
comment when the task ends. Lem supports no other tracker.

## Connect the server

Lem reads and writes tickets through Linear's MCP server, `https://mcp.linear.app/mcp`.

1. Add the server for your user, so that the worktree of each task gets it too:

   ```bash
   claude mcp add --transport http --scope user linear https://mcp.linear.app/mcp
   ```

2. Start a session, type `/mcp`, and select `linear`.
3. Sign in to Linear in the browser.

`claude mcp list` shows whether the server is connected. A team can use `--scope project` instead: it
writes the address into `.mcp.json`, and each person still signs in.

## Fill the settings

When your repository shows Linear, for example ticket keys in branch names, `/lem init` proposes
the `[tracker]` table and checks it. To add it yourself:

```toml
[tracker]
kind = "linear"
server = "linear"          # the name from `claude mcp add`
workspace = "acme"         # as in linear.app/acme
team = "ABC"               # the key of your team
moves = "lem"              # or "tracker", when an automation of Linear moves the tickets
started = "In Progress"    # only with moves = "lem", as your team spells it
landed = "Done"            # only with moves = "lem"
```

[Settings](settings.md#tracker) says what each key means.

## Start a task from a ticket

Type `/lem new` and the ticket's key or its address: `/lem new ABC-12`. The ticket is the request,
and Lem uses the branch name that Linear gives. `/lem linear ABC-12` only reads the ticket.

- Lem writes through the connection of the person who signed in, so Linear shows that person as
  the author. The last line of each comment from Lem names the task: `lem: <task> landed`.
- One connection is one workspace. Lem checks the workspace before it reads or writes, and it
  stops when the workspace is not the one in the settings. For a second workspace, add a second
  server with its own name.

## When it does not connect

[Linear's guide to its MCP server](https://linear.app/docs/mcp) has the steps for each problem.
