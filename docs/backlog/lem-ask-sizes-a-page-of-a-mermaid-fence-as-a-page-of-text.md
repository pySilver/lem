---
worth: later
where: skills/lem-ask/bin/lem-ask:auto_size
added: 2026-11-22
---
# lem-ask sizes a page of a mermaid fence as a page of text

`auto_size` picks the overlay's percent, and gives 90 to a page it calls visual: one whose spec, as
JSON, holds `"mermaid"`, `"chart"`, `"image"` and the like. A ```` ```mermaid ```` fence inside an
`md` block is in that JSON as `"```mermaid\n…`, with no quote before the word, so a criteria page
whose one chart is such a fence is not visual: with two options and one question it opens at 78
(or 66 with `"width": "narrow"`), where a page with the same chart as `{"mermaid": …}` opens at
90. `uses_mermaid(spec)`, which already finds both forms for the bundle, would say it.

Seen outside the change by the builder of task lem-ask-draws-mermaid-fences (2026-11-22); the base commit has it.
