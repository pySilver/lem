---
worth: later
where: skills/lem/scripts/land.py:bar_of
added: 2026-11-22
---
# The bar check reads a method call fit( in a one-line bundle as a new focus mark

The JavaScript marks of `BAR` in `land.py` include `\bf(it|describe)(?=\()`, the focused test of
Jasmine and Mocha. The word boundary also holds after a dot, so `this.fit()` matches, and any method
named `fit`, `fdescribe`, `xit`, `xtest` or `xdescribe` reached through a dot counts as a mark. The
same holds for the marks of the form `\b(it|test|describe)\.(skip|todo|only)(?=\()` when the object is
reached through a dot (`this.test.only(`).

`bar_of` keys a mark by its file, its pattern and the text from the mark to the end of its line. In a
minified file of one line, such as `skills/lem/assets/vendor/board-app.js`, every edit after the first
match changes that text, so the mark that was on the base already counts as new.

The task `sidebar-fold-arrow` (2026-11-22) showed both. On base `569d09c` the bundle held
eight matches of `fit(`, six calls `this.fit()` and two definitions `fit(){`, all from the two `fit`
methods of `tools/board-kit/controllers/chart.js`.
The task changed only `controllers/fold.js`, rebuilt the bundle, and the bar check named
`fit(` in `board-app.js` as a lowered bar. The fast track has no plan, so no reason under `## The bar`
could keep it, and the task renamed the two methods to `fitBox` and `fitWindow` instead.

A fix could skip a match that follows a `.`, and could leave out a built file (a file of one line
over some length, or the paths a project names as built). A fix of `bar_of` reaches "the bar went
lower" in what must never go wrong (`.lem/project.toml`), so the task that makes it is careful.
