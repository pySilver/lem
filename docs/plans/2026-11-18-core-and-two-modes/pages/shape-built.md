# The shape of built.md

The template of `built.md`, the file of what a task built and why. `land.py propose` writes it into
the task's folder from the task's records, beside `decisions.md`, and commits neither. A small change
gets no such file. Each part below is the text it writes, then one note: where the content comes from,
and what to leave out. `{{...}}` is a value; `[...]` is a part that is written only when its condition
holds. Records named "(new)" do not exist today; `notes.md` says what each must hold.

The file must read in one minute. It holds no history of the run: no times, no rounds, no rebase, no
commit hashes, no agent names, no review verdicts.

---

```markdown
[{{ILLUSTRATION LINE}}]
```

Note: only for a sample made by hand (`board.py --demo` or a fixture). A real task never has it.

```markdown
# What was built: {{TITLE}}
```

Note: from `task.md`, its first heading (`# ...`). Not the slug and not the pull request title, which
is a commit subject.

```markdown
[> [!CAUTION]
> **{{N}} thing(s) wait for you.**
>
> 1. **{{WHAT WAITS}}.** {{ONE SENTENCE OF FACT}}. {{THE ONE THING HE DOES}}.
> ...
>
> [The pull request is not green because of {{ITEMS}}. Merge it only when you agree with {{THEM}}.]]
```

Note: written when at least one of these holds, and not written at all otherwise (no "nothing waits"
line). The same block opens `decisions.md`, word for word. One item for each, in this order:
- a step that cannot be reversed: a line of `decisions.jsonl` with `kind: asked`, `irreversible` set,
  and no `answered` line for its `id`; the fact is its `what`, the action is "tell Lem" with its
  options;
- criteria he did not approve: `criteria.json` `by` is not `owner` (today `lem` or `correction`) on a
  full change, or the task's mode is alone (new, plan task 2); the action is "read the criteria below";
- a decision that nobody settled: a decision with `level: none` (new, plan task 3; today the nearest
  is `kind: timeout` with `by: timeout`); the action is "read decision N";
- any other line of `landing.json` `not_green` (a lowered bar, a check that came with the change, a
  criterion changed during the build), each as one item in plain words.
The last line names only the items that are reasons of `not_green`; a step that cannot be reversed is
no reason of it. Leave out: the merge of a green pull request, which every pull request waits for and
which the line below says.

```markdown
Pull request [#{{PR}}]({{PR URL}}), branch `{{BRANCH}}`. {{Green. It waits for your merge, as every pull request does. | The task ran alone from {{WHEN IN PLAIN WORDS}}.}}
```

Note: `landing.json` `pr.number`, `pr.url`, `branch`; green when `not_green` is empty; the mode and
the stage at which he said "go alone" from the task's record (new, plan task 2). Leave out: the base
commit, the forge's mergeable state, the size.

```markdown
## What you asked

> {{HIS WORDS}}

[In the interview you also said:

- "{{HIS ANSWER}}"]
```

Note: `ask.txt`, verbatim, quoted line by line. The interview's answers come from a record of the
interview (new: today no file keeps them); only his own words, at most three, the ones that changed
a criterion. Leave out: Lem's restatement of the ask and the interview's questions.

~~~markdown
## What was built

{{ONE TO THREE SENTENCES, OR A LIST OF ONE TO FOUR ITEMS: WHAT A PERSON CAN NOW DO OR SEE}}

[```bash
{{ONE COMMAND, WHEN THE CHANGE IS A COMMAND}}
```]

The code is {{WHERE, IN ONE SENTENCE}}. {{Nothing else changed. | WHAT ELSE CHANGED}}

[The criteria that the change holds. Lem approved them, not you.] Each one has a test that fails on `main` and passes on the branch.

1. {{CRITERION}}
~~~

Note: the "what" sentences come from the builder's report, `report.md` (its "Changed" item, rewritten
from the code's view to the user's) and from `criteria.json` `criteria[].text`; the files come from the
branch's diff names (`land.py` already has them for `checks.size`). The criteria list is written as
`criteria.json` has it, one item for each `n`; the "Lem approved them" sentence only when the red block
has the criteria item; "a test that fails on main" only when `landing.json`
`checks.criteria.tests` holds each criterion with `on_branch: 0` and `on_base` not 0, else the
criterion says "no test: {{no_test}}". For a small change with one criterion the list is folded into
the sentences (`built.md` of `report-heading-names-both-months`). Leave out: line counts, function
bodies, test names, the investigation's history.

```markdown
## Why we want it

{{TWO SENTENCES AT MOST}}
```

Note: `task.md` `## Outcome`, in plain words, with its example values kept. Leave out: the kind of
the task and its reason (`## Kind`), which tell how Lem worked, not why he wants it.

```markdown
## What did not get built

- {{A THING OUT OF SCOPE, AND WHERE IT IS OR WHO HAS IT}}
- {{A STEP THAT WAITS, WITH A POINTER TO THE RED BLOCK}}
- {{A DEFECT FILED IN THE BACKLOG: ITS FILE AND ONE SENTENCE}}
- {{A THING TO DO AFTER THE MERGE}}
```

Note: `task.md` `## Out of scope`, each item with its state now (another task's pull request is
merged, open, or not started: from that task's `state.md`); the pull request's notes, headings
`## Not done` and `## Left open`; the backlog items that the branch adds (`land.py` `branch_items`) and
the review's `outside` items; a step for after the merge from the notes (the backlog item that the
change makes obsolete, in the real sample). Leave out: an item that the task did build.

~~~markdown
## How to see it work

[In the task's worktree, `{{WORKTREE}}`:]

```bash
{{ONE COMMAND}}
```

It prints {{WHAT IT PRINTS}}. [On `main`, the same command prints {{WHAT MAIN PRINTS}}.]
~~~

Note: a "see it" line of the builder's report (new: today no record holds it; the real sample's
command was written and run by hand for this sample). One command that shows the behavior to a
person, not the test suite. The worktree path from the task's brief (`worktree:`), only while the
worktree exists. Leave out: the suite's command, which the pull request's checks already show.
