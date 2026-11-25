# Notes of the step `slice-land`

What `slice-land` needs in files it does not own. Each item names the file, what to change, and
why.

## For `tree` (and the orchestrator, before the next unit run): the tree's cases run built leaves

`tests/unit/cli/test_tree.py` calls every leaf in the test's own process, with the working
directory of the run. A built leaf acts on the workspace of that directory, and from a worktree of
Lem's repository that workspace is the main checkout (`store.places.workspace` follows
`commondir`). On 2026-11-25 at 05:18 a unit run of `tests/unit/cli` in the worktree of
`slice-land` did this, once the leaves were built:

- `lem task open x --ask x` made `/Users/Silver/Projects/GitHub/lem/.lem/state/tasks/x/`
  (`task.json`, `task.lock`, `step.lock`), and the claim made
  `/Users/Silver/Projects/GitHub/lem/.lem/state/locks/workspace.lock` (the folder `locks/` too);
  `lem task move x queued` moved it;
- `lem land propose x` and the other steps that got past the step lock ran `git fetch --quiet
  --prune origin` in the main checkout (its `.git/FETCH_HEAD` is of 05:18:15) before they
  refused `no-branch`.

The builder's `rm` of the three new files was refused by the permission system, so they are still
there for the orchestrator to remove (all were born at 05:18:05; nothing else under `.lem/state/`
changed). The fetch cannot be undone; it changed only origin's remote-tracking refs.

What the tree's cases need, before any unit run of a branch that has built leaves:

1. Every in-process call (`called`) and every subprocess `lem` of `test_tree.py` runs in a
   temporary folder that is in no repository (an autouse fixture with `monkeypatch.chdir`, and
   `cwd=` for the subprocesses), so a built leaf refuses `no-repository` and touches nothing.
2. `test_each_stub_refuses_not_built_and_names_a_step_of_the_plan` takes only the leaves that are
   still stubs: a stub's docstring says "A stub until the step"; a built leaf's says which step
   owns it. A built leaf that refuses a word it does not build yet still refuses `not-built` with
   the owning step named (`lem land checks --status`, `lem task open --ticket`, ...), which a case
   of the leaf's owner holds.
3. `test_a_call_the_rules_take_reaches_its_stub[land checks x]`,
   `test_a_call_loads_its_own_leaf_and_no_other_noun_and_nothing_heavy` and
   `test_the_command_lem_runs_the_tree_from_its_entry` use `land start x` or `land checks x` as
   "a stub": they take a leaf that stays a stub through group 1 (`lem land polish x`), or accept
   `no-repository` from the temporary folder of item 1.

Until then the unit level of this branch has 20 failing cases of `test_tree.py`, each a built
leaf answering for itself instead of `not-built`; `slice-land`'s report lists them.

## For `core`: the wiring case no longer names a real adapter (done, on the orchestrator's word)

`tests/unit/core/test_wiring.py::test_a_port_with_no_adapter_refuses_every_call_by_name`
expected `lem.adapters.git_cli` and `judge_jev` to be unbound, so it failed once `slice-land`
built `git_cli`. On the orchestrator's word of 2026-11-25, `slice-land` changed it: it binds
`wiring.adapter("lem.adapters.never_built", place)` and checks that the port is `Unbound` and that
each call (`tip`, `over_bar`) is a fault that names the call and the module. It proves the same
rule and holds whichever adapters exist.

## For `core`: a fact the Git port lacks

`GitPlaces` has no fact of the branch a checkout is on. `lem land merged` fast-forwards the main
checkout only when it is on the base branch, and the slice reads that as "HEAD is at the commit of
`refs/heads/BASE`" (`app/landing/merged.py: followed`), which a detached HEAD at the same commit
also passes. A method `branch_of(where: Path) -> str | None` (`git branch --show-current`, None
when detached) closes that, and `lem task worktree` can then check that a worktree that is there
is on the task's branch. Meanwhile `app/landing/merged.py: followed` compares HEAD's commit with
`refs/heads/BASE`, and `app/tasks/worktree.py` takes a worktree that is there as it is.

## For `land-merge`: the queue's merge loses who asked for it

`MergeAccepted` (`records/landing/merge.py`) keeps the tip, the moment and the forge's word, and
not who asked for the merge nor through what. When the queue merges, `lem land merged` writes the
merge with `by: owner, via: github` (`app/landing/merged.py: adopted`). A `by` and a `via` on
`MergeAccepted`, written from the intent it replaces, keep them. Meanwhile a merge the queue
made is written `by: owner, via: github`.
