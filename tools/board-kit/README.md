# board-kit

Builds the browser's files of Lem's board into `skills/lem/assets/vendor/`:

- `board-app.js`, the one script of the board that `lem serve` renders (`app.js`): Turbo, which visits
  the board's pages and morphs a page into its new version when the server's stream says the
  workspace changed; Stimulus and the board's controllers (`controllers/`); and the markdown reader
  of `entry.js` (`marked`), which shows an artifact's text with its links checked and its raw HTML as
  text.
- `board-icons.json`, the Font Awesome icons the board shows, each as an SVG symbol's `viewBox` and
  body, which the server puts into each page it renders as one `<svg>` of symbols.
- `mermaid.min.js`, the diagram library (mermaid 11.12.0, MIT) as its package ships it, the same file
  that `lem-ask` pins by its sha256, which the build checks. `charts.js` loads it only on a page that
  has a chart, from the address that the document holding the chart gives (`data-lem-mermaid`, which
  the server writes only on a document with a chart), and draws each fenced `mermaid` block of a
  document in the board's palette, again when the palette changes; the `chart` controller fits each
  drawing to its box and opens it large.

The script is one classic script (iife), and nothing in it loads from the network. The board's look is
`skills/lem/assets/lem.css` and `board.css`, which the server sends as they are.

```bash
npm --prefix tools/board-kit ci          # Turbo, Stimulus, marked, mermaid and esbuild, from the public registry
npm --prefix tools/board-kit run build   # writes the three files; FA_SVGS names the icons' folder
```

The icons come from the Font Awesome Pro download (`FA_SVGS`, by default
`~/Downloads/fontawesome-pro-6.7.2-web/svgs`), only the ones `icons.mjs` lists. The built files
are committed: people who install the plugin never run this.

## A controller

A controller has one job. It is a file in `controllers/`, a Stimulus controller as its default
export, and one line in `controllers/index.js` that names it as the pages' `data-controller` says it.
What the browser alone knows (an open drawer, the backlog's cursor, a row the filter hides) it keeps in
an attribute named `data-js-*`, which a morph leaves as it is (`app.js`); what the server should
render too goes into the cookie of `controllers/prefs.js`. Then `npm --prefix tools/board-kit run build`.

## The panel of a task

A task opens in `<turbo-frame id="task">` (`lem_board_task.py`). Its controllers: `panel` (it marks the
task's card while it is open, and expands the panel), `splitter` (the grip, whose width goes into the
cookie), `tip` (the hover of the time card), `artifacts` (the groups folded and the list's scroll,
kept for the task while the page lives), `markdown` (a document rendered from the `<template>` the
server fills, with its tables in a box that scrolls sideways, its pictures from the task's media
folder, GitHub's alerts as callouts and its charts drawn, kept through a refresh while its text is the
same: `data-keep` in `app.js`), `chart` (a chart fit to its box, whole and never larger than drawn, or
sideways in its box when its words would be too small; a click opens it over the whole window, where
it pans and zooms), `sheet` (a merge's, a park's or an approval's step with its button: on a phone an
overlay whose button comes on when its text was read to the end) and `copy`.

## What only agterm does

agterm gives a page served over http no bridge, so the `agterm` controller asks the server: a page the
server drew for this Mac (`Ctx.local`) posts the jump to a task's session to
`/HOST/WORKSPACE/agterm/select`, and the server runs `agtermctl session select` (`serve.py`,
`agterm_act`). A page through the tailnet door has no such button.
