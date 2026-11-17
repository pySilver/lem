# Examples

Four tasks, from the request to the end. Each example is an illustration: the repository, the
names and the answers are examples. The lines of Lem have the form that Lem uses.

## A small fix

1. You type `/lem the date column must never wrap`.
2. Lem says: `fix, small: "the date column never wraps". Branch fix/date-column-nowrap. One
   builder, the checks, one read, then the pull request. Nothing waits for you; say "full" to give
   it acceptance criteria.`
3. One builder adds the rule to the stylesheet, and a test that fails on the base branch. It runs
   the tests of the files that it changed, and it commits.
4. The builder saw that the amount column wraps too. It files that as a backlog item, in a commit
   of its own.
5. The checks run the whole suite. The test of the criterion passes on the branch and fails on the
   base commit.
6. The review agent reads the diff itself: one read. It finds nothing that must change.
7. Lem opens a pull request. Its first line is "Green." It lists the backlog item.
8. You merge it on GitHub. The watch of Lem sees the merge, and Lem removes the worktree and the
   branch.

## A full feat, with an interview

1. You type `/lem let an export hold the gift note`.
2. Lem says: `feat, full: "an export holds the gift note". Branch feat/gift-note-in-export. An
   interview now, then acceptance criteria for your yes; after that it runs to the pull request
   without you.`
3. A scout reads the export code. At the same time, Lem asks its first question: "The gift note
   goes into a new last column, `gift_note`. Is that right?" You answer "yes".
4. The scout reports that the export already writes an empty cell for a value that is not there. Lem asks:
   "An order with no note gets an empty cell, the same as other empty values. Keep that?" You
   answer "yes".
5. Lem shows two acceptance criteria, and the personas read them:
   1. A CSV export holds the gift note of an order: order 1042 with the note "for Ania" has that
      text in its row.
   2. An order with no gift note has an empty cell, not the word "None".
6. Nobody is confused, and you type "yes".
7. A lead commits a plan with two tasks. The plan is not careful and not large, so it gets no plan
   talk.
8. One new builder makes each task. Each runs the tests of the files that it changed.
9. A new builder makes the polish pass. It removes one debug line.
10. The checks pass. The review agent calls the change not careful, and runs a round with the
    profiles that fit. It finds nothing that must change.
11. Lem opens a pull request. Its first line is "Green."

## A bug that is no bug

1. You type `/lem the invoice total skips credit notes`.
2. Lem says: `fix: "the total skips credit notes". Branch fix/total-skips-credit-notes. A builder
   finds the cause first, and I tell you what it found: then it is a small fix, a full fix, or no
   bug.`
3. The investigator makes an invoice with one credit note, and reads the total. The total is
   correct: the credit note is a line of its own, under the total, as the invoice template wants.
4. Lem tells you what the code does, in numbered steps, with where each step was read. The task is
   answered.
5. The investigator committed nothing, so Lem removes the worktree and the branch. The board shows
   the task in the "Done" lane, with the answer.

## A careful change

The project has the topic "a customer is charged the wrong amount".

1. You type `/lem round each line of an invoice before the sum`.
2. Lem says: `Careful: this changes how a customer is charged. fix, full: "each line is rounded
   before the sum". Branch fix/round-lines-before-sum. An interview now, then acceptance criteria
   for your yes; after that it runs to the pull request without you.`
3. The interview and the criteria go as in the full feat above.
4. The lead commits a plan, with `careful: yes` and the reason under its title, and stops.
5. Lem opens a companion session for the plan talk. The reviewer gives three questions in its
   first turn. The defender repairs the plan for two of them. The third holds two times, and it
   becomes a design choice.
6. The personas do not agree on the choice, so it comes to you as a card, with the answers of the
   two experts. You pick an option.
7. The companion closes. A new builder leads the build, with one builder for each task.
8. The polish pass and the checks run. The review agent runs the full review set of the project.
9. Lem opens a pull request. Its first lines say green, then careful, with the reason. Its notes
   say that the change holds no migration.
10. A person merges it, whatever `branch.land` says.
