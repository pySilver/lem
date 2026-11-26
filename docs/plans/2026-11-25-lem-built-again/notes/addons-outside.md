# The add-ons at the board and the state store

## Board service and pages

The joined-board routes are already wired by `board.app`. The entry board's pages and
`GET /api/workspaces` also need the combined list. Use the existing `board.app` import of
`lem.addons.peers.routes` to set `app.state.peer_spaces = peers.spaces`. In the workspace index,
API, and switcher, await it with the request and the local rows as `peers.rows.Row` values.
The row fields follow the existing workspace wire format. Set
`app.state.peer_own_rows = local_rows`, a callable from the request to a tuple of the local rows.
The relay uses it to give a peer's switcher the entry board's rows. See
`tests/journeys/test_peers.py` for the callback, the two apps and the same production routes.

A request with `Lem-Hop` may show its own board but must have no local-session or write actions
available from that page. The relay rejects every method except GET and HEAD. Suppress the
agterm links and local actions in that view, including app-rendered links that use GET.
The peer lookup keeps the last table refusal in `peers(request).trouble` for the board's problem
line. The board's lifespan can cancel the pending look tasks in `peer_registry.pending` at stop.

At close, `board/pages/joined.py:peer_problem` still reads the shared last failure on a
forwarded page. A direct page can leave that failure in the registry. The next request with
`Lem-Hop` skips the local table, but the workspace index and page can show the old error.
Make the problem read request-scoped in `joined.py`, using the same hop marker as
`peers/routes.py:spaces`. Keep the direct page's problem and test a forwarded request after
it on the same app. Do not clear the registry to serve a forwarded request, since a direct
request can use it at the same time.

## Inbox duty and task page

Start `lem.addons.inbox.schedule.run(targets, report, stopping)` beside the board's other
lifetime duties. The callback `targets` lists real workspaces as `schedule.Target`, with the
workspace plus its absolute board URL (`/HOST/WORKSPACE/` at the tailnet door when open).
`report` takes each checkout's name and the problem or None. Pass the board's stop event.
Use a composition point in `cli/serve` to bind the add-on if the app needs a callback. Keep
the board's import boundary. The duty reads the owner's waits and the live session through
`app.owner.looking`, uses its own poll interval, and stops at the board's stop event.

The task panel reads `lem.addons.inbox.link.shown(state, slug, away=away)` at the same
composition boundary. A URL is the thread at the Inbox's tailnet address. A reason belongs
by the link when it cannot be shown. The standalone read is covered in the Inbox unit tests.
The task panel's external action still needs its template and board input wiring.

## Retention

The workspace's retention duty owns expiration. Expert folders match
`lem.addons.experts.folders.NAME`. Keep old non-question directories. A brief publishes only its
own folder. Panel and cast copies use `panels`, `personas-cast`, `personas-profile` and
`personas-person` in state. Copy reads update their time. Coordinate the retention test with
`board-duties`; the add-on has no prune command.
