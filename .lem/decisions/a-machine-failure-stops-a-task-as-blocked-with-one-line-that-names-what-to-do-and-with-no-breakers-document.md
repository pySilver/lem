---
decided: 2026-11-21
area: A decision without him: the ladder, the experts and the breaker
---

# A machine failure stops a task as `blocked`, with one line that names what to do, and with no breaker's document

The owner's ruling [Only a circuit breaker stops a task, with a document](../../docs/rulings/only-a-circuit-breaker-stops-a-task-with-a-document.md)
names two causes, and both are decisions: a next step that a later "no" cannot reverse, and no
option that keeps the rule of an approved criterion. Its document holds "choices,
recommendations and assumptions" (P2), and `lem decisions breaker` refuses one without its parts.

Lem also stops a task with the state `blocked`, and with no document. `SKILL.md` defines it as a
stop on "something it could not settle", and the stages write it in four places:

- a lead whose agent refuses it the start of a builder (`stages/build.md`, "You coordinate"; the
  `spawn-builder` row of `harness/README.md`);
- a builder that ended twice with no state block and no report (`prompts/session.md`, the
  paragraph on a subagent's reply);
- `start` of a landing in a project with no command in `checks.commands`: `land.py` writes
  `blocked` with the line `NO_GATE`, and a later `start` takes the task back once the commands
  are there (`stages/land.md`, step 1);
- a red base: `blocked` with `the base is red` and `after: SLUG` of the task that repairs it, and
  `blocked` again after two builders failed on the same check (`stages/land.md`, step 4).

A real run stopped so too: in lem-scratch on 2026-11-21 a landing session opened in its worktree
found no `lem` command and no builder agent, and wrote `blocked` (`session.py`, its module
docstring).

None of these is a choice between options, so a breaker's document would have nothing to put in
its table. The state's one line names what to do: add the commands, open a session where the
builder can start, wait for the repair. The board's "Waits for you" shows the line, and a push
sends it. The second stop of step 4 sits nearest to a decision, since skipping or changing a
command of the checks is the owner's alone; Lem takes no such step, and the line asks him.

An audit of the rulings against the code on 2026-11-21 raised it. The session reads the ruling's
"only" as about a decision that stops a task, and keeps `blocked` for a failure of the machinery.
It is open to him.

The same audit found that the ruling's form names the state `parked` for a breaker. The breaker
writes `held` with the line `breaker N waits for the owner` (`decisions.py`, `stages/breaker.md`),
as it has since its first commit, and `parked` is the state of his own `/lem park`. The ruling's
file says so under its `## Changed in part`.
