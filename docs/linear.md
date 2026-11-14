# Connecting Linear

Lem does not read or close tickets yet: that work is `docs/backlog/a-tracker-ticket-cannot-be-the-ask.md`.
This page is the connection it will use, so a project can set it up and try it. Linear is reached
through Linear's own MCP server. The facts below are from Linear's page, https://linear.app/docs/mcp,
read on 2026-11-14.

## The server

| What | Address |
| --- | --- |
| read and write | `https://mcp.linear.app/mcp` |
| read only | `https://mcp.linear.app/mcp/readonly` |

Linear's page lists no single tools; it says the server finds, creates and updates issues,
projects and comments.

## Claude Code

```bash
claude mcp add --transport http --scope user linear https://mcp.linear.app/mcp
```

Then start a session, type `/mcp`, pick `linear` and sign in to Linear in the browser. The server
uses OAuth; nothing secret goes into a settings file. `claude mcp list` shows whether it is
connected.

The name `linear` is the one a project's settings will give to Lem. `--scope user` makes the
server available in all of a person's projects (Claude Code's documentation, read 2026-11-14). The
default scope, `local`, is stored under the entry of one project folder. A task's worktree is
another folder, so a builder there may not have a `local` server; that was not tested, and it is
the reason for `--scope user` here. A team that shares one workspace may use `--scope project` instead, which writes the
address into `.mcp.json` in the repository; each person still signs in.

## Codex

Only needed when Codex is the agent that runs `/lem`. A reviewer does not touch the tracker.

```bash
codex mcp add linear --url https://mcp.linear.app/mcp
```

Linear's page says to enable the `rmcp` client in `~/.codex/config.toml` on first use
(`[features]` `experimental_use_rmcp_client = true`), and `codex mcp login linear` signs in.

## One server is one workspace

A connection is signed in to one Linear workspace, and connecting again does not switch it. A
person with two workspaces gives each its own server name and its own sign-in. Before the first
write, an agent asks the server who it is and stops when the workspace is not the project's.

## Without a browser

A session that nobody attends cannot sign in. Linear accepts an API key or an OAuth token in the
header instead: `--header "Authorization: Bearer <key>"` on the `claude mcp add` line. A key
with only the `Read` permission gives a read-only connection. The key is a secret: keep it out of
the repository.

## When it does not connect

From Linear's page: an internal server error on connecting is cleared by removing the saved
sign-in (`rm -rf ~/.mcp-auth`) and connecting again; a connection that stops answering is
disconnected and connected again in the client, which changes nothing in Linear.
