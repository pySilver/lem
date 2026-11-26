# Lem, built again from the ground

> **Status: in work** on the branch `rebuild`, cut from `main` at `bf6d2836`. Written on
> 2026-11-25 by an Opus writer and a Sol reader, in a talk of seven turns, from two blueprints
> (Fable's and Astra's). The choices of part 11 were decided by the maintaining session while
> the owner was away, and are open to his review. From its stage 3 on, this plan replaces
> `2026-11-24-lem-as-an-app.md`, whose stages 1 to 3 are on `main`.

Marks: **[F]** from Fable's blueprint, **[A]** from Astra's, **[both]** from both,
**[pair-settled]** a point the writer and the reader both took (a claim of the pair, not a fact),
**[decided]** a choice the maintaining session decided, **[probe]** a measurement made for this
plan (what and when are named), **[seen]** a fact the maintaining session saw on the owner's Mac.
Sizes and times without a source are unmeasured estimates. Every cite of today's code is at
`main` `bf6d2836`, the proof of concept.

Two annexes are part of this plan: `2026-11-25-lem-built-again/landing.md` (the landing's
tables) and `2026-11-25-lem-built-again/surfaces.md` (today's commands, acts, hooks, doctor
checks and settings against the new build). They are maps. The complete list of what the proof
of concept does is the behavior ledger, `tests/ledger/` (part 8), and every row of it has one
owning step (part 9). The build's working files are beside the annexes: `notes/STEP.md` (a
step's request to the owner of a file it may not edit) and `trials/NAME.md` (a trial's checks
and evidence). `builder-rules.md` there holds the standing rules every builder reads.

## 1. What Lem is, and what is in the first version

Lem keeps each task's record, refuses a step that is not due, runs the landing's machine steps,
and tells the owner what waits. Agents do the thinking; the stage files tell them how. [both]
The owner's measure: "new version isn't worse than our proof-of-concept `lem`". Every ledger row
is kept, changed with a reason, or dropped with a reason, and each has a proof.

| Job of the proof of concept | First version |
| --- | --- |
| Open a task in its own agterm session; copy the talk; the first line (type, track, careful, then) | kept; typed fields (`lem task read`), not fixed text lines that code parses [F] |
| Status, `state.md` blocks, fixed state lines, `lem project log` events | changed: one task record with a typed journal; a typed command for each fixed line and event [A] |
| Queue by `after:` and by his order; "start SLUG now"; may-start; plan-only; build by plan file | kept |
| Interview, criteria, persona read, its silence and its skip, approval with digest and history, change with before and after | kept, in the task record |
| Investigation of a bug or a question, its typed result, `answered` | kept |
| Plan file names, the plan talk and its counts in the PR, lead, builders, ladder, breaker documents, decisions log | kept |
| Spans for the time card; live check and merge waits | changed: spans are record fields; waits are typed journal entries [F] |
| The landing: every step, refusal and hard path | kept; the due step derived from evidence inside an explicit phase [F, pair-settled] |
| Owner presence, its watch, the one list of what waits in its nine groups | kept |
| Board: four views, keys, search, five tabs, charts, every act and its refusal, phone, Web Push, tailnet door, two machines, Inbox links | kept, on Starlette and Jinja2 [both] |
| Server duties: forge watch, merge on a verdict, conflict wake, queued start, session guard (45 + 10 min, the unreadable path), hourly prune, notifications; the silent start by a command | kept; one workspace's failure leaves the others' tick (part 8, seams) |
| `lem ask` cards, templates, demos, `render` with attachments, the Stop hook's mark | kept; served by the board server if trial A1 passes, else rendered to a file [decided] |
| The five hooks | kept, through `hooks/run` as on `main` |
| Settings in four files, `set local/global`, machine numbers, sources shown | kept [A] |
| GitHub Issues and Linear steps, after the end too | kept |
| Release stop two releases back | kept (the owner's ruling of 2026-11-18) |
| Night, retro, proposals, reviewer items, lessons, corrections, Jev, experts, cast, naps, Inbox, picker | kept, add-on packages the core never imports [F] |
| `doctor` (personas, push status and the rest), `init`, the version check | kept, with new rows |
| The Python 3.9 launcher, `sibling.py`, `names.py`, `markup.py`, `lem project may-land`, the shell test framework, `board-cdp.mjs`, readers of 0.3 records, `lem corrections collect` (one writer: `settings set`) | dropped; each with a proof that its job is done elsewhere |
| Codex as a session's agent, another forge, another terminal | later: no ruling asks for them |

## 2. The package tree

```text
src/lem/
  __main__.py      `lem`: the version check, the silent server start, then cli.lazy.main
  kernel/          errors, envelope, clock, files (whole write, publish), locks, procs, logs
  records/         msgspec structs only: task, criteria, decisions, questions, journal,
                   landing, owner, items, sessions, corrections
  store/           tasks, steps (the step lock), workspace (the claim lock), owner, retention
  model/           pure rules; no os, subprocess, socket, time
    task/          table, holds, queue, read, spans, claim
    criteria/      approve, change, digest, read
    decisions/     log, ladder, breaker
    owner/         waiting, answers, presence
    landing/       phases, start, base, carry, checks, bar, review, filing, green, propose,
                   mergeread, merge, reconcile, clean, invariants
  ports/           Protocols: git, forge, terminal, harness, tracker, notifier, judge
  adapters/        git_cli, forge_gh, terminal_agterm, harness_claude, tracker_github,
                   notify_push, judge_jev
  settings/        team, shared, machine (structs), places, load, edit, show
  app/             wiring.py (builds Ports at call time), and use cases:
    tasks/ criteria/ decisions/ sessions/ owner/ init/
    landing/       start, base, polish, checks_gate, checks_run, checks_tree,
                   checks_criteria, review, filing, propose, pr_text, mergeread, merge,
                   reconcile, merged, clean, next
  cli/             lazy.py (two-level lazy group), nouns.py, output.py, version.py, and one
                   package for each noun: verbs.py and one leaf module for each command
  board/           (below)
  hooks/           main (lem-hook), corrections, serve, session, precompact, stop, raw
  addons/          proposals, corrections, jev, experts, cast, inbox, peers, naps, picker
tests/             __main__.py (the one entry), conftest.py, fakes/, fixtures/, unit/, model/,
                   histories/, contract/, journeys/, hooks/, browser/, ledger/
hooks/             hooks.json, run (POSIX sh)        [plugin files, carried in the wheel]
```

**Imports.** A package imports only from rows below it; import-linter holds the layers, and a
nested `ruff.toml` in `model/` bans `os`, `subprocess`, `socket` and `time` (ruff's
`banned-api`).

```text
cli   board   addons
app
adapters   settings
ports
model
store
records   kernel
hooks: the standard library only (json, os, sys, tomllib, fcntl)
```

Import-linter permits one import across the top row: the fixed import from `board/app.py`
to `lem.addons.peers.routes`. `slice-board` owns that stub until `addons-outside`.

**Sizes**, lines of Python [between F's 25,600 and A's 18,200]: kernel, records and store
2,000; settings 700; model 4,000 (the landing 2,000); ports and adapters 2,800; app 4,000; cli
1,600; board 3,800; hooks 500; add-ons 2,600. About 22,000 give or take 4,000, against 66,270
in `src/lem` before the stage 3 join (`wc -l src/lem/*.py`).

**The style, as it falls on real pieces.** wemake-python-styleguide 1.9.0 with its own limits
(7 members a module, 12 imports, 5 locals, cognitive complexity 12) holds `src/lem`; `tests/`
has ruff and pyrefly only. The refusals were seen in the style work of 2026-11-24 and 25 [seen]
and in two probes of 2026-11-25 [probe: a Click command, and the 13 commands of `lem land` as
leaf modules, under `flake8 --select=WPS`].

| Refused | Form used |
| --- | --- |
| A Click command with decorators and six inputs (WPS211, WPS216) | `COMMAND = click.Command(name, params=[...], callback=lambda **given: run(msgspec.convert(given, Call)))` |
| A noun's commands in one module (WPS202 13 > 7) | one leaf module per command: a `Call` struct and a `run` function |
| One tree table with the noun repeated (WPS226) | `cli/nouns.py` (noun to verbs module) and `cli/NOUN/verbs.py` (verb to leaf module), tuples of pairs |
| A dict, list or set literal as a module constant (WPS407) | tuples, or `MappingProxyType` |
| Logic or a class in `__init__.py` (WPS412) | empty `__init__.py` |
| `data`, `result`, `item`, `value`, `file`, `info`, `handle`, `content` (WPS110) | specific names; a JSON key `result` is `msgspec.field(name="result")` |
| A string literal over three times (WPS226) | kinds and keys are struct tags and fields |
| A call or subscript in an f-string (WPS237); a nested conditional expression (WPS509) | a local first |
| A complex annotation on one line (WPS221) | a `type` alias |

The probe of `lem land` (13 leaves, the two tables, the lazy group, the envelope) passed with no
finding and ran a leaf in 53 ms of wall time.

**The landing, down to its modules.** Each stage is a pure module in `model/landing/`
(`holds(evidence, world) -> Held | Due`, `decide(...) -> Refusal | Decision`) and an effect
module in `app/landing/` (`gather(ports, task) -> World`, `run(decision, ports) -> Evidence`).

**The board, down to its modules.**

```text
board/
  app.py        the Starlette app. It imports five route tuples by fixed paths:
                lem.board.pages.routes, lem.board.acts.routes, lem.board.ask.routes,
                lem.board.push.routes (push and the server's stop), lem.addons.peers.routes
  server.py     two uvicorn listeners (local, door), the serve lock, the replace rule
  door.py       today's `serve.door_refusal`
  stream.py     watchfiles over the state folders -> a version -> SSE `refresh`
  inputs/       typed view inputs: one msgspec struct per page section
  views/        pure: records and model outputs -> inputs (kanban, waits, backlog, activity,
                overview, criteria_tab, checks_tab, timeline, artifacts, merge_page)
  pages/        routes, workspaces, kanban, waits, backlog, activity, search, task
  acts/         routes, answer, merge, session, start, backlog, jump
  push/         routes, subscribe, send (pywebpush)
  ask/          routes, page, waiter
  duties/       runner (a fixed tuple of duty module paths), forge, merge, conflict, queue,
                guard, prune, notify
  templates/    one Jinja2 file per page section
```

`slice-board` writes `board/app.py` and `duties/runner.py` once, with every route module and duty
path, and each such module as a stub with an empty tuple, `lem.addons.peers.routes` among
them (its stub is `slice-board`'s until `addons-outside`). From group 4 `board-service` owns
`app.py`, and no other step edits it: each step owns only the modules `app.py` names. A template
only loops and prints over `inputs/`; `tools/board-kit` is carried.

## 3. The domain model and its storage

**Entities.** A workspace (a main checkout with `.lem/`); a task (slug, track `small|full`, type,
status, hold, criteria, decisions, questions, spans, the landing); a question (a card or a board
row: id, options, the digest it shows, first answer wins); the owner's presence; a backlog item;
a proposal. [both]

**One record per task, written whole** [A, pair-settled]. `.lem/state/tasks/SLUG/task.json`:
`{schema, release, revision, task, landing, journal}`. The journal is a list of typed entries
(span start and end, state, decision, review round, careful missed, not-green reason, act of the
owner, check wait and end, merge wait: `landing.md` I). Views render its lines; the Activity
chart, the Timeline and the retro read its fields; no rule of `model` reads it. A rename leaves
the old or the new record, never a torn line. Today four readers fold one log
(`board_model.fold`, `project.read_tasks`, `land.events_of`, `criteria.events_of`); none has a
successor. Decoding a 500-entry record and folding 500 events both took 45 ms for the whole
process [probe, 2026-11-25, median of 21], so cost did not decide this.

**Prose and artifacts** [pair-settled]. A Lem-written artifact that the record cites by digest is
published whole before the citation, at a distinct path (numbered, or named by tip and base), so
a cut-off never changes a cited file. Agent-written prose (`handoff.md`, `report.md`, `notes.md`,
the interview's files) is read as it is and never cited by digest. The pull request's text:
each body is a distinct `pr-ROUND-DIGEST.md`, and the record keeps citing the previous body
until the forge confirms the new one; the board shows the confirmed text and, while an edit
waits, one line that a newer text waits for GitHub (part 8, seams).

**The sessions of a task** [pair-settled]. A hook never writes `task.json`. The `session-start`
hook appends one framed record, one `os.write` of `"\n" + json + "\n"`, with `{v, at, source,
claude, transcript, pane, task}`, to `tasks/SLUG/sessions.jsonl`; a reader skips empty lines,
damaged lines and an unknown `v`. A transcript counts for a task by today's rule
(`tokens.transcripts_of`): read across every task's sessions file and summary, each path once, by
its first prompt, and by the recorded task when the prompt names none, so a fork logged under
another slug still counts for its open task.

**Locks** (`landing.md` G). The record lock covers read, `revision` check and write, never an
effect. The step lock covers a whole landing step, and a drop's write [decided]. The workspace
lock covers a claim: the scan of every record and the publication of the new record, together. A
ticket stays claimed by a landed task for good, and by a dropped or answered task while it owes
the ticket a step (`project.released`, `holder_refusal`); a backlog item is claimed by any open
task that started from it. The merge and serial locks and the load line stay.

**A write.** `store.update(slug, change, expect=revision)`: lock, read, refuse a stale `expect`,
apply the pure change, write a unique temporary file, `fsync`, rename, `fsync` the folder. A
board answer carries the question's id and the digest it showed [pair-settled].

**Elsewhere.** `.lem/state/`: `backlog/`, `night/`, `retros/`, `experts/`, `panels/`, `locks/`,
`forge.json`, `inbox.json`. Home (`~/.config/lem/`): `owner.json`, `machine.toml`,
`settings.toml`, `workspaces.json`, `serve.json`, `serve.lock`, `load.line/`, `push-key.pem`,
`push.json`, `lem.log`, the correction queue.

**Retention.** After `state.keep_days` (local over team) with nothing new on an ended task:
`task.json` stays, its journal folded into one summary entry with the facts today's
`project.summary_of` keeps (status run, first and last, PR, type, track, lead, careful,
proposal, investigation, plan talk, night, opened, newest, totals of spans and waits);
`sessions.jsonl` stays, so Done and the token totals still count; `ask.txt`, `task.md`, the
ticket and resume files stay; every other file goes, and the record's citations of them are
cleared. Folders of experts, panels, naps and cast copies unused that long go.

**The task: a status and a hold** [both].

| Status | Entered by | May go to |
| --- | --- | --- |
| `queued` | `task open --after`, `task read --order`, a lead's queue by his order | `shaping`, `building` (`task start --words`), `dropped` |
| `shaping` | `task read` | `building`, `answered`, `dropped`, `queued` |
| `building` | the lead or the fast track's builder | `queued`, `planned`, `ready`, `shaping`, `answered`, `dropped` |
| `planned` | `task planned` | `building` (`task build`), `dropped` |
| `ready` | the report | `landing`, `building` (a breaker's way back), `dropped` |
| `landing` | `land start` | `open`, `ready`, `shaping`, `planned`, `dropped` |
| `open` | `land propose` | `landing` (a new round), `landed`, `dropped` |
| `landed`, `answered`, `dropped` | | none |

| Hold | Set by | Cleared by |
| --- | --- | --- |
| `owner: interview, criteria, skip-read, fact, step, plan` | the stage | his answer |
| `breaker N` | the lead | help, park, drop |
| `blocked: why, fix [, after SLUG]` | a machine failure, a red base, no checks, a gone repair session | the fix, his word, that task landing |
| `parked` | his park | his resume |
| `release` | the store, for a record two releases back | drop, then resume |

A drop goes from any status that is not ended, by the table above, under the step lock
(`landing.md` E, "Drop during a step").

**The landing** [F's ledger, A's binding; pair-settled]. An explicit phase; inside it, the due
step is the first whose evidence does not hold for the world gathered now. Carry is computed from
facts (git's merge of the reviewed tip onto the new base against the new tree), never from a
record of the rebase, which removes the class of
`docs/backlog/a-cut-off-around-lem-land-base-loses-the-record-of-the-rebase-that-made-the-tip.md`.
A merge is an intent before the forge call and a reconcile after a stop. Everything else is
`landing.md` A to I.

## 4. The ports and their adapters

| Port | Interface | First adapter | Stand-in |
| --- | --- | --- | --- |
| `Git` | facts: `tip`, `tree`, `merge_base`, `is_ancestor`, `remote_head`, `clean`, `merge_tree(base, tip) -> Sha \| Conflict`, `show(rev, path)`, `commits(a, b)`, `diff_stat`, `rebase_state`; acts: `fetch`, `rebase(wt, onto, reapply)`, `abort`, `push(wt, branch, expect)`, `commit`, `worktree_add`, `worktree_remove`, `branch_delete(branch, expect)`, `fast_forward(checkout, ref)` | `git` | real git in a temporary repository; `ModelGit` |
| `Forge` | `repo()`, `find_pulls(head, base)` (each with its head), `open_pull`, `update_pull`, `pull(n) -> Pull` (state, head, base, mergeable, queued, merge commit, merged head), `open_pulls()`, `merge(n, expected_head, method, subject, body) -> Merged \| Accepted \| Refused`, `delete_ref(name, expect)` | `gh`. `merge` pins only the head (`--match-head-commit`); `pull` reports the destination from the forge itself, and Lem checks it after every merge (`landing.md` H 2) | `LocalForge`: delayed, queued, refused, retargeted, conflicting and outside merges |
| `Terminal` | `sessions() -> list \| Unreadable`, `open(spec)` (never focus; companion), `close(id, when_unselected)`, `tell(id, line)`, `mark(id, status)`, `show(id, url, mode)`, `select(id)` (his act only), `picker(rows)` | `agtermctl` | `FakeTerminal` |
| `Harness` | `launch(seat, brief, cwd, plugin_dir)`, `transcripts(task)` (the rule of part 3), `signs(transcript)`, `tokens(transcripts)`, `available(seat)` | Claude Code; `psutil` where `session.py` parses `ps -A` | `FakeHarness` |
| `Tracker` | `read(ticket)`, `step(ticket, start \| land \| drop \| answer, text) -> Receipt` | GitHub Issues through `gh`; Linear through the agent's MCP, recorded by `task ticket` | `FakeTracker` |
| `Notifier` | `started(wait)`, `ended(wait_id)` | Web Push; the terminal's mark; the Inbox add-on | `RecordingNotifier` |
| `Judge` | `same_items(defect, items)`, `over_bar(defect) -> Score \| NotAsked(why)` | Jev over `httpx` | `FakeJudge` |

`app/wiring.py` builds one `Ports` struct (a field per port) at call time from the settings;
every use case takes `Ports` as its first argument, and a test builds it from `tests/fakes`. Each
fake passes the same contract suite as its real adapter. The clock and the load average come in
as arguments.

## 5. The surfaces

**The command line** [A's library; F's envelope; pair-settled form]. Standard output is one JSON
document, the envelope of `kernel/envelope.py` (part 9, the agreed text). Exit 0 is done, 1 a
refusal, 2 a wrong call (Click's own), 3 a fault with its traceback in `lem.log`. `lem ask`
gives every outcome with exit 0 in `result.outcome`. `next` orders the machine steps; the stages
keep the reviewer's choices, the repair briefs and the owner's words [pair-settled]. The whole
tree of `surfaces.md` A is fixed in `tree` as stubs that refuse `not-built`.

**`lem` before a command** (`__main__.cli`, `look_for_server`, `NO_LOOK` on `main`). `help` and
`version` answer first. The envelope applies to dispatched commands: `help` prints text, and
`version` prints JSON with the top-level keys `root`, `version` and `commit`. A command whose
environment has `LEM_PLUGIN_ROOT` compares that
`plugin.json` with its own version; on a mismatch `doctor` still answers and every other command
refuses with the one line that names the one behind. Then, except for `serve`, `board`,
`doctor`, `ask` and `jev`, it starts the server detached and silently when the pid file names no
live process, unless `LEM_SERVE=off`.

**The board.** Starlette, uvicorn, Jinja2 with autoescape, Hotwire as ruled; the addresses, acts
and refusals of `surfaces.md` B. An act calls the same `app` function as a command. The server
holds no truth.

**The server's replace rule** [pair-settled]. The same install (the same package path) keeps
today's rule (`serve.ensure_held`): a running server whose door port or settings differ, or whose
code is older, is replaced. Another install replaces it only when its version is higher; at an
equal or lower version it leaves it, and `doctor` names which install serves. Two installs on one
home replaced each other's server at each start before this rule [seen, 2026-11-25].

**The hooks** (as on `main`). `hooks.json` runs
`/bin/sh "$CLAUDE_PLUGIN_ROOT/hooks/run" SELECTOR 2>/dev/null || :`. `hooks/run` tries
`$LEM_HOOK_BIN`, then `/opt/homebrew/opt/lem/libexec/bin/lem-hook`,
`/usr/local/opt/lem/libexec/bin/lem-hook` and `${XDG_BIN_HOME:-$HOME/.local/bin}/lem-hook`, and
passes on the output only when the hook exited 0, because a Claude Code started from a GUI app has
`PATH=/usr/bin:/bin` [seen, 2026-11-24]. `lem-hook` imports the standard library only. The five
selectors are `surfaces.md` C. [probe, 2026-11-25: the manifest's line through `main`'s
`hooks/run`, a stand-in `lem-hook` at the fourth path that appends one framed record and prints
one line, stdout captured, 60 runs at a load average of 4: `session-start` p50 40.4 ms, p95
42.5 ms; `stop` p95 43.3 ms.] The target is about 50 ms; the `hooks` level fails over 55 ms at
p95 for any selector, from the installed manifest line [decided].

**Reads outside the working directory.** Claude Code asks "Allow this read outside the working
directories?" the first time a session reads a file of the plugin or of the app's data [seen,
2026-11-24]. Briefs and stages name files under `root` of `lem version` (the plugin folder)
only; the install guide and `doctor` name the one-time question and its allow rule.

**Command forms held to the tree.** A unit test parses the command lines in `skills/`, `agents/`,
`docs/` (apart from plans and backlog items), `README.md` and `site/` against the tree.
`close` requires every line to pass without an old-form skip.

## 6. The settings

Four files [A]. Each table is a frozen msgspec struct with `forbid_unknown_fields`, each field's
`Meta(description=...)` the fix of a refusal; `settings/places.py` is today's
`state.TABLE_PLACES`. Load: `tomllib` per file, a table outside its places refused with the file
where it is valid, each seat and the fallback from the nearest file, `[flow]`, `[checks]`,
`[branch]` from the main checkout (`Git.show` of the base in a worktree), `naps.on = false` and
`state.keep_days` as local vetoes, `msgspec.convert` over the whole. Edit: `settings set KEY VALUE
--local|--home|--machine` through `tomlkit`, under a lock, checked before the rename, comments
kept; nothing writes `.lem/settings.toml`. Show: every effective value with its source. The
tables of `docs/settings.md` are compared with the structs in a unit test.

## 7. The libraries

| Library | Job | Loaded by | Whole process [probe, 2026-11-25, Python 3.14.10, median of 21, load 7 to 9] |
| --- | --- | --- | --- |
| Python alone; `json`, `os`, `pathlib` | hooks | `lem-hook` | 20.3; 29.5 ms |
| `msgspec` 0.22 | records, settings, envelope | every command | 40.7 ms; 40 record classes 42.6 ms |
| `click` 8.5 | the command line | every command | 41.3 ms; a lazy leaf 43.4 ms |
| `tomlkit` | settings edits | `settings set` | 40.2 ms |
| `psutil` | the process table | sessions, guard | not measured |
| `starlette`, `uvicorn`, `jinja2`, `sse-starlette`, `watchfiles` | the board | the server; `jinja2` also `propose` | F: 119, 119, 76, -, 59 ms CPU |
| `httpx` | peers, Jev | add-ons, Judge | F: 182 ms CPU |
| `pywebpush` | Web Push | the server, at the first push | F: 285 ms CPU |
| `markdown-it-py`, `python-frontmatter` | a plan's sections; a backlog item's head | landing, board | not measured |

Against the others, same probe: `cyclopts` 65.1 ms, its leaf 67.4 ms; pydantic 76.3 ms, 40
classes 112.2 ms, a 500-entry record 106.2 ms against msgspec's 45.4 ms. A task runs `lem`
hundreds of times, so msgspec [F] and Click [A]. Tests and gates: `pytest`, `pytest-xdist`,
`hypothesis`, `pytest-playwright`, `coverage`, `inline-snapshot`, `import-linter`, `flake8` with
`wemake-python-styleguide`, `mutmut`.

## 8. The tests

**The one entry.** `tests/__main__.py`, from `main`'s `tests/unit/__main__.py` and `conftest.py`,
is run as `.venv/bin/python -I -B tests --level LEVEL [PATHS...]`. It clears every `PYTEST_*`
variable and `PYTHONPATH` and sets its own `HOME`, `XDG_CONFIG_HOME`, `TMPDIR` and
`LEM_SERVE=off` before a test module is imported: the owner's shell sets `PYTEST_ADDOPTS`,
`PYTHONPATH` and `PYTEST_XDIST_AUTO_NUM_WORKERS`, and a runner that obeys them stops at once
[seen]. A run counts only when passed plus skipped equals collected; a selection that collects
nothing fails; a failed subtest fails its case; `os._exit` fails the run; a missing browser is a
skip. `--level full` takes the machine lock `/tmp/lem-full-run.lock` (fixed before the entry
sets its own `TMPDIR`) and waits: two full runs at once took the load average over 400 and slowed
every time-bound check [seen]. Each gate runs when its inputs exist (ESLint once
`eslint.config.mjs` exists; an import-linter contract once its packages exist).

| Level | Proves | Needs | Aim |
| --- | --- | --- | --- |
| `gates` | ruff, pyrefly, wemake (`src/lem`), import-linter, ESLint | nothing | 30 s |
| `unit` | rules, view inputs, settings, texts as snapshots, the stage lines, the command tree, journal summaries after prune | nothing | 40 s |
| `model` | Hypothesis over the task table and the landing; the invariants after each rule | `ModelGit`, `LocalForge` | 60 s |
| `histories` | a record, a command, the world: the record after, the forge calls, the owner's text | nothing | in unit |
| `contract` | each adapter and each fake against its port's suite | real git; stand-ins for `gh`, `agtermctl` | 60 s |
| `journeys` | every hard path of `landing.md` E; both tracks; park, resume, drop; board acts; the server; two peers; the seams | real git, `LocalForge`, own home and port | 4 min |
| `hooks` | each selector from the installed manifest line: silent with no app, bad stdin, unwritable state; p95 at most 55 ms | subprocesses | 30 s |
| `browser` | keys, sheets, charts, the merge page read to its end, the pictures | Playwright, a throwaway profile | 3 min |

`model/landing` has 100% branch coverage. A step is verified after every change, a reviewer's
too: three reviewer proposals applied word for word broke a gate in one night [seen].

**Not worse than today: the ledger.** `tests/ledger/rows.tsv`, made by `ledger.py` from `main` at
`bf6d2836`, has 3,281 rows of 14 kinds (`unit`, `check`, `ruling`, `command`, `setting`,
`route`, `act`, `hook`, `doctor`, `refusal`, `text`, `guide`, `duty`, `event`), with the columns
`id kind source what fate proof note`. `tests/ledger/extra.tsv`, kept by hand in the same
columns, adds the `path` rows (one for each row of `landing.md` E) and the `seam` rows below;
`ledger.py` joins it. `owners.py` gives every row exactly one owning step (part 9); it refuses a
row with no owner or with two.

**The rule of every step.** A step takes the ledger rows it owns and, before it is done, gives
each a fate in its own `tests/ledger/fates/STEP.tsv` (`id fate proof note`). Every fate
names its test or trial check. A changed or dropped row also needs a reason. `close` checks
that each named proof passed. A row a step cannot place goes into its report with why, never
silently away. A dropped `ruling` row goes on the owner's list. `check.py` reads the last full
run and the trial files. Each `path` row names its proof owner in `landing.md` E.

**Seams: behavior no other kind shows** (`extra.tsv`, kind `seam`).

| Id | Behavior | Source | Owner |
| --- | --- | --- | --- |
| `seam:forge-look-fails` | one workspace's failed look at the forge is shown on its board, and its sessions, duties and prune still run, and so does the next workspace's tick | `serve.forge_loop`, first `try` | `board-duties` |
| `seam:duties-fail` | a failed sessions look or duty is shown on its board; its prune and the next workspace still run | `serve.forge_loop`, second `try` | `board-duties` |
| `seam:prune-fails` | a failed prune is one log line; the next workspace still runs | `serve.forge_loop`, third `try` | `board-duties` |
| `seam:alike-read-list` | with Jev not asked, `land alike` gives the `read` list (path, title, place, worth) that the fast-track builder reads before it files | `land.cmd_alike`, `prompts/small.md` step 7 | `land-review` |
| `seam:pr-text-edit-fails` | after a failed forge edit of the pull request's text, the board shows the last confirmed text and a line that a newer text waits; `merged` retries the edit. Today the board shows the draft (`land.noted` writes `pr.md` first): changed | `land.noted`, `artifacts.py` (`pr.md`) | `land-merge` |
| `seam:step-lock-not-inherited` | a process a step starts does not hold the step lock, so a server started from a step never blocks the task | `land.step_lock` | `core` |
| `seam:hooks-on-mismatch` | on an app and plugin version mismatch every hook but `session-start` does nothing and says nothing; `session-start` says one line | `hooks.py` | `sessions` |
| `seam:other-lem` | `session-start` compares the first `lem` on the path by identity and never runs it | `hooks.other_lem` | `sessions` |

## 9. The build order

**Where and how.** Branch `rebuild`, cut from `main` at `b712855d` (this plan's commit, on
`bf6d2836`, the commit that joined the last stage 3 pieces). Each step is a worktree off `rebuild`, merged by the orchestrator; every
builder reads `2026-11-25-lem-built-again/builder-rules.md`. Step ids are frozen: a later change
adds a step and renumbers none. Within a group the files are disjoint; a file passes from an
earlier step to the step that owns it later. A step that needs a change in a file it does not own
writes `2026-11-25-lem-built-again/notes/STEP.md`, builds against a fixture, and the file's owner
applies it. Each step writes its own `tests/ledger/fates/STEP.tsv`. A step is done when its
verify passes after its review's changes, every selection collected cases, and its fates cover
its rows. **Default where a gate needs a `noqa` or a package is over 1.5 times its size:** the
orchestrator sends the step back once to split it, puts it on the owner's list, and goes on; the
owner is away, and only `cutover` waits for him [decided]. A builder runs `gates`, `unit`,
`model`, `contract`, `hooks` and its own journeys; `full` runs only in `journeys` and `close`.

`T LEVEL PATHS` below is `.venv/bin/python -I -B tests --level LEVEL PATHS`.

**The text agreed first.** `core`'s first commit holds these files, word for word as here, and
is merged into `rebuild` at once; `tree` starts from it, and both briefs quote it.

`src/lem/kernel/errors.py`:

```python
"""What a command of Lem ends with when it does not succeed."""


class Refusal(Exception):
    """A step that may not run now: a short code, why, and the fix that names the way on."""

    def __init__(self, code: str, why: str, fix: str) -> None:
        """Keep the three parts of the refusal."""
        super().__init__(why)
        self.code = code
        self.why = why
        self.fix = fix


class Fault(Exception):
    """A failure of Lem itself: its traceback goes to `lem.log`, the owner reads one line."""
```

`src/lem/kernel/envelope.py`:

```python
"""The one JSON document every command prints."""

from typing import Literal

import msgspec

type Act = Literal["run", "spawn", "wait", "tell", "done"]


class Next(msgspec.Struct, frozen=True, kw_only=True, omit_defaults=True):
    """What comes next: a command to run, a builder's job, a wait, a line, or the end."""

    act: Act = msgspec.field(name="do")
    command: str | None = None
    job: str | None = None
    paths: tuple[str, ...] = ()
    until: str | None = None
    line: str | None = None
    why: str | None = None


class Refused(msgspec.Struct, frozen=True, kw_only=True):
    """A refusal as printed: exit 1."""

    code: str
    why: str
    fix: str


class Failed(msgspec.Struct, frozen=True, kw_only=True):
    """A fault as printed: exit 3."""

    line: str
    log: str


class Envelope(msgspec.Struct, frozen=True, kw_only=True, omit_defaults=True):
    """`ok`, then the outcome, a line for the owner, and what comes next."""

    ok: bool
    outcome: msgspec.Raw | None = msgspec.field(default=None, name="result")
    say: str | None = None
    following: Next | None = msgspec.field(default=None, name="next")
    refusal: Refused | None = None
    fault: Failed | None = None
```

The two entry lines of `pyproject.toml`:

```toml
[project.scripts]
lem = "lem.__main__:main"
lem-hook = "lem.hooks.main:main"
```

`src/lem/__main__.py` is the wrapper of part 5 (help and version, the version check, the server
start, `NO_LOOK`), then `sys.exit(lem.cli.lazy.main(sys.argv[1:]))`. `lem.cli.lazy.main(argv:
list[str]) -> int` returns the exit code; the first commit has it as a stub that `tree` owns from
its start. `src/lem/hooks/main.py` is a stub that exits 0 with no output. `tests/__main__.py`
and `tests/conftest.py` are the runner of part 8, from `main`'s `tests/unit/__main__.py`.

**Group 0, at the same time** (`tree` after `core`'s first commit)

| Id | Builds, and owns | Needs | Verify | Who; review |
| --- | --- | --- | --- | --- |
| `ledger` | `tests/ledger/` but `fates/`: `ledger.py`, `rows.tsv`, `extra.tsv` (the `path` and `seam` rows), `owners.py`, `owners.tsv`, `check.py`; exempt from `core`'s removal of `tests/`. `owners.py` places, by id, the rows its rules cannot: `command:lem land alike` → `land-review`; `route:GET /{host}/{workspace}/stream` → `board-pages` (the owner of `stream.py`); `ruling:a-correction-hook-registered-twice-judges-ea-f309bf034a652b95` → `sessions`; `act:Question card/replay-tune` → `ask`; `event:builder.start` → `task`; `guide:docs/settings.md` → `settings` | nothing | `ledger.py` twice on `bf6d2836`, the outputs equal byte for byte; `--counts` equals the kinds above; `owners.py` exits 0 (no row with none or two) | Sol; Opus |
| `core` | `pyproject.toml` (packaging from `main`: hatchling, `lem/data`, `cache-keys`, `checkout.pth`, `hatch_build.py`, the two scripts), `uv.lock`, gate configs, `.github/workflows/ci.yml`, `.claude-plugin/plugin.json`, `src/lem/__main__.py`, `kernel/`, `records/` (all of part 3, `landing.md` A and I), `store/`, `ports/`, `app/wiring.py`, `src/lem/hooks/main.py` (stub), `tests/__main__.py`, `tests/conftest.py`, `tests/fakes/`, `tests/unit/core/`, `tests/contract/` (each port's suite, run against the fakes); removes the old `src/lem` and `tests/` but `tests/ledger/` | nothing | `T gates`; `T unit tests/unit/core/`; `T contract tests/contract/` (fakes) | Opus; Astra |
| `tree` | `src/lem/cli/` (lazy, nouns, output, version, every `verbs.py`, every leaf as a stub with its params from `surfaces.md` A); the old-form mark on every file the stage-line test reads; `tests/unit/cli/` | `core`'s first commit | `T unit tests/unit/cli/` (`lem help`, every lazy path imports, every `lem` line parses or its file is marked) | Opus; Sol |

**Group 1, at the same time.** Each makes slice versions that group 2 owns later. What trials S4
to S6 need is here in a minimal form. Each slice verifies with the fakes of group 0 for the
ports of the other slices. The three own disjoint files.

| Id | Builds, and owns | Needs | Verify | Who; review |
| --- | --- | --- | --- | --- |
| `slice-land` | a fast-track task from `task open` to `landed`, each landing step plain, real git and `LocalForge`: `model/landing/*`, `app/landing/*`, `cli/land/*`, `cli/task/{open,read,worktree,move}.py`, `cli/criteria/{approve,record}.py`, `cli/settings/show.py`, `app/tasks/`, `app/criteria/{approve,record}.py`, the slice settings reader (`settings/{team,places,load}.py`), slice `git_cli`, `forge_gh`; texts `SKILL.md`, `stages/new.md`, `stages/land.md`, `prompts/small.md` (fast track only); tests `tests/journeys/test_skeleton.py`, `tests/contract/test_forge_gh_slice.py` | group 0 | `T journeys tests/journeys/test_skeleton.py`; `T contract tests/contract/test_forge_gh_slice.py` | Opus; Astra |
| `slice-board` | `board/{app,server,stream}.py`, every route module and duty path as a stub, the stub `addons/peers/routes.py` (until `addons-outside`), one kanban page from the scratch workspace's records, `cli/serve/{ensure,stop,run}.py` (`serve run` on an explicit scratch port, with the automatic start off), `cli/board/`; tests `tests/unit/board/test_slice.py`, `tests/journeys/test_server_slice.py` | group 0 | `T unit tests/unit/board/test_slice.py`; `T journeys tests/journeys/test_server_slice.py` | Opus; Sol |
| `slice-session` | `hooks/hooks.json`, `hooks/run` (from `main`), `src/lem/hooks/` (the five selectors, slice), `cli/session/{open,next,close,list}.py`, `app/sessions/`, slice `terminal_agterm`, `harness_claude`; text: the fast path of `skills/lem/prompts/session.md`; tests `tests/hooks/test_slice.py`, `tests/contract/test_terminal_slice.py` | group 0 | `T hooks tests/hooks/test_slice.py`; `T contract tests/contract/test_terminal_slice.py` | Opus; Astra |

**Group 2, at the same time** (one trial and nine builders). The landing steps' journeys run on
the slice versions of the other stages and need no stage text.

| Id | Builds, and owns | Needs | Verify | Who; review |
| --- | --- | --- | --- | --- |
| `trial-skeleton` | a scratch tap with a formula of `rebuild`; `2026-11-25-lem-built-again/trials/skeleton.md`. Checks: S1 `brew install --build-from-source --skip-link` from the scratch tap; S2 `lem version` from the formula's path; S3 `forge_gh`'s contract suite against a scratch GitHub repository; S4 `session-start` through `hooks/run` writes `LEM_PLUGIN_ROOT`, with `LEM_HOOK_BIN` set to the scratch formula's absolute `lem-hook`; S5 a fast-track task from `/lem` to a merged PR in that repository, in a session that loads the matching scratch plugin; S6 the board (`serve run` on a scratch port) shows it. In S4 and S5 the formula's commands come first on the session's `PATH`; S7 the owner's running server of release 0.3.1 (ports 4536, 4537) untouched | group 1 | S1 to S7 passed in the file | Session; Sol |
| `land-base` | `model/landing/{start,base,carry}.py`, `app/landing/{start,base}.py`, `cli/land/{start,base}.py`, `adapters/git_cli.py`; tests `tests/unit/landing/test_{start,base,carry}.py`, `tests/contract/test_git.py`, `tests/journeys/landing/test_base.py` | group 1 | `T unit tests/unit/landing/test_start.py tests/unit/landing/test_base.py tests/unit/landing/test_carry.py`; `T contract tests/contract/test_git.py`; `T journeys tests/journeys/landing/test_base.py` | Opus; Astra |
| `land-checks` | `model/landing/{checks,bar}.py`, `app/landing/{polish,checks_gate,checks_run,checks_tree,checks_criteria}.py`, `cli/land/{polish,checks}.py`, `cli/serial/`, `cli/criteria/{red,inputs}.py`; tests `tests/unit/landing/test_{checks,bar}.py`, `tests/journeys/landing/test_checks.py` | group 1 | `T unit tests/unit/landing/test_checks.py tests/unit/landing/test_bar.py`; `T journeys tests/journeys/landing/test_checks.py` | Opus; Sol |
| `land-review` | `model/landing/{review,filing}.py`, `app/landing/{review,filing}.py`, `cli/land/{read,file,alike}.py`, `adapters/judge_jev.py`; tests `tests/unit/landing/test_{review,filing}.py`, `tests/journeys/landing/test_review.py` | group 1 | `T unit tests/unit/landing/test_review.py tests/unit/landing/test_filing.py`; `T journeys tests/journeys/landing/test_review.py` | Opus; Astra |
| `land-propose` | `model/landing/{green,propose}.py`, `app/landing/{propose,pr_text}.py`, `cli/land/propose.py`, `adapters/forge_gh.py`, the PR template; tests `tests/unit/landing/test_{green,propose}.py`, `tests/contract/test_forge.py`, `tests/journeys/landing/test_propose.py` (its end-to-end proof) | group 1 | `T unit tests/unit/landing/test_green.py tests/unit/landing/test_propose.py`; `T contract tests/contract/test_forge.py`; `T journeys tests/journeys/landing/test_propose.py` | Opus; Astra |
| `land-merge` | `model/landing/{phases,mergeread,merge,reconcile,clean,invariants}.py`, `app/landing/{mergeread,merge,reconcile,merged,clean,next}.py`, `cli/land/{merge_review,merge,merged,clean,next}.py`; tests `tests/unit/landing/test_{phases,mergeread,merge,reconcile,clean,invariants}.py`, `tests/journeys/landing/test_merge.py` | group 1 | `T unit tests/unit/landing/test_phases.py tests/unit/landing/test_mergeread.py tests/unit/landing/test_merge.py tests/unit/landing/test_reconcile.py tests/unit/landing/test_clean.py tests/unit/landing/test_invariants.py`; `T journeys tests/journeys/landing/test_merge.py` | Opus; Astra |
| `task` | `model/task/`, `app/tasks/`, `cli/task/`, `cli/issue/`, `adapters/tracker_github.py`, the release stop, the claim; texts `stages/{new,start,park,correct,investigate}.md`, `prompts/{investigator,scout}.md`, `skills/{lem-github,lem-linear}/`, `harness/claude-code/tracker.md`; tests `tests/unit/task/` | group 1 | `T unit tests/unit/task/` | Opus; Sol |
| `criteria` | `model/{criteria,decisions}/`, `app/{criteria,decisions}/`, `cli/{criteria,decisions}/` but `red` and `inputs`; texts `stages/{interview,plan,build,talk,ladder,breaker}.md`, `prompts/{lead,defender,reviewer,writing}.md`, `templates/{handoff,breaker}.md`, `agents/lem-builder.md`, `skills/{lem-gate,lem-interview-me,lem-dialectic,lem-root-cause}/`; tests `tests/unit/criteria/` | group 1 | `T unit tests/unit/criteria/` | Opus; Sol |
| `sessions` | `adapters/{terminal_agterm,harness_claude}.py`, `app/sessions/`, `cli/{session,seat}/`, `src/lem/hooks/`, `hooks/hooks.json`, `hooks/run`; texts `prompts/session.md`, `harness/README.md`, `harness/claude-code.md`, `harness/claude-code/{task-session,plan-talk,second-opinion}.md`, `harness/claude-code/reviewer-guard.json`; tests `tests/unit/sessions/`, `tests/contract/test_{terminal,harness}.py`, `tests/hooks/` (with the correction queue's write) | group 1 | `T unit tests/unit/sessions/`; `T contract tests/contract/test_terminal.py tests/contract/test_harness.py`; `T hooks tests/hooks/` | Opus; Astra |
| `settings` | `settings/`, `cli/{settings,doctor,init,path,rules}/`, `app/init/`, `docs/settings.md`; texts `stages/init.md`, `harness/claude-code/{onboarding,owner-steps}.md`, `templates/{profile,persona}.md`; tests `tests/unit/settings/` | group 1 | `T unit tests/unit/settings/` | Opus; Sol |

**Group 3, at the same time**

| Id | Builds, and owns | Needs | Verify | Who; review |
| --- | --- | --- | --- | --- |
| `land-text` | `stages/{land,polish,conflict}.md`, `prompts/{landing,review,merge,small}.md`, `harness/claude-code/{ask-merger,review-tool}.md`, `tests/model/`, `tests/histories/`; applies the notes of the landing steps | group 2 | `T model tests/model/`; `T histories tests/histories/`; `T journeys tests/journeys/landing/`; coverage of `model/landing` 100% | Opus; Astra, Sol |
| `owner` | `model/owner/`, `app/owner/`, `cli/{owner,waiting}/`; texts `SKILL.md`, `stages/{status,away}.md`; applies the notes of group 2 to `SKILL.md`; tests `tests/unit/owner/` | `task`, `criteria` | `T unit tests/unit/owner/` | Opus; Sol |
| `board-inputs` (new) | `board/inputs/` (a typed struct per page section), `tests/fixtures/board/` (today's showcase afternoon of `tests/board-showcase.py`, as typed inputs); tests `tests/unit/board/inputs/` | group 2 | `T unit tests/unit/board/inputs/` | Opus; Sol |

**Group 4, at the same time.** `board-pages` and `board-views` meet only at `board/inputs/`; the
shared fixture lets the templates be tested before the views are whole. The three old modules
they replace have 16,421 lines (`wc -l src/lem/board_{pages,task,model}.py`).

| Id | Builds, and owns | Needs | Verify | Who; review |
| --- | --- | --- | --- | --- |
| `board-views` | `board/views/`; tests `tests/unit/board/views/` (records and model outputs to inputs) | `owner`, `board-inputs` | `T unit tests/unit/board/views/` | Opus; Sol |
| `board-pages` (new) | `board/pages/`, `board/templates/`, `board/stream.py`, `skills/lem/assets/`, `tools/board-kit/`, `package.json`, `eslint.config.mjs`; tests `tests/unit/board/pages/` (each page rendered from the fixture) | `board-inputs` | `T gates`; `T unit tests/unit/board/pages/` | Opus; Sol |
| `board-acts` | `board/acts/`, `harness/claude-code/{show-page,take-screenshot}.md`; tests `tests/unit/board/acts/`, `tests/journeys/test_acts.py` | `owner` | `T unit tests/unit/board/acts/`; `T journeys tests/journeys/test_acts.py` | Opus; Astra |
| `board-duties` | `board/duties/`, `store/retention.py`, `cli/prune/`; tests `tests/unit/board/duties/`, `tests/journeys/test_duties.py` (the three seams of `forge_loop`) | `owner` | `T unit tests/unit/board/duties/`; `T journeys tests/journeys/test_duties.py` | Opus; Astra |
| `board-service` | `board/{app,server,door}.py`, `board/push/`, `adapters/notify_push.py`, `cli/serve/` but the peers leaves, `cli/board/`; tests `tests/unit/board/service/`, `tests/journeys/test_server.py` | `owner` | `T unit tests/unit/board/service/`; `T journeys tests/journeys/test_server.py` | Opus; Sol |

**Group 5, at the same time**

| Id | Builds, and owns | Needs | Verify | Who; review |
| --- | --- | --- | --- | --- |
| `ask` | `board/ask/`, `cli/ask/`, `skills/lem-ask/`, `harness/claude-code/ask-owner.md`; tests `tests/unit/ask/`; trial A1 in `trials/ask.md`: a card in a real agterm overlay, answered there and on the board (else the file fallback) | group 4 | `T unit tests/unit/ask/`; A1 passed | Opus, then Session; Sol |
| `addons-flow` | `addons/{proposals,corrections,naps,picker}/`, their `cli/` packages; texts `stages/{night,learn,nap}.md`, `prompts/{proposals,nap}.md`, `harness/claude-code/{correction-hook,start-nap}.md`; tests `tests/unit/addons/flow/` (it reads the queue the hook's fixture writes) | group 4 | `T unit tests/unit/addons/flow/` | Opus; Sol |
| `addons-outside` | `addons/{experts,cast,inbox,peers,jev}/` (`lem.addons.peers.routes` among them), their `cli/` packages, `cli/serve/{join,leave,peers}.py`; texts `skills/{lem-ask-expert,lem-panel}/`, `harness/claude-code/ask-experts.md`; tests `tests/unit/addons/outside/`, `tests/journeys/test_peers.py` | group 4 | `T unit tests/unit/addons/outside/`; `T journeys tests/journeys/test_peers.py` | Opus; Astra |

**Groups 6 to 12, one step at a time but group 6**

| Id | Builds, and owns | Needs | Verify | Who; review |
| --- | --- | --- | --- | --- |
| `journeys` | `tests/journeys/` beyond the steps' own files: both tracks end to end, park, resume, drop, the night | group 5 | after both group 6 steps merged: `T full`; every `kept` or `changed` row of kinds `path`, `check`, `act`, `seam` whose proof is a test has passed | Opus; Astra |
| `browser` (with `journeys`) | `tests/browser/`, `assets/screens/` | group 5 | `T browser`, no skip | Sol; Opus |
| `guides` | the public files only: `README.md`, `docs/{flow,when-lem-needs-you,pull-request,board,install,linear,github-issues}.md`, `site/`, `.github/workflows/pages.yml`, `AGENTS.md`; tests `tests/unit/guides/` | `journeys`, `browser` | `T unit tests/unit/guides/` (the `lem` lines, links, the site's copy step) | Opus; Sol |
| `pack-trial` | the tap branch of `pySilver/homebrew-tap`, `.claude-plugin/marketplace.json`, `trials/pack.md`. Checks: P1 the tagged formula and the marketplace plugin together, `--skip-link`, own home; P2 the version line both ways; P3 a GUI-started Claude Code reaches `lem-hook`; P4 p95 for each selector at most 55 ms; P5 `lem doctor` with every required row found; P6 the read-outside question once, then its allow rule | `guides` | P1 to P6 passed | Session; Sol |
| `mutation` | the tests that `mutmut` over `model/landing` shows missing | `pack-trial` | no surviving mutant without a test | Sol runs, Opus writes; Astra |
| `trials` | `trials/real.md`. Checks: R1 the standard track with interview, criteria, persona read, plan and talk; R2 a breaker, help, park, drop; R3 a conflict between two tasks; R4 a moved base, safe and another round; R5 a stop on each side of the forge's merge call and a lost reply, with the count of merge calls across the stop and the reconcile, and a stop in the checks; R6 the phone through the door, a card and a merge; R7 two servers joined; R8 a night task to its PR; R9 a task on a scratch copy of a real project | `mutation` | R1 to R9 passed; a defect becomes a new step | Session; Sol, Astra |
| `close` | `tests/ledger/fates/close.tsv` (the rows of the maintaining session's choices) | `trials` | `T full` once; `check.py` finds every row owned and fated, and each named proof passed (a test or a trial check); no old-form mark | Sol; Opus |
| `cutover` | part 10 | `close` | the owner's word | The owner builds and reviews |

**Ledger ownership.** `owners.py` assigns by this table and the by-id list of `ledger`; it
refuses a row with no owner or with two.

| Step | Old sources | Old tests |
| --- | --- | --- |
| `core` | `clock.py`, `files.py`, `proc.py`, `state.py`, `paths.py`, `python.py` (dropped), `release.py` (the release field) | `test_clock`, `test_files`, `test_proc`, `test_state`, `test_paths`, `test_unit_runner`, `test_release`; `lint.sh`, `shellcheck.sh`, `checks.sh`, `suites.sh`, `all.sh`, `test-lem.sh`, `lib.sh`, `python.sh` (the framework: dropped, its proof in the new entry) |
| `tree` | `__main__.py` (dispatch, help, version), `names.py`, `sibling.py` | `test_commands`, `test_command_lines`, `test_sibling`; `lem-command.sh` |
| `land-base` … `land-merge` | `land.py` by function: start, base, carry, cover → `land-base`; polish, checks, gate, load, serial, criteria red and inputs, the bar → `land-checks`; read, file, alike, due, Jev → `land-review`; propose, PR text, green, notes, section → `land-propose`; merge review, merge, merged, forge done, noted, moved line, follow, clean, after push, forge copy → `land-merge` | `test_land` by the class's function; `test_land_text` → `land-propose`; `test_the_bar` → `land-checks`; `lem-land-guards.sh` → `land-base`; `lem-serial.sh` → `land-checks`; `lem-land-review.sh`, `lem-land-backlog.sh` → `land-review`; `lem-land-local.sh`, `lem-land-github.sh` → `land-propose`; `lem-land-shop.sh` → `land-merge`; `lem-land-small.sh` → `land-text` |
| `task` | `project.py` (tasks, state, claims, tickets, resume, may-start, log), `plans.py`, `issues.py` | `test_task`, `test_task_rules`, `test_issues`; `lem-state.sh` |
| `criteria` | `criteria.py`, `decisions.py` | `test_criteria`, `test_criteria_change`, `test_decisions`; `lem-decisions.sh` |
| `sessions` | `session.py`, `session_hook.py`, `hooks.py`, `serve_hook.py`, `signs.py`, `tokens.py`, `hooks/` | `test_session`, `test_hooks`, `test_signs`, `test_tokens`; `lem-session.sh` |
| `settings` | `project.py` (settings, places, rules, load, handoff, set, init), `doctor.py` | `test_settings`, `test_settings_files`, `test_rule_picker`, `test_doctor`; `lem-settings.sh`, `lem-machine.sh` |
| `owner` | `project.py` (owner, waiting) | `test_owner` |
| `board-views` | `board_model.py`, `artifacts.py` | `test_board_model` |
| `board-pages` | `board_pages.py`, `board_task.py`, `markup.py` | `test_board_pages`, `test_board_task`, `test_markup` |
| `board-acts` | `answers.py`, `serve.py` (`act_*`, jump) | `test_board_answers`, `test_board_criteria_change`; `lem-board-act.sh` |
| `board-duties` | `serve.py` (`forge_loop`, duties, guard, forge, prune), `project.py` (prune, summary) | `test_serve` (duty classes) |
| `board-service` | `serve.py` (the rest), `board.py`, `push.py`, `__main__.py` (`look_for_server`) | `test_serve` (the rest), `test_board`, `test_push`; `lem-serve.sh` |
| `ask` | `ask.py`, `cards.py` | `test_ask`, `test_cards`, `test_serve_cards`; `test-ask.sh` |
| `addons-flow` | `corrections.py`, `picker.py`, `project.py` (proposals, may-nap) | `test_corrections`, `test_picker`, `test_proposals`, `test_backlog`; `lem-naps.sh`, `lem-picker.sh` |
| `addons-outside` | `experts.py`, `cast.py`, `inbox.py`, `peers.py`, `jev.py` | `test_experts`, `test_cast`, `test_inbox`, `test_peers`, `test_jev`; `test-ask-expert.sh`, `test-gate-panel.sh`, `lem-peers.sh` |
| `browser` | `board-cdp.mjs` | `lem-board-keys.sh` |
| `guides` | `README.md`, the public guides, `site/` | `test_agents_md`; `test-site.sh` |

`text` rows belong to the step that owns the file. `route`, `act`, `duty`, `event` and `refusal`
rows belong to the owner of their handler's source above. `path` rows go to the landing step that
owns their row of `landing.md` E; `seam` rows as their table says. `ruling` rows by their group:
"What Lem is" and "README, guides and logo" → `guides`; "What Lem needs on the machine" and
"settings, seats, tracker" → `settings`; "A request" → `task`; "interview, criteria, personas",
"plan, build, tests" and "A decision without him" → `criteria`; "review, PR, merge" →
`land-text`; "A task's session" → `sessions`; "The board" → `board-views`; "lessons, corrections,
naps, night" → `addons-flow`; "Choices of the maintaining session" → `close`; a line of
`docs/rulings/history.md` → the owner of the test or place it names.

**All steps, in order** (the orchestrator ticks this list).

| # | Id | Group | Needs | Builds | Reviews | Verify |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `ledger` | 0 | nothing | Sol | Opus | two equal runs; `owners.py` exits 0 |
| 2 | `core` | 0 | nothing | Opus | Astra | `gates`, `unit tests/unit/core/`, `contract tests/contract/` |
| 3 | `tree` | 0 | `core`'s first commit | Opus | Sol | `unit tests/unit/cli/` |
| 4 | `slice-land` | 1 | group 0 | Opus | Astra | `journeys .../test_skeleton.py`, `contract .../test_forge_gh_slice.py` |
| 5 | `slice-board` | 1 | group 0 | Opus | Sol | `unit tests/unit/board/test_slice.py`, `journeys tests/journeys/test_server_slice.py` |
| 6 | `slice-session` | 1 | group 0 | Opus | Astra | `hooks .../test_slice.py`, `contract .../test_terminal_slice.py` |
| 7 | `trial-skeleton` | 2 | group 1 | Session | Sol | S1 to S7 |
| 8 | `land-base` | 2 | group 1 | Opus | Astra | its unit, contract and journey files |
| 9 | `land-checks` | 2 | group 1 | Opus | Sol | its unit and journey files |
| 10 | `land-review` | 2 | group 1 | Opus | Astra | its unit and journey files |
| 11 | `land-propose` | 2 | group 1 | Opus | Astra | its unit, contract and journey files |
| 12 | `land-merge` | 2 | group 1 | Opus | Astra | its unit and journey files |
| 13 | `task` | 2 | group 1 | Opus | Sol | `unit tests/unit/task/` |
| 14 | `criteria` | 2 | group 1 | Opus | Sol | `unit tests/unit/criteria/` |
| 15 | `sessions` | 2 | group 1 | Opus | Astra | its unit, contract and hooks files |
| 16 | `settings` | 2 | group 1 | Opus | Sol | `unit tests/unit/settings/` |
| 17 | `land-text` | 3 | group 2 | Opus | Astra, Sol | `model`, `histories`, `journeys tests/journeys/landing/`, coverage |
| 18 | `owner` | 3 | `task`, `criteria` | Opus | Sol | `unit tests/unit/owner/` |
| 19 | `board-inputs` | 3 | group 2 | Opus | Sol | `unit tests/unit/board/inputs/` |
| 20 | `board-views` | 4 | `owner`, `board-inputs` | Opus | Sol | `unit tests/unit/board/views/` |
| 21 | `board-pages` | 4 | `board-inputs` | Opus | Sol | `gates`, `unit tests/unit/board/pages/` |
| 22 | `board-acts` | 4 | `owner` | Opus | Astra | its unit and journey files |
| 23 | `board-duties` | 4 | `owner` | Opus | Astra | its unit and journey files |
| 24 | `board-service` | 4 | `owner` | Opus | Sol | its unit and journey files |
| 25 | `ask` | 5 | group 4 | Opus, then Session | Sol | `unit tests/unit/ask/`, A1 |
| 26 | `addons-flow` | 5 | group 4 | Opus | Sol | `unit tests/unit/addons/flow/` |
| 27 | `addons-outside` | 5 | group 4 | Opus | Astra | its unit and peers journey |
| 28 | `journeys` | 6 | group 5 | Opus | Astra | `full`, after `browser` merged |
| 29 | `browser` | 6 | group 5 | Sol | Opus | `browser`, no skip |
| 30 | `guides` | 7 | group 6 | Opus | Sol | `unit tests/unit/guides/` |
| 31 | `pack-trial` | 8 | `guides` | Session | Sol | P1 to P6 |
| 32 | `mutation` | 9 | `pack-trial` | Sol, Opus | Astra | no surviving mutant without a test |
| 33 | `trials` | 10 | `mutation` | Session | Sol, Astra | R1 to R9 |
| 34 | `close` | 11 | `trials` | Sol | Opus | `full`; `check.py`; no old-form mark |
| 35 | `cutover` | 12 | `close` | the owner | the owner | his word |

## 10. The cutover

`rebuild` removes the old `src/lem` and `tests/` (but `tests/ledger/`) in `core`; they stay
readable with `git show main:PATH`. `main` takes fixes only, each with a ledger row [decided]. On
the owner's word: merge `rebuild` into `main`; release 1.0.0 as `AGENTS.md` "A release" says;
wipe from a list what 0.3 left (each repository's `.lem/state/` and worktrees, Lem's home folder,
the running server); `brew upgrade` and the marketplace update; the scratch repository, then
mybaze.

## 11. Choices, decided

Each was decided by the maintaining session while the owner was away, and is open to him.

1. **`main` during the rebuild takes fixes only** [decided, pair-settled]. Other way: features
   on `main`, each ported to `rebuild`.
2. **Question pages are served if trial A1 passes; the file fallback is kept** [decided]. Other
   way: always rendered to a file.
3. **The real-project trial runs on a scratch copy** [decided]. Other way: a real task in
   mybaze, an outward act on his repository while he is away.
4. **A drop during a landing step takes the step lock** [decided]: it stops running checks,
   takes the lock, rereads, and refuses when the forge merged meanwhile. Other way (the writer's
   turn 3): today's drop with no lock, which can write `dropped` over a merged pull request.
5. **The hook budget is about 50 ms, failing over 55 ms at p95 for each selector** [decided].
   Other way: a hard 50 ms.
