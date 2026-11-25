# Notes of the step `tree`

What `tree` needs in files it does not own, and the two local seams it built until they exist.

## For `core`

1. **The log of a fault.** `src/lem/cli/faults.py` is a local seam: on a fault, `lazy.main` sends
   the traceback through the logger named `lem` (`faults.LOGGER`) to `lem.log` in Lem's home
   folder (`$XDG_CONFIG_HOME/lem`, else `~/.config/lem`), and prints the path in the envelope's
   `fault.log`. A log that cannot be written goes to standard error, and `fault.log` says why.
   When `kernel/` has its log, `faults.logged` and `faults.home` call it, and the seam goes.
2. **The root of Lem's files.** `src/lem/cli/version.py` has its own `root()`: the package's
   `data` folder in an installed app, else the checkout when it holds `skills/lem/SKILL.md`, else
   a `Fault` that names both (`main`'s `paths.root`). `__main__.py`'s version check needs the
   same root. When `kernel/` names it, `version.root` calls it.
3. **What `__main__.py` lets through before a command.** The tree answers `help` and `version`
   itself (`lem` alone is `lem help`; `-h` and `--help` work at every level). Part 5 says they
   answer before the version check and the server start, so `__main__.main` skips both for an
   empty `argv` and a first word `help`, `version`, `-h` or `--help`; the version check also
   lets `doctor` through, and the server start skips `serve`, `board`, `doctor`, `ask` and `jev`
   (`main`'s `NO_LOOK`). Then `sys.exit(lazy.main(sys.argv[1:]))`, as now.
4. No new dependency and no gate setting: Click and msgspec are enough for the tree.

## For the steps that fill a leaf

- A leaf is `src/lem/cli/NOUN/VERB.py` (a noun with no verbs: `src/lem/cli/NOUN/command.py`):
  its `Call`, its `run(call)` and its `COMMAND`. Replace `run`; keep `Call` and `COMMAND` equal
  to each other (`tests/unit/cli/test_tree.py` checks every leaf). A change of a command's words
  writes `tests/unit/cli/tree.json` again on purpose:
  `.venv/bin/python -I -B tests/unit/cli/shapes.py --write`.
- `run` returns the outcome (a msgspec struct, printed as `result`), or a whole `Envelope` when
  it says `say` or `next`; it raises `Refusal` for a refusal. `lem ask` returns every outcome.
- A choice is a `type X = Literal[...]` alias and `type=choice(X)` (`cli/words.py`), so each
  value is written once.
- A text the step rewrites loses its first line `<!-- lem: old form -->` (after the front matter
  in a skill); `tests/unit/cli/test_lines.py` fails on a mark over a text with no old line.
