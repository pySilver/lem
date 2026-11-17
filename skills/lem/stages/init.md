# init: onboarding a repository

`/lem init` takes a repository from nothing to a first task: it checks the machine, examines the
project, asks the owner three questions about what only he knows, and writes the project's
settings and profiles as drafts he adjusts. Everything else is read from the repository or
defaulted, and the hand-over page shows it as an assumption he corrects with one word. It runs
once per repository and stops before any task. The audit of 2026-11-16 counted about ten
questions and several offers before the first task, each a page, and 20 to 40 minutes to it (an
unmeasured estimate).

Keep the onboarding's notes in its own task directory: `project.py task-dir onboarding --ask
"Set up Lem in this repository"`. Write its state as any task's, so that the status and the
board show it and never a directory with no state: `held` with the line `the onboarding's
drafts wait for you` when the hand-over page is shown, and at the end `landed` or `dropped`, as
the three replies below say. The first onboarding in Lem's own repository wrote none, and
every later status listed a task whose state nobody wrote (2026-11-17).

On a repository that already has `.lem/project.toml`, `/lem init` finishes an onboarding: it
changes no setting that is there. Run step 1, skip the command of step 4 (it refuses a settings
file that exists, and that is right), and do steps 2, 3 and 5 only for what is missing or
unfinished: a path `project.py show` marks as not existing, and a cast of fewer than two
personas, which the `project personas` row of step 1 shows. That row never stops the
onboarding: writing the personas is what this stage is for.

The owner may ask for it from a session that started in another folder. Work in the repository
he names, and give every command its root. Before step 1, tell him that root as an absolute
path and put the repository's name on the session (the harness file says how): he may have
several sessions open, and one named "init" belongs to none of his repositories.

## 1. Check the machine

```bash
python3 SKILL_DIR/scripts/doctor.py
```

A required tool that is absent stops the onboarding: say which, what it is used for and how it is
installed, and end. Every other row is no question now: an optional tool that is absent is one
line of the hand-over page (the row's `without_it`), and a recommended tool that is absent, cronn
and the correction queue are offers in the short list at the end of that page (step 6). A
`correction hook` row (a settings file that still holds the hook an install of Lem before the
plugin wrote) is one line of that page too, with each file and the entry its guide says to delete
by hand.

## 2. Examine the project

Before any question, read what the repository already says, and write `examined.md` in the
onboarding directory, every line with the path it was read from:

- what the product is and who uses it: `README`, `AGENTS.md` or another agent document, the
  package metadata, the top of the documentation;
- the stack and its versions: the dependency and tool-version files;
- how it is checked: the test configuration, the CI files, a `Makefile` or task runner, and the
  git hooks: a `.pre-commit-config.yaml`, a `.husky/` folder, a `lefthook.yml`, the folder that
  `git config core.hooksPath` names, and each executable file that is no `.sample` in the hooks
  folder of the git directory (`git rev-parse --git-path hooks`). Write which hooks run at a
  commit and what each one runs. Note a sign of a suite that needs the machine to itself too: a
  Playwright, Cypress or Selenium configuration, a compose file for the tests. These become the
  commands of the checks;
- how work lands: the default branch, the branches the last fifty merges went into, whether
  commits are squashed, the form of the commit subjects, whether the remote is GitHub, and any
  branch nothing lands on (a release branch frozen for a rewrite);
- where the work is kept: a tracker the repository shows (Linear issue keys in branch names or
  commit subjects, a link to linear.app in its documents), with the team key it shows;
- where a defect costs most: migrations, money, authentication, anything that writes data which
  cannot be rebuilt, private data, the checks themselves. Most products have most of these, so
  look for each. They become the proposals of what must never go wrong: each one sentence in
  the terms of this product, of what a person would see go wrong ("a merchant's customer is
  charged the wrong price", not "money"), with the code you read it from beside it in
  `examined.md`. No path goes into the settings: an agent reads each change against the
  sentences;
- the conventions the code already keeps: how modules are laid out, how errors are raised, how
  tests are named and what they touch. Note one only where several files agree;
- `python3 SKILL_DIR/scripts/project.py existing`: the settings an older tool already keeps here
  (`.claude/rules`, `.personas`). The review tool's folder is not one of them: it is that tool's
  own, and the settings name it where it is.

In a large repository, `fan-out` one reader per area and merge what they return. A reader reports
what it read and where; it proposes nothing.

A repository with no code yet (`git ls-files` lists nothing beyond a README, a license or an
ignore file) has nothing to examine. Write that one line in `examined.md` and go to step 3, whose
first question is then about what the owner plans to build.

## 3. Three questions

Ask only what only the owner knows, one question at a time in the conversation, each with your
own proposal from `examined.md` so that he corrects a draft instead of composing one, by the
method of the `lem-interview-me` skill (`load-skill`). Three questions, and no fourth: what the
examination answered, and every setting with a default, is an assumption of the hand-over page.

An interview question goes straight to the owner. It does not pass the question gate or the
persona panel, its card gets no framing check, and its answer is not tested for a ruling: it
asks what the owner wants, which no ruling, probe or persona knows. Each answer has a place
already, the settings file or the profile, so no ruling file is written for it. The first
onboarding through Lem put its five questions through the gate: 11m 54s passed between the
owner's first answer and the second question, and three ruling files repeated three lines of the
settings (a scratch repository, 2026-11-15; the time is that session's status line as another
session read it).

1. **What the product is, and who it is for**: what it is judged against and how big it is meant
   to get. The code shows what exists; only the owner knows the rest. A new project, with no
   code to guess from, answers here what he plans to build, the first thing its person should be
   able to do with it (the first task after onboarding), and the stack he wants or "choose for
   me"; then propose one with its reason and what it costs to change later.
2. **The people a change affects**: a customer, an operator, a partner, the engineer on call.
   Each becomes a persona, and every project of Lem has them: before a hard question reaches the
   owner, an agent answers it as each person the decision affects. Propose two or more from what
   you examined, because a panel of one has nobody to disagree: the people the product serves,
   and, where there is no second kind of user, the people who run it or build the next change on
   it. Two people are worth it only when they would notice different things about the same
   change. The first onboarding wrote one persona, "a shop employee who reads report headings",
   and its own page said that this person could not tell the options of a question apart (a
   scratch repository, 2026-11-15).
3. **What must never go wrong here?** Your proposals from the code, each a sentence of what a
   person would see go wrong, with the code each came from beside it. Ask what is wrong or
   missing. No path is proposed or asked: a sentence still holds after the code moves, and an
   agent reads every ask, plan and diff against it. In a repository with no code, propose them
   from his description of the product.

An answer of "whatever you think" is not an answer to the third: say what you will assume and ask
for a yes. Stop after the third.

## 4. Write the settings

```bash
python3 SKILL_DIR/scripts/project.py init --base BRANCH --reviewer codex --existing link    # or: --existing new
```

Leave `--existing` out when `project.py existing` listed nothing, or the style guide alone: a
rules folder needs no choice, and every other folder it lists does. That choice is no question
either: link what is there, so the older tools and Lem read one copy and nothing moves, and say
so on the page, where "change folders new" generates new profiles under `.lem/` instead. The rules
an agent already loads by itself stay in their folder whatever `--existing` says, and the
settings name it as the style guide. Then edit `.lem/project.toml` with the three answers and
the assumptions of step 6:

- the commands of the checks from `examined.md`. `checks.commands` is the whole suite, which runs one time,
  in the checks before the pull request; no builder runs it. When git hooks run at a commit,
  propose only the test commands: the hooks run the formatter, the linter and the type check at
  each commit of a builder, and the checks need not run them again ("test runs only", the owner,
  2026-11-17). With no hooks, propose the linter and the type check the repository has as well;
- `checks.alone`, only when `examined.md` shows a sign of a suite that needs the machine to itself:
  the test command of that suite, your guess from the file the sign is in, out of
  `checks.commands`. The checks run it after `checks.commands` pass, under one lock for the
  repository, and a builder runs a test of it through the same lock. With no sign it stays empty
  and nothing about it is said;
- the sentences of what must never go wrong (`flow.topics`) the owner confirmed;
- `branch.land = "owner"`: a person merges, until he says otherwise;
- `branch.propose`: a pull request where the remote is GitHub;
- `branch.history`: `keep` or `squash`, as the last fifty merges in `examined.md` did;
- `branch.protected`: the branches nothing lands on that `examined.md` found, or none;
- `[tracker]`: none, unless the repository shows one. When it shows Linear, propose it with the
  team key it shows and Lem moving the tickets, and run the tracker's "check" with those values
  before you write the table: a wrong workspace or a status that does not exist shows now, and a
  check that fails leaves the table out and says why on the page;
- the reviewer: Codex when step 1 found it, since two model families disagree more usefully than
  one family twice and a reviewer on another provider's quota does not spend the builders';
  otherwise a second Claude: `reviewer = "codex"` under `[seats]`. Its model and its effort, the
  defender's seat (`seats.planner`) and the experts (`seats.experts`) stay Lem's defaults;
- `tools.annotate` and `tools.ask` keep Lem's defaults.

Run each command of the checks once, at the root, for the last line the hand-over page shows, and each
`checks.alone` command through `python3 SKILL_DIR/scripts/project.py alone -- COMMAND`. Then look at
what they left that git neither tracks nor ignores (`git status --porcelain --untracked-files=all`):
a cache of Python's bytecode, a coverage file, a build folder. Propose an ignore line for each kind
in the repository's ignore file, `.gitignore` when it has none, in the onboarding's commit, and
list them on the hand-over page among the assumptions ("change ignore none" leaves them out). The
checks remove such files after every run anyway (`stages/land.md`, step 4), so the lines keep the
developer's own checkout tidy and nothing waits on them. Then remove what the commands left, the
way it came: the files they wrote, never a file that was there before. In a Python module with
no `.gitignore`, the checks' `python3 -m unittest` left two `__pycache__` folders, the checks of that
day refused the tree, and the first small change ended in a second task for the ignore rule (a
scratch repository, 2026-11-17).

Leave `checks.ignores` empty: an empty list only means the checks run again whenever the base moves.
Lower `flow.max_tasks` when `examined.md` shows tests that share one database or drive a browser,
and say so on the page.

## 5. Generate what is absent

For each path `project.py show` marks as not existing, write a draft. A linked folder is left as
it is, with one exception: a cast of fewer than two personas is completed wherever its folder
is, and no persona file that is there is overwritten.

- **The profile**, from `templates/profile.md`: the three answers and the examined facts,
  one page.
- **The personas**, two or more: one file per person of the second question, from
  `templates/persona.md`, and a `README.md` that lists them with one line each. A persona you
  could fill only by guessing (the owner named the role and nothing more, or you proposed it and
  he only nodded) says so in its first line, as the template shows, and its line in the
  `README.md` says it too: a thin persona answers every question the same way, and only the
  owner can make it a person.
- **The style guide**: first offer the published guides `references/styleguides.md` lists for the
  project's stack; one the owner picks enters as a linter configuration in the checks and a page of
  differences, as that file says. Then one file per area of the code. Its frontmatter names the
  paths it covers in the one form `project.py rules` reads, `paths:` with a list of globs, and a
  file without that covers every path; each rule has its reason and the file it was read from. Write only conventions `examined.md` shows the code
  already keeps, and say at the top of each file that it is a draft read from the code. A rule
  nobody has yet needed is not written: the style guide grows when a review finding or a
  correction repeats (`stages/learn.md`). A new project gets the copy the owner took from the
  offers of step 6, or no style guide yet.
  A draft never cites a file of this skill by the path you read it from. That path is one
  install's copy and does not exist in the next checkout. Name what the owner can use instead:
  `/lem learn`, "the published guides Lem lists for this stack". The first onboarding wrote
  `.claude/skills/lem/stages/learn.md` into a style guide (2026-11-15).
- **A paragraph for the project's agent document**, as a proposal: where the rules are, that a
  file's `paths:` says which files it covers and a file without it covers all, and that an agent
  reads the ones that cover what it changes. With it an agent that runs without Lem finds the
  rules; with Lem, the picker hands them over. Show the paragraph on the hand-over page and put
  it into the agent document, on the onboarding's branch, only on the owner's yes.
- **The checks of a new project** do not exist yet. Leave `checks.commands` empty and name "set up
  the checks" (formatter, linter, type checker, a first test) as the task to run first: no task
  lands through this skill before it. That task's branch writes the commands into
  `checks.commands` of its own `.lem/project.toml`, and the landing checks it with them
  (`stages/land.md`, step 1); its pull request is not green, so that the owner reads the checks. The onboarding's own branch is not a task: it holds
  settings and drafts, and step 6 lands it.
- **The review configuration**: the review tool's own starter set, in the review tool's own
  folder, which the settings' `review` path names (the harness file says how it is made), and its
  project profile: what the project is, what a reviewer
  here must read first, and an empty list of rejected findings.
- **The lessons file**, with one line that says what it is for and nothing else.

## 6. Hand over

Commit the settings and the generated files on a branch of their own, `chore/lem-onboarding`.
It is not landed yet: the owner's read of the drafts is the review.

`show-page` one page to the owner, built from the pattern `SKILL_DIR/assets/handover.html`: copy
that file and `SKILL_DIR/assets/lem.css` into the onboarding's directory, put the facts in the
place of its words in capitals and of its example rows, repeat a block as the content needs and
remove a section that has nothing to say. Keep its classes and add no style of your own. The
stylesheet is the one the board uses, so the page looks like the same tool; the first
onboarding's page was written by hand, and the owner found it "a bit old school" (2026-11-15).
Its title names the repository and its first line is the
root as an absolute path: every other path on the page is relative to it, and a page without it
cannot be checked against any folder. Then what the machine has and lacks, which folders the
settings link and what was generated, and the settings file. The machine's part lists the tools the check lists and
no part of Lem itself: the question page comes with Lem. Say there that the project may bring a
builder of its own, and how (the harness file, `spawn-builder`).

**The assumptions**, each one line with its value, where it came from, and the words that change
it: who lands (`owner`; "change land agent"), a pull request or a merge, what lands, the closed
branches, the tracker, the reviewer and the defender with their models, the folders already here
(linked or new), and each command of the checks. With git hooks, one line says, in these words, why the
checks have only tests: "the git hooks run the rest at each commit of a builder" (the hook files;
"change checks add COMMAND"). With a sign of a suite that needs the machine to itself, one line
names your guess for `checks.alone` with the file the sign is in ("change alone COMMAND", "change
alone none"): that line is the one question about it, and it waits for no answer either. He
corrects one with "change" and what; nothing on the list waits for an answer. With `branch.propose = "pull-request"` one line of it says, in these
words, what his "land" approves: "Lem pushes each task's branch and opens its pull request
without asking" (`branch.propose`; "change propose merge"). That line makes the settings his
standing word for the push, so that no task stops before its pull request to ask for it.

A list of file names is not a hand-over. Every generated file is a draft, and three are read
first: what must never go wrong, the checks, the personas. Name each persona that is a thin guess, as the
one the owner should correct first. Offer to open each in the annotate tool
(`show-page`; `tools.annotate` in the settings), one after the other, and take the owner's notes
as corrections: edit, commit on the same branch, say for each file what changed.

**The offers**, last, as one short list, never a question each; he takes one by its name:

- **the correction queue**, recommended: with it, the project keeps a queue of the owner's
  corrections for the retro; without it, a correction is learned in the session it was given in
  and nowhere else. What he agrees to, in these words or closer ones: each message he types in
  this repository, other than a command that starts with `/`, goes with the agent message it
  answers to the Jev decision model through OpenRouter, under the key of whoever typed it, and
  the ones that may hold a lesson are kept in a file that is never committed. The yes is a line
  in the tracked settings, so it holds for everybody who works in this repository with the hook,
  and one person can say no for themselves (the harness file says how). The check's
  "OpenRouter key" row says whether this session has a key; without one the queue stays empty
  and its log fills, so say that too. On his yes, set `corrections.collect = true` in the
  settings draft on the onboarding's branch, which his "land" then approves with the rest. The
  hook comes with the plugin, so nothing is registered and he has nothing to run;
- **each recommended tool that is absent**: what it gives and its guide (the row's `guide`). Lem
  brings none of them, and installs one only on his yes; a guide copies a skill into the owner's
  own skills folder, so where your agent refuses you the step, give him the guide's commands;
- **cronn**, when it is absent or not running: through the `cronn` skill when that skill is
  there; its installer adds a Homebrew formula and an agent that starts at login, so it runs
  only on his yes, and the harness file says which steps he has to run himself;
- **the scheduled jobs** of step 7, when cronn runs;
- **a paragraph for the project's agent document** (step 5);
- **a starting style guide** for a new project, copied from another of his repositories that
  uses the same stack, marked as copied and from where.

The page and your last message end with the three replies you take, in these words:

- **land**: you bring the branch onto the base branch yourself, by a fast-forward, after a rebase
  when the base moved, and leave the checkout on the base branch. That holds whatever
  `branch.land` says: the owner's read was the review and this word is his go-ahead. It does not
  go through `stages/land.md`, which reads settings the base branch does not have yet. When the
  settings name commands of the checks, run them on the branch first and do not land on a red result; a
  new project names none, and its onboarding lands without them. Never hand him git commands to
  type. Then write the state `landed` with that line (`project.py state onboarding landed
  "main is at COMMIT: Lem's settings and drafts"`). Open your answer with what you did
  ("Landed: `main` is at ..."). On the first onboarding
  the answer to "land it" opened with "It is not a Lem task, so /lem land does not apply", and
  the owner took it for a refusal of a landing that then happened (2026-11-15).
- **change** and what: you edit, commit, and show the file again.
- **drop**: you remove the branch and the onboarding's directory, and say what stays on the
  machine: Lem's plugin and a scheduled job.

The first onboarding ended on "Read these three first" over a list of paths and on a
`git switch` and `git merge` line for the owner, in a project whose settings said the agent
lands. He wrote: "I have no idea what to do about it and whether its correct, I don't even see
what repo it belongs to" (2026-11-15).

## 7. Scheduled work for this repository

Only when step 1 showed cronn running, as an item of the offers of step 6. Two jobs that belong
to this repository, each a session started in it with nobody at the terminal:

- a retro each morning (`/lem retro`), so a correction that came back is moved before the next
  day's work;
- a night plan (`/lem night`), which leaves the owner a plan each morning for one backlog item
  that needs no decision.

Offer a job only when its first run has something to read, and say what that is. A retro reads
landed tasks and the correction queue: in a repository with neither, say that it is worth adding
after the first landing or once the queue is on, and add nothing now.

Add a job only on the owner's yes, through the `cronn` skill when it is installed, and name the
job after the repository. When the step is refused to you, give the owner the command. A scheduled job starts an agent that nobody watches: that choice is
never the agent's.
