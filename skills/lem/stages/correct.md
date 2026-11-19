# `be-careful`, `standard-track`, `drop`

Read when the owner corrects a task: `/lem be-careful [task]`, `/lem standard-track [task]`,
`/lem drop [task]`, or a sentence that plainly says the same ("be careful with this one", "drop
the footer task"). Lem's first line for a
request ends with these words, so that his next message can correct its read.

**Which task.** The one he names. With none named, the task this conversation is about, when
exactly one fits: say which task you took in your answer. When more than one could be meant, ask
once in the terminal, in one line, with the open tasks named. Never guess between two tasks.

**A task in `landing`.** Before `standard-track` or `drop` does anything to it, `lem land checks
SLUG --stop`: it stops the task's checks when they run, and does nothing when they do not.

## be-careful

Careful at any time before the merge, whatever its lead called it. At once, add the line
`careful: the owner says so` to the task's brief, and log his words with `lem decisions log SLUG
--by owner`. During an interview the brief is written already (`stages/new.md`, step 6), and
the lead that starts after his yes reads the line. The brief holds it: whoever reads the task's next stop reads that line, also a Lem
that started after this one, and the landing reads it too: the change gets the project's full
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
wait for its stop (its reply wakes you), since its last state would stand over yours. Then write the state `held` with
the line `the interview waits for the owner`, the lead's brief of step 6 of "Open the task"
(`stages/new.md`) over the fast track's, and open the interview's companion as "The interview's
companion" there says, the copy of the talk first. When its builder ran, the companion reads the
builder's `report.md` as the scout's report. A
move from the fast track to the standard track is his or its builder's; a change of the type is his
only. Once its pull request exists (the task is `open` or ended), say in one line that the track no
longer changes, and that a new request does it.

## drop

A task that is not wanted, at any point before its landing. Write the state `dropped` with his
reason in one line. Close the task's companions: the plan talk's when one is open
(`open-task-session`), and each need's that `lem companion list` names for the task, `lem
companion close SLUG --need NEED --why dropped` (with `--choice N`). Remove its worktree the way
the project does. A branch with commits of its own stays, because those commits are on no other
branch, and `lem land clean` names how to delete it; a branch with none, which the base holds
whole, goes (`lem land clean` does both and says which). For a task that came from a ticket, the
tracker then says so on the ticket (its "drop") and changes no status: tell the owner which status
the ticket has, since where it goes now is his call. Then look at the queue, as `stages/start.md`
says under "The queue".
