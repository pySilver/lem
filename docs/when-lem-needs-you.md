# When Lem needs you

## Three touches

1. **The shape**, on the standard track: you answer the interview, and say yes to the acceptance
   criteria.
2. **A circuit breaker**: a task stops, and leaves a document for you.
3. **A pull request that the merge agent calls you for**: you read its review, and merge.

On the fast track, only the third touch can come. One exception: when another person wrote the
ticket, you say yes to its one acceptance criterion before the build starts. You answer the first
two in the session of the task, or on the [board](board.md#act-from-the-board). The build asks you
nothing.

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

Answer in one of three ways, in the session of the task or with the buttons of its row on the
[board](board.md#act-from-the-board):

- talk about it in the session of the task, and decide. On the board, **Help** sends your note
  to the lead, and the talk starts from it;
- `/lem park <task>`, or **Park**: the worktree, the branch and the files stay;
- `/lem drop <task>`, or **Drop**: the worktree goes, and the files and the commits of the branch
  stay.

While you are away, you can also answer in the [Inbox](#answer-from-the-inbox).

`/lem resume <task>` opens the talk again after a park or a drop. After the days of
[`state.keep_days`](settings.md#state), the events of a dropped task become one summary, only a
small record of its files stays, and Lem cannot resume it. Then type `/lem` and its request to
start a new task.

## A task of an older release

Lem reads the tasks begun on its own release and on the release just before it. A task begun two
releases back or more stops at its first command, and the board shows it blocked. Its message names
the release it began on, and the way on: `/lem drop <task>`, then `/lem resume <task>`. The resume
starts a new request on your release, from the branch and its commits and from the notes of the
task. Its session asks you again for your yes to the acceptance criteria.

## The merge review

A fresh merge agent reads each pull request, writes `merge-review.md`, and merges a green one that
is not careful. It calls you for every other one, and when it finds a problem. With
`branch.land = "owner"`, it calls you for each one. Then "Waits for you" shows one stack for the
task, with "Read the merge review" and "2 things": the review, and the merge of the pull request.
[The pull request](pull-request.md) tells more.

## What waits for you

Type `/lem`. Lem opens the board, and gives one list. Each task that waits for you is one entry,
with the things that you do for it under it. A task has the place of its first thing, in this
order:

1. the breakers, each task that needs a session and has none, and each task whose session
   stopped: "Open a session" starts a fresh agent;
2. the questions of an interview, and the acceptance criteria that wait for your yes;
3. the tasks that wait for a step of yours, or for one more fact;
4. the questions that the session of a task asks you on a card: answer on the card in agterm, or
   on the board;
5. the tasks that wait for a task that you dropped: type "start <task> now" to start the task, or
   `/lem drop <task>` to stop it, in a Lem session of this repository;
6. the tasks that stopped on a problem that they cannot solve alone, and the tasks of an
   [older release](#a-task-of-an-older-release);
7. the plans that wait for you to read them;
8. the merge reviews that call you;
9. the pull requests that wait for your merge, and each merge that GitHub or Lem refused, each
   green or with its reasons.

An interview is on the list only while it asks you a question. While Lem writes the acceptance
criteria, or the personas read them, it is not there. While the session of a task works on your
answer, the task is not on the list either. It comes back when the session stops and waits for you
again. When Lem cannot read the session, the task stays on the list.

The time of a thing starts with the step that started its wait. For example, the acceptance
criteria count from the time that they wait for your yes, not from the start of the interview.

What the night and the retro propose is not on the list. A reviewer agent reads each proposal
first, and only the proposals that pass wait for you, as items of the board's
[**Backlog**](board.md#the-reviewers-items) view. A proposal that it refutes waits for nobody.

The [board](board.md) shows the same list, in the same order, in its view **Waits for you**. A
task with one thing is one row. A task with two or more things is one stack: its title, its first
thing, and the number of its things. Click the stack to open it. Each thing then shows as a row of
its own, with its time and its button. The counts of the board count each task one time. When Lem
cannot read the sessions of agterm, the list says so.

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

- an interview goes on, and is not on the list of what waits for you: Lem takes its own guess
  for each question, and writes it down;
- the ladder settles each criterion that a persona doubted, and Lem approves the criteria for you;
- a new request asks you nothing, and takes the safer read.

The pull request of such a task is not green. A build, a breaker and the merge agent work as when
you are there. A task of `/lem night` always runs without you, to its pull request.

### Answer from the Inbox

While you are away, each thing that waits for you also goes to the
[Plannotator](https://github.com/backnotprop/plannotator) Inbox on this computer, in a thread with
the name of the task. A question there has the same answers as the card in the session of the
task. On your phone, the [page of the task](board.md#the-board-on-your-phone) links to the thread.

- The first answer counts: in the Inbox, in the session or on the board. Lem then closes the
  question in the other places.
- A task with no session gets a note with a link to its page on the board, and no question.
- After `/lem im-back`, a question in the Inbox stays open.

When the Inbox does not run, or has no Tailscale address, Lem sends nothing there.
