# The status boards: one steady look, with tabs, in Lem's own light and dark

careful: no, because no task changes a record, a script that writes one, the text of a pull request or a git act: the board reads `events.js`, `meta.js` and `backlog.js` and writes nothing, `land.py`'s green and its reasons are untouched, and the board's one action (the backlog's "Start a task", which types `/lem new PATH` into Lem's session) keeps its code and its test in `tests/lem-settings.sh`.

## Acceptance criteria

Size: full, because the change redraws the whole board page and `lem.css`, which every page of Lem links, and it adds tabs to both boards.

1. Each button of the board has one fixed place, whatever the length of the texts beside it: on the board of one task, "All tasks" and the button to Lem's session stay at the top right both for the title "fix: the dates stay whole" and for a title of 160 characters, in a window 900 px wide and in one 1400 px wide; a long title wraps to two lines at most and shows whole when the owner points at it or moves the focus to it; the button to Lem's session says that it goes to Lem's session; and every card that has an action ("Open the task", "Start a task" in the backlog) has it at the same side.
2. A card does not change its shape with the length of its text: two task cards in one lane, one with an ask of one line and one with an ask of 300 characters, have the same height. Only the ask is cut, after its last whole line; the card's state and a mark that something waits for the owner always show. The Tab key reaches each card, and the long ask shows whole when the owner points at the card or moves the focus to it.
3. The board takes Lem's own light or dark palette from agterm's background: with the background `#15181c` it draws dark with the night logo, with `#ffffff` and with Solarized light's `#fdf6e3` it draws light with the day logo, and with Solarized's `#002b36` its cards and text use Lem's dark palette and no Solarized color. Opened outside agterm, with no background to read, it follows the system's light or dark setting. In both palettes body text and the small labels (lane names, times, status words) have a contrast of at least 4.5 to 1 against their background.
4. The board of all tasks has three tabs, "Tasks", "Waits for you" and "Backlog": with two choices that wait, one task whose criteria wait for the owner's yes and one green pull request, "Waits for you" shows the count 4 and lists those four, each row saying what the owner does there: answer a choice, approve the criteria, or merge the pull request. The tab the owner chose stays chosen when the page draws itself again every second, and so does a text he selected in the backlog.
5. The board of one task has four tabs, "Overview", "Criteria and decisions", "Checks and review" and "Timeline", and its first view says green or not green with its reasons in plain words: a task whose pull request is not green because the experts took choice 2 shows on "Overview", with no click, "not green: two outside experts chose option 2 while you were away". The tab the owner chose stays chosen when the page draws itself again.
6. Every page of Lem that links `lem.css` has the board's look: the onboarding page shows the same header, fonts and colors as the board, in light and in dark.
7. The pictures of the board in the README and in `docs/when-lem-needs-you.md` show the new board, in light and in dark, and each caption says that the picture shows example tasks.
8. The backlog item `docs/backlog/board-as-a-tabbed-interface.md` is closed by this change: its file is removed.

## What exists

Read in the code at `197cbbc`:

- `skills/lem/assets/board.html` (2,449 lines) is one page for both boards. `view` (a task's slug,
  or null) picks the board of one task; a click on a task sets it in place. `render()` runs every
  second and patches the page by `keyed(...)` keys. The board of all tasks already has two tabs,
  `tab` = `tasks` or `backlog` (`setTab`, `#backlog` in the address, keys `T` and `B`), and the
  backlog is drawn again only when its outside data changed, so that the focus and a selection
  stay. `setTab` returns at once on the board of one task, and `render()` sets `tab = 'tasks'`
  there: the board of one task has no tab of its own.
- The buttons move because `.top` in `lem.css` is `display: flex; justify-content: space-between;
  flex-wrap: wrap`: a long title or ask wraps `.top-right` ("All tasks", "Go to Lem") onto a line of
  its own, where `space-between` puts it at the left. `.card-head`, `.foot` and `.now-side` (under
  760 px) have the same form. "Open the task" stands in `.now-side`, "Go to the session" at the
  bottom right of the large card, "Go to Lem" at the end of each banner, the backlog's Start and
  Cancel at the left of `.bl-actions`.
- The cards of a lane (`taskCard`) and the large card of one task (`buildTaskNow`) take the height
  of their text.
- The background and the text follow `var(--agterm-background, Canvas)` and
  `var(--agterm-foreground, CanvasText)`, so a terminal theme recolors the board; the six actor
  colors are fixed hex values in `lem.css`. No `color-scheme` and no `prefers-color-scheme` rule
  exist. The header always shows the day mark, a copy of `assets/lem-mark.svg` between
  `<!-- lem-mark -->` comments, in `board.html` and in `handover.html`; `assets/lem-mark-night.svg`
  is not used by any page.
- What waits for the owner is in the data already: `derive()` gives each task its `asks` (the
  choices that wait), `criteriaWait`, `status` (`held`, `open`) and `proposal` (`green`, `reasons`,
  the `not_green` lines of `land.py`'s `proposed` event). A choice's record has `options`, `chose`,
  `state` (`timeout` for one taken without the owner), `by` (`experts`) and `experts` (each
  expert's reason). `lem project waiting` (`cmd_waiting` in `project.py`) is the list `/lem` says:
  the choices, the criteria that wait, the other held tasks, the open proposals, and the retro
  proposals, which the board has no file for.
- Tests: `tests/test-board.sh` draws the pages in headless Chrome over a fixture of 30 tasks, reads
  the DOM (`--dump-dom`), and measures one geometry fact with a script put into a copy of the page
  (the phase labels keep 8 px or more apart at 1300 px). `tests/lem-settings.sh` (about lines
  1409-1430) checks that each logo copy equals its file, that the handover pattern links `lem.css`
  once and has no `<style` or ` style="`, and that only `lem.css` holds `--you: #`; its backlog
  journey (about lines 1500-1620) clicks Start and checks the one line typed into Lem's session.
  `tests/board-showcase.py` makes the README's pictures `assets/screens/board-*`, `task-*` and
  `backlog-*` and gives dark by putting `--agterm-background: #15181c` into the page.

## Tasks

Each task is built by a fresh builder in the worktree, in this order: all four edit
`board.html`, so none runs beside another.

1. **Lem's look as a small design system, in its own light and dark.** `lem.css` becomes the
   tokens and the parts every page shares: neutral grays and one accent, the six actor colors only
   as small marks, the system font and a monospace font for slugs, branches and commits, thin
   borders, cards of 8 to 10 px radius, no heavy shadow, one spacing scale of 4 and 8 px; one
   button, one card, one tab bar, one chip, in two palettes of Lem's own. The palette is chosen
   from agterm's background (light or dark by its luminance) and from the system's setting when
   there is no background to read; no agterm color is used beyond that choice. The header is the
   same on every page: the mark (the day logo in the light palette, the night logo in the dark
   one), the title, which wraps to two lines at most and shows whole on hover and on focus, and
   the buttons in a column of their own at the top right that no text moves. On the board the
   button to Lem's session says so ("Go to Lem's session"). `handover.html` follows: same header,
   fonts and colors, with its own `.doc` parts restyled to the new tokens. The board's own
   `<style>` keeps only what is the board's and uses the tokens; the rest of the board's layout is
   tasks 2 and 3.
   Serves criteria 1 (the header: the two buttons at the top right, the long title, the button's
   name), 3 and 6. Files: `skills/lem/assets/lem.css`, `skills/lem/assets/lem.js` (new, see
   decision 3), `skills/lem/assets/handover.html`, `skills/lem/assets/board.html` (the header,
   the second mark, the link to `lem.js`, the name of the button), `skills/lem/scripts/board.py`
   (copies `lem.js` beside the page as it copies `lem.css`), `skills/lem/stages/init.md` (the step
   that copies `handover.html` and `lem.css` copies `lem.js` too), `tests/test-board.sh`,
   `tests/lem-settings.sh` (each logo copy in each page, and `lem.js` copied), `tests/unit/` for
   `board.py`'s copy when a unit case can hold it.
2. **The board of all tasks: three tabs, and cards that hold their shape.** Tabs "Tasks", "Waits
   for you" and "Backlog", in the tab bar of task 1, each with its count. "Waits for you" has one
   row for each thing the owner does (decision 5), each with its verb: answer choice N, approve the
   criteria, merge the pull request (or tell Lem to land it, where there is no pull request), and
   what a held task's state line asks; its count is the number of rows. The task cards of a lane
   have one height: the ask is cut after its last whole line, the state and the mark that
   something waits for the owner always show, the card takes the focus with Tab, and the whole ask
   shows on hover and on focus. Every card with an action has it at the same side ("Open the
   task", the backlog's "Start a task", Cancel beside it). The tab the owner chose stays through
   the redraw of every second, and a text selected in the backlog stays selected. The band above
   the lanes, the banners and the timeline of the board of all tasks take the new look; the banners
   that are now rows of "Waits for you" may go, with what they said kept in the row.
   Serves criteria 1 (the cards' actions), 2 and 4. Files: `skills/lem/assets/board.html`,
   `tests/test-board.sh`, `tests/lem-settings.sh` when its backlog journey names a class or a place
   that moved.
3. **The board of one task: four tabs, and green or not green on its first view.** Tabs
   "Overview", "Criteria and decisions", "Checks and review" and "Timeline". "Overview" holds the
   large card, the phases and the numbers of `buildTaskProgress`, and one line that says green or
   not green with each reason in plain words (decision 4), so that green or not green, the checks
   and the decisions taken without the owner are there with no click. "Criteria and decisions"
   holds the criteria and the decisions; "Checks and review" the checks and the reviews;
   "Timeline" the time card and the activity. The tab the owner chose stays through the redraw,
   and "All tasks" takes him back to the tab of the board of all tasks he left. The large card has
   one height whatever its lines, and "Go to the session" one place.
   Serves criterion 5. Files: `skills/lem/assets/board.html`, `tests/test-board.sh`.
4. **The pictures, the documents, and the backlog item closed.** `tests/board-showcase.py` draws
   the new board (it adds what the tabs need, such as a picture of "Waits for you" when it helps
   the README) and the pictures in `assets/screens/` are made again, light and dark. The captions
   in `README.md` and `docs/when-lem-needs-you.md` say that the picture shows example tasks. The
   documents the change makes false are corrected: `docs/when-lem-needs-you.md` ("The second tab
   shows the backlog"), `skills/lem/SKILL.md` "Status" ("The board of all tasks has a second tab,
   the backlog"), `AGENTS.md` "Layout" (the line of `board.html` and `lem.css`, and `lem.js`
   beside them), and any other sentence a `grep` for the board's tabs, its look or "second tab"
   finds in `README.md`, `docs/` and `skills/`. `README.md` and `docs/` are in ASD-STE100; the
   rulings in `AGENTS.md` keep their words. `docs/backlog/board-as-a-tabbed-interface.md` is
   removed (`git rm`).
   Serves criteria 7 and 8. Files: `tests/board-showcase.py`, `assets/screens/*.png`, `README.md`,
   `docs/when-lem-needs-you.md`, `skills/lem/SKILL.md`, `AGENTS.md`,
   `docs/backlog/board-as-a-tabbed-interface.md`.

## Decisions the plan takes

1. **Four tasks, one after another.** The two boards are two outcomes with criteria of their own,
   each a reviewer can check alone, and the design system under them is a third; all three edit
   `board.html`, so they run in order. The pictures come last, since they are of the finished
   board. Rests on: the criteria, which name the two boards apart (4 and 5), and the size of
   `board.html`.
2. **A tab hides its panel and never removes it.** Every panel is drawn into the page on every
   redraw, and the panels of the other tabs carry `hidden`. Nothing the owner could see before is
   gone, the tab costs no redraw, and `test-board.sh`, which reads the DOM, still finds each part.
   Rests on: the owner's direction "No information goes away: the tabs handle the density"
   (`directions.md`), and `render()`, which patches by keys.
3. **The palette is chosen by a small script that every page of Lem loads beside `lem.css`.** CSS
   alone cannot turn a color into light or dark, and agterm gives the page its background as a CSS
   variable (`--agterm-background`, as `board-showcase.py` puts it into the page). `lem.js` reads
   that variable, sets the palette on the root element (light when the background's relative
   luminance is above the middle, dark otherwise), and leaves it to `prefers-color-scheme` when the
   variable is empty; it reads again when the system's setting changes, and the board, which draws
   every second, may read it on each draw. One file holds that rule, as one file holds the look, so
   the board and the onboarding page cannot choose apart. The cost: `board.py` and the onboarding
   step copy one more file. Rests on: `board.py` `prepare` (it copies `lem.css` beside the page)
   and `stages/init.md` (it copies `handover.html` and `lem.css`).
4. **The reasons of not green are said in plain words from the records.** The line on "Overview"
   is built by the board from the task's decisions and its `proposed` event, never by parsing a
   whole sentence of `land.py`. A choice taken by the experts while the task ran without the owner
   (`state: timeout`, `by: experts`) is "two outside experts chose option N while you were away",
   or "one outside expert ..." when one answered (the `experts` of the record has one reason); N is
   the place of the chosen text in the choice's `options`, counted from 1, and the row names the
   choice beside it. A choice taken as the recommended option while he was away is "Lem took the
   recommended option of choice N while you were away". Every other reason of `not_green` (the bar,
   a changed criterion, the criteria not read, careful on the fast track, a review) is shown in the
   words `land.py` wrote, since the board has no record of its own for it; its lines that begin with
   `choice N ` or `decision N ` are the ones replaced by the plain line. The test's fixture takes
   option 2 of choice 2, so the line of criterion 5 reads the same in both readings of "choice 2"
   and "option 2". Rests on: `not_green()` and `without_him()` in `land.py`, and `decisionEvent()`
   in `board.html`.
5. **"Waits for you" has a row for each action of the owner's that the board can see.** One row
   for each choice that waits, each task whose criteria wait, each other held task (with its state
   line), each proposal that waits for his merge (green or not, with its reasons), and each plan
   whose lead said the owner reads it, as the lane "Waits for you" counts it today. It is
   `lem project waiting` without the retro proposals, which the board has no file for, and with the
   plans to read. Rests on: `cmd_waiting` in `project.py` and `forOwner` in `derive()`.
6. **Out of scope**, by Lem's decision 1 of this task: the question page
   (`skills/lem-ask/runtime/ask.css`) and the agdoc page of a task keep their own look.

## What this plan will not verify

- agterm's own web view: the tests draw in headless Chrome and give the page its background the
  way `board-showcase.py` does. Whether agterm sets `--agterm-background` on every page it opens,
  and whether it sets it again when the owner changes the terminal's theme while a page is open, is
  not checked by any test here; the builder of task 1 says what it read of it.
- How the board looks to the eye: the tests measure places, heights, contrast and texts. The
  pictures of task 4 are where a person looks.
