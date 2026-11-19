# A landing page for Lem on GitHub Pages

careful: no, because no task reaches a topic: the page is a static `site/` folder and a workflow that runs only by hand, outside every plugin folder Claude Code reads (`agents/`, `bin/`, `hooks/`, `skills/`, `.claude-plugin/`), so "Lem as a plugin ... brings a hook or a command he did not install" is not reached; the rulings the page meets (no CI on a push, the README's STE, the logo unchanged, no report of what ran) are kept by the criteria and the directions; and the page starts no product code that other code copies.

## Acceptance criteria

Size: full, because the page is a new folder, a new workflow and a new row of the test map, with its text and look settled in an interview.

1. A developer who opens the page sees in its first screen what Lem is, what it needs and how to install it: at a window of 1280 by 800, the first screen shows the logo, one line of what Lem does (as the README's "Type a request in plain words, and get a pull request whose first line says green or not green."), and the two lines `claude plugin marketplace add pySilver/lem --scope project` and `claude plugin install lem@lem --scope project`, each with a copy button. Under them one line says "Lem needs agterm." with a link to agterm, and "Run the two lines in your repository, then type /lem init."
   - test: `bash tests/test-site.sh` in `tests/test-site.sh`
2. The page is light: one page of five sections and 600 to 900 words of visible text, in this order: the opening (the logo, the line, the install), how a task goes from a request to a pull request on the fast track and on the standard track as one small diagram, the three points where Lem needs the developer (the interview, his yes to the acceptance criteria, the merge), one picture of the board, and the install again with a footer that links to the five guides in `docs/` and to the repository. The diagram shows where each track stops for the developer: the fast track stops only at the merge. One sentence says "Green means you can merge without a read." Near the second install block, one sentence says what Lem keeps in a repository (the `.lem/` folder and its settings in git) and links to the removal steps in `docs/install.md`. A count of the page's visible words gives a number from 600 to 900.
   - test: `bash tests/test-site.sh` in `tests/test-site.sh`
3. The text reads as the README does, in ASD-STE100: no description sentence has more than 25 words and no instruction more than 20; it says nothing about what ran and nothing about history; it names no operating system and calls Lem a plugin for Claude Code that works closely with agterm, and says beside it that Lem needs agterm; an example dialog on the page is marked as an illustration, and the caption of the board picture says that it shows demo data.
   - test: `bash tests/test-site.sh` in `tests/test-site.sh`
4. The page follows the visitor's system theme and has no switch: with the system in dark mode it shows the night logo `assets/lem-night.svg`, the picture `assets/screens/board-dark.png` and a dark background; in light mode `assets/lem.svg` and `assets/screens/board-light.png`. Its colors are the six hues of `skills/lem/assets/lem.css`.
   - test: `bash tests/test-site.sh` in `tests/test-site.sh`
5. A repository that installs Lem gets nothing new from this page. The plugin's own copy gains only `index.html`, one stylesheet and the workflow file, which never runs there: the folder `site/` on `main` holds `index.html` and one stylesheet and no image, and the logo and the board pictures stay where they are in `assets/`. The README, the guides in `docs/` and every other file of the plugin are as before.
   - test: `bash tests/test-site.sh` in `tests/test-site.sh`
6. Lem's maintainer publishes the page with one workflow that he starts by hand: `.github/workflows/pages.yml` runs only on "Run workflow" (`workflow_dispatch`), never on a push, and publishes `site/` with the logo and the board pictures copied in from `assets/`. The workflow stays in Lem's repository and adds nothing to the `.github/` folder of a repository that uses Lem. The same copy, made on the machine, gives a folder in which the page opens with every image and every link to a guide working; after he sets the source of Pages to "GitHub Actions" and runs the workflow, the page opens at `https://pysilver.github.io/lem/`.
   - test: `bash tests/test-site.sh` in `tests/test-site.sh`

## Tasks

1. **The page, its workflow and its suite.** Serves criteria 1 to 6. Files: `site/index.html`,
   `site/style.css`, `.github/workflows/pages.yml`, `tests/test-site.sh` (new), `tests/all.sh`
   (the suite in its list), `tests/pick.py` (a row of `MAP` for `site/*` and
   `.github/workflows/pages.yml`, and `test-site` in `CHROME` and `CHROME_OWN`, since it loads the
   page in headless Chrome).
   - *The page*: one `index.html` with five `<section>` elements in the order of criterion 2, then
     a `<footer>`; one `style.css`; a small inline `<script>` in `index.html` for the copy buttons
     only, no library, no web font, no request to another host for anything the page draws. The
     look is Lem's own: the six hues of `skills/lem/assets/lem.css` with the same values, the round
     boxes and the system type of the board (`lem.css`, `board.html`), light and dark by
     `prefers-color-scheme` with `color-scheme: light dark` and no switch. The logo and the board
     picture are `<picture>` elements with a `(prefers-color-scheme: dark)` source, as the README
     has them. The three inspiration sites (agterm.com, revmux.com, ralphex.com) are looked at as
     screenshots first, for their lightness and their order, never copied. The text is written in
     the README's voice and its STE rules, from the README and the guides: no word it adds that
     the README does not use for the same thing.
   - *The diagram*: inline HTML and CSS (or inline SVG) in `index.html`, two rows, the fast track
     and the standard track, from "your request" to "pull request". Each step where the developer
     acts is marked the same way in the markup (one class) and in the look (the `--you` ochre):
     the fast track has one such step, the merge; the standard track three, the interview, his yes
     to the criteria and the merge.
   - *The workflow*: `on: workflow_dispatch` and no other trigger; `permissions` of `pages: write`
     and `id-token: write`; the `github-pages` environment; checkout, then one step with a fixed
     `name:` whose `run:` makes `_site/` from `site/*` and the four pictures
     (`assets/lem.svg`, `assets/lem-night.svg`, `assets/screens/board-light.png`,
     `assets/screens/board-dark.png`) at the same paths under `_site/` as in the repository, then
     the upload of `_site` and the deploy with GitHub's own Pages actions, at the newest major
     version their releases show (`gh api repos/actions/deploy-pages/releases/latest` and the same
     for `upload-pages-artifact` and `configure-pages`).
   - *The suite* `tests/test-site.sh`, in the form of `tests/checks.sh` (`collected`, `pass`,
     `fail`, `skip_rest`, `results_add_up`), Chrome found and started as `tests/test-board.sh`
     does (`--use-mock-keychain`, a throwaway `--user-data-dir` and temporary folder in the work
     folder). It takes the text of the workflow's copy step out of `pages.yml` by its `name:` and
     runs it in a throwaway folder that holds a copy of `site/` and `assets/`, so the copy it checks
     is the workflow's own; each check of a page reads that folder. The checks without Chrome
     (word count, sentences, words, links, the workflow, the files of `site/`) run everywhere; the
     checks that need a drawn page print `SKIP` lines where no Chrome starts. What it checks, by
     criterion:
     1. at 1280 by 800, the bottom of the logo, the line, both install lines, both copy buttons and
        the line "Lem needs agterm." with its link to `https://agterm.com` and "Run the two lines
        in your repository, then type /lem init." are inside the first 800 pixels; the two lines'
        text is exact; each copy button copies its own line (a probe in the throwaway copy may
        stand in for `navigator.clipboard`);
     2. five sections in the order of the criterion and a footer; the word count of the visible
        text (the body's text outside `script` and `style`) is from 600 to 900; the diagram's
        fast track has one step for the developer and it is the merge, the standard track three;
        the sentence "Green means you can merge without a read." is there; the second install
        block has the two lines and a sentence that names `.lem/` with a link to the removal steps
        of `docs/install.md`; the footer links the five guides and the repository;
     3. no sentence of the visible text has more than 25 words, and none that starts with an
        imperative verb more than 20; no operating system is named (`macOS`, `Mac`, `Linux`,
        `Windows`); no word of what ran or of history (`proven`, `not run`, `previously`, `no
        longer`, `new in`, a year); the words "a plugin for Claude Code that works closely with
        agterm" and "Lem needs agterm." are there; every example dialog (an element the page marks
        as one) has a caption with "illustration"; the board picture's caption says "demo data";
     4. drawn in light and in dark (headless Chrome's dark emulation; a check that the two draws
        differ in the background color proves that the flag took), the logo's and the board's
        `currentSrc` are the files the criterion names for that theme and each image loaded
        (`naturalWidth > 0`); the page has no button or control that switches the theme; the six
        hues in `style.css` have the values of `lem.css`, and every other color in it is a grey or
        a mix of those;
     5. `git ls-files site` gives `site/index.html` and `site/style.css` and nothing else; no file
        under `site/` is an image;
     6. `pages.yml` has `workflow_dispatch` as its only trigger and no `push`, `pull_request` or
        `schedule`; the copied folder holds the four pictures at the paths the page names; every
        guide link of the page has its file in `docs/` of the checkout and every `#` part of a link
        names a heading of that file, as GitHub makes its anchors.
   - Run with `bash tests/test-site.sh`, `bash tests/shellcheck.sh tests/test-site.sh tests/all.sh`
     and `python3 -I -B tests/pick.py --check`. Never `bash tests/all.sh`.
2. **The agent document.** Serves no criterion. `AGENTS.md` describes the current state, and the
   change makes three places of it false: "Layout" (a bullet for `site/`, the page that
   `.github/workflows/pages.yml` publishes by hand with the pictures of `assets/`, and that the
   install of the plugin carries and never runs; the sentence on `.github/workflows/ci.yml` names
   `pages.yml` beside it), "Checks" (the line `bash tests/test-site.sh` with what it checks, in the
   form of the other suite lines), and the bullet on `tests/` where it names what `pick.py` holds
   only if it then reads false. The README and the guides in `docs/` stay as they are (the
   task's "Out of scope"). Check: `bash tests/lem-settings.sh` only if a line it reads changed;
   otherwise no suite reads `AGENTS.md` (`tests/pick.py`, last row of `MAP`).

## Decisions

Each is logged with `lem decisions log --by lead`.

- **The guide links are GitHub's pages of the guides**,
  `https://github.com/pySilver/lem/blob/main/docs/NAME.md`. The copy the workflow publishes holds
  only the page and its pictures (criterion 6), so a relative link to `docs/` would break on
  Pages; GitHub draws the guides with their Mermaid charts. "Working" on the machine means the
  file and its heading exist in the checkout, since the repository is private until the
  maintainer makes it public.
- **The footer links the five guides and the settings reference**: `flow.md`,
  `when-lem-needs-you.md`, `pull-request.md`, `install.md` and `linear.md` are the five guides
  `AGENTS.md` names, and `settings.md`, the reference, is in the README's list of guides too.
- **The pictures keep their repository paths in the published folder** (`assets/lem.svg`,
  `assets/screens/board-light.png`, ...), so the page names them as `assets/...` and the
  workflow's copy step is a plain copy that the suite can run as written.
- **The diagram is HTML and CSS in the page, not Mermaid**: a Mermaid chart needs a script
  library from another host or a copy in `site/`, and criterion 5 allows `index.html` and one
  stylesheet only.
- **Criterion 5's "every other file of the plugin" is read as the files a user of the plugin
  meets**: the README, the guides, the skills, `agents/`, `bin/`, `hooks/` and `.claude-plugin/`
  stay as they are. The repository's own development files change as any task of Lem changes
  them: this plan, the suite `tests/test-site.sh` with its rows in `tests/all.sh` and
  `tests/pick.py` (the task's "Done when" asks `pick.py` to know `site/`), and `AGENTS.md`, whose
  "Layout" must describe the current state.

## Not verified

- The workflow's run on GitHub and the page at `https://pysilver.github.io/lem/`: Pages is off and
  the repository is private; turning Pages on and running the workflow are the maintainer's steps
  on the day the repository goes public (the task's "Out of scope"). The suite checks the
  workflow's text and runs its copy step on the machine.
- The links to GitHub answer only once the repository is public; the suite checks their targets
  in the checkout.
- A copy button in a browser other than headless Chrome.
