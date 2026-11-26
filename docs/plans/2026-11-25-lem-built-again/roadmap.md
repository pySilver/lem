# Lem built again: the roadmap, and where we are

The one page that says where the rebuild stands, what runs now, what is left, and how long it may
take. This file (`.claude/style-tools/reshape/roadmap.md`) is the live copy: the orchestrator
updates it at every change and the owner watches it in a companion. A copy goes to `rebuild` as
`docs/plans/2026-11-25-lem-built-again/roadmap.md` at the end of each group. The design itself is
`docs/plans/2026-11-25-lem-built-again.md` on `rebuild`, with its annexes in the folder of the same
name; this page does not repeat it.

To refresh the owner's page after an edit: `/Users/Silver/Projects/GitHub/lem/.claude/worktrees/rb-main/.venv/bin/python -I -B .claude/style-tools/reshape/roadmap-page.py` (it renders `roadmap.html` and reloads the companion whose id is in `roadmap-page.id`; `--open` makes a new one if it was closed).

## Where we are

- **2026-11-26 17:44 CET.** `rebuild` = `72c3a16b` holds all 35 steps but one row of `close`. The trials:
  P1 to P6, R2 to R9 and A1 to A5 passed (A3, A4, A5 on the fixed `rebuild` after failing on the trial
  tag `v0.99.0`); R1 passed every part but its review, which waits for the trial home's Codex login (the
  owner, at the Mac). Each defect the trials found is fixed on `rebuild` with its test (the Stop hook's
  mark, a reload that dismissed, an old card back, the mailbox hook in the doctor, the fast track's
  criterion, the Tailscale app binary, the door setting, the card that re-rendered under his hand on the
  phone, the white page after a merge). `close`: every one of the 3,327 ledger rows has a fate; the whole
  suite ran once (5,280 collected, 5,275 passed, 5 skipped: the hook timings at load 5.2, measured quiet
  in P4) and `check.py` proves every row but R1's. Astra's reviews of the close found 19 blockers, among
  them an earlier round's reply that could authorize a merge; all fixed, Opus approved the whole.
  The pass over the defects found on the way joined too (decision 30, amended; browser 56 of 56).
  Left: R1's review (his Codex login), then the cutover on his word. The trial tag `v0.99.0` and branch
  `trial-p1` are deleted on GitHub; the keg, the local tap commit and the trial home's gh login stay for R1.
- **Group 3** is on `rebuild`.
- **Group 4** (the board) is on `rebuild`; it built from 15:33 on a base of `rebuild` with core round 2, `owner` and
  `board-inputs` merged in (Astra moved every reader of the task wait to the list: `f3b82ece`).
- **Next:** R1's review once he logs the trial home's Codex in, then the cutover on his word.
- **Measure of progress:** the ledger holds 3,327 rows of today's behavior, each owned by one
  step. The steps of groups 0 to 2 own 1,881 of them (57%); every one of those rows has a fate and
  a proof (`tests/ledger/check.py --step STEP`).
- **Done (11:20):** the trial home's gh is logged out (gh auth status: not logged in; hosts.yml empty); the owner's reminder needs no action.
- **Open with the owner (the trials, `trials-round1.md` beside this page):** a Claude Code login in a scratch profile (R1, R2, R8, A1 to A5, and P5's last row through P1's plugin); P1's tag and tap branch; P3 and P6 from the Dock; R6 his phone; R7 a second tailnet machine with a door; R9 a project he names. One side effect to tell him: the keg install upgraded Homebrew's zstd 1.5.7_1 to 1.6.0 (modes set back; not rolled back). His goal of 15:00 is to complete this roadmap; the cutover
  waits for his word.

## Now running

| Who | What | Since | Waits for |
| --- | --- | --- | --- |
| owner | R1's review (the trial home's Codex login at the Mac), then his word for the cutover | 18:41 | his return |
| Sol | close: the 7 rows that are defects (the merge seat and its stand-in, a reply with no seat, a stale peer refusal) | 15:20 | review, join, then T full and check.py |
| owner | the trial home's Codex login (Inbox), for R1's review | 14:12 | his return |
| owner | a page asks how far the last trials may go without him (P1 needs a tag and a branch on his tap; P3 a Claude Code he starts from the Dock; R6 his phone) | 03:29 | his answer |

**Done since 14:30:** the inventory of the stand-ins (`standins-inventory.md` beside this page: 14 droppable now, 9 after the next joins, 6 kept for later steps); group 3 and group 4 landed (`land-text`, `board-acts`, then the four other board steps in one join); `addons-flow`, `ask` and the seams repairs reviewed and repaired; Sol's case sheets of 8 coming steps (about 880 rows: 760 with a direct proof on `main`, 79 with none); Astra's audit of the landing's seams (25 findings, 11 seams sound).

**Load:** at 20:56 the load average was about 8 on 10 cores. At 16:29 it was 52 to 82 (about 12 agents running test suites at once), and a hook timing case failed under it; new sessions wait while it is over about 20.

**The joins:** approved steps now join in batches on one integration branch (Astra merges and wires, Sol challenges, all seven levels once): eight joins in a row at about 20 minutes each (unmeasured estimate) had become the slowest part.

## Decisions (newest first; the whole text of each is in `choices-for-the-owner.md` under its number)

**O** = the owner decided; **S** = the session decided while he was away or by his delegation (open
to him: tell the session to change one).

| # | Decision | By | Day, time |
| --- | --- | --- | --- |
| 27 | The trials run without him where nothing outside this Mac changes; P1's tag and tap branch, P3 (a Dock-started Claude Code), R6 (his phone) and R9 (his project) wait for him | O | 11-26 10:19 |
| 28 | The rest of the trials: his gateway settings in the trial home, a trial tag `v0.99.0` removed after, P3 and P6 by the agent, R6 now with his phone, R7 on his MacBook Pro, R9 on mybaze | O | 11-26 11:44 |
| 29 | R9: 34 mybaze files at 0455840a, the NFC size task, the operator answers the owner steps | O | 11-26 12:14 |
| 30 | A damaged task record: a view or total over many tasks skips it and names it; a decision refuses only when that record could change its outcome, and a decision about one task reads that task and those it names (amended after Astra's review) | S | 11-26 16:13 |
| 26 | The docs generator is Zensical (Python, uv, the Material team's successor; pinned; its diagrams drawn by Pele, the board's renderer, so no Mermaid copy and no outside host); not Material for MkDocs (end of life 2027-05-05), not Starlight (Node) | O | 11-25 21:35 |
| 25 | The whole documentation lives on the site, built from `docs/*.md` as the one source; the README points to it; no hand-kept copy | O | 11-25 21:25 |
| 24 | The board's views are 15,091 lines (the plan budgeted 3,800 for all of `board/`); the whole new board so far is 18,268 lines against 17,148 for the old board's model, pages and task panel on `main` (+7%): kept; the review cuts duplication; a size pass again at `close` | S | 11-25 17:03 |
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
| — | core round 2 | — | done | | the steps' requests to `core`; `Task.after` a list; then stand-ins go |
| — | merge line | — | done | | follow-up of `land-merge`: amendment A4; Sol's challenge of the second join found its gap on `rebuild` (an approved task merges on a moved base after a safe read, without checks on the rebased task) |
| 17 | `land-text` | 3 | done | 33 | the landing's texts; amendments A1 to A3, A5 |
| 18 | `owner` | 3 | done | 33 | the owner's status, away and back |
| 19 | `board-inputs` | 3 | done | | what the board reads |
| 20 | `board-views` | 4 | done | 199 | the board's model and views |
| 21 | `board-pages` | 4 | done | 256 | the pages, assets, board kit; Pele (A7) |
| 22 | `board-acts` | 4 | done | 116 | the owner's acts; the Approve button (A4) |
| 23 | `board-duties` | 4 | done | 88 | the server's duties; the merge wait count (A4) |
| 24 | `board-service` | 4 | done | 158 | the server, its stream (polling, A8), peers' door |
| 25 | `ask` | 5 | done | 102 | the question pages |
| 26 | `addons-flow` | 5 | done | 122 | the optional parts of the flow |
| 27 | `addons-outside` | 5 | done | 160 | Jev, Linear, GitHub issues, peers |
| 28 | `journeys` | 6 | done | | the journeys of the whole app |
| 29 | `browser` | 6 | done | 49 | headless Chrome checks, no skip |
| 30 | `guides` | 7 | done | 108 | README, docs, site in STE; the whole docs on the site from `docs/*.md` with Zensical (decisions 25, 26) |
| 31 | `pack-trial` | 8 | running | 12 | the Homebrew keg, P1 to P6 |
| 32 | `mutation` | 9 | done | | no surviving mutant without a test |
| 33 | `trials` | 10 | running | 1 | R1 to R9: real agent sessions on real tasks |
| 34 | `close` | 11 | trials | 9 | the full run, the ledger whole, no old-form text |
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
