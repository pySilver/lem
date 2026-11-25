# Notes of the step `tree`

What `tree` needs in files it does not own, and the two local seams it built until they exist.

## For `core`

`core` answered items 1 to 5 in `notes/core.md` ("`tree`: the five notes"). What stays open on
this branch is the switch to them, which waits for `rebuild` merged into `rb/tree`:

1. **The log of a fault.** `src/lem/cli/faults.py` is a local seam, imported only on a fault.
   It appends the time and the traceback to `lem.log` in Lem's home folder, and sends them to
   standard error with the reason when the home is relative or cannot be written
   (`test_tree.py` holds both). The switch: `lazy.main` calls
   `lem.kernel.logs.logged(fault, argv, os.environ)` and prints the `Failed` it gives, and the
   seam goes.
2. **The root of Lem's files.** `src/lem/cli/version.py`'s `root()` follows the rule of `main`'s
   `paths.root`. The switch: it calls `lem.kernel.paths.root()`.
3. **`--repo` before the noun and the version check.** `rebuild`'s `__main__.first_word` reads
   the first word past `--repo PATH` and `--repo=PATH`, so `lem --repo . doctor`, `help` and
   `version` pass the check (finding 8 of the review). The tree's side is in `test_tree.py`
   (`test_repo_before_help_version_and_doctor_reaches_them`). After the merge, a case through
   `tests/fakes/command.py` with `LEM_PLUGIN_ROOT` set to another version shows it end to end.
4. **The workspace of a call.** `lem --repo PATH NOUN ...` is one option of the root, before
   the noun; a folder that does not exist is a wrong call (exit 2). `cli/place.py`'s `folder()`
   gives the folder the call names, resolved, else the working directory, and nothing more.
   Every leaf calls `lem.store.places.workspace(place.folder())` (`notes/core.md` item 5),
   never `Path.cwd()`.
5. No new dependency and no gate setting: Click and msgspec are enough for the tree.

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
- A rule of the call that Click's parser does not hold (exactly one, at most one, at least one
  of some words) is `cli/checks.py`, in the leaf's callback, so that a wrong call is exit 2
  before `run`; a rule of one leaf only is a small function of that leaf (`criteria/read.py`,
  `task/investigated.py`). Keep them when `run` is filled.
- A text the step rewrites loses its first line `<!-- lem: old form -->` (after the front matter
  in a skill); `tests/unit/cli/test_lines.py` fails on a mark over a text with no old line.
