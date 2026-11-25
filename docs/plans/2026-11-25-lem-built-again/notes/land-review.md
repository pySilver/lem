# Notes of the step `land-review`

What `land-review` needs in files it does not own, the stand-in it built until each exists, and
what other steps take from it. Each item names the file, what to change, and why.

## For `core`

1. **`records/landing/review.py`: a review's counts.** The slice's note stands: the counts
   `must_fix`, `should` and `nit` are kept as findings `rA.cN` that only count
   (`model/landing/review_said.counted`), which `app/landing/pr_text.py` reads by `COUNTED`.
   Fields on `Reviewed` would keep them apart; nothing here needs them sooner.
2. **`records/landing/record.py`: Jev's reads of a landing.** `main` kept them in
   `landing.json` (`alike` and `jev`, by the finding's digest), so that no finding is sent twice,
   by this run or the next. Asked: `Landing.jev: tuple[JevRead, ...]` with `{key, path | None,
   score | None, asked_at}`. Until then `app/landing/jev_kept.py` keeps them in
   `tasks/SLUG/jev.json`, written whole; retention may drop it with the other files.
3. **`records/task.py`: the owner's careful word.** `main` read it from the brief
   (`careful: the owner says so`, `land.owner_says_careful`), and `/lem be-careful` writes it.
   The record has no field for it; `Shape.careful` holds the shape's topics, which
   `model/landing/careful.reasons` takes as careful. Asked: a field the task step writes (for
   example `Task.careful_by_owner: str | None`), which `careful.reasons` will read first.
4. **`ports/judge.py`: what `same_items` is told.** The design names `same_items(defect,
   items)`; the port takes `paths`. The adapter now reads each item from its path on disk (the
   worktree is clean when `file` or `alike` asks), so it works as it is; an `Item` struct
   (`path, title, where, first`) in the port would spare the adapter the read.
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

7. **`[flow] topics` and `[jev] findings`** are not in `Team` yet. `app/landing/review_settings.py`
   reads the two keys from the main checkout's `.lem/settings.toml` with `tomllib` (topics `()`,
   findings `true` when the file says nothing, as `project.jev_of` on `main`). Replace it with
   the settings' structs and remove the module.

## For `land-base`

8. **The review's coverage over a rebase** (`landing.md` D, review coverage, `covers_one`).
   `model/landing/review_cover.covers` is the stand-in: a review covers the tip it read, and the
   commit `file` made after it (the checks moved there with `items_after`, after the review).
   `model/landing/review.unmet` should call `carry.py`'s coverage for a clean rebase, for new
   backlog files after the review (an edit of an item of the base asks for another review), and
   for the removal of the task's own item. The ledger rows of those cases moved to you.
9. **The owner's careful on an open request** (`the-owner-s-careful-on-a-task-whose-pull-req`,
   moved to you): `start` takes it in again; the review's floor is full once item 3 gives the
   word a field.
10. **A conflict's resolution.** `read` reads it when `landing.resolution.after` is the tip and
    `read` is None, records `of: resolution` (`scope: resolution` unless the review before left
    a must-fix), and sets `resolution.read` to the attempt. `base` writes the resolution.

## For `land-checks`

11. **The checks carry over `items_after`** (`gate_holds`). `file` moves `checked.tip` and
    `checked.tree` to its own commit and adds the items' paths to `checked.items_after`, as
    `main`'s `gated=tip` did, so the tip-equality of `checks.holds` holds after it. A cut after
    the items' commit and before the record makes the checks due again, then a read, after which
    `file` finds each item by its defect and commits nothing twice
    (`tests/journeys/landing/test_review.py`, the cut). With your carry over commits that only
    add backlog files, that cut lands on `file` again; so does a builder's commit of the items
    after a commit hook refused `file`'s.
12. **The review's word on a lowered bar** is written into `checked.lowered[].reviewer` by `read
    --record`, and `read` refuses a record that says nothing of a lowered file (`bar`).

## For `land-propose`

13. **Careful.** `model/landing/careful.reasons(record, edits)` gives each reason a request is
    careful, in `main`'s order: the shape's topics, `the plan says so: ...`, an edit of
    `.lem/settings.toml` (naming each table) or of `.lem/settings.local.toml`, and `the review says
    so: ...`. `app/landing/review_edits.edits(git, worktree, (base, tip))` gathers the edits. The
    not-green reasons, the line of the pull request and who merges should read them (the moved
    rows of the settings files).
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

## For `land-merge`

17. **The bar file of the merge brief**: `model/landing/jev_bar.named(own=...)` and
    `adapters/judge_jev.bar_of(checkout)` give the file's name as `main`'s `bar_file` did.

## For `land-text`

18. `lem land read SLUG` publishes the brief as `reviews/read-N-DIGEST.json` in the task's folder
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
