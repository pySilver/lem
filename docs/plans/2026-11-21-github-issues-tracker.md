# GitHub Issues as a second tracker

careful: yes, because the topic "Lem changes a developer's repository without his word: a push, a merge, a removed worktree or branch, a protected branch touched." is in reach: task 2 gives Lem writes to the issues of the developer's GitHub repository (an assignee, a comment, a closed issue), and a wrong step writes to the wrong issue or twice; and "Lem reads a project's settings wrong" is near, since task 1 adds a value of `tracker.kind` and task 3 has `/lem init` propose it.

## Acceptance criteria

Size: full, because a new tracker reaches the settings, the id of a ticket, a new skill with its script, the onboarding and four documents.

1. A project whose `.lem/project.toml` has `[tracker]` with `kind = "github"` and no other key is
   taken: `lem project show` gives the tracker as `github`. `kind = "jira"` is refused, and the
   message names `linear` and `github`.
2. In a project whose tracker is GitHub, the id of an issue is its number after `#`:
   1. `lem project task-dir export-keeps-gift-note --ticket 42` keeps `#42` as the task's ticket,
      and `--ticket "#42"` keeps the same.
   2. A second task with `--ticket 42` is refused while the first one is not dropped or answered.
   3. `--ticket MBZ-12` is refused in that project, and `--ticket 42` is refused in a project whose
      tracker is Linear.
3. `/lem read 42`, or the issue's address `https://github.com/OWNER/REPO/issues/42`, shows issue 42
   of the repository that origin names: its title, its text as written, open or closed, its labels
   and its address. It writes nothing to the issue. The address of an issue of another repository
   is refused, and the message names origin's repository.
4. When the build of a task from issue 42 starts, issue 42 gets the person signed in to `gh` as its
   assignee. An issue that has an assignee already keeps its assignees, and Lem adds nobody. A
   second start writes nothing to the issue.
5. When the task from issue 42 lands, issue 42 gets one comment and is closed as completed:
   1. The pull request of `export-keeps-gift-note` merges.
   2. Issue 42 gets a comment with what changed, the pull request's address and the last line of
      each check. Its last line is `lem: export-keeps-gift-note landed`.
   3. Issue 42 is closed as completed. An issue that is closed already stays as it is.
   4. A session that was cut off after the comment posts no second comment: the next session finds
      that last line on the issue, and goes on to the close.
6. When the task from issue 42 is dropped, issue 42 gets one comment that says why in one line, and
   its last line is `lem: export-keeps-gift-note dropped`. When the task ends with an answer, the
   comment holds the answer, and its last line is `lem: export-keeps-gift-note answered`. Either
   way the issue stays open, and Lem tells the owner that it is open.
7. The GitHub tracker's check says the repository that origin names and that its issues are on, or
   names what is missing: `gh` that is not signed in, issues that are off, or an origin that is not
   on GitHub. It writes nothing, to the issues or to the settings.
8. `/lem init` proposes `kind = "github"` for a repository on GitHub whose issues are on and hold
   at least one issue, when the repository shows no Linear key. When it shows Linear keys it
   proposes `linear`, and otherwise no tracker. A check that fails leaves the table out, and the
   onboarding's page says why.
9. A guide, "Connect GitHub Issues", says how to fill `[tracker]` for GitHub and how to start a
   task from an issue, and the README, the site and `docs/settings.md` link it. `docs/linear.md`
   no longer says that Lem supports no other tracker.

## How it works

What Lem writes to an issue, from the task's start to its end.

```mermaid
flowchart TD
  S["The build of the task starts"] --> A{"Does the issue have an assignee?"}
  A -->|"no"| A1["The person signed in to gh becomes its assignee"]
  A -->|"yes"| A2["The issue keeps its assignees"]
  A1 --> E{"How does the task end?"}
  A2 --> E
  E -->|"landed"| C{"Is the landed line on the issue already?"}
  C -->|"no"| C1["One comment, last line: landed"]
  C -->|"yes"| X{"Is the issue closed?"}
  C1 --> X
  X -->|"no"| X1["The issue is closed as completed"]
  X -->|"yes"| X2["The issue stays as it is"]
  E -->|"dropped or answered"| D["One comment, the issue stays open"]
```

## Tasks

1. **The settings and the id of an issue** (criteria 1, 2). `TRACKERS` in
   `skills/lem/scripts/project.py` takes `github`; `cmd_task_dir` reads the project's tracker and
   takes the id form of its kind (`TICKET` stays the Linear form, a new rule takes `42` and `#42`
   and keeps `#42`); the commented `[tracker]` of the settings template names both kinds; the
   row of `tracker.kind` in `docs/settings.md` names both (`tests/lem-settings.sh` holds the
   table one to one). Tests: the rule of the id at the unit level (`tests/unit/test_settings.py`
   or `tests/unit/test_task.py`, where the settings' and the task's rules are now), and the
   task-dir journey with a GitHub tracker in the ticket checks of `tests/lem-settings.sh`.
   Files: `skills/lem/scripts/project.py`, `docs/settings.md`, the tests named.
2. **The skill `lem-github` and its command `lem issue`** (criteria 3 to 7). A new skill,
   `skills/lem-github/SKILL.md`, in the shape of `skills/lem-linear/SKILL.md` (the same six steps,
   `disable-model-invocation: true`, the same "What this skill never does"), whose steps run one
   script, `skills/lem-github/scripts/issues.py`, which `bin/lem` names `issue`: `check`, `read
   ID|URL`, `start SLUG`, `land SLUG --body-file FILE`, `drop SLUG --why TEXT`, `answer SLUG
   --body-file FILE`. Each write is `gh` against origin's repository, looks at
   `lem project tasks`' `ticket_steps` first, writes the step down through `lem project
   ticket-step` after `gh` took it, and for a comment reads the issue's comments for the last
   line `lem: SLUG STEP` before it posts. The script adds that last line itself. Standard library,
   JSON out, exit 1 with the fix, "the owner" in every string for a person. Tests: a unit file
   `tests/unit/test_issues.py` over a stand-in `gh` on `PATH`, written in the manner of the one
   `tests/lib.sh` keeps, for each step and each refusal; the map of `tests/pick.py`. The tracker's
   harness part, `skills/lem/harness/claude-code/tracker.md`, says that the skill is `lem-KIND`
   and that the GitHub tracker needs `gh`, no MCP server; `skills/lem/harness/README.md` lists
   the skill; `NOTICE` says that `lem-github` was written for Lem.
   Files: the two new files, `bin/lem`, the test file, `tests/pick.py`, the harness files, `NOTICE`.
3. **The onboarding proposes GitHub** (criterion 8). `skills/lem/stages/init.md`: the look at
   "where the work is kept" adds GitHub's issues (on, and at least one issue, through `gh`), and
   `[tracker]` proposes `github` when no Linear key shows, with the check of task 2 before the
   table is written, in the same words as for Linear. The onboarding's page pattern, when it names
   the tracker, too.
   Files: `skills/lem/stages/init.md`, and `skills/lem/harness/claude-code/onboarding.md` only if
   it names the tracker.
4. **The documents** (criterion 9, and what the change makes false). A new guide
   `docs/github-issues.md`, "Connect GitHub Issues", in STE, under 800 words, in the shape of
   `docs/linear.md`; `docs/linear.md` loses "Lem supports no other tracker"; `README.md` and
   `site/index.html` link the guide beside "Connect Linear"; `docs/settings.md` links it under
   `[tracker]`; `docs/pull-request.md` says "the ticket", not "the Linear ticket"; `AGENTS.md`
   names the skill in "Layout" (the shipped skills, the guides, `lem issue` among the commands);
   the ruling "Linear and GitHub Issues, and the local backlog stays local" in
   `docs/rulings/rulings.md` points at a backlog item that this change ends: its words change only
   where they name that file, to say that `kind` is `linear` or `github`, and its rule stays word for
   word; `docs/backlog/github-issues-as-a-second-tracker.md` is removed with `git rm`.
   Files: the documents named.

## Decisions of the plan

- The GitHub tracker is a script over `gh`, not skill text over a server (decision 3): `gh` is a
  command a script can call, as `land.py` does, and the steps then hold in tests.
- An issue is started by an assignee (decision 4), finished by one comment and a close (decision
  5), and its id is `#42` (decision 6).
- Out of scope: the status columns of GitHub Projects boards (decision 1) and a tracker on another
  forge (decision 2). The pull request's text gets no `Closes #42` (decision 5).

## What it will not verify

- No step writes to a real GitHub issue in the build: the tests run on a stand-in `gh`. Which
  fields `gh issue view --json` gives, and their names, are read from `gh issue view --help` on
  this machine and named with the version in the script. The first real task from an issue is
  the test of the skill's text.
- The onboarding's proposal (criterion 8) is a step of a stage file, which no test holds: a real
  onboarding of a repository with issues shows it.
