# Notes of the step `settings` for other steps

What the settings give, what `settings` needs in files it does not own, and the local stand-ins
it built until each exists.

## Every step: how to read a setting

- `lem.settings.load.settings_of(checkout, environ) -> Loaded`: every value in force
  (`Loaded.settings`, an `Effective` struct with every table) and the file of each
  (`Loaded.sources`, `"table.key" -> name`). `checkout` is `store.places.workspace(...).checkout`,
  or None outside a repository where Lem is set up. The team's file is the main checkout's while
  it is on the base branch, else the base's newest commit (`settings/base.py`, through the `Git`
  port's `show`), so a task's worktree reads the same settings and a branch cannot lift a rule.
- `lem.settings.load.team_of(checkout) -> Team` and `base_of(team)` keep the slice's form; `Team`
  now holds every table of the team's file (`paths`, `branch`, `checks`, `flow`, `seats`,
  `tracker`, `naps`, `state`, `jev`).
- `lem.settings.load.machine_of(environ) -> Machine`: `load.start` (0.0 is no gate), `serve`
  (`port`, `tailscale`, `tailscale_port`), `peers` (`host -> port`), `handoff.tokens` (0 sets
  nothing: Claude Code's own trigger), `corrections.collect`.
- A seat is a string; `lem.settings.seats.split(line)` gives its `agent`, `model`, `effort`.
  `seats.fallback` is `False` when it is off. `lem.settings.experts.experts_of(seats, environ)`
  gives each expert with its `place` and whether its agent is on the machine (`here`).
- A write of one setting: `lem.settings.write.set_setting(Asked(key, word, scope, folder,
  environ))`, the same as `lem settings set KEY WORD --local|--home|--machine`. It imports
  tomlkit, so a leaf imports `lem.settings.write` only in its `run` (`importlib`), as
  `cli/settings/set.py` does (`HEAVY` of `tests/unit/cli/test_tree.py`).

## For `board-service` (`board/machine.py`) and `addons-outside` (`cli/serve/{join,leave}.py`)

`board/machine.py: settings(home)` reads `[serve]` with `tomllib` into its own `Serve`. It gives
way to `lem.settings.load.machine_of(environ).serve`, with the same defaults (4536, 4537, false)
and the same port range; the guard of the owner's two ports stays where the port is read. The
door's switch and the ports are written with `set_setting(Asked(key="serve.tailscale",
word="on"|"off", scope=Scope.machine, ...))` and `serve.port`, `serve.tailscale_port`; a peer's
line with `key="peers.HOST"`, and `word="default"` takes it out. Every such write goes through
`folders.home_for_writing` inside `write.py`.

## For `sessions`

- The launch line wants `seats.session` and `handoff.tokens` (`notes/slice-session.md`, item 9):
  `settings_of(checkout, environ).settings.seats.session` and `.handoff.tokens`.
- `seat failed`'s fallback: `.settings.seats.fallback` (False: off).
- The correction hook reads `[corrections] collect` of `machine.toml` with `tomllib` alone; the
  key and its file are unchanged, and `settings show` refuses a value that is no bool there
  (`test_a_wrong_value_of_the_machines_file_is_refused_with_its_fix`). The hook rows of
  `lem-machine.sh` are given to you in `tests/ledger/moves/settings.tsv`.

## For `task`

- The onboarding (`stages/init.md`) opens with `lem task open onboarding --ask "Set up Lem in this
  repository"` and ends with `lem task move onboarding landed --line "main is at COMMIT: ..."`
  from `shaping`. The design's part 3 lets `landed` follow `open` only: the onboarding needs a
  way to end that the table takes (a word of `task move`, or `answered`), and the stage's line
  follows it.
- `task plan-file` reads `paths.plan_file` from `team_of(checkout).paths`; its rules are
  `lem.settings.checked.pattern_flaw`, checked at every load.

## For `core`

1. **Origin's address, a `GitPlaces` fact.** `lem init` refuses an origin that is not on GitHub
   and tells a repository with none to add one. `app/init/origin.py` runs `git config --get
   remote.origin.url` itself until the port has `origin_url(where) -> str | None`.
2. **The main checkout where Lem is not set up yet.** `store.places.workspace` refuses `no-lem`,
   which `lem init` cannot use. `app/init/checkout.py` copies its walk up to `.git` and its
   `common_dir`; a `places.checkout_of(folder)` that `workspace` calls would hold the rule once.
3. **The changed paths of a range.** `lem rules --range` needs `git diff --name-only --no-renames
   -z RANGE`; `diff_stat` gives git's short form of a move and quoted names, which
   `cli/rules/renames.py` unfolds meanwhile. Asked: a fact `changed_paths(where, since, until)`.
4. **A home folder the owner made by hand.** `folders.form` reads a home that holds a
   `machine.toml` and no marker as the Lem before's, so a developer who writes `machine.toml`
   into a new home before any Lem write is refused `old-state` by `settings set --machine` (seen
   in this step's tests, which mark the home first). Whether that is the rule you want is yours.
5. **The test entry and a file that fails to collect.** While `test_set.py` had two cases of one
   id, the run printed `total: collected 110, passed 110` and no failure, with the file's 36
   cases left out; `collection failed` stood only in the log. A selection whose file fails to
   collect should fail the run (the design's part 8).

## For the text owners of `SKILL.md`, `stages/`, `prompts/`, `skills/lem-*`

`lem settings show` prints `settings` (every table), `from` (the file of each `table.key`),
`seats` (each seat's parts), `experts` (with `place` and `here`), `places` and `load`. A text that
read `lem project show`'s `tracker`, `flow.topics`, `checks.serial`, `corrections.from` or a seat's
`agent` reads `settings.tracker`, `settings.flow.topics`, `settings.checks.serial`,
`from["corrections.collect"]` and `seats.reviewer.agent`. `lem corrections collect yes|no` is
`lem settings set corrections.collect yes|no --machine`; `lem project set local NAME VALUE` is
`lem settings set seats.NAME VALUE --local`.
