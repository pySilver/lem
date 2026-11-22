---
worth: later
where: skills/lem/scripts/lem_board_pages.py:md_block
added: 2026-11-22
---
# With no script a markdown block of the board shows no text

`md_block()` renders a text as `<div class="md" data-controller="markdown" ...><template>TEXT</template></div>`,
and only the `markdown` controller draws it. A browser with no script never draws a `<template>`, so each
markdown block of the board is empty there: the outcome, the breaker's text and the merge review on a
task's Overview (`outcome-SLUG`, `breaker-SLUG-N`, `merge-review-SLUG`), the
"how" card of the criteria tab (`how-SLUG`), a backlog item's text (`bl-SLUG`), a document opened among
the artifacts (`art-...`) and each chart of `chart_block()`. The task phone-merge-confirm-in-view gave
only the approval of the criteria a `<noscript>` with its text as plain text (`approve_card()` in
`lem_board_task.py`), since there the button must come after the text. A fix gives `md_block()` itself
that `<noscript>` fallback, and the rule of `board.css` that hides the approval's empty box,
`.approve-body .md:has(> template:only-child)`, then has to reach every block.
