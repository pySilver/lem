# When Lem needs you

## Three points

A task usually needs you at three points:

1. **The shape**, on the standard track: an interview if needed, and your yes to the acceptance
   criteria when [the task needs it](flow.md#the-standard-track).
2. **A circuit breaker**: a task stops, and leaves a document for you.
3. **A pull request that the merge agent calls you for**: you read its review, and merge.

You answer the first two in the session of the task, or on the [board](board.md#act-from-the-board).
The build asks you nothing. A task can also need you at other times:

- On the fast track, the one criterion of a ticket that another person wrote waits for your yes.
- A plan of `/lem plan` waits for your read.
- When the session of a task does no work for 55 minutes, the board server opens a fresh session
  one time. When that session also stops, or the server cannot read its work, the task waits for
  you as "stopped". "Open a session" starts a fresh agent.
- A task is blocked when a tool or the computer fails, or when it comes from an
  [older release](update.md#a-task-of-an-older-release).
- A request waits for a task whose result it needs, or that you put before it. When that task is
  dropped, the request waits for you: type `start <task> now` or `/lem drop <task>`.
- GitHub or Lem refuses a merge.

To change the acceptance criteria, tell the session of the task what to change, or answer No with
a note on the board. Lem asks for your yes to the changed criteria, each beside its old text. The
pull request says that they changed after the personas' read. When your note changes no criterion, Lem follows the instruction or answers your question. Then
it asks for your yes to the same criteria.

## A decision in doubt

The build takes each decision in doubt up a ladder, until one level settles it:

1. **The question gate**: a test, a rule or one of your [rulings](settings.md#paths) settles it.
2. **The personas** vote: agents answer as each person that the decision affects.
3. **The dialectic**: two agents argue for and against the option with the most votes.
4. **Two experts** answer: the latest Anthropic Fable, and the latest OpenAI Astra through Codex.
   Without Codex, one expert answers alone.

The task takes the pick at once and goes on. A pick past the personas makes the pull request not
green.

## The circuit breaker

The breaker stops one task, and the other tasks go on. It has two causes:

- the next step cannot be undone: it deletes data, writes to another system, sends a message to a
  person, or spends money;
- no option of the ladder keeps a criterion that you approved.

A task that takes longer than expected does not stop. The task writes `breaker.md`: the case that
broke, its root cause, the options, a recommendation and the assumptions. The board shows it first,
and sends a notification to [your phone](phone.md).

Answer in the session of the task, or with the buttons of its row:

- talk about it in the session, and decide. **Help** sends your note to the agent of
  the task, and the talk starts from it;
- `/lem park <task>`, or **Park**: the worktree, the branch and the files stay;
- `/lem drop <task>`, or **Drop**: the worktree goes, and the files and the commits of the branch
  stay.

`/lem resume <task>` opens the talk again after a park or a drop. After
[`state.keep_days`](settings.md#state), Lem cannot resume a dropped task: type `/lem` and its
request to start a new task.

## What waits for you

Type `/lem` for the board and one list. Each task that waits for you is one entry, with its
things under it. A card is a question page that the session of a task shows.

The most urgent thing comes first: breakers and stopped sessions, then questions and other waits,
then plans to read, then merges. In a group, the oldest wait comes first.

A task is on the list only while it waits for you: not while its session works on your answer.

What the [night and the retro](away.md#the-night-and-the-retro) propose is not on the list. Each
proposal that passes a reviewer agent waits in the board's [**Backlog**](board.md#the-reviewers-items).

The board shows the same list in its view **Waits for you**. A task with two or more things is one
stack. Click it, and each thing shows as a row of its own, with its button.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/screens/task-dark.png">
  <img src="assets/screens/task-light.png" alt="A task on the board, with the merge review first on its Overview" width="1440" height="900">
</picture>

*A task on the board, on its Overview. The picture shows demo data.*
