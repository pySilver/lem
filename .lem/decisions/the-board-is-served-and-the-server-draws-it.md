---
decided: 2026-11-20
area: The board and the pages for him
---

# The board is served, and the server draws it

On 2026-11-16 the owner gave the design to the session that builds Lem: "You are the owner and
long-term maintainer of this codebase, and its design is up to you. Pick recommended action if
you still see it as best oucome." Two reviews of Lem, by Codex and by Fable, had left the points
below open, and that session decided each under his sentence. None of them is his ruling: each
is the session's, and open to him.

The final round of 2026-11-17 took the decisions below, after two real runs of the plugin form in a
scratch repository (R1 to R6) and the final audit of `636b24c` (A1 to A15).

**The board is served, and the server draws it** (2026-11-20). The owner: "Lack of being able to
oversee the process away from laptop its my biggest pain". The board was one file:// page that agterm
opened, with 2,980 lines of its own JavaScript (the one script of `board.html` at 1971c8e)
that read the state folder through copies of the log and of each task's files as scripts. Now
`lem serve`, one standard-library server for the machine, draws every page from the state folder
(`lem_board_model`, `lem_board_pages`, `lem_board_task`), and Turbo and a few Stimulus controllers
are all the browser runs: a stream of server-sent events tells an open page each change, which it
morphs in, so a phone, a laptop and agterm show the same board, and no file of the page is written
at an event. Tailscale is the first-class way in from another device, behind `tailscale serve`, with
the owner's own login as the check, Funnel refused, and the Mac itself served on 127.0.0.1 with no
check. The server starts on demand (`--ensure` from the SessionStart hook and from `lem board`)
and replaces itself after an update, with no launchd agent to install or to outlive the plugin. It
shows a list of workspaces for the machine (`workspaces.json`), and the machine's name is in each
address, so that a second machine's workspaces can join under their own. agterm gives an http page
no bridge, so the board's two acts of agterm go through the server, on this Mac only. The board
notices a merge on the forge itself: a thread of `lem serve` asks GitHub a few minutes apart about
the open pull requests nobody watches, and for one merged or closed there runs `lem land merged`,
the bookkeeping a status runs and no other step. Its notifications are web pushes with no payload,
signed with a key kept in Lem's home folder, and `/usr/bin/openssl` signs them, the one program
outside the standard library (`lem_push.py`). Two machines show under one address with `lem serve
--join HOST`, which lists the other's workspaces as `HOST/WORKSPACE` and passes its pages and its
stream through over the tailnet (`lem_peers.py`). A chart is drawn by a vendored mermaid, the file
`lem-ask` pins, which only a document with a chart names and a page loads at its first chart.
