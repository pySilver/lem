---
name: lem-gate
description: "Lem's question gate: the first level of the ladder of a decision in doubt. Lem's stages load it; it is no call of the owner's."
disable-model-invocation: true
---

# The question gate

The first level of a lead's ladder (`stages/ladder.md` in the `lem` skill): before the personas,
the dialectic and the experts spend anything on a decision, a judge looks whether it needs them
at all. The owner kept it as a hidden part that decides: "Sounds useful and it should stay as
hidden feature. Decisions taken that way lands in `decisions.md` artifact at PR time"
(2026-11-18).

## Steps

1. **Write the question down**, in a file of the task directory: the decision in one sentence,
   the options, the context an outsider needs, and where it came from (the plan, the task). No
   pick of the lead's: the judge reads the question as it stands.
2. **The judge**: a fresh Opus subagent (`subagent_type: "general-purpose"`, `model: "opus"`),
   read-only, with the prompt in
   `references/judge.md`. It returns one verdict with its cite:
   - **decided**: a recorded ruling answers it: the file, the heading and the sentence.
   - **checkable**: a test or an existing rule answers it: which, and what it shows. The lead
     runs that check and takes the option it shows.
   - **cheap**: a wrong pick can be reversed later at little cost, and nobody would notice it in
     the meantime: why. The lead's pick is taken.
   - **held**: only the owner, or the next levels of the ladder, can answer it.

   When the judge finds the question already framed somewhere (a backlog item with its options
   and a recommendation), the options start from that framing, with every option it lists: on a
   2026-11-07 test the judge found a draft that had dropped one of the item's options.
3. **The verdict.** decided, checkable or cheap settle the decision: `lem decisions log SLUG --by
   gate --what "THE QUESTION" --chose "THE OPTION TAKEN" --why "CITE"`. held goes on to the personas.

## What the gate does not do

It never answers intent or taste for the owner, and never settles a question it judged held. It
does not run on a question of an interview (an onboarding, a `lem-interview-me` round): such a
question asks what the owner wants, so no ruling, check or cheap pick can answer it. On the first
onboarding through Lem (2026-11-15) five interview questions went through the gate, and 11m 54s
passed between the owner's first answer and the second question (that session's status line, as
another session read it). It does not argue a ruling: a recorded ruling is reopened only by the
owner.
