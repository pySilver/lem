You review the end of one feature for Lem, before its pull request is proposed to the owner. A
feature is a task whose work came in parts: each part was a task of its own, with its own review
and its own small pull request into the feature's branch, and that branch now goes to the base in
one pull request. You change nothing: no file of the worktree, no commit, no task record.

Read `review.md`, the file beside this one, and follow it: its inputs, its steps and its record
hold for this review too, with the differences below. The brief has one key more, `feature`:

- `parts`: each part with its `status`, its pull request (`pull`, `url`), its `review` as a line
  (the kind, the counts, the careful call, and green or not), `careful`, and for a careful part
  `diff`, the command that prints its whole diff.
- `commits`: each commit of the feature's branch since the base that is no part's merge, with
  `show`, the command that prints it whole. These are the feature's own commits: its start, and
  what the builder of its end wrote for the criteria of the whole feature.
- `syncs`: each merge of the base into the feature's branch. `remerge` is a file in the task
  directory with what the merge changed beside git's own merge of its two parents
  (`git show --remerge-diff`): the hand of a builder who resolved a conflict, or of a repair. A
  sync with no `remerge` is git's own merge, and holds nothing to read.
- `criteria`: the criteria of the whole feature, by number and sentence.

1. **Read the change**, in place of step 1 of `review.md`. Each part's review read that part's
   diff, so the parts are not read again. Read whole: each commit of `commits`, by its `show`;
   each file `remerge` names; and the whole diff of each careful part, by its `diff`. The diff
   of `range` is the whole feature as it will merge: read it where a commit you read needs its
   context, never to review a part again. Check that the commits you read hold the criteria of
   `criteria`, and that each `remerge` keeps both sides: what the base brought, and what the
   feature had. `resolution` and `range_diff` of the brief are null for a feature: its base is
   taken in by a merge, and a resolution of it is a `remerge`.
2. **The careful call**, as step 2 of `review.md` says, of what you read in step 1. A part that
   `parts` names careful makes the feature careful: your call is `careful: true`, and
   `careful_why` names that part and the topic of its call.
3. **Route**, as step 3 of `review.md` says, by what you read in step 1 and not by the size of
   `range`: the parts' lines are no lines of this review. `in_parts` and `lines` of the brief
   count the whole feature, so read them as its size, not as yours.
4. Steps 4 to 8 of `review.md` hold as they are. A defect that you see in a part's code is a
   finding of this review like any other, since the feature merges it; a defect the base already
   has stays outside the change, as step 5 says.

Your reply is the one `review.md` gives.
