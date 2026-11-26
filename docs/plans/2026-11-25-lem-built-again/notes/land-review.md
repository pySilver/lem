# Notes of the step `land-review`

What `land-review` needs in files it does not own, the stand-in it built until each exists, and
what other steps take from it. Each item names the file, what to change, and why.

## For `core`

1. **Review counts.** `Reviewed.counts` holds the counts. The findings hold the defects
   outside the change that `file` places.
2. **Jev's reads.** `Landing.jev` holds the item comparisons and the bar verdicts. A
   comparison names its item path.
3. **The owner's careful word.** `/lem be-careful` records the time in `Task.owner_careful`.
4. **`ports/judge.py`: what `same_items` is told.** The design names `same_items(defect,
   items)`; the port takes `paths`, which the adapter reads. Jev must judge the items as the
   tip's commit has them, never a builder's edit on disk, so `app/landing/jev_staged.py` writes
   each item's title, `where` and first line, read from git, into `tasks/SLUG/items-at-tip/` for
   the one ask and removes the folder after it. An `Item` struct (`path, title, where, first`)
   in the port removes that stand-in.
5. **`ports/git.py`: two facts and one answer.** (a) `files(where, rev, folder) -> tuple[str,
   ...]` (`git ls-tree -r --name-only`): `app/landing/backlog.py` lists the backlog folder from
   the worktree's disk and reads each file with `show`, and finds the base's files as the tip's
   and those the diff touched. (b) `commit(...) -> Sha | GitRefused`: a commit hook that refuses
   the items' commit is an `Unanswered` today, which `app/landing/filing_commits.py` turns into
   the refusal `commit` with git's words.
6. **`tests/conftest.py`: clear Jev's environment.** `isolate` clears `LEM_` and `AGTERM_`; add
   `JEV_` and `OPENROUTER_` to `CLEARED_PREFIXES`, so that no run of the real wiring in a test
   can read the owner's key. Every test of this step passes its own environment to the adapter
   and binds `FakeJudge` or a stand-in transport, and none reads `os.environ` for Jev.

## For `settings`

7. **Done at the join of 2026-11-25:** `review.briefed`, `judge_same.checked` and
   `alike.asked_of` read `team_of(checkout).flow.topics` and `.jev.findings`, the base's
   committed file while the main checkout is elsewhere; the stand-in `review_settings.py` is
   gone.

8b. **`lem rules`.** The brief gives the reviewer the command `lem --repo WORKTREE rules
   --range BASE..TIP` (`inputs.rules`), since `main`'s `cmd_read` listed the rule files from
   `project.cmd_rules`, which is `settings`' (`cli/rules/command.py` refuses `not-built`). Once
   it is built, `review_brief.inputs` calls its function and lists the files.

## For `land-base`

8. **Done at the join:** `review_cover.covers` takes `carry.source(landing, world)`: a review
   covers the tip a clean rebase made of the tip it read; a must-fix it left stays open.

9. **The owner's careful on an open request** (`the-owner-s-careful-on-a-task-whose-pull-req`,
   moved to you): `start` takes it in again. The word on the task's record makes the
   review's floor full.
10. **A conflict's resolution.** `read` reads it when `landing.resolution.after` is the tip and
    `read` is None, records `of: resolution` (`scope: resolution` unless the review before left
    a must-fix), and sets `resolution.read` to the attempt. `base` writes the resolution.

## For `land-checks`

11. **The checks carry over `items_after`.** `file` keeps the checked tip and records the
    item paths. `item_carry` proves that the commits after the checked tip only add those
    items. A cut after the item commit and before the record still makes the checks due.
    The retry finds the item by its defect and commits nothing twice (`test_review.py`).
11b. **The bar's `edited` list.** `Checked.edited` holds the existing files the bar saw
    the change edit. The brief reads it when the range matches.
12. **The review's word on a lowered bar** is written into `checked.lowered[].reviewer` by `read
    --record`, and `read` refuses a record that says nothing of a lowered file (`bar`).

## For `land-propose`

13. **Careful.** Review and proposal use `careful.settings_reasons` for edits of the
    team's settings or one machine's settings.
14. **The places of the defects** are the `Filed` records: `item` with `path`, `worth` (`later`
    under "Filed in the backlog", `no` under "Filed as not worth it") and `cites` (the old `worth:
    no` item a new one names); `same` with the open item's `path` and a `line`; `seen` with a
    `line`. A `line` is `main`'s `seen_line` without its list mark: `` `WHERE`: TITLE; CALL: WHY``
    and `; an open item holds it, `PATH``. The slice's `pr_text` prints `- FINDING: LINE` for
    every record, an item's `line` None among them.
15. **Jev's read of the findings under the bar** (`jev_read`, refusal `jev-over`, the lines that
    end with Jev's read, moved to you): `Judge.over_bar(defect)` is built (the bar is the
    adapter's, from rule 6 of the builder file, `model/landing/jev_bar.py`), `items.read` reads a
    `worth: no` item, and `alike.key_of` is the finding's digest.
16. **A filed item gone from the tip.** `file --again` writes it once more, but `file` is due only
    while a defect waits for its place: `filing.holds` cannot see that an item left the tip
    without a fact of the world (the paths of the backlog folder at the tip). Until the world has
    it, `file --again` runs only while `file` is due, and propose's refusal can name one way on
    that works: a builder commits the item back. Asked of the owner of `app/landing/world.py`:
    `World.backlog: frozenset[str]`, after which `filing.holds` makes `file` due for a gone item.

16b. **No review clears a tip it did not read.** `model/landing/review.newest` is None while
    the newest attempt is one nobody answered: a review was due after the last answered one,
    so after two silent attempts `green.review` gives "no review read the change" and the
    merge agent does not merge it (`land.not_green` adds `due_of`'s why on `main`). A check of
    the review's floor in propose compares with `Reviewed.floor`, which `read --record`
    records from every careful reason, a settings edit and the owner's word among them; or it
    calls `review.holds`, which reads that floor.
16c. **An open item that leaves the tip.** A `same` place whose item the tip no longer holds
    is given its place again by the next `file` (`filing_asks.again_of`); `filing.holds` sees it
    once the world has the backlog's paths (item 16).

16d. **Done at the join:** `lem land file SLUG --again` also runs where `propose` is due, so the
    fix of propose's `item-gone` and `item-refuted` runs (`app/landing/filing_step.py`); with
    `--again` an over-bar defect whose open item now says `worth: no` gets an item of its own
    that names it.

## For `land-merge`

17. **The bar file of the merge brief**: `model/landing/jev_bar.named(own=...)` and
    `adapters/judge_jev.bar_of(checkout)` give the file's name as `main`'s `bar_file` did.

## For `land-text`

18. `lem land read SLUG` publishes the brief (its floor is `floor`, one word, and `floor_why`;
    a resolution's read has `range_diff`; `inputs` has `ask`, `rules` and `edited`) as `reviews/read-N-DIGEST.json` in the task's folder
    and names it in `result.path`; `result.record` is where the agent writes its record
    (`reviews/review-N.json`), and `next` is `lem land read SLUG --record FILE` (`do: spawn`,
    `job: review`). `--record` takes a path from the working directory or inside the task's
    folder. `stages/land.md` step 5 still tells the session to keep the output as `read.json`,
    and `prompts/review.md` reads `read.json`: name the published brief instead.
19. `lem land alike` answers `{task, finding, items, alike, jev?, read?, next}`; each entry of
    `alike` and `read` names its file as `path` (`main`: `item`). `prompts/small.md` step 7 reads
    no key by name, so it holds as written.

## For the orchestrator

20. `tests/journeys/test_skeleton.py`: its review's defect outside the change is now `cheap`, and
    its line of the pull request is `main`'s seen line. An `under` defect is an item with
    `worth: no` and a commit, as on `main`, which the skeleton's count of acts does not hold;
    `tests/journeys/landing/test_review.py` proves the items.
21. `tests/unit/landing/test_decisions.py`: its cases of `review` and `filing` moved into
    `tests/unit/landing/test_review.py` and `test_filing.py`.
22. `pyproject.toml`: `httpx` is a dependency of the app (`build(deps)` commit); it is also still
    in the dev group.
