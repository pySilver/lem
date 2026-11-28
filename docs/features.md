# A feature in parts

A feature is a large change in parts. Its branch, `feature/<name>`, starts from the base. Each part
is a task with its own checks, review and small pull request into that branch. The base gets
nothing until the end, when one pull request brings the whole feature as one squashed commit. No
release flag hides a part.

Lem never splits a task by itself. When a plan needs more than seven tasks, the report tells you
to ask the rest separately, for example as a feature.

## Start a feature

Type `/lem new as a feature:` and your request, or say "in parts" in the request.

1. The interview is the same as for any task.
2. The criteria page shows one group for each part, in the order of the build, and a last group for
   the whole feature.
3. Your yes approves the criteria and the parts. The answer "One pull request" makes one task with
   no parts.

```markdown
### save-endpoint: the server saves an item and returns it

1. A saved item comes back from the server: item 17 saved by Ania is in her list.

### android-saved-list: the Android app lists the saved items (independent)

2. The Android app lists her saved items: item 17 is in the list after a refresh.

### The whole feature

3. An item saved on the server shows on the Android app: item 17 shows there.
```

Each part waits for the part before it. A part with `(independent)` starts at once.

## What Lem does

1. Lem cuts `feature/<name>` from the base and pushes it.
2. Lem opens one task for each part, with the criteria of its group and no second yes.
3. Each part goes to a pull request into `feature/<name>`. The merge agent merges it, or calls you.
4. After each merge to the base, Lem merges the base into `feature/<name>` and runs the checks.
   This is a merge commit, never a rebase.

To add a part, type `/lem new part of <name>:` and what the part does. It is a new task with its
own criteria for your yes.

## The end

After the last part ends, the session of the feature starts its end:

1. A builder writes the tests of the criteria of the whole feature.
2. The review reads the commits that no review of a part read, and each
   [careful](flow.md#careful) part. A careful part can affect what must never go wrong.
3. Lem opens the pull request of the feature into the base.
4. You approve it. The merge agent never merges a feature.

Lem refuses the merge while an open pull request goes into `feature/<name>`. When you drop a part,
the feature waits for you: type `start <name> now`, or `/lem drop <name>`.

## Throw it away

Before the end, type `/lem drop <name>`. Each part that has not ended stops with it, and each pull
request stays open. Lem never deletes the branch. The answer gives the command for you:

```bash
git push origin --delete feature/<name>
```

After the end, ask for a revert in plain words, for example `/lem new revert <name>`. A task
reverts the one commit of the feature.

## A feature from a ticket

The feature keeps the ticket, and a part has no ticket. Lem keeps one comment on the ticket, with a
box for each part, and sets the box when the part lands. Lem writes the comment again from its
records each time. Whether Linear draws the boxes is untested.

## What GitHub does with the parts

- A workflow with `on: pull_request: branches: [main]` does not run on the pull request of a part.
  Add `'feature/**'` to its branches for your CI on the parts. The checks of Lem run on each part.
- When the head branch of a merged pull request goes, GitHub moves each open pull request into it
  onto the base. So Lem refuses the merge of a feature while a pull request goes into its branch.
- GitHub closes the open pull requests of a branch that you delete. Whether this closes a pull
  request of a part into `feature/<name>` is untested.
