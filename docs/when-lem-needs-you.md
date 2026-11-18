# When Lem needs you

## Three points

1. **The standard track**: you answer the interview, and say yes to the acceptance criteria.
2. **A decision in doubt** that the personas did not settle: you pick an option on a card.
3. **The pull request**: you merge it.

On the fast track, one builder makes one rule, and Lem needs you only at its pull request. Lem takes every other decision itself, and the
pull request lists each one with its reason, so that you can reverse it.

## What waits for you

Type `/lem` with nothing after it. Lem asks GitHub what merged, opens the board, and gives one
list, always in this order. When you are away, its first line says so, and since when.

1. the choices of a task;
2. the acceptance criteria that wait for your yes;
3. the tasks that wait for a step of yours, or for one more fact;
4. the open pull requests, each green or with its reasons;
5. the changes that the morning retro proposes, for each correction that you gave two times or more.

Say "open them" to answer the retro's changes on one page: approve, reject or later.

## The board

The board puts each task in a lane by who acts next: you, an agent, the checks, or nobody.
`/lem status <task>` opens the board of one task, with its criteria and their tests, its checks,
its review, and where the time went.

In agterm, a chord lists the tasks, with what waits for you first. Pick one, and its board opens.
`/lem init` gives you the keymap line.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="../assets/screens/task-dark.png">
    <img src="../assets/screens/task-light.png" alt="The board of one task, with its phases, criteria, checks and review" width="900">
  </picture>
</p>

*The board of one task. The picture shows demo data.*

A "Queued" task waits for a free place, or for the result of another task. A "Blocked" task
stopped at a problem that its agent could not solve. "Landed", "Answered" and "Dropped" tasks
are done, and new work on one is a new request.

The second tab shows the backlog. "Start a task" on an item opens a task for it.

## At night

A scheduled job runs `/lem night`. Lem takes the smallest backlog items, four at most, and runs
them one after the other, each without you to its pull request. `/lem night 2` takes two. In the morning, `/lem` shows these pull
requests and the report of the night. A task of the night on the standard track is not green, because you did
not approve its criteria. Lem leaves out an item near what must never go wrong. When two pull
requests of earlier nights are still open, the night opens nothing.

## A decision in doubt

A decision is in doubt when it changes a criterion or a direction, or when each option costs a
person something. It climbs a ladder, one level at a time, until a level settles it:

1. **The question gate** settles it with a ruling of yours in `docs/rulings/` or `AGENTS.md`, a
   test or a rule. It also settles a decision whose wrong pick is cheap to undo.
2. **The personas** vote: agents answer as each person that the decision affects.
3. **Two agents** argue for and against the option with the most votes.
4. **Two experts** answer: Fable, and GPT-6 Astra through Codex.

When the gate or the personas settle a decision, Lem tells you in one line, and nothing waits. Any
other decision comes to you as a card, with one example that goes wrong and the answer of each
level. The card waits for your answer with no time limit, and the other work goes on.

## Away

Type `/lem im-away`, or say "I'm away". Until you say so, Lem takes it that you are there. While you
are away, every task goes on without you:

- each choice that waits is taken at once, with the ladder's pick;
- an interview goes on: Lem takes its own guess for each question, and writes it down;
- the personas read the criteria. Two agents, and the experts when needed, settle each criterion
  that a persona doubted. Then Lem approves the criteria without you.

The pull request is then not green, and it lists each decision that Lem took for you. Type
`/lem im-back` when you are back. For each task, Lem tells you how many decisions it took, and
whether it approved the criteria.

> [!IMPORTANT]
> While you are away, the merge still waits for you, and so does a step that nobody can undo. Such a
> step:
>
> - destroys or rewrites data outside the worktree;
> - writes to an outside system beyond what the settings allow;
> - sends something to a person;
> - spends money.
>
> Only the part of the plan that needs the step waits.
