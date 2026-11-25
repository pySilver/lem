# Notes of the step `board-pages`

## For `board-service` and `board-views`

Bind `app.state.page_inputs` to a callable matching `lem.board.pages.source.Source`.
It takes the request, the resolved workspace (None for `/`), and the version read before
the inputs. It returns a typed `Page` or `Workspaces`. The route is in
`request.state.page_route` and its arguments are in `request.path_params`. The provider
gathers facts, takes preferences and the listener from the request, and calls the pure
views. The templates and the route table do not gather the view's facts. A missing
provider leaves the existing slice's Tasks and stream in place. The other workspace
pages need the binding. Use the same provider to render the page after an act. Content
of `GET /tasks/SLUG/raw/PATH` and `/media/PATH` belongs to `board-service`.

The browser's jump posts to `/HOST/WORKSPACE/agterm/SESSION`. `Head.jump` holds the
base through `agterm`; a refusal's `error.why` is what the browser prints. The app
must supply this address only on the local listener.

The stream polls every 0.5 seconds and sends a ping every 10 seconds. These are the
constants in `board/stream.py`. The route outside the slice uses a version of task
records, sessions, the selected task's artifacts, the owner's presence, settings,
the backlog, and the state files that affect a page. Removing the `watchfiles` lockfile
entry belongs to the step that edits the Python dependencies. A forge or session look
that changes only in memory needs a written stamp or an input to the version.

## For `board-inputs`

A `Parked` row has a task address. It has no session address, so the row itself opens
the task. The session jump still works on a task header that carries one. A backlog
`Entry.where` supplies text. Add a typed link if the place must open as an address.
The switcher uses `Space.reachable` to keep an unreachable peer as text, even when it
retains an old address. Supply a fact with a link if the task header offers Park.

## For `ask` and `guides`

The board ships `/assets/vendor/pele.js`, the pinned browser build of Pele, with its
MIT license beside it. It exposes `window.pele.render`; render with links and images
disabled for task text. The board uses this build for its Mermaid fences. In question
pages, point the chart loader to this local asset. Update `NOTICE` and `AGENTS.md`
when their ownership reaches this change.

## For the join

Regenerate both ownership tables if the join changes the ledger moves.
`tests/unit/board/pages/test_routes.py` checks the HTML or asset each page route serves
and the refresh the stream sends. It supplies the typed inputs to the same route table
the server uses.
