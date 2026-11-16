---
name: lem-ask-expert
description: "Give a choice of a build that waits for the owner to two experts of two model families at once, in the background and read-only, and write each one's advice into the choice's record. Their two answers go on the owner's card while he decides; when he does not answer in time, their shared pick is taken, and at once when he is away. Lem's stages call it right after `decisions.py ask`; the owner calls it as `/lem ask-expert SLUG N`. Use when a choice of a Lem task waits for the owner, or when the user says \"ask expert\", \"ask the experts\", \"/lem ask-expert\"."
argument-hint: 'SLUG N [--file PATH ...]'
---

# Ask the experts

The way out when the owner is not there to answer a choice and a decision has to be taken. His
words: "a skill "ask expert" which calls Fable subagent and GPT-6 Astra experts in background.
This is good solution / way out in a situation where human isn't here to answer the question and
we need to take a decision" (2026-11-16).

Two experts answer one choice from one brief, each on its own, at the same moment: `fable` and
`astra`, two agents of two model families, so that their agreement is worth more than two agents
of one family would give. They read; they change nothing. Their advice decides nothing by
itself. The record does that, by the rules of `decisions.py`:

- while the owner can answer, both answers are on his card, beside the personas';
- when his wait ends with no answer, `decisions.py timeout` takes the option both picked, and the
  recommended option when they split, when one found none fits, or when one did not answer in
  time;
- when he is away, `decisions.py settle SLUG N --away` takes their shared pick at once. Only Lem
  knows that he is away (`stages/new.md`, "When a choice waits for the owner");
- a choice the experts decided is never green: the pull request has a line with their pick and
  both reasons, and he reads it before he merges;
- a step that a later "no" cannot reverse (`--irreversible`) takes advice for his card, and is
  never decided by the experts: it waits for his word.

`SKILL_DIR` is this skill's directory. `WORKTREE` is the task's worktree, or any directory of the
checkout.

## When it runs

- **Right after `decisions.py ask`**, by whoever asked the choice: a task's lead, or Lem. The wait
  started with the ask, and the experts take part of it, so start them before anything else.
- **By the owner**, as `/lem ask-expert SLUG N`: for a choice that waits and has no advice, or the
  advice of one expert only. A choice with both experts' advice is refused.

## Steps

1. **The brief.**

   ```bash
   python3 SKILL_DIR/scripts/experts.py --repo WORKTREE brief SLUG N [--file PATH ...]
   ```

   `--file` names a file the choice is about, relative to the worktree, once for each. The script
   writes `experts/choice-N.brief.md` in the task's directory: the choice, its options word for
   word, the recommended one and why, what the personas said, the task's stories and its plan,
   the files, and the form of an answer. It prints the brief's path, each expert's answer file
   and the experts still to ask (`ask`). It refuses a choice that does not wait.

2. **Start the experts named in `ask` at once, in the background**, through `ask-experts` in the
   harness file of your agent (`harness/` in the `lem` skill's directory). Each gets the brief's
   path and nothing else, works in the task's worktree read-only, and its last message is its
   answer. Do not wait for them: go on with the work that does not depend on the choice. You are
   told when each ends; never poll.

3. **As each one ends**, its answer file holds its last message word for word (the harness file
   says who writes it), and:

   ```bash
   python3 SKILL_DIR/scripts/experts.py --repo WORKTREE record SLUG N --expert fable|astra
   ```

   It writes the advice into the choice's record with `decisions.py advise`, under the task's
   lock. It refuses an answer that is not in the brief's form, and a pick that is no option of
   the choice. Then ask that expert once more with the same brief. When the second answer is
   refused too, or the expert did not start, record nothing for it and say so in one line: with
   one expert's advice the end of the wait takes the recommended option. Advice after the wait
   ended is refused too, and changes nothing.

4. **Tell who reads it.** The defender of a plan talk, in its companion session, sends
   `lem: SLUG choice N advised` through `tell-coordinator` when both answers are in the record;
   a builder that leads has no such line, and Lem finds the advice in `decisions.py pending`. Lem
   then does what `stages/new.md` says. When the owner called this skill, tell him both answers:
   each pick and its reasons, and whether they share one.

`decisions.py list SLUG` and `decisions.py pending SLUG` show the advice under each choice
(`advice`), and `experts_pick` is the option both picked, or null.
