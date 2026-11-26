# The pull request

Lem opens each pull request on GitHub, the one way a task lands. [The merge](merge.md) tells what
comes after.

## What it says

The first line says green or not green, and each reason for "not green" comes next. Then come your
request, the acceptance criteria with their tests, the checks (your test commands), and each
decision with who took it and why.

A pull request is not green when one of these is true:

- your tests got less strict (the bar went down), even with a reason in the plan;
- the review left a must-fix after two rounds, or no reviewer answered;
- a criterion changed during the build. You can clear this reason if you approve the revised
  criteria. Lem also omits this reason for a change you make through a breaker;
- the dialectic or the experts made a decision, or the lead made a choice that the ladder could
  not settle;
- Lem approved the criteria without you: while you were away, or in a night task;
- the personas did not answer, two times, when they read the criteria;
- the change brings the first checks into a project that had none;
- a task on the fast track turned out to be careful: it can affect what must never go wrong.

Smaller choices of an agent do not change green. The pull request lists the ones that matter.
Green usually lets you merge without your own read. A careful change or a call from the merge
agent still needs your read.

## What Lem saw outside the task

The pull request names each defect that an agent found outside the task, under one of four
headings:

- **Fixed on the way**: a cheap defect: text that does not run, or a finding of a check that its
  next run shows fixed. Text that does not run is a comment, a docstring or a sentence of a
  document. An agent that
  already works on the branch fixed it in a commit of its own, whose message names the fix. A
  refactor is never cheap.
- **Filed in the backlog**: a defect that occurs today and confuses a user, breaks a contract,
  damages data or costs money. It is an item in `docs/backlog/` with `worth: later`.
- **Filed as not worth it**: each other defect, as an item with `worth: no`, so that the next
  agent finds it decided. Its last line can give the reason (`Decided against: REASON`).
- **Seen, not filed**: a defect that an open item holds, with the path of that item. Or a line
  with its bar call and its reason.

The bar is rule 6 of `agents/lem-builder.md`, or of your own `.claude/agents/lem-builder.md`. It
is for Lem's agents only: an item that you write or ask for is always filed. When the `worth` of
an item does not agree with the bar, the merge agent calls you.

## A second look by Jev

Before an agent files a defect, the Jev decision model names up to three items of the backlog
that can hold the same defect. The agent reads them. Each line under "Seen, not filed" or "Left
open" must name an item or give a bar call. Use `under: REASON` or `cheap: REASON` for the bar call.
`lem land propose` refuses a line that has neither.

Jev also reads each defect that an agent calls under the bar, one time. When Jev reads it as over
the bar, `propose` stops one time, and the agent looks again. The agent can keep its call. The
line of the defect ends with the score (`Jev: 0.82`), or with why Lem did not ask
(`Jev: not asked (no key)`). [`[jev]`](settings.md#jev) can stop these questions.

## The time and the tokens

The [merge review](merge.md#the-merge-review) of each pull request gives the time of the task and
the tokens that its sessions spent. The board shows the same on the task's **Timeline**.
