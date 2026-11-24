"""Take one task's branch from `ready` to a pull request and to the base branch, one
step at a time.

Nothing reaches the base branch without the machine checks and a review by an agent that
did not build it, and a task ends as a pull request on GitHub, the one way Lem lands; a
fresh merge agent reads each proposed task, and merges it or calls the owner. Each step
here is one command, prints JSON, and refuses with exit 1 and the reason when the step
may not run; nothing is retried and nothing is forced. Every step first asks
`lem project may-land` about the settings' base branch, so a protected branch is never
reached, whoever asks.

    lem land start SLUG [--conflicting]
                           the task's landing starts: its state becomes `landing`, also while other
                           tasks land; an `open` task the forge calls conflicting says so with
                           --conflicting
    lem land base SLUG     bring the base branch in by a rebase; a conflict is reported, not resolved
    lem land polish SLUG   the polish pass starts: what its builder gets, and the tip it starts at
    lem land polish SLUG --done
                           after the polish builder: what it committed is checked, and logged
    lem land checks SLUG   the machine checks on the tip: every command of the checks, each
                           criterion's tests, the bar, the size in files and lines
    lem land checks SLUG --status
                           whether the checks run now, for how long, against their last finished
                           run, and how their last run ended; it starts nothing
    lem land checks SLUG --stop
                           stop the checks that run now and wait for their end; with none, nothing
                           is stopped, and that is no error
    lem land read SLUG     whether a review is due, the least it may be, and what a reviewer gets
    lem land read SLUG --record FILE
                           write down what the review was and what it found
    lem land file SLUG [--again] [--same rN.M=PATH ...] [--new rN.M ...]
                           file each defect a review saw outside the change and called over or
                           under the bar as an item of the backlog, `worth: later` or `worth: no`,
                           and commit the items on the task's branch; a defect whose open item the
                           tip holds is that item; first, a defect Jev reads as one an item holds
                           stops the step, and the next run says `--same` or `--new` for it
    lem land alike SLUG --where WHERE --title TITLE --what FILE
                           the items of the backlog folder at the task's tip that Jev reads as the
                           same defect as a finding, three at most, before an agent files it by
                           hand; with nothing sent, every item, for the agent to read
    lem land propose SLUG --title SUBJECT --notes FILE
                           push the branch and open its pull request on GitHub, or update the one
                           that is there: the state becomes `open`
    lem land merge-review SLUG
                           what the merge agent reads: its brief, merge-brief-TIP-BASE.md in the
                           task directory, with the facts of the task and what moved on the base
                           since the checks, and its seat
    lem land merge-review SLUG --file FILE --tip COMMIT --base COMMIT
                           write down the merge agent's reply as merge-review.md: its verdict,
                           merge or call, whether the owner is called, and on a moved base its call,
                           safe or another round; the commits are the `tip` and the `base` the brief
                           named, and the reply of a brief of an earlier proposal is refused
    lem land merge SLUG --by owner|merger [--message SUBJECT] [--via session|server] [--standing] [--tip COMMIT]
                           merge the pull request through GitHub: the owner's word, or the merge
                           agent's where the settings and the request allow it; `--via server`
                           when the board's server runs it, `--standing` for the owner's merge
                           that a moved base refused and that stood through the new landing or
                           a read that said the move is safe;
                           `--tip` the commit the caller saw, which must be the one proposed now
                           (the board's server always gives it)
    lem land merged SLUG   the owner merged the pull request on the forge: finish the bookkeeping;
                           or he closed it with no merge: the task is dropped
    lem land clean SLUG    remove the task's worktree after the merge, and its branch when it
                           holds nothing that was not merged

What each step keeps for the next is in `landing.json` in the task's directory: the
task's branch, the base it was rebased on, the commit and tree the checks passed on,
each review, and the pull request. Three steps log the start of what they start, so that
the board's time card has a start and an end for each: `polish` logs `polish.start` when
a pass starts (not again for a second start of the same pass), `checks` logs
`gate.start` before its first command, and `read` logs `review.start` once for the
attempt that is due; `polish --done`, the checks' `gate.end` and `read --record` are
their ends. The checks keep the names their step had before it was called the checks:
the events `gate`, `gate.start` and `gate.end`, the folder `gate/` of a task's directory
and `gated` in `landing.json`, which open tasks and the board read.

A FILE of `read --record`, `propose --notes` and `merge-review --file` is read from the
working directory, and a relative one that is not there is read from the task's
directory (`task_file`): a task's session stands in the main checkout, and the files are
the task directory's (`reviews/review-1.json`, `notes.md`, `merge-answer-TIP-BASE.md`,
the answer file `merge-review` names for the tip and the base of its brief).

One step of a task runs at a time. Every step here that names a task takes the task's
one step lock (`step.lock` in its directory) before anything else it does, and holds it
until it ends, however it ends; the first thing it writes there is its name, its process
id and its start. A step of the same task meanwhile exits 1 and names the step that
holds the lock, since when and in which process. While the checks hold it, a second
`checks` is refused because they already run, and any other step says that their end
comes first, so that nothing is proposed, read or rebased while they run.
`checks --status` and `checks --stop` take no lock: they look at the file and at the
process it names, never at the lock, so a look never makes a real start fail. Nor does
`alike`, which writes nothing and which a builder runs between two steps. The commands a
step runs do not get the lock's file, so a server one of them left behind does not
hold it.

A run of the checks is two events: `gate.start` and one `gate.end`, however it ends,
with `result` (`passed` when the step keeps its result; `red` for a command of the
checks that failed; `refused` for a criterion's test that does not hold, a lowered bar,
a command that changed the tree, or an error of the step itself; `stopped` for a stop),
`seconds` from its start, `tip`, `taken` (only for a run that took the polish pass's
result of the criteria's tests in place of its own run: the commit that run was on,
which logs no `task.red` of its own), and `say`, the one line for the owner, with the
slug, the result and the next step, and no question ("SLUG: the checks passed; the
review runs, nothing for you"). A run stopped while it waited at the load gate is its
`gate.end` alone, `stopped`, with `seconds` 0, since none of its commands started. The
step prints `say` in its JSON at every end after `gate.start`, a red, refused or stopped
one before its exit 1. The run clears the result an earlier run kept before its first
command, so a run cut off with no chance to clean up leaves none for its tip. `--status`
gives `running` (the step lock is held by `checks`), `since` and `seconds` of the run,
`last_seconds` (the `seconds` of the newest `gate.end` that passed, of any task, or
null), and `overdue` with its `say` when the run is more than three times as long as
that one (`OVERDUE_TIMES`) and has gone on for at least a minute (`OVERDUE_FLOOR`); and
`ended`, the newest `gate.end` of the task with `resumed`, the line for a session that
did not start that run, which says its result as past and the next step as it is now.
`--stop` sends a term to the process the lock names, only while `checks` holds it, waits
until that run lets the lock go (`STOP_WAIT` at most), and says whether it stopped
one (`stopped`).

A task on the fast track has no plan: its one acceptance criterion is `criteria.md` in
the task directory (`criteria.py` gives `small`), which the steps read in the plan's
place. It is one task and never gets a polish pass (`polish` refuses it): its builder
judges each defect it saw outside the change by the bar of rule 6 of the builder's
standing rules, fixes a cheap one, and files each other one in the backlog folder,
`worth: later` over the bar and `worth: no` under it, each in a commit of its own, and
the pull request lists each file the branch adds there under `## Filed in the backlog`,
or under `## Filed as not worth it` when the file says `worth: no`. It has no reason for
a lowered bar (the checks refuse one: a lowered bar takes the standard track), and its
pull request's text is short. One that is careful after all is not green, since it took
the fast track with no interview, read or plan.

The machine checks have no model in them. `checks` runs the settings' `checks.commands`,
the whole suite, which runs here one time and in no builder; then, when they all passed,
each command of `checks.serial`, the tests that two tasks cannot run at the same time
(an end-to-end suite on fixed ports, one database, a browser), each under the
repository's one lock for them through `lem project serial`, which waits while a builder
or another check holds it; then `lem criteria red` (each criterion's tests pass on the
branch and fail on the base commit), then the bar. The checks take the polish pass's
result of the criteria's tests in place of a run of their own when the pass committed
anything and `lem criteria inputs`, read after the commands, gives the five inputs the
pass's run reported: the tip, the base commit, the plan file, `checks.setup` and
`checks.serial`. That read of the criteria refuses the checks as a run of the tests
would; the result they keep then names the pass and its commit (`taken`), and the pull
request says the tests were taken from it and not run again. A commit after the pass, a
rebase, a base branch that took in a commit of the branch, another plan file or other
settings, and the fast track, which has no pass, make the checks run the tests
themselves. A change lowers the bar when it adds a lint or type suppression, a skipped
test or a mark that runs one test alone, a test that runs again until it passes, deletes
a test file or moves it out of the tests, or leaves fewer assertions in one (counted by
the words `assert` and `expect` on the lines it adds and removes, in a test file and in
every Rust file, where unit tests sit beside the code). In the settings of a test runner
or of coverage (`pyproject.toml`, `setup.cfg`, `pytest.ini`, `tox.ini`, `package.json`,
`.coveragerc`, `.nycrc`, `jest.config.*`, `vitest.config.*`) it lowers it by a new
`--deselect`, `-k "not ..."`, `--ignore`, `testPathIgnorePatterns`, rerun or retry, and
by a coverage threshold whose number went down or that is gone, there or on a command
line of the forge's workflows. Each existing test, snapshot and test configuration the
change edits is listed (`edited`), and the pull request names them: what a test expects
is read by the review, since no mark shows a changed expectation. A mark counts when the
change leaves more of it in a file than the file had, so a line that only moved is no
new mark; a mark whose own text changed is a new one. A lowered bar passes only with a
reason for that file under `## The bar` in the task's plan, as `- PATH: REASON`. The
marks looked for are those of Python, JavaScript and TypeScript, Go, Rust, Java and
Kotlin, and shell. A changed file of another language gets no such check, and the result
says which (`not_covered`). The size of the change, in files and changed lines, is
counted, for the reviewer.

Each command of the checks runs in a process group of its own, with no standard input;
the group is ended when the command ends, so a server or a `sleep` it left behind does
not outlive it, and when the checks are stopped (a signal, an interrupt, `--stop`) the
command that runs is ended with its group and the step exits 1 with no result kept. The
step's handler of a stop holds from its first line to its last: a serial command's
wrapper gets the time of its own cleanup before it is killed (`SERIAL_GRACE`), and
`lem criteria red` gets the stop and is waited for, so that it ends its tests and
removes its two worktrees itself. Checks with no command to run are refused, since
checks that ran nothing show nothing; so is one whose command changed a tracked file or
made a commit on the branch, since its result is then about another tree. A file its
commands wrote that git neither tracks nor ignores (Python's bytecode in a repository
with no rule for it) is the run's output, and nothing of it lands: the step notes what
git does not know before its first command, removes after its last, or after a stop,
each such file that was not there before and each folder that leaves empty, names them
in its output (`removed_untracked`) and in one line of the last command's output file,
and goes on. Before that note, and before the first command, the step removes each
`__pycache__` folder that git ignores by itself, a leftover of someone's Python run (a
builder's test without `-B`), which Python rebuilds from the source: a `__pycache__`
inside a folder that git ignores as a whole (`.venv/`) stays with that folder, and every
other ignored file stays. It names each removed folder in its output only
(`removed_bytecode`), each once it is gone, and goes on; a folder that cannot go refuses
the run with the fix named. A `__pycache__` that a command of the checks writes stays,
so a check that looks for one still sees it. What the checks keep is the tip they ran on
and that tip's tree.

An `open` task lands again when its base moved: after a merge, Lem takes each task whose
pull request the forge calls conflicting through `start --conflicting`, `base`, the
checks, the review that is due and `propose`, which keeps its pull request; every other
open task waits as it is, and `merge` refuses it on a base that moved by any file since
the checks ran until the merge agent's read of what moved says the move is safe (below);
when it says another round, the task lands again the same way, with no `--conflicting`.
`start` counts each new landing of an open task (`relands` in `landing.json`, a
`land.again` event with `count`), for the merge agent's facts; nothing bounds the count.
The pull request's text and the state say in one line what happened ("rebased on main
after the forge called it conflicting; one conflict in shop/dates.py, resolved by a
builder; one read of the resolution; the merge review carried over the resolved
conflict: the resolution read found nothing; the checks passed again"). A conflict that
`base` meets is kept in `landing.json` with the tip before the rebase and whether a
review covered the change then; the builder that resolves it rebases the branch itself,
and the next `base` finds the rewritten commits by that tip, gives the polish pass's
commits their new names, and keeps the resolution. The newest review that saw the change
stands as it was through a rebase that git made with no conflict, also when the base
changed a file of the change in other lines: `base` carries it onto the new base, for a
careful request too, and a must-fix it left stays open, so the request is not green for
it in the same words (`review_carries`). The pull request's text and the `proposed`
event say so ("the review carried over the rebase, and its open must-fix"). Whether that
review also left no must-fix is what a conflict's record keeps as covered: with an open
must-fix a resolved conflict gets the rules of the change, not one read of the
resolution, and keeps the reason no review covers it. A builder's resolution gets one
read of what it changed (`git range-diff` of the commits before and after the rebase),
or the project's full set for a careful request; that read is no round, and anything
committed after the resolution is reviewed as a change like any other. A read of the
resolution that answered and found nothing (0 must-fix, 0 should, 0 nit), on a request
that no call makes careful, carries what was said of the tip at its merge onto the
resolution's tip, as a rebase with no conflict does (`moved_carry`, below). A careful
call is a reason of careful now, or the careful call of the newest round of the change,
which the read's own call does not take back. A read with a finding, a careful request,
a read that did not answer and a commit after the resolution carry nothing: a fresh
merge agent reads the task, and `propose` says why.

`start` refuses a worktree on no branch: `propose` pushes the task's branch and `clean`
deletes it. Any number of tasks land at the same time, each in its own worktree and
under its own step lock: a feature waits for no other task's landing. Two `start`s at
one moment take turns only to read the tasks' states and write `landing`, under a lock
of the state folder (`landing.lock`). With no command of the checks it writes the task's
state `blocked`, and a later `start` takes that task back once the commands are there;
each refusal on the way names the step out, also when its worktree is gone. That check
comes after what `start` does with the record, so its own `blocked` block never stands
between a start over and the record it deletes.

`start` of a `ready` task starts the landing over when the newest state block holds the
line `the landing starts over`, which `lem project state SLUG ready --start-over`
writes, or when the record holds no proposal: `landing.json` keeps only the pull
request, the pushes (`pr`, `pushed`, `taken`) and a polish pass that is done. When the
owner's merge stood (`owner_tap`), its end is logged first (`merge.ended`, with `why`
"the landing started over: WHY") and printed as `owner_merge`, `ended: ...`; otherwise
`owner_merge` is null. A `ready` task whose record holds a proposal, with no such line,
came back from a new landing that was cut (a wait for a red base, a builder that ended
twice), since a task leaves `open` only through `start`, which counts the new landing:
it goes on with that landing, and the record stays whole, with no second count. A second
rebase in one landing then gives what one rebase with no wait gives: when the branch is
still the tip the newest clean rebase of this landing made (`made`, which `filed_on`
does not move), and no conflict or resolution is on record, `base` throws that tip away
(only `propose` pushes, so it was never pushed), moves the branch back to the tip that
rebase started from, and rebases that tip onto the base now, with the polish pass's
names moved back by their place from the tip (`through_rebase`). A commit after `made`,
or a conflict on the way, is judged as a rebase after it, as with no wait.

What two landings share is the machine and the base branch, and each has one rule. The
checks start only while the machine's load average is below the start number of this
machine (`[load] start` in `machine.toml`, beside the owner's mark, else Lem's 40): a
run waits before its first command, logs `gate.wait` with the load and the number while
it waits, and starts when the load is below the number. The runs that wait form one line
for the machine, of every repository on it (`load.line/` beside `load.lock`, one locked
file for each run): the one another open task waits for goes first (the `after:` line of
a queued task, or of a task blocked by a red base), then the one whose wait began first,
and only the first in the line starts. A run behind another logs `gate.wait` with
`behind` and `why`, also while the load is above the number, and a run whose process is
gone loses its place at the next look of another. Two runs that wait start at least
`LOAD_SPACING` seconds apart, so that the load average shows the first before the second
reads it. `lem project load --start none` takes the gate away on one machine
(`lem doctor` gives the line that sets a number). And Lem's own merge calls (`merge`) go
one at a time, under `merge.lock` of the state folder: a second call logs `merge.wait`
with the task that holds it, waits, and reads the base branch after it takes the lock,
so that it meets the merge before it. The commands of `checks.serial` still take the
repository's one lock for them; nothing else does.

The checks are the main checkout's. One task may bring its own: when the main checkout's
settings name no command of the checks and the task's branch adds them to its
`.lem/settings.toml` (they are not on the base commit), `start` and `checks` take those
commands, as for the first task of a new repository, "set up the checks"; the request is
then not green, so that a person reads the checks once. The rest of the branch's
settings, its `checks.setup` too, are not read. A branch that changes checks the main
checkout has is checked by the main checkout's.

The polish pass comes after the task's own work and before the machine checks, so that
the review reads the code as it will merge. A fresh builder looks for a short fixed list
(a comment the change made false, a leftover, code that reads badly, a document the
change made false, and the defects outside the task that the lead's report and the
interview named) and changes no behavior. `polish` prints what that builder gets: the
range of the task's own commits from the base, the plan, the report, `outside.md` of the
interview when the task has one, the backlog folder, the item the task was started from
(below), and the files the pass may not change. It keeps the tip the pass starts at; a
second start before `--done` keeps the same one. `polish --done` refuses a worktree with
changes nobody committed, a branch that no longer holds that tip, a pass that leaves a
criterion's test file or the plan other than it found them, and tests of the criteria
that no longer pass on the branch and fail on the base commit (`lem criteria red`, run
when the pass committed anything). Otherwise it logs one `polish` event (the tip before
and after, the count of commits, the items it added to the backlog folder), and keeps
the result of its run of the criteria's tests, with the inputs that run reported, for
the checks. `checks` refuses a task on the standard track with no pass of this landing
whose last commit the tip holds, and any task whose pass started and is not done. Every
task with a plan is on the standard track: `criteria.py` refuses a plan that says
`Size: small`, and so does every step here that reads the criteria. The commits that
come after the pass, a repair, a fix of a review's findings, the items `file` writes,
are on top of it, and a rebase by `base` gives the pass's commits their new names; a
rebase in which git leaves out one of the branch's commits (`through_rebase`), and any
other rewrite of the branch, ask for the pass again. The pass runs once for a task:
`start` of a `ready` task that starts over keeps a pass that is done while the branch
holds its last commit, and a `ready` task that goes on with its landing keeps the whole
record (above).

A review comes before anything is proposed. There are three kinds: one read, which is
the review tool's smallest profile, for a short and simple change; a round of the review
tool with the profiles or lenses that fit the change; the project's full set. Which one
a change gets, and which profiles fit it, is the judgment of the agent that starts the
review, from the diff and from what each profile is for: no code and no list of words
decides it. This script holds only the floor that no judgment goes under: the full set
for a careful request, and a round at the least for a plan of more than three tasks and
after a review that found a must-fix.

Whether a change is careful is judged against the project's topics (`flow.topics`,
sentences of what must never go wrong, read from the main checkout's settings like every
setting here): no list of paths decides it. A request is careful when the owner says so
(that word in the task's brief), when the plan says so (its `careful: yes` under its
title, in its text now or in any commit of the branch: a later commit does not take the
yes back), when the newest review that answered says so, or when the change edits
`.lem/settings.toml` at all. The last is the one rule this script matches by itself,
because the file is Lem's own and a task rarely edits it: its tables say, for every
later task, what is careful, what the checks run, who merges and where a task lands, and
the reason names each table whose values the change edits, that only its text changed,
or that the file is gone. A change that adds, changes or removes
`.lem/settings.local.toml` is careful by the same rule: that file is one machine's own
and is not to be tracked. The review is the look at the diff itself, by an agent that
did not build it: its record makes the call, and a careful call takes the full set.

The record of a review is a JSON file:

    {"attempt": N,
     "tip": THE WHOLE COMMIT THE REVIEW READ,
     "kind": "read" | "round" | "full",
     "ran": [{"name": PROFILE OR LENS, "why": WHY IT FITS THIS CHANGE}],
     "left_out": [{"name": PROFILE OR LENS, "why": WHY IT DOES NOT}],
     "answered": [SOURCE, ...],
     "silent": [{"name": SOURCE, "why": WHAT STOPPED IT}],
     "bar": [{"name": FILE, "why": WHAT THE REVIEW SAYS OF THE REASON GIVEN FOR IT}],
     "must_fix": N, "should": N, "nit": N,
     "outside": [{"where": PATH OR PATH:SYMBOL, "title": ONE LINE, "what": THE RUN THAT SHOWS IT,
                  "bar": "over" | "under" | "cheap", "why": ONE LINE, "open": AN ITEM OF THE BASE}],
     "careful": true | false, "careful_why": ONE LINE}

`attempt`, `tip`, `kind`, `answered`, `careful` and `careful_why` are always there, but
in the record of an attempt that got no answer at all (`failed_attempt`: `answered`
empty, each silent source with what stopped it, no finding), which may leave the careful
call out. `tip` is the `tip` that `read` printed for the attempt: a record of another
tip than the branch's now is refused, since the attempt counts the records and a review
of an earlier tip carries the same number. `careful` is the review's own reading of the
diff against each topic, and `careful_why` names the topic the change reaches, or what
was checked to say that it reaches none; `careful: true` comes with `kind: full`.
`left_out` is `[]` when `kind` is `full`: the full set is run whole. `bar` has one entry
for each file in which the change lowers the bar, and is left out otherwise. `outside`
names each defect the review saw that the base commit already has: it is no finding of
the change. `what` is the concrete run: what happens, with the input. A count in its
place is refused, and `0` reads as none. `bar` is the review's call on the defect by the
bar of rule 6 of the builder's standing rules: `over`, an item with `worth: later`;
`under`, an item with `worth: no`; `cheap`, its fix is text that does not run (a
comment, a docstring, a sentence of a document) or a finding of a check of the project
that the check's rerun shows fixed. `why` is one line, why the defect is under the bar
or why it is cheap, and an `under` or a `cheap` entry needs it: an `under` item ends
with it, `Decided against: WHY`. `open` names an item of the backlog folder at the base
that holds the same defect, from the base's items `read` lists (`backlog`, each with its
path, its `where` and its title); a path that is no file of that folder at the base is
refused. `read --record` gives each entry its number, `r`, the attempt and its place in
the record (`r2.1`), which `landing.json` keeps and `read` prints: the attempt and not
the round, since the read of a conflict's resolution carries the round of the review
before it.

A review in which a source did not answer is still a review: the record names who
answered and who did not. One in which nobody answered is none; it is started once more,
and a second such record sends the request on as not reviewed. A review is of a change,
known by the content of each file it touches, before and after: a rebase onto a base
that left those files alone does not undo it, nor does a rebase `base` made with no
conflict (above), and a change of one space does. The one addition a review still covers
is a new file in the backlog folder (`docs/backlog`, its one place), when every file the
review saw is as it saw it: that is where the defects outside the change are filed after
the review. The one deletion it still covers is of the task's own item (below). An edit
or a deletion of any other item that was there before is a change like any other. Two
rounds at most: after that the request is proposed as it is, green when the second round
left nothing open and not green otherwise. `attempt` in a record is the number `read`
printed for it, so a record that is sent twice is written down once.

No defect a review saw outside the change gets lost, and none is raised again by the
next review: each one is an item, or one line of the pull request with its reason.
`file` writes one item in the backlog folder for each `over` and each `under` defect of
a review that has none yet and whose `open` item the tip does not hold, in the item
format of `agents/lem-builder.md` (`worth: later` over the bar and `worth: no` under it,
its `where`, the day it was filed; its title; its run and where it was seen; for an
`under` one, its `why` as `Decided against: WHY`), commits the new items on the task's
branch, one commit for each round, and keeps the path of each defect's item in
`landing.json`. A defect whose `open` item the tip holds is that item, and nothing is
written for it (`open` in the output); one whose `open` item the tip lacks (the base
removed or joined it after the review, and a rebase kept the review) is filed. A defect
called over the bar whose `open` item says `worth: no` at the tip is not settled by it:
`file` writes a new item, `worth: later`, whose run is followed by the line "The same
defect as `OLD-PATH`, now over the bar." (`NOW_OVER`), and the old item stays as it is;
the new item is an added file like any other `file` writes.

Before it writes anything, `file` asks the Jev model, for each other defect that waits
for an item and whose own item is not there yet, whether it is the same defect as each
item of the backlog folder at the tip, the base's and the branch's (`check_alike`): the
defect is the state, and each item one yes-or-no question with its title, its `where`
and the first line of its body, in as many requests as jev.py's limit needs, so that
every item is asked. An item with a score at or over SAME_AT is named, three at most,
the highest first. When any defect has items named, `file` writes nothing and refuses,
with each such defect and its items; the next run says for each `--same rN.M=PATH`, that
item holds it and is kept as its `open`, or `--new rN.M`, a defect of its own, and
writes every item at once. Jev's scores are kept in `landing.json` under `alike`, by the
finding's digest and the item's path, so a second run asks nothing it asked. With no
key, no answer or `findings = false`, nothing is named and the filing goes on as without
Jev. `alike` gives the same read for one finding to a builder that files by hand (the
polish pass, the fast track's builder): the items named, or "Jev: not asked (WHY)" and
every item's path and title to read. It writes nothing and takes no lock. A second run
files nothing new. Those commits ask for no check again: `read` and `propose` take the
checks' result for a tip whose commits after the checked one only add items whose paths
`landing.json` keeps, and keep the result for that tip, so that `merge` finds what it
checks. An item written by hand is a commit like any other. `read` names the defects
that wait for an item (`to_file`), and `propose` refuses while one has none or while an
item is gone from the tip; the owner's "not wanted" is `worth: no` in the item, never
its deletion. The file name is the slug of the title. A file of that name that holds the
same defect (the same `where` and title, and its run word for word as paragraphs of the
body, whatever else the body says, such as the owner's reason for `worth: no`) is its
item, and nothing is written twice; a file that holds another takes the next name, with
a suffix from the `where`, then a number. `read` gives the reviewer the items the branch
adds to the backlog folder (`filed`: the fast track's builder or the polish pass filed
them before the review), so that a defect the branch filed already is not reported
again, and the base's items (`backlog`), so that it names in `open` the one that holds a
defect it sees. No script matches a defect to an item by its place: one place holds many
defects, and a match by place alone gives two defects one item, which loses the second.
One defect that two rounds describe in other words gets two items: an extra item costs a
merge of two items by hand, and a lost one costs the defect. The review is asked to
repeat an earlier round's words for a defect it sees again.

A task started from a backlog item lands with the item gone from its branch, so that the
merge takes it off the base and off the board. Its item is its ask: the whole of
`ask.txt`, stripped, is the path of a file of the backlog folder that the base commit
holds (`item_of_ask`), as the board's "Start a task" and the night write it; an ask with
any other word beside the path has none. `polish` prints it as `item`, and `propose`
refuses while the tip still holds it, with the `git rm` of a builder of the landing as
the next step. That commit asks for the checks again, as any commit does, since a
command of the project may read the file; it asks for no other review, since the item
holds no code (`covers_one`).

A task started from a reviewer's item, a file of `.lem/state/backlog/` that git never
holds, has the path of that file as its ask, by project.py's rule of the board's mark
and the owner's drop, with no base to find it at (`state_item_of_ask`, `backlog_item_of`
of project.py). No commit can remove it, so `forge_done`, which every path to `landed`
takes, removes the file from the main checkout's state folder before it writes `landed`,
and prints `item`, with its path and whether it was still there to remove: a file gone
already is no error. A removal that fails leaves the task `open` with the step's error,
and the next `lem land merged` tries again. A dropped task leaves the file, and the item
is undecided again.

The text of the pull request lists what was seen outside the change under four headings,
each written only when it has a line. The two lists of items come from the tip, not from
who filed them: each item the branch adds to the backlog folder (a review's, the polish
pass's, the fast track's builder's, one by hand) is a line under
`## Filed in the backlog` when its file says `worth: later` or `yes`, and under
`## Filed as not worth it`, which comes after it, when it says `no`; a line of the notes
that names such an item takes the place of the step's line, under the heading its
`worth` gives, so no item is written twice. `## Fixed on the way` holds the notes'
lines, one for each cheap defect a builder fixed in a commit of its own, a review's
entry named by its number; and `## Seen, not filed` gets one line from the record,
"`WHERE`: TITLE; cheap: WHY", for each entry whose `open` item holds it (the line names
the item) and each `cheap` entry that no line of the notes under `## Fixed on the way`
names by its number, beside the notes' own lines there. So a cheap fix that never came,
or a note that was not written, leaves its line. A lone `none` of the notes under such a
heading gives way to the record's lines. The fast track's notes have no fixed headings:
its text writes the four itself, at its end.

`propose` refuses each line of the notes that names a finding nobody filed and has
neither a bar call with its reason (`under: REASON`, `cheap: REASON`) nor the path of an
item of the backlog folder that the tip holds, whoever wrote it, and names the line
(`unfiled_lines`). The lines read are those under `## Left open` and
`## Seen, not filed`, and on the fast track the lines before the notes' first heading
too, where the should findings the review left are; a lone `none` is no finding. A line
`seen_line` writes has that form, so a line of the script always passes.

Then `propose` asks the Jev model one question about each finding called under the bar
that the tip holds, whoever wrote it (`jev_read`): each item the branch adds with
`worth: no` (its `where`, its title and its run, the body without its `Decided against:`
line) and each `under:` line of those parts of the notes (its text before the call). The
question is whether the finding is over the bar: yes means the bar's condition, read at
run time from rule 6 of the file `bar_file` names, and no its plain negation. Each
finding is asked once: its entry is kept in `landing.json` under `jev`, by the digest of
its `where`, title and run (`finding_key`), `{score, asked_at}` or `{not_asked: WHY}`,
and `start` carries it into a second landing. A score at or over JEV_OVER refuses the
step one time (`refused` in the entry), and the tip as the next run reads it is the
agent's second answer: an item made `worth: later` is no finding under the bar, an item
still `worth: no` stands with its `Decided against:` line and is refused again without
one, and a notes line stands with its reason. Each line of such a finding in the pull
request's text ends with `Jev: 0.82`, or with `Jev: not asked (WHY)`: `no key` with no
JEV_API_KEY, `no answer` for a failed request or one past JEV_SECONDS, `too long` over
jev.py's limit, `off in the settings` with `findings = false` under `[jev]` of the
team's settings, which sends nothing, and `no bar in FILE` for a rule 6 with no sentence
of the bar's form. The landing goes on in each. Jev is run as the correction hook runs
it, or as the command LEM_JEV names.

`propose` writes the text of the pull request to `pr.md` in the task's directory, from
what the steps kept, from the record of the task's decisions (`lem decisions list`) and
from the notes file, whose headings it checks. The text opens with green or not green,
in one wording for the fast track and the standard track. Green says that the checks
passed with the bar where it was, a review with at least one source left no must-fix, no
criterion changed during the build, and no decision past the personas was taken without
an answer of the owner's. A criterion changed, added or removed after the newest
approval is one line each, from its record (`lem decisions criterion`), with what it
was, what it is and why. The text lists every criterion change of the task, under every
approval; one that a later approval of the owner's took over says so and is no cause of
not green, since that approval made it the owner's. A lowered bar is not green with a
reason either: its line holds the builder's reason and what the review said of it. A
decision of the ladder that went past the personas (`by: dialectic`, `by: experts`) or
that no level settled (`unsettled`) is a line of its own: the ladder decides every
choice of the build at once, with the owner there or away, and he reads its pick here.
So are criteria approved while the task ran without him (`by: alone`) that no approval
of his followed. A decision the gate or the personas settled is no cause of not green:
its line says the gate's cite, or how many personas voted for it and in how many model
families. Nor is the owner's help on a breaker (`--by owner --breaker N`), or a
criterion change that it led to: his decision made it his. Each time the circuit breaker
stopped the build is a line before the decisions, with its cause and the decision of his
that settled it. A task that ran without the owner (his `lem project owner away`, a
night's mark) says so in the line after green or not green, with when and the words;
nothing else about it is a cause of not green. Each reason a request is not green stands
before everything else, one line each; each decision of the record is one line before
the notes. `propose` is refused while a breaker of the task waits for the owner. A plan
that calls itself careful (`careful: yes`) or has more than three tasks was talked
through by its defender and the reviewer in the plan talk's companion before any code,
and the defender wrote it down as one `plan.talk` event in the log `project.py` keeps:
`propose` refuses such a request with none, and the text's checks hold one line from the
newest, with who argued the plan with its defender, the turns (with the bound of its
rules, when the talk went over it), the positions settled and left open, and every other
count the event holds, in words where Lem knows the count (`TALK_SAYS`) and by its name
where it does not. A talk is a step before the build, so a request that is careful only
by the owner's later word, by its review or by its edit of the settings gets the full
set and no talk; it is not asked for one, and its checks say in words that it had none
and why, which is no cause of not green. A careful request says so in the line after
green or not green, with each reason, and its checks hold the call in one line, with the
newest review's call and reason beside it. A request that is not careful gets neither
line. The checks also hold one line on the personas' read of the criteria, from the
newest `criteria.read` event (`lem project log` gives its form): how many of the
personas asked answered, in which model families, who did not answer and why, how many
criteria they flagged, whether the families split, and when the owner approved them
(`lem criteria approve`), or that the build started with no wait for the owner. When the
criteria waited for the owner's yes (the newest `held` state with a line
`the criteria wait for the owner`, other than the fast track's builder's "the small
change is a full change"), the line says when the wait began and how it ended: the first
approval after it, the owner's or one made while the task ran without the owner, with
its time, and a later approval of the owner's on its own. When the criteria the read
names by their digest are not the plan's (which the checks make the expected ones), one
more line says that they changed after the read, by a later approval of the owner's or
by a change of the build, and that the change was not read; that line is no cause of not
green. A task whose scout read the code has one line that says the criteria were written
from its facts. The text names no file of the task directory: the pull request is read
on the forge, where no path of this machine leads anywhere. A request of the type fix
whose investigation found its cause has one more line with that cause and its place,
from the newest `investigation` event; a question's has none. On either track the checks
hold one line for each seat that stood in for another (each `seat.stand-in` of the task,
with no filter, `stand_in_line`): which seat stood in, for which seat, and why, in the
words of `lem_state.SEAT_ERRORS`; one whose own seat then gave an error too says so. It
is a fact of the request and no cause of not green. `propose` refuses a task on the
standard track with no `criteria.read`, unless the owner skipped the read: that word of
the owner's, which Lem asks for only when every criterion names only the developer, is a
decision of the owner's with the two texts of `READ_SKIP`, and it counts only with a
later approval of the owner's, both before the first state that names a lead. A word or
an approval after a lead started belongs to the standard track from a complete request,
where the read always runs, and is refused. Then the checks say "the criteria: not read
by the personas, on the owner's word (DATE); the owner approved them", which is no cause
of not green, since the decision was the owner's. It also refuses one whose newest read
flagged a criterion or showed a split between the families with no approval of the
owner's at or after it; the lead's freeze of a read (`lem criteria approve --read`) is
no approval of the owner's. A complete request that someone else wrote (the line
`request by: someone else` in the task's brief or in a block of its state) needs that
approval after the newest read even when nobody was confused, since nobody at the
terminal read the request. In both cases an approval made while the task ran without the
owner (`approve --alone`, `by: alone`) at or after the read lets it be proposed, not
green. A read in which nobody answered is written down too: `propose` refuses while the
newest one is the first such read in a row, so that the read is started once more, and
after the second in a row the request is not green, with "the criteria were not read"
first, and its checks say so in place of the read's line. A change the review calls
careful and the plan did not is a lesson about the plan's call: `read --record` writes
one `careful.missed` event with the round and the review's reason, the first time a
review finds it, for the retro. `propose` pushes the task's branch and opens the pull
request on GitHub with the `gh` command; a second run updates it. The `proposed` event
is written after that step: a proposal that the push or GitHub refused is none. A
repository whose origin is not on GitHub, or that has none, is refused before anything
is written, with the line that points origin at GitHub: a GitHub pull request is the one
way a task lands.

The merge agent reads every proposed task, the fast track's too, after `propose`.
`merge-review` with no record fetches the base and writes its brief,
`merge-brief-TIP-BASE.md` in the task directory, named by the proposed tip and the base
it reads against, so that the brief of a later base never takes the place of the one an
agent was started with: the line that names `prompts/merge.md`, and the facts as JSON
(the pull request, the range, the files of the task directory there are, the reviews,
green or why not, why careful, `branch.land`, `owner_merges`, the reason the owner
merges whatever the agent finds, or null, `time`, the task's seconds from its first
event to its first proposal against the median of the earlier tasks of its track in the
event log, `base`, and `moved`). `moved` is null when no file changed on origin's base
since the base the checks ran on; otherwise it holds that base (`checks_ran_on`), the
base now (`base_now`), the `range` between them, each `commits` entry (short id and
subject), the `files` they changed, and the `overlap`, those of them the task's change
touches too: always from the checks' base, never from an earlier read, so a read sees
every move since the checks. `base` is origin's base when `moved` is not null, and the
checks' base otherwise. It prints the brief, the answer file the agent's reply goes to
(`merge-answer-TIP-BASE.md`), the tip, the base, and the seat that starts it, the one
`lem project seat SLUG merger` gives (the fallback while it stands in for the merger,
else `seats.merger`), which it keeps with the brief in `landing.json` (`merge_seats`, by
the brief's tip and base). After `lem project seat-failed SLUG merger` printed a
stand-in, `merge-review` runs again: the brief of the same tip and base is written
again, and the stand-in's seat takes the failed one's place beside it. The agent changes
nothing. Its reply opens with its verdict, `Verdict: merge.` or `Verdict: call.`; on a
moved base its second line is its call on the move, `Base: safe.` or
`Base: another round.`, then one sentence of why. `merge-review --file FILE --tip TIP
--base BASE` takes the tip and the base the brief named: an answer of another tip than
the one proposed, or of a base no brief named, is refused, and the read covers BASE,
never the base at the time of the record. A reply with no verdict, or with no base call
on a moved base, is refused, and the agent is asked again; on a moved base the second
such reply of one brief is recorded as another round, with that reason as its why, so
that the checks decide and the owner is not asked; on a base that did not move the
second reply of one brief with no verdict is recorded as a review that calls the owner,
with no verdict and a why that names the verdict a lower line of it gives, if any
(`unread_next`, `unread_why`). It writes the reply as `merge-review.md`, keeps
`merge_review` in `landing.json` (the proposed tip, the verdict, `calls`, `why`, the
seat kept with its brief as `by`, never a new read of the settings, so it names the seat
that read, the time as `at`, the `base` the read covered, and its `base_call` and
`base_why`, null with no move) and logs one `merge.review` with the same for each read,
so the log keeps the why of every base call. `calls` is true for the verdict `call`, for
a `merge` that `owner_merges` overrules, and for that second reply with no verdict: the
owner is called, and "Waits for you" shows "Read the merge review". A review of an
earlier tip counts for nothing, unless `propose` carried it onto the tip after a new
landing (below). The facts hold `relands` too, how many times the proposal landed again,
`pictures`, the PNG, JPEG, GIF and WebP files of the task's `media/` folder by their
paths from the task directory, which the builders took and a review of a change to what
a person sees links, `try`, the worktree's folder from the main checkout and
`gh pr checkout N`, which a review that calls the owner ends with, `filed`, each item
the branch adds to the backlog folder by its path and title, whoever filed it, and
`bar`, the file whose rule 6 holds the bar of an item as `spawn-builder` picks the
builder: the project's own `.claude/agents/lem-builder.md` in the main checkout by its
whole path when it is there (`of`: `project`), else `agents/lem-builder.md` in Lem's
plugin folder (`of`: `lem`). The agent calls the owner for an item under that bar. The
facts hold `stand_ins` as well, each seat that stood in for another in the task
(`stand_ins_of`), a fact of the request and no reason to call him. A merge agent's
stand-in comes after the pull request is open: before the read is written down, `--file`
adds the stand-in's line to the pull request's text on GitHub once, and to `pr.md`.

A read with `Base: safe.` answers Lem's own refusal of a merge of its tip because the
base moved (`merge_refused` with `kind: base`), and so does a read whose brief named the
checks' own base, since origin's base had the checks' tree again (a revert) when it was
written: the record clears it, so that `landing.json`, `lem project waiting` and the
board agree, and when that refused merge was the owner's (`owner_tap` of the tip) it
logs `merge.stands`, so that the board's server runs his merge with `--standing` and he
is not asked again. No read answers any other refusal (GitHub's, a rule's, a tip's). A
read with `Base: another round.` merges nothing: it keeps a refusal of kind `base` for
its tip (`merge_refused` and a `merge.refused` event, with the read's why) and the tip
as `another_round`, so that the server wakes the session and the board says that it
lands again; the task lands again with no question to the owner. Only that new landing
answers such a refusal: `merge-review` refuses a brief or an answer of a tip whose read
said another round.

`merged` asks GitHub about a pull request the owner may have merged or closed there, of
an `open` task, or of one its merge agent's seat blocked
(`the seat that failed: merger`), whose pull request stays open while it waits for the
owner's go on. A merged one finishes as a landing does. A closed one with no merge ends
the task: its state becomes `dropped` with the line "the pull request was closed on the
forge", so nothing of it waits and nobody cleans it by hand; `clean` then removes the
worktree, and the branch keeps its commits, with how to delete it. A task that goes on
after all is a new request. One that is still open is "not merged yet" (exit 1), and
`merged` keeps what the forge said of it, its mergeable state on its head (`forge` in
`landing.json`), so that `lem project waiting` says whether it conflicts with the base.

`merge` is the one route to the base branch, the owner's and the merge agent's alike:
`merge --by owner` is his word (the board's merge and his `/lem land` run it), and
`merge --by merger` is the merge agent's, after its review, which the board's server
runs (`--via server`) once `merge-review` kept the verdict `merge` with no call: the
agent only writes its review, and no session is told to run it. Both run under the merge
lock and read the base after they take it, and `merge.start` says who merges (`by`) and
who ran the call (`via`, `session` unless the server says `server`), as `merged_by` in
`landing.json` does after a merge. `--by merger` is refused where the settings'
`branch.land` is `owner`, for a careful request, for one that is not green (one that is
not reviewed among them), for one whose newest review that answered made no careful
call, and with no merge review of the proposed tip whose verdict is `merge`. A task that
ran without the owner is merged as any other. The pull request is merged through GitHub,
so its own rules hold: a merge GitHub refuses keeps its line as `merge_refused` in
`landing.json` (`from: github`) and a `merge.refused` event, for the row that waits for
the owner, and the step exits 1 with that line. `merged` is for one the owner merged on
GitHub. What lands is the tree the checks passed on: when the tip is another tree,
`merge` refuses and says which steps run again. When the base moved by any file after
the checks ran (`changed` from the base the checks ran on to the base now: every file,
not only those the checks read), it merges only when the base now has the same tree as
the base a read of the proposed tip with `Base: safe.` covered, and no read of that tip
said another round; otherwise it refuses, and the refusal names the merge agent's read
of what moved as the next step, or a new landing after another round. A read of one base
covers no later one. Such a merge leaves its record in git, and only once GitHub took
it: its line names the base the checks ran on, the base it merged on and the merge
agent's sentence of why; with `branch.history = "squash"` it is in the body of the merge
commit, in the same `gh pr merge` call, and `forge_done`, which every path to `landed`
takes (`merge`, and `merged`), adds it to the pull request's text (`gh pr edit`, and
`pr.md`) and to the landed state when the text lacks it. A failed edit leaves the task
`open` with the step's error, and the next `merged` tries again. `forge_done` also reads
the merged commit's parent on the base: when its tree is not the tree the read covered
(a merge on GitHub outside Lem came between Lem's fetch and its merge call, which no
flag of `gh pr merge` can bind), the line names the base it really merged on and says
that no read covered it, and the step prints it as `uncovered`, for the owner. A merge
on the base the checks ran on writes no such line, and a merge GitHub refuses writes
none anywhere. With `branch.history = "squash"` the body of the merge commit holds each
line of `pr.md` under `## Fixed on the way` first, so the base's history names each fix
made outside the task, then that line when there is one, and ends with the line
`Lem task: SLUG`, by which the board names the task of an item of the
backlog (`squash_body`).

A refusal by Lem's own rules under the lock (`Refusal`, with its `kind`: `rule` for one
of the merge agent's rules, `tip` for a tip or a head that is not the one proposed and
checked, `base` for the moved base) keeps its line the same way, with `from: lem` and
the `kind`, for every refusal of the merge agent's merge and for the owner's when the
base moved (`kept_refusal`): the server tries that tip no more and wakes the task's
session with `lem: SLUG refused`. A git or `gh` call that failed is no refusal of the
tip and is not kept; the next try runs it again. After a base refusal a fresh merge
agent reads what moved; after a read that said another round the session lands the task
again. One rule says what a new landing's proposal carries of what was said of the tip
proposed before (`moved_carry`), and it runs before the pull request's text is written.
The tip carries when it is the same, when a rebase with no conflict made it and kept the
review (`rebase_carried`, from the tip before the rebase to the one after it), and when
it is the tip of a builder's resolution whose one read found nothing, on a request that
no call makes careful (above), with no commit after the rebase or the resolution other
than the backlog items `file` commits, which move the tip the record names (`filed_on`).
Then each act has its own last fact. `propose` carries the merge agent's review of the
earlier tip onto the new one when one with a verdict is on record, with its call of the
owner as the rules say now and with no call on a moved base, since the new landing's
checks ran on the new base, and logs it as a `merge.review` with `carried`, so that the
server merges it with no second read. The owner's merge that the base refused
(`owner_tap`) stands while the tip carries and the reasons the request is not green are
the ones he saw: `propose` logs `merge.stands`, and the server runs `merge --by owner
--via server --standing`, which `merge.start` and `merged_by` record as made
`after: a re-check`. Otherwise the merge review does not carry (`"merge_review": null`,
with `merge_review_why`, and a fresh merge agent reads the task) and the owner's merge
ends (`owner_merge`, and a `merge.ended` event with `why`, which the board shows), each
with the rule's reason: a commit after the rebase or the resolution, a base that moved
again after the resolution, a read of the resolution with a finding, or one that did not
answer or did not run, a careful request, a review that does not cover the change (the
review's reason, which the rebase kept, `rebase_uncovered`); for the merge review alone,
no merge review of the earlier tip on record, and for the owner's merge alone, reasons
for not green that are not the ones he saw. The pull request's text and the `proposed`
event (`review`, `merge_review`, `why`, `owner_merge`, `owner_why`) say what carried
("the merge review carried over the resolved conflict: the resolution read found
nothing", or "a fresh merge agent reads it: REASON"). A merge on a moved base that a
read covered is recorded in `merge.start` and `merged_by` as made
`after: a read of the moved base`, with the `base` it read.

A step that was cut off is run again; a merge that GitHub already holds only finishes
the bookkeeping. `clean` knows the branch from `landing.json`, so it finds it after the
worktree is gone. It takes a landed, a dropped or an answered task. The branch of the
last two goes when the base holds it whole, and stays when it has commits of its own,
with what it holds and how to delete it. A landed task's branch goes when the base holds
its tip, when its tip is the head the forge merged, or when it holds by content the
change of that head, which Lem pushed last and the landing rebased after (`rebased` in
clean's output); a branch changed after that push stays, the forge's copy goes, and
`branch_left` names the commit or the files that changed. `landing.json`, `pr.md`,
`merge-review.md` and each item of the backlog are written whole, through a new file
that takes the old one's place, so that a run cut off in the middle leaves no half
of one.

After a merge the checkout that holds the base branch is fast-forwarded when it is
clean, and left alone with a note when it is not. The base branch is never pushed to and
a ref is never moved behind a checkout's back. The task's own branch on GitHub is the
one ref pushed with force, and with a lease that names the commit the push may replace:
the one Lem pushed last (`pushed` in `landing.json`), or a head of origin's whose
commits the branch took in (`taken`), or no branch at all for a first push. Origin is
asked with `ls-remote` before `base` rebases and before `propose` pushes, never through
the remote-tracking branch, which any plain fetch moves: a commit there that Lem did not
push and the branch does not hold (a teammate's suggestion) stops the step with each
such commit named, and the way on is to pull it into the task's worktree, after which it
is part of the change, with its checks and a read. A pull request on the task's branch
name is taken as the task's own only when its head is the commit Lem pushed; any other
is somebody's, and `propose` refuses with its number and author.
"""  # noqa: E501 - the usage table of `--help` and the form of a review keep their columns

import sys

if sys.version_info < (3, 11):
    # an old python3 must still load this file, so that it can say what it needs and not
    # a traceback
    sys.exit(
        "land.py: Lem needs Python 3.11 or newer, and this python3 is "
        f"{sys.version.split()[0]}; put a newer one first on PATH, "
        "or run this file with it"
    )

import argparse
import contextlib
import fcntl
import hashlib
import importlib
import json
import os
import re
import shutil
import signal
import statistics
import subprocess
import tempfile
import time
import tomllib
from collections.abc import Callable, Generator, Iterator
from datetime import UTC, date, datetime
from pathlib import Path
from types import ModuleType
from typing import Any, TextIO, cast

SCRIPTS = Path(__file__).resolve().parent
# How this script calls a sibling: in this process, as one command of it.
sys.dont_write_bytecode = True
sys.path.insert(0, str(SCRIPTS))
import lem_clock  # noqa: E402
import lem_files  # noqa: E402
import lem_proc  # noqa: E402
import lem_sibling  # noqa: E402
import lem_state  # noqa: E402
import lem_tokens  # noqa: E402

# The release a task began on, and the rule that stops a command for a task two
# releases back.
lem_release = importlib.import_module("lem_release")
# A file written whole or not at all, under `NAME.PID.new` first, in a folder that is
# there (`lem_files`); lem-land-guards.sh calls it by this name.
write_whole = lem_files.write_whole

# Who merges: the owner's word, or the merge agent, where the settings and the request
# allow it.
BY = ("owner", "merger")
# A GitHub remote, as the repository writes its address: a task ends as a pull
# request there.
GITHUB = re.compile(r"(https://|ssh://git@|git@)github\.com[:/]")
# The merge agent's verdict, the first line of its review: it merges, or it calls
# the owner.
VERDICT = re.compile(r"Verdict:\s*(merge|call)\b", re.IGNORECASE)
# The merge agent's call on a base that moved after the checks ran, the second line of
# its review: the move is safe for the change as it is, or the change needs another
# round of the checks; then one sentence of why, which the pull request and the merge
# commit carry.
BASE_CALL = re.compile(
    r"Base:\s*(safe|another round)\b[.:;,]?\**\s*(.*)", re.IGNORECASE
)
# What `merged_by` and `merge.start` say of a merge on a base that moved after the
# checks, which a read of the merge agent's covered.
READ_AFTER = "a read of the moved base"
# What `merge.stands` says of the owner's merge after a read whose brief named the
# checks' own base, since origin's base had the checks' tree again (a revert) after Lem
# refused his merge for a move.
READ_BACK = "a read of the base back on the checks' tree"
# The review a change gets, from the least to the most: one read by one agent, a round
# of the project's review tool with the profiles that fit the change, the project's
# full set.
KINDS = ("read", "round", "full")
KIND_SAYS = {
    "read": "one read",
    "round": "a review round with the profiles that fit",
    "full": "the project's full set",
}
# The line Lem writes into a task's brief when the owner says that the task is careful.
OVERRULED = "careful: the owner says so"
# The line of a task's brief, or of a block of its state, that says someone else wrote
# its complete request.
SOMEONE_ELSE = "request by: someone else"
# The state line `start` writes when the project has no command of its checks; a task
# blocked with it is the one `start` takes back once the commands are there.
NO_GATE = "the project has no command in its checks"
# The line `lem project state SLUG ready --start-over` writes in its block (`START_OVER`
# there, a copy, since a stand-in may take project.py's place): `start` starts the
# landing over with nothing carried.
START_OVER = "the landing starts over"
# The steps that take a tip from the start to a proposal, which a refusal of `land`
# names when the tip, the base or the tree is not the one on record.
AGAIN = (
    "run `lem land start`, `lem land base`, `lem land checks`, `lem land read` and "
    "`lem land propose` again (a rebase with no conflict keeps the review)"
)
# How many changed lines one reader takes as one piece; a larger change is read task by
# task, in the plan's own cuts. A guess (2026-11-15), not a measurement.
READ_AT = 800
# A plan of more tasks than this is large: it gets a round at the least, and a plan talk
# before any code. The three-touches plan's own line (2026-11-15), not a measurement.
LARGE_AFTER = 3
# A review that no source answered is started once more; after this many in a row that
# nobody answered, the request goes on to the owner as not reviewed (`stages/land.md`,
# step 5).
SILENT_REVIEWS = 2
# The rounds of review a change gets: what the last of them leaves open goes to the
# owner (`stages/land.md`, step 5).
ROUNDS = 2
# The personas' reads of the criteria in a row that nobody answered after which the
# request is proposed as not green (`stages/interview.md`, step 5; `stages/land.md`,
# step 6).
SILENT_READS = 2
# The commits of origin's copy of a branch that a refusal names one by one; it counts
# the rest. The length of the text, not a measurement.
NAMED_COMMITS = 10
# The plan's own call whether the task is careful, as `stages/plan.md` step 2 has the
# lead write it: one line under the plan's title, before its first `##` heading. A line
# further down is no call: the plan talk's record or a fenced block may quote one.
PLAN_CALL = re.compile(r"(?mi)^careful:\s*(yes|no)\b")
# Lem's own settings: what must never go wrong, what the checks run, who merges, where a
# task lands. Any edit of the file is careful by this script, not by a judgment: the
# file is Lem's, a task rarely edits it, and every table of it guards something for
# every later task (audit A1, 2026-11-17: a branch that set `branch.land` to "agent" got
# one read and a green pull request).
SETTINGS_FILE = ".lem/settings.toml"
# One machine's own settings for the repository (`[seats]`, `[naps]` and `[state]`,
# project.py's LOCAL_TABLES), untracked by design and read from the main checkout. A
# branch that commits it, or changes or removes a tracked copy, is careful by this
# script too: a green request and an agent's merge would make one machine's choices
# every machine's (audit N5, 2026-11-17: a branch that committed it with `git add -f`
# got both).
LOCAL_SETTINGS_FILE = ".lem/settings.local.toml"
# What a decision of the build did to its criterion, as a line of the pull request
# says it.
CHANGE_HOW = {"changed": "changed", "added": "was added", "removed": "was removed"}
# The form of the one event that records the personas' read of a task's criteria.
READ_FORM = (
    "`by=lem|lead asked:=N answered:=N families:='[...]' silent:='[...]' criteria:=N "
    "flagged:=N split:=true|false digest=DIGEST`"
)
# The owner's word that the personas do not read the criteria, which Lem asks for only
# when every criterion names only the developer (`stages/interview.md`, step 5): one
# decision of his that `decisions.py log --by owner` writes, known by these two texts
# word for word.
READ_SKIP = {
    "what": "the personas' read of the criteria",
    "chose": "no read: the criteria name only the developer",
}
# The state line of a task whose criteria wait for the owner's yes, as `project.py`
# writes it (`CRITERIA_WAIT` there), and the one such line that is no wait for his yes:
# the fast track's builder found a full change, and that task goes to an interview
# (`FAST_GREW` there). Copies, since a stand-in may take project.py's
# place (`project_now`).
CRITERIA_WAIT = "the criteria wait for the owner"
FAST_GREW = re.compile(r"\bthe small change is a full change$")
# The approvals that end such a wait: the owner's, or one made while the task ran
# without him.
WAIT_ENDS = ("owner", "alone")
# The held line a change of the criteria from the owner's note ends with (criteria.py's
# CHANGED_WAIT, the last write of `lem criteria change`, which a retry after a stop
# never writes twice).
CHANGED_WAIT = "the criteria wait for the owner: changed from the owner's note"
# How many model families read the criteria, in the words of the pull request.
FAMILIES = {1: "one model family", 2: "two model families"}
# The form of the one event that records a plan talk, as `talk_form` in `project.py`
# checks it.
TALK_FORM = (
    "reviewer=AGENT turns:=N questions:=N settled:=N open:=N repaired:=N design:=N "
    "unargued:=N root:=N layer:=N shared:=N"
)
# The counts of a plan talk after its turns and positions, in the words of the pull
# request, one form for one and one for more. A count the event holds and this table
# does not is shown by its name.
TALK_SAYS = {
    "questions": (
        "question in the reviewer's first list",
        "questions in the reviewer's first list",
    ),
    "repaired": ("repaired by the defender", "repaired by the defender"),
    "design": ("of the open ones a design choice", "of the open ones a design choice"),
    "unargued": (
        "raised after the list and not argued",
        "raised after the list and not argued",
    ),
    "root": ("repaired at the cause", "repaired at the cause"),
    "layer": ("layer over a cited decision", "layers over a cited decision"),
    "shared": ("decision two questions named", "decisions two questions named"),
}
# What every event has and the talk's line says first, so it is no count after the
# positions; and the bound of turns its rules give, which `project.py log` adds and the
# line names only when the talk went over it.
TALK_FIRST = ("ts", "event", "task", "reviewer", "turns", "settled", "open", "bound")
# Who took a decision of the record, as the text of a pull request names them.
TAKEN_BY = {
    "lead": "the lead",
    "gate": "the gate",
    "personas": "the personas",
    "dialectic": "the dialectic",
    "owner": "the owner",
    "lem": "Lem",
    "experts": "the experts",
}
# The two causes of the circuit breaker, as a line of the pull request says them
# (`decisions.py` CAUSES).
BREAKER_SAYS = {
    "irreversible": "the next step could not be reversed by a later no",
    "criteria": "no option of the ladder kept the approved criteria",
}
# The levels of the ladder whose decision, taken without the owner, is never green: past
# the personas.
PAST_PERSONAS = ("dialectic", "experts")
# The name of each track, by the word of the `Size:` line that the criteria keep.
TRACKS = {"small": "fast", "full": "standard"}
# The first line of a green pull request, one wording for the fast track and the
# standard track.
GREEN = (
    "**Green.** The checks passed with the bar where it was, the review left no "
    "must-fix, no criterion changed, and no decision past the personas was "
    "taken without an answer."
)
# What a review names of each defect it saw outside the change.
DEFECT = ("where", "title", "what")
# The review's call on such a defect, by the bar of rule 6 of the builder's standing
# rules: over the bar (an item with `worth: later`), under it (an item with
# `worth: no`), or cheap (its fix is text that does not run, or a finding of a check of
# the project that the check's rerun shows fixed).
BARS = ("over", "under", "cheap")
# The calls that make an item, each with the `worth` of the item `file` writes for it.
FILED_BARS = {"over": "later", "under": "no"}
# The headings of the pull request's text for what was seen outside the change, after
# the notes' `## Filed in the backlog`, in this order.
NOT_WORTH = "## Filed as not worth it"
FIXED = "## Fixed on the way"
SEEN = "## Seen, not filed"
# The bar call of a line of the notes that names a finding nobody filed: `under: REASON`
# or `cheap: REASON`, anywhere in the line.
CALLED = re.compile(r"(?i)(?<![\w-])(under|cheap):[ \t]*\S")
# The call of a line of the notes under the bar, where its reason starts: the text
# before it is the finding Jev reads (`line_finding`).
UNDER = re.compile(r"(?i)(?<![\w-])under:[ \t]*(?=\S)")
# The parts of the notes whose lines name a finding nobody filed, on both tracks; the
# fast track's lines before the first heading are such lines too (`called_bodies`).
LEFT_OPEN = "## Left open"
# Jev's one read of each finding an agent called under the bar (`jev_read`). JEV_OVER is
# the score at or over which `propose` refuses once: the starting value of Jev's
# documentation, which the jev-specialist named ("start at 0.7, Jev's docs' starting
# value, a guess until measured", jev-advice.md of task backlog-refuted-items-and-jev,
# 2026-11-23); a guess, not measured on findings, of which no labeled sample exists.
JEV_OVER = 0.7
# The seconds one request to Jev may take before it is "no answer": shorter than
# jev.py's 120, since the read only adds a line and a landing should not wait for it. A
# guess (2026-11-23), not a measurement.
JEV_SECONDS = 20
# jev.py's exit status for a request too long to send
JEV_TOO_LONG = 3
# The name of the one question of a finding's request.
JEV_QUESTION = "over"
# The sentence of the bar in rule 6 of the builder's standing rules: its condition,
# after the colon.
BAR_SENTENCE = re.compile(r"filed only for a defect over the bar:\s*(.+?)\.(?=\s|$)")
# The end of a line of the pull request that holds Jev's read of its
# finding (`jev_said`).
JEV_SAID = re.compile(r"Jev: (\d\.\d\d|not asked \([^)]*\))$")
# Jev's read of whether a finding is the same defect as an item of the backlog
# (`alike`). SAME_AT is the score at or over which an item is named to the agent: a
# guess (2026-11-23), so that a weak match never reaches the agent's three, not measured
# on findings, of which no labeled sample exists.
SAME_AT = 0.5
# The most items `alike` names for one finding: the agent reads each (criterion 8 of
# task backlog-refuted-items-and-jev, 2026-11-23).
ALIKE_MOST = 3
# The paragraph of an item filed over the bar for a defect whose open item says
# `worth: no` at the tip: the old item stays as it is, and the new one names it
# (decision 10 of task backlog-refuted-items-and-jev).
NOW_OVER = "The same defect as `{}`, now over the bar."
# The longest file name an item of the backlog gets from its title, before `.md`. A
# guess (2026-11-16), not a measurement: long enough for a title of a dozen words.
SLUG_AT = 80
# The headings the notes of a pull request hold, in this order: what only the one who
# read the task's report can say.
FILED = "## Filed in the backlog"
NOTES = ("## Decisions", "## Left open", "## Worth a look", FILED, "## Not done")
# A document may quote a mark of the bar, the plan's own reason for one too: no mark is
# looked for in these.
DOCS = (".md", ".rst", ".adoc")
# The marks by which a change lowers the bar, for the languages whose tools read them.
# Chosen by the session that built this check (2026-11-15) from those tools' own syntax,
# and the focus marks of JavaScript's runners (`.only`, `fit`, `fdescribe`), which run
# one test alone and so leave the others out, after an audit of the bar (2026-11-17);
# not measured. A mark that a call's "(" follows is looked for with that "(" and named
# without it, so a refusal says `it.only`, never `it.only(`. The marks of a test that
# runs again until it passes came after a probe of the bar passed eight ways of
# weakening a test unseen (audit T-F2, 2026-11-17).
BAR = {
    (".py",): (
        r"#\s*noqa",
        r"#\s*type:\s*ignore",
        r"#\s*pyright:\s*ignore",
        r"#\s*pylint:\s*disable",
        r"#\s*nosec",
        r"\bpytest\.mark\.(skip|xfail)",
        r"\bunittest\.skip",
        r"\bpytest\.skip(?=\()",
        r"\bpytest\.mark\.(flaky|retry)\b",
        r"^\s*@flaky\b",
    ),
    (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"): (
        r"eslint-disable",
        r"@ts-ignore",
        r"@ts-expect-error",
        r"@ts-nocheck",
        r"\b(it|test|describe)\.(skip|todo|only)(?=\()",
        r"\bx(it|test|describe)(?=\()",
        r"\bf(it|describe)(?=\()",
        r"\bjest\.retryTimes(?=\()",
        r"\bthis\.retries(?=\()",
    ),
    (".go",): (r"//\s*nolint", r"\bt\.Skip(f|Now)?(?=\()"),
    (".rs",): (r"#!?\[allow\(", r"#\[ignore\b"),
    (".java", ".kt"): (r"@Disabled", r"@Ignore", r"@SuppressWarnings"),
    (".sh", ".bash"): (r"#\s*shellcheck\s+disable",),
}
# The settings files of a test runner or of coverage, by name: their marks leave tests
# out, or run a failing test again until it passes, for the whole suite at once.
TEST_CONFIG = re.compile(
    r"(^|/)(pyproject\.toml|setup\.cfg|pytest\.ini|tox\.ini|package\.json|\.coveragerc|\.nycrc(\.json|\.ya?ml)?|(jest|vitest)\.config\.[A-Za-z0-9.]+)$"
)
TEST_CONFIG_MARKS = (
    r"--deselect\b",
    r"-k[\s=]+[\"']?not\b",
    r"--ignore(-glob)?\b",
    r"\btestPathIgnorePatterns\b",
    r"(--)?\breruns\b",
    r"\bretries\b",
    r"\bretryTimes\b",
    r"\bflaky\b",
)
# A coverage threshold, as a runner's settings or a command line write it: its name and
# its number. The bar is lower when a number of one name went down, or the name is gone,
# anywhere in those files.
THRESHOLD = re.compile(
    r"(fail_under|fail-under|cov-fail-under)[\s\"']*[=:\s][\s\"']*([0-9]+(?:\.[0-9]+)?)|[\"']?\b(lines|branches|functions|statements)[\"']?\s*:\s*([0-9]+(?:\.[0-9]+)?)"
)
# The forge's workflows: a coverage threshold on a command line there counts, and an
# edit of one is an edit of a test configuration.
WORKFLOW = re.compile(r"(^|/)\.github/workflows/[^/]+\.ya?ml$")
# A file a test compares its output with, written once and read by the test.
SNAPSHOT = re.compile(r"(^|/)__snapshots__/|\.snap$|\.ambr$|\.approved\.[A-Za-z0-9]+$")
# Files that are neither code nor documentation: no language's marks apply, and none
# is missed.
DATA = (
    ".txt",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
    ".lock",
    ".cfg",
    ".ini",
    ".csv",
    ".tsv",
    ".svg",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".html",
    ".css",
    ".xml",
    "",
)
# An assertion, as far as a line shows one: the word a test framework uses for it.
ASSERTS = re.compile(r"\b(assert|expect)", re.IGNORECASE)
# A test file, by its place or its name.
TEST_FILE = re.compile(
    r"(^|/)(tests?|spec|specs|__tests__)/|(^|/)test_[^/]*$|_test\.[A-Za-z0-9]+$|\.(test|spec)\.[A-Za-z0-9]+$"
)
# The languages that keep unit tests in the module they test: there every file's
# assertions count.
INLINE_TESTS = (".rs",)


class LandError(Exception):
    pass


class ForgeSaid(LandError):
    """What GitHub said of a merge Lem asked for: its refusal, whose line `merge_locked`
    has kept already, or a merge it took and has not made yet, which is no refusal."""


class Refusal(LandError):
    """A merge that one of Lem's own rules refuses, with the rule's kind (`REFUSALS`).
    Only such a refusal is kept for the tip (`cmd_merge`): a git or `gh` call that
    failed is no word on the tip, and the next try runs it again."""

    def __init__(self, kind: str, said: str) -> None:
        super().__init__(said)
        self.kind = kind


# The kinds of a merge that Lem's rules refuse: one of the merge agent's rules
# (`merger_refusal`), a tip that is not the one proposed and checked (or a pull request
# whose base on GitHub is not the task's), and a base that moved after the checks ran.
REFUSALS = ("rule", "tip", "base")


def run(
    args: list[str], cwd: Path | None = None, *, check: bool = True
) -> subprocess.CompletedProcess:
    ran = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)
    if check and ran.returncode != 0:
        raise LandError(
            f"{' '.join(args[:4])} failed: {(ran.stderr or ran.stdout).strip()}"
        )
    return ran


def git(where: Path, *args: str, check: bool = True) -> str:
    ran = lem_state.run_git(where, list(args))
    if check and ran.returncode != 0:
        # the refusal of `run`, of the same command
        raise LandError(
            f"{' '.join(ran.args[:4])} failed: {(ran.stderr or ran.stdout).strip()}"
        )
    return ran.stdout.strip()


def script(
    name: str, repo: Path, *args: str, check: bool = True
) -> subprocess.CompletedProcess:
    """One command of a sibling script, so this one reads a repository the way every
    stage does."""
    return lem_sibling.checked(
        SCRIPTS / name, repo, *args, error=LandError, check=check
    )


def project_now(repo: Path) -> tuple[dict, list[dict], Path]:
    """What a landing reads of the repository before its step: the main checkout's
    settings, every task as the state files say now, and the state folder. Refused
    before anything else: settings that do not read, no settings file, and what
    `may-land` refuses (a protected branch, a missing base, a wrong target). The
    settings are loaded once and handed to the functions of `project.py` that need them;
    nothing git answered is kept past this one call."""
    path = SCRIPTS / "project.py"
    if not lem_sibling.in_form(path):
        # a stand-in in project.py's place (a test's copy of the scripts) answers each
        # command as a process
        settings = json.loads(script("project.py", repo, "show").stdout)
        if Path(settings["root"]).resolve() != Path(settings["main"]).resolve():
            settings = json.loads(
                script("project.py", Path(settings["main"]), "show").stdout
            )
        if settings["settings"] is None:
            raise LandError(
                "this repository has no .lem/settings.toml; `/lem init` writes it"
            )
        script("project.py", repo, "may-land", str(settings["branch"]["base"]))
        return (
            settings,
            json.loads(script("project.py", repo, "tasks").stdout),
            Path(script("project.py", repo, "state-dir").stdout.strip()),
        )
    project = lem_sibling.module(path)
    try:
        root = project.repo_root(repo)
        here = project.load(root)
        settings = here
        if root.resolve() != Path(here["main"]).resolve():
            # Run from a task's worktree, the landing still reads the main checkout's
            # settings: the branch it lands does not get to choose its checks or what is
            # careful. The worktree's own load stays, for what only it answers: it
            # refuses a branch whose settings do not read, and `may-land` and the tasks'
            # tracker read the branch's tables there, as their commands do.
            settings = project.load(Path(here["main"]))
        if settings["settings"] is None:
            raise LandError(
                "this repository has no .lem/settings.toml; `/lem init` writes it"
            )
        project.may_land(here, str(settings["branch"]["base"]))
        return settings, project.read_tasks(root, here), project.state_root(root)
    except project.SettingsError as error:
        raise LandError(str(error)) from error


class Task:
    """One task as the landing needs it: its settings, its worktree, its branch and what
    it kept."""

    def __init__(self, repo: Path, slug: str) -> None:
        self.settings, tasks, state = project_now(repo)
        self.slug = slug
        self.base = self.settings["branch"]["base"]
        self.repo = repo
        self.read_states(tasks)
        # the main checkout's state folder, as `project.state_root` gives it, also from
        # a task's worktree
        self.state_folder = state
        self.directory = state / "tasks" / slug
        # -z: a NUL ends each field and an empty field ends each worktree, so a path
        # with a line break stays whole
        listed = run(
            ["git", "-C", str(repo), "worktree", "list", "--porcelain", "-z"]
        ).stdout
        entries = [
            block.split("\0") for block in listed.split("\0\0") if block.strip("\0")
        ]
        self.main = Path(self.settings["main"])
        relative = Path(self.settings["places"]["worktrees"]["path"]).relative_to(
            Path(self.settings["root"]).resolve()
        )
        self.worktree = self.main / relative / slug
        # the checkout that holds the base branch, when one does
        self.base_checkout = next(
            (
                Path(entry[0].removeprefix("worktree "))
                for entry in entries
                if f"branch refs/heads/{self.base}" in entry
            ),
            None,
        )
        self.remote = git(self.main, "remote", "get-url", "origin", check=False) != ""
        self.onto = f"origin/{self.base}" if self.remote else str(self.base)
        self.kept_file = self.directory / "landing.json"
        self.recorded: list[dict] | None = None
        self.criteria: dict | None = None
        self.plan_said: bool | None = None
        self.branch_gate: list[str] | None = None
        # The address as the repository has it, before any rewrite of it: the forge is
        # known by its host. A task ends as a GitHub pull request, the one way Lem
        # lands; `propose` refuses another remote.
        url = git(self.main, "config", "--get", "remote.origin.url", check=False)
        self.forge = "github" if GITHUB.match(url) else None

    def read_states(self, tasks: list[dict] | None = None) -> None:
        """This task's record, as the state files say now."""
        tasks = (
            tasks
            if tasks is not None
            else json.loads(script("project.py", self.repo, "tasks").stdout)
        )
        record = next((task for task in tasks if task["slug"] == self.slug), None)
        if record is None:
            raise LandError(
                f"no task {self.slug!r}; the tasks are: "
                f"{', '.join(task['slug'] for task in tasks) or 'none yet'}"
            )
        self.record: dict[str, Any] = record

    def need_worktree(self) -> None:
        if not (self.worktree / ".git").exists():
            branch = self.kept().get("branch") or "BRANCH"
            raise LandError(
                f"the task has no worktree at {self.worktree}: "
                f"`git -C {self.main} worktree prune` forgets a worktree whose folder "
                f"was removed by hand, and `git -C {self.main} worktree add "
                f"{self.worktree} {branch}` puts the task's branch back in it, then "
                "this step runs again; when the work is gone with it, "
                f'`lem project state {self.slug} dropped "WHY"` ends the task',
            )
        dirty = git(self.worktree, "status", "--porcelain")
        if dirty:
            raise LandError(
                f"the worktree has changes nobody committed:\n{dirty}\n"
                "commit them or remove them before this step"
            )

    def blocked_by_start(self) -> bool:
        """Whether the task is `blocked` by `start` itself, for want of a command of
        the checks."""
        block = self.record.get("state") or ""
        return self.record["status"] == "blocked" and block.splitlines()[0].endswith(
            f" blocked: {NO_GATE}"
        )

    def block_lines(self) -> list[str]:
        """The lines of the task's newest state block, its first one without its time
        and status."""
        rows = (self.record.get("state") or "").splitlines()
        return [rows[0].split(": ", 1)[-1], *rows[1:]] if rows else []

    def starts_over(self) -> bool:
        """Whether the newest state block starts the landing over (`ready --start-over`
        wrote it)."""
        return START_OVER in (line.strip() for line in self.block_lines())

    def need_landing(self) -> None:
        if self.record["status"] != "landing":
            if self.record["status"] in ("ready", "open") or self.blocked_by_start():
                raise LandError(
                    f"the task is {self.record['status']!r}, not `landing`; "
                    f"`lem land start {self.slug}` comes first"
                )
            raise LandError(
                f"the task is {self.record['status']!r}, not `landing`: "
                "`lem land start` takes a `ready` or an `open` task into it, "
                "and this one is neither"
            )

    def kept(self) -> dict:
        if not self.kept_file.is_file():
            return {}
        try:
            return json.loads(self.kept_file.read_text(encoding="utf-8"))
        except ValueError as error:
            raise LandError(
                f"{self.kept_file} does not read as JSON ({error}); land.py writes it "
                "whole, so something else wrote it. Move it aside, then `lem project "
                f'state {self.slug} ready --start-over "WHY"` and '
                f"`lem land start {self.slug}` start the landing over: "
                "its checks and its review run again, and `propose` finds a pull "
                "request the task has on the forge",
            ) from error

    def keep(self, **values: object) -> None:
        write_whole(
            self.kept_file, json.dumps({**self.kept(), **values}, indent=2) + "\n"
        )

    def state(self, status: str, *lines: str) -> None:
        script(
            "project.py",
            self.worktree if self.worktree.exists() else self.main,
            "state",
            self.slug,
            status,
            *lines,
        )

    def logged(self) -> list[dict]:
        """Each decision and breaker of the task as it stands, through the one script
        that writes them."""
        if self.recorded is None:
            self.recorded = json.loads(
                script("decisions.py", self.main, "list", self.slug).stdout
            )
        return self.recorded

    def decisions(self) -> list[dict]:
        """Each decision of the task: taken by a level of the ladder, by the lead, or by
        the owner."""
        return [decision for decision in self.logged() if decision["kind"] == "taken"]

    def breakers(self) -> list[dict]:
        """Each time the circuit breaker stopped the task, with whether the owner's help
        settled it."""
        return [breaker for breaker in self.logged() if breaker["kind"] == "breaker"]

    def gate(self) -> tuple[list[str], bool]:
        """The commands of this task's checks, and whether its own branch brought them:
        the main checkout's, unless those are none and the branch adds some to
        its `.lem/settings.toml`."""
        own = self.settings["checks"]["commands"]
        if own or not (self.worktree / ".git").exists():
            return own, False
        if self.branch_gate is None:
            # asked twice by one proposal (the text and its reasons), and kept: no step
            # writes the branch's settings
            self.branch_gate = json.loads(
                script("project.py", self.worktree, "show").stdout
            )["checks"]["commands"]
        tip = self.branch_gate
        if not tip:
            return [], False
        base = git(self.worktree, "merge-base", "HEAD", self.onto, check=False)
        before = (
            git(self.worktree, "show", f"{base}:.lem/settings.toml", check=False)
            if base
            else ""
        )
        try:
            parsed = tomllib.loads(before) if before else {}
            on_base = parsed.get("checks", {}).get("commands", [])
        except tomllib.TOMLDecodeError:
            on_base = []
        return (tip, True) if not on_base else ([], False)

    def fetch(self) -> None:
        if self.remote:
            git(self.main, "fetch", "origin", str(self.base))

    def own_remote(self, branch: str) -> str:
        """The commit origin's copy of the task's branch is at, which a push of the
        branch may replace, or "" when origin has no such branch: the value of the
        push's lease. Refused when that copy holds a commit that neither Lem pushed nor
        the branch holds, a teammate's: a push would remove it. Origin is asked by
        `ls-remote`, never by the remote-tracking branch, which any plain fetch moves to
        the teammate's commit."""
        ref = f"refs/heads/{branch}"
        listed = [
            line.split("\t")
            for line in run(
                ["git", "-C", str(self.main), "ls-remote", "origin", ref]
            ).stdout.splitlines()
        ]
        there = next((commit for commit, name in listed if name == ref), None)
        if there is None:
            return ""
        kept = self.kept()
        # what Lem pushed last, and what the remote held when the branch took its
        # commits in
        known = [commit for commit in (kept.get("pushed"), kept.get("taken")) if commit]
        if there in known:
            return there
        git(self.main, "fetch", "-q", "origin", f"+{ref}:refs/remotes/origin/{branch}")
        theirs = run(
            [
                "git",
                "-C",
                str(self.worktree),
                "log",
                "--format=%H%x00%an%x00%s",
                there,
                "--not",
                "HEAD",
                *known,
                self.onto,
                "--",
            ]
        ).stdout.splitlines()
        if not theirs:
            # every commit of origin's copy is on the branch, the base or a push of
            # Lem's: the branch took them in
            self.keep(taken=there)
            return there
        named = "; ".join(
            f'{sha[:9]} {author} "{subject}"'
            for sha, author, subject in (
                line.split("\0", 2) for line in theirs[:NAMED_COMMITS]
            )
        )
        more = (
            f", and {len(theirs) - NAMED_COMMITS} more"
            if len(theirs) > NAMED_COMMITS
            else ""
        )
        raise LandError(
            f"origin's {branch} holds {len(theirs)} commit(s) that Lem did not push "
            f"and the task's branch does not hold: {named}{more}. A push would remove "
            f"them. Bring them into the task's worktree with `git -C {self.worktree} "
            f"pull --rebase origin {branch}`, then run the landing again from "
            f"`lem land start {self.slug}`: they are part of the change then, "
            "with its checks and a read",
        )


def cmd_start(task: Task, *, conflicting: bool = False) -> dict:
    # Two starts at one moment take turns to read the tasks' states and write `landing`,
    # under the lock of the state folder. The lock is the kernel's, and it goes with the
    # process, however that ends. It holds no task back: any number of tasks are in
    # `landing` at once.
    path = task.directory.parent.parent / "landing.lock"
    try:
        lock = path.open("w")
    except OSError as error:
        # a file nobody may write, or a folder of that name: the lock holds nothing, so
        # it may go
        raise LandError(
            f"the landing lock {path} cannot be opened ({error.strerror}); "
            f"it holds no state, so remove it (`rm -r {path}`) and run "
            f"`lem land start {task.slug}` again",
        ) from error
    with lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        task.read_states()
        return start_locked(task, conflicting=conflicting)


def start_locked(task: Task, *, conflicting: bool = False) -> dict:  # noqa: C901, PLR0912 - over the limit before the limit was set
    # a task `start` blocked for want of a command of the checks is taken back as a
    # `ready` one
    again = task.blocked_by_start()
    if task.record["status"] not in ("ready", "landing", "open") and not again:
        raise LandError(
            f"the task is {task.record['status']!r}; only a `ready` task, or an `open` "
            "one whose base moved, starts a landing"
        )
    if conflicting and task.record["status"] != "open":
        raise LandError(
            "--conflicting is for an `open` task whose pull request the forge calls "
            f"conflicting, and {task.slug} is {task.record['status']!r}"
        )
    task.need_worktree()
    # The landing needs the task's branch: `propose` pushes it, and `clean` deletes it
    # after the merge.
    if not git(task.worktree, "branch", "--show-current"):
        pointing = [
            name
            for name in git(
                task.worktree,
                "for-each-ref",
                "--points-at",
                "HEAD",
                "--format=%(refname:short)",
                "refs/heads/",
            ).splitlines()
            if name != task.base
        ]
        branch = task.kept().get("branch") or (
            pointing[0] if len(pointing) == 1 else "BRANCH"
        )
        raise LandError(
            "the task's worktree is on no branch (a detached HEAD), and the landing "
            f"needs the task's branch: `git -C {task.worktree} switch {branch}` puts "
            "it back on it, then this step runs again",
        )
    # the end of the owner's standing merge that a start over gives, in the words
    # `propose` gives an end
    ended = None
    if task.record["status"] == "ready" or again:
        kept = task.kept()
        if task.starts_over() or not kept.get("proposed"):
            # A task that was built further, or whose landing `ready --start-over` gives
            # back, starts over, with new checks and new reads. Its pull request stays
            # its own, and so does what Lem knows of its branch on the forge: the commit
            # it pushed last, and the one whose commits the branch took in
            # (`own_remote`); and Jev's read of each finding called under the bar
            # (`jev`), so a second landing sends no finding twice. The polish pass runs
            # once for a task (`stages/polish.md`): a pass that is done stays while the
            # branch holds its last commit, and `base` carries it through the rebase.
            forge = {
                key: value
                for key, value in kept.items()
                if key in ("pr", "pushed", "taken", "jev") and value
            }
            polish = kept.get("polish")
            if (
                polish
                and polish.get("done")
                and holds_commit(
                    task, polish.get("after"), git(task.worktree, "rev-parse", "HEAD")
                )
            ):
                forge["polish"] = polish
            tap = kept.get("owner_tap")
            if tap:
                # His standing merge ends with the record: a fact of the log, which the
                # board shows, logged before the deletion, so that a run cut between the
                # two still told it (a rerun logs it twice).
                why = (
                    "the landing started over: "
                    f"{(task.block_lines() or ['no reason given'])[0]}"
                )
                script(
                    "project.py",
                    task.main,
                    "log",
                    task.slug,
                    "merge.ended",
                    "by=owner",
                    f"tip={str(tap.get('tip'))[:9]}",
                    f"why={why}",
                )
                ended = f"ended: {why}; the owner merges it again"
            task.kept_file.unlink(missing_ok=True)
            if forge:
                task.keep(**forge)
        # Otherwise the record stays whole: no deletion, no new count. A task leaves
        # `open` only through `start`, which counts the new landing below, so a proposal
        # on record means that a new landing of that proposal was cut (a red base, a
        # builder that ended twice) and the task came back `ready`: it goes on, and what
        # the landing carried (the reviews, the merge agent's review, the owner's merge,
        # a conflict and its resolution, the count) carries as with no wait between.
    if task.record["status"] == "open":
        # An open task brought onto a base that moved: what the pull request's text says
        # of it is kept from here, and a conflict or a resolution of an earlier landing
        # says nothing of this one. Each new landing of a proposal is counted, for the
        # merge agent's facts: nothing bounds them, since the checks run outside the
        # merge lock and a busy base can move again meanwhile.
        relands = int(task.kept().get("relands") or 0) + 1
        task.keep(
            sync={
                "conflicting": conflicting,
                "onto": None,
                "moved": None,
                "conflict": None,
                "resolved": False,
                "carried": None,
            },
            conflict=None,
            resolution=None,
            rebase_carried=None,
            rebase_uncovered=None,
            made=None,
            relands=relands,
        )
        script(
            "project.py",
            task.main,
            "log",
            task.slug,
            "land.again",
            f"count:={relands}",
            f"conflicting:={json.dumps(conflicting)}",
        )
    # The check for a command of the checks comes after the record's two branches: its
    # own `blocked` block never stands between the block of a start over and the record
    # that start over deletes, and an `open` task's new landing is counted before
    # anything here can refuse it.
    if not task.gate()[0]:
        if not again:
            task.state("blocked", NO_GATE)
        raise LandError(
            (
                f"{NO_GATE}, so nothing would show that the change works; "
                "the task is `blocked`. Add the commands to checks.commands in "
                ".lem/settings.toml, or, for the task that sets up the checks, in its "
                f"own branch's, then run `lem land start {task.slug}` again"
            )
            + (f". The owner's merge {ended}" if ended else ""),
        )
    if task.record["status"] != "landing":
        # kept here because `clean` needs the branch after the worktree, which names it,
        # is gone
        task.keep(branch=git(task.worktree, "branch", "--show-current"))
        if conflicting:
            moved = (
                f"the forge calls the pull request conflicting with {task.base}: "
                "the branch is brought onto it again"
            )
        else:
            moved = "the base moved: the checks run again"
        task.state(
            "landing",
            "the checks start" if task.record["status"] == "ready" or again else moved,
        )
    return {
        "task": task.slug,
        "base": task.base,
        "worktree": str(task.worktree),
        "remote": task.remote,
        "forge": task.forge,
        "owner_merge": ended,
    }


def cmd_base(task: Task) -> dict:  # noqa: C901, PLR0912, PLR0915 - over the limit before the limit was set
    task.need_landing()
    task.need_worktree()
    task.fetch()
    if task.forge == "github":
        # Before the rebase rewrites the branch: a commit a teammate added to it on the
        # forge is taken in by hand first, or the push after this rebase would
        # remove it.
        task.own_remote(git(task.worktree, "branch", "--show-current"))
    onto = git(task.worktree, "rev-parse", task.onto)
    entry = git(task.worktree, "rev-parse", "HEAD")
    kept = task.kept()
    # A conflict this landing met before: a builder rebased the branch since and
    # resolved it, or left it as it was. Its record keeps the tip before any rebase,
    # whether a review covered it, and why not.
    pending = kept.get("conflict")
    made = kept.get("made")
    if (
        made
        and not pending
        and not kept.get("resolution")
        and made.get("tip") == entry
        and made.get("from") != entry
        and entry not in (kept.get("pushed"), kept.get("proposed"))
    ):
        # A second rebase in one landing (after a wait for a red base, or a step run
        # again) gives what one rebase with no wait gives: the branch goes back to the
        # tip before Lem's own first rebase, and that tip is rebased onto the base now,
        # judged as one rebase. The tip thrown away is one only `base` wrote, with
        # nothing after it, and never pushed (only `propose` pushes); a commit after it,
        # or a conflict on the way, is judged as a rebase after it, as with no wait.
        if kept.get("polish"):
            # the polish pass's names go back to the commits of that tip, by their place
            # from the tip
            task.keep(
                polish=through_rebase(
                    task, kept["polish"], entry, made["from"], made["onto"]
                )
            )
        git(task.worktree, "reset", "-q", "--hard", made["from"])
        kept = task.kept()
    before = git(task.worktree, "rev-parse", "HEAD")
    answered = [read for read in kept.get("reads", []) if read["answered"]]
    # what a rebase with no conflict carries: the newest review that answered, while it
    # saw this change, with whatever it left open (read before the rebase, on the branch
    # as it is) the task's own item, whose deletion on the branch asks for no other
    # review (`task_item`)
    own = task_item(task)
    carries = not (pending and before != pending["before"]) and review_carries(
        answered, backlog_of(task), change(task), own
    )
    if pending:
        covered = pending["covered"]
        uncovered = pending["uncovered"]
    else:
        # covered: the newest review that answered saw this change and left nothing to
        # fix in it, which a conflict's record keeps: it decides between one read of the
        # resolution and the rules of the change
        covered = carries and not answered[-1]["must_fix"]
        # why it is not, for the owner's merge that `propose` ends after this
        # rebase (`moved_carry`)
        uncovered = why_uncovered(answered, backlog_of(task), change(task), own)
    rebased = run(["git", "-C", str(task.worktree), "rebase", task.onto], check=False)
    if rebased.returncode != 0:
        conflicts = git(
            task.worktree, "diff", "--name-only", "--diff-filter=U", check=False
        ).splitlines()
        git(task.worktree, "rebase", "--abort", check=False)
        task.keep(
            conflict={
                "before": pending["before"] if pending else before,
                "base": pending["base"]
                if pending
                else git(task.worktree, "merge-base", before, onto),
                "files": sorted({*(pending["files"] if pending else []), *conflicts}),
                "covered": covered,
                "uncovered": uncovered,
            }
        )
        if kept.get("sync"):
            task.keep(
                sync={
                    **kept["sync"],
                    "conflict": sorted(
                        {*(kept["sync"].get("conflict") or []), *conflicts}
                    ),
                }
            )
        print(
            json.dumps(
                {
                    "task": task.slug,
                    "conflict": conflicts,
                    "onto": task.onto,
                    "branch": git(task.worktree, "branch", "--show-current"),
                },
                indent=2,
            )
        )
        raise LandError(
            f"the rebase onto {task.onto} stopped on {len(conflicts)} file(s) and was "
            "undone; a builder resolves it in the worktree, then this step runs again",
        )
    tip = git(task.worktree, "rev-parse", "HEAD")
    ahead = int(git(task.worktree, "rev-list", "--count", f"{onto}..HEAD"))
    if ahead == 0:
        raise LandError(
            f"the branch has no commit that {task.onto} lacks: there is nothing to "
            "land. When the work reached the base another way, or there is none, "
            f'`lem project state {task.slug} dropped "WHY"` ends the task',
        )
    # A builder that resolved the conflict rebased the branch itself: its commits are
    # the ones the rebase rewrote, from the tip before it. One that left the branch as
    # it was resolved nothing.
    resolved = bool(pending) and before != pending["before"]
    origin = pending["before"] if pending else before
    if tip != origin and task.kept().get("polish"):
        # The rebase rewrote the commits the polish pass names; each takes its new name,
        # so that the checks still find the pass on the tip they check.
        task.keep(polish=through_rebase(task, task.kept()["polish"], origin, tip, onto))
    now = change(task)
    # the tip a rebase with no conflict made of the tip before it, while the review
    # carried: what was said of that tip at the merge (the merge agent's review, the
    # owner's merge) is kept for this one
    updates: dict = {
        "base": onto,
        "gated": None,
        "tree": None,
        "conflict": None,
        "rebase_carried": None,
        "rebase_uncovered": None,
        "made": None,
    }
    if tip != origin and not resolved:
        # the tip this rebase made itself, from which tip and onto which base: a second
        # rebase of this landing goes back to `from` while the branch is still `tip`
        # (above). `filed_on` never moves it: `file`'s commits after it are commits
        # after the rebase here.
        updates["made"] = {"from": origin, "tip": tip, "onto": onto}
    # the review this rebase carried, with what it left open, for the pull request's
    # text (`synced`)
    carried = None
    if resolved:
        # What the review saw is the change before the conflict; what the builder chose
        # where the two sides met is new, and gets one read of its own (`due`).
        updates["resolution"] = {
            "files": pending["files"],
            "before": origin,
            "after": tip,
            "base": pending["base"],
            "onto": onto,
            "covered": covered,
            "patch": now["patch"],
            "read": None,
        }
    elif tip != origin and carries:
        # A rebase that git made with no conflict keeps the review of the change as it
        # was: the newest review that answered covers the change on the new base too,
        # and a must-fix it left stays open, a reason for not green in the same
        # words (`due_of`).
        reads = task.kept().get("reads", [])
        last = max(index for index, read in enumerate(reads) if read["answered"])
        reads[last] = {
            **reads[last],
            "carried": [
                *reads[last].get("carried", []),
                {"patch": now["patch"], "contents": now["contents"], "onto": onto[:9]},
            ],
        }
        updates["reads"] = reads
        updates["rebase_carried"] = {"from": origin, "to": tip}
        carried = {"round": reads[last]["round"], "must_fix": reads[last]["must_fix"]}
    if tip != origin and not (covered if resolved else carries):
        # the tip a rebase made while no review covered the change, and why: the words
        # of the owner's merge that `propose` of this tip ends
        updates["rebase_uncovered"] = {"from": origin, "to": tip, "why": uncovered}
    if kept.get("sync"):
        updates["sync"] = {
            **task.kept()["sync"],
            "onto": onto[:9],
            "moved": tip != origin,
            "resolved": resolved or task.kept()["sync"].get("resolved", False),
            "carried": carried,
        }
    # a new base or a new tip means the last result of the checks is about another tree
    task.keep(**updates)
    return {
        "task": task.slug,
        "onto": task.onto,
        "base": onto,
        "tip": tip,
        "moved": tip != entry,
        "ahead": ahead,
        "resolved": pending["files"] if resolved else None,
    }


def holds_commit(task: Task, commit: object, tip: str) -> bool:
    """Whether the branch at `tip` holds `commit`."""
    return (
        bool(commit)
        and run(
            [
                "git",
                "-C",
                str(task.worktree),
                "merge-base",
                "--is-ancestor",
                # a record's value: text as Lem writes it, and anything in a file
                # changed by hand
                str(commit),
                tip,
            ],
            check=False,
        ).returncode
        == 0
    )


def through_rebase(task: Task, polish: dict, before: str, tip: str, onto: str) -> dict:
    """The polish pass's record after a rebase by `base`: each commit it names, by its
    place from the tip. A rebase keeps the branch's commits one for one, unless one
    became empty and was dropped; then no place is sure, the names are dropped, and the
    checks ask for the pass again."""
    same = int(git(task.worktree, "rev-list", "--count", f"{onto}..{before}")) == int(
        git(task.worktree, "rev-list", "--count", f"{onto}..{tip}")
    )
    moved = dict(polish)
    for key in ("before", "after"):
        commit = polish.get(key)
        if not commit:
            continue
        if same and holds_commit(task, commit, before):
            after = int(
                git(task.worktree, "rev-list", "--count", f"{commit}..{before}")
            )
            moved[key] = git(task.worktree, "rev-parse", f"{tip}~{after}")
        else:
            moved[key] = None
    return moved


def test_files(found: dict) -> list[str]:
    """The files that hold a criterion's test, as the plan names them."""
    return sorted(
        {
            file
            for criterion in found["criteria"]
            for test in criterion["tests"]
            for file in test["files"]
        }
    )


def cmd_polish(task: Task, *, done: bool) -> dict:  # noqa: C901, PLR0912 - over the limit before the limit was set
    """The polish pass: what its builder gets, and after the builder, the check of what
    it did."""
    task.need_landing()
    task.need_worktree()
    found = criteria_of(task)
    if found["small"]:
        raise LandError(
            "the fast track has no polish pass: its builder judged what it saw outside "
            "the change by the bar of rule 6 of the builder's standing rules, in "
            "commits of its own, and the review reads every line of it. "
            f"`lem land checks {task.slug}` is the next step",
        )
    kept = task.kept()
    if "base" not in kept:
        raise LandError(
            f"`lem land base {task.slug}` comes first: the polish pass works on the "
            "branch as it will be checked"
        )
    tip = git(task.worktree, "rev-parse", "HEAD")
    # what the pass may not change: the test files of the criteria and the plan that
    # names them; a fast track's criteria file is in the task directory, which no
    # commit holds
    frozen = [
        *test_files(found),
        *(
            []
            if found["small"]
            else [Path(found["plan"]).relative_to(task.worktree).as_posix()]
        ),
    ]
    polish: dict[str, Any] | None = kept.get("polish")
    if not done:
        # A pass that started and is not done keeps the tip it started at: a run that is
        # cut off, or a second start, must not take the builder's first commits for the
        # task's own.
        if (
            not polish
            or not polish.get("before")
            or (polish.get("done") and not holds_commit(task, polish.get("after"), tip))
        ):
            polish = {"before": tip, "done": False}
            task.keep(polish=polish)
            # the start of the pass, once: the board draws its span from here
            # to `polish`
            script(
                "project.py",
                task.worktree,
                "log",
                task.slug,
                "polish.start",
                f"before={tip[:9]}",
            )
        base = git(task.worktree, "merge-base", polish["before"], task.onto)
        report, outside = task.directory / "report.md", task.directory / "outside.md"
        return {
            "task": task.slug,
            "size": found["size"],
            "done": polish["done"],
            "before": polish["before"],
            # the task's own commits, which the pass reads; what it commits comes
            # after `before`
            "range": f"{base}..{polish['before']}",
            "commits": git(
                task.worktree, "log", "--format=%h %s", f"{base}..{polish['before']}"
            ).splitlines(),
            "plan": found["plan"],
            "report": str(report) if report.is_file() else None,
            "outside": str(outside) if outside.is_file() else None,
            "backlog": backlog_of(task),
            # the item the task was started from, which the pass removes when the branch
            # still holds it
            "item": task_item(task),
            "frozen": frozen,
        }
    if not polish:
        raise LandError(
            f"no polish pass started for this landing; `lem land polish {task.slug}` "
            "starts it and prints what its builder gets"
        )
    if polish.get("done"):
        raise LandError(
            "the polish pass of this landing is done already, at "
            f"{str(polish.get('after'))[:9]}; a builder of the landing after it has "
            "the same list in its brief"
        )
    before = polish["before"]
    if not holds_commit(task, before, tip):
        raise LandError(
            f"the branch no longer holds {str(before)[:9]}, the tip the polish pass "
            "started at: its builder rewrote the task's commits, which no builder of "
            "the pass does. Put the branch back on its own commits (git reflog names "
            "them), then run this again",
        )
    commits = git(
        task.worktree, "log", "--reverse", "--format=%H %s", f"{before}..{tip}"
    ).splitlines()
    touched: dict[str, list[str]] = {}
    for line in commits:
        commit = line.split(" ", 1)[0]
        for file in git(
            task.worktree,
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "--no-renames",
            "-r",
            commit,
        ).splitlines():
            touched.setdefault(file, []).append(commit[:9])
    # What counts is what the pass leaves: a commit that changed a criterion's test and
    # one that put it back leave the contract as it was.
    differs = set(changed(task, before, tip))
    wrong = [
        f"{file} (by {', '.join(touched.get(file, []))})"
        for file in frozen
        if file in differs
    ]
    if wrong:
        raise LandError(
            f"the polish pass changed what it may not: {'; '.join(wrong)}. "
            "A criterion's test and the plan are the task's contract, and the pass "
            "changes no behavior: a builder reverts those commits (`git revert`), "
            "and this step runs again",
        )
    result: dict = {
        "task": task.slug,
        "before": before,
        "after": tip,
        "commits": [line.split(" ", 1)[1] if " " in line else "" for line in commits],
    }
    if commits:
        held = script("criteria.py", task.main, "red", task.slug, check=False)
        if held.returncode != 0:
            raise LandError(
                "after the polish pass the tests of the criteria do not hold: "
                f"{held.stderr.strip().removeprefix('criteria.py: ')}. "
                "The pass changes no behavior: a builder finds the commit of the pass "
                "that broke it and takes it out, and this step runs again",
            )
        result["criteria"] = json.loads(held.stdout)
    else:
        result["criteria"] = None
    folder = backlog_of(task)
    added = [
        row.split("\t", 1)[1]
        for row in git(
            task.worktree, "diff", "--name-status", "--no-renames", before, tip
        ).splitlines()
        if row.startswith("A\t")
    ]
    result["filed"] = [path for path in added if path.startswith(folder + "/")]
    script(
        "project.py",
        task.worktree,
        "log",
        task.slug,
        "polish",
        f"before={before[:9]}",
        f"after={tip[:9]}",
        f"commits:={len(commits)}",
        f"filed:={json.dumps(result['filed'])}",
    )
    # the pass's result of the criteria's tests, with the inputs its run reported: the
    # checks take it in place of a run of their own when those inputs are the same when
    # they decide (`taken_from_polish`)
    task.keep(
        polish={
            "before": before,
            "after": tip,
            "done": True,
            "commits": len(commits),
            "filed": result["filed"],
            "criteria": result["criteria"],
        }
    )
    return result


def polish_missing(task: Task, tip: str, found: dict) -> str | None:
    """Why the checks may not run on this tip for want of the polish pass; none when it
    may. A task on the standard track, which is every task with a plan, needs a pass of
    this landing whose last commit the tip holds, and a pass that started and is not
    done stops it: a builder may still be at work. A task on the fast track never
    has one."""
    if found["small"]:
        return None
    polish = task.kept().get("polish")
    if polish and not polish.get("done"):
        return (
            f"the polish pass started at {str(polish.get('before'))[:9]} and is not "
            f"done: after its builder, `lem land polish {task.slug} --done` checks "
            "what it did"
        )
    if not polish:
        return (
            f"{task.slug} takes the standard track, and no polish pass is on record "
            f"for this landing: `lem land polish {task.slug}` starts it, a builder "
            "does it, and `--done` checks it"
        )
    if not holds_commit(task, polish.get("after"), tip):
        return (
            "the tip does not hold the polish pass's last commit "
            f"({str(polish.get('after'))[:9]}): the branch was rewritten after the "
            "pass by something else than `lem land base`. The pass runs again: "
            f"`lem land polish {task.slug}`, its builder, and `--done`"
        )
    return None


def taken_from_polish(
    polish: dict | None, now: dict | None, *, small: bool
) -> dict | None:
    """The polish pass's result of the criteria's tests when the checks take it in place
    of a run of their own, with `taken`, which names the pass and its commit; None when
    the checks run the tests.

    The fast track has no pass, and a pass with no commits ran no tests. Otherwise the
    result is taken only when NOW, the inputs `lem criteria inputs` gives after the
    checks' commands, are the inputs the pass's run reported, all five: the tip, the
    base commit, the plan file, `checks.setup` and `checks.serial`. `polish.after`
    decides nothing here: a rebase by `base` gives it the rebased commit's name
    (`through_rebase`), while the run named the tip it ran on."""
    if small or not polish or not polish.get("done") or not polish.get("commits"):
        return None
    ran = polish.get("criteria") or {}
    if (
        not ran.get("ok")
        or not ran.get("inputs")
        or now is None
        or ran["inputs"] != now
    ):
        return None
    return {**ran, "taken": {"from": "polish", "at": ran["inputs"]["tip"]}}


def taken_at(criteria: object) -> str | None:
    """The commit, as `gate.end` names it, whose polish pass's result of the criteria's
    tests a run of the checks took (`taken_from_polish`); None for a run that ran them,
    or that never reached them."""
    taken = criteria.get("taken") if isinstance(criteria, dict) else None
    at = (
        taken.get("at")
        if isinstance(taken, dict) and taken.get("from") == "polish"
        else None
    )
    return at[:9] if isinstance(at, str) and at else None


def criteria_of(task: Task) -> dict:
    """The task's acceptance criteria and its plan, through the one script that reads
    them. A step asks for them many times, and no step writes the plan, the approval or
    a criterion's record, so the first answer is kept for the life of this process."""
    if task.criteria is None:
        task.criteria = json.loads(
            script("criteria.py", task.main, "show", task.slug).stdout
        )
    return task.criteria


def change(task: Task) -> dict:
    """The change as the branch holds it now: its two ends, its files, its size, and the
    id of its patch."""
    tip = git(task.worktree, "rev-parse", "HEAD")
    base = git(task.worktree, "merge-base", tip, task.onto)
    # The id of the change: each file it touches, with the content the file had on the
    # base and the content it has now. A rebase onto a base that left those files alone
    # keeps the id, and everything else is another change: one space, the same edit in
    # another place of a file, a base that changed a file under the change. git's own
    # patch id is not used: it ignores spaces and places, and either can be the whole of
    # a change.
    raw = git(task.worktree, "diff", "--raw", "--no-abbrev", "--no-renames", base, tip)
    patch = hashlib.sha256(raw.encode()).hexdigest()[:16]
    # The same listing path by path, with NUL ends so that no path is quoted: each file
    # with its mode and blob on the base and on the tip. A review keeps it, so that what
    # was added after the review is known file by file (`covers`).
    listed = run(
        [
            "git",
            "-C",
            str(task.worktree),
            "diff",
            "--raw",
            "-z",
            "--no-abbrev",
            "--no-renames",
            base,
            tip,
        ]
    ).stdout.split("\0")
    # each head is ":MODE_BASE MODE_TIP BLOB_BASE BLOB_TIP STATUS"
    heads = {
        path: head.lstrip(":").split()
        for head, path in zip(listed[0::2], listed[1::2], strict=False)
    }
    contents = {
        path: {"base": head[2], "tip": head[3], "modes": head[:2]}
        for path, head in heads.items()
    }
    counted = git(
        task.worktree, "diff", "--numstat", "--no-renames", base, tip
    ).splitlines()
    lines = sum(int(n) for row in counted for n in row.split("\t")[:2] if n.isdigit())
    return {
        "tip": tip,
        "base": base,
        "files": changed(task, base, tip),
        "patch": patch,
        "contents": contents,
        "lines": lines,
    }


def backlog_of(task: Task) -> str:
    """The backlog folder, relative to the root of the repository: its one
    place, `docs/backlog`."""
    return (
        Path(task.settings["places"]["backlog"]["path"])
        .relative_to(Path(task.settings["root"]).resolve())
        .as_posix()
    )


def task_item(task: Task) -> str | None:
    """The backlog item the task was started from, by `item_of_ask` over its `ask.txt`
    and the base commit of its branch: the path relative to the root, or None when the
    task has no such item."""
    file = task.directory / "ask.txt"
    if not file.is_file():
        return None
    base = git(task.worktree, "merge-base", "HEAD", task.onto, check=False)
    if not base:
        return None
    roots = (str(task.main), str(task.main.resolve()))
    return item_of_ask(
        file.read_text(encoding="utf-8", errors="replace"),
        backlog_of(task),
        roots,
        lambda path: file_at(task, base, path),
    )


def item_of_ask(
    ask: str, folder: str, roots: tuple[str, ...], at_base: Callable[[str], bool]
) -> str | None:
    """The item a task was started from: its ASK, stripped, is one path and nothing
    else, of a file of the backlog folder FOLDER itself whose name ends in `.md`, and
    AT_BASE finds it at the base commit. The board's "Start a task" writes the path
    relative to the root; the night may write it whole, from `lem project path backlog`,
    and a whole path under one of ROOTS (the main checkout) reads as the same item. An
    ask with any other word beside the path asks for more than the item's work, and has
    no item. The path relative to the root, or None."""
    path = ask.strip()
    if path.startswith("/"):
        root = next(
            (
                f"{root.rstrip('/')}/"
                for root in roots
                if path.startswith(f"{root.rstrip('/')}/")
            ),
            None,
        )
        if root is None:
            return None
        path = path[len(root) :]
    parent, _, name = path.rpartition("/")
    if parent != folder or not name.endswith(".md"):
        return None
    return path if at_base(path) else None


def state_item_of_ask(ask: str, state: Path) -> str | None:
    """The reviewer's item a task was started from, a file of `.lem/state/backlog/` that
    git never holds, so no commit of a task's branch removes it and the landing removes
    the file itself (`forge_done`): project.py's one rule, `backlog_item_of`, over ASK
    and the main checkout's state folder STATE. The path relative to the root, whether
    the file is there or not, or None."""
    path = SCRIPTS / "project.py"
    if not lem_sibling.in_form(path):
        raise LandError(
            f"{path} has no main(argv), so the landing cannot read by its rule which "
            "backlog item of the state folder a task was started from"
        )
    return lem_sibling.module(path).backlog_item_of(state, ask)


def state_item(task: Task) -> str | None:
    """The reviewer's item the task was started from, by `state_item_of_ask` over its
    `ask.txt`, or None."""
    file = task.directory / "ask.txt"
    if not file.is_file():
        return None
    return state_item_of_ask(
        file.read_text(encoding="utf-8", errors="replace"), task.state_folder
    )


def remove_item(state: Path, item: str, slug: str, url: str) -> bool:
    """Remove the file of the reviewer's item ITEM (`state_item`) from the state folder
    STATE, for the task SLUG whose pull request URL GitHub merged. False when it is gone
    already, which is no error. A removal that fails raises the landing's error, so the
    task stays `open` and the next `lem land merged` tries again."""
    file = state / "backlog" / item.rpartition("/")[2]
    try:
        file.unlink()
    except FileNotFoundError:
        return False
    except OSError as error:
        raise LandError(
            f"GitHub merged {url}, and the file of the backlog item the task was "
            f"started from, {file}, was not removed ({error.strerror or error}); "
            f"the task stays open, and `lem land merged {slug}` tries again"
        ) from error
    return True


def covers(task: Task, read: dict, now: dict, own: str | None = None) -> bool:
    """Whether a review that was recorded still covers the change as it is now: the
    change it reviewed, or that change as each rebase `base` made with no conflict
    carried it onto a new base. OWN is the task's own item (`task_item`), whose deletion
    asks for no other review."""
    return covered(backlog_of(task), read, now, own)


def covered(folder: str, read: dict, now: dict, own: str | None = None) -> bool:
    """`covers`, with the backlog folder given: the rule alone, which reads no file."""
    return any(
        covers_one(folder, seen, now, own) for seen in [read, *read.get("carried", [])]
    )


def review_carries(
    answered: list[dict], folder: str, now: dict, own: str | None = None
) -> bool:
    """Whether a rebase with no conflict carries the review onto the new base, from the
    reviews that answered, in order, the backlog folder, the change as it is now and the
    task's own item: the newest one covers the change, whatever it left open. A must-fix
    it left stays open on the new tip, a reason for not green in the same words
    (`due_of`). That it also left no must-fix is the `covered` of a conflict's record,
    which `why_uncovered` gives the reason against."""
    return bool(answered) and covered(folder, answered[-1], now, own)


def why_uncovered(
    answered: list[dict], folder: str, now: dict, own: str | None = None
) -> str | None:
    """Why no review covers the change as it is now, from the reviews that answered, in
    order, the backlog folder and the task's own item: the newest one's words, for the
    owner whose merge `propose` ends. None when the newest one covers it and left no
    must-fix, which is when `cmd_base`'s `covered` is true."""
    if not answered:
        return "no review answered for the change"
    last = answered[-1]
    if last["must_fix"]:
        return (
            f"round {last['round']} left {last['must_fix']} must-fix, and no review "
            "read the change after it"
        )
    if not covered(folder, last, now, own):
        return f"no review read what changed after round {last['round']}"
    return None


def covers_one(folder: str, read: dict, now: dict, own: str | None = None) -> bool:
    """Whether one form of a reviewed change covers the change as it is now. It does
    when the change is the same, or when the change is the reviewed one plus new files
    of the backlog folder and the deletion of OWN, the item the task was started from
    (`task_item`), and nothing else: `file` writes the defects a review saw outside the
    change there after the review, a builder of the landing removes the task's own item
    when the review came first, and neither holds code, so neither asks for another
    review. Any other file does, another item that was on the base too. A record that
    kept no contents covers only the same change."""
    if read["patch"] == now["patch"]:
        return True
    was = read.get("contents")
    if was is None:
        return False
    extra = [path for path in now["contents"] if path not in was]
    return (
        bool(extra)
        and all(now["contents"].get(path) == entry for path, entry in was.items())
        and all(
            (
                set(now["contents"][path]["base"]) == {"0"}
                and path.startswith(folder + "/")
            )
            or (path == own and set(now["contents"][path]["tip"]) == {"0"})
            for path in extra
        )
    )


def defects_of(
    value: object, attempt: int, folder: str, at_base: Callable[[str], bool]
) -> list[dict]:
    """The defects outside the change as the record of ATTEMPT names them, each with the
    review's call on it (`bar`, `why`, `open`) and its number (`r2.1`); `0` is none, and
    a count is refused. FOLDER is the backlog folder, and AT_BASE tells whether a path
    is a file at the base commit: an `open` names an item that was there."""
    if isinstance(value, int) and not isinstance(value, bool) and value == 0:
        return []
    if not isinstance(value, list) or not all(
        isinstance(item, dict)
        and set(DEFECT) <= set(item)
        and all(isinstance(item[key], str) and item[key].strip() for key in DEFECT)
        and "\n" not in item["where"] + item["title"]
        and slug_of(item["title"])
        for item in value
    ):
        raise LandError(
            "`outside` is the list of the defects the review saw outside the change, "
            'each {"where": PATH OR PATH:SYMBOL, "title": ONE LINE, "what": '
            'THE RUN THAT SHOWS IT, "bar": "over" | "under" | "cheap"}, so '
            "that each one can be filed or named: a count names none of them, "
            "and 0 is none",
        )
    found = []
    for place, item in enumerate(value, start=1):
        number, title = f"r{attempt}.{place}", item["title"].strip()
        extra = set(item) - {*DEFECT, "bar", "why", "open"}
        if extra:
            raise LandError(
                f'the defect {number} outside the change ("{title}") has '
                f"{', '.join(sorted(extra))}: an entry of `outside` holds `where`, "
                "`title`, `what`, `bar`, and `why` and `open` where they apply"
            )
        call, why, open_ = item.get("bar"), item.get("why"), item.get("open")
        if call not in BARS:
            raise LandError(
                f'the defect {number} outside the change ("{title}") has '
                f"{'no `bar`' if call is None else f'the bar {call!r}'}: "
                "`bar` is the review's call by the bar of rule 6 of the builder's "
                'standing rules, "over" (an item with `worth: later`), "under" (an '
                'item with `worth: no`) or "cheap" (its fix is text that does not run, '
                "or a finding of a check of the project that the "
                "check's rerun shows fixed)",
            )
        if why is not None and (
            not isinstance(why, str) or not why.strip() or "\n" in why.strip()
        ):
            raise LandError(
                f"`why` of the defect {number} outside the change "
                f'("{title}") is one line of text'
            )
        if call != "over" and why is None:
            raise LandError(
                f'the defect {number} outside the change ("{title}") is {call}, and '
                "has no `why`: one line that says why it is "
                f"{'under the bar' if call == 'under' else 'cheap'}"
            )
        if open_ is not None and not (
            isinstance(open_, str)
            and open_ == open_.strip()
            and open_.startswith(folder + "/")
            and "\\" not in open_
            and Path(open_).as_posix() == open_
            and ".." not in Path(open_).parts
            and at_base(open_)
        ):
            raise LandError(
                f'`open` of the defect {number} outside the change ("{title}") is '
                f"{open_!r}, which is no file of the backlog folder {folder} at the "
                "base: it is the path of an item of the base that holds the same "
                "defect, as `backlog` in what `lem land read` printed gives it, "
                "or it is left out",
            )
        found.append(
            {
                **{key: item[key].strip() for key in DEFECT},
                "bar": call,
                **({"why": why.strip()} if why is not None else {}),
                **({"open": open_} if open_ is not None else {}),
                "number": number,
            }
        )
    return found


def outside_of(read: dict) -> list[dict]:
    """The defects outside the change of one kept review, each with the path of its item
    once it has one."""
    return read.get("outside", [])


def to_file(
    reads: list[dict],
    in_tip: Callable[[str], bool],
    refuted: Callable[[str], bool] = lambda path: False,
) -> list[dict]:
    """Each defect outside the change that waits for an item: one of a review that
    answered, called over or under the bar, with no item yet, and whose `open` item
    IN_TIP does not find in the tip. The base may remove or join that item after the
    review while a rebase keeps the review: then it is filed. An over defect whose open
    item says `worth: no` at the tip (REFUTED) waits too: it gets a new item that names
    the old one (`NOW_OVER`). A cheap one waits for none: a builder fixes it, or it is a
    line of the pull request."""
    return [
        {
            "round": read["round"],
            "number": defect["number"],
            **{key: defect[key] for key in DEFECT},
        }
        for read in reads
        if read["answered"]
        for defect in outside_of(read)
        if defect["bar"] in FILED_BARS
        and not defect.get("item")
        and not settled_by_open(defect, in_tip, refuted)
    ]


def settled_by_open(
    defect: dict, in_tip: Callable[[str], bool], refuted: Callable[[str], bool]
) -> bool:
    """Whether the `open` item of DEFECT settles it: IN_TIP finds the item in the tip,
    and it is not an item that says `worth: no` (REFUTED) of a defect now called over
    the bar, which gets an item of its own, `worth: later`, that names the old one; the
    old item stays as it is."""
    open_ = defect.get("open")
    return (
        bool(open_)
        and in_tip(open_)
        and not (defect["bar"] == "over" and refuted(open_))
    )


def named_by(number: str, text: str) -> bool:
    """Whether TEXT names an entry of `outside` by its NUMBER (`r1.3`), and not another
    that starts the same (`r1.30`, `r11.3`)."""
    return re.search(rf"(?<![\w.]){re.escape(number)}(?![\w]|\.\d)", text) is not None


def seen_line(defect: dict) -> str:
    """The line of a defect under `## Seen, not filed`: its place, its title, the
    review's call with its why (`cheap: WHY`), and the open item that holds it, in the
    form `propose` asks of a line of the notes there (`unfiled_lines`), so a line the
    script writes always passes."""
    line = f"- `{defect['where']}`: {defect['title']}"
    if defect.get("why"):
        line += f"; {defect['bar']}: {defect['why']}"
    if defect.get("open"):
        line += f"; an open item holds it, `{defect['open']}`"
    return line


def outside_parts(
    reads: list[dict], fixed: str, added: list[dict] | tuple = ()
) -> tuple[list[str], list[str], list[str]]:
    """What was seen outside the change, for the pull request's text: the lines under
    `## Filed in the backlog`, those under `## Filed as not worth it`, and those under
    `## Seen, not filed`. ADDED is each item the branch adds to the backlog folder,
    whoever filed it, with its `worth` at the tip (`builder_filed`); an item of a review
    that is not among them (a file of the base that holds the same defect) follows the
    review's call. FIXED is the text of the notes under `## Fixed on the way`, whose
    lines name the cheap entries a builder fixed by their numbers."""
    items, seen = list(added), []
    for read in reads:
        if not read["answered"]:
            continue
        for defect in outside_of(read):
            if defect.get("item"):
                if all(item["item"] != defect["item"] for item in items):
                    items.append(
                        {
                            "item": defect["item"],
                            "title": defect["title"],
                            "worth": FILED_BARS.get(defect["bar"]),
                        }
                    )
            elif not (defect["bar"] == "cheap" and named_by(defect["number"], fixed)):
                seen.append(seen_line(defect))
    filed, not_worth = item_lines(items)
    return filed, not_worth, seen


def item_lines(items: list[dict]) -> tuple[list[str], list[str]]:
    """The line of each item, `- `PATH`: TITLE`, under the heading its `worth` gives:
    `## Filed as not worth it` for `no`, `## Filed in the backlog` for any other."""
    filed: list[str] = []
    not_worth: list[str] = []
    for item in items:
        line = f"- `{item['item']}`" + (
            f": {item['title']}" if item.get("title") else ""
        )
        into = not_worth if (item.get("worth") or "").strip().lower() == "no" else filed
        if line not in into:
            into.append(line)
    return filed, not_worth


def names_item(line: str, path: str) -> bool:
    """Whether LINE names the item at PATH, and not another whose path starts
    the same."""
    return re.search(rf"(?<![\w./-]){re.escape(path)}(?![\w./-])", line) is not None


def placed(
    own_filed: list[str], own_not: list[str], filed: list[str], not_worth: list[str]
) -> tuple[list[str], list[str]]:
    """The lines under `## Filed in the backlog` and `## Filed as not worth it`: the
    notes' own lines (OWN_FILED, OWN_NOT), then the step's (FILED, NOT_WORTH). A notes
    line that names an item the step lists takes the place of the step's line, under the
    heading the item's `worth` gives, so no item is written twice and none under the
    other heading. The step's line of each item is found by its place in its list, which
    a notes line in any form may have taken."""
    lists = {FILED: list(filed), NOT_WORTH: list(not_worth)}
    heading_of = {
        line.split("`")[1]: heading
        for heading, lines in lists.items()
        for line in lines
    }
    slot = {
        line.split("`")[1]: index
        for lines in lists.values()
        for index, line in enumerate(lines)
    }
    own: dict[str, list[str]] = {FILED: [], NOT_WORTH: []}
    taken: set[str] = set()
    for heading, lines in ((FILED, own_filed), (NOT_WORTH, own_not)):
        for line in lines:
            path = next((path for path in heading_of if names_item(line, path)), None)
            if path is None:
                own[heading].append(line)
                continue
            into = lists[heading_of[path]]
            if path in taken:
                into.append(line)
                continue
            taken.add(path)
            into[slot[path]] = line
    return [*own[FILED], *lists[FILED]], [*own[NOT_WORTH], *lists[NOT_WORTH]]


def entry_spans(lines: list[str]) -> list[list[int]]:
    """The entries of a part of the notes as the places of their lines: a list item with
    the lines that continue it, a list item indented deeper than the entry's first line
    among them, or a paragraph's line; blank lines, a lone `none` and a heading of a
    lower level are none."""
    spans: list[list[int]] = []
    if not lines_of(lines):
        return spans
    new = True
    depth = 0
    for at, line in enumerate(lines):
        if not line.strip():
            new = True
            continue
        if line.lstrip().startswith("#"):
            new = True
            continue
        mark = re.match(r"(\s*)([-*+]|\d+[.)])\s", line)
        if new or (mark and len(mark.group(1)) <= depth):
            spans.append([at])
            depth = len(line) - len(line.lstrip())
        else:
            spans[-1].append(at)
        new = False
    return spans


def entries_of(lines: list[str]) -> list[list[str]]:
    """The entries of a part of the notes, each as its lines (`entry_spans`)."""
    return [[lines[at] for at in span] for span in entry_spans(lines)]


def called_bodies(notes: str, *, small: bool) -> list[list[str]]:
    """The parts of the notes whose lines name a finding nobody filed: `## Left open`
    and `## Seen, not filed`, and on the fast track (SMALL), whose notes have no fixed
    headings, the lines before the first heading too, where the should findings the
    review left are."""
    head, parts = sections_of(notes)
    return [
        *([head] if small else []),
        *(lines for heading, lines in parts if heading in (LEFT_OPEN, SEEN)),
    ]


def unfiled_lines(
    notes: str, *, small: bool, folder: str, in_tip: Callable[[str], bool]
) -> list[str]:
    """The first line of each entry of the notes that names a finding nobody filed and
    has neither a bar call with its reason (`under: REASON`, `cheap: REASON`) nor the
    path of an item of the backlog folder FOLDER that IN_TIP finds in the tip, in the
    parts `called_bodies` gives."""
    found = []
    for body in called_bodies(notes, small=small):
        for entry in entries_of(body):
            text = "\n".join(entry)
            if CALLED.search(text):
                continue
            paths = [
                path.rstrip(".:")
                for path in re.findall(
                    rf"(?<![\w./-]){re.escape(folder)}/[^\s`'\"()\[\],;]+", text
                )
            ]
            if any(in_tip(path) for path in paths):
                continue
            found.append(entry[0].strip())
    return found


def outside_words(read: dict, fixed: str) -> str:
    """What one review saw outside the change, for its line of the pull request's
    checks: how many defects, the items they were filed as, how many a builder fixed on
    the way (FIXED, the notes' lines under `## Fixed on the way`, names them by their
    numbers), and how many are seen and not filed. `propose` refuses while one over or
    under the bar has neither its item nor its open item in the tip, so each one is one
    of the three. Nothing for a review that saw none."""
    defects = outside_of(read)
    if not defects:
        return ""
    items = [defect["item"] for defect in defects if defect.get("item")]
    mended = sum(
        1
        for defect in defects
        if not defect.get("item")
        and defect["bar"] == "cheap"
        and named_by(defect["number"], fixed)
    )
    seen = len(defects) - len(items) - mended
    return (
        (
            f"; it saw {len(defects)} defect{'' if len(defects) == 1 else 's'} outside "
            "the change"
        )
        + (", filed as " + ", ".join(f"`{item}`" for item in items) if items else "")
        + (f"; {mended} fixed on the way" if mended else "")
        + (f"; {seen} seen, not filed" if seen else "")
    )


def sections_of(text: str) -> tuple[list[str], list[tuple[str, list[str]]]]:
    """A notes file as its lines before the first `## ` heading, and each heading with
    its lines."""
    head: list[str] = []
    parts: list[tuple[str, list[str]]] = []
    for line in text.splitlines():
        if re.fullmatch(r"## \S.*", line.rstrip()):
            parts.append((line.rstrip(), []))
        elif parts:
            parts[-1][1].append(line)
        else:
            head.append(line)
    return head, parts


def section(text: str, heading: str) -> str:
    """The lines of TEXT under HEADING, or nothing."""
    return "\n".join(
        line
        for name, lines in sections_of(text)[1]
        if name == heading
        for line in lines
    )


def lines_of(body: list[str]) -> list[str]:
    """The lines of a section with text in them, and none for a lone `none`."""
    said = [line for line in body if line.strip()]
    return [] if [line.strip().lower() for line in said] == ["none"] else said


def joined(body: list[str], more: list[str]) -> list[str]:
    """A section's lines with MORE after them: a lone `none` gives way, and a line it
    holds already is not written twice."""
    kept = lines_of(body)
    return ["", *kept, *(line for line in more if line not in kept), ""]


def with_outside(
    notes: str, filed: list[str], not_worth: list[str], seen: list[str]
) -> str:
    """The notes of the standard track with what was seen outside the change: FILED and
    NOT_WORTH, the line of each item the branch adds, under `## Filed in the backlog`
    and `## Filed as not worth it` (`placed`: a notes line that names the item takes the
    place of the step's), and SEEN under `## Seen, not filed`. A heading the notes lack
    comes after `## Filed in the backlog`, in the order `## Filed as not worth it`,
    `## Fixed on the way`, `## Seen, not filed`. Notes that get no line come back as
    they are."""
    if not filed and not not_worth and not seen:
        return notes
    head, parts = sections_of(notes)
    at = {name: index for index, (name, _) in enumerate(parts)}
    own_filed = lines_of(parts[at[FILED]][1]) if FILED in at else []
    own_not = lines_of(parts[at[NOT_WORTH]][1]) if NOT_WORTH in at else []
    items = dict(
        zip(
            (FILED, NOT_WORTH),
            placed(own_filed, own_not, filed, not_worth),
            strict=True,
        )
    )
    for heading, own in ((FILED, own_filed), (NOT_WORTH, own_not)):
        if heading in at and items[heading] != own:
            # its lines as `placed` put them; a heading the notes hold keeps its `none`
            # when no line is left
            parts[at[heading]] = (heading, ["", *(items[heading] or ["none"]), ""])
    order = (FILED, NOT_WORTH, FIXED, SEEN)
    for heading, more in (
        (FILED, items[FILED]),
        (NOT_WORTH, items[NOT_WORTH]),
        (SEEN, seen),
    ):
        if not more:
            continue
        index = next(
            (index for index, (name, _) in enumerate(parts) if name == heading), None
        )
        if index is not None:
            if heading == SEEN:
                parts[index] = (heading, joined(parts[index][1], more))
            continue
        before = order[: order.index(heading)]
        after = [index for index, (name, _) in enumerate(parts) if name in before]
        place = after[-1] + 1 if after else len(parts)
        if place and parts[place - 1][1][-1:] != [""]:
            # a heading of its own paragraph, after the lines of the one before it
            parts[place - 1][1].append("")
        parts.insert(place, (heading, ["", *more, ""]))
    out = [*head, *(line for name, lines in parts for line in (name, *lines))]
    return "\n".join(out) + ("\n" if notes.endswith("\n") else "")


def slug_of(text: str) -> str:
    """A file name from a title, as the backlog's item format has it: words joined
    by `-`."""
    slug = re.sub(r"[\W_]+", "-", text.lower()).strip("-")
    return slug if len(slug) <= SLUG_AT else slug[:SLUG_AT].rsplit("-", 1)[0]


def names_for(defect: dict) -> Iterator[str]:
    """The file names an item of this defect may take, in turn: its slug, the slug with
    a suffix from its `where` (`src/json.py:parse` gives `-json-parse`), then that with
    a number."""
    slug = slug_of(defect["title"])
    path, _, symbol = defect["where"].partition(":")
    suffix = slug_of(f"{Path(path).stem} {symbol}")
    longer = f"{slug}-{suffix}" if suffix else slug
    yield f"{slug}.md"
    if longer != slug:
        yield f"{longer}.md"
    number = 2
    while True:
        yield f"{longer}-{number}.md"
        number += 1


def item_of(file: Path) -> tuple[dict[str, str], list[str]] | None:
    """An item of the backlog as the item format has it: its front matter, and its lines
    after it, of which the first is its title (`# TITLE`). None for a file that is no
    such item."""
    try:
        text = file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    return item_text(text)


def item_text(text: str) -> tuple[dict[str, str], list[str]] | None:
    """`item_of`, from the text of the file."""
    front: dict[str, str] = {}
    head = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    if head:
        for line in head.group(1).splitlines():
            key, _, value = line.partition(":")
            front[key.strip()] = value.strip()
        text = text[head.end() :]
    lines = text.strip().splitlines()
    if not lines or not lines[0].startswith("# "):
        return None
    return front, lines


def holds(file: Path, defect: dict) -> bool:
    """Whether an item file is this defect: the same `where`, the same title, and the
    defect's run as paragraphs of the body, word for word. Any other text of the body,
    the owner's reason for a `worth: no` or a later note, leaves it the same defect."""
    item = item_of(file)
    if item is None:
        return False
    front, lines = item
    if front.get("where") != defect["where"] or lines[0][2:].strip() != defect["title"]:
        return False
    # Paragraphs as `file` writes them: `what` stripped, a blank line between
    # two paragraphs.
    body = paragraphs("\n".join(lines[1:]))
    run_of = paragraphs(defect["what"])
    return any(
        body[start : start + len(run_of)] == run_of
        for start in range(len(body) - len(run_of) + 1)
    )


def paragraphs(text: str) -> list[str]:
    return [
        part.strip() for part in re.split(r"\n[ \t]*\n", text.strip()) if part.strip()
    ]


def in_tree(task: Task, tip: str, path: str) -> bool:
    return (
        run(
            ["git", "-C", str(task.worktree), "cat-file", "-e", f"{tip}:{path}"],
            check=False,
        ).returncode
        == 0
    )


def file_at(task: Task, commit: str, path: str) -> bool:
    """Whether PATH is a file at COMMIT, and not a folder."""
    return (
        run(
            ["git", "-C", str(task.worktree), "cat-file", "-t", f"{commit}:{path}"],
            check=False,
        ).stdout.strip()
        == "blob"
    )


def base_items(task: Task, base: str) -> list[dict]:
    """Each file of the backlog folder at BASE, with its `where` and its title where it
    is an item, for the reviewer, who names in `open` the one that holds a defect
    it sees."""
    return [
        {key: item[key] for key in ("item", "where", "title")}
        for item in items_at(task, base)
    ]


def items_at(task: Task, commit: str) -> list[dict]:
    """Each file of the backlog folder at COMMIT, with its `where`, its title, its
    `worth` and the first line of its body where it is an item: one read of git
    for all."""
    folder = backlog_of(task)
    paths = [
        path
        for path in run(
            [
                "git",
                "-C",
                str(task.worktree),
                "ls-tree",
                "-r",
                "-z",
                "--name-only",
                commit,
                "--",
                folder + "/",
            ]
        ).stdout.split("\0")
        if path
    ]
    if not paths:
        return []
    out = subprocess.run(
        ["git", "-C", str(task.worktree), "cat-file", "--batch"],
        input="".join(f"{commit}:{path}\n" for path in paths).encode(),
        capture_output=True,
        check=False,
    ).stdout
    found, at = [], 0
    for path in paths:
        end = out.index(b"\n", at)
        head, at = out[at:end].split(), end + 1
        present = len(head) == 3  # noqa: PLR2004 - git's head of an object it found: its name, type and size
        size = int(head[2]) if present else 0
        item = (
            item_text(out[at : at + size].decode("utf-8", errors="replace"))
            if present
            else None
        )
        at += size + (1 if present else 0)
        found.append(item_facts(path, item))
    return found


def item_facts(path: str, item: tuple[dict[str, str], list[str]] | None) -> dict:
    """What `alike` and the reviewer are told of the file at PATH, from `item_text`: its
    `where`, its title, its `worth` and the first line of its body, each None where it
    has none."""
    front, lines = item or ({}, [])
    first = next((line.strip() for line in lines[1:] if line.strip()), None)
    return {
        "item": path,
        "where": front.get("where"),
        "title": lines[0][2:].strip() if lines else None,
        "worth": front.get("worth"),
        "first": first,
    }


def worth_at(task: Task, commit: str, path: str) -> str | None:
    """The `worth` the item at PATH says at COMMIT, lowercase, or None."""
    shown = run(
        ["git", "-C", str(task.worktree), "show", f"{commit}:{path}"], check=False
    )
    item = item_text(shown.stdout) if shown.returncode == 0 else None
    worth = item[0].get("worth") if item else None
    return worth.strip().lower() if worth else None


def someone_elses(task: Task) -> bool:
    """Whether the task's brief, or a block of its state, says that someone other than
    the owner wrote its complete request (`stages/new.md`, step 4): nobody at the
    terminal read it."""
    brief = task.directory / "brief.md"
    if brief.is_file() and SOMEONE_ELSE in [
        line.strip()
        for line in brief.read_text(encoding="utf-8", errors="replace").splitlines()
    ]:
        return True
    return any(
        record.get("event") == "task.state"
        and SOMEONE_ELSE
        in [
            str(line).strip()
            for line in [record.get("text", ""), *record.get("lines", [])]
        ]
        for record in events_of(task)
    )


def owner_says_careful(task: Task) -> bool:
    """Whether the owner's word that the task is careful is in its brief."""
    brief = task.directory / "brief.md"
    return brief.is_file() and OVERRULED in [
        line.strip()
        for line in brief.read_text(encoding="utf-8", errors="replace").splitlines()
    ]


def plan_call(text: str) -> bool:
    """Whether one text of the plan says `careful: yes` where the call stands: under its
    title, before its first `##` heading."""
    found = PLAN_CALL.search(re.split(r"(?m)^##\s", text, maxsplit=1)[0])
    return bool(found) and found.group(1).lower() == "yes"


def plan_careful(task: Task) -> bool:
    """Whether the plan called the task careful, in its text now or in any commit of the
    branch. The talk was due when the plan said yes, so a later commit that takes the
    yes back does not take back the talk, the full set or the person's merge. A step
    asks it many times, and no step writes the plan, so the first answer is kept for the
    life of this process."""
    if task.plan_said is None and criteria_of(task)["small"]:
        # the fast track has no plan: its criteria file is in the task directory, with
        # no history in git
        task.plan_said = plan_call(
            Path(criteria_of(task)["plan"]).read_text(encoding="utf-8")
        )
    if task.plan_said is None:
        plan = Path(criteria_of(task)["plan"])
        relative = plan.relative_to(task.worktree).as_posix()
        base = git(task.worktree, "merge-base", "HEAD", task.onto)
        texts = [plan.read_text(encoding="utf-8")]
        for commit in git(
            task.worktree, "log", "--format=%H", f"{base}..HEAD", "--", relative
        ).splitlines():
            shown = run(
                ["git", "-C", str(task.worktree), "show", f"{commit}:{relative}"],
                check=False,
            )
            texts.append(shown.stdout if shown.returncode == 0 else "")
        task.plan_said = any(plan_call(text) for text in texts)
    return task.plan_said


def settings_edit(task: Task, now: dict) -> str | None:
    """Why the change is careful by its edit of Lem's own settings: any edit of
    `.lem/settings.toml`, whose tables, once landed, say for every later task what is
    careful, what the checks run, who merges and where a task lands. The reason names
    each table whose values change, or says that only the file's text does. None when
    the change leaves the file alone."""
    if SETTINGS_FILE not in now["files"]:
        return None
    guards = (
        "Lem's own settings, which say for every later task what is careful, what the "
        "checks run, who merges and where a task lands"
    )
    if not in_commit(task, now["tip"], SETTINGS_FILE):
        # removed, or moved away: no table of it is edited, the whole file is gone
        return f"the change removes {SETTINGS_FILE}, {guards}"

    def tables(commit: str) -> dict:
        shown = run(
            ["git", "-C", str(task.worktree), "show", f"{commit}:{SETTINGS_FILE}"],
            check=False,
        )
        return tomllib.loads(shown.stdout) if shown.returncode == 0 else {}

    try:
        before, after = tables(now["base"]), tables(now["tip"])
    except tomllib.TOMLDecodeError:
        # in doubt, careful: what it says cannot be told
        return (
            f"the change leaves {SETTINGS_FILE} in a form that does not read as TOML, "
            "so what it says is careful cannot be told"
        )
    edited = sorted(
        name for name in {*before, *after} if before.get(name) != after.get(name)
    )
    what = (
        f"{' and '.join(f'[{name}]' for name in edited)} of {SETTINGS_FILE}"
        if edited
        else f"the text of {SETTINGS_FILE}, and no value in it"
    )
    return f"the change edits {what}, {guards}"


def in_commit(task: Task, commit: str, path: str) -> bool:
    """Whether the commit holds the file."""
    return (
        run(
            ["git", "-C", str(task.worktree), "cat-file", "-e", f"{commit}:{path}"],
            check=False,
        ).returncode
        == 0
    )


def local_settings_edit(task: Task, now: dict) -> str | None:
    """Why the change is careful by a commit of one machine's own settings:
    `.lem/settings.local.toml` is untracked by design, and a tracked copy gives every
    machine that machine's seats, naps and days the state keeps. None when the change
    leaves the file alone."""
    if LOCAL_SETTINGS_FILE not in now["files"]:
        return None
    before, after = (
        in_commit(task, now["base"], LOCAL_SETTINGS_FILE),
        in_commit(task, now["tip"], LOCAL_SETTINGS_FILE),
    )
    how = (
        "adds"
        if after and not before
        else "removes"
        if before and not after
        else "changes"
    )
    return (
        f"the change {how} {LOCAL_SETTINGS_FILE}, one machine's own settings, which "
        "git does not track: tracked, that machine's seats, naps and days the state "
        "keeps become every machine's"
    )


def review_call(task: Task) -> dict | None:
    """The careful call of the newest review that answered, as its record made it:
    `careful` and its `why`. None when no review answered, or when the newest record
    holds no call."""
    answered = [read for read in task.kept().get("reads", []) if read["answered"]]
    if not answered or "careful" not in answered[-1]:
        return None
    return {"careful": answered[-1]["careful"], "why": answered[-1]["careful_why"]}


def careful(task: Task, now: dict) -> list[str]:
    """Each reason for which this request is careful; none when it is not. The owner's
    word, the plan's own call and the newest review's are judgments against the
    project's topics; the edit of Lem's own settings, or of one machine's, is the one
    rule this script matches by itself."""
    why = []
    if owner_says_careful(task):
        why.append("the owner says so")
    if plan_careful(task):
        why.append("the plan says so")
    why.extend(
        edited
        for edited in (settings_edit(task, now), local_settings_edit(task, now))
        if edited
    )
    call = review_call(task)
    if call and call["careful"]:
        why.append(f"the review says so: {reason(call['why'])}")
    return why


def tasks_of(plan: str) -> int:
    """How many tasks the plan has: the numbered lines, or numbered headings, under its
    `## Tasks` heading."""
    section = re.search(r"(?ms)^##\s+Tasks\b[^\n]*$(.*?)(?=^##\s|\Z)", plan)
    count = (
        len(re.findall(r"(?m)^(?:###\s+)?\d+\.\s", section.group(1))) if section else 0
    )
    if not count:
        # no quiet default: the count decides which read the change gets
        raise LandError(
            "the task's plan has no `## Tasks` section with numbered tasks, and their "
            "count decides which read the change gets; the lead writes the section"
        )
    return count


def bar(task: Task, base: str, tip: str, plan: str) -> dict:
    """Where the change lowers the bar, each with the reason the plan gives for that
    file, or none."""
    # -M: a file that moved is one file, so its tests are not counted as gone and
    # come again
    return bar_of(
        git(task.worktree, "diff", "-U0", "-M", base, tip),
        git(task.worktree, "diff", "--name-status", "-M", base, tip).splitlines(),
        plan,
        changed(task, base, tip),
    )


def bar_of(diff: str, rows: list[str], plan: str, files: list[str]) -> dict:  # noqa: C901, PLR0912, PLR0915 - over the limit before the limit was set
    """The bar's result from what git gave: `diff` is `git diff -U0 -M`, `rows` the
    lines of `git diff --name-status -M`, `files` every changed path; `plan` is the
    plan's text, or "" when there is none."""
    section = re.search(r"(?ms)^##\s+The bar\s*$(.*?)(?=^##\s|\Z)", plan)
    reasons = (
        {
            found.group(1).strip(): found.group(2).strip()
            for found in re.finditer(
                r"(?m)^-\s+`?([^`:\n]+?)`?:\s+(\S.*)$", section.group(1)
            )
        }
        if section
        else {}
    )
    lowered: list[dict] = []
    asserts: dict[str, int] = {}
    # A mark counts when the change leaves more of it in a file than the file had: a
    # line that only moved, or got another space, took the mark out and put it back. A
    # mark is the same one only with the same text from the mark to the end of its line:
    # `noqa: F401` that becomes `noqa` is a wider suppression, and a new one.
    came: dict[tuple[str, str, str], list[dict]] = {}
    went: dict[tuple[str, str, str], int] = {}
    # each coverage threshold's numbers before and after, whatever file of a runner's
    # settings holds it
    thresholds: dict[str, dict[str, list[tuple[float, str]]]] = {}
    file = old = ""
    marks: list[re.Pattern] = []
    for line in diff.splitlines():
        if line.startswith("--- "):
            old = line[6:] if line.startswith("--- a/") else ""
        elif line.startswith("+++ "):
            # a file that is gone has its lines counted under the name it had
            file = line[6:] if line.startswith("+++ b/") else old
            if Path(file).suffix.lower() in DOCS:
                # a document may quote a mark, the plan's own reason for one too
                file = ""
            marks = (
                [
                    *(
                        re.compile(mark)
                        for suffixes, found in BAR.items()
                        if Path(file).suffix.lower() in suffixes
                        for mark in found
                    ),
                    *(
                        re.compile(mark)
                        for mark in TEST_CONFIG_MARKS
                        if TEST_CONFIG.search(file)
                    ),
                ]
                if file
                else []
            )
        elif not file or line[:1] not in "+-":
            continue
        else:
            # every mark of the line counts, as a runner's settings put several on
            # one line
            for hit in (found for mark in marks if (found := mark.search(line[1:]))):
                key = (file, hit.re.pattern, " ".join(line[1:][hit.start() :].split()))
                if line.startswith("+"):
                    came.setdefault(key, []).append(
                        {
                            "file": file,
                            "what": hit.group(0),
                            "line": line[1:].strip()[:160],
                        }
                    )
                else:
                    went[key] = went.get(key, 0) + 1
            if TEST_CONFIG.search(file) or WORKFLOW.search(file):
                for found in THRESHOLD.finditer(line[1:]):
                    name, number = (
                        (found.group(1), found.group(2))
                        if found.group(1)
                        else (found.group(3), found.group(4))
                    )
                    thresholds.setdefault(name, {"-": [], "+": []})[line[0]].append(
                        (float(number), file)
                    )
            if (
                TEST_FILE.search(file) or Path(file).suffix.lower() in INLINE_TESTS
            ) and ASSERTS.search(line[1:]):
                asserts[file] = asserts.get(file, 0) + (
                    1 if line.startswith("-") else -1
                )
    for key, entries in came.items():
        lowered += entries[went.get(key, 0) :]
    for name, fewer in sorted(asserts.items()):
        if fewer > 0:
            lowered.append(
                {"file": name, "what": f"{fewer} assertion(s) fewer", "line": ""}
            )
    for name, numbers in sorted(thresholds.items()):
        if not numbers["-"]:
            continue
        before, where = max(numbers["-"])
        after = min(number for number, _ in numbers["+"]) if numbers["+"] else None
        if after is None or after < before:
            said = (
                f"{name} went from {before:g} to {after:g}"
                if after is not None
                else f"{name} ({before:g}) is gone"
            )
            lowered.append({"file": where, "what": said, "line": ""})
    edited = []
    for row in rows:
        status, name, *moved = row.split("\t")
        # a test file that moved out of the tests is one the tests no longer run, as a
        # deleted one
        gone = status == "D" or (
            status.startswith("R") and moved and not TEST_FILE.search(moved[0])
        )
        if gone and TEST_FILE.search(name):
            lowered = [entry for entry in lowered if entry["file"] != name]
            lowered.append(
                {
                    "file": name,
                    "what": "a test file is deleted"
                    if status == "D"
                    else f"a test file is moved out of the tests, to {moved[0]}",
                    "line": "",
                }
            )
        # an existing file a reviewer reads first: a test, a snapshot, a runner's or a
        # workflow's settings the change edits
        now = moved[0] if moved else name
        kind = (
            "snapshot"
            if SNAPSHOT.search(now)
            else "test configuration"
            if TEST_CONFIG.search(now) or WORKFLOW.search(now)
            else "test"
            if TEST_FILE.search(now)
            else None
        )
        if kind and (status == "M" or (status.startswith("R") and status != "R100")):
            edited.append({"file": now, "kind": kind})
    for entry in lowered:
        entry["reason"] = reasons.get(entry["file"])
    covered = {suffix for suffixes in BAR for suffix in suffixes}
    not_covered = sorted(
        {Path(name).suffix.lower() for name in files} - covered - set(DOCS) - set(DATA)
    )
    return {
        "lowered": lowered,
        "not_covered": not_covered,
        "edited": sorted(edited, key=lambda entry: entry["file"]),
    }


def bar_refusal(lowered: list[dict], *, small: bool) -> str | None:
    """The checks' refusal of a bar lowered with no reason, or None. The fast track
    gives no reason: it has no plan, and a lowered bar never takes the fast track."""
    unexplained = [entry for entry in lowered if not entry["reason"]]
    if not unexplained:
        return None
    named = "; ".join(f"{entry['file']} ({entry['what']})" for entry in unexplained[:5])
    if small:
        return (
            f"a task on the fast track does not lower the bar: {named}. "
            "Take the mark out; when the change needs it, it takes the standard track, "
            "and Lem tells the developer so and takes that track, whose plan gives the "
            "reason under `## The bar`"
        )
    return (
        f"the change lowers the bar with no reason given: {named}. Take the mark out, "
        "or give the reason in the task's plan under `## The bar` as `- PATH: REASON`, "
        "where the one who reads the change sees it"
    )


# The task's one step lock: every step of `lem land` that names a task holds it for as
# long as it runs, so that two steps of one task never run at one time, in either order:
# a proposal never comes while its checks run, and `base` never rebases the worktree
# they run in. A file in the task directory; the lock is the kernel's, and it goes with
# the process, however that ends.
STEP_LOCK = "step.lock"

# What a run of the checks ends as, in its `gate.end` event.
RESULTS = ("passed", "red", "refused", "stopped")

# The checks are overdue when they run more than this many times as long as their last
# finished run: the owner's "three times longer than their last finished run" (criterion
# 5 of the plan 2026-11-19-landing-in-the-background).
OVERDUE_TIMES = 3

# And only after they ran for at least this many seconds, a minute: a last run of 0 or 1
# second (a stand-in such as `true`, rounded under load) is no measure, and three times
# it passed while five Python steps started (the guards check under tests/all.sh,
# load-gate-default-forty, 2026-11-22). The minute is the criterion of the task
# overdue-race-after-one-second-run (2026-11-22), a guess that no real suite of the
# checks ends in under a minute, not a measurement.
OVERDUE_FLOOR = 60

# How long `checks --stop` waits for the run it stopped to end: the stop of a serial
# command takes up to SERIAL_GRACE, and `criteria.py red` up to its own GRACE for each
# signal to each command it runs, and its SERIAL_GRACE for the term to a serial test's
# wrapper (its `stop`). A guess with room, not a measurement.
STOP_WAIT = 60

# How long a serial command's wrapper (`project.py serial`) gets after a term before it
# is killed: its own cleanup sends its command a term, waits 3 s, sends a kill and waits
# 3 s more (`cmd_serial`), and one second is left for its exit. Any other command gets
# one second.
SERIAL_GRACE = 7.0
GRACE = 1.0


# How often a run of the checks that waits for the load looks at it again, how often it
# logs a new `gate.wait` while it waits, and the least time between two starts of the
# checks under the gate on one machine. The spacing is a guess, not a measurement: the
# load average of one minute needs about a minute to show a run that started, so that
# the next reader sees it.
LOAD_LOOK = 15
LOAD_SAY = 300
LOAD_SPACING = 60
# Lem's own merge calls go one at a time, under this lock of the state folder.
MERGE_LOCK = "merge.lock"
# The answers of the merge agent for one tip and base that cannot be recorded: the first
# is asked again of a fresh merge agent, and at this many the next step goes on without
# one (`unread_next`).
MERGER_TRIES = 2
# The files of a moved base that a refusal names; it ends with `...` for more. The
# length of the text, not a measurement.
NAMED_FILES = 5


def load_now() -> float:
    """The machine's load average of the last minute, as `uptime` gives it."""
    return round(os.getloadavg()[0], 1)


# The words of `why` in a wait behind another run: the first in the line is one another
# task waits for and this run is not, its wait began earlier, or the two began at one
# moment and the tie-break put it first.
BEHIND_WHY = {
    "wanted": "which another task waits for",
    "longer": "which waits longer",
    "first": "which is first in the line",
}
# The line of a task that its session blocked because the base branch fails a check
# (`stages/land.md`, step 4, the same words as `lem_board_model.BASE_RED`): its `after:`
# line names the repair it waits for.
BASE_RED = "the base is red"


def wait_say(  # noqa: PLR0913 - over the limit before the limit was set
    slug: str,
    load: float,
    start: float,
    after: str | None = None,
    *,
    behind: str | None = None,
    behind_repo: str | None = None,
    why: str | None = None,
    unread: list[str] | None = None,
) -> str:
    """The one line of a run of the checks that waits, for the owner and the board.
    `behind` is the first in the line when it is another run, `behind_repo` its
    repository when that is not this run's, and `unread` the repositories whose state
    did not read at this look."""
    if behind:
        other = behind + (f" of {Path(behind_repo).name}" if behind_repo else "")
        said = (
            f"{slug}: the checks wait behind {other}, {BEHIND_WHY[why or 'first']}; "
            f"they start below {start:g}"
        )
    elif after:
        said = (
            f"{slug}: the checks wait a minute after the checks of {after} started, so "
            f"that the load shows them; then they start below {start:g}"
        )
    else:
        said = (
            f"{slug}: the checks wait for the load: {load:g}, "
            f"they start below {start:g}"
        )
    return said + "".join(
        (
            f"; the state of {Path(repo).name} does not read, "
            "so its landings count as wanted by no task"
        )
        for repo in unread or []
    )


def line_order(entries: list[dict]) -> list[dict]:
    """The machine's line of the runs that wait, first first: the ones another task
    waits for (`wanted`), then by the time each wait began (`since`), then by the task
    and the repository, so that every run reads the same first, also of two waits that
    began at one moment."""
    return sorted(
        entries,
        key=lambda entry: (
            not entry["wanted"],
            entry["since"],
            entry["task"],
            entry["repo"],
        ),
    )


def line_why(first: dict, own: dict) -> str:
    """Why FIRST goes before OWN in the line: `wanted`, `longer` or `first`
    (BEHIND_WHY)."""
    if first["wanted"] and not own["wanted"]:
        return "wanted"
    return "longer" if first["since"] < own["since"] else "first"


def waited_for(state: Path, project: ModuleType) -> set[str]:
    """The tasks that another open task of the repository whose state folder is STATE
    waits for: the slug of the `after:` line of each task whose newest state block is
    `queued`, or `blocked` with the line BASE_RED. Read with `project.py`'s own readers
    of a block. A task gone between the list of the folder and the read of its file is
    no task."""
    named = set()
    for file in sorted((state / "tasks").glob("*/state.md")):
        try:
            blocks = project.blocks_of(project.text_of(file))
        except FileNotFoundError:
            continue
        if not blocks:
            continue
        lines = [line.strip() for line in blocks[0]["lines"]]
        if blocks[0]["status"] == "queued" or (
            blocks[0]["status"] == "blocked" and BASE_RED in lines
        ):
            slug = project.after_in(lines)
            if slug:
                named.add(slug)
    return named


def line_state(project: ModuleType, repo: str) -> Path:
    """The state folder of a repository of the line, as `project.py` finds
    it (`state_root`)."""
    return project.state_root(Path(repo))


def line_wanted(entries: list[dict], own_repo: str) -> list[str]:
    """Mark each entry of the line `wanted` when another open task of its repository
    waits for it, read now from that repository's state folder, once for each
    repository. Gives the repositories whose state does not read (the checkout moved or
    is gone): for this look their entries count as wanted by no task. The run's own
    repository that does not read refuses the run, as every step does."""
    path = SCRIPTS / "project.py"
    # a stand-in in project.py's place (a test's copy of the scripts) answers commands
    # only: no task waits
    project = lem_sibling.module(path) if lem_sibling.in_form(path) else None
    named: dict[str, set[str]] = {}
    unread = []
    for repo in sorted({entry["repo"] for entry in entries}):
        if project is None:
            named[repo] = set()
            continue
        try:
            named[repo] = waited_for(line_state(project, repo), project)
        except project.SettingsError as error:
            if repo == own_repo:
                raise LandError(str(error)) from error
            named[repo] = set()
            unread.append(repo)
    for entry in entries:
        entry["wanted"] = entry["task"] in named[entry["repo"]]
    return unread


def line_join(folder: Path, slug: str, repo: str, pid: int) -> dict:
    """The run's own entry in the line, made under the hold of LOAD_LOCK: its file
    `PID.json`, locked for the whole wait, with the task, its repository and the time
    its wait began, written whole once."""
    folder.mkdir(parents=True, exist_ok=True)
    file = folder / f"{pid}.json"
    # "a+" and a truncate after the lock: a file is emptied only by the one that
    # holds it
    handle = file.open("a+", encoding="utf-8")
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        handle.close()
        raise LandError(
            f"the line of the load gate holds {file} for a run that still waits, with "
            f"this process's id {pid}; `lem land checks --status` of the "
            "task says which run waits"
        ) from None
    entry = {"task": slug, "repo": repo, "since": time.time()}
    handle.seek(0)
    handle.truncate()
    handle.write(json.dumps({"pid": pid, **entry}) + "\n")
    handle.flush()
    return {**entry, "name": file.name, "file": file, "handle": handle}


def line_leave(own: dict) -> None:
    """The run leaves the line: its file goes, then its lock with the handle. A reader
    that opened the file before it went reads it as held, and one that opens it after
    finds no file."""
    with contextlib.suppress(FileNotFoundError):
        own["file"].unlink()
    own["handle"].close()


def line_live(folder: Path, own_name: str) -> list[dict]:
    """The other runs that wait, under the hold of LOAD_LOCK. An entry is live while a
    process holds its file's lock, however late its look comes; a lock that a shared try
    takes is held by no process, so its run is gone (it ended, was stopped or killed, or
    died in the middle of its write), and its file is removed. Nothing else ends
    an entry."""
    live = []
    for file in sorted(folder.glob("*.json")):
        if file.name == own_name:
            continue
        try:
            handle = file.open("r", encoding="utf-8")
        except FileNotFoundError:
            continue
        with handle:
            try:
                fcntl.flock(handle, fcntl.LOCK_SH | fcntl.LOCK_NB)
            except BlockingIOError:
                try:
                    record = json.loads(handle.read())
                except ValueError:
                    record = None
                # a held file is written whole under LOAD_LOCK, which this look holds;
                # one that does not read is no run
                if (
                    isinstance(record, dict)
                    and isinstance(record.get("task"), str)
                    and isinstance(record.get("repo"), str)
                    and isinstance(record.get("since"), (int, float))
                ):
                    live.append(
                        {
                            "task": record["task"],
                            "repo": record["repo"],
                            "since": record["since"],
                            "name": file.name,
                        }
                    )
                continue
            with contextlib.suppress(FileNotFoundError):
                file.unlink()
    return live


def gate_look(lock: TextIO, folder: Path, own: dict, load: float, start: float) -> dict:
    """One look of a run that waits, under the hold of LOAD_LOCK (LOCK, the open lock
    file, which holds the last start): the line now, read whole, and whether this run
    starts. It starts only when it is first in the line, the load is below START and
    LOAD_SPACING passed since the last start; then it writes the last start and leaves
    the line in the same hold. Otherwise the reason it waits: `behind` the first, also
    while the load is above the number; `load`; or `after` the last start, with
    its `gap`."""
    entries = [*line_live(folder, own["name"]), own]
    unread = line_wanted(entries, own["repo"])
    first = line_order(entries)[0]
    if first is not own:
        return {
            "go": False,
            "reason": "behind",
            "behind": first["task"],
            "behind_repo": first["repo"] if first["repo"] != own["repo"] else None,
            "why": line_why(first, own),
            "unread": unread,
        }
    if load >= start:
        return {"go": False, "reason": "load", "unread": unread}
    lock.seek(0)
    try:
        last = json.loads(lock.read() or "null")
    except ValueError:
        last = None
    gap = (
        time.time() - last["at"]
        if isinstance(last, dict) and isinstance(last.get("at"), (int, float))
        else None
    )
    if gap is not None and isinstance(last, dict) and 0 <= gap < LOAD_SPACING:
        return {
            "go": False,
            "reason": "after",
            "after": str(last.get("task") or "another task"),
            "gap": gap,
            "unread": unread,
        }
    lock.seek(0)
    lock.truncate()
    lock.write(
        json.dumps({"at": time.time(), "task": own["task"], "repo": own["repo"]}) + "\n"
    )
    lock.flush()
    line_leave(own)
    return {"go": True, "unread": unread}


def wait_for_load(task: Task, pid: int | None = None) -> dict | None:
    """Wait, before the first command of the checks, until this run is first in the
    machine's one line of the runs that wait (`line_order`), the machine's load average
    is below the start number of this machine (`lem_state.load_start`), and LOAD_SPACING
    seconds passed since the last start under the gate on this machine, of any
    repository. The run is in the line from its first look to its end, by its own locked
    file (`line_join`, PID the file's name); it leaves the line when it starts, and in a
    `finally` when its wait ends in any other way, and a run that is killed leaves it by
    the lock it loses. Logs `gate.wait` when it waits, again when the reason or the
    first in the line changes and each LOAD_SAY seconds. None when the developer took
    the gate away on this machine. The number is read again at each look, so that a run
    that waits takes the developer's new number, or starts at once when he took the
    gate away."""
    home = lem_state.machine_file().parent
    folder = home / lem_state.LOAD_LINE
    said: tuple[tuple, float] | None = None
    waited = False
    own: dict | None = None
    try:
        while True:
            try:
                start = lem_state.load_start()
            except lem_state.StateError as error:
                raise LandError(str(error)) from error
            if start is None:
                return {"start": None, "waited": waited} if waited else None
            load = load_now()
            folder.mkdir(parents=True, exist_ok=True)
            with (home / lem_state.LOAD_LOCK).open("a+", encoding="utf-8") as handle:
                # one look at a time on the machine: no look reads the line while
                # another changes it
                fcntl.flock(handle, fcntl.LOCK_EX)
                if own is None:
                    own = line_join(
                        folder,
                        task.slug,
                        str(task.main),
                        os.getpid() if pid is None else pid,
                    )
                look = gate_look(handle, folder, own, load, start)
            if look["go"]:
                own = None
                return {"start": start, "load": load, "waited": waited}
            unread = look["unread"]
            # a new line when the reason or the first in the line changed, or after
            # LOAD_SAY seconds of the same
            reason = (
                look["reason"],
                look.get("behind"),
                look.get("behind_repo"),
                look.get("why"),
                tuple(unread),
            )
            if (
                said is None
                or said[0] != reason
                or time.monotonic() - said[1] >= LOAD_SAY
            ):
                fields = [f"after={look['after']}"] if look["reason"] == "after" else []
                if look["reason"] == "behind":
                    fields += [
                        f"behind={look['behind']}",
                        *(
                            [f"behind_repo={look['behind_repo']}"]
                            if look["behind_repo"]
                            else []
                        ),
                        f"why={look['why']}",
                    ]
                # the first repository whose state did not read; the line for the owner
                # names each
                fields += [f"unread={unread[0]}"] if unread else []
                say = wait_say(
                    task.slug,
                    load,
                    start,
                    look.get("after"),
                    behind=look.get("behind"),
                    behind_repo=look.get("behind_repo"),
                    why=look.get("why"),
                    unread=unread,
                )
                script(
                    "project.py",
                    task.worktree,
                    "log",
                    task.slug,
                    "gate.wait",
                    f"load:={load}",
                    f"start:={start:g}",
                    *fields,
                    f"say={say}",
                )
                said = (reason, time.monotonic())
                waited = True
            time.sleep(
                min(LOAD_LOOK, max(1.0, LOAD_SPACING - look["gap"]))
                if look["reason"] == "after"
                else LOAD_LOOK
            )
    finally:
        if own is not None:
            line_leave(own)


def seconds_since(stamp: str, now: datetime | None = None) -> int:
    """The whole seconds from a stamp of the form `now_utc` writes to now."""
    then = datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    return max(0, int(((now or datetime.now(UTC)) - then).total_seconds()))


def duration(seconds: float) -> str:
    """Seconds in the words a person reads: `26 s`, `4 min 26 s`, `14 min`."""
    minutes, rest = divmod(int(seconds), 60)
    if not minutes:
        return f"{rest} s"
    return f"{minutes} min" + (f" {rest} s" if rest else "")


def checks_say(
    slug: str,
    result: str,
    *,
    red: list[str] | None = None,
    refused: str | None = None,
    next_due: str | None = None,
) -> str:
    """The one line for the owner at the end of a run of the checks: the slug, the
    result and the next step, with no question. `red` names the commands that failed,
    `refused` what the checks refused, and `next_due` is what `due` says after a passed
    run (`review`, `none` or `owner`)."""
    if result == "passed":
        if next_due in ("none", "owner"):
            return (
                f"{slug}: the checks passed; no review is due, so it is proposed, "
                "nothing for you"
            )
        return f"{slug}: the checks passed; the review runs, nothing for you"
    if result == "red":
        return (
            f"{slug}: the checks are red on {' and '.join(red or ['a command'])}; "
            "a builder repairs it, nothing for you"
        )
    if result == "refused":
        return (
            f"{slug}: the checks refused the change: "
            f"{refused or 'the step met an error'}; a builder repairs it, "
            "nothing for you"
        )
    if result == "stopped":
        return f"{slug}: the checks were stopped; the landing waits for your word"
    raise ValueError(
        f"a run of the checks ends as one of {', '.join(RESULTS)}, not {result!r}"
    )


def last_seconds(events: list[dict]) -> int | None:
    """The length of the checks' last finished run: the `seconds` of the newest
    `gate.end` whose result is `passed`, of any task. A red run stops before the serial
    commands, and would make the next run look overdue; with no such run there
    is none."""
    ends = [
        event
        for event in events
        if event.get("event") == "gate.end"
        and event.get("result") == "passed"
        and isinstance(event.get("seconds"), int)
    ]
    return ends[-1]["seconds"] if ends else None


def is_overdue(seconds: int | None, last: int | None) -> bool:
    """Whether a run that has gone on for `seconds` runs more than OVERDUE_TIMES as long
    as the last finished one, and for at least OVERDUE_FLOOR seconds. A last run of a
    few seconds (a stand-in command such as `true`) has no length to multiply: three
    times 0 or 1 second would call a run overdue while its processes start."""
    return (
        seconds is not None
        and last is not None
        and seconds >= OVERDUE_FLOOR
        and seconds > OVERDUE_TIMES * last
    )


def overdue_say(slug: str, seconds: int, last: int) -> str:
    return (
        f"{slug}: the checks run for {duration(seconds)}, more than three times their "
        f'last run of {duration(last)}; "stop the checks" stops them'
    )


def resumed_line(slug: str, end: dict) -> str:
    """The line for a session that did not start the run: its result, as past, and the
    next step as it is now, not as the session that saw the run end took it. A stopped
    run waits for the owner's word; after any other, the landing goes on from its first
    step, as after a cut-off."""
    result = end.get("result")
    after = (
        "the landing waits for your word"
        if result == "stopped"
        else "the landing goes on from its first step, as after a cut-off"
    )
    return (
        f"{slug}: its last run of the checks ended at {utc(end['ts'])}, "
        f"{result}; {after}"
    )


def ended_of(end: dict | None, slug: str) -> dict | None:
    """The newest end of a task's checks, as `--status` and `--stop` print it."""
    if end is None:
        return None
    return {
        "at": end["ts"],
        "tip": end.get("tip"),
        "result": end.get("result"),
        "seconds": end.get("seconds"),
        "say": end.get("say"),
        "resumed": resumed_line(slug, end),
    }


def holder_of(path: Path) -> dict | None:
    """The step the lock file names, its process and its start, or none: the holder
    writes the line after it takes the lock and takes it away before it lets the
    lock go."""
    try:
        found = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if (
        not isinstance(found, dict)
        or not isinstance(found.get("pid"), int)
        or not isinstance(found.get("step"), str)
    ):
        return None
    return found


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def held_refusal(slug: str, step: str, holder: dict | None) -> str:
    """Why a step of a task may not run now: another step of the same task holds
    its lock."""
    if holder is None:
        return (
            f"another step of {slug} runs now and holds its lock ({STEP_LOCK} in its "
            "task directory); it ends first, then this step runs again"
        )
    when = (
        f"since {utc(holder['since'])}, in process {holder['pid']}"
        if isinstance(holder.get("since"), str)
        else f"in process {holder['pid']}"
    )
    status = f"`lem land checks {slug} --status` says whether they still run"
    if holder["step"] == "checks" and step == "checks":
        return (
            f"the checks of {slug} already run ({when}): a second run is refused. "
            f"The session that started them goes on when they end; {status}"
        )
    if holder["step"] == "checks":
        return (
            f"the checks of {slug} run ({when}), and their end comes first: "
            "the session that started them goes on when they end, "
            f"and this step waits for it; {status}"
        )
    return (
        f"another step of {slug} runs now, `lem land {holder['step']} {slug}` "
        f"({when}); it ends first, then this step runs again"
    )


@contextlib.contextmanager
def step_lock(task: Task, step: str) -> Generator[None, None, None]:
    """Hold the task's one step lock for as long as the step runs, however it ends, with
    the step's name, process and start in its file; a step of the same task meanwhile is
    refused with that holder. The commands a step starts do not get the lock's file
    (Popen closes it in them), so a server a command left behind does not hold it."""
    path = task.directory / STEP_LOCK
    try:
        handle = path.open("a+", encoding="utf-8")
    except OSError as error:
        raise LandError(
            f"the step lock {path} cannot be opened ({error.strerror}); "
            f"it holds no state, so remove it (`rm -r {path}`) and run "
            f"`lem land {step} {task.slug}` again",
        ) from error
    with handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise LandError(held_refusal(task.slug, step, holder_of(path))) from None
        handle.seek(0)
        handle.truncate()
        handle.write(
            json.dumps({"step": step, "pid": os.getpid(), "since": lem_clock.stamp()})
            + "\n"
        )
        handle.flush()
        try:
            yield
        finally:
            # the holder's line goes with the hold, so that a look at the file never
            # names a step that ended
            handle.seek(0)
            handle.truncate()
            handle.flush()


def running_checks(task: Task) -> dict | None:
    """The run of the task's checks that holds its step lock now, or none. A look at the
    file and at the process it names, never at the lock itself, so that a look never
    makes a real start fail."""
    holder = holder_of(task.directory / STEP_LOCK)
    if holder is None or holder["step"] != "checks" or not alive(holder["pid"]):
        return None
    return holder


def gate_ends(task: Task) -> list[dict]:
    """Every end of a run of the checks in the repository's event log, of any task,
    oldest first."""
    log = task.directory.parent.parent / "events.jsonl"
    found = []
    for line in (
        lem_state.jsonl_lines(log.read_text(encoding="utf-8")) if log.is_file() else []
    ):
        if '"gate.end"' not in line:
            continue
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if record.get("event") == "gate.end":
            found.append(record)
    return found


def waits_of(task: Task, since: str) -> dict | None:
    """The newest `gate.wait` of the task's run that holds the step lock since `since`,
    while no `gate.start` came after it: the run waits at the load gate, for the load or
    behind another run."""
    log = task.directory.parent.parent / "events.jsonl"
    found = None
    for line in (
        lem_state.jsonl_lines(log.read_text(encoding="utf-8")) if log.is_file() else []
    ):
        if f'"{task.slug}"' not in line or '"gate.' not in line:
            continue
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if record.get("task") != task.slug or str(record.get("ts", "")) < since:
            continue
        if record.get("event") == "gate.wait":
            found = record
        elif record.get("event") == "gate.start":
            found = {"started": record["ts"]}
    return found


def checks_status(task: Task) -> dict:
    """Whether the task's checks run, for how long, against their last finished run, and
    how the last run ended. A run that waits at the load gate says so in `waits`, and
    its time counts from its start."""
    holder = running_checks(task)
    ends = gate_ends(task)
    last = last_seconds(ends)
    since = holder.get("since") if holder else None
    seen = waits_of(task, since) if isinstance(since, str) else None
    waits = None
    if seen and "started" in seen:
        since = seen["started"]
    elif seen:
        # the run holds the lock and waits for the load or behind another run: none of
        # its commands started yet
        waits = {
            key: seen[key]
            for key in ("load", "start", "after", "behind", "behind_repo", "why", "say")
            if key in seen
        }
    seconds = seconds_since(since) if isinstance(since, str) and not waits else None
    overdue = holder is not None and is_overdue(seconds, last)
    own = [end for end in ends if end.get("task") == task.slug]
    lock_holder = holder_of(task.directory / STEP_LOCK)
    return {
        "task": task.slug,
        "running": holder is not None,
        "pid": holder["pid"] if holder else None,
        "since": since,
        "seconds": seconds,
        "waits": waits,
        # the step that holds the lock when it is not the checks: a step of the task
        # waits for it too
        "step": lock_holder["step"]
        if lock_holder and lock_holder["step"] != "checks" and alive(lock_holder["pid"])
        else None,
        "last_seconds": last,
        "overdue": overdue,
        "say": overdue_say(task.slug, seconds, last)
        if overdue and seconds is not None and last is not None
        else None,
        "ended": ended_of(own[-1] if own else None, task.slug),
    }


def checks_stop(task: Task) -> dict:
    """Stop the task's checks: a term to the process the lock names, only while the lock
    is held by `checks`, and a wait until that run let it go. With no run, nothing is
    stopped and that is no error."""

    def stop_result(pid: int | None) -> dict:
        return {
            "task": task.slug,
            "stopped": pid is not None,
            "pid": pid,
            "ended": checks_status(task)["ended"],
        }

    holder = running_checks(task)
    if holder is None:
        return stop_result(None)
    pid = holder["pid"]
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return stop_result(None)
    except PermissionError as error:
        raise LandError(
            f"the checks of {task.slug} run in process {pid}, which this user may not "
            f"stop ({error.strerror}); the user that started them stops them"
        ) from error
    deadline = time.monotonic() + STOP_WAIT
    while time.monotonic() < deadline:
        now = holder_of(task.directory / STEP_LOCK)
        # the run takes its line away last, after its commands ended and its result
        # is kept
        if not alive(pid) or now is None or now["pid"] != pid:
            return stop_result(pid)
        time.sleep(0.1)
    raise LandError(
        f"the checks of {task.slug} were asked to stop, and process {pid} still runs "
        f"after {STOP_WAIT} s; `lem land checks {task.slug} --stop` asks again, and "
        f"`lem land checks {task.slug} --status` says whether they still run",
    )


def criteria_red(task: Task) -> subprocess.CompletedProcess:
    """`lem criteria red` as a process of its own, as `lem_sibling` runs it (`APART`).
    On a stop of the checks it gets a term and its end is waited for, so that its own
    handler ends its tests and removes its two worktrees: it is never killed first, as
    `subprocess.run` does on an exception."""
    args = [
        sys.executable,
        "-B",
        str(SCRIPTS / "criteria.py"),
        "--repo",
        str(task.main),
        "red",
        task.slug,
    ]
    with (
        tempfile.TemporaryFile("w+", encoding="utf-8") as out,
        tempfile.TemporaryFile("w+", encoding="utf-8") as err,
    ):
        proc = subprocess.Popen(args, stdout=out, stderr=err, stdin=subprocess.DEVNULL)
        try:
            code = proc.wait()
        except KeyboardInterrupt:
            proc.send_signal(signal.SIGTERM)
            try:
                proc.wait(timeout=STOP_WAIT)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
            raise
        out.seek(0)
        err.seek(0)
        return subprocess.CompletedProcess(args, code, out.read(), err.read())


def cmd_checks(task: Task) -> dict:
    """The machine checks on the tip: the commands, the serial ones, the criteria's
    tests, or the polish pass's run of them when its five inputs are the same now
    (`taken_from_polish`), and the bar. The step's SIGTERM handler holds from its first
    line to its last, the criteria's tests and the bar included: a stop ends what runs
    and keeps no result."""
    flags = {"stopping": False, "done": False}

    def stopped(*_: object) -> None:
        # one stop is enough: a second term, or one after the result is kept,
        # changes nothing
        if flags["stopping"] or flags["done"]:
            return
        flags["stopping"] = True
        raise KeyboardInterrupt

    before = signal.signal(signal.SIGTERM, stopped)
    try:
        return checks_run(task, flags)
    finally:
        signal.signal(signal.SIGTERM, before)


def checks_run(task: Task, flags: dict) -> dict:
    stopped = (
        "the checks were stopped before their first command; "
        f"`lem land checks {task.slug}` runs them again"
    )
    try:
        tip, found, commands = checks_ready(task)
    except KeyboardInterrupt:
        raise LandError(stopped) from None
    try:
        # the load gate, after every refusal the step makes before it runs anything, so
        # that a run that would be refused does not wait first
        gated = wait_for_load(task)
    except KeyboardInterrupt:
        # a stop while the run waits: its one `gate.end`, so that the board's wait ends
        # and `--status` gives the end
        with contextlib.suppress(LandError):
            # the stop is the step's refusal, also when the event log refuses the end
            script(
                "project.py",
                task.worktree,
                "log",
                task.slug,
                "gate.end",
                "result=stopped",
                "seconds:=0",
                f"tip={tip[:9]}",
                f"say={checks_say(task.slug, 'stopped')}",
            )
        raise LandError(stopped) from None
    logs = task.directory / "gate"
    logs.mkdir(exist_ok=True)
    # The commands that need the machine to themselves come after the others, each under
    # the repository's one lock for them (`project.py serial`), and only when the others
    # passed. The field of their result and of their `gate` event is `serial`, which the
    # board reads. The output folder and the events are named `gate`, which the
    # board reads.
    serial = task.settings["checks"]["serial"]
    started = time.monotonic()
    ended: list[str] = []

    def end(how: str, say: str) -> None:
        """The one `gate.end` of the run, however it ends."""
        if not ended:
            ended.append(how)
            # a run that took the polish pass's result logs no `task.red`: its end names
            # the pass's commit
            taken = taken_at(result.get("criteria"))
            script(
                "project.py",
                task.worktree,
                "log",
                task.slug,
                "gate.end",
                f"result={how}",
                f"seconds:={round(time.monotonic() - started)}",
                f"tip={tip[:9]}",
                *([f"taken={taken}"] if taken else []),
                f"say={say}",
            )

    # No result of an earlier run stays while this one runs: a run cut off with no
    # chance to clean up (a kill) leaves none for its tip either.
    task.keep(gated=None, tree=None)
    # the start of the checks: the board draws them from here to their last result
    script(
        "project.py",
        task.worktree,
        "log",
        task.slug,
        "gate.start",
        f"tip={tip[:9]}",
        f"commands:={len(commands) + len(serial)}",
    )
    result: dict = {
        "task": task.slug,
        "tip": tip,
        "green": None,
        "commands": [],
        "load": gated,
    }
    try:
        outcome, refusal = checks_body(
            task, flags, tip, found, commands, serial, logs, result
        )
        flags["done"] = True
    except KeyboardInterrupt:
        # a stop: what ran is ended, and no result is kept
        flags["done"] = True
        task.keep(gated=None, tree=None)
        result.update(result="stopped", say=checks_say(task.slug, "stopped"))
        end("stopped", result["say"])
        print(json.dumps(result, indent=2))
        raise LandError(
            "the checks were stopped, and the command that ran is ended with what it "
            f"started; `lem land checks {task.slug}` runs them again"
        ) from None
    except Exception:
        # an error of the step itself (git, the event log): the run ends, refused, and
        # the error is the step's exit
        flags["done"] = True
        task.keep(gated=None, tree=None)
        result.update(result="refused", say=checks_say(task.slug, "refused"))
        with contextlib.suppress(LandError):
            # the error may be the event log's own: the step's error is the one to say
            end("refused", result["say"])
        print(json.dumps(result, indent=2))
        raise
    end(outcome, result["say"])
    if refusal:
        print(json.dumps(result, indent=2))
        raise LandError(refusal)
    return result


def checks_ready(task: Task) -> tuple[str, dict, list[str]]:
    """What the checks refuse before their first command, and what they run on: the tip,
    the criteria and the commands."""
    task.need_landing()
    task.need_worktree()
    if "base" not in task.kept():
        raise LandError(
            f"`lem land base {task.slug}` comes first: "
            "the checks run on the tip that will land"
        )
    tip = git(task.worktree, "rev-parse", "HEAD")
    # Before any command runs: the review reads the code as it will merge, so the polish
    # pass comes first.
    try:
        found = criteria_of(task)
    except LandError as error:
        raise LandError(
            f"{error}. A builder repairs the test or the plan; "
            "the check is never edited to pass"
        ) from error
    missing = polish_missing(task, tip, found)
    if missing:
        raise LandError(missing)
    commands = task.gate()[0]
    if not commands:
        # `start` refuses a project with none; the main checkout's settings may lose
        # them after it
        task.keep(gated=None, tree=None)
        raise LandError(
            "the checks have no command to run, and checks that ran nothing show "
            f"nothing: {NO_GATE} in the main checkout's .lem/settings.toml, and the "
            "branch brings none that the base commit lacks. Add the commands to "
            f"checks.commands there, then run `lem land checks {task.slug}` again",
        )
    return tip, found, commands


def checks_body(  # noqa: C901, PLR0911, PLR0912, PLR0913, PLR0915, PLR0917 - over the limit before the limit was set
    task: Task,
    flags: dict,
    tip: str,
    found: dict,
    commands: list[str],
    serial: list[str],
    logs: Path,
    result: dict,
) -> tuple[str, str | None]:
    """The run itself: the commands, the serial ones, the criteria's tests (or the
    polish pass's result of them, `taken_from_polish`) and the bar. It fills `result`
    with what the step prints, its `say` among it, and gives back how the run ends and
    the refusal to exit with, none for a passed run."""
    # An ignored `__pycache__` that was there before the run is a leftover of someone's
    # Python (a builder's test run without `-B`), not of these commands, and a suite
    # that looks for bytecode would go red on it with no defect of the code. Python
    # rebuilds it from the source, so it goes before the first command; every other
    # ignored file stays. Each folder is named once it is gone.
    result["removed_bytecode"] = []
    for folder in stale_bytecode(task):
        remove_bytecode(task, folder)
        result["removed_bytecode"].append(folder)
    # What git does not know before the first command. `need_worktree` refused any such
    # file, so this is empty unless something wrote one since; it is taken all the same,
    # so that the removal after the run can never reach a file that was there before it.
    there = untracked(task)
    results = result["commands"]
    running: list[subprocess.Popen] = []
    grace = GRACE
    output = logs / "01.log"
    try:
        for number, (command, apart) in enumerate(
            [
                *((command, False) for command in commands),
                *((command, True) for command in serial),
            ],
            start=1,
        ):
            if apart and any(entry["exit"] != 0 for entry in results):
                break
            output = logs / f"{number:02d}.log"
            line: str | list[str] = command
            grace = SERIAL_GRACE if apart else GRACE
            if apart:
                line = [
                    sys.executable,
                    "-B",
                    str(SCRIPTS / "project.py"),
                    "--repo",
                    str(task.main),
                    "serial",
                    "--",
                    command,
                ]
            with output.open("w", encoding="utf-8") as handle:
                # a group of its own, as criteria.py runs a test: what the command
                # starts ends with it
                proc = subprocess.Popen(
                    line,
                    shell=not apart,
                    cwd=task.worktree,
                    stdout=handle,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    start_new_session=True,
                )
                running.append(proc)
                code = proc.wait()
                end_group(running, grace)
            lines = [
                text
                for text in output.read_text(
                    encoding="utf-8", errors="replace"
                ).splitlines()
                if text.strip()
            ]
            last = lines[-1].strip() if lines else ""
            results.append(
                {
                    "command": command,
                    "exit": code,
                    "last": last,
                    "output": str(output),
                    **({"serial": True} if apart else {}),
                }
            )
            script(
                "project.py",
                task.worktree,
                "log",
                task.slug,
                "gate",
                f"command={command}",
                f"exit:={code}",
                f"last={last}",
                f"tip={tip[:9]}",
                *(["serial:=true"] if apart else []),
            )
    finally:
        # a stop ends the command that runs with its group; a serial command's wrapper
        # gets the time of its own cleanup
        end_group(running, grace)
        # A file the commands wrote that git neither tracks nor ignores (Python's
        # bytecode in a repository with no rule for it) is the run's output, and nothing
        # of it lands: it goes, with the folders it leaves empty, red, green or stopped,
        # so that the next step finds the worktree clean. The worktree is the task's
        # own, made by Lem.
        removed = sorted(set(untracked(task)) - set(there))
        for path in removed:
            remove_left(task, path)
        if removed:
            with output.open("a", encoding="utf-8") as handle:
                handle.write(
                    "land.py removed what the commands of the checks left untracked: "
                    f"{', '.join(removed)}\n"
                )
        result["removed_untracked"] = removed
    green = all(entry["exit"] == 0 for entry in results)
    result.update(green=green, polish=task.kept().get("polish"))
    # A command of the checks that changed a tracked file, or made a commit, changed the
    # tree it just judged.
    dirty = git(task.worktree, "status", "--porcelain")
    if green and dirty:
        result.update(
            result="refused",
            say=checks_say(
                task.slug,
                "refused",
                refused="a command of the checks changed what git tracks",
            ),
        )
        return "refused", (
            "a command of the checks changed what git tracks, so its result is about "
            f"another tree:\n{dirty}\n"
            f"put the files back (`git -C {task.worktree} checkout -- FILE`) and make "
            "the command change no tracked file, then run this again"
        )
    moved = git(task.worktree, "rev-parse", "HEAD")
    if green and moved != tip:
        result.update(
            result="refused",
            say=checks_say(
                task.slug,
                "refused",
                refused="a command of the checks made a commit on the branch",
            ),
        )
        return "refused", (
            "a command of the checks made a commit on the branch "
            f"({tip[:9]}..{moved[:9]}), so its result is about another tree: "
            "make the command commit nothing, put the branch back with "
            f"`git -C {task.worktree} reset --hard {tip}`, then run this again"
        )
    if not green:
        red = [entry["command"] for entry in results if entry["exit"] != 0]
        result.update(result="red", say=checks_say(task.slug, "red", red=red))
        return (
            "red",
            (
                f"the checks are red on {len(red)} command(s): {'; '.join(red)}. "
                "A builder reads the output files; the checks are never edited to pass"
            ),
        )
    # The commands of the checks are green. Now what no command of the project checks:
    # that each criterion is held by a test that fails without the change, and that the
    # change did not lower the bar.

    def criteria_refused(stderr: str) -> tuple[str, str]:
        """The run refused by the check of the criteria, in the words its
        script gave."""
        result.update(
            result="refused",
            say=checks_say(
                task.slug, "refused", refused="the check of the criteria did not pass"
            ),
        )
        return (
            "refused",
            (
                f"{stderr.strip().removeprefix('criteria.py: ')}. A builder repairs "
                "the test or the plan; the check is never edited to pass"
            ),
        )

    taken = None
    if not found["small"]:
        # A new read of the criteria, here and not the one `checks_ready` made before
        # the load wait and the commands: an approval or a recorded change since then
        # counts. It refuses as a run of the tests would.
        read = script("criteria.py", task.main, "inputs", task.slug, check=False)
        if read.returncode != 0:
            result["criteria"] = None
            return criteria_refused(read.stderr)
        taken = taken_from_polish(
            task.kept().get("polish"), json.loads(read.stdout)["inputs"], small=False
        )
    if taken:
        # the pass ran these tests on this tip, against this base commit, plan file and
        # settings: they run no second time
        result["criteria"] = taken
    else:
        held = criteria_red(task)
        try:
            result["criteria"] = json.loads(held.stdout)
        except ValueError:
            result["criteria"] = None
        if held.returncode != 0:
            return criteria_refused(held.stderr)
    # The fast track gives no reason for a lowered bar: it has no plan, and a lowered
    # bar never takes the fast track.
    plan = "" if found["small"] else Path(found["plan"]).read_text(encoding="utf-8")
    now = change(task)
    result["bar"] = bar(task, now["base"], tip, plan)
    result["size"] = {
        "files": len(now["files"]),
        "lines": now["lines"],
        "in_parts": now["lines"] > READ_AT,
    }
    refused = bar_refusal(result["bar"]["lowered"], small=found["small"])
    if refused:
        result.update(
            result="refused",
            say=checks_say(
                task.slug,
                "refused",
                refused="the change lowers the bar with no reason given",
            ),
        )
        return "refused", refused
    try:
        next_due = due(task)["due"]
    except LandError:
        # `read` says what stops it; the next step is still the review's
        next_due = "review"
    result.update(
        result="passed", say=checks_say(task.slug, "passed", next_due=next_due)
    )
    # From here a stop changes nothing: the run passed, and its result is kept whole.
    flags["done"] = True
    task.keep(
        gated=tip,
        tree=git(task.worktree, "rev-parse", f"{tip}^{{tree}}"),
        checks={
            "commands": results,
            "criteria": result["criteria"],
            "bar": result["bar"],
            "size": result["size"],
        },
    )
    return "passed", None


def end_group(running: list[subprocess.Popen], grace: float = GRACE) -> None:
    """End each command's process group and everything still in it: a term first, then a
    kill for what is left after `grace` seconds (a second, or the time of a serial
    wrapper's own cleanup). A group that ends within its grace gets no kill."""
    for proc in running:
        lem_proc.stop_group(proc, grace, GRACE, whole_group=True)
    running.clear()


def untracked(task: Task) -> list[str]:
    """Each file of the worktree that git neither tracks nor ignores, one by one, a file
    in a new folder too."""
    listed = run(
        [
            "git",
            "-C",
            str(task.worktree),
            "status",
            "--porcelain",
            "--untracked-files=all",
            "-z",
        ]
    ).stdout.split("\0")
    return [entry[3:] for entry in listed if entry.startswith("?? ")]


def bytecode_candidates(listed: list[str]) -> list[str]:
    """Each folder named `__pycache__` in git's list of what it ignores
    (`ls-files --ignored --directory`), which names a folder with its final slash: a
    file or a link of that name is none."""
    return sorted(
        entry
        for entry in listed
        if entry.endswith("/") and entry.rstrip("/").rsplit("/", 1)[-1] == "__pycache__"
    )


def folders_above(candidates: list[str]) -> list[str]:
    """Each proper folder above a candidate (`build` for `build/__pycache__/`), the
    paths whose ignore rules the choice asks git for."""
    found: set[str] = set()
    for candidate in candidates:
        parts = candidate.rstrip("/").split("/")[:-1]
        found.update("/".join(parts[:depth]) for depth in range(1, len(parts) + 1))
    return sorted(found)


def bytecode_of(listed: list[str], ignored: set[str]) -> list[str]:
    """The `__pycache__` folders the checks remove before their first command, from
    git's two lists: the ignored paths of the worktree, and the folders above a
    candidate that a rule ignores. A `__pycache__` inside an ignored folder is part of
    that folder and stays, also when git lists it on its own because that folder holds a
    tracked file."""
    return [
        candidate
        for candidate in bytecode_candidates(listed)
        if not set(folders_above([candidate])) & ignored
    ]


def nul_paths(output: bytes) -> list[str]:
    """The paths of git's `-z` output, each as the file system names it: never through
    text mode, which turns a `\\r` in a name into `\\n`."""
    return [os.fsdecode(entry) for entry in output.split(b"\0") if entry]


def stale_bytecode(task: Task) -> list[str]:
    """Each ignored `__pycache__` folder of the worktree with no ignored folder above
    it, as git names it."""
    where = ["git", "-C", str(task.worktree)]
    listed = subprocess.run(
        [
            *where,
            "ls-files",
            "--others",
            "--ignored",
            "--exclude-standard",
            "--directory",
            "-z",
        ],
        capture_output=True,
        check=False,
    )
    if listed.returncode != 0:
        raise LandError(
            "git ls-files --ignored failed: "
            f"{listed.stderr.decode(errors='replace').strip()}"
        )
    paths = nul_paths(listed.stdout)
    above = folders_above(bytecode_candidates(paths))
    if not above:
        return bytecode_of(paths, set())
    # `check-ignore` reads each path as a pathspec, so a folder named `:(top)x` would
    # read as `x` at the top; `./` before it makes git read it as it is, and git prints
    # it back with its `./`. With no `--no-index`, a folder that holds a tracked file is
    # never printed. Exit 1 is "none of them".
    asked = b"".join(os.fsencode(f"./{folder}") + b"\0" for folder in above)
    said = subprocess.run(
        [*where, "check-ignore", "--no-index", "--stdin", "-z"],
        input=asked,
        capture_output=True,
        check=False,
    )
    if said.returncode not in (0, 1):
        raise LandError(
            f"git check-ignore failed: {said.stderr.decode(errors='replace').strip()}"
        )
    return bytecode_of(
        paths, {path.removeprefix("./") for path in nul_paths(said.stdout)}
    )


def remove_bytecode(task: Task, folder: str) -> None:
    """Remove one ignored `__pycache__` folder whole. A link, or what is no folder on
    disk when the removal comes to it, stays, and so does a folder whose parent resolves
    outside the worktree; a link inside it is removed as a link, never followed. A
    folder that cannot go refuses the run."""
    root = task.worktree.resolve()
    path = root / folder.rstrip("/")
    if (
        path.is_symlink()
        or not path.is_dir()
        or not path.parent.resolve().is_relative_to(root)
    ):
        return
    try:
        shutil.rmtree(path)
    except OSError as error:
        raise LandError(
            f"the checks cannot remove the ignored {path} that was there before them "
            f"({error}): remove it, then run `lem land checks {task.slug}` again"
        ) from None


def remove_left(task: Task, path: str) -> None:
    """Remove one file a command of the checks left untracked, and each folder above it
    that it leaves empty, up to the worktree's root. A link is removed as a link,
    never followed."""
    root = task.worktree.resolve()
    file = root / path
    # git lists no file under a linked folder, so the folder that holds it is inside
    # the worktree
    if not file.parent.resolve().is_relative_to(root):
        return
    file.unlink(missing_ok=True)
    folder = file.parent
    while folder != root and folder.is_relative_to(root):
        try:
            folder.rmdir()
        except OSError:
            # not empty: it holds something else, tracked or not
            break
        folder = folder.parent


def changed(task: Task, old: str, new: str) -> list[str]:
    """Every path that differs between two trees. A rename counts as the path that went
    and the path that came."""
    return git(
        task.worktree, "diff", "--name-only", "--no-renames", old, new
    ).splitlines()


def due(task: Task) -> dict:
    """Whether a review is due now, and the least it may be. Within that, the one who
    starts the review chooses."""
    now = change(task)
    found = criteria_of(task)
    kept = task.kept()
    # the fast track has no plan, and is the one task of its builder
    tasks = (
        1
        if found["small"]
        else tasks_of(Path(found["plan"]).read_text(encoding="utf-8"))
    )
    return due_of(
        now,
        kept.get("reads", []),
        kept.get("resolution"),
        careful(task, now),
        tasks,
        small=found["small"],
        folder=backlog_of(task),
        own=task_item(task),
    )


def due_of(  # noqa: C901, PLR0911, PLR0912, PLR0913 - over the limit before the limit was set
    now: dict,
    reads: list[dict],
    resolution: dict | None,
    why_careful: list[str],
    tasks: int,
    *,
    small: bool,
    folder: str,
    own: str | None = None,
) -> dict:
    """`due` from what it read: the change as `change` gives it, the kept reviews and
    resolution, each reason the request is careful, the plan's count of tasks, the
    track, the backlog folder, and the task's own item (`task_item`)."""
    answered = [read for read in reads if read["answered"]]
    # The read of a conflict's resolution is no round: the two rounds are of the
    # change itself.
    rounds = [read for read in answered if read.get("of") != "resolution"]
    facts: dict[str, Any] = {
        "round": len(rounds) + 1,
        "careful": why_careful,
        "tasks": tasks,
        "small": small,
        "lines": now["lines"],
        "in_parts": now["lines"] > READ_AT,
        "resolution": None,
        **now,
    }
    silent = (
        len(reads)
        - max(
            (index for index, read in enumerate(reads) if read["answered"]), default=-1
        )
        - 1
    )
    if (
        resolution
        and resolution["covered"]
        and resolution["read"] is None
        and resolution["patch"] == now["patch"]
    ):
        # A builder resolved a conflict with the base, after a review covered the
        # change: what the review saw stands, and what the builder chose where the two
        # sides met gets one read, or the project's full set for a careful request.
        # Anything committed after the resolution makes it a change like any other,
        # which the rules below review whole.
        files = ", ".join(resolution["files"])
        facts.update(
            floor="full" if why_careful else "read",
            attempt=len(reads) + 1,
            round=max(len(rounds), 1),
            resolution={
                **{
                    key: resolution[key]
                    for key in ("files", "before", "after", "base", "onto")
                },
                "range_diff": (
                    "git range-diff "
                    f"{resolution['base'][:12]}..{resolution['before'][:12]} "
                    f"{resolution['onto'][:12]}..{resolution['after'][:12]}"
                ),
            },
        )
        if silent >= SILENT_REVIEWS:
            return {
                "due": "owner",
                "why": (
                    f"not reviewed: the read of the conflict's resolution in {files} "
                    "was started twice and no source answered"
                ),
                **facts,
            }
        why = (
            (
                f"the request is careful: {why_careful[0]}; a builder resolved a "
                f"conflict with the base in {files}"
            )
            if why_careful
            else (
                f"a builder resolved a conflict with the base in {files}: "
                "one read of what the resolution changed, and the earlier "
                "review stands for the rest"
            )
        )
        return {"due": "review", "why": why, **facts}
    # The floor is what no judgment goes under. Which profiles fit a change is read from
    # the diff and from what each profile is for, by an agent: no code and no list of
    # words decides that.
    if why_careful:
        floor, why = "full", f"the request is careful: {why_careful[0]}"
    elif facts["tasks"] > LARGE_AFTER:
        floor, why = "round", f"the plan has {facts['tasks']} tasks, more than three"
    elif any(read["must_fix"] for read in answered):
        floor, why = (
            "round",
            (
                "an earlier review found a must-fix: after its fix a "
                "round reviews the change"
            ),
        )
    else:
        floor, why = (
            "read",
            (
                "nothing asks for more than one read: the diff and what "
                "each profile is for decide"
            ),
        )
    facts.update(floor=floor, attempt=len(reads) + 1)
    # What the newest review that answered leaves open, for this change as it is now.
    last = answered[-1] if answered else None
    unmet = []
    if last:
        if last["must_fix"]:
            unmet.append(f"the last one left {last['must_fix']} must-fix")
        if not covered(folder, last, now, own):
            unmet.append("nobody reviewed what changed after it")
        # the read of a resolution is as large as the resolution; the change itself was
        # reviewed by the round before it
        sized = rounds[-1] if last.get("of") == "resolution" and rounds else last
        if KINDS.index(sized["kind"]) < KINDS.index(floor):
            unmet.append(
                f"it was {KIND_SAYS[sized['kind']]}, and this change gets "
                f"{KIND_SAYS[floor]} at the least ({why})"
            )
    if last and not unmet:
        if last.get("of") == "resolution":
            return {
                "due": "none",
                "why": (
                    f"round {last['round']} reviewed this change, one read of the "
                    "conflict's resolution read what changed after it, "
                    "and neither left a must-fix"
                ),
                **facts,
            }
        return {
            "due": "none",
            "why": f"round {last['round']} reviewed this change and left no must-fix",
            **facts,
        }
    if len(rounds) >= ROUNDS:
        return {
            "due": "owner",
            "why": f"two rounds reviewed it: {', and '.join(unmet)}",
            **facts,
        }
    if silent >= SILENT_REVIEWS:
        return {
            "due": "owner",
            "why": "not reviewed: the review was started twice and no source answered",
            **facts,
        }
    return {"due": "review", "why": why, **facts}


def talk_due(task: Task, state: dict) -> str | None:
    """Why this request's plan had to be talked through before any code; none when it
    did not.

    A talk is a step before the build, so only the plan itself calls for one: its own
    `careful: yes` line, or more than three tasks. The owner's later word, the review's
    call or an edit of Lem's own settings gives the full review set at the landing and
    no talk after the code exists."""
    if plan_careful(task):
        return "the plan says that the request is careful"
    if state["tasks"] > LARGE_AFTER:
        return f"the plan has {state['tasks']} tasks, more than three"
    return None


def events_of(task: Task) -> list[dict]:
    """The task's events in the log `project.py` writes, oldest first."""
    log = task.directory.parent.parent / "events.jsonl"
    found = []
    lines = (
        lem_state.jsonl_lines(log.read_text(encoding="utf-8")) if log.is_file() else []
    )
    for number, line in enumerate(lines, start=1):
        if f'"task": {json.dumps(task.slug)}' not in line:
            continue
        try:
            record = json.loads(line)
        except ValueError as error:
            raise LandError(
                f"line {number} of {log} is not JSON ({error}); the log is written by "
                "`lem project log`, never by hand"
            ) from error
        if record.get("task") == task.slug:
            found.append(record)
    return found


def events_all(task: Task) -> list[dict]:
    """Every event of the log `project.py` writes, oldest first; a line that does not
    read is passed over."""
    log = task.directory.parent.parent / "events.jsonl"
    found = []
    for line in (
        lem_state.jsonl_lines(log.read_text(encoding="utf-8")) if log.is_file() else []
    ):
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if isinstance(record, dict):
            found.append(record)
    return found


def talk_of(task: Task) -> dict | None:
    """The newest record of the task's plan talk in the event log."""
    return next(
        (
            record
            for record in reversed(events_of(task))
            if record.get("event") == "plan.talk"
        ),
        None,
    )


def untalked(task: Task, state: dict) -> str | None:
    """Why a careful request had no plan talk, when none was due: it became careful
    after its plan."""
    if not state["careful"] or talk_due(task, state):
        return None
    call = review_call(task)
    how = [
        *(["by the owner's word"] if owner_says_careful(task) else []),
        *(
            ["by its change to the settings"]
            if settings_edit(task, state) or local_settings_edit(task, state)
            else []
        ),
        *(["by its review"] if call and call["careful"] else []),
    ]
    return (
        "- no plan talk: the request became careful after "
        f"its plan, {' and '.join(how)}"
    )


def careful_line(task: Task, state: dict) -> str:
    """Whether the request is careful, as one line of the pull request's checks: each
    reason it is, and the newest review's call with its reason when the review
    said no."""
    call = review_call(task)
    line = (
        "- careful: yes, " + "; ".join(state["careful"])
        if state["careful"]
        else "- careful: no"
    )
    if call is None:
        return line + "; no review that answered made the call"
    if not call["careful"]:
        return line + f"; the review says no: {reason(call['why'])}"
    return line


def talked(talk: dict) -> str:
    """The plan talk as one line of the pull request's checks: the turns, with the bound
    of its rules when the talk went over it, and the positions, then each other count
    the event holds, in the event's order."""

    def many(count: int, one: str, more: str) -> str:
        return f"{count} {one if count == 1 else more}"

    counts = [
        many(value, *TALK_SAYS[key]) if key in TALK_SAYS else f"{key}: {value}"
        for key, value in talk.items()
        if key not in TALK_FIRST
        and isinstance(value, int)
        and not isinstance(value, bool)
    ]
    bound = talk.get("bound")
    over = (
        (
            f", over the bound of {bound} for its "
            f"{many(talk['questions'], 'question', 'questions')}"
        )
        if isinstance(bound, int) and talk["turns"] > bound
        else ""
    )
    return (
        f"- the plan talk: {talk['reviewer']} argued the plan with its defender, "
        f"{many(talk['turns'], 'turn', 'turns')}{over}; "
        f"{many(talk['settled'], 'position', 'positions')} settled by the two, "
        f"{talk['open']} left open"
    ) + (f"; {', '.join(counts)}" if counts else "")


def stand_ins_of(events: list[dict]) -> list[dict]:
    """Each seat that stood in for another in the task, from its `seat.stand-in` events
    (EVENTS, the task's own, oldest first), every one, with no filter: the seat, the one
    it stood in for, the error, the agent's words, and `failed_too`, the error of the
    stand-in itself when a `seat.blocked` of that seat names its seat as the one that
    failed, before any later `seat.again` of it (at its start, or later). A stand-in
    that a block of another cause followed did its part of the work before it."""
    out = []
    for number, event in enumerate(events):
        if event.get("event") != "seat.stand-in":
            continue
        then = None
        for later in events[number + 1 :]:
            if later.get("seat") != event.get("seat"):
                continue
            if later.get("event") == "seat.again":
                break
            if later.get("event") == "seat.blocked" and later.get(
                "failed"
            ) == event.get("took"):
                then = later
                break
        out.append(
            {
                "seat": event.get("seat"),
                "took": event.get("took"),
                "failed": event.get("failed"),
                "error": event.get("error"),
                "said": event.get("said"),
                "at": event.get("ts"),
                "failed_too": {"error": then.get("error"), "said": then.get("said")}
                if then
                else None,
            }
        )
    return out


def stand_in_line(stand_in: dict) -> str:
    """One stand-in as a line of the pull request's checks, a fact and no reason of not
    green: which seat stood in, for which seat, and why; and, when it gave an error
    itself, that too."""
    name = lem_state.SEAT_NAMES.get(stand_in["seat"], stand_in["seat"])
    failed, took = stand_in["failed"], stand_in["took"]
    why = (
        f"{lem_state.agent_name(failed)} "
        f"{lem_state.SEAT_ERRORS[stand_in['error']]['pr']}"
    )
    too = stand_in["failed_too"]
    if not too:
        return f"- {name} was `{took}` in place of `{failed}`: {why}"
    return (
        f"- {name} was to be `{took}` in place of `{failed}`: {why}; "
        f"then {lem_state.agent_name(took)} gave an error too: "
        f"{lem_state.agent_name(took)} {lem_state.SEAT_ERRORS[too['error']]['pr']}"
    )


def stand_in_lines(task: Task) -> list[str]:
    """The line of each seat that stood in for another in the task, in the order of
    the log."""
    return [stand_in_line(stand_in) for stand_in in stand_ins_of(events_of(task))]


def merger_noted(task: Task, pr: dict, then: str) -> None:
    """The line of each stand-in of the merge agent in the pull request's text on GitHub
    and in pr.md, once (`noted`). A merge agent's stand-in comes after the pull request
    is open, so both steps that follow it run this: the record of a read
    (`merge-review --file`) and every path to `landed` (`forge_done`), which a merge on
    GitHub takes while the stand-in reads or after it blocked the task. A stand-in that
    gave an error after its line went in has that line replaced by the one that says so.
    THEN is the refusal's words on what stays and what tries again."""
    for stand_in in stand_ins_of(events_of(task)):
        if stand_in["seat"] != "merger":
            continue
        earlier = (
            stand_in_line({**stand_in, "failed_too": None})
            if stand_in["failed_too"]
            else None
        )
        noted(
            task,
            pr,
            stand_in_line(stand_in),
            "the line of the merge agent's stand-in",
            then,
            earlier,
        )


def polished(polish: dict) -> str:
    """The polish pass as one line of the pull request's checks, from what
    `polish --done` logged. The checks refuse a task on the standard track with no pass
    that is done."""
    commits, filed = polish["commits"], len(polish["filed"])
    return (
        f"- the polish pass: {commits} commit{'' if commits == 1 else 's'}, {filed} "
        f"item{'' if filed == 1 else 's'} filed in the backlog"
    )


def criteria_read_of(task: Task) -> dict | None:
    """The newest record of the personas' read of the task's criteria in the
    event log."""
    return next(
        (
            record
            for record in reversed(events_of(task))
            if record.get("event") == "criteria.read"
        ),
        None,
    )


def unanswered(task: Task) -> int:
    """How many reads of the criteria in a row, the newest last, nobody answered."""
    count = 0
    for record in reversed(events_of(task)):
        if record.get("event") != "criteria.read":
            continue
        if record.get("answered") != 0:
            break
        count += 1
    return count


def read_form(read: dict) -> bool:
    """Whether a `criteria.read` event has the form `lem project log` gives it; one that
    nobody answered names no family."""
    counts = ("asked", "answered", "criteria", "flagged")
    families, silent = read.get("families"), read.get("silent")
    return (
        read.get("by") in ("lem", "lead")
        and all(
            isinstance(read.get(key), int)
            and not isinstance(read.get(key), bool)
            and read[key] >= 0
            for key in counts
        )
        and isinstance(families, list)
        and bool(families) == bool(read["answered"])
        and all(isinstance(name, str) and name.strip() for name in families)
        and isinstance(silent, list)
        and all(
            isinstance(item, dict) and set(item) == {"name", "why"} for item in silent
        )
        and isinstance(read.get("split"), bool)
        and isinstance(read.get("digest"), str)
        and read["answered"] <= read["asked"]
    )


def read_skip_form(slug: str) -> str:
    """The command that writes the owner's word to skip the personas' read, as the
    landing knows it."""
    return (
        f'`lem decisions log {slug} --by owner --what "{READ_SKIP["what"]}" --chose '
        f'"{READ_SKIP["chose"]}" --why "THE OWNER\'S ANSWER"`'
    )


def read_skipped(task: Task) -> tuple[dict | None, str | None]:
    """The owner's newest word to skip the personas' read, when an approval of his
    follows it and both came before any lead of the task started; or why the word on
    record does not count. A lead writes the criteria on the standard track from a
    complete request, where the read is the only approval and always runs, so a word or
    an approval after the first state that names a lead belongs to such a task. Neither,
    with no word of his."""
    events = events_of(task)
    words = [
        index
        for index, record in enumerate(events)
        if record.get("event") == "decision.taken"
        and record.get("by") == "owner"
        and record.get("what") == READ_SKIP["what"]
        and record.get("chose") == READ_SKIP["chose"]
    ]
    if not words:
        return None, None
    word = words[-1]
    lead = next(
        (
            index
            for index, record in enumerate(events)
            if record.get("event") == "task.state"
            and any(
                line.startswith("lead:")
                for line in [record.get("text", ""), *record.get("lines", [])]
            )
        ),
        None,
    )
    approval = next(
        (
            index
            for index in range(word + 1, len(events))
            if events[index].get("event") == "criteria.approved"
            and events[index].get("by") == "owner"
        ),
        None,
    )
    complete = (
        "the lead wrote the criteria, and on the standard track from a complete "
        "request the read always runs, as the only approval there (`stages/plan.md`, "
        "step 1): the lead runs it and writes "
        f"`lem project log {task.slug} criteria.read` with the form {READ_FORM}"
    )
    if lead is not None and lead < word:
        return (
            None,
            (
                f"a lead of {task.slug} started before the owner's word to skip the "
                f"personas' read: {complete}"
            ),
        )
    if lead is not None and (approval is None or lead < approval):
        return (
            None,
            (
                f"a lead of {task.slug} started before the owner's approval that came "
                f"after the word to skip the personas' read: {complete}"
            ),
        )
    if approval is None:
        return None, (
            f"the owner's word to skip the personas' read of {task.slug}'s criteria is "
            "on record, and no approval of the owner's came after it: the owner's yes "
            "to the criteria is kept with "
            f"`lem criteria approve {task.slug} --file FILE` (`stages/interview.md`, "
            "step 7)"
        )
    return {"word": events[word], "approval": events[approval]}, None


def interview_unapproved(
    events: list[dict], approvals: list[dict], *, small: bool
) -> bool:
    """Whether a task on the standard track had an interview (`interview.start` among
    its EVENTS) and its criteria carry no approval of the owner's, nor one made while it
    ran without him (`alone`): the interview ends with his yes (`stages/interview.md`,
    steps 6 and 7), and the lead's freeze of a read is the complete request's approval,
    not his. The fast track asks nothing of it."""
    if small or not any(event.get("event") == "interview.start" for event in events):
        return False
    return not any(approval.get("by") in ("owner", "alone") for approval in approvals)


def when(event: dict) -> str:
    """The time an event happened: its own, or for one a resumed task copied from the
    task it came from (`lem project resume`), the time it had there (`was_at`), which an
    approval's `at` keeps too."""
    return event.get("was_at") or event["ts"]


def approved_after(found: dict, read: dict) -> bool:
    """Whether the owner himself approved the criteria at the read's time or after it. A
    freeze of a read (`by: read`) and Lem's approval on the fast track are not
    his yes."""
    return any(
        approval["by"] == "owner" and approval["at"] >= when(read)
        for approval in found.get("approvals", [])
    )


def approved_alone(found: dict, read: dict) -> bool:
    """Whether Lem or the lead approved the criteria at the read's time or after it
    while the task ran without the owner (`lem criteria approve --alone`): enough to
    propose, never green."""
    return any(
        approval["by"] == "alone" and approval["at"] >= when(read)
        for approval in found.get("approvals", [])
    )


def criteria_waited(events: list[dict]) -> dict | None:
    """The newest wait of the task's criteria for the owner's yes, with the approval
    that ended it, from the task's events oldest first; None when no such wait ended.
    The wait is the newest `held` state whose line is a `CRITERIA_WAIT` one other than
    `FAST_GREW` (that task went to an interview), and its end is the first approval
    after it that is the owner's or made while the task ran without him (`WAIT_ENDS`),
    whoever gave it: an approval of his after Lem's is no end of that wait."""
    waits = [
        index
        for index, record in enumerate(events)
        if record.get("event") == "task.state"
        and record.get("status") == "held"
        and any(
            str(line).startswith(CRITERIA_WAIT) and not FAST_GREW.search(str(line))
            for line in [record.get("text", ""), *record.get("lines", [])]
        )
    ]
    if not waits:
        return None
    end = next(
        (
            record
            for record in events[waits[-1] + 1 :]
            if record.get("event") == "criteria.approved"
            and record.get("by") in WAIT_ENDS
        ),
        None,
    )
    return {"from": events[waits[-1]]["ts"], "end": end} if end else None


def approval_said(found: dict, waited: dict | None) -> str:
    """The part of the read's line that says who approved the criteria and when; empty
    when nobody whose approval counts for the build did. With a wait for his yes
    (`criteria_waited`), the part says when the wait began and whether his yes ended it,
    and names a later approval of his."""
    approval = found.get("approved")
    if waited:
        end = waited["end"]
        said = (
            f"the criteria waited for the owner's yes from {utc(waited['from'])}, "
            + (
                f"and the owner gave it on {utc(end['ts'])}"
                if end["by"] == "owner"
                else (
                    "and the wait ended without the owner: "
                    f"approved on {utc(end['ts'])} while the task ran without the owner"
                )
            )
        )
        if (
            approval
            and approval["by"] == "owner"
            and approval["number"] != end.get("number")
        ):
            said += (
                "; the owner approved them "
                f"{'again ' if end['by'] == 'owner' else ''}on {approval['at'][:10]}"
            )
        return said
    # a plan is the standard track's: its criteria are the owner's approval, or the
    # lead's freeze by a read, which is not his
    if approval and approval["by"] == "owner":
        return f"the owner approved them on {approval['at'][:10]}"
    if approval and approval["by"] == "alone":
        return f"approved on {approval['at'][:10]} while the task ran without the owner"
    return ""


def changed_after_read(events: list[dict]) -> int:
    """How many times the criteria changed from the owner's notes after the newest
    personas' read, from the task's events oldest first: the held blocks CHANGED_WAIT
    after it, one for each change (`lem criteria change`), whatever text the owner
    approved at the end. 0 with no read."""
    read = next(
        (
            i
            for i in range(len(events) - 1, -1, -1)
            if events[i].get("event") == "criteria.read"
        ),
        None,
    )
    if read is None:
        return 0
    return sum(
        1
        for record in events[read + 1 :]
        if record.get("event") == "task.state"
        and record.get("status") == "held"
        and record.get("text") == CHANGED_WAIT
    )


def changes_said(changed: int) -> str:
    """The part of the read's line that counts the changes from the owner's notes after
    the read."""
    if not changed:
        return ""
    return (
        f"; the criteria changed {'once' if changed == 1 else f'{changed} times'} "
        "after the personas' read, from the owner's notes"
    )


def read_line(  # noqa: PLR0913, PLR0917 - over the limit before the limit was set
    read: dict | None,
    found: dict,
    quiet_reads: int = 0,
    skipped: dict | None = None,
    waited: dict | None = None,
    changed: int = 0,
) -> str:
    """The personas' read of the criteria and his approval, as one line of the pull
    request's checks; `skipped` is his word to skip the read with his approval after it,
    as `read_skipped` gives them, `waited` the criteria's wait for his yes with its end,
    as `criteria_waited` gives them, and `changed` how many changes from his notes came
    after the read, as `changed_after_read` counts them."""
    approved = approval_said(found, waited)
    if read and not read["answered"]:
        # propose refuses the first such read, so this is the second in a row at
        # the least
        return (
            (
                f"- the criteria were not read by the personas: {quiet_reads} reads in "
                f"a row, and none of the {read['asked']} personas asked answered"
            )
            + changes_said(changed)
            + (
                f"; {approved}"
                if approved
                else "; the build started with no wait for the owner"
            )
        )
    if read:
        count = len(read["families"])
        line = (
            (
                f"- the criteria were read by {read['answered']} of {read['asked']} "
                f"personas asked, {FAMILIES.get(count, f'{count} model families')} "
                f"({', '.join(read['families'])}); "
            )
            + (
                "nobody confused"
                if not read["flagged"]
                else (
                    f"{read['flagged']} of {read['criteria']} "
                    f"{'criterion' if read['criteria'] == 1 else 'criteria'} flagged"
                )
            )
            + ("; the two families split" if read["split"] else "")
            + "".join(
                f"; no answer from {source['name']} ({source['why']})"
                for source in read["silent"]
            )
            + changes_said(changed)
        )
        if approved:
            return f"{line}; {approved}"
        return line + "; the build started with no wait for the owner"
    if skipped:
        return (
            "- the criteria: not read by the personas, on the owner's word "
            f"({skipped['word']['at'][:10]}); the owner approved them"
        )
    return "- the criteria: no read by the personas is on record" + (
        f"; {approved}" if approved else ""
    )


def unread(read: dict | None, found: dict) -> str | None:
    """The line that says the criteria are not the ones the personas read, and what
    changed them. The plan's criteria are the expected ones (the checks refuse any
    other), so they are compared."""
    if (
        read is None
        or not read["answered"]
        or found["criteria_digest"] == read["digest"]
    ):
        return None
    # an approval of his after the read changed the criteria only when it holds other
    # criteria than the read did
    his = [
        approval
        for approval in found.get("approvals", [])
        if approval["by"] == "owner"
        and approval["at"] >= when(read)
        and approval["digest"] != read["digest"]
    ]
    what = [
        *([f"by the owner's approval {his[-1]['number']}"] if his else []),
        *(
            ["by a change of the build"]
            if any(change["at"] >= when(read) for change in found.get("history", []))
            else []
        ),
    ]
    return (
        "- the criteria changed after the personas' "
        f"read{', ' + ' and '.join(what) if what else ''}, and the change was not read"
    )


def named(value: object, where: str) -> list[dict]:
    """A list of names, each with its why: the profiles of a round, or the sources that
    did not answer."""
    if not isinstance(value, list) or not all(
        isinstance(item, dict)
        and set(item) == {"name", "why"}
        and all(isinstance(text, str) and text.strip() for text in item.values())
        for item in value
    ):
        raise LandError(
            f'`{where}` is a list of {{"name": ..., "why": ...}}, '
            "each with both as text"
        )
    return value


def same_checks(results: list[dict], commands: list[str], serial: list[str]) -> bool:
    """Whether a kept result of the checks (its `commands`, each with its `serial` flag)
    ran the commands the checks have now, in their order: the plain ones, then the
    serial ones. With no command there is no result to hold: only the task that adds one
    lands (`docs/settings.md`, `[checks]`)."""
    ran = [(entry.get("command"), bool(entry.get("serial"))) for entry in results]
    now = [
        *((command, False) for command in commands),
        *((command, True) for command in serial),
    ]
    return bool(commands) and ran == now


def gate_missing(task: Task, tip: str) -> str | None:
    """Why no result of the checks holds for `tip`, in words for a refusal; None when
    one holds."""
    if gate_holds(task, tip):
        return None
    kept = task.kept()
    if kept.get("gated") and not same_checks(
        (kept.get("checks") or {}).get("commands") or [],
        task.gate()[0],
        task.settings["checks"]["serial"],
    ):
        return (
            "the commands of the checks are not the ones that passed (checks.commands "
            "and checks.serial of the main checkout's .lem/settings.toml changed "
            "since), so their green result is not this one's"
        )
    return "no green check is on record for this tip"


def gate_holds(task: Task, tip: str) -> bool:
    """Whether the result of the checks holds for `tip`: it ran the commands the checks
    have now (`same_checks`: the main checkout's settings count at once, an edit nobody
    committed too), and the tip is the commit they passed on, or that commit with
    commits after it that only add the backlog items `file` wrote for this landing's
    reviews. Those hold no code and no test, so they ask for no checks again; the result
    is then kept for the tip, so that `land` finds what it checks. Any other commit, an
    item written by hand among them, asks for the checks."""
    kept = task.kept()
    gated = kept.get("gated")
    if gated and not same_checks(
        (kept.get("checks") or {}).get("commands") or [],
        task.gate()[0],
        task.settings["checks"]["serial"],
    ):
        return False
    if gated == tip:
        return True
    if not gated or not holds_commit(task, gated, tip):
        return False
    items = {
        defect["item"]
        for read in kept.get("reads", [])
        if read["answered"]
        for defect in outside_of(read)
        if defect.get("item")
    }
    rows = [
        row.split("\t", 1)
        for row in git(
            task.worktree, "diff", "--name-status", "--no-renames", gated, tip
        ).splitlines()
    ]
    if not rows or not all(status == "A" and path in items for status, path in rows):
        return False
    task.keep(gated=tip, tree=git(task.worktree, "rev-parse", f"{tip}^{{tree}}"))
    return True


def items_added(task: Task, base: str) -> list[dict]:
    """Each item the branch adds to the backlog folder between BASE and its tip, whoever
    wrote it (a builder, the polish pass, `file` for a review), with its `where`, its
    title and its `worth` as the tip's file says them."""
    folder = backlog_of(task)
    rows = [
        row.split("\t", 1)
        for row in git(
            task.worktree,
            "diff",
            "--name-status",
            "--no-renames",
            "--diff-filter=A",
            base,
            "HEAD",
        ).splitlines()
    ]
    found = []
    for _, path in rows:
        if not path.startswith(folder + "/"):
            continue
        item = item_of(task.worktree / path)
        front, lines = item or ({}, [])
        found.append(
            {
                "item": path,
                "where": front.get("where"),
                "title": lines[0][2:].strip() if lines else None,
                "worth": front.get("worth"),
            }
        )
    return found


def branch_items(task: Task) -> list[dict]:
    """Each item the branch adds to the backlog folder that `file` did not write for a
    review: what the fast track's builder or the polish pass filed, with its `where` and
    its title."""
    written = {
        defect["item"]
        for read in task.kept().get("reads", [])
        for defect in outside_of(read)
        if defect.get("item")
    }
    return [
        item
        for item in items_added(
            task, git(task.worktree, "merge-base", "HEAD", task.onto)
        )
        if item["item"] not in written
    ]


# A project's own builder, which `spawn-builder` starts in place of
# Lem's (harness/claude-code.md).
OWN_BUILDER = Path(".claude") / "agents" / "lem-builder.md"


def bar_file(main: Path) -> dict:
    """The file whose rule 6 holds the bar of a backlog item for this project, as
    `spawn-builder` picks the builder that the polish pass, the fast track's builder and
    the review run as: the project's own `.claude/agents/lem-builder.md` in the main
    checkout MAIN, where the task's session stands, when it is there, by its whole path
    (`of`: `project`); else Lem's `agents/lem-builder.md`, by its place in the plugin
    (`of`: `lem`), since an update of the plugin replaces this Lem's folder. So the
    merge agent judges the items by the rule 6 the builders read."""
    own = main / OWN_BUILDER
    if own.is_file():
        return {"file": str(own), "of": "project"}
    return {"file": "agents/lem-builder.md", "of": "lem"}


def bar_path(main: Path) -> tuple[Path, str]:
    """The file of `bar_file` on this machine, and its name as a line of the pull
    request gives it: the project's `.claude/agents/lem-builder.md`, or Lem's
    `agents/lem-builder.md` in the plugin."""
    found = bar_file(main)
    if found["of"] == "project":
        return Path(found["file"]), OWN_BUILDER.as_posix()
    return SCRIPTS.parents[2] / found["file"], found["file"]


def bar_condition(text: str) -> str | None:
    """The condition of the bar in the text of a builder's standing rules: of rule 6,
    from its number to rule 7's, the sentence "... is filed only for a defect over the
    bar: CONDITION.", read whole over its line breaks. None when rule 6 holds no
    sentence of that form (a project that writes its bar in its own words): Jev is then
    not asked, since a question with no bar has no meaning."""
    rule = re.search(r"(?ms)^6\.\s(.*?)(?=^7\.\s|\Z)", text)
    if not rule:
        return None
    found = BAR_SENTENCE.search(" ".join(rule.group(1).replace("**", "").split()))
    return found.group(1).strip() if found else None


def finding_key(where: str, title: str, run: str) -> str:
    """The digest Jev's entry of a finding is kept by: its `where`, its title and its
    run, as `holds` tells two defects apart, so two runs of one place and title are two
    findings, and a new reason (an item's `Decided against:` line, a notes line's text
    after `under:`) is the same one."""
    return hashlib.sha256(
        json.dumps(
            [where.strip(), title.strip(), "\n\n".join(paragraphs(run))]
        ).encode()
    ).hexdigest()[:16]


def item_finding(
    path: str, item: tuple[dict[str, str], list[str]] | None
) -> dict | None:
    """The finding of an item of the backlog that says `worth: no`, from `item_of`: its
    `where`, its title and its run, the body without its `Decided against:` line, and
    whether that line gives a reason. None for a file that is no item, or one of
    another worth."""
    if item is None:
        return None
    front, lines = item
    if (front.get("worth") or "").strip().lower() != "no":
        return None
    decided = [line for line in lines[1:] if re.match(r"(?i)\s*decided against:", line)]
    run = "\n".join(line for line in lines[1:] if line not in decided)
    where, title = front.get("where") or "", lines[0][2:].strip()
    return {
        "item": path,
        "where": where,
        "title": title,
        "run": "\n\n".join(paragraphs(run)),
        "reason": any(
            re.match(r"(?i)\s*decided against:\s*\S", line) for line in decided
        ),
        "key": finding_key(where, title, run),
    }


def line_finding(entry: list[str]) -> dict | None:
    """The finding of an entry of the notes that calls it under the bar
    (`under: REASON`): its text before the call, without the list's mark, is its run; it
    has no `where` and no title of its own. None for an entry with no such call."""
    text = " ".join(" ".join(entry).split())
    call = UNDER.search(text)
    if call is None:
        return None
    run = (
        re.sub(r"^([-*+]|\d+[.)])\s+", "", text[: call.start()]).rstrip(" ;,:-(")
        or text
    )
    return {
        "line": entry[0].strip(),
        "where": "",
        "title": "",
        "run": run,
        "reason": True,
        "key": finding_key("", "", run),
    }


def under_findings(
    added: list[dict],
    read_item: Callable[[str], tuple[dict[str, str], list[str]] | None],
    notes: str,
    *,
    small: bool,
) -> list[dict]:
    """Each finding called under the bar that the tip holds, whoever wrote it: each item
    the branch adds (ADDED, `items_added`) that says `worth: no`, whose file READ_ITEM
    reads as `item_of` does, and each line of the notes that calls one `under:` in the
    parts `propose` checks (`called_bodies`)."""
    found = [
        finding
        for item in added
        if (item.get("worth") or "").strip().lower() == "no"
        for finding in [item_finding(item["item"], read_item(item["item"]))]
        if finding
    ]
    found += [
        finding
        for body in called_bodies(notes, small=small)
        for entry in entries_of(body)
        for finding in [line_finding(entry)]
        if finding
    ]
    return found


def jev_sends(settings: dict) -> bool:
    """Whether the project sends a finding's text to the Jev model: `findings` of the
    team's `[jev]`, true when the file says nothing (`project.py`, `jev_of`)."""
    return settings["jev"]["findings"]


def jev_command() -> list[str]:
    """How the landing runs Jev, as corrections.py does: Lem's own jev.py beside this
    file, or the command LEM_JEV names, with the same contract (a test's stand-in)."""
    other = os.environ.get("LEM_JEV")
    return [other] if other else [sys.executable, "-B", str(SCRIPTS / "jev.py")]


def ask_jev(spec: dict) -> dict:
    """One request to Jev with SPEC, `jev.py`'s form, given JEV_SECONDS:
    `{"answers": {NAME: P}}`, each question's probability of yes, or
    `{"not_asked": WHY}` when no answer came, and the landing goes on as without Jev:
    `no key` with no JEV_API_KEY, where nothing is started; `too long` for a spec over
    jev.py's limit (its exit 3, nothing sent); `no answer` for a failed or timed-out
    request, or a reply that does not read."""
    if not os.environ.get("JEV_API_KEY"):
        return {"not_asked": "no key"}
    try:
        ran = subprocess.run(
            [*jev_command(), "-"],
            input=json.dumps(spec),
            capture_output=True,
            text=True,
            check=False,
            timeout=JEV_SECONDS,
            env={**os.environ, "JEV_TIMEOUT": str(JEV_SECONDS)},
        )
    except (OSError, subprocess.TimeoutExpired):
        return {"not_asked": "no answer"}
    if ran.returncode == JEV_TOO_LONG:
        return {"not_asked": "too long"}
    try:
        if ran.returncode:
            raise ValueError(ran.stderr)
        answers = json.loads(ran.stdout)["answers"]
        said = {name: answers[name]["noul"] for name in spec["questions"]}
    except (ValueError, KeyError, TypeError):
        return {"not_asked": "no answer"}
    if not all(
        isinstance(p, (int, float)) and not isinstance(p, bool) and 0 <= p <= 1
        for p in said.values()
    ):
        return {"not_asked": "no answer"}
    return {"answers": said}


def jev_spec(finding: dict, condition: str) -> dict:
    """The request of one finding: the finding as the state (its `where`, title and run,
    each that it has), and one yes-or-no question, whether it is over the bar, with both
    meanings: yes, the bar's CONDITION as rule 6 says it; no, its plain negation, so
    that the two never both apply."""
    return {
        "state": finding_state(finding),
        "questions": {
            JEV_QUESTION: {
                "type": "noul",
                "instructions": (
                    "This finding is a defect that an agent saw in the change it "
                    "worked on or in the code outside it, and called under the bar for "
                    "an item of the backlog. Is the finding over the bar?"
                ),
                "yes": f"The finding meets the bar: {condition}.",
                "no": "The finding does not meet that bar.",
            }
        },
    }


def jev_entry(
    finding: dict, *, sends: bool, bar: tuple[str | None, str] | None
) -> dict:
    """Jev's entry for one finding that has none yet: `{score, asked_at}`, or
    `{not_asked: WHY}`: `off in the settings` when SENDS is false, `no bar in FILE` when
    BAR, the condition of rule 6 and the file's name, has no condition; else what
    `ask_jev` says. Nothing is sent but by `ask_jev`."""
    if not sends:
        return {"not_asked": "off in the settings"}
    # with SENDS, `jev_read` read the bar before the first finding it asks about
    condition, name = cast("tuple[str | None, str]", bar)
    if condition is None:
        return {"not_asked": f"no bar in {name}"}
    said = ask_jev(jev_spec(finding, condition))
    if "not_asked" in said:
        return said
    return {"score": said["answers"][JEV_QUESTION], "asked_at": lem_clock.stamp()}


def jev_said(entry: dict | None) -> str | None:
    """The end of a finding's line in the pull request: `Jev: 0.82`,
    or `Jev: not asked (WHY)`."""
    if not entry:
        return None
    if "score" in entry:
        return f"Jev: {entry['score']:.2f}"
    return f"Jev: not asked ({entry['not_asked']})"


def jev_refused(
    findings: list[dict], kept: dict
) -> tuple[list[tuple[dict, float, bool]], dict]:
    """What `propose` refuses for Jev's read of FINDINGS, by the entries KEPT: each
    finding with a score at or over JEV_OVER that was never refused, once; and each
    refused before that is an item still `worth: no` with no `Decided against:` line,
    until it has one. A notes line has its reason in its call. Each as (finding, score,
    again), with the entries after it, those refused now marked `refused`."""
    kept = {key: dict(entry) for key, entry in kept.items()}
    out = []
    for finding in findings:
        entry = kept.get(finding["key"]) or {}
        if "score" not in entry or entry["score"] < JEV_OVER:
            continue
        if not entry.get("refused"):
            entry["refused"] = True
            out.append((finding, entry["score"], False))
        elif finding.get("item") and not finding["reason"]:
            out.append((finding, entry["score"], True))
    return out, kept


def jev_endings(findings: list[dict], kept: dict) -> dict:
    """The end each finding's line gets in the pull request (`jev_said`), by the item's
    path and by the digest of a notes line's finding."""
    endings: dict = {"items": {}, "lines": {}}
    for finding in findings:
        said = jev_said(kept.get(finding["key"]))
        if said:
            if finding.get("item"):
                endings["items"][finding["item"]] = said
            else:
                endings["lines"][finding["key"]] = said
    return endings


def jev_marked(body: list[str], endings: dict) -> list[str]:
    """The lines of a part of the pull request's text, each entry of a finding Jev read
    ending with what Jev said (`; Jev: 0.82`): an entry that names an item by its path,
    or calls a finding `under:`. An entry that ends so already is left as it is."""
    out = list(body)
    for span in entry_spans(body):
        entry = [body[at] for at in span]
        said = next(
            (
                said
                for path, said in endings["items"].items()
                if any(names_item(line, path) for line in entry)
            ),
            None,
        )
        if said is None:
            finding = line_finding(entry)
            said = endings["lines"].get(finding["key"]) if finding else None
        last = out[span[-1]].rstrip()
        if said and not JEV_SAID.search(last):
            out[span[-1]] = last.rstrip(";") + f"; {said}"
    return out


def jev_notes(notes: str, *, small: bool, endings: dict) -> str:
    """The notes with Jev's read at the end of each line of a finding called under the
    bar: under `## Filed as not worth it`, `## Left open` and `## Seen, not filed`, and
    on the fast track (SMALL) the lines before the first heading. Notes with no such
    finding come back as they are."""
    if not endings["items"] and not endings["lines"]:
        return notes
    head, parts = sections_of(notes)
    head = jev_marked(head, endings) if small else head
    parts = [
        (
            heading,
            jev_marked(lines, endings)
            if heading in (NOT_WORTH, LEFT_OPEN, SEEN)
            else lines,
        )
        for heading, lines in parts
    ]
    return "\n".join(
        [*head, *(line for heading, lines in parts for line in (heading, *lines))]
    ) + ("\n" if notes.endswith("\n") else "")


def jev_read(task: Task, notes: str, *, small: bool) -> dict:
    """Jev's one read of each finding called under the bar that the tip holds
    (`under_findings`), for `propose`: a finding with no entry kept in `landing.json`
    (`jev`, by `finding_key`) gets one, kept at once, so that no finding is sent twice,
    by this landing or the next (`start_locked` carries `jev`). Refused once, with each
    finding and its score, when Jev reads one as over the bar (`jev_refused`); otherwise
    the end of each finding's line in the pull request (`jev_endings`)."""
    findings = under_findings(
        builder_filed(task),
        lambda path: item_of(task.worktree / path),
        notes,
        small=small,
    )
    kept = dict(task.kept().get("jev") or {})
    sends = jev_sends(task.settings)
    bar = None
    for finding in findings:
        if finding["key"] in kept:
            continue
        if sends and bar is None:
            file, name = bar_path(task.main)
            try:
                bar = (bar_condition(file.read_text(encoding="utf-8")), name)
            except (OSError, UnicodeDecodeError):
                bar = (None, name)
        kept[finding["key"]] = jev_entry(finding, sends=sends, bar=bar)
        task.keep(jev=kept)
    refused, kept = jev_refused(findings, kept)
    if refused:
        task.keep(jev=kept)
        named = "; ".join(
            (f"`{finding['item']}`" if finding.get("item") else f'"{finding["line"]}"')
            + f" (Jev: {score:.2f}"
            + (
                (
                    "; refused before, and the item still says `worth: no` with no "
                    "`Decided against:` line)"
                )
                if again
                else ")"
            )
            for finding, score, again in refused
        )
        raise LandError(
            f"{len(refused)} finding(s) called under the bar, which Jev reads as over "
            f"it at {JEV_OVER} or more: {named}. Jev reads this as over the bar: "
            "make the item `worth: later`, or keep `worth: no` with its "
            "`Decided against:` line (for a notes line, keep `under:` with its "
            "reason), then run this step again. An edit of an item is a commit, so "
            f"`lem land checks {task.slug}` runs before this step; Jev is not asked "
            "again about a finding it read",
        )
    return jev_endings(findings, kept)


def alike_question(item: dict) -> dict:
    """The question of `alike` about one item of the backlog: whether the finding, the
    state, is the same defect as the item, told by its title, its `where` and the first
    line of its body, each that it has; both meanings, as jev.py asks for both
    or neither."""
    told = [f"title: {item['title'] or item['item']}"] + [
        f"{key}: {item[key]}" for key in ("where", "first") if item.get(key)
    ]
    return {
        "type": "noul",
        "instructions": (
            "Is the finding the same defect as this item of the backlog? The item, "
        )
        + "; ".join(told).replace("first: ", "the first line of its body: "),
        "yes": (
            "The finding and the item are one defect, so the item holds the finding "
            "and no second item is needed."
        ),
        "no": (
            "The finding is another defect than the item's, "
            "in the same place or in another."
        ),
    }


def finding_state(finding: dict) -> dict:
    """The state of a request about a finding: its `where`, its title and its run, each
    that it has."""
    return {key: finding[key] for key in ("where", "title", "run") if finding.get(key)}


def alike_specs(
    finding: dict, items: list[dict], fits: Callable[[dict], bool]
) -> list[dict] | None:
    """The requests of `alike` for FINDING: the finding as the state of each, and one
    question for each of ITEMS (`alike_question`, named `iN` by the item's place), in as
    many requests as FITS, which says whether a request is under jev.py's limit, needs.
    Jev answers each question alone, so every item is asked, and none is left out by its
    place. None when the state with one question alone does not fit: that item cannot
    be asked."""
    state = finding_state(finding)
    specs: list[dict] = []
    questions: dict = {}
    for place, item in enumerate(items):
        name, question = f"i{place}", alike_question(item)
        if fits({"state": state, "questions": {**questions, name: question}}):
            questions[name] = question
            continue
        if not questions or not fits({"state": state, "questions": {name: question}}):
            return None
        specs.append({"state": state, "questions": questions})
        questions = {name: question}
    if questions:
        specs.append({"state": state, "questions": questions})
    return specs


def jev_fits(spec: dict) -> bool:
    """Whether jev.py takes SPEC under its limit (`LIMIT_BYTES`), by its own count of
    the bytes."""
    try:
        importlib.import_module("jev").build(spec)
    except OverflowError:
        return False
    return True


def ask_alike(
    finding: dict, items: list[dict], *, sends: bool, known: dict | None = None
) -> dict:
    """Jev's read of whether FINDING is the same defect as each of ITEMS:
    `{"scores": {PATH: P}}` for every item, or `{"not_asked": WHY}` when any request got
    no answer (or SENDS is false: `off in the settings`), so that the agent then reads
    every item. KNOWN holds the scores of this finding an earlier run kept, by the
    item's path, which are not asked again: one text read twice moved by up to 0.11
    (jev-advice.md of task backlog-refuted-items-and-jev, 2026-11-23), so a second ask
    could name an item the first did not."""
    if not sends:
        return {"not_asked": "off in the settings"}
    scores = dict(known or {})
    ask = [item for item in items if item["item"] not in scores]
    specs = alike_specs(finding, ask, jev_fits) if ask else []
    if specs is None:
        return {"not_asked": "too long"}
    for spec in specs:
        said = ask_jev(spec)
        if "not_asked" in said:
            return said
        scores.update(
            {
                ask[int(name[1:])]["item"]: score
                for name, score in said["answers"].items()
            }
        )
    return {"scores": {item["item"]: scores[item["item"]] for item in items}}


def alike_named(scores: dict, items: list[dict]) -> list[dict]:
    """The items `alike` names: those whose score is at or over SAME_AT, the highest
    first, ALIKE_MOST at most, each with its path, title, `where`, `worth` and
    Jev's score."""
    by_path = {item["item"]: item for item in items}
    named = sorted(
        (
            path
            for path, score in scores.items()
            if path in by_path and score >= SAME_AT
        ),
        key=lambda path: (-scores[path], path),
    )
    return [
        {
            **{key: by_path[path][key] for key in ("item", "title", "where", "worth")},
            "score": scores[path],
            "jev": f"Jev: {scores[path]:.2f}",
        }
        for path in named[:ALIKE_MOST]
    ]


def flag_line(flag: str, value: str) -> str:
    """VALUE of FLAG, stripped, when it is one line of text; a LandError otherwise."""
    if not value.strip() or "\n" in value.strip():
        raise LandError(f"{flag} is one line of text, and it is {value!r}")
    return value.strip()


def cmd_alike(task: Task, where: str, title: str, what: str) -> dict:
    """The items of the backlog folder, as the task's tip holds them, that Jev reads as
    the same defect as the finding (WHERE, TITLE, and the run in the file WHAT): at most
    ALIKE_MOST, at or over SAME_AT, the highest first. With nothing sent, every item,
    for the agent to read. It reads and writes nothing else, and takes no lock: a
    builder runs it while it files by hand."""
    if not (task.worktree / ".git").exists():
        raise LandError(
            f"the task has no worktree at {task.worktree}, and `alike` reads the "
            "backlog folder as the task's tip holds it"
        )
    finding = {
        "where": flag_line("--where", where),
        "title": flag_line("--title", title),
    }
    if not slug_of(finding["title"]):
        raise LandError(
            f"--title is the finding's title, and {title!r} has no word "
            "for an item's file name"
        )
    try:
        run_ = Path(what).read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError) as error:
        raise LandError(
            "--what names the file of the finding's run, "
            f"and {what} does not read ({error})"
        ) from error
    if not run_:
        raise LandError(
            "--what names the file of the finding's run, what happens with the input, "
            f"and {what} is empty"
        )
    finding["run"] = run_
    items = items_at(task, "HEAD")
    out = {
        "task": task.slug,
        "finding": {"where": finding["where"], "title": finding["title"]},
        "items": len(items),
    }
    if not items:
        return {
            **out,
            "alike": [],
            "next": (
                "the backlog folder holds no item: judge the "
                "finding by the bar of rule 6"
            ),
        }
    said = ask_alike(finding, items, sends=jev_sends(task.settings))
    if "not_asked" in said:
        return {
            **out,
            "alike": [],
            "jev": f"Jev: not asked ({said['not_asked']})",
            "read": [
                {key: item[key] for key in ("item", "title", "where", "worth")}
                for item in items
            ],
            "next": (
                "Jev was not asked: read the items of `read` whose title or `where` is "
                "near the finding, and judge it by rule 6 as for "
                "the items `alike` names"
            ),
        }
    named = alike_named(said["scores"], items)
    if not named:
        return {
            **out,
            "alike": [],
            "next": (
                f"Jev reads no item as the same defect at {SAME_AT} or more: "
                "judge the finding by the bar of rule 6"
            ),
        }
    return {
        **out,
        "alike": named,
        "next": (
            "read each item named here. One that holds the same defect gets no second "
            "file: name it on the finding's line. When it says `worth: no` and your "
            "call is over the bar, file a new item with `worth: later` whose run is "
            f'followed by the line "{NOW_OVER.format("PATH")}", and leave the old item '
            "as it is. A defect none of them holds you judge by the bar of rule 6"
        ),
    }


def item_body(  # noqa: PLR0913, PLR0917 - over the limit before the limit was set
    defect: dict,
    round_: int,
    slug: str,
    seen: str,
    today: str,
    same_as: str | None = None,
) -> str:
    """The text of the item `file` writes for DEFECT of review round ROUND_ of task
    SLUG, seen on the day SEEN, in the item format of rule 6: `worth` by the review's
    call, the run, the line of the old item SAME_AS when the defect is one that item
    holds and it says `worth: no` (`NOW_OVER`), where it was seen, and for an item under
    the bar the review's `why` as its last line, `Decided against: WHY`."""
    text = (
        (
            f"---\nworth: {FILED_BARS[defect['bar']]}\n"
            f"where: {defect['where']}\nadded: {today}\n---\n"
            f"# {defect['title']}\n\n{defect['what']}\n\n"
        )
        + (f"{NOW_OVER.format(same_as)}\n\n" if same_as else "")
        + (
            f"Seen outside the change by review round {round_} of task {slug} "
            f"({seen}); the base commit has it.\n"
        )
    )
    if defect["bar"] == "under" and defect.get("why"):
        text += f"\nDecided against: {defect['why']}\n"
    return text


def item_name(
    worktree: Path, folder: str, defect: dict, old: str | None = None
) -> tuple[str, bool]:
    """The path of DEFECT's item by the names `names_for` gives it, in turn: the first
    that holds this very defect (`holds`, True), or the first that is free (False). A
    name that holds another defect is passed: an extra item is the price, never a lost
    one. OLD, the `worth: no` item an over defect gets a new item beside, is never
    its item."""
    for name in names_for(defect):
        path = f"{folder}/{name}"
        file = worktree / path
        if path != old and holds(file, defect):
            return path, True
        if not (file.exists() or file.is_symlink()):
            return path, False
    raise AssertionError("names_for gives names without end")


def same_flags(
    said: list[str], folder: str, in_tip: Callable[[str], bool]
) -> dict[str, str]:
    """The defects `--same rN.M=PATH` names, each with its item: a file of the backlog
    folder FOLDER that IN_TIP finds in the tip. A LandError for any other form."""
    found: dict[str, str] = {}
    for value in said:
        number, _, path = value.partition("=")
        number, path = number.strip(), path.strip()
        if (
            not re.fullmatch(r"r\d+\.\d+", number)
            or not path.startswith(folder + "/")
            or ".." in Path(path).parts
            or not in_tip(path)
        ):
            raise LandError(
                f"--same {value!r} is no defect and item: it is `--same rN.M=PATH`, "
                "the number of a defect (`r1.2`) and the path of the item of the "
                f"backlog folder {folder} that holds it, a file of the task's tip, as "
                "`lem land file` named it",
            )
        found[number] = path
    return found


def cmd_file(  # noqa: C901, PLR0912, PLR0915 - over the limit before the limit was set
    task: Task,
    *,
    again: bool,
    same_said: list[str] | tuple = (),
    new_said: list[str] | tuple = (),
) -> dict:
    """File each defect a review saw outside the change and called over or under the bar
    as an item of the backlog, `worth: later` over it and `worth: no` under it, with the
    review's `why` as the item's last line (`Decided against: WHY`), and commit the
    items, one commit for each round. A cheap defect is a builder's fix or a line of the
    pull request, and no file; one whose `open` item the tip holds is that item, unless
    the defect is over the bar and that item says `worth: no`: then a new item,
    `worth: later`, names the old one (`NOW_OVER`), and the old one stays as it is.

    Before it writes anything, it asks Jev whether each other defect that waits for an
    item is the same defect as an item of the backlog folder at the tip (`ask_alike`).
    When Jev names an item for any of them, it writes nothing and refuses, with each
    such defect and its items: the next run says for each `--same rN.M=PATH` (that item
    holds it: it is kept as its `open`) or `--new rN.M` (a defect of its own: filed). A
    defect whose own item is there already (`holds`) is not asked about. Jev's scores
    are kept in `landing.json` (`alike`, by the finding's digest and the item's path),
    so a second run asks nothing it asked before."""
    task.need_landing()
    task.need_worktree()
    kept = task.kept()
    reads = kept.get("reads", [])
    tip = git(task.worktree, "rev-parse", "HEAD")
    folder = backlog_of(task)
    today = date.today().isoformat()  # noqa: DTZ011 - the item's day as a person reads it, the local one

    def in_tip(path: str) -> bool:
        return in_tree(task, tip, path)

    named_same = same_flags(list(same_said), folder, in_tip)
    named_new = {value.strip() for value in new_said}
    both = sorted(set(named_same) & named_new)
    if both:
        raise LandError(
            f"{', '.join(both)} is named by both --same and --new: a defect is the "
            "item it names, or a defect of its own"
        )
    filed, same, open_, gone, written = [], [], [], [], {}
    # each defect to write, with the `worth: no` item it is a new item beside, or None
    todo: list[tuple[dict, dict, str | None]] = []
    free: set[str] = set()
    for read in reads:
        if not read["answered"]:
            continue
        for defect in outside_of(read):
            if defect["bar"] not in FILED_BARS:
                continue
            entry = {
                "round": read["round"],
                "number": defect["number"],
                "title": defect["title"],
            }
            if defect.get("item"):
                if in_tip(defect["item"]):
                    continue
                if not again:
                    gone.append({**entry, "item": defect["item"]})
                    continue
                todo.append((read, defect, None))
                continue
            if not (defect.get("open") and in_tip(defect["open"])):
                free.add(defect["number"])
            held = named_same.get(defect["number"]) or defect.get("open")
            if held and in_tip(held):
                if defect["bar"] == "over" and worth_at(task, tip, held) == "no":
                    todo.append((read, defect, held))
                else:
                    open_.append({**entry, "item": held})
                continue
            todo.append((read, defect, None))
    stray = sorted((set(named_same) | named_new) - free)
    if stray:
        raise LandError(
            (
                f"{', '.join(stray)} is no defect that waits for an item with no open "
                "item of its own: --same and --new name such a defect by its number"
            )
            + (
                f", and the ones here are {', '.join(sorted(free))}"
                if free
                else ", and none waits here"
            ),
        )
    alike = check_alike(
        task,
        [
            (read, defect)
            for read, defect, old in todo
            if old is None
            and not defect.get("item")
            and defect["number"] not in named_new
            and not item_name(task.worktree, folder, defect)[1]
        ],
        tip,
    )
    for number, path in named_same.items():
        next(
            defect
            for read in reads
            for defect in outside_of(read)
            if defect["number"] == number
        )["open"] = path
    for read, defect, old in todo:
        path, held = item_name(task.worktree, folder, defect, old)
        entry = {
            "round": read["round"],
            "number": defect["number"],
            "title": defect["title"],
            "item": path,
        }
        if held:
            same.append(entry)
        else:
            (task.worktree / path).parent.mkdir(parents=True, exist_ok=True)
            write_whole(
                task.worktree / path,
                item_body(
                    defect,
                    read["round"],
                    task.slug,
                    read.get("date", today),
                    today,
                    old,
                ),
            )
            filed.append(entry)
            written.setdefault(read["round"], []).append(path)
        defect["item"] = path
    # One commit for each round, of its new items and nothing else: the worktree was
    # clean. A commit hook of the project may refuse the message, which has Lem's form
    # and not the project's: the items stay written, and a builder commits them in the
    # project's form, after which a second run finds each one by its defect and
    # records it.
    for number, paths in written.items():
        git(task.worktree, "add", "--", *paths)
        made = run(
            [
                "git",
                "-C",
                str(task.worktree),
                "commit",
                "-q",
                "-m",
                f"docs(backlog): what review round {number} saw outside {task.slug}",
                "--",
                *paths,
            ],
            check=False,
        )
        if made.returncode != 0:
            said = (
                " ".join((made.stderr or made.stdout).split())
                or f"git exited {made.returncode} and said nothing"
            )
            raise LandError(
                f"the commit of the backlog items of review round {number} was "
                f"refused, most likely by a commit hook of the project: {said}. "
                "The items are written and staged in the worktree "
                f"({', '.join(paths)}): a builder commits them with a message in the "
                f"form the hook asks for (`git -C {task.worktree} commit -m MESSAGE -- "
                f"{' '.join(paths)}`), never with --no-verify, then "
                f"`lem land file {task.slug}` runs again and finds "
                "each item by its defect",
            )
    before, tip = tip, git(task.worktree, "rev-parse", "HEAD")
    if filed or same:
        items = [{**entry, "new": True} for entry in filed] + [
            {**entry, "new": False} for entry in same
        ]
        script(
            "project.py",
            task.worktree,
            "log",
            task.slug,
            "review.filed",
            f"items:={json.dumps(items)}",
            f"tip={tip[:9]}",
        )
    # A run cut off after its commit finds each item again by its defect, so this write
    # comes last; a resolution or a rebase whose tip these commits moved names the new
    # one (`filed_on`).
    task.keep(reads=reads, **filed_on(task.kept(), before, tip))
    return {
        "task": task.slug,
        "filed": filed,
        "same": same,
        "open": open_,
        "gone": gone,
        "alike": alike,
        "tip": tip,
    }


def check_alike(
    task: Task, waiting: list[tuple[dict, dict]], tip: str
) -> dict[str, str]:
    """`file`'s look for the items that may hold each defect of WAITING (its read and
    the defect), before any file is written: Jev's read of each against every item of
    the backlog folder at TIP (`ask_alike`), its scores kept in `landing.json` under
    `alike`, by the finding's digest (`finding_key`) and the item's path. A LandError
    that names each defect Jev reads as one an item holds, with its items
    (`alike_named`) and the two ways on; otherwise what Jev said of each defect, by its
    number: `none named`, `Jev: not asked (WHY)`, or `no item to compare` when the
    backlog folder at TIP holds no item."""
    if not waiting:
        return {}
    items = items_at(task, tip)
    if not items:
        return {defect["number"]: "no item to compare" for _, defect in waiting}
    kept = dict(task.kept().get("alike") or {})
    sends = jev_sends(task.settings)
    said: dict[str, str] = {}
    named: list[tuple[dict, list[dict]]] = []
    for _, defect in waiting:
        finding = {
            "where": defect["where"],
            "title": defect["title"],
            "run": defect["what"],
        }
        key = finding_key(defect["where"], defect["title"], defect["what"])
        read = ask_alike(finding, items, sends=sends, known=kept.get(key))
        if "not_asked" in read:
            said[defect["number"]] = f"Jev: not asked ({read['not_asked']})"
            continue
        kept[key] = read["scores"]
        found = alike_named(read["scores"], items)
        if found:
            named.append((defect, found))
        else:
            said[defect["number"]] = "none named"
    if kept != (task.kept().get("alike") or {}):
        task.keep(alike=kept)
    if named:
        listed = "; ".join(
            f'{defect["number"]} "{defect["title"]}" (`{defect["where"]}`): '
            + ", ".join(
                (
                    f'`{item["item"]}` "{item["title"]}" ({item["jev"]}, '
                    f"worth: {item['worth'] or 'none'})"
                )
                for item in found
            )
            for defect, found in named
        )
        first = named[0][0]["number"]
        raise LandError(
            f"{len(named)} defect(s) to file may be one an item of the backlog holds "
            f"already, by Jev's read at {SAME_AT} or more: {listed}. "
            "Nothing is written. Read each item named, then run "
            f"`lem land file {task.slug}` again with, for each defect named here, "
            f"`--same {first}=PATH` when that item holds the defect (it is kept as its "
            "open item, and no file is written for it; an item that says `worth: no` "
            "of a defect called over the bar gets a new item, `worth: later`, that "
            f"names it), or `--new {first}` when it is a defect "
            "of its own (it is filed)",
        )
    return said


def task_file(value: str, flag: str, directory: Path, here: Path) -> str:
    """The file a step's FLAG names: VALUE from the working directory HERE (or an
    absolute path), else a relative VALUE in the task's DIRECTORY. A LandError that
    names each place it looked when neither has it."""
    given = Path(value)
    first = given if given.is_absolute() else here / given
    if first.is_file():
        return str(first)
    if given.is_absolute():
        raise LandError(
            f"{value} is not a file; {flag} names a file, by its path or by its name "
            f"in the task directory {directory}"
        )
    second = directory / given
    if second.is_file():
        return str(second)
    raise LandError(
        f"{value} is not a file in the working directory ({first}) nor in the task "
        f"directory ({second}); {flag} names a file by its path, "
        "or by its path inside the task directory"
    )


def failed_attempt(said: dict) -> bool:
    """Whether a review's record is of an attempt that got no answer at all: nobody in
    `answered`, a reason for each source in `silent`, and no finding. The review agent
    writes it when every source was silent, and the landing session when the review
    agent itself ended with no files; it counts as an attempt, so a second one in a row
    sends the request on as not reviewed (`due_of`)."""
    silent = said.get("silent")
    return (
        said.get("answered") == []
        and isinstance(silent, list)
        and bool(silent)
        and all(
            isinstance(item, dict) and str(item.get("why") or "").strip()
            for item in silent
        )
        and not any(said.get(key) for key in ("must_fix", "should", "nit", "outside"))
    )


def record_tip_refusal(said: object, tip: str, slug: str) -> str | None:
    """Why a review's record whose `tip` is SAID is not the review of the branch at TIP;
    None when it is. The attempt counts the records, so a review of an earlier tip
    carries the same number."""
    if said == tip:
        return None
    if not isinstance(said, str) or not re.fullmatch(r"[0-9a-f]{40}", said):
        return (
            "`tip` in the record is the whole commit the review read, 40 hex digits, "
            f"as `lem land read {slug}` printed it, and it is {said!r}"
        )
    return (
        f"the record is of the review of {said[:12]}, and the branch is at {tip[:12]} "
        "now: that review read another change, and it is not written down. "
        f"`lem land read {slug}` says what is due for this one"
    )


def cmd_read(task: Task, record: str | None) -> dict:  # noqa: C901, PLR0912, PLR0915 - over the limit before the limit was set
    task.need_landing()
    task.need_worktree()
    state = due(task)
    missing = gate_missing(task, state["tip"])
    if missing:
        raise LandError(
            f"the review is of the tip the checks passed on, and {missing}; "
            f"`lem land checks {task.slug}` comes first"
        )
    reads = task.kept().get("reads", [])
    if record is None:
        # The review starts when it is due, and its record ends it. A second `read` of
        # the same attempt, after a cut-off run or before `file`, is the same review and
        # logs no second start.
        if state["due"] == "review" and not any(
            event.get("event") == "review.start"
            and event.get("attempt") == state["attempt"]
            for event in events_of(task)
        ):
            script(
                "project.py",
                task.worktree,
                "log",
                task.slug,
                "review.start",
                f"attempt:={state['attempt']}",
                f"floor={state['floor']}",
            )
        rules = json.loads(
            script(
                "project.py",
                task.worktree,
                "rules",
                "--range",
                f"{state['base']}..{state['tip']}",
            ).stdout
        )["rules"]
        return {
            "task": task.slug,
            "due": state["due"],
            "why": state["why"],
            "floor": state["floor"],
            "kinds": KIND_SAYS,
            "round": state["round"],
            # the number the record of this review carries, so that the same record is
            # never written down twice, and the tip it reads, which the record names too
            "attempt": state["attempt"],
            "tip": state["tip"],
            # the defects outside the change that reviews called over or under the bar
            # and that have no item yet: `lem land file` files them
            "to_file": to_file(
                reads,
                lambda path: in_tree(task, state["tip"], path),
                lambda path: worth_at(task, state["tip"], path) == "no",
            ),
            "careful": state["careful"],
            "tasks": state["tasks"],
            "small": state["small"],
            "lines": state["lines"],
            "in_parts": state["in_parts"],
            # a builder's resolution of a conflict with the base, when the review due is
            # the read of it: what it changed is what `range_diff` shows, the branch's
            # commits before the rebase beside the same commits after it
            "resolution": state["resolution"],
            "reads": [
                {
                    key: value
                    for key, value in read.items()
                    if key not in ("contents", "carried")
                }
                for read in reads
            ],
            # what a reviewer gets, and nothing of the builder's reasoning
            "inputs": {
                # the owner's words as given, and the request as Lem wrote it down,
                # where the task has them
                **{
                    name: str(task.directory / file)
                    for name, file in (("words", "ask.txt"), ("request", "task.md"))
                    if (task.directory / file).is_file()
                },
                "plan": criteria_of(task)["plan"],
                "range": f"{state['base']}..{state['tip']}",
                "worktree": str(task.worktree),
                "rules": [rule["file"] for rule in rules],
                "bar": task.kept().get("checks", {}).get("bar"),
                # what must never go wrong, from the main checkout's settings: the
                # review reads the diff against each
                "topics": task.settings["flow"]["topics"],
                # what the branch filed in the backlog before the review: a defect named
                # there is not reported again
                "filed": branch_items(task),
                # the base's items: a defect one of them holds is named by its path in
                # `open`, and gets no second file
                "backlog": base_items(task, state["base"]),
                # where the project's review tool keeps each profile and lens, with what
                # each is for
                "review": task.settings["places"]["review"]["path"],
            },
        }
    if state["due"] != "review":
        raise LandError(f"no review is due: {state['why']}")
    try:
        said = json.loads(Path(record).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise LandError(
            f"{record} does not read as JSON ({error}); --record names the file that "
            "says what the review was and what it found"
        ) from error
    known = {
        "attempt",
        "tip",
        "kind",
        "ran",
        "left_out",
        "answered",
        "silent",
        "bar",
        "must_fix",
        "should",
        "nit",
        "outside",
        "careful",
        "careful_why",
    }
    if (
        not isinstance(said, dict)
        or set(said) - known
        or not {"attempt", "tip", "kind", "answered"} <= set(said)
    ):
        raise LandError(
            "the record is one object with `attempt`, `tip`, `kind` and `answered`, "
            f"and of the others what applies: {', '.join(sorted(known))}"
        )
    # A record that is sent again, after a run that was cut off or by mistake, must not
    # count as a second review: it says which start of the review it is, and only the
    # next one is taken.
    if said["attempt"] != state["attempt"]:
        raise LandError(
            (
                f"the record says attempt {said['attempt']!r}, and the next review of "
                f"this task is attempt {state['attempt']}: "
            )
            + (
                "that review is written down already"
                if said["attempt"] in [read.get("attempt") for read in reads]
                else "`lem land read` prints the number a record carries"
            ),
        )
    # The attempt counts the records, not the tips: the record also names the tip its
    # review read.
    stale = record_tip_refusal(said["tip"], state["tip"], task.slug)
    if stale:
        raise LandError(stale)
    kind = said["kind"]
    if kind not in KINDS:
        raise LandError(
            f"`kind` is one of {', '.join(KINDS)}: "
            f"{'; '.join(f'{name} is {says}' for name, says in KIND_SAYS.items())}"
        )
    if KINDS.index(kind) < KINDS.index(state["floor"]):
        raise LandError(
            f"this change gets {KIND_SAYS[state['floor']]} at the least "
            f"({state['why']}), and the record says {KIND_SAYS[kind]}"
        )
    # The careful call is the review's own reading of the diff against the project's
    # topics, by an agent that did not build it: it is what lets an agent merge, or
    # keeps the merge a person's. A review that got no answer at all, written down by
    # the session when its agent died, makes none: it counts as an attempt, and the next
    # one makes the call.
    call, call_why = said.get("careful"), said.get("careful_why")
    failed = failed_attempt(said) and call is None and call_why is None
    if not failed and (
        not isinstance(call, bool)
        or not isinstance(call_why, str)
        or not call_why.strip()
        or "\n" in call_why.strip()
    ):
        raise LandError(
            'the record makes the careful call: "careful": true or false, the '
            "review's own reading of the diff against each of the project's topics "
            '(`topics` in what `lem land read` printed), and "careful_why": '
            "one line that names the topic the change reaches, or what was checked to "
            "say that it reaches none",
        )
    if call and kind != "full":
        raise LandError(
            "a change the review calls careful gets the project's full set, and the "
            f"record says {KIND_SAYS[kind]}: the review runs the full set and writes "
            'its record with "kind": "full"',
        )
    ran, left_out, silent, bar_says = (
        named(said.get(key, []), key) for key in ("ran", "left_out", "silent", "bar")
    )
    answered = said["answered"]
    if not isinstance(answered, list) or not all(
        isinstance(source, str) and source.strip() for source in answered
    ):
        raise LandError(
            "`answered` is the list of the sources that answered, by name; "
            "an empty list says that none did"
        )
    if kind != "read" and not ran and not failed:
        raise LandError(
            "a round names each profile it ran in `ran`, "
            "with why that profile fits this change"
        )
    if kind == "full" and left_out:
        raise LandError(
            "the project's full set leaves no profile out: a profile may be added to "
            'it, never dropped; write "left_out": [] on a full review'
        )
    counts = {key: said.get(key, 0) for key in ("must_fix", "should", "nit")}
    if not all(
        isinstance(count, int) and not isinstance(count, bool) and count >= 0
        for count in counts.values()
    ):
        raise LandError("`must_fix`, `should` and `nit` are counts")
    outside = defects_of(
        said.get("outside", []),
        state["attempt"],
        backlog_of(task),
        lambda path: file_at(task, state["base"], path),
    )
    if not answered and (any(counts.values()) or outside):
        raise LandError(
            "the record has findings and no source that answered: "
            "`answered` names who found them"
        )
    # A lowered bar is what the owner reads himself, so the review says what it thinks
    # of each one.
    lowered = sorted(
        {
            entry["file"]
            for entry in task.kept().get("checks", {}).get("bar", {}).get("lowered", [])
        }
    )
    unsaid = [
        file for file in lowered if file not in {entry["name"] for entry in bar_says}
    ]
    if answered and unsaid:
        raise LandError(
            f"the change lowers the bar in {', '.join(unsaid)} and the record says "
            'nothing of it: `bar` holds one {"name": FILE, "why": WHAT THE REVIEW '
            "SAYS OF THE BUILDER'S REASON} for each such file",
        )
    entry = {
        "attempt": state["attempt"],
        "round": state["round"],
        "kind": kind,
        "ran": ran,
        "left_out": left_out,
        "answered": answered,
        "silent": silent,
        "bar": bar_says,
        **counts,
        "outside": outside,
        "careful": call,
        "careful_why": call_why.strip() if isinstance(call_why, str) else None,
        "date": date.today().isoformat(),  # noqa: DTZ011 - the review's day as a person reads it, the local one
        "verdict": "not reviewed"
        if not answered
        else "must-fix"
        if counts["must_fix"]
        else "clean",
        "tip": state["tip"][:9],
        "patch": state["patch"],
        # the read of a builder's resolution of a conflict, which is no round of
        # the change
        **({"of": "resolution"} if state["resolution"] else {}),
    }
    # The event first: a run that is cut off between the two writes the review down at
    # its next run, and the second event has the same attempt, by which a reader of the
    # log knows it.
    script(
        "project.py",
        task.worktree,
        "log",
        task.slug,
        "review",
        *(f"{key}:={json.dumps(value)}" for key, value in entry.items()),
    )
    # The contents of the change stay out of the log: only `covers` reads them, from the
    # kept record.
    task.keep(reads=[*reads, {**entry, "contents": state["contents"]}])
    if state["resolution"] and answered:
        # the resolution is read: from here the rules of the change hold again
        task.keep(resolution={**task.kept()["resolution"], "read": state["attempt"]})
    # A change the review calls careful and the plan did not is a lesson about the
    # plan's call: one event for the retro, the first time a review finds it.
    if (
        answered
        and call
        and isinstance(call_why, str)
        and not plan_careful(task)
        and not any(
            record.get("event") == "careful.missed" for record in events_of(task)
        )
    ):
        script(
            "project.py",
            task.worktree,
            "log",
            task.slug,
            "careful.missed",
            f"round:={state['round']}",
            f"why={call_why.strip()}",
        )
    return {
        "task": task.slug,
        "recorded": entry,
        "next": due(task)["due"],
        "to_file": to_file(
            task.kept()["reads"],
            lambda path: in_tree(task, state["tip"], path),
            lambda path: worth_at(task, state["tip"], path) == "no",
        ),
        # the cheap defects of this record, which a builder that fixes its must-fix
        # fixes too: its brief names each by its number
        "cheap": [
            {key: defect[key] for key in ("number", "where", "title")}
            for defect in outside
            if defect["bar"] == "cheap"
        ],
    }


def not_green(task: Task, state: dict) -> list[str]:
    """Each reason for which this request is not green, one line each; none when it
    is green."""
    reasons = []
    # The fast track has no interview, no read of its criterion, no plan. A task on it
    # that is careful after all is read by a person, whatever its checks and its
    # review say.
    if criteria_of(task)["small"] and state["careful"]:
        reasons.append(
            f"careful on the fast track ({reason(state['careful'][0])}): "
            "it took the fast track, with no interview, no personas' read of its "
            "criterion and no plan, so a person reads it",
        )
    # the personas' read of the criteria, started twice with no answer: the criteria
    # went on unread
    read = criteria_read_of(task)
    if read is not None and unanswered(task) >= SILENT_READS:
        quiet = "".join(
            f"; no answer from {source['name']} ({source['why']})"
            for source in read.get("silent", [])
        )
        reasons.append(
            "the criteria were not read: the personas' read was started twice "
            f"and nobody answered{quiet}"
        )
    commands, brought = task.gate()
    if brought:
        reasons.append(
            (
                "the checks came with this change: the main checkout's settings name "
                "no command of the checks, and the branch's .lem/settings.toml brings "
            )
            + ", ".join(f"`{command}`" for command in commands)
            + ". Read the checks once: every later task is checked by them",
        )
    if state["due"] != "none":
        reasons.append(state["why"])
    # A lowered bar is never green, with a reason too: it is the one change that makes
    # the other green lines worth less, so the owner reads its line himself.
    kept = task.kept()
    said = {
        entry["name"]: entry["why"]
        for read in kept.get("reads", [])
        if read["answered"]
        for entry in read.get("bar", [])
    }
    for entry in (kept.get("checks") or {}).get("bar", {}).get("lowered", []):
        review = (
            f"The review: {said[entry['file']]}"
            if entry["file"] in said
            else "No review said anything of it."
        )
        reasons.append(
            f"the bar is lower in `{entry['file']}` ({entry['what']}). "
            f"The builder: {entry['reason']} {review}"
        )
    # a change that a later approval of his took over is his, and no cause of not green
    found = criteria_of(task)
    reasons.extend(
        (
            f"criterion {change['criterion']} {CHANGE_HOW[change['how']]} during "
            f"the build: {change_why(task, change)}"
        )
        for change in found["history"]
        if change["taken_over_by"] is None and not owners_change(task, change)
    )
    # criteria approved without him, which no approval of his took over: the newest
    # approval is the one that holds
    approval = found.get("approved") or {}
    if approval.get("by") == "alone":
        how = (
            "while the task ran without the owner"
            if task.record.get("without_owner") or not someone_elses(task)
            else "without the owner, since someone else wrote the request"
        )
        reasons.append(
            "the owner did not approve the criteria: they were approved "
            f"on {approval['at'][:10]} {how}"
        )
    for decision in task.decisions():
        if without_him(decision):
            # past the personas: the dialectic, the experts, or the lead's pick that no
            # level settled
            who = (
                "the lead's pick, which no level of the ladder settled"
                if decision.get("unsettled")
                else f"by {taken_by(decision)}"
            )
            reasons.append(
                f"decision {decision['id']} was taken without the owner "
                f'({decision["what"]}): "{decision["chose"]}", {who}'
            )
    return reasons


def without_him(decision: dict) -> bool:
    """Whether a decision is the owner's and was taken without him, so that the request
    is not green for it: past the personas (the dialectic, the experts), or a pick that
    no level settled. The ladder decides each one at once, and he reads it here."""
    return decision.get("by") in PAST_PERSONAS or bool(decision.get("unsettled"))


def owners_change(task: Task, change: dict) -> bool:
    """Whether a criterion change came from the owner's own help on a breaker: his
    decision makes it his, as a later approval of his does."""
    led = next(
        (
            decision
            for decision in task.decisions()
            if decision["id"] == change.get("decision")
        ),
        None,
    )
    return bool(led and led.get("by") == "owner" and "breaker" in led)


def without_owner(task: Task) -> str | None:
    """The line that says when the task ran without the owner, from the spans
    `lem project tasks` gives (the owner's away and back, a night's mark), with the
    words that started and ended each; none for a task that always ran with him."""

    def said(words: dict) -> str:
        return (
            f"{'the owner' if words.get('by') == 'owner' else 'Lem'}: "
            f'"{words.get("words")}"'
        )

    spans = [
        f"from {utc(span['from'])} ({said(span['started'])})"
        + (f" to {utc(span['to'])} ({said(span['ended'])})" if span["to"] else "")
        for span in task.record.get("without_owner") or []
    ]
    return f"It ran without the owner {', and '.join(spans)}." if spans else None


def utc(stamp: str) -> str:
    return f"{stamp[:10]} {stamp[11:16]} UTC"


def change_why(task: Task, change: dict) -> str:
    """Why a criterion changed: the reason the record gives, and the decision that led
    to it, when one did."""
    if "decision" not in change:
        return change["why"]
    led = next(
        decision
        for decision in task.decisions()
        if decision["id"] == change["decision"]
    )
    how = (
        f"the owner's help on breaker {led['breaker']}, which took"
        if owners_change(task, change)
        else f"where {taken_by(led)} took"
    )
    return (
        f"{reason(change['why'])}, after decision {led['id']} ({led['what']}), "
        f'{how} "{led["chose"]}"'
    )


def change_line(task: Task, change: dict) -> str:
    """One recorded change of a criterion as one line of the pull request: what it was,
    what it is, why, and who."""
    # a criterion with a case is its sentence and its steps, one to a line: here
    # one line
    was, now = (" ".join(str(change.get(key)).split()) for key in ("was", "now"))
    said = {
        "changed": f'was "{was}", now "{now}"',
        "added": f'added, "{now}"',
        "removed": f'removed, was "{was}"',
    }[change["how"]]
    who = (
        ""
        if "decision" in change
        else " By the lead."
        if change["by"] == "lead"
        else f" By the personas: {change['said']}"
    )
    later = (
        f" Approved by the owner afterwards (approval {change['taken_over_by']})."
        if change.get("taken_over_by")
        else ""
    )
    return (
        f"- criterion {change['criterion']}: {said}. "
        f"{reason(change_why(task, change))}.{who}{later}"
    )


def reason(text: str) -> str:
    """A reason as written, without its own full stop, for a sentence around it."""
    return text.rstrip(".")


def one_expert(decision: dict) -> bool:
    """Whether one expert answered alone: the machine had one of the
    agents (`advisers`)."""
    return len(decision.get("advisers") or "ab") == 1


def taken_by(decision: dict) -> str:
    """Who took a decision, for a line of the pull request: one expert is named
    as one."""
    return (
        "one expert"
        if decision.get("by") == "experts" and one_expert(decision)
        else TAKEN_BY[decision["by"]]
    )


def breaker_lines(task: Task) -> list[str]:
    """One line for each time the circuit breaker stopped the build: its cause and how
    it ended."""
    out = []
    for breaker in task.breakers():
        cause = BREAKER_SAYS[breaker["cause"]] + (
            f" ({breaker['irreversible']})" if breaker.get("irreversible") else ""
        )
        ended = (
            f"the owner helped, decision {breaker['help']}"
            if breaker["state"] == "helped"
            else "it waits for the owner"
        )
        out.append(
            f"- the build stopped at breaker {breaker['id']}, {utc(breaker['at'])}: "
            f"{breaker['what']}. Why it stopped: {cause}; {ended}."
        )
    return out


def decided(decision: dict) -> str:
    """One decision of the record as one line of the pull request: what, what was
    chosen, by whom, why."""
    return f'- {decision["what"]}: "{decision["chose"]}"' + after(decision)


def after(decision: dict) -> str:
    """What follows the option a decision took in its line: by whom, why, and what each
    level and the owner said. It opens with ", " or "."."""
    line = f", by {taken_by(decision)}"
    if decision.get("unsettled"):
        line = ", the lead's pick, which no level of the ladder settled"
    if decision["by"] == "owner" and "breaker" in decision:
        # his help on a breaker: the build stopped and he decided; nothing of it is a
        # cause of not green
        line += f", his help on breaker {decision['breaker']}. {decision['why']}"
    elif decision["by"] == "personas":
        # the one stop of the ladder past the gate that is green: how many voted, in how
        # many model families
        votes = decision["votes"]
        personas = {name.rpartition(", ")[0] or name for name, _ in votes}
        families = {name.rpartition(", ")[2] for name, _ in votes if ", " in name}
        named = (
            f", {FAMILIES.get(len(families), f'{len(families)} model families')}"
            if families
            else ""
        )
        line += (
            f": {len(votes)} votes of {len(personas)} personas{named}, "
            f"all for it. {decision['why']}"
        )
    else:
        line += f". {decision['why']}"
    if decision.get("levels"):
        line += (
            " Each level: "
            + "; ".join(f"{name}: {said}" for name, said in decision["levels"].items())
            + "."
        )
    if decision.get("words", decision["chose"]) != decision["chose"]:
        line += f' The owner\'s words: "{decision["words"]}"'
    return line


def checked_criteria(checks: dict) -> dict:
    """What the checks kept of the check of the criteria."""
    kept = checks.get("criteria") or {}
    return {**kept, "tests": kept.get("tests", [])}


def criteria_check_line(held: dict) -> str:
    """The check of the criteria as one line of the pull request's checks: how many
    tests pass on the branch and fail on the base commit, and, when the checks took the
    polish pass's result, that the tests were taken from the pass at its commit and not
    run again."""
    tests, without, taken = (
        held["tests"],
        held.get("without_a_test", []),
        held.get("taken"),
    )
    line = (
        f"- the tests of the criteria: {len(tests)} pass on the branch and "
        "fail on the base commit"
    )
    if taken:
        line += (
            f", taken from the polish pass at {str(taken['at'])[:9]}, and not run again"
        )
    return line + (
        (
            f"; {len(without)} "
            f"{'criterion has' if len(without) == 1 else 'criteria have'} no test"
        )
        if without
        else ""
    )


def criterion_lines(criterion: dict, *, chart: bool = False) -> list[str]:
    """One criterion as a numbered item: its sentence, the steps of its case under it,
    and its chart when `chart` (the pull request leaves the chart to the
    owner's page)."""
    out = [
        f"{criterion['n']}. {criterion['text']}",
        *(f"   {step}" for step in criterion.get("case", [])),
    ]
    if chart and criterion.get("chart"):
        out += [
            "",
            "   ```mermaid",
            *(f"   {row}" if row else "" for row in criterion["chart"].splitlines()),
            "   ```",
            "",
        ]
    return out


def criteria_lines(found: dict, held: dict, *, chart: bool = False) -> list[str]:
    """Each criterion of the text, with its case, each of its tests and what the check
    gave, or its line of no test."""
    out = []
    for criterion in found["criteria"]:
        out += criterion_lines(criterion, chart=chart)
        for test in criterion["tests"]:
            proof = held.get((criterion["n"], test["command"]))
            gave = (
                "passes on the branch, fails on the base commit"
                if proof and not proof["problem"]
                else "not checked"
            )
            out.append(f"   - `{test['command']}`: {gave}")
        if criterion["no_test"]:
            out.append(f"   - no test: {criterion['no_test']}")
    return out


def builder_filed(task: Task) -> list[dict]:
    """Each item the branch adds to the backlog folder, whoever filed it (a review
    through `file`, the polish pass, the fast track's builder, a session by hand), with
    its title and its `worth` as the tip's file says them: the pull request lists each
    under the heading its `worth` gives."""
    return items_added(task, git(task.worktree, "merge-base", "HEAD", task.onto))


def synced(task: Task) -> str | None:
    """What bringing an open task onto a base that moved did, in one line for the pull
    request and for Lem's line to the owner: why, the rebase, a conflict and who
    resolved it, and what carried over: the review and the merge review, as `propose`
    worked them out (`carry` of the kept `sync`, `moved_carry`). None for a landing that
    did not start from `open`, or before its `base`."""
    sync = task.kept().get("sync")
    if not sync or not sync.get("onto"):
        return None
    return sync_line(sync, task.base)


def sync_line(sync: dict, base: str) -> str:
    """`synced` from the kept `sync` and the base branch's name: the one place of the
    line's words."""
    after = " after the forge called it conflicting" if sync.get("conflicting") else ""
    line = (
        f"rebased on {base}{after}"
        if sync.get("moved")
        else f"checked again on {base}{after}, with no rebase needed"
    )
    files = sync.get("conflict") or []
    if files and sync.get("resolved"):
        line += (
            f"; one conflict in {files[0]}"
            if len(files) == 1
            else f"; conflicts in {len(files)} files, {', '.join(files)}"
        )
        line += ", resolved by a builder"
    carry = sync.get("carry")
    for said in (
        carry["review"] if carry else review_line(sync.get("carried")),
        merge_line(carry),
    ):
        if said:
            line += f"; {said}"
    return line + "; the checks passed again"


def review_line(carried: dict | None) -> str | None:
    """What a rebase with no conflict carried of the review (`carried` of the kept
    `sync`: the round and the must-fix it left), in the words of the pull request's text
    and of the `proposed` event (`moved_carry`'s `review`); None when it
    carried none."""
    if not carried:
        return None
    return "the review carried over the rebase" + (
        ", and its open must-fix" if carried["must_fix"] else ""
    )


def edited_line(bar: dict) -> list[str]:
    """The existing tests, snapshots and test configurations the change edits, as one
    line under the bar's: no mark finds a changed expectation, so a reviewer knows where
    to look first."""
    edited = bar.get("edited") or []
    if not edited:
        return []
    kinds = [
        (kind, [entry["file"] for entry in edited if entry["kind"] == kind])
        for kind in ("test", "snapshot", "test configuration")
    ]
    said = [
        f"{len(files)} existing {kind if len(files) == 1 else kind + 's'} ("
        + ", ".join(f"`{file}`" for file in files)
        + ")"
        for kind, files in kinds
        if files
    ]
    return [
        "- the change edits "
        + (", ".join(said[:-1]) + " and " + said[-1] if len(said) > 1 else said[0])
    ]


def resolution_line(read: dict) -> str:
    """The read of a conflict's resolution as one line of the pull request's checks."""
    who = (
        f"answered: {', '.join(read['answered'])}"
        if read["answered"]
        else "no source answered"
    )
    said = (
        (
            f"{read['verdict']}, {read['must_fix']} must-fix, {read['should']} should, "
            f"{read['nit']} nit"
        )
        if read["answered"]
        else "not reviewed"
    )
    return (
        f"- the read of the conflict's resolution ({KIND_SAYS[read['kind']]}; "
        f"{who}): {said}"
    )


def head_lines(task: Task, state: dict) -> list[str]:
    """The head of a pull request's text on either track, in the order the owner reads
    it: green or not green with each reason, the time the task ran without him, why it
    is careful, and what bringing it onto a base that moved did."""
    reasons = not_green(task, state)
    out = (
        ["**Not green.**", "", *(f"- {why}" for why in reasons), ""]
        if reasons
        else [GREEN, ""]
    )
    alone = without_owner(task)
    if alone:
        # which part ran without him: a cause of not green only through what was decided
        # then, which the lines above name
        out += [alone, ""]
    if state["careful"]:
        # a careful request is a person's to merge, green or not, and he reads why first
        out += [
            (
                "**Careful**, so the owner merges it: "
                f"{'; '.join(reason(why) for why in state['careful'])}."
            ),
            "",
        ]
    moved = synced(task)
    if moved:
        # an open task brought onto a base that a merge moved: what happened to it since
        # the owner last read it
        out += [moved[0].upper() + moved[1:] + ".", ""]
    return out


def issue_line(task: Task) -> list[str]:
    """The line `Issue: #42` under the request, for a task whose ticket is an issue of a
    project whose tracker is GitHub: GitHub links the issue and the pull request both
    ways from it. No word that closes the issue (`Closes`, `Fixes`): `lem issue land`
    comments and closes it itself."""
    ticket = task.record.get("ticket") or ""
    if (task.settings.get("tracker") or {}).get(
        "kind"
    ) != "github" or not ticket.startswith("#"):
        return []
    return [f"Issue: {ticket}", ""]


def small_text(task: Task, notes: str, state: dict, jev: dict | None = None) -> str:
    """The text of a pull request on the fast track: green or not, the criterion, the
    checks, the read. What the fast track does not have (a plan, a personas' read, a
    polish pass, a talk) gets no line. Its notes have no fixed headings, so the text
    writes the four of what was seen outside the change itself, at its end, each when it
    has a line: the items the branch adds, its builder's and the reviews', under
    `## Filed in the backlog` or `## Filed as not worth it` by their `worth`, the cheap
    defects fixed on the way, and the defects seen and not filed. JEV ends the line of
    each item Jev read (`jev_marked`); the notes come with Jev's ends of their own lines
    already (`pr_text`)."""
    kept = task.kept()
    head, parts = sections_of(notes)
    own = {
        heading: lines_of(lines)
        for heading, lines in parts
        if heading in (FILED, NOT_WORTH, FIXED, SEEN)
    }
    fixed = "\n".join(own.get(FIXED, []))
    checks = kept.get("checks") or {}
    found = criteria_of(task)
    ask = (
        (task.directory / "ask.txt").read_text(encoding="utf-8").strip()
        if (task.directory / "ask.txt").is_file()
        else ""
    )
    held = {
        (test["criterion"], test["command"]): test
        for test in checked_criteria(checks)["tests"]
    }
    out = head_lines(task, state)
    out += [
        "## The request",
        "",
        *(
            f"> {line}"
            for line in (
                ask or "(the owner's words were not kept for this task)"
            ).splitlines()
        ),
        "",
    ]
    out += issue_line(task)
    approval: dict[str, Any] = found.get("approved") or {}
    opened_by = (
        "the night opened the task"
        if task.record.get("night")
        else "someone else wrote the request"
    )
    by = {
        "lem": (
            f" Lem approved it in the owner's name on {approval.get('at', '')[:10]}; "
            "the personas did not read it."
        ),
        # a night's task, or a request someone else wrote: not the owner's own sentence,
        # so not his approval either
        "alone": (
            f" Lem approved it on {approval.get('at', '')[:10]} without the owner "
            f"({opened_by}); the personas did not read it."
        ),
    }.get(approval.get("by", ""), "")
    out += [
        "## The acceptance criterion",
        "",
        f"The fast track, because {reason(found['why'])}.{by}",
        "",
    ]
    out += criteria_lines(found, held)
    out += [change_line(task, change) for change in found["history"]]
    out += ["", "## Checks", ""]
    out += [
        f"- check, `{command['command']}`"
        f"{' (serial, under the lock)' if command.get('serial') else ''}: "
        f"{command['last'] or 'exit ' + str(command['exit'])}"
        for command in checks.get("commands", [])
    ]
    cause = task.record.get("investigation")
    if cause and cause.get("type") == "fix":
        where = f" ({cause['where']})" if cause.get("where") else ""
        out.append(
            f"- the cause, as the investigation found it: {cause['line']}{where}"
        )
    lowered = (checks.get("bar") or {}).get("lowered", [])
    out.append(
        "- the bar: no mark of a lowered bar found"
        if not lowered
        else "- the bar is lowered: "
        + "; ".join(f"`{entry['file']}` ({entry['what']})" for entry in lowered)
    )
    out += edited_line(checks.get("bar") or {})
    for read in kept.get("reads", []):
        if read.get("of") == "resolution":
            out.append(resolution_line(read))
            continue
        who = (
            f"answered: {', '.join(read['answered'])}"
            if read["answered"]
            else "no source answered"
        )
        said = (
            (
                f"{read['verdict']}, {read['must_fix']} must-fix, {read['should']} "
                f"should, {read['nit']} nit"
            )
            if read["answered"]
            else "not reviewed"
        )
        said += outside_words(read, fixed)
        out.append(
            f"- the review, round {read['round']} ({KIND_SAYS[read['kind']]}; "
            f"{who}): {said}"
        )
    # each seat that stood in for another, a fact of the request and no reason of
    # not green
    out += stand_in_lines(task)
    out.append(careful_line(task, state))
    decisions = [
        *breaker_lines(task),
        *(decided(decision) for decision in task.decisions()),
    ]
    if decisions:
        out += ["", "## Decisions", "", *decisions]
    # the notes but for the four headings, which come at the end with the record's lines
    rest = no_media(
        "\n".join(
            [
                *head,
                *(
                    line
                    for heading, lines in parts
                    if heading not in own
                    for line in (heading, *lines)
                ),
            ]
        )
    ).strip()
    filed, not_worth, seen = outside_parts(
        kept.get("reads", []), fixed, builder_filed(task)
    )
    filed, not_worth = placed(
        own.get(FILED, []), own.get(NOT_WORTH, []), filed, not_worth
    )
    not_worth = jev_marked(not_worth, jev or {"items": {}, "lines": {}})
    ends = [
        (FILED, filed),
        (NOT_WORTH, not_worth),
        (FIXED, own.get(FIXED, [])),
        (SEEN, [*own.get(SEEN, []), *seen]),
    ]
    tail = "".join(
        f"\n\n{heading}\n\n" + "\n".join(lines) for heading, lines in ends if lines
    )
    return (
        "\n".join(out)
        + ("\n\n" + rest if rest and rest.lower() != "none" else "")
        + tail
        + "\n"
    )


def pr_text(  # noqa: C901, PLR0915 - over the limit before the limit was set
    task: Task, notes: str, state: dict, jev: dict | None = None
) -> str:
    """The text of the pull request, in the order the owner reads it. JEV is the end of
    each line of a finding called under the bar, what Jev said of it (`jev_read`)."""
    jev = jev or {"items": {}, "lines": {}}
    if criteria_of(task)["small"]:
        return small_text(task, jev_notes(notes, small=True, endings=jev), state, jev)
    kept = task.kept()
    # the notes' lines of the cheap defects a builder fixed, each a review's entry by
    # its number
    fixed = section(notes, FIXED)
    checks = kept.get("checks") or {}
    found = criteria_of(task)
    ask = (
        (task.directory / "ask.txt").read_text(encoding="utf-8").strip()
        if (task.directory / "ask.txt").is_file()
        else ""
    )
    held = {
        (test["criterion"], test["command"]): test
        for test in checked_criteria(checks)["tests"]
    }
    out = head_lines(task, state)
    out += [
        "## The request",
        "",
        *(
            f"> {line}"
            for line in (
                ask or "(the owner's words were not kept for this task)"
            ).splitlines()
        ),
        "",
    ]
    out += issue_line(task)
    out += [
        "## Acceptance criteria",
        "",
        f"The {TRACKS.get(found['size'], found['size'])} track, because {found['why']}",
        "",
    ]
    out += criteria_lines(found, held)
    if found["history"]:
        out += [
            "",
            "Criteria that changed during the build, in the order of the record:",
            "",
        ]
        out += [change_line(task, change) for change in found["history"]]
    out += ["", "## Checks", ""]
    for command in checks.get("commands", []):
        code = command["exit"]
        out.append(
            f"- check, `{command['command']}`"
            f"{' (serial, under the lock)' if command.get('serial') else ''}: "
            f"{command['last'] or f'exit {code}'}"
        )
    out.append(criteria_check_line(checked_criteria(checks)))
    out.append(polished(cast("dict", kept.get("polish"))))
    read = criteria_read_of(task)
    out.append(
        read_line(
            read,
            found,
            unanswered(task),
            read_skipped(task)[0] if read is None else None,
            criteria_waited(events_of(task)),
            changed_after_read(events_of(task)),
        )
    )
    if changed := unread(read, found):
        out.append(changed)
    if (task.directory / "scout.md").is_file():
        # no path: the pull request is read on the forge, where a file of this machine
        # leads nowhere
        out.append(
            "- the criteria were written from the scout's facts of the code, "
            "read during the interview"
        )
    cause = task.record.get("investigation")
    if cause and cause.get("type") == "fix":
        # a task on the standard track that came from a bug names the cause its
        # investigation found
        where = f" ({cause['where']})" if cause.get("where") else ""
        out.append(
            "- the cause, as the investigation before the build "
            f"found it: {cause['line']}{where}"
        )
    lowered = (checks.get("bar") or {}).get("lowered", [])
    out.append(
        "- the bar: no mark of a lowered bar found"
        if not lowered
        else "- the bar is lowered, with these reasons:"
    )
    out += [
        f"  - `{entry['file']}` ({entry['what']}): {entry['reason']}"
        for entry in lowered
    ]
    out += edited_line(checks.get("bar") or {})
    if (checks.get("bar") or {}).get("not_covered"):
        out.append(
            "- the bar has no marks of its own for files of these kinds: "
            f"{', '.join(checks['bar']['not_covered'])}"
        )
    size = checks.get("size") or {}
    out.append(
        f"- size: {size.get('files', '?')} files, "
        f"{size.get('lines', '?')} changed lines"
    )
    for read in kept.get("reads", []):
        if read.get("of") == "resolution":
            out.append(resolution_line(read))
            continue
        who = (
            f"answered: {', '.join(read['answered'])}"
            if read["answered"]
            else "no source answered"
        )
        quiet = "".join(
            f"; no answer from {source['name']} ({source['why']})"
            for source in read["silent"]
        )
        found = (
            (
                f"{read['verdict']}, {read['must_fix']} must-fix, {read['should']} "
                f"should, {read['nit']} nit"
            )
            if read["answered"]
            else "not reviewed"
        )
        found += outside_words(read, fixed)
        out.append(
            f"- the review, round {read['round']} ({KIND_SAYS[read['kind']]}; "
            f"{who}{quiet}): {found}"
        )
        out += [
            f"  - ran {profile['name']}: {profile['why']}" for profile in read["ran"]
        ]
        out += [
            f"  - left out {profile['name']}: {profile['why']}"
            for profile in read["left_out"]
        ]
    if talk_due(task, state):
        # propose refuses a request whose plan called for a talk with none on record, so
        # there is one here
        out.append(talked(cast("dict", talk_of(task))))
    elif no_talk := untalked(task, state):
        # careful after its plan: the full set ran and a person merges, so this is no
        # cause of not green
        out.append(no_talk)
    # each seat that stood in for another, a fact of the request and no reason of
    # not green
    out += stand_in_lines(task)
    out.append(careful_line(task, state))
    out += [
        "",
        "## Decisions of the build",
        "",
        *(
            [
                *breaker_lines(task),
                *(decided(decision) for decision in task.decisions()),
            ]
            or ["none"]
        ),
    ]
    out += folded_stories(task)
    notes = jev_notes(
        with_outside(
            notes, *outside_parts(kept.get("reads", []), fixed, builder_filed(task))
        ),
        small=False,
        endings=jev,
    )
    return "\n".join(out) + "\n\n" + no_media(notes).strip() + "\n"


# A picture of a task's `media/` folder, linked from a document: the task directory is
# in no commit, so the pull request names the picture and links nothing.
MEDIA = re.compile(
    r"(!?)\[([^\]]*)\]\(\s*(?:[^)\s]*/)?media/([^)\s]+)(?:\s+\"[^\"]*\")?\s*\)"
)


def no_media(text: str) -> str:
    """The text with each link to a file of `media/` replaced by its caption: the forge
    has no such file."""
    return MEDIA.sub(
        lambda found: (
            f"{found.group(2) or found.group(3)} (a picture on the task's board)"
        ),
        text,
    )


def folded_stories(task: Task) -> list[str]:
    """The story and the chart of each important decision that has one, folded under the
    list of the pull request, which the forge draws; nothing for a task with none, so
    its text stays as short."""
    out = []
    for decision in task.decisions():
        if not important(decision) or not (
            decision.get("case") or decision.get("chart")
        ):
            continue
        out += [
            "",
            (
                f"<details><summary>Decision {decision['id']}, its story: "
                f"{one_line(decision['what'])}</summary>"
            ),
            "",
        ]
        out += story_lines(decision)
        out += chart_lines(decision)
        out += ["</details>"]
    return out


# The longest text of a decision's summary in the pull request, in characters: one line
# at the width of a laptop's window. A guess, not a measurement.
CELL = 80


def one_line(text: str, most: int = CELL) -> str:
    """A text in one line of at most MOST characters, cut at a word, with an ellipsis
    when cut."""
    flat = " ".join(text.split())
    if len(flat) <= most:
        return flat
    return flat[:most].rsplit(" ", 1)[0].rstrip(",;:.") + "…"


def label(option: str) -> str:
    """An option's label: its text before the first colon, as
    `lem decisions log --option` asks an option to be written ("LABEL: what the person
    sees after it"), or the whole option in one line."""
    head, colon, _ = option.partition(":")
    # a colon inside a quote is no end of a label: "the say 'the checks refused: ...'"
    opened = len(re.findall(r"(?:^|\s)['\"]", head)) > len(
        re.findall(r"\w['\"](?:\s|$|[.,;])", head)
    )
    labelled = colon and head.strip() and len(head) <= CELL and not opened
    return one_line(head if labelled else option)


def important(decision: dict) -> bool:
    """Whether a decision is important, the ones whose story `stages/ladder.md` asks
    for: one the request is not green for (past the personas, or unsettled), or the
    owner's help on a breaker."""
    return without_him(decision) or (
        decision["by"] == "owner" and "breaker" in decision
    )


def story_lines(decision: dict[str, Any]) -> list[str]:
    """The story of a decision as its record keeps it: the case in its numbered steps,
    how it is known, and the cause. Nothing when the record has no case."""
    if not decision.get("case"):
        return []
    known = {
        "reproduced": "reproduced",
        "derived": "derived from the code, not run",
    }.get(decision.get("case_was", ""), decision.get("case_was"))
    out = [
        f"**The case**{f' ({known})' if known else ''}:",
        "",
        *decision["case"].splitlines(),
        "",
    ]
    if decision.get("cause"):
        out += [f"**Why it could happen:** {decision['cause']}", ""]
    return out


def chart_lines(decision: dict) -> list[str]:
    """A decision's chart as a fenced mermaid block, which the board and the
    forge draw."""
    return (
        ["```mermaid", *decision["chart"].splitlines(), "```", ""]
        if decision.get("chart")
        else []
    )


def gh(task: Task, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return gh_in(
        task.worktree if task.worktree.exists() else task.main, *args, check=check
    )


def gh_in(where: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    """One command of the forge's `gh`, run in a checkout of the repository, which tells
    it the repository."""
    if not shutil.which("gh"):
        raise LandError(
            "the remote is GitHub and the `gh` command is not on PATH: "
            "install it and sign in, then run this again"
        )
    ran = subprocess.run(
        ["gh", *args],
        cwd=where,
        capture_output=True,
        text=True,
        check=False,
        stdin=subprocess.DEVNULL,
    )
    if check and ran.returncode != 0:
        raise LandError(
            f"gh {' '.join(args[:2])} failed: {(ran.stderr or ran.stdout).strip()}"
        )
    return ran


def not_github(task: Task) -> str:
    """The refusal of a step that needs the pull request, where origin is not
    on GitHub."""
    return (
        f"origin of {task.main} is not a repository on GitHub, or there is none: "
        "a task ends as a GitHub pull request, the one way Lem lands. Point origin at "
        f"the repository on GitHub (`git -C {task.main} remote add origin "
        "git@github.com:OWNER/REPO.git`, or `remote set-url` for one that is there), "
        f"push {task.base} there, then run this step again"
    )


def protected_refusal(branch: str, settings: dict, does: str) -> str | None:
    """Why Lem may not push to the branch named BRANCH (DOES `pushes`) or delete it
    (`deletes`), by the settings' `[branch]` as they are now: the base branch, or a name
    in `branch.protected`, which the owner may add after the task's worktree was made.
    None for a branch of the task's own."""
    what = "to" if does == "pushes" else "of"
    if branch == settings["base"]:
        return (
            f"{branch} is the base branch of .lem/settings.toml: Lem {does} nothing "
            f"{what} it outside a merge through its pull request"
        )
    if branch in settings["protected"]:
        return (
            f"{branch} is in branch.protected of .lem/settings.toml: "
            f"Lem {does} nothing {what} it"
        )
    return None


def cmd_propose(task: Task, title: str, notes_file: str) -> dict:  # noqa: C901, PLR0912, PLR0915 - over the limit before the limit was set
    task.need_landing()
    task.need_worktree()
    if task.forge != "github":
        raise LandError(not_github(task))
    tip = git(task.worktree, "rev-parse", "HEAD")
    # A task started from a backlog item did that item's work, so it lands with the item
    # gone: the merge takes it off the base and off the board. Asked before the checks'
    # result: the removal asks for a run of the checks, since a command of the project
    # may read the file.
    own = task_item(task)
    if own and in_tree(task, tip, own):
        raise LandError(
            f"{task.slug} was started from the backlog item {own} (its ask is that "
            "path), and the branch still holds it: the task does that item's work, so "
            "its branch removes it. A builder of the landing removes it in a commit of "
            f"its own (`git -C {task.worktree} rm -q -- {own}`, then `git -C "
            f"{task.worktree} commit -m MESSAGE -- {own}` in the project's message "
            f"form), then `lem land checks {task.slug}` and this step run again; "
            "the review that read the change still covers it",
        )
    missing = gate_missing(task, tip)
    if missing:
        raise LandError(f"{missing}; `lem land checks {task.slug}` comes first")
    kept = task.kept()
    reads = kept.get("reads", [])
    unfiled = to_file(
        reads,
        lambda path: in_tree(task, tip, path),
        lambda path: worth_at(task, tip, path) == "no",
    )
    state = due(task)
    if state["due"] == "review":
        raise LandError(
            f"a review is due before anything is proposed, {KIND_SAYS[state['floor']]} "
            f"at the least ({state['why']}); `lem land read {task.slug}` "
            "says what a reviewer gets"
        )
    # A careful or large plan is talked through by its defender and the reviewer, in the
    # plan talk's companion, before any code. The talk leaves one event, and a request
    # without it skipped that step.
    needs_talk = talk_due(task, state)
    talk = talk_of(task) if needs_talk else None
    if needs_talk and talk is None:
        raise LandError(
            f"{needs_talk}, so its defender and the reviewer talk its plan through in "
            "the plan talk's companion before any code (`stages/talk.md`), and the "
            f"event log has no `plan.talk` of {task.slug}. The defender writes it "
            f"after the talk: `lem project log {task.slug} plan.talk {TALK_FORM}`; "
            "for a plan that had no talk, the task's lead opens the talk first, "
            "as `stages/talk.md` says",
        )
    if talk is not None and not (
        isinstance(talk.get("reviewer"), str)
        and talk["reviewer"].strip()
        and all(
            isinstance(talk.get(key), int) and not isinstance(talk.get(key), bool)
            for key in ("turns", "settled", "open")
        )
    ):
        raise LandError(
            f"the newest `plan.talk` of {task.slug} does not have the form "
            f"`{TALK_FORM}`; its defender writes it again with `lem project log`"
        )
    read = criteria_read_of(task)
    if read is not None and not read_form(read):
        raise LandError(
            f"the newest `criteria.read` of {task.slug} does not have the form "
            f"{READ_FORM}; whoever ran the read writes it again with `lem project log`"
        )
    # The personas read the criteria of a task on the standard track before the build,
    # and a doubt of theirs reaches him: a request is not proposed over criteria nobody
    # read, or over a doubt he never saw.
    found = criteria_of(task)
    if read is None and not found["small"]:
        # his word to skip the read, with his approval after it and both before any lead
        # started, is the one way past it
        skipped, why_not = read_skipped(task)
        if why_not:
            raise LandError(why_not)
        if skipped is None:
            raise LandError(
                f"{task.slug} takes the standard track, and the event log has no "
                "`criteria.read`: the personas read its criteria before the build "
                "(`stages/interview.md`, step 5; for the standard track from a "
                "complete request `stages/plan.md`, step 1), and whoever ran the read "
                f"writes `lem project log {task.slug} criteria.read` with the form "
                f"{READ_FORM}. Only the owner skips a read, at the interview and when "
                "every criterion names only the developer: Lem writes the owner's word "
                f"with {read_skip_form(task.slug)}, and the owner approves the "
                "criteria after it, both before a lead starts",
            )
    if read is not None and not read["answered"] and unanswered(task) < SILENT_READS:
        raise LandError(
            f"nobody answered the newest read of {task.slug}'s criteria: "
            "it is started once more, and its record written again with "
            f"`lem project log {task.slug} criteria.read` (`stages/interview.md`, step "
            "5; for the standard track from a complete request `stages/plan.md`, step "
            "1). After a second read in a row that nobody answered, "
            "the request is proposed as not green",
        )
    # Without the owner, an approval made then lets the request go on, and it is not
    # green for it.
    if (
        read is not None
        and (read["flagged"] or read["split"])
        and not approved_after(found, read)
        and not approved_alone(found, read)
    ):
        doubt = (
            (
                f"{read['flagged']} flagged "
                f"{'criterion' if read['flagged'] == 1 else 'criteria'}"
            )
            if read["flagged"]
            else "a split between the two families"
        )
        raise LandError(
            f"the newest read of {task.slug}'s criteria found {doubt}, and no approval "
            "of the owner's came after it: the criteria with the personas' answers on "
            "top go to the owner (`stages/interview.md`, step 6), and the owner's yes "
            f"is kept with `lem criteria approve {task.slug} --file FILE`",
        )
    # A request that had an interview ends it with his yes, whatever the read found: a
    # step that skipped it, and a lead that then froze the criteria as a complete
    # request's, do not make it his.
    if interview_unapproved(
        events_of(task), found.get("approvals", []), small=found["small"]
    ):
        raise LandError(
            f"{task.slug} had an interview (`interview.start` in the event log), and "
            "its criteria carry no approval of the owner's: the interview ends with "
            f"his yes, kept with `lem criteria approve {task.slug} --file FILE` "
            "(`stages/interview.md`, steps 6 and 7), or, while the task runs without "
            "him, with `--alone` (`stages/away.md`). The criteria with the personas' "
            "answers go to the owner",
        )
    # A complete request that someone else wrote: nobody at the terminal read it, so its
    # criteria wait for his yes even when nobody was confused, and the lead's freeze of
    # the read is not that yes.
    if (
        read is not None
        and not approved_after(found, read)
        and not approved_alone(found, read)
        and someone_elses(task)
    ):
        raise LandError(
            f"{task.slug} is a complete request that someone else wrote, and no "
            "approval of the owner's came after the newest read of its criteria: "
            "nobody at the terminal read that request, so its criteria wait for his "
            "yes even when nobody was confused, and a freeze by the read is not his "
            "yes (`stages/plan.md`, step 1). The criteria with the personas' answers "
            "go to the owner, and his yes is kept with "
            f"`lem criteria approve {task.slug} --file FILE`",
        )
    # Each defect a review saw outside the change and called over or under the bar has
    # its item in the tip, or the open item it names is there, so that none is lost and
    # none is raised again: one that a session never filed, and one whose item a later
    # commit took out. The cheap ones are lines of the text, from the record.
    if unfiled:
        raise LandError(
            (
                f"{len(unfiled)} defect(s) a review saw outside the change and called "
                "over or under the bar have no item in the backlog: "
            )
            + "; ".join(
                f'"{defect["title"]}" ({defect["number"]}, round {defect["round"]})'
                for defect in unfiled
            )
            + f". `lem land file {task.slug}` files them, then this step runs again",
        )
    gone = [
        (read, defect)
        for read in reads
        if read["answered"]
        for defect in outside_of(read)
        if defect.get("item") and not in_tree(task, tip, defect["item"])
    ]
    if gone:
        read, defect = gone[0]
        raise LandError(
            (
                f'the item {defect["item"]} of the defect "{defect["title"]}" (review '
                f"round {read['round']}) was removed after it was filed"
            )
            + (f", and {len(gone) - 1} more" if len(gone) > 1 else "")
            + (
                f": a builder puts it back with `lem land file {task.slug} --again`, "
                "then this step runs again; when the owner does not want it, the item "
                "stays with `worth: no` and the owner's reason in it, never deleted"
            ),
        )
    # A request is never proposed over a breaker that stopped its build and that the
    # owner did not help on.
    waiting = next(
        (breaker for breaker in task.breakers() if breaker["state"] == "waits"), None
    )
    if waiting:
        raise LandError(
            f"breaker {waiting['id']} of {task.slug} waits for the owner "
            f"({waiting['what']}): its build stopped there, and a request is never "
            "proposed over it. The owner reads its document and helps (`lem decisions "
            f"log {task.slug} --by owner --breaker {waiting['id']} ...`), "
            "parks the task or drops it",
        )
    notes = (
        Path(notes_file).read_text(encoding="utf-8")
        if Path(notes_file).is_file()
        else None
    )
    if notes is None:
        raise LandError(
            f"{notes_file} is not a file; --notes names the notes of the pull request"
        )
    # The fast track's notes are what the review left open, in a few lines, or `none`:
    # it has no plan to decide from, no polish pass to file from, and nothing it set out
    # of scope.
    wanted = [
        *([] if criteria_of(task)["small"] else NOTES),
        *(["## Migration"] if state["careful"] else []),
    ]
    missing = [
        heading
        for heading in wanted
        if not re.search(rf"(?m)^{re.escape(heading)}\s*$", notes)
    ]
    if missing:
        raise LandError(
            f"the notes lack {', '.join(missing)}: they hold {', '.join(wanted)}, each "
            "with what is true of this task or the one word `none`"
        )
    # A finding nobody filed reaches the pull request only with a bar call and its
    # reason, or as an item the tip holds, whoever wrote its line: a line with neither
    # is a defect the next review raises again, or one over the bar that nobody judged.
    bare = unfiled_lines(
        notes,
        small=criteria_of(task)["small"],
        folder=backlog_of(task),
        in_tip=lambda path: file_at(task, tip, path),
    )
    if bare:
        raise LandError(
            (
                f"{len(bare)} line(s) of the notes name a finding with no "
                "bar call and no item: "
            )
            + "; ".join(f'"{line}"' for line in bare)
            + (
                ". Give it a bar call and a reason, or file it: by the bar of rule 6 "
                "of the builder's standing rules, the line ends with `under: REASON` "
                "or `cheap: REASON`, or a builder files it as an item of "
                f"{backlog_of(task)} and the line names the item's path; "
                "then this step runs again"
            ),
        )
    if not title.strip() or "\n" in title:
        raise LandError("--title is one line: the subject of the change")
    # Jev reads each finding called under the bar once, the tip's items and the notes'
    # lines alike, and a read over the bar stops the step one time, so that the agent
    # looks again.
    endings = jev_read(task, notes, small=criteria_of(task)["small"])
    reasons = not_green(task, state)
    # The one rule of a moved base runs before the text is written: the text, the
    # `proposed` event and what is carried after the push all say what this one
    # result gives.
    carry = moved_carry(kept, tip, state["careful"], reasons)
    if kept.get("sync"):
        task.keep(
            sync={
                **task.kept()["sync"],
                "carry": {
                    key: carry[key]
                    for key in ("how", "why", "review", "merge_review", "merge_why")
                },
            }
        )
    body = task.directory / "pr.md"
    write_whole(body, pr_text(task, notes, state, endings))
    says = "green" if not reasons else f"not green: {'; '.join(reasons)}"
    branch = git(task.worktree, "branch", "--show-current")
    # the name the push goes to, by the settings as they are now: the owner may protect
    # it after the worktree was made
    protected = protected_refusal(branch, task.settings["branch"], "pushes")
    if protected:
        raise LandError(
            f"{protected}, and the task's branch has that name; nothing was pushed. "
            "The owner takes the name out of branch.protected, or, while the task has "
            "no pull request, a builder gives the task a branch of its own "
            f"(`git -C {task.worktree} branch -m NEW-NAME`); then this step runs again",
        )
    pr = kept.get("pr")
    # What origin's copy of the branch holds may be replaced only when it is Lem's push
    # or the branch holds it: the lease names that commit, or no branch at all for a
    # first push.
    lease = task.own_remote(branch)
    if not pr:
        # A run that was cut off after the forge made the pull request wrote none down:
        # the forge knows it. Only a pull request whose head is the commit Lem pushed
        # for this task is its own; any other on the same branch name is somebody's, and
        # is not taken.
        there = json.loads(
            gh(
                task,
                "pr",
                "list",
                "--head",
                branch,
                "--base",
                str(task.base),
                "--state",
                "open",
                "--json",
                "number,url,headRefOid,author",
            ).stdout
        )
        pushed = task.kept().get("pushed")
        mine = [
            found for found in there if pushed and found.get("headRefOid") == pushed
        ]
        others = [found for found in there if found not in mine]
        if others:
            other = others[0]
            raise LandError(
                f"pull request #{other['number']} by "
                f"{(other.get('author') or {}).get('login') or 'someone'} is open on "
                f"{branch}, and its head is no commit Lem pushed for this task: "
                "it is somebody else's, and Lem does not push over it or rewrite its "
                "text. Give the task a branch of its own "
                f"(`git -C {task.worktree} branch -m NEW-NAME`), "
                "then run this step again",
            )
        pr = {"number": mine[0]["number"], "url": mine[0]["url"]} if mine else None
    elif (state_now := viewed(task, pr)["state"]) != "OPEN":
        raise LandError(
            (
                f"the pull request {pr['url']} is {state_now.lower()}: "
                f"`lem land merged {task.slug}` "
            )
            + (
                "finishes the task"
                if state_now == "MERGED"
                else "writes the task dropped, and its branch keeps its commits"
            ),
        )
    # With the lease of the one commit the push may replace: a commit that came in
    # between stops it.
    git(
        task.worktree,
        "push",
        f"--force-with-lease=refs/heads/{branch}:{lease}",
        "origin",
        f"HEAD:refs/heads/{branch}",
    )
    # kept before the forge's step, so that a run cut off after it knows the push as
    # its own
    task.keep(pushed=tip)
    if pr:
        gh(
            task,
            "pr",
            "edit",
            str(pr["number"]),
            "--title",
            title,
            "--body-file",
            str(body),
        )
    else:
        url = (
            gh(
                task,
                "pr",
                "create",
                "--base",
                str(task.base),
                "--head",
                branch,
                "--title",
                title,
                "--body-file",
                str(body),
            )
            .stdout.strip()
            .splitlines()[-1]
        )
        number = url.rstrip("/").rsplit("/", 1)[-1]
        if not number.isdigit():
            raise LandError(f"gh pr create printed no pull request address: {url!r}")
        pr = {"number": int(number), "url": url}
    # The events come after the forge's step: a proposal that the forge or the push
    # refused is none. for the retro: how often a request is not green, and for which
    # reason and, for a landing that started from `open`, what carried over the moved
    # base: the review, the merge review (`carried`, or `fresh` with `why`) and the
    # owner's merge
    carried_facts = []
    if kept.get("sync"):
        carried_facts = [
            *([f"review={carry['review']}"] if carry["review"] else []),
            f"merge_review={'carried' if carry['merge_review'] else 'fresh'}",
            *([f"why={carry['merge_why']}"] if carry["merge_why"] else []),
            *([f"owner_merge={carry['owner_merge']}"] if carry["owner_merge"] else []),
            *([f"owner_why={carry['owner_why']}"] if carry["owner_why"] else []),
        ]
    script(
        "project.py",
        task.worktree,
        "log",
        task.slug,
        "proposed",
        f"green:={json.dumps(not reasons)}",
        f"not_green:={json.dumps(reasons)}",
        f"tip={tip[:9]}",
        *carried_facts,
    )
    moved = synced(task)
    task.keep(pr=pr, proposed=tip, title=title, not_green=reasons)
    carried = carry_merge(task, kept, tip, state, reasons, carry)
    task.state("open", f"pull request {pr['url']}", says, *([moved] if moved else []))
    return {
        "task": task.slug,
        "text": str(body),
        "pull_request": pr,
        "green": not reasons,
        "not_green": reasons,
        "branch": branch,
        "tip": tip,
        "synced": moved,
        **carried,
    }


def carry_merge(  # noqa: PLR0913, PLR0917 - over the limit before the limit was set
    task: Task, kept: dict, tip: str, state: dict, reasons: list[str], carry: dict
) -> dict:
    """After a proposal, what was said of the tip proposed before (KEPT, the record
    before this proposal) at its merge, carried onto TIP as the rule of a moved base
    says (CARRY, `moved_carry`): the merge agent's review, with whether it calls the
    owner as the rules say now and with no call on a moved base (`carried_review`),
    logged again as a `merge.review` of TIP with `carried`; and the owner's merge that a
    moved base refused, which stands (`merge.stands`) or ends with the rule's reason
    (`merge.ended`). What it gives the output: `merge_review` (carried or null),
    `merge_review_why` (why a fresh merge agent reads the task, after a moved base) and
    `owner_merge` (`stands`, the reason it ended, or null)."""
    old = kept.get("proposed")
    out: dict = {
        "merge_review": None,
        "merge_review_why": carry["merge_why"],
        "owner_merge": None,
    }
    if carry["merge_review"]:
        review = kept["merge_review"]
        refusal = merger_refusal(
            task.slug,
            task.settings["branch"]["land"],
            state["careful"],
            reasons,
            called=review_call(task) is not None,
            review={"verdict": "merge"},
        )
        calls = review.get("verdict") == "call" or refusal is not None
        why = refusal or (
            review.get("why") if review.get("verdict") == "call" else None
        )
        review = carried_review(review, tip, calls=calls, why=why, old=old)
        task.keep(merge_review=review)
        script(
            "project.py",
            task.main,
            "log",
            task.slug,
            "merge.review",
            f"verdict={review['verdict']}",
            f"calls:={json.dumps(calls)}",
            f"by={review.get('by')}",
            f"tip={tip[:9]}",
            f"carried={str(old)[:9]}",
            *([f"why={why}"] if why else []),
        )
        out["merge_review"] = "carried"
    if carry["owner_merge"] == "stands":
        task.keep(owner_tap=carry["tap"])
        script(
            "project.py",
            task.main,
            "log",
            task.slug,
            "merge.stands",
            "by=owner",
            f"tip={tip[:9]}",
            f"from={str(old)[:9]}",
        )
        out["owner_merge"] = (
            "stands: the board's server merges it after the checks and the "
            "reviews were checked again"
        )
    elif carry["owner_merge"] == "ended":
        task.keep(owner_tap=None)
        # the end is a fact of the log, which the board shows, and not only a line a
        # session may never say
        script(
            "project.py",
            task.main,
            "log",
            task.slug,
            "merge.ended",
            "by=owner",
            f"tip={tip[:9]}",
            f"from={str(old)[:9]}",
            f"why={carry['owner_why']}",
        )
        out["owner_merge"] = f"ended: {carry['owner_why']}; the owner merges it again"
    return out


def follow(task: Task) -> str | None:
    """After the remote's base moved: the checkout that holds the base follows, or the
    reason it did not."""
    if not (task.remote and task.base_checkout is not None):
        return None
    # The checkout that holds the base follows, so the next task's worktree starts from
    # what just landed. git refuses the fast-forward, and changes nothing, when a file
    # with changes of its own is in the way or the checkout has commits the remote
    # lacks; then it stays as it is.
    followed = run(
        [
            "git",
            "-C",
            str(task.base_checkout),
            "merge",
            "--ff-only",
            f"origin/{task.base}",
        ],
        check=False,
    )
    if followed.returncode == 0:
        return None
    why = [
        line
        for line in (followed.stderr or followed.stdout).strip().splitlines()
        if line.strip()
    ]
    return (
        f"{task.base_checkout} did not follow origin/{task.base}, and nothing in it "
        f"was changed. git said: {why[-1] if why else 'nothing'}"
    )


def merger_refusal(  # noqa: PLR0911, PLR0913 - over the limit before the limit was set
    slug: str,
    land: str,
    careful: list[str],
    reasons: list[str],
    *,
    called: bool,
    review: dict | None,
) -> str | None:
    """Why the merge agent may not merge a request, or None when it may. The facts: the
    settings' `branch.land`, why the request is careful (none when it is not), why it is
    not green (none when it is), whether the newest review that answered made the
    careful call, and the merge agent's review of the proposed tip (its `verdict`), or
    None. The owner's merge asks none of this; a task that ran without him is merged as
    any other."""
    if land != "agent":
        return (
            'branch.land is "owner" in .lem/settings.toml: the owner merges every '
            "task, after the merge review; it waits as `open` for his word"
        )
    if careful:
        return (
            "a careful request is merged by the owner, whatever the settings say "
            f"({careful[0]}); it waits as `open` for his word"
        )
    if reasons:
        return (
            f"the request is not green ({'; '.join(reasons)}), so the owner merges it; "
            "it waits as `open` for his word"
        )
    # The merge agent merges only on the newest review's "not careful": a record with no
    # call is no such word.
    if not called:
        return (
            "no review that answered made the careful call for this change, so the "
            "owner merges it; it waits as `open` for his word"
        )
    if review is None:
        return (
            "no merge review of the proposed tip is on record: the merge agent reads "
            f"the task first, and `lem land merge-review {slug} --file FILE --tip TIP "
            "--base BASE` writes its review down"
        )
    if review.get("verdict") != "merge":
        return (
            "the merge review calls the owner: he reads it, "
            "and it waits as `open` for his word"
        )
    return None


def kept_refusal(by: str, kind: str | None) -> bool:
    """Whether a refused merge is kept for its tip, so that the server tries that tip no
    more and wakes the task's session: every refusal of the merge agent's merge by Lem's
    rules, and the owner's when the base moved, which the session answers with a fresh
    merge agent's read of what moved, or with a new landing after a read that said
    another round. A git or `gh` call that failed (no kind) is never kept: the next try
    runs it again."""
    return kind in REFUSALS and (by == "merger" or kind == "base")


def tip_carry(  # noqa: C901, PLR0911, PLR0912 - over the limit before the limit was set
    kept: dict, new: str, why_careful: list[str]
) -> tuple[str | None, str | None]:
    """Whether what was said of the proposed tip at its merge holds for the tip NEW
    proposed now, from the record before this proposal (KEPT: `proposed`,
    `rebase_carried`, `resolution`, `reads`, `rebase_uncovered`) and each reason the
    request is careful now. It gives how the tip carries (`same`, `rebase` for a rebase
    with no conflict that kept the code review, `resolution` for a builder's resolution
    whose one read found nothing) and None, or None and why it does not; (None, None)
    for a first proposal. A careful request never carries over a resolved conflict: a
    reason of careful now, or the careful call of the newest round of the change, which
    the read of the resolution does not take back (careful in doubt), though who merges
    still follows the newest call (`review_call`)."""
    old, rebased, uncovered = (
        kept.get("proposed"),
        kept.get("rebase_carried"),
        kept.get("rebase_uncovered"),
    )
    if not old:
        return None, None
    if old == new:
        return "same", None
    if rebased == {"from": old, "to": new}:
        return "rebase", None
    resolution = kept.get("resolution")
    uncovers = (
        bool(uncovered) and uncovered.get("from") == old and uncovered.get("to") == new
    )
    if not (resolution and resolution.get("before") == old):
        if uncovers and uncovered:
            return None, f"no review covers the change: {uncovered['why']}"
        if (rebased or uncovered or {}).get("from") == old:
            return None, "a commit came after the rebase"
        return None, "a commit came after the tip proposed before"
    met = "the rebase met a conflict, and"
    if uncovers and uncovered:
        return None, f"{met} no review covers the change: {uncovered['why']}"
    reads = kept.get("reads", [])
    read = resolution_read(kept)
    if (
        read
        and read["answered"]
        and (read["must_fix"] or read["should"] or read["nit"])
    ):
        return (
            None,
            (
                f"{met} the read of its resolution found {read['must_fix']} must-fix, "
                f"{read['should']} should and {read['nit']} nit"
            ),
        )
    if any(
        (one or {}).get("from") == resolution.get("after")
        and (one or {}).get("to") == new
        for one in (rebased, uncovered)
    ):
        return None, f"{met} the base moved again after its resolution"
    if resolution.get("after") != new:
        return None, f"{met} a commit came after its resolution"
    if not (read and read["answered"]):
        silent = any(
            one.get("of") == "resolution"
            and not one["answered"]
            and one.get("tip") == new[:9]
            for one in reads
        )
        return (
            None,
            (
                f"{met} the read of its resolution "
                f"{'did not answer' if silent else 'did not run'}"
            ),
        )
    rounds = [one for one in reads if one["answered"] and one.get("of") != "resolution"]
    if why_careful:
        return None, f"{met} the request is careful: {why_careful[0]}"
    if rounds and rounds[-1].get("careful"):
        careful_said = rounds[-1].get("careful_why") or "a round called it careful"
        return (
            None,
            f"{met} the request is careful: the review says so: {reason(careful_said)}",
        )
    return "resolution", None


def filed_on(kept: dict, before: str, after: str) -> dict:
    """The records of a moved base that name BEFORE as the tip a builder's resolution or
    a rebase made (`resolution.after`, `rebase_carried.to`, `rebase_uncovered.to`),
    moved to AFTER, from the record KEPT: `file`'s commits from BEFORE to AFTER only add
    the backlog items of the reviews' defects outside the change, which ask for no
    review and no check again (`covers_one`, `gate_holds`), so what was said of BEFORE
    holds for AFTER (`tip_carry`). Empty when nothing names BEFORE."""
    if before == after:
        return {}
    moved: dict = {}
    resolution = kept.get("resolution")
    if resolution and resolution.get("after") == before:
        moved["resolution"] = {**resolution, "after": after}
    for key in ("rebase_carried", "rebase_uncovered"):
        one = kept.get(key)
        if one and one.get("to") == before:
            moved[key] = {**one, "to": after}
    return moved


def resolution_read(kept: dict) -> dict | None:
    """The review of the builder's resolution that the record KEPT names
    (`resolution.read`, its attempt, among `reads`); None when no resolution is kept, or
    no read of it."""
    resolution = kept.get("resolution")
    if not resolution or resolution.get("read") is None:
        return None
    return next(
        (
            one
            for one in kept.get("reads", [])
            if one.get("attempt") == resolution["read"]
        ),
        None,
    )


def moved_carry(
    kept: dict, new: str, why_careful: list[str], reasons: list[str]
) -> dict:
    """What a proposal of the tip NEW carries of what was said of the tip proposed
    before, from the record before this proposal (KEPT), each reason the request is
    careful now and each reason it is not green now: the one rule of a moved base, which
    the pull request's text, the `proposed` event and `carry_merge` read. The tip's
    carry (`tip_carry`) comes first; then each act has its own last fact. The merge
    review carries when a merge agent's review of the proposed tip with a verdict is on
    record (`merge_review`, else `merge_why` says why a fresh merge agent reads the
    task); the owner's merge that a moved base refused (`owner_tap`) stands, with the
    new tip (`tap`), while the reasons the request is not green are the ones he saw, and
    else ends with `owner_why`. `review` is what the rebase did with the review, in the
    text's words: carried over it (`sync.carried`), or the read of the resolution that
    answered, by its kind."""
    old = kept.get("proposed")
    how, why = tip_carry(kept, new, why_careful)
    resolution = kept.get("resolution")
    read = resolution_read(kept)
    review = review_line((kept.get("sync") or {}).get("carried")) or (
        (
            "one read of the resolution"
            if read["kind"] == "read"
            else f"a read of the resolution by {KIND_SAYS[read['kind']]}"
        )
        if resolution and resolution.get("before") == old and read and read["answered"]
        else None
    )
    out: dict = {
        "how": how,
        "why": why,
        "review": review,
        "merge_review": False,
        "merge_why": None,
        "owner_merge": None,
        "owner_why": None,
        "tap": None,
    }
    if not old:
        return out
    said = kept.get("merge_review")
    # a review with no verdict (a second answer whose first line gave none, on a moved
    # base or not) has nothing to carry
    if (
        how
        and isinstance(said, dict)
        and said.get("verdict") in ("merge", "call")
        and said.get("tip") == old
    ):
        out["merge_review"] = True
    else:
        out["merge_why"] = why or "no merge review of the earlier tip was on record"
    tap = kept.get("owner_tap")
    if tap:
        if tap.get("tip") != old:
            ended = "the change is not the one the owner merged"
        elif not how:
            ended = why
        elif list(tap.get("not_green") or []) != list(reasons):
            ended = (
                "the reasons the request is not green are not the ones the "
                "owner saw when he merged it"
            )
        else:
            ended = None
        out.update(
            owner_merge="ended" if ended else "stands",
            owner_why=ended,
            tap=None if ended else {**tap, "tip": new},
        )
    return out


def merge_line(carry: dict | None) -> str | None:
    """What a new landing did with the merge review, in the words of the pull request's
    text and of the `proposed` event: carried over, with how, or a fresh merge agent's
    read with its reason. None for a first proposal."""
    if not carry:
        return None
    if carry["merge_review"]:
        return {
            "resolution": (
                "the merge review carried over the resolved conflict: "
                "the resolution read found nothing"
            ),
            "rebase": "the merge review carried over the rebase",
        }.get(carry["how"], "the merge review carried over")
    return (
        f"a fresh merge agent reads it: {carry['merge_why']}"
        if carry["merge_why"]
        else None
    )


def merge_review_of(task: Task) -> dict | None:
    """The merge agent's review of the tip that was proposed, as `merge-review` kept it;
    None for none, or for a review of an earlier tip."""
    kept = task.kept()
    review = kept.get("merge_review")
    return (
        review
        if isinstance(review, dict)
        and kept.get("proposed")
        and review.get("tip") == kept["proposed"]
        else None
    )


def may_merge(task: Task, by: str) -> None:
    """Who may merge. The owner's word is enough; the merge agent merges only what
    nobody has a reason to look at first."""
    if by == "owner":
        return
    state = due(task)
    refusal = merger_refusal(
        task.slug,
        task.settings["branch"]["land"],
        state["careful"],
        not_green(task, state),
        called=review_call(task) is not None,
        review=merge_review_of(task),
    )
    if refusal:
        raise Refusal("rule", refusal)


def base_refusal(view: dict, base: str, url: str, slug: str) -> str | None:
    """Why a pull request as GitHub shows it (VIEW, with `baseRefName`) is not the
    task's: its base on GitHub is not BASE, the settings' base branch, as after a change
    of its base there. None when it is."""
    there = view.get("baseRefName")
    if not there:
        return (
            f"GitHub's answer for the pull request {url} names no base branch, so Lem "
            f"cannot tell that it goes into {base}; nothing was merged or recorded. "
            "Run this step again"
        )
    if there == base:
        return None
    number = url.rstrip("/").rsplit("/", 1)[-1]
    if view.get("state") == "MERGED":
        return (
            f"the pull request {url} was merged into {there} on GitHub, not into "
            f"{base}, the base of the task's settings, so the task did not land, and "
            "nothing was recorded: the owner ends it with "
            f'`lem project state {slug} dropped "WHY"`, '
            f"or a new task brings the change onto {base}"
        )
    return (
        f"the pull request {url} is on {there} on GitHub, not on {base}, the base of "
        "the task's settings: its base was changed there. Nothing was merged or "
        f"recorded. Its base goes back to {base} on GitHub "
        f"(`gh pr edit {number} --base {base}`), then this step runs again"
    )


def forge_done(task: Task, view: dict) -> dict:
    """The bookkeeping of a pull request GitHub merged, the one step every path to
    `landed` takes: Lem's merge, and `lem land merged` of a merge GitHub took later or
    the owner made there. A merge on a base that moved after the checks leaves its line
    in the pull request's text first (`moved_line`), and so does each stand-in of the
    merge agent (`merger_noted`); a failed edit leaves the task as it was with this
    step's error, and the next `lem land merged` tries again. A task started from a
    reviewer's item of the state folder (`state_item`) removes the item's file the same
    way, before `landed`; a dropped task never comes here, so its item is
    undecided again."""
    pr = task.kept()["pr"]
    # a merge into another branch than the base is no landing: the task stays as it is,
    # and the owner reads why
    wrong = base_refusal(view, task.base, pr["url"], task.slug)
    if wrong:
        raise LandError(wrong)
    task.fetch()
    merged = (view.get("mergeCommit") or {}).get("oid")
    line, uncovered = moved_line(task, merged)
    if line:
        noted(
            task,
            pr,
            line,
            f"GitHub merged {pr['url']}, and the line of its merge on the moved base",
            f"the task stays open, and `lem land merged {task.slug}` tries again",
        )
    merger_noted(
        task,
        pr,
        (
            f"GitHub merged {pr['url']}; the task stays as it was, and "
            f"`lem land merged {task.slug}` tries again"
        ),
    )
    item = state_item(task)
    removed = (
        remove_item(task.state_folder, item, task.slug, pr["url"]) if item else False
    )
    # the commit of the branch that the forge merged: `clean` removes the branch only
    # when it holds nothing after it
    task.keep(merged=merged or True, merged_head=view["headRefOid"])
    left_behind = follow(task)
    task.state(
        "landed",
        f"{task.base}: pull request {pr['url']} is merged",
        *([line] if line else []),
    )
    return {
        "task": task.slug,
        "base": task.base,
        "pull_request": pr,
        "merged": merged,
        "left_behind": left_behind,
        "base_read": line,
        **({"item": {"path": item, "removed": removed}} if item else {}),
        **({"uncovered": f"{task.slug}: {line}"} if uncovered else {}),
    }


def moved_line(task: Task, merged: str | None) -> tuple[str | None, bool]:
    """The line of a merge on a base that moved after the checks, from Lem's record of
    the merge (`merged_by`): the base the checks ran on, the base the read covered and
    its why. The merged commit's parent on the base is read too: when its tree is not
    the tree the read covered (a merge on GitHub outside Lem came between Lem's fetch
    and its merge call), the line names the base it really merged on and says that no
    read covered it (True beside it). (None, False) for any other merge."""
    record = task.kept().get("merged_by") or {}
    if record.get("after") != READ_AFTER:
        return None, False
    if merged and record.get("commits"):
        parent = git(
            task.worktree,
            "rev-parse",
            f"{merged}~{int(record['commits'])}",
            check=False,
        )
        if parent and changed(task, record["base"], parent):
            return uncovered_line(
                task.base, record["checks_ran_on"], parent, record["base"]
            ), True
    return record["line"], False


def noted_body(body: str, line: str, replaces: str | None = None) -> str | None:
    """The pull request's text BODY with LINE in it once, or None when it holds LINE
    already: in the place of the line REPLACES, an earlier form of the same fact, when
    the text holds that line, else at its end."""
    if line in body:
        return None
    lines = body.rstrip("\n").split("\n")
    if replaces is not None and replaces in lines:
        lines[lines.index(replaces)] = line
        return "\n".join(lines) + "\n"
    return body.rstrip("\n") + "\n\n" + line + "\n"


def noted(  # noqa: PLR0913, PLR0917 - over the limit before the limit was set
    task: Task, pr: dict, line: str, what: str, then: str, replaces: str | None = None
) -> None:
    """LINE in the pull request's text on GitHub, once (`noted_body`): in the place of
    REPLACES, or added at its end when the text lacks it, and in `pr.md`, the task's
    copy of that text, which the board shows. A failed edit is refused with WHAT, the
    line as the owner knows it, and THEN, what stays and what tries again."""
    body = (
        json.loads(
            gh(task, "pr", "view", str(pr["number"]), "--json", "body").stdout
        ).get("body")
        or ""
    )
    new = noted_body(body, line, replaces)
    if new is None:
        return
    text = task.directory / "pr.md"
    write_whole(text, new)
    edited = gh(
        task, "pr", "edit", str(pr["number"]), "--body-file", str(text), check=False
    )
    if edited.returncode != 0:
        said = [
            one.strip()
            for one in (edited.stderr or edited.stdout).splitlines()
            if one.strip()
        ]
        raise LandError(
            f"{what} did not reach the pull request's text (gh pr edit said: "
            f"{said[-1] if said else edited.returncode}); {then}"
        )


def viewed(task: Task, pr: dict | None = None) -> dict:
    pr = pr or task.kept()["pr"]
    # the base too, which anyone may change on GitHub: a merge there goes into whatever
    # base the pull request has then
    return json.loads(
        gh(
            task,
            "pr",
            "view",
            str(pr["number"]),
            "--json",
            "state,headRefOid,mergeCommit,mergeable,baseRefName",
        ).stdout
    )


def merger_blocked(record: dict) -> bool:
    """Whether a task is `blocked` by its merge agent's seat
    (`the seat that failed: merger` in its newest block): its pull request stays open,
    and a merge on GitHub while it waits still lands it."""
    lines = (record.get("state") or "").splitlines()
    return record.get("status") == "blocked" and f"{lem_state.FAILED_SEAT}merger" in (
        line.strip() for line in lines
    )


def cmd_merged(task: Task) -> dict:
    # `landing` too: the owner may merge on the forge while an open task runs its checks
    # again; and a task its merge agent's seat blocked, whose pull request is open while
    # it waits for the owner's go on
    if (
        task.record["status"] not in ("open", "landing")
        and not merger_blocked(task.record)
    ) or not task.kept().get("pr"):
        raise LandError(
            f"the task is {task.record['status']!r} and has "
            f"{'a' if task.kept().get('pr') else 'no'} pull request; this step is for "
            "a task whose pull request the owner merged"
        )
    view = viewed(task)
    if view["state"] == "MERGED":
        return forge_done(task, view)
    if view["state"] == "CLOSED":
        # The owner closed it on the forge: the task ends, and nothing of it waits. Its
        # branch keeps its commits (`clean` removes the worktree and names how to delete
        # the branch), and a task that goes on after all is a new request.
        pr = task.kept()["pr"]
        task.keep(closed=True)
        task.state(
            "dropped",
            "the pull request was closed on the forge",
            (
                f"pull request {pr['url']} is closed with no merge; "
                "the branch keeps its commits"
            ),
        )
        return {
            "task": task.slug,
            "pull_request": pr,
            "closed": True,
            "state": "dropped",
        }
    # Still open: what the forge says of a conflict with the base, on the head it says
    # it of, for the list of what waits
    task.keep(
        forge={"mergeable": view.get("mergeable"), "head": view.get("headRefOid")}
    )
    raise LandError(
        "the pull request is not merged yet"
        + (
            f", and the forge calls it conflicting with {task.base}"
            if view.get("mergeable") == "CONFLICTING"
            else ""
        )
    )


# The fields of a pull request one look at the forge reads (the board's server,
# `forge_look`), for all the open tasks at once.
WATCHED = "number,state,mergeable,headRefOid,mergeCommit"
# How many pull requests of the base branch one look lists, the newest first. A task's
# pull request that is not among them (more than this many were opened after it) is
# asked for by its number.
WATCH_LIST = 100


def forge_look(main: Path, base: str, numbers: list[int]) -> dict[int, dict]:
    """What the forge says of each pull request: one call that lists the base branch's
    newest ones, and one more for each number that list does not hold."""
    listed = json.loads(
        gh_in(
            main,
            "pr",
            "list",
            "--state",
            "all",
            "--base",
            base,
            "--limit",
            str(WATCH_LIST),
            "--json",
            WATCHED,
        ).stdout
        or "[]"
    )
    seen = {pr["number"]: pr for pr in listed if pr.get("number") in numbers}
    for number in numbers:
        if number not in seen:
            seen[number] = json.loads(
                gh_in(main, "pr", "view", str(number), "--json", WATCHED).stdout
            )
    return seen


@contextlib.contextmanager
def merge_lock(
    task: Task, by: str, via: str, *, standing: bool = False
) -> Generator[None, None, None]:
    """Hold the repository's one lock of Lem's merge calls while this one runs. A call
    that finds it held logs `merge.wait` with the task that holds it and waits; whoever
    holds it is done in seconds (a fetch, a merge on the forge or a push). The call
    reads the base branch after it takes it."""
    path = task.directory.parent.parent / MERGE_LOCK
    try:
        handle = path.open("a+", encoding="utf-8")
    except OSError as error:
        raise LandError(
            f"the merge lock {path} cannot be opened ({error.strerror}); "
            f"it holds no state, so remove it (`rm -r {path}`) and run "
            f"`lem land merge {task.slug}` again"
        ) from error
    with handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            holder = holder_of(path)
            other = holder.get("task") if holder else None
            script(
                "project.py",
                task.main,
                "log",
                task.slug,
                "merge.wait",
                f"after={other or 'another task'}",
                f"say={task.slug}: waits for the merge of {other or 'another task'}",
            )
            fcntl.flock(handle, fcntl.LOCK_EX)
        handle.seek(0)
        handle.truncate()
        handle.write(
            json.dumps(
                {
                    "step": "merge",
                    "task": task.slug,
                    "pid": os.getpid(),
                    "since": lem_clock.stamp(),
                }
            )
            + "\n"
        )
        handle.flush()
        script(
            "project.py",
            task.main,
            "log",
            task.slug,
            "merge.start",
            f"by={by}",
            f"via={via}",
            *start_after(task, standing=standing),
        )
        try:
            yield
        finally:
            handle.seek(0)
            handle.truncate()
            handle.flush()


def start_after(task: Task, *, standing: bool) -> list[str]:
    """What `merge.start` says the merge comes after: a read of the merge agent that
    said a move of the base since the checks is safe for the proposed tip (`after` and
    the `base` it read), or the owner's merge that stood through a new landing
    (`a re-check`); nothing for a plain merge."""
    kept = task.kept()
    tip = kept.get("proposed")
    covered = (
        read_base(kept.get("merge_review"), tip, kept.get("another_round"))
        if tip
        else None
    )
    if covered and covered != kept.get("base"):
        return [f"after={READ_AFTER}", f"base={covered[:9]}"]
    return ["after=a re-check"] if standing else []


def stamp_seconds(stamp: str) -> float:
    """A time of the event log, `YYYY-MM-DDTHH:MM:SSZ`, as seconds since the epoch."""
    return (
        datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC).timestamp()
    )


def task_time(events: list[dict], slug: str) -> dict:
    """How long the task took from its first event to its first proposal, against what
    was expected: the median of the same span of every task of the same track proposed
    before it, from the event log (`EVENTS` of every task, oldest first). The track is
    the size of a task's criteria (`small` or `full`); a task whose track the log does
    not say is compared with every earlier task. None where the log cannot tell."""
    first: dict[str, str] = {}
    proposed: dict[str, str] = {}
    track: dict[str, str] = {}
    for event in events:
        name, stamp = event.get("task"), event.get("ts")
        if not isinstance(name, str) or not isinstance(stamp, str):
            continue
        first.setdefault(name, stamp)
        if event.get("event") == "proposed":
            proposed.setdefault(name, stamp)
        if (
            event.get("event") in ("task.criteria", "criteria.approved")
            and event.get("size") in TRACKS
        ):
            track[name] = event["size"]

    def span(name: str) -> int:
        return round(stamp_seconds(proposed[name]) - stamp_seconds(first[name]))

    if slug not in proposed:
        return {"seconds": None, "expected": None, "from": "the task was not proposed"}
    mine = track.get(slug)
    earlier = [
        name
        for name in proposed
        if name != slug
        and proposed[name] < proposed[slug]
        and (mine is None or track.get(name) == mine)
    ]
    which = f"the {TRACKS[mine]} track" if mine else "both tracks"
    if not earlier:
        return {
            "seconds": span(slug),
            "expected": None,
            "from": (
                f"no task of {which} was proposed before it, "
                "so nothing says what to expect"
            ),
        }
    return {
        "seconds": span(slug),
        "expected": round(statistics.median(span(name) for name in earlier)),
        "from": (
            f"the median of {len(earlier)} earlier "
            f"task{'' if len(earlier) == 1 else 's'} of {which}, from the first event "
            "to the proposal, in the event log"
        ),
    }


def pictures_of(directory: Path) -> list[str]:
    """The pictures of a task's `media/` folder that the board's media route shows (PNG,
    JPEG, GIF, WebP, by `lem_artifacts.IMAGES`), each by its path from the task
    directory (`media/NAME`), with those of a subfolder and without a hidden part,
    sorted; [] when the task has no such folder. The merge agent links the ones a report
    links: a builder takes them, since the agent changes nothing."""
    # the board's module, here for its one table of picture suffixes
    import lem_artifacts

    folder = directory / "media"
    if not folder.is_dir():
        return []
    found = []
    for path in folder.rglob("*"):
        parts = path.relative_to(folder).parts
        if (
            path.is_file()
            and not any(part.startswith(".") for part in parts)
            and path.suffix.lower() in lem_artifacts.IMAGES
        ):
            found.append("/".join(("media", *parts)))
    return sorted(found)


def try_of(main: Path, worktree: Path, pr: dict) -> dict:
    """The two ways the owner gets a proposed branch to try it himself: the worktree's
    folder, by its path from the main checkout when it is under it
    (`.lem/worktrees/SLUG`), else whole, and the forge's checkout of the pull request.
    The merge agent copies both into the last line of a review that calls him."""
    try:
        folder = str(worktree.relative_to(main))
    except ValueError:
        folder = str(worktree)
    return {"worktree": folder, "checkout": f"gh pr checkout {pr['number']}"}


def line_verdict(line: str) -> str | None:
    """The verdict one LINE of the merge agent's review gives, `merge` or `call`, past a
    heading's, a quote's or a bold mark; None when it gives none."""
    found = VERDICT.match(line.strip().lstrip("#*> ").strip())
    return found.group(1).lower() if found else None


def verdict_of(text: str) -> str | None:
    """The merge agent's verdict, from the first line of its review: `merge` or `call`,
    or None."""
    return line_verdict(next((line for line in text.splitlines() if line.strip()), ""))


def base_call_of(text: str) -> tuple[str, str] | None:
    """The merge agent's call on a base that moved after the checks, from the second
    line of its review that is not empty: (`safe` or `another round`, its sentence of
    why), or None when that line gives no call, or a call with no sentence of why."""
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) < 2:  # noqa: PLR2004 - the call is the review's second line
        return None
    found = BASE_CALL.match(lines[1].strip().lstrip("#*> ").strip())
    if not found:
        return None
    why = found.group(2).strip().strip("*").strip()
    return (found.group(1).lower(), why) if why else None


def unread_next(
    verdict: str | None,
    *,
    moved: bool,
    base_call: tuple[str, str] | None,
    tries: int,
) -> str | None:
    """What an answer of the merge agent leads to when it cannot be recorded as it is,
    from its facts: its VERDICT (`verdict_of`), whether its brief's base MOVED since the
    checks, its BASE_CALL on that move (`base_call_of`), and TRIES, the count of such
    answers for its tip and base with this one. None when the answer can be recorded;
    `again` for the first such answer, which a fresh merge agent answers; for the
    second, `another round` on a moved base, so the checks decide (in doubt, another
    round), and `owner` on a base that did not move, a review that calls the owner, as
    no answer twice does."""
    if verdict is not None and (not moved or base_call is not None):
        return None
    if tries < MERGER_TRIES:
        return "again"
    return "another round" if moved else "owner"


def lower_verdict(text: str) -> str | None:
    """The verdict a line below the first of the merge agent's answer gives, `merge` or
    `call`, as `verdict_of` reads a first line (`line_verdict`); None when no such
    line does."""
    lines = [line for line in text.splitlines() if line.strip()]
    return next((found for found in map(line_verdict, lines[1:]) if found), None)


def unread_why(lower: str | None, refusal: str | None) -> str:
    """Why a second answer with no verdict on its first line, on a base that did not
    move, calls the owner: what the two answers are known to hold, the first only as one
    with no verdict on its first line, the last whole, so the verdict a lower line of it
    gives (LOWER, `lower_verdict`), which never becomes the verdict; then the reason the
    merge agent may not merge (REFUSAL, `merger_refusal`), if any."""
    last = (
        f"its last answer puts another line above its verdict, `Verdict: {lower}.`"
        if lower
        else "its last answer gives no verdict at all"
    )
    return f"the merge agent twice gave no verdict on its first line; {last}" + (
        f"; {refusal}" if refusal else ""
    )


def moved_of(
    checks_ran_on: str, base_now: str, log: str, files: list[str], own: list[str]
) -> dict | None:
    """What moved on the base since the checks ran, as the merge agent's brief gives it:
    the base the checks ran on, the base now, the range between them, each commit of
    that range (LOG, git's `%h NUL %s` lines, as its short id and subject), the files
    they changed (FILES), and which of those the task's own change touches too (OWN, the
    files of the change). None when no file moved: an empty commit on the base moves
    nothing. Always from the checks' base, never from an earlier read, so a read sees
    every move since the checks."""
    if not files:
        return None
    commits = [
        {"commit": commit, "subject": subject}
        for commit, _, subject in (
            line.partition("\0") for line in log.splitlines() if line.strip()
        )
    ]
    mine = set(own)
    return {
        "checks_ran_on": checks_ran_on,
        "base_now": base_now,
        "range": f"{checks_ran_on}..{base_now}",
        "commits": commits,
        "files": files,
        "overlap": [path for path in files if path in mine],
    }


def read_base(review: dict | None, tip: str, another_round: str | None) -> str | None:
    """The base a merge review of TIP lets it merge on when the base moved after the
    checks: the base the read covered, when it said `Base: safe.` and no read of TIP
    said `Base: another round.` (ANOTHER_ROUND, the tip such a read was of), whose
    refusal only a new landing answers. None for none: a read with no base call covers
    only the checks' own base."""
    if not isinstance(review, dict) or review.get("tip") != tip or another_round == tip:
        return None
    return review.get("base") if review.get("base_call") == "safe" else None


def refusal_answered(refused: object, tip: str) -> bool:
    """Whether a read of TIP with `Base: safe.` answers the refusal on record (REFUSED,
    `merge_refused`): only Lem's own refusal of that tip because the base moved
    (`kind: base`). GitHub's, a rule's and a tip's stay until a new proposal."""
    return (
        isinstance(refused, dict)
        and refused.get("from") == "lem"
        and refused.get("kind") == "base"
        and refused.get("tip") == tip
    )


def read_answers(
    refused: object, tip: str, base_call: str | None, *, on_checks_base: bool
) -> bool:
    """Whether the record of a read of TIP answers the refusal on record (REFUSED,
    `refusal_answered`): a read with `Base: safe.` (BASE_CALL), or a read whose brief
    named the checks' own base (ON_CHECKS_BASE): origin's base had the checks' tree
    again when the brief was written, after a revert of the move Lem refused for, so the
    read has no call on a move, and the merge checks the base once more. A read with
    `Base: another round.` answers nothing."""
    return refusal_answered(refused, tip) and (base_call == "safe" or on_checks_base)


def base_line(base: str, checks_ran_on: str, merged_on: str, why: str) -> str:
    """The record of a merge on a base that moved after the checks, for the pull
    request's text and the merge commit: the base the checks ran on, the base it merged
    on, and the merge agent's sentence of why."""
    return (
        f"The checks ran on {base} at {checks_ran_on[:9]}; it merged on {base} at "
        f"{merged_on[:9]}, after the merge agent's read of what moved: {why}"
    )


def uncovered_line(base: str, checks_ran_on: str, real: str, read: str) -> str:
    """The record of a merge whose real base on GitHub is not the one the merge agent's
    read covered: a merge outside Lem came between Lem's look at the base and its merge
    call, which nothing can undo."""
    return (
        f"The checks ran on {base} at {checks_ran_on[:9]}; it merged on {base} at "
        f"{real[:9]}, which no read of the merge agent covered (its read covered "
        f"{read[:9]}): a merge on GitHub came between Lem's look at the base and its "
        "merge, and nothing undoes it"
    )


def moved_refusal(  # noqa: PLR0913 - over the limit before the limit was set
    slug: str,
    onto: str,
    files: list[str],
    by: str,
    covered: str | None,
    *,
    round_said: bool,
) -> str:
    """Why a merge on a base that moved after the checks by FILES is refused, and the
    step that comes next: the merge agent's read of what moved, or a new landing when a
    read of the tip said `Base: another round.` (ROUND_SAID). COVERED is the base an
    earlier read with `Base: safe.` covered, which covers no later base."""
    said = (
        f"{onto} moved after the checks ran, by files "
        f"({', '.join(files[:NAMED_FILES])}"
        f"{', ...' if len(files) > NAMED_FILES else ''})"
    )
    if round_said:
        then = (
            (
                "the owner's merge stands while the change and the reasons it is not "
                "green stay the same, and the board's server "
                "merges it after the proposal"
            )
            if by == "owner"
            else (
                "the board's server merges it after the proposal when the merge "
                "review still says merge"
            )
        )
        return (
            f"{said}, and the merge agent's read of this tip said another round; "
            f"{AGAIN}. The merge review is kept with the review, and {then}"
        )
    earlier = (
        f"; the read of {covered[:9]} said safe, and it covers no later base"
        if covered
        else ""
    )
    then = (
        (
            "the owner's merge stands, and goes through after a read that says "
            "`Base: safe.`; on `Base: another round.` the task lands again"
        )
        if by == "owner"
        else (
            "the board's server merges it after a read that says `Base: safe.` "
            "when its verdict is merge"
        )
    )
    return (
        f"{said}{earlier}. A fresh merge agent reads what moved: "
        f"`lem land merge-review {slug}` writes its brief, with the commits and the "
        "files that moved since the checks, and the answer names its "
        f"base (`--base`); {then}"
    )


def carried_review(
    review: dict, tip: str, *, calls: bool, why: str | None, old: str | None
) -> dict:
    """The merge agent's review of the proposed tip OLD as `propose` carries it onto TIP
    after a new landing: its verdict, with whether it calls the owner as the rules say
    now. Its call on a moved base is dropped: the new landing's checks ran on the new
    base, so a read of an older one says nothing of it."""
    kept = {
        key: value
        for key, value in review.items()
        if key not in ("base", "base_call", "base_why")
    }
    return {**kept, "tip": tip, "calls": calls, "why": why, "carried_from": old}


def merger_seat(task: Task) -> dict:
    """The merge agent's seat in use for the task, as `lem project seat SLUG merger`
    prints it: the fallback while it stands in for the merger, else the
    settings' `seats.merger`."""
    found = json.loads(
        script("project.py", task.main, "seat", task.slug, "merger").stdout
    )
    return {key: found.get(key) for key in ("agent", "model", "effort", "seat", "from")}


def seats_kept(kept: object, tip: str, base: str, seat: dict) -> dict:
    """The seats kept with the merge agent's briefs (`merge_seats` of landing.json,
    KEPT) once the brief of TIP on BASE was written for SEAT: that brief's seat is SEAT,
    a stand-in's in the place of the one that failed on the same brief, and the briefs
    of an earlier tip go."""
    earlier = kept if isinstance(kept, dict) else {}
    return {
        **{key: value for key, value in earlier.items() if key.startswith(f"{tip}-")},
        f"{tip}-{base}": seat,
    }


def seat_of_brief(kept: object, tip: str, base: str) -> dict | None:
    """The seat kept with the brief of TIP on BASE (`seats_kept`), the one that reads
    it; None for none."""
    seat = kept.get(f"{tip}-{base}") if isinstance(kept, dict) else None
    return seat if isinstance(seat, dict) and seat.get("seat") else None


def brief_file(task: Task, tip: str, base: str) -> Path:
    """The merge agent's brief of a proposed tip on one base, so that the brief of a
    later base never takes the place of the one an agent was started with."""
    return task.directory / f"merge-brief-{tip[:12]}-{base[:12]}.md"


def answer_file(task: Task, tip: str, base: str) -> Path:
    """The file the merge agent's answer goes to, one for each proposed tip and base, so
    that the answer of a read of an earlier proposal, or of an earlier base, never takes
    the place of the newest one's."""
    return task.directory / f"merge-answer-{tip[:12]}-{base[:12]}.md"


def moved_facts(task: Task, checks_ran_on: str, base_now: str, tip: str) -> dict | None:
    """`moved_of` from git: what moved on the base between the checks' base and
    BASE_NOW, beside the files of the task's change from the checks' base to TIP."""
    files = changed(task, checks_ran_on, base_now) if base_now != checks_ran_on else []
    if not files:
        return None
    log = git(task.worktree, "log", "--format=%h%x00%s", f"{checks_ran_on}..{base_now}")
    return moved_of(
        checks_ran_on, base_now, log, files, changed(task, checks_ran_on, tip)
    )


def cmd_merge_review(  # noqa: C901, PLR0912, PLR0915 - over the limit before the limit was set
    task: Task,
    record: str | None,
    read_tip: str | None = None,
    read_on: str | None = None,
) -> dict:
    """The merge agent's read of a proposed task. With no record: its brief,
    `merge-brief-TIP-BASE.md` in the task directory, and the facts in it, the proposed
    `tip`, the `base` it reads against and what `moved` on the base since the checks
    among them. With the agent's reply, READ_TIP and READ_ON, the tip and the base its
    brief named: the review written down as `merge-review.md`, whether it merges or
    calls the owner, and on a moved base its call on the move; the reply of a brief of
    another tip than the one proposed now, or of a base no brief named, is refused."""
    if task.record["status"] != "open":
        raise LandError(
            f"the task is {task.record['status']!r}, not `open`: the merge agent reads "
            f"a proposed task; `lem land propose {task.slug}` comes first"
        )
    task.need_worktree()
    kept = task.kept()
    tip = kept.get("proposed")
    if not tip or not kept.get("pr"):
        raise LandError(
            f"{task.slug} has no pull request on record; "
            f"`lem land propose {task.slug}` comes first"
        )
    if git(task.worktree, "rev-parse", "HEAD") != tip:
        raise LandError(f"the branch's tip is not the tip that was proposed; {AGAIN}")
    if kept.get("another_round") == tip:
        # a read of this tip said the moved base needs another round: its refusal is
        # answered by the new landing alone
        raise LandError(
            f"the merge agent's read of {tip[:9]} said that the moved base needs "
            f"another round of the checks, and no later read answers that; {AGAIN}"
        )
    state = due(task)
    reasons = not_green(task, state)
    land = task.settings["branch"]["land"]
    # whether the merge agent may merge when it finds nothing: every rule but its
    # own verdict
    refusal = merger_refusal(
        task.slug,
        land,
        state["careful"],
        reasons,
        called=review_call(task) is not None,
        review={"verdict": "merge"},
    )
    if record is None:
        # origin's base now, after a fetch: a move since the checks is read in this
        # brief, so one read answers both questions
        task.fetch()
        base_now = git(task.worktree, "rev-parse", task.onto)
        moved = moved_facts(task, kept["base"], base_now, tip)
        base = base_now if moved else kept["base"]
        found = criteria_of(task)
        files: dict[str, str | list[str]] = {
            name: str(task.directory / file)
            for name, file in (
                ("pull_request_text", "pr.md"),
                ("words", "ask.txt"),
                ("request", "task.md"),
                ("report", "report.md"),
                ("notes", "notes.md"),
                ("investigation", "investigation.md"),
            )
            if (task.directory / file).is_file()
        }
        # each breaker's document, the newest last (decisions.py keeps them
        # as breaker-N.md)
        breakers = sorted(
            task.directory.glob("breaker-*.md"),
            key=lambda path: int(re.sub(r"\D", "", path.stem) or 0),
        )
        if breakers:
            files["breakers"] = [str(path) for path in breakers]
        facts = {
            "task": task.slug,
            "worktree": str(task.worktree),
            "task_directory": str(task.directory),
            "pull_request": kept["pr"],
            "tip": tip,
            "range": f"{kept['base']}..{tip}",
            "track": TRACKS.get(found["size"], found["size"]),
            "criteria": found["plan"],
            "files": files,
            "reviews": sorted(
                str(file) for file in (task.directory / "reviews").glob("review-*.md")
            )
            if (task.directory / "reviews").is_dir()
            else [],
            "decisions": f"lem decisions list {task.slug}",
            "green": not reasons,
            "not_green": reasons,
            "careful": state["careful"],
            "land": land,
            # the call is the owner's whatever the agent finds, when this names why
            "owner_merges": refusal,
            "time": task_time(events_all(task), task.slug),
            # the tokens of the task's Claude Code sessions and their subagents, with
            # what the number leaves out (`covers`); null when no transcript the log
            # names counts for the task (`lem_tokens.transcripts_of`)
            "tokens": lem_tokens.task_tokens(task.directory.parent.parent, task.slug),
            # how many times this proposal landed again (a base that moved, a conflict):
            # nothing bounds them
            "relands": int(kept.get("relands") or 0),
            # the builders' pictures, which a review of a change to what a person
            # sees links
            "pictures": pictures_of(task.directory),
            # each item the branch adds to the backlog folder, whoever filed it, which
            # the agent reads against the bar of rule 6 in the file `bar` names, the one
            # the project's builders read
            "filed": [
                {"item": item["item"], "title": item["title"]}
                for item in items_added(task, kept["base"])
            ],
            "bar": bar_file(task.main),
            # how the owner tries the branch himself, the last line of a review that
            # calls him
            "try": try_of(task.main, task.worktree, kept["pr"]),
            # each seat that stood in for another in this task, for which seat and why:
            # a fact, and no reason to call the owner
            "stand_ins": [
                {
                    key: stand_in[key]
                    for key in ("seat", "took", "failed", "error", "failed_too")
                }
                for stand_in in stand_ins_of(events_of(task))
            ],
            # the base this read is against, and what moved on it since the checks ran
            # (null when nothing moved); on a moved base the answer's second line is
            # `Base: safe.` or `Base: another round.`, then one sentence of why
            "base": base,
            "moved": moved,
        }
        # The seat in use, a stand-in while one holds: it is kept with this brief, by
        # its tip and base, so the record of its answer names the seat that read it,
        # whatever the settings say by then. After a stand-in this step runs again for
        # the same brief, and the stand-in's seat takes the failed one's place.
        seat = merger_seat(task)
        task.keep(merge_seats=seats_kept(kept.get("merge_seats"), tip, base, seat))
        brief = brief_file(task, tip, base)
        write_whole(
            brief,
            "\n".join(
                [
                    # by its place in the plugin, never by this Lem's folder, which an
                    # update of the plugin replaces
                    "Read `skills/lem/prompts/merge.md` in the folder that `lem version` prints as `root`, and follow it; when `lem version` fails, stop and say that `lem` is not on the PATH, with `lem doctor` as the check. Your reply is the review, in the form that file gives, and nothing else.",  # noqa: E501 - tests/unit/test_session.py reads this line whole (BRIEF_LINE)
                    "",
                    "The facts of this task, as `lem land merge-review` gave them:",
                    "",
                    "```json",
                    json.dumps(facts, indent=2),
                    "```",
                    "",
                ]
            ),
        )
        return {
            "task": task.slug,
            "brief": str(brief),
            "answer": str(answer_file(task, tip, base)),
            "tip": tip,
            "base": base,
            "worktree": str(task.worktree),
            "seat": seat,
            "facts": facts,
        }
    # The reply is of the brief that named its tip and its base: one of an earlier
    # proposal is no read of this one, and the read covers the base its brief named,
    # never the base at the time of this record.
    if read_tip is None or read_on is None:
        raise LandError(
            "--file goes with --tip and --base, the `tip` and the `base` that "
            f"`lem land merge-review {task.slug}` printed for the "
            "brief the merge agent read"
        )
    if read_tip != tip:
        raise LandError(
            f"the merge agent's answer is of {read_tip[:12]}, and the proposal is "
            f"{tip[:12]} now: it read an earlier proposal, and its answer is not "
            f"written down. `lem land merge-review {task.slug}` writes the brief of "
            "this one, and a fresh merge agent reads it",
        )
    if (
        not re.fullmatch(r"[0-9a-f]{40}", read_on)
        or not brief_file(task, tip, read_on).is_file()
    ):
        raise LandError(
            f"--base is {read_on!r}, and no brief of {tip[:12]} on that base was "
            f"written: --base is the whole commit `lem land merge-review {task.slug}` "
            "printed as `base` with the brief the merge agent read; "
            "its answer is not written down",
        )
    # the seat that read: the one kept with the brief, never a new read of the settings
    seat = seat_of_brief(kept.get("merge_seats"), tip, read_on)
    if seat is None:
        raise LandError(
            f"no seat is kept with the brief of {tip[:12]} on {read_on[:12]}, so the "
            "record could not name the seat that read it: "
            f"`lem land merge-review {task.slug}` writes the brief again with its "
            "seat, and a fresh merge agent reads it"
        )
    try:
        text = Path(record).read_text(encoding="utf-8")
    except OSError as error:
        raise LandError(
            f"{record} cannot be read ({error.strerror}); "
            "--file names the merge agent's reply"
        ) from error
    moved = read_on != kept["base"]
    verdict = verdict_of(text)
    call = base_call_of(text) if moved else None
    problem, short = None, None
    if verdict is None:
        problem = (
            f"the first line of {record} gives no verdict: it is `Verdict: merge.` or "
            "`Verdict: call.`, then one sentence, as `prompts/merge.md` asks"
        )
        short = "its first line gave no verdict"
    elif moved and call is None:
        problem = (
            f"the second line of {record} gives no call on the moved base: "
            "the base moved after the checks ran, so it is `Base: safe.` or "
            "`Base: another round.`, then one sentence of why, "
            "as `prompts/merge.md` asks"
        )
        short = "its second line gave no call on the moved base"
    owner = False
    if problem:
        # The merge agent is asked again once (`unread_next`). Its second answer that
        # cannot be recorded is recorded as another round on a moved base, so the checks
        # decide, and the owner is not asked (in doubt, another round); on a base that
        # did not move it is a review that calls the owner, with no verdict, whatever a
        # lower line of it says.
        unread = kept.get("merge_unread") or {}
        tries = (
            int(unread.get("count") or 0) + 1
            if unread.get("tip") == tip and unread.get("base") == read_on
            else 1
        )
        task.keep(merge_unread={"tip": tip, "base": read_on, "count": tries})
        then = unread_next(verdict, moved=moved, base_call=call, tries=tries)
        if then == "again":
            raise LandError(f"{problem}; the merge agent is asked again")
        if then == "another round":
            call = (
                "another round",
                (
                    f"the merge agent's answer could not be recorded twice ({short}), "
                    "and in doubt the checks run again"
                ),
            )
        owner = then == "owner"
    calls = verdict == "call" or refusal is not None or owner
    if owner:
        why = unread_why(lower_verdict(text), refusal)
    else:
        why = refusal or (
            next(line for line in text.splitlines() if line.strip())
            .strip()
            .lstrip("#*> ")
            .strip()
            if verdict == "call"
            else None
        )
    # the merge agent's stand-ins go into the pull request's text before the read is
    # written down, so a failed edit leaves the read to record again
    merger_noted(
        task,
        kept["pr"],
        (
            "the read is not written down, and the same "
            f"`lem land merge-review {task.slug} --file` tries again"
        ),
    )
    write_whole(
        task.directory / "merge-review.md", text if text.endswith("\n") else text + "\n"
    )
    review = {
        "tip": tip,
        "verdict": verdict,
        "calls": calls,
        "why": why,
        "by": seat["seat"],
        "at": lem_clock.stamp(),
        "base": read_on,
        "base_call": call[0] if call else None,
        "base_why": call[1] if call else None,
    }
    task.keep(merge_review=review, merge_unread=None)
    # one event for each read, with its call on the base and its why, so the log keeps
    # every read's reason after merge-review.md is written over
    script(
        "project.py",
        task.main,
        "log",
        task.slug,
        "merge.review",
        *([f"verdict={verdict}"] if verdict else []),
        f"calls:={json.dumps(calls)}",
        f"by={seat['seat']}",
        f"tip={tip[:9]}",
        *([f"why={why}"] if why else []),
        f"base={read_on[:9]}",
        *([f"base_call={call[0]}", f"base_why={call[1]}"] if call else []),
    )
    stands = False
    if call and call[0] == "another round":
        # The read keeps a refusal of kind `base` for its tip, as a moved base's refusal
        # is kept: the server wakes the session, the board says it lands again, and only
        # the new landing answers it.
        before = (
            kept.get("merge_refused")
            if refusal_answered(kept.get("merge_refused"), tip)
            else None
        )
        by, via = (
            (before["by"], before.get("via", "session"))
            if before
            else ("merger", "session")
        )
        said = (
            f"the merge agent's read of what moved on {task.base} since the checks "
            f"says another round: {call[1]}; {AGAIN}"
        )
        task.keep(
            merge_refused={
                "tip": tip,
                "by": by,
                "via": via,
                "from": "lem",
                "kind": "base",
                "said": said,
                "at": lem_clock.stamp(),
            },
            another_round=tip,
        )
        script(
            "project.py",
            task.main,
            "log",
            task.slug,
            "merge.refused",
            f"by={by}",
            f"via={via}",
            "from=lem",
            "kind=base",
            f"said={said}",
            f"tip={tip[:9]}",
        )
    elif read_answers(
        kept.get("merge_refused"),
        tip,
        call[0] if call else None,
        on_checks_base=not moved,
    ):
        # A safe read, or a read on the checks' own base after main went back to their
        # tree, answers Lem's refusal of this tip for the moved base, so landing.json,
        # `lem project waiting` and the board agree; the owner's merge that it refused
        # stands, and the server runs it.
        task.keep(merge_refused=None)
        tap = kept.get("owner_tap")
        if isinstance(tap, dict) and tap.get("tip") == tip:
            stands = True
            script(
                "project.py",
                task.main,
                "log",
                task.slug,
                "merge.stands",
                "by=owner",
                f"tip={tip[:9]}",
                f"after={READ_AFTER if moved else READ_BACK}",
                f"base={read_on[:9]}",
            )
    if call and call[0] == "another round":
        after = (
            "the merge agent says that the moved base needs another round of the "
            f"checks: the task lands again, and the owner is not asked; {AGAIN}"
        ) + (
            (
                "; the owner's merge stands through the new landing while the "
                "change and the reasons it is not green stay the same"
            )
            if (kept.get("owner_tap") or {}).get("tip") == tip
            else ""
        )
    elif stands:
        after = (
            "the owner's merge stands: the board's server merges it on "
            f"{task.base}{f' at {read_on[:9]}' if moved else ''} (`lem land merge "
            f"{task.slug} --by owner --via server --standing`), and the owner is not "
            f"asked again; wait for the wake-up `lem: {task.slug} merged`, or "
            f"`lem: {task.slug} refused`"
        )
    elif calls:
        after = (
            'it calls the owner: "Read the merge review" waits for him, '
            "and only his merge lands it"
        )
    else:
        after = (
            f"the board's server merges it (`lem land merge {task.slug} --by merger "
            "--via server`): tell the owner in one line that the merge agent found "
            f"nothing for him, and wait for the wake-up `lem: {task.slug} merged`, or "
            f"`lem: {task.slug} refused`"
        )
    return {
        "task": task.slug,
        "review": str(task.directory / "merge-review.md"),
        "verdict": verdict,
        "calls": calls,
        "why": why,
        "by": seat["seat"],
        "base": read_on,
        "base_call": call[0] if call else None,
        "base_why": call[1] if call else None,
        "next": after,
    }


def expected_refusal(
    expected: str | None, proposed: str | None, slug: str
) -> str | None:
    """Why a merge given the tip its caller saw (EXPECTED, `--tip`: the commit the
    owner's confirm step showed, the one the merge agent's review read, the one his
    standing merge was of) may not merge the tip proposed now; None when they are one,
    or when no tip was given."""
    if expected is None:
        return None
    if not re.fullmatch(r"[0-9a-f]{40}", expected):
        return (
            "--tip is the whole commit the merge is for, 40 hex digits, as "
            f"`landing.json` keeps `proposed`, and it is {expected!r}; "
            "nothing was merged"
        )
    if expected != proposed:
        return (
            f"the merge was asked for {expected[:9]}, and the proposal is "
            f"{str(proposed)[:9]} now: the branch was proposed again since, and "
            "nothing was merged. The new proposal is read again "
            f"(`lem land merge-review {slug}`), and the owner's word "
            "is for the commit he saw"
        )
    return None


def cmd_merge(  # noqa: PLR0913 - over the limit before the limit was set
    task: Task,
    by: str,
    message: str | None,
    via: str,
    *,
    standing: bool = False,
    expected: str | None = None,
) -> dict:
    if task.record["status"] != "open":
        raise LandError(
            f"the task is {task.record['status']!r}, not `open`; "
            f"`lem land propose {task.slug}` comes first"
        )
    if standing and by != "owner":
        raise LandError(
            "--standing is the owner's merge that stood through a new landing or a "
            "read of the moved base: it goes with --by owner"
        )
    # Under the task's step lock, so no proposal comes in between, and before anything
    # of the merge is kept: a word for another commit than the one proposed now merges
    # nothing and stands for nothing.
    wrong = expected_refusal(expected, task.kept().get("proposed"), task.slug)
    if wrong:
        raise LandError(wrong)
    with merge_lock(task, by, via, standing=standing):
        # another call may have merged this task, or the owner closed it, while this
        # one waited
        task.read_states()
        try:
            return merge_locked(task, by, message, via, standing=standing)
        except Refusal as error:
            # A refusal by Lem's rules is kept for that tip (`kept_refusal`), so that
            # the server tries it no more and wakes the task's session: the merge
            # agent's, which runs with nobody to read it, and a moved base's, of the
            # owner's merge too, which the session answers with a fresh read of what
            # moved. The owner's merge then stands on that read's `Base: safe.`
            # (`merge.stands`), or for the next proposal after `Base: another round.`
            # (`moved_carry`).
            if (
                kept_refusal(by, error.kind)
                and task.record["status"] == "open"
                and task.kept().get("proposed")
            ):
                kept = task.kept()
                tip = kept["proposed"]
                task.keep(
                    merge_refused={
                        "tip": tip,
                        "by": by,
                        "via": via,
                        "from": "lem",
                        "kind": error.kind,
                        "said": str(error),
                        "at": lem_clock.stamp(),
                    }
                )
                if by == "owner":
                    task.keep(
                        owner_tap={
                            "tip": tip,
                            "not_green": kept.get("not_green", []),
                            "via": via,
                            "at": lem_clock.stamp(),
                        }
                    )
                script(
                    "project.py",
                    task.main,
                    "log",
                    task.slug,
                    "merge.refused",
                    f"by={by}",
                    f"via={via}",
                    "from=lem",
                    f"kind={error.kind}",
                    f"said={error}",
                    f"tip={tip[:9]}",
                )
            raise


def merge_locked(  # noqa: C901, PLR0912, PLR0915 - over the limit before the limit was set
    task: Task, by: str, message: str | None, via: str, *, standing: bool = False
) -> dict:
    """The one merge of a task's pull request, the owner's and the merge agent's alike:
    through GitHub, at the commit that was proposed, on the base it was checked on, or
    on the base a read of the merge agent's covered when it said the move is safe."""
    if task.record["status"] != "open":
        raise LandError(
            f"the task is {task.record['status']!r}, not `open`; "
            f"`lem land propose {task.slug}` comes first"
        )
    task.need_worktree()
    kept = task.kept()
    if not kept.get("pr"):
        # every merge goes through the pull request: a branch is never pushed onto the
        # base past it
        raise LandError(
            f"{task.slug} has no pull request on record; "
            f"`lem land propose {task.slug}` opens it or finds it, "
            "and the merge goes through it"
        )
    view = viewed(task)
    if view["state"] == "MERGED":
        # GitHub already holds the merge, whoever made it: only the bookkeeping is left
        return forge_done(task, view)
    if view["state"] != "OPEN":
        raise LandError(
            "the pull request was closed without a merge: "
            f"`lem land merged {task.slug}` writes the task dropped, "
            "and its branch keeps its commits"
        )
    # GitHub merges into the base the pull request has now, which is not always the one
    # it was proposed on
    wrong = base_refusal(view, task.base, kept["pr"]["url"], task.slug)
    if wrong:
        raise Refusal("tip", wrong)
    may_merge(task, by)
    tip = git(task.worktree, "rev-parse", "HEAD")
    if kept.get("proposed") != tip:
        raise Refusal(
            "tip", f"the branch's tip is not the tip that was proposed; {AGAIN}"
        )
    if view["headRefOid"] != tip:
        raise Refusal(
            "tip", f"the pull request's head is not the tip that was proposed; {AGAIN}"
        )
    missing = gate_missing(task, tip)
    if missing:
        raise Refusal("tip", f"{missing}; {AGAIN}")
    if standing and (kept.get("owner_tap") or {}).get("tip") != tip:
        raise Refusal(
            "tip",
            (
                "no merge of the owner's stands for the proposed tip: it ended at the "
                "proposal (`lem land propose` said why), and the owner merges it again "
                f"from the board or with `lem land merge {task.slug} --by owner`"
            ),
        )
    squash = task.settings["branch"]["history"] == "squash"
    if squash and not message:
        raise LandError(
            'branch.history is "squash": pass --message with the one commit\'s '
            "subject, from the task's report"
        )
    if not squash and message:
        raise LandError(
            'branch.history is "keep": the branch\'s own commits land, '
            "so --message has nothing to name"
        )
    # The base is read after the lock is taken, so that a merge just before this one is
    # met here. What lands is the tree the checks passed on, on the base they ran on, or
    # on the base a read of the merge agent's covered when it said the move is safe: by
    # tree, so an empty commit on either moves nothing.
    task.fetch()
    base_now = git(task.worktree, "rev-parse", task.onto)
    moved = changed(task, kept["base"], base_now) if base_now != kept["base"] else []
    record: dict = {}
    if moved:
        review = merge_review_of(task)
        covered = read_base(review, tip, kept.get("another_round"))
        if not covered or review is None or changed(task, covered, base_now):
            raise Refusal(
                "base",
                moved_refusal(
                    task.slug,
                    task.onto,
                    moved,
                    by,
                    covered,
                    round_said=kept.get("another_round") == tip,
                ),
            )
        line = base_line(task.base, kept["base"], covered, review["base_why"])
        commits = (
            1
            if squash
            else int(
                git(task.worktree, "rev-list", "--count", f"{kept['base']}..{tip}")
            )
        )
        record = {
            "after": READ_AFTER,
            "base": covered,
            "checks_ran_on": kept["base"],
            "base_why": review["base_why"],
            "line": line,
            "commits": commits,
        }
    proposed = task.directory / "pr.md"
    body = squash_body(
        proposed.read_text(encoding="utf-8") if proposed.is_file() else "",
        record.get("line"),
        task.slug,
    )
    how = (
        ["--squash", "--subject", cast("str", message), "--body", body]
        if squash
        else ["--rebase"]
    )
    merged = gh(
        task,
        "pr",
        "merge",
        str(kept["pr"]["number"]),
        "--match-head-commit",
        tip,
        *how,
        check=False,
    )
    if merged.returncode != 0:
        # GitHub's own rules hold (a required review, a check it waits for, a protected
        # branch): its line is kept for "Waits for you", and the owner acts on GitHub or
        # asks Lem for a change.
        said = [
            line.strip()
            for line in (merged.stderr or merged.stdout).splitlines()
            if line.strip()
        ]
        line = said[-1] if said else f"gh pr merge exited {merged.returncode}"
        task.keep(
            merge_refused={
                "tip": tip,
                "by": by,
                "via": via,
                "from": "github",
                "said": line,
                "at": lem_clock.stamp(),
            }
        )
        script(
            "project.py",
            task.main,
            "log",
            task.slug,
            "merge.refused",
            f"by={by}",
            f"via={via}",
            "from=github",
            f"said={line}",
            f"tip={tip[:9]}",
        )
        raise ForgeSaid(
            f"GitHub refused the merge of {kept['pr']['url']}: {line}. "
            "It waits for the owner as `open`"
        )
    # who merged, and who ran the call: the merge agent's merge is the board's server's
    # (`--via server`); the owner's that stood through a new landing ran after the
    # checks and the reviews were checked again; one on a moved base ran after the merge
    # agent's read of it, whose line `forge_done` writes into the pull request's text
    # once GitHub holds the merge
    task.keep(
        merged_by={
            "by": by,
            "via": via,
            **(record or ({"after": "a re-check"} if standing else {})),
        }
    )
    view = viewed(task)
    if view["state"] != "MERGED":
        raise ForgeSaid(
            "GitHub took the merge and the pull request is not merged yet (a queue, or "
            "a check it waits for); run `lem land merged` when it is"
        )
    return forge_done(task, view)


def squash_body(text: str, moved: str | None, slug: str) -> str:
    """The body of the one commit a squash merge makes, from TEXT, the pull request's
    text as `propose` wrote it: each line under `## Fixed on the way`, so the base's
    history names each fix made outside the task on the way; then MOVED, the line of a
    merge on a base that moved after the checks, when there is one; and last the line
    `Lem task: SLUG`, by which the board names the task that added an item of
    the backlog."""
    fixed = lines_of(section(text, FIXED).splitlines())
    return "\n\n".join(
        [
            *(["\n".join(fixed)] if fixed else []),
            *([moved] if moved else []),
            f"Lem task: {slug}",
        ]
    )


def first_differ(replayed: list[str], own: list[str]) -> int | None:
    """The place of the first commit whose tree is not the tree the replay made there,
    or None when each pair holds the same tree. Both lists are in the order of their
    commits, one tree each."""
    return next(
        (
            place
            for place, (made, held) in enumerate(zip(replayed, own, strict=True))
            if made != held
        ),
        None,
    )


def after_push(task: Task, branch: str, tip: str, merged: str) -> tuple[bool, str]:
    """Whether a branch whose tip is not the head the forge merged holds that head's
    change, rebased after its push, and the sentence that says so or names what changed.

    The change is compared by content: the merged head's whole change, merged onto the
    tip's own base, must give the tip's tree. Git's patch id is not the proof, as
    `change` says: it ignores spaces and changes with its context lines, which a base
    that moved next to the change gives. The commit named is the one a replay of the
    merged head's commits onto the tip's base, as the rebase made them, first gives
    another tree than the tip's commit at its place; the files when none can be named.

    The merged head's base is where it meets the tip's base, not where it meets the base
    branch: a merge commit on the forge puts the merged head itself on the base branch,
    where a squash or its "Rebase and merge" leaves it off it, and the tip's base is
    older than any of the three merges."""
    where = task.main
    base_tip = git(where, "merge-base", tip, task.onto)
    base_merged = git(where, "merge-base", merged, base_tip)
    together = run(
        [
            "git",
            "-C",
            str(where),
            "merge-tree",
            "--write-tree",
            "--merge-base",
            base_merged,
            base_tip,
            merged,
        ],
        check=False,
    )
    if together.returncode not in (0, 1):
        raise LandError(
            f"git merge-tree of {merged[:9]} onto {base_tip[:9]} failed: "
            f"{(together.stderr or together.stdout).strip()}"
        )
    tree = together.stdout.split()[0]
    theirs = git(
        where, "rev-list", "--reverse", "--no-merges", f"{base_merged}..{merged}"
    ).split()
    ours = git(
        where, "rev-list", "--reverse", "--no-merges", f"{base_tip}..{tip}"
    ).split()
    if together.returncode == 0 and tree == git(where, "rev-parse", f"{tip}^{{tree}}"):
        commits = (
            f"the same {len(ours)} commits"
            if len(ours) == len(theirs)
            else (
                f"the same change, in {len(theirs)} commits where the "
                f"branch has {len(ours)}"
            )
        )
        return True, (
            f"{branch} was rebased after its push: its tip {tip[:9]} holds the same "
            f"change as {merged[:9]}, the head Lem pushed, "
            f"and the forge merged {commits}"
        )
    named = None
    if len(ours) == len(theirs):
        replayed: list[str] = []
        made = f"{base_tip}^{{tree}}"
        for commit in theirs:
            step = run(
                [
                    "git",
                    "-C",
                    str(where),
                    "merge-tree",
                    "--write-tree",
                    "--merge-base",
                    f"{commit}^",
                    made,
                    commit,
                ],
                check=False,
            )
            if step.returncode != 0:
                break
            made = step.stdout.split()[0]
            replayed.append(made)
        else:
            place = first_differ(
                replayed,
                [git(where, "rev-parse", f"{commit}^{{tree}}") for commit in ours],
            )
            if place is not None:
                named = (
                    f"its commit {ours[place][:9]} "
                    f'"{git(where, "log", "-1", "--format=%s", ours[place])}"'
                )
    if not named:
        files = [
            name
            for name in git(
                where, "diff", "--name-only", tree, f"{tip}^{{tree}}"
            ).splitlines()
            if name
        ]
        named = (
            f"the files {', '.join(files)}"
            if files
            else "a change one merge of it cannot carry"
        )
    return False, (
        f"{branch} was changed after its push: the forge merged {merged[:9]}, the head "
        f"Lem pushed, and the tip {tip[:9]} differs from it in {named}. "
        f"`git range-diff {base_merged[:9]}..{merged[:9]} {base_tip[:9]}..{tip[:9]}` "
        f"shows the difference, and `git branch -D {branch}` removes the branch"
    )


def drop_forge_copy(task: Task, branch: str, removed: dict) -> None:
    """The forge's copy of a merged task's branch goes, only when it is the commit that
    was merged: a failure here is said, and the next run finds the local branch and
    tries again. The ref is looked up by its whole name (a pattern also matches
    `archive/BRANCH`), and the deletion carries the commit it was checked at, so a push
    that came in between stops it."""
    kept = task.kept()
    if not (kept.get("merged") and task.forge):
        return
    ref = f"refs/heads/{branch}"
    listed = [
        line.split("\t")
        for line in run(
            ["git", "-C", str(task.main), "ls-remote", "origin", ref]
        ).stdout.splitlines()
    ]
    there = next((commit for commit, name in listed if name == ref), None)
    if there and there != kept.get("merged_head"):
        removed["remote_left"] = (
            f"origin has {there[:9]} on {branch}, which is not the commit the "
            "forge merged; it stays"
        )
    elif there:
        git(task.main, "push", f"--force-with-lease={ref}:{there}", "origin", f":{ref}")
        removed["remote"] = branch


def cmd_clean(task: Task) -> dict:  # noqa: C901, PLR0912 - over the limit before the limit was set
    if task.record["status"] not in ("landed", "dropped", "answered"):
        raise LandError(
            f"the task is {task.record['status']!r}; only a landed, dropped or "
            "answered task loses its worktree"
        )
    removed: dict = {
        "worktree": False,
        "branch": None,
        "branch_left": None,
        "remote": None,
        "remote_left": None,
        "rebased": None,
    }
    # The worktree names its branch while it is there; after it, what `start` wrote
    # down does.
    branch = task.kept().get("branch")
    if (task.worktree / ".git").exists():
        branch = git(task.worktree, "branch", "--show-current") or branch
    # Before anything goes: a branch whose name the owner protected since is not deleted
    # here or on origin, and the refusal leaves the task as it was.
    protected = (
        protected_refusal(branch, task.settings["branch"], "deletes")
        if branch
        else None
    )
    if protected:
        raise LandError(
            f"{protected}, and the task's branch has that name; nothing was removed. "
            "The owner takes the name out of branch.protected and "
            f"`lem land clean {task.slug}` runs again, or removes the worktree himself "
            f"(`git -C {task.main} worktree remove {task.worktree}`) and keeps the "
            "branch",
        )
    if (task.worktree / ".git").exists():
        if branch:
            task.keep(branch=branch)
        # git refuses a worktree with changes or untracked files: they are someone's
        # work until the owner says otherwise.
        git(task.main, "worktree", "remove", str(task.worktree))
        removed["worktree"] = True
    if not branch or not git(task.main, "branch", "--list", branch):
        return {"task": task.slug, **removed}
    # `branch -d` judges by the checkout it runs in, which may be behind. The proof
    # wanted is that the base holds the branch's tip, so that is what is checked before
    # the branch goes.
    tip = git(task.main, "rev-parse", branch)
    on_base = (
        run(
            [
                "git",
                "-C",
                str(task.main),
                "merge-base",
                "--is-ancestor",
                tip,
                task.onto,
            ],
            check=False,
        ).returncode
        == 0
    )
    if task.record["status"] != "landed":
        # A dropped task's commits are on no other branch: its branch is the owner's to
        # delete. An answered task's may hold the test that reproduced its bug, which a
        # task started from its report can take. A branch with no commit of its own,
        # which the base (or the base branch here, when a remote is behind it) holds
        # whole, holds nothing of either, and goes.
        here = (
            run(
                [
                    "git",
                    "-C",
                    str(task.main),
                    "merge-base",
                    "--is-ancestor",
                    tip,
                    f"refs/heads/{task.base}",
                ],
                check=False,
            ).returncode
            == 0
        )
        if not (on_base or here):
            held = (
                "the dropped task's commits"
                if task.record["status"] == "dropped"
                else (
                    "the answered task's commits, the test that reproduced its bug "
                    "among them when it has one"
                )
            )
            removed["branch_left"] = (
                f"{branch} holds {held}; `git branch -D {branch}` deletes them"
            )
            return {"task": task.slug, **removed}
        git(task.main, "branch", "-D", branch)
        removed["branch"] = branch
        return {"task": task.slug, **removed}
    # A pull request that the forge merged as one commit, or as a merge commit, leaves
    # no such proof in git: there the proof is that the branch's tip is the commit the
    # forge merged, or, when the landing rebased the branch after Lem's last push, that
    # its tip holds that head's change (`after_push`).
    kept = task.kept()
    if not on_base and not (kept.get("merged") and tip == kept.get("merged_head")):
        after = ""
        if kept.get("merged"):
            merged = kept["merged_head"]

            def under(older: str, newer: str) -> bool:
                return (
                    run(
                        [
                            "git",
                            "-C",
                            str(task.main),
                            "merge-base",
                            "--is-ancestor",
                            older,
                            newer,
                        ],
                        check=False,
                    ).returncode
                    == 0
                )

            # The owner may have pressed "Update branch" on the forge and then merged as
            # one commit: the head the forge merged then holds the branch's tip and the
            # forge's merge of the base after it, and this checkout may not hold that
            # head at all.
            if under(merged, tip):
                after = (
                    f"; the forge merged {merged[:9]}, and the "
                    "branch has commits after it"
                )
            elif under(tip, merged):
                after = (
                    f"; the forge merged {merged[:9]}, which holds the tip of {branch} "
                    'and a commit made on the forge after it (its "Update branch"), '
                    "so the branch holds nothing that was not merged: "
                    f"`git branch -D {branch}` removes it"
                )
            elif (
                merged == kept.get("pushed")
                and run(
                    [
                        "git",
                        "-C",
                        str(task.main),
                        "cat-file",
                        "-e",
                        f"{merged}^{{commit}}",
                    ],
                    check=False,
                ).returncode
                == 0
            ):
                # The head Lem pushed last, which this checkout holds: the landing
                # rebased the branch after that push (a base that moved), and nothing
                # pushed the rebase. The forge's copy holds only what was merged and
                # goes either way; the local branch goes only when it holds the
                # same change.
                same, said = after_push(task, branch, tip, merged)
                drop_forge_copy(task, branch, removed)
                if same:
                    git(task.main, "branch", "-D", branch)
                    return {
                        "task": task.slug,
                        **removed,
                        "branch": branch,
                        "rebased": said,
                    }
                return {"task": task.slug, **removed, "branch_left": said}
            else:
                after = (
                    f"; the forge merged {merged[:9]}, which is not the tip of "
                    f"{branch} and which this checkout does not hold: a commit made on "
                    'the forge after the tip, as its "Update branch" makes. '
                    f"`git log {branch}` shows what the branch holds, and "
                    f"`git branch -D {branch}` removes it"
                )
        raise LandError(
            f"{task.onto} does not hold the tip of {branch}, so the branch stays{after}"
        )
    drop_forge_copy(task, branch, removed)
    git(task.main, "branch", "-D", branch)
    removed["branch"] = branch
    return {"task": task.slug, **removed}


def step(task: Task, args: argparse.Namespace) -> dict:  # noqa: C901, PLR0911 - over the limit before the limit was set
    """One step of a task's landing, which `main` runs under the task's step lock."""
    if args.command == "start":
        return cmd_start(task, conflicting=args.conflicting)
    if args.command == "base":
        return cmd_base(task)
    if args.command == "polish":
        return cmd_polish(task, done=args.done)
    if args.command == "checks":
        return cmd_checks(task)
    here = Path.cwd()
    if args.command == "read":
        return cmd_read(
            task,
            args.record and task_file(args.record, "--record", task.directory, here),
        )
    if args.command == "file":
        return cmd_file(task, again=args.again, same_said=args.same, new_said=args.new)
    if args.command == "propose":
        return cmd_propose(
            task, args.title, task_file(args.notes, "--notes", task.directory, here)
        )
    if args.command == "merge-review":
        if (args.tip or args.base) and not args.file:
            raise LandError(
                "--tip and --base go with --file: the tip and the base of the brief "
                "whose answer is written down"
            )
        return cmd_merge_review(
            task,
            args.file and task_file(args.file, "--file", task.directory, here),
            args.tip,
            args.base,
        )
    if args.command == "merge":
        return cmd_merge(
            task,
            args.by,
            args.message,
            args.via,
            standing=args.standing,
            expected=args.tip,
        )
    if args.command == "merged":
        return cmd_merged(task)
    return cmd_clean(task)


@lem_release.one_command
def main(argv: list[str] | None = None) -> None:  # noqa: PLR0915 - over the limit before the limit was set
    parser = argparse.ArgumentParser(
        prog="lem land",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="a directory inside the checkout (default: the current one)",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("base").add_argument("slug")
    checks = commands.add_parser("checks")
    checks.add_argument("slug")
    look = checks.add_mutually_exclusive_group()
    look.add_argument(
        "--status",
        action="store_true",
        help=(
            "whether the checks run now, for how long, and how their last run ended; "
            "starts nothing"
        ),
    )
    look.add_argument(
        "--stop",
        action="store_true",
        help=(
            "stop the checks that run now, and wait for their end; with none, "
            "nothing is stopped"
        ),
    )
    for name in ("merged", "clean"):
        commands.add_parser(name).add_argument("slug")
    start = commands.add_parser("start")
    start.add_argument("slug")
    start.add_argument(
        "--conflicting",
        action="store_true",
        help=(
            "for an open task the forge calls conflicting, "
            "with no merge of a task to name"
        ),
    )
    polish = commands.add_parser("polish")
    polish.add_argument("slug")
    polish.add_argument(
        "--done",
        action="store_true",
        help="after the polish builder: check what it committed, and log the pass",
    )
    read = commands.add_parser("read")
    read.add_argument("slug")
    read.add_argument(
        "--record",
        metavar="FILE",
        help=(
            "a JSON file that says what the review was and what it found; "
            "without it the step says what is due"
        ),
    )
    filing = commands.add_parser("file")
    filing.add_argument("slug")
    filing.add_argument(
        "--again",
        action="store_true",
        help="write once more each item that was filed and is gone from the tip",
    )
    filing.add_argument(
        "--same",
        action="append",
        default=[],
        metavar="rN.M=PATH",
        help=(
            "the defect rN.M is the one the item PATH of the backlog folder holds: "
            "kept as its open item, with no file of its own"
        ),
    )
    filing.add_argument(
        "--new",
        action="append",
        default=[],
        metavar="rN.M",
        help=(
            "the defect rN.M is a defect of its own, "
            "whatever item Jev named for it: filed"
        ),
    )
    alike = commands.add_parser(
        "alike",
        help=(
            "the items of the backlog that may hold the same defect as a finding, by "
            "Jev's read, before an agent files it"
        ),
    )
    alike.add_argument("slug")
    alike.add_argument(
        "--where", required=True, help="the finding's place, PATH or PATH:SYMBOL"
    )
    alike.add_argument("--title", required=True, help="the finding's title, one line")
    alike.add_argument(
        "--what",
        required=True,
        metavar="FILE",
        help="a file with the finding's run: what happens, with the input",
    )
    propose = commands.add_parser("propose")
    propose.add_argument("slug")
    propose.add_argument(
        "--title", required=True, help="the subject of the change, one semantic line"
    )
    propose.add_argument(
        "--notes",
        required=True,
        metavar="FILE",
        help=(
            "the notes of the pull request: decisions, what is left open, what is "
            "worth a look, what was filed, what was not done"
        ),
    )
    review = commands.add_parser(
        "merge-review",
        help=(
            "what the merge agent reads, in a brief file; with --file, "
            "its review written down"
        ),
    )
    review.add_argument("slug")
    review.add_argument(
        "--file",
        metavar="FILE",
        help="the merge agent's reply, its review with the verdict on its first line",
    )
    review.add_argument(
        "--tip",
        metavar="COMMIT",
        help=(
            "with --file: the `tip` the step printed with the brief the agent read; "
            "the answer of another proposal than the one now is refused"
        ),
    )
    review.add_argument(
        "--base",
        metavar="COMMIT",
        help=(
            "with --file: the `base` the step printed with the brief the agent read; "
            "the read covers that base and no later one"
        ),
    )
    merge = commands.add_parser("merge")
    merge.add_argument("slug")
    merge.add_argument(
        "--by",
        required=True,
        choices=BY,
        help=(
            "who merges: the owner's word, or the merge agent where the settings "
            "and the request allow it"
        ),
    )
    merge.add_argument(
        "--message",
        help='the subject of the one commit, when branch.history is "squash"',
    )
    merge.add_argument(
        "--via",
        choices=("session", "server"),
        default="session",
        help=(
            "who runs this call: a session (the default), or the board's server, which "
            "runs the merge agent's merge and the owner's merge from the board"
        ),
    )
    merge.add_argument(
        "--standing",
        action="store_true",
        help=(
            "with --by owner: the owner's merge that a moved base refused and that "
            "stood through the new landing or a read that said the move is safe; "
            "the board's server runs it"
        ),
    )
    merge.add_argument(
        "--tip",
        metavar="COMMIT",
        help=(
            "the whole commit the caller saw: the one the board's confirm step showed, "
            "the one the merge review read; any other proposal is refused, "
            "and nothing is merged or kept"
        ),
    )
    args = parser.parse_args(argv)
    try:
        task = Task(Path(args.repo), args.slug)
        # the release rule (lem_release), before the step reads or writes anything: the
        # end of a merge, the cleanup and the stop of the checks, which a drop runs
        # first, pass
        stopped = lem_release.check(
            task.directory,
            passes=args.command in ("merged", "clean")
            or (args.command == "checks" and args.stop),
        )
        if stopped:
            raise LandError(stopped)
        if args.command == "checks" and (args.status or args.stop):
            # a look and a stop take no lock: they are about the run that holds it
            result = checks_stop(task) if args.stop else checks_status(task)
        elif args.command == "alike":
            # a read that writes nothing, which a builder runs while it files by hand,
            # between two steps
            result = cmd_alike(
                task,
                args.where,
                args.title,
                task_file(args.what, "--what", task.directory, Path.cwd()),
            )
        else:
            with step_lock(task, args.command):
                result = step(task, args)
    except LandError as error:
        sys.exit(f"land.py: {error}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
