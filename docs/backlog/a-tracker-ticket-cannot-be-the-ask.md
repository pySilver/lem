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

The owner's reading, which is the design: a ticket is a source of the task's context, the same
thing to Lem as a backlog item. Both are where an ask comes from, and both are closed by the
landing: a backlog file by `git rm` in the commit that lands the fix, a ticket by its move to the
team's "done" state with the landed range in a comment. So this is one role, "where asks come
from and are closed", with the repository's backlog as the form that is always there and a
tracker as a second form a project may name.

What it has to do, in the order a task meets it:

- `new`: read the ticket (title, description, parent, labels) into `task.md` with its link; take
  the tracker's own branch name when it gives one, so a second worktree is never made for the same
  ticket; move the ticket to the team's "started" state.
- `land`: comment the landed range and what the owner gets, and move the ticket to its "done"
  state. With `branch.land = "owner"`, do both when the owner lands, not before.
- `night`: a tracker is a second list of candidates beside the backlog. Not needed for the first
  version.
- A decision Lem takes alone is never written to the ticket as if the owner took it.

How another setup does it (sadensmol/skills, read 2026-11-14; that repository has no license, so
it is a reference for ideas and none of its text may be copied): Linear is reached through the
Linear MCP server, one server per Linear workspace, and the project's own skill names the server;
team, issue prefix and status names are never written into the generic skill but read at run time
from environment variables, the project's documents or the server itself, because status names
are each team's own; before the first write it calls `whoami` and stops on the wrong workspace;
its `task new <tracker URL>` takes the tracker's branch name instead of a slug of the URL.

Options: (a) a role in the harness contract, "the tracker", with Linear as the first form: a
`[tracker]` table in `.lem/project.toml` (kind, the MCP server's name, the team), a shipped
`linear` skill of our own, and the calls in `new` and `land` above. A second tracker is then one
more skill. (b) Linear written straight into the stages: less to build, and every later tracker
is a rewrite of two stage files. (c) No integration: the owner pastes the ticket's text.
Recommendation: (a). The machine check gains one optional row, the tracker's server.

Not known yet, and it decides when this is built: which of the owner's projects keeps its work in
Linear. Lem's first runs are in a scratch repository and then in mybaze, whose work is in
`docs/backlog/`.

The owner asked for this on 2026-11-14, in the session that started Lem: "put on queue:
integration with Linear".
