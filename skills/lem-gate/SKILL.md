---
name: lem-gate
description: "Lem's question gate: checks whether a question must reach the owner. Lem's stages load it; the owner calls it as `/lem gate`."
disable-model-invocation: true
---

# The question gate

```text
a question for the user
  -> judge: has the user already ruled?      yes -> decided: quote the ruling
  -> checkable by a probe, a test or a rule?  yes -> sent back: probe it, test it, follow the rule
  -> reversible and cheap?                    yes -> an agent decides, and says so
  -> held, and each option costs something?   yes -> persona panel (panel), which makes the card
  -> Jev: is the card framed for the user?    no  -> back to the card's author
  -> the user answers
  -> Jev: is the answer a durable ruling?     yes -> a ruling file; no -> this task only
```

## Shadow mode

Until the user says the judge may act alone, it is in **shadow mode**: every question still
reaches the user, and the judge's verdict is only logged beside the answer. The point is to measure
the judge before trusting it. The user reads the comparison after about a week of runs and then
decides; `scripts/gate-log.py report` prints it. In shadow mode, never tell the user the judge's
verdict before they answer, or the answer stops being an independent check.

## Steps

### 1. Write the question down

One file, `QUESTION_FILE`: the question in one sentence, the options, the context an outsider
needs, and where it came from (the plan, task and exchange). It goes in the folder
`lem gate-log dir` makes and prints, as `<NNN>-<slug>.md`, and
its card goes beside it. That folder is in Lem's state folder, which git does not show, so a question
leaves no file git sees. Pick an `ID`: the file's stem.

### 2. The judge

A fresh Opus subagent (`subagent_type: "general-purpose"`, `model: "opus"`), read-only, with the
prompt in `references/judge.md`. It returns one verdict with its cite:

- **decided** — a recorded ruling answers it: the file, the heading and the sentence.
- **checkable** — a probe, a test or an existing rule answers it: which, and what it would show.
- **cheap** — it can be reversed later at little cost and no user would notice a wrong pick in the
  meantime: why.
- **held** — only the user can answer it.

When the judge finds the question already framed somewhere (a backlog item with its options and
a recommendation), the card starts from that framing, with every option it lists, instead of from
the draft: on a 2026-11-07 test the judge found a draft that had dropped one of the item's options.

Log it: `lem gate-log ask --id ID --question "<one sentence>"
--verdict <verdict> --cite "<cite>"`. In shadow mode, go on to step 3 whatever the verdict.

Once the user has let the judge act alone (they say so; record it as a ruling): on **decided**,
quote the ruling and go on without asking; on **checkable**, do the check; on **cheap**, decide,
and tell the user in one line with the reason. Only **held** goes on to step 3.

### 3. The card

A question the judge called **held** whose options each cost something goes through the persona
panel (`lem-panel`), which writes the card and runs the framing check. The panel asks the
project's own personas; a project with none has a setup that is not finished, and the panel says
so and stops. That holds for a
technical fork as much as for one users would see: the panel brings the people who run and build
the system to a technical question, and its practice scout checks the facts an option turns on,
so the card's recommendation is not the asking agent's view alone. In shadow mode the verdict only
picks which card is made; the question still reaches the user either way, and the card never shows
the verdict. Any other question still goes out as a card in the panel's format (the question in
user terms, the options, the recommendation and what it costs, the strongest dissent, "wrong if",
the undo cost), and gets the same framing check through `lem-jev`, the command Lem's plugin
puts on PATH, with the spec in `lem-panel`'s `references/messages.md`.

### 4. Ask the user

A project that uses Lem says how in its settings (`tools.ask`, which `lem project show` of the
`lem` skill prints), and that value decides. With `lem-ask` there, or with no such setting: in
agterm with the `lem-ask` skill, otherwise as plain text. Then log the answer:
`lem gate-log answer --id ID --answer "<the user's choice and their words>"`.

### 5. Is the answer a durable ruling?

Ask Jev with the spec in `references/durable.md`. A **durable** answer is a rule for later cases:
it binds work beyond this task. **This task** answers one choice inside one task: a size for this
change, an order of tasks, a one-off scope call.

On **durable**, write it in the project's rulings folder (in mybaze, `docs/rulings/<slug>.md`,
the format its AGENTS.md "Where things live" row names): the ruling in one sentence, the user's
words verbatim, why, how to apply. First check the folder for a ruling it overturns; the new file
names that one in `supersedes:` and the old file is `git rm`'d. Commit it with the work in hand,
tell the user in the same message ("recorded as `docs/rulings/<slug>.md`"), and add `--ruling
<slug>` to a second `lem gate-log answer` line. The user can undo it by saying so; Jev's call is a
sorting aid, and a user's "that was only for this task" wins.

## What the gate does not do

It never answers intent or taste for the user, never hides a question it judged **held**, and in
shadow mode never skips one. It does not run on a question of an interview (an onboarding, a
`lem-interview-me` round): such a question asks what the user wants, so no ruling, probe or cheap
pick can answer it, and its answer goes where the interview's stage puts it, not into a ruling
file. On the first onboarding through Lem (2026-11-15) five interview questions went through
the gate, and 11m 54s passed between the owner's first answer and the second question (that
session's status line, as another session read it). It does not argue a ruling: a recorded ruling is reopened only by the
user.
