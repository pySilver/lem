# When Lem needs you

## Three points

1. **The standard track**: you answer the interview, and say yes to the acceptance criteria.
2. **A decision in doubt** that the personas did not settle: you pick an option on a card.
3. **The pull request**: you merge it.

On the fast track, Lem needs you only at the pull request. Lem takes every other decision itself,
and the pull request lists each one with its reason.

You answer the first two points in a companion: a session under Lem's session for one thing that
waits for you, such as `gift-note-in-export · interview` in the sidebar. It closes after your
answer. Lem's own session takes your next request at once.

## What waits for you

Type `/lem`. Lem opens the board, and gives one list in this order. While you are away, its first
line says so.

1. the choices of a task;
2. the acceptance criteria that wait for your yes;
3. the tasks that wait for a step of yours, or for one more fact;
4. the open pull requests, each green or with its reasons;
5. the changes that the morning retro proposes.

`/lem` also opens a companion for each choice and for the criteria in the list. Say "open them" to
approve, reject or delay the retro's changes.

## The board

The board of all tasks has three tabs: **Tasks**, in lanes by who acts next; **Waits for you**, a
row for each thing that you do, which opens its companion; and **Backlog**, with "Start a task" on
each item.
`/lem status <task>` opens a task's board: what it builds, then green or not green.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="../assets/screens/task-dark.png">
    <img src="../assets/screens/task-light.png" alt="The board of one task" width="900">
  </picture>
</p>

*The board of one task. The picture shows example tasks.*

In agterm, a chord lists the tasks, with what waits for you first. Pick one, and its board opens.
`/lem init` gives you the keymap line.

## At night

A scheduled job runs `/lem night`. Lem takes the smallest backlog items, four at most, and runs
them one after the other, each without you to its pull request. In the morning, `/lem` shows them
with the report of the night. On the standard track, such a pull request is not green, because you
did not approve its criteria. Lem leaves out an item near what must never go wrong. With two night pull requests still open, the night opens nothing.

## A decision in doubt

A decision is in doubt when it changes a criterion or a direction, or when each option costs a
person something. It climbs a ladder, level by level, until one settles it:

1. **The question gate** settles it with a ruling of yours, a test or a rule. A ruling is a
   decision of yours that holds for later tasks, in the rulings folder of
   [your settings](settings.md#paths). The gate also settles a decision whose wrong pick is cheap
   to undo.
2. **The personas** vote: agents answer as each person that the decision affects.
3. **Two agents** argue for and against the option with the most votes.
4. **Two experts** answer: the newest Fable of Anthropic, and the newest Astra of OpenAI through
   Codex. Without Codex, one expert answers alone.

When the gate or the personas settle a decision, Lem tells you in one line, and nothing waits. Any
other decision comes to you as a card in its companion, with one example that goes wrong and the
answer of each level. The card waits for your answer with no time limit, and the other work goes on.

## Away

Type `/lem im-away`, or say "I'm away". Only your word changes it. While you
are away, no companion opens, and every task goes on without you:

- each choice that waits is taken at once, with the ladder's pick;
- an interview goes on: Lem takes its own guess for each question, and writes it down;
- the personas read the criteria, the ladder settles each criterion that a persona doubted, and
  Lem approves the criteria without you.

The pull request is then not green, and it lists each decision that Lem took for you. Type
`/lem im-back` when you are back. For each task, Lem tells you how many decisions it took, and
whether it approved the criteria.

> [!IMPORTANT]
> Two things always wait for you, also while you are away:
>
> - **The merge.** Lem merges nothing for you while you are away.
> - **A step that nobody can undo**, such as a migration that deletes shared data. Lem builds the
>   rest of the task, and asks you on a card. While you are away, its companion opens at
>   `/lem im-back`.
