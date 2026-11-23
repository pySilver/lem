# The checks remove an ignored `__pycache__` that was in the worktree before they ran

careful: yes, because the checks start to remove files from a task's worktree before they run, which reaches the owner's topics "Lem writes over something of the developer's: a file in his home or his repository that was there" and "A pull request says green when it should not: a check failed".

## Acceptance criteria

Size: full, because the change removes files from a task's worktree before the checks, a careful part of the landing.

1. Before the checks run their first command, Lem removes each `__pycache__` folder of the task's own worktree that git ignores by itself, and nothing else: a `__pycache__` inside a folder that git ignores as a whole, such as `.venv/`, stays with that folder; the output of `lem land checks` names each folder it removed.
   1. A builder of task X ran `python3 -m unittest tests.unit.test_land` in X's worktree, without `-B`, and left `skills/lem/scripts/__pycache__/land.cpython-315.pyc` there.
   2. X's worktree also holds an ignored `.env`, and an ignored `.venv/` folder with a `__pycache__` folder inside it.
   3. `lem land checks X` runs, and its first command, `bash tests/all.sh`, starts with no `skills/lem/scripts/__pycache__` in the worktree.
   4. `.env` and `.venv/`, with the `__pycache__` inside it, are as they were.
   5. The output of `lem land checks X` names `skills/lem/scripts/__pycache__/` as removed.
   6. A `__pycache__` that a command of the checks writes during the run is still there when the run ends, so a check that looks for one still goes red.

## Tasks

1. **The checks remove an ignored `__pycache__` before their first command** (criterion 1). In `skills/lem/scripts/land.py`, at the start of `checks_body`, before the snapshot of what git does not know (`there = untracked(task)`):
   - Take git's own list of what it ignores in the worktree: `git -C WORKTREE ls-files --others --ignored --exclude-standard --directory -z`. An entry whose last part is `__pycache__/` is a candidate; every other entry stays. An ignored folder with no tracked file in it is one entry (`.venv/`), so the `__pycache__` inside it is never listed, and so does `node_modules/` or a `.env` stay. But git goes into an ignored folder that holds a tracked file, and then lists its `__pycache__/` on its own: with the rule `build/` and a force-added `build/.gitkeep`, the list holds `build/__pycache__/` (a probe in a throwaway repository, git 2.55.0, 2026-11-23). So each proper folder above a candidate (`build`, for `build/__pycache__/`) goes to one more call, `git -C WORKTREE check-ignore --no-index --stdin -z`, which prints each such folder a rule ignores (`build`) and exits 1 when it prints none; without `--no-index` it does not print `build`, which holds a tracked file (the same probe). A candidate with an ignored folder above it stays with that folder; every other candidate is removed with what it holds. No candidate, no second call.
   - The choice of entries is one pure function of git's two lists (unit cases in `tests/unit/test_land.py`: a `__pycache__/` at any depth goes; `build/__pycache__/` with `build` among the ignored folders above it stays; `.venv/`, `.env`, `build/`, a file named `__pycache__.py` and a folder `x__pycache__/` stay). The removal does not follow a link: a `__pycache__` that is a link is removed as a link, and an entry whose parent folder resolves outside the worktree is left, as `remove_left` does today.
   - The result of `lem land checks` names each removed folder in `removed_bytecode` (a list, empty when nothing went), and one line at the top of the first command's output file says what was removed before the run. It is no failure, and nothing waits for it.
   - The docstring of `land.py` that says what the checks remove (the paragraph with `removed_untracked`) says this too.
   - Tests: one journey in `tests/lem-land-guards.sh`, beside the check of `removed_untracked` (the `cached` run): before the checks, the worktree holds an ignored `shop/__pycache__/c.pyc`, an ignored `.env` and an ignored `.venv/lib/__pycache__/x.pyc`; the first command fails when `shop/__pycache__` is there, and a later command writes `tests/__pycache__/w.pyc` while it is ignored; the checks are green, `removed_bytecode` is `['shop/__pycache__/']`, `.env` and `.venv/lib/__pycache__/x.pyc` are there, and so is `tests/__pycache__/w.pyc` after the run.
2. **The landing's stage text says it** (no criterion). `skills/lem/stages/land.md`, the point of step 5 that says what the commands wrote that git neither tracks nor ignores (`removed_untracked`): one sentence that an ignored `__pycache__` that was in the worktree before the run is removed before the first command and named in `removed_bytecode`, and that this is no failure. No guide of `docs/`, the README or `site/index.html` names what the checks remove (`grep -rn "removed_untracked\|__pycache__" docs README.md site`, 2026-11-23, found nothing), so none changes.

## Decisions

- **The fix is in the checks, not only in the builder's text.** Rule 10 of `agents/lem-builder.md` already asks a builder to remove a `__pycache__` of its runs, and in moved-base-merge-agent-call (2026-11-22) two builders left one all the same; its test, `git status --short`, shows no ignored file. A text that a builder already missed twice is no fix; one call of git before the first command is. Cost on a small task: one `git ls-files` per run of the checks (unmeasured estimate: well under a second).
- **Only a folder named `__pycache__` that git ignores, with no ignored folder above it, goes** (criterion 1: "a `__pycache__` inside a folder that git ignores as a whole ... stays with that folder"). Python writes it and rebuilds it from the source, so its removal loses nothing. Every other ignored file may be the developer's (`.env`) or a setup's output (`node_modules/`, `.venv/`), and Lem cannot tell those from a leftover. A `__pycache__` inside an ignored folder is part of that folder and stays, also when that folder holds a tracked file and git lists the `__pycache__` on its own. Cost: a second git call only when a candidate is there.
- **The builder texts stay as they are.** Rule 10 of `agents/lem-builder.md`, `prompts/small.md`, `prompts/investigator.md` and `prompts/review.md` ask for an empty `git status --short`, which is still true of what git does not ignore; the ignored bytecode is now the checks' to remove.
- **The pull request gets no line for a removed cache** (the owner's answer B1, 2026-11-23): a removed cache changes no result of the change's code, and the checks' output and log keep the line.
- **The four suites' own check for a `__pycache__` stays** (decision 1 of the task's record): it catches a script that writes bytecode during the run, and step 6 of the criterion keeps that.

## What this plan does not verify

- Caches of other tools that git ignores (`.pytest_cache/`, `.mypy_cache/`) stay, and the plan does not check whether another project's checks count them: no run has shown one that does.
- A repository with no ignore rule for bytecode is not changed: there a `__pycache__` is untracked, and `need_worktree` refuses it before the checks, as today.
