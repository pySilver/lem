# Annex: the surfaces, today's against the new build

An annex of `docs/plans/2026-11-25-lem-built-again.md`. One row for each of the proof of
concept's commands (`tests/unit/commands.json`), board acts (`docs/board.md`, `serve.py`), hooks
(`hooks/hooks.json`), doctor checks (`doctor.py: main`) and settings keys (`docs/settings.md`),
at `main` `bf6d2836`. "Step" is the step id of the design's part 9. This annex is the map; the
behavior ledger (`tests/ledger/rows.tsv` and `extra.tsv`) is the complete list, and a row this
annex misses is placed by the step that owns its source. A command that group 1 builds
first as a slice names that slice too; the step named owns it from group 2 on.

## A. Commands

| Today | New | Step |
| --- | --- | --- |
| `project show` | `settings show` (each value with `from`, the places, `settings: null` when not onboarded) | `settings` (slice: `slice-land`) |
| `project path NAME` | `path NAME` (`lessons`, `rulings`, `plans`, `profile`, `cast`, `state`, `backlog`) | `settings` |
| `project may-land BRANCH` | dropped: each step refuses `protected` itself | `land-base` |
| `project worktree-dir SLUG` | `task worktree SLUG --path` | `task` |
| `project worktree SLUG BRANCH` | `task worktree SLUG [--branch B] [--checkout DIR]` (makes it, runs `checks.setup`) | `task` |
| `project init --base --codex` | `init --base B [--codex]` | `settings` |
| `project set SCOPE NAME WORDS` | `settings set seats.NAME VALUE --local\|--home` (`default` removes; a seat without model or effort refused) | `settings` |
| `project plan-file SLUG --date` | `task plan-file SLUG [--date]` | `task` |
| `project rules FILES --range` | `rules [FILES] [--range]` | `settings` |
| `project task-dir SLUG --ask --ticket --ticket-repo --branch --night` | `task open SLUG --ask WORDS [--ticket ID] [--ticket-repo R] [--branch B] [--night YYYY-MM-DD] [--after SLUG] [--plan-only] [--item PATH] [--from SLUG]`; `task dir SLUG` | `task` |
| `project state SLUG STATUS LINES --start-over` | `task move SLUG STATUS [--line L]... [--start-over WHY]`; `dropped` by his drop from any status that is not ended, by the transitions of the design's part 3 (`correct.md`, "drop"), under the step lock | `task` (slice of `task move`: `slice-land`) |
| (lines `type: T, because WHY`, `then:`, `the owner's order:`) | `task read SLUG --type T --why W --track small\|full [--careful TOPIC]... [--then interview\|fast\|lead\|investigation] [--order WORDS] [--after SLUG] [--wait criteria\|interview]` | `task` |
| (lines `lead: builder`, `small change: one builder`, `plan committed N tasks`, `task N of M`) | `task span SLUG lead\|small\|task --of N/M start\|end`; `task planned SLUG --tasks N [--careful WHY] [--large]` | `task` |
| `project seat SLUG SEAT` | `seat show SLUG ROLE` | `sessions` |
| `project seat-failed SLUG SEAT --seat --error --said` | `seat failed SLUG ROLE --seat --error --said` (the fallback starts; the PR names who stood in) | `sessions` |
| `project seat-again SLUG` | `seat again SLUG` | `sessions` |
| `project tasks` | `task list [--ended]`, `task show SLUG` (status, hold, `ticket_owed`, `board_answer`, `night`, `mode`) | `task` |
| `project resume SLUG` | `task resume SLUG` (parked: same task; dropped: a new task with `--from`; release-stopped: a new request) | `task` |
| `project owner STATUS --words --seen --every` | `owner away\|back [--words]`, `owner watch [--seen ID] [--every N]` | `owner` |
| `project ticket-step SLUG STEP --login` | `task ticket SLUG STEP [--login]`, accepted after the end | `task` |
| `project log SLUG EVENT FIELDS` | typed: `task span SLUG NAME start\|end [--job J] [--by B]`; `task investigated SLUG --result bug\|none\|question\|unreproduced --call small\|full`; `task talked SLUG --reviewer AGENT --turns N --questions N --settled N --open N --repaired N --design N --unargued N --root N --layer N --shared N` (`project.talk_form`; the PR shows them); `criteria read SLUG start\|done\|silent --by lem\|lead`; `criteria skip SLUG asked\|yes\|no` | `task`, `criteria` |
| `project may-start SLUG` | `task may-start SLUG` (prints the commands of "start SLUG now") | `task` |
| (his "start SLUG now", `/lem build`) | `task start SLUG --words WORDS`; `task build SLUG\|PLAN-FILE` | `task` |
| `project state-dir` | `path state` | `settings` |
| `project waiting` | `waiting [--task SLUG]` (the nine groups; `merge_refused`, `conflict`, `after_dropped`) | `owner` |
| `project proposals` | `proposals list\|add --kind night\|retro --date D --file F\|verdict\|drop` | `addons-flow` |
| `project serial WORDS` | `serial -- CMD` | `land-checks` |
| `project may-nap` | `nap may` | `addons-flow` |
| `project prune --dry-run --days` | `prune [--dry-run] [--days N]` | `board-duties` |
| `project load --start` | `settings set load.start N\|none --machine` (a waiting run reads it at its next look) | `settings` |
| `project handoff --tokens` | `settings set handoff.tokens N --machine` | `settings` |
| `land start SLUG --conflicting` | same | `land-base` |
| `land base SLUG` | same | `land-base` |
| `land polish SLUG --done` | same | `land-checks` |
| `land alike SLUG --where --title --what` | same; with Jev not asked, its `read` list (each item's path, title, place and worth) for the builder to read (`cmd_alike`) | `land-review` |
| `land checks SLUG --status --stop` | same (`overdue`, `say`, `waits`, `resumed`) | `land-checks` |
| `land read SLUG --record` | same | `land-review` |
| `land file SLUG --again --same --new` | same | `land-review` |
| `land propose SLUG --title --notes` | same | `land-propose` |
| `land merge-review SLUG --file --no-answer --tip --base` | same | `land-merge` |
| `land merge SLUG --by --message --via --standing --tip` | same | `land-merge` |
| `land merged SLUG` | same | `land-merge` |
| `land clean SLUG` | same | `land-merge` |
| (none) | `land next SLUG`: the due step and why | `land-merge` |
| `criteria STEP SLUG` (approve, approved, change, digest, show, record, red, inputs; `--file --small --read --alone --shown --words --typed --pairs --unchanged`) | `criteria VERB SLUG`, the same verbs and options; `--repo` dropped | `criteria` (`red`, `inputs`: `land-checks`; slices of `approve`, `record`: `slice-land`) |
| `decisions log\|criterion\|changes\|breaker\|pending\|list` | same | `criteria` |
| `board --repo --task --follow --no-open --demo --page --name` | same, `--repo` dropped | `board-service` |
| `serve --ensure --stop --tailscale --tailscale-off --port --tailscale-port --host --verbose --add --remove --list --push-test` | `serve ensure\|stop\|run [--host] [--verbose]\|door on\|off\|add DIR\|remove DIR\|list\|push-test`; ports by `settings set` | `board-service` (slices of `ensure`, `stop`, `run`: `slice-board`) |
| `serve --join --leave --peers` | `serve join HOST\|leave HOST\|peers` | `addons-outside` |
| (a `lem` command) | starts the server detached, silently, when its pid file names no live process (`__main__.look_for_server`); not for `help` and `version` (they answer first) and not for `serve`, `board`, `doctor`, `ask`, `jev` (`__main__.NO_LOOK`); `LEM_SERVE=off` stops it | `board-service` |
| `picker --repo --list` | `picker [--list]` | `addons-flow` |
| `session open\|next\|close\|close-job\|handoff\|talk\|wake\|stopped\|worked\|wait\|list\|plugin-dir` | same, same options | `sessions` (slices of `open`, `next`, `close`, `list`: `slice-session`) |
| `doctor` | same (D) | `settings` |
| `corrections hook` | `lem-hook corrections` | `sessions` |
| `corrections list\|lessons\|worker PAYLOAD\|show ID\|record ID ...` | same | `addons-flow` |
| `corrections collect ANSWER` | `settings set corrections.collect yes\|no --machine` | `settings` |
| `experts brief\|record`, `cast init\|run-dir`, `jev check SPEC` | same | `addons-outside` |
| `issue check\|read\|start\|land\|drop\|answer` | same | `task` |
| `ask ask SPEC`, `ask q`, `ask wait`, `ask close`, `ask demo`, `ask templates`, `ask render SPEC --out` (attachments kept) | same; outcomes in `result.outcome` | `ask` |
| `ask hook-stop` | `lem-hook stop` | `sessions` |
| `help`, `version`, `doctor` on a version mismatch | answer as today; every other command refuses with the one line (`__main__.cli`). The envelope applies to dispatched commands: `help` prints text; `version` prints JSON with the top-level keys `root`, `version` and `commit` (`__main__.version`) | `tree` |

## B. Board acts and addresses

| Today | New | Step |
| --- | --- | --- |
| `/`, `/HOST/WS/` views T, W, B, A; tabs 1 to 5; Cmd-K search; J, K, H, L, arrows, Enter, Escape | same | `board-pages` |
| Charts: Fit (button or `0`) | same (`chart.js`) | `board-pages` |
| A parked task's row: open the task or its session | same | `board-pages` |
| Backlog attribution "added by AUTHOR on DAY, in task SLUG" | from git and the `Lem task:` line | `board-views` |
| `GET .../stream` | SSE; Turbo morph on `refresh`; reread on reconnect and phone wake; in-flight form, note and focus kept | `board-pages` |
| New task (`+`, `N`); backlog "Start a task" | POST `.../tasks`; the claim under the workspace lock | `board-acts` |
| Reviewer item Drop | refused while a task builds it; the proposals record keeps it | `board-acts` |
| Merge (confirm page; phone: active after reading to the end) | POST `.../tasks/SLUG/merge` with the shown tip | `board-acts` |
| Open a session | POST `.../tasks/SLUG/session` | `board-acts` |
| Plan Build/Drop; breaker Help/Park/Drop (Help needs a note; Park and Drop confirm); Skip the persona read; Approve this criterion (No needs a note; shown digest current); Approve the criteria (No is a change); prior-release Approve | POST `.../tasks/SLUG/answer` with question id, option, note, shown digest | `board-acts` (rules: `owner`) |
| A note with no option; a wish to talk | refused, the row stays | `owner` |
| First answer counts; the board says which took effect | `expect` on the question | `owner` |
| A card answered on the board; its tune preview Replay (button or `R`) | POST `.../tasks/SLUG/cards/PAGE/answer`; the card page keeps `ask.js` | `ask` |
| Jump to a session (his click) | POST `/HOST/WS/agterm/SESSION` | `board-acts` |
| Server stop | POST `/api/server/stop`, local listener only | `board-service` |
| Manifest, service worker, "Turn on" notifications | `/manifest.webmanifest`, `/sw.js`, `/push/key`, `/push/subscribe` | `board-service` |
| The door: his Tailscale login only, never Funnel, one host, same-origin writes | `board/door.py` on the door listener only | `board-service` |
| An unreadable session: guard by events, no fresh session, "stopped" with the reason | `duties/guard.py` | `board-duties` |
| Inbox link while away; "no link" reason | kept | `addons-outside` |
| Another machine under one address; "not reachable"; the loop guard | `peers` proxy, one hop | `addons-outside` |

## C. Hooks (`hooks/hooks.json`, each through `/bin/sh "$CLAUDE_PLUGIN_ROOT/hooks/run" SELECTOR`)

The selectors are `main`'s (`src/lem/hooks.py`); `sessions` owns them all.

| Event, matcher | Selector | New |
| --- | --- | --- |
| UserPromptSubmit | `corrections` | only when `corrections.collect` is true (`tomllib`); empty, injected and slash-command prompts skipped (`corrections.cmd_hook`) |
| SessionStart `startup\|resume` | `serve` | the server's start, detached |
| SessionStart `startup\|resume\|clear\|compact\|fork` | `session-start` | one framed line to `tasks/SLUG/sessions.jsonl`; `LEM_PLUGIN_ROOT` to `CLAUDE_ENV_FILE`; the version line; the other-`lem` line; after `compact`, the task's handoff and files |
| PreCompact `auto\|manual` | `precompact` | the handoff's headings |
| Stop, async | `stop` | the open card's mark, rechecked |

## D. Doctor checks (`doctor.py: main`)

Kept, each with its need (`required`, `recommended`, `optional`, `project`) and its fix: Python,
git, revmux and its skill, agterm and agtermctl, gh and its login, webrev, agdoc
(recommended), backlog, plannotator-tui (recommended), Plannotator, Jev's key, Codex
(recommended), the mailbox chat and its skill, cronn, the load gate, the compaction number, the
hooks' modules, the project's personas (`project`, never fails the machine check), the board's
notifications (`optional`, with `serve push-test`). New rows: the app's and the plugin's
versions; the `lem` first on the path; `hooks/run` finds `lem-hook`; the door's state and fix;
the "read outside the working directories" question and its allow rule. Step `settings`.

## E. Settings keys (`docs/settings.md`)

All kept, in the same files and places (step `settings`): `paths.plans`, `paths.plan_file`,
`paths.rulings`; `branch.base`, `branch.land`, `branch.history`, `branch.protected`;
`checks.commands`, `checks.serial`, `checks.setup`; `flow.topics`; `seats.reviewer`,
`seats.planner`, `seats.merger`, `seats.session`, `seats.experts`, `seats.fallback` (team, local,
home; per key, nearest wins; `default` removes); `naps.on` (local: only `false`);
`state.keep_days` (team, local); `jev.findings`; `tracker.kind`; home: `ask.style`, `ask.size`,
`ask.review`, `ask.browser`, `ask.status`; machine: `load.start`, `serve.port`,
`serve.tailscale`, `serve.tailscale_port`, `peers.HOST`, `handoff.tokens`,
`corrections.collect`. `settings show` names the source of every effective value.
