# Notes of the step `board-service`

What the board service gives the other steps, and what it needs in files it does not own.

## What is built

- The server: `board/server.py` (uvicorn on the main socket and, with the door open, the door's
  socket in one server: one app, and the port a request came to picks its check, `shield.py`),
  `listening.py` (the sockets bound before uvicorn, the stop), `opening.py` (the door, the
  machine's names, the session the server leaves), `serving.py` (what the app serves with:
  home, environment, the stop, the counts, the watcher), `life.py` (serve.json, the duties and
  the push watcher while the server runs).
- The replace rule (`install.replaces`, `ensure.kept`): the same install keeps `main`'s rule (a
  server whose code or settings differ is replaced; `ensure.held` takes the main and door ports
  from `[serve]`); another install replaces it only at a higher release. `ensure.rebound` stops
  the listener that `serve.json` names on a port the settings left, so a moved `serve.port`
  takes effect at the next ensure, whoever wrote it.
- The door: `door.py` (the check of every request, the owner's login read again at most once in
  30 s), `tailscale.py` (the CLI: a home that is not the owner's runs only the one
  `LEM_TAILSCALE` names), `tailnet.py` (status, name, login), `served.py` and `publish.py` (the
  entry in `tailscale serve`), `doorway.py` (`lem serve door on|off`).
- The server's own addresses, the last route table (`push/routes.py`): `own.py`
  (`/api/server` with the notifications, the stop, `/api/workspaces` from `counts.py`),
  `taskfiles.py` (raw and media), `aliases.py` and `renamed.py` (the other name, an address with
  no machine's name, a workspace's address with no final slash).
- The notifications: `adapters/notify_push*.py` (the `Notifier` port on pywebpush and py_vapid;
  `LEM_PUSH=record|send`, unset: a home that is not the owner's records), `board/push/` (the
  routes, the manifest, a device on and off, the news rule, the watcher every 5 s).
- `listener.py` (`at_door`, `act_refusal`: the main listener's check of a page's act),
  `prefs.py` (`asker_of(request)`: local, may act, native, and the cookie), `watched.py` (what
  the stream's poll stamps), `look.py` (the look before a command), `boards.py`,
  `companion.py`, `editing.py`, and the leaves of `cli/serve/` (but join, leave, peers) and
  `cli/board/`.

## For `board-pages`: `board/stream.py`

The plan gives `stream.py` to board-pages and amendment A8 (the stream polls) to this step. This
step changed it as little as A8 needs: `awatch` left for a loop of `anyio.sleep(TICK)` (0.5 s)
that compares `watched.look(state, home, task)`, and `events` takes `home` and `task`
(`?task=SLUG`); the id is that look's digest. `watchfiles` left `pyproject.toml`.

The stream controller reads `data-stream-rendered` from the newly rendered scope when it opens.
The layout puts it on `main` with `data-stream-task=""` for the workspace or the slug for a full
task page. Read `watched.look(state, home, slug)` before reading the task or its files. Put that
digest and slug on the rendered task frame too, so a frame visit can supply its own version.
Keep both attributes outside the permanent live indicator.

## For `board-acts`

- `lem.board.listener.act_refusal(request)` is `main`'s `action_refusal` for an act of a page:
  None through the door (the door checked the origin) or from the board's own page on this Mac.
  `listener.at_door(request)` tells the door's requests apart (the jump to a session is not
  taken there).
- `request.app.state` holds `home`, `environ`, `stop`, `counts` and `watcher` (`serving.SHARED`)
  beside `facts`.

## For `board-pages` and `board-views`: who asks

`lem.board.prefs.asker_of(request) -> Asker` gives `local`, `may_act`, `native` and the cookie's
`Prefs` (`folded`, `rail`, `pw`, `full`, `head`), each checked as `main`'s `prefs_of`, for the
`Viewer` of `board/inputs/layout.py`. The manifest's icons are at `/assets/icons/icon-*.png`.

## For `board-duties`

The push watcher runs in `life.py` beside `duties/runner.loop`, every 5 s, not in
`duties/notify.py`: that stub can stay empty, or call `lem.board.push.watch.Watcher.look` if the
duties take it over (then `life.py` drops its own loop).

## For `sessions`: the terminal's port

`lem board` opens a page with `Terminal.show(here, url, "companion")`. `main` did more: it found
the companion of the session's group that shows the same workspace's board (or the same file),
reloaded it where it stood or opened it again at a task's address, closed stale ones, renamed
it `Lem board · REPO`, tinted it, and selected it with `--follow`. Asked: `show` in the mode
`companion` keeps one companion per address base (reload, or open again when the path differs),
and returns the companion's id, so that `--follow` can select it and `rename` can name it. Until
then `lem board --follow` is refused, and each `lem board` opens a new companion. A page of
`--page` opens by its `file://` address, which agterm's `--url` was not tried with (`main` used
`--html FILE --cwd DIR`): untested.

## For `task`: the list of workspaces at a task's open

`main`'s `project task-dir` put the main checkout on the machine's list. The rebuild's
`cli/task/open.py` (task's) may call `lem.board.workspaces.noted(folders.home_for_writing(env),
folder)` (cli may import board); the `serve` hook runs `lem serve ensure` with `cwd="/"`, so it
puts nothing there. Until then a new repository gets on the list at `lem board`,
`lem serve ensure`, `lem serve run` or `lem serve add`.

## For `settings`

- `lem settings set serve.tailscale_port N --machine` while the door is open leaves Lem's entry of
  the old port in `tailscale serve`; `lem serve door off` before the move takes it out. A check
  of the door in `lem doctor` may name a stale entry.
- `lem doctor`'s push row may read `lem.board.push.listing.status_of(home)`.

## For `core`

- One commit (`build(deps)`) adds `pywebpush` and removes `watchfiles` with `uv`.
- `tests/unit/board/test_slice.py` (slice-board's) builds the app through `serving.Serving` now,
  and no longer expects 501 from the addresses this step built.
