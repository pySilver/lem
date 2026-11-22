#!/usr/bin/env python3
"""Take one task's branch from `ready` to a pull request and to the base branch, one step at a time.

Nothing reaches the base branch without the machine checks and a review by an agent that did not
build it, and a task ends as a pull request on GitHub, the one way Lem lands; a fresh merge agent
reads each proposed task, and merges it or calls the owner.
Each step here is one command, prints JSON, and refuses with exit 1 and the reason when the step
may not run; nothing is retried and nothing is forced. Every step first asks `lem project
may-land` about the settings' base branch, so a protected branch is never reached, whoever asks.

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
    lem land file SLUG [--again]
                           file each defect a review saw outside the change as an item of the
                           backlog, and commit the items on the task's branch; a defect whose
                           place an item of the branch already names is that item
    lem land propose SLUG --title SUBJECT --notes FILE
                           push the branch and open its pull request on GitHub, or update the one
                           that is there: the state becomes `open`
    lem land merge-review SLUG
                           what the merge agent reads: its brief, merge-brief.md in the task
                           directory, with the facts of the task, and its seat
    lem land merge-review SLUG --file FILE --tip COMMIT
                           write down the merge agent's reply as merge-review.md: its verdict,
                           merge or call, and whether the owner is called; COMMIT is the `tip` the
                           brief named, and the reply of a brief of an earlier proposal is refused
    lem land merge SLUG --by owner|merger [--message SUBJECT] [--via session|server] [--standing] [--tip COMMIT]
                           merge the pull request through GitHub: the owner's word, or the merge
                           agent's where the settings and the request allow it; `--via server`
                           when the board's server runs it, `--standing` for the owner's merge
                           that a moved base refused and that stood through the new landing;
                           `--tip` the commit the caller saw, which must be the one proposed now
                           (the board's server always gives it)
    lem land merged SLUG   the owner merged the pull request on the forge: finish the bookkeeping;
                           or he closed it with no merge: the task is dropped
    lem land clean SLUG    remove the task's worktree and its branch after the merge

What each step keeps for the next is in `landing.json` in the task's directory: the task's
branch, the base it was rebased on, the commit and tree the checks passed on, each review, and
the pull request. Three steps log the start of what they start, so that the board's time card has
a start and an end for each: `polish` logs `polish.start` when a pass starts (not again for a
second start of the same pass), `checks` logs `gate.start` before its first command, and `read`
logs `review.start` once for the attempt that is due; `polish --done`, the checks' `gate.end`
and `read --record` are their ends. The checks keep the names their step had before it was called
the checks: the events `gate`, `gate.start` and `gate.end`, the folder `gate/` of a task's directory and
`gated` in `landing.json`, which open tasks and the board read.

A FILE of `read --record`, `propose --notes` and `merge-review --file` is read from the working
directory, and a relative one that is not there is read from the task's directory (`task_file`): a
task's session stands in the main checkout, and the files are the task directory's
(`reviews/review-1.json`, `notes.md`, `merge-answer-TIP.md`, the answer file `merge-review` names
for the tip of its brief).

One step of a task runs at a time. Every step here that names a task takes the task's one step
lock (`step.lock` in its directory) before anything else it does, and holds it until it ends,
however it ends; the first thing it writes there is its name, its process id and its start. A step
of the same task meanwhile exits 1 and names the step that holds the lock, since when and in which
process. While the checks hold it, a second `checks` is refused because they already run, and any
other step says that their end comes first, so that nothing is proposed, read or rebased while they
run. `checks --status` and `checks --stop` take no lock: they look at the file
and at the process it names, never at the lock, so a look never makes a real start fail. The
commands a step runs do not get the lock's file, so a server one of them left behind does not hold
it.

A run of the checks is two events: `gate.start` and one `gate.end`, however it ends, with `result`
(`passed` when the step keeps its result; `red` for a command of the checks that failed; `refused`
for a criterion's test that does not hold, a lowered bar, a command that changed the tree, or an
error of the step itself; `stopped` for a stop), `seconds` from its start, `tip`, `taken` (only for
a run that took the polish pass's result of the criteria's tests in place of its own run: the commit
that run was on, which logs no `task.red` of its own), and `say`, the one line for the owner, with
the slug, the result and the next step, and no question ("SLUG: the checks passed; the review runs,
nothing for you"). The step prints `say` in its JSON at every end after
`gate.start`, a red, refused or stopped one before its exit 1. The run clears the result an earlier
run kept before its first command, so a run cut off with no chance to clean up leaves none for its
tip. `--status` gives `running` (the step lock is held by `checks`), `since` and `seconds` of the
run, `last_seconds` (the `seconds` of the newest `gate.end` that passed, of any task, or null), and
`overdue` with its `say` when the run is more than three times as long as that one
(`OVERDUE_TIMES`), never against a last run of 0 seconds; and `ended`, the newest `gate.end` of the task with `resumed`, the line for a
session that did not start that run, which says its result as past and the next step as it is now.
`--stop` sends a term to the process the lock names, only while `checks` holds it, waits until that
run lets the lock go (`STOP_WAIT` at most), and says whether it stopped one (`stopped`).

A task on the fast track has no plan: its one acceptance criterion is `criteria.md` in the task directory
(`criteria.py` gives `small`), which the steps read in the plan's place. It is one task and never gets a polish
pass (`polish` refuses it): its builder files each defect it saw outside the change in the backlog
folder, in a commit of its own, and the pull request lists each file the branch adds there. It has
no reason for a lowered bar (the checks refuse one: a lowered bar takes the standard track), and its pull
request's text is short. One that is careful after all is not green, since it took the fast track
with no interview, read or plan.

The machine checks have no model in them. `checks` runs the settings' `checks.commands`, the whole
suite, which runs here one time and in no builder; then, when they all passed, each command of
`checks.serial`, the tests that two tasks cannot run at the same time (an end-to-end suite on fixed
ports, one database, a browser), each under the repository's one lock for them through `lem project serial`,
which waits while a builder or another check holds it; then `lem criteria red` (each criterion's tests pass on the branch and fail on the base commit), then the
bar. The checks take the polish pass's result of the criteria's tests in place of a run of their own
when the pass committed anything and `lem criteria inputs`, read after the commands, gives the five
inputs the pass's run reported: the tip, the base commit, the plan file, `checks.setup` and
`checks.serial`. That read of the criteria refuses the checks as a run of the tests would; the
result they keep then names the pass and its commit (`taken`), and the pull request says the tests
were taken from it and not run again. A commit after the pass, a rebase, a base branch that took in
a commit of the branch, another plan file or other settings, and the fast track, which has no pass,
make the checks run the tests themselves. A change lowers the bar when it adds a lint or type suppression, a skipped test or a mark
that runs one test alone, a test that runs again until it passes, deletes a test file or moves it
out of the tests, or leaves fewer assertions in one (counted by the words `assert` and `expect` on
the lines it adds and removes, in a test file and in every Rust file, where unit tests sit beside
the code). In the settings of a test runner or of coverage (`pyproject.toml`, `setup.cfg`, `pytest.ini`,
`tox.ini`, `package.json`, `.coveragerc`, `.nycrc`, `jest.config.*`, `vitest.config.*`) it lowers it
by a new `--deselect`, `-k "not ..."`, `--ignore`, `testPathIgnorePatterns`, rerun or retry, and by
a coverage threshold whose number went down or that is gone, there or on a command line of the
forge's workflows. Each existing test, snapshot and test configuration the change edits is listed
(`edited`), and the pull request names them: what a test expects is read by the review, since no
mark shows a changed expectation. A mark counts when the change leaves more of it in a file than the file had, so a
line that only moved is no new mark; a mark whose own text changed is a new one. A lowered bar passes only with a reason for that file under
`## The bar` in the task's plan, as `- PATH: REASON`. The marks looked for are those of Python, JavaScript and
TypeScript, Go, Rust, Java and Kotlin, and shell. A changed file of another language gets no such check, and the
result says which (`not_covered`). The size of the change, in files and changed lines, is counted, for the reviewer.

Each command of the checks runs in a process group of its own, with no standard input; the group is ended
when the command ends, so a server or a `sleep` it left behind does not outlive it, and when the
checks are stopped (a signal, an interrupt, `--stop`) the command that runs is ended with its group and the
step exits 1 with no result kept. The step's handler of a stop holds from its first line to its
last: a serial command's wrapper gets the time of its own cleanup before it is killed
(`SERIAL_GRACE`), and `lem criteria red` gets the stop and is waited for, so that it ends its tests
and removes its two worktrees itself. Checks with no command to run are refused, since checks that ran nothing show nothing; so is one
whose command changed a tracked file or made a commit on the branch, since its result is then
about another tree. A file its commands wrote that git neither tracks nor ignores (Python's bytecode
in a repository with no rule for it) is the run's output, and nothing of it lands: the step notes
what git does not know before its first command, removes after its last, or after a stop, each such
file that was not there before and each folder that leaves empty, names them in its output (`removed_untracked`)
and in one line of the last command's output file, and goes on. What the checks keep is the tip they
ran on and that tip's tree.

An `open` task lands again when its base moved: after a merge, Lem takes each task whose
pull request the forge calls conflicting through `start --conflicting`, `base`, the checks, the
review that is due and `propose`, which keeps its pull request; every other open task waits as it
is, and `merge` refuses it on a base that moved by any file since the checks ran (below), after
which it lands again the same way, with no `--conflicting`. `start` counts each new landing of an
open task (`relands` in `landing.json`, a `land.again` event with `count`), for the merge agent's
facts; nothing bounds the count. The pull request's text
and the state say in one line what happened ("rebased on main after the forge called it
conflicting; one conflict in shop/dates.py, resolved by a builder; the checks passed again"). A conflict that `base` meets is kept in `landing.json` with the tip before the rebase and
whether a review covered the change then; the builder that resolves it rebases the branch itself,
and the next `base` finds the rewritten commits by that tip, gives the polish pass's commits their
new names, and keeps the resolution. A review that saw the change and left no must-fix stands
through a rebase that git made with no conflict, also when the base changed a file of the change in
other lines: `base` carries it onto the new base, for a careful request too. A builder's resolution gets one read of what it
changed (`git range-diff` of the commits before and after the rebase), or the project's full set
for a careful request; that read is no round, and anything committed after the resolution is
reviewed as a change like any other.

`start` refuses a worktree on no branch: `propose` pushes the task's branch and `clean` deletes
it. Any number of tasks land at the same time, each in its own worktree and under its own step
lock: a feature waits for no other task's landing. Two `start`s at one moment take turns only to
read the tasks' states and write `landing`, under a lock of the state folder (`landing.lock`). With
no command of the checks it writes the task's state `blocked`, and a later `start` takes that task
back once the commands are there; each refusal on the way names the step out, also when its
worktree is gone.

What two landings share is the machine and the base branch, and each has one rule. The checks start
only while the machine's load average is below the start number the developer set for this machine
(`[load] start` in `machine.toml`, beside the owner's mark): a run waits before its first command,
logs `gate.wait` with the load and the number while it waits, and starts when the load is below the
number. Two runs that wait start at least `LOAD_SPACING` seconds apart, so that the load average
shows the first before the second reads it. A machine with no number has no gate; Lem picks none
(`lem doctor` gives the line that sets one). And Lem's own merge calls (`merge`) go one at a time,
under `merge.lock` of the state folder: a second call logs `merge.wait` with the task that holds
it, waits, and reads the base branch after it takes the lock, so that it meets the merge before it.
The commands of `checks.serial` still take the repository's one lock for them; nothing else does.

The checks are the main checkout's. One task may bring its own: when the main checkout's settings
name no command of the checks and the task's branch adds them to its `.lem/project.toml` (they are not on
the base commit), `start` and `checks` take those commands, as for the first task of a new
repository, "set up the checks"; the request is then not green, so that a person reads the
checks once. The rest of the branch's settings, its `checks.setup` too, are not read. A branch that changes checks the main checkout has is checked by the main
checkout's.

The polish pass comes after the task's own work and before the machine checks, so that the
review reads the code as it will merge. A fresh builder looks for a short fixed list (a comment
the change made false, a leftover, code that reads badly, a document the change made false, and
the defects outside the task that the lead's report and the interview named) and changes no
behavior. `polish` prints what that builder gets: the range of the task's own commits from the
base, the plan, the report, `outside.md` of the interview when the task has one, the backlog
folder, and the files the pass may not change. It keeps the tip the pass starts at; a second
start before `--done` keeps the same one. `polish --done` refuses a worktree with changes
nobody committed, a branch that no longer holds that tip, a pass that leaves a criterion's test
file or the plan other than it found them, and tests of the criteria that no longer pass on the branch and fail on
the base commit (`lem criteria red`, run when the pass committed anything). Otherwise it logs one
`polish` event (the tip before and after, the count of commits, the items it added to the
backlog folder), and keeps the result of its run of the criteria's tests, with the inputs that run
reported, for the checks. `checks` refuses a task on the standard track with no pass of this landing whose last commit the
tip holds, and any task whose pass started and is not done. Every task with a plan is on the
standard track: `criteria.py` refuses a plan that says `Size: small`, and so does every step here that
reads the criteria. The commits
that come after the pass, a repair, a fix of a review's findings, the items `file` writes, are
on top of it, and a rebase by `base` gives the pass's commits their new names; any other rewrite
of the branch asks for the pass again. The pass is one of this landing: `start` of a `ready`
task forgets it with the rest of `landing.json`.

A review comes before anything is proposed. There are three kinds: one read, which is the
review tool's smallest profile, for a short and simple change; a round of the review tool with
the profiles or lenses that fit the change; the project's full set. Which one a change gets, and which profiles fit it, is the
judgment of the agent that starts the review, from the diff and from what each profile is for:
no code and no list of words decides it. This script holds only the floor that no judgment goes
under: the full set for a careful request, and a round at the least for a plan of more than three
tasks and after a review that found a must-fix.

Whether a change is careful is judged against the project's topics (`flow.topics`, sentences of
what must never go wrong, read from the main checkout's settings like every setting here): no list
of paths decides it. A request is careful when the owner says so (that word in the task's brief),
when the plan says so (its `careful: yes` under its title, in its text now or in any commit of the
branch: a later commit does not take the yes back), when the newest review that answered says so,
or when the change edits `.lem/project.toml` at all. The last is the one rule this script matches
by itself, because the file is Lem's own and a task rarely edits it: its tables say, for every
later task, what is careful, what the checks run, who merges and where a task lands, and the reason
names each table whose values the change edits, that only its text changed, or that the file is
gone. A change that adds, changes or removes `.lem/project.local.toml` is careful by the same rule:
that file is one machine's own and is not to be tracked. The review is the look at the diff itself, by
an agent that did not build it: its record makes the call, and a careful call takes the full set.

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
     "outside": [{"where": PATH OR PATH:SYMBOL, "title": ONE LINE, "what": THE RUN THAT SHOWS IT}],
     "careful": true | false, "careful_why": ONE LINE}

`attempt`, `tip`, `kind`, `answered`, `careful` and `careful_why` are always there, but in the record of
an attempt that got no answer at all (`failed_attempt`: `answered` empty, each silent source with
what stopped it, no finding), which may leave the careful call out. `tip` is the
`tip` that `read` printed for the attempt: a record of another tip than the branch's now is refused,
since the attempt counts the records and a review of an earlier tip carries the same number. `careful` is the
review's own reading of the diff against each topic, and `careful_why` names the topic the change
reaches, or what was checked to say that it reaches none; `careful: true` comes with `kind: full`.
`left_out` is `[]` when `kind` is `full`: the full set is run whole. `bar` has one entry for each file in which
the change lowers the bar, and is left out otherwise. `outside` names each defect the review saw
that the base commit already has: it is no finding of the change, and it goes to the backlog.
`what` is the concrete run: what happens, with the input. A count in its place is refused, and
`0` reads as none.

A review in which a source did not answer is still a review: the record names who answered and
who did not. One in which nobody answered is none; it is started once more, and a second such
record sends the request on as not reviewed. A review is of a change, known by the content of
each file it touches, before and after: a rebase onto a base that left those files alone does
not undo it, nor does a rebase `base` made with no conflict (above), and a change of one space does. The one addition a review still covers is a new file
in the backlog folder (`docs/backlog`, its one place), when every file the review saw is as it saw
it: that is where the defects outside the change are filed after the review. An edit or a
deletion of an item that was there before is a change like any other.
Two rounds at most: after that the request is proposed as it is, green when the second round
left nothing open and not green otherwise. `attempt` in a record is the number `read` printed
for it, so a record that is sent twice is written down once.

No defect outside the change gets lost. `file` writes one item in the backlog folder
for each such defect of a review that has none yet, in the item format of `agents/lem-builder.md`
(`worth: later`, its `where`, the day it was filed; its title; its run and where it was seen),
commits the new items on the task's branch, one commit for each round, and keeps the path of
each defect's item in `landing.json`. A second run files nothing new. Those commits ask for no
check again: `read` and `propose` take the checks' result for a tip whose commits after the checked
one only add items whose paths `landing.json` keeps, and keep the result for that tip, so that
`merge` finds what it checks. An item written by hand is a commit like any other. `read` names
the defects that have no item yet (`to_file`), and `propose` refuses while one has none or while an item is
gone from the tip; the owner's "not wanted" is `worth: no` in the item, never its deletion.
The file name is the slug of the title. A file of that name that holds the same defect (the same
`where` and title, and its run word for word as paragraphs of the body, whatever else the body
says, such as the owner's reason for `worth: no`) is its item, and nothing is written twice; a
file that holds another takes the next name, with a suffix from the `where`, then a number. A
defect whose `where` is, word for word, the `where` of an item the branch adds to the backlog
folder that `file` did not write (the builder of a task on the fast track or the polish pass filed it before
the review) is that item too: it is named in the output (`named`), and nothing is written for it.
Only the `where` is compared, because the builder and the review describe one defect in their own
words; two defects of one place that a builder filed as one are one item, the price of the
review's not filing the same defect twice. `read` gives the reviewer those items (`filed`), so
that a defect the branch filed already is not reported again. One defect that two rounds
describe in other words gets two items: an extra item costs a merge of two items by hand, and
a lost one costs the defect. The review is asked to repeat an earlier round's words for a defect
it sees again.

`propose` writes the text of the pull request to `pr.md` in the task's directory, from what the
steps kept, from the record of the task's decisions (`lem decisions list`) and from the notes
file, whose headings it checks. The text opens with green or not green, in one wording for the
fast track and the standard track. Green says that the
checks passed with the bar where it was, a review with at least one source left no
must-fix, no criterion changed during the build, and no decision past the personas was taken
without an answer of the owner's. A criterion changed, added or removed after the newest approval is one line each, from its
record (`lem decisions criterion`), with what it was, what it is and why. The text lists every
criterion change of the task, under every approval; one that a later approval of the owner's took over says
so and is no cause of not green, since that approval made it the owner's. A lowered bar is not
green with a reason either: its line holds the builder's reason and what the review said of it. A
decision of the ladder that went past the personas (`by: dialectic`, `by: experts`) or that no
level settled (`unsettled`) is a line of its own: the ladder decides every choice of the build at
once, with the owner there or away, and he reads its pick here. So are criteria approved while the
task ran without him (`by: alone`) that no approval of his followed. A decision the gate or the
personas settled is no cause of not green: its line says the gate's cite, or how many personas
voted for it and in how many model families. Nor is the owner's help on a breaker
(`--by owner --breaker N`), or a criterion change that it led to: his decision made it his. Each
time the circuit breaker stopped the build is a line before the decisions, with its cause and the
decision of his that settled it. A task that ran without the owner (his `lem project owner away`, a night's
mark) says so in the line after green or not green, with when and the words; nothing else about it
is a cause of not green.
Each reason a request is not
green stands before everything else, one line each; each decision of the record is one line
before the notes. `propose` is refused while a breaker of the task waits for the owner. A plan
that calls itself careful (`careful: yes`) or has more than three tasks was talked through by
its defender and the reviewer in the plan talk's companion before any code, and the defender
wrote it down as one `plan.talk` event in the log `project.py` keeps: `propose` refuses such a
request with none, and the text's checks hold one line from the newest, with who argued the plan
with its defender, the turns (with the bound of its rules, when the talk went over it), the
positions settled and left open, and every other count the event holds, in words where Lem
knows the count (`TALK_SAYS`) and by its name where it does not. A talk is a step before the build, so a request
that is careful only by the owner's later word, by its review or by its edit of the settings gets
the full set and no talk; it is not asked for one, and its checks say in words that it had none
and why, which is no cause of not green. A careful request says so in the line after green or not
green, with each reason, and its checks hold the call in one line, with the newest review's call
and reason beside it. A request that is not careful gets
neither line. The checks also hold one line on the personas' read of the criteria, from the
newest `criteria.read` event (`lem project log` gives its form): how many of the personas asked
answered, in which model families, who did not answer and why, how many criteria they flagged,
whether the families split, and when the owner approved them (`lem criteria approve`), or that the
build started with no wait for the owner. When the criteria waited for the owner's yes (the newest
`held` state with a line `the criteria wait for the owner`, other than the fast track's builder's
"the small change is a full change"), the line says when the wait began and how it ended: the first
approval after it, the owner's or one made while the task ran without the owner, with its time, and
a later approval of the owner's on its own.
When the criteria the read names by their digest are not the plan's (which the checks make the expected
ones), one more line says that they changed after the read, by a later approval of the owner's or by
a change of the build, and that the change was not read; that line is no cause of not green. A
task whose scout read the code has one line that says the criteria were written from its facts.
The text names no file of the task directory: the pull request is read on the forge, where no
path of this machine leads anywhere.
A request of the type fix whose investigation found its cause has one more line with that cause
and its place, from the newest `investigation` event; a question's has none.
`propose` refuses a task on the standard track with no `criteria.read`, unless the owner skipped the read: that word
of the owner's, which Lem asks for only when every criterion names only the developer, is a decision
of the owner's with the two texts of `READ_SKIP`, and it counts only with a later approval of
the owner's, both before the first state that names a lead. A word or an approval after a lead started belongs to the standard
track from a complete request, where the read always runs, and is refused. Then the checks say "the criteria: not read by the
personas, on the owner's word (DATE); the owner approved them", which is no cause of not green, since the
decision was the owner's. It also refuses one whose newest read flagged a criterion or
showed a split between the families with no approval of the owner's at or after it; the lead's
freeze of a read (`lem criteria approve --read`) is no approval of the owner's. A complete request
that someone else wrote (the line `request by: someone else` in the task's brief or in a block of its
state) needs that approval after the newest read even when nobody was confused, since nobody at the
terminal read the request. In both cases an approval made while the task ran without the owner
(`approve --alone`, `by: alone`) at or after the read lets it be proposed, not green. A read in which nobody
answered is written down too: `propose` refuses while the newest one is the first such read in a
row, so that the read is started once more, and after the second in a row the request is not
green, with "the criteria were not read" first, and its checks say so in place of the read's line. A
change the review calls careful and the plan did not is a lesson about the plan's call: `read
--record` writes one `careful.missed` event with the round and the review's reason, the first time
a review finds it, for the retro. `propose` pushes the task's branch and opens the pull request
on GitHub with the `gh` command; a second run updates it. The `proposed` event is written after
that step: a proposal that the push or GitHub refused is none. A repository whose origin is not on
GitHub, or that has none, is refused before anything is written, with the line that points origin
at GitHub: a GitHub pull request is the one way a task lands.

The merge agent reads every proposed task, the fast track's too, after `propose`. `merge-review`
with no record writes its brief, `merge-brief.md` in the task directory: the line that names
`prompts/merge.md`, and the facts as JSON (the pull request, the range, the files of the task
directory there are, the reviews, green or why not, why careful, `branch.land`, `owner_merges`, the
reason the owner merges whatever the agent finds, or null, and `time`, the task's seconds from its
first event to its first proposal against the median of the earlier tasks of its track in the
event log). It prints the brief, the answer file the agent's reply goes to, and the seat that
starts it, `seats.merger` as `lem project show` resolves it. The agent changes nothing. Its reply
opens with its verdict, `Verdict: merge.` or `Verdict: call.`; `merge-review --file FILE` refuses one
that does not, writes the reply as `merge-review.md`, keeps `merge_review` in `landing.json` (the
proposed tip, the verdict, `calls`, `why`, the seat as `by`, and the time) and logs `merge.review`
with the same. `calls` is true for the verdict `call`, and for a `merge` that `owner_merges` overrules:
the owner is called, and "Waits for you" shows "Read the merge review". A review of an earlier tip
counts for nothing, unless `propose` carried it onto the tip after a new landing (below). The facts
hold `relands` too, how many times the proposal landed again.

`merged` asks GitHub about a pull request the owner may have merged or closed there. A merged one
finishes as a landing does. A closed one with no merge ends the task: its state becomes `dropped`
with the line "the pull request was closed on the forge", so nothing of it waits and nobody cleans
it by hand; `clean` then removes the worktree, and the branch keeps its commits, with how to delete
it. A task that goes on after all is a new request. One that is still open is "not merged yet"
(exit 1), and `merged` keeps what the forge said of it, its mergeable state on its head
(`forge` in `landing.json`), so that `lem project waiting` says whether it conflicts with the base.

`merge` is the one route to the base branch, the owner's and the merge agent's alike: `merge --by
owner` is his word (the board's merge and his `/lem land` run it), and `merge --by merger` is the merge
agent's, after its review, which the board's server runs (`--via server`) once `merge-review` kept the
verdict `merge` with no call: the agent only writes its review, and no session is told to run it.
Both run under the merge lock and read the base after they take it, and `merge.start` says who merges
(`by`) and who ran the call (`via`, `session` unless the server says `server`), as `merged_by` in
`landing.json` does after a merge. `--by
merger` is refused where the settings' `branch.land` is `owner`, for a careful request, for one that
is not green (one that is not reviewed among them), for one whose newest review that answered made no
careful call, and with no merge review of the proposed tip whose verdict is `merge`. A task that ran
without the owner is merged as any other. The pull request is merged through GitHub, so its own rules
hold: a merge GitHub refuses keeps its line as `merge_refused` in `landing.json` (`from: github`) and a
`merge.refused` event, for the row that waits for the owner, and the step exits 1 with that line.
`merged` is for one the owner merged on GitHub. What lands is the tree the checks passed on: when the
tip is another tree, or the base moved by any file after the checks ran (`changed` from the base the
checks ran on to the base now: every file, not only those the checks read), `merge` refuses and says
which steps run again.

A refusal by Lem's own rules under the lock (`Refusal`, with its `kind`: `rule` for one of the merge
agent's rules, `tip` for a tip or a head that is not the one proposed and checked, `base` for the
moved base) keeps its line the same way, with `from: lem` and the `kind`, for every refusal of the
merge agent's merge and for the owner's when the base moved (`kept_refusal`): the server tries that
tip no more and wakes the task's session with `lem: SLUG refused`. A git or `gh` call that failed is
no refusal of the tip and is not kept; the next try runs it again. After a base refusal the session
lands the task again. A rebase with no conflict carries the review (above) and, with it, what was
said of the tip at the merge (`rebase_carried`, from the tip before the rebase to the one after it);
`propose` of that tip, with no commit after the rebase, carries the merge agent's review onto it,
with its call of the owner as the rules say now, and logs it as a `merge.review` with `carried`, so
that the server merges it with no second read. The owner's merge that the base refused
(`owner_tap`) stands the same way, while the reasons the request is not green are the ones he saw:
`propose` logs `merge.stands`, and the server runs `merge --by owner --via server --standing`, which
`merge.start` and `merged_by` record as made `after: a re-check`. A commit after the rebase, a
conflict or other reasons end it, and `propose` says why (`owner_merge`).

A step that was cut off is run again; a merge that GitHub already holds only finishes the bookkeeping.
`clean` knows the branch from `landing.json`, so it finds it after the worktree is gone. It
takes a landed, a dropped or an answered task. The branch of the last two goes when the base
holds it whole, and stays when it has commits of its own, with what it holds and how to delete
it. `landing.json`, `pr.md`, `merge-review.md` and each item of the backlog are written whole, through
a new file that takes the old one's place, so that a run cut off in the middle leaves no half of one.

After a merge the checkout that holds the base branch is fast-forwarded when it is clean, and left
alone with a note when it is not. The base branch is never pushed to and a ref is never moved behind
a checkout's back. The task's own branch on GitHub is the one ref pushed with force, and with a lease that names the commit the
push may replace: the one Lem pushed last (`pushed` in `landing.json`), or a head of origin's whose
commits the branch took in (`taken`), or no branch at all for a first push. Origin is asked with
`ls-remote` before `base` rebases and before `propose` pushes, never through the remote-tracking
branch, which any plain fetch moves: a commit there that Lem did not push and the branch does not
hold (a teammate's suggestion) stops the step with each such commit named, and the way on is to
pull it into the task's worktree, after which it is part of the change, with its checks and a read.
A pull request on the task's branch name is taken as the task's own only when its head is the
commit Lem pushed; any other is somebody's, and `propose` refuses with its number and author.
"""

import sys

if sys.version_info < (3, 11):
    # an old python3 must still load this file, so that it can say what it needs and not a traceback
    sys.exit(f"land.py: Lem needs Python 3.11 or newer, and this python3 is {sys.version.split()[0]}; put a newer one first on PATH, or run this file with it")

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import re
import shutil
import signal
import statistics
import subprocess
import tempfile
import tomllib
import time
from datetime import date, datetime, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
# How this script calls a sibling: in this process, as one command of it.
sys.dont_write_bytecode = True
sys.path.insert(0, str(SCRIPTS))
import lem_sibling  # noqa: E402
import lem_state  # noqa: E402
import lem_tokens  # noqa: E402

# Who merges: the owner's word, or the merge agent, where the settings and the request allow it.
BY = ("owner", "merger")
# A GitHub remote, as the repository writes its address: a task ends as a pull request there.
GITHUB = re.compile(r"(https://|ssh://git@|git@)github\.com[:/]")
# The merge agent's verdict, the first line of its review: it merges, or it calls the owner.
VERDICT = re.compile(r"Verdict:\s*(merge|call)\b", re.IGNORECASE)
# The review a change gets, from the least to the most: one read by one agent, a round of the
# project's review tool with the profiles that fit the change, the project's full set.
KINDS = ("read", "round", "full")
KIND_SAYS = {"read": "one read", "round": "a review round with the profiles that fit", "full": "the project's full set"}
# The line Lem writes into a task's brief when the owner says that the task is careful.
OVERRULED = "careful: the owner says so"
# The line of a task's brief, or of a block of its state, that says someone else wrote its complete request.
SOMEONE_ELSE = "request by: someone else"
# The state line `start` writes when the project has no command of its checks; a task blocked with
# it is the one `start` takes back once the commands are there.
NO_GATE = "the project has no command in its checks"
# The steps that take a tip from the start to a proposal, which a refusal of `land` names when the
# tip, the base or the tree is not the one on record.
AGAIN = "run `lem land start`, `lem land base`, `lem land checks`, `lem land read` and `lem land propose` again (a rebase with no conflict keeps the review)"
# How many changed lines one reader takes as one piece; a larger change is read task by task, in
# the plan's own cuts. A guess (2026-11-15), not a measurement.
READ_AT = 800
# A plan of more tasks than this is large: it gets a round at the least, and a plan talk before
# any code. The three-touches plan's own line (2026-11-15), not a measurement.
LARGE_AFTER = 3
# The plan's own call whether the task is careful, as `stages/plan.md` step 2 has the lead write it:
# one line under the plan's title, before its first `##` heading. A line further down is no call:
# the plan talk's record or a fenced block may quote one.
PLAN_CALL = re.compile(r"(?mi)^careful:\s*(yes|no)\b")
# Lem's own settings: what must never go wrong, what the checks run, who merges, where a task lands.
# Any edit of the file is careful by this script, not by a judgment: the file is Lem's, a task
# rarely edits it, and every table of it guards something for every later task (audit A1,
# 2026-11-17: a branch that set `branch.land` to "agent" got one read and a green pull request).
SETTINGS_FILE = ".lem/project.toml"
# One machine's own settings (`[seats]`, `[corrections]` and `[naps]`, project.py's LOCAL_TABLES),
# untracked by design and read from the main checkout. A branch that commits it, or changes or
# removes a tracked copy, is careful by this script too: a green request and an agent's merge would
# make one machine's choices every machine's (audit N5, 2026-11-17: a branch that committed it with `git add -f` got both).
LOCAL_SETTINGS_FILE = ".lem/project.local.toml"
# What a decision of the build did to its criterion, as a line of the pull request says it.
CHANGE_HOW = {"changed": "changed", "added": "was added", "removed": "was removed"}
# The form of the one event that records the personas' read of a task's criteria.
READ_FORM = "`by=lem|lead asked:=N answered:=N families:='[...]' silent:='[...]' criteria:=N flagged:=N split:=true|false digest=DIGEST`"
# The owner's word that the personas do not read the criteria, which Lem asks for only when every
# criterion names only the developer (`stages/interview.md`,
# step 5): one decision of his that `decisions.py log --by owner` writes, known by these two texts
# word for word.
READ_SKIP = {"what": "the personas' read of the criteria", "chose": "no read: the criteria name only the developer"}
# The state line of a task whose criteria wait for the owner's yes, as `project.py` writes it
# (`CRITERIA_WAIT` there), and the one such line that is no wait for his yes: the fast track's
# builder found a full change, and that task goes to an interview (`FAST_GREW` there). Copies, since
# a stand-in may take project.py's place (`project_now`).
CRITERIA_WAIT = "the criteria wait for the owner"
FAST_GREW = re.compile(r"\bthe small change is a full change$")
# The approvals that end such a wait: the owner's, or one made while the task ran without him.
WAIT_ENDS = ("owner", "alone")
# How many model families read the criteria, in the words of the pull request.
FAMILIES = {1: "one model family", 2: "two model families"}
# The form of the one event that records a plan talk, as `talk_form` in `project.py` checks it.
TALK_FORM = "reviewer=AGENT turns:=N questions:=N settled:=N open:=N repaired:=N design:=N unargued:=N root:=N layer:=N shared:=N"
# The counts of a plan talk after its turns and positions, in the words of the pull request, one
# form for one and one for more. A count the event holds and this table does not is shown by its name.
TALK_SAYS = {
    "questions": ("question in the reviewer's first list", "questions in the reviewer's first list"),
    "repaired": ("repaired by the defender", "repaired by the defender"),
    "design": ("of the open ones a design choice", "of the open ones a design choice"),
    "unargued": ("raised after the list and not argued", "raised after the list and not argued"),
    "root": ("repaired at the cause", "repaired at the cause"),
    "layer": ("layer over a cited decision", "layers over a cited decision"),
    "shared": ("decision two questions named", "decisions two questions named"),
}
# What every event has and the talk's line says first, so it is no count after the positions; and the
# bound of turns its rules give, which `project.py log` adds and the line names only when the talk went over it.
TALK_FIRST = ("ts", "event", "task", "reviewer", "turns", "settled", "open", "bound")
# Who took a decision of the record, as the text of a pull request names them.
TAKEN_BY = {"lead": "the lead", "gate": "the gate", "personas": "the personas", "dialectic": "the dialectic", "owner": "the owner", "lem": "Lem", "experts": "the experts"}
# The two causes of the circuit breaker, as a line of the pull request says them (`decisions.py` CAUSES).
BREAKER_SAYS = {"irreversible": "the next step could not be reversed by a later no", "criteria": "no option of the ladder kept the approved criteria"}
# The levels of the ladder whose decision, taken without the owner, is never green: past the personas.
PAST_PERSONAS = ("dialectic", "experts")
# The name of each track, by the word of the `Size:` line that the criteria keep.
TRACKS = {"small": "fast", "full": "standard"}
# The first line of a green pull request, one wording for the fast track and the standard track.
GREEN = "**Green.** The checks passed with the bar where it was, the review left no must-fix, no criterion changed, and no decision past the personas was taken without an answer."
# What a review names of each defect it saw outside the change.
DEFECT = ("where", "title", "what")
# The longest file name an item of the backlog gets from its title, before `.md`. A guess
# (2026-11-16), not a measurement: long enough for a title of a dozen words.
SLUG_AT = 80
# The headings the notes of a pull request hold, in this order: what only the one who read the
# task's report can say.
NOTES = ("## Decisions", "## Left open", "## Worth a look", "## Filed in the backlog", "## Not done")
# A document may quote a mark of the bar, the plan's own reason for one too: no mark is looked for in these.
DOCS = (".md", ".rst", ".adoc")
# The marks by which a change lowers the bar, for the languages whose tools read them. Chosen by
# the session that built this check (2026-11-15) from those tools' own syntax, and the focus marks
# of JavaScript's runners (`.only`, `fit`, `fdescribe`), which run one test alone and so leave the
# others out, after an audit of the bar (2026-11-17); not measured. A mark that a call's "(" follows
# is looked for with that "(" and named without it, so a refusal says `it.only`, never `it.only(`.
# The marks of a test that runs again until it passes came after a probe of the bar passed eight
# ways of weakening a test unseen (audit T-F2, 2026-11-17).
BAR = {
    (".py",): (r"#\s*noqa", r"#\s*type:\s*ignore", r"#\s*pyright:\s*ignore", r"#\s*pylint:\s*disable", r"#\s*nosec", r"\bpytest\.mark\.(skip|xfail)", r"\bunittest\.skip", r"\bpytest\.skip(?=\()",
               r"\bpytest\.mark\.(flaky|retry)\b", r"^\s*@flaky\b"),
    (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"): (r"eslint-disable", r"@ts-ignore", r"@ts-expect-error", r"@ts-nocheck", r"\b(it|test|describe)\.(skip|todo|only)(?=\()", r"\bx(it|test|describe)(?=\()", r"\bf(it|describe)(?=\()",
                                                     r"\bjest\.retryTimes(?=\()", r"\bthis\.retries(?=\()"),
    (".go",): (r"//\s*nolint", r"\bt\.Skip(f|Now)?(?=\()"),
    (".rs",): (r"#!?\[allow\(", r"#\[ignore\b"),
    (".java", ".kt"): (r"@Disabled", r"@Ignore", r"@SuppressWarnings"),
    (".sh", ".bash"): (r"#\s*shellcheck\s+disable",),
}
# The settings files of a test runner or of coverage, by name: their marks leave tests out, or run
# a failing test again until it passes, for the whole suite at once.
TEST_CONFIG = re.compile(r"(^|/)(pyproject\.toml|setup\.cfg|pytest\.ini|tox\.ini|package\.json|\.coveragerc|\.nycrc(\.json|\.ya?ml)?|(jest|vitest)\.config\.[A-Za-z0-9.]+)$")
TEST_CONFIG_MARKS = (r"--deselect\b", r"-k[\s=]+[\"']?not\b", r"--ignore(-glob)?\b", r"\btestPathIgnorePatterns\b", r"(--)?\breruns\b", r"\bretries\b", r"\bretryTimes\b", r"\bflaky\b")
# A coverage threshold, as a runner's settings or a command line write it: its name and its number.
# The bar is lower when a number of one name went down, or the name is gone, anywhere in those files.
THRESHOLD = re.compile(r"(fail_under|fail-under|cov-fail-under)[\s\"']*[=:\s][\s\"']*([0-9]+(?:\.[0-9]+)?)|[\"']?\b(lines|branches|functions|statements)[\"']?\s*:\s*([0-9]+(?:\.[0-9]+)?)")
# The forge's workflows: a coverage threshold on a command line there counts, and an edit of one is
# an edit of a test configuration.
WORKFLOW = re.compile(r"(^|/)\.github/workflows/[^/]+\.ya?ml$")
# A file a test compares its output with, written once and read by the test.
SNAPSHOT = re.compile(r"(^|/)__snapshots__/|\.snap$|\.ambr$|\.approved\.[A-Za-z0-9]+$")
# Files that are neither code nor documentation: no language's marks apply, and none is missed.
DATA = (".txt", ".json", ".toml", ".yaml", ".yml", ".lock", ".cfg", ".ini", ".csv", ".tsv", ".svg", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".html", ".css", ".xml", "")
# An assertion, as far as a line shows one: the word a test framework uses for it.
ASSERTS = re.compile(r"\b(assert|expect)", re.IGNORECASE)
# A test file, by its place or its name.
TEST_FILE = re.compile(r"(^|/)(tests?|spec|specs|__tests__)/|(^|/)test_[^/]*$|_test\.[A-Za-z0-9]+$|\.(test|spec)\.[A-Za-z0-9]+$")
# The languages that keep unit tests in the module they test: there every file's assertions count.
INLINE_TESTS = (".rs",)


class LandError(Exception):
    pass


class ForgeSaid(LandError):
    """What GitHub said of a merge Lem asked for: its refusal, whose line `merge_locked` has kept
    already, or a merge it took and has not made yet, which is no refusal."""


class Refusal(LandError):
    """A merge that one of Lem's own rules refuses, with the rule's kind (`REFUSALS`). Only such a
    refusal is kept for the tip (`cmd_merge`): a git or `gh` call that failed is no word on the tip,
    and the next try runs it again."""

    def __init__(self, kind: str, said: str) -> None:
        super().__init__(said)
        self.kind = kind


# The kinds of a merge that Lem's rules refuse: one of the merge agent's rules (`merger_refusal`), a
# tip that is not the one proposed and checked (or a pull request whose base on GitHub is not the
# task's), and a base that moved after the checks ran.
REFUSALS = ("rule", "tip", "base")


def run(args: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    ran = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)
    if check and ran.returncode != 0:
        raise LandError(f"{' '.join(args[:4])} failed: {(ran.stderr or ran.stdout).strip()}")
    return ran


def git(where: Path, *args: str, check: bool = True) -> str:
    return run(["git", "-C", str(where), *args], check=check).stdout.strip()


def write_whole(file: Path, text: str) -> None:
    """Write a file whole or not at all: a run cut off in the middle leaves the old file, never half of one.
    The new file's name holds this process's id, so two writers of one file at one moment never write one new file."""
    fresh = file.with_name(f"{file.name}.{os.getpid()}.new")
    fresh.write_text(text, encoding="utf-8")
    fresh.replace(file)


def script(name: str, repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    """One command of a sibling script, so this one reads a repository the way every stage does."""
    ran = lem_sibling.run(SCRIPTS / name, repo, *args)
    if check and ran.returncode != 0:
        raise LandError(ran.stderr.strip().removeprefix(f"{name}: ") or f"{name} {args[0]} failed")
    # a line project.py writes on stderr when it succeeds (the settings read from the base branch) is this script's to say too
    if ran.returncode == 0 and ran.stderr:
        sys.stderr.write(ran.stderr)
    return ran


def project_now(repo: Path) -> tuple[dict, list[dict], Path]:
    """What a landing reads of the repository before its step: the main checkout's settings, every
    task as the state files say now, and the state folder. Refused before anything else: settings
    that do not read, no settings file, and what `may-land` refuses (a protected branch, a missing
    base, a wrong target). The settings are loaded once and handed to the functions of `project.py`
    that need them; nothing git answered is kept past this one call."""
    path = SCRIPTS / "project.py"
    if not lem_sibling.in_form(path):
        # a stand-in in project.py's place (a test's copy of the scripts) answers each command as a process
        settings = json.loads(script("project.py", repo, "show").stdout)
        if Path(settings["root"]).resolve() != Path(settings["main"]).resolve():
            settings = json.loads(script("project.py", Path(settings["main"]), "show").stdout)
        if settings["settings"] is None:
            raise LandError("this repository has no .lem/project.toml; `/lem init` writes it")
        script("project.py", repo, "may-land", str(settings["branch"]["base"]))
        return settings, json.loads(script("project.py", repo, "tasks").stdout), Path(script("project.py", repo, "state-dir").stdout.strip())
    project = lem_sibling.module(path)
    try:
        root = project.repo_root(repo)
        here = project.load(root)
        settings = here
        if root.resolve() != Path(here["main"]).resolve():
            # Run from a task's worktree, the landing still reads the main checkout's settings: the
            # branch it lands does not get to choose its checks or what is careful. The worktree's own
            # load stays, for what only it answers: it refuses a branch whose settings do not read,
            # and `may-land` and the tasks' tracker read the branch's tables there, as their commands do.
            settings = project.load(Path(here["main"]))
        if settings["settings"] is None:
            raise LandError("this repository has no .lem/project.toml; `/lem init` writes it")
        project.may_land(here, str(settings["branch"]["base"]))
        return settings, project.read_tasks(root, here), project.state_root(root)
    except project.SettingsError as error:
        raise LandError(str(error)) from error


class Task:
    """One task as the landing needs it: its settings, its worktree, its branch and what it kept."""

    def __init__(self, repo: Path, slug: str) -> None:
        self.settings, tasks, state = project_now(repo)
        self.slug = slug
        self.base = self.settings["branch"]["base"]
        self.repo = repo
        self.read_states(tasks)
        self.directory = state / "tasks" / slug
        # -z: a NUL ends each field and an empty field ends each worktree, so a path with a line break stays whole
        listed = run(["git", "-C", str(repo), "worktree", "list", "--porcelain", "-z"]).stdout
        entries = [block.split("\0") for block in listed.split("\0\0") if block.strip("\0")]
        self.main = Path(self.settings["main"])
        relative = Path(self.settings["places"]["worktrees"]["path"]).relative_to(Path(self.settings["root"]).resolve())
        self.worktree = self.main / relative / slug
        # the checkout that holds the base branch, when one does
        self.base_checkout = next(
            (Path(entry[0].removeprefix("worktree ")) for entry in entries if f"branch refs/heads/{self.base}" in entry), None,
        )
        self.remote = git(self.main, "remote", "get-url", "origin", check=False) != ""
        self.onto = f"origin/{self.base}" if self.remote else str(self.base)
        self.kept_file = self.directory / "landing.json"
        self.recorded: list[dict] | None = None
        self.criteria: dict | None = None
        self.plan_said: bool | None = None
        self.branch_gate: list[str] | None = None
        # The address as the repository has it, before any rewrite of it: the forge is known by its host.
        # A task ends as a GitHub pull request, the one way Lem lands; `propose` refuses another remote.
        url = git(self.main, "config", "--get", "remote.origin.url", check=False)
        self.forge = "github" if GITHUB.match(url) else None

    def read_states(self, tasks: list[dict] | None = None) -> None:
        """This task's record, as the state files say now."""
        tasks = tasks if tasks is not None else json.loads(script("project.py", self.repo, "tasks").stdout)
        self.record = next((task for task in tasks if task["slug"] == self.slug), None)
        if self.record is None:
            raise LandError(f"no task {self.slug!r}; the tasks are: {', '.join(task['slug'] for task in tasks) or 'none yet'}")

    def need_worktree(self) -> None:
        if not (self.worktree / ".git").exists():
            branch = self.kept().get("branch") or "BRANCH"
            raise LandError(
                f"the task has no worktree at {self.worktree}: `git -C {self.main} worktree prune` forgets a worktree whose folder was removed by hand, "
                f"and `git -C {self.main} worktree add {self.worktree} {branch}` puts the task's branch back in it, then this step runs again; "
                f"when the work is gone with it, `lem project state {self.slug} dropped \"WHY\"` ends the task",
            )
        dirty = git(self.worktree, "status", "--porcelain")
        if dirty:
            raise LandError(f"the worktree has changes nobody committed:\n{dirty}\ncommit them or remove them before this step")

    def blocked_by_start(self) -> bool:
        """Whether the task is `blocked` by `start` itself, for want of a command of the checks."""
        block = self.record.get("state") or ""
        return self.record["status"] == "blocked" and block.splitlines()[0].endswith(f" blocked: {NO_GATE}")

    def need_landing(self) -> None:
        if self.record["status"] != "landing":
            if self.record["status"] in ("ready", "open") or self.blocked_by_start():
                raise LandError(f"the task is {self.record['status']!r}, not `landing`; `lem land start {self.slug}` comes first")
            raise LandError(f"the task is {self.record['status']!r}, not `landing`: `lem land start` takes a `ready` or an `open` task into it, and this one is neither")

    def kept(self) -> dict:
        if not self.kept_file.is_file():
            return {}
        try:
            return json.loads(self.kept_file.read_text(encoding="utf-8"))
        except ValueError as error:
            raise LandError(
                f"{self.kept_file} does not read as JSON ({error}); land.py writes it whole, so something else wrote it. "
                f"Move it aside, then `lem project state {self.slug} ready --start-over \"WHY\"` and `lem land start {self.slug}` start the landing over: "
                "its checks and its review run again, and `propose` finds a pull request the task has on the forge",
            ) from error

    def keep(self, **values: object) -> None:
        write_whole(self.kept_file, json.dumps({**self.kept(), **values}, indent=2) + "\n")

    def state(self, status: str, *lines: str) -> None:
        script("project.py", self.worktree if self.worktree.exists() else self.main, "state", self.slug, status, *lines)

    def logged(self) -> list[dict]:
        """Each decision and breaker of the task as it stands, through the one script that writes them."""
        if self.recorded is None:
            self.recorded = json.loads(script("decisions.py", self.main, "list", self.slug).stdout)
        return self.recorded

    def decisions(self) -> list[dict]:
        """Each decision of the task: taken by a level of the ladder, by the lead, or by the owner."""
        return [decision for decision in self.logged() if decision["kind"] == "taken"]

    def breakers(self) -> list[dict]:
        """Each time the circuit breaker stopped the task, with whether the owner's help settled it."""
        return [breaker for breaker in self.logged() if breaker["kind"] == "breaker"]

    def gate(self) -> tuple[list[str], bool]:
        """The commands of this task's checks, and whether its own branch brought them: the main
        checkout's, unless those are none and the branch adds some to its `.lem/project.toml`."""
        own = self.settings["checks"]["commands"]
        if own or not (self.worktree / ".git").exists():
            return own, False
        if self.branch_gate is None:
            # asked twice by one proposal (the text and its reasons), and kept: no step writes the branch's settings
            self.branch_gate = json.loads(script("project.py", self.worktree, "show").stdout)["checks"]["commands"]
        tip = self.branch_gate
        if not tip:
            return [], False
        base = git(self.worktree, "merge-base", "HEAD", self.onto, check=False)
        before = git(self.worktree, "show", f"{base}:.lem/project.toml", check=False) if base else ""
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
        """The commit origin's copy of the task's branch is at, which a push of the branch may
        replace, or "" when origin has no such branch: the value of the push's lease. Refused when
        that copy holds a commit that neither Lem pushed nor the branch holds, a teammate's: a push
        would remove it. Origin is asked by `ls-remote`, never by the remote-tracking branch, which
        any plain fetch moves to the teammate's commit."""
        ref = f"refs/heads/{branch}"
        listed = [line.split("\t") for line in run(["git", "-C", str(self.main), "ls-remote", "origin", ref]).stdout.splitlines()]
        there = next((commit for commit, name in listed if name == ref), None)
        if there is None:
            return ""
        kept = self.kept()
        # what Lem pushed last, and what the remote held when the branch took its commits in
        known = [commit for commit in (kept.get("pushed"), kept.get("taken")) if commit]
        if there in known:
            return there
        git(self.main, "fetch", "-q", "origin", f"+{ref}:refs/remotes/origin/{branch}")
        theirs = run(["git", "-C", str(self.worktree), "log", "--format=%H%x00%an%x00%s", there, "--not", "HEAD", *known, self.onto, "--"]).stdout.splitlines()
        if not theirs:
            # every commit of origin's copy is on the branch, the base or a push of Lem's: the branch took them in
            self.keep(taken=there)
            return there
        named = "; ".join(f"{sha[:9]} {author} \"{subject}\"" for sha, author, subject in (line.split("\0", 2) for line in theirs[:10]))
        more = f", and {len(theirs) - 10} more" if len(theirs) > 10 else ""
        raise LandError(
            f"origin's {branch} holds {len(theirs)} commit(s) that Lem did not push and the task's branch does not hold: {named}{more}. "
            f"A push would remove them. Bring them into the task's worktree with `git -C {self.worktree} pull --rebase origin {branch}`, "
            f"then run the landing again from `lem land start {self.slug}`: they are part of the change then, with its checks and a read",
        )


def cmd_start(task: Task, conflicting: bool = False) -> dict:
    # Two starts at one moment take turns to read the tasks' states and write `landing`, under the
    # lock of the state folder. The lock is the kernel's, and it goes with the process, however
    # that ends. It holds no task back: any number of tasks are in `landing` at once.
    path = task.directory.parent.parent / "landing.lock"
    try:
        lock = path.open("w")
    except OSError as error:
        # a file nobody may write, or a folder of that name: the lock holds nothing, so it may go
        raise LandError(
            f"the landing lock {path} cannot be opened ({error.strerror}); it holds no state, so remove it "
            f"(`rm -r {path}`) and run `lem land start {task.slug}` again",
        ) from error
    with lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        task.read_states()
        return start_locked(task, conflicting)


def start_locked(task: Task, conflicting: bool = False) -> dict:
    # a task `start` blocked for want of a command of the checks is taken back as a `ready` one
    again = task.blocked_by_start()
    if task.record["status"] not in ("ready", "landing", "open") and not again:
        raise LandError(f"the task is {task.record['status']!r}; only a `ready` task, or an `open` one whose base moved, starts a landing")
    if conflicting and task.record["status"] != "open":
        raise LandError(f"--conflicting is for an `open` task whose pull request the forge calls conflicting, and {task.slug} is {task.record['status']!r}")
    if not task.gate()[0]:
        if not again:
            task.state("blocked", NO_GATE)
        raise LandError(
            f"{NO_GATE}, so nothing would show that the change works; the task is `blocked`. "
            "Add the commands to checks.commands in .lem/project.toml, or, for the task that sets up the checks, in its own branch's, "
            f"then run `lem land start {task.slug}` again",
        )
    task.need_worktree()
    # The landing needs the task's branch: `propose` pushes it, and `clean` deletes it after the merge.
    if not git(task.worktree, "branch", "--show-current"):
        pointing = [name for name in git(task.worktree, "for-each-ref", "--points-at", "HEAD", "--format=%(refname:short)", "refs/heads/").splitlines() if name != task.base]
        branch = task.kept().get("branch") or (pointing[0] if len(pointing) == 1 else "BRANCH")
        raise LandError(
            f"the task's worktree is on no branch (a detached HEAD), and the landing needs the task's branch: "
            f"`git -C {task.worktree} switch {branch}` puts it back on it, then this step runs again",
        )
    if task.record["status"] == "ready" or again:
        # A task that was built further starts over, with new checks and new reads. Its pull request
        # stays its own, and so does what Lem knows of its branch on the forge: the commit it pushed
        # last, and the one whose commits the branch took in (`own_remote`). The polish pass runs once
        # for a task (`stages/polish.md`): a pass that is done stays while the branch holds its last
        # commit, as after a stop on a red base, and `base` carries it through the rebase.
        kept = task.kept()
        forge = {key: value for key, value in kept.items() if key in ("pr", "pushed", "taken") and value}
        polish = kept.get("polish")
        if polish and polish.get("done") and holds_commit(task, polish.get("after"), git(task.worktree, "rev-parse", "HEAD")):
            forge["polish"] = polish
        task.kept_file.unlink(missing_ok=True)
        if forge:
            task.keep(**forge)
    if task.record["status"] == "open":
        # An open task brought onto a base that moved: what the pull request's text says of it is
        # kept from here, and a conflict or a resolution of an earlier landing says nothing of this one.
        # Each new landing of a proposal is counted, for the merge agent's facts: nothing bounds them,
        # since the checks run outside the merge lock and a busy base can move again meanwhile.
        relands = int(task.kept().get("relands") or 0) + 1
        task.keep(sync={"conflicting": conflicting, "onto": None, "moved": None, "conflict": None, "resolved": False},
                  conflict=None, resolution=None, rebase_carried=None, relands=relands)
        script("project.py", task.main, "log", task.slug, "land.again", f"count:={relands}", f"conflicting:={json.dumps(conflicting)}")
    if task.record["status"] != "landing":
        # kept here because `clean` needs the branch after the worktree, which names it, is gone
        task.keep(branch=git(task.worktree, "branch", "--show-current"))
        if conflicting:
            moved = f"the forge calls the pull request conflicting with {task.base}: the branch is brought onto it again"
        else:
            moved = "the base moved: the checks run again"
        task.state("landing", "the checks start" if task.record["status"] == "ready" or again else moved)
    return {"task": task.slug, "base": task.base, "worktree": str(task.worktree), "remote": task.remote, "forge": task.forge}


def cmd_base(task: Task) -> dict:
    task.need_landing()
    task.need_worktree()
    task.fetch()
    if task.forge == "github":
        # Before the rebase rewrites the branch: a commit a teammate added to it on the forge is
        # taken in by hand first, or the push after this rebase would remove it.
        task.own_remote(git(task.worktree, "branch", "--show-current"))
    onto = git(task.worktree, "rev-parse", task.onto)
    before = git(task.worktree, "rev-parse", "HEAD")
    kept = task.kept()
    # A conflict this landing met before: a builder rebased the branch since and resolved it, or
    # left it as it was. Its record keeps the tip before any rebase and whether a review covered it.
    pending = kept.get("conflict")
    if pending:
        covered = pending["covered"]
    else:
        # covered: the newest review that answered saw this change and left nothing to fix in it
        answered = [read for read in kept.get("reads", []) if read["answered"]]
        covered = bool(answered) and not answered[-1]["must_fix"] and covers(task, answered[-1], change(task))
    rebased = run(["git", "-C", str(task.worktree), "rebase", task.onto], check=False)
    if rebased.returncode != 0:
        conflicts = git(task.worktree, "diff", "--name-only", "--diff-filter=U", check=False).splitlines()
        git(task.worktree, "rebase", "--abort", check=False)
        task.keep(conflict={
            "before": pending["before"] if pending else before,
            "base": pending["base"] if pending else git(task.worktree, "merge-base", before, onto),
            "files": sorted({*(pending["files"] if pending else []), *conflicts}), "covered": covered,
        })
        if kept.get("sync"):
            task.keep(sync={**kept["sync"], "conflict": sorted({*(kept["sync"].get("conflict") or []), *conflicts})})
        print(json.dumps({"task": task.slug, "conflict": conflicts, "onto": task.onto, "branch": git(task.worktree, "branch", "--show-current")}, indent=2))
        raise LandError(
            f"the rebase onto {task.onto} stopped on {len(conflicts)} file(s) and was undone; "
            "a builder resolves it in the worktree, then this step runs again",
        )
    tip = git(task.worktree, "rev-parse", "HEAD")
    ahead = int(git(task.worktree, "rev-list", "--count", f"{onto}..HEAD"))
    if ahead == 0:
        raise LandError(
            f"the branch has no commit that {task.onto} lacks: there is nothing to land. When the work reached the base another way, "
            f"or there is none, `lem project state {task.slug} dropped \"WHY\"` ends the task",
        )
    # A builder that resolved the conflict rebased the branch itself: its commits are the ones the
    # rebase rewrote, from the tip before it. One that left the branch as it was resolved nothing.
    resolved = bool(pending) and before != pending["before"]
    origin = pending["before"] if pending else before
    if tip != origin and task.kept().get("polish"):
        # The rebase rewrote the commits the polish pass names; each takes its new name, so that
        # the checks still find the pass on the tip they check.
        task.keep(polish=through_rebase(task, task.kept()["polish"], origin, tip, onto))
    now = change(task)
    # the tip a rebase with no conflict made of the tip before it, while the review carried: what was
    # said of that tip at the merge (the merge agent's review, the owner's merge) is kept for this one
    updates: dict = {"base": onto, "gated": None, "tree": None, "conflict": None, "rebase_carried": None}
    if resolved:
        # What the review saw is the change before the conflict; what the builder chose where the
        # two sides met is new, and gets one read of its own (`due`).
        updates["resolution"] = {
            "files": pending["files"], "before": origin, "after": tip, "base": pending["base"], "onto": onto,
            "covered": covered, "patch": now["patch"], "read": None,
        }
    elif tip != origin and covered:
        # A rebase that git made with no conflict keeps the review of the change: the newest review
        # that answered covers the change on the new base too.
        reads = task.kept().get("reads", [])
        last = max(index for index, read in enumerate(reads) if read["answered"])
        reads[last] = {**reads[last], "carried": [*reads[last].get("carried", []), {"patch": now["patch"], "contents": now["contents"], "onto": onto[:9]}]}
        updates["reads"] = reads
        updates["rebase_carried"] = {"from": origin, "to": tip}
    if kept.get("sync"):
        updates["sync"] = {**task.kept()["sync"], "onto": onto[:9], "moved": tip != origin, "resolved": resolved or task.kept()["sync"].get("resolved", False)}
    # a new base or a new tip means the last result of the checks is about another tree
    task.keep(**updates)
    return {"task": task.slug, "onto": task.onto, "base": onto, "tip": tip, "moved": tip != before, "ahead": ahead, "resolved": pending["files"] if resolved else None}


def holds_commit(task: Task, commit: str | None, tip: str) -> bool:
    """Whether the branch at `tip` holds `commit`."""
    return bool(commit) and run(["git", "-C", str(task.worktree), "merge-base", "--is-ancestor", str(commit), tip], check=False).returncode == 0


def through_rebase(task: Task, polish: dict, before: str, tip: str, onto: str) -> dict:
    """The polish pass's record after a rebase by `base`: each commit it names, by its place from
    the tip. A rebase keeps the branch's commits one for one, unless one became empty and was
    dropped; then no place is sure, the names are dropped, and the checks ask for the pass again."""
    same = int(git(task.worktree, "rev-list", "--count", f"{onto}..{before}")) == int(git(task.worktree, "rev-list", "--count", f"{onto}..{tip}"))
    moved = dict(polish)
    for key in ("before", "after"):
        commit = polish.get(key)
        if not commit:
            continue
        if same and holds_commit(task, commit, before):
            after = int(git(task.worktree, "rev-list", "--count", f"{commit}..{before}"))
            moved[key] = git(task.worktree, "rev-parse", f"{tip}~{after}")
        else:
            moved[key] = None
    return moved


def test_files(found: dict) -> list[str]:
    """The files that hold a criterion's test, as the plan names them."""
    return sorted({file for criterion in found["criteria"] for test in criterion["tests"] for file in test["files"]})


def cmd_polish(task: Task, done: bool) -> dict:
    """The polish pass: what its builder gets, and after the builder, the check of what it did."""
    task.need_landing()
    task.need_worktree()
    found = criteria_of(task)
    if found["small"]:
        raise LandError(
            f"the fast track has no polish pass: its builder filed in the backlog what it saw outside the change, in a commit of its own, "
            f"and the review reads every line of it. `lem land checks {task.slug}` is the next step",
        )
    kept = task.kept()
    if "base" not in kept:
        raise LandError(f"`lem land base {task.slug}` comes first: the polish pass works on the branch as it will be checked")
    tip = git(task.worktree, "rev-parse", "HEAD")
    # what the pass may not change: the test files of the criteria and the plan that names them; a
    # fast track's criteria file is in the task directory, which no commit holds
    frozen = [*test_files(found), *([] if found["small"] else [Path(found["plan"]).relative_to(task.worktree).as_posix()])]
    polish = kept.get("polish")
    if not done:
        # A pass that started and is not done keeps the tip it started at: a run that is cut off,
        # or a second start, must not take the builder's first commits for the task's own.
        if not polish or not polish.get("before") or (polish.get("done") and not holds_commit(task, polish.get("after"), tip)):
            polish = {"before": tip, "done": False}
            task.keep(polish=polish)
            # the start of the pass, once: the board draws its span from here to `polish`
            script("project.py", task.worktree, "log", task.slug, "polish.start", f"before={tip[:9]}")
        base = git(task.worktree, "merge-base", polish["before"], task.onto)
        report, outside = task.directory / "report.md", task.directory / "outside.md"
        return {
            "task": task.slug, "size": found["size"], "done": polish["done"], "before": polish["before"],
            # the task's own commits, which the pass reads; what it commits comes after `before`
            "range": f"{base}..{polish['before']}",
            "commits": git(task.worktree, "log", "--format=%h %s", f"{base}..{polish['before']}").splitlines(),
            "plan": found["plan"], "report": str(report) if report.is_file() else None, "outside": str(outside) if outside.is_file() else None,
            "backlog": backlog_of(task),
            "frozen": frozen,
        }
    if not polish:
        raise LandError(f"no polish pass started for this landing; `lem land polish {task.slug}` starts it and prints what its builder gets")
    if polish.get("done"):
        raise LandError(f"the polish pass of this landing is done already, at {str(polish.get('after'))[:9]}; a builder of the landing after it has the same list in its brief")
    before = polish["before"]
    if not holds_commit(task, before, tip):
        raise LandError(
            f"the branch no longer holds {str(before)[:9]}, the tip the polish pass started at: its builder rewrote the task's commits, which no builder of the pass does. "
            "Put the branch back on its own commits (git reflog names them), then run this again",
        )
    commits = git(task.worktree, "log", "--reverse", "--format=%H %s", f"{before}..{tip}").splitlines()
    touched: dict[str, list[str]] = {}
    for line in commits:
        commit = line.split(" ", 1)[0]
        for file in git(task.worktree, "diff-tree", "--no-commit-id", "--name-only", "--no-renames", "-r", commit).splitlines():
            touched.setdefault(file, []).append(commit[:9])
    # What counts is what the pass leaves: a commit that changed a criterion's test and one that put it back leave the contract as it was.
    differs = set(changed(task, before, tip))
    wrong = [f"{file} (by {', '.join(touched.get(file, []))})" for file in frozen if file in differs]
    if wrong:
        raise LandError(
            f"the polish pass changed what it may not: {'; '.join(wrong)}. A criterion's test and the plan are the task's contract, and the pass changes no behavior: "
            f"a builder reverts those commits (`git revert`), and this step runs again",
        )
    result: dict = {"task": task.slug, "before": before, "after": tip, "commits": [line.split(" ", 1)[1] if " " in line else "" for line in commits]}
    if commits:
        held = script("criteria.py", task.main, "red", task.slug, check=False)
        if held.returncode != 0:
            raise LandError(
                f"after the polish pass the tests of the criteria do not hold: {held.stderr.strip().removeprefix('criteria.py: ')}. "
                "The pass changes no behavior: a builder finds the commit of the pass that broke it and takes it out, and this step runs again",
            )
        result["criteria"] = json.loads(held.stdout)
    else:
        result["criteria"] = None
    folder = backlog_of(task)
    added = [row.split("\t", 1)[1] for row in git(task.worktree, "diff", "--name-status", "--no-renames", before, tip).splitlines() if row.startswith("A\t")]
    result["filed"] = [path for path in added if path.startswith(folder + "/")]
    script("project.py", task.worktree, "log", task.slug, "polish", f"before={before[:9]}", f"after={tip[:9]}", f"commits:={len(commits)}", f"filed:={json.dumps(result['filed'])}")
    # the pass's result of the criteria's tests, with the inputs its run reported: the checks take it
    # in place of a run of their own when those inputs are the same when they decide (`taken_from_polish`)
    task.keep(polish={"before": before, "after": tip, "done": True, "commits": len(commits), "filed": result["filed"], "criteria": result["criteria"]})
    return result


def polish_missing(task: Task, tip: str, found: dict) -> str | None:
    """Why the checks may not run on this tip for want of the polish pass; none when it may. A task on
    the standard track, which is every task with a plan, needs a pass of this landing whose last commit the tip holds,
    and a pass that started and is not done stops it: a builder may still be at work. A task on the
    fast track never has one."""
    if found["small"]:
        return None
    polish = task.kept().get("polish")
    if polish and not polish.get("done"):
        return f"the polish pass started at {str(polish.get('before'))[:9]} and is not done: after its builder, `lem land polish {task.slug} --done` checks what it did"
    if not polish:
        return f"{task.slug} takes the standard track, and no polish pass is on record for this landing: `lem land polish {task.slug}` starts it, a builder does it, and `--done` checks it"
    if not holds_commit(task, polish.get("after"), tip):
        return (
            f"the tip does not hold the polish pass's last commit ({str(polish.get('after'))[:9]}): the branch was rewritten after the pass by something else than `lem land base`. "
            f"The pass runs again: `lem land polish {task.slug}`, its builder, and `--done`"
        )
    return None


def taken_from_polish(polish: dict | None, now: dict | None, small: bool) -> dict | None:
    """The polish pass's result of the criteria's tests when the checks take it in place of a run of
    their own, with `taken`, which names the pass and its commit; None when the checks run the tests.

    The fast track has no pass, and a pass with no commits ran no tests. Otherwise the result is taken
    only when NOW, the inputs `lem criteria inputs` gives after the checks' commands, are the inputs
    the pass's run reported, all five: the tip, the base commit, the plan file, `checks.setup` and
    `checks.serial`. `polish.after` decides nothing here: a rebase by `base` gives it the rebased
    commit's name (`through_rebase`), while the run named the tip it ran on."""
    if small or not polish or not polish.get("done") or not polish.get("commits"):
        return None
    ran = polish.get("criteria") or {}
    if not ran.get("ok") or not ran.get("inputs") or now is None or ran["inputs"] != now:
        return None
    return {**ran, "taken": {"from": "polish", "at": ran["inputs"]["tip"]}}


def taken_at(criteria: object) -> str | None:
    """The commit, as `gate.end` names it, whose polish pass's result of the criteria's tests a run of the
    checks took (`taken_from_polish`); None for a run that ran them, or that never reached them."""
    taken = criteria.get("taken") if isinstance(criteria, dict) else None
    at = taken.get("at") if isinstance(taken, dict) and taken.get("from") == "polish" else None
    return at[:9] if isinstance(at, str) and at else None


def criteria_of(task: Task) -> dict:
    """The task's acceptance criteria and its plan, through the one script that reads them. A step
    asks for them many times, and no step writes the plan, the approval or a criterion's record, so
    the first answer is kept for the life of this process."""
    if task.criteria is None:
        task.criteria = json.loads(script("criteria.py", task.main, "show", task.slug).stdout)
    return task.criteria


def change(task: Task) -> dict:
    """The change as the branch holds it now: its two ends, its files, its size, and the id of its patch."""
    tip = git(task.worktree, "rev-parse", "HEAD")
    base = git(task.worktree, "merge-base", tip, task.onto)
    # The id of the change: each file it touches, with the content the file had on the base and
    # the content it has now. A rebase onto a base that left those files alone keeps the id, and
    # everything else is another change: one space, the same edit in another place of a file, a
    # base that changed a file under the change. git's own patch id is not used: it ignores
    # spaces and places, and either can be the whole of a change.
    raw = git(task.worktree, "diff", "--raw", "--no-abbrev", "--no-renames", base, tip)
    patch = hashlib.sha256(raw.encode()).hexdigest()[:16]
    # The same listing path by path, with NUL ends so that no path is quoted: each file with its
    # mode and blob on the base and on the tip. A review keeps it, so that what was added after
    # the review is known file by file (`covers`).
    listed = run(["git", "-C", str(task.worktree), "diff", "--raw", "-z", "--no-abbrev", "--no-renames", base, tip]).stdout.split("\0")
    # each head is ":MODE_BASE MODE_TIP BLOB_BASE BLOB_TIP STATUS"
    heads = {path: head.lstrip(":").split() for head, path in zip(listed[0::2], listed[1::2])}
    contents = {path: {"base": head[2], "tip": head[3], "modes": head[:2]} for path, head in heads.items()}
    counted = git(task.worktree, "diff", "--numstat", "--no-renames", base, tip).splitlines()
    lines = sum(int(n) for row in counted for n in row.split("\t")[:2] if n.isdigit())
    return {"tip": tip, "base": base, "files": changed(task, base, tip), "patch": patch, "contents": contents, "lines": lines}


def backlog_of(task: Task) -> str:
    """The backlog folder, relative to the root of the repository: its one place, `docs/backlog`."""
    return Path(task.settings["places"]["backlog"]["path"]).relative_to(Path(task.settings["root"]).resolve()).as_posix()


def covers(task: Task, read: dict, now: dict) -> bool:
    """Whether a review that was recorded still covers the change as it is now: the change it
    reviewed, or that change as each rebase `base` made with no conflict carried it onto a new base."""
    return covered(backlog_of(task), read, now)


def covered(folder: str, read: dict, now: dict) -> bool:
    """`covers`, with the backlog folder given: the rule alone, which reads no file."""
    return any(covers_one(folder, seen, now) for seen in [read, *read.get("carried", [])])


def covers_one(folder: str, read: dict, now: dict) -> bool:
    """Whether one form of a reviewed change covers the change as it is now. It does when the
    change is the same, or when the change is the reviewed one plus new files of the backlog
    folder and nothing else: `file` writes the defects a review saw outside the change there after
    the review, and that asks for no other review. Any other file does, an item that was on the
    base too. A record that kept no contents covers only the same change."""
    if read["patch"] == now["patch"]:
        return True
    was = read.get("contents")
    if was is None:
        return False
    extra = [path for path in now["contents"] if path not in was]
    return bool(extra) and all(now["contents"].get(path) == entry for path, entry in was.items()) and all(
        set(now["contents"][path]["base"]) == {"0"} and path.startswith(folder + "/") for path in extra
    )


def defects_of(value: object) -> list[dict]:
    """The defects outside the change as a new record names them; `0` is none, and a count is refused."""
    if isinstance(value, int) and not isinstance(value, bool) and value == 0:
        return []
    if not isinstance(value, list) or not all(
        isinstance(item, dict) and set(item) == set(DEFECT) and all(isinstance(item[key], str) and item[key].strip() for key in DEFECT)
        and "\n" not in item["where"] + item["title"] and slug_of(item["title"]) for item in value
    ):
        raise LandError(
            "`outside` is the list of the defects the review saw outside the change, each "
            "{\"where\": PATH OR PATH:SYMBOL, \"title\": ONE LINE, \"what\": THE RUN THAT SHOWS IT}, so that each one can be filed: "
            "a count names none of them, and 0 is none",
        )
    return [{key: item[key].strip() for key in DEFECT} for item in value]


def outside_of(read: dict) -> list[dict]:
    """The defects outside the change of one kept review, each with the path of its item once it has one."""
    return read.get("outside", [])


def to_file(reads: list[dict]) -> list[dict]:
    """Each defect outside the change of a review that answered, with no item yet."""
    return [
        {"round": read["round"], **{key: defect[key] for key in DEFECT}}
        for read in reads if read["answered"] for defect in outside_of(read) if not defect.get("item")
    ]


def slug_of(text: str) -> str:
    """A file name from a title, as the backlog's item format has it: words joined by `-`."""
    slug = re.sub(r"[\W_]+", "-", text.lower()).strip("-")
    return slug if len(slug) <= SLUG_AT else slug[:SLUG_AT].rsplit("-", 1)[0]


def names_for(defect: dict):
    """The file names an item of this defect may take, in turn: its slug, the slug with a suffix
    from its `where` (`src/json.py:parse` gives `-json-parse`), then that with a number."""
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
    """An item of the backlog as the item format has it: its front matter, and its lines after it, of
    which the first is its title (`# TITLE`). None for a file that is no such item."""
    try:
        text = file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    front: dict[str, str] = {}
    head = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if head:
        for line in head.group(1).splitlines():
            key, _, value = line.partition(":")
            front[key.strip()] = value.strip()
        text = text[head.end():]
    lines = text.strip().splitlines()
    if not lines or not lines[0].startswith("# "):
        return None
    return front, lines


def holds(file: Path, defect: dict) -> bool:
    """Whether an item file is this defect: the same `where`, the same title, and the defect's run
    as paragraphs of the body, word for word. Any other text of the body, the owner's reason for a
    `worth: no` or a later note, leaves it the same defect."""
    item = item_of(file)
    if item is None:
        return False
    front, lines = item
    if front.get("where") != defect["where"] or lines[0][2:].strip() != defect["title"]:
        return False
    # Paragraphs as `file` writes them: `what` stripped, a blank line between two paragraphs.
    body = paragraphs("\n".join(lines[1:]))
    run_of = paragraphs(defect["what"])
    return any(body[start:start + len(run_of)] == run_of for start in range(len(body) - len(run_of) + 1))


def paragraphs(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"\n[ \t]*\n", text.strip()) if part.strip()]


def in_tree(task: Task, tip: str, path: str) -> bool:
    return run(["git", "-C", str(task.worktree), "cat-file", "-e", f"{tip}:{path}"], check=False).returncode == 0


def someone_elses(task: Task) -> bool:
    """Whether the task's brief, or a block of its state, says that someone other than the owner
    wrote its complete request (`stages/new.md`, step 4): nobody at the terminal read it."""
    brief = task.directory / "brief.md"
    if brief.is_file() and SOMEONE_ELSE in [line.strip() for line in brief.read_text(encoding="utf-8", errors="replace").splitlines()]:
        return True
    return any(
        record.get("event") == "task.state" and SOMEONE_ELSE in [str(line).strip() for line in [record.get("text", ""), *record.get("lines", [])]]
        for record in events_of(task)
    )


def owner_says_careful(task: Task) -> bool:
    """Whether the owner's word that the task is careful is in its brief."""
    brief = task.directory / "brief.md"
    return brief.is_file() and OVERRULED in [line.strip() for line in brief.read_text(encoding="utf-8", errors="replace").splitlines()]


def plan_call(text: str) -> bool:
    """Whether one text of the plan says `careful: yes` where the call stands: under its title, before its first `##` heading."""
    found = PLAN_CALL.search(re.split(r"(?m)^##\s", text, maxsplit=1)[0])
    return bool(found) and found.group(1).lower() == "yes"


def plan_careful(task: Task) -> bool:
    """Whether the plan called the task careful, in its text now or in any commit of the branch.
    The talk was due when the plan said yes, so a later commit that takes the yes back does not
    take back the talk, the full set or the person's merge. A step asks it many times, and no step
    writes the plan, so the first answer is kept for the life of this process."""
    if task.plan_said is None and criteria_of(task)["small"]:
        # the fast track has no plan: its criteria file is in the task directory, with no history in git
        task.plan_said = plan_call(Path(criteria_of(task)["plan"]).read_text(encoding="utf-8"))
    if task.plan_said is None:
        plan = Path(criteria_of(task)["plan"])
        relative = plan.relative_to(task.worktree).as_posix()
        base = git(task.worktree, "merge-base", "HEAD", task.onto)
        texts = [plan.read_text(encoding="utf-8")]
        for commit in git(task.worktree, "log", "--format=%H", f"{base}..HEAD", "--", relative).splitlines():
            shown = run(["git", "-C", str(task.worktree), "show", f"{commit}:{relative}"], check=False)
            texts.append(shown.stdout if shown.returncode == 0 else "")
        task.plan_said = any(plan_call(text) for text in texts)
    return task.plan_said


def settings_edit(task: Task, now: dict) -> str | None:
    """Why the change is careful by its edit of Lem's own settings: any edit of `.lem/project.toml`,
    whose tables, once landed, say for every later task what is careful, what the checks run, who
    merges and where a task lands. The reason names each table whose values change, or says that
    only the file's text does. None when the change leaves the file alone."""
    if SETTINGS_FILE not in now["files"]:
        return None
    guards = "Lem's own settings, which say for every later task what is careful, what the checks run, who merges and where a task lands"
    if not in_commit(task, now["tip"], SETTINGS_FILE):
        # removed, or moved away: no table of it is edited, the whole file is gone
        return f"the change removes {SETTINGS_FILE}, {guards}"

    def tables(commit: str) -> dict:
        shown = run(["git", "-C", str(task.worktree), "show", f"{commit}:{SETTINGS_FILE}"], check=False)
        return tomllib.loads(shown.stdout) if shown.returncode == 0 else {}
    try:
        before, after = tables(now["base"]), tables(now["tip"])
    except tomllib.TOMLDecodeError:
        # in doubt, careful: what it says cannot be told
        return f"the change leaves {SETTINGS_FILE} in a form that does not read as TOML, so what it says is careful cannot be told"
    edited = sorted(name for name in {*before, *after} if before.get(name) != after.get(name))
    what = f"{' and '.join(f'[{name}]' for name in edited)} of {SETTINGS_FILE}" if edited else f"the text of {SETTINGS_FILE}, and no value in it"
    return f"the change edits {what}, {guards}"


def in_commit(task: Task, commit: str, path: str) -> bool:
    """Whether the commit holds the file."""
    return run(["git", "-C", str(task.worktree), "cat-file", "-e", f"{commit}:{path}"], check=False).returncode == 0


def local_settings_edit(task: Task, now: dict) -> str | None:
    """Why the change is careful by a commit of one machine's own settings: `.lem/project.local.toml`
    is untracked by design, and a tracked copy gives every machine that machine's seats, corrections and naps.
    None when the change leaves the file alone."""
    if LOCAL_SETTINGS_FILE not in now["files"]:
        return None
    before, after = in_commit(task, now["base"], LOCAL_SETTINGS_FILE), in_commit(task, now["tip"], LOCAL_SETTINGS_FILE)
    how = "adds" if after and not before else "removes" if before and not after else "changes"
    return (
        f"the change {how} {LOCAL_SETTINGS_FILE}, one machine's own settings, which git does not track: "
        "tracked, that machine's seats, corrections and naps become every machine's"
    )


def review_call(task: Task) -> dict | None:
    """The careful call of the newest review that answered, as its record made it: `careful` and its
    `why`. None when no review answered, or when the newest record holds no call."""
    answered = [read for read in task.kept().get("reads", []) if read["answered"]]
    if not answered or "careful" not in answered[-1]:
        return None
    return {"careful": answered[-1]["careful"], "why": answered[-1]["careful_why"]}


def careful(task: Task, now: dict) -> list[str]:
    """Each reason for which this request is careful; none when it is not. The owner's word, the
    plan's own call and the newest review's are judgments against the project's topics; the edit of
    Lem's own settings, or of one machine's, is the one rule this script matches by itself."""
    why = []
    if owner_says_careful(task):
        why.append("the owner says so")
    if plan_careful(task):
        why.append("the plan says so")
    for edited in (settings_edit(task, now), local_settings_edit(task, now)):
        if edited:
            why.append(edited)
    call = review_call(task)
    if call and call["careful"]:
        why.append(f"the review says so: {reason(call['why'])}")
    return why


def tasks_of(plan: str) -> int:
    """How many tasks the plan has: the numbered lines, or numbered headings, under its `## Tasks` heading."""
    section = re.search(r"(?ms)^##\s+Tasks\b[^\n]*$(.*?)(?=^##\s|\Z)", plan)
    count = len(re.findall(r"(?m)^(?:###\s+)?\d+\.\s", section.group(1))) if section else 0
    if not count:
        # no quiet default: the count decides which read the change gets
        raise LandError("the task's plan has no `## Tasks` section with numbered tasks, and their count decides which read the change gets; the lead writes the section")
    return count


def bar(task: Task, base: str, tip: str, plan: str) -> dict:
    """Where the change lowers the bar, each with the reason the plan gives for that file, or none."""
    # -M: a file that moved is one file, so its tests are not counted as gone and come again
    return bar_of(
        git(task.worktree, "diff", "-U0", "-M", base, tip),
        git(task.worktree, "diff", "--name-status", "-M", base, tip).splitlines(),
        plan,
        changed(task, base, tip),
    )


def bar_of(diff: str, rows: list[str], plan: str, files: list[str]) -> dict:
    """The bar's result from what git gave: `diff` is `git diff -U0 -M`, `rows` the lines of
    `git diff --name-status -M`, `files` every changed path; `plan` is the plan's text, or "" when
    there is none."""
    section = re.search(r"(?ms)^##\s+The bar\s*$(.*?)(?=^##\s|\Z)", plan)
    reasons = {found.group(1).strip(): found.group(2).strip() for found in re.finditer(r"(?m)^-\s+`?([^`:\n]+?)`?:\s+(\S.*)$", section.group(1))} if section else {}
    lowered: list[dict] = []
    asserts: dict[str, int] = {}
    # A mark counts when the change leaves more of it in a file than the file had: a line that
    # only moved, or got another space, took the mark out and put it back. A mark is the same
    # one only with the same text from the mark to the end of its line: `noqa: F401` that
    # becomes `noqa` is a wider suppression, and a new one.
    came: dict[tuple[str, str, str], list[dict]] = {}
    went: dict[tuple[str, str, str], int] = {}
    # each coverage threshold's numbers before and after, whatever file of a runner's settings holds it
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
            marks = [*(re.compile(mark) for suffixes, found in BAR.items() if Path(file).suffix.lower() in suffixes for mark in found),
                     *(re.compile(mark) for mark in TEST_CONFIG_MARKS if TEST_CONFIG.search(file))] if file else []
        elif not file or line[:1] not in "+-":
            continue
        else:
            # every mark of the line counts, as a runner's settings put several on one line
            for hit in (found for mark in marks if (found := mark.search(line[1:]))):
                key = (file, hit.re.pattern, " ".join(line[1:][hit.start():].split()))
                if line.startswith("+"):
                    came.setdefault(key, []).append({"file": file, "what": hit.group(0), "line": line[1:].strip()[:160]})
                else:
                    went[key] = went.get(key, 0) + 1
            if TEST_CONFIG.search(file) or WORKFLOW.search(file):
                for found in THRESHOLD.finditer(line[1:]):
                    name, number = (found.group(1), found.group(2)) if found.group(1) else (found.group(3), found.group(4))
                    thresholds.setdefault(name, {"-": [], "+": []})[line[0]].append((float(number), file))
            if (TEST_FILE.search(file) or Path(file).suffix.lower() in INLINE_TESTS) and ASSERTS.search(line[1:]):
                asserts[file] = asserts.get(file, 0) + (1 if line.startswith("-") else -1)
    for key, entries in came.items():
        lowered += entries[went.get(key, 0):]
    for name, fewer in sorted(asserts.items()):
        if fewer > 0:
            lowered.append({"file": name, "what": f"{fewer} assertion(s) fewer", "line": ""})
    for name, numbers in sorted(thresholds.items()):
        if not numbers["-"]:
            continue
        before, where = max(numbers["-"])
        after = min(number for number, _ in numbers["+"]) if numbers["+"] else None
        if after is None or after < before:
            said = f"{name} went from {before:g} to {after:g}" if after is not None else f"{name} ({before:g}) is gone"
            lowered.append({"file": where, "what": said, "line": ""})
    edited = []
    for row in rows:
        status, name, *moved = row.split("\t")
        # a test file that moved out of the tests is one the tests no longer run, as a deleted one
        gone = status == "D" or (status.startswith("R") and moved and not TEST_FILE.search(moved[0]))
        if gone and TEST_FILE.search(name):
            lowered = [entry for entry in lowered if entry["file"] != name]
            lowered.append({"file": name, "what": "a test file is deleted" if status == "D" else f"a test file is moved out of the tests, to {moved[0]}", "line": ""})
        # an existing file a reviewer reads first: a test, a snapshot, a runner's or a workflow's settings the change edits
        now = moved[0] if moved else name
        kind = "snapshot" if SNAPSHOT.search(now) else "test configuration" if TEST_CONFIG.search(now) or WORKFLOW.search(now) else "test" if TEST_FILE.search(now) else None
        if kind and (status == "M" or (status.startswith("R") and status != "R100")):
            edited.append({"file": now, "kind": kind})
    for entry in lowered:
        entry["reason"] = reasons.get(entry["file"])
    covered = {suffix for suffixes in BAR for suffix in suffixes}
    not_covered = sorted({Path(name).suffix.lower() for name in files} - covered - set(DOCS) - set(DATA))
    return {"lowered": lowered, "not_covered": not_covered, "edited": sorted(edited, key=lambda entry: entry["file"])}


def bar_refusal(lowered: list[dict], small: bool) -> str | None:
    """The checks' refusal of a bar lowered with no reason, or None. The fast track gives no reason:
    it has no plan, and a lowered bar never takes the fast track."""
    unexplained = [entry for entry in lowered if not entry["reason"]]
    if not unexplained:
        return None
    named = "; ".join(f"{entry['file']} ({entry['what']})" for entry in unexplained[:5])
    if small:
        return (
            f"a task on the fast track does not lower the bar: {named}. Take the mark out; when the change needs it, it takes the standard track, "
            f"and Lem tells the developer so and takes that track, whose plan gives the reason under `## The bar`"
        )
    return (
        f"the change lowers the bar with no reason given: {named}. Take the mark out, or give the reason in the task's plan "
        "under `## The bar` as `- PATH: REASON`, where the one who reads the change sees it"
    )


# The task's one step lock: every step of `lem land` that names a task holds it for as long as it
# runs, so that two steps of one task never run at one time, in either order: a proposal never
# comes while its checks run, and `base` never rebases the worktree they run in. A file in the task
# directory; the lock is the kernel's, and it goes with the process, however that ends.
STEP_LOCK = "step.lock"

# What a run of the checks ends as, in its `gate.end` event.
RESULTS = ("passed", "red", "refused", "stopped")

# The checks are overdue when they run more than this many times as long as their last finished run:
# the owner's "three times longer than their last finished run" (criterion 5 of the plan
# 2026-11-19-landing-in-the-background).
OVERDUE_TIMES = 3

# How long `checks --stop` waits for the run it stopped to end: the stop of a serial command takes
# up to SERIAL_GRACE, and `criteria.py red` up to its own GRACE for each signal to each command it runs,
# and its SERIAL_GRACE for the term to a serial test's wrapper (its `stop`). A guess with room, not a measurement.
STOP_WAIT = 60

# How long a serial command's wrapper (`project.py serial`) gets after a term before it is killed:
# its own cleanup sends its command a term, waits 3 s, sends a kill and waits 3 s more (`cmd_serial`),
# and one second is left for its exit. Any other command gets one second.
SERIAL_GRACE = 7.0
GRACE = 1.0


# How often a run of the checks that waits for the load looks at it again, how often it logs a new
# `gate.wait` while it waits, and the least time between two starts of the checks under the gate on
# one machine. The spacing is a guess, not a measurement: the load average of one minute needs about
# a minute to show a run that started, so that the next reader sees it.
LOAD_LOOK = 15
LOAD_SAY = 300
LOAD_SPACING = 60
# Lem's own merge calls go one at a time, under this lock of the state folder.
MERGE_LOCK = "merge.lock"


def load_now() -> float:
    """The machine's load average of the last minute, as `uptime` gives it."""
    return round(os.getloadavg()[0], 1)


def wait_say(slug: str, load: float, start: float, after: str | None = None) -> str:
    """The one line of a run of the checks that waits, for the owner and the board."""
    if after:
        return f"{slug}: the checks wait a minute after the checks of {after} started, so that the load shows them; then they start below {start:g}"
    return f"{slug}: the checks wait for the load: {load:g}, they start below {start:g}"


def wait_for_load(task: Task) -> dict | None:
    """Wait, before the first command of the checks, until the machine's load average is below the start
    number the developer set for this machine, and until LOAD_SPACING seconds passed since the last start
    under the gate on this machine, of any repository. Logs `gate.wait` when it waits, again each
    LOAD_SAY seconds while it waits. None when the machine has no number: then there is no gate. The
    number is read again at each look, so that a run that waits takes the developer's new number, or
    starts at once when he took the gate away."""
    path = lem_state.machine_file().parent / lem_state.LOAD_LOCK
    said: tuple[str, float] | None = None
    waited = False
    while True:
        try:
            start = lem_state.load_start()
        except lem_state.StateError as error:
            raise LandError(str(error)) from error
        if start is None:
            return {"start": None, "waited": waited} if waited else None
        load = load_now()
        after = None
        if load < start:
            with path.open("a+", encoding="utf-8") as handle:
                # held for a read and a write only, so that two runs that wait take turns
                fcntl.flock(handle, fcntl.LOCK_EX)
                handle.seek(0)
                try:
                    last = json.loads(handle.read() or "null")
                except ValueError:
                    last = None
                gap = time.time() - last["at"] if isinstance(last, dict) and isinstance(last.get("at"), (int, float)) else None
                if gap is None or gap >= LOAD_SPACING or gap < 0:
                    handle.seek(0)
                    handle.truncate()
                    handle.write(json.dumps({"at": time.time(), "task": task.slug, "repo": str(task.main)}) + "\n")
                    handle.flush()
                    return {"start": start, "load": load, "waited": waited}
                after = str(last.get("task") or "another task")
        # a new line when the reason changed, or after LOAD_SAY seconds of the same one
        reason = "after" if after else "load"
        if said is None or said[0] != reason or time.monotonic() - said[1] >= LOAD_SAY:
            script("project.py", task.worktree, "log", task.slug, "gate.wait", f"load:={load}", f"start:={start:g}",
                   *([f"after={after}"] if after else []), f"say={wait_say(task.slug, load, start, after)}")
            said = (reason, time.monotonic())
            waited = True
        time.sleep(LOAD_LOOK if not after else min(LOAD_LOOK, max(1.0, LOAD_SPACING - gap)))


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def seconds_since(stamp: str, now: datetime | None = None) -> int:
    """The whole seconds from a stamp of the form `now_utc` writes to now."""
    then = datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return max(0, int(((now or datetime.now(timezone.utc)) - then).total_seconds()))


def duration(seconds: int) -> str:
    """Seconds in the words a person reads: `26 s`, `4 min 26 s`, `14 min`."""
    minutes, rest = divmod(int(seconds), 60)
    if not minutes:
        return f"{rest} s"
    return f"{minutes} min" + (f" {rest} s" if rest else "")


def checks_say(slug: str, result: str, *, red: list[str] | None = None, refused: str | None = None, next_due: str | None = None) -> str:
    """The one line for the owner at the end of a run of the checks: the slug, the result and the next
    step, with no question. `red` names the commands that failed, `refused` what the checks refused,
    and `next_due` is what `due` says after a passed run (`review`, `none` or `owner`)."""
    if result == "passed":
        if next_due in ("none", "owner"):
            return f"{slug}: the checks passed; no review is due, so it is proposed, nothing for you"
        return f"{slug}: the checks passed; the review runs, nothing for you"
    if result == "red":
        return f"{slug}: the checks are red on {' and '.join(red or ['a command'])}; a builder repairs it, nothing for you"
    if result == "refused":
        return f"{slug}: the checks refused the change: {refused or 'the step met an error'}; a builder repairs it, nothing for you"
    if result == "stopped":
        return f"{slug}: the checks were stopped; the landing waits for your word"
    raise ValueError(f"a run of the checks ends as one of {', '.join(RESULTS)}, not {result!r}")


def last_seconds(events: list[dict]) -> int | None:
    """The length of the checks' last finished run: the `seconds` of the newest `gate.end` whose result
    is `passed`, of any task. A red run stops before the serial commands, and would make the next run
    look overdue; with no such run there is none."""
    ends = [event for event in events if event.get("event") == "gate.end" and event.get("result") == "passed" and isinstance(event.get("seconds"), int)]
    return ends[-1]["seconds"] if ends else None


def is_overdue(seconds: int | None, last: int | None) -> bool:
    """Whether a run that has gone on for `seconds` runs more than OVERDUE_TIMES as long as the last finished one.
    A last run that rounds to 0 seconds (a stand-in command such as `true`) has no length to multiply, so
    nothing is overdue against it: three times 0 would call any run overdue after 1 second."""
    return seconds is not None and last is not None and last > 0 and seconds > OVERDUE_TIMES * last


def overdue_say(slug: str, seconds: int, last: int) -> str:
    return f"{slug}: the checks run for {duration(seconds)}, more than three times their last run of {duration(last)}; \"stop the checks\" stops them"


def resumed_line(slug: str, end: dict) -> str:
    """The line for a session that did not start the run: its result, as past, and the next step as it is
    now, not as the session that saw the run end took it. A stopped run waits for the owner's word; after
    any other, the landing goes on from its first step, as after a cut-off."""
    result = end.get("result")
    after = "the landing waits for your word" if result == "stopped" else "the landing goes on from its first step, as after a cut-off"
    return f"{slug}: its last run of the checks ended at {utc(end['ts'])}, {result}; {after}"


def ended_of(end: dict | None, slug: str) -> dict | None:
    """The newest end of a task's checks, as `--status` and `--stop` print it."""
    if end is None:
        return None
    return {"at": end["ts"], "tip": end.get("tip"), "result": end.get("result"), "seconds": end.get("seconds"), "say": end.get("say"), "resumed": resumed_line(slug, end)}


def holder_of(path: Path) -> dict | None:
    """The step the lock file names, its process and its start, or none: the holder writes the line
    after it takes the lock and takes it away before it lets the lock go."""
    try:
        found = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(found, dict) or not isinstance(found.get("pid"), int) or not isinstance(found.get("step"), str):
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
    """Why a step of a task may not run now: another step of the same task holds its lock."""
    if holder is None:
        return f"another step of {slug} runs now and holds its lock ({STEP_LOCK} in its task directory); it ends first, then this step runs again"
    when = f"since {utc(holder['since'])}, in process {holder['pid']}" if isinstance(holder.get("since"), str) else f"in process {holder['pid']}"
    status = f"`lem land checks {slug} --status` says whether they still run"
    if holder["step"] == "checks" and step == "checks":
        return f"the checks of {slug} already run ({when}): a second run is refused. The session that started them goes on when they end; {status}"
    if holder["step"] == "checks":
        return f"the checks of {slug} run ({when}), and their end comes first: the session that started them goes on when they end, and this step waits for it; {status}"
    return f"another step of {slug} runs now, `lem land {holder['step']} {slug}` ({when}); it ends first, then this step runs again"


@contextlib.contextmanager
def step_lock(task: Task, step: str):
    """Hold the task's one step lock for as long as the step runs, however it ends, with the step's
    name, process and start in its file; a step of the same task meanwhile is refused with that
    holder. The commands a step starts do not get the lock's file (Popen closes it in them), so a
    server a command left behind does not hold it."""
    path = task.directory / STEP_LOCK
    try:
        handle = path.open("a+", encoding="utf-8")
    except OSError as error:
        raise LandError(
            f"the step lock {path} cannot be opened ({error.strerror}); it holds no state, so remove it (`rm -r {path}`) and run `lem land {step} {task.slug}` again",
        ) from error
    with handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise LandError(held_refusal(task.slug, step, holder_of(path))) from None
        handle.seek(0)
        handle.truncate()
        handle.write(json.dumps({"step": step, "pid": os.getpid(), "since": now_utc()}) + "\n")
        handle.flush()
        try:
            yield
        finally:
            # the holder's line goes with the hold, so that a look at the file never names a step that ended
            handle.seek(0)
            handle.truncate()
            handle.flush()


def running_checks(task: Task) -> dict | None:
    """The run of the task's checks that holds its step lock now, or none. A look at the file and at
    the process it names, never at the lock itself, so that a look never makes a real start fail."""
    holder = holder_of(task.directory / STEP_LOCK)
    if holder is None or holder["step"] != "checks" or not alive(holder["pid"]):
        return None
    return holder


def gate_ends(task: Task) -> list[dict]:
    """Every end of a run of the checks in the repository's event log, of any task, oldest first."""
    log = task.directory.parent.parent / "events.jsonl"
    found = []
    for line in lem_state.jsonl_lines(log.read_text(encoding="utf-8")) if log.is_file() else []:
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
    """The newest `gate.wait` of the task's run that holds the step lock since `since`, while no
    `gate.start` came after it: the run waits for the load."""
    log = task.directory.parent.parent / "events.jsonl"
    found = None
    for line in lem_state.jsonl_lines(log.read_text(encoding="utf-8")) if log.is_file() else []:
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
    """Whether the task's checks run, for how long, against their last finished run, and how the last
    run ended. A run that waits for the load says so in `waits`, and its time counts from its start."""
    holder = running_checks(task)
    ends = gate_ends(task)
    last = last_seconds(ends)
    since = holder.get("since") if holder else None
    seen = waits_of(task, since) if isinstance(since, str) else None
    waits = None
    if seen and "started" in seen:
        since = seen["started"]
    elif seen:
        # the run holds the lock and waits for the load: none of its commands started yet
        waits = {key: seen[key] for key in ("load", "start", "after", "say") if key in seen}
    seconds = seconds_since(since) if isinstance(since, str) and not waits else None
    overdue = holder is not None and is_overdue(seconds, last)
    own = [end for end in ends if end.get("task") == task.slug]
    lock_holder = holder_of(task.directory / STEP_LOCK)
    return {
        "task": task.slug, "running": holder is not None, "pid": holder["pid"] if holder else None, "since": since, "seconds": seconds, "waits": waits,
        # the step that holds the lock when it is not the checks: a step of the task waits for it too
        "step": lock_holder["step"] if lock_holder and lock_holder["step"] != "checks" and alive(lock_holder["pid"]) else None,
        "last_seconds": last, "overdue": overdue, "say": overdue_say(task.slug, seconds, last) if overdue else None,
        "ended": ended_of(own[-1] if own else None, task.slug),
    }


def checks_stop(task: Task) -> dict:
    """Stop the task's checks: a term to the process the lock names, only while the lock is held by
    `checks`, and a wait until that run let it go. With no run, nothing is stopped and that is no error."""
    def stop_result(pid: int | None) -> dict:
        return {"task": task.slug, "stopped": pid is not None, "pid": pid, "ended": checks_status(task)["ended"]}

    holder = running_checks(task)
    if holder is None:
        return stop_result(None)
    pid = holder["pid"]
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return stop_result(None)
    except PermissionError as error:
        raise LandError(f"the checks of {task.slug} run in process {pid}, which this user may not stop ({error.strerror}); the user that started them stops them") from error
    deadline = time.monotonic() + STOP_WAIT
    while time.monotonic() < deadline:
        now = holder_of(task.directory / STEP_LOCK)
        # the run takes its line away last, after its commands ended and its result is kept
        if not alive(pid) or now is None or now["pid"] != pid:
            return stop_result(pid)
        time.sleep(0.1)
    raise LandError(
        f"the checks of {task.slug} were asked to stop, and process {pid} still runs after {STOP_WAIT} s; "
        f"`lem land checks {task.slug} --stop` asks again, and `lem land checks {task.slug} --status` says whether they still run",
    )


def criteria_red(task: Task) -> subprocess.CompletedProcess:
    """`lem criteria red` as a process of its own, as `lem_sibling` runs it (`APART`). On a stop of the
    checks it gets a term and its end is waited for, so that its own handler ends its tests and
    removes its two worktrees: it is never killed first, as `subprocess.run` does on an exception."""
    args = [sys.executable, "-B", str(SCRIPTS / "criteria.py"), "--repo", str(task.main), "red", task.slug]
    with tempfile.TemporaryFile("w+", encoding="utf-8") as out, tempfile.TemporaryFile("w+", encoding="utf-8") as err:
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
    """The machine checks on the tip: the commands, the serial ones, the criteria's tests, or the polish
    pass's run of them when its five inputs are the same now (`taken_from_polish`), and the bar. The
    step's SIGTERM handler holds from its first line to its last, the criteria's tests and the bar
    included: a stop ends what runs and keeps no result."""
    flags = {"stopping": False, "done": False}

    def stopped(*_: object) -> None:
        # one stop is enough: a second term, or one after the result is kept, changes nothing
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
    try:
        tip, found, commands = checks_ready(task)
        # the load gate, after every refusal the step makes before it runs anything, so that a run
        # that would be refused does not wait first
        gated = wait_for_load(task)
    except KeyboardInterrupt:
        raise LandError(f"the checks were stopped before their first command; `lem land checks {task.slug}` runs them again") from None
    logs = task.directory / "gate"
    logs.mkdir(exist_ok=True)
    # The commands that need the machine to themselves come after the others, each under the
    # repository's one lock for them (`project.py serial`), and only when the others passed. The field
    # of their result and of their `gate` event is `serial`, which the board reads.
    # The output folder and the events are named `gate`, which the board reads.
    serial = task.settings["checks"]["serial"]
    started = time.monotonic()
    ended: list[str] = []

    def end(how: str, say: str) -> None:
        """The one `gate.end` of the run, however it ends."""
        if not ended:
            ended.append(how)
            # a run that took the polish pass's result logs no `task.red`: its end names the pass's commit
            taken = taken_at(result.get("criteria"))
            script("project.py", task.worktree, "log", task.slug, "gate.end", f"result={how}", f"seconds:={round(time.monotonic() - started)}", f"tip={tip[:9]}",
                   *([f"taken={taken}"] if taken else []), f"say={say}")

    # No result of an earlier run stays while this one runs: a run cut off with no chance to clean
    # up (a kill) leaves none for its tip either.
    task.keep(gated=None, tree=None)
    # the start of the checks: the board draws them from here to their last result
    script("project.py", task.worktree, "log", task.slug, "gate.start", f"tip={tip[:9]}", f"commands:={len(commands) + len(serial)}")
    result: dict = {"task": task.slug, "tip": tip, "green": None, "commands": [], "load": gated}
    try:
        outcome, refusal = checks_body(task, flags, tip, found, commands, serial, logs, result)
        flags["done"] = True
    except KeyboardInterrupt:
        # a stop: what ran is ended, and no result is kept
        flags["done"] = True
        task.keep(gated=None, tree=None)
        result.update(result="stopped", say=checks_say(task.slug, "stopped"))
        end("stopped", result["say"])
        print(json.dumps(result, indent=2))
        raise LandError(f"the checks were stopped, and the command that ran is ended with what it started; `lem land checks {task.slug}` runs them again") from None
    except Exception:
        # an error of the step itself (git, the event log): the run ends, refused, and the error is the step's exit
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
    """What the checks refuse before their first command, and what they run on: the tip, the criteria and the commands."""
    task.need_landing()
    task.need_worktree()
    if "base" not in task.kept():
        raise LandError(f"`lem land base {task.slug}` comes first: the checks run on the tip that will land")
    tip = git(task.worktree, "rev-parse", "HEAD")
    # Before any command runs: the review reads the code as it will merge, so the polish pass comes first.
    try:
        found = criteria_of(task)
    except LandError as error:
        raise LandError(f"{error}. A builder repairs the test or the plan; the check is never edited to pass") from error
    missing = polish_missing(task, tip, found)
    if missing:
        raise LandError(missing)
    commands = task.gate()[0]
    if not commands:
        # `start` refuses a project with none; the main checkout's settings may lose them after it
        task.keep(gated=None, tree=None)
        raise LandError(
            f"the checks have no command to run, and checks that ran nothing show nothing: {NO_GATE} in the main checkout's .lem/project.toml, "
            f"and the branch brings none that the base commit lacks. Add the commands to checks.commands there, then run `lem land checks {task.slug}` again",
        )
    return tip, found, commands


def checks_body(task: Task, flags: dict, tip: str, found: dict, commands: list[str], serial: list[str], logs: Path, result: dict) -> tuple[str, str | None]:
    """The run itself: the commands, the serial ones, the criteria's tests (or the polish pass's result of
    them, `taken_from_polish`) and the bar. It fills `result`
    with what the step prints, its `say` among it, and gives back how the run ends and the refusal to
    exit with, none for a passed run."""
    # What git does not know before the first command. `need_worktree` refused any such file, so
    # this is empty unless something wrote one since; it is taken all the same, so that the
    # removal after the run can never reach a file that was there before it.
    there = untracked(task)
    results = result["commands"]
    running: list[subprocess.Popen] = []
    grace = GRACE
    output = logs / "01.log"
    try:
        for number, (command, apart) in enumerate([*((command, False) for command in commands), *((command, True) for command in serial)], start=1):
            if apart and any(entry["exit"] != 0 for entry in results):
                break
            output = logs / f"{number:02d}.log"
            line: str | list[str] = command
            grace = SERIAL_GRACE if apart else GRACE
            if apart:
                line = [sys.executable, "-B", str(SCRIPTS / "project.py"), "--repo", str(task.main), "serial", "--", command]
            with output.open("w", encoding="utf-8") as handle:
                # a group of its own, as criteria.py runs a test: what the command starts ends with it
                proc = subprocess.Popen(line, shell=not apart, cwd=task.worktree, stdout=handle, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)  # noqa: S602
                running.append(proc)
                code = proc.wait()
                end_group(running, grace)
            lines = [text for text in output.read_text(encoding="utf-8", errors="replace").splitlines() if text.strip()]
            last = lines[-1].strip() if lines else ""
            results.append({"command": command, "exit": code, "last": last, "output": str(output), **({"serial": True} if apart else {})})
            script("project.py", task.worktree, "log", task.slug, "gate", f"command={command}", f"exit:={code}", f"last={last}", f"tip={tip[:9]}", *(["serial:=true"] if apart else []))
    finally:
        # a stop ends the command that runs with its group; a serial command's wrapper gets the time of its own cleanup
        end_group(running, grace)
        # A file the commands wrote that git neither tracks nor ignores (Python's bytecode in a
        # repository with no rule for it) is the run's output, and nothing of it lands: it goes, with
        # the folders it leaves empty, red, green or stopped, so that the next step finds the worktree
        # clean. The worktree is the task's own, made by Lem.
        removed = sorted(set(untracked(task)) - set(there))
        for path in removed:
            remove_left(task, path)
        if removed:
            with output.open("a", encoding="utf-8") as handle:
                handle.write(f"land.py removed what the commands of the checks left untracked: {', '.join(removed)}\n")
        result["removed_untracked"] = removed
    green = all(entry["exit"] == 0 for entry in results)
    result.update(green=green, polish=task.kept().get("polish"))
    # A command of the checks that changed a tracked file, or made a commit, changed the tree it just judged.
    dirty = git(task.worktree, "status", "--porcelain")
    if green and dirty:
        result.update(result="refused", say=checks_say(task.slug, "refused", refused="a command of the checks changed what git tracks"))
        return "refused", (
            f"a command of the checks changed what git tracks, so its result is about another tree:\n{dirty}\n"
            f"put the files back (`git -C {task.worktree} checkout -- FILE`) and make the command change no tracked file, then run this again"
        )
    moved = git(task.worktree, "rev-parse", "HEAD")
    if green and moved != tip:
        result.update(result="refused", say=checks_say(task.slug, "refused", refused="a command of the checks made a commit on the branch"))
        return "refused", (
            f"a command of the checks made a commit on the branch ({tip[:9]}..{moved[:9]}), so its result is about another tree: "
            f"make the command commit nothing, put the branch back with `git -C {task.worktree} reset --hard {tip}`, then run this again"
        )
    if not green:
        red = [entry["command"] for entry in results if entry["exit"] != 0]
        result.update(result="red", say=checks_say(task.slug, "red", red=red))
        return "red", f"the checks are red on {len(red)} command(s): {'; '.join(red)}. A builder reads the output files; the checks are never edited to pass"
    # The commands of the checks are green. Now what no command of the project checks: that each criterion is
    # held by a test that fails without the change, and that the change did not lower the bar.

    def criteria_refused(stderr: str) -> tuple[str, str]:
        """The run refused by the check of the criteria, in the words its script gave."""
        result.update(result="refused", say=checks_say(task.slug, "refused", refused="the check of the criteria did not pass"))
        return "refused", f"{stderr.strip().removeprefix('criteria.py: ')}. A builder repairs the test or the plan; the check is never edited to pass"

    taken = None
    if not found["small"]:
        # A new read of the criteria, here and not the one `checks_ready` made before the load wait and the
        # commands: an approval or a recorded change since then counts. It refuses as a run of the tests would.
        read = script("criteria.py", task.main, "inputs", task.slug, check=False)
        if read.returncode != 0:
            result["criteria"] = None
            return criteria_refused(read.stderr)
        taken = taken_from_polish(task.kept().get("polish"), json.loads(read.stdout)["inputs"], small=False)
    if taken:
        # the pass ran these tests on this tip, against this base commit, plan file and settings: they run no second time
        result["criteria"] = taken
    else:
        held = criteria_red(task)
        try:
            result["criteria"] = json.loads(held.stdout)
        except ValueError:
            result["criteria"] = None
        if held.returncode != 0:
            return criteria_refused(held.stderr)
    # The fast track gives no reason for a lowered bar: it has no plan, and a lowered bar never takes the fast track.
    plan = "" if found["small"] else Path(found["plan"]).read_text(encoding="utf-8")
    now = change(task)
    result["bar"] = bar(task, now["base"], tip, plan)
    result["size"] = {"files": len(now["files"]), "lines": now["lines"], "in_parts": now["lines"] > READ_AT}
    refused = bar_refusal(result["bar"]["lowered"], found["small"])
    if refused:
        result.update(result="refused", say=checks_say(task.slug, "refused", refused="the change lowers the bar with no reason given"))
        return "refused", refused
    try:
        next_due = due(task)["due"]
    except LandError:
        # `read` says what stops it; the next step is still the review's
        next_due = "review"
    result.update(result="passed", say=checks_say(task.slug, "passed", next_due=next_due))
    # From here a stop changes nothing: the run passed, and its result is kept whole.
    flags["done"] = True
    task.keep(gated=tip, tree=git(task.worktree, "rev-parse", f"{tip}^{{tree}}"), checks={"commands": results, "criteria": result["criteria"], "bar": result["bar"], "size": result["size"]})
    return "passed", None


def end_group(running: list[subprocess.Popen], grace: float = GRACE) -> None:
    """End each command's process group and everything still in it: a term first, then a kill for
    what is left after `grace` seconds (a second, or the time of a serial wrapper's own cleanup)."""
    for proc in running:
        for sign, wait in ((signal.SIGTERM, grace), (signal.SIGKILL, GRACE)):
            try:
                os.killpg(proc.pid, sign)
            except (ProcessLookupError, PermissionError):
                break
            deadline = time.monotonic() + wait
            while time.monotonic() < deadline:
                try:
                    os.killpg(proc.pid, 0)
                except (ProcessLookupError, PermissionError):
                    break
                if proc.poll() is None:
                    try:
                        proc.wait(timeout=0.05)
                    except subprocess.TimeoutExpired:
                        pass
                else:
                    time.sleep(0.05)
            else:
                continue
            break
    running.clear()


def untracked(task: Task) -> list[str]:
    """Each file of the worktree that git neither tracks nor ignores, one by one, a file in a new folder too."""
    listed = run(["git", "-C", str(task.worktree), "status", "--porcelain", "--untracked-files=all", "-z"]).stdout.split("\0")
    return [entry[3:] for entry in listed if entry.startswith("?? ")]


def remove_left(task: Task, path: str) -> None:
    """Remove one file a command of the checks left untracked, and each folder above it that it leaves
    empty, up to the worktree's root. A link is removed as a link, never followed."""
    root = task.worktree.resolve()
    file = root / path
    # git lists no file under a linked folder, so the folder that holds it is inside the worktree
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
    """Every path that differs between two trees. A rename counts as the path that went and the path that came."""
    return git(task.worktree, "diff", "--name-only", "--no-renames", old, new).splitlines()


def due(task: Task) -> dict:
    """Whether a review is due now, and the least it may be. Within that, the one who starts the review chooses."""
    now = change(task)
    found = criteria_of(task)
    kept = task.kept()
    # the fast track has no plan, and is the one task of its builder
    tasks = 1 if found["small"] else tasks_of(Path(found["plan"]).read_text(encoding="utf-8"))
    return due_of(now, kept.get("reads", []), kept.get("resolution"), careful(task, now), tasks, found["small"], backlog_of(task))


def due_of(now: dict, reads: list[dict], resolution: dict | None, why_careful: list[str], tasks: int, small: bool, folder: str) -> dict:
    """`due` from what it read: the change as `change` gives it, the kept reviews and resolution,
    each reason the request is careful, the plan's count of tasks, the track, and the backlog folder."""
    answered = [read for read in reads if read["answered"]]
    # The read of a conflict's resolution is no round: the two rounds are of the change itself.
    rounds = [read for read in answered if read.get("of") != "resolution"]
    facts = {"round": len(rounds) + 1, "careful": why_careful, "tasks": tasks, "small": small, "lines": now["lines"], "in_parts": now["lines"] > READ_AT, "resolution": None, **now}
    silent = len(reads) - max((index for index, read in enumerate(reads) if read["answered"]), default=-1) - 1
    if resolution and resolution["covered"] and resolution["read"] is None and resolution["patch"] == now["patch"]:
        # A builder resolved a conflict with the base, after a review covered the change: what the
        # review saw stands, and what the builder chose where the two sides met gets one read, or
        # the project's full set for a careful request. Anything committed after the resolution
        # makes it a change like any other, which the rules below review whole.
        files = ", ".join(resolution["files"])
        facts.update(
            floor="full" if why_careful else "read", attempt=len(reads) + 1, round=max(len(rounds), 1),
            resolution={**{key: resolution[key] for key in ("files", "before", "after", "base", "onto")},
                        "range_diff": f"git range-diff {resolution['base'][:12]}..{resolution['before'][:12]} {resolution['onto'][:12]}..{resolution['after'][:12]}"},
        )
        if silent >= 2:
            return {"due": "owner", "why": f"not reviewed: the read of the conflict's resolution in {files} was started twice and no source answered", **facts}
        why = f"the request is careful: {why_careful[0]}; a builder resolved a conflict with the base in {files}" if why_careful else (
            f"a builder resolved a conflict with the base in {files}: one read of what the resolution changed, and the earlier review stands for the rest"
        )
        return {"due": "review", "why": why, **facts}
    # The floor is what no judgment goes under. Which profiles fit a change is read from the diff
    # and from what each profile is for, by an agent: no code and no list of words decides that.
    if why_careful:
        floor, why = "full", f"the request is careful: {why_careful[0]}"
    elif facts["tasks"] > LARGE_AFTER:
        floor, why = "round", f"the plan has {facts['tasks']} tasks, more than three"
    elif any(read["must_fix"] for read in answered):
        floor, why = "round", "an earlier review found a must-fix: after its fix a round reviews the change"
    else:
        floor, why = "read", "nothing asks for more than one read: the diff and what each profile is for decide"
    facts.update(floor=floor, attempt=len(reads) + 1)
    # What the newest review that answered leaves open, for this change as it is now.
    last = answered[-1] if answered else None
    unmet = []
    if last:
        if last["must_fix"]:
            unmet.append(f"the last one left {last['must_fix']} must-fix")
        if not covered(folder, last, now):
            unmet.append("nobody reviewed what changed after it")
        # the read of a resolution is as large as the resolution; the change itself was reviewed by the round before it
        sized = rounds[-1] if last.get("of") == "resolution" and rounds else last
        if KINDS.index(sized["kind"]) < KINDS.index(floor):
            unmet.append(f"it was {KIND_SAYS[sized['kind']]}, and this change gets {KIND_SAYS[floor]} at the least ({why})")
    if last and not unmet:
        if last.get("of") == "resolution":
            return {"due": "none", "why": f"round {last['round']} reviewed this change, one read of the conflict's resolution read what changed after it, and neither left a must-fix", **facts}
        return {"due": "none", "why": f"round {last['round']} reviewed this change and left no must-fix", **facts}
    if len(rounds) >= 2:
        return {"due": "owner", "why": f"two rounds reviewed it: {', and '.join(unmet)}", **facts}
    if silent >= 2:
        return {"due": "owner", "why": "not reviewed: the review was started twice and no source answered", **facts}
    return {"due": "review", "why": why, **facts}


def talk_due(task: Task, state: dict) -> str | None:
    """Why this request's plan had to be talked through before any code; none when it did not.

    A talk is a step before the build, so only the plan itself calls for one: its own `careful:
    yes` line, or more than three tasks. The owner's later word, the review's call or an edit of
    Lem's own settings gives the full review set at the landing and no talk after the code exists."""
    if plan_careful(task):
        return "the plan says that the request is careful"
    if state["tasks"] > LARGE_AFTER:
        return f"the plan has {state['tasks']} tasks, more than three"
    return None


def events_of(task: Task) -> list[dict]:
    """The task's events in the log `project.py` writes, oldest first."""
    log = task.directory.parent.parent / "events.jsonl"
    found = []
    lines = lem_state.jsonl_lines(log.read_text(encoding="utf-8")) if log.is_file() else []
    for number, line in enumerate(lines, start=1):
        if f'"task": {json.dumps(task.slug)}' not in line:
            continue
        try:
            record = json.loads(line)
        except ValueError as error:
            raise LandError(f"line {number} of {log} is not JSON ({error}); the log is written by `lem project log`, never by hand") from error
        if record.get("task") == task.slug:
            found.append(record)
    return found


def events_all(task: Task) -> list[dict]:
    """Every event of the log `project.py` writes, oldest first; a line that does not read is passed over."""
    log = task.directory.parent.parent / "events.jsonl"
    found = []
    for line in lem_state.jsonl_lines(log.read_text(encoding="utf-8")) if log.is_file() else []:
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if isinstance(record, dict):
            found.append(record)
    return found


def talk_of(task: Task) -> dict | None:
    """The newest record of the task's plan talk in the event log."""
    return next((record for record in reversed(events_of(task)) if record.get("event") == "plan.talk"), None)


def untalked(task: Task, state: dict) -> str | None:
    """Why a careful request had no plan talk, when none was due: it became careful after its plan."""
    if not state["careful"] or talk_due(task, state):
        return None
    call = review_call(task)
    how = [
        *(["by the owner's word"] if owner_says_careful(task) else []),
        *(["by its change to the settings"] if settings_edit(task, state) or local_settings_edit(task, state) else []),
        *(["by its review"] if call and call["careful"] else []),
    ]
    return f"- no plan talk: the request became careful after its plan, {' and '.join(how)}"


def careful_line(task: Task, state: dict) -> str:
    """Whether the request is careful, as one line of the pull request's checks: each reason it is,
    and the newest review's call with its reason when the review said no."""
    call = review_call(task)
    line = "- careful: yes, " + "; ".join(state["careful"]) if state["careful"] else "- careful: no"
    if call is None:
        return line + "; no review that answered made the call"
    if not call["careful"]:
        return line + f"; the review says no: {reason(call['why'])}"
    return line


def talked(talk: dict) -> str:
    """The plan talk as one line of the pull request's checks: the turns, with the bound of its rules
    when the talk went over it, and the positions, then each other count the event holds, in the
    event's order."""
    def many(count: int, one: str, more: str) -> str:
        return f"{count} {one if count == 1 else more}"
    counts = [
        many(value, *TALK_SAYS[key]) if key in TALK_SAYS else f"{key}: {value}"
        for key, value in talk.items()
        if key not in TALK_FIRST and isinstance(value, int) and not isinstance(value, bool)
    ]
    bound = talk.get("bound")
    over = f", over the bound of {bound} for its {many(talk['questions'], 'question', 'questions')}" if isinstance(bound, int) and talk["turns"] > bound else ""
    return (
        f"- the plan talk: {talk['reviewer']} argued the plan with its defender, {many(talk['turns'], 'turn', 'turns')}{over}; "
        f"{many(talk['settled'], 'position', 'positions')} settled by the two, {talk['open']} left open"
        + (f"; {', '.join(counts)}" if counts else "")
    )


def polished(polish: dict) -> str:
    """The polish pass as one line of the pull request's checks, from what `polish --done` logged.
    The checks refuse a task on the standard track with no pass that is done."""
    commits, filed = polish["commits"], len(polish["filed"])
    return f"- the polish pass: {commits} commit{'' if commits == 1 else 's'}, {filed} item{'' if filed == 1 else 's'} filed in the backlog"


def criteria_read_of(task: Task) -> dict | None:
    """The newest record of the personas' read of the task's criteria in the event log."""
    return next((record for record in reversed(events_of(task)) if record.get("event") == "criteria.read"), None)


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
    """Whether a `criteria.read` event has the form `lem project log` gives it; one that nobody
    answered names no family."""
    counts = ("asked", "answered", "criteria", "flagged")
    families, silent = read.get("families"), read.get("silent")
    return (
        read.get("by") in ("lem", "lead")
        and all(isinstance(read.get(key), int) and not isinstance(read.get(key), bool) and read[key] >= 0 for key in counts)
        and isinstance(families, list) and bool(families) == bool(read["answered"]) and all(isinstance(name, str) and name.strip() for name in families)
        and isinstance(silent, list) and all(isinstance(item, dict) and set(item) == {"name", "why"} for item in silent)
        and isinstance(read.get("split"), bool) and isinstance(read.get("digest"), str) and read["answered"] <= read["asked"]
    )


def read_skip_form(slug: str) -> str:
    """The command that writes the owner's word to skip the personas' read, as the landing knows it."""
    return f"`lem decisions log {slug} --by owner --what \"{READ_SKIP['what']}\" --chose \"{READ_SKIP['chose']}\" --why \"THE OWNER'S ANSWER\"`"


def read_skipped(task: Task) -> tuple[dict | None, str | None]:
    """The owner's newest word to skip the personas' read, when an approval of his follows it and both
    came before any lead of the task started; or why the word on record does not count. A lead writes
    the criteria on the standard track from a complete request, where the read is the only approval and always runs, so a word or an
    approval after the first state that names a lead belongs to such a task. Neither, with no word of his."""
    events = events_of(task)
    words = [
        index for index, record in enumerate(events)
        if record.get("event") == "decision.taken" and record.get("by") == "owner"
        and record.get("what") == READ_SKIP["what"] and record.get("chose") == READ_SKIP["chose"]
    ]
    if not words:
        return None, None
    word = words[-1]
    lead = next(
        (index for index, record in enumerate(events)
         if record.get("event") == "task.state" and any(line.startswith("lead:") for line in [record.get("text", ""), *record.get("lines", [])])),
        None,
    )
    approval = next((index for index in range(word + 1, len(events)) if events[index].get("event") == "criteria.approved" and events[index].get("by") == "owner"), None)
    complete = (
        "the lead wrote the criteria, and on the standard track from a complete request the read always runs, as the only approval there "
        f"(`stages/plan.md`, step 1): the lead runs it and writes `lem project log {task.slug} criteria.read` with the form {READ_FORM}"
    )
    if lead is not None and lead < word:
        return None, f"a lead of {task.slug} started before the owner's word to skip the personas' read: {complete}"
    if lead is not None and (approval is None or lead < approval):
        return None, f"a lead of {task.slug} started before the owner's approval that came after the word to skip the personas' read: {complete}"
    if approval is None:
        return None, (
            f"the owner's word to skip the personas' read of {task.slug}'s criteria is on record, and no approval of the owner's came after it: "
            f"the owner's yes to the criteria is kept with `lem criteria approve {task.slug} --file FILE` (`stages/interview.md`, step 7)"
        )
    return {"word": events[word], "approval": events[approval]}, None


def interview_unapproved(events: list[dict], approvals: list[dict], small: bool) -> bool:
    """Whether a task on the standard track had an interview (`interview.start` among its EVENTS) and
    its criteria carry no approval of the owner's, nor one made while it ran without him (`alone`):
    the interview ends with his yes (`stages/interview.md`, steps 6 and 7), and the lead's freeze of a
    read is the complete request's approval, not his. The fast track asks nothing of it."""
    if small or not any(event.get("event") == "interview.start" for event in events):
        return False
    return not any(approval.get("by") in ("owner", "alone") for approval in approvals)


def when(event: dict) -> str:
    """The time an event happened: its own, or for one a resumed task copied from the task it came
    from (`lem project resume`), the time it had there (`was_at`), which an approval's `at` keeps too."""
    return event.get("was_at") or event["ts"]


def approved_after(found: dict, read: dict) -> bool:
    """Whether the owner himself approved the criteria at the read's time or after it. A freeze of
    a read (`by: read`) and Lem's approval on the fast track are not his yes."""
    return any(approval["by"] == "owner" and approval["at"] >= when(read) for approval in found.get("approvals", []))


def approved_alone(found: dict, read: dict) -> bool:
    """Whether Lem or the lead approved the criteria at the read's time or after it while the task ran
    without the owner (`lem criteria approve --alone`): enough to propose, never green."""
    return any(approval["by"] == "alone" and approval["at"] >= when(read) for approval in found.get("approvals", []))


def criteria_waited(events: list[dict]) -> dict | None:
    """The newest wait of the task's criteria for the owner's yes, with the approval that ended it, from
    the task's events oldest first; None when no such wait ended. The wait is the newest `held` state
    whose line is a `CRITERIA_WAIT` one other than `FAST_GREW` (that task went to an interview), and
    its end is the first approval after it that is the owner's or made while the task ran without him
    (`WAIT_ENDS`), whoever gave it: an approval of his after Lem's is no end of that wait."""
    waits = [
        index for index, record in enumerate(events)
        if record.get("event") == "task.state" and record.get("status") == "held"
        and any(str(line).startswith(CRITERIA_WAIT) and not FAST_GREW.search(str(line)) for line in [record.get("text", ""), *record.get("lines", [])])
    ]
    if not waits:
        return None
    end = next(
        (record for record in events[waits[-1] + 1:] if record.get("event") == "criteria.approved" and record.get("by") in WAIT_ENDS),
        None,
    )
    return {"from": events[waits[-1]]["ts"], "end": end} if end else None


def approval_said(found: dict, waited: dict | None) -> str:
    """The part of the read's line that says who approved the criteria and when; empty when nobody
    whose approval counts for the build did. With a wait for his yes (`criteria_waited`), the part
    says when the wait began and whether his yes ended it, and names a later approval of his."""
    approval = found.get("approved")
    if waited:
        end = waited["end"]
        said = f"the criteria waited for the owner's yes from {utc(waited['from'])}, " + (
            f"and the owner gave it on {utc(end['ts'])}" if end["by"] == "owner"
            else f"and the wait ended without the owner: approved on {utc(end['ts'])} while the task ran without the owner"
        )
        if approval and approval["by"] == "owner" and approval["number"] != end.get("number"):
            said += f"; the owner approved them {'again ' if end['by'] == 'owner' else ''}on {approval['at'][:10]}"
        return said
    # a plan is the standard track's: its criteria are the owner's approval, or the lead's freeze by a read, which is not his
    if approval and approval["by"] == "owner":
        return f"the owner approved them on {approval['at'][:10]}"
    if approval and approval["by"] == "alone":
        return f"approved on {approval['at'][:10]} while the task ran without the owner"
    return ""


def read_line(read: dict | None, found: dict, quiet_reads: int = 0, skipped: dict | None = None, waited: dict | None = None) -> str:
    """The personas' read of the criteria and his approval, as one line of the pull request's checks;
    `skipped` is his word to skip the read with his approval after it, as `read_skipped` gives them,
    and `waited` the criteria's wait for his yes with its end, as `criteria_waited` gives them."""
    approved = approval_said(found, waited)
    if read and not read["answered"]:
        # propose refuses the first such read, so this is the second in a row at the least
        return (
            f"- the criteria were not read by the personas: {quiet_reads} reads in a row, and none of the {read['asked']} personas asked answered"
            + (f"; {approved}" if approved else "; the build started with no wait for the owner")
        )
    if read:
        count = len(read["families"])
        line = (
            f"- the criteria were read by {read['answered']} of {read['asked']} personas asked, {FAMILIES.get(count, f'{count} model families')} ({', '.join(read['families'])}); "
            + ("nobody confused" if not read["flagged"] else f"{read['flagged']} of {read['criteria']} {'criterion' if read['criteria'] == 1 else 'criteria'} flagged")
            + ("; the two families split" if read["split"] else "")
            + "".join(f"; no answer from {source['name']} ({source['why']})" for source in read["silent"])
        )
        if approved:
            return f"{line}; {approved}"
        return line + "; the build started with no wait for the owner"
    if skipped:
        return f"- the criteria: not read by the personas, on the owner's word ({skipped['word']['at'][:10]}); the owner approved them"
    return "- the criteria: no read by the personas is on record" + (f"; {approved}" if approved else "")


def unread(read: dict | None, found: dict) -> str | None:
    """The line that says the criteria are not the ones the personas read, and what changed them.
    The plan's criteria are the expected ones (the checks refuse any other), so they are compared."""
    if read is None or not read["answered"] or found["criteria_digest"] == read["digest"]:
        return None
    # an approval of his after the read changed the criteria only when it holds other criteria than the read did
    his = [approval for approval in found.get("approvals", []) if approval["by"] == "owner" and approval["at"] >= when(read) and approval["digest"] != read["digest"]]
    what = [*([f"by the owner's approval {his[-1]['number']}"] if his else []), *(["by a change of the build"] if any(change["at"] >= when(read) for change in found.get("history", [])) else [])]
    return f"- the criteria changed after the personas' read{', ' + ' and '.join(what) if what else ''}, and the change was not read"


def named(value: object, where: str) -> list[dict]:
    """A list of names, each with its why: the profiles of a round, or the sources that did not answer."""
    if not isinstance(value, list) or not all(
        isinstance(item, dict) and set(item) == {"name", "why"} and all(isinstance(text, str) and text.strip() for text in item.values()) for item in value
    ):
        raise LandError(f"`{where}` is a list of {{\"name\": ..., \"why\": ...}}, each with both as text")
    return value


def same_checks(results: list[dict], commands: list[str], serial: list[str]) -> bool:
    """Whether a kept result of the checks (its `commands`, each with its `serial` flag) ran the commands
    the checks have now, in their order: the plain ones, then the serial ones. With no command there is
    no result to hold: only the task that adds one lands (`docs/settings.md`, `[checks]`)."""
    ran = [(entry.get("command"), bool(entry.get("serial"))) for entry in results]
    now = [*((command, False) for command in commands), *((command, True) for command in serial)]
    return bool(commands) and ran == now


def gate_missing(task: Task, tip: str) -> str | None:
    """Why no result of the checks holds for `tip`, in words for a refusal; None when one holds."""
    if gate_holds(task, tip):
        return None
    kept = task.kept()
    if kept.get("gated") and not same_checks((kept.get("checks") or {}).get("commands") or [], task.gate()[0], task.settings["checks"]["serial"]):
        return "the commands of the checks are not the ones that passed (checks.commands and checks.serial of the main checkout's .lem/project.toml changed since), so their green result is not this one's"
    return "no green check is on record for this tip"


def gate_holds(task: Task, tip: str) -> bool:
    """Whether the result of the checks holds for `tip`: it ran the commands the checks have now
    (`same_checks`: the main checkout's settings count at once, an edit nobody committed too), and the
    tip is the commit they passed on, or that commit
    with commits after it that only add the backlog items `file` wrote for this landing's reviews.
    Those hold no code and no test, so they ask for no checks again; the result is then kept for the
    tip, so that `land` finds what it checks. Any other commit, an item written by hand among them,
    asks for the checks."""
    kept = task.kept()
    gated = kept.get("gated")
    if gated and not same_checks((kept.get("checks") or {}).get("commands") or [], task.gate()[0], task.settings["checks"]["serial"]):
        return False
    if gated == tip:
        return True
    if not gated or not holds_commit(task, gated, tip):
        return False
    items = {defect["item"] for read in kept.get("reads", []) if read["answered"] for defect in outside_of(read) if defect.get("item")}
    rows = [row.split("\t", 1) for row in git(task.worktree, "diff", "--name-status", "--no-renames", gated, tip).splitlines()]
    if not rows or not all(status == "A" and path in items for status, path in rows):
        return False
    task.keep(gated=tip, tree=git(task.worktree, "rev-parse", f"{tip}^{{tree}}"))
    return True


def branch_items(task: Task) -> list[dict]:
    """Each item the branch adds to the backlog folder that `file` did not write for a review: what
    the fast track's builder or the polish pass filed, with its `where` and its title."""
    folder = backlog_of(task)
    base = git(task.worktree, "merge-base", "HEAD", task.onto)
    written = {defect["item"] for read in task.kept().get("reads", []) for defect in outside_of(read) if defect.get("item") and not defect.get("named")}
    rows = [row.split("\t", 1) for row in git(task.worktree, "diff", "--name-status", "--no-renames", "--diff-filter=A", base, "HEAD").splitlines()]
    found = []
    for _, path in rows:
        if not path.startswith(folder + "/") or path in written:
            continue
        item = item_of(task.worktree / path)
        front, lines = item if item else ({}, [])
        found.append({"item": path, "where": front.get("where"), "title": lines[0][2:].strip() if lines else None})
    return found


def cmd_file(task: Task, again: bool) -> dict:
    """File each defect a review saw outside the change as an item of the backlog, and commit the items."""
    task.need_landing()
    task.need_worktree()
    reads = task.kept().get("reads", [])
    tip = git(task.worktree, "rev-parse", "HEAD")
    folder = backlog_of(task)
    today = date.today().isoformat()
    # what the branch filed itself, before the review: a defect at the same place is that item
    on_branch = branch_items(task)
    filed, same, named, gone, written = [], [], [], [], {}
    for read in reads:
        if not read["answered"]:
            continue
        for defect in outside_of(read):
            if defect.get("item"):
                if in_tree(task, tip, defect["item"]):
                    continue
                if not again:
                    gone.append({"round": read["round"], "title": defect["title"], "item": defect["item"]})
                    continue
            match = next((item for item in on_branch if item["where"] == defect["where"]), None)
            if match and not defect.get("item"):
                defect["item"], defect["named"] = match["item"], True
                named.append({"round": read["round"], "title": defect["title"], "item": match["item"], "where": defect["where"], "its_title": match["title"]})
                continue
            # The first name that holds this very defect is its item; the first that is free gets it.
            # A name that holds another defect is passed: an extra item is the price, never a lost one.
            for name in names_for(defect):
                path = f"{folder}/{name}"
                file = task.worktree / path
                if holds(file, defect):
                    same.append({"round": read["round"], "title": defect["title"], "item": path})
                    break
                if not (file.exists() or file.is_symlink()):
                    file.parent.mkdir(parents=True, exist_ok=True)
                    write_whole(
                        file,
                        f"---\nworth: later\nwhere: {defect['where']}\nadded: {today}\n---\n# {defect['title']}\n\n{defect['what']}\n\n"
                        f"Seen outside the change by review round {read['round']} of task {task.slug} ({read.get('date', today)}); the base commit has it.\n",
                    )
                    filed.append({"round": read["round"], "title": defect["title"], "item": path})
                    written.setdefault(read["round"], []).append(path)
                    break
            defect["item"] = path
    # One commit for each round, of its new items and nothing else: the worktree was clean. A commit
    # hook of the project may refuse the message, which has Lem's form and not the project's: the
    # items stay written, and a builder commits them in the project's form, after which a second
    # run finds each one by its defect and records it.
    for number, paths in written.items():
        git(task.worktree, "add", "--", *paths)
        made = run(["git", "-C", str(task.worktree), "commit", "-q", "-m", f"docs(backlog): what review round {number} saw outside {task.slug}", "--", *paths], check=False)
        if made.returncode != 0:
            said = " ".join((made.stderr or made.stdout).split()) or f"git exited {made.returncode} and said nothing"
            raise LandError(
                f"the commit of the backlog items of review round {number} was refused, most likely by a commit hook of the project: {said}. "
                f"The items are written and staged in the worktree ({', '.join(paths)}): a builder commits them with a message in the form "
                f"the hook asks for (`git -C {task.worktree} commit -m MESSAGE -- {' '.join(paths)}`), never with --no-verify, "
                f"then `lem land file {task.slug}` runs again and finds each item by its defect",
            )
    tip = git(task.worktree, "rev-parse", "HEAD")
    if filed or same or named:
        items = [{**entry, "new": True} for entry in filed] + [{**entry, "new": False} for entry in [*same, *named]]
        script("project.py", task.worktree, "log", task.slug, "review.filed", f"items:={json.dumps(items)}", f"tip={tip[:9]}")
    # A run cut off after its commit finds each item again by its defect, so this write comes last.
    task.keep(reads=reads)
    return {"task": task.slug, "filed": filed, "same": same, "named": named, "gone": gone, "tip": tip}


def task_file(value: str, flag: str, directory: Path, here: Path) -> str:
    """The file a step's FLAG names: VALUE from the working directory HERE (or an absolute path), else a
    relative VALUE in the task's DIRECTORY. A LandError that names each place it looked when neither
    has it."""
    given = Path(value)
    first = given if given.is_absolute() else here / given
    if first.is_file():
        return str(first)
    if given.is_absolute():
        raise LandError(f"{value} is not a file; {flag} names a file, by its path or by its name in the task directory {directory}")
    second = directory / given
    if second.is_file():
        return str(second)
    raise LandError(f"{value} is not a file in the working directory ({first}) nor in the task directory ({second}); {flag} names a file by its path, or by its path inside the task directory")


def failed_attempt(said: dict) -> bool:
    """Whether a review's record is of an attempt that got no answer at all: nobody in `answered`, a
    reason for each source in `silent`, and no finding. The review agent writes it when every source
    was silent, and the landing session when the review agent itself ended with no files; it counts as
    an attempt, so a second one in a row sends the request on as not reviewed (`due_of`)."""
    silent = said.get("silent")
    return (said.get("answered") == [] and isinstance(silent, list) and bool(silent)
            and all(isinstance(item, dict) and str(item.get("why") or "").strip() for item in silent)
            and not any(said.get(key) for key in ("must_fix", "should", "nit", "outside")))


def record_tip_refusal(said: object, tip: str, slug: str) -> str | None:
    """Why a review's record whose `tip` is SAID is not the review of the branch at TIP; None when it is.
    The attempt counts the records, so a review of an earlier tip carries the same number."""
    if said == tip:
        return None
    if not isinstance(said, str) or not re.fullmatch(r"[0-9a-f]{40}", said):
        return f"`tip` in the record is the whole commit the review read, 40 hex digits, as `lem land read {slug}` printed it, and it is {said!r}"
    return (f"the record is of the review of {said[:12]}, and the branch is at {tip[:12]} now: that review read another change, and it is not written down. "
            f"`lem land read {slug}` says what is due for this one")


def cmd_read(task: Task, record: str | None) -> dict:
    task.need_landing()
    task.need_worktree()
    state = due(task)
    missing = gate_missing(task, state["tip"])
    if missing:
        raise LandError(f"the review is of the tip the checks passed on, and {missing}; `lem land checks {task.slug}` comes first")
    reads = task.kept().get("reads", [])
    if record is None:
        # The review starts when it is due, and its record ends it. A second `read` of the same
        # attempt, after a cut-off run or before `file`, is the same review and logs no second start.
        if state["due"] == "review" and not any(
            event.get("event") == "review.start" and event.get("attempt") == state["attempt"] for event in events_of(task)
        ):
            script("project.py", task.worktree, "log", task.slug, "review.start", f"attempt:={state['attempt']}", f"floor={state['floor']}")
        rules = json.loads(script("project.py", task.worktree, "rules", "--range", f"{state['base']}..{state['tip']}").stdout)["rules"]
        return {
            "task": task.slug, "due": state["due"], "why": state["why"], "floor": state["floor"], "kinds": KIND_SAYS, "round": state["round"],
            # the number the record of this review carries, so that the same record is never written down twice,
            # and the tip it reads, which the record names too
            "attempt": state["attempt"], "tip": state["tip"],
            # the defects outside the change that reviews saw and that have no item yet: `land.py file` files them
            "to_file": to_file(reads),
            "careful": state["careful"], "tasks": state["tasks"], "small": state["small"], "lines": state["lines"], "in_parts": state["in_parts"],
            # a builder's resolution of a conflict with the base, when the review due is the read of it: what it changed is
            # what `range_diff` shows, the branch's commits before the rebase beside the same commits after it
            "resolution": state["resolution"],
            "reads": [{key: value for key, value in read.items() if key not in ("contents", "carried")} for read in reads],
            # what a reviewer gets, and nothing of the builder's reasoning
            "inputs": {
                # the owner's words as given, and the request as Lem wrote it down, where the task has them
                **{name: str(task.directory / file) for name, file in (("words", "ask.txt"), ("request", "task.md")) if (task.directory / file).is_file()},
                "plan": criteria_of(task)["plan"], "range": f"{state['base']}..{state['tip']}",
                "worktree": str(task.worktree), "rules": [rule["file"] for rule in rules], "bar": task.kept().get("checks", {}).get("bar"),
                # what must never go wrong, from the main checkout's settings: the review reads the diff against each
                "topics": task.settings["flow"]["topics"],
                # what the branch filed in the backlog before the review: a defect named there is not reported again
                "filed": branch_items(task),
                # where the project's review tool keeps each profile and lens, with what each is for
                "review": task.settings["places"]["review"]["path"],
            },
        }
    if state["due"] != "review":
        raise LandError(f"no review is due: {state['why']}")
    try:
        said = json.loads(Path(record).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise LandError(f"{record} does not read as JSON ({error}); --record names the file that says what the review was and what it found") from error
    known = {"attempt", "tip", "kind", "ran", "left_out", "answered", "silent", "bar", "must_fix", "should", "nit", "outside", "careful", "careful_why"}
    if not isinstance(said, dict) or set(said) - known or not {"attempt", "tip", "kind", "answered"} <= set(said):
        raise LandError(f"the record is one object with `attempt`, `tip`, `kind` and `answered`, and of the others what applies: {', '.join(sorted(known))}")
    # A record that is sent again, after a run that was cut off or by mistake, must not count as
    # a second review: it says which start of the review it is, and only the next one is taken.
    if said["attempt"] != state["attempt"]:
        raise LandError(
            f"the record says attempt {said['attempt']!r}, and the next review of this task is attempt {state['attempt']}: "
            + ("that review is written down already" if said["attempt"] in [read.get("attempt") for read in reads] else "`lem land read` prints the number a record carries"),
        )
    # The attempt counts the records, not the tips: the record also names the tip its review read.
    stale = record_tip_refusal(said["tip"], state["tip"], task.slug)
    if stale:
        raise LandError(stale)
    kind = said["kind"]
    if kind not in KINDS:
        raise LandError(f"`kind` is one of {', '.join(KINDS)}: {'; '.join(f'{name} is {says}' for name, says in KIND_SAYS.items())}")
    if KINDS.index(kind) < KINDS.index(state["floor"]):
        raise LandError(f"this change gets {KIND_SAYS[state['floor']]} at the least ({state['why']}), and the record says {KIND_SAYS[kind]}")
    # The careful call is the review's own reading of the diff against the project's topics, by an
    # agent that did not build it: it is what lets an agent merge, or keeps the merge a person's.
    # A review that got no answer at all, written down by the session when its agent died, makes none:
    # it counts as an attempt, and the next one makes the call.
    call, call_why = said.get("careful"), said.get("careful_why")
    failed = failed_attempt(said) and call is None and call_why is None
    if not failed and (not isinstance(call, bool) or not isinstance(call_why, str) or not call_why.strip() or "\n" in call_why.strip()):
        raise LandError(
            "the record makes the careful call: \"careful\": true or false, the review's own reading of the diff against each of the project's topics "
            "(`topics` in what `lem land read` printed), and \"careful_why\": one line that names the topic the change reaches, or what was checked to say that it reaches none",
        )
    if call and kind != "full":
        raise LandError(
            f"a change the review calls careful gets the project's full set, and the record says {KIND_SAYS[kind]}: "
            "the review runs the full set and writes its record with \"kind\": \"full\"",
        )
    ran, left_out, silent, bar_says = (named(said.get(key, []), key) for key in ("ran", "left_out", "silent", "bar"))
    answered = said["answered"]
    if not isinstance(answered, list) or not all(isinstance(source, str) and source.strip() for source in answered):
        raise LandError("`answered` is the list of the sources that answered, by name; an empty list says that none did")
    if kind != "read" and not ran and not failed:
        raise LandError("a round names each profile it ran in `ran`, with why that profile fits this change")
    if kind == "full" and left_out:
        raise LandError(
            "the project's full set leaves no profile out: a profile may be added to it, never dropped; "
            "write \"left_out\": [] on a full review"
        )
    counts = {key: said.get(key, 0) for key in ("must_fix", "should", "nit")}
    if not all(isinstance(count, int) and not isinstance(count, bool) and count >= 0 for count in counts.values()):
        raise LandError("`must_fix`, `should` and `nit` are counts")
    outside = defects_of(said.get("outside", []))
    if not answered and (any(counts.values()) or outside):
        raise LandError("the record has findings and no source that answered: `answered` names who found them")
    # A lowered bar is what the owner reads himself, so the review says what it thinks of each one.
    lowered = sorted({entry["file"] for entry in task.kept().get("checks", {}).get("bar", {}).get("lowered", [])})
    unsaid = [file for file in lowered if file not in {entry["name"] for entry in bar_says}]
    if answered and unsaid:
        raise LandError(
            f"the change lowers the bar in {', '.join(unsaid)} and the record says nothing of it: "
            "`bar` holds one {\"name\": FILE, \"why\": WHAT THE REVIEW SAYS OF THE BUILDER'S REASON} for each such file",
        )
    entry = {
        "attempt": state["attempt"], "round": state["round"], "kind": kind, "ran": ran, "left_out": left_out, "answered": answered, "silent": silent, "bar": bar_says, **counts, "outside": outside,
        "careful": call, "careful_why": call_why.strip() if isinstance(call_why, str) else None,
        "date": date.today().isoformat(), "verdict": "not reviewed" if not answered else "must-fix" if counts["must_fix"] else "clean", "tip": state["tip"][:9], "patch": state["patch"],
        # the read of a builder's resolution of a conflict, which is no round of the change
        **({"of": "resolution"} if state["resolution"] else {}),
    }
    # The event first: a run that is cut off between the two writes the review down at its next
    # run, and the second event has the same attempt, by which a reader of the log knows it.
    script("project.py", task.worktree, "log", task.slug, "review", *(f"{key}:={json.dumps(value)}" for key, value in entry.items()))
    # The contents of the change stay out of the log: only `covers` reads them, from the kept record.
    task.keep(reads=[*reads, {**entry, "contents": state["contents"]}])
    if state["resolution"] and answered:
        # the resolution is read: from here the rules of the change hold again
        task.keep(resolution={**task.kept()["resolution"], "read": state["attempt"]})
    # A change the review calls careful and the plan did not is a lesson about the plan's call: one
    # event for the retro, the first time a review finds it.
    if answered and call and not plan_careful(task) and not any(record.get("event") == "careful.missed" for record in events_of(task)):
        script("project.py", task.worktree, "log", task.slug, "careful.missed", f"round:={state['round']}", f"why={call_why.strip()}")
    return {"task": task.slug, "recorded": entry, "next": due(task)["due"], "to_file": to_file(task.kept()["reads"])}


def not_green(task: Task, state: dict) -> list[str]:
    """Each reason for which this request is not green, one line each; none when it is green."""
    reasons = []
    # The fast track has no interview, no read of its criterion, no plan. A task on it that is
    # careful after all is read by a person, whatever its checks and its review say.
    if criteria_of(task)["small"] and state["careful"]:
        reasons.append(
            f"careful on the fast track ({reason(state['careful'][0])}): it took the fast track, with no interview, "
            "no personas' read of its criterion and no plan, so a person reads it",
        )
    # the personas' read of the criteria, started twice with no answer: the criteria went on unread
    read = criteria_read_of(task)
    if read is not None and unanswered(task) >= 2:
        quiet = "".join(f"; no answer from {source['name']} ({source['why']})" for source in read.get("silent", []))
        reasons.append(f"the criteria were not read: the personas' read was started twice and nobody answered{quiet}")
    commands, brought = task.gate()
    if brought:
        reasons.append(
            "the checks came with this change: the main checkout's settings name no command of the checks, and the branch's .lem/project.toml brings "
            + ", ".join(f"`{command}`" for command in commands) + ". Read the checks once: every later task is checked by them",
        )
    if state["due"] != "none":
        reasons.append(state["why"])
    # A lowered bar is never green, with a reason too: it is the one change that makes the other
    # green lines worth less, so the owner reads its line himself.
    kept = task.kept()
    said = {entry["name"]: entry["why"] for read in kept.get("reads", []) if read["answered"] for entry in read.get("bar", [])}
    for entry in (kept.get("checks") or {}).get("bar", {}).get("lowered", []):
        review = f"The review: {said[entry['file']]}" if entry["file"] in said else "No review said anything of it."
        reasons.append(f"the bar is lower in `{entry['file']}` ({entry['what']}). The builder: {entry['reason']} {review}")
    # a change that a later approval of his took over is his, and no cause of not green
    found = criteria_of(task)
    for change in (change for change in found["history"] if change["taken_over_by"] is None and not owners_change(task, change)):
        reasons.append(f"criterion {change['criterion']} {CHANGE_HOW[change['how']]} during the build: {change_why(task, change)}")
    # criteria approved without him, which no approval of his took over: the newest approval is the one that holds
    approval = found.get("approved") or {}
    if approval.get("by") == "alone":
        how = "while the task ran without the owner" if task.record.get("without_owner") or not someone_elses(task) else "without the owner, since someone else wrote the request"
        reasons.append(f"the owner did not approve the criteria: they were approved on {approval['at'][:10]} {how}")
    for decision in task.decisions():
        if without_him(decision):
            # past the personas: the dialectic, the experts, or the lead's pick that no level settled
            who = "the lead's pick, which no level of the ladder settled" if decision.get("unsettled") else f"by {taken_by(decision)}"
            reasons.append(f"decision {decision['id']} was taken without the owner ({decision['what']}): \"{decision['chose']}\", {who}")
    return reasons


def without_him(decision: dict) -> bool:
    """Whether a decision is the owner's and was taken without him, so that the request is not green
    for it: past the personas (the dialectic, the experts), or a pick that no level settled. The
    ladder decides each one at once, and he reads it here."""
    return decision.get("by") in PAST_PERSONAS or bool(decision.get("unsettled"))


def owners_change(task: Task, change: dict) -> bool:
    """Whether a criterion change came from the owner's own help on a breaker: his decision makes it
    his, as a later approval of his does."""
    led = next((decision for decision in task.decisions() if decision["id"] == change.get("decision")), None)
    return bool(led and led.get("by") == "owner" and "breaker" in led)


def without_owner(task: Task) -> str | None:
    """The line that says when the task ran without the owner, from the spans `lem project tasks`
    gives (the owner's away and back, a night's mark), with the words that
    started and ended each; none for a task that always ran with him."""
    def said(words: dict) -> str:
        return f"{'the owner' if words.get('by') == 'owner' else 'Lem'}: \"{words.get('words')}\""

    spans = [
        f"from {utc(span['from'])} ({said(span['started'])})" + (f" to {utc(span['to'])} ({said(span['ended'])})" if span["to"] else "")
        for span in task.record.get("without_owner") or []
    ]
    return f"It ran without the owner {', and '.join(spans)}." if spans else None


def utc(stamp: str) -> str:
    return f"{stamp[:10]} {stamp[11:16]} UTC"


def change_why(task: Task, change: dict) -> str:
    """Why a criterion changed: the reason the record gives, and the decision that led to it, when one did."""
    if "decision" not in change:
        return change["why"]
    led = next(decision for decision in task.decisions() if decision["id"] == change["decision"])
    how = f"the owner's help on breaker {led['breaker']}, which took" if owners_change(task, change) else f"where {taken_by(led)} took"
    return f"{reason(change['why'])}, after decision {led['id']} ({led['what']}), {how} \"{led['chose']}\""


def change_line(task: Task, change: dict) -> str:
    """One recorded change of a criterion as one line of the pull request: what it was, what it is, why, and who."""
    # a criterion with a case is its sentence and its steps, one to a line: here one line
    was, now = (" ".join(str(change.get(key)).split()) for key in ("was", "now"))
    said = {
        "changed": f"was \"{was}\", now \"{now}\"",
        "added": f"added, \"{now}\"",
        "removed": f"removed, was \"{was}\"",
    }[change["how"]]
    who = "" if "decision" in change else " By the lead." if change["by"] == "lead" else f" By the personas: {change['said']}"
    later = f" Approved by the owner afterwards (approval {change['taken_over_by']})." if change.get("taken_over_by") else ""
    return f"- criterion {change['criterion']}: {said}. {reason(change_why(task, change))}.{who}{later}"


def reason(text: str) -> str:
    """A reason as written, without its own full stop, for a sentence around it."""
    return text.rstrip(".")


def one_expert(decision: dict) -> bool:
    """Whether one expert answered alone: the machine had one of the agents (`advisers`)."""
    return len(decision.get("advisers") or "ab") == 1


def taken_by(decision: dict) -> str:
    """Who took a decision, for a line of the pull request: one expert is named as one."""
    return "one expert" if decision.get("by") == "experts" and one_expert(decision) else TAKEN_BY[decision["by"]]


def breaker_lines(task: Task) -> list[str]:
    """One line for each time the circuit breaker stopped the build: its cause and how it ended."""
    out = []
    for breaker in task.breakers():
        cause = BREAKER_SAYS[breaker["cause"]] + (f" ({breaker['irreversible']})" if breaker.get("irreversible") else "")
        ended = f"the owner helped, decision {breaker['help']}" if breaker["state"] == "helped" else "it waits for the owner"
        out.append(f"- the build stopped at breaker {breaker['id']}, {utc(breaker['at'])}: {breaker['what']}. Why it stopped: {cause}; {ended}.")
    return out


def decided(decision: dict) -> str:
    """One decision of the record as one line of the pull request: what, what was chosen, by whom, why."""
    return f"- {decision['what']}: \"{decision['chose']}\"" + after(decision)


def after(decision: dict) -> str:
    """What follows the option a decision took in its line: by whom, why, and what each level and the
    owner said. It opens with ", " or "."."""
    line = f", by {taken_by(decision)}"
    if decision.get("unsettled"):
        line = ", the lead's pick, which no level of the ladder settled"
    if decision["by"] == "owner" and "breaker" in decision:
        # his help on a breaker: the build stopped and he decided; nothing of it is a cause of not green
        line += f", his help on breaker {decision['breaker']}. {decision['why']}"
    elif decision["by"] == "personas":
        # the one stop of the ladder past the gate that is green: how many voted, in how many model families
        votes = decision["votes"]
        personas = {name.rpartition(", ")[0] or name for name, _ in votes}
        families = {name.rpartition(", ")[2] for name, _ in votes if ", " in name}
        named = f", {FAMILIES.get(len(families), f'{len(families)} model families')}" if families else ""
        line += f": {len(votes)} votes of {len(personas)} personas{named}, all for it. {decision['why']}"
    else:
        line += f". {decision['why']}"
    if decision.get("levels"):
        line += " Each level: " + "; ".join(f"{name}: {said}" for name, said in decision["levels"].items()) + "."
    if decision.get("words", decision["chose"]) != decision["chose"]:
        line += f" The owner's words: \"{decision['words']}\""
    return line


def checked_criteria(checks: dict) -> dict:
    """What the checks kept of the check of the criteria."""
    kept = checks.get("criteria") or {}
    return {**kept, "tests": kept.get("tests", [])}


def criteria_check_line(held: dict) -> str:
    """The check of the criteria as one line of the pull request's checks: how many tests pass on the
    branch and fail on the base commit, and, when the checks took the polish pass's result, that the
    tests were taken from the pass at its commit and not run again."""
    tests, without, taken = held["tests"], held.get("without_a_test", []), held.get("taken")
    line = f"- the tests of the criteria: {len(tests)} pass on the branch and fail on the base commit"
    if taken:
        line += f", taken from the polish pass at {str(taken['at'])[:9]}, and not run again"
    return line + (f"; {len(without)} {'criterion has' if len(without) == 1 else 'criteria have'} no test" if without else "")


def criterion_lines(criterion: dict, chart: bool = False) -> list[str]:
    """One criterion as a numbered item: its sentence, the steps of its case under it, and its chart
    when `chart` (the pull request leaves the chart to the owner's page)."""
    out = [f"{criterion['n']}. {criterion['text']}", *(f"   {step}" for step in criterion.get("case", []))]
    if chart and criterion.get("chart"):
        out += ["", "   ```mermaid", *(f"   {row}" if row else "" for row in criterion["chart"].splitlines()), "   ```", ""]
    return out


def criteria_lines(found: dict, held: dict, chart: bool = False) -> list[str]:
    """Each criterion of the text, with its case, each of its tests and what the check gave, or its line of no test."""
    out = []
    for criterion in found["criteria"]:
        out += criterion_lines(criterion, chart)
        for test in criterion["tests"]:
            proof = held.get((criterion["n"], test["command"]))
            out.append(f"   - `{test['command']}`: {'passes on the branch, fails on the base commit' if proof and not proof['problem'] else 'not checked'}")
        if criterion["no_test"]:
            out.append(f"   - no test: {criterion['no_test']}")
    return out


def builder_filed(task: Task) -> list[str]:
    """The items the fast track's builder filed: each file the branch adds to the backlog folder,
    other than those `file` wrote for a review, which the review's own line names."""
    return [item["item"] for item in branch_items(task)]


def synced(task: Task) -> str | None:
    """What bringing an open task onto a base that moved did, in one line for the pull request and
    for Lem's line to the owner: why, the rebase, a conflict and who resolved it. None for a landing
    that did not start from `open`, or before its `base`."""
    sync = task.kept().get("sync")
    if not sync or not sync.get("onto"):
        return None
    after = " after the forge called it conflicting" if sync.get("conflicting") else ""
    line = f"rebased on {task.base}{after}" if sync.get("moved") else f"checked again on {task.base}{after}, with no rebase needed"
    files = sync.get("conflict") or []
    if files and sync.get("resolved"):
        line += f"; one conflict in {files[0]}" if len(files) == 1 else f"; conflicts in {len(files)} files, {', '.join(files)}"
        line += ", resolved by a builder"
    return line + "; the checks passed again"


def edited_line(bar: dict) -> list[str]:
    """The existing tests, snapshots and test configurations the change edits, as one line under the
    bar's: no mark finds a changed expectation, so a reviewer knows where to look first."""
    edited = bar.get("edited") or []
    if not edited:
        return []
    kinds = [(kind, [entry["file"] for entry in edited if entry["kind"] == kind]) for kind in ("test", "snapshot", "test configuration")]
    said = [f"{len(files)} existing {kind if len(files) == 1 else kind + 's'} (" + ", ".join(f"`{file}`" for file in files) + ")" for kind, files in kinds if files]
    return ["- the change edits " + (", ".join(said[:-1]) + " and " + said[-1] if len(said) > 1 else said[0])]


def resolution_line(read: dict) -> str:
    """The read of a conflict's resolution as one line of the pull request's checks."""
    who = f"answered: {', '.join(read['answered'])}" if read["answered"] else "no source answered"
    said = f"{read['verdict']}, {read['must_fix']} must-fix, {read['should']} should, {read['nit']} nit" if read["answered"] else "not reviewed"
    return f"- the read of the conflict's resolution ({KIND_SAYS[read['kind']]}; {who}): {said}"


def head_lines(task: Task, state: dict) -> list[str]:
    """The head of a pull request's text on either track, in the order the owner reads it: green or
    not green with each reason, the time the task ran without him, why it is careful, and what
    bringing it onto a base that moved did."""
    reasons = not_green(task, state)
    out = ["**Not green.**", "", *(f"- {why}" for why in reasons), ""] if reasons else [GREEN, ""]
    alone = without_owner(task)
    if alone:
        # which part ran without him: a cause of not green only through what was decided then, which the lines above name
        out += [alone, ""]
    if state["careful"]:
        # a careful request is a person's to merge, green or not, and he reads why first
        out += [f"**Careful**, so the owner merges it: {'; '.join(reason(why) for why in state['careful'])}.", ""]
    moved = synced(task)
    if moved:
        # an open task brought onto a base that a merge moved: what happened to it since the owner last read it
        out += [moved[0].upper() + moved[1:] + ".", ""]
    return out


def issue_line(task: Task) -> list[str]:
    """The line `Issue: #42` under the request, for a task whose ticket is an issue of a project whose
    tracker is GitHub: GitHub links the issue and the pull request both ways from it. No word that
    closes the issue (`Closes`, `Fixes`): `lem issue land` comments and closes it itself."""
    ticket = task.record.get("ticket") or ""
    if (task.settings.get("tracker") or {}).get("kind") != "github" or not ticket.startswith("#"):
        return []
    return [f"Issue: {ticket}", ""]


def small_text(task: Task, notes: str, state: dict) -> str:
    """The text of a pull request on the fast track: green or not, the criterion, the checks, the read.
    What the fast track does not have (a plan, a personas' read, a polish pass, a talk) gets no line;
    what its builder filed in the backlog gets one."""
    kept = task.kept()
    checks = kept.get("checks") or {}
    found = criteria_of(task)
    ask = (task.directory / "ask.txt").read_text(encoding="utf-8").strip() if (task.directory / "ask.txt").is_file() else ""
    held = {(test["criterion"], test["command"]): test for test in checked_criteria(checks)["tests"]}
    out = head_lines(task, state)
    out += ["## The request", "", *(f"> {line}" for line in (ask or "(the owner's words were not kept for this task)").splitlines()), ""]
    out += issue_line(task)
    approval = found.get("approved") or {}
    by = {"lem": f" Lem approved it in the owner's name on {approval.get('at', '')[:10]}; the personas did not read it.",
          # a night's task, or a request someone else wrote: not the owner's own sentence, so not his approval either
          "alone": f" Lem approved it on {approval.get('at', '')[:10]} without the owner ({'the night opened the task' if task.record.get('night') else 'someone else wrote the request'}); the personas did not read it."}.get(approval.get("by"), "")
    out += ["## The acceptance criterion", "", f"The fast track, because {reason(found['why'])}.{by}", ""]
    out += criteria_lines(found, held)
    out += [change_line(task, change) for change in found["history"]]
    out += ["", "## Checks", ""]
    out += [f"- check, `{command['command']}`{' (serial, under the lock)' if command.get('serial') else ''}: {command['last'] or 'exit ' + str(command['exit'])}" for command in checks.get("commands", [])]
    own = builder_filed(task)
    if own:
        out.append("- filed in the backlog by the builder: " + ", ".join(f"`{path}`" for path in own))
    cause = task.record.get("investigation")
    if cause and cause.get("type") == "fix":
        where = f" ({cause['where']})" if cause.get("where") else ""
        out.append(f"- the cause, as the investigation found it: {cause['line']}{where}")
    lowered = (checks.get("bar") or {}).get("lowered", [])
    out.append("- the bar: no mark of a lowered bar found" if not lowered else "- the bar is lowered: " + "; ".join(f"`{entry['file']}` ({entry['what']})" for entry in lowered))
    out += edited_line(checks.get("bar") or {})
    for read in kept.get("reads", []):
        if read.get("of") == "resolution":
            out.append(resolution_line(read))
            continue
        who = f"answered: {', '.join(read['answered'])}" if read["answered"] else "no source answered"
        said = f"{read['verdict']}, {read['must_fix']} must-fix, {read['should']} should, {read['nit']} nit" if read["answered"] else "not reviewed"
        defects = outside_of(read)
        if defects:
            said += "; filed outside the change: " + ", ".join(f"`{defect['item']}`" for defect in defects)
        out.append(f"- the review, round {read['round']} ({KIND_SAYS[read['kind']]}; {who}): {said}")
    out.append(careful_line(task, state))
    decisions = [*breaker_lines(task), *(decided(decision) for decision in task.decisions())]
    if decisions:
        out += ["", "## Decisions", "", *decisions]
    rest = no_media(notes).strip()
    return "\n".join(out) + ("\n\n" + rest if rest and rest.lower() != "none" else "") + "\n"


def pr_text(task: Task, notes: str, state: dict) -> str:
    """The text of the pull request, in the order the owner reads it."""
    if criteria_of(task)["small"]:
        return small_text(task, notes, state)
    kept = task.kept()
    checks = kept.get("checks") or {}
    found = criteria_of(task)
    ask = (task.directory / "ask.txt").read_text(encoding="utf-8").strip() if (task.directory / "ask.txt").is_file() else ""
    held = {(test["criterion"], test["command"]): test for test in checked_criteria(checks)["tests"]}
    out = head_lines(task, state)
    out += ["## The request", "", *(f"> {line}" for line in (ask or "(the owner's words were not kept for this task)").splitlines()), ""]
    out += issue_line(task)
    out += ["## Acceptance criteria", "", f"The {TRACKS.get(found['size'], found['size'])} track, because {found['why']}", ""]
    out += criteria_lines(found, held)
    if found["history"]:
        out += ["", "Criteria that changed during the build, in the order of the record:", ""]
        out += [change_line(task, change) for change in found["history"]]
    out += ["", "## Checks", ""]
    for command in checks.get("commands", []):
        code = command["exit"]
        out.append(f"- check, `{command['command']}`{' (serial, under the lock)' if command.get('serial') else ''}: {command['last'] or f'exit {code}'}")
    out.append(criteria_check_line(checked_criteria(checks)))
    out.append(polished(kept.get("polish")))
    read = criteria_read_of(task)
    out.append(read_line(read, found, unanswered(task), read_skipped(task)[0] if read is None else None, criteria_waited(events_of(task))))
    if unread(read, found):
        out.append(unread(read, found))
    if (task.directory / "scout.md").is_file():
        # no path: the pull request is read on the forge, where a file of this machine leads nowhere
        out.append("- the criteria were written from the scout's facts of the code, read during the interview")
    cause = task.record.get("investigation")
    if cause and cause.get("type") == "fix":
        # a task on the standard track that came from a bug names the cause its investigation found
        where = f" ({cause['where']})" if cause.get("where") else ""
        out.append(f"- the cause, as the investigation before the build found it: {cause['line']}{where}")
    lowered = (checks.get("bar") or {}).get("lowered", [])
    out.append("- the bar: no mark of a lowered bar found" if not lowered else "- the bar is lowered, with these reasons:")
    out += [f"  - `{entry['file']}` ({entry['what']}): {entry['reason']}" for entry in lowered]
    out += edited_line(checks.get("bar") or {})
    if (checks.get("bar") or {}).get("not_covered"):
        out.append(f"- the bar has no marks of its own for files of these kinds: {', '.join(checks['bar']['not_covered'])}")
    size = checks.get("size") or {}
    out.append(f"- size: {size.get('files', '?')} files, {size.get('lines', '?')} changed lines")
    for read in kept.get("reads", []):
        if read.get("of") == "resolution":
            out.append(resolution_line(read))
            continue
        who = f"answered: {', '.join(read['answered'])}" if read["answered"] else "no source answered"
        quiet = "".join(f"; no answer from {source['name']} ({source['why']})" for source in read["silent"])
        found = f"{read['verdict']}, {read['must_fix']} must-fix, {read['should']} should, {read['nit']} nit" if read["answered"] else "not reviewed"
        defects = outside_of(read)
        if defects:
            # propose refuses while one has no item in the tip, so each one here is filed
            found += f"; it saw {len(defects)} defect{'' if len(defects) == 1 else 's'} outside the change, filed as " + ", ".join(f"`{defect['item']}`" for defect in defects)
        out.append(f"- the review, round {read['round']} ({KIND_SAYS[read['kind']]}; {who}{quiet}): {found}")
        out += [f"  - ran {profile['name']}: {profile['why']}" for profile in read["ran"]]
        out += [f"  - left out {profile['name']}: {profile['why']}" for profile in read["left_out"]]
    if talk_due(task, state):
        # propose refuses a request whose plan called for a talk with none on record, so there is one here
        out.append(talked(talk_of(task)))
    elif untalked(task, state):
        # careful after its plan: the full set ran and a person merges, so this is no cause of not green
        out.append(untalked(task, state))
    out.append(careful_line(task, state))
    out += ["", "## Decisions of the build", "", *([*breaker_lines(task), *(decided(decision) for decision in task.decisions())] or ["none"])]
    out += folded_stories(task)
    return "\n".join(out) + "\n\n" + no_media(notes).strip() + "\n"


# A picture of a task's `media/` folder, linked from a document: the task directory is in no
# commit, so the pull request names the picture and links nothing.
MEDIA = re.compile(r"(!?)\[([^\]]*)\]\(\s*(?:[^)\s]*/)?media/([^)\s]+)(?:\s+\"[^\"]*\")?\s*\)")


def no_media(text: str) -> str:
    """The text with each link to a file of `media/` replaced by its caption: the forge has no such file."""
    return MEDIA.sub(lambda found: f"{found.group(2) or found.group(3)} (a picture on the task's board)", text)


def folded_stories(task: Task) -> list[str]:
    """The story and the chart of each important decision that has one, folded under the list of the
    pull request, which the forge draws; nothing for a task with none, so its text stays as short."""
    out = []
    for decision in task.decisions():
        if not important(decision) or not (decision.get("case") or decision.get("chart")):
            continue
        out += ["", f"<details><summary>Decision {decision['id']}, its story: {one_line(decision['what'])}</summary>", ""]
        out += story_lines(decision)
        out += chart_lines(decision)
        out += ["</details>"]
    return out


# The longest text of a decision's summary in the pull request, in characters: one line at the width
# of a laptop's window. A guess, not a measurement.
CELL = 80


def one_line(text: str, most: int = CELL) -> str:
    """A text in one line of at most MOST characters, cut at a word, with an ellipsis when cut."""
    flat = " ".join(text.split())
    if len(flat) <= most:
        return flat
    return flat[:most].rsplit(" ", 1)[0].rstrip(",;:.") + "…"


def label(option: str) -> str:
    """An option's label: its text before the first colon, as `lem decisions log --option` asks an option to
    be written ("LABEL: what the person sees after it"), or the whole option in one line."""
    head, colon, _ = option.partition(":")
    # a colon inside a quote is no end of a label: "the say 'the checks refused: ...'"
    opened = len(re.findall(r"(?:^|\s)['\"]", head)) > len(re.findall(r"\w['\"](?:\s|$|[.,;])", head))
    labelled = colon and head.strip() and len(head) <= CELL and not opened
    return one_line(head if labelled else option)


def important(decision: dict) -> bool:
    """Whether a decision is important, the ones whose story `stages/ladder.md` asks for: one the
    request is not green for (past the personas, or unsettled), or the owner's help on a breaker."""
    return without_him(decision) or (decision["by"] == "owner" and "breaker" in decision)


def story_lines(decision: dict) -> list[str]:
    """The story of a decision as its record keeps it: the case in its numbered steps, how it is known,
    and the cause. Nothing when the record has no case."""
    if not decision.get("case"):
        return []
    known = {"reproduced": "reproduced", "derived": "derived from the code, not run"}.get(decision.get("case_was"), decision.get("case_was"))
    out = [f"**The case**{f' ({known})' if known else ''}:", "", *decision["case"].splitlines(), ""]
    if decision.get("cause"):
        out += [f"**Why it could happen:** {decision['cause']}", ""]
    return out


def chart_lines(decision: dict) -> list[str]:
    """A decision's chart as a fenced mermaid block, which the board and the forge draw."""
    return ["```mermaid", *decision["chart"].splitlines(), "```", ""] if decision.get("chart") else []


def gh(task: Task, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return gh_in(task.worktree if task.worktree.exists() else task.main, *args, check=check)


def gh_in(where: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    """One command of the forge's `gh`, run in a checkout of the repository, which tells it the repository."""
    if not shutil.which("gh"):
        raise LandError("the remote is GitHub and the `gh` command is not on PATH: install it and sign in, then run this again")
    ran = subprocess.run(["gh", *args], cwd=where, capture_output=True, text=True, check=False, stdin=subprocess.DEVNULL)
    if check and ran.returncode != 0:
        raise LandError(f"gh {' '.join(args[:2])} failed: {(ran.stderr or ran.stdout).strip()}")
    return ran


def not_github(task: Task) -> str:
    """The refusal of a step that needs the pull request, where origin is not on GitHub."""
    return (
        f"origin of {task.main} is not a repository on GitHub, or there is none: a task ends as a GitHub pull request, the one way Lem lands. "
        f"Point origin at the repository on GitHub (`git -C {task.main} remote add origin git@github.com:OWNER/REPO.git`, "
        f"or `remote set-url` for one that is there), push {task.base} there, then run this step again"
    )


def protected_refusal(branch: str, settings: dict, does: str) -> str | None:
    """Why Lem may not push to the branch named BRANCH (DOES `pushes`) or delete it (`deletes`), by the
    settings' `[branch]` as they are now: the base branch, or a name in `branch.protected`, which the
    owner may add after the task's worktree was made. None for a branch of the task's own."""
    what = "to" if does == "pushes" else "of"
    if branch == settings["base"]:
        return f"{branch} is the base branch of .lem/project.toml: Lem {does} nothing {what} it outside a merge through its pull request"
    if branch in settings["protected"]:
        return f"{branch} is in branch.protected of .lem/project.toml: Lem {does} nothing {what} it"
    return None


def cmd_propose(task: Task, title: str, notes_file: str) -> dict:
    task.need_landing()
    task.need_worktree()
    if task.forge != "github":
        raise LandError(not_github(task))
    tip = git(task.worktree, "rev-parse", "HEAD")
    missing = gate_missing(task, tip)
    if missing:
        raise LandError(f"{missing}; `lem land checks {task.slug}` comes first")
    kept = task.kept()
    reads = kept.get("reads", [])
    unfiled = to_file(reads)
    state = due(task)
    if state["due"] == "review":
        raise LandError(f"a review is due before anything is proposed, {KIND_SAYS[state['floor']]} at the least ({state['why']}); `lem land read {task.slug}` says what a reviewer gets")
    # A careful or large plan is talked through by its defender and the reviewer, in the plan
    # talk's companion, before any code. The talk leaves one event, and a request without it
    # skipped that step.
    needs_talk = talk_due(task, state)
    talk = talk_of(task) if needs_talk else None
    if needs_talk and talk is None:
        raise LandError(
            f"{needs_talk}, so its defender and the reviewer talk its plan through in the plan talk's companion before any code (`stages/talk.md`), "
            f"and the event log has no `plan.talk` of {task.slug}. The defender writes it after the talk: "
            f"`lem project log {task.slug} plan.talk {TALK_FORM}`; for a plan that had no talk, the task's lead opens the talk first, as `stages/talk.md` says",
        )
    if talk is not None and not (
        isinstance(talk.get("reviewer"), str) and talk["reviewer"].strip()
        and all(isinstance(talk.get(key), int) and not isinstance(talk.get(key), bool) for key in ("turns", "settled", "open"))
    ):
        raise LandError(f"the newest `plan.talk` of {task.slug} does not have the form `{TALK_FORM}`; its defender writes it again with `lem project log`")
    read = criteria_read_of(task)
    if read is not None and not read_form(read):
        raise LandError(f"the newest `criteria.read` of {task.slug} does not have the form {READ_FORM}; whoever ran the read writes it again with `lem project log`")
    # The personas read the criteria of a task on the standard track before the build, and a doubt of theirs reaches him:
    # a request is not proposed over criteria nobody read, or over a doubt he never saw.
    found = criteria_of(task)
    if read is None and not found["small"]:
        # his word to skip the read, with his approval after it and both before any lead started, is the one way past it
        skipped, why_not = read_skipped(task)
        if why_not:
            raise LandError(why_not)
        if skipped is None:
            raise LandError(
                f"{task.slug} takes the standard track, and the event log has no `criteria.read`: the personas read its criteria before the build "
                "(`stages/interview.md`, step 5; for the standard track from a complete request `stages/plan.md`, step 1), "
                f"and whoever ran the read writes `lem project log {task.slug} criteria.read` with the form {READ_FORM}. "
                f"Only the owner skips a read, at the interview and when every criterion names only the developer: Lem writes the owner's word with {read_skip_form(task.slug)}, "
                "and the owner approves the criteria after it, both before a lead starts",
            )
    if read is not None and not read["answered"] and unanswered(task) < 2:
        raise LandError(
            f"nobody answered the newest read of {task.slug}'s criteria: it is started once more, and its record written again with `lem project log {task.slug} criteria.read` "
            "(`stages/interview.md`, step 5; for the standard track from a complete request `stages/plan.md`, step 1). "
            "After a second read in a row that nobody answered, the request is proposed as not green",
        )
    # Without the owner, an approval made then lets the request go on, and it is not green for it.
    if read is not None and (read["flagged"] or read["split"]) and not approved_after(found, read) and not approved_alone(found, read):
        doubt = f"{read['flagged']} flagged {'criterion' if read['flagged'] == 1 else 'criteria'}" if read["flagged"] else "a split between the two families"
        raise LandError(
            f"the newest read of {task.slug}'s criteria found {doubt}, and no approval of the owner's came after it: the criteria with the personas' answers "
            "on top go to the owner (`stages/interview.md`, step 6), and the owner's yes is kept with "
            f"`lem criteria approve {task.slug} --file FILE`",
        )
    # A request that had an interview ends it with his yes, whatever the read found: a step that skipped
    # it, and a lead that then froze the criteria as a complete request's, do not make it his.
    if interview_unapproved(events_of(task), found.get("approvals", []), found["small"]):
        raise LandError(
            f"{task.slug} had an interview (`interview.start` in the event log), and its criteria carry no approval of the owner's: the interview ends with "
            f"his yes, kept with `lem criteria approve {task.slug} --file FILE` (`stages/interview.md`, steps 6 and 7), or, while the task runs without him, "
            "with `--alone` (`stages/away.md`). The criteria with the personas' answers go to the owner",
        )
    # A complete request that someone else wrote: nobody at the terminal read it, so its criteria wait
    # for his yes even when nobody was confused, and the lead's freeze of the read is not that yes.
    if read is not None and not approved_after(found, read) and not approved_alone(found, read) and someone_elses(task):
        raise LandError(
            f"{task.slug} is a complete request that someone else wrote, and no approval of the owner's came after the newest read of its criteria: "
            f"nobody at the terminal read that request, so its criteria wait for his yes even when nobody was confused, and a freeze by the read is not his yes "
            f"(`stages/plan.md`, step 1). The criteria with the personas' answers go to the owner, and his yes is kept with `lem criteria approve {task.slug} --file FILE`",
        )
    # Each defect a review saw outside the change has its item in the tip, so that none is lost: one
    # that a session never filed, and one whose item a later commit took out.
    if unfiled:
        raise LandError(
            f"{len(unfiled)} defect(s) a review saw outside the change have no item in the backlog: "
            + "; ".join(f"\"{defect['title']}\" (round {defect['round']})" for defect in unfiled)
            + f". `lem land file {task.slug}` files them, then this step runs again",
        )
    gone = [(read, defect) for read in reads if read["answered"] for defect in outside_of(read) if not in_tree(task, tip, defect["item"])]
    if gone:
        read, defect = gone[0]
        raise LandError(
            f"the item {defect['item']} of the defect \"{defect['title']}\" (review round {read['round']}) was removed after it was filed"
            + (f", and {len(gone) - 1} more" if len(gone) > 1 else "")
            + f": a builder puts it back with `lem land file {task.slug} --again`, then this step runs again; when the owner does not want it, "
            "the item stays with `worth: no` and the owner's reason in it, never deleted",
        )
    # A request is never proposed over a breaker that stopped its build and that the owner did not help on.
    waiting = next((breaker for breaker in task.breakers() if breaker["state"] == "waits"), None)
    if waiting:
        raise LandError(
            f"breaker {waiting['id']} of {task.slug} waits for the owner ({waiting['what']}): its build stopped there, and a request is never proposed over it. "
            f"The owner reads its document and helps (`lem decisions log {task.slug} --by owner --breaker {waiting['id']} ...`), parks the task or drops it",
        )
    notes = Path(notes_file).read_text(encoding="utf-8") if Path(notes_file).is_file() else None
    if notes is None:
        raise LandError(f"{notes_file} is not a file; --notes names the notes of the pull request")
    # The fast track's notes are what the review left open, in a few lines, or `none`: it has no
    # plan to decide from, no polish pass to file from, and nothing it set out of scope.
    wanted = [*([] if criteria_of(task)["small"] else NOTES), *(["## Migration"] if state["careful"] else [])]
    missing = [heading for heading in wanted if not re.search(rf"(?m)^{re.escape(heading)}\s*$", notes)]
    if missing:
        raise LandError(f"the notes lack {', '.join(missing)}: they hold {', '.join(wanted)}, each with what is true of this task or the one word `none`")
    if not title.strip() or "\n" in title:
        raise LandError("--title is one line: the subject of the change")
    body = task.directory / "pr.md"
    write_whole(body, pr_text(task, notes, state))
    reasons = not_green(task, state)
    says = "green" if not reasons else f"not green: {'; '.join(reasons)}"
    branch = git(task.worktree, "branch", "--show-current")
    # the name the push goes to, by the settings as they are now: the owner may protect it after the worktree was made
    protected = protected_refusal(branch, task.settings["branch"], "pushes")
    if protected:
        raise LandError(
            f"{protected}, and the task's branch has that name; nothing was pushed. The owner takes the name out of branch.protected, "
            f"or, while the task has no pull request, a builder gives the task a branch of its own (`git -C {task.worktree} branch -m NEW-NAME`); then this step runs again",
        )
    pr = kept.get("pr")
    # What origin's copy of the branch holds may be replaced only when it is Lem's push or the
    # branch holds it: the lease names that commit, or no branch at all for a first push.
    lease = task.own_remote(branch)
    if not pr:
        # A run that was cut off after the forge made the pull request wrote none down: the
        # forge knows it. Only a pull request whose head is the commit Lem pushed for this task
        # is its own; any other on the same branch name is somebody's, and is not taken.
        there = json.loads(gh(task, "pr", "list", "--head", branch, "--base", str(task.base), "--state", "open", "--json", "number,url,headRefOid,author").stdout)
        pushed = task.kept().get("pushed")
        mine = [found for found in there if pushed and found.get("headRefOid") == pushed]
        others = [found for found in there if found not in mine]
        if others:
            other = others[0]
            raise LandError(
                f"pull request #{other['number']} by {(other.get('author') or {}).get('login') or 'someone'} is open on {branch}, and its head is no commit Lem pushed for this task: "
                f"it is somebody else's, and Lem does not push over it or rewrite its text. Give the task a branch of its own "
                f"(`git -C {task.worktree} branch -m NEW-NAME`), then run this step again",
            )
        pr = {"number": mine[0]["number"], "url": mine[0]["url"]} if mine else None
    elif (state_now := viewed(task, pr)["state"]) != "OPEN":
        raise LandError(
            f"the pull request {pr['url']} is {state_now.lower()}: `lem land merged {task.slug}` "
            + ("finishes the task" if state_now == "MERGED" else "writes the task dropped, and its branch keeps its commits"),
        )
    # With the lease of the one commit the push may replace: a commit that came in between stops it.
    git(task.worktree, "push", f"--force-with-lease=refs/heads/{branch}:{lease}", "origin", f"HEAD:refs/heads/{branch}")
    # kept before the forge's step, so that a run cut off after it knows the push as its own
    task.keep(pushed=tip)
    if pr:
        gh(task, "pr", "edit", str(pr["number"]), "--title", title, "--body-file", str(body))
    else:
        url = gh(task, "pr", "create", "--base", str(task.base), "--head", branch, "--title", title, "--body-file", str(body)).stdout.strip().splitlines()[-1]
        number = url.rstrip("/").rsplit("/", 1)[-1]
        if not number.isdigit():
            raise LandError(f"gh pr create printed no pull request address: {url!r}")
        pr = {"number": int(number), "url": url}
    # The events come after the forge's step: a proposal that the forge or the push refused is none.
    # for the retro: how often a request is not green, and for which reason
    script("project.py", task.worktree, "log", task.slug, "proposed", f"green:={json.dumps(not reasons)}", f"not_green:={json.dumps(reasons)}", f"tip={tip[:9]}")
    moved = synced(task)
    task.keep(pr=pr, proposed=tip, title=title, not_green=reasons)
    carried = carry_merge(task, kept, tip, state, reasons)
    task.state("open", f"pull request {pr['url']}", says, *([moved] if moved else []))
    return {
        "task": task.slug, "text": str(body), "pull_request": pr, "green": not reasons, "not_green": reasons, "branch": branch, "tip": tip,
        "synced": moved, **carried,
    }


def carry_merge(task: Task, kept: dict, tip: str, state: dict, reasons: list[str]) -> dict:
    """After a proposal, what was said of the tip proposed before (KEPT, the record before this
    proposal) at its merge, carried onto TIP where the change is the same (`carried_over`): the merge
    agent's review, with whether it calls the owner as the rules say now, logged again as a
    `merge.review` of TIP with `carried`; and the owner's merge that a moved base refused, which stands
    (`merge.stands`) or ends (`tap_after`). What it gives the output: `merge_review` (carried or
    null) and `owner_merge` (`stands`, the reason it ended, or null)."""
    old, rebased = kept.get("proposed"), kept.get("rebase_carried")
    out: dict = {"merge_review": None, "owner_merge": None}
    review = kept.get("merge_review")
    if isinstance(review, dict) and review.get("tip") == old and carried_over(old, tip, rebased):
        refusal = merger_refusal(task.slug, task.settings["branch"]["land"], state["careful"], reasons, review_call(task) is not None, {"verdict": "merge"})
        calls = review.get("verdict") == "call" or refusal is not None
        why = refusal if refusal else (review.get("why") if review.get("verdict") == "call" else None)
        review = {**review, "tip": tip, "calls": calls, "why": why, "carried_from": old}
        task.keep(merge_review=review)
        script("project.py", task.main, "log", task.slug, "merge.review", f"verdict={review['verdict']}", f"calls:={json.dumps(calls)}", f"by={review.get('by')}",
               f"tip={tip[:9]}", f"carried={str(old)[:9]}", *([f"why={why}"] if why else []))
        out["merge_review"] = "carried"
    tap, ended = tap_after(kept.get("owner_tap"), old, tip, rebased, reasons)
    if tap:
        task.keep(owner_tap=tap)
        script("project.py", task.main, "log", task.slug, "merge.stands", "by=owner", f"tip={tip[:9]}", f"from={str(old)[:9]}")
        out["owner_merge"] = "stands: the board's server merges it after the checks and the reviews were checked again"
    elif ended:
        task.keep(owner_tap=None)
        out["owner_merge"] = f"ended: {ended}; the owner merges it again"
    return out


def follow(task: Task) -> str | None:
    """After the remote's base moved: the checkout that holds the base follows, or the reason it did not."""
    if not (task.remote and task.base_checkout is not None):
        return None
    # The checkout that holds the base follows, so the next task's worktree starts from what just
    # landed. git refuses the fast-forward, and changes nothing, when a file with changes of its
    # own is in the way or the checkout has commits the remote lacks; then it stays as it is.
    followed = run(["git", "-C", str(task.base_checkout), "merge", "--ff-only", f"origin/{task.base}"], check=False)
    if followed.returncode == 0:
        return None
    why = [line for line in (followed.stderr or followed.stdout).strip().splitlines() if line.strip()]
    return f"{task.base_checkout} did not follow origin/{task.base}, and nothing in it was changed. git said: {why[-1] if why else 'nothing'}"


def merger_refusal(slug: str, land: str, careful: list[str], reasons: list[str], called: bool, review: dict | None) -> str | None:
    """Why the merge agent may not merge a request, or None when it may. The facts: the settings'
    `branch.land`, why the request is careful (none when it is not), why it is not green (none when it
    is), whether the newest review that answered made the careful call, and the merge agent's review
    of the proposed tip (its `verdict`), or None. The owner's merge asks none of this; a task that ran
    without him is merged as any other."""
    if land != "agent":
        return 'branch.land is "owner" in .lem/project.toml: the owner merges every task, after the merge review; it waits as `open` for his word'
    if careful:
        return f"a careful request is merged by the owner, whatever the settings say ({careful[0]}); it waits as `open` for his word"
    if reasons:
        return f"the request is not green ({'; '.join(reasons)}), so the owner merges it; it waits as `open` for his word"
    # The merge agent merges only on the newest review's "not careful": a record with no call is no such word.
    if not called:
        return "no review that answered made the careful call for this change, so the owner merges it; it waits as `open` for his word"
    if review is None:
        return f"no merge review of the proposed tip is on record: the merge agent reads the task first, and `lem land merge-review {slug} --file FILE --tip TIP` writes its review down"
    if review.get("verdict") != "merge":
        return "the merge review calls the owner: he reads it, and it waits as `open` for his word"
    return None


def kept_refusal(by: str, kind: str | None) -> bool:
    """Whether a refused merge is kept for its tip, so that the server tries that tip no more and wakes
    the task's session: every refusal of the merge agent's merge by Lem's rules, and the owner's when
    the base moved, which the session repairs by landing the task again. A git or `gh` call that failed
    (no kind) is never kept: the next try runs it again."""
    return kind in REFUSALS and (by == "merger" or kind == "base")


def carried_over(old: str | None, new: str, rebased: dict | None) -> bool:
    """Whether what was said of the proposed tip OLD holds for the tip NEW proposed now: the same tip,
    or the tip that `base` made of it by a rebase with no conflict that kept the code review
    (`rebase_carried`), with no commit after it."""
    return bool(old) and (old == new or rebased == {"from": old, "to": new})


def tap_after(tap: dict | None, old: str | None, new: str, rebased: dict | None, reasons: list[str]) -> tuple[dict | None, str | None]:
    """The owner's merge that a moved base refused, after a new proposal: it stands, with the new tip,
    while the change is the one he merged (`carried_over`) and the reasons it is not green are the same;
    else it ends, with why. (None, None) when no merge of his waits."""
    if not tap:
        return None, None
    if tap.get("tip") != old or not carried_over(old, new, rebased):
        return None, "the change is not the one the owner merged: a commit came after the rebase, or the rebase met a conflict"
    if list(tap.get("not_green") or []) != list(reasons):
        return None, "the reasons the request is not green are not the ones the owner saw when he merged it"
    return {**tap, "tip": new}, None


def merge_review_of(task: Task) -> dict | None:
    """The merge agent's review of the tip that was proposed, as `merge-review` kept it; None for none,
    or for a review of an earlier tip."""
    kept = task.kept()
    review = kept.get("merge_review")
    return review if isinstance(review, dict) and kept.get("proposed") and review.get("tip") == kept["proposed"] else None


def may_merge(task: Task, by: str) -> None:
    """Who may merge. The owner's word is enough; the merge agent merges only what nobody has a reason to look at first."""
    if by == "owner":
        return
    state = due(task)
    refusal = merger_refusal(task.slug, task.settings["branch"]["land"], state["careful"], not_green(task, state), review_call(task) is not None, merge_review_of(task))
    if refusal:
        raise Refusal("rule", refusal)


def base_refusal(view: dict, base: str, url: str, slug: str) -> str | None:
    """Why a pull request as GitHub shows it (VIEW, with `baseRefName`) is not the task's: its base on
    GitHub is not BASE, the settings' base branch, as after a change of its base there. None when it is."""
    there = view.get("baseRefName")
    if not there:
        return f"GitHub's answer for the pull request {url} names no base branch, so Lem cannot tell that it goes into {base}; nothing was merged or recorded. Run this step again"
    if there == base:
        return None
    number = url.rstrip("/").rsplit("/", 1)[-1]
    if view.get("state") == "MERGED":
        return (f"the pull request {url} was merged into {there} on GitHub, not into {base}, the base of the task's settings, so the task did not land, "
                f"and nothing was recorded: the owner ends it with `lem project state {slug} dropped \"WHY\"`, or a new task brings the change onto {base}")
    return (f"the pull request {url} is on {there} on GitHub, not on {base}, the base of the task's settings: its base was changed there. "
            f"Nothing was merged or recorded. Its base goes back to {base} on GitHub (`gh pr edit {number} --base {base}`), then this step runs again")


def forge_done(task: Task, view: dict) -> dict:
    pr = task.kept()["pr"]
    # a merge into another branch than the base is no landing: the task stays as it is, and the owner reads why
    wrong = base_refusal(view, task.base, pr["url"], task.slug)
    if wrong:
        raise LandError(wrong)
    task.fetch()
    merged = (view.get("mergeCommit") or {}).get("oid")
    # the commit of the branch that the forge merged: `clean` removes the branch only when it holds nothing after it
    task.keep(merged=merged or True, merged_head=view["headRefOid"])
    left_behind = follow(task)
    task.state("landed", f"{task.base}: pull request {pr['url']} is merged")
    return {"task": task.slug, "base": task.base, "pull_request": pr, "merged": merged, "left_behind": left_behind}


def viewed(task: Task, pr: dict | None = None) -> dict:
    pr = pr or task.kept()["pr"]
    # the base too, which anyone may change on GitHub: a merge there goes into whatever base the pull request has then
    return json.loads(gh(task, "pr", "view", str(pr["number"]), "--json", "state,headRefOid,mergeCommit,mergeable,baseRefName").stdout)


def cmd_merged(task: Task) -> dict:
    # `landing` too: the owner may merge on the forge while an open task runs its checks again
    if task.record["status"] not in ("open", "landing") or not task.kept().get("pr"):
        raise LandError(f"the task is {task.record['status']!r} and has {'a' if task.kept().get('pr') else 'no'} pull request; this step is for a task whose pull request the owner merged")
    view = viewed(task)
    if view["state"] == "MERGED":
        return forge_done(task, view)
    if view["state"] == "CLOSED":
        # The owner closed it on the forge: the task ends, and nothing of it waits. Its branch keeps
        # its commits (`clean` removes the worktree and names how to delete the branch), and a task
        # that goes on after all is a new request.
        pr = task.kept()["pr"]
        task.keep(closed=True)
        task.state("dropped", "the pull request was closed on the forge", f"pull request {pr['url']} is closed with no merge; the branch keeps its commits")
        return {"task": task.slug, "pull_request": pr, "closed": True, "state": "dropped"}
    # Still open: what the forge says of a conflict with the base, on the head it says it of, for the list of what waits
    task.keep(forge={"mergeable": view.get("mergeable"), "head": view.get("headRefOid")})
    raise LandError("the pull request is not merged yet" + (f", and the forge calls it conflicting with {task.base}" if view.get("mergeable") == "CONFLICTING" else ""))


# The fields of a pull request one look at the forge reads (the board's server, `forge_look`), for all the open tasks at once.
WATCHED = "number,state,mergeable,headRefOid,mergeCommit"
# How many pull requests of the base branch one look lists, the newest first. A task's pull request
# that is not among them (more than this many were opened after it) is asked for by its number.
WATCH_LIST = 100
def forge_look(main: Path, base: str, numbers: list[int]) -> dict[int, dict]:
    """What the forge says of each pull request: one call that lists the base branch's newest ones,
    and one more for each number that list does not hold."""
    listed = json.loads(gh_in(main, "pr", "list", "--state", "all", "--base", base, "--limit", str(WATCH_LIST), "--json", WATCHED).stdout or "[]")
    seen = {pr["number"]: pr for pr in listed if pr.get("number") in numbers}
    for number in numbers:
        if number not in seen:
            seen[number] = json.loads(gh_in(main, "pr", "view", str(number), "--json", WATCHED).stdout)
    return seen


@contextlib.contextmanager
def merge_lock(task: Task, by: str, via: str, standing: bool = False):
    """Hold the repository's one lock of Lem's merge calls while this one runs. A call that finds it
    held logs `merge.wait` with the task that holds it and waits; whoever holds it is done in seconds
    (a fetch, a merge on the forge or a push). The call reads the base branch after it takes it."""
    path = task.directory.parent.parent / MERGE_LOCK
    try:
        handle = path.open("a+", encoding="utf-8")
    except OSError as error:
        raise LandError(f"the merge lock {path} cannot be opened ({error.strerror}); it holds no state, so remove it (`rm -r {path}`) and run `lem land merge {task.slug}` again") from error
    with handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            holder = holder_of(path)
            other = holder.get("task") if holder else None
            script("project.py", task.main, "log", task.slug, "merge.wait", f"after={other or 'another task'}",
                   f"say={task.slug}: waits for the merge of {other or 'another task'}")
            fcntl.flock(handle, fcntl.LOCK_EX)
        handle.seek(0)
        handle.truncate()
        handle.write(json.dumps({"step": "merge", "task": task.slug, "pid": os.getpid(), "since": now_utc()}) + "\n")
        handle.flush()
        script("project.py", task.main, "log", task.slug, "merge.start", f"by={by}", f"via={via}", *(["after=a re-check"] if standing else []))
        try:
            yield
        finally:
            handle.seek(0)
            handle.truncate()
            handle.flush()


def stamp_seconds(stamp: str) -> float:
    """A time of the event log, `YYYY-MM-DDTHH:MM:SSZ`, as seconds since the epoch."""
    return datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()


def task_time(events: list[dict], slug: str) -> dict:
    """How long the task took from its first event to its first proposal, against what was expected:
    the median of the same span of every task of the same track proposed before it, from the event
    log (`EVENTS` of every task, oldest first). The track is the size of a task's criteria (`small`
    or `full`); a task whose track the log does not say is compared with every earlier task. None
    where the log cannot tell."""
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
        if event.get("event") in ("task.criteria", "criteria.approved") and event.get("size") in TRACKS:
            track[name] = event["size"]

    def span(name: str) -> int:
        return round(stamp_seconds(proposed[name]) - stamp_seconds(first[name]))

    if slug not in proposed:
        return {"seconds": None, "expected": None, "from": "the task was not proposed"}
    mine = track.get(slug)
    earlier = [name for name in proposed if name != slug and proposed[name] < proposed[slug] and (mine is None or track.get(name) == mine)]
    which = f"the {TRACKS[mine]} track" if mine else "both tracks"
    if not earlier:
        return {"seconds": span(slug), "expected": None, "from": f"no task of {which} was proposed before it, so nothing says what to expect"}
    return {"seconds": span(slug), "expected": round(statistics.median(span(name) for name in earlier)),
            "from": f"the median of {len(earlier)} earlier task{'' if len(earlier) == 1 else 's'} of {which}, from the first event to the proposal, in the event log"}


def verdict_of(text: str) -> str | None:
    """The merge agent's verdict, from the first line of its review: `merge` or `call`, or None."""
    first = next((line for line in text.splitlines() if line.strip()), "")
    found = VERDICT.match(first.strip().lstrip("#*> ").strip())
    return found.group(1).lower() if found else None


def answer_file(task: Task, tip: str) -> Path:
    """The file the merge agent's answer goes to, one for each proposed tip, so that the answer of a
    read of an earlier proposal never takes the place of the newest one's."""
    return task.directory / f"merge-answer-{tip[:12]}.md"


def cmd_merge_review(task: Task, record: str | None, read_tip: str | None = None) -> dict:
    """The merge agent's read of a proposed task. With no record: its brief, `merge-brief.md` in the
    task directory, and the facts in it, the proposed `tip` among them. With the agent's reply and
    READ_TIP, the tip its brief named: the review written down as `merge-review.md`, and whether it
    merges or calls the owner; the reply of a brief of another tip than the one proposed now is refused."""
    if task.record["status"] != "open":
        raise LandError(f"the task is {task.record['status']!r}, not `open`: the merge agent reads a proposed task; `lem land propose {task.slug}` comes first")
    task.need_worktree()
    kept = task.kept()
    tip = kept.get("proposed")
    if not tip or not kept.get("pr"):
        raise LandError(f"{task.slug} has no pull request on record; `lem land propose {task.slug}` comes first")
    if git(task.worktree, "rev-parse", "HEAD") != tip:
        raise LandError(f"the branch's tip is not the tip that was proposed; {AGAIN}")
    state = due(task)
    reasons = not_green(task, state)
    land = task.settings["branch"]["land"]
    seat = task.settings["seats"]["merger"]
    # whether the merge agent may merge when it finds nothing: every rule but its own verdict
    refusal = merger_refusal(task.slug, land, state["careful"], reasons, review_call(task) is not None, {"verdict": "merge"})
    if record is None:
        found = criteria_of(task)
        files = {name: str(task.directory / file) for name, file in (
            ("pull_request_text", "pr.md"), ("words", "ask.txt"), ("request", "task.md"), ("report", "report.md"), ("notes", "notes.md"),
            ("investigation", "investigation.md"),
        ) if (task.directory / file).is_file()}
        # each breaker's document, the newest last (decisions.py keeps them as breaker-N.md)
        breakers = sorted(task.directory.glob("breaker-*.md"), key=lambda path: int(re.sub(r"\D", "", path.stem) or 0))
        if breakers:
            files["breakers"] = [str(path) for path in breakers]
        facts = {
            "task": task.slug, "worktree": str(task.worktree), "task_directory": str(task.directory),
            "pull_request": kept["pr"], "tip": tip, "range": f"{kept['base']}..{tip}", "track": TRACKS.get(found["size"], found["size"]),
            "criteria": found["plan"], "files": files,
            "reviews": sorted(str(file) for file in (task.directory / "reviews").glob("review-*.md")) if (task.directory / "reviews").is_dir() else [],
            "decisions": f"lem decisions list {task.slug}",
            "green": not reasons, "not_green": reasons, "careful": state["careful"], "land": land,
            # the call is the owner's whatever the agent finds, when this names why
            "owner_merges": refusal,
            "time": task_time(events_all(task), task.slug),
            # the tokens of the task's Claude Code sessions and their subagents, with what the number
            # leaves out (`covers`); null when the log names no transcript of the task
            "tokens": lem_tokens.task_tokens(task.directory.parent.parent, task.slug),
            # how many times this proposal landed again (a base that moved, a conflict): nothing bounds them
            "relands": int(kept.get("relands") or 0),
        }
        brief = task.directory / "merge-brief.md"
        write_whole(brief, "\n".join([
            # by its place in the plugin, never by this Lem's folder, which an update of the plugin replaces
            "Read `skills/lem/prompts/merge.md` in the folder that `lem version` prints as `root`, and follow it; when `lem version` fails, stop and say that `lem` is not on the PATH, with `lem doctor` as the check. Your reply is the review, in the form that file gives, and nothing else.",
            "", "The facts of this task, as `lem land merge-review` gave them:", "", "```json", json.dumps(facts, indent=2), "```", "",
        ]))
        return {"task": task.slug, "brief": str(brief), "answer": str(answer_file(task, tip)), "tip": tip, "worktree": str(task.worktree), "seat": seat, "facts": facts}
    # The reply is of the brief that named its tip: one of an earlier proposal is no read of this one.
    if read_tip is None:
        raise LandError(f"--file goes with --tip, the `tip` that `lem land merge-review {task.slug}` printed for the brief the merge agent read")
    if read_tip != tip:
        raise LandError(
            f"the merge agent's answer is of {read_tip[:12]}, and the proposal is {tip[:12]} now: it read an earlier proposal, and its answer is not written down. "
            f"`lem land merge-review {task.slug}` writes the brief of this one, and a fresh merge agent reads it",
        )
    try:
        text = Path(record).read_text(encoding="utf-8")
    except OSError as error:
        raise LandError(f"{record} cannot be read ({error.strerror}); --file names the merge agent's reply") from error
    verdict = verdict_of(text)
    if verdict is None:
        raise LandError(f"the first line of {record} gives no verdict: it is `Verdict: merge.` or `Verdict: call.`, then one sentence, as `prompts/merge.md` asks; the merge agent is asked again")
    calls = verdict == "call" or refusal is not None
    why = refusal if refusal else (next(line for line in text.splitlines() if line.strip()).strip().lstrip("#*> ").strip() if verdict == "call" else None)
    write_whole(task.directory / "merge-review.md", text if text.endswith("\n") else text + "\n")
    review = {"tip": tip, "verdict": verdict, "calls": calls, "why": why, "by": seat["seat"], "at": now_utc()}
    task.keep(merge_review=review)
    script("project.py", task.main, "log", task.slug, "merge.review", f"verdict={verdict}", f"calls:={json.dumps(calls)}", f"by={seat['seat']}",
           f"tip={tip[:9]}", *([f"why={why}"] if why else []))
    if calls:
        after = "it calls the owner: \"Read the merge review\" waits for him, and only his merge lands it"
    else:
        after = (f"the board's server merges it (`lem land merge {task.slug} --by merger --via server`): tell the owner in one line that the merge agent "
                 f"found nothing for him, and wait for the wake-up `lem: {task.slug} merged`, or `lem: {task.slug} refused`")
    return {"task": task.slug, "review": str(task.directory / "merge-review.md"), "verdict": verdict, "calls": calls, "why": why, "by": seat["seat"], "next": after}


def expected_refusal(expected: str | None, proposed: str | None, slug: str) -> str | None:
    """Why a merge given the tip its caller saw (EXPECTED, `--tip`: the commit the owner's confirm step
    showed, the one the merge agent's review read, the one his standing merge was of) may not merge
    the tip proposed now; None when they are one, or when no tip was given."""
    if expected is None:
        return None
    if not re.fullmatch(r"[0-9a-f]{40}", expected):
        return f"--tip is the whole commit the merge is for, 40 hex digits, as `landing.json` keeps `proposed`, and it is {expected!r}; nothing was merged"
    if expected != proposed:
        return (f"the merge was asked for {expected[:9]}, and the proposal is {str(proposed)[:9]} now: the branch was proposed again since, and nothing was merged. "
                f"The new proposal is read again (`lem land merge-review {slug}`), and the owner's word is for the commit he saw")
    return None


def cmd_merge(task: Task, by: str, message: str | None, via: str, standing: bool = False, expected: str | None = None) -> dict:
    if task.record["status"] != "open":
        raise LandError(f"the task is {task.record['status']!r}, not `open`; `lem land propose {task.slug}` comes first")
    if standing and by != "owner":
        raise LandError("--standing is the owner's merge that stood through a new landing: it goes with --by owner")
    # Under the task's step lock, so no proposal comes in between, and before anything of the merge is
    # kept: a word for another commit than the one proposed now merges nothing and stands for nothing.
    wrong = expected_refusal(expected, task.kept().get("proposed"), task.slug)
    if wrong:
        raise LandError(wrong)
    with merge_lock(task, by, via, standing):
        # another call may have merged this task, or the owner closed it, while this one waited
        task.read_states()
        try:
            return merge_locked(task, by, message, via, standing)
        except Refusal as error:
            # A refusal by Lem's rules is kept for that tip (`kept_refusal`), so that the server tries it
            # no more and wakes the task's session: the merge agent's, which runs with nobody to read
            # it, and a moved base's, of the owner's merge too, which the session repairs by landing the
            # task again. The owner's merge then stands for the next proposal (`tap_after`).
            if kept_refusal(by, error.kind) and task.record["status"] == "open" and task.kept().get("proposed"):
                kept = task.kept()
                tip = kept["proposed"]
                task.keep(merge_refused={"tip": tip, "by": by, "via": via, "from": "lem", "kind": error.kind, "said": str(error), "at": now_utc()})
                if by == "owner":
                    task.keep(owner_tap={"tip": tip, "not_green": kept.get("not_green", []), "via": via, "at": now_utc()})
                script("project.py", task.main, "log", task.slug, "merge.refused", f"by={by}", f"via={via}", "from=lem", f"kind={error.kind}", f"said={error}", f"tip={tip[:9]}")
            raise


def merge_locked(task: Task, by: str, message: str | None, via: str, standing: bool = False) -> dict:
    """The one merge of a task's pull request, the owner's and the merge agent's alike: through
    GitHub, at the commit that was proposed, on the base it was checked on."""
    if task.record["status"] != "open":
        raise LandError(f"the task is {task.record['status']!r}, not `open`; `lem land propose {task.slug}` comes first")
    task.need_worktree()
    kept = task.kept()
    if not kept.get("pr"):
        # every merge goes through the pull request: a branch is never pushed onto the base past it
        raise LandError(f"{task.slug} has no pull request on record; `lem land propose {task.slug}` opens it or finds it, and the merge goes through it")
    view = viewed(task)
    if view["state"] == "MERGED":
        # GitHub already holds the merge, whoever made it: only the bookkeeping is left
        return forge_done(task, view)
    if view["state"] != "OPEN":
        raise LandError(f"the pull request was closed without a merge: `lem land merged {task.slug}` writes the task dropped, and its branch keeps its commits")
    # GitHub merges into the base the pull request has now, which is not always the one it was proposed on
    wrong = base_refusal(view, task.base, kept["pr"]["url"], task.slug)
    if wrong:
        raise Refusal("tip", wrong)
    may_merge(task, by)
    tip = git(task.worktree, "rev-parse", "HEAD")
    if kept.get("proposed") != tip:
        raise Refusal("tip", f"the branch's tip is not the tip that was proposed; {AGAIN}")
    if view["headRefOid"] != tip:
        raise Refusal("tip", f"the pull request's head is not the tip that was proposed; {AGAIN}")
    missing = gate_missing(task, tip)
    if missing:
        raise Refusal("tip", f"{missing}; {AGAIN}")
    if standing and (kept.get("owner_tap") or {}).get("tip") != tip:
        raise Refusal("tip", f"no merge of the owner's stands for the proposed tip: it ended at the proposal (`lem land propose` said why), and the owner merges it again from the board or with `lem land merge {task.slug} --by owner`")
    squash = task.settings["branch"]["history"] == "squash"
    if squash and not message:
        raise LandError("branch.history is \"squash\": pass --message with the one commit's subject, from the task's report")
    if not squash and message:
        raise LandError("branch.history is \"keep\": the branch's own commits land, so --message has nothing to name")
    # The base is read after the lock is taken, so that a merge just before this one is met here.
    task.fetch()
    base_now = git(task.worktree, "rev-parse", task.onto)
    moved = changed(task, kept["base"], base_now) if base_now != kept["base"] else []
    if moved:
        then = ("the owner's merge stands while the change and the reasons it is not green stay the same, and the board's server merges it after the proposal"
                if by == "owner" else "the board's server merges it after the proposal when the merge review still says merge")
        raise Refusal("base", f"{task.onto} moved after the checks ran, by files ({', '.join(moved[:5])}{', ...' if len(moved) > 5 else ''}); {AGAIN}. "
                              f"The merge review is kept with the review, and {then}")
    how = ["--squash", "--subject", message] if squash else ["--rebase"]
    merged = gh(task, "pr", "merge", str(kept["pr"]["number"]), "--match-head-commit", tip, *how, check=False)
    if merged.returncode != 0:
        # GitHub's own rules hold (a required review, a check it waits for, a protected branch): its
        # line is kept for "Waits for you", and the owner acts on GitHub or asks Lem for a change.
        said = [line.strip() for line in (merged.stderr or merged.stdout).splitlines() if line.strip()]
        line = said[-1] if said else f"gh pr merge exited {merged.returncode}"
        task.keep(merge_refused={"tip": tip, "by": by, "via": via, "from": "github", "said": line, "at": now_utc()})
        script("project.py", task.main, "log", task.slug, "merge.refused", f"by={by}", f"via={via}", "from=github", f"said={line}", f"tip={tip[:9]}")
        raise ForgeSaid(f"GitHub refused the merge of {kept['pr']['url']}: {line}. It waits for the owner as `open`")
    # who merged, and who ran the call: the merge agent's merge is the board's server's (`--via server`);
    # the owner's that stood through a new landing ran after the checks and the reviews were checked again
    task.keep(merged_by={"by": by, "via": via, **({"after": "a re-check"} if standing else {})})
    view = viewed(task)
    if view["state"] != "MERGED":
        raise ForgeSaid("GitHub took the merge and the pull request is not merged yet (a queue, or a check it waits for); run `lem land merged` when it is")
    return forge_done(task, view)


def cmd_clean(task: Task) -> dict:
    if task.record["status"] not in ("landed", "dropped", "answered"):
        raise LandError(f"the task is {task.record['status']!r}; only a landed, dropped or answered task loses its worktree")
    removed: dict = {"worktree": False, "branch": None, "branch_left": None, "remote": None, "remote_left": None}
    # The worktree names its branch while it is there; after it, what `start` wrote down does.
    branch = task.kept().get("branch")
    if (task.worktree / ".git").exists():
        branch = git(task.worktree, "branch", "--show-current") or branch
    # Before anything goes: a branch whose name the owner protected since is not deleted here or on
    # origin, and the refusal leaves the task as it was.
    protected = protected_refusal(branch, task.settings["branch"], "deletes") if branch else None
    if protected:
        raise LandError(
            f"{protected}, and the task's branch has that name; nothing was removed. The owner takes the name out of branch.protected and "
            f"`lem land clean {task.slug}` runs again, or removes the worktree himself (`git -C {task.main} worktree remove {task.worktree}`) and keeps the branch",
        )
    if (task.worktree / ".git").exists():
        if branch:
            task.keep(branch=branch)
        # git refuses a worktree with changes or untracked files: they are someone's work until the owner says otherwise.
        git(task.main, "worktree", "remove", str(task.worktree))
        removed["worktree"] = True
    if not branch or not git(task.main, "branch", "--list", branch):
        return {"task": task.slug, **removed}
    # `branch -d` judges by the checkout it runs in, which may be behind. The proof wanted is that
    # the base holds the branch's tip, so that is what is checked before the branch goes.
    tip = git(task.main, "rev-parse", branch)
    on_base = run(["git", "-C", str(task.main), "merge-base", "--is-ancestor", tip, task.onto], check=False).returncode == 0
    if task.record["status"] != "landed":
        # A dropped task's commits are on no other branch: its branch is the owner's to delete. An
        # answered task's may hold the test that reproduced its bug, which a task started from its
        # report can take. A branch with no commit of its own, which the base (or the base branch
        # here, when a remote is behind it) holds whole, holds nothing of either, and goes.
        here = run(["git", "-C", str(task.main), "merge-base", "--is-ancestor", tip, f"refs/heads/{task.base}"], check=False).returncode == 0
        if not (on_base or here):
            held = "the dropped task's commits" if task.record["status"] == "dropped" else "the answered task's commits, the test that reproduced its bug among them when it has one"
            removed["branch_left"] = f"{branch} holds {held}; `git branch -D {branch}` deletes them"
            return {"task": task.slug, **removed}
        git(task.main, "branch", "-D", branch)
        removed["branch"] = branch
        return {"task": task.slug, **removed}
    # A pull request that the forge merged as one commit, or as a merge commit, leaves no such
    # proof in git: there the proof is that the branch's tip is the commit the forge merged.
    kept = task.kept()
    if not on_base and not (kept.get("merged") and tip == kept.get("merged_head")):
        after = ""
        if kept.get("merged"):
            merged = kept["merged_head"]

            def under(older: str, newer: str) -> bool:
                return run(["git", "-C", str(task.main), "merge-base", "--is-ancestor", older, newer], check=False).returncode == 0

            # The owner may have pressed "Update branch" on the forge and then merged as one commit: the
            # head the forge merged then holds the branch's tip and the forge's merge of the base after
            # it, and this checkout may not hold that head at all.
            if under(merged, tip):
                after = f"; the forge merged {merged[:9]}, and the branch has commits after it"
            elif under(tip, merged):
                after = (f"; the forge merged {merged[:9]}, which holds the tip of {branch} and a commit made on the forge after it "
                         f"(its \"Update branch\"), so the branch holds nothing that was not merged: `git branch -D {branch}` removes it")
            else:
                after = (f"; the forge merged {merged[:9]}, which is not the tip of {branch} and which this checkout does not hold: "
                         f"a commit made on the forge after the tip, as its \"Update branch\" makes. `git log {branch}` shows what the branch holds, "
                         f"and `git branch -D {branch}` removes it")
        raise LandError(f"{task.onto} does not hold the tip of {branch}, so the branch stays{after}")
    if kept.get("merged") and task.forge:
        # The forge's copy first, and only when it is the commit that was merged: a failure here
        # is said, and the next run finds the local branch and tries again. The ref is looked up
        # by its whole name (a pattern also matches `archive/BRANCH`), and the deletion carries
        # the commit it was checked at, so a push that came in between stops it.
        ref = f"refs/heads/{branch}"
        listed = [line.split("\t") for line in run(["git", "-C", str(task.main), "ls-remote", "origin", ref]).stdout.splitlines()]
        there = next((commit for commit, name in listed if name == ref), None)
        if there and there != kept.get("merged_head"):
            removed["remote_left"] = f"origin has {there[:9]} on {branch}, which is not the commit the forge merged; it stays"
        elif there:
            git(task.main, "push", f"--force-with-lease={ref}:{there}", "origin", f":{ref}")
            removed["remote"] = branch
    git(task.main, "branch", "-D", branch)
    removed["branch"] = branch
    return {"task": task.slug, **removed}


def step(task: Task, args: argparse.Namespace) -> dict:
    """One step of a task's landing, which `main` runs under the task's step lock."""
    if args.command == "start":
        return cmd_start(task, args.conflicting)
    if args.command == "base":
        return cmd_base(task)
    if args.command == "polish":
        return cmd_polish(task, args.done)
    if args.command == "checks":
        return cmd_checks(task)
    here = Path.cwd()
    if args.command == "read":
        return cmd_read(task, args.record and task_file(args.record, "--record", task.directory, here))
    if args.command == "file":
        return cmd_file(task, args.again)
    if args.command == "propose":
        return cmd_propose(task, args.title, task_file(args.notes, "--notes", task.directory, here))
    if args.command == "merge-review":
        if args.tip and not args.file:
            raise LandError("--tip goes with --file: the tip of the brief whose answer is written down")
        return cmd_merge_review(task, args.file and task_file(args.file, "--file", task.directory, here), args.tip)
    if args.command == "merge":
        return cmd_merge(task, args.by, args.message, args.via, args.standing, args.tip)
    if args.command == "merged":
        return cmd_merged(task)
    return cmd_clean(task)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="lem land", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=".", help="a directory inside the checkout (default: the current one)")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("base").add_argument("slug")
    checks = commands.add_parser("checks")
    checks.add_argument("slug")
    look = checks.add_mutually_exclusive_group()
    look.add_argument("--status", action="store_true", help="whether the checks run now, for how long, and how their last run ended; starts nothing")
    look.add_argument("--stop", action="store_true", help="stop the checks that run now, and wait for their end; with none, nothing is stopped")
    for name in ("merged", "clean"):
        commands.add_parser(name).add_argument("slug")
    start = commands.add_parser("start")
    start.add_argument("slug")
    start.add_argument("--conflicting", action="store_true", help="for an open task the forge calls conflicting, with no merge of a task to name")
    polish = commands.add_parser("polish")
    polish.add_argument("slug")
    polish.add_argument("--done", action="store_true", help="after the polish builder: check what it committed, and log the pass")
    read = commands.add_parser("read")
    read.add_argument("slug")
    read.add_argument("--record", metavar="FILE", help="a JSON file that says what the review was and what it found; without it the step says what is due")
    filing = commands.add_parser("file")
    filing.add_argument("slug")
    filing.add_argument("--again", action="store_true", help="write once more each item that was filed and is gone from the tip")
    propose = commands.add_parser("propose")
    propose.add_argument("slug")
    propose.add_argument("--title", required=True, help="the subject of the change, one semantic line")
    propose.add_argument("--notes", required=True, metavar="FILE", help="the notes of the pull request: decisions, what is left open, what is worth a look, what was filed, what was not done")
    review = commands.add_parser("merge-review", help="what the merge agent reads, in a brief file; with --file, its review written down")
    review.add_argument("slug")
    review.add_argument("--file", metavar="FILE", help="the merge agent's reply, its review with the verdict on its first line")
    review.add_argument("--tip", metavar="COMMIT", help="with --file: the `tip` the step printed with the brief the agent read; the answer of another proposal than the one now is refused")
    merge = commands.add_parser("merge")
    merge.add_argument("slug")
    merge.add_argument("--by", required=True, choices=BY, help="who merges: the owner's word, or the merge agent where the settings and the request allow it")
    merge.add_argument("--message", help="the subject of the one commit, when branch.history is \"squash\"")
    merge.add_argument("--via", choices=("session", "server"), default="session", help="who runs this call: a session (the default), or the board's server, which runs the merge agent's merge and the owner's merge from the board")
    merge.add_argument("--standing", action="store_true", help="with --by owner: the owner's merge that a moved base refused and that stood through the new landing; the board's server runs it")
    merge.add_argument("--tip", metavar="COMMIT", help="the whole commit the caller saw: the one the board's confirm step showed, the one the merge review read; any other proposal is refused, and nothing is merged or kept")
    args = parser.parse_args(argv)
    try:
        task = Task(Path(args.repo), args.slug)
        if args.command == "checks" and (args.status or args.stop):
            # a look and a stop take no lock: they are about the run that holds it
            result = checks_stop(task) if args.stop else checks_status(task)
        else:
            with step_lock(task, args.command):
                result = step(task, args)
    except LandError as error:
        sys.exit(f"land.py: {error}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
