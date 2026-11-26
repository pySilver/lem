# Notes of the step `guides` for the owners of other files

## `eslint.config.mjs` (board-pages): the built site

The site's script and the link to Pele are in `docs/assets/`, under a config of their own
(`docs/assets/eslint.config.mjs`: ESLint 10 takes the nearest config of each file, and
`zensical.toml` leaves that file off the site), so the root's config needs no change for them. A
build in the checkout (`.venv/bin/zensical build`) writes `_site/`, with copies of Zensical's
bundle, of Pele and of the site's script, which the root's config reads as Lem's own: one line
`'_site/'` in its `globalIgnores` keeps a local build out of the gate. The step's tests build in a
copy of the checkout and leave no `_site/`.

## `.gitignore` (core): the built site

`_site/`, which `.venv/bin/zensical build` writes at the root (`zensical.toml`, `site_dir`), is
not ignored: one line `_site/` keeps a build out of `git status`.

## `docs/rulings/history.md` (close, and each step whose test it names)

The history still carries the old-form mark, and its first part names main's tests
(`tests/unit/test_*.py::...`, `tests/lem-*.sh: "..."`); one line of its second part names
`src/lem/serve.py`. `tests/unit/guides/test_rulings.py` reads a guard of any level
(`tests/LEVEL/.../test_x.py::test_name`) and skips the two history cases while the mark stands. The
step changed only the lines of its own rulings: the three that named the README's sections now name
`docs/index.md`, and the one that named the AGENTS.md bullet "Scripts are standard-library Python"
names its successor.
