---
worth: later
where: skills/lem/stages/build.md
added: 2026-11-27
---
# A builder is not told of other open tasks on its files

Many tasks of one repository build at the same time, each in its own worktree. The brief of a
builder (`skills/lem/stages/build.md`, step 1) names the other builder of the same task when two run
at one moment ("another builder runs: task N, its files PATH"), but it names no other task. So two
tasks can change one file and learn of it only at the merge: task `gift-note` adds a column to
`shop/export.py` while task `export-dates` reorders that file's columns, and the second to merge meets a
conflict that its builder could have avoided by a word in its brief.

What a reader would get wrong: the merge line's rebase and checks catch the conflict, so nothing is
lost. True, and the cost is a second build round and a merge review after it, on work that one line in
the brief would have shaped.

Options:

- (a) The brief names, as facts, each other open task whose branch changes a file this task's plan
  names (`git diff --name-only` of that task's branch against its base): its slug, its files in common,
  and its stage. The builder keeps its own scope; the facts only let it avoid a needless clash. Cost: one
  read per open task when a brief is written, and a few lines in a brief.
- (b) The board shows the overlap, and the owner decides. Cost: one more thing for him to read.
- (c) Nothing: the merge line handles it.

Recommendation: (a). Unknown that settles the `later`: how often two open tasks of one repository touch
one file in his use. Count it from the task records of mybaze after a few weeks on Lem 0.4 (the
landing records keep each task's edited files).

Surfaced in the roadmap of the rebuild, "After the cutover" (the owner's list of 2026-11-25).
