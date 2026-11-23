# The checks remove an ignored `__pycache__` that was in the worktree before they ran

careful: yes, because the checks start to remove files from a task's worktree before they run, which reaches the owner's topics "Lem writes over something of the developer's: a file in his home or his repository that was there" and "A pull request says green when it should not: a check failed".

## Acceptance criteria

Size: full, because the change removes files from a task's worktree before the checks, a careful part of the landing.

1. Before the checks run their first command, Lem removes each `__pycache__` folder of the task's worktree that git ignores, and nothing else that git ignores; the output of `lem land checks` names each folder it removed.
   1. A builder of task X ran `python3 -m unittest tests.unit.test_land` in X's worktree, without `-B`, and left `skills/lem/scripts/__pycache__/land.cpython-315.pyc` there.
   2. X's worktree also holds an ignored `.env`, and an ignored `.venv/` folder with a `__pycache__` folder inside it.
   3. `lem land checks X` runs, and its first command, `bash tests/all.sh`, starts with no `skills/lem/scripts/__pycache__` in the worktree.
   4. `.env` and `.venv/`, with the `__pycache__` inside it, are as they were.
   5. The output of `lem land checks X` names `skills/lem/scripts/__pycache__/` as removed.
   6. A `__pycache__` that a command of the checks writes during the run is still there when the run ends, so a check that looks for one still goes red.

## Tasks

1. **The checks remove an ignored `__pycache__` before their first command** (criterion 1). In `skills/lem/scripts/land.py`, at the start of `checks_body`, before the snapshot of what git does not know (`there = untracked(task)`):
   - Take git's own list of what it ignores in the worktree, each ignored folder as one entry and not its content: `git -C WORKTREE ls-files --others --ignored --exclude-standard --directory -z`. An entry whose last part is `__pycache__/` is removed with what it holds; every other entry stays. So `.venv/` is one entry and stays whole, with each `__pycache__` inside it, and so does `node_modules/` or a `.env`.
   - The choice of entries is one pure function of git's list (unit cases in `tests/unit/test_land.py`: a `__pycache__/` at any depth goes; `.venv/`, `.env`, `build/`, a file named `__pycache__.py` and a folder `x__pycache__/` stay). The removal does not follow a link: a `__pycache__` that is a link is removed as a link, and an entry whose parent folder resolves outside the worktree is left, as `remove_left` does today.
   - The result of `lem land checks` names each removed folder in `removed_bytecode` (a list, empty when nothing went), and one line at the top of the first command's output file says what was removed before the run. It is no failure, and nothing waits for it.
   - The docstring of `land.py` that says what the checks remove (the paragraph with `removed_untracked`) says this too.
   - Tests: one journey in `tests/lem-land-guards.sh`, beside the check of `removed_untracked` (the `cached` run): before the checks, the worktree holds an ignored `shop/__pycache__/c.pyc`, an ignored `.env` and an ignored `.venv/lib/__pycache__/x.pyc`; the first command fails when `shop/__pycache__` is there, and a later command writes `tests/__pycache__/w.pyc` while it is ignored; the checks are green, `removed_bytecode` is `['shop/__pycache__/']`, `.env` and `.venv/lib/__pycache__/x.pyc` are there, and so is `tests/__pycache__/w.pyc` after the run.
2. **The landing's stage text says it** (no criterion). `skills/lem/stages/land.md`, the point of step 5 that says what the commands wrote that git neither tracks nor ignores (`removed_untracked`): one sentence that an ignored `__pycache__` that was in the worktree before the run is removed before the first command and named in `removed_bytecode`, and that this is no failure. No guide of `docs/`, the README or `site/index.html` names what the checks remove (`grep -rn "removed_untracked\|__pycache__" docs README.md site`, 2026-11-23, found nothing), so none changes.

## Decisions

- **The fix is in the checks, not only in the builder's text.** Rule 10 of `agents/lem-builder.md` already asks a builder to remove a `__pycache__` of its runs, and in moved-base-merge-agent-call (2026-11-22) two builders left one all the same; its test, `git status --short`, shows no ignored file. A text that a builder already missed twice is no fix; one call of git before the first command is. Cost on a small task: one `git ls-files` per run of the checks (unmeasured estimate: well under a second).
- **Only a folder named `__pycache__` that git lists as ignored on its own goes.** Python writes it and rebuilds it from the source, so its removal loses nothing. Every other ignored file may be the developer's (`.env`) or a setup's output (`node_modules/`, `.venv/`), and Lem cannot tell those from a leftover. A `__pycache__` inside an ignored folder is part of that folder and stays.
- **The builder texts stay as they are.** Rule 10 of `agents/lem-builder.md`, `prompts/small.md`, `prompts/investigator.md` and `prompts/review.md` ask for an empty `git status --short`, which is still true of what git does not ignore; the ignored bytecode is now the checks' to remove.
- **The four suites' own check for a `__pycache__` stays** (decision 1 of the task's record): it catches a script that writes bytecode during the run, and step 6 of the criterion keeps that.

## What this plan does not verify

- Caches of other tools that git ignores (`.pytest_cache/`, `.mypy_cache/`) stay, and the plan does not check whether another project's checks count them: no run has shown one that does.
- A repository with no ignore rule for bytecode is not changed: there a `__pycache__` is untracked, and `need_worktree` refuses it before the checks, as today.
