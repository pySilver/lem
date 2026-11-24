---
worth: later
where: src/lem/land.py:BAR
added: 2026-11-24
---
# The bar check reads a method fit defined in a one-line bundle as a new focus mark

The JavaScript marks of `BAR` in `land.py` count `fit(`, `fdescribe(`, `xit(`, `xtest(` and
`xdescribe(` unless a `.` comes before them, so a method call (`this.fit()`) is no mark. A method
definition in a class body is none of these either, and still counts: `}fit(){` and `},fit(){`.

`bar_of` keys a mark by its file, its pattern and the text after it on its line. In a built file
of long lines, an edit after the definition on the same line makes the old mark count as new.

The task `sidebar-fold-arrow` (2026-11-22) changed only the fold controller and rebuilt
`skills/lem/assets/vendor/board-app.js`. Its bundle with the chart's two methods named `fit` again
(the bundle of `6698997d` with `fitBox` and `fitWindow` renamed back), against the bundle of
`569d09ca`, still gives one lowered bar: `fit` in `board-app.js`, the definition `},fit(){` on line
83, where the fold code changed after it (`bar_of` at the commit that skips a method call,
2026-11-24). The bundle holds two definitions and six calls; the calls no longer count.

- (a) Nothing now: a builder renames the method, as `sidebar-fold-arrow` did.
- (b) A definition is no mark either: a name whose `(...)` is followed by `{` on its line. A call
  of a runner's `fit` never is. Cost: one pattern and its unit cases, in a careful task.
- (c) A built file is the one git's attributes mark as generated (`linguist-generated`), and the
  bar reads none. Cost: one `git check-attr` call and a line for each built file in each project.

Seen by the worker that made a method call no mark, 2026-11-24.
