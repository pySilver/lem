# init: onboarding a repository

`/lem init` takes a repository from nothing to a first task: it checks the machine, examines the
project, interviews the owner about what the code cannot say, and writes the project's settings
and profiles as drafts the owner adjusts. It runs once per repository and stops before any task.

Keep the onboarding's notes in its own task directory: `project.py task-dir onboarding`.

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
installed, and end. For each optional tool that is absent, tell the owner in one line what the
skill does without it (the row's `without_it`), and go on. A recommended tool that is absent
(`need: recommended`) gets one line too: what it gives and its guide (the row's `guide`). Lem
brings none of them. Offer to install one by its guide, and do it only on the owner's yes; a
guide copies a skill into the owner's own skills folder, so where your agent refuses you the
step, give him the guide's commands. Three things need a sentence of their
own: cronn that is installed and not running, cronn that is absent, and the correction queue.
Recommend the queue and turn it on only when the owner agrees: with it, the project keeps a
queue of the owner's corrections for the retro; without it, a correction is learned in the
session it was given in and nowhere else. Tell the owner what he agrees to, in these words or
closer ones: each message he types in this repository, other than a command that starts with
`/`, goes with the agent message it answers to the Jev decision model through OpenRouter, under
the key of whoever typed it, and the ones that may hold a lesson are kept in a file that is
never committed. The yes is a line in the tracked settings, so it holds for everybody who works
in this repository with the hook, and one person can say no for themselves (the harness file
says how). The check's "OpenRouter key" row says whether
this session has a key; without one the queue stays empty and its log fills, so say that too. On
his yes, set `corrections.collect = true` in step 4. What else is needed depends on how Lem
reached this session, and the harness file says which: with Lem as a plugin the hook is there
already and nothing is registered; with Lem linked by the setup, name the one command that
registers the hook, which he runs himself, today or on any later day. Give him no settings
lines to paste, and never name that command to an owner who has Lem as a plugin: it would add
the hook a second time. For an absent cronn, offer to install
it through the `cronn` skill when that skill is there: its installer adds a Homebrew formula and
an agent that starts at login, so it runs only on the owner's yes. The owner may have to run it
himself: the harness file says which steps an agent is refused, and then you give him the
command.

## 2. Examine the project

Before any question, read what the repository already says, and write `examined.md` in the
onboarding directory, every line with the path it was read from:

- what the product is and who uses it: `README`, `AGENTS.md` or another agent document, the
  package metadata, the top of the documentation;
- the stack and its versions: the dependency and tool-version files;
- how it is checked: the test configuration, the CI files, the commit hooks, a `Makefile` or task
  runner. These become the gate commands;
- how work lands: the default branch, the branches the last fifty merges went into, whether
  commits are squashed, the form of the commit subjects;
- where a defect costs most: migrations, money, authentication, anything that writes data which
  cannot be rebuilt, private data, the checks themselves. Most products have most of these, so
  look for each. They become two proposals: the danger topics, each one sentence in the terms of
  this product ("the price a merchant's customer pays", not "money"), and the careful paths
  where the code keeps them today;
- the conventions the code already keeps: how modules are laid out, how errors are raised, how
  tests are named and what they touch. Note one only where several files agree;
- `python3 SKILL_DIR/scripts/project.py existing`: the settings an older tool already keeps here
  (`.claude/rules`, `.personas`). The review tool's folder is not one of them: it is that tool's
  own, and the settings name it where it is.

In a large repository, `fan-out` one reader per area and merge what they return. A reader reports
what it read and where; it proposes nothing.

A repository with no code yet (`git ls-files` lists nothing beyond a README, a license or an
ignore file) has nothing to examine. Write that one line in `examined.md` and go to step 3, where
the interview is about what the owner plans to build.

## 3. Interview the owner

Hold the interview by the rules of the `lem-interview-me` skill (`load-skill`): open with a
one-sentence hypothesis and how sure you are, ask one question at a time through `ask-owner`, each
with your own guess so the owner corrects a draft instead of composing one, restate what you
heard at the end, and take only an explicit yes. Ask only what the examination could not answer;
what it answered is stated as an assumption in step 6, never asked.

An interview question goes straight to the owner. It does not pass the question gate or the
persona panel, its card gets no framing check, and its answer is not tested for a ruling: it
asks what the owner wants, which no ruling, probe or persona knows. Each answer has a place
already, the settings file or the profile, so no ruling file is written for it. The first
onboarding through Lem put its five questions through the gate: 11m 54s passed between the
owner's first answer and the second question, and three ruling files repeated three lines of the
settings (a scratch repository, 2026-11-15; the time is that session's status line as another
session read it).

**A new project** has a different interview, because there is no code to guess from:

- **What the owner plans to build**: the product, who it is for, and the first thing such a
  person should be able to do with it. That first thing becomes the first task after onboarding.
- **How big it is meant to get**, and what would make it a failure.
- **The stack**: what the owner wants, or "choose for me"; then propose one with its reason and
  what it costs to change later.
- **The people** a decision here will affect, and **what must never break** once it exists.
- **A starting style guide**: when another of the owner's repositories uses the same stack and
  has a style guide, offer to start from a copy of it, marked as copied and from where.

For a repository that has code:

- **The product in the owner's words**: what it is for, who it is for, how big it is meant to
  get. The code shows what exists; only the owner knows what it is judged against.
- **The people**: who is affected when a decision here goes one way or the other (a customer, an
  operator, a partner, the engineer on call). Each becomes a persona, and every project of Lem
  has them: before a hard question reaches the owner, an agent answers it as each person the
  decision affects. The onboarding ends with two or more, because a panel of one has nobody to
  disagree: the people the product serves, and, where there is no second kind of user, the
  people who run it or build the next change on it. Two people are worth it only when they would
  notice different things about the same change. Propose them from what you examined and let the
  owner correct the list. The first onboarding wrote one persona, "a shop employee who reads
  report headings", and its own page said that this person could not tell the options of a
  question apart (a scratch repository, 2026-11-15).
- **What must never break**: show the danger topics and the careful paths you propose, and ask
  what is wrong or missing. The topics come first: a person names a danger more surely than a
  folder, and a topic still holds after the code moves. In a repository with no code, propose
  the topics from the owner's description of the product; the paths come with the first tasks.
  Confirm or correct both. This is the one
  setting that is the owner's to choose.
- **Who lands**: the owner, or the agent once the gate is green; and the branch tasks land on.
- **What lands**: a task's own commits, or one commit for the whole task. Guess from the last
  fifty merges in `examined.md`.
- **Which branches are closed**: branches nothing may land on or be pushed to, such as a
  release branch during a rewrite that lands on a branch of its own. They go into
  `branch.protected`.
- **Where the work is kept**: when the project keeps its work in a tracker Lem has a skill for
  (Linear), the name of its server in the agent, the key of the one team, and who moves a
  ticket's status: Lem, or the tracker's own automation, as with a pull-request integration that
  moves a ticket when a pull request opens and merges. When Lem moves it, the two status names
  as the team spells them, for "work started" and for "landed"; and the workspace, as its address
  has it. Then run the tracker's "check" with these values before you write the table: it takes
  them from you at this one moment, so a wrong workspace or a status that does not exist shows
  now.
- **Who reviews**: the agent in the reviewer's pane, Codex or a second Claude. Guess Codex when
  step 1 found it, since two model families disagree more usefully than one family twice, and a
  reviewer on another provider's quota does not spend the builders'. Then, only when the owner
  has a preference: the reviewer's model, its effort for the review of a diff and its effort for
  the talk over a careful or large plan. No answer means the agent's own default.
- **The folders already here**, when `project.py existing` listed any: link them, so the older
  tools and this skill read one copy and nothing moves; or generate new profiles under
  `.lem/`, and leave the old folders for the owner to remove. Linking is what a project that
  works today does. That choice is about the cast and the profile only. The rules an agent
  already loads by itself are not asked about: they stay in their folder, the settings name it
  as the style guide whatever `--existing` says, and Lem gives the ones that cover a change to
  every builder and reviewer (`project.py rules`). A move of those rules is the owner's
  decision on another day, and no step here proposes it. A cast and a profile that are linked
  can move under `.lem` later by hand, with a `git mv` and their two lines in the settings.

Stop when you could predict the owner's answer to the next question. An answer of "whatever you
think" is not an answer to the careful paths or to who lands: say what you will assume and ask
for a yes.

## 4. Write the settings

```bash
python3 SKILL_DIR/scripts/project.py init --base BRANCH --reviewer codex --existing link    # or: --existing new
```

Leave `--existing` out when `project.py existing` listed nothing, or the style guide alone: a rules folder needs no choice, and every other folder it lists does. Then edit `.lem/project.toml`: the
gate commands from `examined.md`, the danger topics (`flow.topics`) and the careful patterns the owner confirmed, `land`, `history`,
the protected branches, the `[tracker]` table when the project has one, the reviewer's `model`,
`effort` and `plan_effort` when the owner named them, and `tools.annotate` or `tools.ask` when the owner marks up plans or takes questions with a tool of their own. Leave `gate.ignores` empty unless the owner names paths the gate does not read: an empty list
only means the gate runs again whenever the base moves.
Lower `flow.max_tasks` when `examined.md` shows tests that share one database or drive a browser,
and say so in the handover.

## 5. Generate what is absent

For each path `project.py show` marks as not existing, write a draft. A linked folder is left as
it is, with one exception: a cast of fewer than two personas is completed wherever its folder
is, and no persona file that is there is overwritten.

- **The profile**, from `templates/profile.md`: the interview's answers and the examined facts,
  one page.
- **The personas**, two or more: one file per person from the interview, from
  `templates/persona.md`, and a `README.md` that lists them with one line each. A persona you
  could fill only by guessing (the owner named the role and nothing more, or you proposed it and
  he only nodded) says so in its first line, as the template shows, and its line in the
  `README.md` says it too: a thin persona answers every question the same way, and only the
  owner can make it a person.
- **The style guide**: first offer the published guides `references/styleguides.md` lists for the
  project's stack; one the owner picks enters as a linter configuration in the gate and a page of
  differences, as that file says. Then one file per area of the code. Its frontmatter names the
  paths it covers in the one form `project.py rules` reads, `paths:` with a list of globs, and a
  file without that covers every path; each rule has its reason and the file it was read from. Write only conventions `examined.md` shows the code
  already keeps, and say at the top of each file that it is a draft read from the code. A rule
  nobody has yet needed is not written: the style guide grows when a review finding or a
  correction repeats (`stages/learn.md`). A new project gets the copy the owner accepted in the
  interview, or no style guide yet.
  A draft never cites a file of this skill by the path you read it from. That path is one
  setup's link and does not exist in the next checkout. Name what the owner can use instead:
  `/lem learn`, "the published guides Lem lists for this stack". The first onboarding wrote
  `.claude/skills/lem/stages/learn.md` into a style guide (2026-11-15).
- **A paragraph for the project's agent document**, as a proposal: where the rules are, that a
  file's `paths:` says which files it covers and a file without it covers all, and that an agent
  reads the ones that cover what it changes. With it an agent that runs without Lem finds the
  rules; with Lem, the picker hands them over. Show the paragraph on the hand-over page and put
  it into the agent document, on the onboarding's branch, only on the owner's yes.
- **The gate of a new project** does not exist yet. Leave `gate.commands` empty and name "set up
  the checks" (formatter, linter, type checker, a first test) as the task to run first: no task
  lands through this skill before it. The onboarding's own branch is not a task: it holds
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
cannot be checked against any folder. Then what the machine has and lacks, what was linked and
what was generated, each assumption taken from the code with its source, and the settings file.
The machine's part lists the tools the check lists and no part of Lem itself: the question page
comes with Lem. Say there that the project may bring a builder of its own,
and how (the harness file, `spawn-builder`). When the owner said yes to the correction queue and Lem is linked by the setup, the page names the command he
runs for its hook, in the form for this one repository, and nothing he has to edit; with Lem as
a plugin the page says that the hook came with the install, and names no command.

A list of file names is not a hand-over. Every generated file is a draft, and three are read
first: the careful paths, the gate, the personas. Name each persona that is a thin guess, as the
one the owner should correct first. Offer to open each in the annotate tool
(`show-page`; `tools.annotate` in the settings), one after the other, and take the owner's notes
as corrections: edit, commit on the same branch, say for each file what changed. The page and
your last message end with the three replies you take, in these words:

- **land**: you bring the branch onto the base branch yourself, by a fast-forward, after a rebase
  when the base moved, and leave the checkout on the base branch. That holds whatever
  `branch.land` says: the owner's read was the review and this word is his go-ahead. It does not
  go through `stages/land.md`, which reads settings the base branch does not have yet. When the
  settings name gate commands, run them on the branch first and do not land on a red result; a
  new project names none, and its onboarding lands without them. Never hand him git commands to
  type. Open your answer with what you did ("Landed: `main` is at ..."). On the first onboarding
  the answer to "land it" opened with "It is not a Lem task, so /lem land does not apply", and
  the owner took it for a refusal of a landing that then happened (2026-11-15).
- **change** and what: you edit, commit, and show the file again.
- **drop**: you remove the branch and the onboarding's directory, and say what stays on the
  machine: the links of the setup, a scheduled job, the hook.

The first onboarding ended on "Read these three first" over a list of paths and on a
`git switch` and `git merge` line for the owner, in a project whose settings said the agent
lands. He wrote: "I have no idea what to do about it and whether its correct, I don't even see
what repo it belongs to" (2026-11-15).

## 7. Scheduled work for this repository

Only when step 1 showed cronn running. Offer two jobs that belong to this repository, each a
session started in it with nobody at the terminal:

- a retro each morning (`/lem retro`), so a correction that came back is moved before the next
  day's work;
- a night plan (`/lem night`), which leaves the owner a plan each morning for one backlog item
  that needs no decision.

Offer a job only when its first run has something to read, and say what that is. A retro reads
landed tasks and the correction queue: in a repository with neither, say that it is worth adding
after the first landing or once the hook is registered, and add nothing now.

Add a job only on the owner's yes, through the `cronn` skill when it is installed, and name the
job after the repository. When the step is refused to you, give the owner the command. A scheduled job starts an agent that nobody watches: that choice is
never the agent's.
