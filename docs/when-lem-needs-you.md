# When Lem needs you

After this page, you know when Lem stops for you, how to see what waits, and how to let a task go
on without you.

## Three points

1. **A full change**: you answer the interview, and say yes to the acceptance criteria.
2. **A decision in doubt** that the personas did not settle: you pick an option on a card.
3. **The pull request**: you merge it.

A small change needs you only at its pull request. Lem takes every other decision itself, and the
pull request lists each one with its reason, so that you can reverse it.

## What waits for you

Type `/lem` with nothing after it. Lem asks GitHub what merged, opens the board, and gives one
list, always in this order:

1. the choices of a task, each with the minutes that are left;
2. the acceptance criteria that wait for your yes;
3. the tasks that wait for a step of yours, or for one more fact;
4. the open pull requests, each green or with its reasons;
5. the plans that `/lem night` wrote, each for one backlog item;
6. the proposals of a retro, which finds a correction that you gave two times.

Say "open them" for the night plans and the retro proposals. One page shows them, and you answer
each with approve, reject or later.

## The board

The board puts each task in a lane by who acts next: you, an agent, the checks, or nobody.
`/lem status <task>` opens the board of one task, with its criteria and their tests, its checks,
its review, and where the time went.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="../assets/screens/task-dark.png">
    <img src="../assets/screens/task-light.png" alt="The board of one task: its phases, where the time went, its acceptance criteria, its checks and its review" width="900">
  </picture>
</p>

*The board of one task. The picture shows demo data.*

A task that is "Queued" waits for a free place, or for a task whose result it needs. "Blocked"
means that an agent stopped at a problem that it could not solve. "Landed", "Answered" and
"Dropped" tasks are done: new work on one of them is a new request.

The second tab shows the backlog. "Start a task" on an item opens a task for it.

## A decision in doubt

A decision is in doubt when it changes a criterion or a direction, or when each option costs a
person something. It climbs a ladder, one level at a time, until a level settles it:

1. **The question gate** settles it with a ruling of yours in `docs/rulings/` or `AGENTS.md`, a
   test or a rule. It also settles a decision whose wrong pick is cheap to undo.
2. **The personas** vote.
3. **Two agents** argue for and against the option with the most votes.
4. **Two experts** answer: Fable, and GPT-6 Astra through Codex.

A decision that the gate or the personas settled comes to you as one line, and nothing waits. Any
other decision comes as a card, with one example that goes wrong and the answer of each level. The
card waits 15 minutes (`flow.decision_wait`) while the other work goes on. Then the ladder's pick
is taken, and the pull request is not green.

## Go alone

Type "go alone" for one task, or "go alone for all" for every open task. Then nothing waits for
you:

- each choice that waits is taken at once;
- an interview goes on: Lem takes its own guess for each question, and writes it down;
- the personas read the criteria, and Lem approves them without you.

The pull request is not green for each thing of yours that Lem decided. Type "I am back" to take
the tasks back. For each task, Lem tells you how many decisions it took, and if it approved the
criteria. Nothing is undone.

> [!IMPORTANT]
> After "go alone", the merge and a step that nobody can undo still wait for you. Such a step
> destroys data outside the worktree, or spends money, or sends something to a person. It can also
> write to an outside system beyond what the settings allow. Only the part of the plan that needs
> it waits.
