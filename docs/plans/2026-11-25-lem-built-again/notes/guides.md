# Notes of the step `guides` for the owners of other files

## `eslint.config.mjs` (board-pages): two ignores and one browser group

The site's theme links Pele into the built site: `overrides/assets/pele.js` is a link to
`skills/lem/assets/vendor/pele.js`, because Zensical copies a linked file of its `custom_dir` and
not a linked folder. ESLint follows the link and reads Pele's bundle as Lem's own JavaScript: on
2026-11-26 `node_modules/.bin/eslint .` gave 143,790 findings in `overrides/assets/pele.js`, and the
gate `gates.test_eslint_holds_the_javascript_to_its_style` fails on every machine with
`node_modules`. A build in the checkout (`.venv/bin/zensical build`) also writes `_site/`, whose
copies of Zensical's bundle and of Pele the same gate would read. `overrides/assets/lem-charts.js`
is a classic script for the browser, like `lem.js`.

What the step needs, in `eslint.config.mjs`:

```js
  globalIgnores([
    // The board's built files and Pele's own, which tools/board-kit writes (its README), the site's
    // link to Pele, and the built site.
    'skills/lem/assets/vendor/',
    'overrides/assets/pele.js',
    '_site/',
    ...
  ]),
  ...
  {
    files: [PALETTE, ASK, 'overrides/assets/lem-charts.js'],
    extends: [neostandard({ env: ['browser'] })],
    languageOptions: { sourceType: 'script' },
  },
```

Until then the step built against the ESLint of its own file:
`node_modules/.bin/eslint overrides/assets/lem-charts.js` is silent.

## `.gitignore` (core): the built site

`_site/`, which `.venv/bin/zensical build` writes at the root (`zensical.toml`, `site_dir`), is
not ignored: one line `_site/` keeps a build out of `git status`. The step's tests build in a copy
of the checkout (`tests/unit/guides/built.py`) and leave nothing at the root.

## `docs/rulings/history.md` (close, and each step whose test it names)

The history still carries the old-form mark, and its first part names main's tests
(`tests/unit/test_*.py::...`, `tests/lem-*.sh: "..."`); one line of its second part names
`src/lem/serve.py`. `tests/unit/guides/test_rulings.py` reads a guard of any level
(`tests/LEVEL/.../test_x.py::test_name`) and skips the two history cases while the mark stands. The
step changed only the lines of its own rulings: the three that named the README's sections now name
`docs/index.md`, and the one that named the AGENTS.md bullet "Scripts are standard-library Python"
names its successor.
