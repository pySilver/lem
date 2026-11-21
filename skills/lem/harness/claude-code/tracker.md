# Claude Code: the tracker

A part of `../claude-code.md`, read at the first read of a ticket.

## The tracker

The tracker is the skill the settings' `tracker.kind` names, `lem-linear` for `linear`. The
tracker's server is an MCP server, and Claude Code shows its tools as `mcp__SERVER__NAME`, with
the name the server was added under as SERVER (`linear` in `docs/linear.md`; a second
workspace is a second server with a name of its own, and the skill says which one a ticket
takes). A session that was running when the server was added
does not have them, and a new one does (seen on 2026-11-14 with the Linear server). In a new
session they may be listed by name only and load on their first use, through the tool search
(seen on 2026-11-15). A builder
gets the tools of a server the owner added for all his projects; one added for a single folder
may be absent in a task's worktree, which is another folder (not tested).
