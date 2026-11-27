# How a task goes

The chart of the [Overview](index.md#how-a-task-goes) shows the whole path. This page tells each
step.

## One session at a time

`/lem` and a request opens the task in an agterm session of its own. A task has one session at a
time. On the standard track, Lem opens a new session for each phase: the shape with you, the
build, the landing. The fast track is one session to its merge. Say "hand off" for a fresh session
at any time. Inside a phase, Claude Code compacts the session at 600,000 tokens of context, or at the
number of [`handoff.tokens`](settings.md#configlemmachinetoml).

## The first line

The session of the task first says the type, the track, and what you must do. The session where
you typed the request says it too. The type is a Conventional Commits type such as `feat`, or
`question`, which commits nothing. In doubt, Lem asks one question, with its guess.
`/lem standard-track` and `/lem be-careful` correct the line.

## The fast track

The fast track is for one rule in your words, with no open question and nothing careful: a typo,
a rename, a version bump.

1. Lem writes the rule as one acceptance criterion, and approves it for you. When another person
   wrote the ticket, the criterion waits for your yes, except while you are away or in a night task.
2. One builder makes the change, with a test when the behavior changes.
3. The checks run, an agent that did not build the change reads it, and Lem opens the pull request.

When the request does not fit, the builder stops, and the standard track starts.

## The standard track

1. **Interview, if needed.** You answer one question at a time, each with its guess. If you name a
   library or an approach, the plan uses it.
2. **Acceptance criteria.** Each is a rule in plain words with one real example, and gets a test.
3. **The personas read them**, as each person that the change affects.
4. **Your yes, if needed.** If you are present, an interview, a disputed criterion or a request
   from another person needs your yes. Lem can build your complete request without a wait if the
   personas agree. A task that runs [without you](away.md) goes on without your yes.
5. **The plan.** A short plan goes to `docs/plans/`, and a new builder makes each part. The
   [ladder](when-lem-needs-you.md#a-decision-in-doubt) decides each choice, and asks you nothing.
6. **The polish pass.** A new builder removes leftovers. Outside the task, it fixes a wrong
   comment, docstring or sentence of a document. It files each other defect in `docs/backlog/`
   ([what Lem saw outside the task](pull-request.md#what-lem-saw-outside-the-task)).

A ticket or a backlog item that already says what you want skips the interview. Say "interview
me" to get it.

## A bug or a question

An investigator looks first at a question, and at a bug whose cause your words do not show. It
writes a test that fails, and finds the cause. Then:

- one rule removes the cause: the fast track;
- the fix needs more: the standard track, with an interview that starts from the cause;
- no bug: Lem explains what the code does;
- no way to reproduce it: Lem asks for one more fact;
- a question: an answer, and nothing merges.

## Careful

Your settings list what must never go wrong as topics, such as "a customer is charged the wrong
amount". A change that can affect one is careful, also in doubt. Every reviewer reads a careful
change, and you merge it.

## The checks and the review

The checks run your test commands. The test of each criterion must pass on the branch and fail
on the old code. The review is as large as the change: one read on the fast track, more reviewers
for a larger change. A reviewer marks each finding as a must-fix, a should (worth a fix) or a nit
(a small point). A builder fixes each must-fix, in two rounds at most. Then Lem opens
[the pull request](pull-request.md).

## Many tasks at once

Many tasks build and land at the same time, and Lem merges one at a time. The checks start only
while the load of your computer is below [`load.start`](settings.md#configlemmachinetoml), 40 by
default.
