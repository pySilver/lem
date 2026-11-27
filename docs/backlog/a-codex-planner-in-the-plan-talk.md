---
worth: later
where: src/lem/settings/seats.py:RULES
added: 2026-11-27
---
# A Codex planner in the plan talk

`seats.planner` takes only `claude`. A team that writes `planner = "codex/gpt-6.2-sol:high"` in
`.lem/settings.toml` gets a refusal: "the harness was checked in Claude Code only". The rule is in
two places, `RULES` of `src/lem/settings/seats.py` and `ROLES` of
`src/lem/app/sessions/seating.py`, and `skills/lem/harness/claude-code/plan-talk.md` opens the pair
with a `claude` line only. A Codex fallback cannot stand in for a failed planner either: the task
blocks (`test_a_codex_fallback_can_merge_and_cannot_plan`).

The owner asked on 2026-11-27 how much a Codex planner costs, and asked for this item after the
experts answered.

The misreading this entry exists to stop: a Codex planner does not need the whole Codex port. The
defender never waits on a background command (`prompts/defender.md`, `stages/talk.md` and
`stages/ladder.md` name no `run-in-background`), never asks the owner (`defender.md`, step 5), and
stops when the breaker trips ("As a defender: stop", `stages/breaker.md`). The lead keeps the long
wait and the owner's question. The reviewer's reply reaches the defender as a prompt through the
mailbox, which a Codex pane already did in two plan talks (`second-opinion.md`, 2026-11-22). The
other misreading: the seat lines are not the whole job, since `AGENTS.md` allows a harness file
"only for an agent the contract was checked in".

The work:

1. `codex` beside `claude` for the planner in `RULES` and `ROLES`, with their tests, the fallback
   test above among them, and `docs/settings.md`, `[seats]`.
2. A `codex` line in `plan-talk.md`, step 1, with the seat's model and effort, by the agent of the
   seat `lem seat show SLUG planner` prints.
3. `skills/lem/harness/codex.md`, which answers the rows a defender uses (`load-skill`,
   `second-opinion`, `mark-waiting`, `fan-out`, `ask-experts`) and says each other row is absent.
   `harness/README.md` allows a file that says so.
4. A Codex way for the readers of the ladder. `lem-gate` and `lem-panel` start Claude Code
   subagents (`subagent_type`), and `ask-experts` starts a `claude` expert with the `Agent` tool.
   From Codex each reader is a process of its own CLI, waited for inside the turn.
5. A permission profile for the defender, the one part that can fail. The defender edits and
   commits the plan in a worktree whose git folder is outside it, runs `lem`, which writes
   `.lem/state/` of the main checkout, reaches agterm's socket, and starts agents that need the
   network. The reviewer's inline profile `permissions.lem_review` reads only and writes one file,
   so it is too narrow. A wider profile or full access is the owner's call.
6. One plan talk with a Codex defender on a scratch repository, before the file is committed.

A pair of one family argues less. With Codex on the machine, `/lem init` writes the reviewer
`codex/gpt-6.2-sol:high`, so a Codex planner is worth having only with a `claude` reviewer.

Options:

- (a) Nothing; the planner stays `claude`. Cost: none.
- (b) An opt-in Codex planner, by the six steps above; Lem's default stays `claude/opus:high`. A
  talk opens only for a careful plan or one of more than three parts, so a small task sees no
  change. Cost: two seat rules and their tests, one launch line, a harness file of five rows, a
  Codex paragraph in three skills, and one trial talk.
- (c) The planner as the first part of the whole Codex harness, with `seats.session` (option (c)
  of `a-seat-for-each-phase-of-a-task-s-session.md`). Cost: large. The transcript readers alone
  are 1,127 lines (`src/lem/adapters/claude_*.py`, `harness_claude.py` and the port, `wc -l`,
  2026-11-27).

Recommendation: (b). The unknown that settles the `later` is the owner's ruling "Claude Code and
agterm first, and Codex for reviews … the harness file for Codex comes after Claude Code works"
(2026-11-14, 2026-11-20): take (b) on the owner's word that Claude Code works. Fable recommended
(b) and advised against (c). Astra rated the planner medium and the full port large, with no
recommendation.

Surfaced in a maintaining session on 2026-11-27, with Lem's experts:
`.lem/state/experts/2026-11-27-223934-how-hard-is-it-really-to/`, which the state folder keeps for
30 days. Fable's answer is recorded there. Astra's two answers, `astra.first.md` and `astra.md`, are
not, since `lem experts record` refused a `why:` on a line of its own. Neither expert ran a Codex
session: the sizes are their judgment, and nobody tested them.
