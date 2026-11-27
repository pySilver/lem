# Claude Code: the tracker

A part of `../claude-code.md`, read at the first read of a ticket.

## The tracker

The tracker is the skill the settings' `tracker.kind` names, `lem-KIND`: `lem-linear` for
`linear`, `lem-github` for `github`.

The GitHub tracker needs GitHub's `gh`, installed and signed in, and no MCP server: its steps are
the lines of `lem issue`, which the permission rule `Bash(lem *)` already covers.

The Linear tracker's server is an MCP server, and Claude Code shows its tools as `mcp__SERVER__NAME`, with
the name the server was added under as SERVER (`linear` in the part "Linear" of `docs/tickets.md`; a second
workspace is a second server with a name of its own, and the skill says which one a ticket
takes). A session that was running when the server was added
does not have them, and a new one does (seen on 2026-11-14 with the Linear server). In a new
session they may be listed by name only and load on their first use, through the tool search
(seen on 2026-11-15). A builder
gets the tools of a server the owner added for all his projects; one added for a single folder
may be absent in a task's worktree, which is another folder (not tested).
