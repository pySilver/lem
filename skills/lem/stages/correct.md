# `be-careful`, `standard-track`, `drop`

Read when the owner corrects a task: `/lem be-careful [task]`, `/lem standard-track [task]`,
`/lem drop [task]`, or a sentence that plainly says the same ("be careful with this one", "drop
the footer task"). Lem's first line for a
request ends with these words, so that his next message can correct its read.

**Which task.** The one he names. With none named, in a task's session, that session's task. In
another session, the task this conversation is about, when exactly one fits: say which task you
took in your answer. When more than one could be meant, ask once in the terminal, in one line, with
the open tasks named. Never guess between two tasks.

**Where it runs.** What is a file (the brief's line, the record, a state) is written at once, in
whichever session he typed it. A step of the task's work (its landing again, its interview) runs in
the task's own session: typed elsewhere, `lem session open SLUG --why owner` opens it, or prints
the one that runs, and its session takes the step at his word.

**A task in `landing`.** Before `standard-track` does anything to it, `lem land checks SLUG
--stop`: it stops the task's checks when they run, and does nothing when they do not. A drop stops
them itself.

## be-careful

Careful at any time before the merge, whatever its lead called it. At once, add the line
`careful: the owner says so` to the task's brief, and log his words with `lem decisions log SLUG
--by owner --what "whether the task is careful" --chose "careful until its merge"
--why "HIS WORDS, AS HE TYPED THEM"`. During an interview the brief is written already
(`stages/new.md`, "The request", step 6), and the lead reads the line. The brief holds it, so every session of the task after this one
reads it, and the landing reads it too: the change gets the project's full
review set, its notes say whether it holds a migration, and a person merges it whatever the
settings say (`stages/land.md`). What follows depends on where the task is:

- it still builds, or it is `ready`: it finishes and goes to the landing like any other; nothing
  is built again for the word;
- it is `landing`: the review of step 5 of `stages/land.md` takes the full set when it runs, and
  a review that already ran is under that floor, so `lem land read` asks for it again, unless two
  rounds ran already;
- it is `open`: `lem land start SLUG` takes it into the landing again, and steps 2 to 6 of
  `stages/land.md` run on it: the checks, the review with the full set, and `lem land propose`,
  which updates its pull request. It then says careful, and a person merges it.

Then ask what his word was about, when it is not plain. A topic the settings already name, which
the lead read wrong, is a lesson about that judgment (`stages/learn.md`). Something no topic names
may be a rule for later tasks or a wish for this one task: only he knows, and only his yes puts a
topic into the settings.

## standard-track

A task on the fast track takes the standard track with an interview, until its pull request exists:
the interview (`stages/interview.md`), the personas' read, and his approval, which replaces the
fast track's. A builder that runs then finishes, and its commits stay on the branch for the lead;
wait for its stop (its reply wakes you), since its last state would stand over yours. Then move
it back to its shape and read it again for the standard track, with the type, its reason and each
careful topic of the read before (`lem task show SLUG`):

```bash
lem task move SLUG shaping
lem task read SLUG --type TYPE --why "WHY" --track full --then interview --wait interview
```

Write the lead's brief of step 6 of "The request" (`stages/new.md`) over the fast track's, and take
`stages/interview.md` in the task's session. When its builder ran, the interview reads the
builder's `report.md` as the scout's report. A task that is `queued` stays queued, and takes no
move and no wait: the correction changes only the path its wait ends in. Read it again with
`--track full --then interview` in place of `--track small --then fast`, with the same `--after`
and `--order` as before (`lem task show SLUG`), and write the lead's brief of step 6 of "The
request" over the fast track's; the interview starts when the wait ends (`prompts/session.md`,
"What comes next"). A
move from the fast track to the standard track is his or its builder's; a change of the type is his
only. Once its pull request exists (the task is `open` or ended), say in one line that the track no
longer changes, and that a new request does it.

## drop

A task that is not wanted, at any point before its landing, and one of his three answers to a
breaker. A task the release stop blocked (its first `lem` command printed the message that it began
two releases back) drops at any status, `open` too: the line that tells him it is dropped names its
pull request, which stays open on GitHub for him to close. Drop it with his reason in one line:

```bash
lem task move SLUG dropped --line "HIS REASON"
```

It stops the task's checks when they run, and takes the landing's step lock, so a step of the
landing that runs ends first; then it reads the record again. When GitHub merged the pull request
meanwhile, it refuses with `merged`: the task is merged, not dropped, so tell him so in one line
and take the step `lem land next SLUG` names, which lands it. For a task that came from a ticket,
the tracker says so on the ticket next (`load-skill` the skill `tracker.kind` names, its "drop"),
before anything else of the drop, so that a worktree the cleanup refuses does not stop the
comment. It comments, removes an assignee it added at the start, and changes no status.
Tell the owner which status the ticket has now (an issue stays open), since where it goes now is
his call. Close the plan talk's pair when one
is open (`open-task-session`). Remove its worktree the way the project does. A branch with commits of its own stays, because
those commits are on no other branch, and `lem land clean` names how to delete it; a branch with
none, which the base holds whole, goes (`lem land clean` does both and says which). Its task
directory stays, `handoff.md` and each breaker's document (`breaker-N.md`) with it, so that `/lem resume SLUG` opens a new task
from them and from the branch (`stages/park.md`), and for a task the release stop blocked a new
request from its notes and its branch; say so in the line that tells him it is dropped. A task queued after this one does not
start: it stays `queued` for his word (step 7 of "The request", `stages/new.md`). The same line
that tells him this one is dropped names each such task as one that waits for his word, "start
SLUG now" or `/lem drop SLUG`: in `lem waiting`, take each `after_dropped` entry whose `after`
list contains the slug of the task just dropped. Last, the task's session closes: typed there, as its
last act (`prompts/session.md`, "The end"); typed elsewhere, `lem session close SLUG --why owner`.
