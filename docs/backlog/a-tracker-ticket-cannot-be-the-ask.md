---
worth: yes
where: skills/lem/stages/new.md
added: 2026-11-14
---
# a tracker ticket cannot be the ask

The owner types `/lem new https://linear.app/acme/issue/ENG-123/report-dates-are-cut`. `stages/new.md`
names "an issue link" as one form of the ask and says nothing more, so Lem has only the words of
the URL: it does not read the ticket's title and description, the ticket stays in "Todo" while the
work runs, and nothing closes it when the change lands. The owner then moves ENG-123 by hand, or
forgets, and the tracker says work is open that landed days ago.

## What the owner ruled (2026-11-14)

- **Linear only.** Lem supports Linear and no other tracker now. It is organized so that another
  one can be added later, and nothing for another one is built.
- **The local backlog is a different thing, and it stays.** A backlog item appears during other
  work, when an agent finds something that is out of scope and worth keeping. It may never become
  a ticket. It is kept in the repository because that is cheap, and because the next agent that
  meets the same thing learns that it was already caught, and maybe already decided. So the
  backlog is never mirrored to Linear, a backlog item never needs a ticket, and Lem creates no
  ticket from one unless the owner asks.

A ticket is therefore one more place an ask can come from, beside the owner's own words and a
backlog item. It is not a second form of the backlog.

## What is built, and what is left (2026-11-15)

Built: the role "the tracker" in the harness contract, the `[tracker]` table in
`.lem/project.toml` (`kind`, `server`, `team`, `moves`, and with `moves = "lem"` the two status
names `started` and `landed`), the `lem-linear` skill with its four procedures (check, read,
start, land), one ticket for one task (`project.py task-dir --ticket`), and the steps of
`stages/new.md`, `stages/land.md`, `stages/night.md` and `stages/init.md` that use them.

Left, and the reason this item stays:

- **The trial.** No task from a real ticket ran. The owner named `MBZ-1` for it. The skill's
  "check" and "read" ran against his workspace on 2026-11-15, in a session that had read tools
  only, and the skill's text was corrected from what the server really returns. The write half
  (a status change and a comment on that ticket) runs on his word. Do not write into any other
  ticket of that team.
- **The machine check has no row for the tracker's server.** Whether a server is connected is a
  fact of one agent and one project, so the check is the skill's own "check" and not
  `doctor.py`. Decide after the trial whether that is enough.
- **A builder in a task's worktree** and a server that was added for one folder only: not
  tested (`docs/linear.md`).

## How another setup does it

sadensmol/skills, read 2026-11-14. That repository has no license, so it is a reference for ideas
and none of its text may be copied. Linear is reached through the Linear MCP server, one server
per Linear workspace, and the project's own skill names the server. Team, issue prefix and status
names are never written into the generic skill: they are read at run time from environment
variables, the project's documents or the server itself, because status names are each team's
own. Before the first write it calls `whoami` and stops on the wrong workspace. Its
`task new <tracker URL>` takes the tracker's branch name instead of a slug of the URL.

## What the real server returned (2026-11-14)

The owner connected his workspace under the name `linear`, at user scope, and a fresh Claude Code
run read the trial ticket with only read tools allowed. Facts for whoever builds the skill:

- The server gives 59 tools as `mcp__linear__<name>`. The ones this work needs: `whoami`,
  `get_issue`, `get_team`, `list_issue_statuses`, `list_comments`, `save_issue`, `save_comment`.
  A session that was already running when the server was added does not get them; a new one does.
- `whoami` returns the workspace and the user, which is the check before the first write.
- `get_issue` for `MBZ-1` returns the identifier, title, state name with its type, assignee, URL,
  description and `gitBranchName`. It does not return the team's key; `get_team` on the team id
  does.
- `gitBranchName` was `antek/mbz-1-do-nothing`: the user's display name, a slash, then the
  identifier and the title. That is not Lem's `<type>/<slug>` form, so the skill has to say which
  of the two a task's branch takes and how the other is still found from it.
- That team has eight statuses, and two of them have the type `started` ("In Progress" and
  "In Review"); the others are Backlog (`backlog`), Todo (`unstarted`), Done (`completed`),
  Canceled (`canceled`), Duplicate (`duplicate`) and Triage (`triage`). So a type does not name
  one status: the project's settings have to name the status for "work started" and the one for
  "landed", or the skill asks once and writes them down.
- `MBZ-1` is titled "Do nothing", in Todo, and its description says it is a sample ticket for
  the integration test.

The owner asked for this on 2026-11-14, in the session that started Lem: "put on queue:
integration with Linear".

The owner has a Linear workspace of his own (said on 2026-11-14), so the `linear` skill can be
tried against a real workspace before it is called done. He named the ticket for the trial:
`MBZ-1` (2026-11-14). `docs/linear.md` says how the server is connected, under the name `linear`;
he sets that up himself and says when it is done. Do not write into any other ticket of that team.
