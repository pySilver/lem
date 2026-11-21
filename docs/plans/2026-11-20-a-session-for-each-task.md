# Lem's flow after the interview of 2026-11-20: shape, build, merge

> **Status: built**, and released as 0.1.0 on 2026-11-21 in `65df09a`, with the fixes after it.
> Later decisions changed parts of it: the board's server runs the merge agent's merge, and the
> agent only writes its review; a task's session opens in the main checkout and reaches its
> worktree by its path; the load gate has one number, with no second one that stops a run; the
> parity tool went with the old board page; and the cheap look of `bin/lem` at the server was
> measured at 0.4 ms (the integration builder's medians of 30 runs). `AGENTS.md` ("His rulings of
> 2026-11-20 and 2026-11-21", "Decisions the maintaining session took") holds each. The shapes of
> tasks 2 to 4 and the plan of task 4 are in the folder of this name; the files they cite
> (`interview-notes.md`, `scout.md`, the research) stay in Lem's untracked state folder.

A draft by the interview's companion, from the owner's answers of 2026-11-20. Each settled point
names where his words are: `interview-notes.md` (N), `directions.md` (D) or `owner-notes-process.md`
(P, his notes by their number). The facts of today's code are in `scout.md`; the sources of the process are in
`research-team-process.md` and `research-parallel-e2e.md`. This file is the task's, not the
repository's: the session that builds makes the plan and the five tasks from it.

## Why

He plans one or two tasks at a time and holds their context in his head; several other tasks build
meanwhile, in several projects. "The problem appears when exeuction wants something from me: change
of decisions, wrap up, merge etc." (N). Each such call reaches him far from the moment he thought
about that task. And on 2026-11-19 a `ready` task waited 7 h 40 min for another session's landings
(`task.md`).

So the line Lem draws is between two phases, not between "here" and "away": in the shape he is the
product owner and fully there; in the build he is not there at all.

## The flow

1. **Shape.** He and one agent, in the task's own session. Short when a ticket or a backlog item is
   complete, wide (dialectic, research, experts, panel) when the shape is open (P1). It ends with
   the acceptance criteria he approved, the directions, and the handoff.
2. **Plan and build, unattended.** The lead plans and builds with fresh builders. A surprise goes
   to the automatic tools first: the personas, the dialectic, the two experts, a root-cause
   analysis. What is "not hard to reverse and isn't considered totally wrong should not interrupt
   work" (P3). The lead takes the pick, records it with its reasoning, and goes on. A small defect
   outside the task is fixed or filed in the backlog, as today.
3. **The hard circuit breaker.** It stops one task; the others go on. Two causes: the next step
   cannot be reversed by a later "no"; or the automatic tools find no option that keeps the outcome
   he approved. It gives him a document, never a bare question: user stories that bring the context
   back, diagrams, the root cause, the choices, a recommendation, the assumptions (P2, P3, P8). He
   helps, parks the task, or drops it. An overrun of time or tokens stops nothing: the review
   document shows the time and the tokens of the task, and the merge agent can call him because of
   them (N, the Inbox answer).
4. **Checks and review**, as today, in parallel for all tasks (see "Landings in parallel").
5. **The merge agent.** A fresh agent on a model the settings name reads the artifacts and the
   code, writes the review document of the task (what was built and why, the results, each decision
   taken without him with its reasoning), and decides: merge now, or call him to read it (P6).
   A careful change always waits for his merge, also when the agent finds it correct: it writes
   the document and calls him (N, the Inbox answer).
6. **After the merge**, the task's session does its own steps (the worktree, the branch, the
   tracker), as `lem land merged` does today.

Every document for him has two forms, markdown for agents and HTML for him, "agdoc does it that
way" (P9).

## The layout

- **No Lem session.** One session for each task, driven by its lead, with companions "permanent or
  temporary" (P, notes on agterm; N, Q11). He talks to a task in its session, and mostly only in
  the shape.
- **A new idea**: `/lem <the idea>` in any session of the workspace, or "+" on the board. A script
  opens the task's session, and the shape starts there.
- **Each task session watches its own pull request** and reacts to its merge.
- **The board is the single entry point**: one for each workspace, an HTML overlay; the state of
  each task, what it is about, its artifacts and plan, a jump to its session, and whether it needs
  him. It compares the task files with agterm's list of sessions and shows a task whose session
  died; one click opens a fresh session from the handoff. His examples are in
  a folder of screenshots on his machine (a column for each state, a "Waiting for you" list, a
  task panel with tabs); that app's merge train is not taken. WebAwesome may build it.
- **The night and the retro** stay cronn jobs that open their own sessions.

What goes with it: the need's companions with `lem companion due` and the copy of the talk, the
`coordinator:` lines and `tell-coordinator`, the plan talk's own companion as a separate session of
Lem's, and from this task's first form the guard of one Lem session, the move, and the take-back of
dead leads (his "yes" to Q1 to Q4 rested on a Lem session and is replaced by Q11).

## The handoff

One `handoff.md` in each task directory, in a fixed form: what is settled, what is open, the next
step, what was tried and failed. The agent that leaves writes it (N, Q10). Three moments:

1. a change of phase (shape to build, build to merge): the next agent is always fresh;
2. a session that grows too large writes it and restarts itself in the same pane, with no question
   (the companion's number: 200,000 tokens; on 2026-11-19 that limit would have saved 84.5M tokens,
   D, the token assessment);
3. his word, such as "hand off", when a session works badly.

A parked task starts again in a new session from `handoff.md` and the circuit breaker's document.

## Landings in parallel

- `lem land start` no longer refuses a second task (`land.py` `start_locked`, `scout.md`); the
  step lock of each task stays.
- **GitHub pull requests only** (D). `branch.propose = "merge"` and the landing with no forge go.
- **Lem is the queue.** GitHub's merge queue is for repositories an organization owns
  (`research-team-process.md`, 3b), and `gh api repos/pySilver/lem` says `owner.type` is `User`.
  So the merge calls go one at a time under a file lock, each after a read of the base. When the
  base tree changed after a task's checks, that task rebases and its checks run again; its review
  stays when its diff is the same (N, the four changes after Codex's check). A pull request he
  merges on GitHub himself keeps his ruling: repaired only on a conflict.
- **The load gate.** A long process (the checks, a build, a test run) starts only below a load
  average, and one that drives the load past a second number is stopped and tried again (P7,
  Umputun's 40 and 80). Two numbers for each machine: the MacBook stays comfortable, the Mac mini
  is used hard. The numbers for his machines are not measured (the trial of 2026-11-20 reached 423
  on 10 cores, D). The same rule is a text for every session, Lem's or not, and the same two
  numbers are what `land.py` reads before it starts the checks, since a script reads no rule. GNU
  make `-l` and Ninja `-l` gate a job's start the same way (`research-parallel-e2e.md`, 7).
- `bash tests/all.sh` leaves `checks.serial` (D). `checks.serial` stays for a project whose
  end-to-end runs are not isolated yet; the recipe for isolating them (one Compose project for each
  worktree, no fixed host port, a database for each run) is the project's work, set up in
  `checks.setup` (`research-parallel-e2e.md`).

## The five tasks, in order (N, Q9)

1. **Landings in parallel and the load gate.** This task, made smaller: the section above without
   "GitHub only". A feature waits for no other task's landing.
2. **Execution asks nothing.** The ladder always decides; the circuit breaker with its document; a
   parked task keeps its context.
3. **The merge agent** with its review document, its seat in the settings, and GitHub only.
4. **A session for each task**, the handoff, and the end of the companions and of Lem's session.
5. **The workspace board.**

## How this work is done

Fail-fast (D): the builder changes the plugin, he tries it in a real task, he gives notes, the
builder corrects. New behavior goes into skill texts, prompts and templates; no new test is written
and no suite is a gate while the shape is open. Integration tests follow when he says the shape is
right. The work is on one long-lived branch in a worktree, which he loads into a trial session with
`claude --plugin-dir <that worktree>`; `main` stays as it is until then (N). One existing check
changes with task 1, or the suite fails: `tests/lem-land-guards.sh` asserts "one branch lands at a
time" (`scout.md`).

## His rulings that this changes

For `AGENTS.md`, each with the new fact, which is his own word of 2026-11-20:

- "One Lem session for each repository" (2026-11-19, "Ok (B)"): no Lem session; N, Q11.
- "A companion opens only when something waits for him" (2026-11-19): the companions of a need go
  with the Lem session; a task's own session takes their place.
- "He says whether he is there": while he is there, "a choice of his waits for his answer with no
  time limit" (2026-11-18): in the build no choice waits for him; N, Q7.
- "A choice they decided: Not green ... he reads it before he merges" (2026-11-16): the merge agent
  decides whether he reads; P6.
- "A project may land with no pull request" (2026-11-16) and "Every way to merge stays"
  (2026-11-18): GitHub pull requests only; D.
- "One task lands at a time" (criterion 6 of `landing-in-the-background`, 2026-11-19): landings in
  parallel; `ask.txt`.
- "A change to a script comes with its test" (`AGENTS.md`, a rule): set aside for this work; D.

## Out of scope

- The iOS app over tailscale (P, "later").
- Codex as a lead or a builder (its own backlog item).
- The rebases of an open pull request after each merge, beyond what "Lem is the queue" says: a talk
  of its own, on his word of 2026-11-20 (`task.md`).
