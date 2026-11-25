# Lem built again: the roadmap, and where we are

The one page that says where the rebuild stands, what runs now, what is left, and how long it may
take. This file (`.claude/style-tools/reshape/roadmap.md`) is the live copy: the orchestrator
updates it at every change and the owner watches it in a companion. A copy goes to `rebuild` as
`docs/plans/2026-11-25-lem-built-again/roadmap.md` at the end of each group. The design itself is
`docs/plans/2026-11-25-lem-built-again.md` on `rebuild`, with its annexes in the folder of the same
name; this page does not repeat it.

To refresh the owner's page after an edit: `/Users/Silver/Projects/GitHub/lem/.claude/worktrees/rb-main/.venv/bin/python -I -B .claude/style-tools/reshape/roadmap-page.py` (it renders `roadmap.html` and reloads the companion whose id is in `roadmap-page.id`; `--open` makes a new one if it was closed).

## Where we are

- **2026-11-25 15:22 CET. Groups 0 to 2 are complete:** `rebuild` = `7a637e91` holds 16 of 35
  steps. Its last join: gates 7 passed and 1 skip of 8; unit 2,259 passed and 23 skips of 2,282;
  contract 169 of 169; hooks 42 passed and 5 skips of 47; journeys 192 of 192.
- **Group 3** (`land-text`, `owner`, `board-inputs`) is built and in review; core round 2 builds.
- **Next:** the two reviews of each built step, the joins, then each step drops its stand-ins
  (Sol, Opus reviews), then group 4.
- **Measure of progress:** the ledger holds 3,327 rows of today's behavior, each owned by one
  step. The steps of groups 0 to 2 own 1,881 of them (57%); every one of those rows has a fate and
  a proof (`tests/ledger/check.py --step STEP`).
- **Open with the owner:** nothing. His goal of 15:00 is to complete this roadmap; the cutover
  waits for his word.

## Now running

| Who | What | Since | Waits for |
| --- | --- | --- | --- |
| Opus | core round 2: every request of the steps to `core`; `Task.after` a list; `ticked`; the test entry fails on a file that does not collect | 14:45 | its report, then Sol and Astra review |
| Sol | review of `land-text` (built: 9 texts, A1 A2 A3 A5, model and history tests, coverage of the landing's model 100%) | 15:22 | its findings |
| Sol | checks each of Astra's 25 findings on the landing's seams (Astra overstates; each confirmed one gets a probe that becomes its failing test) | 15:06 | `audit-g2/verify/`; then Sol repairs the confirmed ones, Opus approves |
| Sol | review of `owner`, round 2 (round 1: 15 findings, all repaired by Sol and committed `1b41f8e6`; unit 2,095 passed, 20 skipped) | 15:21 | no must left, then Astra |
| Sol | repairs `board-inputs`: 10 findings (6 musts: a criteria fixture that refuses its own file, a merge test that accepts a wrong commit on the page, the forge clock and artifact links lost, a damaged picture, elapsed time across a clock change) | 15:19 | its repair; then Sol again |

**Done since 14:30:** Sol's case sheets of 8 coming steps (about 880 rows: 760 with a direct proof on `main`, 79 with none); Astra's audit of the landing's seams (25 findings, 11 seams sound).

**Next:** each built step gets a review by Sol and one by Astra; then its join. Group 4 (the board)
starts when `owner` and `board-inputs` are on `rebuild`.

## Decisions (newest first; the whole text of each is in `choices-for-the-owner.md` under its number)

**O** = the owner decided; **S** = the session decided while he was away or by his delegation (open
to him: tell the session to change one).

| # | Decision | By | Day, time |
| --- | --- | --- | --- |
| 23 | Less Opus: Sol reviews first, Sol repairs, Astra reviews, Opus approves last; Astra integrates a join, Sol challenges it; Sol builds `board-pages`, `ask`, `addons-outside`, `browser`, `close`, mutation, trial scripts, stand-in drops, faster tests | O | 11-25 15:00 |
| 22 | A feature larger than one pull request: a feature branch, part pull requests into it, one squashed pull request to the base; the feature is a task with parts; built after the cutover | O | 11-25 14:20 |
| 21 | `Task.after` becomes a list, and `TicketAct` takes `ticked`, before release 1.0 | S | 11-25 14:20 |
| 20 | One man's show: explore large features and shipment (Lem does next to nothing there); signals only through Linear; no product memory, no roadmap ranking, no token limits; several repositories later | O | 11-25 13:50 |
| 19 | The merge line: Approve button; checks on a moved base; a red task leaves the line; a task already checked goes first; the server counts who waits; no agent sets the order | O | 11-25 13:10 |
| 18 | From SeeMasta: the merge review checks each cited test's assertion; decisions go into the merge commit; the agent chooses the fast track's review (his design); later: neighbours in a brief, a throwaway prototype | O | 11-25 12:30 |
| 17 | Pele replaces Mermaid.js on the board and the question pages | O | 11-25 10:50 |
| 16 | `watchfiles` leaves; the board's stream polls (its Homebrew build failed) | S | 11-25 06:15 |
| 15 | The hooks' timing test measures only on a quiet machine (load at or under 4.0) | S | 11-25 05:50 |
| 14 | A test wrote into the real Lem state for two minutes: removed; guards added (tests run in a temp folder; the new Lem never writes into a 0.3 state) | S | 11-25 05:20 |
| 13 | The command line is three times its estimated size; `--repo PATH` is one option of the root | S | 11-25 04:10 |
| 12 | The design is on `main`; the build branch `rebuild` is on GitHub | S | 11-25 03:35 |
| 11 | Defaults of the design talk: `main` takes fixes only; the hook budget 50 ms (fails over 55 ms at p95); trials on a scratch copy; wemake holds `src/lem` only | S | 11-25 03:00 |
| 10 | A drop during a landing step takes the step lock | S | 11-25 03:05 |
| 1-9 | Before and during his sleep: the libraries (Click, Jinja2, msgspec, tomlkit, httpx), the style pieces merged to `main`, the pytest entry | S | 11-24 to 11-25 |

**Open with the owner:** none asked now. Waiting for his word only: the cutover (merge to `main`,
release 1.0.0, the wipe of 0.3's state).

## The steps

Status: **done** (merged into `rebuild`), **join** (built, reviewed, in its join), **repair**,
**building**, **next**, **later**. Rows: the ledger rows the step owns (`tests/ledger/owners.tsv`).

| # | Step | Group | Status | Rows | What it is |
| --- | --- | --- | --- | --- | --- |
| 1 | `ledger` | 0 | done | | every behavior of today's Lem as a row with an owner |
| 2 | `core` | 0 | done | 48 | kernel, records, store, ports, wiring, test entry, fakes |
| 3 | `tree` | 0 | done | 39 | the whole command line, every leaf a stub |
| 4 | `slice-land` | 1 | done | | a fast-track task from open to landed, thin |
| 5 | `slice-board` | 1 | done | | the board server, thin |
| 6 | `slice-session` | 1 | done | | a task's session and its hooks, thin |
| 7 | `trial-skeleton` | 2 | done | | S1 to S7 on a scratch repository |
| 8 | `land-base` | 2 | done | 115 | the base, its read, the standing rule |
| 9 | `land-checks` | 2 | done | 192 | the checks, the load gate, red and hold |
| 10 | `land-review` | 2 | done | 128 | the review and its record |
| 11 | `land-propose` | 2 | done | 150 | the pull request and its text |
| 12 | `land-merge` | 2 | done | 164 | the merge agent's read, the merge, reconcile, clean |
| 13 | `task` | 2 | done | 303 | a task's records, statuses, holds, queue |
| 14 | `criteria` | 2 | done | 165 | the criteria and their check on the base |
| 15 | `sessions` | 2 | done | 235 | sessions, hooks, transcripts, signs |
| 16 | `settings` | 2 | done | 342 | the four settings files and their places |
| — | core round 2 | — | building | | the steps' requests to `core`; `Task.after` a list; then stand-ins go |
| — | merge line | — | next | | follow-up of `land-merge`: amendment A4 |
| 17 | `land-text` | 3 | review | 33 | the landing's texts; amendments A1 to A3, A5 |
| 18 | `owner` | 3 | repair | 33 | the owner's status, away and back |
| 19 | `board-inputs` | 3 | repair | | what the board reads |
| 20 | `board-views` | 4 | later | 199 | the board's model and views |
| 21 | `board-pages` | 4 | later | 256 | the pages, assets, board kit; Pele (A7) |
| 22 | `board-acts` | 4 | later | 116 | the owner's acts; the Approve button (A4) |
| 23 | `board-duties` | 4 | later | 88 | the server's duties; the merge wait count (A4) |
| 24 | `board-service` | 4 | later | 158 | the server, its stream (polling, A8), peers' door |
| 25 | `ask` | 5 | later | 102 | the question pages |
| 26 | `addons-flow` | 5 | later | 122 | the optional parts of the flow |
| 27 | `addons-outside` | 5 | later | 160 | Jev, Linear, GitHub issues, peers |
| 28 | `journeys` | 6 | later | | the journeys of the whole app |
| 29 | `browser` | 6 | later | 49 | headless Chrome checks, no skip |
| 30 | `guides` | 7 | later | 108 | README, docs, site in STE |
| 31 | `pack-trial` | 8 | later | 12 | the Homebrew keg, P1 to P6 |
| 32 | `mutation` | 9 | later | | no surviving mutant without a test |
| 33 | `trials` | 10 | later | 1 | R1 to R9: real agent sessions on real tasks |
| 34 | `close` | 11 | later | 9 | the full run, the ledger whole, no old-form text |
| 35 | `cutover` | 12 | his word | | merge to `main`, release 1.0.0, wipe 0.3's state |

## Who does what (the owner's scheme of 2026-11-25 15:00: Opus is the limit)

- **Each step goes:** build -> Sol reviews -> Sol repairs (the session keeps or drops each finding
  and commits) -> Sol again, until no must -> Astra reviews (the session weighs each finding) ->
  Sol repairs -> Opus gives the final approval (short, read only) -> the join.
- **The join:** the script; on a conflict or a red level, Astra integrates and Sol challenges the
  resolution; the step's Opus builder only when both cannot settle it.
- **Opus builds:** core round 2, `land-text`, `owner`, `board-inputs`, `board-views`,
  `board-acts`, `board-duties`, `board-service`, `addons-flow`, `journeys`, `guides`; and approves.
- **Sol builds** (Opus approves): `board-pages`, `ask`, `addons-outside`, `browser`, `close`, the
  mutation runs, the trial scripts R1 to R9, each step's drop of its stand-ins, faster test levels
  (journeys in parallel once each test has its own home); and the case sheets of each coming step.
- **Astra:** the second review of each step, the joins' integration, the audits across seams.
- **The session** orchestrates: briefs, keeps or drops findings, commits Codex's repairs, merges,
  this page. It writes no code.

## Amendments since the design (2026-11-25)

Each is in `.claude/style-tools/reshape/choices-for-the-owner.md` under its entry number, and goes
into the step named. The step's builder folds it into the design's text when it builds it.

| # | Amendment | Entry | Step |
| --- | --- | --- | --- |
| A1 | The merge agent checks that each criterion's cited test holds its assertion, and names any observation the evidence cannot settle and who can make it | 18 | `land-text` |
| A2 | The merge commit's text lists the task's decisions, so they survive the prune | 18 | `land-text` |
| A3 | The fast track's review is the agent's choice: an intake hint beside the criterion; at the end its own read or a round with the lenses that fit, a reason for each | 18 | `land-text` |
| A4 | The merge line: the board's button says Approve; before the merge of an approved task on a moved base, the checks run on the rebased task; a task red on its rebase leaves the line; a task checked on the current base goes first; the server records how many approved tasks wait at each merge | 19 | merge line, `board-acts`, `board-duties`, `land-text` |
| A5 | The owner's ruling of A4 as a bullet of `docs/rulings/rulings.md` | 19 | `land-text` |
| A6 | `Task.after` is a list, and `TicketAct` takes the word `ticked` (both for the feature branch after the cutover; a change of either after 1.0 takes two releases) | 21, 22 | core round 2 |
| A7 | Pele replaces Mermaid.js on the board and the question pages | 17 | `board-pages`, `ask` |
| A8 | `watchfiles` leaves; the stream polls | 16 | `board-service` |

## After the cutover

| Item | State | Where |
| --- | --- | --- |
| A feature larger than one pull request: a feature branch, part pull requests into it, one pull request to the base at the end; the feature is a task with parts | his direction (entry 22); Astra and Fable check it against the landing rules, and name what the rebuild must reserve now | `.claude/style-tools/reshape/feature-parts/`; a new step 36 |
| Other open tasks on the same files, named as facts in a brief | backlog item to write | after 36 |
| A throwaway prototype for a task whose shape is unknown | option (b) of the interview item | `docs/backlog/the-interview-grills-every-task-the-same-way.md` |
| Signals from production through Linear: Lem watches Linear for issues of a given type | his word (entry 20); no direct integration | backlog item to write |
| One change across repositories | low priority (entry 20) | none |
| A watch of the deploy run a merge started | not taken now; beside "CI repair" | `docs/backlog/add-ons-after-the-core.md` |

## How long (an unmeasured estimate)

What was measured, from the commit times of `rebuild` and the handoff's `date` lines on
2026-11-25: the design was final at about 03:40; group 0 (4 steps) was on `rebuild` at 05:35;
group 1 (3 slices) at 06:15; group 2 (10 steps, 9 builders at once) from 06:15 to 15:22, about
9 hours, of which an 80-minute stop on a rate limit of Opus, and journeys levels that took over
2.5 hours each until a test fault was found (a shared load gate; fixed at 15:10, the level now
takes about 12 minutes). So the first 57% of the ledger's rows took about
11 hours of clock time with the orchestrator at work the whole time.

What is left: 1,446 rows, of which the board's five steps hold 817 and the add-ons 282, and five
steps with few rows but real work (`journeys`, `browser`, `mutation`, `pack-trial`, `trials`).
By group, from the rates above (an unmeasured estimate): core round 2, 2 to 3 hours; group 3,
2 to 4; group 4, 6 to 10; group 5, 4 to 6; groups 6 and 7, 4 to 7; `pack-trial` and `mutation`,
3 to 5; the trials, 4 to 8, with each defect a trial finds becoming a new step; `close`, 1 to 2.

- **To the cutover:** about 26 to 45 hours of work, 2 to 4 days of calendar if the session
  works through, as it did on 2026-11-25. A rate limit, a long trial, or a question that waits
  for the owner adds to it.
- **To a stable companion:** the cutover plus his daily use on his own projects (the scratch
  repository, then mybaze) until a week passes with no defect of Lem that stops a task. That
  week is a rule of thumb, not a measure.

The estimate is checked at each group's end: this section gets the group's real time beside its
estimate.

## How to resume (after a compaction, or in a new session)

1. Read this page, then the newest "Update" of `.claude/style-tools/reshape/handoff.md` (the live
   log: what runs, which builder, which review), then `choices-for-the-owner.md`.
2. The design: `../2026-11-25-lem-built-again.md` (part 9 is the build order and the ownership
   table), `builder-rules.md`, `landing.md`, `surfaces.md`, and `notes/STEP.md` for each step's
   requests to others.
3. The tools of the orchestrator: `/tmp/lem-rebuild/join.sh STEP` (copy in
   `.claude/style-tools/reshape/rebuild/`), the review launcher `reviews/launch.py`, the step
   template `step.template.md`. `/tmp` does not survive a restart: copy them back from there.
4. The rules that bind every session of the rebuild: the owner's board server (pid 3311, ports
   4536 and 4537) is never touched; nothing writes into `/Users/Silver/Projects/GitHub/lem/.lem/`;
   every `lem` or hook run has `LEM_SERVE=off` and a throwaway `HOME` and `XDG_CONFIG_HOME`; one
   `--level full` run at a time; builders never merge, the orchestrator does; `cutover`, a
   release, a tag and a wipe of his state wait for his word.
