# Standing rules for a builder of the rebuild

You build one step of "Lem, built again". The orchestrating session gave you a step id, a
worktree and a branch. These rules hold in every step; your step's brief adds the rest.

## What you read first

1. `docs/plans/2026-11-25-lem-built-again.md` in your worktree: the design. Read parts 2, 3 and
   9 whole, and the part your step builds. Its annexes are in the folder of the same name
   (`landing.md`, `surfaces.md`): read the rows your step names.
2. `AGENTS.md` of your worktree ("Rules for a change here") and `docs/rulings/rulings.md`.
   `AGENTS.md` still describes the proof of concept until the step `guides` rewrites it. Where
   it and the design disagree, the design holds: libraries, not standard-library scripts (the
   owner's ruling of 2026-11-25, "Lem uses the well-known open-source library for a job, and
   writes no copy of its own"); no record, event, command line or page address of `main` must
   be kept (his ruling "The release of the reshape reads no record of the Lem before it"); the
   tests are the levels of the design's part 8, not the shell suites of "Checks". Its rules on
   voice, on what a skill may name, on numbers with their source, and every ruling still hold.
3. Today's code for what you build, with `git show main:PATH` (the proof of concept is on
   `main`; `rebuild` no longer holds it after the foundation step). The measure of the whole
   work is the owner's: "new version isn't worse than our proof-of-concept `lem`". So what
   today's code does for him in your step's sources, your step still does, unless the design
   names it as dropped.
4. `tests/ledger/rows.tsv` and `tests/ledger/owners.tsv`: the ledger of what `main` does, and
   the step that owns each row. Your rows are the ones `owners.tsv` gives your step id. Each
   gets a `fate` (`kept`, `changed`, `dropped`). Every fate names its test or trial check in
   `proof`. A changed or dropped row also needs a reason, in `note`. `close` checks that each
   named proof passed.
   Write these into `tests/ledger/fates/STEP.tsv` (the columns `id fate proof note`),
   never into `rows.tsv`. A row you cannot place goes into your report with why, never
   silently away. Until `owners.tsv` is on the branch, your brief names your sources.

## Where you work

- Only in your worktree, on your branch. Never write into the main checkout
  (`/Users/Silver/Projects/GitHub/lem`) or another worktree. Never `git stash`. Never push.
  Never rebase or merge by yourself: the orchestrator joins the steps.
- Only the files and folders your step owns (part 9 of the design). When you need a change in a
  file another step owns, do not edit it: write what you need and why into
  `docs/plans/2026-11-25-lem-built-again/notes/STEP.md`, build against a local stand-in or a
  fixture, and say so in your report. `kernel/errors.py`, `kernel/envelope.py`, `records/` and
  `ports/` change only this way: every step builds on them.
- Remove the old-form mark (`<!-- lem: old form -->`) from each checked file you rewrite; a
  file you do not rewrite keeps it.
- Commit as you go, small commits, messages `type(scope): subject` in this repository's voice
  (read `git log --oneline -20 main`).

## What you must never do

- Never run `lem`, `lem-hook`, `python -m lem`, a hook or a server without `LEM_SERVE=off` AND a
  throwaway `HOME` and `XDG_CONFIG_HOME` (the test entry sets them; a hand run must set them
  too). The owner's board server of the old release runs on this Mac (pid 3311, ports 4536 and
  4537): no test, probe or trial may touch it, stop it, replace it or use its ports. Never touch
  a process or a file under `~/.claude/` or `~/.config/`.
- Never start Chrome or a browser without a throwaway profile folder (and `--use-mock-keychain`
  for Chrome on macOS).
- No release, no version bump, no tag, no `brew install`, no change to the machine's settings.
- No network call that carries the owner's name, paths or project names.

## How the code is written

- Python 3.14. The well-known library for a job, never a copy of our own (the design's part 7
  names each). Dependencies only through `uv` (`uv add`, `uv sync --locked`); never pip.
- The gates pass with no `noqa`, no `type: ignore`, no per-file ignore that you add: ruff,
  pyrefly, wemake-python-styleguide on `src/lem` (7 members a module, 12 imports, 5 locals,
  complexity 12), import-linter (the layers of part 2). The design's part 2 lists the forms
  that pass. If a gate cannot be met in a natural form, split the module or the function once;
  if it still cannot, stop and say so in your report with the smallest case: do not bend the
  code into something worse, and do not silence the gate.
- Small modules, small pure functions, typed structs for every record and every command's
  input. No silent fallback: a wrong input is a refusal with a code, a why and a fix.
- Every text a person reads says "the owner". Names say what a thing is; no version suffixes.
- Comments and docstrings in this repository's voice: what the thing is and why, one or two
  lines. No history ("previously", "now").
- A test for every rule you build, at the lowest level that can prove it (the design's part 8).
  A test that needs time or a dated name keeps the value it made. Your step's verify selector
  must collect cases.

## Before you report

1. Run your step's verify commands and the gates (each gate when its inputs exist), in the form
   `.venv/bin/python -I -B tests --level LEVEL PATHS` (after `uv sync --locked` in your
   worktree). A selection that collects nothing is a failure. Never run `--level full`: one
   full run at a time on this Mac is the orchestrator's.
2. `git status --short` is empty; no process of yours is left; no file outside your worktree
   was written except under `/tmp`.
3. Report, under 500 words: what you built (files, lines of `src` and of tests); each verify
   command with its last lines (collected, passed, skipped: passed plus skipped must equal
   collected); what the ledger rows got (counts by fate) and the rows you could not place; the
   notes you left for other steps; what you are not sure of; `git log --oneline rebuild..HEAD`.

A reviewer of another model reads your step afterwards. Its changes come back to you as a list;
each is a proposal that the gates and the tests decide, not an order.
