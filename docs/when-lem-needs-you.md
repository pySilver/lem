# When Lem needs you

## Three touches

1. **The shape**, on the standard track: you answer the interview, and say yes to the acceptance
   criteria.
2. **A circuit breaker**: a task stops, and leaves a document for you.
3. **A pull request that the merge agent calls you for**: you read its review, and merge.

On the fast track, only the third touch can come. One exception: when another person wrote the
ticket, you say yes to its one acceptance criterion before the build starts. You answer the first
two in the session of the task. The build asks you nothing.

## A decision in doubt

The build takes each decision in doubt up a ladder, until one level settles it:

1. **The question gate**: a test, a rule or one of your [rulings](settings.md#paths) settles it.
2. **The personas** vote: agents answer as each person that the decision affects.
3. **Two agents** argue for and against the option with the most votes.
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
broke, its root cause, the options, a recommendation and the assumptions. The board shows it first
on the task, and sends a notification to [your phone](board.md#the-board-on-your-phone).

Answer in one of three ways:

- talk about it in the session of the task, and decide;
- `/lem park <task>`: the worktree, the branch and the files stay;
- `/lem drop <task>`: the worktree goes, and the files and the commits of the branch stay.

`/lem resume <task>` opens the talk again after a park or a drop.

## The merge review

A fresh merge agent reads each pull request, writes `merge-review.md`, and merges a green one that
is not careful. It calls you for every other one, and when it finds a problem. With
`branch.land = "owner"`, it calls you for each one. Then "Waits for you" shows "Read the merge
review". [The pull request](pull-request.md) tells more.

## What waits for you

Type `/lem`. Lem opens the board, and gives one list in this order:

1. the breakers, and each task that needs a session and has none: "Open a session" starts a
   fresh agent;
2. the acceptance criteria that wait for your yes;
3. the tasks that wait for a step of yours, or for one more fact;
4. the tasks that wait for a task that you dropped: type "start <task> now" to start the task, or
   `/lem drop <task>` to stop it, in a Lem session of this repository;
5. the tasks that stopped on a problem that they cannot solve alone;
6. the plans that wait for you to read them;
7. the merge reviews that call you;
8. the pull requests that wait for your merge, and each merge that GitHub or Lem refused, each
   green or with its reasons;
9. the changes that the morning retro proposes.

The [board](board.md) shows the same rows, in the same order, in its view **Waits for you**. When
Lem cannot read the sessions of agterm, the list says so.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="../assets/screens/task-dark.png">
    <img src="../assets/screens/task-light.png" alt="A task on the board: the merge review that calls you, first on its Overview" width="900">
  </picture>
</p>

*A task on the board, on its Overview. The picture shows example tasks.*

## Away

Type `/lem im-away`, or say "I'm away". It holds in every repository on this computer, until you
type `/lem im-back`. While you are away:

- an interview goes on: Lem takes its own guess for each question, and writes it down;
- the ladder settles each criterion that a persona doubted, and Lem approves the criteria for you;
- a new request asks you nothing, and takes the safer read.

The pull request of such a task is not green. A build, a breaker and the merge stay the same. A
task of `/lem night` always runs without you, to its pull request.
