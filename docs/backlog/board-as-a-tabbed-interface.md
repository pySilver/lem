---
worth: yes
where: skills/lem/assets/board.html
added: 2026-11-18
---
# The board as a tabbed interface

The owner: "redesign board to a tabbed interface, consider using the WebAwesome (we have a
professional license)" (2026-11-18).

The board is one page, `skills/lem/assets/board.html`, with its look in `lem.css` beside it. It
has two tabs today, the tasks and the backlog, and the board of one task is the same page drawn
for one task. It draws `events.js`, `meta.js` and `backlog.js` from the state folder, which a
`file://` page can load as scripts and cannot fetch.

Open before a plan:

- Which views become tabs: the tasks, one task, the backlog, the decisions that wait, the report
  of the night, the retro's proposals. The owner has not said.
- Web Awesome as the component library: how its files reach a page that opens from the state
  folder with no server and no network (a copy that ships in the plugin, or its kit address), what
  the professional license allows for a public repository (its terms must be read first; a
  licensed component must not be published where the license forbids it), and what a developer
  without that license sees.
- What stays of `lem.css`: every page of Lem links it (his ruling "A page for the owner has the
  board's look"), so the hand-over page and the question page follow the same look.
- The pictures of the board in `assets/screens/` and the test `tests/test-board.sh`, which loads
  the page in headless Chrome, follow the new page.
