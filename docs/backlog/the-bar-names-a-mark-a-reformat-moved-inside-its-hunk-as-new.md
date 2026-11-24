---
worth: later
where: src/lem/land.py:same_in_hunk
added: 2026-11-24
---
# The bar names a mark that a reformat moved inside its hunk as new

`same_lines` pairs each added line of a file with a removed one: first a line with the same words
from anywhere in the file, then, in the hunk, a line that kept its code before its first mark
(`same_in_hunk`), then the rest of the hunk in their order. `new_marks` counts a mark of an added
line as new unless its pair holds the same mark. When a formatter splits or joins a statement,
no line keeps its words or its code, and the order decides which line takes the old mark.

The run, `bar_of` at 3247d8fe on one hunk of `calc.py` (`# noqa` written whole here):

1. A split. The line `total = compute(alpha, beta, gamma, delta)  # noqa: E501` went. Three came:
   `total = compute(`, `    alpha, beta, gamma, delta` and `)  # noqa: E501`. The first came
   line takes the old line by order, so the mark on `)` is new: one lowered bar,
   `('calc.py', '# noqa', ')  # noqa: E501')`.
2. A join, the other way. `    alpha, beta, gamma, delta  # noqa: E501` and its two neighbors
   went, and one line with the mark came. It takes `total = compute(` by order, which has no
   mark: one lowered bar, `('calc.py', '# noqa', 'total = compute(alpha, beta, gamma, delta)  # noqa: E501')`.
3. A move. `import os  # noqa: F401` and `import sys` went, and `import os` and
   `import sys  # noqa: F401` came. Each line keeps its code, so `import sys` pairs with
   `import sys`, and the mark on it is new: one lowered bar. This one is right: the rule of
   `new_marks` is that a suppression taken off one line and put on another is a new one.

So the sentence "a mark that a reformat moved is a false lowered bar" holds for 1 and 2 only if a
mark that follows its statement to another line is the same mark. By the rule as written, a mark
on another line is a new one, and the bar asks for a reason under `## The bar`. A reader could
fix 1 and 2 by pairing a mark with a mark in the hunk, and so make 3 pass unseen.

- (a) Nothing now. A reformat that moves a mark asks for one line of reason in the plan. Cost:
  the line, and a refusal on the fast track, which has no plan.
- (b) A hunk whose text without marks and spaces is the same before and after is a reformat, and
  a mark in it counts as new only when the hunk holds more of it after than before. Cost: case 3
  is such a hunk too (`importosimportsys` both times), so a mark moved to another import passes
  with no reason.
- (c) In such a hunk, a mark is the same mark when it stands at the same place of that text: the
  same mark after the same character. Case 1 passes (the end of the statement both times), case 3
  stays new (after `os`, then after `sys`), and so does case 2 (after `delta`, then after `)`).
  Cost: one rule in `same_in_hunk`, the three runs as unit cases, and a join that moves a mark
  past a bracket still asks for a reason.
- (d) Pair a mark with a mark of the same own text in its hunk before the order. Cost: case 3,
  and any mark moved to another line of the same hunk, passes with no reason.

Recommendation: (c). It keeps the rule of `new_marks` and takes the most common split, a mark at
the end of a statement that a formatter cut. Its unknown: a formatter that also changes words in
the same hunk (a trailing comma) makes the texts differ, and the hunk falls back to the order.

Seen by a builder of 2026-11-24 while it repaired the bar's diff reader (9497aa41); the three runs
above are of this item.
