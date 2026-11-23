# Lem

Every persona, reviewer and builder reads this page first. It is a draft written at the
onboarding on 2026-11-16, from the repository and the owner's answers; correct what is wrong.

## What it is

Lem is a Claude Code plugin, installed and never cloned, whose skills carry one unit of work in a
repository from the ask to a pull request that says green or not green. It runs on macOS inside agterm only, with a reviewer
(Codex or a second Claude) in a split pane. Its user is a senior developer whose attention is
short and spread over many projects; a team may adopt it for one repository, as with revmux.

## Scale

One owner builds it, and Lem runs the tasks of this repository too (`AGENTS.md`, "Rules for a
change here": the scheduled `/lem night` of this repository). It is meant for one repository at a
time with several tasks open in it, and for teams that adopt it per repository. Four to five tasks
ran well on one Mac (convertiser-server, 2026-11-14).

## Rules every answer works within

- The owner's rulings are reopened only by asking him. They are the list `docs/rulings/rulings.md`, and what a
  test or one place holds of them is `docs/rulings/history.md`.
- The rules of a change in `AGENTS.md` hold: the skill knows no project; a stage names a
  capability, never a tool; a number carries its source and date; scripts are standard-library
  Python 3.11 or newer, print JSON, and refuse a wrong input with exit 1 and the fix.
- A change to a script comes with its test. A change to a stage file names the task that showed
  the need.
- Documentation describes the current state. The README is in ASD-STE100.
- No fallback that hides a failure: a step refuses loudly.

## Tools and versions

Python 3.11 or newer, standard library only; bash and ShellCheck for the tests; headless Chrome
for the page checks when one is installed; Claude Code 2.1.325, codex-cli 0.169.0, revmux v0.2.7
and agterm on the owner's machine (`doctor.py`, 2026-11-16).

## What a newcomer gets wrong

- **The newest release tag of this repository is what every project installs next.** A project
  gets a release when it updates the plugin, with its tasks open, and a merge to `main` reaches it
  only through the next release. So a release reads what the release before it wrote (`AGENTS.md`,
  "Rules for a change here" and "A release"). A task works in its own worktree, and nothing edits
  the main checkout by hand.
- **The skill files are instructions to agents.** A sentence in a stage file is followed word for
  word by a builder. A vague or wrong sentence is a defect, as a wrong line of code is.
- **A ruling is not a design.** `docs/rulings/rulings.md` keeps the choices the maintaining
  session took, open to the owner, in a last part of their own, apart from his rulings. Only his
  rulings need him to change.

## Who to compare with

revmux and peer-planning, the owner's own tools that Lem grew out of. Large agent frameworks are
not a fair comparison: Lem is opinionated on purpose ("Opinionated",
`docs/rulings/rulings.md`).
