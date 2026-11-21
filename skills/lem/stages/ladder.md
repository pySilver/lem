# A decision in doubt: the ladder

Read by a lead or a plan talk's defender at a decision in doubt, and by a task's session in the
shape at a criterion the personas flagged while the task runs without the owner (`stages/away.md`). A decision is
in doubt when it changes a criterion or a direction, or when its options each cost a person
something and nothing you read answers it. Every other decision is yours: decide it from the
code, the settings and the rulings, log it with `--by lead` and `--undo`, and go on.

A decision in doubt climbs, one level at a time, and a level runs only when the one before left
it open. It always ends in a pick, which is taken at once, with the owner there or away: nothing of
a build waits for him. A count decides each level, not a model, and you apply it, since you read the code: the
owner's "Next level follows if no clear consensus reached" (2026-11-18). Each log below is

```bash
lem decisions --repo WORKTREE log SLUG --what TEXT --chose OPTION --why TEXT --by LEVEL --option TEXT --option TEXT [--level NAME=ANSWER ...] [--case STEPS --case-was reproduced|derived --cause TEXT] [--chart FILE]
```

with each option, and a `--level` for each level that ran with what it answered, so that the
record shows later which level changes picks and which never does.

0. **The gate.** The `lem-gate` skill (`load-skill`) asks its judge. It settles the decision when
   a ruling of the owner's answers it (a file of the rulings folder, `lem project path rulings`, or a line of the project's agent
   document), when a test or a rule answers it, or when a wrong pick is cheap to reverse and
   nobody would notice it meanwhile: `--by gate`, with the cite in `--why`. `held` goes on.
1. **You** write the options, each as what a person would see and what it costs, your pick, and
   the facts it rests on, each with its file and line.
2. **The personas.** The persona panel (`lem-panel`, `load-skill`), "In the ladder", with the
   personas the decision concerns. Each persona's answer in one model family is one vote. Two
   votes or more, all for your pick: settled, `--by personas` with a `--vote "PERSONA,
   FAMILY=OPTION"` for each; the script refuses fewer, or one for another option. An answer with
   no clear pick, or one you cannot read, blocks the stop: ask that persona once more, and when
   it still has none, the level is open. Never drop an answer.
3. **The dialectic**, when the personas split or one blocked: the `lem-dialectic` skill, "In the
   ladder", two read-only agents of yours (`fan-out`), one for the option with the most votes and one
   against it. The one against ends with `no break`, or names each break with its file and line.
   Open each cite yourself. No break you can confirm: settled, `--by dialectic`. A confirmed break
   is a fact, and it goes to the experts with the question.
4. **The experts.** The `lem-ask-expert` skill with the question in words (`lem experts --repo
   WORKTREE brief --question TEXT --context TEXT --option TEXT ...`, with each confirmed break in
   the context), then `record --folder` for each answer, which prints whether they agree. Both
   for one option: settled, `--by experts`. On a machine with one of their agents (no Codex), one
   expert answers alone, and its pick settles: `--by experts`, which the record and the pull
   request name as one expert.
5. **Else your pick stands**: `--by lead --unsettled`.

## The end

- **The log is the end**, and the work goes on. The pull request is not green for a decision of the
  dialectic, of the experts or one that no level settled, and stays green for one of the gate or
  the personas; the owner reads each at the pull request and asks for a fix when it was wrong.
- **The story.** A decision that the dialectic, the experts or no level settled is important, and
  carries its story (`prompts/writing.md`) in `--case`, `--case-was` and `--cause`; the log refuses
  one without. Its chart, when it branches, is a file you write and name with `--chart FILE`. Each
  `--option` is "LABEL: what the person sees after it".
- **The breaker, not a pick**: when the pick is a step that a later "no" cannot reverse, or no
  option keeps the rule of an approved criterion, log nothing and trip the breaker
  (`stages/breaker.md`), with what each level said in its document.

A question the plan talk left open, and a design choice of it, climb the same way.
