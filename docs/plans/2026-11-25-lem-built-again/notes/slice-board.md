# Notes of the step `slice-board`

What the walking skeleton of the board needs in files it does not own, and what the steps that
own its files later take over.

## For `tree`: the stub test of `tests/unit/cli/test_tree.py`

`test_each_stub_refuses_not_built_and_names_a_step_of_the_plan` runs every leaf of the tree and
expects `not-built`. The slice fills `serve ensure`, `serve stop` and `serve run`, so these three
cases fail: in the test's home they refuse `owner-port`, since the machine's port is 4536 there,
and no server starts. `lem board` still refuses `not-built` with no `--no-open`, so it passes.
Every slice that fills a leaf meets the same case. The change asked: a leaf is a stub while its
module holds `not_built` (it imports it from `lem.cli.stub`); the test takes only such leaves, as
`[leaf for leaf in LEAVES if hasattr(importlib.import_module(leaf[1]), "not_built")]`. A filled
leaf no longer imports it.

## For `core`: `pyproject.toml` and `uv.lock`

One commit (`build(deps)`) adds `starlette`, `uvicorn`, `jinja2`, `sse-starlette` and
`watchfiles` to the dependencies and `httpx` to the dev group, with `uv add`. No change of
`records/`, `ports/`, `kernel/errors.py` or `kernel/envelope.py` was needed.

## For `board-service`: the files it takes over

The plan names `board/{app,server,stream}.py`; the gates' limits (7 members, 12 imports) split the
rest of `serve.py`'s job into modules of their own, all under `board/`:

- `facts.py`: `Facts` (the answer of `GET /api/server` and the body of `serve.json`), `Install`,
  and what `serve ensure`, `serve stop` and `serve run` print. `HEADER`, `Lem-Server`, marks the
  server's own answer: a port that answers without it, or with another home folder, is refused
  and never stopped.
- `serve_file.py`: `serve.json` replaces `serve.pid`, written by the app's life at its start and
  removed at its clean stop only while it names that pid. `__main__`'s look reads it
  (`notes/core.md`, "the silent server start").
- `install.py` (the replace rule, pure), `client.py` (the questions to a port, `http.client`),
  `start.py` (the detached start: `python -B -P -s -m lem serve run --port N` with
  `PYTHONPATH` set to the starting install's package folder, so the server runs that install),
  `ensure.py` (`ensure`, `stop`, the serve lock with a deadline).
- `machine.py`: the port and the guard of the owner's two ports, and the machine's name.
- `workspaces.py`: `workspaces.json`, a list of absolute paths, and the names of the addresses.
- `life.py` (`serve.json` and the duties' loop while the server lives), `shield.py` (the `Host`
  check by Starlette's `TrustedHostMiddleware`, and the page of a `Fault`), `stub.py` (the 501).
- `server.py`: binds the socket before uvicorn, so a held port is a refusal; `Board.stop_by` is
  the handler of SIGINT and SIGTERM outside uvicorn's own, because uvicorn raises the signal again
  after its clean stop (`capture_signals`), which would end `lem serve run` with -15 and no
  envelope.
- `lem serve run` takes `--port N` (`tests/unit/cli/tree.json` written again). `serve run`,
  `serve ensure` and `lem board --no-open` put the workspace of the call on the list, since
  `serve add` is not built.

## For `settings`

`board/machine.py` reads `[serve]` of `machine.toml` with `tomllib` into its own `Serve` struct
(`port`, `tailscale`, `tailscale_port`). It gives way to `settings/machine.py`; the guard of the
owner's ports (`guarded`) stays wherever the port is read.

## For `board-inputs`, `board-views`, `board-pages`, `board-duties`, `addons-outside`

- `board/inputs/kanban.py` and `board/views/kanban.py` are slice versions: four columns by
  status and hold only, with no actor, progress, chip or wait.
- `board/pages/` holds the kanban, `place.py` (a page's workspace, 404 else) and `render.py` (the
  Jinja2 environment, `autoescape=True`, `StrictUndefined`); `board/templates/` has `layout.html`
  and `kanban.html`, with no sidebar, search, panel or keys. Assets are served by `StaticFiles` at
  `/assets/`, with no digest in the address and no cache header.
- `board/stream.py`: the version is a digest of each `tasks/*/task.json`'s name, inode, size and
  change time, so a change of another file (the owner's mark, the settings, the backlog, a task's
  artifact, `?task=`) sends no refresh yet.
- `board/duties/runner.py` runs each of the seven stubs' `tick(workspace, now)` every 20 s in a
  thread; one duty's failure is not kept from the others yet (the seams of `forge_loop`).
- `lem.addons.peers.routes.ROUTES` is empty: its one address, `/{peer}/{rest}`, would take every
  address that no other table names.
