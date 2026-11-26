# While you are away

## Away

Type `/lem im-away`, or say "I'm away". It holds in every repository on this computer, until you
type `/lem im-back`. Lem never guesses whether you are there: only these two commands change it.

While you are away:

- an interview goes on, and is not on the list of what waits for you: Lem takes its own guess
  for each question, and writes it down;
- the ladder settles each criterion that a persona doubted, and Lem approves the criteria for you;
- a new request asks you nothing, and takes the safer read.

The pull request of such a task is not green. A build, a breaker and the merge agent work as when
you are there. A task of `/lem night` always runs without you, to its pull request.

## Answer from the Inbox

While you are away, each thing that waits for you also goes to the
[Plannotator](https://github.com/backnotprop/plannotator) Inbox on this computer. Each task has a
thread there with its name. A question there has the same answers as the card in the session of the
task. On your phone, the page of the task on the [board](phone.md) links to the thread.

- The first answer counts: in the Inbox, in the session or on the board. Lem then closes the
  question in the other places.
- A task with no session gets a note with a link to its page on the board, and no question.
- After `/lem im-back`, a question in the Inbox stays open.

When the Inbox does not run, or has no Tailscale address, Lem sends nothing there. The page of the
task on your phone then says why it has no link.

A breaker and a merge also take an answer in the Inbox. A merge from the Inbox merges
only the commit that the question names ([The merge](merge.md#merge-it)).
