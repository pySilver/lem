# init: onboarding a repository

`/task init` takes a repository from nothing to a first task: it checks the machine, examines the
project, interviews the owner about what the code cannot say, and writes the project's settings
and profiles as drafts the owner adjusts. It runs once per repository and stops before any task.

Keep the onboarding's notes in its own task directory: `project.py task-dir onboarding`.

## 1. Check the machine

```bash
python3 SKILL_DIR/scripts/doctor.py
```

A required tool that is absent stops the onboarding: say which, what it is used for and how it is
installed, and end. For each optional tool that is absent, tell the owner in one line what the
skill does without it (the row's `without_it`), and go on. Two cases need a sentence of their own:
agterm is there and its skill is not (an agent then has the terminal and not its commands), and
cronn is installed and not running.

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
  cannot be rebuilt, the checks themselves. These become the proposed careful paths;
- the conventions the code already keeps: how modules are laid out, how errors are raised, how
  tests are named and what they touch. Note one only where several files agree;
- `python3 SKILL_DIR/scripts/project.py existing`: the settings an older tool already keeps here
  (`.claude/rules`, `.revmux`, `.personas`).

In a large repository, `fan-out` one reader per area and merge what they return. A reader reports
what it read and where; it proposes nothing.

## 3. Interview the owner

Ask only what the examination could not answer, one question at a time through `ask-owner`, each
with your own guess from `examined.md` so the owner corrects a draft instead of composing one.
What the examination answered is stated as an assumption in step 6, never asked.

- **The product in the owner's words**: what it is for, who it is for, how big it is meant to
  get. The code shows what exists; only the owner knows what it is judged against.
- **The people**: who is affected when a decision here goes one way or the other (a customer, an
  operator, a partner, the engineer on call). Each becomes a persona.
- **What must never break**: confirm or correct the proposed careful paths. This is the one
  setting that is the owner's to choose.
- **Who lands**: the owner, or the agent once the gate is green; and the branch tasks land on.
- **The folders already here**, when `project.py existing` listed any: link them, so the older
  tools and this skill read one copy and nothing moves; or generate new profiles under
  `.agents/`, and leave the old folders for the owner to remove.

Stop when you could predict the owner's answer to the next question. An answer of "whatever you
think" is not an answer to the careful paths or to who lands: say what you will assume and ask
for a yes.

## 4. Write the settings

```bash
python3 SKILL_DIR/scripts/project.py init --base BRANCH --existing link    # or: --existing new
```

Leave `--existing` out when step 2 found no older folder. Then edit `.agents/project.toml`: the
gate commands from `examined.md`, the careful patterns the owner confirmed, and `land`.

## 5. Generate what is absent

For each path `project.py show` marks as not existing, write a draft. A linked folder is left as
it is.

- **The profile**, from `templates/profile.md`: the interview's answers and the examined facts,
  one page.
- **The personas**, one file per person the owner named, from `templates/persona.md`, and a
  `README.md` that lists them with one line each.
- **The style guide**: one file per area of the code, each rule with the paths it covers, its
  reason, and the file it was read from. Write only conventions `examined.md` shows the code
  already keeps, and say at the top of each file that it is a draft read from the code. A rule
  nobody has yet needed is not written: the style guide grows when a review finding or a
  correction repeats (`stages/learn.md`).
- **The review configuration**: the review tool's own starter set, moved to the settings' `review`
  path (the harness file says how), and its project profile: what the project is, what a reviewer
  here must read first, and an empty list of rejected findings.
- **The lessons file**, with one line that says what it is for and nothing else.

## 6. Hand over

`show-page` one page to the owner: what the machine has and lacks, what was linked and what was
generated, each assumption taken from the code with its source, and the settings file. Every
generated file is a draft; say which three the owner should read first (the careful paths, the
gate, the personas). Commit the settings and the generated files on a branch of their own,
`chore/task-onboarding`, and do not land it: the owner's read of the drafts is the review.
