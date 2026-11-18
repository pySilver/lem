# A decision in doubt: the ladder

Read by a lead or a plan talk's defender at a decision in doubt, and by Lem at a criterion the
personas flagged while the task runs without the owner (`stages/mode.md`). A decision is
in doubt when it changes a criterion or a direction, or when its options each cost a person
something and nothing you read answers it. Every other decision is yours: decide it from the
code, the settings and the rulings, log it with `--by lead` and `--undo`, and go on.

A decision in doubt climbs, one level at a time, and a level runs only when the one before left
it open. A count decides each level, not a model, and you apply it, since you read the code: the
owner's "Next level follows if no clear consensus reached" (2026-11-18). Each log below is

```bash
lem decisions --repo WORKTREE log SLUG --what TEXT --chose OPTION --why TEXT --by LEVEL --option TEXT --option TEXT [--level NAME=ANSWER ...]
```

with each option, and a `--level` for each level that ran with what it answered, so that the
record shows later which level changes picks and which never does.

0. **The gate.** The `lem-gate` skill (`load-skill`) asks its judge. It settles the decision when
   a ruling of the owner's answers it (a file of `docs/rulings`, or a line of the project's agent
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
   for one option: settled, `--by experts`.
5. **Else your pick stands**: `--by lead --unsettled`.

## The end

- **Without the owner** (`mode` is `alone` in `lem project --repo WORKTREE tasks`): the log is the
  end, and the work goes on. The pull request is not green for a decision of the dialectic, of
  the experts or one that no level settled, and stays green for one of the gate or the personas.
- **With the owner**: a decision the gate or the personas settled is the log, and Lem tells him
  in one line. One that went past the personas is no log: it is his card, with the ladder's pick
  as `--recommended` and each level's answer in `--said`, as `stages/build.md`, "A choice in the
  build", step 2, asks it. Its wait and its end are steps 3 and 4 there.
- **A step that a later "no" cannot reverse** is a card in both modes, with `--irreversible`.
- **All opinions**, the owner's words on a card: run each level that did not run, and give him
  the new answers through Lem. The experts on that choice are `lem experts brief SLUG N` and
  `record SLUG N`, which keep their advice on his card.
- **A night plan** (`night: yes` in the brief) asks no card: the decision goes where
  `stages/plan.md`, step 5, says.

A choice of the plan talk that it left open, and a design choice of it, climb the same way.
