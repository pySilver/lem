---
worth: later
where: skills/lem/scripts/serve.py:Workspace.count
added: 2026-11-22
---
# The switcher's count of this board lags the sidebar for up to 5 seconds

The switcher's row for "this board" and `GET /api/workspaces` take their number of what waits for the
owner from `Workspace.count`, which keeps its answer for REFRESH_SECONDS (5 s). The sidebar's "Waits for
you" and the inbox icon count `bm.waits_of` of the model at each render. So a page that the stream
refreshes within 5 s of a change can show the switcher's row one more or one less than the sidebar, and
a read of `/api/workspaces` just after a write gives the old count. The builder of task 1 of
counters-in-sync met it on the demo board: the waits read from `/api/workspaces` before and just after
each of two writes of merge events were `["5", "5", "3", "5"]`, while the page showed 5, 3, 5, 3. A fix drops the
cache for the workspace the page shows, or keys it on the log's version and the watched files as the
stream does.
