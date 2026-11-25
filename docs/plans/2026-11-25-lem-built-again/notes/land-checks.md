# Notes of the step `land-checks`

What the checks, the polish pass, `lem serial` and the criteria's check need in files the step
does not own, the local stand-in each uses until then, and what other steps take over.

## For `core` (`records/`)

1. **`CheckWait` holds the whole wait.** `land.wait_for_load` on `main` logged why a run waits:
   the load, the run it waits a minute after (`after`), the first in the line with its
   repository (`behind_repo`) and why it goes first (`why`: `wanted`, `longer`, `first`), the
   repositories whose state did not read (`unread`), and the line for the owner (`say`), which
   `--status` prints as `waits`. `CheckWait` has `reason` `load` or `behind` and no field for the
   rest. Asked: `reason` takes `after` too, and fields `after`, `behind_repo`, `why`, `unread`,
   `say`. Meanwhile the gate writes a `CheckWait` with what fits (a wait after the last start is
   `load`) and the whole wait into `tasks/SLUG/checks-wait.json` (`app/landing/checks_waits.py`,
   `Waited`), which `--status` reads; the file goes once the entry holds it.
2. **`CheckEnd` says how long the run took and on which tip.** `gate.end` on `main` had
   `seconds`, `tip` and `taken` (the commit of the polish pass whose run of the criteria's tests
   the checks took). Meanwhile the length is the checks' span (`Task.spans`, name `checks`,
   which ends at the `CheckEnd`'s moment: `app/landing/checks_last.py`), the tip is
   `Landing.checked.tip`, and `taken` is `CriterionCheck.taken_at` on each criterion.
3. **`Lowered.line`.** `land.bar_of` keeps the marked line (160 characters) beside each lowered
   file; the pull request and the review show it. `Lowered` has `path`, `how`, `reason`,
   `reviewer`. Meanwhile the line is not kept.
4. **`Checked.not_covered` and `Checked.edited`.** The bar's other two lists (the suffixes it has
   no marks for; the tests, snapshots and test settings the change edits, which a reviewer
   reads first) have no field. Meanwhile they are computed (`model/landing/bar.py`, `BarRead`)
   and not kept.
5. **`Checked.inputs`** says "commands, serial, setup, plan file"; the checks' definitions that
   make a passed run hold no more are the commands and the serial ones (`land.same_checks`), so
   the digest is of those two (`model/landing/checks.py`, `inputs`). The five inputs of the
   criteria's run are `records.red.Inputs`, digested into `PassRun.inputs`.

## For `core` (`ports/git.py`) and `land-base` (`adapters/git_cli.py`)

The facts and acts below are git calls the checks, the bar, the polish pass and the criteria's
check make, and the `Git` port has none of them. Each runs today through the git adapter's own
shell (`adapters/git_cli_shell.py`, with `own(os.environ)`) in a stand-in module of the step:

- `app/landing/checks_git.py`: the untracked files (`status --porcelain --untracked-files=all
  -z`), what git ignores (`ls-files --others --ignored --exclude-standard --directory -z`) and
  which folders a rule ignores (`check-ignore --no-index --stdin -z`), the porcelain status of
  what git tracks, a path's kind at a commit (`cat-file -t`).
- `app/landing/checks_diff.py`: the diff with no context (`diff -U0 -M`), its rows of names
  and status (`diff --name-status -M`), the paths that differ (`--name-only --no-renames`), the
  paths a change adds (`--diff-filter=A`), the paths one commit touched (`diff-tree`), and a
  file's first line at a commit (`cat-file blob`, 256 bytes at most).
- `app/landing/checks_red_*.py` and `checks_criteria.py`: a detached worktree at a commit
  (`worktree add --detach`), the test files laid over the base (`checkout TIP -- FILES`), and a
  worktree removed whole, a locked one too (`worktree unlock`, `remove --force --force`,
  `prune`); each in a process group of its own, since a hook may leave a process.

Asked: a `GitTree` part of the port with these, and the adapter's methods; then the stand-ins go.

## For the owner of `model/landing/world.py` and `app/landing/world.py`

6. **Whether the tip holds the polish pass.** `landing.md` C row 3 holds while `polished.after`
   is in the tip; the world has no such fact. Meanwhile `checks.polished` holds once a pass is
   done, and the checks look before their first command (`app/landing/checks_ready.py`,
   `polish_in_tip`): a tip that lost the pass gives it back (`polished` cleared, the refusal
   `no-polish`), so the pass is due again. Asked: `World.polish_in_tip: bool`, gathered with
   `git.is_ancestor(worktree, polished.after, tip)`.
7. **The checks carry over the items `file` committed** (`landing.md` D, "Checks carry";
   `land.gate_holds`). `checks.holds` needs to know that the commits between `checked.tip` and
   the tip only add the paths of `checked.items_after`. Asked: a world fact of the paths the
   commits after the checked tip add, when they only add (`land-base`'s `carry.py` judges it,
   `land-review`'s `file` writes `items_after`). Meanwhile a commit after the run makes the
   checks due.

## For the owner of `app/landing/say.py`

8. A pass that started and is not done makes the polish row due with the why "`lem land polish
   SLUG --done` checks what it did", but `next` names `lem land polish SLUG`, which gives the
   brief again (the start is kept). Asked: `words_of` gives ` --done` for `polish` when the
   record holds a pass with no `after` (or `Due` carries the words).

## For `settings`

9. This machine's start number of the load gate, `[load] start` of `machine.toml` (0 takes the
   gate away, a negative number is refused): `app/landing/checks_machine.py` reads it with
   `tomllib` until `settings/machine.py` does; its fix names `lem settings set load.start 40
   --machine`.

## For `land-base`

10. `base` keeps the polish pass through a rebase (`land.through_rebase`: each commit the pass
    names, by its place from the tip, when the rebase kept the branch's commits one for one).
    Until it does, the checks after a rebase find the pass's last commit gone from the tip and
    give the pass back (item 6).
11. `Checked.own_checks` (the task that adds the checks: no command on the main checkout, the
    branch brings them) is not written by the checks: `landing.md` E, "No checks", is
    `land-base`'s.

## For `land-text`

12. `stages/land.md` step 4 and `stages/polish.md`: `lem serial -- COMMAND` replaces `lem project
    serial`; `lem land polish SLUG` prints the brief (`range`, `commits`, `frozen`, `item`, ...),
    kept as `polish.json`; a `--done` refusal names its code (`dirty`, `rewritten`, `frozen`,
    `criteria`); the checks' result is on the record (`Landing.checked`) and their end is a
    `CheckEnd`; `--status` gives `waits` as `Waited` (its `say` and `wait`). The paths "Red base"
    and "Repair limit" are acts of the stage (a repair task, the hold `blocked` with `after`, a
    session's wait), moved to you in `tests/ledger/moves/land-checks.tsv`.

## For `slice-land`'s skeleton (`tests/journeys/test_skeleton.py`)

13. The journey starts its checks at the machine's default start number, 40: on a machine whose
    load average is over 40 a run waits at the gate, 15 s a look. `tests/journeys/landing/
    test_checks.py` sets `[load] start = 1000` in the test's home first; the skeleton could do the
    same in `made()`.

## Done in a file of another step, on the brief's word

- `tests/unit/landing/test_decisions.py`: the case `test_checks_refuse_serial_commands_and_a_red_
  tip_as_later_steps` held the slice's `not-built` refusals of `checks.decide` and `checks.left`,
  which this step replaced; it is removed, and `tests/unit/landing/test_checks.py` holds the rules
  that replaced them.
