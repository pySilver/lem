# The status boards: one steady look, with tabs, in Lem's own light and dark

careful: no, because no task changes a record, a script that writes one, the text of a pull request or a git act: the board reads `events.js`, `meta.js` and `backlog.js` and writes nothing, `land.py`'s green and its reasons are untouched, and the board's one action (the backlog's "Start a task", which types `/lem new PATH` into Lem's session) keeps its code and its test in `tests/lem-settings.sh`.

## Acceptance criteria

Size: full, because the change redraws the whole board page and `lem.css`, which every page of Lem links, and it adds tabs to both boards.

1. Each button of the board has one fixed place, whatever the length of the texts beside it: on the board of one task, "All tasks" and the button to Lem's session stay at the top right both for the title "fix: the dates stay whole" and for a title of 160 characters, in a window 900 px wide and in one 1400 px wide; a long title wraps to two lines at most and shows whole when the owner points at it or moves the focus to it; the button to Lem's session says that it goes to Lem's session; and every card that has an action ("Open the task", "Start a task" in the backlog) has it at the same side.
   - test: `bash tests/test-board.sh` in `tests/test-board.sh`, `tests/checks.sh`
2. A card does not change its shape with the length of its text: two task cards in one lane, one with an ask of one line and one with an ask of 300 characters, have the same height. Only the ask is cut, after its last whole line; the card's state and a mark that something waits for the owner always show. The Tab key reaches each card, and the long ask shows whole when the owner points at the card or moves the focus to it.
   - test: `bash tests/test-board.sh` in `tests/test-board.sh`, `tests/checks.sh`
3. The board takes Lem's own light or dark palette from agterm's background: with the background `#15181c` it draws dark with the night logo, with `#ffffff` and with Solarized light's `#fdf6e3` it draws light with the day logo, and with Solarized's `#002b36` its cards and text use Lem's dark palette and no Solarized color. Opened outside agterm, with no background to read, it follows the system's light or dark setting. In both palettes body text and the small labels (lane names, times, status words) have a contrast of at least 4.5 to 1 against their background.
   - test: `bash tests/test-board.sh` in `tests/test-board.sh`, `tests/checks.sh`
4. The board of all tasks has three tabs, "Tasks", "Waits for you" and "Backlog": with two choices that wait, one task whose criteria wait for the owner's yes and one green pull request, "Waits for you" shows the count 4 and lists those four, each row saying what the owner does there: answer a choice, approve the criteria, or merge the pull request. The tab the owner chose stays chosen when the page draws itself again every second, and so does a text he selected in the backlog.
   - test: `bash tests/test-board.sh` in `tests/test-board.sh`, `tests/checks.sh`
5. The board of one task has four tabs, "Overview", "Criteria and decisions", "Checks and review" and "Timeline", and its first view says green or not green with its reasons in plain words: a task whose pull request is not green because the experts took choice 2 shows on "Overview", with no click, "not green: two outside experts chose option 2 while you were away". The tab the owner chose stays chosen when the page draws itself again.
   - test: `bash tests/test-board.sh` in `tests/test-board.sh`, `tests/checks.sh`
6. Every page of Lem that links `lem.css` has the board's look: the onboarding page shows the same header, fonts and colors as the board, in light and in dark.
   - test: `bash tests/test-board.sh` in `tests/test-board.sh`, `tests/checks.sh`
7. The pictures of the board in the README and in `docs/when-lem-needs-you.md` show the new board, in light and in dark, and each caption says that the picture shows example tasks.
   - no test: what a picture shows is read by a person's eye, and no suite reads the README or the guides; the builder of task 4 read each of the six pictures in light and in dark
8. The backlog item `docs/backlog/board-as-a-tabbed-interface.md` is closed by this change: its file is removed.
   - no test: the removal of one file, which the branch's diff shows

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
   button, one card, one tab bar, one chip, in two palettes of Lem's own. The palette is the one
   agterm already chose for the page (decision 3): the `color-scheme` its theme stylesheet sets on
   `html`, and the system's setting when no agterm theme is there; no agterm color is used, and
   Lem computes no luminance of its own. `lem.css` sets no `color-scheme` on the root element except
   under the palette mark that `lem.js` sets, so that it never hides agterm's before `lem.js` reads
   it. The tests of criterion 3 put agterm's own stylesheet into the page, the line
   `HtmlOverlayTheme.stylesheet` writes (`:where(html) { color-scheme: dark; color: …;
   --agterm-background: #15181c; … }`), with the scheme agterm's rule gives each color of the
   criterion, and add `#d8b590` (an installed light theme just under the middle of relative
   luminance), which must draw light. The header is the
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
   have one height, and only the ask is cut. A card has its rows in one order: the title; the ask,
   cut after its last whole line of two; the state line, which always says the task's state and
   is never replaced by the text of a choice (today `cardLine` puts "Choice N waits for you: …" in
   its place); one wait mark, "choice N waits" or "N choices wait", in the place of today's badge
   for each further choice in `tags`, with each choice's text in its hover and in its row of
   "Waits for you"; then the tags. The cards of a lane share one height: the lane is a grid of
   equal rows (`grid-auto-rows: 1fr`), so a longer title or a row of tags that wraps makes every
   card of that lane taller together, and nothing but the ask is cut. The test of criterion 2
   puts into one lane a card with an ask of one line and a card with an ask of 300 characters
   whose task builds while a choice with a long text and a second choice wait, and checks the
   equal heights, the state line on both and the wait mark. The card takes the focus with Tab,
   and the whole ask shows on hover and on focus. Every card with an action has it at the same side ("Open the
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
   one height whatever its lines, and "Go to the session" one place. The check that the line of
   criterion 5 is there "with no click" reads only the text that is not under an element with
   `hidden` (decision 2), and it fails when the same line is only in a panel of another tab.
   Serves criterion 5. Files: `skills/lem/assets/board.html`, `tests/test-board.sh`.
4. **The pictures, the documents, and the backlog item closed.** `tests/board-showcase.py` draws
   the new board (it adds what the tabs need, such as a picture of "Waits for you" when it helps
   the README) and the pictures in `assets/screens/` are made again, light and dark; it gives dark
   by agterm's theme stylesheet, as the tests of task 1 do, since `--agterm-background` alone no
   longer chooses the palette (decision 3). The captions
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

## Plan talk

Argued on 2026-11-19 in the task's companion session: the reviewer was Codex, GPT 6.2 Sol at high
effort, as its pane's status line showed (a fresh pane, 5% of its context used); the defender
was Claude Code, Opus 5.5 at high effort, as the task's state gives (`defender: Opus 5.5, high`).
Two families. 7 turns, 5 questions, under the bound of 22 that the rules give for 5 questions.

The list, as the reviewer gave it in its first turn:

1. **Decision 4, the reasons of "not green": a `decision N` line and a night's choice.** The plan
   replaced every line that begins with `choice N ` or `decision N `, but gave words only for a
   `timeout` choice, and a night's task takes its choice at once while the owner's status is
   there, so "while you were away" would be false. Repaired once (only `choice N ` lines are
   replaced; "while you were away" only when the newest `owner` event before the choice's time
   says away, else "while the task ran without you"). The reviewer: `holds, layer over D4`: the
   `owner` event and the choice that `cmd_away` takes share one whole second (`project.py`
   `append_event`, `decisions.py` `stamp`), so "strictly before" misses the away that caused
   the choice. The defender checked it and had no refutation. **A design choice**: the plan's
   rule (the newest `owner` event strictly before the choice's time), against the reviewer's
   (an `owner` event of the same second counts too). Taken up after the talk by `stages/plan.md`,
   step 5: the gate found it checkable in the code and took the reviewer's rule (decision 2 of the
   task's record); decision 4 of the plan says it.
2. **Decision 5, "Waits for you": one action counted twice, and a merge verb on a conflicting
   request.** A task `held` with "choice N waits for the owner" is the same action as its choice,
   and `watch.js` can call an open request `CONFLICTING`. Repaired once (one row for a held task
   whose choice waits, as `buildBanners` does; a request that `watch.js` calls `CONFLICTING`
   gets no merge verb). The reviewer: `holds, layer over D5`: after Lem repairs the conflict
   and proposes again, `watch.js` still says `CONFLICTING` for the old head until the next watch
   looks, which with two conflicting requests is the length of the second repair (`stages/land.md`,
   step 9, starts the watch again last); `cmd_watch` records each entry's `head`, and
   `project.py` `proposal` checks it. The defender checked it and had no refutation. **A design
   choice**: the plan's rule (`CONFLICTING` in `watch.js`), against the reviewer's (only when
   the entry's `head` is the head of the newest proposal, the `tip` of its `proposed` event).
   Taken up after the talk by `stages/plan.md`, step 5: the gate found it checkable ("Lem owns
   the truth of its words … each state on the board", `AGENTS.md`) and took the reviewer's rule
   (decision 3 of the task's record); decision 5 of the plan says it.
3. **Decision 3, the palette's cutoff.** The middle of relative luminance does not match
   agterm's own light or dark: the installed Desert Morning, `#d8b590`, falls under it while
   agterm calls it light. Settled: decision 3 changed, so that `lem.js` takes the `color-scheme`
   agterm's theme stylesheet sets on `html` (`HtmlOverlayTheme.stylesheet`,
   `ThemeBrightness.isDark`) and Lem computes no luminance; a changed theme reloads the file page
   (`applyTheme`). The reviewer: `closed, at the cause`. Settled by the two, not checked by the
   review.
4. **Decision 2, the redraw: a selection in the backlog and a check that reads hidden text.**
   The plan drew every panel on every redraw, and the `SHOWN` helper of `test-board.sh` reads
   text under `hidden`. Repaired once (each panel keeps its redraw of today, the backlog by
   `blDrawn`; each check of what a tab shows skips text under `hidden`). The reviewer: `holds,
   layer over D2`: when Lem's session goes back to the shell, `agentRuns(lemNow)` in the
   backlog's key changes, `renderBacklog` replaces the whole group, and a selected sentence of an
   item's body is lost on that draw. The defender refuted it: that draw changes what each item
   shows ("Start a task" becomes "No agent runs in Lem's session now…", `board.html` lines
   2082-2083), and criterion 4 names the redraw of every second. The reviewer: `holds` a second
   time: the draw comes from the `setInterval(render, 1000)` call, and the criterion gives no
   exception for a changed action text beside the selection. **A design choice**: the plan's
   rule (the backlog drawn again whole when what it shows changed, `agentRuns` included),
   against the reviewer's (a selection survives that draw too). Taken up after the talk by
   `stages/plan.md`, step 5: the gate held it; the personas split (the developer for redrawing
   only the changed foot lines, the newcomer for one band above the backlog), none for the plan's
   rule; the dialectic confirmed a break of the developer's option (a selected command in a
   changed foot is lost); both experts picked a fourth design, the backlog patched by keys down
   to the foot's parts (decision 4 of the task's record, by the experts); decision 2 of the plan
   says it.
5. **Task 2, cards of one height: what shows when a task builds while a long choice waits.**
   `cardLine` puts the choice's text in the place of the state, `.tc-text` cuts it after two
   lines, and `tags` adds a badge for each further choice. Settled: task 2 gives the card a fixed
   order of rows (a state line never replaced, one wait mark, the choice's text in the hover and
   in its row) and lanes of equal rows (`grid-auto-rows: 1fr`), with a test of that input. The
   reviewer: `closed, at the cause`. Settled by the two, not checked by the review.

Mechanisms a repair added, with the decision each sits on and the reviewer's word:

- the away test of a choice's plain line (question 1): a layer over decision 4, which rests on
  criterion 5's words and the `owner` events the board reads; `holds`, a design choice.
- the row of a conflicting request with no merge verb (question 2): a layer over decision 5,
  which rests on `cmd_waiting` and `watch.js`; `holds`, a design choice.
- the check of what a tab shows that skips text under `hidden` (question 4): a layer over
  decision 2, which rests on the owner's direction "No information goes away" and `render()`;
  the reviewer called the check itself an answer to the false pass, and the question held on the
  selection.
- the read of agterm's `color-scheme` by `lem.js` (question 3): at the cause, decision 3 changed.
- the fixed rows of a card and the lane of equal rows (question 5): at the cause, task 2 changed.

No question was raised after the first turn. No addition was refused as unpriced.

What changed in the plan, by question and by task: task 1 takes agterm's `color-scheme` and puts
agterm's stylesheet into its tests, with `#d8b590` (question 3); task 2 has the card's fixed
rows, one wait mark and lanes of equal rows, and its test of a long choice (question 5); task 3's
check of the line of criterion 5 skips hidden text (question 4); task 4's pictures give dark by
agterm's stylesheet (question 3); decision 2 keeps each panel's redraw of today and names the
hidden-aware check (question 4); decision 3 is the palette agterm chose (question 3); decision 4
replaces only `choice N ` lines and says "while you were away" only for an away span
(question 1); decision 5 counts a held task with a waiting choice once and gives a conflicting
request no merge verb (question 2); "What this plan will not verify" names agterm's stylesheet
and its reload as read in its source (question 3).

## Decisions the plan takes

1. **Four tasks, one after another.** The two boards are two outcomes with criteria of their own,
   each a reviewer can check alone, and the design system under them is a third; all three edit
   `board.html`, so they run in order. The pictures come last, since they are of the finished
   board. Rests on: the criteria, which name the two boards apart (4 and 5), and the size of
   `board.html`.
2. **A tab hides its panel and never removes it.** Every panel stays in the page, and the panels
   of the other tabs carry `hidden`. The panels of tasks are patched by keys every second, as
   today. The backlog is patched by keys too, with `patch()` and `keyed()`, down to the foot's
   parts, in the place of today's `replaceChildren` of the whole group: a node whose markup did not
   change keeps its place, so a selection in an item's body or in an unchanged `<code>` command of
   its foot survives every draw, also when an agent in Lem's session stops or starts and when a
   read of agterm's sessions fails, and only the words that changed are swapped. `patch()`
   compares a parent's direct children, so the group, the item (its `cur` class and
   `aria-expanded` set in place), `.bl-body` and `.bl-actions` are each patched at their own level,
   with the note, the button and the `<code>` of `itemActions()` as keyed parts. The test of
   criterion 4 selects a sentence of a body and a command of a foot, changes whether an agent runs
   and makes a read of the sessions fail, and finds both selections still there; the Start journey
   of `tests/lem-settings.sh` still passes (`askToStart()` gives the Start button the focus after
   the draw). Settled after the talk by the experts, both for this design, decision 4 of the
   task's record. Nothing the owner could see before is gone, a change of tab
   draws nothing again, and `test-board.sh`, which reads the DOM, still finds each part. Because a
   hidden panel is in the DOM, the `SHOWN` helper of `test-board.sh`, which reads every text but
   `script` and `style`, cannot tell what the owner sees on a tab: each check of what a tab shows
   (criteria 4 and 5) skips the text under an element with `hidden`, as a form of `SHOWN` or a
   helper beside it. Rests on: the owner's direction "No information goes away: the tabs handle
   the density" (`directions.md`), criterion 4, and `patch()`, which keeps a keyed block whose
   markup did not change.
3. **The palette is the one agterm chose, and a small script that every page of Lem loads beside
   `lem.css` takes it.** agterm already tells a file page whether its theme is light or dark: its
   theme stylesheet, put into the page at document start, sets `color-scheme: dark` or `light` on
   `html` from its own rule, Rec. 601 luminance under 0.5 (`HtmlOverlayTheme.stylesheet` in
   `agtermCore/Sources/agtermCore/HtmlOverlay.swift`, `ThemeBrightness.isDark`, called from
   `HtmlOverlayRegistry.theme`; read in the agterm source on 2026-11-19, not run). So Lem does not
   classify the color itself, and a theme agterm calls light is light on the board too: a rule of
   Lem's own (relative luminance against the middle) put the installed `#d8b590` on the dark side
   where agterm puts it on the light one. `lem.js` reads the root element's computed `color-scheme`
   once at load, before it sets the palette mark that `lem.css` keys its palettes on: `dark` or
   `light` is agterm's choice, and anything else (`normal`, no agterm theme) leaves it to
   `prefers-color-scheme`, which it follows when the system's setting changes. One read at load is
   enough inside agterm: a changed theme reloads a file page (`applyTheme` then `reloadShown` in
   `HtmlOverlayRegistry.swift`), and the board opens as such a page (`agtermctl session overlay
   open --html`, `board.py`). The script stays because the header shows one of two logos, which
   needs one mark on the root to show by, and because agterm's rule sits at zero specificity before
   the page's own styles: a `color-scheme` that `lem.css` set on the root for the system's setting
   would hide agterm's. One file
   holds that rule, as one file holds the look, so the board and the onboarding page cannot choose
   apart. The cost: `board.py` and the onboarding step copy one more file. Rests on: agterm's
   theme stylesheet (cited above), `board.py` `prepare` (it copies `lem.css` beside the page) and
   `stages/init.md` (it copies `handover.html` and `lem.css`).
4. **The reasons of not green are said in plain words from the records.** The line on "Overview"
   is built by the board from the task's decisions and its `proposed` event, never by parsing a
   whole sentence of `land.py`. A choice taken by the experts while the task ran without the owner
   (`state: timeout`, `by: experts`) is "two outside experts chose option N while you were away",
   or "one outside expert ..." when one answered (the `experts` of the record has one reason); N is
   the place of the chosen text in the choice's `options`, counted from 1, and the row names the
   choice beside it. A choice taken as the recommended option while he was away is "Lem took the
   recommended option of choice N while you were away". "While you were away" is said only when
   the owner's status was away at the time the choice was taken: the newest `owner` event at or
   before that time (the same second counts, since `cmd_owner` writes it and `cmd_away` takes the
   choice in one second; settled after the talk by the gate, decision 2 of the task's record) says
   `away` (the events `derive()` already reads for the header, line 848). A choice
   taken at once in a task that ran without him while he was there, which is a night's task
   (`stages/night.md`, step 3; `decisions.py`, the `timeout` of a task that runs without the
   owner), says "while the task ran without you" in its place. Only the lines of `not_green` that
   begin with `choice N ` (a choice that waited for him and was taken without him, `state:
   timeout`) are replaced by the plain line. Every other reason is shown in the words `land.py`
   wrote, since they are plain already and the board has no other record for them: a line that
   begins with `decision N ` (a decision past the personas, by the dialectic or the experts, or
   the lead's pick that no level settled: `decision N was taken without the owner (WHAT):
   "CHOSE", by the dialectic`), the bar, a changed criterion, the criteria not read, careful on the
   fast track, a review. The test's fixture takes
   option 2 of choice 2, so the line of criterion 5 reads the same in both readings of "choice 2"
   and "option 2". Rests on: `not_green()` and `without_him()` in `land.py`, and `decisionEvent()`
   in `board.html`.
5. **"Waits for you" has a row for each action of the owner's that the board can see.** One row
   for each choice that waits, each task whose criteria wait, each other held task (with its state
   line), each proposal that waits for his merge (green or not, with its reasons), and each plan
   whose lead said the owner reads it, as the lane "Waits for you" counts it today. A task is
   counted once for each thing he does: a task `held` with the line "choice N waits for the owner"
   (`stages/build.md`, "A choice in the build", step 4) is the row of that choice and no second
   row, as the banners do today (`buildBanners` draws a held task's row only for `status ===
   'held' && !asks.length`); `cmd_waiting` counts such a task twice, under `choices` and under
   `held`, which is a defect outside this task. A proposal whose pull request the forge calls
   conflicting with the base (its entry in `open` of `watch.js` has `mergeable: CONFLICTING` and a
   `head` that is the head of the task's newest proposal, the `tip` of its newest `proposed`
   event, as `project.py` `proposal` checks the forge's head; settled after the talk by the gate,
   decision 3 of the task's record) says that it conflicts with the base and that
   Lem brings it onto the base first (`stages/land.md`, step 9), and gives no merge verb; it is
   still counted, since its merge waits for him after that. It is `lem project waiting` without
   the retro proposals, which the board has no file for, and with the plans to read. Rests on:
   `cmd_waiting` in `project.py`, `forOwner` in `derive()`, `buildBanners` and `watch.js`.
6. **Out of scope**, by Lem's decision 1 of this task: the question page
   (`skills/lem-ask/runtime/ask.css`) and the agdoc page of a task keep their own look.

## What this plan will not verify

- agterm's own web view: the tests draw in headless Chrome and put agterm's theme stylesheet into
  the page. That agterm puts it into each file page it opens, and reloads such a page when the
  owner changes the terminal's theme, is read in the agterm source (decision 3) and checked by no
  test here.
- How the board looks to the eye: the tests measure places, heights, contrast and texts. The
  pictures of task 4 are where a person looks.
