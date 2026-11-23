# Lem's page proves one claim: Lem asks little of you

careful: no, because the change is the text and the look of `site/`, two lines and one section of `README.md`, and the page's own test; it reaches no record, no landing, no push and no hook. Of the 13 topics only "A change bends a ruling of the owner" is near, and the change keeps every ruling of "The README, the guides and the logo" (STE, an illustration says so, no history, the logo stays), which `tests/test-site.sh` checks; the Inbox goes on the owner's own word.

## Acceptance criteria

Size: full, because the page gets four new sections and a new order, and the README and the page's test change with it.

1. Under the lead line, the hero of the page has one more line that says who Lem is for, and the README has the same line under its lead line:
   1. A visitor opens the page in a window of 1280 x 800.
   2. Under the lead line, the visitor reads "For a developer who works alone, and for a team on Linear or GitHub Issues."
   3. The two install lines, both copy buttons and "Lem needs agterm." are still in that first screen.
2. Section 01, "A task needs you three times at most", shows the three touches of `docs/when-lem-needs-you.md` as three cards: the shape (the interview and your yes to the criteria), a circuit breaker, and a pull request that the merge agent calls you for. Below the cards are the two tracks and the two dialogs of the present page, each dialog still captioned as an illustration.
3. Section 02, "What you can rely on", lists the five guarantees of the README in their words, then the block "Green, or not green with each reason" with its sentence "Green means you can merge without a read." and its picture. One sentence says what "careful" means, after `docs/flow.md`: a change that can affect what you said must never go wrong is careful, every reviewer reads it, and you merge it.
4. A section "Lem learns your repository" names the profile, the personas, the lessons and the rulings, and says that each is a file in your repository's git. It says that a second model family, Codex, reviews the larger changes and answers as a second expert.
5. A section "Start from a ticket" shows `/lem new ABC-12` for a Linear ticket and `/lem new 42` for a GitHub issue. It says what a team shares and what stays with each developer:
   1. Ana and Ben work on one repository with Lem and Linear.
   2. They share the settings in git, the tickets and the pull requests.
   3. Ana's board shows the tasks on Ana's computer, and Ben's board shows the tasks on Ben's.
6. The install section keeps its present block and its link to the removal steps, and says that Lem is MIT, with a link to `LICENSE`.
7. The README holds each new fact the page states that no guide states: the line of criterion 1, what a team shares and that each developer has their own board, and that Lem is MIT.
8. Neither the page nor the README names the Plannotator Inbox: `grep -i plannotator site/index.html README.md` prints nothing. The guides keep their own lines.
9. The dot "You can act here" is the one mark of the page for a step of the owner: each such step in the diagram and on the three cards carries it, and no other sign marks one.
10. The sections "The board", "On your phone" and "Many tasks at once" keep their text, except the Inbox sentence of criterion 8 and the green block that moves to section 02. The page's order is: the hero, 01, 02, the board, on your phone, many tasks at once, Lem learns your repository, start from a ticket, install.
11. The copy buttons stay the page's one script, and `bash tests/test-site.sh` passes. Its list of sections follows the new page, and its upper limit of visible words rises to the new count, rounded up to the next hundred.

## The page after the change

The order and the ids, top to bottom. An id that the page has today stays, so the nav and every link
to `#board`, `#flow`, `#phone` and `#install` stay true; the nav keeps its four links and GitHub.

| Id | Eyebrow | Heading | What it holds |
| --- | --- | --- | --- |
| `start` | none | the logo | the lead line, the new line of criterion 1 (`p.for`), `.sub`, the install block, `.needs`, the showcase |
| `flow` | 01 · How a task goes | A task needs you three times at most | three cards (the three touches), then the diagram of the two tracks with its legend, then the present text and the two dialogs |
| `rely` | 02 · Guarantees | What you can rely on | the five guarantees of the README word for word, the sentence of careful, then the block "Green, or not green with each reason" with its picture, as it is today in `#parallel` |
| `board` | 03 · The board | as today | as today |
| `phone` | 04 · On your phone | as today | as today, without the Inbox paragraph |
| `parallel` | 05 · Many tasks at once | as today | its intro and three cards, without the green block |
| `learns` | 06 · Your repository | Lem learns your repository | the profile, the personas, the lessons and the rulings, each a file in your repository's git, and Codex as the second model family |
| `tickets` | 07 · Teams | Start from a ticket | `/lem new ABC-12` and `/lem new 42`, each with its guide's link, what a team shares, and that each developer has their own board |
| `install` | 08 · Install | as today | as today, and one more sentence: Lem has the MIT License, with a link to `LICENSE` |

The words of the new parts come from the README and the guides, in their STE:

- The three cards: "Three touches" of `docs/when-lem-needs-you.md`: the shape (on the standard
  track, you answer the interview and say yes to the acceptance criteria), a circuit breaker (a task
  stops, and leaves a document for you), a pull request that the merge agent calls you for (you read
  its review, and merge).
- The sentence of careful: "Careful" of `docs/flow.md`: a change that can affect what you said must
  never go wrong is careful, every reviewer reads it, and you merge it.
- The four files: "What Lem keeps" of `docs/install.md`: `.lem/profile.md` (the product),
  `.lem/personas/` (the people that a change affects), `.lem/lessons.md` (your corrections of how an
  agent does a step), `docs/rulings.md` (your decisions, which no agent reopens without asking you).
- Codex: the README's tip, in the criterion's words: a second model family, Codex, reviews the larger
  changes and answers as a second expert.
- The tickets: "Start a task from a ticket" of `docs/linear.md` and "Start a task from an issue" of
  `docs/github-issues.md`. A `/lem` line is a `<code>` in the text, not a `.cmd` row: a `.cmd` row
  draws a `$ ` before its line and gets a copy button, and `/lem new` is typed in Claude Code, not
  in a shell.

The README gets three things, each the source of a fact the page states:

- the line of criterion 1, as a paragraph of its own directly under the lead sentence of line 10;
  the two sentences after the lead sentence become the next paragraph;
- in "The board, also on your phone", in the place of the Inbox sentence: "A team shares the
  settings in git, the tickets and the pull requests. Each developer has their own board, with the
  tasks on their own computer.";
- a last section, `## License`: "Lem has the [MIT License](LICENSE)."

## Tasks

1. **The page's new order and words, the README's three facts, and the suite's checks of them.**
   Criteria 1, 2, 3, 4, 5, 6, 7, 8, 10 and 11. Build the page of the table above in
   `site/index.html` and its look in `site/style.css` (a new part reuses the page's classes and
   its six hues, and brings no hue of its own); write the README's three facts and remove its Inbox
   sentence; change `tests/test-site.sh` so that it checks the new page:
   - `sections`: the nine ids in the order above, and its pass line says so;
   - `words`: the upper limit is the new count of visible words rounded up to the next hundred, the
     lower limit stays 800, and its pass line says the new range;
   - a check of the hero's new line, on the page directly after `.lead` and in the README directly
     under its lead sentence, word for word;
   - a check for each new section: `flow` holds the three cards before the diagram and the two
     dialogs; `rely` holds each bullet of the README's "What you can rely on", read from
     `README.md` so the two cannot drift, the sentence of careful, the green block and the task
     picture; `learns` names the four files, git and Codex as the second model family; `tickets`
     holds `/lem new ABC-12`, `/lem new 42`, links to the two guides' headings, the team sentence
     and the own board; `install` says MIT and links `LICENSE`, and the README does too;
   - a check that `site/index.html` and `README.md` hold no "plannotator" in any case;
   - a check that `board`, `phone` and `parallel` keep their heading and their intro;
   - the drawn checks of the first screen, the layer and the contrast take the new line as an
     eighth hero text, so that criterion 1's case 3 is held at 1280 x 800;
   - `tests/pick.py` maps `README.md` to the suite `test-site`, since the suite now reads it, and
     `python3 tests/pick.py --check` passes.
   Files: `site/index.html`, `site/style.css`, `README.md`, `tests/test-site.sh`, `tests/pick.py`.
2. **The dot "You can act here" as the one mark of a step of the owner.** Criterion 9. Each
   `li.step.you` of the diagram and each of the three cards of `#flow` holds the dot
   (`<i class="dot" aria-hidden="true"></i>`), the legend stays as its key, and `site/style.css`
   takes away the other mark: the tinted border, the tinted background and the tinted title of
   `.step.you`. The class `you` stays on those steps, for the suite. `tests/test-site.sh`:
   `diagram` also checks that each `.step.you` has one dot and no other step has one; a new check
   says that each card of the three touches has one, that no element outside these steps, these
   cards and the legend has the class `dot`, and that no rule of the stylesheet gives `.step.you` a
   border, a background or a color of its own.
   Files: `site/index.html`, `site/style.css`, `tests/test-site.sh`.

Task 2 starts after task 1 ended: both change the same three files.

## Decisions

- The ids `start`, `flow`, `board`, `phone`, `parallel` and `install` stay, and the nav keeps its
  four links: each link to the page stays true, and a fifth link in the hero's nav would push the
  first screen down (decision 6).
- The dot's reach: the dot marks the owner's steps of the diagram and the three cards. The word
  "you" before a line of a dialog names who speaks, and the numbers of the phone's setup steps give
  their order; neither marks a step of the owner, and both stay as they are (decision 7).
- The README's places for its three facts, as above: the line under the lead sentence, the team
  sentence where the Inbox sentence was, and `## License` last (decision 8).
- The words of the eyebrows: "01 · How a task goes", "02 · Guarantees", "06 · Your repository",
  "07 · Teams", and the others renumbered in the new order (decision 9).

## Not verified

- The page as GitHub Pages serves it: `.github/workflows/pages.yml` publishes only when someone
  starts it by hand, and this task does not start it. `tests/test-site.sh` runs its copy step.
- The drawn checks need headless Chrome; where none starts they print SKIP lines.
