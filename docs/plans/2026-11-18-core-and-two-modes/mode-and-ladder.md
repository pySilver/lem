# The mode and the ladder: the design to build

The maintaining session's decision of 2026-11-18, after a second opinion by Fable on
`first-design.md` beside this file (the "full design" below; `D:N` is a line of it, and its cites
of the code are of commit cfc4831). Fable's verdict:
"build the smaller design. The mode half is close to the smallest and is sound after two repairs.
The ladder half is a state machine with parsers that no act of Lem's needs, and three of its rules
fail toward settled." This file wins wherever it and the full design disagree. The full design
stays the source for: where each text changes (its T5 list, D:721-734), the file and line cites
of today's code, the mode's step-by-step (D:98-200), and the old forms that must still read.

## The owner's requirement (his words are in docs/rulings/, "His interview of 2026-11-17 and 2026-11-18")

The switch at any stage; decisions taken without him while he is away, with the panel, the
dialectic and the experts used "in doubt"; each such decision with its reason in a file at the end;
a true "green / not green"; a red flag for what waits for him. "A count decides, not a model" came
from his doubt that the Jev model can judge without the code: the lead reads the code, so the
stop rule is a count the lead applies, and a script checks only what is cheap to check.

## Commands and keys

- `lem project mode SLUG|--all alone|with-owner --by owner|lem --words TEXT` (as D:101-113). The
  event is `task.mode`. `lem project tasks` gives `mode` and `mode_since`. A task with no such
  event reads as `with-owner`. `lem project alone` (the lock for commands that need the machine)
  keeps its name; texts for people say "without the owner" for the mode, never "alone" for both.
- `lem criteria approve SLUG --file FILE --alone` (as D:184-195): the approval's `by` is `alone`.
- `lem decisions log`: `--by` gains `gate`, `dialectic`, `experts`; `--by personas` stays. New
  optional, repeatable flags: `--vote NAME=OPTION`, `--option TEXT`, `--level NAME=ANSWER`; and
  `--unsettled` with `--by lead`. With `--by personas` the script refuses fewer than two votes
  and a vote that is not `--chose`. Nothing else is parsed.
- `lem decisions ask`: unchanged. `--recommended` is the ladder's result, `--said` holds each
  level's answer.
- `lem decisions timeout`: allowed before the deadline when the task's mode is `alone`, recorded
  with `early: true`. `lem decisions wait` returns when the mode becomes `alone`.
- `settle` goes, with no stub. `advise` stays as it is (for "all opinions" on a card, and for the
  records of open tasks).
- The experts before a card use what exists: `lem experts brief --question ... --option ...`, then
  `record --folder`, which prints whether they agree. `experts.py` does not change.
- No new kind of line in `decisions.jsonl`. New keys on a `taken` line: `votes`, `options`,
  `levels`, `unsettled`, `early`.
- NOT built: `decisions gate|personas|dialectic|experts|all|levels`, `ladder.py`, the answer
  forms and the cite check, the `sure:` line, `--interview`, `--intent`, `rule: true` and the
  ruling commit, `CARD_FROM`, the `choices/` files, any stub, the board's view of a climbing
  choice.

## `land.py`

- Not green for a `taken` line whose `by` is `dialectic` or `experts`, or that has `unsettled`.
  (The owner's ruling of 2026-11-16: a choice the experts decided is not green. The dialectic is
  two subagents of the lead, the least independent look, so the same holds.)
- Not green for criteria approved `by: alone`; the two refusals of `propose` (today near lines
  2423 and 2432) take such an approval.
- A task that ran without the owner and in which nothing of his was decided without him is green,
  and the pull request's first lines say which part ran without him. (This corrects the plan's
  sentence "a pull request of a task that ran alone is not green"; the session tells the owner.)
- `may_merge` refuses an agent's merge while the task's mode is `alone`, whatever `branch.land`
  says: the merge waits for him. With the owner, `branch.land` rules as today.
- The words of the green line must stay true: not "nothing that was the owner's was decided
  without the owner" when the gate or the personas settled one (D:243 has the true wording).
- A persona stop is the one stop that is green: its line in the pull request says how many
  personas voted and from how many model families.
- `gate-log.py` and the gate's shadow mode go.

## The rules, in one new stage text, `stages/ladder.md`, read only when a decision is in doubt

Which decisions enter: today's rule (a choice that changes a criterion, or whose options each
cost a person something). Every other choice is the lead's own, with a log line.

0. The gate: a ruling of the owner's answers it (cite the file in `docs/rulings` or the line of
   the project's agent document), a test or a rule answers it, or it is cheap and can be
   reversed: `log --by gate --why CITE`.
1. The lead writes the options, its pick and the facts.
2. The personas: settled with two or more votes, all for the lead's pick. An answer with no clear
   pick, or one that cannot be read, blocks: it is never dropped.
3. The dialectic, when the personas split: one subagent argues for the option with the most
   votes, one against. The one against ends with "no break" or names breaks with file and line.
   The lead opens each cite. No confirmed break: clear, taken. A confirmed break is a fact, and it
   goes to the experts with the question.
4. The experts: settled when both pick one option.
5. Else the lead's pick stands, `--unsettled`.
6. At the end: without the owner, `log`. With him, a decision that went past the personas is an
   `ask` (the card, with each level's answer); one that the gate or the personas settled is a
   `log`, no card.

"All opinions" (his words on a card): the levels that did not run yet, run; today's `advise`
serves the experts.

With the owner, Lem says each decision taken in a task since its last turn once, in one line, in
the conversation, and waits for nothing: his "Sometimes I would love to know the decisions taken
before implementation". (The session's decision, open to him: no card for a settled decision,
because a page that demands him for a settled thing is extra attention.)

Irreversible steps: as today, in both modes; they wait for him.

## What this gives up against the full design (accepted)

Answers parsed by a script and the cite check; a choice shown on the board while it climbs; the
levels of a ladder kept when a lead dies in its middle (they run again); the `levels` command; one
outcome under a lock for a switch in the middle of a ladder (a narrow race that ends "not green"
and told).

## What would bring a check back

A real run in which a lead, with the rules in text only, records a level wrongly in a way that
`--vote` does not catch. Then that one count moves into the script, and only that one.

## Size (Fable's unmeasured estimate)

About zero net script lines: about +165 added, about -210 removed (164 of `gate-log.py`, about 45
of `settle`).

## Must not break

A lead that is in flight with the stage text of before: every command it knows (`log --by
personas`, `ask`, `lem experts brief`, `timeout`, `advise`) works as before. A record of the form
before reads. Tests for each.
