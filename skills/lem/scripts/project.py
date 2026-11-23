"""Say where one repository keeps what Lem reads, and what its flow settings are.

Every project keeps its own settings in its repository: the machine checks of a landing,
what must never go wrong there, who lands, the seats, the tracker. `.lem/settings.toml`
at the root of the checkout names them, the team's file, in git;
`.lem/settings.local.toml` beside it is the developer's own for that one repository, and
`settings.toml` of Lem's home folder (`lem_state.home_settings_file()`) his own for
every repository on the machine. The nearest file that holds a setting wins. What Lem
reads beside them has one place each and no setting (`PLACES`): Lem's own files under
`.lem/` (the profile, the personas, the lessons, the worktrees), the rules for the code
in the harness's folder (`.claude/rules`), the review tool's folder (`.revmux`) and the
backlog (`docs/backlog`). A project that keeps one of them in another place moves it
there. The plans folder, the name of a plan's file there, and the rulings file are
settings (`[paths]`): a team that adopts Lem may have its own.

    lem project show                everything, resolved, as JSON
    lem project path NAME           one path, absolute: plans, rulings (the file), or a place of PLACES
    lem project may-land BRANCH     exit 1 unless tasks of this project may land on BRANCH
    lem project init [--base NAME] [--codex yes|no]
                                    write .lem/settings.toml, with a whole seat for each of the
                                    three: the reviewer on Codex and two experts, or with
                                    `--codex no` (the machine check found no Codex) the
                                    reviewer on Claude and one expert
    lem project set global|local NAME VALUE
                                    write one line of [seats]: global in ~/.config/lem/settings.toml,
                                    for each repository on this machine that names none, local in
                                    this repository's .lem/settings.local.toml, for this machine only.
                                    NAME is reviewer, planner, merger, session, experts or fallback;
                                    VALUE a whole seat, one or two joined by a comma for experts,
                                    false for fallback only, or default, which takes the line out.
                                    Every other line of the file stays; nothing writes
                                    .lem/settings.toml. It prints the seat show then gives
    lem project load [--start N|none]
                                    the load average under which the checks of a landing start on
                                    this machine (40 when none is set), and the load now; --start
                                    sets the number for every repository here, and none takes
                                    the gate away
    lem project handoff [--tokens N|default]
                                    the number of tokens past which a task's session compacts
                                    itself, for every repository here; 0 leaves it to Claude Code
    lem project rules [FILE ...] [--range BASE..TIP]
                                    the rule files of .claude/rules that cover these files, as JSON
    lem project task-dir SLUG [--ask TEXT] [--ticket ID [--ticket-repo OWNER/REPO]] [--branch NAME] [--night YYYY-MM-DD]
                                    make and print one task's state directory; keep the owner's words
                                    and the ticket the ask came from: MBZ-12 for Linear, #42 for
                                    GitHub, with the repository of the issue that was read. A ticket
                                    another task holds is refused, until that task was dropped or
                                    answered and owes the ticket nothing. At a task's opening it
                                    refuses a slug whose branch origin has already: TYPE/SLUG for
                                    every type, or the NAME --branch gives. --night marks the task
                                    as the night's, which runs it without the owner. A task it opens
                                    gets its mark, release.txt: the release its project's sessions load
    lem project ticket-step SLUG started|assigned --login LOGIN|unassigned|commented|landed|dropped|answered
                                    write down what Lem did to the task's ticket, once
    lem project worktree-dir SLUG   print where the task's worktree goes, inside a folder git ignores
    lem project worktree SLUG BRANCH
                                    make the task's worktree there, on BRANCH: a branch that exists
                                    as it is, a new one from origin's base branch after a fetch
                                    (from the local base branch with no remote, or when origin
                                    does not answer), with no upstream; then run checks.setup in
                                    it one time, so that its tests can run
    lem project state SLUG STATUS LINE...
                                    put a new block at the top of the task's state.md, with the time.
                                    For the block that names the task's path with its type line, the
                                    first of a day's task, it prints `say` too: the task's first line
                                    to the owner, which its session says as it is. The hold of an
                                    order that names no task names no path: the first block after
                                    it that names one prints it, with the hold's type line. It
                                    refuses a type line, the owner's order, a `then:` line and the
                                    line of the one open task that fits in another form
    lem project seat SLUG SEAT      the seat in use for the task, as `show` parses one: the fallback
                                    while it stands in for SEAT (`from` is `stand-in`), else the seat
                                    the settings name, with its `from`; every stage that opens a seat
                                    takes it here
    lem project seat-failed SLUG reviewer|planner|merger --seat LINE --error missing|login|tokens|model [--said TEXT]
                                    the agent on LINE, the seat the stage opened, gave one of the four
                                    errors: the fallback stands in for SEAT from now on (it prints the
                                    seat to open, with `say`), or the task is `blocked` with the seat
                                    and the error and the line `the seat that failed: SEAT` (it prints
                                    `blocked: true` with `say`): when the fallback is false, when it
                                    is LINE, or when its agent may not sit in SEAT. The experts and
                                    the session take no fallback
    lem project seat-again SLUG     the owner's go on over such a block: the block before it comes
                                    back, the stand-in ends, and the seat the settings name is tried again.
                                    No other state but a park, another block or an end comes over it
    lem project tasks               every task's ask, status and newest state block, as JSON
    lem project owner away|back --words TEXT
                                    the owner says that he is away, or back again: his words as typed,
                                    kept in the machine's mark, so every repository on this machine
                                    reads them. It changes nothing in a build, which asks him nothing
                                    either way: an interview and criteria that wait for his yes read it
    lem project owner watch --seen N [--every SECONDS]
                                    look at the machine's mark every 5 seconds, and end with his
                                    status as JSON (`away`, `since`, `words`, `seen`) as soon as the
                                    mark holds another number of records than N, owner.seen of
                                    `waiting`: at once when it does at the start. It writes nothing
                                    to the mark; a session of a task's shape keeps it in the background
    lem project log SLUG EVENT [key=value ...] [key:=json ...]
                                    append one event about a task to the log the board draws
    lem project resume SLUG         the owner's word to go on with a task he put aside: a parked task
                                    gets back the block that `parked` put aside (a breaker's wait, the
                                    criteria's) and stays in its worktree; a dropped task stays ended,
                                    and a new task opens from its files, its handoff and its branch's
                                    commits, as SLUG-2 (then -3) on TYPE/SLUG-2 cut from the old
                                    branch's tip, with `resumed-from.txt` naming the old one; a
                                    dropped task resumes only with a breaker that waits and with its
                                    events whole: after `prune` made them one summary event, the
                                    refusal ends with `/lem` and its ask, the new task to open. A
                                    dropped task the release stop blocked (a `release.stop` of its
                                    own in the log) needs no breaker: SLUG-2 opens as a new request
                                    on this release, with the old notes and no record, no state and
                                    no worktree, on TYPE/SLUG-2 cut from the branch the stop named,
                                    or from the base when git has none; `next` names its step,
                                    `lem session open SLUG-2 --why new`
    lem project may-start SLUG      exit 1 for a task in `landing`, `open`, `parked` or an ended state, which
                                    gets no lead, and for a task `queued` with an `after: OTHER`
                                    line while OTHER has not landed or been answered, whether it needs
                                    OTHER's result or the owner's words put it after OTHER; the refusal
                                    names the way out of each. A dropped OTHER leaves it queued for the
                                    owner's word, and the refusal prints the commands of his "start
                                    SLUG now", from the task's newest block, which the agent runs only
                                    when it printed them after his word. No count of tasks stops a
                                    start: each start by day is the owner's own request
    lem project state-dir           the folder that holds every task, the event log and the night reports
    lem project serial -- COMMAND ...
                                    run one test command that two tasks cannot run at the same
                                    time (checks.serial), under the repository's one lock for them
    lem project waiting             everything that waits for the owner, as JSON: the rows of the board's
                                    "Waits for you" (a breaker, criteria or a step of his, a blocked task,
                                    a plan, a merge review, a pull request with green or not, a task with
                                    no session, a task whose session stopped after the status message and
                                    its restart, or after the message alone when Lem cannot read the
                                    session), and last night's report
    lem project proposals add --kind retro|night [--date YYYY-MM-DD] --file FILE|-
                                    add a run's proposals to the record of its day, made when it is
                                    not there, with the numbers after those already there; a run
                                    of no proposal is kept too
    lem project proposals read      every proposal with no verdict, of any day, the refuted, passed
                                    and dropped ones of every day, and the newest run of each kind
    lem project proposals verdict --file FILE|-
                                    the reviewer's verdict on each proposal, refuted with its reason
                                    or passed with its area; the passed ones of one area become one
                                    item of the state folder's backlog
    lem project proposals drop PATH the owner's drop of a reviewer's item: refused while a task that
                                    has not ended holds it; else each proposal's drop is kept in its
                                    record, and the item's file goes
    lem project plan-file SLUG [--date YYYY-MM-DD]
                                    the name a task's plan takes (`paths.plan_file`), and the plan
                                    of the task the plans folder holds, as JSON
    lem project may-nap             whether a nap may start now, as JSON, and when it may, the nap is
                                    written down as started
    lem project prune [--dry-run [--days N]]
                                    remove what the state folder no longer needs, older than
                                    `state.keep_days` days, leave each ended task with no event in
                                    that time its small record only and its events one summary
                                    event, and say what went, which tasks it summarized with the
                                    count of their events, and where the number came from, as JSON;
                                    the board server runs it. --dry-run
                                    removes nothing, writes nothing and says what would go, and --days
                                    says it for another number than the settings'

Task state is kept in `.lem/state/` of the main checkout, the one folder `lem_state.py`
names for every script: every worktree writes there, git never tracks it, a worktree's
removal does not take it, and a session that replaces another finds it.

An ended task stays ended. `state` refuses a move out of `landed`, `answered` or
`dropped` (the same status again is taken), so that a stale wake-up, a lead that
finished after a later step, cannot reopen it: new work for it is a new ask, with a slug
of its own.

Each command that names one task runs the release rule first (`lem_release`): a task
begun two releases back or more stops it with exit 1 and a message that names the way
on, logged once as `release.stop`, and its state stays as it is. `state SLUG` with
`dropped`, `landed` or `answered`, the three ends of a task, and `resume` of a dropped
task pass, and log the same stop once; `resume` of a parked task stops. A dropped task
with a stop of its own resumes as a new request, from its notes and its branch, and
reads none of its records. A task begun on a newer release than this Lem stops each
command, and nothing is written.

Every state block is also an event. `events.jsonl` in the state folder is the record,
one JSON object per line: `ts` (UTC to the second), `event`, `task`, then the event's
fields; the board server (`lem serve`) reads it as it grows, and whole again when it is
a new file. Each writer appends under the log's one lock (`lem_state.events_lock`). Only
`prune` shortens it: past `state.keep_days`, all the events of a task that ended become
one `task.summary` (`summary_of`) in the place of its newest, with the facts the board
and `tasks` read of an ended task and the paths of its transcripts, which `lem_tokens`
reads, and the new log replaces the old one under the same lock. `log` refuses a
`task.summary`. `state` writes `task.state` with the status, the lines, the ask and the
branch and newest commit of the task's worktree, so the board needs no agent to remember
a second command, and for the block that names a day's task's path with its type, the
task's first line to the owner as `say` (`opening_line`), which `state` prints too, and
`say_named`, the same line as the session where he typed the request says it, with the
task named and in its commands (`lem session wait SLUG --first-line` prints it). `log`
writes any other event: `key=value` stores a string and `key:=value` parses JSON, so a
commit made only of digits stays a string and an exit code stays a number. The start of
each stage that logs its end has a fixed form (`STARTS`: `interview.start` and
`interview.end`, the end of the questions to the owner, `scout.start` and `scout`,
`read.skip.asked`, the question whether he skips the personas' read,
`criteria.read.start`, `investigation.start`, `builder.start`, and the three `land.py`
writes, `polish.start`, `gate.start` (the start of the checks) and `review.start`), so
that the board draws each span from its start to its end, and tells who acts on a held
interview from them. Four more events have a fixed form. `plan.talk.start`, which the
defender of a careful or large plan writes when the reviewer's seat opens, as
`reviewer=AGENT`, so that the board draws the talk from its start. `plan.talk`, which
the landing reads and the plan's defender writes after the talk, as `reviewer=AGENT
turns:=N questions:=N settled:=N open:=N repaired:=N design:=N unargued:=N root:=N
layer:=N shared:=N`: the turns, the questions of the reviewer's first list, how many of
them were settled and left open (the two add up to questions), how many the defender
repaired, how many of the open ones are a design choice, how many were raised after the
list and not argued, how many repairs changed a decision of the plan and how many put a
layer over a decision with a cite (the two add up to at most the repairs), and how many
decisions two questions named. The rules of a talk keep it within 4 × questions + 2
turns; a record over that bound is taken as it ran, and `log` adds the bound to it as
`bound`, for the landing and the board to say that the talk went over. `tasks` gives
each task its newest `plan.talk` as `talk`, the record Lem and a builder read before the
build of a careful or large plan. The owner's status is no event of a repository's log:
`owner` appends it to the machine's mark, `owner.jsonl` in `$XDG_CONFIG_HOME/lem`, or in
`~/.config/lem` when that variable is not set, one record in the form of an event,
`event` `owner` with no task and `away`, `by` `owner`, his `words` and the `repo` he
typed it in. Every repository on this machine reads it, its newest record holds, and
with no mark he is there. `owner` writes the folder and the file, and no other command
of Lem's writes in the home directory beside the machine's own files (`lem_state`).
`task.mode` is the night's mark, which `task-dir --night` writes, as `mode=alone by=lem
words="the night of YYYY-MM-DD"`. A task runs without the owner while he is away, and a
night's task from its mark until it ends, whatever his status; `tasks` gives each task
`mode` (`alone` or `with-owner`, now), `mode_since` and `without_owner`, each span of it
with the words that started and ended it, and the night's date as `night` (null for a
task of the day). And `criteria.read`, which Lem or the lead writes after the personas
read the acceptance criteria, as `by=lem|lead asked:=N answered:=N families:='["FAMILY",
...]' silent:='[{"name": ..., "why": ...}]' criteria:=N flagged:=N split:=true|false
digest=DIGEST`: who ran the read, how many personas were asked and how many answered,
the model families that answered, each source that did not and why (a partial read
counts), how many criteria were read and how many an answer flagged, whether the
families split, and the digest `lem criteria digest` gives for the criteria read. A read
in which nobody answered is written too, with `answered:=0`, no family and each source
that was asked in `silent`; the landing counts two of those in a row as criteria that
went on unread. `investigation`, which Lem writes after it reads the investigator's
report of a fix or a question, as `type=fix|question call=CALL line=TEXT
[where=PATH:SYMBOL] [reproduced:=true|false]`: a fix's call is small (the fast track),
full (the standard track), not-a-bug or not-reproduced, and it says whether the bug was
reproduced; a plain cause names its place; a question's call is answer. `tasks` gives
each task its newest as `investigation`, and `state SLUG answered` refuses a task with
no `investigation.md` and no record whose call is not-a-bug or answer.

A state line that starts with `type:` names the type of the request with its reason, as
`type: fix, because the total is wrong today`, one of feat, fix, docs, refactor, perf,
test, chore and question; `state` refuses any other, and `tasks` gives the newest
as `type`.

Lem's settings are four files, and each table is valid in some of them only
(`lem_state.TABLE_PLACES`, the one map): a table in another file is refused, and the
refusal names the file where it is valid. `machine.toml` of the home folder holds what
is true for the whole machine, `[load]`, `[serve]`, `[peers]`, `[handoff]` and
`[corrections]`, and nothing overrides it (`lem_state`). The three `settings.toml` files
hold the rest, and for a setting that more than one of them may hold, the nearest that
holds it wins: `.lem/settings.local.toml`, then `.lem/settings.toml`, then the home
folder's `settings.toml`, then Lem's default. `show` names in `from` the file each such
value came from: each seat, each expert, the fallback, `naps.on` and `state.keep_days`.
It gives `corrections.collect`, the machine's yes or no to the correction queue, with
`from` too: `machine.toml`, which `lem corrections collect yes|no` writes, or Lem's
default, which is no, and which `/lem init` asks about.

The home folder's `settings.toml` is the developer's own for every repository on the
machine: each seat and the fallback (`[seats]`, which `lem project set global` writes),
and the question page's defaults (`[ask]`, which only that page reads; here only its
keys are checked). What guards a team's repository (`[flow]`, `[checks]`, `[branch]`,
`[paths]`, `[tracker]`) is valid in the team's file only. `keep_days` is a repository's
(the owner, 2026-11-21), and so is the naps' switch: this file refuses `[state]` and
`[naps]` too.

`.lem/settings.local.toml` is one person's or one day's choice on one machine for one
repository: who sits in each seat of this repository, before the team's file and the
home folder's `settings.toml` (`lem project set local` writes it; an agent that gives an
error needs no edit here, since `seats.fallback` stands in for it), a no to the naps,
which spend that person's tokens, and how many days the state folder keeps old files on
this machine's disk. It is not committed (`init` writes `.lem/.gitignore` for it), and
it is read from the main checkout, because a task's worktree has no copy of a file git
does not track. It may hold `[seats]`, `[naps]` with `on = false` and `[state]` with
`keep_days`, and nothing else: the checks, what must never go wrong, the protected
branches and who lands are the project's rules, and a file nobody reviews must not open
them. For the same reason it can switch the naps off for its person and never on:
nobody's tokens are spent because of a file that git does not show. `show` names each
setting that came from it: a seat by its `from`, any other in `local.overrides`.

The rules for the code are the markdown files of `.claude/rules`, the folder Claude Code
loads by itself; Lem writes none of them and moves none. A file scopes itself to paths
in its frontmatter, in Claude Code's form (`paths:` with a list of globs), and a file
without that covers every path. `rules` is the one place that matches a change against
those scopes: a builder's brief, the message to the reviewer and a review round all get
its answer, so an agent that does not load the folder by itself (Codex, the agents of
the review tool) reads the same rules as one that does.

What must never go wrong is `flow.topics`: sentences in the owner's words, against which
an agent reads an ask, a plan and a diff. No list of paths says whether a change is
careful: such a list goes stale as the code moves, misses new code, and a branch can
edit the list that guards it. The `[flow]` table is read from the main checkout's
settings, also in a task's worktree, as the checks are read by the landing: a branch
that empties its topics or shortens the owner's wait lifts nothing, since every lead,
reviewer and landing reads the table as the main checkout has it. The table the branch
writes is still checked, so that its error shows before it lands. `[naps]` is read the
same way: a nap spends the tokens of whoever works on the machine, and a branch does not
switch them on.

The main checkout's settings are its working tree's `.lem/settings.toml` while it is on
the base branch: an edit of the owner's there counts at once, committed or not. When
another branch is checked out there (a colleague's, `gh pr checkout 57`), the file is
read as the base branch's newest commit holds it (`git show BASE:.lem/settings.toml`),
with one line on stderr when the two differ, so that branch does not change who lands
and what is careful for every running task. The base is the branch the file names: the
file of the remote's default branch is read first, then the one of the branch the main
checkout's own copy names, and a file that names another base is read on that one.
Before any commit of the base holds the file (an onboarding, on its own branch), the
working tree is read. `show` says which in `settings_from`.

`[checks]` holds the machine checks of a landing: `commands`, the whole suite, `setup`
and `serial`. `checks.setup` is what a new worktree needs before its tests can run
(`uv sync`, `npm ci`): `worktree` runs it one time in a worktree that it makes, and
`lem criteria red` in each of its two fresh worktrees; its output goes to `setup.log` in
the task directory. `checks.serial` names the tests that two tasks cannot run at the
same time: an end-to-end suite that uses fixed ports, one database or a browser.
`serial` runs any command under one lock for the repository, `serial.lock` in the state
folder, apart from the landing's lock, since a builder takes this one too: the checks of
a landing run each `checks.serial` command through it after `checks.commands` pass,
`lem criteria red` runs a criterion's test of such a suite through it, and a builder
runs such a test through it in its worktree. Builders of other tasks go on meanwhile:
the lock holds only these commands. It waits while another run holds the lock and says
so on stderr with the holder's line, passes the command's exit status through (128 and
the signal's number for a command a signal ended), and ends the command's process group
when it is stopped. The lock is the kernel's: it goes with the process that holds it,
however that ends, so a file a dead run left blocks nothing. One word list after `--`
runs as it is; one quoted line runs in the shell, as a command of the checks does.

A seat is one string, `agent/model:effort`: `seats.reviewer`, the agent in the
reviewer's pane; `seats.planner`, the defender of a plan talk; `seats.merger`, the merge
agent, which reads each proposed task and merges it or calls the owner; `seats.session`,
the agent of each task's own session (`lem session open`), only `claude` for now; and
`seats.experts`, the one or two experts, the last level of the ladder of a decision in
doubt. Each seat comes from the first of four places that names it: this machine's own
file for the repository (`.lem/settings.local.toml` of the main checkout), the team's
file (the branch's copy in a task's worktree), the developer's own file for all his
repositories (`[seats]` of the home folder's `settings.toml`,
`lem_state.home_settings_file()`), else Lem's default (`DEFAULT_SEATS`:
`claude/opus:high` for the reviewer, the defender, the merge agent and the session, and
`EXPERTS`). A file's seat replaces the ones after it whole, and the experts' list too.
`show` gives each seat, and each expert, with `from`: the file's name as above, or
`Lem's default`. `seats.fallback`, from the same four places, is the seat that stands in
for the reviewer, the defender or the merge agent when its agent gives an error: a whole
seat turns it on, `false` turns it off, and with no line in any place it is
`claude/opus:high` (`FALLBACK`); `show` gives it as a seat with `from`, or as
`{"seat": false, "from": ...}`. The experts and the session take no fallback. When a
stage sees one of the four errors of a seat's agent (the program is not on the Mac, no
login, no tokens, an unknown model; a slow agent is none), `seat-failed` alone decides,
under the task's lock: the fallback stands in, logged as `seat.stand-in`, and holds that
seat for the task until it ends or the owner's go on (`seat-again`, which logs
`seat.again`); or the task is `blocked`, logged as `seat.blocked`, when the fallback is
off, is the seat that failed, or has an agent that may not sit in that seat.
`seat SLUG SEAT` is the seat in use, the one every opener starts. `show` marks each
expert `here` when its agent is on this machine (Claude Code always, Codex when its
command is on PATH): only those answer, so without Codex the default's one Claude expert
answers alone. The reviewer's, the defender's, each expert's and the fallback's seat is
written whole, in each of the three files, and `show` and `set` refuse one that leaves
out its model or its effort (the owner, 2026-11-18: "I think it should be explicitly
`agent/model:effort` in all 3; not simply "claude" or "codex""); `init` writes the three
so. The merge agent's and the session's seat may leave out the effort (`claude/opus`),
and the model too (`claude`, `claude:high`): the part a named seat leaves out is that
agent's own default, and Lem passes nothing for it; `set` still takes only a whole seat
for them. `show` gives each seat parsed, as `agent`, `model`, `effort` and the `seat` as
written, with its `from`. `set global` and `set local` write one line of `[seats]` in
the home folder's `settings.toml` or in this machine's own file for the repository, and
keep every other line of it (`lem_state.edited`); no command writes the team's file, and
none writes a seat into `machine.toml`, which refuses `[seats]`.

A plan's file is named by `paths.plan_file`, a pattern of the tokens `YYYY`, `MM`, `DD`
and `<slug>`, `YYYY-MM-DD-<slug>.md` unless the settings say otherwise. A task's plan is
found by it: `lem_plans` is the one place that builds and finds the name, and
`plan-file` prints both. The owner's rulings are one markdown file, `paths.rulings`
(`docs/rulings.md` unless the settings say otherwise), one bullet for each ruling under
the heading of its group. A value that is no `.md` file, or that names a folder, is
refused: the retro, the ladder and the question gate read one list.

`waiting` is the one list of what waits for the owner, which a bare `/lem` says. Its
rows are the rows of the board's "Waits for you" (`lem_board_model.waits_of`, over the
model the board server builds: the event log, the owner's mark, the forge's last look
that the server keeps in `forge.json` of the state folder, and the task sessions, from
`lem session list`, which it asks itself when the log has a `session.open`), so the
terminal and the phone list the same. First his status (`owner`: `away`, `since` and his
`words`, from the machine's mark, and `seen`, the number of its records, from which a
watch of the mark starts); then one group for each kind of row: the breakers that wait,
as `lem decisions pending` gives them (`breakers`); the tasks `held` with the line
`the criteria wait for the owner` (`criteria`) and the other `held` ones, a step of his
or one more fact (`held`); a task `queued` after a task that was dropped
(`after_dropped`, with that task as `after` and the row's own words: `verb`, `start`,
"start SLUG now", `drop`, `/lem drop SLUG`, and `where`, which says that he types either
one in any Lem session of the repository); a task its session stopped as `blocked` on
something it cannot settle, not one that waits for the base to be green again
(`blocked`); a plan that names him (`plans`); the merge agent's review that calls him
(`reviews`, with its `why` and `tip`); each `open` task whose merge waits for him, a
review of the proposed tip that calls him, a refused merge of it, or no proposal on
record, with its proposal (`pull_requests`: `pull_request`, `green`, `not_green`,
`conflict`, true or false as the forge said it of the pushed head at the last
`lem land merged`, null when nothing asked or the head moved since, `merge_review` and
`merge_refused`, each null when the task has no `landing.json`); and a task stuck for
want of its session (`no_session`, with `need`: `gone`, no live session, or `deaf`, a
wake-up unanswered for 10 minutes); and a task whose live session showed no sign of work
after the status message and the restart, or, for a session whose signs of work Lem
cannot read, no event of the task after the status message alone, the stop the board
server logged (`stopped`, with `open`, the command that opens a fresh session beside it,
and `unread`, true for such a session). Each of these has the task's `task`, `ask`,
`since`, `night` and its state's first `line`. `rows` is the board's rows in its order,
each `{key, kind, task}`. `tasks` is the same rows grouped by task, as the board's
stacks (`lem_board_model.wait_stacks`): one entry for each task in the place of its
first row, with the task's `task`, `ask`, `since`, `night` and `line`, and `things`,
each of its rows in their order as `{key, kind, verb}`, `verb` the row's own words
("Read the merge review", "Merge the pull request #73"). `sessions` says whether the
sessions are known (`known`) and, when not, why (`said`): then no row of `no_session`
can show. `forge.looked` is the time of the server's last look at the forge, or null.
`count` is the tasks of `tasks`, each once however many things of it wait. The proposals
of the night and the retro are no row and not counted: they reach the owner only as the
reviewer's items on the board's "Backlog" view. A task's `night` is the date of the
night that opened it, or null; its report is `night/DATE.md` in the state folder.
`night_report` is the report of last night, today's or yesterday's, or null; it waits
for no answer and is not counted, and neither is `parked`, each task the owner put
aside, with the line that says why. It reads and writes nothing else.

The proposals of the night and the retro go through a reviewer before the owner sees any
(`proposals`). Each kind of run keeps one record a day in the state folder,
`retros/DATE.json` and `night/DATE.json` (beside the night's report, `night/DATE.md`):
its `date`, its `kind`, its `runs` (each with its time `at`, what it `read`, and the
numbers of the `proposals` it added), its `proposals` (each with its `number` from 1,
its `area`, the `move` in one line, its `body`, its `source` and its `where`, the path
or `PATH:SYMBOL` it would change), and the verdicts: `refuted` (each with the reviewer's
`reason` and the `day`), `passed` (each with its `area`, the `item` it went into and the
`day`) and `dropped` (each with its `text`, `said` "the owner dropped it", the `day` and
the `item`). `add` makes the day's record when it is not there and appends a run, also a
run of no proposal, with the next numbers, and never rewrites a number, a verdict or a
drop, so a second retro of a day keeps the first one's. `read` gives each proposal by
its name, `KIND of DATE #N`. `verdict` takes each proposal's verdict once: the passed
ones of one area become one item of `.lem/state/backlog/`, named by the words of the
title the reviewer gives the area (`-2`, `-3` when the name is taken), in the backlog's
item format with the front-matter line `proposals: KIND of DATE #N, ...`; no item when
nothing passed. A reviewer's item is held while a task that has not ended has its path
as its ask, and `drop` refuses it then, with that task in its JSON (`held_by`) on
stdout; else it keeps the drop of each proposal the item names and removes the file, in
one call under the records' one lock (`proposals.lock` in the state folder), which `add`
and `verdict` take too. `task-dir --ask` refuses the path of such an item whose file is
gone. A record that does not have this form is refused with the fix; one in the form of
Lem's question page, which the retro wrote before, is converted by hand.

A nap is an optional part (`[naps]`, off unless the owner says yes): a fresh agent that
reads the recent tasks, dreams, and writes the dream down in a folder of its own,
`naps/TIME-WORDS/` in the state folder, where TIME is the clock's UTC time when the nap
started, as `YYYY-MM-DD-HHMM`. `may-nap` is the one place that says whether one may
start: the naps are on, no nap runs, and the newest one started 6 hours ago or more
(`NAPS_GAP_HOURS`), or there is none. A nap runs from its start until its folder holds
`waking.md`, the last file it writes, and for an hour at most (`ASLEEP_MINUTES`). Its
answer is JSON with exit 0 whether it says yes or no, because a no is the usual answer
and nothing is wrong; a broken settings file is exit 1. A yes writes `naps/.asleep` with
the start, so a second call finds the nap that runs.

The state folder does not grow without end (`prune`, the owner's word of 2026-11-21).
What Lem no longer needs goes `state.keep_days` days after it was last needed, 30 unless
the settings say otherwise. The project's number is the base branch's, in a task's
worktree too, so a branch cannot lower it. This machine's own file,
`.lem/settings.local.toml` of the main checkout, may set its own number, lower or
higher, which wins on this machine and in each of its worktrees: it removes only this
machine's files. `show` and `prune` say in `from` which file the number came from. A
task that ended (`landed`, `dropped`, `answered`) and of which the event log holds
nothing newer than that has its events replaced with one summary event, then loses every
file of its folder but its small record (`lem_artifacts.SMALL_RECORD`): its state, its
request, its pull request, and its ticket's and its resume's files, which `tasks`,
`may-start`, `task-dir`, the ticket's owed steps and `resume` read. Its pictures, its
pages, its report, its decisions, its criteria and its reviews' records go, so a retro
or a nap after that time finds none of them. A task that is open is never touched, and
one whose state.md does not read, or whose state the log does not agree with, is named
in `skipped` and left as it is. Whole entries go from the other folders (PRUNED): a
question to the experts and a panel's folder after their last write, a nap after the
time in its name, and a copy of the cast after its last write or read. The event log,
the night reports, the records of the proposals (`retros/`, `night/`), the reviewer's
items (`backlog/`) and the correction queue stay. Nothing is removed through a link or
outside the state folder, and each removal that fails is named in `failed`, with exit 1,
while the others go on. The board server runs it for each workspace (`serve.py`, the
duties across tasks); `--dry-run` says what would go and removes nothing, and with
`--days N` it says that for another number.

A settings file with an unknown key, a wrong type or a path outside the repository is an
error: a stage that read half of it would run on defaults nobody chose. Needs Python
3.11 for tomllib.
"""

import sys

if sys.version_info < (3, 11):
    # an old python3 must still load this file, so that it can say what it needs and not
    # a traceback
    sys.exit(
        "project.py: Lem needs Python 3.11 or newer, and this python3 is "
        f"{sys.version.split()[0]}; put a newer one first on PATH, "
        "or run this file with it"
    )

import argparse
import contextlib
import difflib
import fcntl
import fnmatch
import importlib
import json
import os
import re
import shlex
import shutil
import signal
import stat
import subprocess
import tempfile
import threading
import time
import tomllib
from collections.abc import Generator, Sequence
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any, TypeVar, cast

if TYPE_CHECKING:
    from lem_board_model import Model

# The one place that says where the state is, shared with the scripts that cannot import
# this file.
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lem_artifacts  # noqa: E402
import lem_plans  # noqa: E402
import lem_state  # noqa: E402

# The release a task began on, and the rule that stops a command for a task two
# releases back.
lem_release = importlib.import_module("lem_release")

# The team's file, in git, and the developer's own for one repository, beside
# it (`lem_state`).
SETTINGS = lem_state.TEAM_SETTINGS
LOCAL = lem_state.LOCAL_SETTINGS
# the tables one machine may set for itself in one repository; of [naps] only
# `on = false`, and of [state] its one key, `keep_days` (`lem_state.TABLE_PLACES`)
LOCAL_TABLES = tuple(
    table for table, places in lem_state.TABLE_PLACES.items() if "local" in places
)
# What Lem reads beside its settings, each in one place with no setting (the owner's
# note of 2026-11-18 on the plan, task 1b of
# docs/plans/2026-11-18-core-and-two-modes.md): Lem's own files, the rules for the code
# in the folder Claude Code loads by itself, the review tool's folder, and the backlog
# where the agterm cookbook's recipe keeps it. `lem project path NAME` answers for each.
PLACES: dict[str, str] = {
    "profile": ".lem/profile.md",
    "personas": ".lem/personas",
    "lessons": ".lem/lessons.md",
    "worktrees": ".lem/worktrees",
    "rules": ".claude/rules",
    "review": ".revmux",
    "backlog": "docs/backlog",
}
# The paths of [paths], which a team may name for itself (the owner, 2026-11-18: "all 3
# should be configurable: rulings location, plans location, plan file names format,
# rulings file names format"): the plans folder, and the rulings file, one list with a
# bullet for each ruling (the owner, 2026-11-22: "One list for every project"). The name
# of a plan's file in its folder is `plan_file`.
PATHS = {"plans": "docs/plans", "rulings": "docs/rulings.md"}
# what the settings say the rulings file is, in each refusal of a value that is none
RULINGS_FORM = (
    "paths.rulings names the list file of the owner's rulings, a markdown file with "
    'one bullet for each, as rulings = "docs/rulings.md"'
)
# Who merges a proposed task: "agent", the merge agent, which reads each one and merges
# only a green request that is not careful, and calls the owner for every other one; or
# "owner", who merges each one after the same read. The merge agent by default (the
# owner, 2026-11-20: P6, "merge right away or call me to read his summary
# and reasoning").
LAND = ("agent", "owner")
LAND_DEFAULT = "agent"
# How a task's branch reaches the base branch: its own commits, or one commit for the
# whole branch. One commit unless the settings say otherwise (the owner, 2026-11-18: "my
# opionated default is "squash"").
HISTORY = ("keep", "squash")
HISTORY_DEFAULT = "squash"
# A task ends as a pull request on GitHub, the one way Lem lands (the owner's GitHub
# notes, 2026-11-20: "we can assume that we fully use Github"); `init` refuses an
# origin elsewhere.
GITHUB = re.compile(r"(https://|ssh://git@|git@)github\.com[:/]")
# the agents that can sit in the reviewer's pane
REVIEWERS = ("claude", "codex")
# A seat is one string, `agent/model:effort` (the owner, 2026-11-17: "I personally
# prefer `codex/gpt-6.1-sol:high`"; and 2026-11-18, of the models `init` writes: "Use
# latest `codex/gpt-6.2-sol:high` and `codex/gpt-6.2-astra:high` (released yesterday)").
# A model and an effort are not checked against a list: their names change with each
# release of an agent's command, and that command refuses a wrong one loudly when it
# starts. The three seats of WHOLE_SEATS are written whole (the owner, 2026-11-18: "I
# think it should be explicitly `agent/model:effort` in all 3; not simply "claude" or
# "codex""); a part left out of the merge agent's or a task session's seat is the
# agent's own default, and Lem passes nothing for it; a seat nobody names is Lem's own
# (DEFAULT_SEATS), written whole.
SEAT_FORM = "agent/model:effort"
WHOLE_SEATS = ("reviewer", "planner", "experts")
# The defender's seat: the agent Lem starts in the companion of a plan talk, which
# defends the plan against the reviewer. Only Claude Code, because the harness was
# checked in no other agent.
PLANNERS = ("claude",)
PLANNER = "claude/opus:high"
# The reviewer's seat that `init` writes for each agent: Codex when the machine has it,
# since two model families disagree more usefully than one family twice, and
# Claude otherwise.
REVIEWER_SEATS = {"codex": "codex/gpt-6.2-sol:high", "claude": "claude/opus:high"}
# The reviewer's seat when no file names one: Claude, which is where Lem runs, so that a
# repository that names none has a reviewer on every machine (the owner, 2026-11-23, in
# the ask of the task seat-defaults-and-fallback: "`claude/opus:high` is used to
# review plans").
REVIEWER = "claude/opus:high"
# The experts, the last level of the ladder of a decision in doubt: one or two seats,
# each named by its place, `fable` for the first seat and `astra` for the second,
# whatever model sits there, so that a record (`advisers` of
# `decisions.py log --by experts`) says one expert or two. The default is the newest
# Fable of Anthropic as a Claude Code subagent and the newest Astra of OpenAI through
# Codex, each at high effort. An expert answers only where its agent is on the machine
# (`here`): without Codex, one expert answers alone (the owner, 2026-11-18, of a second
# Claude model in its place: "Sound pointless and should be degraded to a single
# expert then").
EXPERTS = ("claude/fable:high", "codex/gpt-6.2-astra:high")
EXPERT_PLACES = ("fable", "astra")
# seat -> (the agents that may sit in it, why only those, an example of the line)
SEATS = {
    "reviewer": (
        REVIEWERS,
        "the agents that can sit in the reviewer's pane",
        REVIEWER_SEATS["codex"],
    ),
    "planner": (PLANNERS, "the harness was checked in Claude Code only", PLANNER),
    "merger": (
        REVIEWERS,
        "the agents the harness starts a merge agent with, read-only",
        "claude:high",
    ),
    # A task's own session is a top-level agent that `lem session open` starts in
    # agterm: Claude Code only, since the launch line, the two hooks and the compaction
    # were checked there only.
    "session": (
        ("claude",),
        "a task's session runs Claude Code only for now",
        "claude:high",
    ),
}
# The merge agent's and a task session's seat when no file names one (the owner,
# 2026-11-22: "`seats.merger`, `seats.session` should default to `claude/opus:high`").
SEAT_DEFAULT = "claude/opus:high"
# Lem's own seat of each of SEATS, the last of its four places (`seat_of`): this
# machine's own file for the repository, the team's file, the developer's file for all
# his repositories (the home folder's `settings.toml`), then this.
DEFAULT_SEATS = {
    "reviewer": REVIEWER,
    "planner": PLANNER,
    "merger": SEAT_DEFAULT,
    "session": SEAT_DEFAULT,
}
# The seat that stands in for the reviewer, the planner or the merge agent when its
# agent gives an error, from the same four places; `false` in one turns the fallback
# off. On unless a file says otherwise (the owner, 2026-11-23: "and keep fallback: on
# (default)"; of the key: "y, one key").
FALLBACK = "claude/opus:high"
# Where a value came from when no file names it: a seat, an expert, the fallback,
# `naps.on`, `state.keep_days`.
DEFAULT_FROM = "Lem's default"
# What `seat` gives as `from` for a seat in which the fallback stands in for the
# task (`seat-failed`).
STAND_IN = "stand-in"
# The events of a seat whose agent gave an error, which only `seat-failed` and
# `seat-again` write: the fallback that stands in (`seat=SEAT failed=LINE took=FALLBACK
# error=KIND`), the block (`seat=SEAT failed=LINE error=KIND`), and the owner's go on
# (`seat=SEAT`), after which the seat the settings name opens again. A stand-in holds
# for its seat until the task ends or that go on.
SEAT_EVENTS = ("seat.stand-in", "seat.blocked", "seat.again")
# the fixed line of a block that a seat's error wrote, which `state` takes in this
# form only
FAILED_LINE = re.compile(
    re.escape(lem_state.FAILED_SEAT)
    + r"(?P<seat>"
    + "|".join(lem_state.SEAT_NAMES)
    + r")"
)
# the first line of the owner's go on over such a block
GO_ON = "the owner's go on: "
# A plan's file name: its default, and its tokens; `lem_plans` builds and finds
# the name.
PLAN_FILE = lem_plans.PLAN_FILE
PLAN_TOKENS = lem_plans.TOKENS
# a task's slug: plain words joined by hyphens, e.g. report-dates-stay-whole
SLUG = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
# What a task's newest state block may say, and who acts next:
#   queued    the ask is written and no lead runs yet: its `after:` line names the task it waits for,
#             whose result it needs, or after which the owner's words put it. Three of its lines have a
#             fixed form, which `state` checks and the task's first line reads (`opening_line_facts`):
#             `the owner's order: "HIS WORDS"`, `then: PATH` and `the one open task that fits his words`
#   building  a lead plans or builds
#   planned   the plan is committed and nothing builds it: it needs its talk, or a builder after the talk, or the owner reads it
#   held      it waits for the owner: the criteria, one more fact, a step of his, the task his order names
#             (`the order waits for the owner`, ORDER_WAIT), or a breaker's document (`breaker N waits for
#             the owner`); no choice of the build waits for him, the ladder decides it
#   blocked   the task stopped on something its session could not settle: the base is red, a builder ended two times with no report,
#             or a seat's agent gave an error and no fallback could stand in (`seat-failed`, the line `the seat that failed: SEAT`)
#   ready     the report is written and the branch waits for its checks
#   landing   the checks and the read run on it, or a builder repairs what they or the base showed
#   open      it is proposed: its pull request is open, and it waits for the merge agent's read and the merge
#   landed    it is on the base branch
#   dropped   nobody will build it
#   answered  it ended with a report and nothing to merge: a question answered, or a bug that is none
#   parked    put aside on the owner's word (`/lem park`): its worktree, branch and files stay, nothing
#             waits for him, and `resume` brings back the block it put aside
STATES = (
    "queued",
    "building",
    "planned",
    "held",
    "blocked",
    "ready",
    "landing",
    "open",
    "landed",
    "dropped",
    "answered",
    "parked",
)
# The states a task does not leave: its folder stays under its slug, whole until `prune`
# finds nothing of the task for `state.keep_days` days and leaves its small record only,
# and nothing of it waits.
ENDED = ("landed", "dropped", "answered")
# The state of a task the owner put aside, and the states it is put aside from: no lead
# runs in them. A task whose lead builds is parked after the lead stops, and one with
# its landing is dropped or merged.
PARKED = "parked"
PARKABLE = ("queued", "held", "blocked", "planned")
# The states of a task that is with its landing: the checks run on it, or it
# is proposed.
WITH_LANDING = ("landing", "open")
# The states only a lead, or the start or the queue of a task, writes. None comes over a
# task with its landing: there it is a lead that woke late. `ready` does with
# `--start-over`, which only the way out that land.py names gives: a landing that cannot
# go on, or whose record is broken, starts over. `held` is not here: Lem writes it over
# `landing` when the checks find that a task on the fast track needs the standard track,
# and the interview of that path starts with it (`stages/new.md`, "The fast track").
LEADS_WRITE = ("queued", "building", "planned", "ready")
# The type of a request, which Lem takes from the request's words alone
# (`stages/new.md`, "Open the task"): a Conventional Commits type, and `question` for a
# task that ends with an answer and commits nothing. A state line
# `type: TYPE, because WHY` says it; no code matches a request's words against them. The
# track of a request (the fast track or the standard track) is no type: a task on the
# fast track has the state line `small change: one builder`.
TYPES = ("feat", "fix", "docs", "refactor", "perf", "test", "chore", "question")
TYPE_LINE = re.compile(r"type:\s*(?P<type>[^,\s]+)\s*(?:,\s*because\s+(?P<why>.+))?")
# What the investigation of a fix or of a question found, as `log investigation` takes
# it: the call that sets the task's next path (`stages/investigate.md`). A fix goes on
# by the fast track (`small`) or the standard track (`full`), or it is no bug; two of
# the calls end the task with its report, as `answered`.

CALLS = {
    "fix": ("small", "full", "not-a-bug", "not-reproduced"),
    "question": ("answer",),
}
ANSWERING = ("not-a-bug", "answer")
# The states in which the task loads the machine: a lead builds, or the checks run and a
# builder may repair a conflict or a red check.
RUNNING = ("building", "landing")
# The lock of the tests that two tasks cannot run at the same time (`serial`,
# `checks.serial`), in the state folder. Not the landing's `landing.lock`: a builder
# takes this one too, while another task holds the landing line.
SERIAL_LOCK = "serial.lock"
# the lock of one task's state.md, in its task directory (`cmd_state`)
STATE_LOCK = "state.lock"
# The first line of a state block: the time in UTC, the status, one line of text.
STATE_LINE = re.compile(
    r"(?P<since>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z) (?P<status>[a-z]+): (?P<text>.+)"
)
TABLES: dict[str, tuple[str, ...]] = {
    "paths": ("plans", "plan_file", "rulings"),
    "branch": ("base", "land", "history", "protected"),
    "checks": ("commands", "setup", "serial"),
    "flow": ("topics",),
    "seats": ("reviewer", "planner", "merger", "session", "experts", "fallback"),
    "tracker": ("kind",),
    "naps": ("on",),
    "state": ("keep_days",),
    # the question page's defaults, which only that page reads and checks (`lem-ask`)
    "ask": ("style", "size", "review", "browser", "status"),
}
# The trackers Lem has a skill for, `lem-KIND`. The rest is the tracker skill's read,
# not a setting: for Linear the team is in the ticket's id, the server is the one
# connected in the agent, and the status a ticket gets is the team's status of the type
# it needs (the lem-linear skill); for GitHub the repository is origin's (the
# lem-github skill).
TRACKERS = ("linear", "github")
# a Linear ticket's id as the tracker writes it, e.g. MBZ-12
TICKET = re.compile(r"[A-Za-z][A-Za-z0-9]*-[0-9]+")
# a GitHub issue's number as the owner may give it, 42, #42 or #042; kept as #42, the
# number as an integer, so that one issue has one saved form
ISSUE = re.compile(r"#?([0-9]+)")
# the repository of a GitHub issue, OWNER/REPO, as the issue's address gives it
ISSUE_REPO = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?/[A-Za-z0-9._-]+")
# the login of a GitHub account, which `ticket-step SLUG assigned --login LOGIN` keeps
LOGIN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?")
# What Lem did to a task's ticket, each written down after the tracker took it (`assigned` before),
# so that a step is never done twice and a session that was cut off can see what is still owed:
#   started    the ticket got the status for work that started; for an issue, the start ran
#   assigned   Lem set out to add the person signed in to `gh` as the issue's assignee: written
#              before the add, with the login (`assigned LOGIN`), since a removal reads the
#              assignees first and a record lost after the add would leave his name on the issue
#   unassigned Lem removed that assignee again, or the add failed
#   commented  the landing was commented on the ticket
#   landed     the ticket got the status for work that landed; an issue is closed as completed
#   dropped    the ticket got the comment that its task was dropped
#   answered   the ticket got the comment with its task's answer: not a bug, or the answer to a question
TICKET_STEPS = (
    "started",
    "assigned",
    "unassigned",
    "commented",
    "landed",
    "dropped",
    "answered",
)
# The steps a task's end writes (`ticket_owed`), which pass the release rule as the end
# itself does
TICKET_ENDS = ("unassigned", "commented", "landed", "dropped", "answered")
# The ended states that give a task's ticket back, once the task owes it nothing
# (`ticket_owed`): a new task may take it then. A landed task keeps it.
RETURNED = ("dropped", "answered")
# The tracker's step that pays what a dropped or answered task still owes its ticket.
PAID_BY = {"dropped": "drop", "answered": "answer"}
# The folder of the state folder that holds a mark for each ticket a task holds: a file
# named by the ticket's id without its `#` (`42`, `MBZ-12`) that holds the slug. A link
# of a finished file claims the name, as `ask.txt` is written, so of two opens of one
# ticket at one moment one takes it. `prune` leaves it alone.
TICKET_MARKS = "tickets"
# How many days the state folder keeps what Lem no longer needs (`prune`,
# `[state] keep_days`): the owner, 2026-11-21: "I think that `.lem/state` should not
# grow to gigabytes. Maybe KEEP_DAYS should be configurable and one would configure it
# to let's say 7 days instead of 30 to keep disk usage in control", a key of the
# project's settings and not of machine.toml ("Why machines? I thought that those logs
# are per project and stored in project .lem dir"). One machine's own file may set its
# own number, which wins there, lower or higher (the same day: "In that case one
# developer with a smaller disk free space will suffer while for another dev of that
# project it will be fine. I think [this repository's local file] should be
# acceptable"). 30 is the number of the two guesses it replaces, the experts' folders'
# and the naps'.
KEEP_DAYS = 30
# The settings' key of the number, as the messages and the help name it.
KEEP_KEY = "state.keep_days"
# The naps (`may-nap`). A guess, not a measurement: the owner's own nap routine runs
# three times a day.
NAPS_GAP_HOURS = 6
# How long a nap that wrote no `waking.md` counts as running. A guess: the owner's own
# routine leaves a nap "about twenty minutes", and an hour is three of those.
ASLEEP_MINUTES = 60
# a nap's folder: the clock's time when it started, then a few words of the dream
NAP_NAME = re.compile(r"(?P<time>\d{4}-\d{2}-\d{2}-\d{4})(?:-.+)?")
NAP_TIME = "%Y-%m-%d-%H%M"
ASLEEP = ".asleep"

TEMPLATE = """\
# What Lem reads in this repository: the team's settings, in git. `lem project show` prints them
# resolved, with the file each seat came from. Your own settings for this repository alone go in
# .lem/settings.local.toml, which git does not track and which wins here; yours for every
# repository go in ~/.config/lem/settings.toml.

[paths]
# The folder of the plans, relative to the root of the checkout. Lem's own files are in .lem/, the
# rules for the code in .claude/rules, the review tool's folder is .revmux and the backlog is
# docs/backlog: each has that one place, and no line here.
plans = "{plans}"
# The name of a plan's file in the plans folder: YYYY, MM and DD are the day the plan was
# written, <slug> is the task's.
plan_file = "{plan_file}"
# The rulings file: the list of your product decisions, one bullet for each, which outlive a task.
# A bullet is `- **The rule in one sentence.** (YYYY-MM-DD)` under the `##` heading of its group.
# The file comes with the first ruling.
rulings = "{rulings}"

[branch]
# The branch a task starts from and lands on.
base = "{base}"
# Who merges a task's pull request. A fresh merge agent reads each proposed task and writes its
# review either way. "agent": it merges a green request that is not careful, and calls the owner
# for every other one. "owner": it never merges, and the owner merges each one after its review.
# Lem pushes each task's branch and opens its pull request on GitHub without asking: these settings
# are the owner's word for exactly that.
land = "agent"
# What lands: "squash" lands one commit for the whole task, "keep" lands the branch's own commits.
history = "squash"
# Branches nothing lands on and nothing is pushed to through this skill, whoever asks.
protected = []

[checks]
# During the build, each builder runs only the tests of its own change. Before the pull request,
# Lem runs these commands one time, at the root of the task's worktree: the whole suite. A linter
# and a type checker belong in a git hook, which runs at each commit; a test suite belongs here,
# since a hook must be fast and "green" must be what Lem saw.
commands = []
# What a new worktree needs before its tests can run: install the packages, copy an environment
# file ("uv sync", "npm ci"). Lem runs these one time in each worktree it makes for a task, and in
# the two worktrees of the check that each criterion's tests fail on the base commit. Leave it
# empty when the tests run as they are.
setup = []
# The tests that two tasks cannot run at the same time: an end-to-end suite that uses fixed ports,
# one database or a browser. They run after `commands`, one at a time for all tasks, under one lock
# for the repository, and a builder runs a test of such a suite through `lem project serial`. Keep
# them out of `commands`.
serial = []

[flow]
# What must never go wrong in this project, each as one sentence in the owner's words: "a
# customer is charged the wrong amount", "data that cannot be rebuilt is lost", "someone signs in
# as another user". No code matches these and no list of paths stands in for them: Lem reads the
# ask against each, the lead its plan, and the agent that reviews the diff the change itself, and
# a change in reach of one takes the careful flow: its plan is talked through with the reviewer
# before any code, the landing gives it the project's full review set, and a person merges it.
# This table is read from the main checkout, so a branch cannot lift what guards it.
topics = []

[seats]
# Who sits where, each as "agent/model:effort". The reviewer, the planner, each expert and the
# fallback are written whole: Lem refuses "codex" or "codex/gpt-6.2-sol" there. A part left out of
# the merger or the session ("claude", "claude:high") takes that agent's own default. Each seat comes
# from the first file that names it: .lem/settings.local.toml, this file, the developer's
# ~/.config/lem/settings.toml for all his repositories, then Lem's own, "claude/opus:high" for each
# seat but the experts.
# The reviewer, on the agent "claude" or "codex". Lem's builders build; this one talks the plan of
# a careful or large task through with its defender, in the other pane of the pair the task's lead
# opens for the talk. The same family twice is allowed.
reviewer = "{reviewer}"
# The defender of a careful or large plan in its talk with the reviewer, in the pair the task's
# lead opens under the task's session for the talk and closes after it. Only the agent "claude" for
# now.
planner = "{planner}"
# The merge agent, which reads each proposed task and merges it or calls the owner: "claude" or
# "codex", read-only.
# merger = "agent/model:effort"
# The agent of each task's own session in agterm: "claude" only for now.
# session = "agent/model:effort"
# The experts, the last level of the ladder of a decision in doubt, at the same moment and read-only: two
# model families, so that their agreement is worth more than two of one. Where the machine has one
# of their agents, that expert answers alone.
experts = [{experts}]
# The seat that stands in for the reviewer, the planner or the merge agent when its agent gives an
# error (it is not on the machine, or says it has no login, no tokens or no such model), so that the
# task goes on and the pull request says so. false turns it off: the task then waits for the owner.
# Left out, it is "claude/opus:high".
# fallback = "agent/model:effort"

# The tracker a task's ask may come from: "linear" or "github". Leave it out when the project has
# none. Lem reads a ticket into a task, marks it when its work starts, and comments the landing.
# For Linear the team is in the ticket's id (ABC-12), and each status is the team's own of its
# type. For GitHub the issues are origin's, the id is the issue's number (#42), and Lem adds an
# assignee at the start and closes the issue at the landing.
# [tracker]
# kind = "linear"
"""
# The state's table and the naps' table, the last of the file.
TEMPLATE += f"""
[state]
# How many days Lem keeps what it no longer needs in .lem/state/, the folder git never sees: every
# file of a task that ended and that nothing happened in for that many days but its small record
# (its state, its request, its pull request, and its ticket's and its resume's files), and a
# question to the experts, a persona panel's folder, a nap and a copy of the cast that nobody wrote
# or read in that time. The event log stays. The board server removes them, and
# `lem project prune --dry-run --days 7` shows what 7 would remove. The default, {KEEP_DAYS}, is the
# owner's word of 2026-11-21, and the two constants it replaces, which were guesses. One person with
# less free disk, or more, sets a number for their machine alone with `keep_days` under [state] in
# .lem/settings.local.toml, which wins there.
keep_days = {KEEP_DAYS}

[naps]
# Now and then, when a task has ended or Lem waits for the owner, Lem takes a nap: a fresh agent
# reads the recent tasks, dreams, and writes the dream down in .lem/state/naps/, which the retro
# reads. It costs an agent's session of some minutes, a few times a day while Lem works, and
# nobody has shown that it helps. {NAPS_GAP_HOURS} hours pass between two naps: a guess, from the
# owner's own nap routine. A nap's folder is kept for state.keep_days.
on = false
"""


class SettingsError(Exception):
    pass


def repo_root(start: Path) -> Path:
    found = subprocess.run(
        ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if found.returncode != 0:
        raise SettingsError(f"{start} is not inside a git checkout")
    return Path(found.stdout.strip())


def nearest(key: str, valid: tuple[str, ...]) -> str:
    close = difflib.get_close_matches(key, valid, n=1)
    listed = f"valid: {', '.join(valid)}"
    return f"; did you mean {close[0]!r}? {listed}" if close else f"; {listed}"


def strings(value: object, where: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise SettingsError(f"{where} must be a list of strings")
    return value


def commands(value: object, where: str) -> list[str]:
    """A list of shell commands. An empty one runs nothing and exits 0, so checks of it
    are green."""
    found = strings(value, where)
    if any(not item.strip() for item in found):
        raise SettingsError(
            f"{where} holds an empty command, which passes without running anything; "
            "take it out of the list"
        )
    return found


def inside(root: Path, relative: str, where: str) -> Path:
    if Path(relative).is_absolute():
        raise SettingsError(
            f"{where} = {relative!r} must be relative to the root of the checkout"
        )
    resolved = (root / relative).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise SettingsError(f"{where} = {relative!r} leaves the repository")
    if resolved == root.resolve():
        # every path names a folder or a file of its own: the root would read the whole
        # checkout as backlog items or rules, and a worktrees folder there ignores every
        # file of the project
        raise SettingsError(
            f"{where} = {relative!r} names the root of the checkout; name a folder or "
            "a file inside it, or leave the line out for the default"
        )
    return resolved


def main_checkout(root: Path) -> Path:
    """The checkout every worktree hangs off: the first entry git lists. A file git does
    not track lives only there."""
    # lem_state's search, which asks git once a command for each folder
    try:
        return lem_state.main_checkout(root)
    except lem_state.StateError:
        return root


def text_of(file: Path) -> str:
    """A text file Lem reads, as UTF-8. A file in another encoding is refused by name:
    read as the locale's, a settings file would mean something else on
    another machine."""
    try:
        return file.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise SettingsError(
            f"{file} is not UTF-8 text (byte {error.start} does not read); "
            "save it as UTF-8"
        ) from error


def unreadable_argument(argv: list[str]) -> str | None:
    """The first argument that is not UTF-8 text, as the message that names it; None
    when all are. Such an argument would stop the write of the file it goes into
    half way."""
    for arg in argv:
        try:
            arg.encode("utf-8")
        except UnicodeEncodeError:
            return (
                f"the argument {os.fsencode(arg)!r} is not UTF-8 text; give it in UTF-8"
            )
    return None


# a string as TOML writes it, for the template and the refusals; the line edit of a
# settings file writes the same
toml_string = lem_state.toml_string


def read_settings(file: Path, name: Path, place: str) -> dict:
    """One settings file as a dict, with every table and key it may not hold refused.
    PLACE is the file's word in `lem_state.TABLE_PLACES`: `home`, `team` or `local`."""
    if not file.is_file():
        return {}
    return settings_of(text_of(file), name, place)


def committed_settings(main: Path) -> dict | None:
    """The tracked settings as the base branch's newest commit holds them: the text, the
    branch and the commit; None when no commit of the base holds the file yet (an
    onboarding, whose settings are only in the working tree or on its own branch). The
    base is the branch the file names, so the first file read is the remote's default
    branch's, then the one of the branch the main checkout's own copy names; a file that
    names another base is read on that branch."""

    def shown(branch: str) -> str | None:
        ran = subprocess.run(
            [
                "git",
                "-C",
                str(main),
                "show",
                f"refs/heads/{branch}:{SETTINGS.as_posix()}",
            ],
            capture_output=True,
            check=False,
        )
        if ran.returncode != 0:
            return None
        try:
            return ran.stdout.decode("utf-8")
        except UnicodeDecodeError as error:
            raise SettingsError(
                f"{branch}:{SETTINGS} is not UTF-8 text (byte {error.start} does not "
                "read); save it as UTF-8"
            ) from error

    def names(text: str) -> str | None:
        try:
            base = tomllib.loads(text).get("branch", {}).get("base")
        except (tomllib.TOMLDecodeError, AttributeError):
            return None
        return base if isinstance(base, str) and base.strip() else None

    working = main / SETTINGS
    try:
        own = names(working.read_text(encoding="utf-8")) if working.is_file() else None
    except UnicodeDecodeError:
        own = None
    for start in dict.fromkeys(
        branch for branch in (default_branch(main), own) if branch
    ):
        text = shown(start)
        if text is None:
            continue
        named = names(text) or start
        base = start
        if named != start:
            other = shown(named)
            if other is None:
                raise SettingsError(
                    f"{start}:{SETTINGS} names {named!r} as branch.base, and {named} "
                    f"holds no {SETTINGS}: the base branch's own "
                    "file is the one Lem reads"
                )
            base, text = named, other
        commit = subprocess.run(
            ["git", "-C", str(main), "rev-parse", f"refs/heads/{base}"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
        return {"text": text, "branch": base, "commit": commit}
    return None


# Whether this run said once already that the main checkout's copy of the settings is
# not the one Lem reads.
DIFFERS_SAID: list[bool] = []


def settings_of(text: str, name: Path | str, place: str) -> dict:
    """The text of one settings file as a dict, checked as `read_settings` says: a table
    Lem does not know, a table whose place is another file (named in the refusal), and a
    key the table does not have are refused."""
    try:
        raw = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise SettingsError(f"{name}: {error}") from error
    for table, body in raw.items():
        if table not in lem_state.TABLE_PLACES:
            raise SettingsError(
                f"{name}: unknown table "
                f"[{table}]{nearest(table, tuple(lem_state.TABLE_PLACES))}"
            )
        wrong = lem_state.misplaced(table, place)
        if wrong:
            raise SettingsError(f"{name}: {wrong}")
        if not isinstance(body, dict):
            raise SettingsError(f"{name}: [{table}] must be a table")
        for key in body:
            if key not in TABLES[table]:
                raise SettingsError(
                    f"{name}: unknown key {table}.{key}{nearest(key, TABLES[table])}"
                )
    return raw


def flow_of(raw: dict, name: Path) -> dict:
    """The `[flow]` table of one settings file, checked."""
    return {"topics": strings(raw.get("flow", {}).get("topics", []), "flow.topics")}


def parse_seat(
    text: object,
    where: str,
    agents: tuple[str, ...],
    why: str,
    example: str,
    *,
    whole: bool = False,
) -> dict:
    """One seat, `agent/model:effort`, as its parts: the agent, the model and the
    effort, each None when the line leaves it out, and the line as written. The effort
    is what follows the one `:` after the model, or after the agent when the line names
    no model; a second `:` is refused. A `whole` seat (WHOLE_SEATS) that leaves out its
    model or its effort is refused."""
    if whole:
        form = f'one string, "{SEAT_FORM}", written whole, as "{example}"'
    else:
        form = (
            f'one string, "{SEAT_FORM}", as "{example}"; the effort, or the model and '
            "the effort, may be left out"
        )
    if not isinstance(text, str):
        raise SettingsError(f"{where} = {text!r} must be {form}")
    if not text.strip():
        raise SettingsError(
            f"{where} is empty: it is {form}. Leave the line out for Lem's default"
        )
    if any(char.isspace() for char in text):
        raise SettingsError(
            f"{where} = {text!r} holds a space: it is {form}, with no space in it"
        )
    if text.count(":") > 1:
        raise SettingsError(
            f"{where} = {text!r} holds {text.count(':')} `:`, and a seat has one at "
            f"most, before the effort: it is {form}"
        )
    agent, slash, rest = text.partition("/")
    if slash:
        model, colon, effort = rest.partition(":")
    else:
        agent, colon, effort = agent.partition(":")
        model = None
    if not agent:
        raise SettingsError(
            f"{where} = {text!r} names no agent before the `/`: it is {form}"
        )
    if whole:
        if agent not in agents:
            raise SettingsError(
                f"{where} = {text!r}: the agent {agent!r} must "
                f"be {' or '.join(agents)}: {why}"
            )
        missing = [
            part for part, value in (("model", model), ("effort", effort)) if not value
        ]
        if missing:
            raise SettingsError(
                f"{where} = {text!r} names no {' and no '.join(missing)}: it is {form}"
            )
    if slash and not model:
        raise SettingsError(
            f"{where} = {text!r} names no model after the `/`: leave the `/` out with "
            f'the model, as "{agent}", or write {form}'
        )
    if colon and not effort:
        raise SettingsError(
            f"{where} = {text!r} names no effort after the `:`: leave the `:` out with "
            f"the effort, or write {form}"
        )
    if agent not in agents:
        raise SettingsError(
            f"{where} = {text!r}: the agent {agent!r} must "
            f"be {' or '.join(agents)}: {why}"
        )
    return {
        "agent": agent,
        "model": model or None,
        "effort": effort or None,
        "seat": text,
    }


def seat(raw: dict, name: Path, which: str = "reviewer") -> dict | None:
    """The seat (`SEATS`) one file names, checked; None when the file names none."""
    agents, why, example = SEATS[which]
    given = raw.get("seats", {}).get(which)
    if given is None:
        return None
    return parse_seat(
        given,
        f"{name}: seats.{which}",
        agents,
        why,
        example,
        whole=which in WHOLE_SEATS,
    )


def home_name() -> str:
    """The home folder's `settings.toml`, as a message and `from` name it."""
    return lem_state.shown(lem_state.home_settings_file())


def places_of(local: dict, raw: dict, home: dict) -> list[tuple[dict, Path]]:
    """The three files a seat may come from, first to last, each as its tables and the
    name `from` gives it: this machine's own file for the repository, the team's file,
    and the developer's file for all his repositories, the home folder's
    `settings.toml`."""
    return [(local, LOCAL), (raw, SETTINGS), (home, Path(home_name()))]


# A value one of the places gives (`first_of`).
Given = TypeVar("Given")


def first_of(found: Sequence[tuple[Given | None, Path]]) -> tuple[Given | None, str]:
    """The first value a place gives, with that place's name as `from`; else None, from
    Lem's default."""
    for value, name in found:
        if value is not None:
            return value, str(name)
    return None, DEFAULT_FROM


def seat_of(which: str, local: dict, raw: dict, home: dict) -> dict:
    """One seat of SEATS with `from`, the place it came from: the first of the three
    files that names it (`places_of`), else Lem's own (DEFAULT_SEATS). Each file's seat
    is checked, the ones after the first too, so that a wrong line is refused wherever
    it is."""
    found = [
        (seat(tables, name, which), name)
        for tables, name in places_of(local, raw, home)
    ]
    chosen, place = first_of(found)
    if chosen is None:
        # Lem's own default names the seat, so it gives one
        chosen = cast(
            "dict",
            seat({"seats": {which: DEFAULT_SEATS[which]}}, Path(DEFAULT_FROM), which),
        )
    return {**chosen, "from": place}


def experts_from(local: dict, raw: dict, home: dict) -> list[dict]:
    """The experts with `from` on each, from the first of the three files that names
    them, else Lem's (EXPERTS). A file's list replaces the one after it whole."""
    found = [
        (experts_of(tables, name), name) for tables, name in places_of(local, raw, home)
    ]
    chosen, place = first_of(found)
    if chosen is None:
        # Lem's own default names the experts, so it gives them
        chosen = cast(
            "list[dict]",
            experts_of({"seats": {"experts": list(EXPERTS)}}, Path(DEFAULT_FROM)),
        )
    return [{**expert, "from": place} for expert in chosen]


def fallback_of(raw: dict, name: Path) -> dict | None:
    """The fallback one file names, checked: a whole seat, which turns it on, or
    `false`, which turns it off; None when the file names none."""
    given = raw.get("seats", {}).get("fallback")
    if given is None:
        return None
    if given is False:
        return {"seat": False}
    where = f"{name}: seats.fallback"
    form = (
        f'a whole seat, "{SEAT_FORM}", as "{FALLBACK}", which stands in for the '
        "reviewer, the planner or the merger when its agent gives an error, or false, "
        "which turns the fallback off"
    )
    if given is True:
        raise SettingsError(
            f"{where} = true is no seat: it is {form}. Leave the line out "
            f'for Lem\'s, "{FALLBACK}"'
        )
    if isinstance(given, str) and not given.strip():
        raise SettingsError(
            f"{where} is empty: it is {form}. Leave the line out "
            f'for Lem\'s, "{FALLBACK}"'
        )
    return parse_seat(
        given,
        where,
        REVIEWERS,
        "the agents Lem can start in a seat's place",
        FALLBACK,
        whole=True,
    )


def fallback_from(local: dict, raw: dict, home: dict) -> dict:
    """The fallback with `from`, from the first of the three files that names it, else
    Lem's (FALLBACK): `{"seat": false, "from": ...}` when it is off."""
    found = [
        (fallback_of(tables, name), name)
        for tables, name in places_of(local, raw, home)
    ]
    chosen, place = first_of(found)
    if chosen is None:
        # Lem's own default names the fallback, so it gives one
        chosen = cast(
            "dict",
            fallback_of({"seats": {"fallback": FALLBACK}}, Path(DEFAULT_FROM)),
        )
    return {**chosen, "from": place}


def agent_here(agent: str) -> bool:
    """Whether an expert of this agent can answer on this machine: Claude Code is where
    Lem runs and starts its expert as a subagent; Codex needs its command."""
    return agent == "claude" or shutil.which(agent) is not None


def experts_of(raw: dict, name: Path) -> list[dict] | None:
    """The one or two experts one file names, checked, each with its place in a record
    and whether its agent is on this machine (`here`); None when the file names none."""
    given = raw.get("seats", {}).get("experts")
    if given is None:
        return None
    if not isinstance(given, list) or not 1 <= len(given) <= len(EXPERT_PLACES):
        raise SettingsError(
            f"{name}: seats.experts = {given!r} must be a list of one or two seats, "
            f'"{SEAT_FORM}" each, as experts = '
            f"[{', '.join(toml_string(one) for one in EXPERTS)}]: "
            "the ladder asks two experts at most",
        )
    found = [
        {
            **parse_seat(
                one,
                f"{name}: seats.experts[{number}]",
                REVIEWERS,
                "the agents the harness starts an expert with",
                EXPERTS[number],
                whole=True,
            ),
            "place": place,
        }
        for number, (one, place) in enumerate(zip(given, EXPERT_PLACES, strict=False))
    ]
    return [{**expert, "here": agent_here(expert["agent"])} for expert in found]


def file_pattern_of(raw: dict, name: Path) -> str:
    """The pattern of a plan's file name, checked: the tokens it may hold, `<slug>`
    once, a name and not a path, and a markdown file."""
    key, default, folder, what = "plan_file", PLAN_FILE, "plans", "plan"
    pattern = raw.get("paths", {}).get(key, default)
    where = f"{name}: paths.{key}"
    if not isinstance(pattern, str) or not pattern.strip():
        raise SettingsError(
            f"{where} = {pattern!r} must be a file name in quotes, "
            f'as {key} = "{default}"'
        )
    if pattern.count("<slug>") != 1:
        raise SettingsError(
            f"{where} = {pattern!r} must hold <slug> once, where the {what}'s slug "
            f'goes, as {key} = "{default}": without it no {what} '
            "can be told from another"
        )
    if "/" in pattern or "\\" in pattern:
        raise SettingsError(
            f"{where} = {pattern!r} is a file name in the {folder} folder, with no "
            f"folder in it; paths.{folder} names the folder"
        )
    if not pattern.endswith(".md"):
        raise SettingsError(
            f"{where} = {pattern!r} must end with .md: a {what} is a markdown file"
        )
    if re.search(r"<(?!slug>)[^>]*>", pattern):
        raise SettingsError(
            f"{where} = {pattern!r} holds a token Lem does not know; "
            "it knows YYYY, MM, DD and <slug>"
        )
    twice = [token for token in PLAN_TOKENS if pattern.count(token) > 1]
    if twice:
        raise SettingsError(
            f"{where} = {pattern!r} holds {twice[0]} twice; each of YYYY, MM, DD and "
            "<slug> stands in it once at most"
        )
    return pattern


def local_naps_off(local: dict) -> bool:
    """Whether this machine's own file says no to the naps: a nap spends this person's
    tokens. It can say nothing else about them."""
    naps = local.get("naps", {})
    for key in naps:
        if key != "on":
            raise SettingsError(
                f"{LOCAL}: naps.{key} is the project's and belongs in {SETTINGS}; "
                "this file may hold only `on = false` under [naps]"
            )
    if "on" not in naps:
        return False
    if naps["on"] is not False:
        raise SettingsError(
            f"{LOCAL}: naps.on = {naps['on']!r} is not for this file. "
            "It may say `on = false`, which keeps Lem from napping by itself on this "
            f"machine; only {SETTINGS}, which everybody reads in git, "
            "switches the naps on",
        )
    return True


def naps_of(raw: dict, name: Path) -> dict:
    """The `[naps]` table of one settings file, checked: its one key, `on`, with `from`,
    the team's file when it names it, else DEFAULT_FROM, as `state_of` gives it."""
    given = raw.get("naps", {}).get("on")
    if given is None:
        return {"on": False, "from": DEFAULT_FROM}
    if not isinstance(given, bool):
        raise SettingsError(f"{name}: naps.on = {given!r} must be true or false")
    return {"on": given, "from": str(SETTINGS)}


def keep_days_of(value: object, where: str, left_out: str = str(KEEP_DAYS)) -> int:
    """A number of days the state folder keeps what Lem no longer needs, checked: a
    whole number, 1 or more. 0 would take all but a task's small record at the first
    look after it ended, while the owner may still read its board. `left_out` is what
    the number is without the line."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise SettingsError(
            f"{where} = {value!r} must be a whole number of days, 1 or more, as "
            f"keep_days = {KEEP_DAYS}; leave the line out for {left_out}"
        )
    return value


def state_of(raw: dict, name: Path) -> dict:
    """The `[state]` table of one settings file, checked: its one key, `keep_days`, with
    `from`, the file that names it, or DEFAULT_FROM when the file names none. `from` is
    the tracked file's name in a task's worktree too, where the number is the base
    branch's (`decide`)."""
    given = raw.get("state", {}).get("keep_days")
    if given is None:
        return {"keep_days": KEEP_DAYS, "from": DEFAULT_FROM}
    return {
        "keep_days": keep_days_of(given, f"{name}: {KEEP_KEY}"),
        "from": str(SETTINGS),
    }


def local_keep_days(local: dict) -> int | None:
    """The number of days this machine's own file sets for itself, checked; None when it
    sets none. It wins over the project's number on this machine, lower or higher: one
    developer's disk is not another's. `[state]` holds no other key (`settings_of`
    refuses one)."""
    given = local.get("state", {}).get("keep_days")
    if given is None:
        return None
    return keep_days_of(given, f"{LOCAL}: {KEEP_KEY}", f"the number of {SETTINGS}")


def load(root: Path) -> dict:
    file = root / SETTINGS
    main = main_checkout(root)
    # The project's settings are the main checkout's working tree while it is on the
    # base branch: the developer's own edit there is his act, and counts at once.
    # Another branch checked out there is no rule for the tasks that run (audit M-F5,
    # 2026-11-17: `gh pr checkout 57` in the main checkout changed `branch.land` and the
    # topics for every task), so then the file is read as the base branch's newest
    # commit has it. Before any commit of the base holds the file (an onboarding), the
    # working tree's is read.
    committed = committed_settings(main)
    if (
        committed
        and subprocess.run(
            ["git", "-C", str(main), "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
        == committed["branch"]
    ):
        committed = None
    base_file = (
        Path(f"{committed['branch']}:{SETTINGS}") if committed else main / SETTINGS
    )

    def base_raw() -> dict:
        if not committed:
            return read_settings(main / SETTINGS, main / SETTINGS, "team")
        try:
            return settings_of(committed["text"], base_file, "team")
        except SettingsError as error:
            # the fix is an edit of the file, and it counts once the base holds it
            raise SettingsError(
                f"Lem reads {SETTINGS} as {committed['branch']} has it, so a fix "
                f"counts once it is committed there. {error}"
            ) from error

    if main.resolve() == root.resolve():
        raw = base_raw()
        here = text_of(file) if file.is_file() else None
        if committed and here != committed["text"] and not DIFFERS_SAID:
            DIFFERS_SAID.append(True)
            print(
                (
                    f"project.py: the main checkout is not on {committed['branch']}, "
                    f"so Lem reads {SETTINGS} as {committed['branch']} has it "
                    f"({committed['commit'][:9]}), not the copy checked out there"
                ),
                file=sys.stderr,
            )
    else:
        # in a task's worktree the file is the branch's copy
        raw = read_settings(file, SETTINGS, "team")
    local = read_settings(main / LOCAL, LOCAL, "local")
    on_base = raw if main.resolve() == root.resolve() else base_raw()
    try:
        home = read_settings(lem_state.home_settings_file(), Path(home_name()), "home")
        # read whole, so that a file that does not read, or a table in it whose place is
        # another file, is refused here too
        machine = lem_state.machine_tables()
        lem_state.checked_table(machine, "corrections")
    except lem_state.StateError as error:
        raise SettingsError(str(error)) from error
    return decide(root, main, raw, local, on_base, committed, home, machine)


def decide(
    root: Path,
    main: Path,
    raw: dict,
    local: dict,
    on_base: dict,
    committed: dict | None,
    home: dict | None = None,
    machine: dict | None = None,
) -> dict:
    """The settings from the tables `load` read: the team's file's (`raw`, the branch's
    copy in a task's worktree), this machine's own file's for the repository (`local`),
    and the base branch's copy (`on_base`, the same table as `raw` in the main
    checkout), with `committed` the commit of the base it came from, or None for the
    working tree; `home`, the tables of the developer's file for all his repositories
    (the home folder's `settings.toml`); and `machine`, the tables of `machine.toml`.
    Every value is checked here; it refuses with a SettingsError."""
    file = root / SETTINGS
    local_file = main / LOCAL
    base_file = (
        Path(f"{committed['branch']}:{SETTINGS}") if committed else main / SETTINGS
    )
    # What must never go wrong, and the owner's wait, are the base branch's: the branch
    # that a rule guards does not get to lift it. The branch's own table is
    # still checked.
    flow = flow_of(raw, SETTINGS)
    if main.resolve() != root.resolve():
        flow = flow_of(on_base, base_file)
    overridden = []

    paths = {}
    for name, default in PATHS.items():
        relative = raw.get("paths", {}).get(name, default)
        if not isinstance(relative, str):
            raise SettingsError(f"{SETTINGS}: paths.{name} must be a string")
        resolved = inside(root, relative, f"paths.{name}")
        if name == "rulings" and not relative.endswith(".md"):
            raise SettingsError(
                f"{SETTINGS}: paths.rulings = {relative!r} is no "
                f"markdown file: {RULINGS_FORM}"
            )
        if name == "rulings" and resolved.is_dir():
            raise SettingsError(
                f"{SETTINGS}: paths.rulings = {relative!r} is a folder: {RULINGS_FORM}"
            )
        paths[name] = {"path": str(resolved), "exists": resolved.exists()}
    # a pattern, not a path: the name of a plan's file in the plans folder
    paths["plan_file"] = {"pattern": file_pattern_of(raw, SETTINGS)}
    # what Lem reads beside the settings, each in its one place: no setting names them
    places = {
        name: {"path": str(root.resolve() / place), "exists": (root / place).exists()}
        for name, place in PLACES.items()
    }

    branch = raw.get("branch", {})
    base = branch.get("base")
    if base is not None and not isinstance(base, str):
        raise SettingsError(f"{SETTINGS}: branch.base must be a string")
    if base is not None and not base.strip():
        raise SettingsError(
            f"{SETTINGS}: branch.base = {base!r} names no branch; write the branch "
            'tasks start from and land on, as base = "main"'
        )
    land = branch.get("land", LAND_DEFAULT)
    if land not in LAND:
        raise SettingsError(
            f"{SETTINGS}: branch.land = {land!r} must be one of {', '.join(LAND)}"
        )

    history = branch.get("history", HISTORY_DEFAULT)
    if history not in HISTORY:
        raise SettingsError(
            f"{SETTINGS}: branch.history = {history!r} must be "
            f"one of {', '.join(HISTORY)}"
        )
    protected = strings(branch.get("protected", []), "branch.protected")
    if base in protected:
        raise SettingsError(
            f"{SETTINGS}: branch.base = {base!r} is in branch.protected, "
            "so no task could land"
        )

    # Each seat is the first of its four places, whole: a model and an effort belong to
    # the agent of the line they are on. `from` names the place, so the seats stay out
    # of `local.overrides`.
    seats: dict = {which: seat_of(which, local, raw, home or {}) for which in SEATS}
    seats["experts"] = experts_from(local, raw, home or {})
    seats["fallback"] = fallback_from(local, raw, home or {})
    # the machine's own switch of the correction queue, which no file of a repository
    # may hold; with no line it is Lem's default, no, and the hook sends nothing
    machine_corrections = (machine or {}).get("corrections", {})
    corrections = (
        {
            "collect": machine_corrections["collect"],
            "from": lem_state.shown(lem_state.machine_file()),
        }
        if "collect" in machine_corrections
        else {"collect": False, "from": DEFAULT_FROM}
    )
    tracker = None
    if "tracker" in raw:
        given = raw["tracker"]
        for key, value in given.items():
            if not isinstance(value, str) or not value.strip():
                raise SettingsError(
                    f"{SETTINGS}: tracker.{key} must be a word in quotes, not {value!r}"
                )
        if "kind" not in given:
            raise SettingsError(
                f"{SETTINGS}: [tracker] needs kind; leave the whole table out when the "
                "project has no tracker"
            )
        if given["kind"] not in TRACKERS:
            raise SettingsError(
                f"{SETTINGS}: tracker.kind = {given['kind']!r} must be "
                f"one of {', '.join(TRACKERS)}"
            )
        tracker = {"kind": given["kind"]}
    # The naps spend the tokens of whoever works on this machine, so their switch is the
    # base branch's too: a task's branch that switches them on has not been agreed
    # to yet.
    naps = naps_of(raw, SETTINGS)
    if main.resolve() != root.resolve():
        naps = naps_of(on_base, base_file)
    if local_naps_off(local):
        if naps["on"]:
            overridden.append("naps.on")
        naps = {"on": False, "from": str(LOCAL)}
    # How long the state folder keeps old files is the base branch's too: a task's
    # branch that lowers it would remove files of other tasks before anybody agreed to
    # it. The branch's own table is still checked. This machine's own file, the main
    # checkout's, may set its own number, which wins here, in a task's worktree too: it
    # removes only this machine's files.
    state = state_of(raw, SETTINGS)
    if main.resolve() != root.resolve():
        state = state_of(on_base, base_file)
    own_days = local_keep_days(local)
    if own_days is not None:
        state = {"keep_days": own_days, "from": str(LOCAL)}
        overridden.append(KEEP_KEY)
    return {
        "root": str(root),
        # the checkout every worktree hangs off; it is `root` unless this ran in a
        # task's worktree
        "main": str(main),
        "settings": str(file) if file.is_file() or committed else None,
        # where the settings were read: the working tree, or the base branch's commit
        # while another branch is checked out
        "settings_from": (
            f"{committed['branch']}@{committed['commit'][:9]}"
            if committed
            else "the working tree"
        )
        if main.resolve() == root.resolve()
        else "this worktree's branch, with [flow], [naps] and [state] from "
        + (
            f"{committed['branch']}@{committed['commit'][:9]}"
            if committed
            else "the main checkout"
        ),
        "paths": paths,
        "places": places,
        "branch": {
            "base": base,
            "land": land,
            "history": history,
            "protected": protected,
        },
        "checks": {
            "commands": commands(
                raw.get("checks", {}).get("commands", []), "checks.commands"
            ),
            "setup": commands(raw.get("checks", {}).get("setup", []), "checks.setup"),
            "serial": commands(
                raw.get("checks", {}).get("serial", []), "checks.serial"
            ),
        },
        # read from the main checkout's settings, in a task's worktree too
        "flow": flow,
        "seats": seats,
        "corrections": corrections,
        "tracker": tracker,
        "naps": naps,
        # read from the main checkout's settings, in a task's worktree too, or from this
        # machine's own file; `from` names which, as each seat's does
        "state": state,
        # what this machine set for itself in the tables that are not seats; a seat's
        # `from` says it of the seat
        "local": {
            "file": str(local_file) if local_file.is_file() else None,
            "overrides": overridden,
        },
    }


def cmd_path(settings: dict, name: str) -> None:
    if name == "plan_file":
        raise SettingsError(
            "paths.plan_file is the pattern of a plan's name, not a path: "
            "`lem project plan-file SLUG` prints the name of a plan's file"
        )
    found = {**settings["places"], **{key: settings["paths"][key] for key in PATHS}}
    if name not in found:
        raise SettingsError(f"no path named {name!r}{nearest(name, tuple(found))}")
    print(found[name]["path"])


def cmd_plan_file(settings: dict, slug: str, day: str | None) -> None:
    """The name a task's plan takes, written today or on DAY, and the plan the plans
    folder holds now."""
    if not SLUG.fullmatch(slug):
        raise SettingsError(f"slug {slug!r} must be lower-case words joined by hyphens")
    day = day or datetime.now(UTC).strftime("%Y-%m-%d")
    try:
        datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=UTC)
    except ValueError as error:
        raise SettingsError(f"--date {day!r} is not a day as YYYY-MM-DD") from error
    pattern = settings["paths"]["plan_file"]["pattern"]
    folder = Path(settings["paths"]["plans"]["path"])
    # a task resumed from a dropped one works on the old branch's commits, its plan
    # among them
    before = lem_plans.resumed_from(state_root(Path(settings["root"])) / "tasks", slug)
    found = lem_plans.found(folder, pattern, slug, before)
    name = lem_plans.name(pattern, slug, day)
    print(
        json.dumps(
            {
                "slug": slug,
                "pattern": pattern,
                "name": name,
                "path": str(folder / name),
                "found": str(found) if found else None,
            },
            indent=2,
        )
    )


def cmd_may_land(settings: dict, target: str) -> None:
    """Exit 1 unless TARGET is the branch this project's tasks land on."""
    print(may_land(settings, target))


def may_land(settings: dict, target: str) -> str:
    """What `may-land` says of TARGET with these settings, or its refusal as a
    SettingsError. The landing calls it with the settings it loaded; whether the branch
    exists is asked of git each time."""
    branch = settings["branch"]
    if target in branch["protected"]:
        raise SettingsError(
            f"{target!r} is protected in {SETTINGS}: "
            "nothing lands on it or is pushed to it"
        )
    if branch["base"] is None:
        raise SettingsError(
            f"{SETTINGS} names no branch.base, so no branch can be landed on"
        )
    if target != branch["base"]:
        raise SettingsError(
            f"tasks of this project land on {branch['base']!r}, not on {target!r}"
        )
    found = subprocess.run(
        [
            "git",
            "-C",
            settings["root"],
            "rev-parse",
            "--verify",
            "--quiet",
            f"refs/heads/{target}",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if found.returncode != 0:
        raise SettingsError(
            f"branch.base = {target!r} is no branch of this repository; "
            f"correct it in {SETTINGS}, or make the branch first"
        )
    return f"{target}: tasks land here; " + (
        "the merge agent merges a green request that is not careful"
        if branch["land"] == "agent"
        else "the owner merges"
    )


def default_branch(root: Path) -> str | None:
    head = subprocess.run(
        ["git", "-C", str(root), "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return head.stdout.strip().removeprefix("origin/") if head.returncode == 0 else None


def rule_files(folder: Path) -> list[Path]:
    """Every .md below the folder, through links too, as the agent that loads such a
    folder by itself reads it."""
    found, seen = [], set()
    for where, folders, names in os.walk(folder, followlinks=True):
        real = os.path.realpath(where)
        if real in seen:
            folders[:] = []
            continue
        seen.add(real)
        folders.sort()
        found += [Path(where) / name for name in sorted(names) if name.endswith(".md")]
    return found


def cmd_init(root: Path, base: str | None, codex: str) -> None:
    file = root / SETTINGS
    if file.exists():
        raise SettingsError(f"{SETTINGS} already exists; edit it")
    # A task ends as a GitHub pull request, so a remote elsewhere could land nothing. A
    # repository with no remote yet gets its settings, and the first proposal asks for
    # the remote.
    origin = subprocess.run(
        ["git", "-C", str(root), "config", "--get", "remote.origin.url"],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    if origin and not GITHUB.match(origin):
        raise SettingsError(
            f"origin is {origin}, and Lem lands through GitHub pull requests only: "
            "point origin at the repository on GitHub (`git remote set-url origin "
            "git@github.com:OWNER/REPO.git`), then run init again",
        )
    if not origin:
        print(
            (
                "project.py: this repository has no remote origin yet; "
                "Lem lands through GitHub pull requests, so add it (`git remote add "
                "origin git@github.com:OWNER/REPO.git`) before the first landing"
            ),
            file=sys.stderr,
        )
    base = base or default_branch(root)
    if not base:
        raise SettingsError(
            "cannot tell the base branch (no origin/HEAD); pass --base NAME"
        )
    file.parent.mkdir(exist_ok=True)
    # a whole seat for each of the three, of the agents the machine has
    file.write_text(
        TEMPLATE.format(
            plans=PATHS["plans"],
            plan_file=PLAN_FILE,
            rulings=PATHS["rulings"],
            base=base,
            reviewer=REVIEWER_SEATS["codex" if codex == "yes" else "claude"],
            planner=PLANNER,
            experts=", ".join(
                toml_string(one)
                for one in EXPERTS
                if codex == "yes" or one.startswith("claude")
            ),
        ),
        encoding="utf-8",
    )
    # one machine's own settings and Lem's state are never committed (the state folder
    # also holds an ignore file of its own, `lem_state.py`)
    ignore = file.parent / ".gitignore"
    known = text_of(ignore).splitlines() if ignore.is_file() else []
    missing = [
        line for line in (LOCAL.name, f"{lem_state.STATE.name}/") if line not in known
    ]
    if missing:
        ignore.write_text("\n".join([*known, *missing]) + "\n", encoding="utf-8")
    print(file)


# What `set` writes: each seat, and the seat that stands in when one fails; with the
# words it says each by, a seat that can fail by the name its block and the pull request
# give it (`lem_state.SEAT_NAMES`).
SET_NAMES = (*SEATS, "experts", "fallback")
SET_WORDS = {
    **lem_state.SEAT_NAMES,
    "session": "a task's session",
    "experts": "the experts",
    "fallback": "the fallback",
}
# Where `set` writes: the developer's file for all his repositories (the home folder's
# `settings.toml`), or this machine's own file for this one. The team's file is
# everybody's, edited by hand and committed, and no command writes it.
SCOPES = ("global", "local")
# the first line of a file `set` makes; a file left with nothing but it and blank lines
# goes, and one with a comment of the owner's stays
SET_FIRST = {
    "global": (
        "# Your own settings for Lem, for every repository on this machine. "
        "`lem project set global NAME VALUE` writes a seat."
    ),
    "local": (
        "# This machine's own settings for Lem, for this repository. "
        "Not committed; `lem project set local NAME VALUE` writes a seat."
    ),
}


def set_value(scope: str, name: str, value: str) -> object:
    """What `set SCOPE NAME VALUE` writes, checked by the rule `show` reads it with: a
    whole seat for each seat (the merge agent's and the session's too), one or two whole
    seats joined by a comma for the experts, written as a list, `false` for the fallback
    only; None for `default`, which takes the line out."""
    if name not in SET_NAMES:
        raise SettingsError(
            "set takes a seat or fallback as NAME, not "
            f"{name!r}{nearest(name, SET_NAMES)}"
        )
    if value == "default":
        return None
    where = Path(f"set {scope} {name}")
    if value == "false":
        if name != "fallback":
            raise SettingsError(
                f"{where}: false is for fallback only, which it turns off; "
                f'{SET_WORDS[name]} takes a whole seat, "{SEAT_FORM}", or default, '
                "which takes the line out"
            )
        return False
    if name == "fallback":
        # `true` is refused as the settings refuse it, with the line to leave out; a
        # fallback named here gives a seat
        return cast(
            "dict",
            fallback_of(
                {"seats": {"fallback": True if value == "true" else value}}, where
            ),
        )["seat"]
    if name == "experts":
        parts = [part.strip() for part in value.split(",")]
        if len(parts) > len(EXPERT_PLACES):
            raise SettingsError(
                f"{where}: {value!r} names {len(parts)} seats, and the experts are one "
                "or two whole seats joined by a comma, as "
                f"`set {scope} experts {','.join(EXPERTS)}`"
            )
        experts_of({"seats": {"experts": parts}}, where)
        return parts
    agents, why, example = SEATS[name]
    # the example of SEATS may leave out a part, as the files may; the one `set` names
    # is whole, as it asks
    return parse_seat(
        value,
        f"{where}: seats.{name}",
        agents,
        why,
        example if name in WHOLE_SEATS else DEFAULT_SEATS[name],
        whole=True,
    )["seat"]


def seats_checked(tables: dict, name: Path) -> None:
    """The seats of one settings file, each by the rule `show` reads it with; it refuses
    with a SettingsError and the fix."""
    for which in SEATS:
        seat(tables, name, which)
    experts_of(tables, name)
    fallback_of(tables, name)


def local_checked(file: Path) -> None:
    """This machine's own file for the repository, read and checked whole; it refuses
    with a SettingsError and the fix."""
    local = read_settings(file, LOCAL, "local")
    local_naps_off(local)
    local_keep_days(local)
    seats_checked(local, LOCAL)


def cmd_set(root: Path, scope: str, name: str, words: list[str]) -> dict:
    """Write one line of `[seats]`, or with `default` take it out: `global` in the home
    folder's `settings.toml`, for each repository on this machine that names none,
    `local` in this machine's own file of the repository, in the main checkout. The
    value is checked first, then the file whole, then the repository's settings: a wrong
    one is refused with its fix, and the file stays as it was. Every other line of the
    file stays, its comments too (`lem_state.edited`). It gives the seat as `show` then
    reads it, with its `from`."""
    if scope not in SCOPES:
        raise SettingsError(
            f"set takes global, which writes {home_name()} for each repository on this "
            f"machine that names none, or local, which writes {LOCAL} of this "
            f"repository for this machine only; not {scope!r}. {SETTINGS} is the "
            "project's, edited by hand and committed: no command writes it"
        )
    if len(words) != 1:
        raise SettingsError(
            f'set {scope} {name} takes one VALUE, a whole seat "{SEAT_FORM}", as '
            f"`set {scope} reviewer {REVIEWER_SEATS['codex']}`, or default; "
            f"not {len(words)} words"
        )
    value = set_value(scope, name, words[0])
    if scope == "global":
        file, place = lem_state.home_settings_file(), home_name()
        seats_checked(read_settings(file, Path(place), "home"), Path(place))
    else:
        file = main_checkout(root) / LOCAL
        local_checked(file)
        place = str(LOCAL)
    # the repository's settings too, which the answer reads after the write: a refusal
    # comes before anything is written
    load(root)
    try:
        lem_state.write_edits(file, [("seats", name, value)], SET_FIRST[scope])
    except lem_state.StateError as error:
        raise SettingsError(str(error)) from error
    except OSError as error:
        raise SettingsError(
            f"{file} was not written ({error.strerror}); make its folder writable, "
            "then run this again"
        ) from error
    found = load(root)["seats"][name]
    if name == "experts":
        shown, source, verb = (
            ", ".join(expert["seat"] for expert in found),
            found[0]["from"],
            "are",
        )
    else:
        shown, source, verb = (
            ("off" if found["seat"] is False else found["seat"]),
            found["from"],
            "is",
        )
    said = f"{SET_WORDS[name]} here {verb} {shown}, from {source}"
    if value is None:
        said += f"; {place} names none"
    elif source != place:
        said += f", which comes before {place}"
    return {
        "scope": scope,
        "file": str(file),
        "name": name,
        "line": None if value is None else f"{name} = {lem_state.toml_value(value)}",
        "seat": found,
        "said": said,
    }


def braces(pattern: str) -> list[str]:
    """`*.{ts,tsx}` as `*.ts` and `*.tsx`, a group inside a group too. A brace with no
    comma stays as written."""
    depth, start = 0, 0
    for i, char in enumerate(pattern):
        if char == "{":
            if depth == 0:
                start = i
            depth += 1
        elif char == "}" and depth:
            depth -= 1
            if depth:
                continue
            parts, level, last = [], 0, start + 1
            for j in range(start + 1, i):
                level += (pattern[j] == "{") - (pattern[j] == "}")
                if pattern[j] == "," and level == 0:
                    parts.append(pattern[last:j])
                    last = j + 1
            parts.append(pattern[last:i])
            if len(parts) == 1:
                return [pattern[: i + 1] + rest for rest in braces(pattern[i + 1 :])]
            return [
                done
                for part in parts
                for done in braces(pattern[:start] + part + pattern[i + 1 :])
            ]
    return [pattern]


def glob_regex(glob: str) -> re.Pattern[str]:
    """One glob of a rule file's `paths:` as a pattern over a path relative to the root.

    The forms Claude Code documents for `paths:` (its page on `.claude/rules`, read
    2026-11-15): `**/*.ts` is every such file in any directory, `src/**/*` every file
    under `src/`, `*.md` the files of the root only, `src/components/*.tsx` the files of
    that one directory. So `*` and `?` stay inside one path segment, and `**` as a whole
    segment is any number of directories, none too. Not documented there, and matched
    here because a rule too many costs less than a rule missed: a name that starts with
    a dot, and a character class in brackets.
    """
    out, i = [], 0
    while i < len(glob):
        char = glob[i]
        whole = (
            glob.startswith("**", i)
            and (i == 0 or glob[i - 1] == "/")
            and (i + 2 == len(glob) or glob[i + 2] == "/")
        )
        if whole and i + 2 < len(glob):
            out.append("(?:.*/)?")
            i += 3
        elif whole:
            out.append(".*")
            i += 2
        elif char == "*":
            out.append("[^/]*")
            i += 1
        elif char == "?":
            out.append("[^/]")
            i += 1
        elif char == "[" and "]" in glob[i + 2 :]:
            end = glob.index("]", i + 2)
            inner = glob[i + 1 : end]
            inner = "^" + inner[1:] if inner[0] == "!" else inner
            out.append("[" + inner.replace("\\", "\\\\") + "]")
            i = end + 1
        else:
            out.append(re.escape(char))
            i += 1
    return re.compile("".join(out))


def glob_patterns(glob: str) -> list[re.Pattern[str]]:
    """The patterns one glob of a rule file's `paths:` stands for, one for each of its
    brace forms, with a leading `./` taken off; a path is covered when one of them
    matches it whole."""
    return [glob_regex(one) for one in braces(glob.removeprefix("./"))]


def rule_scope(file: Path, name: str) -> list[str] | None:
    """The globs a rule file scopes itself to, or None for one that covers every path.

    The one format read is Claude Code's: `paths:` in the file's frontmatter, as a list
    of globs. A `paths:` that names no glob is refused: whether the file then covers
    every path or none is not for a script to guess.
    """
    # utf-8-sig: a byte order mark before the first `---` must not turn a scoped rule
    # into one for every path
    lines = file.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    if not lines or lines[0].strip() != "---":
        return None

    def bare(text: str) -> str:
        """The text without a YAML comment: a `#` at the start or after a space,
        outside quotes."""
        quote = ""
        for i, char in enumerate(text):
            if quote:
                quote = "" if char == quote else quote
            elif char in "\"'":
                quote = char
            elif char == "#" and (i == 0 or text[i - 1].isspace()):
                return text[:i].strip()
        return text.strip()

    end = next(
        (i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), None
    )
    if end is None:
        return None
    block = lines[1:end]
    at = next((i for i, line in enumerate(block) if re.match(r"paths\s*:", line)), None)
    if at is None:
        return None
    rest = bare(block[at].split(":", 1)[1])
    items: list[str] = []
    if rest.startswith("[") and rest.endswith("]"):
        level, last, quote = 0, 1, ""
        for j in range(1, len(rest) - 1):
            char = rest[j]
            if quote:
                quote = "" if char == quote else quote
            elif char in "\"'":
                quote = char
            elif char in "{}":
                level += 1 if char == "{" else -1
            elif char == "," and level == 0:
                items.append(rest[last:j])
                last = j + 1
        items.append(rest[last:-1])
    elif rest:
        items = [rest]
    else:
        for follow in block[at + 1 :]:
            if not follow.strip() or follow.lstrip().startswith("#"):
                continue
            item = re.match(r"\s*-\s+(.*)$", follow)
            if item:
                items.append(bare(item.group(1)))
            elif follow[:1].isspace():
                raise SettingsError(
                    f"{name}: a line under `paths:` is not a list item "
                    f'({follow.strip()!r}); write each glob as `  - "GLOB"`'
                )
            else:
                break
    globs = [item.strip() for item in items]
    globs = [
        glob[1:-1]
        if len(glob) > 1 and glob[0] == glob[-1] and glob[0] in "\"'"
        else glob
        for glob in globs
    ]
    if not globs or not all(globs):
        raise SettingsError(
            f"{name}: its `paths:` names no glob; write each glob under it as "
            '`  - "GLOB"`, or take the line out so the file covers every path'
        )
    return globs


def cmd_rules(settings: dict, files: list[str], commits: str | None) -> None:
    """The rule files that cover the given files: one match for every reader of
    the rules."""
    root = Path(settings["root"]).resolve()
    changed = []
    for file in files:
        # One file has one answer, however it is named. Its folder is resolved the way
        # the file system reads it, a link first and `..` after it: `alias/../x` is
        # beside what `alias` points at. The last name is kept as written, since the
        # file may be a link or be gone.
        full = root / file
        if full == root or full.name in ("", ".", ".."):
            raise SettingsError(
                f"{file} does not name a file; name the files a change touches"
            )
        full = Path(os.path.realpath(full.parent)) / full.name
        if not full.is_relative_to(root) or full == root:
            raise SettingsError(
                f"{file} is not inside {root}; name files of this repository"
            )
        changed.append(full.relative_to(root).as_posix())
    if commits:
        # --no-renames: a file that moved counts under its old path and its new one,
        # each with its rules
        listed = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "diff",
                "--name-only",
                "--no-renames",
                "-z",
                commits,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if listed.returncode != 0:
            raise SettingsError(
                f"git diff --name-only {commits} failed: {listed.stderr.strip()}"
            )
        changed += [name for name in listed.stdout.split("\0") if name]
    changed = sorted(set(changed))
    if not files and not commits:
        raise SettingsError(
            "rules needs the files a change touches: name them, "
            "or pass --range BASE..TIP"
        )
    folder = Path(settings["root"]).resolve() / PLACES["rules"]
    rules: list[dict] = []
    for file in rule_files(folder):
        shown = (
            file.relative_to(root).as_posix()
            if file.is_relative_to(root)
            else str(file)
        )
        globs = rule_scope(file, shown)
        if globs is None:
            rules.append({"file": str(file), "scope": "every path"})
            continue
        try:
            patterns = [
                (glob, pattern) for glob in globs for pattern in glob_patterns(glob)
            ]
        except re.error as error:
            raise SettingsError(
                f"{shown}: a glob of its `paths:` does not read as a pattern "
                f"({error}); correct it, most likely a `[` with no `]` or a "
                "range that runs backwards"
            ) from error
        covers = sorted(
            {
                name
                for name in changed
                for _, pattern in patterns
                if pattern.fullmatch(name)
            }
        )
        if covers:
            rules.append(
                {
                    "file": str(file),
                    "scope": sorted(
                        {
                            glob
                            for glob, pattern in patterns
                            if any(pattern.fullmatch(name) for name in changed)
                        }
                    ),
                    "covers": covers,
                }
            )
    print(
        json.dumps(
            {
                "folder": str(folder),
                "exists": folder.is_dir(),
                "files": changed,
                "rules": rules,
            },
            indent=2,
        )
    )


STATE_ROOTS: dict[Path, Path] = {}


def state_root(root: Path) -> Path:
    """The folder task state lives in, `.lem/state/` of the main checkout, as
    `lem_state` says; asked once a run."""
    if root not in STATE_ROOTS:
        try:
            STATE_ROOTS[root] = lem_state.folder(root)
        except lem_state.StateError as error:
            raise SettingsError(str(error)) from error
    return STATE_ROOTS[root]


def taken_on_remote(root: Path, slug: str, branch: str | None) -> None:
    """Refuse a new task whose branch origin has already: a teammate's work, or a task
    of another machine. The name is the one `--branch` gives, else TYPE/SLUG for every
    type a task takes. One question to origin; a repository with no remote has nobody to
    collide with, and an origin that does not answer is said on stderr, since the push
    of `lem land propose` refuses such a branch too."""
    if (
        subprocess.run(
            ["git", "-C", str(root), "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=False,
        ).returncode
        != 0
    ):
        return
    names = [branch] if branch else [f"{kind}/{slug}" for kind in TYPES]
    asked = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "ls-remote",
            "--heads",
            "origin",
            *(f"refs/heads/{name}" for name in names),
        ],
        capture_output=True,
        text=True,
        check=False,
        stdin=subprocess.DEVNULL,
    )
    if asked.returncode != 0:
        said = [
            line.strip()
            for line in (asked.stderr or asked.stdout).splitlines()
            if line.strip()
        ]
        print(
            (
                "project.py: origin did not answer "
                f"({said[-1] if said else 'git ls-remote failed'}), so nothing checked "
                f"that no branch of {slug!r} is there already"
            ),
            file=sys.stderr,
        )
        return
    there = sorted(
        {
            line.split("\t", 1)[1].removeprefix("refs/heads/")
            for line in asked.stdout.splitlines()
            if "\t" in line
        }
        & set(names)
    )
    if there:
        raise SettingsError(
            (
                f"origin has the branch {there[0]} already, and no task here holds it: "
                "somebody's work, or a task of another machine. A new task takes a "
                "branch of its own: add a word to the slug"
            )
            + (", or give another --branch" if branch else ""),
        )


def ask_refusal(slug: str, kept: str | None, ask: str) -> str | None:
    """Why ASK cannot be the words of the task SLUG, whose ask.txt holds KEPT (None when
    it has none): the same words again are a retry and pass, and other words are another
    request under the same name."""
    if kept is None or kept.strip() == ask.strip():
        return None
    return (
        f"the task {slug!r} holds other words already ({kept.strip()!r}), and a task's "
        "words are written once: this is another request under the same name, so "
        "choose another name for it (add a word to the slug)"
    )


def ticket_id(tracker: dict | None, given: str) -> str:
    """The id of a ticket as the task keeps it, by the kind of the project's tracker: a
    Linear id in upper case (MBZ-12), a GitHub issue's number after `#` (#42). A project
    with no tracker takes no ticket: no tracker would act on it, and `ticket_owed` gives
    nothing with none."""
    if tracker is None:
        raise SettingsError(
            f"--ticket {given!r} names a tracker's ticket, and {SETTINGS} has no "
            '[tracker]: add the table with its kind (kind = "linear" or kind = '
            '"github"), or open the task with --ask alone'
        )
    if tracker["kind"] == "github":
        found = ISSUE.fullmatch(given)
        if not found or int(found[1]) == 0:
            raise SettingsError(
                f"--ticket {given!r} is not an issue's number, such as 42 or #42: "
                "the project's tracker is github"
            )
        return f"#{int(found[1])}"
    if not TICKET.fullmatch(given):
        raise SettingsError(
            f"--ticket {given!r} is not a ticket's id, such as MBZ-12: "
            f"the project's tracker is {tracker['kind']}"
        )
    return given.upper()


def released(task: dict) -> bool:
    """Whether a task gave its ticket back: it was dropped or answered, and owes the
    ticket nothing."""
    return task["status"] in RETURNED and not task["ticket_owed"]


def holder_refusal(task: dict, ticket: str, kind: str | None) -> str:
    """Why a new task cannot take TICKET, which TASK holds, with the way on."""
    slug = task["slug"]
    if task["status"] == "landed":
        return (
            f"the task {slug!r} landed the ticket {ticket}, and a ticket that landed "
            "stays with its task: start the new task from the owner's own words "
            "(--ask), with no --ticket"
        )
    if task["status"] in RETURNED:
        step = PAID_BY[task["status"]]
        pay = (
            f"the line `lem issue {step} {slug}`"
            if kind == "github"
            else f"the lem-linear skill's step `{step}` for {slug}, run from a session"
        )
        return (
            f"the task {slug!r} is {task['status']} and still owes the ticket {ticket} "
            f"{', '.join(task['ticket_owed'])}: pay it with {pay}, "
            "then open this task again"
        )
    return (
        f"the task {slug!r} already holds the ticket {ticket}; go on with that task, "
        "or drop it first"
    )


def mark_of(root: Path, ticket: str) -> Path:
    """The mark of a ticket in the state folder (TICKET_MARKS)."""
    return state_root(root) / TICKET_MARKS / ticket.lstrip("#")


def claim_ticket(
    root: Path,
    slug: str,
    ticket: str,
    tasks: list[dict],
    kind: str | None,
    succeeds: str | None = None,
) -> Path | None:
    """Take TICKET for the task SLUG, or refuse it with the task that holds it.
    `task-dir` and `resume` both call it; SUCCEEDS is the dropped task a resumed one
    goes on from, whose mark moves.

    The mark comes first and the scan of the tasks after it, so two opens at one moment
    cannot both pass: the mark is a link of a finished file, and only one link takes the
    name. A mark that names SLUG is a retry and passes. A mark whose task gave the
    ticket back is taken over. Returns the mark when this call made it, so that
    `held_ticket` gives it back when a refusal later in the opening stops it."""
    mark = mark_of(root, ticket)
    mark.parent.mkdir(parents=True, exist_ok=True)
    by_slug = {task["slug"]: task for task in tasks}
    made = None
    for _ in range(3):
        if link_mark(mark, slug):
            made = mark
            break
        try:
            holder = text_of(mark).strip()
        except FileNotFoundError:
            continue
        if holder == slug:
            break
        task = by_slug.get(holder)
        if holder == succeeds or (task is not None and released(task)):
            take_over(mark, holder, ticket)
            continue
        if task is None and not (state_root(root) / "tasks" / holder).is_dir():
            raise SettingsError(
                f"the ticket {ticket} has a mark, {mark}, that names the task "
                f"{holder!r}, whose folder is not there: a task that opens in this "
                f"moment, or a mark left behind. When no task {holder!r} opens, remove "
                f"the mark (rm '{mark}') and open this task again"
            )
        raise SettingsError(
            holder_refusal(
                task or {"slug": holder, "status": None, "ticket_owed": []},
                ticket,
                kind,
            )
        )
    else:
        raise SettingsError(
            f"the mark of the ticket {ticket}, {mark}, changed hands three times while "
            "this task asked for it: open this task again"
        )
    other = next(
        (
            task
            for task in tasks
            if task["ticket"] == ticket
            and task["slug"] not in (slug, succeeds)
            and not released(task)
        ),
        None,
    )
    if other:
        # a task that holds the ticket with no mark: a task the hand moved, or one of a
        # state folder from before the marks
        if made:
            made.unlink(missing_ok=True)
        raise SettingsError(holder_refusal(other, ticket, kind))
    return made


@contextlib.contextmanager
def held_ticket(
    root: Path,
    slug: str,
    ticket: str,
    tasks: list[dict],
    kind: str | None,
    succeeds: str | None = None,
) -> Generator[None, None, None]:
    """Take TICKET for the task SLUG (`claim_ticket`) for the rest of an opening,
    `task-dir`'s or `resume`'s: a refusal raised in the block gives back the mark this
    claim made, to the dropped task SUCCEEDS when the claim took it from that one, so
    that no mark names a task that never opened."""
    mark = mark_of(root, ticket)
    try:
        before = text_of(mark).strip()
    except FileNotFoundError:
        before = None
    made = claim_ticket(root, slug, ticket, tasks, kind, succeeds)
    try:
        yield
    except BaseException:
        if (
            made
            and unmark(made, slug) is None
            and succeeds is not None
            and before == succeeds
        ):
            link_mark(made, succeeds)
        raise


def link_mark(mark: Path, slug: str) -> bool:
    """Make MARK name the task SLUG, only when no mark is there: a link of a finished
    file, so of two writers at one moment one takes the name. False when a mark was
    there already."""
    fresh = mark.with_name(f"{mark.name}.{os.getpid()}.new")
    fresh.write_text(slug + "\n", encoding="utf-8")
    try:
        os.link(fresh, mark)
    except FileExistsError:
        return False
    else:
        return True
    finally:
        fresh.unlink(missing_ok=True)


def unmark(mark: Path, holder: str) -> str | None:
    """Remove MARK only while it still names the task HOLDER: it moves aside first, and
    a mark another open took in the meantime goes back. Returns the task that mark
    named, else None (removed, or no mark)."""
    aside = mark.with_name(f"{mark.name}.{os.getpid()}.gone")
    try:
        mark.rename(aside)
    except FileNotFoundError:
        return None
    moved = text_of(aside).strip()
    if moved != holder:
        try:
            os.link(aside, mark)
        except FileExistsError:
            pass
        finally:
            aside.unlink(missing_ok=True)
        return moved
    aside.unlink(missing_ok=True)
    return None


def take_over(mark: Path, holder: str, ticket: str) -> None:
    """Remove the mark of a task that gave its ticket back, only while it still names
    that task (`unmark`), and refuse when another open took it in the meantime."""
    moved = unmark(mark, holder)
    if moved is not None:
        raise SettingsError(
            f"the task {moved!r} took the ticket {ticket} in this moment; "
            "go on with that task"
        )


def give_back(root: Path, slug: str) -> None:
    """Remove the mark of the task SLUG's ticket once the task gave the ticket back:
    dropped or answered, and owing it nothing. A mark that names another task stays."""
    directory = state_root(root) / "tasks" / slug
    if not (directory / "ticket.txt").is_file():
        return
    blocks = (
        blocks_of(text_of(directory / "state.md"))
        if (directory / "state.md").is_file()
        else []
    )
    status = blocks[0]["status"] if blocks else None
    names, _ = ticket_steps_of(directory)
    if status not in RETURNED or ticket_owed(status, names, load(root)["tracker"]):
        return
    unmark(mark_of(root, text_of(directory / "ticket.txt").strip()), slug)


def ticket_steps_of(directory: Path) -> tuple[list[str], str | None]:
    """The steps written down for a task's ticket, one a line, and the login of the
    line `assigned LOGIN`."""
    file = directory / "ticket-steps.txt"
    rows = (
        [line.split() for line in text_of(file).splitlines() if line.strip()]
        if file.is_file()
        else []
    )
    login = next(
        (row[1] for row in rows if row[0] == "assigned" and len(row) > 1), None
    )
    return [row[0] for row in rows], login


def cmd_task_dir(
    root: Path,
    slug: str,
    ask: str | None,
    ticket: str | None,
    branch: str | None = None,
    night: str | None = None,
    ticket_repo: str | None = None,
) -> None:
    if not SLUG.fullmatch(slug):
        raise SettingsError(f"slug {slug!r} must be lower-case words joined by hyphens")
    if ask is not None and not ask.strip():
        raise SettingsError(
            "--ask is the owner's words for this task, and they are empty"
        )
    if night is not None:
        if ask is None:
            raise SettingsError(
                "--night marks a task the night opens, so it goes with --ask, "
                "the backlog item's path"
            )
        try:
            date.fromisoformat(night)
        except ValueError:
            raise SettingsError(
                f"--night is the night's date, YYYY-MM-DD, not {night!r}"
            ) from None
    if ask is not None or ticket is not None:
        # This call opens a task. A slug whose task has ended keeps that task's files,
        # its state and what was done to its ticket: a new task under it would start
        # with another task's record.
        ended = next(
            (
                task["status"]
                for task in read_tasks(root)
                if task["slug"] == slug and task["status"] in ENDED
            ),
            None,
        )
        if ended:
            raise SettingsError(
                f"the task {slug!r} is {ended}; a new task takes a slug of its own: "
                "add a word to this one"
            )
    if ask is not None and (gone := dropped_item_refusal(state_root(root), ask)):
        # the reviewer's item the board showed is gone: the owner dropped it in
        # the meantime
        raise SettingsError(gone)
    if ticket_repo is not None and ticket is None:
        raise SettingsError(
            "--ticket-repo is the repository of the issue the task came from, "
            "so it goes with --ticket"
        )
    directory = state_root(root) / "tasks" / slug
    claim: contextlib.AbstractContextManager = contextlib.nullcontext()
    if ticket is not None:
        tracker = load(root)["tracker"]
        ticket = ticket_id(tracker, ticket)
        if tracker["kind"] == "github":
            if ticket_repo is None:
                raise SettingsError(
                    f"--ticket {ticket} is an issue of GitHub, and the task keeps the "
                    "repository of the issue that was read: give it as --ticket-repo "
                    "OWNER/REPO, from the address `lem issue read` gave"
                )
            if not ISSUE_REPO.fullmatch(ticket_repo):
                raise SettingsError(
                    f"--ticket-repo {ticket_repo!r} is not a repository of GitHub: "
                    "give it as OWNER/REPO, from the issue's address"
                )
        elif ticket_repo is not None:
            raise SettingsError(
                "--ticket-repo names the repository of a GitHub issue, and the "
                f"project's tracker is {tracker['kind']}: leave it out"
            )
        tasks = read_tasks(root)
        mine = next((task for task in tasks if task["slug"] == slug), None)
        if (
            mine
            and mine["ticket"]
            and (mine["ticket"], mine["ticket_repo"]) != (ticket, ticket_repo)
        ):
            # two tickets with one title would give one slug: the first task keeps
            # its ticket
            held = mine["ticket"] + (
                f" of {mine['ticket_repo']}" if mine["ticket_repo"] else ""
            )
            raise SettingsError(
                f"the task {slug!r} already holds the ticket {held}; give the task for "
                f"{ticket} another slug"
            )
        # one ticket is one task: a second task for it would be a second branch for the
        # same work
        claim = held_ticket(root, slug, ticket, tasks, tracker["kind"])
    with claim:
        opens = (ask is not None or ticket is not None) and not directory.is_dir()
        if opens:
            taken_on_remote(root, slug, branch)
        (directory / "reports").mkdir(parents=True, exist_ok=True)
        if opens:
            # the release the task begins on: the one its project's sessions load
            # (lem_release.chosen). A task whose directory was there already keeps what
            # it has, a mark or none.
            try:
                lem_release.mark(directory, main_checkout(root))
            except ValueError as error:
                raise SettingsError(str(error)) from None
        if ask is not None:
            # The owner's words, as given. task.md is a document with headings; the
            # board and the status show these words, so they have a file of their own
            # that nothing rewrites: a link of a finished file claims the name, so of
            # two writers at one moment one writes, and the other finds its words whole
            # and compares them.
            file = directory / "ask.txt"
            fresh = directory / f"ask.txt.{os.getpid()}.new"
            fresh.write_text(ask.strip() + "\n", encoding="utf-8")
            try:
                os.link(fresh, file)
            except FileExistsError:
                refused = ask_refusal(slug, text_of(file), ask)
                if refused:
                    raise SettingsError(refused) from None
            finally:
                fresh.unlink(missing_ok=True)
        if ticket is not None:
            (directory / "ticket.txt").write_text(ticket + "\n", encoding="utf-8")
            if ticket_repo is not None:
                (directory / "ticket-repo.txt").write_text(
                    ticket_repo + "\n", encoding="utf-8"
                )
    if night is not None and not any(
        record.get("task") == slug for record in events_named(root, "task.mode")
    ):
        # the night's mark
        append_event(
            root,
            "task.mode",
            slug,
            {
                "mode": "alone",
                "by": "lem",
                "words": f"the night of {night}",
                "all": False,
                "was": "with-owner",
            },
        )
    register_checkout(root)
    print(directory)


def register_checkout(root: Path) -> None:
    """Put the repository's main checkout into the machine's list of workspaces
    (`lem_state.register`), so that the board server shows it and runs its duties from
    its first task: `task-dir` and `lem session open` call it, as `lem board` does. A
    state folder of example tasks (its `demo` mark, board.py `meta_of`) stays out. A
    list that cannot be written is one line on stderr with the line that puts the
    repository there, and the task still opens."""
    main = main_checkout(root)
    if (state_root(root) / "demo").is_file():
        return
    try:
        lem_state.register(main)
    except (OSError, lem_state.StateError) as error:
        print(
            (
                f"project.py: {main} is not in the list of workspaces the board server "
                f"shows ({error}); `lem serve --add {main}` puts it there"
            ),
            file=sys.stderr,
        )


def cmd_ticket_step(root: Path, slug: str, step: str, login: str | None = None) -> None:
    """Write down one thing Lem did to the task's ticket, after the tracker took it (the
    assignee's step before, with the login). The step that leaves a dropped or answered
    task owing nothing gives its ticket's mark back."""
    directory = task_directory(root, slug)
    ticket = directory / "ticket.txt"
    if not ticket.is_file():
        raise SettingsError(f"the task {slug!r} came from no ticket")
    if step not in TICKET_STEPS:
        raise SettingsError(f"{step!r} is not a step{nearest(step, TICKET_STEPS)}")
    if step == "assigned" and login is None:
        raise SettingsError(
            "the step 'assigned' keeps the login Lem adds as the issue's assignee: "
            "give it as --login LOGIN"
        )
    if step != "assigned" and login is not None:
        raise SettingsError(
            f"--login goes with the step 'assigned' only, not with {step!r}"
        )
    if login is not None and not LOGIN.fullmatch(login):
        raise SettingsError(
            f"--login {login!r} is not a login of GitHub: "
            "give the login `gh api user --jq .login` prints"
        )
    file = directory / "ticket-steps.txt"
    steps, _ = ticket_steps_of(directory)
    if step in steps:
        # the caller should have looked first: a step that is written down was done, and
        # is not done again
        raise SettingsError(
            f"the step {step!r} is already written down for {text_of(ticket).strip()}: "
            "it was done, do not do it again"
        )
    if step == "unassigned" and "assigned" not in steps:
        raise SettingsError(
            "the step 'unassigned' undoes the step 'assigned', which is not written "
            f"down for {text_of(ticket).strip()}: Lem added nobody to remove"
        )
    rows = (
        [line.strip() for line in text_of(file).splitlines() if line.strip()]
        if file.is_file()
        else []
    )
    file.write_text(
        "\n".join([*rows, f"{step} {login}" if login else step]) + "\n",
        encoding="utf-8",
    )
    give_back(root, slug)
    steps, assignee = ticket_steps_of(directory)
    print(
        json.dumps(
            {
                "slug": slug,
                "ticket": text_of(ticket).strip(),
                "steps": steps,
                "assignee": assignee,
            }
        )
    )


def ask_of(directory: Path) -> str | None:
    """What the owner asked for: the words `task-dir --ask` kept, else the first words
    of task.md without their markup."""
    for name in ("ask.txt", "task.md"):
        file = directory / name
        lines = (
            [line.strip() for line in text_of(file).splitlines() if line.strip()]
            if file.is_file()
            else []
        )
        if lines:
            return (
                " ".join(lines)
                if name == "ask.txt"
                else lines[0].lstrip("#> ").strip() or None
            )
    return None


def cmd_worktree_dir(settings: dict, slug: str) -> None:
    """Print where a task's worktree goes, and keep the folder that holds worktrees out
    of git status."""
    if not SLUG.fullmatch(slug):
        raise SettingsError(f"slug {slug!r} must be lower-case words joined by hyphens")
    parent = Path(settings["places"]["worktrees"]["path"])
    parent.mkdir(parents=True, exist_ok=True)
    ignore = parent / ".gitignore"
    if not ignore.is_file():
        # `*` ignores the folder's content and this file, so the project needs no
        # ignore rule
        ignore.write_text("*\n", encoding="utf-8")
    print(parent / slug)


def cmd_worktree(root: Path, settings: dict, slug: str, branch: str) -> dict:
    """Make the task's worktree where `worktree-dir` says, on BRANCH. A new branch
    starts from the base branch as origin has it now, after a fetch: the local base
    branch may be days old. It gets no upstream, so that no `git push` of a builder's
    reaches the base. With no remote, or an origin that does not answer (said in one
    line on stderr), it starts from the local base branch."""

    def git(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(main), *args],
            capture_output=True,
            text=True,
            check=False,
            stdin=subprocess.DEVNULL,
        )

    def said(ran: subprocess.CompletedProcess) -> str:
        lines = [
            line.strip()
            for line in (ran.stderr or ran.stdout).splitlines()
            if line.strip()
        ]
        return lines[-1] if lines else f"exit {ran.returncode}"

    main = main_checkout(root)
    if not SLUG.fullmatch(slug):
        raise SettingsError(f"slug {slug!r} must be lower-case words joined by hyphens")
    if git("check-ref-format", "--branch", branch).returncode != 0:
        raise SettingsError(f"{branch!r} is not a name git takes for a branch")
    base = settings["branch"]["base"]
    if base is None:
        raise SettingsError(
            f"{SETTINGS} names no branch.base, so a new task has nothing to start from"
        )
    if branch == base or branch in settings["branch"]["protected"]:
        raise SettingsError(
            f"{branch!r} is the base branch or a protected one; "
            "a task works on a branch of its own"
        )
    parent = Path(settings["places"]["worktrees"]["path"])
    place = main / parent.relative_to(root.resolve()) / slug
    if (place / ".git").exists():
        on = subprocess.run(
            ["git", "-C", str(place), "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
        if on != branch:
            raise SettingsError(
                f"{place} is a worktree on {on or 'no branch'}, not on {branch}: "
                "the task's worktree is the one on its branch"
            )
        return {
            "task": slug,
            "worktree": str(place),
            "branch": branch,
            "made": False,
            "from": None,
        }
    place.parent.mkdir(parents=True, exist_ok=True)
    if not (place.parent / ".gitignore").is_file():
        (place.parent / ".gitignore").write_text("*\n", encoding="utf-8")
    if git("rev-parse", "--verify", "--quiet", f"refs/heads/{branch}").returncode == 0:
        # a branch the task has already (a task whose worktree was removed): as it is
        made, start = git("worktree", "add", str(place), branch), branch
    else:
        start = base
        if git("remote", "get-url", "origin").returncode == 0:
            fetched = git("fetch", "-q", "origin", base)
            if fetched.returncode == 0:
                start = f"origin/{base}"
            else:
                print(
                    (
                        f"project.py: origin did not answer ({said(fetched)}), so "
                        f"{slug} starts from the local {base} as it is now"
                    ),
                    file=sys.stderr,
                )
        made = git("worktree", "add", "--no-track", "-b", branch, str(place), start)
    if made.returncode != 0:
        raise SettingsError(
            f"git could not make the worktree {place} on {branch}: {said(made)}"
        )
    commit = subprocess.run(
        ["git", "-C", str(place), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    setup = worktree_setup(root, settings, slug, place)
    return {
        "task": slug,
        "worktree": str(place),
        "branch": branch,
        "made": True,
        "from": start,
        "commit": commit,
        "setup": setup,
    }


def worktree_setup(root: Path, settings: dict, slug: str, place: Path) -> list[dict]:
    """Run `checks.setup` one time in a worktree just made, so that its tests can run:
    without it a task on the fast track whose builder runs no test reaches the checks
    with no packages, and the checks fail on what the change did not cause (a probe on
    2026-11-18: `setup = ["npm ci"]`, a README fix, and the checks red on a missing
    package). Each command's output goes to `setup.log` in the task directory (beside
    the worktree for a slug with none). A command that fails stops the rest and is
    refused with its exit; the worktree stays, made."""
    done: list[dict] = []
    if not settings["checks"]["setup"]:
        return done
    directory = state_root(root) / "tasks" / slug
    log = (
        directory / "setup.log"
        if directory.is_dir()
        else place.parent / f"{slug}.setup.log"
    )
    with log.open("w", encoding="utf-8") as out:
        for command in settings["checks"]["setup"]:
            out.write(f"$ {command}\n")
            out.flush()
            code = subprocess.run(  # noqa: S602 - checks.setup is the project's own shell line, which runs as written
                command,
                shell=True,
                cwd=place,
                stdout=out,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                check=False,
            ).returncode
            done.append({"command": command, "exit": code})
            if code != 0:
                raise SettingsError(
                    f"`{command}` of checks.setup failed in the new worktree {place} "
                    f"(exit {code}; its output is in {log}), so its tests cannot run. "
                    f"The worktree stays: correct the command in {SETTINGS}, "
                    "then run it there by hand",
                )
    return done


def task_directory(root: Path, slug: str) -> Path:
    if not SLUG.fullmatch(slug):
        raise SettingsError(f"slug {slug!r} must be lower-case words joined by hyphens")
    directory = state_root(root) / "tasks" / slug
    if not directory.is_dir():
        raise SettingsError(
            f"no task {slug!r}; `lem project task-dir {slug}` makes its directory"
        )
    return directory


def append_event(root: Path, event: str, slug: str, fields: dict) -> dict:
    """Append one record to the log, under the log's lock: a `prune` that rewrites the
    log either has not read it yet, or has put its new file in place, and the record
    goes into the file that stays."""
    record = {
        "ts": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": event,
        "task": slug,
        **fields,
    }
    line = json.dumps(record, ensure_ascii=False)
    try:
        line.encode("utf-8")
    except UnicodeEncodeError as error:
        # a `key:=json` value may spell a lone surrogate, "\udcff", which no UTF-8 file
        # can hold
        raise SettingsError(
            "a field of the event is not UTF-8 text "
            f"({line[max(0, error.start - 20) : error.start]!r} comes before it); "
            "give its text in UTF-8"
        ) from error
    directory = state_root(root)
    with (
        lem_state.events_lock(directory),
        (directory / lem_state.EVENTS).open("a", encoding="utf-8") as log,
    ):
        log.write(line + "\n")
    return record


def task_plan(root: Path, settings: dict, slug: str) -> tuple[Path, str] | None:
    """The task's plan in its worktree, with its path from the repository root, as the
    board's artifacts explorer lists it; None when the task has no worktree or its plan
    is not written."""
    resolved = root.resolve()
    worktree = (
        main_checkout(root)
        / Path(settings["places"]["worktrees"]["path"]).relative_to(resolved)
        / slug
    )
    if not (worktree / ".git").exists():
        return None
    folder = Path(settings["paths"]["plans"]["path"]).relative_to(resolved)
    found = lem_plans.found(
        worktree / folder,
        settings["paths"]["plan_file"]["pattern"],
        slug,
        lem_plans.resumed_from(state_root(root) / "tasks", slug),
    )
    return (found, (folder / found.name).as_posix()) if found else None


def task_worktree(root: Path, settings: dict, slug: str) -> dict:
    """The branch and the newest commit of the task's worktree; nothing when it has
    no worktree."""

    def git(where: Path, *args: str) -> str | None:
        ran = subprocess.run(
            ["git", "-C", str(where), *args],
            capture_output=True,
            text=True,
            check=False,
        )
        return (
            ran.stdout.strip() if ran.returncode == 0 and ran.stdout.strip() else None
        )

    # Worktrees hang off the main checkout, and this may run in one of them.
    path = (
        main_checkout(root)
        / Path(settings["places"]["worktrees"]["path"]).relative_to(root.resolve())
        / slug
    )
    if not (path / ".git").exists():
        return {}
    commit = git(path, "log", "-1", "--format=%h%x00%s")
    head, _, subject = (commit or "").partition("\0")
    found = {
        "branch": git(path, "branch", "--show-current"),
        "head": head or None,
        "subject": subject or None,
    }
    return {key: value for key, value in found.items() if value}


def parked_refusal(
    slug: str, now: str | None, status: str, *, resumed: bool = False
) -> str | None:
    """Why `state` refuses STATUS over a task whose newest status is NOW, for the park:
    a parked task leaves `parked` only by a drop or by `resume`, and only a task no
    agent works on is parked."""
    if now == PARKED and status not in (PARKED, "dropped") and not resumed:
        return (
            f"the task {slug!r} is parked: the owner put it aside, and a reply or a "
            f"message about {slug} that comes now is a stale wake-up. "
            f"`lem project resume {slug}` brings it back on his word, "
            "and `dropped` ends it"
        )
    if status == PARKED and now not in (*PARKABLE, PARKED):
        return (
            f"the task {slug!r} is {now or 'new'}, and only a task that no agent "
            f"works on is parked ({', '.join(PARKABLE)}): "
        ) + (
            (
                "its lead or its investigator works now, so park it once it stops, "
                "or drop it now"
            )
            if now == "building"
            else "its build is done: its landing goes on, or the owner drops it"
            if now in ("ready", *WITH_LANDING)
            else "an ended task stays ended"
            if now in ENDED
            else "nothing of it runs to put aside"
        )
    return None


# The task directories whose state lock each thread of this process holds
# (`state_locked`), so that a command that decides under the lock (`seat-failed`,
# `seat-again`) writes its block through `cmd_state` without waiting for itself: a
# second flock of the same file in one process waits for the first. By thread, since
# another thread of the board's server is another writer.
LOCKS_HELD: set[tuple[int, Path]] = set()


@contextlib.contextmanager
def state_locked(directory: Path) -> Generator[None, None, None]:
    """Hold the lock of one task's state.md (STATE_LOCK in its directory), or go on
    under it when this thread holds it already."""
    mine = (threading.get_ident(), directory)
    if mine in LOCKS_HELD:
        yield
        return
    with (directory / STATE_LOCK).open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        LOCKS_HELD.add(mine)
        try:
            yield
        finally:
            LOCKS_HELD.discard(mine)


def cmd_state(
    root: Path,
    slug: str,
    status: str,
    lines: list[str],
    *,
    start_over: bool = False,
    resumed: bool = False,
    again: bool = False,
) -> dict:
    """Put a new block at the top of the task's state.md, and the same as an event in
    the log. `resumed` is `resume`'s own write over a parked task, the one way out of
    `parked` but a drop; `again` is `seat-again`'s, the one way from `blocked` back to
    `open`, and the one way over a block with `the seat that failed: SEAT` but a park,
    another block or an end."""
    directory = task_directory(root, slug)
    settings = load(root)
    if status not in STATES:
        raise SettingsError(
            f"status {status!r} is not one a task has{nearest(status, STATES)}"
        )
    if start_over and status != "ready":
        raise SettingsError(
            "--start-over gives a landing's line back, and only the state ready "
            f"does that, not {status}"
        )
    if any(not line.strip() or "\n" in line for line in lines):
        # a blank line ends a block, so one inside a block would hide the lines after it
        raise SettingsError(
            "each LINE of a state block is one line of text, and none is empty"
        )
    for line in lines:
        type_line(line)
        fixed_form(line)
    # one writer at a time, from the read of the newest status through the event's
    # append: the lead's `building` and the owner's drop at one moment would else each
    # read the old status, and one block would be lost or land above the drop
    with state_locked(directory):
        # the status the newest block gives, read from this task's file alone
        written = (
            text_of(directory / "state.md").strip()
            if (directory / "state.md").is_file()
            else ""
        )
        first = (
            STATE_LINE.fullmatch(written.split("\n\n")[0].splitlines()[0])
            if written
            else None
        )
        now = first["status"] if first else None
        if now in ENDED and status != now:
            raise SettingsError(
                f"the task {slug!r} is {now}, and an ended task stays ended: "
                "new work for it is a new ask (`/lem new`), whose task takes a slug of "
                f"its own. A reply or a message about {slug} that comes now is a stale "
                "wake-up, and nothing is done for it",
            )
        if (
            now in WITH_LANDING
            and status in LEADS_WRITE
            and not (status == "ready" and start_over)
        ):
            raise SettingsError(
                f"the task {slug!r} is {now}: it is with its landing, and a reply or a "
                f"message about {slug} that comes now is a stale wake-up, and no state "
                "is written for it; what the landing needs, land.py says itself",
            )
        refused = parked_refusal(slug, now, status, resumed=resumed)
        if refused:
            raise SettingsError(refused)
        if now == "blocked" and status == "open" and not again:
            # a merge agent's seat that failed blocks an open task, and only the owner's
            # go on opens it again
            raise SettingsError(
                f"the task {slug!r} is blocked, and only the owner's go on gives "
                f"`open` back: `lem project seat-again {slug}` writes it, when the "
                "block names the seat that failed"
            )
        held_seat = (
            failed_seat(written.split("\n\n")[0].splitlines())
            if now == "blocked"
            else None
        )
        if held_seat and not again and status not in ("blocked", PARKED, *ENDED):
            # a seat's block waits for the owner: a lead's state written after it (the
            # `building` of a pair whose defender's seat failed at its open) would take
            # the task out of "Waits for you" with no go on
            raise SettingsError(
                f"the task {slug!r} is blocked with "
                f"`{lem_state.FAILED_SEAT}{held_seat}`, and only the owner's go on "
                f"lifts that block: `lem project seat-again {slug}` writes the state "
                "before it. A lead that wrote no state since it opened the pair takes "
                "the block as its wait gives it"
            )
        if status == "answered":
            answered_form(root, directory, slug)
        # the time is the clock's, never a writer's estimate
        since = datetime.now(UTC).strftime("%Y-%m-%dT%H:%MZ")
        block = "\n".join(
            [
                f"{since} {status}: {lines[0].strip()}",
                *(line.strip() for line in lines[1:]),
            ]
        )
        file = directory / "state.md"
        older = text_of(file).strip() if file.is_file() else ""
        # the process's id in the name: two writers at one moment never write one
        # new file
        fresh = directory / f"state.md.{os.getpid()}.new"
        fresh.write_text(
            block + ("\n\n" + older if older else "") + "\n", encoding="utf-8"
        )
        fresh.replace(file)
        worktree = task_worktree(root, settings, slug)
        # the task's first line, for the block that names its path: the session says it,
        # the board shows it, and the session where he typed the request says its named
        # form (`lem session wait SLUG --first-line`)
        said = opening_line(
            root, directory, slug, status, lines, older, worktree.get("branch")
        )
        append_event(
            root,
            "task.state",
            slug,
            {
                "status": status,
                "text": lines[0].strip(),
                "lines": [line.strip() for line in lines[1:]],
                "ask": ask_of(directory),
                **worktree,
                **(said or {}),
            },
        )
    return {
        "slug": slug,
        "status": status,
        "since": since,
        **({"say": said["say"]} if said else {}),
    }


# What `resume` copies from a dropped task into the new one: the documents a fresh agent
# goes on from, the records the landing reads, the release the task began on
# (lem_release.MARK: the new task goes on with the old one's records, so it keeps their
# release, and one with no mark stays unmarked), each breaker's document
# (`breaker-N.md`, RESUMED_GLOBS) and the breaker's pictures (`media/`). The landing's
# own files (`landing.json`, `gate/`, `reviews/`, `pr.md`) stay with the old task: the
# new one lands anew.
RESUMED_FILES = (
    "task.md",
    "talk.md",
    "directions.md",
    "interview-notes.md",
    "scout.md",
    "investigation.md",
    "outside.md",
    "criteria.md",
    "criteria-read.md",
    "criteria.json",
    "decisions.jsonl",
    "handoff.md",
    "ticket.txt",
    "ticket-repo.txt",
    lem_release.MARK,
)
RESUMED_GLOBS = ("breaker-*.md",)
# What the resume of a task the release stop blocked copies: the documents an agent
# reads as text and the ticket, and no record (`criteria.json`, `decisions.jsonl`). That
# task began two releases back or more, and a release reads the records of the release
# just before it and no older ones (lem_release).
RESUMED_NOTES = (
    *(name for name in RESUMED_FILES if name.endswith(".md")),
    "ticket.txt",
    "ticket-repo.txt",
)
# The events of a dropped task that the new one takes with it, under its own slug and
# with `from`, in the log's order and each with its own time as `was_at`: what the
# landing and the board read of its criteria, its decisions, its plan talk and its
# investigation, each stage's start with its end.
RESUMED_EVENTS = (
    "criteria.read.start",
    "criteria.read",
    "criteria.approved",
    "task.criteria",
    "plan.talk.start",
    "plan.talk",
    "investigation.start",
    "investigation",
    "interview.start",
    "interview.end",
    "read.skip.asked",
    "scout.start",
    "scout",
)
# The file of a resumed task that names the task it came from.
RESUMED_FROM = lem_plans.RESUMED_FROM


def blocks_of(text: str) -> list[dict]:
    """The blocks of a state.md, newest first, each with its status and its lines."""
    out = []
    for block in (part for part in text.strip().split("\n\n") if part.strip()):
        rows = block.splitlines()
        found = STATE_LINE.fullmatch(rows[0])
        if found:
            out.append({"status": found["status"], "lines": [found["text"], *rows[1:]]})
    return out


def failed_seat(lines: list[str]) -> str | None:
    """The seat a block names as the one that failed (`the seat that failed: SEAT`),
    or None."""
    return next(
        (
            found["seat"]
            for found in map(FAILED_LINE.fullmatch, (line.strip() for line in lines))
            if found
        ),
        None,
    )


def stand_in_of(events: list[dict], which: str) -> dict | None:
    """The `seat.stand-in` that holds WHICH for a task: its newest, when no `seat.again`
    of WHICH came after it; else None. EVENTS are the task's seat events in the
    log's order."""
    held = None
    for event in events:
        if event.get("seat") != which:
            continue
        if event.get("event") == "seat.stand-in":
            held = event
        elif event.get("event") == "seat.again":
            held = None
    return held


def seat_events(root: Path, slug: str) -> list[dict]:
    """The task's seat events (SEAT_EVENTS), oldest first."""
    return [
        event for event in events_named(root, *SEAT_EVENTS) if event.get("task") == slug
    ]


def seat_name_refusal(which: str, command: str) -> str | None:
    """Why WHICH is no seat that COMMAND takes; None when it is one of SEATS."""
    if which in SEATS:
        return None
    if which == "experts":
        return (
            f"`{command}` takes one seat, and the experts are one or two that take no "
            "fallback seat: when one expert's agent gives an error, the other answers "
            "alone; `lem project show` gives them as seats.experts"
        )
    return (
        f"{which!r} is no seat{nearest(which, tuple(SEATS))}; "
        f"a seat is one of {', '.join(SEATS)}"
    )


def cmd_seat(root: Path, slug: str, which: str) -> dict:
    """The seat in use for a task: the fallback that stands in for it (`from` is
    STAND_IN), or else the seat the settings name, as `show` gives it. Every stage that
    opens a seat's agent takes it here."""
    task_directory(root, slug)
    refused = seat_name_refusal(which, "lem project seat")
    if refused:
        raise SettingsError(refused)
    settings = load(root)
    held = stand_in_of(seat_events(root, slug), which)
    if held is None:
        return {"task": slug, "name": which, **settings["seats"][which]}
    agents, why, example = SEATS[which]
    parsed = parse_seat(
        held.get("took"),
        f"the stand-in of {which} in the event log",
        agents,
        why,
        example,
        whole=which in WHOLE_SEATS,
    )
    return {
        "task": slug,
        "name": which,
        **parsed,
        "from": STAND_IN,
        "for": held.get("failed"),
        "error": held.get("error"),
    }


def seat_call(which: str, line: str, kind: str, fallback: dict) -> dict:
    """What a seat whose agent on LINE gave the error KIND comes to, with FALLBACK as
    `show` gives it: `{"took": SEAT}`, the fallback's seat parsed, which stands in; or
    `{"block": LINE}`, the first line of the block, when the fallback is off, when it is
    the seat that failed (a stand-in that failed too, or a fallback that is the seat the
    settings name), or when its agent may not sit in WHICH."""
    name = lem_state.SEAT_NAMES[which]
    head = call_head(which, line, kind)
    if fallback["seat"] is False:
        return {"block": f"{head}, and this project permits no fallback"}
    if fallback["seat"] == line:
        return {"block": f"{head}, and it was the fallback"}
    agents = SEATS[which][0]
    if fallback["agent"] not in agents:
        takes = " or ".join(lem_state.AGENT_NAMES.get(agent, agent) for agent in agents)
        return {
            "block": (
                f"{head}, and its fallback `{fallback['seat']}` cannot sit in {name}'s "
                f"seat, which takes {takes} only"
            )
        }
    return {
        "took": {key: fallback[key] for key in ("agent", "model", "effort", "seat")}
    }


def cmd_seat_failed(
    root: Path, slug: str, which: str, line: str, kind: str, said: str | None
) -> dict:
    """A seat's agent gave one of the four errors: the fallback stands in for WHICH from
    now on, logged as `seat.stand-in`, or the task is blocked, with the block's line and
    the fixed line FAILED_LINE, logged as `seat.blocked`. LINE is the seat the stage
    opened, as `seat` printed it, so the record names the agent that failed and not the
    settings at a later moment. Decided under the task's lock."""
    directory = task_directory(root, slug)
    if which in ("session", "experts"):
        raise SettingsError(
            f"the {which} take no fallback seat: "
            + (
                "when one expert's agent gives an error, the other expert answers alone"
                if which == "experts"
                else "the session seat is the Claude session that runs the task"
            )
            + "; `seat-failed` takes the reviewer, the planner or the merger"
        )
    if which not in lem_state.SEAT_NAMES:
        raise SettingsError(
            f"{which!r} is no seat{nearest(which, tuple(lem_state.SEAT_NAMES))}; "
            f"`seat-failed` takes {', '.join(lem_state.SEAT_NAMES)}"
        )
    if kind not in lem_state.SEAT_ERRORS:
        raise SettingsError(
            f"--error {kind!r} is none of the four errors of a seat's agent: "
            f"{', '.join(lem_state.SEAT_ERRORS)} (the program is not on the Mac, no "
            "login, no tokens, an unknown model). A slow agent is no error: wait for it"
        )
    agents, why, example = SEATS[which]
    parse_seat(line, "--seat", agents, why, example, whole=which in WHOLE_SEATS)
    if said is not None and (not said.strip() or "\n" in said):
        raise SettingsError(
            "--said is the agent's own line of the error, one line of text"
        )
    settings = load(root)
    with state_locked(directory):
        call = seat_call(which, line, kind, settings["seats"]["fallback"])
        words = {
            "seat": which,
            "failed": line,
            "error": kind,
            **({"said": said.strip()} if said else {}),
        }
        if "took" in call:
            took = call["took"]
            say = (
                f"{call_head(which, line, kind)}; `{took['seat']}` stands in for it "
                "from now on, and the pull request says so"
            )
            append_event(
                root, "seat.stand-in", slug, {**words, "took": took["seat"], "say": say}
            )
            return {
                "task": slug,
                "name": which,
                "blocked": False,
                **took,
                "from": STAND_IN,
                "for": line,
                "error": kind,
                "say": say,
            }
        # the block first: a state `state` refuses (an ended task) leaves no event of a
        # block behind
        written = cmd_state(
            root, slug, "blocked", [call["block"], f"{lem_state.FAILED_SEAT}{which}"]
        )
        append_event(root, "seat.blocked", slug, {**words, "say": call["block"]})
    return {
        "task": slug,
        "name": which,
        "blocked": True,
        "status": "blocked",
        "since": written["since"],
        "failed": line,
        "error": kind,
        "say": call["block"],
    }


def call_head(which: str, line: str, kind: str) -> str:
    """The words of a seat's error, as both the stand-in's line and the
    block's begin."""
    return (
        f"{lem_state.SEAT_NAMES[which]} `{line}` gave an error: "
        f"{lem_state.SEAT_ERRORS[kind]['block']}"
    )


def cmd_seat_again(root: Path, slug: str) -> dict:
    """The owner's go on over a task that a seat's error blocked: the block before it
    comes back (the plan talk's `building`, the merge agent's `open`) under one line for
    each seat it tries again, and `seat.again` ends each stand-in of that seat, so the
    seat the settings name opens. A run of such blocks at the top is gone over together:
    each of their seats is tried again."""
    directory = task_directory(root, slug)
    settings = load(root)
    with state_locked(directory):
        blocks = (
            blocks_of(text_of(directory / "state.md"))
            if (directory / "state.md").is_file()
            else []
        )
        seats: list[str] = []
        count = 0
        for block in blocks:
            named = (
                failed_seat(block["lines"]) if block["status"] == "blocked" else None
            )
            if named is None:
                break
            count += 1
            if named not in seats:
                seats.append(named)
        if not seats:
            now = (
                f"{blocks[0]['status']}: {blocks[0]['lines'][0]}"
                if blocks
                else "with no state"
            )
            raise SettingsError(
                f"the task {slug!r} is {now}, and its newest block has no line "
                f"`{lem_state.FAILED_SEAT}SEAT`: the owner's go on tries again a seat "
                "whose agent gave an error, and this task waits for no such seat"
            )
        before = blocks[count] if count < len(blocks) else None
        if before is None:
            raise SettingsError(
                f"the task {slug!r} has no block before the seat's block to bring "
                "back: write its state by hand"
            )
        tried = [{"name": which, **settings["seats"][which]} for which in seats]
        lines = [
            f"{GO_ON}{lem_state.SEAT_NAMES[seat['name']]} {seat['seat']} is tried again"
            for seat in tried
        ]
        # the lines of the block before, without the lines of an earlier go on, which
        # this one's replace
        kept = [line for line in before["lines"] if not line.startswith(GO_ON)]
        written = cmd_state(root, slug, before["status"], [*lines, *kept], again=True)
        for which, said in zip(seats, lines, strict=True):
            append_event(root, "seat.again", slug, {"seat": which, "say": said})
    return {
        "task": slug,
        "status": before["status"],
        "since": written["since"],
        **tried[0],
        "tried": tried,
        "say": "; ".join(lines),
    }


def resumed_slug(root: Path, slug: str) -> str:
    """The slug of the task a dropped one goes on in: the first slug of its line (the
    task it came from, when it came from one) with the next free number, `gift-note-2`,
    then `gift-note-3`."""
    first = slug
    while (state_root(root) / "tasks" / first / RESUMED_FROM).is_file():
        first = (
            text_of(state_root(root) / "tasks" / first / RESUMED_FROM).strip() or first
        )
    taken = {path.name for path in (state_root(root) / "tasks").iterdir()}
    return next(f"{first}-{n}" for n in range(2, 1000) if f"{first}-{n}" not in taken)


def resumed_reads(
    directory: Path,
) -> tuple[dict[str, tuple[bytes, os.stat_result]], list[str], str | None]:
    """What a resume carries from the dropped task's folder, read whole before anything
    is written: the bytes and the facts of each file of RESUMED_FILES, RESUMED_GLOBS,
    brief.md and media/, by its path in the folder; the folders of media/; and the first
    read that failed, with its error, or None."""
    read: dict[str, tuple[bytes, os.stat_result]] = {}
    folders: list[str] = []

    def one(file: Path) -> str | None:
        path = file.relative_to(directory).as_posix()
        try:
            facts = file.stat()
            if not stat.S_ISREG(facts.st_mode):
                return f"{file} is not a plain file"
            read[path] = (file.read_bytes(), facts)
        except FileNotFoundError:
            # gone since it was listed: only prune removes a file of a dropped task, and
            # it writes the task's summary first, which the second read of the log finds
            return None
        except OSError as error:
            return f"{file} does not read: {error}"
        return None

    names = [
        directory / name
        for name in (*RESUMED_FILES, "brief.md")
        if (directory / name).is_file()
    ]
    names += [
        found for pattern in RESUMED_GLOBS for found in sorted(directory.glob(pattern))
    ]
    media = directory / "media"
    unlisted: list[str] = []
    if media.is_dir():
        for at, inner, files in os.walk(
            media,
            followlinks=True,
            onerror=lambda error: unlisted.append(
                f"{error.filename} does not list: {error}"
            ),
        ):
            folders.append(Path(at).relative_to(directory).as_posix())
            inner.sort()
            names += [Path(at) / name for name in sorted(files)]
    if unlisted:
        return read, folders, unlisted[0]
    for file in names:
        failed = one(file)
        if failed:
            return read, folders, failed
    return read, folders, None


def summarized_refusal(log: list[dict], slug: str, ask: str) -> None:
    """The refusal of a resume of SLUG once the log holds its summary: the events it
    would carry are gone."""
    if any(
        event.get("task") == slug and event.get("event") == SUMMARY for event in log
    ):
        raise SettingsError(
            f"the events of {slug!r} (its approved criteria, the personas' read, its "
            f"decisions' events) became one summary event past {KEEP_KEY} (nothing of "
            "it was logged for that many days), so a resumed task would start with "
            f"none of them. A new task with its ask is the way on: type\n/lem {ask}",
        )


def resumed_files(names: list[str], *, notes: bool) -> list[str]:
    """Of NAMES, the files of a dropped task's directory, the ones its resume copies
    into the new task: RESUMED_FILES and RESUMED_GLOBS, or with NOTES, for a task the
    release stop blocked, the documents and the ticket alone (RESUMED_NOTES)."""
    kept = RESUMED_NOTES if notes else RESUMED_FILES
    return sorted(
        name
        for name in set(names)
        if name in kept
        or any(fnmatch.fnmatchcase(name, pattern) for pattern in RESUMED_GLOBS)
    )


def write_resumed(
    target: Path,
    carried: dict[str, tuple[bytes, os.stat_result]],
    folders: list[str],
    *,
    notes: bool,
) -> None:
    """Write into TARGET what `resumed_files` chooses of the files a resume read
    (`resumed_reads`), and the pictures of `media/` with its folders, each file as it
    was read, with its mode and its times, as a copy keeps them."""
    chosen = set(
        resumed_files([path for path in carried if "/" not in path], notes=notes)
    )
    for folder in folders:
        (target / folder).mkdir(parents=True, exist_ok=True)
    for path, (data, facts) in carried.items():
        if path not in chosen and not path.startswith("media/"):
            continue
        (target / path).write_bytes(data)
        (target / path).chmod(stat.S_IMODE(facts.st_mode))
        os.utime(target / path, ns=(facts.st_atime_ns, facts.st_mtime_ns))


def went_on_in(root: Path, slug: str) -> str | None:
    """The task a dropped task SLUG went on in already (its `resumed-from.txt` names
    SLUG), or None."""
    return next(
        (
            path.parent.name
            for path in sorted((state_root(root) / "tasks").glob(f"*/{RESUMED_FROM}"))
            if text_of(path).strip() == slug
        ),
        None,
    )


def has_branch(main: Path, name: str | None) -> bool:
    """Whether the checkout MAIN has the local branch NAME."""
    return (
        name is not None
        and subprocess.run(
            [
                "git",
                "-C",
                str(main),
                "rev-parse",
                "--verify",
                "--quiet",
                f"refs/heads/{name}",
            ],
            capture_output=True,
            text=True,
            check=False,
        ).returncode
        == 0
    )


def open_resumed(
    root: Path,
    settings: dict,
    main: Path,
    slug: str,
    new: str,
    branch: str | None,
    source: str | None,
    ticket: str | None,
) -> Path:
    """The folder of NEW, the task that a resume of the dropped task SLUG opens, made
    with its `reports/`. It refuses a folder that is there already and a BRANCH that
    origin has; the TICKET of SLUG, when it has one, goes on with NEW; and BRANCH is cut
    from SOURCE in the checkout MAIN when SOURCE is given."""
    target = state_root(root) / "tasks" / new
    if target.exists():
        raise SettingsError(
            f"{target} exists already: no task is resumed into another task's folder"
        )
    taken_on_remote(root, new, branch)
    claim: contextlib.AbstractContextManager = contextlib.nullcontext()
    if ticket is not None:
        # the ticket goes on with the work, as for a new task: refused while another
        # task holds it, and the dropped task's mark moves to the new slug, and back to
        # it when git refuses the branch
        claim = held_ticket(
            root,
            new,
            ticket,
            read_tasks(root, settings),
            (settings["tracker"] or {}).get("kind"),
            succeeds=slug,
        )
    with claim:
        if source is not None:
            made = subprocess.run(
                ["git", "-C", str(main), "branch", "--no-track", str(branch), source],
                capture_output=True,
                text=True,
                check=False,
            )
            if made.returncode != 0:
                raise SettingsError(
                    f"git could not make {branch} from {source}: "
                    f"{(made.stderr or made.stdout).strip()}"
                )
    (target / "reports").mkdir(parents=True)
    return target


def resume_as_request(
    root: Path,
    slug: str,
    directory: Path,
    ask: str,
    stops: list[dict],
    carried: dict[str, tuple[bytes, os.stat_result]],
    folders: list[str],
) -> dict:
    """The resume of a dropped task that the release stop blocked (STOPS, its
    `release.stop` events, oldest first), with the files the resume read of it (CARRIED,
    FOLDERS): a new request on this release, which reads no record of the old one. Its
    branch is cut from the branch the newest stop named (git's own name for it at the
    stop, lem_release.branch_of), and with none, or one git no longer has, the new task
    starts from the base. Its directory gets the notes (RESUMED_NOTES), its ask, its own
    mark and `resumed-from.txt`, and no state: its session opens as a new task's does
    (`serve.py:act_start`) and takes the shape anew, with the old criteria.md as the
    proposal of its criteria."""
    again = went_on_in(root, slug)
    if again:
        raise SettingsError(
            f"the dropped task {slug!r} goes on in {again!r} already: "
            f"`lem project resume {again}` when that one is parked or dropped too"
        )
    settings = load(root)
    main = main_checkout(root)
    new = resumed_slug(root, slug)
    old = next(
        (
            stop.get("branch")
            for stop in reversed(stops)
            if isinstance(stop.get("branch"), str) and stop.get("branch")
        ),
        None,
    )
    exists = has_branch(main, old)
    # the type of the old branch's name (`fix/invoice-totals`), since the old state's
    # type line is a record of a release two back; the new session takes the type anew,
    # and keeps this branch
    first = old.split("/", 1)[0] if exists and old is not None and "/" in old else None
    branch = f"{first if first in TYPES else 'feat'}/{new}" if exists else None
    ticket = (
        text_of(directory / "ticket.txt").strip()
        if (directory / "ticket.txt").is_file()
        else None
    )
    target = open_resumed(
        root, settings, main, slug, new, branch, old if exists else None, ticket
    )
    try:
        lem_release.mark(target, main)
    except ValueError as error:
        raise SettingsError(str(error)) from None
    (target / "ask.txt").write_text(ask + "\n", encoding="utf-8")
    write_resumed(target, carried, folders, notes=True)
    (target / RESUMED_FROM).write_text(slug + "\n", encoding="utf-8")
    gone = (
        f"the branch {old} is gone"
        if old
        else f"git named no branch of {slug} when Lem stopped it"
    )
    return {
        "task": new,
        "resumed": "request",
        "from": slug,
        "branch": branch,
        "from_branch": old if exists else None,
        "missing": None if exists else old,
        "status": None,
        "next": f"lem session open {new} --why new",
        "says": (
            f"{slug} stays dropped; {new} is a new request on this release, from the "
            f"notes {slug} left and "
        )
        + (
            f"the commits of {old}, on {branch}"
            if exists
            else f"the base branch, since {gone}"
        )
        + (
            f": `lem session open {new} --why new` opens its session, "
            "which takes its shape anew"
        ),
    }


def cmd_resume(root: Path, slug: str) -> dict:
    """The owner's word to go on with a task he put aside: a parked one comes back as it
    was, and a dropped one goes on in a new task that starts from its files and its
    branch. A dropped task whose events became its summary (SUMMARY) is refused: the
    events a resumed task carries over are gone, and so are the files, since prune keeps
    only its small record. A dropped task the release stop blocked goes on as a new
    request (`resume_as_request`)."""
    directory = task_directory(root, slug)
    blocks = (
        blocks_of(text_of(directory / "state.md"))
        if (directory / "state.md").is_file()
        else []
    )
    now = blocks[0]["status"] if blocks else None
    if now in (PARKED, "dropped"):
        # a parked task two releases back stops before it is brought back; a dropped one
        # passes, since its way on is a new task (lem_release)
        stopped = lem_release.check(directory, passes=now == "dropped")
        if stopped:
            raise SettingsError(stopped)
    if now == PARKED:
        before = next((block for block in blocks if block["status"] != PARKED), None)
        if before is None:
            raise SettingsError(
                f"the task {slug!r} has no block before its park to bring back: "
                "write its state by hand"
            )
        written = cmd_state(root, slug, before["status"], before["lines"], resumed=True)
        breaker = re.fullmatch(
            r"breaker ([1-9]\d*) waits for the owner", before["lines"][0]
        )
        return {
            "task": slug,
            "resumed": "parked",
            "status": before["status"],
            "line": before["lines"][0],
            "since": written["since"],
            "breaker": int(breaker[1]) if breaker else None,
            "says": f"{slug} goes on in its own worktree from where it was put aside",
        }
    if now != "dropped":
        raise SettingsError(
            (
                f"the task {slug!r} is {now or 'new'}: `resume` takes a parked "
                "task or a dropped one. "
            )
            + (
                (
                    "An ended task stays ended, and new work for it is "
                    "a new ask (`/lem new`)"
                )
                if now in ENDED
                else "This one goes on as it is"
            ),
        )
    # The log, then every file the new task takes, then the log again. Prune writes a
    # task's summary before it removes any file of it, so a second read with no summary
    # comes after reads of files that no removal had reached; the old branch and the
    # events carried over come from that second read. A summary in the first read
    # refuses before any file is read, so a file that prune could not remove and that
    # does not read meets the same refusal; a read that fails stops the resume before
    # any write.
    ask = (
        text_of(directory / "ask.txt").strip()
        if (directory / "ask.txt").is_file()
        else (ask_of(directory) or slug)
    )
    summarized_refusal(
        log_events(
            root, "resume reads the task's events from the log, so it made nothing"
        ),
        slug,
        ask,
    )
    carried_files, media_folders, failed = resumed_reads(directory)
    log = log_events(
        root, "resume reads the task's events from the log, so it made nothing"
    )
    summarized_refusal(log, slug, ask)
    if failed:
        raise SettingsError(
            f"resume reads every file it carries before it writes, and {failed}, so it "
            "made nothing: make it readable, then resume again"
        )

    # a task the release stop blocked goes on as a new request; it reads no record of
    # the old one
    stops = [
        event
        for event in log
        if event.get("task") == slug and event.get("event") == lem_release.STOP
    ]
    if stops:
        return resume_as_request(
            root, slug, directory, ask, stops, carried_files, media_folders
        )

    def carried_text(name: str) -> str:
        try:
            return carried_files[name][0].decode("utf-8")
        except UnicodeDecodeError as error:
            raise SettingsError(
                f"{directory / name} is not UTF-8 text (byte {error.start} does not "
                "read); save it as UTF-8"
            ) from error

    lines = (
        [
            json.loads(line)
            for line in lem_state.jsonl_lines(carried_text("decisions.jsonl"))
            if line.strip()
        ]
        if "decisions.jsonl" in carried_files
        else []
    )
    helped = {
        line.get("breaker")
        for line in lines
        if line.get("kind") == "taken" and "breaker" in line
    }
    breaker = next(
        (
            line
            for line in reversed(lines)
            if line.get("kind") == "breaker" and line["id"] not in helped
        ),
        None,
    )
    if breaker is None or "handoff.md" not in carried_files:
        raise SettingsError(
            f"the task {slug!r} was dropped with no breaker that waits and its handoff "
            "beside it, so there is no talk to go back to: new work for it is a new "
            "ask (`/lem new`), which may name its branch",
        )
    again = went_on_in(root, slug)
    if again:
        raise SettingsError(
            f"the dropped task {slug!r} goes on in {again!r} already: "
            f"`lem project resume {again}` when that one is parked or dropped too"
        )
    settings = load(root)
    main = main_checkout(root)
    new = resumed_slug(root, slug)
    typed = type_of(text_of(directory / "state.md"))
    kind = typed["type"] if typed else "feat"
    branch = f"{kind}/{new}"
    # the old branch, as the newest state event that saw the task's worktree named it
    old = next(
        (
            event.get("branch")
            for event in reversed(log)
            if event.get("event") == "task.state"
            and event.get("task") == slug
            and event.get("branch")
        ),
        None,
    )
    exists = has_branch(main, old)
    ticket = (
        carried_text("ticket.txt").strip() if "ticket.txt" in carried_files else None
    )
    target = open_resumed(
        root, settings, main, slug, new, branch, old if exists else None, ticket
    )
    (target / "ask.txt").write_text(ask + "\n", encoding="utf-8")
    write_resumed(target, carried_files, media_folders, notes=False)
    (target / RESUMED_FROM).write_text(slug + "\n", encoding="utf-8")
    worktree = (
        main
        / Path(settings["places"]["worktrees"]["path"]).relative_to(root.resolve())
        / new
    )
    if "brief.md" in carried_files:
        # the old brief with this task's own lines: a fresh lead reads where it works
        # from it
        own = {
            "task": new,
            "branch": branch,
            "worktree": str(worktree),
            "task directory": str(target),
        }
        rows = [
            f"{row.split(':', 1)[0]}: {own[row.split(':', 1)[0]]}"
            if row.split(":", 1)[0] in own
            else row
            for row in carried_text("brief.md").splitlines()
        ]
        (target / "brief.md").write_text(
            "\n".join(
                [
                    *rows,
                    (
                        f"resumed from: {slug}; read handoff.md and "
                        f"{breaker.get('document') or 'the breaker document'} in "
                        "the task directory first"
                    ),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
    # In the log's own order, each with the time it had (`was_at`, the first task's time
    # for a task resumed twice): the landing compares his approval with a read by those
    # times, and finds his word to skip a read before the approval that followed it.
    carried = {
        *RESUMED_EVENTS,
        *(f"decision.{kind}" for kind in ("taken", "breaker", "criterion")),
    }
    for event in log:
        if (
            event.get("task") == slug
            and isinstance(event.get("event"), str)
            and event["event"] in carried
        ):
            append_event(
                root,
                event["event"],
                new,
                {
                    **{
                        key: value
                        for key, value in event.items()
                        if key not in ("ts", "event", "task", "was_at")
                    },
                    "from": slug,
                    "was_at": event.get("was_at") or event["ts"],
                },
            )
    try:
        made_tree = cmd_worktree(root, settings, new, branch)
    except SettingsError as error:
        # the task is whole without its worktree's last step (a `checks.setup` that
        # failed, or git): its state goes on record, so that it waits as the resumed
        # task it is, and the error says what is left
        cmd_state(
            root,
            new,
            "held",
            [
                f"breaker {breaker['id']} waits for the owner",
                f"resumed from {slug}, which was dropped",
                *([f"type: {kind}, because {typed['why']}"] if typed else []),
            ],
        )
        raise SettingsError(
            f"{slug} goes on in {new}, which is held by its breaker {breaker['id']} as "
            f"a resumed task should be, and its worktree is not whole: {error}"
        ) from None
    written = cmd_state(
        root,
        new,
        "held",
        [
            f"breaker {breaker['id']} waits for the owner",
            f"resumed from {slug}, which was dropped",
            *([f"type: {kind}, because {typed['why']}"] if typed else []),
        ],
    )
    return {
        "task": new,
        "resumed": "dropped",
        "from": slug,
        "branch": branch,
        "from_branch": old if exists else None,
        "worktree": made_tree["worktree"],
        "breaker": breaker["id"],
        "status": "held",
        "since": written["since"],
        "says": f"{slug} stays dropped; {new} goes on from its handoff and "
        + (
            f"the commits of {old}"
            if exists
            else f"the base branch, since the branch {old or 'of ' + slug} is gone"
        ),
    }


def type_line(line: str) -> dict | None:
    """The type of the request, when the line names one: `type: fix, because the total
    is wrong today`. The status and the board read it, so a line that starts with
    `type:` has this form."""
    text = line.strip()
    if not text.startswith("type:"):
        return None
    found = TYPE_LINE.fullmatch(text)
    kind = found["type"] if found else text.removeprefix("type:").strip()
    if kind not in TYPES:
        raise SettingsError(
            f"{kind!r} is not a type of request{nearest(kind, TYPES)}; "
            "a type line reads `type: TYPE, because WHY`, "
            f"with TYPE one of {', '.join(TYPES)}"
        )
    if not found or not found["why"]:
        raise SettingsError(
            f"the line {text!r} names the type without its reason: "
            f"write it as `type: {kind}, because ...`"
        )
    return {"type": kind, "why": found["why"].strip()}


def answered_form(root: Path, directory: Path, slug: str) -> None:
    """A task is answered only when it has something to show: the investigation's report
    in its directory, and a record of it whose call ends the task (a question answered,
    a bug that is none)."""
    if not (directory / "investigation.md").is_file():
        raise SettingsError(
            f"the task {slug!r} has no investigation.md in its directory: "
            "an answered task ends with its report; write the "
            "investigator's report there first",
        )
    found = newest_events(root, "investigation").get(slug)
    if not found or found.get("call") not in ANSWERING:
        said = f"its newest says {found.get('call')!r}" if found else "it has none"
        raise SettingsError(
            f"the task {slug!r} is answered only after a record whose call is "
            f"not-a-bug or answer (`log {slug} investigation ...`); {said}",
        )


def investigation_form(fields: dict) -> None:
    """What the investigation of a fix or of a question found, which Lem writes after it
    reads the report: the type, the call that sets the next path, one line (the cause,
    the answer, or what was tried), the cause's place, and for a fix whether the bug
    was reproduced."""
    form = (
        "investigation takes type=fix|question call=CALL line=TEXT [where=PATH:SYMBOL] "
        "[reproduced:=true|false, for a fix]"
    )
    allowed = {"type", "call", "line", "where", "reproduced"}
    if not {"type", "call", "line"} <= set(fields) <= allowed:
        raise SettingsError(
            f"{form}, and nothing else; this one has "
            f"{', '.join(sorted(fields)) or 'no field'}"
        )
    kind, call = fields["type"], fields["call"]
    if kind not in CALLS:
        raise SettingsError(f"{form}: type is fix or question, not {kind!r}")
    if call not in CALLS[kind]:
        raise SettingsError(
            f"{form}: call is small, full, not-a-bug or not-reproduced for a fix, and "
            f"answer for a question; this one is {call!r} for a {kind}"
        )
    if (
        not isinstance(fields["line"], str)
        or not fields["line"].strip()
        or "\n" in fields["line"]
    ):
        raise SettingsError(
            f"{form}: line is one line of text: the cause, the answer, "
            "or what was tried"
        )
    if "where" in fields and (
        not isinstance(fields["where"], str) or not fields["where"].strip()
    ):
        raise SettingsError(
            f"{form}: where is the cause's file and symbol, as path:symbol"
        )
    if kind == "question" and "reproduced" in fields:
        raise SettingsError(
            f"{form}: reproduced is a fix's; the investigation of a question answers "
            "it and reproduces nothing"
        )
    if kind == "fix":
        if not isinstance(fields.get("reproduced"), bool):
            raise SettingsError(
                f"{form}: a fix's record says whether the bug was reproduced, as "
                "reproduced:=true or reproduced:=false, written with :="
            )
        if call in ("small", "full") and not fields.get("where"):
            raise SettingsError(
                f"{form}: a plain cause has a place: where names the "
                "cause's file and symbol"
            )
        if call == "not-reproduced" and fields["reproduced"]:
            raise SettingsError(
                f"{form}: not-reproduced is a bug that was not reproduced, "
                "and this record says it was"
            )


def cmd_log(root: Path, slug: str, event: str, pairs: list[str]) -> None:
    """Append one event about a task; `state` is the only writer of task.state."""
    task_directory(root, slug)
    if event == "task.state":
        raise SettingsError(
            "task.state is written by `lem project state`, "
            "which also writes the state block"
        )
    if event == SUMMARY:
        raise SettingsError(
            f"{SUMMARY} is written by `lem project prune` only, in place of the events "
            f"of an ended task that nothing happened in for {KEEP_KEY} days"
        )
    if event in SEAT_EVENTS:
        raise SettingsError(
            f"{event} is written by `lem project seat-failed` and "
            "`lem project seat-again` only, with the block they write: "
            "a stage that saw a seat's agent give an error runs `lem project "
            f"seat-failed {slug} SEAT --seat LINE --error KIND`"
        )
    if event in ("task.mode", OWNER):
        raise SettingsError(
            f"{event} is written by `lem project owner` and `task-dir --night` only: "
            "the owner's status is his words, kept in the machine's mark and never in "
            "a repository's log, and a night's mark is the night's"
        )
    fields: dict[str, Any] = {}
    for pair in pairs:
        key, separator, raw = pair.partition("=")
        typed = key.endswith(":")
        key = key.removesuffix(":")
        if not separator or not key:
            raise SettingsError(f"{pair!r} is neither key=value nor key:=json")
        if key in fields or key in ("ts", "event", "task"):
            raise SettingsError(
                f"field {key!r} is given twice or is one the log sets itself"
            )
        try:
            fields[key] = json.loads(raw) if typed else raw
        except json.JSONDecodeError as error:
            raise SettingsError(f"{key!r} is not JSON ({error}): {raw!r}") from error
    if event in STARTS:
        start_form(event, fields)
    if event == "plan.talk.start":
        talk_start_form(fields)
    if event == "plan.talk":
        talk_form(fields)
        # the bound its rules give, beside the record, so that a reader says when the
        # talk went over it
        fields["bound"] = TURNS_PER_QUESTION * fields["questions"] + TURNS_AROUND
    if event == "criteria.read":
        read_form(fields)
    if event == "investigation":
        investigation_form(fields)
    print(json.dumps(append_event(root, event, slug, fields)))


# A cast has two personas or more, and a split is between two model families.
LEAST_PERSONAS = 2
SPLIT_FAMILIES = 2


def read_form(fields: dict) -> None:
    """The personas' read of the criteria is read by the landing, so it has one form:
    who ran it, how many personas were asked and how many answered, the model families
    that answered, each source that did not answer and why, how many criteria were read
    and flagged, whether the families split, and the digest of the criteria it
    read (`lem criteria digest`)."""
    form = (
        'criteria.read takes by=lem|lead asked:=N answered:=N families:=\'["FAMILY", '
        '...]\' silent:=\'[{"name": SOURCE, "why": WHY}, ...]\' criteria:=N '
        "flagged:=N split:=true|false digest=DIGEST"
    )
    counts = ("asked", "answered", "criteria", "flagged")
    if set(fields) != {"by", "families", "silent", "split", "digest", *counts}:
        raise SettingsError(
            f"{form}, and nothing else; this one has "
            f"{', '.join(sorted(fields)) or 'no field'}"
        )
    if fields["by"] not in ("lem", "lead"):
        raise SettingsError(
            f"{form}: by is lem, when Lem ran the read in its session, or lead, when "
            "the task's lead ran it"
        )
    if not all(
        isinstance(fields[key], int)
        and not isinstance(fields[key], bool)
        and fields[key] >= 0
        for key in counts
    ):
        raise SettingsError(
            f"{form}: each N is a whole number, written with := so that it stays one"
        )
    families = fields["families"]
    if (
        not isinstance(families, list)
        or not all(isinstance(name, str) and name.strip() for name in families)
        or len(set(families)) != len(families)
        or (fields["answered"] and not families)
    ):
        raise SettingsError(
            f"{form}: families is the list of the model families that answered, each "
            'named once, as in families:=\'["opus", "sol"]\''
        )
    silent = fields["silent"]
    if not isinstance(silent, list) or not all(
        isinstance(item, dict)
        and set(item) == {"name", "why"}
        and all(isinstance(value, str) and value.strip() for value in item.values())
        for item in silent
    ):
        raise SettingsError(
            f'{form}: silent is a list of {{"name": ..., "why": ...}}, one for each '
            "source that did not answer; [] when every one did"
        )
    if not isinstance(fields["split"], bool):
        raise SettingsError(
            f"{form}: split is true when the two families answered a criterion "
            "differently, false otherwise, written with :="
        )
    if not isinstance(fields["digest"], str) or not re.fullmatch(
        r"[0-9a-f]{12}", fields["digest"]
    ):
        raise SettingsError(
            f"{form}: digest is the twelve characters `lem criteria digest` prints for "
            "the criteria that were read"
        )
    # every project's cast has two people or more
    if fields["asked"] < LEAST_PERSONAS:
        raise SettingsError(f"{form}: a read asks two personas at the least")
    if fields["answered"] > fields["asked"]:
        raise SettingsError(
            f"{form}: answered is at most asked; 0 is a read in which nobody answered"
        )
    # A read in which nobody answered is written down too, and started once more: the
    # landing counts two in a row as the criteria going on unread, and the request as
    # not green.
    if fields["answered"] == 0 and (
        families
        or fields["flagged"]
        or fields["split"]
        or len(silent) < fields["asked"]
    ):
        raise SettingsError(
            f"{form}: a read in which nobody answered has families:='[]', flagged:=0 "
            "and split:=false, and silent names each source that was asked, one for "
            "each persona at the least, with why",
        )
    if fields["answered"] < fields["asked"] and not silent:
        raise SettingsError(
            f"{form}: when fewer answered than were asked, silent names each source "
            "that did not, with why"
        )
    if fields["criteria"] < 1 or fields["flagged"] > fields["criteria"]:
        raise SettingsError(
            f"{form}: a read has one criterion at the least, "
            "and no more criteria flagged than it read"
        )
    if fields["split"] and len(families) < SPLIT_FAMILIES:
        raise SettingsError(
            f"{form}: a split is between two model families, and families names one"
        )


# The start of each stage that logs its end and had no start, so that the board draws a
# span from the one to the other (the owner's pick of 2026-11-17: "each stage logs its
# start, and the card becomes exact"). Event -> (its form, the fields it takes, the
# values each may have). An agent logs the first eight where its stage text says;
# land.py logs the last three itself. The end of each: the interview at `interview.end`,
# the end of its questions, which starts Lem's writing of the criteria, which ends at
# the first `read.skip.asked`, `criteria.read.start` or `criteria.approved` after it;
# the skip question at his decision or at `criteria.read.start`; the scout at `scout`,
# the read at `criteria.read`, an investigation at `investigation`, a builder's job at
# the next state block or step of the landing after it, the polish pass at `polish`, the
# checks at `gate.end`, and the review at `review`.
BUILDER_JOBS = (
    "the small change",
    "the repair of a conflict with the base",
    "the repair of a failed check",
    "the fix of a review's findings",
    "the removal of the task's item",
)
TASK_JOB = re.compile(r"task [1-9]\d* of [1-9]\d*")
STARTS: dict[str, tuple[str, dict[str, tuple[str, ...] | None]]] = {
    "interview.start": ("interview.start takes nothing", {}),
    "interview.end": (
        "interview.end, the end of the questions to the owner, takes nothing",
        {},
    ),
    "scout.start": ("scout.start takes nothing", {}),
    "scout": ("scout, the end of the scout's read, takes nothing", {}),
    "read.skip.asked": (
        (
            "read.skip.asked, the question whether the owner skips the personas' read, "
            "takes nothing"
        ),
        {},
    ),
    "criteria.read.start": (
        "criteria.read.start takes by=lem|lead, and nothing else",
        {"by": ("lem", "lead")},
    ),
    "investigation.start": (
        "investigation.start takes type=fix|question, and nothing else",
        {"type": ("fix", "question")},
    ),
    "builder.start": (
        (
            "builder.start takes job=JOB, and nothing else: `task N of M`, or one of "
            f"{', '.join(BUILDER_JOBS)}; the polish pass logs its own "
            "start (`lem land polish`)"
        ),
        {"job": None},
    ),
    "polish.start": (
        "polish.start takes before=TIP, and land.py polish writes it",
        {"before": None},
    ),
    "gate.start": (
        "gate.start takes tip=TIP commands:=N, and land.py checks writes it",
        {"tip": None, "commands": None},
    ),
    "review.start": (
        (
            "review.start takes attempt:=N floor=read|round|full, "
            "and land.py read writes it"
        ),
        {"attempt": None, "floor": ("read", "round", "full")},
    ),
}


def start_form(event: str, fields: dict) -> None:
    """A stage's start has one form, so that the board can draw its span from it to
    its end."""
    form, wants = STARTS[event]
    if set(fields) != set(wants):
        raise SettingsError(
            f"{form}; this one has {', '.join(sorted(fields)) or 'no field'}"
        )
    for key, allowed in wants.items():
        value = fields[key]
        if allowed is not None and value not in allowed:
            raise SettingsError(f"{form}; {key} is {value!r}")
    if event == "builder.start" and not (
        fields["job"] in BUILDER_JOBS
        or (isinstance(fields["job"], str) and TASK_JOB.fullmatch(fields["job"]))
    ):
        raise SettingsError(f"{form}; job is {fields['job']!r}")
    if event in ("polish.start", "gate.start") and not (
        isinstance(fields.get("before", fields.get("tip")), str)
        and re.fullmatch(r"[0-9a-f]{7,40}", fields.get("before", fields.get("tip")))
    ):
        raise SettingsError(f"{form}; the tip is a commit, as git names it")
    for key in ("commands", "attempt"):
        if key in fields and not (
            isinstance(fields[key], int)
            and not isinstance(fields[key], bool)
            and fields[key] >= 1
        ):
            raise SettingsError(
                f"{form}; {key} is a whole number, 1 or more, written with :="
            )


def talk_start_form(fields: dict) -> None:
    """The start of a plan talk, written when the reviewer's seat opens, so that the
    board can draw the talk's minutes from two events: it names the reviewer, and
    nothing else."""
    if (
        set(fields) != {"reviewer"}
        or not isinstance(fields["reviewer"], str)
        or not fields["reviewer"].strip()
    ):
        raise SettingsError(
            "plan.talk.start takes reviewer=AGENT, and nothing else; "
            f"this one has {', '.join(sorted(fields)) or 'no field'}"
        )


# The most turns a talk of N questions has by its rules: the reviewer's list, two
# answers of the defender and two of the reviewer on each question (a question that
# holds a second time stops), and the close. Derived from the rules of `stages/talk.md`,
# in a Fable second opinion (2026-11-16); no talk under these rules has been measured
# yet. It is the defender's to keep, not a check of the record: a talk that ran longer
# is written as it ran, and `log` adds the bound to it, so the pull request and the
# board can say that it went over.
TURNS_PER_QUESTION = 4
TURNS_AROUND = 2


def talk_form(fields: dict) -> None:
    """A plan talk's record is read by the landing, so it has one form: who argued the
    plan with its defender, how many turns the talk had, how many questions the
    reviewer's first list held, how many of them it settled and left open, how many the
    lead repaired, how many of the open ones are a design choice (a question that held a
    second time), how many questions were raised after the list and not argued, and
    three counts of Fable's check for a layer of patches (2026-11-16): `root`, the
    repairs that changed a decision of the plan; `layer`, the repairs that put a
    mechanism over a decision the plan cites (a criterion, a ruling, existing code) and
    stayed; and `shared`, the decisions two questions named."""
    form = (
        "plan.talk takes reviewer=AGENT turns:=N questions:=N settled:=N open:=N "
        "repaired:=N design:=N unargued:=N root:=N layer:=N shared:=N"
    )
    counts = (
        "turns",
        "questions",
        "settled",
        "open",
        "repaired",
        "design",
        "unargued",
        "root",
        "layer",
        "shared",
    )
    if set(fields) != {"reviewer", *counts}:
        raise SettingsError(
            f"{form}, and nothing else; this one has "
            f"{', '.join(sorted(fields)) or 'no field'}"
        )
    if not isinstance(fields["reviewer"], str) or not fields["reviewer"].strip():
        raise SettingsError(
            f"{form}: reviewer names the agent that argued the plan with its defender"
        )
    if not all(
        isinstance(fields[key], int)
        and not isinstance(fields[key], bool)
        and fields[key] >= 0
        for key in counts
    ):
        raise SettingsError(
            f"{form}: each N is a whole number, written with := so that it stays one"
        )
    turns, questions = fields["turns"], fields["questions"]
    # A floor against an empty record, not a measure of a good talk. A reviewer that
    # found nothing says so in its first turn, and the defender closes: a talk of no
    # question has those two turns.
    if turns < TURNS_AROUND:
        raise SettingsError(
            f"{form}: a talk has two turns at the least: the reviewer's list, which "
            "may be empty, and the close"
        )
    if questions == 0 and fields["unargued"] and turns <= TURNS_AROUND:
        raise SettingsError(
            f"{form}: a talk of no question and two turns has no turn after the list, "
            "so unargued is 0"
        )
    if fields["settled"] + fields["open"] != questions:
        raise SettingsError(
            f"{form}: each question of the reviewer's first list ends settled or left "
            "open, so settled and open add up to questions"
        )
    if fields["design"] > fields["open"]:
        raise SettingsError(
            f"{form}: a design choice is a question left open because it held a second "
            "time, so design is at most open"
        )
    if fields["repaired"] > questions:
        raise SettingsError(
            f"{form}: repaired counts the questions whose answer changed the plan, so "
            "repaired is at most questions"
        )
    if fields["root"] + fields["layer"] > fields["repaired"]:
        raise SettingsError(
            f"{form}: a repair either changed a decision of the plan (root) or put a "
            "mechanism over a decision with a cite (layer), or neither, so root and "
            "layer add up to at most repaired",
        )
    # No check of the rules themselves: a talk over its bound of turns, or one whose
    # second question on a decision did not close as a design choice, is a fact, and a
    # record refused for it would leave the companion open and the request unproposed
    # for ever.


def ticket_owed(
    status: str | None,
    steps: list[str],
    tracker: dict | None,
    held_by: str | None = None,
) -> list[str]:
    """The steps a ticket still waits for, now that its task has ended. A session may be
    cut off between a task's last state and the tracker, and this is how the next one
    sees it. HELD_BY is the task that holds the ticket now when it is another one
    (`ticket_held_by`): the dropped task a resume went on from owes nothing, since a
    drop comment would tell the issue's readers that work they still get was dropped."""
    if tracker is None or held_by is not None:
        return []
    if status == "landed":
        # the status too: a ticket that an automation of the tracker already moved is
        # written down with no move
        wanted = ["commented", "landed"]
    elif status in RETURNED:
        # the comment of the tracker's "drop" or "answer", and no status: where it goes
        # is the owner's call; and the assignee Lem added at the start goes, since
        # nobody works on the issue now
        wanted = [status, *(["unassigned"] if "assigned" in steps else [])]
    else:
        wanted = []
    return [step for step in wanted if step not in steps]


def proposal(directory: Path) -> dict | None:
    """What `lem land propose` kept for a task: the pull request's address, when there
    is one, and green or the reasons it is not."""
    kept_file = directory / "landing.json"
    if not kept_file.is_file():
        return None
    # every task's record is read here, so one that does not read stops `tasks` for all:
    # the message says how to start that landing over
    way_out = (
        "land.py writes it whole, so something else wrote it. Move it aside, then `lem "
        f'project state {directory.name} ready --start-over "WHY"` and '
        f"`lem land start {directory.name}` start the landing over: "
        "its checks and its review run again"
    )
    try:
        kept = json.loads(kept_file.read_bytes().decode("utf-8"))
    except ValueError as error:
        raise SettingsError(
            f"{kept_file} does not read as JSON ({error}); {way_out}"
        ) from error
    if not isinstance(kept, dict):
        raise SettingsError(
            f"{kept_file} is not an object, as the landing's record is; {way_out}"
        )
    if not kept.get("proposed"):
        return None
    reasons = kept.get("not_green", [])
    # Whether the forge called the pull request conflicting with the base when
    # `lem land merged` last asked, on the head Lem pushed: null when nothing asked, the
    # forge did not know, or the head moved since.
    forge = kept.get("forge") if isinstance(kept.get("forge"), dict) else {}
    pushed = kept.get("pushed") or kept.get("proposed")
    conflicting: dict[object, bool] = {"CONFLICTING": True, "MERGEABLE": False}
    conflict = (
        conflicting.get(forge.get("mergeable"))
        if pushed and forge.get("head") == pushed
        else None
    )
    # the merge agent's review of the proposed tip, and GitHub's refusal of a merge
    # after it
    review = (
        kept.get("merge_review")
        if isinstance(kept.get("merge_review"), dict)
        and kept["merge_review"].get("tip") == kept["proposed"]
        else None
    )
    refused = (
        kept.get("merge_refused")
        if isinstance(kept.get("merge_refused"), dict)
        and kept["merge_refused"].get("tip") == kept["proposed"]
        else None
    )
    return {
        "pull_request": (kept.get("pr") or {}).get("url"),
        "green": not reasons,
        "not_green": reasons,
        "conflict": conflict,
        "merge_review": review,
        "merge_refused": refused,
    }


def events_named(root: Path, *events: str) -> list[dict]:
    """Every event of these names in the event log, in the log's order, oldest first."""
    log, found = state_root(root) / "events.jsonl", []
    if not log.is_file():
        return found
    for number, line in enumerate(lem_state.jsonl_lines(text_of(log)), 1):
        if not any(f'"{event}"' in line for event in events):
            continue
        try:
            record = json.loads(line)
        except ValueError as error:
            raise SettingsError(
                f"{log}:{number} does not read as JSON ({error}); the log is written "
                "by project.py, never by hand"
            ) from error
        if record.get("event") in events:
            found.append(record)
    return found


def newest_events(root: Path, event: str) -> dict[str | None, dict]:
    """Each task's newest event of one name in the event log. A task's lead closes the
    plan talk's pair, and a builder leads the build of a careful or large plan, only on
    the newest `plan.talk`, never on a line that says so; a task's session takes a bug's
    next path on the newest `investigation`."""
    return {record.get("task"): record for record in events_named(root, event)}


# The words of the `task.mode` event with which a night marks its task
# (`task-dir --night`, `stages/night.md`): the one mark that tells a task of the night
# from a day's task.
NIGHT_WORDS = re.compile(r"the night of (\d{4}-\d{2}-\d{2})")
# The `event` of each record of the owner's status, which names no task (`owner`): a
# record of the machine's mark, never of a repository's log, which `log` refuses it.
OWNER = "owner"
# The one event that stands for all the events of an ended task that nothing happened in
# for `state.keep_days` days, which only `prune` writes (`summary_of`): the facts each
# reader of the log read from those events.
SUMMARY = "task.summary"


def nights(modes: list[dict]) -> dict[str | None, str]:
    """The night that opened each task, as its date, from the first `task.mode` event
    Lem wrote in the night's words, or from the task's summary, which keeps that date.
    The owner's "back" later takes neither the date nor the night's span away."""
    found: dict[str | None, str] = {}
    for record in modes:
        if record.get("event") == SUMMARY and isinstance(record.get("night"), str):
            found.setdefault(record.get("task"), record["night"])
            continue
        night = (
            NIGHT_WORDS.fullmatch(str(record.get("words", "")))
            if record.get("event") == "task.mode" and record.get("by") == "lem"
            else None
        )
        if night:
            found.setdefault(record.get("task"), night[1])
    return found


def owner_records() -> list[dict]:
    """Every record of the owner's status in the machine's mark
    (`lem_state.owner_mark`), oldest first: none when no mark is there, which reads as
    him being there. A read never makes the file."""
    try:
        mark = lem_state.owner_mark()
    except lem_state.StateError as error:
        raise SettingsError(str(error)) from error
    if not mark.is_file():
        return []
    found = []
    for number, line in enumerate(lem_state.jsonl_lines(text_of(mark)), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except ValueError as error:
            raise SettingsError(
                f"{mark}:{number} does not read as JSON ({error}); the file is written "
                "by `lem project owner`, never by hand"
            ) from error
        if (
            not isinstance(record, dict)
            or record.get("event") != OWNER
            or not isinstance(record.get("ts"), str)
        ):
            raise SettingsError(
                f"{mark}:{number} is no record of the owner's status; "
                "the file is written by `lem project owner`, never by hand"
            )
        found.append(record)
    return found


def append_owner(root: Path, *, away: bool, words: str) -> dict:
    """Append one record of the owner's status to the machine's mark, made with its
    folder when it is absent. One short line in one write with O_APPEND: two
    repositories that write at once each add their own line whole, so no lock is kept
    beside it."""
    record = {
        "ts": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": OWNER,
        "task": None,
        "away": away,
        "by": "owner",
        "words": words,
        # where he typed it, for a reader of the file; no script acts on it
        "repo": str(main_checkout(root)),
    }
    line = json.dumps(record, ensure_ascii=False) + "\n"
    try:
        data = line.encode("utf-8")
    except UnicodeEncodeError as error:
        raise SettingsError(
            "--words are not UTF-8 text "
            f"({line[max(0, error.start - 20) : error.start]!r} comes before it); "
            "give the owner's words in UTF-8"
        ) from error
    try:
        mark = lem_state.owner_mark()
    except lem_state.StateError as error:
        raise SettingsError(str(error)) from error
    mark.parent.mkdir(parents=True, exist_ok=True)
    handle = os.open(mark, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        os.write(handle, data)
    finally:
        os.close(handle)
    return record


# How many seconds the watch of the mark waits between two looks at it. A guess
# (2026-11-19), not a measurement: an away typed in another repository reaches this
# one's interviews within seconds, and one read of a file of a few lines every 5 seconds
# costs nothing.
OWNER_WATCH_SECONDS = 5


def merged(events: list[dict], marks: list[dict]) -> list[dict]:
    """A repository's events and the records of the owner's mark in one list, in the
    order of `ts`. A `ts` has whole seconds, so the sort is stable over the repository's
    list followed by the mark's: on the same second the repository's events come first,
    and each list keeps its order."""
    return sorted([*events, *marks], key=lambda record: record["ts"])


def owner_now(records: list[dict]) -> dict:
    """The owner's status from the newest `owner` record: there, the default, or away
    since then."""
    newest = next(
        (
            record
            for record in reversed(records)
            if record.get("event") == OWNER and record.get("task") is None
        ),
        None,
    )
    if newest is None or not newest.get("away"):
        return {
            "away": False,
            "since": newest["ts"] if newest else None,
            "words": newest.get("words") if newest else None,
        }
    return {"away": True, "since": newest["ts"], "words": newest.get("words")}


def runs_without_owner(slug: str, records: list[dict], first: str | None) -> list[dict]:
    """The spans in which a task ran without the owner, oldest first, each with the
    words that started it and the words that ended it (`to` is null for a span that runs
    now). A span runs while the owner is away, and while the task's own mark holds: a
    night's. The owner's "back" ends the span his "away" started and never a night's: a
    night's task runs without him until it ends, whatever his status. No span starts
    before `first`, the task's first event, since a task opened while he is away runs
    without him from its opening. `records` are the task marks of the repository's log
    and the records of the machine's mark, in the order of their `ts`."""

    def said(record: dict) -> dict:
        return {"by": record.get("by", "owner"), "words": record.get("words")}

    spans: list[dict] = []
    own: dict | None = None
    away: dict | None = None
    for record in records:
        if record.get("event") == "task.mode" and record.get("task") == slug:
            own = own or record
        elif record.get("event") == OWNER and record.get("task") is None:
            away = (away or record) if record.get("away") else None
        else:
            continue
        start = own or away
        if start and (not spans or spans[-1]["to"] is not None):
            spans.append(
                {
                    "from": max(start["ts"], first or start["ts"]),
                    "to": None,
                    "started": said(start),
                    "ended": None,
                }
            )
        elif not start and spans and spans[-1]["to"] is None:
            if first and record["ts"] < first:
                # an away and a back that both came before the task opened are no span
                # of it
                spans.pop()
            else:
                spans[-1].update(
                    to=max(record["ts"], spans[-1]["from"]), ended=said(record)
                )
    return spans


def type_of(text: str) -> dict | None:
    """The newest type of the request that a block of state.md names (newest
    block first)."""
    for line in text.splitlines():
        try:
            found = type_line(line)
        except SettingsError:
            # state wrote every type line in its form; a line written by hand that is
            # not is no type
            found = None
        if found:
            return found
    return None


# The state lines that tell a task's track (SKILL.md, the lines of a fixed form), as the
# board reads them (lem_board_model's FAST_BUILDER, FAST_GREW): the fast track's one
# builder; the line of a fast task whose builder found that it needs the standard track;
# a lead, which only the standard track has.
FAST_BUILDER = "small change: one builder"
FAST_GREW = re.compile(r"\bthe small change is a full change$")
LEAD_LINE = re.compile(r"lead: (builder|session)\b")
# The state line of a task whose interview waits for the owner (`stages/new.md`, "The
# request", step 8).
INTERVIEW_WAIT = "the interview waits for the owner"
# The state line of a task on the fast track whose one criterion waits for the owner's
# yes before its builder starts: a request someone else wrote, while he is there
# (`stages/new.md`, "The fast track", step 1).
FAST_WAIT = (
    "the criteria wait for the owner: a small change that someone else asked for"
)
# The first line of a `held` block whose order names no task Lem can tell, while he is
# away (step 1 of "The request"), in whatever form the rest of it has: it names no path,
# so its first line comes with the first block after his answer that names one, which
# may take its type line from this block.
ORDER_WAIT = "the order waits for the owner"


def track_of(text: str) -> str | None:
    """The track of a task, `fast` or `standard`, from the newest of its state lines
    that tells it (state.md is newest block first); None while nothing has: an
    investigation before its call, or a task queued before its first builder. Criteria
    that wait for the owner's yes are the standard track's, except the fast track's one
    criterion of a request someone else wrote (`FAST_WAIT`). So is an interview: only
    the standard track has one, also for a task that `/lem standard-track` moved off the
    fast track, whose older block names its one builder."""
    for line in text.splitlines():
        found = STATE_LINE.fullmatch(line.strip())
        said = found["text"] if found else line.strip()
        if said in (FAST_BUILDER, FAST_WAIT):
            return "fast"
        if (
            FAST_GREW.search(said)
            or LEAD_LINE.match(said)
            or said.startswith((CRITERIA_WAIT, INTERVIEW_WAIT))
        ):
            return "standard"
    return None


# The first line of a task's session to the owner (`stages/new.md`, "The request", step
# 8): the type, the criterion or the outcome in his words, the branch, the track with
# its steps and what he must do, composed here from the task's records and printed by
# `state` as `say` for the block that names the task's path. A session says it as it is:
# in three of four real tasks on 2026-11-21 (lem-trial and lem-scratch) a session told
# to say the line in a form the stage gave said "The builder runs now" instead, also
# after the text said it more strongly.
INVESTIGATION_LINE = re.compile(r"investigation: (bug|question)")
AFTER_LINE = re.compile(r"after: (?P<slug>[a-z0-9][a-z0-9-]*)")
# A `queued` block of step 7: the owner's order as its first line, the path its wait
# ends in, and the line of a task put after the one open task that fits his words while
# he was away. The first line reads them, so `state` refuses a line that starts as one
# of them in another form (`fixed_form`); the match of his words is greedy, so a double
# quote of his own stays inside them.
ORDER_LINE = re.compile(r"the owner's order: \"(?P<words>.*)\"")
# The line of a block that is the owner's order (`stages/new.md`, step 7 of "The
# request"), in whatever form the rest has.
ORDER_START = "the owner's order:"
THEN_LINE = re.compile(r"then: (?P<path>the interview|the fast track|the lead)")
THEN_PATHS = {
    "the interview": "interview",
    "the fast track": "fast",
    "the lead": "complete",
}
FITS_LINE = "the one open task that fits his words"
CAREFUL_LINE = re.compile(r"careful:\s*(?P<why>.+)", re.IGNORECASE)
BRANCH_NAME = re.compile(r"[\w][\w./+-]*")
SENTENCE = re.compile(r"(.+?[.!?])(?=\s|$)")
# a code span, kept as it is, or a bold run, whose text is kept without its `**`: the
# `**` a code span names (`src/**/*.py`, `**kwargs`) never opens or closes a run
BOLD_RUN = re.compile(r"(`[^`]*`)|\*\*(?=\S)((?:`[^`]*`|[^`])+?)(?<=\S)\*\*")
FAST_STEPS = "Fast track: one builder, the checks, one read, then the pull request."


def fixed_form(line: str) -> None:
    """Refuse a state line that starts as one of the three lines the first line reads
    (the owner's order, `then:`, the one open task that fits) and is not in its form, so
    that no first line leaves out his order because of how a line was typed. Every other
    line is free."""
    text = line.strip()
    if text.startswith(ORDER_START) and not ORDER_LINE.fullmatch(text):
        raise SettingsError(
            f"the line {text!r} starts as the owner's order and is not in its form: "
            'write it as `the owner\'s order: "HIS WORDS"`, '
            "his words on one line between double quotes"
        )
    if text.startswith("then:") and not THEN_LINE.fullmatch(text):
        raise SettingsError(
            f"the line {text!r} names no path a wait ends in: "
            "write `then: the interview`, `then: the fast track` or `then: the lead`"
        )
    if text.startswith("the one open task") and text != FITS_LINE:
        raise SettingsError(
            f"the line {text!r} is not in its form: write it as `{FITS_LINE}`"
        )
    if text.startswith(lem_state.FAILED_SEAT.strip()) and not FAILED_LINE.fullmatch(
        text
    ):
        raise SettingsError(
            f"the line {text!r} is not in its form: "
            f"write it as `{lem_state.FAILED_SEAT}SEAT`, SEAT one of "
            f"{', '.join(lem_state.SEAT_NAMES)}; `lem project seat-failed` writes it"
        )


def correction(*, fast: bool, task: str | None) -> str:
    """The commands that correct the read, the fast track's two or the standard track's
    one. In the task's own session they need no task; in another session (`task`) each
    names it."""
    named = f" {task}" if task else ""
    commands = [f"/lem standard-track{named}"] if fast else []
    return "Wrong read? " + ", ".join([*commands, f"/lem be-careful{named}"]) + "."


def first_sentence(text: str) -> str:
    """The first sentence of TEXT on one line, without its closing period or colon; the
    whole text when it has no sentence's end."""
    flat = " ".join(text.split())
    found = SENTENCE.match(flat)
    said = (found[1] if found else flat).strip()
    return said[:-1].rstrip() if said.endswith((".", ":")) else said


def in_his_words(text: str) -> str:
    """A sentence as the middle of a line: its first word lower-cased when it is an
    ordinary word with a capital ("The footer says" reads "the footer says"), never a
    name such as README or I."""
    word = text.split(" ", 1)[0]
    if (
        len(word) > 1
        and word[0].isupper()
        and word[1:].isalpha()
        and word[1:].islower()
    ):
        return word[0].lower() + text[1:]
    return text


def criterion_of(text: str) -> str | None:
    """The sentence of the first criterion of a criteria.md (`lem criteria --help`),
    or None."""
    rows = text.splitlines()
    for at, row in enumerate(rows):
        found = re.match(r"1\.\s+(.+)", row)
        if not found:
            continue
        said = [found[1]]
        for more in rows[at + 1 :]:
            # its sentence goes on on the lines indented under it, up to its case, a
            # test line or a chart
            if (
                not more.strip()
                or not more.startswith((" ", "\t"))
                or re.match(r"\s*(\d+\.|[-*+]|```)", more)
            ):
                break
            said.append(more.strip())
        return first_sentence(" ".join(said)) or None
    return None


# A few words: a bold run of no more opens a paragraph as its label, and a paragraph or
# a sentence of no more is no outcome.
FEW_WORDS = 3


def outcome_of(text: str) -> str | None:
    """The first sentence of prose under `## Outcome` in a task.md, or None: a numbered
    story, a list, a chart or a bold label (a few words, or any that ends in a colon:
    "Today:") is no sentence to quote. A bold sentence, on one line or wrapped over
    more, is quoted whole and without its `**`; the `**` inside a code span stays."""
    found = re.search(r"(?m)^##[ \t]+Outcome[ \t]*$", text)
    if not found:
        return None
    paragraph: list[str] = []
    fenced = False
    for row in text[found.end() :].splitlines():
        line = row.strip()
        if line.startswith("```"):
            fenced = not fenced
            continue
        if line.startswith("#"):
            break
        # a line that opens with bold is a label when its bold closes on it within a few
        # words, or ends in a colon inside the bold or right after it; a *** rule opens
        # with no bold; the `**` a code span names never closes the label, as
        # in BOLD_RUN
        label = re.match(r"\*\*((?:`[^`]*`|[^*`])*)\*\*(:?)", line)
        bold = bool(re.match(r"\*\*[^*\s]", line)) and not (
            label
            and (
                len(label[1].split()) <= FEW_WORDS
                or label[1].rstrip().endswith(":")
                or label[2]
            )
        )
        prose = (
            line
            and not fenced
            and (bold or not re.match(r"(\d+\.|[-*+>|!]|\*\*)", line))
        )
        if prose:
            paragraph.append(line)
            continue
        if paragraph and len(" ".join(paragraph).split()) > FEW_WORDS:
            break
        paragraph = []
    said = BOLD_RUN.sub(lambda run: run[1] or run[2], " ".join(paragraph))
    return first_sentence(said) if len(said.split()) > FEW_WORDS else None


def opening_line_facts(
    directory: Path,
    main: Path,
    status: str,
    lines: list[str],
    branch: str | None,
    held: list[str] | None = None,
) -> dict | None:
    """What the first line of a task says, from its records at the moment its first
    block is written, or None for a block that names no path. `lines` are the block's
    lines, its first among them; `branch` is the branch of the task's worktree, when it
    has one; `held` the lines of the hold of an order that named no task (ORDER_WAIT)
    before it, whose type and `careful:` lines stand for a block that has none of
    its own."""

    def file(name: str) -> str:
        return text_of(directory / name) if (directory / name).is_file() else ""

    held = [line.strip() for line in held or []]
    typed = next((found for found in map(type_line, [*lines, *held]) if found), None)
    if typed is None:
        return None
    brief = file("brief.md")
    said = [line.strip() for line in lines]
    investigation = next(
        (found[1] for found in map(INVESTIGATION_LINE.fullmatch, said) if found), None
    )
    after = next(
        (found["slug"] for found in map(AFTER_LINE.fullmatch, said) if found), None
    )
    order = ORDER_LINE.fullmatch(said[0]) if status == "queued" and after else None
    then = (
        next((found["path"] for found in map(THEN_LINE.fullmatch, said) if found), None)
        if status == "queued"
        else None
    )
    if status == "held" and said[0] == INTERVIEW_WAIT:
        path = "interview"
    elif status == "held" and said[0] == FAST_WAIT:
        path = "fast"
    elif status in ("building", "queued") and investigation:
        path = "investigation"
    elif then:
        path = THEN_PATHS[then]
    elif (status in ("building", "queued") and FAST_BUILDER in said) or (
        status == "queued" and "prompts/small.md" in brief
    ):
        path = "fast"
    elif (status == "building" and any(LEAD_LINE.match(line) for line in said)) or (
        status == "queued" and "prompts/lead.md" in brief
    ):
        path = "complete"
    else:
        return None
    brief_rows = [row.strip() for row in brief.splitlines()]
    named = next(
        (
            row.split(":", 1)[1].strip()
            for row in brief_rows
            if row.startswith("branch:")
        ),
        "",
    )
    careful = next(
        (
            found["why"].strip()
            for found in map(CAREFUL_LINE.fullmatch, [*said, *held, *brief_rows])
            if found
        ),
        None,
    )
    ask = " ".join(file("ask.txt").split())
    item = re.fullmatch(r"\S*backlog/\S+\.md", ask)
    quote = criterion_of(file("criteria.md")) if path == "fast" else None
    quote = quote or outcome_of(file("task.md"))
    if not quote and item and (main / ask).is_file():
        title = next(
            (
                row.lstrip("# ").strip()
                for row in text_of(main / ask).splitlines()
                if row.startswith("# ")
            ),
            None,
        )
        quote = title and first_sentence(title)
    # ask.txt keeps the command that carried his words
    # (`/lem After the gift note: ...`); the quote is his words alone
    words = re.sub(r"^/lem\s+", "", ask)
    quote = quote or (first_sentence(words) if words else None)
    return {
        "type": typed["type"],
        "path": path,
        "quote": quote and in_his_words(quote),
        "branch": named if BRANCH_NAME.fullmatch(named) else branch,
        "careful": careful,
        "after": after,
        "slug": directory.name,
        "order": order["words"] if order else None,
        "fits": FITS_LINE in said,
        "plan": "stop after the plan: yes" in brief_rows,
        "someone_else": "request by: someone else" in brief_rows,
        # a first block before the builder's: on the fast track his yes to someone
        # else's criterion comes first
        "before_builder": status != "building",
        "stands_in": (
            "the ticket"
            if (directory / "ticket.txt").is_file()
            else "the backlog item"
            if item
            else "the investigation's report"
            if (directory / "investigation.md").is_file()
            else "your request"
        ),
        "question": investigation == "question" or typed["type"] == "question",
    }


def compose_opening_line(facts: dict, task: str | None = None) -> str:
    """The first line itself, in the forms of `stages/new.md`, "The request", step 8.
    With `task`, the line as another session says it: the task named first, and its name
    in each command."""
    words = [f"{task} ·"] if task else []
    if facts.get("careful"):
        why = facts["careful"].rstrip(".")
        words.append(f"Careful: {why}.")
    # his words between double quotes, with a double quote of his own as a single one
    quote = facts["quote"].replace('"', "'") if facts.get("quote") else None
    words.append(f'{facts["type"]}: "{quote}".' if quote else f"{facts['type']}.")
    if facts.get("branch"):
        words.append(f"Branch {facts['branch']}.")
    path = facts["path"]
    # another session speaks of the task's session, where the interview runs and the
    # answer comes
    here, teller = (
        ("in its own session", "Then its session tells you")
        if task
        else ("here", "Then I tell you")
    )
    standard = (
        "Standard track, because you asked for its plan:"
        if facts.get("plan")
        else "Standard track:"
    )
    then = (
        "After that a lead writes the plan and stops for you to read it."
        if facts.get("plan")
        else "After that it runs to the pull request without you."
    )
    # A block with an `after:` line waits on every path: the wait comes before the steps
    # of the track, which run when it ends, and those steps follow the `after:` line
    # ("Then ..."). Only what names his order (as you said, the one open task that fits,
    # his word that starts it before that) follows the order line, so a free order line
    # still leaves the wait in the line.
    waiting = bool(facts.get("after"))
    if facts.get("order") is not None:
        start = f'"start {task or facts["slug"]} now" starts it before that.'
        which = (
            f'the one open task that fits "{facts["order"].replace(chr(34), chr(39))}";'
            if facts.get("fits")
            else "as you said;"
        )
        words.append(f"It waits for {facts['after']}, {which} {start}")
    elif waiting:
        words.append(
            f"It waits for {facts['after']}, and starts when that "
            "task lands or is answered."
        )
    if waiting:
        standard = "Then the s" + standard[1:]
    if path == "fast":
        nothing = "Nothing waits for you." if facts.get("order") is None else None
        if facts.get("someone_else"):
            # someone else's request: his yes comes before the builder while he is there
            # (`FAST_WAIT`, or a wait that ends in it); a first block that is the
            # builder's own was approved without him
            nothing = (
                (
                    "Someone else wrote the request, so its criterion waits for your "
                    "yes before the builder starts."
                )
                if facts.get("before_builder")
                else (
                    "Nothing waits for you but the pull request, which calls you: "
                    "you did not approve its criterion."
                )
            )
        steps = "Then the f" + FAST_STEPS[1:] if waiting else FAST_STEPS
        words += [steps, nothing, correction(fast=True, task=task)]
    elif path == "interview":
        now = "" if waiting else " now"
        words += [
            (
                f"{standard} an interview {here}{now}, "
                "then acceptance criteria for your yes."
            ),
            then,
            correction(fast=False, task=task),
        ]
    elif path == "complete":
        read = (
            (
                "a lead writes acceptance criteria, the personas read them, "
                "and they wait for your yes."
            )
            if facts.get("someone_else")
            else "a lead writes acceptance criteria, and the personas read them."
        )
        words += [
            (
                f"{standard.rstrip(':')}, with no interview, since "
                f"{facts['stands_in']} says what is wanted: {read}"
            ),
            then,
            correction(fast=False, task=task),
        ]
    else:
        investigator = "Then an investigator" if waiting else "An investigator"
        words += (
            [f"{investigator} finds the answer first.", f"{teller} the answer."]
            if facts.get("question")
            else [
                f"{investigator} finds the cause first.",
                (
                    f"{teller} what it found: the fast track, the standard track, "
                    "or no bug."
                ),
            ]
        )
    return " ".join(word for word in words if word)


def held_order(directory: Path, main: Path, older: str) -> list[str] | None:
    """The lines of each hold of an order that named no task (a `held` block whose first
    line starts as ORDER_WAIT) in OLDER, the blocks of state.md before the one written
    now, for that block to take its type from; None when an OLDER block said the first
    line already: one that names a type and is no such hold, or one after a hold that
    names the task's path with the hold's type."""
    held: list[str] = []
    for part in reversed(
        [part for part in older.strip().split("\n\n") if part.strip()]
    ):
        rows = part.splitlines()
        found = STATE_LINE.fullmatch(rows[0])
        lines = [found["text"], *rows[1:]] if found else rows
        if (
            found
            and found["status"] == "held"
            and lines[0].strip().startswith(ORDER_WAIT)
        ):
            held += lines
            continue
        if type_of(part) is not None:
            return None
        if (
            held
            and found
            and opening_line_facts(directory, main, found["status"], lines, None, held)
            is not None
        ):
            return None
    return held


def opening_line_of(
    directory: Path,
    main: Path,
    status: str,
    lines: list[str],
    older: str,
    branch: str | None,
    *,
    night: bool,
    task: str | None = None,
) -> str | None:
    """The `say` of a state block: the task's first line when this block is the first
    that names its path with its type (no OLDER block of state.md said it,
    `held_order`), and the task is no night's, whose report names it. A hold of his
    order names no path: the first block after his answer that names one says the line,
    with the hold's type when it has none. None for every other block. With `task`, the
    form for another session."""
    held = held_order(directory, main, older)
    if night or held is None:
        return None
    facts = opening_line_facts(directory, main, status, lines, branch, held)
    return compose_opening_line(facts, task) if facts else None


def opening_line(
    root: Path,
    directory: Path,
    slug: str,
    status: str,
    lines: list[str],
    older: str,
    branch: str | None,
) -> dict | None:
    """`opening_line_of` for a task of this repository, with its night's mark read from
    the log: the `say` of the task's own session and the `say_named` of the session the
    owner typed the request in, both from the same facts, or None."""
    if type_of(older) is not None and ORDER_WAIT not in older:
        # a block before this one said the line, and no hold of his order is there to
        # look past
        return None
    night = bool(nights(events_named(root, "task.mode")).get(slug))
    main = main_checkout(root)
    say = opening_line_of(directory, main, status, lines, older, branch, night=night)
    return (
        {
            "say": say,
            "say_named": opening_line_of(
                directory, main, status, lines, older, branch, night=night, task=slug
            ),
        }
        if say
        else None
    )


def read_tasks(root: Path, settings: dict | None = None) -> list[dict]:
    """Every task of the repository as its state files say now. `settings` is
    `load(root)` when the caller read it already; only a task with a ticket
    needs them."""
    tasks: list[dict] = []
    talks = newest_events(root, "plan.talk")
    investigations = newest_events(root, "investigation")
    # each task's own mark and its first and newest state, from the repository's log; a
    # task whose events became its summary has both times and its night's date there,
    # and no mark of its own
    presence = events_named(root, "task.mode", "task.state", SUMMARY)
    opened: dict[str | None, str] = {}
    newest: dict[str | None, str] = {}
    for record in presence:
        if record.get("event") == SUMMARY:
            if record.get("opened"):
                opened.setdefault(record.get("task"), record["opened"])
            if record.get("newest"):
                newest[record.get("task")] = record["newest"]
            continue
        opened.setdefault(record.get("task"), record["ts"])
        newest[record.get("task")] = record["ts"]
    night = nights(presence)
    presence = [record for record in presence if record.get("event") == "task.mode"]
    # and the owner's status, the machine's. An `owner` event a repository's log may
    # still hold is not read: the mark is the one place of his status.
    presence = merged(presence, owner_records())
    parent = state_root(root) / "tasks"
    for directory in sorted(
        d for d in (parent.iterdir() if parent.is_dir() else ()) if d.is_dir()
    ):
        state = directory / "state.md"
        # state.md is newest block first; a block ends at the first blank line
        written = text_of(state) if state.is_file() else ""
        block = written.strip().split("\n\n")[0] if written.strip() else None
        first = STATE_LINE.fullmatch(block.splitlines()[0]) if block else None
        known = first if first is not None and first["status"] in STATES else None
        # an ended task ran without the owner only up to its last event: an "away" after
        # it is no span of it
        ended = (
            known is not None and known["status"] in ENDED and directory.name in newest
        )
        spans = runs_without_owner(
            directory.name,
            [record for record in presence if record["ts"] <= newest[directory.name]]
            if ended
            else presence,
            opened.get(directory.name),
        )
        alone = bool(spans) and spans[-1]["to"] is None
        steps, assignee = ticket_steps_of(directory)
        tasks.append(
            {
                "slug": directory.name,
                "ask": ask_of(directory),
                # the tracker's ticket the ask came from; a dropped or answered task
                # gives its ticket back once it owes it nothing
                "ticket": text_of(directory / "ticket.txt").strip() or None
                if (directory / "ticket.txt").is_file()
                else None,
                # the repository of a GitHub issue, OWNER/REPO from the address its read
                # gave, or null
                "ticket_repo": text_of(directory / "ticket-repo.txt").strip() or None
                if (directory / "ticket-repo.txt").is_file()
                else None,
                # what Lem did to that ticket so far (TICKET_STEPS), by name
                "ticket_steps": steps,
                # the login Lem set out to add as the issue's assignee
                # (`assigned LOGIN`), or null
                "ticket_assignee": assignee,
                # the task that holds the ticket now when it is another one (a resume
                # went on from this one), or null
                "ticket_held_by": None,
                "ticket_owed": [],
                # null when no block was written through `project.py state`: nobody can
                # tell who acts next
                "status": known["status"] if known else None,
                "since": known["since"] if known else None,
                "state": block,
                # what the landing proposed to the owner, for the status and the board:
                # where, and green or why not
                "proposal": proposal(directory),
                # the newest record of its plan talk, as `log plan.talk` wrote it, or
                # null when it had none
                "talk": talks.get(directory.name),
                # the type of the request with its reason, from the newest block that
                # names it, or null
                "type": type_of(written),
                # `fast` or `standard`, from the newest state line that tells it
                # (`track_of`), or null
                "track": track_of(written),
                # what the investigation of a fix or a question found, as
                # `log investigation` wrote it last, or null
                "investigation": investigations.get(directory.name),
                # with the owner or without him now, and since when: from the owner's
                # status and the task's own mark (`runs_without_owner`)
                "mode": "alone" if alone else "with-owner",
                "mode_since": (spans[-1]["from"] if alone else spans[-1]["to"])
                if spans
                else None,
                # each span in which it ran without the owner, with the words that
                # started and ended it, for the pull request
                "without_owner": spans,
                # the date of the night that opened it, or null for a task of the day
                "night": night.get(directory.name),
            }
        )
    if any(task["ticket"] for task in tasks):
        # only a project with a ticket needs its settings here; a broken settings file
        # then stops this, loudly
        tracker = (settings or load(root))["tracker"]
        went_on = {
            text_of(parent / task["slug"] / RESUMED_FROM).strip(): task
            for task in tasks
            if (parent / task["slug"] / RESUMED_FROM).is_file()
        }
        for task in tasks:
            if task["ticket"]:
                task["ticket_held_by"] = ticket_held_by(
                    root, task, went_on.get(task["slug"])
                )
                task["ticket_owed"] = ticket_owed(
                    task["status"],
                    task["ticket_steps"],
                    tracker,
                    task["ticket_held_by"],
                )
    return tasks


def ticket_held_by(root: Path, task: dict, successor: dict | None) -> str | None:
    """The task that holds TASK's ticket now, when it is another one, or None. The
    ticket's mark names it (a resume moves the mark to the new task), and else the task
    a resume went on in, SUCCESSOR, with the same ticket: that one may have given the
    ticket back already, and its mark is gone then."""
    mark = mark_of(root, task["ticket"])
    holder = text_of(mark).strip() if mark.is_file() else ""
    if holder and holder != task["slug"]:
        return holder
    if successor is not None and successor["ticket"] == task["ticket"]:
        return successor["slug"]
    return None


def queued_refusal(slug: str, after: str, other: str | None) -> str:
    """The refusal of `may-start` for a task queued after AFTER, whose status OTHER is
    not ended (None for no task of that name; a dropped AFTER has a refusal of its own),
    with both ways out: a need that went is written away by the agent, and the owner's
    order only by his word, which is logged first."""
    return (
        f"the task {slug!r} is queued after {after!r}, which is {other or 'no task'}: "
        f"it starts when {after} is landed or answered. When it waits because it needs "
        f"the result of {after} and no longer does, write its state `queued` again "
        "without the `after:` line. When the block's first line says "
        "`the owner's order`, only the owner's word removes the order: "
        f'log his words first (`lem decisions log {slug} --by owner --words "HIS '
        'WORDS" ...`), then write its state `queued` again without the `after:` line '
        'and with the line `the owner\'s order was removed: "HIS WORDS"`'
    )


# The owner's words in the commands that the refusal of a task behind a dropped task
# prints: the agent puts the words of his "start SLUG now" in their place, inside the
# single quotes that hold them.
HIS_WORDS = "HIS WORDS"


def after_in(lines: list[str]) -> str | None:
    """The task that the `after:` line of a block names, read from each of its LINES,
    its first among them, as `after_of` of the board's model reads the newest block: the
    refusal of `may-start` and the row of "Waits for you" name the same task. None for a
    block with no such line."""
    return next(
        (found["slug"] for found in map(AFTER_LINE.fullmatch, lines) if found), None
    )


def start_commands(slug: str, lines: list[str]) -> list[str]:
    """The commands of the owner's "start SLUG now" for a task queued behind a dropped
    task, from the LINES of its newest block, each argument quoted for the shell. A
    block with his order (a line that starts as ORDER_START) gets the log of his words,
    then the block again with each of its lines but the `after:` line and with the line
    that says his word removed the order; a need gets that block alone, and no log, as
    step 7 of "The request" has it. HIS_WORDS stands inside single quotes."""
    kept = [line for line in lines if not AFTER_LINE.fullmatch(line)]
    if not any(line.startswith(ORDER_START) for line in lines):
        return [shlex.join(["lem", "project", "state", slug, "queued", *kept])]
    return [
        shlex.join(
            [
                "lem",
                "decisions",
                "log",
                slug,
                "--by",
                "owner",
                "--what",
                "the owner's order",
                "--chose",
                "start now",
                "--why",
                "his word",
                "--words",
                HIS_WORDS,
            ]
        ),
        shlex.join(
            [
                "lem",
                "project",
                "state",
                slug,
                "queued",
                *kept,
                f'the owner\'s order was removed: "{HIS_WORDS}"',
            ]
        ),
    ]


def dropped_refusal(slug: str, after: str, lines: list[str]) -> str:
    """The refusal of `may-start` for a task queued after AFTER, which was dropped: it
    waits for the owner's word, and the commands of his "start SLUG now", composed from
    the LINES of its newest block, are printed whole, one to a line, for the agent to
    run on his word."""
    commands = start_commands(slug, lines)
    how = (
        (
            "Run them as printed, one command to a line, with his words as he typed "
            f"them, on one line, in place of {HIS_WORDS}, inside its single quotes, "
            "where a single quote of his is written '\\'':"
        )
        if len(commands) > 1
        else "Run it as printed:"
    )
    return (
        (
            f"the task {slug!r} is queued after {after!r}, which was dropped, so the "
            "result it waited for never came: it stays queued for the owner's word, "
            f'"start {slug} now" or `/lem drop {slug}`, and nothing below runs '
            f'before it. On his "start {slug} now", or his "start it" for this '
            f"task, run `lem project may-start {slug}` once more and run the commands "
            "that it prints then, never ones printed before his word: "
            f"a correction between the two (`/lem standard-track {slug}`) changes the "
            f"block they copy. {how}\n"
        )
        + "\n".join(commands)
        + (
            '\nThen the task starts, as `stages/start.md`, "`/lem build`", says. '
            f'On his `/lem drop {slug}`, drop it as `stages/correct.md`, "drop", says'
        )
    )


def cmd_may_start(settings: dict, root: Path, slug: str) -> None:
    """Exit 1 for a task that gets no lead: in the landing, proposed or ended, since a
    stale wake-up must not start one, or queued behind a task that has not landed or
    been answered. No count of tasks stops a start: by day each start is the owner's own
    request (the owner, 2026-11-18: "Why block him?"), and a night works its items one
    after another."""
    task_directory(root, slug)
    tasks = read_tasks(root, settings)
    status = next((task["status"] for task in tasks if task["slug"] == slug), None)
    if status in ENDED:
        raise SettingsError(
            f"the task {slug!r} is {status}: an ended task gets no lead, and new work "
            "for it is a new ask (`/lem new`) with a slug of its own"
        )
    if status == PARKED:
        raise SettingsError(
            f"the task {slug!r} is parked: it gets no lead until the owner's "
            f"`/lem resume {slug}` (`lem project resume {slug}`) brings it back"
        )
    if status in ("landing", "open"):
        raise SettingsError(
            f"the task {slug!r} is {status}: its build is done, and it gets no lead. "
            "Its landing goes on with `land.py` (`stages/land.md`; an open task takes "
            f"the line again with `lem land start {slug}`), and a change the owner "
            "asks for now is a new ask",
        )
    # A task queued behind another (`after: OTHER`) starts when that task has ended. Lem
    # writes the line for an ask that needs another's result, and a lead for a plan that
    # does, so that it builds on what the other one changed; and Lem or a lead writes it
    # for an ask whose owner's words put it after another task, whose block's first line
    # is `the owner's order: "HIS WORDS"`. The script reads the `after:` line to tell
    # whether it waits, from every line of the newest block as the board reads it, and
    # behind a dropped task the order line too, to print the commands of the
    # owner's word.
    mine = next((task for task in tasks if task["slug"] == slug), None)
    lines = (
        blocks_of(mine["state"])[0]["lines"]
        if mine and status == "queued" and mine["state"]
        else []
    )
    after = after_in(lines)
    if after:
        other = next((task["status"] for task in tasks if task["slug"] == after), None)
        if other == "dropped":
            # what it waited for never came: whether it starts without it is the
            # owner's word
            raise SettingsError(dropped_refusal(slug, after, lines))
        if other not in ENDED:
            raise SettingsError(queued_refusal(slug, after, other))
    running = [
        task["slug"]
        for task in tasks
        if task["status"] in RUNNING and task["slug"] != slug
    ]
    print(json.dumps({"running": running}))


# The state line of a task whose criteria wait for the owner's yes.
CRITERIA_WAIT = "the criteria wait for the owner"
# Where the retro keeps the record of its proposals, `retros/YYYY-MM-DD.json` in the
# state folder, one file a day for every run of that day (`proposals add`).
RETROS = "retros"
# Where a night keeps its report, `night/YYYY-MM-DD.md` in the state folder
# (`stages/night.md`), and beside it the record of its proposals of the day,
# `night/YYYY-MM-DD.json`, in the retro's form.
NIGHTS = "night"
# A held block's first line while a breaker holds the task (decisions.py BREAKER_WAIT),
# which `lem session` reads for its phase.
BREAKER_WAIT = re.compile(r"breaker ([1-9]\d*) waits for the owner")


def waiting_brief(task: dict) -> dict:
    """What the list of what waits says of every task it names."""
    return {
        "task": task["slug"],
        "ask": task["ask"],
        "since": task["since"],
        "night": task["night"],
    }


def waiting_model(root: Path, settings: dict) -> "tuple[Model, str | None]":
    """The board's model of the repository as the board server builds it
    (`lem_board_model`), for `waiting`: the event log, the owner's mark, the demo mark
    (board.py `meta_of`), the forge's last look that the server wrote
    (`lem_board_model.FORGE_LOOK`), and the task sessions, which it asks
    `lem session list` for itself (`waiting_sessions`), with the turn of the session
    that runs this command left as one Lem cannot tell
    (`lem_board_model.own_turn_unread`), since that turn runs while it asks. With the
    model, what the session said of the sessions: None when they are known, else
    why not."""
    bm = importlib.import_module("lem_board_model")
    state = state_root(root)
    reader = bm.Reader(main_checkout(root), state)
    reader.read_log()
    if "events" in reader.problems:
        raise SettingsError(
            f"{state / 'events.jsonl'}: {reader.problems['events']}; "
            "the log is written by project.py, never by hand"
        )
    model = bm.derive(
        reader.events,
        owner_records(),
        bm.now_ms(),
        meta={"demo": (state / "demo").is_file()},
    )
    model.seen = (bm.forge_look(state) or {}).get("seen")
    said = None
    if not model.meta["demo"]:
        sessions, said = waiting_sessions(root, settings, model, bm)
        caller = (
            os.environ.get("AGTERM_SESSION_ID")
            or os.environ.get("AGT_SESSION_ID")
            or None
        )
        bm.put_sessions(model, bm.own_turn_unread(sessions, caller))
    return model, said


def waiting_sessions(
    root: Path, settings: dict, model: "Model", bm: ModuleType
) -> tuple[dict | None, str | None]:
    """The task sessions as the board server knows them (`lem_board_model.sessions_of`):
    what `lem session list` says, with the ended tasks whose worktree is still there;
    and None with why, when the list cannot be had (no agterm). A log with no
    `session.open` has no session to ask agterm about."""
    parent = main_checkout(root) / Path(
        settings["places"]["worktrees"]["path"]
    ).relative_to(root.resolve())
    kept = {t.slug for t in model.tasks if t.closed and (parent / t.slug).is_dir()}
    if not any(t.opened for t in model.tasks):
        return bm.sessions_of({}, kept), None
    ran = subprocess.run(
        [
            sys.executable,
            "-B",
            str(Path(__file__).resolve().parent / "session.py"),
            "--repo",
            str(root),
            "list",
        ],
        capture_output=True,
        text=True,
        check=False,
        stdin=subprocess.DEVNULL,
    )
    try:
        if ran.returncode != 0:
            lines = [
                line.strip()
                for line in (ran.stderr or ran.stdout).splitlines()
                if line.strip()
            ]
            raise ValueError(lines[-1] if lines else f"it exited {ran.returncode}")
        return bm.sessions_of(bm.session_entries(ran.stdout), kept), None
    except ValueError as error:
        return None, f"the task sessions are not known: `lem session list` said {error}"


def first_line_of(task: dict) -> str | None:
    found = (
        STATE_LINE.fullmatch(task["state"].splitlines()[0])
        if task.get("state")
        else None
    )
    return found["text"] if found else None


def cmd_waiting(root: Path) -> dict:
    """Everything that waits for the owner, from the files that hold it: nothing here
    decides or writes. Its rows are the rows of the board's "Waits for you"
    (`lem_board_model.waits_of`), so that the terminal and the phone list the same; each
    group holds the rows of one kind, and `tasks` holds them grouped by task, as the
    board's stacks (`lem_board_model.wait_stacks`)."""
    # a broken settings file is an error here too
    settings = load(root)
    tasks = {task["slug"]: task for task in read_tasks(root, settings)}
    model, unknown = waiting_model(root, settings)
    bm = importlib.import_module("lem_board_model")
    rows = [row for row in bm.waits_of(model) if row["t"].slug in tasks]
    asked = subprocess.run(
        [
            sys.executable,
            "-B",
            str(Path(__file__).resolve().parent / "decisions.py"),
            "--repo",
            str(root),
            "pending",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if asked.returncode != 0:
        raise SettingsError(
            asked.stderr.strip().removeprefix("decisions.py: ")
            or "decisions.py pending failed"
        )
    pending = json.loads(asked.stdout)

    def brief(row: dict, **more: object) -> dict:
        task = tasks[row["t"].slug]
        return {**waiting_brief(task), "line": first_line_of(task), **more}

    def kind(name: str) -> list[dict]:
        return [row for row in rows if row["kind"] == name]

    def breaker(row: dict) -> dict:
        number = row["c"].id
        found = next(
            (
                item
                for item in pending["waiting"]
                if item["task"] == row["t"].slug and item.get("id") == number
            ),
            None,
        )
        return found or {
            "task": row["t"].slug,
            "id": number,
            "what": row["c"].what,
            "status": row["t"].status,
        }

    def dropped_after(row: dict) -> dict:
        # the row's own words, so that the terminal says what the board says, also for a
        # first line that names neither
        say = bm.wait_say(row)
        return brief(
            row,
            after=row["after"],
            **{key: say[key] for key in ("verb", "start", "drop", "where")},
        )

    def pull_request(row: dict) -> dict:
        task = tasks[row["t"].slug]
        proposal = task["proposal"] or {}
        return {
            **waiting_brief(task),
            **{
                key: proposal.get(key)
                for key in (
                    "pull_request",
                    "green",
                    "not_green",
                    "conflict",
                    "merge_review",
                    "merge_refused",
                )
            },
        }

    marks = owner_records()
    found: dict[str, Any] = {
        # whether the owner said he is away, since when and in which words, from the
        # machine's mark: the list says it first; `seen` is the number of records in the
        # mark, from which a watch of it starts
        "owner": {**owner_now(marks), "seen": len(marks)},
        "breakers": [breaker(row) for row in kind("breaker")],
        "criteria": [brief(row) for row in kind("criteria")],
        "held": [brief(row) for row in kind("held")],
        "after_dropped": [dropped_after(row) for row in kind("after_dropped")],
        # a task two releases back says the release stop's message as its
        # line (lem_release)
        "blocked": [
            brief(row, **({"line": row["say"]} if row.get("say") else {}))
            for row in kind("blocked")
        ],
        "plans": [brief(row) for row in kind("plan")],
        "reviews": [
            brief(row, why=bm.review_why(row["c"]), tip=row["c"].get("tip"))
            for row in kind("review")
        ],
        "pull_requests": [pull_request(row) for row in kind("merge")],
        "no_session": [
            brief(row, need="deaf" if row.get("deaf") else "gone")
            for row in kind("session")
        ],
        # a task whose live session the guard of a stopped session logged as stopped,
        # and the open of its button
        "stopped": [
            brief(
                row,
                open=f"lem session open {row['t'].slug} --why stopped",
                unread=row["unread"],
            )
            for row in kind("stopped")
        ],
        # the board's rows in its order, each by its key (`waits_of`): the rows the
        # phone shows
        "rows": [
            {"key": row["key"], "kind": row["kind"], "task": row["t"].slug}
            for row in rows
        ],
        # the same rows grouped by task, as the board draws them (`wait_stacks`): one
        # entry for each task, in the place of its first row, with each of its things in
        # its order and in the row's own words
        "tasks": [
            {
                **waiting_brief(tasks[stack["t"].slug]),
                "line": first_line_of(tasks[stack["t"].slug]),
                "things": [
                    {
                        "key": row["key"],
                        "kind": row["kind"],
                        "verb": bm.wait_say(row)["verb"],
                    }
                    for row in stack["rows"]
                ],
            }
            for stack in bm.wait_stacks(rows)
        ],
        # what the list knows of the task sessions, which the rows of `no_session` need,
        # and the forge's last look
        "sessions": {"known": unknown is None, "said": unknown},
        "forge": {"looked": (bm.forge_look(state_root(root)) or {}).get("looked")},
    }
    # the report of last night: a night writes it under the day it started, so today's
    # or yesterday's
    today = datetime.now().date()  # noqa: DTZ005 - the list looks for the report of today and of yesterday by the local day
    recent = [
        (state_root(root) / NIGHTS / f"{day.isoformat()}.md")
        for day in (today, today - timedelta(days=1))
    ]
    report = next((file for file in recent if file.is_file()), None)
    found["night_report"] = (
        {"date": report.stem, "file": str(report)} if report else None
    )
    # the tasks the owner put aside: no row of what waits, and not counted, so a status
    # can name them apart
    found["parked"] = [
        {**waiting_brief(task), "line": first_line_of(task)}
        for task in tasks.values()
        if task["status"] == PARKED
    ]
    # a task counts once, however many of its things wait, as each count of the
    # board does
    found["count"] = len(found["tasks"])
    return found


# ---- the proposals of the night and the retro, and the reviewer's items (`proposals`) ----

# The two kinds of run that propose, each with its folder of the state folder: one
# record a day.
PROPOSAL_KINDS = {"retro": RETROS, "night": NIGHTS}
# The folder of the reviewer's items in the state folder, which git never sees: one item
# for each area whose proposals passed, in the backlog's item format
# (agents/lem-builder.md, rule 6).
STATE_BACKLOG = "backlog"
# The one lock of the records and the items, in the state folder: add, verdict and drop
# each read and write under it, so that two writers at one moment (a retro of the
# owner's while the reviewer writes its verdicts, a drop from the board) never lose
# a write.
PROPOSALS_LOCK = "proposals.lock"
# The keys of a day's record, of a proposal as add takes it, and of each entry of a
# record's lists.
RECORD_KEYS = ("date", "kind", "runs", "proposals", "refuted", "passed", "dropped")
PROPOSAL_KEYS = ("area", "move", "body", "source", "where")
ENTRY_KEYS = {
    "runs": ("at", "read", "proposals"),
    "proposals": ("number", *PROPOSAL_KEYS),
    "refuted": ("number", "reason", "day"),
    "passed": ("number", "area", "item", "day"),
    "dropped": ("number", "text", "said", "day", "item"),
}
# What a drop says in the record, which the reviewer of a later morning reads as the
# owner's no.
DROPPED_SAID = "the owner dropped it"
# The front-matter key of a reviewer's item that names each of its proposals, as
# `KIND of DATE #N`: where it came from (the retro or the night), its day and its number
# in that day's record.
ITEM_KEY = "proposals"
PROPOSAL_NAME = re.compile(r"(retro|night) of (\d{4}-\d{2}-\d{2}) #([1-9]\d*)")
RUN_TIME = "%Y-%m-%dT%H:%M:%SZ"
# How a record reads, for every refusal of one that does not.
RECORD_FORM = (
    "a JSON object with `date` (its day), `kind` (retro or night), `runs` (each with "
    "`at`, `read` and the `proposals` it added), `proposals` (each with `number`, from "
    "1, `area`, `move`, `body`, `source` and `where`), `refuted` (each with `number`, "
    "`reason` and `day`), `passed` (each with `number`, `area`, `item` and `day`) and "
    "`dropped` (each with `number`, `text`, `said`, `day` and `item`)"
)


def proposal_name(kind: str, day: str, number: int) -> str:
    """How an item, a verdict and the read name one proposal:
    `retro of 2026-11-23 #3`."""
    return f"{kind} of {day} #{number}"


def record_file(state: Path, kind: str, day: str) -> Path:
    return state / PROPOSAL_KINDS[kind] / f"{day}.json"


def a_day(value: object) -> bool:
    try:
        return isinstance(value, str) and date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def text_problem(value: object, where: str) -> str | None:
    return None if isinstance(value, str) and value.strip() else f"{where} is no text"


def record_problem(data: object, kind: str, day: str) -> str | None:
    """Why DATA is not the record of KIND's proposals of DAY, or None when it is. A file
    in the form of Lem's question page, as the retro wrote it before its proposals went
    to the reviewer, says so."""
    if isinstance(data, dict) and ("questions" in data or "prompt" in data):
        return (
            "it holds questions in the form of the question page, which no longer "
            "reads as a record of proposals"
        )
    if not isinstance(data, dict):
        return "it is not a JSON object"
    if missing := [key for key in RECORD_KEYS if key not in data]:
        return f"it has no {', '.join(missing)}"
    if extra := sorted(set(data) - set(RECORD_KEYS)):
        return f"it holds keys a record has not: {', '.join(extra)}"
    if data["date"] != day:
        return f"its date is {data['date']!r}, and its name says {day}"
    if data["kind"] != kind:
        return f"its kind is {data['kind']!r}, and its folder holds the {kind}'s"
    for key, keys in ENTRY_KEYS.items():
        if not isinstance(data[key], list) or not all(
            isinstance(entry, dict) and sorted(entry) == sorted(keys)
            for entry in data[key]
        ):
            return f"`{key}` is not a list of entries with {', '.join(keys)}"
    for n, proposal in enumerate(data["proposals"], 1):
        if proposal["number"] != n:
            return (
                f"its proposal {n} has the number {proposal['number']!r}: "
                "the numbers go 1, 2, 3 in order"
            )
        for key in PROPOSAL_KEYS:
            if problem := text_problem(proposal[key], f"the {key} of proposal {n}"):
                return problem
        if not SLUG.fullmatch(proposal["area"]):
            return (
                f"the area of proposal {n}, {proposal['area']!r}, is not lower-case "
                "words joined by hyphens"
            )
    numbers = set(range(1, len(data["proposals"]) + 1))
    added: list = []
    for run in data["runs"]:
        if not isinstance(run["at"], str) or not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", run["at"]
        ):
            return f"a run's time, {run['at']!r}, is not YYYY-MM-DDTHH:MM:SSZ"
        if not isinstance(run["read"], str) or not isinstance(run["proposals"], list):
            return (
                f"the run of {run['at']} has no `read` text or no list of `proposals`"
            )
        added += run["proposals"]
    if any(not isinstance(n, int) or isinstance(n, bool) for n in added) or sorted(
        added
    ) != sorted(numbers):
        return (
            "its runs do not add up to its proposals: each proposal is added by one run"
        )
    seen: dict[str, set] = {}
    for key in ("refuted", "passed", "dropped"):
        seen[key] = set()
        for entry in data[key]:
            if entry["number"] not in numbers or entry["number"] in seen[key]:
                return (
                    f"`{key}` names the proposal {entry['number']!r}, which the record "
                    "has not, or names it twice"
                )
            if not a_day(entry["day"]):
                return (
                    f"the day of `{key}` of proposal {entry['number']} is not "
                    "YYYY-MM-DD"
                )
            seen[key].add(entry["number"])
    if both := seen["refuted"] & seen["passed"]:
        return f"the proposal {min(both)} is refuted and passed at once"
    if not seen["dropped"] <= seen["passed"]:
        return (
            f"the proposal {min(seen['dropped'] - seen['passed'])} is dropped, "
            "and it passed into no item"
        )
    return None


def read_record(file: Path, kind: str) -> dict | None:
    """The record of FILE, of KIND's proposals, or None when there is no such file. A
    record that does not read is refused with the fix, since a reviewer that read half
    of it would judge again what was judged, or miss what was not."""
    if not file.is_file():
        return None
    try:
        data = json.loads(text_of(file))
    except ValueError as error:
        data, problem = None, f"it does not read as JSON ({error})"
    else:
        problem = record_problem(data, kind, file.stem)
    if problem is None:
        return data
    if "question page" in problem:
        raise SettingsError(
            f"{file}: {problem}. The maintaining session converts it by hand into a "
            f"record of proposals, {RECORD_FORM}: each question a proposal with no "
            "verdict, in one run, so that the next reviewer reads them",
        )
    raise SettingsError(
        f"{file}: {problem}. A record is {RECORD_FORM}, and only "
        "`lem project proposals` writes one: correct the file by hand into that form"
    )


def write_whole(file: Path, text: str) -> None:
    """Write FILE whole under another name first, so that a reader never finds half
    of it."""
    file.parent.mkdir(parents=True, exist_ok=True)
    staging = file.with_name(f"{file.name}.{os.getpid()}.new")
    staging.write_text(text, encoding="utf-8")
    staging.replace(file)


def write_record(file: Path, data: dict) -> None:
    write_whole(file, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


@contextlib.contextmanager
def proposals_lock(state: Path) -> Generator[None, None, None]:
    with (state / PROPOSALS_LOCK).open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def records_of(state: Path) -> list[tuple[str, Path, dict]]:
    """Every record of the state folder, the retro's and the night's, oldest day first:
    (kind, file, record)."""
    found = []
    for kind, folder in PROPOSAL_KINDS.items():
        for file in sorted((state / folder).glob("*.json")):
            if not a_day(file.stem):
                raise SettingsError(
                    f"{file}: a record of proposals is named by its day, "
                    f"YYYY-MM-DD.json; rename it or move it out of {folder}/"
                )
            # the file was listed just now, so it gives a record
            found.append((kind, file, cast("dict", read_record(file, kind))))
    return sorted(found, key=lambda one: (one[2]["date"], one[0]))


def spec_of(text: str, where: str) -> dict:
    try:
        spec = json.loads(text)
    except ValueError as error:
        raise SettingsError(f"{where} does not read as JSON ({error})") from None
    if not isinstance(spec, dict):
        raise SettingsError(f"{where} is not a JSON object")
    return spec


def cmd_proposals_add(
    state: Path, kind: str, day: str, spec: dict, now: datetime
) -> dict:
    """Add one run of KIND to its record of DAY, which this makes when it is not there:
    what the run read, and its proposals with the numbers after those already there.
    Nothing of the record is rewritten: a second run of the day keeps the numbers, the
    verdicts and the drops of the first."""
    if kind not in PROPOSAL_KINDS:
        raise SettingsError(f"--kind is retro or night, not {kind!r}")
    if not a_day(day):
        raise SettingsError(f"--date is the run's day, YYYY-MM-DD, not {day!r}")
    if extra := sorted(set(spec) - {"read", "proposals"}):
        raise SettingsError(
            f"the run holds keys add does not take: {', '.join(extra)}; "
            "give `read` and `proposals`"
        )
    if problem := text_problem(spec.get("read"), "`read`, what the run read,"):
        raise SettingsError(
            f"{problem}: say in a line what the run read (the tasks since the last "
            "run, the naps, the night's file)"
        )
    proposals = spec.get("proposals")
    if not isinstance(proposals, list):
        raise SettingsError(
            "`proposals` is the run's list of proposals, "
            "[] for a run that proposes nothing"
        )
    for n, proposal in enumerate(proposals, 1):
        if not isinstance(proposal, dict) or sorted(proposal) != sorted(PROPOSAL_KEYS):
            raise SettingsError(
                f"proposal {n} of the run is not an object with "
                f"{', '.join(PROPOSAL_KEYS)}, and nothing else"
            )
        for key in PROPOSAL_KEYS:
            if problem := text_problem(
                proposal[key], f"the {key} of proposal {n} of the run"
            ):
                raise SettingsError(problem)
        if not SLUG.fullmatch(proposal["area"]):
            raise SettingsError(
                f"the area of proposal {n} of the run, {proposal['area']!r}, is "
                "lower-case words joined by hyphens, as lessons or board"
            )
        if "\n" in proposal["move"].strip():
            raise SettingsError(
                f"the move of proposal {n} of the run is one line; "
                "its body says the rest"
            )
    file = record_file(state, kind, day)
    at = now.astimezone(UTC).strftime(RUN_TIME)
    with proposals_lock(state):
        record = read_record(file, kind) or {
            "date": day,
            "kind": kind,
            "runs": [],
            "proposals": [],
            "refuted": [],
            "passed": [],
            "dropped": [],
        }
        first = len(record["proposals"]) + 1
        numbers = list(range(first, first + len(proposals)))
        for number, proposal in zip(numbers, proposals, strict=True):
            record["proposals"].append(
                {
                    "number": number,
                    **{key: proposal[key].strip() for key in PROPOSAL_KEYS},
                }
            )
        record["runs"].append(
            {"at": at, "read": spec["read"].strip(), "proposals": numbers}
        )
        write_record(file, record)
    return {
        "file": str(file),
        "kind": kind,
        "date": day,
        "at": at,
        "numbers": numbers,
        "names": [proposal_name(kind, day, n) for n in numbers],
    }


def cmd_proposals_read(state: Path) -> dict:
    """Every proposal of every record with no verdict yet (a morning whose reviewer did
    not finish is read on the next one), every one refuted, passed or dropped on any
    day, and the newest run of each kind, from whose time the next retro reads."""
    found: dict = {
        "undecided": [],
        "refuted": [],
        "passed": [],
        "dropped": [],
        "newest": dict.fromkeys(PROPOSAL_KINDS),
    }
    for kind, file, record in records_of(state):
        verdicts = {
            key: {entry["number"]: entry for entry in record[key]}
            for key in ("refuted", "passed", "dropped")
        }
        for proposal in record["proposals"]:
            one = {
                "name": proposal_name(kind, record["date"], proposal["number"]),
                "kind": kind,
                "date": record["date"],
                **proposal,
                "file": str(file),
            }
            number = proposal["number"]
            if number in verdicts["dropped"]:
                dropped = verdicts["dropped"][number]
                found["dropped"].append(
                    {
                        **one,
                        "said": dropped["said"],
                        "day": dropped["day"],
                        "item": dropped["item"],
                    }
                )
            elif number in verdicts["refuted"]:
                found["refuted"].append(
                    {
                        **one,
                        "reason": verdicts["refuted"][number]["reason"],
                        "day": verdicts["refuted"][number]["day"],
                    }
                )
            elif number in verdicts["passed"]:
                passed = verdicts["passed"][number]
                found["passed"].append(
                    {
                        **one,
                        "item": passed["item"],
                        "day": passed["day"],
                        "there": (
                            state / STATE_BACKLOG / Path(passed["item"]).name
                        ).is_file(),
                    }
                )
            else:
                found["undecided"].append(one)
        for run in record["runs"]:
            newest = found["newest"][kind]
            if newest is None or run["at"] > newest["at"]:
                found["newest"][kind] = {
                    "date": record["date"],
                    "at": run["at"],
                    "read": run["read"],
                }
    return found


def item_slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def item_text(
    title: str, area: str, today: str, entries: list[tuple[str, dict]]
) -> str:
    """A reviewer's item in the backlog's item format, with the front-matter key
    ITEM_KEY that names each proposal in it, and for each its move, where it came from,
    its source and its body."""
    names = [name for name, _ in entries]
    head = [
        "---",
        "worth: later",
        f"where: {entries[0][1]['where']}",
        f"added: {today}",
        f"{ITEM_KEY}: {', '.join(names)}",
        "---",
        f"# {title}",
        "",
    ]
    said = names[0] if len(names) == 1 else f"{', '.join(names[:-1])} and {names[-1]}"
    lines = [
        *head,
        (
            f"The reviewer passed {counted(len(names), 'proposal')} about "
            f"{area} on {today}: {said}."
        ),
        "",
    ]
    for name, proposal in entries:
        # each name had its verdict read in this form
        kind, day, number = cast(
            "re.Match[str]", PROPOSAL_NAME.fullmatch(name)
        ).groups()
        lines += [
            f"## {proposal['move']}",
            "",
            (
                f"From the {kind} of {day}, proposal {number}. "
                f"Its source: {proposal['source']}. Where: `{proposal['where']}`."
            ),
            "",
            proposal["body"],
            "",
        ]
    return "\n".join(lines)


def counted(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def cmd_proposals_verdict(state: Path, spec: dict, today: str) -> dict:
    """The reviewer's verdict on each proposal SPEC names: refuted, with its reason, or
    passed, with its area. The passed proposals of one area become one item of the state
    folder's backlog, under the title SPEC gives that area, and no item when nothing
    passed. Every verdict is checked before any is written; the items are written before
    the records, so an interruption leaves a proposal with no verdict, which the next
    read gives again, and never a verdict with no item."""
    if extra := sorted(set(spec) - {"verdicts", "titles"}):
        raise SettingsError(
            f"the verdicts hold keys verdict does not take: {', '.join(extra)}; "
            "give `verdicts` and `titles`"
        )
    verdicts, titles = spec.get("verdicts"), spec.get("titles", {})
    if not isinstance(verdicts, list) or not verdicts:
        raise SettingsError(
            '`verdicts` is the list of the reviewer\'s verdicts, each {"proposal": '
            '"retro of DATE #N", "refuted": REASON} or {"proposal": '
            '..., "passed": AREA}'
        )
    if not isinstance(titles, dict) or not all(
        isinstance(title, str) for title in titles.values()
    ):
        raise SettingsError(
            "`titles` gives each area that passed the title of its item, "
            '{"AREA": "TITLE"}'
        )
    with proposals_lock(state):
        records: dict[tuple[str, str], tuple[Path, dict]] = {}
        judged: list[tuple[str, str, str, dict, dict]] = []
        named: set[str] = set()
        for n, verdict in enumerate(verdicts, 1):
            if (
                not isinstance(verdict, dict)
                or "proposal" not in verdict
                or len(set(verdict) & {"refuted", "passed"}) != 1
                or not set(verdict) <= {"proposal", "refuted", "passed"}
            ):
                raise SettingsError(
                    f'verdict {n} is not {{"proposal": "retro of DATE #N", "refuted": '
                    'REASON} or {"proposal": ..., "passed": AREA}'
                )
            name = verdict["proposal"]
            found = PROPOSAL_NAME.fullmatch(name) if isinstance(name, str) else None
            if not found:
                raise SettingsError(
                    f"verdict {n} names {name!r}, and a proposal is named as "
                    "`lem project proposals read` gives it: "
                    "retro of DATE #N or night of DATE #N"
                )
            if name in named:
                raise SettingsError(f"{name} has two verdicts here; give it one")
            named.add(name)
            kind, day, number = found[1], found[2], int(found[3])
            if (kind, day) not in records:
                file = record_file(state, kind, day)
                record = read_record(file, kind)
                if record is None:
                    raise SettingsError(
                        f"{name}: there is no record of the {kind} of {day} ({file}); "
                        "`lem project proposals read` gives the proposals"
                    )
                records[(kind, day)] = (file, record)
            record = records[(kind, day)][1]
            if number > len(record["proposals"]):
                raise SettingsError(
                    f"{name}: the record of the {kind} of {day} has "
                    f"{counted(len(record['proposals']), 'proposal')}"
                )
            if any(
                entry["number"] == number
                for key in ("refuted", "passed")
                for entry in record[key]
            ):
                raise SettingsError(
                    f"{name} has a verdict already, which stays: "
                    "`lem project proposals read` gives the proposals with none"
                )
            word = "refuted" if "refuted" in verdict else "passed"
            if problem := text_problem(
                verdict[word],
                (
                    f"the {'reason' if word == 'refuted' else 'area'} of "
                    f"the verdict on {name}"
                ),
            ):
                raise SettingsError(problem)
            if word == "passed" and not SLUG.fullmatch(verdict[word]):
                raise SettingsError(
                    f"the area of the verdict on {name}, {verdict[word]!r}, is "
                    "lower-case words joined by hyphens, as lessons or board"
                )
            judged.append((name, kind, word, verdict, record["proposals"][number - 1]))
        areas: dict[str, list[tuple[str, dict]]] = {}
        for name, _kind, word, verdict, proposal in judged:
            if word == "passed":
                areas.setdefault(verdict["passed"], []).append((name, proposal))
        if missing := [area for area in areas if not (titles.get(area) or "").strip()]:
            raise SettingsError(
                f"`titles` gives no title for the area {', '.join(missing)}: "
                "each area that passed becomes one item, "
                "with the title the reviewer gives it"
            )
        if extra := sorted(set(titles) - set(areas)):
            raise SettingsError(
                f"`titles` names {', '.join(extra)}, and no "
                "proposal passed with that area"
            )
        folder = state / STATE_BACKLOG
        taken = (
            {file.name for file in folder.glob("*.md")} if folder.is_dir() else set()
        )
        items: dict[str, dict] = {}
        for area, entries in areas.items():
            title = " ".join(titles[area].split())
            stem = item_slug(title)
            if not stem:
                raise SettingsError(
                    f"the title of the area {area}, {title!r}, "
                    "has no word to name its file by"
                )
            name, n = f"{stem}.md", 1
            while name in taken:
                n += 1
                name = f"{stem}-{n}.md"
            taken.add(name)
            items[area] = {
                "area": area,
                "title": title,
                "path": (lem_state.STATE / STATE_BACKLOG / name).as_posix(),
                "file": folder / name,
                "proposals": [one for one, _ in entries],
                "text": item_text(title, area, today, entries),
            }
        for item in items.values():
            write_whole(item["file"], item["text"])
        for name, kind, word, verdict, _proposal in judged:
            # each name had its verdict read in this form
            found = cast("re.Match[str]", PROPOSAL_NAME.fullmatch(name))
            record = records[(kind, found[2])][1]
            number = int(found[3])
            if word == "refuted":
                record["refuted"].append(
                    {
                        "number": number,
                        "reason": verdict["refuted"].strip(),
                        "day": today,
                    }
                )
            else:
                record["passed"].append(
                    {
                        "number": number,
                        "area": verdict["passed"],
                        "item": items[verdict["passed"]]["path"],
                        "day": today,
                    }
                )
        for file, record in records.values():
            write_record(file, record)
    return {
        "day": today,
        "refuted": [
            name
            for name, _kind, word, _verdict, _proposal in judged
            if word == "refuted"
        ],
        "items": [
            {key: item[key] for key in ("area", "title", "path", "proposals")}
            for item in items.values()
        ],
    }


def ask_path(state: Path, text: str) -> str | None:
    """The one path a task's ask TEXT is, relative to the root of the main checkout (the
    parent of the state folder STATE's `.lem/`): TEXT stripped, as the board's "Start a
    task" writes it, or a whole path under the main checkout, as the night may write it.
    None for a whole path outside it."""
    path = text.strip()
    main = state.parent.parent
    if path.startswith("/"):
        root = next(
            (
                prefix
                for prefix in (
                    f"{str(main).rstrip('/')}/",
                    f"{str(main.resolve()).rstrip('/')}/",
                )
                if path.startswith(prefix)
            ),
            None,
        )
        if root is None:
            return None
        path = path[len(root) :]
    return path


def backlog_item_of(state: Path, text: str) -> str | None:
    """The reviewer's item TEXT names: TEXT is the path of a file of the state folder's
    backlog and nothing else, relative to the root of the main checkout as the board's
    "Start a task" writes it (`.lem/state/backlog/NAME.md`), or whole (`ask_path`). The
    path relative to the root, whether the file is there or not, or None. land.py reads
    a task's ask by this function."""
    path = ask_path(state, text)
    if path is None:
        return None
    parent, _, name = path.rpartition("/")
    if (
        parent != (lem_state.STATE / STATE_BACKLOG).as_posix()
        or not name.endswith(".md")
        or name == ".md"
    ):
        return None
    return path


def item_holder(state: Path, item: str) -> dict | None:
    """The task that holds the backlog item ITEM, a path relative to the root of the
    main checkout (a reviewer's item as `backlog_item_of` gives it, or an item of the
    backlog folder): a task whose ask.txt is the item's path (`ask_path`) and that has
    not ended, as `{"task": SLUG, "status": STATUS}`, with STATUS null for a task that
    has no state yet; None when no task holds it. The drop reads it, and the board's
    "Start a task" and its mark of a reviewer's item read the same rule."""
    tasks = state / "tasks"
    for directory in sorted(
        d for d in (tasks.iterdir() if tasks.is_dir() else ()) if d.is_dir()
    ):
        ask = directory / "ask.txt"
        if not ask.is_file() or ask_path(state, text_of(ask)) != item:
            continue
        written = (
            text_of(directory / "state.md").strip()
            if (directory / "state.md").is_file()
            else ""
        )
        first = STATE_LINE.fullmatch(written.splitlines()[0]) if written else None
        status = first["status"] if first else None
        if status not in ENDED:
            return {"task": directory.name, "status": status}
    return None


class ItemRefused(SettingsError):
    """A drop the records refuse, with its answer as JSON for the board: the task that
    holds the item, or none."""

    def __init__(self, message: str, answer: dict) -> None:
        super().__init__(message)
        self.answer = answer


def item_proposals(text: str) -> list[str] | None:
    """The proposals a reviewer's item names in its front matter (ITEM_KEY), or None
    when it names none."""
    if not text.startswith("---"):
        return None
    head, mark, _ = text[3:].partition("\n---")
    for line in head.splitlines() if mark else ():
        key, colon, value = line.partition(":")
        if colon and key.strip() == ITEM_KEY:
            names = [name.strip() for name in value.split(",") if name.strip()]
            return (
                names
                if names and all(PROPOSAL_NAME.fullmatch(name) for name in names)
                else None
            )
    return None


def cmd_proposals_drop(state: Path, given: str, today: str) -> dict:
    """The owner's drop of a reviewer's item, in one call: refused while a task that has
    not ended holds it (`item_holder`), with that task; else the drop of each proposal
    the item names is kept in its day's record, and then the item's file goes. The
    board's server runs it under its script lock, so a start from the board comes before
    it or after it, never between its read and its removal."""
    item = backlog_item_of(state, given)
    if item is None:
        raise ItemRefused(
            (
                f"{given!r} is not the path of an item of "
                f"{lem_state.STATE / STATE_BACKLOG}/, such as "
                f"{lem_state.STATE / STATE_BACKLOG}/NAME.md: only the reviewer's items "
                "are dropped here; an item of the backlog folder leaves it on a branch"
            ),
            {"dropped": False, "item": given, "held_by": None},
        )
    file = state / STATE_BACKLOG / item.rpartition("/")[2]
    with proposals_lock(state):
        if not file.is_file():
            raise ItemRefused(
                (
                    f"the item {item} is not there: it was dropped, or its task "
                    "landed; read the backlog again"
                ),
                {"dropped": False, "item": item, "held_by": None, "gone": True},
            )
        holder = item_holder(state, item)
        if holder:
            raise ItemRefused(
                (
                    f"the task {holder['task']} ({holder['status'] or 'new'}) builds "
                    f"the item {item}, so it is not dropped: it leaves with that "
                    "task's landing, or is undecided again once "
                    "the owner drops the task"
                ),
                {
                    "dropped": False,
                    "item": item,
                    "held_by": holder["task"],
                    "status": holder["status"],
                },
            )
        names = item_proposals(text_of(file))
        if names is None:
            raise ItemRefused(
                (
                    f"the item {item} names no proposal in its `{ITEM_KEY}:` line, so "
                    "no record keeps its drop: only `lem project proposals verdict` "
                    "writes the reviewer's items; remove a file "
                    "it did not write by hand"
                ),
                {"dropped": False, "item": item, "held_by": None},
            )
        records: dict[tuple[str, str], tuple[Path, dict | None]] = {}
        for name in names:
            # item_proposals gives the names of this form only
            kind, day, number = cast(
                "re.Match[str]", PROPOSAL_NAME.fullmatch(name)
            ).groups()
            number = int(number)
            if (kind, day) not in records:
                record_path = record_file(state, kind, day)
                records[(kind, day)] = (record_path, read_record(record_path, kind))
            record = records[(kind, day)][1]
            if record is None or not any(
                entry["number"] == number and entry["item"] == item
                for entry in record["passed"]
            ):
                raise ItemRefused(
                    (
                        f"the item {item} names {name}, and no record says that it "
                        "passed into this item, so no record keeps its drop: "
                        "the maintaining session compares the item with the records of "
                        "`lem project proposals read`"
                    ),
                    {"dropped": False, "item": item, "held_by": None},
                )
            if not any(entry["number"] == number for entry in record["dropped"]):
                record["dropped"].append(
                    {
                        "number": number,
                        "text": record["proposals"][number - 1]["move"],
                        "said": DROPPED_SAID,
                        "day": today,
                        "item": item,
                    }
                )
        for record_path, record in records.values():
            # a name whose record is missing was refused above
            write_record(record_path, cast("dict", record))
        file.unlink()
    return {"dropped": True, "item": item, "proposals": names, "day": today}


def dropped_item_refusal(state: Path, ask: str) -> str | None:
    """Why `task-dir --ask` refuses ASK: the path of a reviewer's item whose file is
    gone, since the owner dropped it after the board showed it. None for every
    other ask."""
    item = backlog_item_of(state, ask)
    if item is None or (state / STATE_BACKLOG / item.rpartition("/")[2]).is_file():
        return None
    return (
        f"the item was dropped: read the backlog again ({item} is no longer in the "
        "state folder's backlog)"
    )


def cmd_owner(root: Path, status: str, words: str | None) -> dict:
    """Write the owner's status, away or back, with his words as typed, into the
    machine's mark, so that every repository on this machine reads it. Nothing is
    written when it changes nothing: away while he is away, back while he is there. His
    status changes nothing in a build, which asks him nothing in either; it is read by
    an interview, criteria that wait for his yes, the task sessions, and the merge.
    `tasks` are this repository's: after an away the tasks that run without him, after a
    back the ones that came back to him (a night's task does not), and none after a back
    while he was there."""
    if status not in ("away", "back"):
        raise SettingsError(
            f"the owner is away or back, not {status!r}: "
            '`lem project owner away --words "I\'m away"` or '
            '`lem project owner back --words "I\'m back"` '
            "(`lem project owner watch --seen N` watches his status)"
        )
    if not words or not words.strip():
        raise SettingsError(
            '--words are the owner\'s words as typed ("I\'m away", "/lem im-back"); '
            "no script can tell who typed, so they are his only"
        )
    marks = owner_records()
    now = owner_now(marks)
    away = status == "away"
    without = [
        task["slug"]
        for task in read_tasks(root)
        if task["status"] not in ENDED and task["mode"] == "alone"
    ]
    if now["away"] == away:
        return {**now, "written": False, "tasks": without if away else []}
    record = append_owner(root, away=away, words=words.strip())
    after = [
        task["slug"]
        for task in read_tasks(root)
        if task["status"] not in ENDED and task["mode"] == "alone"
    ]
    return {
        "away": away,
        "since": record["ts"],
        "words": record["words"],
        "written": True,
        "tasks": after if away else [slug for slug in without if slug not in after],
    }


def cmd_owner_watch(root: Path, seen: int, every: int = OWNER_WATCH_SECONDS) -> dict:
    """Look at the machine's mark once every EVERY seconds, and end with the owner's
    status as soon as the mark holds another number of records than SEEN, the count
    `waiting` gave as `owner.seen`: at once when that is so at the start, so that no
    change is lost between Lem's read and this start. The count is the cursor and no
    time is, since a `ts` has whole seconds and an away and a back can share one; the
    mark is only appended to, so a new record always changes the count. It writes
    nothing. Lem acts on its result."""
    if seen < 0:
        raise SettingsError(
            "--seen is the number of records in the owner's mark, 0 or more, not "
            f"{seen}: `lem project waiting` gives it as owner.seen"
        )
    marks = owner_records()

    def stopped(*_: object) -> None:
        raise KeyboardInterrupt

    before = (
        signal.signal(signal.SIGTERM, stopped),
        signal.signal(signal.SIGINT, stopped),
    )
    try:
        while len(marks) == seen:
            time.sleep(every)
            marks = owner_records()
    except KeyboardInterrupt:
        raise SettingsError(
            "the watch of the owner's status was stopped; start no other until the "
            "reason for the stop is gone"
        ) from None
    finally:
        signal.signal(signal.SIGTERM, before[0])
        signal.signal(signal.SIGINT, before[1])
    return {**owner_now(marks), "seen": len(marks)}


def cmd_load(start: str | None) -> dict:
    """The machine's load gate: the start number the developer set, else Lem's
    LOAD_START, and the load average now. With --start, the number is written first;
    none writes 0, so that the gate stays away and Lem's number does not come back
    by itself."""
    file = lem_state.machine_file()
    if start is not None:
        if start == "none":
            value = 0.0
        else:
            try:
                value = float(start)
            except ValueError:
                value = -1.0
            if not value > 0:
                raise SettingsError(
                    "--start is a load average above 0, or none to take the gate away, "
                    f"not {start!r}"
                )
        # the file is written whole, with the board server's table kept as it reads
        try:
            lem_state.write_machine(
                "load", {"start": int(value) if value.is_integer() else value}
            )
        except OSError as error:
            raise SettingsError(
                f"{file} was not written ({error.strerror}); make its folder writable, "
                "then run this again"
            ) from error
        except lem_state.StateError as error:
            # a file that does not read, or holds a table that is not valid there, stays
            # as it is
            raise SettingsError(str(error)) from error
    try:
        number = lem_state.load_start()
        written = "start" in lem_state.machine_table("load")
    except lem_state.StateError as error:
        raise SettingsError(str(error)) from error
    now = round(os.getloadavg()[0], 1)
    return {
        "file": str(file),
        "start": number,
        "default": not written,
        "load": now,
        "cores": os.cpu_count(),
        "gate": None
        if number is None
        else (
            "open"
            if now < number
            else f"closed: the checks wait for a load below {number:g}"
        ),
    }


def cmd_handoff(tokens: str | None) -> dict:
    """The number of tokens past which a task's session compacts itself, for every
    repository on this machine (`[handoff] tokens`). With --tokens it is written first;
    `default` takes the line out, so that Lem's own number holds."""
    file = lem_state.machine_file()
    if tokens is not None:
        if tokens == "default":
            value = None
        else:
            value = int(tokens) if re.fullmatch(r"\d+", tokens) else -1
            if value != 0 and value < lem_state.HANDOFF_FLOOR:
                raise SettingsError(
                    "--tokens is 0 (Claude Code compacts at its own trigger), a whole "
                    f"number of {lem_state.HANDOFF_FLOOR} or more, or default for "
                    f"{lem_state.HANDOFF_TOKENS}, not {tokens!r}: Claude Code refuses "
                    f"a window under {lem_state.HANDOFF_FLOOR}"
                )
        try:
            lem_state.write_machine(
                "handoff", None if value is None else {"tokens": value}
            )
        except OSError as error:
            raise SettingsError(
                f"{file} was not written ({error.strerror}); make its folder writable, "
                "then run this again"
            ) from error
        except lem_state.StateError as error:
            # a file that does not read, or holds a table that is not valid there, stays
            # as it is
            raise SettingsError(str(error)) from error
    try:
        number = lem_state.handoff_tokens()
        written = "tokens" in lem_state.machine_table("handoff")
    except lem_state.StateError as error:
        raise SettingsError(str(error)) from error
    return {
        "file": str(file),
        "tokens": number,
        "default": not written,
        "said": f"handoff tokens: {number} ({'default' if not written else 'set here'})"
        if number is not None
        else (
            "handoff tokens: 0, so Lem sets nothing and Claude Code "
            "compacts at its own trigger"
        ),
    }


def cmd_serial(root: Path, words: list[str]) -> int:
    """Run one command under the repository's lock for commands that need the machine to
    themselves, and give its exit status back. Another run that holds the lock is
    waited for."""
    words = words[1:] if words[:1] == ["--"] else words
    if not words or not any(word.strip() for word in words):
        raise SettingsError(
            "serial takes the command to run: `lem project serial -- COMMAND ...`, or "
            "one quoted line for the shell"
        )
    shown = words[0] if len(words) == 1 else " ".join(words)
    path = state_root(root) / SERIAL_LOCK
    try:
        handle = path.open("a+", encoding="utf-8")
    except OSError as error:
        raise SettingsError(
            f"the lock {path} cannot be opened ({error.strerror}); it holds no state, "
            f"so remove it (`rm -r {path}`) and run this again"
        ) from error
    with handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            handle.seek(0)
            holder = handle.read().strip() or "its holder wrote no line yet"
            print(
                (
                    f"project.py: another serial test holds the lock ({holder}); "
                    "this one waits"
                ),
                file=sys.stderr,
                flush=True,
            )
            fcntl.flock(handle, fcntl.LOCK_EX)
        handle.seek(0)
        handle.truncate()
        handle.write(
            f"pid {os.getpid()}, since "
            f"{datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')}, in {Path.cwd()}: "
            f"{shown}\n"
        )
        handle.flush()
        proc: subprocess.Popen | None = None

        def stopped(number: int, _frame: object) -> None:
            raise InterruptedError(number)

        before = {
            sign: signal.signal(sign, stopped)
            for sign in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP)
        }
        try:
            # a group of its own, so that what the command starts ends with it when this
            # run is stopped
            proc = subprocess.Popen(
                words[0] if len(words) == 1 else words,
                shell=len(words) == 1,
                start_new_session=True,
            )
            code = proc.wait()
        except InterruptedError as stop:
            code = 128 + stop.args[0]
        finally:
            if proc is not None:
                for sign in (signal.SIGTERM, signal.SIGKILL):
                    try:
                        os.killpg(proc.pid, sign)
                    except (ProcessLookupError, PermissionError):
                        break
                    try:
                        proc.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        continue
                    # the leader ended; a process it left in the group gets the next
                    # signal too
                    try:
                        os.killpg(proc.pid, 0)
                    except (ProcessLookupError, PermissionError):
                        break
            for sign, handler in before.items():
                signal.signal(sign, handler)
            # the holder's line goes with the hold, so that a waiting run never names a
            # run that ended
            handle.seek(0)
            handle.truncate()
    return code if code >= 0 else 128 - code


def nap_time(name: str) -> datetime | None:
    """When the nap of a folder started, from its name; None for a name that holds no
    such time."""
    found = NAP_NAME.fullmatch(name)
    if not found:
        return None
    try:
        return datetime.strptime(found["time"], NAP_TIME).replace(tzinfo=UTC)
    except ValueError:
        return None


def hours(seconds: float) -> str:
    return f"{seconds / 3600:.1f} hours"


def cmd_may_nap(root: Path) -> None:
    """Whether a nap may start now, from the settings and the naps folder. A yes writes
    the nap down as started. An old nap's folder goes with `prune`."""
    settings = load(root)
    naps = settings["naps"]
    folder = state_root(root) / "naps"
    folder.mkdir(exist_ok=True)
    now = datetime.now(UTC)
    kept = []
    for entry in sorted(folder.iterdir()):
        when = nap_time(entry.name)
        if when is None or entry.is_symlink() or not entry.is_dir():
            continue
        kept.append((when, entry))
    marker = folder / ASLEEP
    asleep = None
    # both are read only while a nap is asleep, which sets them
    since, started = now, ""
    if marker.is_file():
        try:
            asleep = json.loads(text_of(marker))
            since = datetime.strptime(asleep["since"], "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=UTC
            )
            started = asleep["time"]
            if not isinstance(started, str) or not NAP_NAME.fullmatch(started):
                raise ValueError(f"time = {started!r}")
        except (ValueError, KeyError, TypeError) as error:
            raise SettingsError(
                f"{marker} is not the record may-nap writes ({error}); "
                "remove the file, and the next call writes it again"
            ) from error
    answer: dict[str, Any] = {
        "may": False,
        "why": "",
        "folder": str(folder),
        "time": None,
        "newest": max(kept)[1].name if kept else None,
    }
    # a nap runs until its folder holds waking.md, the last file it writes, and for an
    # hour at most
    woke = asleep is not None and any(
        (nap / "waking.md").is_file()
        for _when, nap in kept
        if nap.name.startswith(started)
    )
    if (
        asleep is not None
        and not woke
        and (now - since).total_seconds() < ASLEEP_MINUTES * 60
    ):
        answer["why"] = (
            f"a nap runs since {asleep['since']}: it ends when naps/{started}-... "
            f"holds waking.md, or {ASLEEP_MINUTES} minutes after its start"
        )
    elif not naps["on"]:
        answer["why"] = (
            f"the naps are off on this machine (naps.on = false in {LOCAL})"
            if "naps.on" in settings["local"]["overrides"]
            else f"the naps are off (naps.on = false in {SETTINGS})"
        )
    else:
        last = max(
            [when for when, _nap in kept] + ([since] if asleep is not None else []),
            default=None,
        )
        age = (now - last).total_seconds() if last else None
        if age is not None and age < NAPS_GAP_HOURS * 3600:
            answer["why"] = (
                f"the newest nap started {hours(age)} ago, and {NAPS_GAP_HOURS} "
                "hours pass between two naps"
            )
        else:
            answer["may"] = True
            answer["why"] = (
                "there is no nap yet"
                if age is None
                else f"the newest nap started {hours(age)} ago"
            )
            answer["time"] = now.strftime(NAP_TIME)
            record = {
                "since": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "time": answer["time"],
            }
            # written whole under another name first, so that a reader never finds half
            # of it
            staging = folder / f"{ASLEEP}.{os.getpid()}"
            staging.write_text(json.dumps(record) + "\n", encoding="utf-8")
            staging.replace(marker)
    print(json.dumps(answer, indent=2))


# ---- what the state folder keeps (`prune`) ----

# The folders of the state folder whose old entries go whole, each with how an entry's
# day is told: `written`, its last write, the newest time of anything in it; `named`,
# the nap's start in its name. An entry of `written` folders that is a folder must start
# with its day, YYYY-MM-DD-, as a question to the experts and a panel do; the copies of
# the cast are named by a commit or a blob, and cast.py writes the time of each read on
# its copy, so a copy that a panel reads stays.
PRUNED = (
    ("experts", "experts", "written", True),
    ("panels", "panels", "written", True),
    ("naps", "naps", "named", True),
    ("cast", "personas-cast", "written", False),
    ("cast", "personas-profile", "written", False),
    ("cast", "personas-person", "written", False),
)
DAY_NAME = re.compile(r"\d{4}-\d{2}-\d{2}-.+")


def task_calls(found: list[dict], events: list[dict], cutoff: datetime) -> list[dict]:
    """What `prune` does with each task: `found` gives each task's `slug` and the text
    of its state.md (`state`, None with no such file), `events` the event log, oldest
    first. Each call is `open` (no state yet, or a status that is not ended: never
    touched), `young` (ended, and its newest event is after `cutoff`), `old` (ended, and
    nothing of it was logged since `cutoff`: all but its small record goes), or `skip`,
    with `why`: a state.md that does not read, or a log that does not agree with it, is
    never guessed at. A task's summary (SUMMARY) is its stated status, and its `ts` the
    time of its newest event, so a task whose events became its summary stays `old`."""
    newest: dict[str, str] = {}
    stated: dict[str, str] = {}
    for record in events:
        task, ts = record.get("task"), record.get("ts")
        if not isinstance(task, str) or not isinstance(ts, str):
            continue
        newest[task] = max(newest.get(task, ts), ts)
        if record.get("event") in ("task.state", SUMMARY):
            stated[task] = str(record.get("status"))
    calls = []
    for task in found:
        slug, text = task["slug"], task["state"]
        call: dict[str, Any] = {
            "task": slug,
            "status": None,
            "last_event": newest.get(slug),
        }
        if text is None or not text.strip():
            calls.append({**call, "call": "open"})
            continue
        first = STATE_LINE.fullmatch(text.strip().split("\n\n")[0].splitlines()[0])
        if first is None or first["status"] not in STATES:
            calls.append(
                {
                    **call,
                    "call": "skip",
                    "why": (
                        "its state.md does not read: the first line of its newest "
                        "block is not `TIME STATUS: TEXT` with a status Lem knows"
                    ),
                }
            )
            continue
        call["status"] = first["status"]
        if first["status"] not in ENDED:
            calls.append({**call, "call": "open"})
            continue
        if slug not in newest:
            calls.append(
                {
                    **call,
                    "call": "skip",
                    "why": (
                        f"its state.md says {first['status']}, and the event log holds "
                        "no event of it, so the day it ended is not known"
                    ),
                }
            )
            continue
        if stated.get(slug) != first["status"]:
            calls.append(
                {
                    **call,
                    "call": "skip",
                    "why": (
                        f"its state.md says {first['status']}, and the newest state of "
                        f"it in the event log says {stated.get(slug) or 'nothing'}"
                    ),
                }
            )
            continue
        try:
            last = datetime.strptime(newest[slug], "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=UTC
            )
        except ValueError:
            calls.append(
                {
                    **call,
                    "call": "skip",
                    "why": (
                        f"the time of its newest event, {newest[slug]!r}, does not read"
                    ),
                }
            )
            continue
        calls.append({**call, "call": "old" if last <= cutoff else "young"})
    return calls


class Remover:
    """What `prune` removes, or with `dry` would remove, inside one state folder: a path
    is touched only when it is no link and its folder resolves inside the state folder.
    A link is never followed and never removed: it is named in `skipped`. Each removal
    that fails is named in `failed`, and the others go on."""

    def __init__(self, top: Path, *, dry: bool) -> None:
        self.top = top.resolve()
        self.dry = dry
        self.skipped: list[dict] = []
        self.failed: list[dict] = []

    def shown(self, path: Path) -> str:
        return (
            path.relative_to(self.top).as_posix()
            if path.is_relative_to(self.top)
            else str(path)
        )

    def inside(self, path: Path) -> bool:
        """Whether PATH is no link, and its folder resolves inside the state folder: the
        one guard of every removal."""
        try:
            if path.is_symlink():
                self.skipped.append(
                    {
                        "path": self.shown(path),
                        "why": "a link, which prune never follows and never removes",
                    }
                )
                return False
            parent = path.parent.resolve()
        except OSError as error:
            self.failed.append({"path": self.shown(path), "error": str(error)})
            return False
        if parent != self.top and not parent.is_relative_to(self.top):
            self.skipped.append(
                {"path": str(path), "why": f"not inside the state folder {self.top}"}
            )
            return False
        return True

    def file(self, path: Path) -> int | None:
        """Remove one file; its bytes, or None when it was not removed."""
        if not self.inside(path):
            return None
        try:
            facts = path.lstat()
            if not stat.S_ISREG(facts.st_mode):
                self.skipped.append(
                    {"path": self.shown(path), "why": "not a plain file"}
                )
                return None
            if not self.dry:
                path.unlink()
        except OSError as error:
            self.failed.append({"path": self.shown(path), "error": str(error)})
            return None
        return facts.st_size

    def empty_folders(self, folder: Path) -> None:
        """Remove the folders under FOLDER that hold nothing now, deepest first; FOLDER
        itself stays."""
        if self.dry:
            return
        for at, folders, _ in os.walk(folder, topdown=False):
            for name in folders:
                path = Path(at) / name
                try:
                    if not path.is_symlink() and not any(path.iterdir()):
                        path.rmdir()
                except OSError as error:
                    self.failed.append({"path": self.shown(path), "error": str(error)})

    def tree(self, path: Path) -> int:
        """Remove a file, or a folder with all it holds, deepest first; the bytes
        removed. A link inside stays, and so does the folder that holds it."""
        if not self.inside(path):
            return 0
        if not path.is_dir():
            return self.file(path) or 0
        removed = 0
        for at, folders, names in os.walk(path, topdown=False):
            for name in names:
                removed += self.file(Path(at) / name) or 0
            for name in folders:
                inner = Path(at) / name
                if inner.is_symlink():
                    # os.walk lists a link to a folder among the folders, and never goes
                    # into it
                    self.skipped.append(
                        {
                            "path": self.shown(inner),
                            "why": (
                                "a link, which prune never follows and never removes"
                            ),
                        }
                    )
                elif not self.dry:
                    try:
                        inner.rmdir()
                    except OSError as error:
                        self.failed.append(
                            {"path": self.shown(inner), "error": str(error)}
                        )
        if not self.dry:
            try:
                path.rmdir()
            except OSError as error:
                self.failed.append({"path": self.shown(path), "error": str(error)})
        return removed


def last_write(path: Path) -> float:
    """The newest time of a write to PATH or to anything in it, read with no
    link followed."""
    newest = path.lstat().st_mtime
    if path.is_dir() and not path.is_symlink():
        for at, folders, names in os.walk(path):
            for name in [*folders, *names]:
                try:
                    newest = max(newest, (Path(at) / name).lstat().st_mtime)
                except OSError:
                    continue
    return newest


def stamp_of(seconds: float) -> str:
    return datetime.fromtimestamp(seconds, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# What a line of the log that does not read stops in `prune`, which dates each ended
# task by the log.
PRUNE_STOPS = "prune dates each task by the log, so it removed nothing"


def unread_line(log: Path, number: int, error: ValueError, why: str) -> SettingsError:
    """The refusal of line NUMBER of the event log LOG, which does not read as JSON; WHY
    says what it stopped."""
    return SettingsError(
        f"{log}:{number} does not read as JSON ({error}), and {why}; "
        "the log is written by project.py, never by hand: correct or remove that line"
    )


def log_events(root: Path, why: str = PRUNE_STOPS) -> list[dict]:
    """Every event of the repository's log, oldest first. A line that does not read
    stops the caller, WHY says how: `prune` dates each ended task by the log, and
    removes nothing by a guess."""
    log = state_root(root) / "events.jsonl"
    if not log.is_file():
        return []
    found = []
    for number, line in enumerate(lem_state.jsonl_lines(text_of(log)), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except ValueError as error:
            raise unread_line(log, number, error, why) from error
        if isinstance(record, dict):
            found.append(record)
    return found


def stamp_ms(ms: int) -> str:
    """A time of the board's model, in ms, as the log writes a `ts`."""
    return datetime.fromtimestamp(ms / 1000, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def summary_of(slug: str, records: list[dict], now: int) -> dict:
    """The one SUMMARY event that stands for RECORDS, every event of the ended task SLUG
    in the log's order. Each fact is the one the function that reads it from the events
    gives, so that a reader of the summary and a reader of the events cannot disagree:
    the board's model (`lem_board_model` `derive`, then `settle` for the newest block,
    `since`, `first` and `last`, `pr_of`, the card's `type`, `criteria_size` for the
    track, `lead_of`, `careful_of`, `proposal` and `investigation`, and whether a plan
    talk ended before the newest block, which `said_of` reads), `read_tasks` for
    `opened` and `newest` (the first and newest `task.mode` or `task.state`), and
    `nights` for `night`. `transcripts` is the path of each `session.transcript` of the
    task, each once in the log's order, after those of an older summary: `lem_tokens`
    reads them by each transcript's first prompt, so that a fork of an open task's
    session logged under this one still counts for that task. `ts` is the time of the
    task's newest event, which `prune` dates the task by. A task whose events hold its
    summary and newer events gets one new summary: the old one is the task's past, a
    newer fact replaces its old one, and `events` adds the old count to the
    newer events."""
    bm = importlib.import_module("lem_board_model")
    old = next(
        (record for record in reversed(records) if record.get("event") == SUMMARY), None
    )
    rest = [record for record in records if record is not old]
    task = bm.derive(rest, [], now).by_slug.get(slug)
    stated = task is not None and any(
        record.get("event") == "task.state" and bm.at(record.get("ts")) is not None
        for record in rest
    )
    past = old or {}
    if not stated and old is None:
        raise SettingsError(
            f"the task {slug!r} has no state event in the log to summarize; "
            "prune summarizes only a task the log dates"
        )

    def newer(fact: object, key: str) -> object:
        return fact if fact is not None else past.get(key)

    if stated:
        block = task.blocks[-1]
        # the run of the newest status goes back into the old summary when every newer
        # block has that status too
        since = (
            past["since"]
            if old
            and old.get("status") == task.status
            and all(b["status"] == task.status for b in task.blocks)
            else stamp_ms(task.since)
        )
        facts = {
            "status": task.status,
            "text": task.text,
            "lines": list(block["lines"]),
            "since": since,
            "first": past.get("first") or stamp_ms(task.first),
            "last": stamp_ms(task.last_ts),
            "talked": bool(past.get("talked")) or bm.talked_before(task, block["ts"]),
        }
    else:
        facts = {
            key: past.get(key)
            for key in ("status", "text", "lines", "since", "first", "last", "talked")
        }
    times = [
        record["ts"]
        for record in rest
        if record.get("event") in ("task.mode", "task.state")
        and isinstance(record.get("ts"), str)
    ]
    proposal = task.proposal if task else None
    investigation = task.investigation if task else None
    transcripts = [
        path for path in past.get("transcripts") or [] if isinstance(path, str)
    ]
    for record in rest:
        path = record.get("transcript")
        if (
            record.get("event") == "session.transcript"
            and isinstance(path, str)
            and path
            and path not in transcripts
        ):
            transcripts.append(path)
    return {
        "ts": max(
            record["ts"] for record in records if isinstance(record.get("ts"), str)
        ),
        "event": SUMMARY,
        "task": slug,
        "status": facts["status"],
        "text": facts["text"],
        "lines": facts["lines"],
        "since": facts["since"],
        "first": facts["first"],
        "last": facts["last"],
        "opened": past.get("opened") or (times[0] if times else None),
        "newest": times[-1] if times else past.get("newest"),
        "pr": newer(bm.pr_of(task) if stated else None, "pr"),
        "ask": newer(task.ask if task else None, "ask"),
        "branch": newer(task.branch if task else None, "branch"),
        "type": newer(task.type if task else None, "type"),
        "size": newer(bm.criteria_size(task) if task else None, "size"),
        "lead": newer(bm.lead_of(task) if task and task.lead else None, "lead"),
        "careful": newer(bm.careful_of(task) if task else None, "careful"),
        "proposal": newer(
            {
                "ts": stamp_ms(proposal["ts"]),
                "green": proposal["green"],
                "reasons": proposal["reasons"],
                "tip": proposal["tip"],
            }
            if proposal
            else None,
            "proposal",
        ),
        "investigation": newer(
            {**investigation, "ts": stamp_ms(investigation["ts"])}
            if investigation
            else None,
            "investigation",
        ),
        "talked": facts["talked"],
        "night": nights(records).get(slug),
        "transcripts": transcripts,
        "events": int(past.get("events") or 0) + len(rest),
    }


def summaries(
    records: Sequence[dict | None], calls: list[dict], now: int
) -> dict[str, tuple[dict, int]]:
    """The summary of each task that `task_calls` calls `old`, by its slug, with how
    many lines of the log it replaces, from RECORDS, the log's records in its order
    (None for a line that is no record). A task whose events are already its one summary
    gets none: a second prune writes nothing."""
    old = {call["task"] for call in calls if call["call"] == "old"}
    mine: dict[str, list[dict]] = {}
    for record in records:
        if (
            record is not None
            and isinstance(record.get("task"), str)
            and record["task"] in old
        ):
            mine.setdefault(record["task"], []).append(record)
    return {
        slug: (summary_of(slug, found, now), len(found))
        for slug, found in mine.items()
        if not (len(found) == 1 and found[0].get("event") == SUMMARY)
    }


def log_lines(data: bytes, log: Path) -> tuple[list[tuple[bytes, dict | None]], int]:
    """The whole lines of DATA, the bytes of the event log LOG, each as it is with its
    record (None for a blank line or a value that is no object), and how many bytes they
    take: a line that is being written has no newline yet, and is not read. A line that
    does not read stops the caller, as in `log_events`."""
    whole = data.rfind(b"\n") + 1
    lines: list[tuple[bytes, dict | None]] = []
    for number, raw in enumerate(data[:whole].split(b"\n")[:-1], 1):
        if not raw.strip():
            lines.append((raw, None))
            continue
        try:
            record = json.loads(raw.decode("utf-8"))
        except ValueError as error:
            raise unread_line(log, number, error, PRUNE_STOPS) from error
        lines.append((raw, record if isinstance(record, dict) else None))
    return lines, whole


def summarized_log(
    lines: list[tuple[bytes, dict | None]], made: dict[str, tuple[dict, int]]
) -> bytes:
    """The log's LINES with the events of each task of MADE replaced by its summary, in
    the place of the task's newest line; every other line byte for byte, in
    its order."""
    last = {
        record["task"]: n
        for n, (_raw, record) in enumerate(lines)
        if record is not None
        and isinstance(record.get("task"), str)
        and record["task"] in made
    }
    out = []
    for n, (raw, record) in enumerate(lines):
        task = record.get("task") if record is not None else None
        if isinstance(task, str) and task in made:
            if last[task] == n:
                out.append(
                    json.dumps(made[task][0], ensure_ascii=False).encode("utf-8")
                )
            continue
        out.append(raw)
    return b"".join(line + b"\n" for line in out)


def rewrite_log(
    state: Path, found: list[dict], cutoff: datetime, now: int
) -> tuple[list[dict], dict[str, tuple[dict, int]]]:
    """Under the log's lock, which the caller holds: read the event log, call each task
    (`task_calls`), and when a task's events become its summary, write the new log whole
    to a file of the state folder and put it in the log's place. The new file has a new
    inode, so a reader that reads the log on from where it stopped reads it whole. The
    old file stays open across the replace: what a writer that takes no lock (a task's
    session of an older Lem) appended to it after the read goes on at the end of the
    new log."""
    log = state / lem_state.EVENTS
    try:
        handle = log.open("rb")
    except FileNotFoundError:
        return task_calls(found, [], cutoff), {}
    with handle:
        lines, whole = log_lines(handle.read(), log)
        records = [record for _raw, record in lines]
        calls = task_calls(
            found, [record for record in records if record is not None], cutoff
        )
        made = summaries(records, calls, now)
        if not made:
            return calls, made
        descriptor, name = tempfile.mkstemp(dir=state, prefix=".events.", suffix=".new")
        try:
            with os.fdopen(descriptor, "wb") as out:
                out.write(summarized_log(lines, made))
                out.flush()
                os.fsync(out.fileno())
            Path(name).chmod(stat.S_IMODE(os.fstat(handle.fileno()).st_mode))
            Path(name).replace(log)
        except BaseException:
            Path(name).unlink(missing_ok=True)
            raise
        handle.seek(whole)
        carried = handle.read()
        if carried:
            with log.open("ab") as out:
                out.write(carried)
    return calls, made


def cmd_prune(root: Path, *, dry: bool, days: int | None) -> tuple[dict, int]:
    """Remove what the state folder no longer needs, older than `state.keep_days` (or,
    in a dry run, --days): the events of each task that ended, which become its one
    summary event (`rewrite_log`), then every file of that task's folder but its small
    record (`lem_artifacts.outside_record`) and the folders left empty, and the old
    entries of PRUNED. The summary is written before any file of the task goes, which
    `cmd_resume` counts on. With `dry`, only say what would go. The answer, and the
    exit: 1 when a removal failed. The answer's `files` is the number of the tasks'
    files removed. The answer's `from` says where the number came from: the project's
    settings, this machine's own file, Lem's default, or `--days N`."""
    if days is not None and not dry:
        raise SettingsError(
            f"--days goes with --dry-run only: a removal keeps what {KEEP_KEY} says, "
            f"so set the number in {SETTINGS} for the project, "
            f"or in {LOCAL} for this machine alone",
        )
    if days is not None and (isinstance(days, bool) or days < 0):
        raise SettingsError(f"--days {days} is no number of days: give 0 or more")
    settings = load(root)
    keep, source = (
        (settings["state"]["keep_days"], settings["state"]["from"])
        if days is None
        else (days, f"--days {days}")
    )
    state = state_root(root)
    if state.is_symlink():
        raise SettingsError(
            f"{state} is a link, and prune removes nothing through a link: "
            "make the state folder a folder of the main checkout"
        )
    remover = Remover(state, dry=dry)
    now = datetime.now(UTC)
    cutoff = now - timedelta(days=keep)
    tasks_folder = state / "tasks"
    found, links = [], []
    if tasks_folder.is_symlink():
        remover.skipped.append(
            {
                "path": "tasks",
                "why": "a link, which prune never follows and never removes",
            }
        )
    elif tasks_folder.is_dir():
        for directory in sorted(tasks_folder.iterdir()):
            if directory.is_symlink():
                links.append(directory)
                continue
            if not directory.is_dir():
                continue
            state_file = directory / "state.md"
            if state_file.is_symlink():
                remover.skipped.append(
                    {
                        "path": f"tasks/{directory.name}",
                        "why": "its state.md is a link, which prune never follows",
                    }
                )
                continue
            try:
                text = text_of(state_file) if state_file.is_file() else None
            except (OSError, SettingsError) as error:
                remover.skipped.append(
                    {
                        "path": f"tasks/{directory.name}",
                        "why": f"its state.md does not read: {error}",
                    }
                )
                continue
            found.append({"slug": directory.name, "state": text})
    for link in links:
        remover.skipped.append(
            {
                "path": f"tasks/{link.name}",
                "why": "a link, which prune never follows and never removes",
            }
        )
    # An ended task past the days has its events replaced with one summary event. A dry
    # run takes no lock and writes nothing: it reads the log as it is, and says what a
    # removal would summarize.
    moment = int(now.timestamp() * 1000)
    if dry:
        events = log_events(root)
        calls = task_calls(found, events, cutoff)
        made = summaries(events, calls, moment)
    else:
        with lem_state.events_lock(state):
            calls, made = rewrite_log(state, found, cutoff, moment)
    summarized = [
        {"task": slug, "status": summary["status"], "events": count}
        for slug, (summary, count) in made.items()
    ]
    pruned_tasks: list[dict] = []
    counts = {"open": 0, "young": 0, "old": 0}
    for call in calls:
        if call["call"] in counts:
            counts[call["call"]] += 1
        if call["call"] in ("open", "young"):
            continue
        if call["call"] == "skip":
            remover.skipped.append(
                {"path": f"tasks/{call['task']}", "why": call["why"]}
            )
            continue
        # every file of it but its small record, of a task whose events became its
        # summary in an earlier run too: a run that stopped after the summary, or a
        # removal that failed, is finished here
        directory = tasks_folder / call["task"]
        gone, size = [], 0
        for path in lem_artifacts.outside_record(directory):
            removed = remover.file(directory / path)
            if removed is not None:
                gone.append(path)
                size += removed
        remover.empty_folders(directory)
        kept = 0
        for at, _folders, names in os.walk(directory):
            for name in names:
                if (Path(at) / name).relative_to(directory).as_posix() in gone:
                    continue
                try:
                    kept += (Path(at) / name).lstat().st_size
                except OSError:
                    continue
        if gone:
            pruned_tasks.append(
                {
                    "task": call["task"],
                    "status": call["status"],
                    "last_event": call["last_event"],
                    "files": gone,
                    "bytes": size,
                    "kept_bytes": kept,
                }
            )
    folders: list[dict] = []
    for kind, name, dated, day_named in PRUNED:
        top = state / name
        if top.is_symlink():
            remover.skipped.append(
                {
                    "path": name,
                    "why": "a link, which prune never follows and never removes",
                }
            )
            continue
        if not top.is_dir():
            continue
        for entry in sorted(top.iterdir()):
            if entry.name.startswith(".") or entry.name.endswith(".lock"):
                continue
            if entry.is_symlink():
                remover.skipped.append(
                    {
                        "path": f"{name}/{entry.name}",
                        "why": "a link, which prune never follows and never removes",
                    }
                )
                continue
            if dated == "named":
                when = nap_time(entry.name)
                if when is None or not entry.is_dir():
                    continue
                last = when.timestamp()
            else:
                if day_named and not (
                    entry.is_dir() and DAY_NAME.fullmatch(entry.name)
                ):
                    continue
                try:
                    last = last_write(entry)
                except OSError as error:
                    remover.failed.append(
                        {"path": f"{name}/{entry.name}", "error": str(error)}
                    )
                    continue
            if last > cutoff.timestamp():
                continue
            size = remover.tree(entry)
            folders.append(
                {
                    "kind": kind,
                    "path": f"{name}/{entry.name}",
                    "last": stamp_of(last),
                    "bytes": size,
                }
            )
    total = sum(task["bytes"] for task in pruned_tasks) + sum(
        folder["bytes"] for folder in folders
    )
    files = sum(len(task["files"]) for task in pruned_tasks)
    verb = "would remove" if dry else "removed"
    replaced = sum(one["events"] for one in summarized)
    answer = {
        "dry_run": dry,
        "keep_days": keep,
        "from": source,
        "before": stamp_of(cutoff.timestamp()),
        "state": str(state),
        "tasks": pruned_tasks,
        "summarized": summarized,
        "events": replaced,
        "folders": folders,
        "files": files,
        "bytes": total,
        "said": (
            f"{verb} {files} files of {len(pruned_tasks)} ended tasks with no event "
            f"since {stamp_of(cutoff.timestamp())[:10]}, so that each keeps only its "
            "small record (its state, its request, its pull request, and its ticket's "
            f"and its resume's files), {'would replace' if dry else 'replaced'} the "
            f"{replaced} events of {len(summarized)} such tasks with one summary event "
            f"each, and {verb} {len(folders)} old folders and copies, "
            f"{total / 1_000_000:.1f} MB"
        ),
        "open": counts["open"],
        "young": counts["young"],
        "old": counts["old"],
        "skipped": remover.skipped,
        "failed": remover.failed,
    }
    return answer, 1 if remover.failed else 0


def release_refusal(root: Path, args: argparse.Namespace) -> str | None:
    """The release rule (lem_release) for a command that names one task, before it reads
    or writes anything; `resume` runs it itself, once it reads whether the task is
    parked or dropped. The three ends of a task pass at `state` (`land.py` writes
    `landed` through it at the end of a merge), and so do the tracker's steps of an end
    at `ticket-step` (TICKET_ENDS), which the Linear skill writes as commands of their
    own after the end."""
    slug = getattr(args, "slug", None)
    if (
        args.command == "resume"
        or not isinstance(slug, str)
        or not SLUG.fullmatch(slug)
    ):
        return None
    ends = (args.command == "state" and args.status in ENDED) or (
        args.command == "ticket-step" and args.step in TICKET_ENDS
    )
    return lem_release.check(state_root(root) / "tasks" / slug, passes=ends)


@lem_release.one_command
def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="lem project",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="a directory inside the checkout (default: the current one)",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("show")
    commands.add_parser("path").add_argument("name")
    commands.add_parser("may-land").add_argument("branch")
    commands.add_parser("worktree-dir").add_argument("slug")
    worktree = commands.add_parser(
        "worktree",
        help="make a task's worktree, a new branch from origin's base branch",
    )
    worktree.add_argument("slug")
    worktree.add_argument("branch")
    init = commands.add_parser("init")
    init.add_argument("--base")
    init.add_argument(
        "--codex",
        choices=("yes", "no"),
        default="yes",
        help=(
            "whether the machine check found Codex: no writes the reviewer "
            "on Claude (default: yes)"
        ),
    )
    set_seat = commands.add_parser(
        "set",
        help=(
            "write one seat, or the fallback, for every repository on this machine "
            "(global) or for this one on this machine (local)"
        ),
    )
    set_seat.add_argument("scope", metavar="global|local")
    set_seat.add_argument("name", metavar="|".join(SET_NAMES))
    set_seat.add_argument(
        "words", nargs="+", metavar="AGENT/MODEL:EFFORT|default|false"
    )
    plan_file = commands.add_parser(
        "plan-file",
        help="the name a task's plan takes, and the plan the plans folder holds",
    )
    plan_file.add_argument("slug")
    plan_file.add_argument(
        "--date",
        metavar="YYYY-MM-DD",
        help="the day the plan is written (default: today, in UTC)",
    )
    rules = commands.add_parser("rules")
    rules.add_argument("files", nargs="*", metavar="FILE")
    rules.add_argument(
        "--range",
        dest="commits",
        metavar="BASE..TIP",
        help="also the files this range of commits changes",
    )
    task_dir = commands.add_parser("task-dir")
    task_dir.add_argument("slug")
    task_dir.add_argument("--ask", help="the owner's words for this task, as given")
    task_dir.add_argument(
        "--ticket",
        help=(
            "the id of the tracker's ticket the ask came from: MBZ-12 for Linear, "
            "42 or #42 for GitHub"
        ),
    )
    task_dir.add_argument(
        "--ticket-repo",
        metavar="OWNER/REPO",
        help=(
            "with a GitHub issue: the repository of the issue that was read, "
            "from its address"
        ),
    )
    task_dir.add_argument(
        "--branch",
        help=(
            "the branch the task takes, when it is not TYPE/SLUG (a tracker's name, "
            "the project's own scheme)"
        ),
    )
    task_dir.add_argument(
        "--night",
        metavar="YYYY-MM-DD",
        help="the night that opens the task, which then runs without the owner",
    )
    state = commands.add_parser("state")
    state.add_argument("slug")
    state.add_argument("status")
    state.add_argument("lines", nargs="+", metavar="LINE")
    state.add_argument(
        "--start-over",
        action="store_true",
        help=(
            "ready over a task in landing or open: its landing starts over, as "
            "land.py's message says"
        ),
    )
    seat_now = commands.add_parser(
        "seat",
        help=(
            "the seat in use for a task: the fallback while it stands in, else the "
            "seat the settings name"
        ),
    )
    seat_now.add_argument("slug")
    seat_now.add_argument("seat", metavar="|".join(SEATS))
    failed = commands.add_parser(
        "seat-failed",
        help=(
            "a seat's agent gave an error: the fallback stands in for it, or the task "
            "is blocked for the owner"
        ),
    )
    failed.add_argument("slug")
    failed.add_argument("seat", metavar="|".join(lem_state.SEAT_NAMES))
    failed.add_argument(
        "--seat",
        dest="line",
        required=True,
        metavar="AGENT/MODEL:EFFORT",
        help="the seat the stage opened, as `lem project seat` printed it",
    )
    failed.add_argument(
        "--error",
        required=True,
        metavar="|".join(lem_state.SEAT_ERRORS),
        help=(
            "missing: the program is not on the Mac; login, tokens, model: "
            "the agent's own message of no login, no tokens or an unknown model"
        ),
    )
    failed.add_argument(
        "--said",
        metavar="TEXT",
        help="the agent's own line of the error, kept in the event",
    )
    commands.add_parser(
        "seat-again",
        help=(
            "the owner's go on over a task a seat's error blocked: "
            "the seat the settings name is tried again"
        ),
    ).add_argument("slug")
    commands.add_parser("tasks")
    commands.add_parser(
        "resume",
        help=(
            "bring a parked task back on the owner's word, or open a new task from a "
            "dropped one's handoff or notes and its branch"
        ),
    ).add_argument("slug")
    owner = commands.add_parser(
        "owner",
        help=(
            "the owner says that he is away, or back again, for every repository on "
            "this machine; watch waits for his next word"
        ),
    )
    owner.add_argument("status", metavar="away|back|watch")
    owner.add_argument("--words", help="the owner's words as typed (away and back)")
    owner.add_argument(
        "--seen",
        type=int,
        metavar="N",
        help=(
            "watch: the number of records in the owner's mark, "
            "owner.seen of `lem project waiting`"
        ),
    )
    owner.add_argument(
        "--every",
        type=int,
        default=OWNER_WATCH_SECONDS,
        metavar="SECONDS",
        help=(
            "watch: seconds between two looks at the mark (default "
            f"{OWNER_WATCH_SECONDS}); for a test that cannot wait"
        ),
    )
    step = commands.add_parser("ticket-step")
    step.add_argument("slug")
    step.add_argument("step")
    step.add_argument(
        "--login",
        help="with the step assigned: the login Lem adds as the issue's assignee",
    )
    log = commands.add_parser("log")
    log.add_argument("slug")
    log.add_argument("event")
    log.add_argument("fields", nargs="*", metavar="key=value")
    commands.add_parser("may-start").add_argument("slug")
    commands.add_parser("state-dir")
    commands.add_parser("waiting", help="everything that waits for the owner, as JSON")
    proposals = commands.add_parser(
        "proposals",
        help=(
            "the records of the night's and the retro's proposals, the reviewer's "
            "verdicts, and the owner's drop of an item"
        ),
    )
    acts = proposals.add_subparsers(dest="act", required=True)
    add = acts.add_parser(
        "add",
        help=(
            "add a run's proposals to the record of its day, "
            "which this makes when it is not there"
        ),
    )
    add.add_argument(
        "--kind",
        required=True,
        choices=tuple(PROPOSAL_KINDS),
        help="the run: the retro or the night",
    )
    add.add_argument(
        "--date", metavar="YYYY-MM-DD", help="the run's day (default: today, in UTC)"
    )
    add.add_argument(
        "--file",
        required=True,
        metavar="FILE|-",
        help='the run as JSON, {"read": TEXT, "proposals": [...]}, or - for stdin',
    )
    acts.add_parser(
        "read",
        help=(
            "every proposal with no verdict, of any day, with the refuted, passed and "
            "dropped ones, and the newest run of each kind"
        ),
    )
    verdict = acts.add_parser(
        "verdict",
        help=(
            "the reviewer's verdict on each proposal; the passed ones of one area "
            "become one item of the state folder's backlog"
        ),
    )
    verdict.add_argument(
        "--file",
        required=True,
        metavar="FILE|-",
        help=(
            'the verdicts as JSON, {"verdicts": [...], "titles": {AREA: '
            "TITLE}}, or - for stdin"
        ),
    )
    acts.add_parser(
        "drop",
        help=(
            "the owner's drop of a reviewer's item, refused while a task that "
            "has not ended holds it"
        ),
    ).add_argument("path", metavar="PATH")
    serial = commands.add_parser(
        "serial",
        help=(
            "run one test command that two tasks cannot run at the same time, under "
            "the repository's one lock"
        ),
    )
    serial.add_argument("words", nargs=argparse.REMAINDER, metavar="-- COMMAND")
    commands.add_parser("may-nap")
    prune = commands.add_parser(
        "prune",
        help=(
            f"remove what the state folder no longer needs, older than {KEEP_KEY} days"
        ),
    )
    prune.add_argument(
        "--dry-run", action="store_true", help="remove nothing: say what would go"
    )
    prune.add_argument(
        "--days",
        type=int,
        metavar="N",
        help=f"with --dry-run: what would go if {KEEP_KEY} were N",
    )
    load_gate = commands.add_parser(
        "load",
        help=(
            "the load average under which the checks of a landing start on this "
            "machine, and the load now"
        ),
    )
    load_gate.add_argument(
        "--start",
        metavar="N|none",
        help=(
            "set the number for every repository on this machine "
            f"({lem_state.LOAD_START} when none is set), or none to take the gate away"
        ),
    )
    handoff = commands.add_parser(
        "handoff",
        help=(
            "the number of tokens past which a task's session compacts itself, for "
            "every repository on this machine"
        ),
    )
    handoff.add_argument(
        "--tokens",
        metavar="N|default",
        help="set the number: 0 leaves it to Claude Code, default takes the line out",
    )
    args = parser.parse_args(argv)
    if problem := unreadable_argument(sys.argv[1:] if argv is None else argv):
        sys.exit(f"project.py: {problem}")
    try:
        root = repo_root(Path(args.repo))
        stopped = release_refusal(root, args)
        if stopped:
            raise SettingsError(stopped)
        if args.command == "init":
            cmd_init(root, args.base, args.codex)
            return
        if args.command == "set":
            print(
                json.dumps(cmd_set(root, args.scope, args.name, args.words), indent=2)
            )
            return
        if args.command == "task-dir":
            cmd_task_dir(
                root,
                args.slug,
                args.ask,
                args.ticket,
                args.branch,
                args.night,
                args.ticket_repo,
            )
            return
        if args.command == "state":
            print(
                json.dumps(
                    cmd_state(
                        root,
                        args.slug,
                        args.status,
                        args.lines,
                        start_over=args.start_over,
                    )
                )
            )
            return
        if args.command == "resume":
            print(json.dumps(cmd_resume(root, args.slug), indent=2))
            return
        if args.command == "seat":
            print(json.dumps(cmd_seat(root, args.slug, args.seat), indent=2))
            return
        if args.command == "seat-failed":
            print(
                json.dumps(
                    cmd_seat_failed(
                        root, args.slug, args.seat, args.line, args.error, args.said
                    ),
                    indent=2,
                )
            )
            return
        if args.command == "seat-again":
            print(json.dumps(cmd_seat_again(root, args.slug), indent=2))
            return
        if args.command == "tasks":
            print(json.dumps(read_tasks(root), indent=2))
            return
        if args.command == "owner" and args.status == "watch":
            if args.seen is None:
                raise SettingsError(
                    "watch takes --seen N, the number of records in the owner's mark: "
                    "`lem project waiting` gives it as owner.seen"
                )
            if args.words is not None:
                raise SettingsError(
                    "watch takes no --words: it reads the owner's status, and only "
                    "away and back write it"
                )
            print(json.dumps(cmd_owner_watch(root, args.seen, max(1, args.every))))
            return
        if args.command == "owner":
            if args.seen is not None:
                raise SettingsError(
                    f"--seen belongs to watch, not to {args.status}: "
                    "`lem project owner watch --seen N`"
                )
            print(json.dumps(cmd_owner(root, args.status, args.words)))
            return
        if args.command == "log":
            cmd_log(root, args.slug, args.event, args.fields)
            return
        if args.command == "ticket-step":
            cmd_ticket_step(root, args.slug, args.step, args.login)
            return
        if args.command == "state-dir":
            print(state_root(root))
            return
        if args.command == "waiting":
            print(json.dumps(cmd_waiting(root), indent=2))
            return
        if args.command == "proposals":
            print(
                json.dumps(proposals_command(root, args), indent=2, ensure_ascii=False)
            )
            return
        if args.command == "serial":
            sys.exit(cmd_serial(root, args.words))
        if args.command == "may-nap":
            cmd_may_nap(root)
            return
        if args.command == "prune":
            answer, code = cmd_prune(root, dry=args.dry_run, days=args.days)
            print(json.dumps(answer, indent=2))
            if code:
                sys.exit(code)
            return
        if args.command == "load":
            print(json.dumps(cmd_load(args.start), indent=2))
            return
        if args.command == "handoff":
            print(json.dumps(cmd_handoff(args.tokens), indent=2))
            return
        settings = load(root)
        if args.command == "rules":
            cmd_rules(settings, args.files, args.commits)
            return
        if args.command == "show":
            print(json.dumps(settings, indent=2))
        elif args.command == "path":
            cmd_path(settings, args.name)
        elif args.command == "worktree-dir":
            cmd_worktree_dir(settings, args.slug)
        elif args.command == "worktree":
            print(
                json.dumps(
                    cmd_worktree(root, settings, args.slug, args.branch), indent=2
                )
            )
        elif args.command == "plan-file":
            cmd_plan_file(settings, args.slug, args.date)
        elif args.command == "may-land":
            cmd_may_land(settings, args.branch)
        else:
            cmd_may_start(settings, root, args.slug)
    except ItemRefused as error:
        print(
            json.dumps(
                {**error.answer, "said": str(error)}, indent=2, ensure_ascii=False
            )
        )
        sys.exit(f"project.py: {error}")
    except SettingsError as error:
        sys.exit(f"project.py: {error}")


def proposals_command(root: Path, args: argparse.Namespace) -> dict:
    """`lem project proposals ACT`: the day is today in UTC, as the time of a run is."""
    state = state_root(root)
    now = datetime.now(UTC)
    if args.act == "read":
        return cmd_proposals_read(state)
    if args.act == "drop":
        return cmd_proposals_drop(state, args.path, now.date().isoformat())
    where = "stdin" if args.file == "-" else args.file
    try:
        text = sys.stdin.read() if args.file == "-" else text_of(Path(args.file))
    except OSError as error:
        raise SettingsError(
            f"--file {args.file}: {error.strerror or error}; "
            "give the file the JSON is in, or - for stdin"
        ) from None
    spec = spec_of(text, where)
    if args.act == "add":
        return cmd_proposals_add(
            state, args.kind, args.date or now.date().isoformat(), spec, now
        )
    return cmd_proposals_verdict(state, spec, now.date().isoformat())


if __name__ == "__main__":
    main()
