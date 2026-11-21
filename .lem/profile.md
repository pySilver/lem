# Lem

Every persona, reviewer and builder reads this page first. It is a draft written at the
onboarding on 2026-11-16, from the repository and the owner's answers; correct what is wrong.

## What it is

Lem is a set of Claude Code skills that carries one unit of work in a repository from the ask to
a pull request that says green or not green. It runs on macOS inside agterm only, with a reviewer
(Codex or a second Claude) in a split pane. Its user is a senior developer whose attention is
short and spread over many projects; a team may adopt it for one repository, as with revmux.

## Scale

One owner builds it today, and no real project uses it yet (`docs/examples.md`, "What ran, and what did not"). It is meant
for one repository at a time with several tasks open in it, and for teams that adopt it per
repository. Four to five tasks ran well on one Mac (convertiser-server, 2026-11-14).

## Rules every answer works within

- The owner's rulings are reopened only by asking him. Their sentences are in `AGENTS.md` ("The
  owner's rulings"), and their full text in `docs/rulings/`.
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

- **`main` of this repository is what every project installs next.** The plugin takes each
  commit of `main` as an update, and a project gets it when it updates the plugin, with its tasks
  open. So the new scripts read what the scripts before them wrote (`AGENTS.md`, "Rules for a
  change here"). A task works in its own worktree, and nothing edits the main checkout by hand.
- **The skill files are instructions to agents.** A sentence in a stage file is followed word for
  word by a builder. A vague or wrong sentence is a defect, as a wrong line of code is.
- **A ruling is not a design.** `AGENTS.md` separates the sentences of the owner's rulings from
  those of the decisions and designs a session took, and their full text is in `docs/rulings/` and
  in `.lem/decisions/`. Only the first need him to change.

## Who to compare with

revmux and peer-planning, the owner's own tools that Lem grew out of. Large agent frameworks are
not a fair comparison: Lem is opinionated and small on purpose ("Opinionated and small",
`AGENTS.md`).
