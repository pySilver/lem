# Connect Linear

Lem can turn a Linear ticket into a task. It moves the ticket when the work starts. When the task
lands, it adds a comment and moves the ticket again. Lem does this through the `lem-linear` skill,
the `[tracker]` table of the settings ([settings.md](settings.md#tracker)), and the MCP server of
Linear. The facts below come from the documentation of Linear, https://linear.app/docs/mcp.

## The server

| Access | Address |
| --- | --- |
| read and write | `https://mcp.linear.app/mcp` |
| read only | `https://mcp.linear.app/mcp/readonly` |

The server finds, creates and updates issues, projects and comments.

## Claude Code

```bash
claude mcp add --transport http --scope user linear https://mcp.linear.app/mcp
```

Then connect:

1. Start a session.
2. Type `/mcp`, and select `linear`.
3. Sign in to Linear in the browser.

The server uses OAuth, so no secret goes into a settings file. `claude mcp list` shows if the
server is connected.

- The name `linear` is the value of `tracker.server` in the settings.
- `--scope user` makes the server available in all your projects, and also in the worktree of a
  task. The default scope, `local`, belongs to one project folder, and a worktree is another
  folder.
- A team that shares one workspace can use `--scope project`. It writes the address into
  `.mcp.json` in the repository, and each person still signs in.

## Whose name is on a comment

Lem writes through the connection of the person who signed in. Linear shows that person as the
author of each comment and status change that Lem makes. The last line of each comment from Lem
says that it is from Lem (`lem: <task> landed`).

## One server is one workspace

A connection is signed in to one Linear workspace, and a new sign-in does not change it. A person
with two workspaces gives each one its own server name and its own sign-in. Before the first
write, Lem asks the server which workspace it uses. If it is not the workspace of the project, Lem
stops.

## With no browser

A session with nobody at the terminal cannot sign in. Linear also accepts an API key or an OAuth
token in a header: add `--header "Authorization: Bearer <key>"` to the `claude mcp add` command.
A key with only the `Read` permission gives a read-only connection. The key is a secret: keep it
out of the repository.

## When it does not connect

- An internal server error when you connect: remove the saved sign-in (`rm -rf ~/.mcp-auth`), and
  connect again.
- A connection that does not answer: disconnect it, and connect it again in Claude Code. This
  changes nothing in Linear.
