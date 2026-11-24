---
worth: later
where: src/lem/land.py:BAR
added: 2026-11-24
---
# The bar misses a chained focus mark, and Python under a uv or shell header

The JavaScript marks of `BAR` in `land.py` count `it.only(`, `test.only(`, `describe.only(`, their
`.skip(` and `.todo(`, and `fit(`, `fdescribe(`, `xit(`, `xtest(` and `xdescribe(`: a mark is a
name and its modifier with `(` right after them. The runners document more forms, which run one
test alone or leave tests out all the same, and the bar names none of them:

- Jest (jestjs.io, `test.only.each`): `test.only.each(table)(name, fn)`, under the aliases
  `it.only.each`, `fit.each`, and the tagged forms ``it.only.each`table` `` and ``fit.each`table` ``;
  `describe.only.each(table)(name, fn)`; and the same with `.skip`.
- Vitest (its `SuiteAPI` types, 5.1.0-beta.1): each modifier chains with the others in any order
  and carries `each`: `describe.only.each(`, `describe.skip.each(`, `describe.todo.each(`, and
  `test.concurrent.only(`, `test.only.concurrent(`, `describe.concurrent.only(`.

A Python script with no suffix is read by its first line (`shebang_suffix`). Two headers run Python
and are read as no language, so none of its marks count:

- `#!/usr/bin/env -S uv run --script`, the header of a script with inline dependencies: the first
  word after the options of `env` is `uv`.
- A shell header that hands the file to Python, `#!/bin/sh` and then a line such as
  `''''exec python3 "$0" "$@" #'''`: the first line names `sh`, and its marks are the shell's.

The review that found these (Astra, 2026-11-24) ran both `41a69d47` and `7f980474`: each missed
every one.

- (a) Nothing now: a review reads every line of the diff and sees such a mark.
- (b) The JavaScript marks take any chain of modifiers between the name and `(`:
  `\b(it|test|describe)(\.\w+)*\.(skip|todo|only)(\.\w+)*(?=\(|`)`, and `\bf(it|describe)\.each`.
  Cost: a method of the same shape counts too (`results.test.only(`, a chain no runner has), and
  the unit cases of the bar, in a careful task.
- (c) `uv run` in a header is Python, and a header of `sh` whose second line runs `exec python`
  is too. Cost: `uv run` also runs a command that is not Python (`uv run --with x bash`), whose
  `#` comments would count as Python's marks, and the second read reads one more line of each file
  with no suffix.

Seen by the worker that repaired the review's findings, 2026-11-24.
