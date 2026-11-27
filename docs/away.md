# While you are away

## Away

Type `/lem im-away`, or say "I'm away". It holds in every repository on this computer, until you
type `/lem im-back`. Lem never guesses whether you are there: only these two commands change it.

While you are away:

- an interview goes on without a wait. Lem takes its own guess for each question and writes it
  down;
- the ladder settles each criterion that a persona doubted, and Lem approves the criteria for you;
- a new request asks you nothing, and takes the safer read.

The pull request of such a task is not green. A build, a breaker and the merge agent work as when
you are there. A task of `/lem night` always runs without you, to its pull request.

## Answer from the Inbox

The [Plannotator Inbox](https://plannotator.ai/inbox/) is optional. If it runs on this computer,
Lem sends what waits for you to it while you are away. Each task has a thread there with its name.
A question there has the same answers as the card, the question page, in the task's session. On your phone, the page
of the task on the [board](phone.md) links to the thread.

See the [Plannotator Inbox reference](https://plannotator.ai/docs/reference/inbox/) for setup.

- The first answer counts: in the Inbox, in the session or on the board. Lem then closes the
  question in the other places.
- A task with no session gets a note with a link to its page on the board, and no question.
- After `/lem im-back`, a question in the Inbox stays open.

When the Inbox does not run, or has no Tailscale address, Lem sends nothing there. The page of the
task on your phone then says why it has no link.

A breaker and a merge also take an answer in the Inbox. Your answer approves the commit that
the question names. [The merge rules](merge.md#merge-it) say when that approval can carry.

## The night and the retro

`/lem night` takes up to four items of `docs/backlog/`, or N with `/lem night N`, the smallest
first. It builds each item without you, one after another, to its pull request. Lem approves the
criteria for you, so each of these pull requests is not green. A night opens nothing while two or
more pull requests of earlier nights wait for your merge. It leaves out an item that can affect
what must never go wrong.

`/lem retro` reads the tasks since the last retro, and your corrections. It changes no file. It
writes each thing that it finds as a **proposal**: a change that it suggests, such as a lesson, a
ruling or a topic. A reviewer agent then reads each proposal, and each proposal that passes waits
as an item of the board's [**Backlog**](board.md#the-reviewers-items). When your `AGENTS.md`
asks for it, a night also writes proposals.

Both run when you type them. [cronn](https://cronn.umputun.dev) can also start them on a schedule:
the night at night, and the retro each morning. `/lem init` adds such a job only on your yes.
