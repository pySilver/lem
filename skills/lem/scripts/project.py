#!/usr/bin/env python3
"""Say where one repository keeps what Lem reads, and what its flow settings are.

Every project keeps its own settings in its repository: what the project is, its style guide, its
personas, its review configuration, its lessons, the machine checks of a landing, and what must
never go wrong there. `.lem/project.toml` at the root of the checkout names them. A project that keeps a cast or a profile where an older tool already reads them
(`.personas`), or its worktrees, may point at them there (`init --existing link`), so adopting the skill moves
nothing, or start the skill's own layout beside them (`init --existing new`). Which of the two is
the owner's choice, so `init` refuses to guess it. The rules an agent already loads by itself
(`.claude/rules`) are no choice: they are the style guide, where they are.

    lem project show                everything, resolved, as JSON
    lem project path NAME           one path, absolute
    lem project may-land BRANCH     exit 1 unless tasks of this project may land on BRANCH
    lem project existing            the folders an older tool already reads here, as JSON
    lem project init [--base NAME] [--existing link|new] [--reviewer claude|codex]
                                    write .lem/project.toml
    lem project reviewer AGENT[/MODEL[:EFFORT]]
                                    who reviews on this machine, until `reviewer default`
    lem project reviewer default    the project's own reviewer again
    lem project rules [FILE ...] [--range BASE..TIP]
                                    the style guide files that cover these files, as JSON
    lem project task-dir SLUG [--ask TEXT] [--ticket ID] [--branch NAME]
                                    make and print one task's state directory; keep the owner's words
                                    and the ticket the ask came from. At a task's opening it refuses
                                    a slug whose branch origin has already: TYPE/SLUG for every
                                    type, or the NAME --branch gives
    lem project ticket-step SLUG started|commented|landed|dropped|answered
                                    write down what Lem did to the task's ticket, once
    lem project worktree-dir SLUG   print where the task's worktree goes, inside a folder git ignores
    lem project worktree SLUG BRANCH
                                    make the task's worktree there, on BRANCH: a branch that exists
                                    as it is, a new one from origin's base branch after a fetch
                                    (from the local base branch with no remote, or when origin
                                    does not answer), with no upstream
    lem project state SLUG STATUS LINE...
                                    put a new block at the top of the task's state.md, with the time
    lem project tasks               every task's ask, status and newest state block, as JSON
    lem project log SLUG EVENT [key=value ...] [key:=json ...]
                                    append one event about a task to the log the board draws
    lem project may-start SLUG      exit 1 when as many other tasks build or land as flow.max_tasks
                                    allows; the task SLUG, whose lead starts, is not counted. Also
                                    exit 1 for a task in `landing`, `open` or an ended state, which
                                    gets no lead, and for a task `queued` with an `after: OTHER`
                                    line while OTHER has not ended
    lem project state-dir           the folder that holds every task, the event log and the night reports
    lem project alone -- COMMAND ...
                                    run one command that needs the machine to itself, under the
                                    repository's one lock for such commands
    lem project waiting             everything that waits for the owner, as JSON: each choice of a task,
                                    each task whose criteria or a step of his hold it, each pull
                                    request with green or not, each plan drafted at night, each
                                    retro's proposals
    lem project plan-file SLUG [--date YYYY-MM-DD]
                                    the name a task's plan takes (`paths.plan_file`), and the plan
                                    of the task the plans folder holds, as JSON
    lem project may-nap             whether a nap may start now, as JSON, and when it may, the nap is
                                    written down as started; it also removes the naps older than
                                    naps.keep_days

Task state is kept in `.lem/state/` of the main checkout, the one folder `lem_state.py` names for
every script: every worktree writes there, git never tracks it, a worktree's removal does not take
it, and a session that replaces another finds it. A state folder an older Lem kept in the git
directory (`.git/lem/`) is moved there by the first script that reads it, which says so in one
line on stderr.

An ended task stays ended. `state` refuses a move out of `landed`, `answered` or `dropped` (the
same status again is taken), so that a stale wake-up, a lead that finished after a later step,
cannot reopen it: new work for it is a new ask, with a slug of its own.

Every state block is also an event. `events.jsonl` in the state folder is the record, one JSON
object per line: `ts` (UTC to the second), `event`, `task`, then the event's fields. The same
record goes to `events.js` as a `lemEvent({...});` line, because the board is a file:// page: it
cannot read a file with fetch, and it can load a script (measured in agterm 0.34.0 by the monitor
this one follows). `state` writes `task.state` with the status, the lines, the ask, the limit and
the branch and newest commit of the task's worktree, so the board needs no agent to remember a
second command. `log` writes any other event: `key=value` stores a string and `key:=value` parses
JSON, so a commit made only of digits stays a string and an exit code stays a number. The start
of each stage that logs its end has a fixed form (`STARTS`: `interview.start`, `scout.start` and
`scout`, `criteria.read.start`, `investigation.start`, `builder.start`, and the three `land.py`
writes, `polish.start`, `gate.start` (the start of the checks, by the step's older name) and `review.start`), so that the board draws each span from
its start to its end. Four more events have a fixed form. `plan.talk.start`, which the defender of a careful or large plan writes when
the reviewer's seat opens, as `reviewer=AGENT`, so that the board draws the talk from its start.
`plan.talk`, which the landing reads and the plan's defender writes after the talk, as
`reviewer=AGENT turns:=N questions:=N settled:=N open:=N repaired:=N design:=N unargued:=N
root:=N layer:=N shared:=N`: the turns, the questions of the reviewer's first list, how many of
them were settled and left open (the two add up to questions), how many the defender repaired,
how many of the open ones are a design choice, how many were raised after the list and not
argued, how many repairs changed a decision of the plan and how many put a layer over a decision
with a cite (the two add up to at most the repairs), and how many decisions two questions named.
The rules of a talk keep it within 4 × questions + 2 turns; a record over that bound is taken as
it ran, and `log` adds the bound to it as `bound`, for the landing and the board to say that the
talk went over. `tasks` gives each task
its newest `plan.talk` as `talk`, the record Lem and a builder read before the build of a
careful or large plan.
And `criteria.read`, which Lem or the lead writes after the personas read the acceptance
criteria, as `by=lem|lead asked:=N answered:=N families:='["FAMILY", ...]' silent:='[{"name": ...,
"why": ...}]' criteria:=N flagged:=N split:=true|false digest=DIGEST`: who ran the read, how many
personas were asked and how many answered, the model families that answered, each source that did
not and why (a partial read counts), how many criteria were read and how many an answer flagged,
whether the families split, and the digest `lem criteria digest` gives for the criteria read. A
read in which nobody answered is written too, with `answered:=0`, no family and each source that
was asked in `silent`; the landing counts two of those in a row as criteria that went on unread.
`log` refuses the names an older Lem gave the read and its start, `stories.read` and
`stories.read.start`, with the name of now; the landing still reads the events an older Lem wrote.
`investigation`, which Lem writes after it reads the investigator's report of a fix or a
question, as `type=fix|question call=CALL line=TEXT [where=PATH:SYMBOL]
[reproduced:=true|false]`: a fix's call is small, full, not-a-bug or not-reproduced, and it says
whether the bug was reproduced; a plain cause names its place; a question's call is answer.
`tasks` gives each task its newest as `investigation`, and `state SLUG answered` refuses a task
with no `investigation.md` and no record whose call is not-a-bug or answer. A record an older Lem
wrote (`kind=bug|investigation`, the calls correction and usual) is given in the form of now.

A state line that starts with `type:` names the type of the request with its reason, as `type:
fix, because the total is wrong today`, one of feat, fix, docs, refactor, perf, test, chore and
question; `state` refuses any other, and `tasks` gives the newest as `type`. A `kind:` line, which
an older Lem wrote, is refused by `state` with the type line to write, and read by `tasks` as the
type its kind maps to (bug and correction a fix, feature a feat, investigation a question).

`.lem/project.local.toml` is one person's or one day's choice on one machine: who sits in the
reviewer's pane (the usual reviewer is down, or out of tokens) and on which model the defender of
a plan talk runs, which tool marks up a plan and which one puts a question to the owner, a no to the correction queue for that one person, a no
to the naps, which spend that person's tokens, and how many tasks build or land at one time on that machine. It
is not committed (`init` writes `.lem/.gitignore` for it), and it is read from the main checkout,
because a task's worktree has no copy of a file git does not track. It may hold `[seats]` and
`[tools]`, `[corrections]` with `collect = false`, `[naps]` with `on = false` and `[flow]` with
`max_tasks`, which is one machine's limit and no guard, and nothing else: the checks, what must
never go wrong, the protected branches and who lands are the project's rules, and a file nobody reviews
must not open them. For the same reason it can switch the correction queue and the naps off
for its person and never on: nobody's messages are sent, and nobody's tokens spent, because of a
file that git does not show. `show` names each setting that
came from it.

The style guide is a folder of markdown files, in an adopted project the one an agent already
loads by itself (`.claude/rules`), which Lem reads and never moves; when `.lem/styleguide` holds
rules beside it, `rules` reads both folders, and `folders` in its answer names them. A file scopes itself to paths
in its frontmatter, in Claude Code's form (`paths:` with a list of globs), and a file without
that covers every path. `rules` is the one place that matches a change against those scopes: a
builder's brief, the message to the reviewer and a review round all get its answer, so an agent
that does not load the folder by itself reads the same rules as one that does.

What must never go wrong is `flow.topics`: sentences in the owner's words, against which an agent
reads an ask, a plan and a diff. No list of paths says whether a change is careful: such a list
goes stale as the code moves, misses new code, and a branch can edit the list that guards it.
`flow.careful` is refused, with the sentence to write in its place. The `[flow]` table is read
from the main checkout's settings, also in a task's worktree, as the checks are read by the
landing: a branch that empties its topics or shortens the owner's wait lifts nothing, since every
lead, reviewer and landing reads the table as the main checkout has it. The table the branch writes
is still checked, so that its error shows before it lands. `[naps]` is read the same way: a nap
spends the tokens of whoever works on the machine, and a branch does not switch them on.

The main checkout's settings are its working tree's `.lem/project.toml` while it is on the base
branch: an edit of the owner's there counts at once, committed or not. When another branch is
checked out there (a colleague's, `gh pr checkout 57`), the file is read as the base branch's
newest commit holds it (`git show BASE:.lem/project.toml`), with one line on stderr when the two
differ, so that branch does not change who lands and what is careful for every running task. The
base is the branch the file names: the file of the remote's default branch is read first, then
the one of the branch the main checkout's own copy names, and a file that names another base is
read on that one. Before any commit of the base holds the file (an onboarding, on its own branch),
the working tree is read. `show` says which in `settings_from`.

`[checks]` holds the machine checks of a landing: `commands`, the whole suite, `setup`, `ignores`
and `bar`. `checks.alone` names the commands that need the machine to themselves: an end-to-end suite that
uses fixed ports, one database or a browser. `alone` runs any command under one lock for the
repository, `alone.lock` in the state folder, apart from the landing's lock, since a builder takes
this one too: the checks of a landing run each `checks.alone` command through it after
`checks.commands` pass, `lem criteria red` runs a criterion's test of such a suite through it, and a
builder runs such a test through it in its worktree. It waits while another run holds the lock
and says so on stderr with the holder's line, passes the command's exit status through (128 and
the signal's number for a command a signal ended), and ends the command's process group when it
is stopped. The lock is the kernel's: it goes with the process that holds it, however that ends,
so a file a dead run left blocks nothing. One word list after `--` runs as it is; one quoted line
runs in the shell, as a command of the checks does.

A seat is one string, `agent/model:effort`: `seats.reviewer`, the agent in the reviewer's pane;
`seats.planner`, the defender of a plan talk; and `seats.experts`, the two experts of a choice
that waits for the owner. The effort may be left out (`codex/gpt-6.1-sol`), and so may the model
(`codex`, `codex:high`): the part left out is that agent's own default, and Lem passes nothing for
it. `show` gives each seat parsed, as `agent`, `model`, `effort` and the `seat` as written.

A file with the tables of an older Lem, `[gate]` (the checks' older name), `[seats.reviewer]` (with
`agent`, `model` and `plan_effort`) or `[seats.planner]`, is refused once, with every such table
named and the whole text to write in their place.

A plan's file is named by `paths.plan_file`, a pattern of the tokens `YYYY`, `MM`, `DD` and
`<slug>`, `YYYY-MM-DD-<slug>.md` unless the settings say otherwise. A task's plan is found by it; a plan named `YYYYMMDD-<slug>.md`, as an older Lem
named it, is found too: `lem_plans` is the one place that builds and finds the name, and `plan-file` prints both.

`waiting` is the one list of what waits for the owner, which a bare `/lem` says: the choices of
`lem decisions pending` (`choices`), the tasks `held` with the line `the criteria wait for the
owner` (`criteria`) and the other `held` ones, a step of his or one more fact (`held`), each `open`
task with its proposal (`pull_requests`, with `conflict`: true or false as the forge said it of the
pushed head at the last `lem land merged`, null when nothing asked or the head moved since), each `drafted` task with its plan (`drafts`), and each
file of a retro's proposals in `retros/` of the state folder (`retros`), which a retro started
with nobody at the terminal writes in the form Lem's question page takes, one question for each
proposal. `count` adds them up. It reads and writes nothing else.

A nap is an optional part (`[naps]`, off unless the owner says yes): a fresh agent that reads the
recent tasks, dreams, and writes the dream down in a folder of its own, `naps/TIME-WORDS/` in the
state folder, where TIME is the clock's UTC time when the nap started, as `YYYY-MM-DD-HHMM`.
`may-nap` is the one place that says whether one may start: the naps are on, no nap runs, and the newest one started `naps.gap_hours` ago or more, or there is
none. A nap runs from its start until its folder holds `waking.md`, the last file it writes, and
for an hour at most (`ASLEEP_MINUTES`). Its answer is JSON with exit 0 whether it says yes or
no, because a no is the usual answer and nothing is wrong; a broken settings file is exit 1. A
yes writes `naps/.asleep` with the start, so a second call finds the nap that runs. Each call
removes the nap folders whose time is older than `naps.keep_days` days, and names them in
`removed`; a folder whose name has no such time is never removed.

A settings file with an unknown key, a wrong type or a path outside the repository is an error:
a stage that read half of it would run on defaults nobody chose. Needs Python 3.11 for tomllib.
"""

from __future__ import annotations

import sys

if sys.version_info < (3, 11):
    # an old python3 must still load this file, so that it can say what it needs and not a traceback
    sys.exit(f"project.py: Lem needs Python 3.11 or newer, and this python3 is {sys.version.split()[0]}; put a newer one first on PATH, or run this file with it")

import argparse
import difflib
import fcntl
import json
import os
import re
import signal
import shutil
import subprocess
import tomllib
from datetime import datetime, timezone
from pathlib import Path

# The one place that says where the state is, shared with the scripts that cannot import this file.
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lem_plans  # noqa: E402
import lem_state  # noqa: E402

# A role a developer may give to a tool of their own -> the tool Lem uses for it unless the
# settings say otherwise. The one place that names each. `lem-ask` comes with Lem; `webrev` is a
# recommended tool the developer installs (the machine check has its row and its guide).
TOOLS = {"annotate": "webrev", "ask": "lem-ask"}
SETTINGS = Path(".lem") / "project.toml"
LOCAL = Path(".lem") / "project.local.toml"
# the tables one machine may set for itself; of [flow] only max_tasks, of [naps] only `on = false`,
# and of [corrections] only `collect = false`
LOCAL_TABLES = ("seats", "tools", "corrections", "flow", "naps")
# name -> (where the skill's own layout keeps it, where an older tool keeps it)
PATHS: dict[str, tuple[str, str | None]] = {
    "profile": (".lem/profile.md", ".personas/profile.md"),
    "styleguide": (".lem/styleguide", ".claude/rules"),
    "personas": (".lem/personas", ".personas/cast"),
    # the review tool's own folder, where that tool reads it: another program's settings stay where they are
    "review": (".revmux", None),
    "lessons": (".lem/lessons.md", None),
    "rulings": ("docs/rulings", None),
    "backlog": ("docs/backlog", None),
    "plans": ("docs/plans", None),
    "worktrees": (".lem/worktrees", ".claude/worktrees"),
}
LAND = ("owner", "agent")
# How a task's branch reaches the base branch: its own commits, or one commit for the whole branch.
HISTORY = ("keep", "squash")
# How a task that has a forge ends: a pull request there, or a merge into the base branch with
# none, for a developer who wants no pull requests. With no forge it is always the merge.
PROPOSE = ("pull-request", "merge")
# the agents that can sit in the reviewer's pane
REVIEWERS = ("claude", "codex")
# A seat is one string, `agent/model:effort` (the owner, 2026-11-17: "I personally prefer
# `codex/gpt-6.1-sol:high`"). A model and an effort are not checked against a list: their names
# change with each release of an agent's command, and that command refuses a wrong one loudly when
# it starts. A part left out is the agent's own default, and Lem passes nothing for it.
SEAT_FORM = "agent/model:effort"
SEAT_KEYS = ("agent", "model", "effort")
# The defender's seat: the agent Lem starts in the companion of a plan talk, which defends the
# plan against the reviewer. Only Claude Code, because the harness was checked in no other agent.
PLANNERS = ("claude",)
# The experts of a choice that waits for the owner: two, because the record of a choice holds two
# answers (`decisions.py advise --expert fable|astra`): the first seat answers in the place named
# `fable`, the second in the place named `astra`. The default is what `harness/claude-code.md`
# ran before the seats named them: Fable as a Claude Code subagent at the agent's own effort, and
# GPT-6 Astra through Codex at high.
EXPERTS = ("claude/fable", "codex/gpt-6-astra:high")
EXPERT_PLACES = ("fable", "astra")
# seat -> (the agents that may sit in it, why only those, an example of the line)
SEATS = {
    "reviewer": (REVIEWERS, "the agents that can sit in the reviewer's pane", "codex/gpt-6.1-sol:high"),
    "planner": (PLANNERS, "the harness was checked in Claude Code only", "claude/opus:high"),
}
# The keys the tables of an older Lem had for each seat, read only to write the refusal's line:
# `[seats.reviewer]` with `plan_effort` as its effort, and `effort`, the effort for the review of a
# diff, which no step used (audit W7, 2026-11-16); `[seats.planner]` with `effort`.
OLD_SEAT_EFFORT = {"reviewer": "plan_effort", "planner": "effort"}
# A plan's file name: its default, and its tokens; `lem_plans` builds and finds the name.
PLAN_FILE = lem_plans.PLAN_FILE
PLAN_TOKENS = lem_plans.TOKENS
# a task's slug: plain words joined by hyphens, e.g. report-dates-stay-whole
SLUG = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
# What a task's newest state block may say, and who acts next:
#   queued    the ask is written and no lead runs yet: the limit was reached, or its `after:` line names the task it needs
#   building  a lead plans or builds
#   planned   the plan is committed and nothing builds it: it needs its talk, or a builder after the talk, or the owner reads it
#   held      it waits for the owner on what is no decision with options: the criteria, one more fact, a
#             step of his, or an irreversible choice every task left needs; a decision of his is a choice
#   blocked   the lead stopped on something the coordinator has to settle
#   ready     the report is written and the branch waits for its checks
#   landing   the checks and the read run on it, or a builder repairs what they or the base showed
#   open      it is proposed: a pull request is open, or the branch is ready to land, and it waits for the merge
#   landed    it is on the base branch
#   drafted   a plan written at night that waits for the owner's word
#   dropped   nobody will build it
#   answered  it ended with a report and nothing to merge: a question answered, or a bug that is none
STATES = ("queued", "building", "planned", "held", "blocked", "ready", "landing", "open", "landed", "drafted", "dropped", "answered")
# The states a task does not leave: its files stay under its slug, and nothing of it waits.
ENDED = ("landed", "dropped", "answered")
# The states of a task that is with its landing: the checks run on it, or it is proposed.
WITH_LANDING = ("landing", "open")
# The states only a lead, or the start or the queue of a task, writes. None comes over a task with its
# landing: there it is a lead that woke late. `ready` does with `--start-over`, which only the way out
# that land.py names gives: a landing that cannot go on, or whose record is broken, starts over.
# `held` is not here: Lem writes it over `landing` when the checks find a small change to be a full
# change, and the interview of a full change starts with it (`stages/new.md`, "A small change").
LEADS_WRITE = ("queued", "building", "planned", "ready", "drafted")
# The type of a request, which Lem takes from the request's words alone (`stages/new.md`, "Open the
# task"): a Conventional Commits type, and `question` for a task that ends with an answer and commits
# nothing. A state line `type: TYPE, because WHY` says it; no code matches a request's words against
# them. The size of a request (a small change or a full change) is no type: a small change has the
# state line `small change: one builder`.
TYPES = ("feat", "fix", "docs", "refactor", "perf", "test", "chore", "question")
TYPE_LINE = re.compile(r"type:\s*(?P<type>[^,\s]+)\s*(?:,\s*because\s+(?P<why>.+))?")
# The line an older Lem wrote for the same, `kind: KIND, because WHY`, and the type each of its kinds
# reads as. `tasks` still reads it in a state.md that an older Lem wrote, and `state` refuses it with
# the type line to write. A later change may drop it once no task whose state holds such a line is open.
OLD_KIND_LINE = re.compile(r"kind:\s*(?P<kind>[^,\s]+)\s*(?:,\s*because\s+(?P<why>.+))?")
OLD_KINDS = {"bug": "fix", "feature": "feat", "correction": "fix", "investigation": "question", "chore": "chore", "docs": "docs"}
# What the investigation of a fix or of a question found, as `log investigation` takes it: the call
# that sets the task's next path (`stages/investigate.md`). A fix goes on as a small
# change or a full change, or it is no bug; two of the calls end the task with its report, as `answered`.
CALLS = {"fix": ("small", "full", "not-a-bug", "not-reproduced"), "question": ("answer",)}
ANSWERING = ("not-a-bug", "answer")
# The record an older Lem wrote for an investigation: `kind=bug|investigation`, and the calls
# `correction` and `usual` for what are now `small` and `full`. `tasks` gives such a record in the
# form of now, and `log` refuses the old form with the new one. A later change may drop it once no
# task with such a record is open.
OLD_INVESTIGATION_KINDS = {"bug": "fix", "investigation": "question"}
OLD_CALLS = {"correction": "small", "usual": "full"}
# The states in which the task loads the machine: a lead builds, or the checks run and a builder may
# repair a conflict or a red check.
RUNNING = ("building", "landing")
# The lock of the commands that need the machine to themselves (`alone`), in the state folder. Not the
# landing's `landing.lock`: a builder takes this one too, while another task holds the landing line.
ALONE_LOCK = "alone.lock"
# The first line of a state block: the time in UTC, the status, one line of text.
STATE_LINE = re.compile(r"(?P<since>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z) (?P<status>[a-z]+): (?P<text>.+)")
# How many tasks build or land at one time when the settings do not say. Four to five ran well on one Mac;
# six gave a load average of 12 to 16 and unstable browser tests (convertiser-server, as its owner
# reported it on 2026-11-14). The right number depends on the machine and on the project's tests.
MAX_TASKS = 4
# How many minutes a choice of the build waits for the owner before the recommended action is
# taken. The owner's own number: "if there is decision taken in 15 min" (2026-11-16).
DECISION_WAIT = 15
# How many seconds the watch of the open pull requests (`land.py watch`) waits between two looks at
# the forge. A guess (2026-11-17), not a measurement: a merge shows on the board within a minute,
# and one call of the forge a minute stays far under its limits.
WATCH_SECONDS = 60
TABLES: dict[str, tuple[str, ...]] = {
    "paths": (*PATHS, "plan_file"),
    "branch": ("base", "land", "history", "propose", "protected"),
    "checks": ("commands", "ignores", "setup", "bar", "alone"),
    "flow": ("topics", "max_tasks", "decision_wait", "watch_seconds"),
    "seats": ("reviewer", "planner", "experts"),
    "tools": tuple(TOOLS),
    "corrections": ("collect",),
    "tracker": ("kind", "server", "workspace", "team", "moves", "started", "landed"),
    "naps": ("on", "keep_days", "gap_hours"),
}
# The trackers Lem has a skill for, and who may move a ticket's status: Lem, or the tracker's own
# automation (a pull-request integration that moves a ticket by itself).
TRACKERS = ("linear",)
MOVES = ("lem", "tracker")
# a ticket's id as a tracker writes it, e.g. MBZ-12
TICKET = re.compile(r"[A-Za-z][A-Za-z0-9]*-[0-9]+")
# What Lem did to a task's ticket, each written down after the tracker took it, so that a step is
# never done twice and a session that was cut off can see what is still owed:
#   started    the ticket got the status for work that started
#   commented  the landing was commented on the ticket
#   landed     the ticket got the status for work that landed
#   dropped    the ticket got the comment that its task was dropped
#   answered   the ticket got the comment with its task's answer: not a bug, or the answer to a question
TICKET_STEPS = ("started", "commented", "landed", "dropped", "answered")
# The ended states that give a task's ticket back: a new task may take it. A landed task keeps it.
RETURNED = ("dropped", "answered")
# The naps (`may-nap`). Both numbers are guesses, not measurements: the owner said "a week or a
# month (?)" of history is worth keeping, and his own nap routine runs three times a day.
NAPS_KEEP_DAYS = 30
NAPS_GAP_HOURS = 6
# How long a nap that wrote no `waking.md` counts as running. A guess: the owner's own routine
# leaves a nap "about twenty minutes", and an hour is three of those.
ASLEEP_MINUTES = 60
# a nap's folder: the clock's time when it started, then a few words of the dream
NAP_NAME = re.compile(r"(?P<time>\d{4}-\d{2}-\d{2}-\d{4})(?:-.+)?")
NAP_TIME = "%Y-%m-%d-%H%M"
ASLEEP = ".asleep"

TEMPLATE = """\
# What Lem reads in this repository. `project.py show` prints it resolved.

[paths]
# Where each kind of setting lives, relative to the root of the checkout.
{paths}
# The name of a plan's file in the plans folder: YYYY, MM and DD are the day the plan was
# written, <slug> is the task's. A plan named YYYYMMDD-<slug>.md is found too.
plan_file = "{plan_file}"

[branch]
# The branch a task starts from and lands on.
base = "{base}"
# Who lands a finished task: "owner", or "agent", which lands only a request that is green and
# that the review called not careful; the owner lands every other one.
land = "owner"
# What lands: "keep" lands the branch's own commits, "squash" lands one commit for the whole task.
history = "keep"
# How a task ends where the remote is GitHub: "pull-request" opens one there, "merge" lands the
# branch on the remote's base branch with none. With any other remote, or none, it is the merge.
# With "pull-request", Lem pushes each task's branch and opens its pull request without asking:
# this line is the owner's word for exactly that.
propose = "pull-request"
# Branches nothing lands on and nothing is pushed to through this skill, whoever asks.
protected = []

[checks]
# The machine checks of a landing, each run at the root of the task's worktree: the whole suite,
# which runs here one time, before the pull request, and in no builder.
commands = []
# Paths the checks do not read. When the base branch moves after green checks by these files
# only, the result stands; any other file means the checks run again. A `*` crosses directories.
ignores = []
# What a fresh worktree of this project needs before its tests can start: install the packages,
# copy an environment file. The check that each criterion's tests fail on the base commit runs in a
# worktree of its own and runs these there first. Leave it empty when the tests start as they are.
setup = []
# Commands that need the machine to themselves: an end-to-end suite that uses fixed ports, one
# database or a browser. The checks run each after `commands` pass, under one lock for the
# repository, and a builder runs a test of such a suite through `project.py alone`. `commands` is
# the whole suite without them, which runs one time, before the pull request.
alone = []
# Extra regular expressions that find a mark of a lowered bar (a new suppression, a skipped test)
# in a language Lem has no marks of its own for. Lem has its own for Python, JavaScript,
# TypeScript, Go, Rust, Java, Kotlin and shell.
bar = []

[flow]
# What must never go wrong in this project, each as one sentence in the owner's words: "a
# customer is charged the wrong amount", "data that cannot be rebuilt is lost", "someone signs in
# as another user". No code matches these and no list of paths stands in for them: Lem reads the
# ask against each, the lead its plan, and the agent that reviews the diff the change itself, and
# a change in reach of one takes the careful flow: its plan is talked through with the reviewer
# before any code, the landing gives it the project's full review set, and a person merges it.
# This table is read from the main checkout, so a branch cannot lift what guards it.
topics = []
# How many tasks build or land at one time. Four to five ran well on one Mac; six gave a load
# average of 12 to 16 and unstable browser tests (convertiser-server, 2026-11-14). Lower it when
# the tests share one database or drive a browser.
max_tasks = {max_tasks}
# How many minutes a choice of the build waits for the owner before the lead takes the recommended
# option, and the pull request is not green for it. The owner's own number (2026-11-16).
decision_wait = {decision_wait}
# How many seconds Lem's watch of the open pull requests waits between two looks at the forge, for
# a merge or a close the owner made there. A guess, not a measurement.
watch_seconds = {watch_seconds}

[seats]
# Who sits where, each as "agent/model:effort". Leave out the effort ("codex/gpt-6.1-sol"), or
# the model and the effort ("codex"), and that agent's own default holds.
# The reviewer: "claude" or "codex". Lem's builders build; this one talks the plan of a careful
# or large task through with its defender, in the plan talk's companion. The same family twice is
# allowed.
{reviewer}
# The defender of a careful or large plan in its talk with the reviewer, in a companion session
# Lem opens for the talk and closes after it. Only "claude" for now.
# planner = "claude/opus:high"
# The two experts who answer a choice that waits for the owner, at the same moment and read-only:
# two model families, so that their agreement is worth more than two of one.
# experts = [{experts}]

[corrections]
# Keep a queue of the owner's corrections for the retro. The hook that fills it sends each
# message the owner types, with the agent message it answers, to the Jev decision model. That
# is the owner's choice, so it is false until the owner says yes. `true` here, in git, is a yes for
# everybody who works in this repository: the hook comes with Lem's plugin. One person says
# no for themselves with `collect = false` under [corrections] in .lem/project.local.toml.
collect = false

# The tracker a task's ask may come from. Leave it out when the project has none. Lem reads a
# ticket into a task, and comments it when the task lands. `moves` says who moves the ticket's
# status: "lem", with the two status names as the team spells them, or "tracker" when the
# tracker's own automation moves it (a pull-request integration).
# [tracker]
# kind = "linear"
# server = "linear"      # the name of the tracker's MCP server in the agent
# workspace = "acme"     # the workspace, as in its address linear.app/acme: nothing is read or written in another
# team = "ABC"           # the key of the one team whose tickets this project takes
# moves = "lem"
# started = "In Progress"
# landed = "Done"

[tools]
# The skill or command the owner marks up a plan or a draft with. "{annotate}" is the one Lem
# recommends, a recipe of the agterm cookbook that you install; name your own instead.
annotate = "{annotate}"
# How a question that asks the owner to choose or to approve reaches the owner. "{ask}" comes with
# Lem and shows a page with the options side by side. "terminal" asks in the conversation, as a
# numbered list. Or name a skill or a command of your own.
ask = "{ask}"
"""
# The naps' table, the last of the file. Its numbers are written in here, so it holds no `{}` for
# the `format` of `init`.
TEMPLATE += f"""
[naps]
# Now and then, when a task has ended or Lem waits for the owner, Lem takes a nap: a fresh agent
# reads the recent tasks, dreams, and writes the dream down in .lem/state/naps/, which the retro
# reads. It costs an agent's session of some minutes, a few times a
# day while Lem works, and nobody has shown that it helps.
on = false
# How many days a nap is kept. A guess, from the owner's "a week or a month (?)".
keep_days = {NAPS_KEEP_DAYS}
# How many hours at least between two naps that Lem starts by itself. A guess, from "three times a
# day" in the routine the naps follow.
gap_hours = {NAPS_GAP_HOURS}
"""


class SettingsError(Exception):
    pass


def repo_root(start: Path) -> Path:
    found = subprocess.run(
        ["git", "-C", str(start), "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=False,
    )
    if found.returncode != 0:
        raise SettingsError(f"{start} is not inside a git checkout")
    return Path(found.stdout.strip())


def nearest(key: str, valid: tuple[str, ...]) -> str:
    close = difflib.get_close_matches(key, valid, n=1)
    return f"; did you mean {close[0]!r}?" if close else f"; valid: {', '.join(valid)}"


def strings(value: object, where: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise SettingsError(f"{where} must be a list of strings")
    return value


def commands(value: object, where: str) -> list[str]:
    """A list of shell commands. An empty one runs nothing and exits 0, so checks of it are green."""
    found = strings(value, where)
    if any(not item.strip() for item in found):
        raise SettingsError(f"{where} holds an empty command, which passes without running anything; take it out of the list")
    return found


def patterns(value: object, where: str) -> list[str]:
    """A list of regular expressions, each one read here so that a wrong one is named where it is written."""
    for item in strings(value, where):
        try:
            re.compile(item)
        except re.error as error:
            raise SettingsError(f"{where}: {item!r} is not a regular expression ({error})") from error
    return value


def inside(root: Path, relative: str, where: str) -> Path:
    if Path(relative).is_absolute():
        raise SettingsError(f"{where} = {relative!r} must be relative to the root of the checkout")
    resolved = (root / relative).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise SettingsError(f"{where} = {relative!r} leaves the repository")
    if resolved == root.resolve():
        # every path names a folder or a file of its own: the root would read the whole checkout as
        # backlog items or rules, and a worktrees folder there ignores every file of the project
        raise SettingsError(f"{where} = {relative!r} names the root of the checkout; name a folder or a file inside it, or leave the line out for the default")
    return resolved


def main_checkout(root: Path) -> Path:
    """The checkout every worktree hangs off: the first entry git lists. A file git does not track lives only there."""
    # -z ends each field with a NUL: a path may hold a line break, and a split on lines would cut it
    listed = subprocess.run(["git", "-C", str(root), "worktree", "list", "--porcelain", "-z"], capture_output=True, text=True, check=False)
    first = next((field.removeprefix("worktree ") for field in listed.stdout.split("\0") if field.startswith("worktree ")), None)
    return Path(first) if first else root


def text_of(file: Path) -> str:
    """A text file Lem reads, as UTF-8. A file in another encoding is refused by name: read as
    the locale's, a settings file would mean something else on another machine."""
    try:
        return file.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise SettingsError(f"{file} is not UTF-8 text (byte {error.start} does not read); save it as UTF-8") from error


def unreadable_argument(argv: list[str]) -> str | None:
    """The first argument that is not UTF-8 text, as the message that names it; None when all are.
    Such an argument would stop the write of the file it goes into half way."""
    for arg in argv:
        try:
            arg.encode("utf-8")
        except UnicodeEncodeError:
            return f"the argument {os.fsencode(arg)!r} is not UTF-8 text; give it in UTF-8"
    return None


def toml_string(value: str) -> str:
    """A string as TOML writes it. JSON's own escapes would turn a character outside the basic plane into two halves TOML refuses."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return '"' + "".join(f"\\u{ord(c):04x}" if ord(c) < 0x20 or ord(c) == 0x7F else c for c in escaped) + '"'


def read_settings(file: Path, name: Path, tables: tuple[str, ...], branch_copy: bool = False) -> dict:
    """One settings file as a dict, with every table and key it may not hold refused. A task
    branch's copy (`branch_copy`) in the form of an older Lem is read in the form of now."""
    if not file.is_file():
        return {}
    return settings_of(text_of(file), name, tables, branch_copy)


def committed_settings(main: Path) -> dict | None:
    """The tracked settings as the base branch's newest commit holds them: the text, the branch and
    the commit; None when no commit of the base holds the file yet (an onboarding, whose settings
    are only in the working tree or on its own branch). The base is the branch the file names, so
    the first file read is the remote's default branch's, then the one of the branch the main
    checkout's own copy names; a file that names another base is read on that branch."""
    def shown(branch: str) -> str | None:
        ran = subprocess.run(["git", "-C", str(main), "show", f"refs/heads/{branch}:{SETTINGS.as_posix()}"], capture_output=True, check=False)
        if ran.returncode != 0:
            return None
        try:
            return ran.stdout.decode("utf-8")
        except UnicodeDecodeError as error:
            raise SettingsError(f"{branch}:{SETTINGS} is not UTF-8 text (byte {error.start} does not read); save it as UTF-8") from error

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
    for start in dict.fromkeys(branch for branch in (default_branch(main), own) if branch):
        text = shown(start)
        if text is None:
            continue
        named = names(text) or start
        if named != start:
            other = shown(named)
            if other is None:
                raise SettingsError(f"{start}:{SETTINGS} names {named!r} as branch.base, and {named} holds no {SETTINGS}: the base branch's own file is the one Lem reads")
            start, text = named, other
        commit = subprocess.run(["git", "-C", str(main), "rev-parse", f"refs/heads/{start}"], capture_output=True, text=True, check=False).stdout.strip()
        return {"text": text, "branch": start, "commit": commit}
    return None


# Whether this run said once already that the main checkout's copy of the settings is not the one Lem reads.
DIFFERS_SAID: list[bool] = []


def settings_of(text: str, name: Path, tables: tuple[str, ...], branch_copy: bool = False) -> dict:
    """The text of one settings file as a dict, checked as `read_settings` says."""
    try:
        raw = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise SettingsError(f"{name}: {error}") from error
    if branch_copy:
        raw = now_form(raw, name)
    older = older_form(raw, name)
    if older:
        # The tracked file: a worktree of an open task reads its branch's own copy, which takes the
        # fix only from the base, and a fresh worktree starts from origin's base.
        raise SettingsError(older + (
            "\n\nThen commit the file on the base branch and push it: that makes the fix count for the tasks that are open, whose branches take the file from the base"
            if "checks" in tables else ""
        ))
    for table, body in raw.items():
        if table not in TABLES:
            raise SettingsError(f"{name}: unknown table [{table}]{nearest(table, tuple(TABLES))}")
        if table not in tables:
            raise SettingsError(
                f"{name}: [{table}] is the project's rule and belongs in {SETTINGS}; "
                f"this file may hold only {', '.join(f'[{t}]' for t in tables)}",
            )
        if not isinstance(body, dict):
            raise SettingsError(f"{name}: [{table}] must be a table")
        if table == "flow" and "careful" in body:
            raise SettingsError(careful_gone(name, body["careful"]))
        for key in body:
            if key not in TABLES[table]:
                raise SettingsError(f"{name}: unknown key {table}.{key}{nearest(key, TABLES[table])}")
    return raw


def toml_value(value: object) -> str:
    """A value of a settings file as TOML writes it: a string, a list of strings, true or false, a number."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return toml_string(value)
    if isinstance(value, list):
        return "[" + ", ".join(toml_value(item) for item in value) + "]"
    return str(value)


def older_form(raw: dict, name: Path) -> str | None:
    """The one refusal of a file that has tables of an older Lem: `[gate]`, `[seats.reviewer]`,
    `[seats.planner]`. It names every one the file has and gives the whole text to write in their
    place, ready to paste; None when the file has none. The keys of `[gate]` are those of `[checks]`,
    so its lines are the table's own, and an unknown key among them is refused after the move."""
    gate = raw.get("gate")
    seats = raw.get("seats") if isinstance(raw.get("seats"), dict) else {}
    tables = [which for which in SEATS if isinstance(seats.get(which), dict)]
    if gate is None and not tables:
        return None

    def joined(words: list[str]) -> str:
        return words[0] if len(words) == 1 else ", ".join(words[:-1]) + " and " + words[-1]

    named, said, text = [], [], []
    if gate is not None:
        named.append("[gate]")
        said.append("[gate] is called [checks] now, with the same keys (commands, setup, ignores, bar, alone)")
        text += ["[checks]", *([f"{key} = {toml_value(value)}" for key, value in gate.items()] if isinstance(gate, dict) else [])]
    if tables:
        # the keys of [seats] that are lines already go into the one [seats] table with the new lines
        plain = [f"{key} = {toml_value(value)}" for key, value in seats.items() if not isinstance(value, dict)]
        if plain:
            named.append("[seats]")
        named += [f"[seats.{which}]" for which in tables]
        said.append(
            f"{joined([f'[seats.{which}]' for which in tables])} {'is' if len(tables) == 1 else 'are each'} one line under [seats] now, \"{SEAT_FORM}\""
            + ("; the reviewer's effort for the review of a diff was used by no step, and has no place in the line" if "reviewer" in tables and "effort" in seats["reviewer"] else ""),
        )
        text += [*([""] if text else []), "[seats]", *plain, *(old_seat_line(which, seats[which]) for which in tables)]
    return (
        f"{name} has the form of an older Lem: {'; '.join(said)}. "
        f"Write these lines in place of the {joined(named)} table{'s' if len(named) > 1 else ''}:\n" + "\n".join(text)
    )


def careful_gone(name: Path, paths: object) -> str:
    """The refusal of a list of careful paths, with the sentence to write in its place."""
    first = paths[0] if isinstance(paths, list) and paths and isinstance(paths[0], str) else None
    example = (
        f'say what the paths stood for as sentences in flow.topics, as topics = ["what goes wrong for a person when {first} breaks, in your words"], '
        if first else "say in flow.topics, as sentences, what must never go wrong here, "
    )
    return (
        f"{name}: flow.careful is gone: whether a change is careful is judged against flow.topics, at the ask, at the plan and at the diff, "
        f"and no list of paths decides it, since a list goes stale as the code moves and a branch can edit it. {example.capitalize()}"
        "then remove the line careful = [...]"
    )


def flow_of(raw: dict, name: Path) -> dict:
    """The `[flow]` table of one settings file, checked."""
    flow = raw.get("flow", {})
    max_tasks = flow.get("max_tasks", MAX_TASKS)
    # a bool is an int in Python, and `max_tasks = true` is a mistake, not the number 1
    if isinstance(max_tasks, bool) or not isinstance(max_tasks, int) or max_tasks < 1:
        raise SettingsError(f"{name}: flow.max_tasks = {max_tasks!r} must be a whole number, 1 or more")
    decision_wait = flow.get("decision_wait", DECISION_WAIT)
    if isinstance(decision_wait, bool) or not isinstance(decision_wait, int) or decision_wait < 1:
        raise SettingsError(f"{name}: flow.decision_wait = {decision_wait!r} must be a whole number of minutes, 1 or more")
    watch_seconds = flow.get("watch_seconds", WATCH_SECONDS)
    if isinstance(watch_seconds, bool) or not isinstance(watch_seconds, int) or watch_seconds < 1:
        raise SettingsError(f"{name}: flow.watch_seconds = {watch_seconds!r} must be a whole number of seconds, 1 or more")
    return {"topics": strings(flow.get("topics", []), "flow.topics"), "max_tasks": max_tasks, "decision_wait": decision_wait, "watch_seconds": watch_seconds}


def parse_seat(text: object, where: str, agents: tuple[str, ...], why: str, example: str) -> dict:
    """One seat, `agent/model:effort`, as its parts: the agent, the model and the effort, each None
    when the line leaves it out, and the line as written. The effort is what follows the one `:`
    after the model, or after the agent when the line names no model; a second `:` is refused."""
    form = f'one string, "{SEAT_FORM}", as "{example}"; the effort, or the model and the effort, may be left out'
    if not isinstance(text, str):
        raise SettingsError(f"{where} = {text!r} must be {form}")
    if not text.strip():
        raise SettingsError(f"{where} is empty: it is {form}. Leave the line out for Lem's default")
    if any(char.isspace() for char in text):
        raise SettingsError(f"{where} = {text!r} holds a space: it is {form}, with no space in it")
    if text.count(":") > 1:
        raise SettingsError(f"{where} = {text!r} holds {text.count(':')} `:`, and a seat has one at most, before the effort: it is {form}")
    agent, slash, rest = text.partition("/")
    if slash:
        model, colon, effort = rest.partition(":")
    else:
        agent, colon, effort = agent.partition(":")
        model = None
    if not agent:
        raise SettingsError(f"{where} = {text!r} names no agent before the `/`: it is {form}")
    if slash and not model:
        raise SettingsError(f"{where} = {text!r} names no model after the `/`: leave the `/` out with the model, as \"{agent}\", or write {form}")
    if colon and not effort:
        raise SettingsError(f"{where} = {text!r} names no effort after the `:`: leave the `:` out with the effort, or write {form}")
    if agent not in agents:
        raise SettingsError(f"{where} = {text!r}: the agent {agent!r} must be {' or '.join(agents)}: {why}")
    return {"agent": agent, "model": model or None, "effort": effort or None, "seat": text}


def old_seat_value(which: str, table: dict) -> str:
    """The one line an older Lem's seat table says now, from what the table holds."""
    agent, model, effort = table.get("agent"), table.get("model"), table.get(OLD_SEAT_EFFORT[which])
    words = [value if isinstance(value, str) and value.strip() else None for value in (agent, model, effort)]
    return (words[0] or "AGENT") + (f"/{words[1]}" if words[1] else "") + (f":{words[2]}" if words[2] else "")


def old_seat_line(which: str, table: dict) -> str:
    """The line to write in place of an older Lem's seat table."""
    return f"{which} = {toml_string(old_seat_value(which, table))}"


def now_form(raw: dict, name: Path) -> dict:
    """A task branch's copy of the settings in the form an older Lem wrote, in the form of now: the
    `[gate]` table as `[checks]`, a seat table as its one line, so that the task goes on. The branch
    took the file from a base that held it so, and holds it until the file of now is on the base it
    is brought onto, which only the owner's commit and push make. The main checkout's own file,
    which the owner keeps, is refused instead (`older_form`). One line on stderr says what was read
    so, and why. A later change may drop this once no task whose branch holds such a file is open."""
    read = []
    if "gate" in raw and "checks" not in raw:
        raw = {("checks" if table == "gate" else table): body for table, body in raw.items()}
        read.append("[gate] as [checks]")
    seats = raw.get("seats")
    if isinstance(seats, dict):
        for which in SEATS:
            if isinstance(seats.get(which), dict):
                seats[which] = old_seat_value(which, seats[which])
                read.append(f"[seats.{which}] as {which} = {toml_string(seats[which])}")
    if read:
        print(
            f"project.py: this worktree's {name} is the task branch's own copy, in the form of an older Lem; "
            f"Lem reads it as now ({'; '.join(read)}), so that the task goes on",
            file=sys.stderr,
        )
    return raw


def seat(raw: dict, name: Path, which: str = "reviewer") -> dict | None:
    """The seat (`SEATS`) one file names, checked; None when the file names none."""
    agents, why, example = SEATS[which]
    given = raw.get("seats", {}).get(which)
    if given is None:
        return None
    # a table of an older Lem never comes here: `older_form` refused it when the file was read
    return parse_seat(given, f"{name}: seats.{which}", agents, why, example)


def experts_of(raw: dict, name: Path) -> list[dict] | None:
    """The two experts one file names, checked; None when the file names none."""
    given = raw.get("seats", {}).get("experts")
    if given is None:
        return None
    if not isinstance(given, list) or len(given) != len(EXPERT_PLACES):
        raise SettingsError(
            f'{name}: seats.experts = {given!r} must be a list of two seats, "{SEAT_FORM}" each, as experts = [{", ".join(toml_string(one) for one in EXPERTS)}]: '
            "a choice's record holds the answers of two experts",
        )
    return [
        {**parse_seat(one, f"{name}: seats.experts[{number}]", REVIEWERS, "the agents the harness starts an expert with", EXPERTS[number]), "place": place}
        for number, (one, place) in enumerate(zip(given, EXPERT_PLACES))
    ]


def plan_file_of(raw: dict, name: Path) -> str:
    """The pattern of a plan's file name, checked: the tokens it may hold, `<slug>` once, a name
    and not a path, and a markdown file."""
    pattern = raw.get("paths", {}).get("plan_file", PLAN_FILE)
    where = f"{name}: paths.plan_file"
    if not isinstance(pattern, str) or not pattern.strip():
        raise SettingsError(f'{where} = {pattern!r} must be a file name in quotes, as plan_file = "{PLAN_FILE}"')
    if pattern.count("<slug>") != 1:
        raise SettingsError(f'{where} = {pattern!r} must hold <slug> once, where the task\'s slug goes, as plan_file = "{PLAN_FILE}": without it no plan can be told from another task\'s')
    if "/" in pattern or "\\" in pattern:
        raise SettingsError(f"{where} = {pattern!r} is a file name in the plans folder, with no folder in it; paths.plans names the folder")
    if not pattern.endswith(".md"):
        raise SettingsError(f"{where} = {pattern!r} must end with .md: a plan is a markdown file")
    if re.search(r"<(?!slug>)[^>]*>", pattern):
        raise SettingsError(f"{where} = {pattern!r} holds a token Lem does not know; it knows YYYY, MM, DD and <slug>")
    twice = [token for token in PLAN_TOKENS if pattern.count(token) > 1]
    if twice:
        raise SettingsError(f"{where} = {pattern!r} holds {twice[0]} twice; each of YYYY, MM, DD and <slug> stands in it once at most")
    return pattern


def local_off(local: dict) -> bool:
    """Whether this machine's own file says no to the correction queue. It can say nothing else about it."""
    if "collect" not in local.get("corrections", {}):
        return False
    if local["corrections"]["collect"] is not False:
        raise SettingsError(
            f"{LOCAL}: corrections.collect = {local['corrections']['collect']!r} is not for this file. It may say `collect = false`, "
            f"which keeps one person's messages out of the queue; only {SETTINGS}, which everybody reads in git, switches the queue on",
        )
    return True


def local_naps_off(local: dict) -> bool:
    """Whether this machine's own file says no to the naps: a nap spends this person's tokens. It
    can say nothing else about them."""
    naps = local.get("naps", {})
    for key in naps:
        if key != "on":
            raise SettingsError(f"{LOCAL}: naps.{key} is the project's and belongs in {SETTINGS}; this file may hold only `on = false` under [naps]")
    if "on" not in naps:
        return False
    if naps["on"] is not False:
        raise SettingsError(
            f"{LOCAL}: naps.on = {naps['on']!r} is not for this file. It may say `on = false`, which keeps Lem from napping by itself "
            f"on this machine; only {SETTINGS}, which everybody reads in git, switches the naps on",
        )
    return True


def local_max_tasks(local: dict) -> int | None:
    """The limit of tasks that build or land at one time on this machine, when its own file names
    one: a machine's load, and no guard of the project's."""
    flow = local.get("flow", {})
    for key in flow:
        if key != "max_tasks":
            raise SettingsError(
                f"{LOCAL}: flow.{key} is the project's rule and belongs in {SETTINGS}; this file may hold only max_tasks under [flow], one machine's limit",
            )
    return flow_of(local, LOCAL)["max_tasks"] if "max_tasks" in flow else None


def tool_of(raw: dict, name: Path, role: str) -> str | None:
    """The tool one file names for a role, checked; None when the file names none."""
    if role not in raw.get("tools", {}):
        return None
    tool = raw["tools"][role]
    if not isinstance(tool, str) or not tool.strip():
        raise SettingsError(f'{name}: tools.{role} = {tool!r} must name a skill or a command in quotes, as in {role} = "{TOOLS[role]}"')
    return tool


def naps_of(raw: dict, name: Path) -> dict:
    """The `[naps]` table of one settings file, checked."""
    naps = raw.get("naps", {})
    on = naps.get("on", False)
    if not isinstance(on, bool):
        raise SettingsError(f"{name}: naps.on = {on!r} must be true or false")
    numbers = {}
    for key, default, unit in (("keep_days", NAPS_KEEP_DAYS, "days"), ("gap_hours", NAPS_GAP_HOURS, "hours")):
        value = naps.get(key, default)
        # a bool is an int in Python, and `keep_days = true` is a mistake, not the number 1
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise SettingsError(f"{name}: naps.{key} = {value!r} must be a whole number of {unit}, 1 or more")
        numbers[key] = value
    return {"on": on, **numbers}


def load(root: Path) -> dict:
    file = root / SETTINGS
    main = main_checkout(root)
    # The project's settings are the main checkout's working tree while it is on the base branch:
    # the developer's own edit there is his act, and counts at once. Another branch checked out there
    # is no rule for the tasks that run (audit M-F5, 2026-11-17: `gh pr checkout 57` in the main
    # checkout changed `branch.land` and the topics for every task), so then the file is read as the
    # base branch's newest commit has it. Before any commit of the base holds the file (an
    # onboarding), the working tree's is read.
    committed = committed_settings(main)
    if committed and subprocess.run(["git", "-C", str(main), "branch", "--show-current"], capture_output=True, text=True, check=False).stdout.strip() == committed["branch"]:
        committed = None
    base_file = Path(f"{committed['branch']}:{SETTINGS}") if committed else main / SETTINGS

    def base_raw() -> dict:
        if not committed:
            return read_settings(main / SETTINGS, main / SETTINGS, tuple(TABLES))
        try:
            return settings_of(committed["text"], base_file, tuple(TABLES))
        except SettingsError as error:
            # the fix is an edit of the file, and it counts once the base holds it
            raise SettingsError(f"Lem reads {SETTINGS} as {committed['branch']} has it, so a fix counts once it is committed there. {error}") from error

    if main.resolve() == root.resolve():
        raw = base_raw()
        here = text_of(file) if file.is_file() else None
        if committed and here != committed["text"] and not DIFFERS_SAID:
            DIFFERS_SAID.append(True)
            print(
                f"project.py: the main checkout is not on {committed['branch']}, so Lem reads {SETTINGS} as {committed['branch']} has it ({committed['commit'][:9]}), "
                f"not the copy checked out there",
                file=sys.stderr,
            )
    else:
        # in a task's worktree the file is the branch's copy, which may be older than the base's
        raw = read_settings(file, SETTINGS, tuple(TABLES), branch_copy=True)
    local_file = main / LOCAL
    local = read_settings(local_file, LOCAL, LOCAL_TABLES)
    # What must never go wrong, and the owner's wait, are the base branch's: the branch that a
    # rule guards does not get to lift it. The branch's own table is still checked.
    flow = flow_of(raw, SETTINGS)
    if main.resolve() != root.resolve():
        flow = flow_of(base_raw(), base_file)
    overridden = []
    machine_limit = local_max_tasks(local)
    if machine_limit is not None:
        flow["max_tasks"] = machine_limit
        overridden.append("flow.max_tasks")

    paths = {}
    for name, (default, _older) in PATHS.items():
        relative = raw.get("paths", {}).get(name, default)
        if not isinstance(relative, str):
            raise SettingsError(f"{SETTINGS}: paths.{name} must be a string")
        resolved = inside(root, relative, f"paths.{name}")
        paths[name] = {"path": str(resolved), "exists": resolved.exists()}
    # a pattern, not a path: the name of a plan's file in the plans folder
    paths["plan_file"] = {"pattern": plan_file_of(raw, SETTINGS)}

    branch = raw.get("branch", {})
    base = branch.get("base")
    if base is not None and not isinstance(base, str):
        raise SettingsError(f"{SETTINGS}: branch.base must be a string")
    if base is not None and not base.strip():
        raise SettingsError(f"{SETTINGS}: branch.base = {base!r} names no branch; write the branch tasks start from and land on, as base = \"main\"")
    land = branch.get("land", "owner")
    if land not in LAND:
        raise SettingsError(f"{SETTINGS}: branch.land = {land!r} must be one of {', '.join(LAND)}")

    history = branch.get("history", "keep")
    if history not in HISTORY:
        raise SettingsError(f"{SETTINGS}: branch.history = {history!r} must be one of {', '.join(HISTORY)}")
    propose = branch.get("propose", "pull-request")
    if propose not in PROPOSE:
        raise SettingsError(
            f"{SETTINGS}: branch.propose = {propose!r} must be one of {', '.join(PROPOSE)}: "
            '"pull-request" ends a task as a pull request on the forge, "merge" lands it on the base branch with none',
        )
    protected =strings(branch.get("protected", []), "branch.protected")
    if base in protected:
        raise SettingsError(f"{SETTINGS}: branch.base = {base!r} is in branch.protected, so no task could land")
    tools = {}
    for role, own in TOOLS.items():
        tools[role] = tool_of(raw, SETTINGS, role) or own
        here = tool_of(local, LOCAL, role)
        if here is not None:
            tools[role] = here
            overridden.append(f"tools.{role}")

    # A local seat replaces the project's whole: its model and effort belong to the project's agent.
    seats: dict = {}
    for which in SEATS:
        seats[which] = seat(raw, SETTINGS, which) or {**{key: None for key in SEAT_KEYS}, "seat": None}
        local_seat = seat(local, LOCAL, which)
        if local_seat is not None:
            seats[which] = local_seat
            overridden.append(f"seats.{which}")
    seats["experts"] = experts_of(raw, SETTINGS) or experts_of({"seats": {"experts": list(EXPERTS)}}, Path("Lem's default"))
    local_experts = experts_of(local, LOCAL)
    if local_experts is not None:
        seats["experts"] = local_experts
        overridden.append("seats.experts")
    collect = raw.get("corrections", {}).get("collect", False)
    if not isinstance(collect, bool):
        raise SettingsError(f"{SETTINGS}: corrections.collect = {collect!r} must be true or false")
    if local_off(local):
        if collect:
            overridden.append("corrections.collect")
        collect = False
    tracker = None
    if "tracker" in raw:
        given = raw["tracker"]
        for key, value in given.items():
            if not isinstance(value, str) or not value.strip():
                raise SettingsError(f"{SETTINGS}: tracker.{key} must be a word in quotes, not {value!r}")
        for key in ("kind", "server", "workspace", "team", "moves"):
            if key not in given:
                raise SettingsError(f"{SETTINGS}: [tracker] needs {key}; leave the whole table out when the project has no tracker")
        if given["kind"] not in TRACKERS:
            raise SettingsError(f"{SETTINGS}: tracker.kind = {given['kind']!r} must be one of {', '.join(TRACKERS)}")
        if given["moves"] not in MOVES:
            raise SettingsError(f"{SETTINGS}: tracker.moves = {given['moves']!r} must be one of {', '.join(MOVES)}")
        named = [key for key in ("started", "landed") if key in given]
        if given["moves"] == "lem" and len(named) != 2:
            raise SettingsError(
                f'{SETTINGS}: with tracker.moves = "lem" the table names both statuses, started and landed, as the team spells them',
            )
        if given["moves"] == "lem" and given["started"].strip().lower() == given["landed"].strip().lower():
            raise SettingsError(
                f"{SETTINGS}: tracker.started and tracker.landed are both {given['started']!r}: "
                "a ticket would be marked as landed the moment its work starts",
            )
        if given["moves"] == "tracker" and named:
            raise SettingsError(f'{SETTINGS}: with tracker.moves = "tracker" Lem moves no ticket, so {" and ".join(named)} say nothing: remove them')
        tracker = {key: given.get(key) for key in TABLES["tracker"]}
    # The naps spend the tokens of whoever works on this machine, so their switch is the base
    # branch's too: a task's branch that switches them on has not been agreed to yet.
    naps = naps_of(raw, SETTINGS)
    if main.resolve() != root.resolve():
        naps = naps_of(base_raw(), base_file)
    if local_naps_off(local):
        if naps["on"]:
            overridden.append("naps.on")
        naps["on"] = False
    return {
        "root": str(root),
        # the checkout every worktree hangs off; it is `root` unless this ran in a task's worktree
        "main": str(main),
        "settings": str(file) if file.is_file() or committed else None,
        # where the settings were read: the working tree, or the base branch's commit while another branch is checked out
        "settings_from": (f"{committed['branch']}@{committed['commit'][:9]}" if committed else "the working tree")
        if main.resolve() == root.resolve() else "this worktree's branch, with [flow] and [naps] from " + (f"{committed['branch']}@{committed['commit'][:9]}" if committed else "the main checkout"),
        "paths": paths,
        "branch": {"base": base, "land": land, "history": history, "propose": propose, "protected": protected},
        "checks": {
            "commands": commands(raw.get("checks", {}).get("commands", []), "checks.commands"),
            "ignores": strings(raw.get("checks", {}).get("ignores", []), "checks.ignores"),
            "setup": commands(raw.get("checks", {}).get("setup", []), "checks.setup"),
            "bar": patterns(raw.get("checks", {}).get("bar", []), "checks.bar"),
            "alone": commands(raw.get("checks", {}).get("alone", []), "checks.alone"),
        },
        # read from the main checkout's settings, in a task's worktree too
        "flow": flow,
        "seats": seats,
        "tools": tools,
        "corrections": {"collect": collect},
        "tracker": tracker,
        "naps": naps,
        # what this machine set for itself, so a report can say that the reviewer is not the project's
        "local": {"file": str(local_file) if local_file.is_file() else None, "overrides": overridden},
    }


def cmd_path(settings: dict, name: str) -> None:
    if name == "plan_file":
        raise SettingsError("paths.plan_file is the pattern of a plan's name, not a path: `lem project plan-file SLUG` prints the name of a task's plan")
    if name not in settings["paths"]:
        raise SettingsError(f"no path named {name!r}{nearest(name, tuple(PATHS))}")
    print(settings["paths"][name]["path"])


def cmd_plan_file(settings: dict, slug: str, day: str | None) -> None:
    """The name a task's plan takes, written today or on DAY, and the plan the plans folder holds now."""
    if not SLUG.fullmatch(slug):
        raise SettingsError(f"slug {slug!r} must be lower-case words joined by hyphens")
    day = day or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        datetime.strptime(day, "%Y-%m-%d")
    except ValueError as error:
        raise SettingsError(f"--date {day!r} is not a day as YYYY-MM-DD") from error
    pattern = settings["paths"]["plan_file"]["pattern"]
    folder = Path(settings["paths"]["plans"]["path"])
    found = lem_plans.found(folder, pattern, slug)
    name = lem_plans.name(pattern, slug, day)
    print(json.dumps({"slug": slug, "pattern": pattern, "name": name, "path": str(folder / name), "found": str(found) if found else None}, indent=2))


def cmd_may_land(settings: dict, target: str) -> None:
    """Exit 1 unless TARGET is the branch this project's tasks land on."""
    branch = settings["branch"]
    if target in branch["protected"]:
        raise SettingsError(f"{target!r} is protected in {SETTINGS}: nothing lands on it or is pushed to it")
    if branch["base"] is None:
        raise SettingsError(f"{SETTINGS} names no branch.base, so no branch can be landed on")
    if target != branch["base"]:
        raise SettingsError(f"tasks of this project land on {branch['base']!r}, not on {target!r}")
    found = subprocess.run(["git", "-C", settings["root"], "rev-parse", "--verify", "--quiet", f"refs/heads/{target}"], capture_output=True, text=True, check=False)
    if found.returncode != 0:
        raise SettingsError(f"branch.base = {target!r} is no branch of this repository; correct it in {SETTINGS}, or make the branch first")
    print(f"{target}: tasks land here; the {branch['land']} lands")


def default_branch(root: Path) -> str | None:
    head = subprocess.run(
        ["git", "-C", str(root), "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
        capture_output=True, text=True, check=False,
    )
    return head.stdout.strip().removeprefix("origin/") if head.returncode == 0 else None


def rule_files(folder: Path) -> list[Path]:
    """Every .md below the folder, through links too, as the agent that loads such a folder by itself reads it."""
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


def older_folders(root: Path) -> dict[str, str]:
    """The settings an older tool already keeps here, where the skill's own layout has nothing yet."""
    found = {
        name: older for name, (default, older) in PATHS.items()
        if older and (root / older).exists() and not (root / default).exists()
    }
    # The rules an agent loads by itself are the style guide wherever they exist. An empty folder
    # of the skill's own layout beside them (a setup that stopped half way) does not hide them.
    # Files are compared by where they really are: one folder linked from the other, or rule
    # files linked between the two, is one set of rules. The settings name the agent's folder
    # unless the skill's own holds every file of it and more. Either way `rules` reads both
    # (`style_folders`), so two folders that each hold a file the other lacks are no refusal and
    # no move: "The rules of an existing project stay where they are" (the owner, 2026-11-15).
    own, rules = PATHS["styleguide"]
    found.pop("styleguide", None)
    if (root / rules).exists():
        ours = {os.path.realpath(file) for file in rule_files(root / own)}
        theirs = {os.path.realpath(file) for file in rule_files(root / rules)}
        if not theirs < ours:
            found["styleguide"] = rules
    return found


def style_folders(settings: dict) -> list[Path]:
    """The folders the style guide is read from: the one the settings name, and when that is the
    agent's rules folder or the skill's own, the other of the two where it exists too. A project
    may keep rules in both, and Lem moves no file between them."""
    # compared as the settings resolve a path, through links: a rules folder linked to the other is one folder
    root = Path(settings["root"])
    named = Path(settings["paths"]["styleguide"]["path"])
    pair = [(root / folder).resolve() for folder in PATHS["styleguide"]]
    if named not in pair:
        return [named]
    return [named, *(folder for folder in pair if folder != named and folder.is_dir())]


def cmd_init(root: Path, base: str | None, existing: str | None, reviewer: str | None) -> None:
    file = root / SETTINGS
    if file.exists():
        raise SettingsError(f"{SETTINGS} already exists; edit it")
    base = base or default_branch(root)
    if not base:
        raise SettingsError("cannot tell the base branch (no origin/HEAD); pass --base NAME")
    older = older_folders(root)
    # The rules an agent already loads by itself are never a choice: they stay, and they are the
    # style guide. Where the cast, the profile and the worktrees live is the owner's to say.
    choice = {name: path for name, path in older.items() if name != "styleguide"}
    if choice and existing is None:
        found = ", ".join(f"{name} in {path}" for name, path in choice.items())
        raise SettingsError(
            f"this repository already keeps {found}; pass --existing link to point at them, "
            "or --existing new to start the skill's own layout",
        )
    lines = []
    for name, (default, _older) in PATHS.items():
        chosen = older[name] if name in older and (name == "styleguide" or existing == "link") else default
        lines.append(f'{name} = "{chosen}"')
    file.parent.mkdir(exist_ok=True)
    agent = f'reviewer = "{reviewer}"' if reviewer else '# reviewer = "codex/gpt-6.1-sol:high"'
    file.write_text(TEMPLATE.format(
        paths="\n".join(lines), plan_file=PLAN_FILE, base=base, reviewer=agent, experts=", ".join(toml_string(one) for one in EXPERTS),
        max_tasks=MAX_TASKS, decision_wait=DECISION_WAIT, watch_seconds=WATCH_SECONDS, **TOOLS,
    ), encoding="utf-8")
    # one machine's own settings and Lem's state are never committed (the state folder hides itself
    # too, for a repository whose ignore file is older than it)
    ignore = file.parent / ".gitignore"
    known = text_of(ignore).splitlines() if ignore.is_file() else []
    missing = [line for line in (LOCAL.name, f"{lem_state.STATE.name}/") if line not in known]
    if missing:
        ignore.write_text("\n".join([*known, *missing]) + "\n", encoding="utf-8")
    print(file)


def cmd_reviewer(root: Path, words: list[str]) -> None:
    """Write, or with `default` remove, this machine's own reviewer seat."""
    file = main_checkout(root) / LOCAL
    local = read_settings(file, LOCAL, LOCAL_TABLES)
    # What the file already holds is checked before any of it is written again: a wrong value is
    # refused with its fix, and the file stays as the owner left it.
    for role in TOOLS:
        tool_of(local, LOCAL, role)
    local_off(local)
    local_naps_off(local)
    local_max_tasks(local)
    seat(local, LOCAL, "reviewer")
    seat(local, LOCAL, "planner")
    experts_of(local, LOCAL)
    if words == ["default"]:
        local.get("seats", {}).pop("reviewer", None)
    else:
        if len(words) != 1:
            raise SettingsError(
                f'reviewer takes one seat, "{SEAT_FORM}", as `reviewer codex/gpt-6.1-sol:high`, or the word default; '
                f"not {len(words)} words. The effort, or the model and the effort, may be left out",
            )
        parse_seat(words[0], "the reviewer", REVIEWERS, SEATS["reviewer"][1], SEATS["reviewer"][2])
        local.setdefault("seats", {})["reviewer"] = words[0]
    lines = ["# This machine's own settings for Lem. Not committed; `lem project reviewer` writes the seat."]
    for table in LOCAL_TABLES:
        body = local.get(table) or {}
        if body:
            # a value here is a word in quotes, a list of them, the one `false` the corrections and the
            # naps tables may hold, or the number of max_tasks
            lines += ["", f"[{table}]", *(f"{key} = {toml_value(value)}" for key, value in body.items())]
    if len(lines) == 1:
        file.unlink(missing_ok=True)
    else:
        file.parent.mkdir(exist_ok=True)
        file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    resolved = load(root)
    print(json.dumps({"reviewer": resolved["seats"]["reviewer"], "local": resolved["local"]}, indent=2))


def braces(pattern: str) -> list[str]:
    """`*.{ts,tsx}` as `*.ts` and `*.tsx`, a group inside a group too. A brace with no comma stays as written."""
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
                return [pattern[: i + 1] + rest for rest in braces(pattern[i + 1:])]
            return [done for part in parts for done in braces(pattern[:start] + part + pattern[i + 1:])]
    return [pattern]


def glob_regex(glob: str) -> re.Pattern[str]:
    """One glob of a rule file's `paths:` as a pattern over a path relative to the root.

    The forms Claude Code documents for `paths:` (its page on `.claude/rules`, read 2026-11-15):
    `**/*.ts` is every such file in any directory, `src/**/*` every file under `src/`, `*.md` the
    files of the root only, `src/components/*.tsx` the files of that one directory. So `*` and `?`
    stay inside one path segment, and `**` as a whole segment is any number of directories, none
    too. Not documented there, and matched here because a rule too many costs less than a rule
    missed: a name that starts with a dot, and a character class in brackets.
    """
    out, i = [], 0
    while i < len(glob):
        char = glob[i]
        whole = glob.startswith("**", i) and (i == 0 or glob[i - 1] == "/") and (i + 2 == len(glob) or glob[i + 2] == "/")
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
        elif char == "[" and "]" in glob[i + 2:]:
            end = glob.index("]", i + 2)
            inner = glob[i + 1:end]
            inner = "^" + inner[1:] if inner[0] == "!" else inner
            out.append("[" + inner.replace("\\", "\\\\") + "]")
            i = end + 1
        else:
            out.append(re.escape(char))
            i += 1
    return re.compile("".join(out))


def rule_scope(file: Path, name: str) -> list[str] | None:
    """The globs a rule file scopes itself to, or None for one that covers every path.

    The one format read is Claude Code's: `paths:` in the file's frontmatter, as a list of globs.
    A `paths:` that names no glob is refused: whether the file then covers every path or none is
    not for a script to guess.
    """
    # utf-8-sig: a byte order mark before the first `---` must not turn a scoped rule into one for every path
    lines = file.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    if not lines or lines[0].strip() != "---":
        return None

    def bare(text: str) -> str:
        """The text without a YAML comment: a `#` at the start or after a space, outside quotes."""
        quote = ""
        for i, char in enumerate(text):
            if quote:
                quote = "" if char == quote else quote
            elif char in "\"'":
                quote = char
            elif char == "#" and (i == 0 or text[i - 1].isspace()):
                return text[:i].strip()
        return text.strip()

    end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), None)
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
        for follow in block[at + 1:]:
            if not follow.strip() or follow.lstrip().startswith("#"):
                continue
            item = re.match(r"\s*-\s+(.*)$", follow)
            if item:
                items.append(bare(item.group(1)))
            elif follow[:1].isspace():
                raise SettingsError(f"{name}: a line under `paths:` is not a list item ({follow.strip()!r}); write each glob as `  - \"GLOB\"`")
            else:
                break
    globs = [item.strip() for item in items]
    globs = [glob[1:-1] if len(glob) > 1 and glob[0] == glob[-1] and glob[0] in "\"'" else glob for glob in globs]
    if not globs or not all(globs):
        raise SettingsError(f"{name}: its `paths:` names no glob; write each glob under it as `  - \"GLOB\"`, or take the line out so the file covers every path")
    return globs


def cmd_rules(settings: dict, files: list[str], commits: str | None) -> None:
    """The style guide files that cover the given files: one match for every reader of the rules."""
    root = Path(settings["root"]).resolve()
    changed = []
    for file in files:
        # One file has one answer, however it is named. Its folder is resolved the way the file
        # system reads it, a link first and `..` after it: `alias/../x` is beside what `alias`
        # points at. The last name is kept as written, since the file may be a link or be gone.
        full = root / file
        if full == root or full.name in ("", ".", ".."):
            raise SettingsError(f"{file} does not name a file; name the files a change touches")
        full = Path(os.path.realpath(full.parent)) / full.name
        if not full.is_relative_to(root) or full == root:
            raise SettingsError(f"{file} is not inside {root}; name files of this repository")
        changed.append(full.relative_to(root).as_posix())
    if commits:
        # --no-renames: a file that moved counts under its old path and its new one, each with its rules
        listed = subprocess.run(["git", "-C", str(root), "diff", "--name-only", "--no-renames", "-z", commits], capture_output=True, text=True, check=False)
        if listed.returncode != 0:
            raise SettingsError(f"git diff --name-only {commits} failed: {listed.stderr.strip()}")
        changed += [name for name in listed.stdout.split("\0") if name]
    changed = sorted(set(changed))
    if not files and not commits:
        raise SettingsError("rules needs the files a change touches: name them, or pass --range BASE..TIP")
    folders = style_folders(settings)
    folder = folders[0]
    # Each file once by where it really is, so a file linked into both folders is one rule. Two
    # files of one name, one in each folder, are two files: both are read, the named folder's first.
    rules, seen, files_read = [], set(), []
    for one in folders:
        for file in rule_files(one):
            if os.path.realpath(file) not in seen:
                seen.add(os.path.realpath(file))
                files_read.append(file)
    for file in files_read:
        shown = file.relative_to(root).as_posix() if file.is_relative_to(root) else str(file)
        globs = rule_scope(file, shown)
        if globs is None:
            rules.append({"file": str(file), "scope": "every path"})
            continue
        try:
            patterns = [(glob, glob_regex(one)) for glob in globs for one in braces(glob.removeprefix("./"))]
        except re.error as error:
            raise SettingsError(f"{shown}: a glob of its `paths:` does not read as a pattern ({error}); correct it, most likely a `[` with no `]` or a range that runs backwards") from error
        covers = sorted({name for name in changed for _, pattern in patterns if pattern.fullmatch(name)})
        if covers:
            rules.append({"file": str(file), "scope": sorted({glob for glob, pattern in patterns if any(pattern.fullmatch(name) for name in changed)}), "covers": covers})
    print(json.dumps({"styleguide": str(folder), "exists": folder.is_dir(), "folders": [str(one) for one in folders], "files": changed, "rules": rules}, indent=2))


STATE_ROOTS: dict[Path, Path] = {}


def state_root(root: Path) -> Path:
    """The folder task state lives in, `.lem/state/` of the main checkout, as `lem_state` says; asked once a run."""
    if root not in STATE_ROOTS:
        try:
            STATE_ROOTS[root] = lem_state.folder(root)
        except lem_state.StateError as error:
            raise SettingsError(str(error)) from error
    return STATE_ROOTS[root]


def taken_on_remote(root: Path, slug: str, branch: str | None) -> None:
    """Refuse a new task whose branch origin has already: a teammate's work, or a task of another
    machine. The name is the one `--branch` gives, else TYPE/SLUG for every type a task takes. One
    question to origin; a repository with no remote has nobody to collide with, and an origin that
    does not answer is said on stderr, since the push of `lem land propose` refuses such a branch too."""
    if subprocess.run(["git", "-C", str(root), "remote", "get-url", "origin"], capture_output=True, text=True, check=False).returncode != 0:
        return
    names = [branch] if branch else [f"{kind}/{slug}" for kind in TYPES]
    asked = subprocess.run(["git", "-C", str(root), "ls-remote", "--heads", "origin", *(f"refs/heads/{name}" for name in names)],
                           capture_output=True, text=True, check=False, stdin=subprocess.DEVNULL)
    if asked.returncode != 0:
        said = [line.strip() for line in (asked.stderr or asked.stdout).splitlines() if line.strip()]
        print(f"project.py: origin did not answer ({said[-1] if said else 'git ls-remote failed'}), so nothing checked that no branch of {slug!r} is there already", file=sys.stderr)
        return
    there = sorted({line.split("\t", 1)[1].removeprefix("refs/heads/") for line in asked.stdout.splitlines() if "\t" in line} & set(names))
    if there:
        raise SettingsError(
            f"origin has the branch {there[0]} already, and no task here holds it: somebody's work, or a task of another machine. "
            "A new task takes a branch of its own: add a word to the slug" + (", or give another --branch" if branch else ""),
        )


def cmd_task_dir(root: Path, slug: str, ask: str | None, ticket: str | None, branch: str | None = None) -> None:
    if not SLUG.fullmatch(slug):
        raise SettingsError(f"slug {slug!r} must be lower-case words joined by hyphens")
    if ask is not None and not ask.strip():
        raise SettingsError("--ask is the owner's words for this task, and they are empty")
    if ask is not None or ticket is not None:
        # This call opens a task. A slug whose task has ended keeps that task's files, its state and
        # what was done to its ticket: a new task under it would start with another task's record.
        ended = next((task["status"] for task in read_tasks(root) if task["slug"] == slug and task["status"] in ENDED), None)
        if ended:
            raise SettingsError(f"the task {slug!r} is {ended}; a new task takes a slug of its own: add a word to this one")
    if ticket is not None:
        if not TICKET.fullmatch(ticket):
            raise SettingsError(f"--ticket {ticket!r} is not a ticket's id, such as MBZ-12")
        ticket = ticket.upper()
        # one ticket is one task: a second task for it would be a second branch for the same work
        tasks = read_tasks(root)
        taken = next((task["slug"] for task in tasks if task["ticket"] == ticket and task["slug"] != slug and task["status"] not in RETURNED), None)
        if taken:
            raise SettingsError(f"the task {taken!r} already holds the ticket {ticket}; go on with that task, or drop it first")
        mine = next((task["ticket"] for task in tasks if task["slug"] == slug), None)
        if mine and mine != ticket:
            # two tickets with one title would give one slug: the first task keeps its ticket
            raise SettingsError(f"the task {slug!r} already holds the ticket {mine}; give the task for {ticket} another slug")
    directory = state_root(root) / "tasks" / slug
    if (ask is not None or ticket is not None) and not directory.is_dir():
        taken_on_remote(root, slug, branch)
    (directory / "reports").mkdir(parents=True, exist_ok=True)
    if ask is not None:
        # The owner's words, as given. task.md is a document with headings; the board and the
        # status show these words, so they have a file of their own that nothing rewrites.
        (directory / "ask.txt").write_text(ask.strip() + "\n", encoding="utf-8")
    if ticket is not None:
        (directory / "ticket.txt").write_text(ticket + "\n", encoding="utf-8")
    print(directory)


def cmd_ticket_step(root: Path, slug: str, step: str) -> None:
    """Write down one thing Lem did to the task's ticket, after the tracker took it."""
    directory = task_directory(root, slug)
    ticket = directory / "ticket.txt"
    if not ticket.is_file():
        raise SettingsError(f"the task {slug!r} came from no ticket")
    if step not in TICKET_STEPS:
        raise SettingsError(f"{step!r} is not a step{nearest(step, TICKET_STEPS)}")
    file = directory / "ticket-steps.txt"
    steps = text_of(file).split() if file.is_file() else []
    if step in steps:
        # the caller should have looked first: a step that is written down was done, and is not done again
        raise SettingsError(f"the step {step!r} is already written down for {text_of(ticket).strip()}: it was done, do not do it again")
    file.write_text("\n".join([*steps, step]) + "\n", encoding="utf-8")
    print(json.dumps({"slug": slug, "ticket": text_of(ticket).strip(), "steps": [*steps, step]}))


def ask_of(directory: Path) -> str | None:
    """What the owner asked for: the words `task-dir --ask` kept, else the first words of task.md without their markup."""
    for name in ("ask.txt", "task.md"):
        file = directory / name
        lines = [line.strip() for line in text_of(file).splitlines() if line.strip()] if file.is_file() else []
        if lines:
            return " ".join(lines) if name == "ask.txt" else lines[0].lstrip("#> ").strip() or None
    return None


def cmd_worktree_dir(settings: dict, slug: str) -> None:
    """Print where a task's worktree goes, and keep the folder that holds worktrees out of git status."""
    if not SLUG.fullmatch(slug):
        raise SettingsError(f"slug {slug!r} must be lower-case words joined by hyphens")
    parent = Path(settings["paths"]["worktrees"]["path"])
    parent.mkdir(parents=True, exist_ok=True)
    ignore = parent / ".gitignore"
    if not ignore.is_file():
        # `*` ignores the folder's content and this file, so the project needs no ignore rule
        ignore.write_text("*\n", encoding="utf-8")
    print(parent / slug)


def cmd_worktree(root: Path, settings: dict, slug: str, branch: str) -> None:
    """Make the task's worktree where `worktree-dir` says, on BRANCH. A new branch starts from the
    base branch as origin has it now, after a fetch: the local base branch may be days old. It gets
    no upstream, so that no `git push` of a builder's reaches the base. With no remote, or an
    origin that does not answer (said in one line on stderr), it starts from the local base branch."""
    def git(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", "-C", str(main), *args], capture_output=True, text=True, check=False, stdin=subprocess.DEVNULL)

    def said(ran: subprocess.CompletedProcess) -> str:
        lines = [line.strip() for line in (ran.stderr or ran.stdout).splitlines() if line.strip()]
        return lines[-1] if lines else f"exit {ran.returncode}"

    main = main_checkout(root)
    if not SLUG.fullmatch(slug):
        raise SettingsError(f"slug {slug!r} must be lower-case words joined by hyphens")
    if git("check-ref-format", "--branch", branch).returncode != 0:
        raise SettingsError(f"{branch!r} is not a name git takes for a branch")
    base = settings["branch"]["base"]
    if base is None:
        raise SettingsError(f"{SETTINGS} names no branch.base, so a new task has nothing to start from")
    if branch == base or branch in settings["branch"]["protected"]:
        raise SettingsError(f"{branch!r} is the base branch or a protected one; a task works on a branch of its own")
    parent = Path(settings["paths"]["worktrees"]["path"])
    place = main / parent.relative_to(root.resolve()) / slug
    if (place / ".git").exists():
        on = subprocess.run(["git", "-C", str(place), "branch", "--show-current"], capture_output=True, text=True, check=False).stdout.strip()
        if on != branch:
            raise SettingsError(f"{place} is a worktree on {on or 'no branch'}, not on {branch}: the task's worktree is the one on its branch")
        print(json.dumps({"task": slug, "worktree": str(place), "branch": branch, "made": False, "from": None}, indent=2))
        return
    place.parent.mkdir(parents=True, exist_ok=True)
    if not (place.parent / ".gitignore").is_file():
        (place.parent / ".gitignore").write_text("*\n", encoding="utf-8")
    if git("rev-parse", "--verify", "--quiet", f"refs/heads/{branch}").returncode == 0:
        # a branch the task has already (a night draft, a task whose worktree was removed): as it is
        made, start = git("worktree", "add", str(place), branch), branch
    else:
        start = base
        if git("remote", "get-url", "origin").returncode == 0:
            fetched = git("fetch", "-q", "origin", base)
            if fetched.returncode == 0:
                start = f"origin/{base}"
            else:
                print(f"project.py: origin did not answer ({said(fetched)}), so {slug} starts from the local {base} as it is now", file=sys.stderr)
        made = git("worktree", "add", "--no-track", "-b", branch, str(place), start)
    if made.returncode != 0:
        raise SettingsError(f"git could not make the worktree {place} on {branch}: {said(made)}")
    commit = subprocess.run(["git", "-C", str(place), "rev-parse", "HEAD"], capture_output=True, text=True, check=False).stdout.strip()
    print(json.dumps({"task": slug, "worktree": str(place), "branch": branch, "made": True, "from": start, "commit": commit}, indent=2))


def task_directory(root: Path, slug: str) -> Path:
    if not SLUG.fullmatch(slug):
        raise SettingsError(f"slug {slug!r} must be lower-case words joined by hyphens")
    directory = state_root(root) / "tasks" / slug
    if not directory.is_dir():
        raise SettingsError(f"no task {slug!r}; `lem project task-dir {slug}` makes its directory")
    return directory


def append_event(root: Path, event: str, slug: str, fields: dict) -> dict:
    """Append one record to the log, and to the copy of it the board can load."""
    record = {"ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "event": event, "task": slug, **fields}
    line = json.dumps(record, ensure_ascii=False)
    try:
        line.encode("utf-8")
    except UnicodeEncodeError as error:
        # a `key:=json` value may spell a lone surrogate, "\udcff", which no UTF-8 file can hold
        raise SettingsError(f"a field of the event is not UTF-8 text ({line[max(0, error.start - 20):error.start]!r} comes before it); give its text in UTF-8") from error
    directory = state_root(root)
    with (directory / "events.jsonl").open("a", encoding="utf-8") as log:
        log.write(line + "\n")
    with (directory / "events.js").open("a", encoding="utf-8") as feed:
        feed.write(f"lemEvent({line});\n")
    return record


def task_worktree(root: Path, settings: dict, slug: str) -> dict:
    """The branch and the newest commit of the task's worktree; nothing when it has no worktree."""
    def git(where: Path, *args: str) -> str | None:
        ran = subprocess.run(["git", "-C", str(where), *args], capture_output=True, text=True, check=False)
        return ran.stdout.strip() if ran.returncode == 0 and ran.stdout.strip() else None

    # Worktrees hang off the main checkout, and this may run in one of them.
    path = main_checkout(root) / Path(settings["paths"]["worktrees"]["path"]).relative_to(root.resolve()) / slug
    if not (path / ".git").exists():
        return {}
    commit = git(path, "log", "-1", "--format=%h%x00%s")
    head, _, subject = (commit or "").partition("\0")
    found = {"branch": git(path, "branch", "--show-current"), "head": head or None, "subject": subject or None}
    return {key: value for key, value in found.items() if value}


def cmd_state(root: Path, slug: str, status: str, lines: list[str], start_over: bool = False) -> None:
    """Put a new block at the top of the task's state.md, and the same as an event in the log."""
    directory = task_directory(root, slug)
    settings = load(root)
    if status not in STATES:
        raise SettingsError(f"status {status!r} is not one a task has{nearest(status, STATES)}")
    if start_over and status != "ready":
        raise SettingsError(f"--start-over gives a landing's line back, and only the state ready does that, not {status}")
    if any(not line.strip() or "\n" in line for line in lines):
        # a blank line ends a block, so one inside a block would hide the lines after it
        raise SettingsError("each LINE of a state block is one line of text, and none is empty")
    for line in lines:
        type_line(line)
    # the status the newest block gives, read from this task's file alone
    written = text_of(directory / "state.md").strip() if (directory / "state.md").is_file() else ""
    first = STATE_LINE.fullmatch(written.split("\n\n")[0].splitlines()[0]) if written else None
    now = first["status"] if first else None
    if now in ENDED and status != now:
        raise SettingsError(
            f"the task {slug!r} is {now}, and an ended task stays ended: new work for it is a new ask (`/lem new`), "
            f"whose task takes a slug of its own. A reply or a message about {slug} that comes now is a stale wake-up, and nothing is done for it",
        )
    if now in WITH_LANDING and status in LEADS_WRITE and not (status == "ready" and start_over):
        raise SettingsError(
            f"the task {slug!r} is {now}: it is with its landing, and a reply or a message about {slug} that comes now is a stale wake-up, "
            f"and no state is written for it; what the landing needs, land.py says itself",
        )
    if status == "answered":
        answered_form(root, directory, slug)
    # the time is the clock's, never a writer's estimate
    since = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    block = "\n".join([f"{since} {status}: {lines[0].strip()}", *(line.strip() for line in lines[1:])])
    file = directory / "state.md"
    older = text_of(file).strip() if file.is_file() else ""
    # the process's id in the name: two writers at one moment never write one new file
    fresh = directory / f"state.md.{os.getpid()}.new"
    fresh.write_text(block + ("\n\n" + older if older else "") + "\n", encoding="utf-8")
    fresh.replace(file)
    append_event(root, "task.state", slug, {
        "status": status, "text": lines[0].strip(), "lines": [line.strip() for line in lines[1:]],
        "ask": ask_of(directory),
        "limit": settings["flow"]["max_tasks"], **task_worktree(root, settings, slug),
    })
    print(json.dumps({"slug": slug, "status": status, "since": since}))


def type_line(line: str) -> dict | None:
    """The type of the request, when the line names one: `type: fix, because the total is wrong
    today`. The status and the board read it, so a line that starts with `type:` has this form. A
    `kind:` line, the form an older Lem wrote, is refused with the type line to write."""
    text = line.strip()
    if text.startswith("kind:"):
        old = OLD_KIND_LINE.fullmatch(text)
        named = OLD_KINDS.get(old["kind"]) if old else None
        raise SettingsError(
            f"the line {text!r} is the kind line of an older Lem: a task has a type now, one of {', '.join(TYPES)}; write it as "
            f"`type: {named or 'TYPE'}, because {old['why'].strip() if old and old['why'] else '...'}`",
        )
    if not text.startswith("type:"):
        return None
    found = TYPE_LINE.fullmatch(text)
    kind = found["type"] if found else text.removeprefix("type:").strip()
    if kind not in TYPES:
        raise SettingsError(f"{kind!r} is not a type of request{nearest(kind, TYPES)}; a type line reads `type: TYPE, because WHY`, with TYPE one of {', '.join(TYPES)}")
    if not found or not found["why"]:
        raise SettingsError(f"the line {text!r} names the type without its reason: write it as `type: {kind}, because ...`")
    return {"type": kind, "why": found["why"].strip()}


def old_kind_line(line: str) -> dict | None:
    """The type a `kind:` line of an older Lem reads as, with its reason; none for any other line.
    A later change may drop it once no task whose state holds such a line is open."""
    found = OLD_KIND_LINE.fullmatch(line.strip())
    if not found or found["kind"] not in OLD_KINDS or not found["why"]:
        return None
    return {"type": OLD_KINDS[found["kind"]], "why": found["why"].strip()}


def investigation_now(record: dict | None) -> dict | None:
    """An investigation's record in the form of now: one an older Lem wrote (`kind=bug|investigation`,
    the calls `correction` and `usual`) reads as `type=fix|question` and `small` and `full`. A later
    change may drop the old form once no task with such a record is open."""
    if record is None or "kind" not in record or "type" in record:
        return record
    out = {key: value for key, value in record.items() if key != "kind"}
    out["type"] = OLD_INVESTIGATION_KINDS.get(record["kind"], record["kind"])
    out["call"] = OLD_CALLS.get(record.get("call"), record.get("call"))
    return out


def answered_form(root: Path, directory: Path, slug: str) -> None:
    """A task is answered only when it has something to show: the investigation's report in its
    directory, and a record of it whose call ends the task (a question answered, a bug that is none)."""
    if not (directory / "investigation.md").is_file():
        raise SettingsError(
            f"the task {slug!r} has no investigation.md in its directory: an answered task ends with its report; "
            "write the investigator's report there first",
        )
    found = newest_events(root, "investigation").get(slug)
    if not found or found.get("call") not in ANSWERING:
        said = f"its newest says {found.get('call')!r}" if found else "it has none"
        raise SettingsError(
            f"the task {slug!r} is answered only after a record whose call is not-a-bug or answer (`log {slug} investigation ...`); {said}",
        )


def investigation_form(fields: dict) -> None:
    """What the investigation of a fix or of a question found, which Lem writes after it reads the
    report: the type, the call that sets the next path, one line (the cause, the answer, or what was
    tried), the cause's place, and for a fix whether the bug was reproduced."""
    form = "investigation takes type=fix|question call=CALL line=TEXT [where=PATH:SYMBOL] [reproduced:=true|false, for a fix]"
    if "kind" in fields:
        # the form of an older Lem: its kind and two of its calls have the names of now
        kind = OLD_INVESTIGATION_KINDS.get(fields["kind"], "fix|question")
        call = OLD_CALLS.get(fields.get("call"), fields.get("call"))
        raise SettingsError(f"{form}: kind=bug|investigation is the form of an older Lem; write type={kind}" + (f" call={call}" if call else ""))
    allowed = {"type", "call", "line", "where", "reproduced"}
    if not {"type", "call", "line"} <= set(fields) <= allowed:
        raise SettingsError(f"{form}, and nothing else; this one has {', '.join(sorted(fields)) or 'no field'}")
    kind, call = fields["type"], fields["call"]
    if kind not in CALLS:
        raise SettingsError(f"{form}: type is fix or question, not {kind!r}")
    if call not in CALLS[kind]:
        raise SettingsError(f"{form}: call is small, full, not-a-bug or not-reproduced for a fix, and answer for a question; this one is {call!r} for a {kind}")
    if not isinstance(fields["line"], str) or not fields["line"].strip() or "\n" in fields["line"]:
        raise SettingsError(f"{form}: line is one line of text: the cause, the answer, or what was tried")
    if "where" in fields and (not isinstance(fields["where"], str) or not fields["where"].strip()):
        raise SettingsError(f"{form}: where is the cause's file and symbol, as path:symbol")
    if kind == "question" and "reproduced" in fields:
        raise SettingsError(f"{form}: reproduced is a fix's; the investigation of a question answers it and reproduces nothing")
    if kind == "fix":
        if not isinstance(fields.get("reproduced"), bool):
            raise SettingsError(f"{form}: a fix's record says whether the bug was reproduced, as reproduced:=true or reproduced:=false, written with :=")
        if call in ("small", "full") and not fields.get("where"):
            raise SettingsError(f"{form}: a plain cause has a place: where names the cause's file and symbol")
        if call == "not-reproduced" and fields["reproduced"]:
            raise SettingsError(f"{form}: not-reproduced is a bug that was not reproduced, and this record says it was")


def cmd_log(root: Path, slug: str, event: str, pairs: list[str]) -> None:
    """Append one event about a task; `state` is the only writer of task.state."""
    task_directory(root, slug)
    if event == "task.state":
        raise SettingsError("task.state is written by `lem project state`, which also writes the state block")
    fields: dict[str, object] = {}
    for pair in pairs:
        key, separator, raw = pair.partition("=")
        typed = key.endswith(":")
        key = key.removesuffix(":")
        if not separator or not key:
            raise SettingsError(f"{pair!r} is neither key=value nor key:=json")
        if key in fields or key in ("ts", "event", "task"):
            raise SettingsError(f"field {key!r} is given twice or is one the log sets itself")
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
        # the bound its rules give, beside the record, so that a reader says when the talk went over it
        fields["bound"] = TURNS_PER_QUESTION * fields["questions"] + TURNS_AROUND
    if event in OLD_EVENTS:
        raise SettingsError(f"{event} is the name an older Lem gave this event; it is {OLD_EVENTS[event]} now, with the same fields" + (" and criteria:=N for stories:=N" if event == "stories.read" else ""))
    if event == "criteria.read":
        read_form(fields)
    if event == "investigation":
        investigation_form(fields)
    print(json.dumps(append_event(root, event, slug, fields)))


def read_form(fields: dict) -> None:
    """The personas' read of the criteria is read by the landing, so it has one form: who ran it,
    how many personas were asked and how many answered, the model families that answered, each
    source that did not answer and why, how many criteria were read and flagged, whether the
    families split, and the digest of the criteria it read (`lem criteria digest`)."""
    form = (
        "criteria.read takes by=lem|lead asked:=N answered:=N families:='[\"FAMILY\", ...]' "
        "silent:='[{\"name\": SOURCE, \"why\": WHY}, ...]' criteria:=N flagged:=N split:=true|false digest=DIGEST"
    )
    counts = ("asked", "answered", "criteria", "flagged")
    if set(fields) != {"by", "families", "silent", "split", "digest", *counts}:
        raise SettingsError(f"{form}, and nothing else; this one has {', '.join(sorted(fields)) or 'no field'}")
    if fields["by"] not in ("lem", "lead"):
        raise SettingsError(f"{form}: by is lem, when Lem ran the read in its session, or lead, when the task's lead ran it")
    if not all(isinstance(fields[key], int) and not isinstance(fields[key], bool) and fields[key] >= 0 for key in counts):
        raise SettingsError(f"{form}: each N is a whole number, written with := so that it stays one")
    families = fields["families"]
    if not isinstance(families, list) or not all(isinstance(name, str) and name.strip() for name in families) or len(set(families)) != len(families) \
            or (fields["answered"] and not families):
        raise SettingsError(f"{form}: families is the list of the model families that answered, each named once, as in families:='[\"opus\", \"sol\"]'")
    silent = fields["silent"]
    if not isinstance(silent, list) or not all(
        isinstance(item, dict) and set(item) == {"name", "why"} and all(isinstance(value, str) and value.strip() for value in item.values()) for item in silent
    ):
        raise SettingsError(f"{form}: silent is a list of {{\"name\": ..., \"why\": ...}}, one for each source that did not answer; [] when every one did")
    if not isinstance(fields["split"], bool):
        raise SettingsError(f"{form}: split is true when the two families answered a criterion differently, false otherwise, written with :=")
    if not isinstance(fields["digest"], str) or not re.fullmatch(r"[0-9a-f]{12}", fields["digest"]):
        raise SettingsError(f"{form}: digest is the twelve characters `lem criteria digest` prints for the criteria that were read")
    # every project's cast has two people or more
    if fields["asked"] < 2:
        raise SettingsError(f"{form}: a read asks two personas at the least")
    if fields["answered"] > fields["asked"]:
        raise SettingsError(f"{form}: answered is at most asked; 0 is a read in which nobody answered")
    # A read in which nobody answered is written down too, and started once more: the landing
    # counts two in a row as the criteria going on unread, and the request as not green.
    if fields["answered"] == 0 and (families or fields["flagged"] or fields["split"] or len(silent) < fields["asked"]):
        raise SettingsError(
            f"{form}: a read in which nobody answered has families:='[]', flagged:=0 and split:=false, "
            "and silent names each source that was asked, one for each persona at the least, with why",
        )
    if fields["answered"] < fields["asked"] and not silent:
        raise SettingsError(f"{form}: when fewer answered than were asked, silent names each source that did not, with why")
    if fields["criteria"] < 1 or fields["flagged"] > fields["criteria"]:
        raise SettingsError(f"{form}: a read has one criterion at the least, and no more criteria flagged than it read")
    if fields["split"] and len(families) < 2:
        raise SettingsError(f"{form}: a split is between two model families, and families names one")


# The start of each stage that logs its end and had no start, so that the board draws a span from
# the one to the other (the owner's pick of 2026-11-17: "each stage logs its start, and the card
# becomes exact"). Event -> (its form, the fields it takes, the values each may have). An agent logs
# the first six where its stage text says; land.py logs the last three itself. The end of each:
# `interview.start` ends at the first `criteria.read.start` or `criteria.approved` after it, the
# scout at `scout`, the read at `criteria.read`, an investigation at `investigation`, a builder's
# job at the next state block or step of the landing after it, the polish pass at `polish`, the
# checks at their last `gate` or `task.red` (the events keep the step's older name), and the review at `review`.
BUILDER_JOBS = ("the small change", "the repair of a conflict with the base", "the repair of a failed check", "the fix of a review's findings")
TASK_JOB = re.compile(r"task [1-9]\d* of [1-9]\d*")
STARTS: dict[str, tuple[str, dict[str, tuple[str, ...] | None]]] = {
    "interview.start": ("interview.start takes nothing", {}),
    "scout.start": ("scout.start takes nothing", {}),
    "scout": ("scout, the end of the scout's read, takes nothing", {}),
    "criteria.read.start": ("criteria.read.start takes by=lem|lead, and nothing else", {"by": ("lem", "lead")}),
    "investigation.start": ("investigation.start takes type=fix|question, and nothing else", {"type": ("fix", "question")}),
    "builder.start": (
        f"builder.start takes job=JOB, and nothing else: `task N of M`, or one of {', '.join(BUILDER_JOBS)}; the polish pass logs its own start (`lem land polish`)",
        {"job": None},
    ),
    "polish.start": ("polish.start takes before=TIP, and land.py polish writes it", {"before": None}),
    "gate.start": ("gate.start takes tip=TIP commands:=N, and land.py checks writes it", {"tip": None, "commands": None}),
    "review.start": ("review.start takes attempt:=N floor=read|round|full, and land.py read writes it", {"attempt": None, "floor": ("read", "round", "full")}),
}


def start_form(event: str, fields: dict) -> None:
    """A stage's start has one form, so that the board can draw its span from it to its end."""
    form, wants = STARTS[event]
    if set(fields) != set(wants):
        raise SettingsError(f"{form}; this one has {', '.join(sorted(fields)) or 'no field'}")
    for key, allowed in wants.items():
        value = fields[key]
        if allowed is not None and value not in allowed:
            raise SettingsError(f"{form}; {key} is {value!r}")
    if event == "builder.start" and not (fields["job"] in BUILDER_JOBS or (isinstance(fields["job"], str) and TASK_JOB.fullmatch(fields["job"]))):
        raise SettingsError(f"{form}; job is {fields['job']!r}")
    if event in ("polish.start", "gate.start") and not (isinstance(fields.get("before", fields.get("tip")), str) and re.fullmatch(r"[0-9a-f]{7,40}", fields.get("before", fields.get("tip")))):
        raise SettingsError(f"{form}; the tip is a commit, as git names it")
    for key in ("commands", "attempt"):
        if key in fields and not (isinstance(fields[key], int) and not isinstance(fields[key], bool) and fields[key] >= 1):
            raise SettingsError(f"{form}; {key} is a whole number, 1 or more, written with :=")


def talk_start_form(fields: dict) -> None:
    """The start of a plan talk, written when the reviewer's seat opens, so that the board can draw
    the talk's minutes from two events: it names the reviewer, and nothing else."""
    if set(fields) != {"reviewer"} or not isinstance(fields["reviewer"], str) or not fields["reviewer"].strip():
        raise SettingsError(f"plan.talk.start takes reviewer=AGENT, and nothing else; this one has {', '.join(sorted(fields)) or 'no field'}")


# The most turns a talk of N questions has by its rules: the reviewer's list, two answers of the defender
# and two of the reviewer on each question (a question that holds a second time stops), and the close.
# Derived from the rules of `stages/talk.md`, in a Fable second opinion (2026-11-16); no talk
# under these rules has been measured yet. It is the defender's to keep, not a check of the record: a
# talk that ran longer is written as it ran, and `log` adds the bound to it, so the pull request and
# the board can say that it went over.
TURNS_PER_QUESTION = 4
# The names an older Lem gave the personas' read and its start, which `log` refuses with the name of
# now. The landing and the board still read events of the old names; a later change may drop this
# once no task with such an event is open.
OLD_EVENTS = {"stories.read": "criteria.read", "stories.read.start": "criteria.read.start"}
TURNS_AROUND = 2


def talk_form(fields: dict) -> None:
    """A plan talk's record is read by the landing, so it has one form: who argued the plan with its
    defender, how many turns the talk had, how many questions the reviewer's first list held, how many
    of them it settled and left open, how many the lead repaired, how many of the open ones are a
    design choice (a question that held a second time), how many questions were raised after the
    list and not argued, and three counts of Fable's check for a layer of patches (2026-11-16):
    `root`, the repairs that changed a decision of the plan; `layer`, the repairs that put a
    mechanism over a decision the plan cites (a criterion, a ruling, existing code) and stayed; and
    `shared`, the decisions two questions named."""
    form = "plan.talk takes reviewer=AGENT turns:=N questions:=N settled:=N open:=N repaired:=N design:=N unargued:=N root:=N layer:=N shared:=N"
    counts = ("turns", "questions", "settled", "open", "repaired", "design", "unargued", "root", "layer", "shared")
    if set(fields) != {"reviewer", *counts}:
        raise SettingsError(f"{form}, and nothing else; this one has {', '.join(sorted(fields)) or 'no field'}")
    if not isinstance(fields["reviewer"], str) or not fields["reviewer"].strip():
        raise SettingsError(f"{form}: reviewer names the agent that argued the plan with its defender")
    if not all(isinstance(fields[key], int) and not isinstance(fields[key], bool) and fields[key] >= 0 for key in counts):
        raise SettingsError(f"{form}: each N is a whole number, written with := so that it stays one")
    turns, questions = fields["turns"], fields["questions"]
    # A floor against an empty record, not a measure of a good talk. A reviewer that found nothing
    # says so in its first turn, and the defender closes: a talk of no question has those two turns.
    if turns < 2:
        raise SettingsError(f"{form}: a talk has two turns at the least: the reviewer's list, which may be empty, and the close")
    if questions == 0 and fields["unargued"] and turns <= TURNS_AROUND:
        raise SettingsError(f"{form}: a talk of no question and two turns has no turn after the list, so unargued is 0")
    if fields["settled"] + fields["open"] != questions:
        raise SettingsError(f"{form}: each question of the reviewer's first list ends settled or left open, so settled and open add up to questions")
    if fields["design"] > fields["open"]:
        raise SettingsError(f"{form}: a design choice is a question left open because it held a second time, so design is at most open")
    if fields["repaired"] > questions:
        raise SettingsError(f"{form}: repaired counts the questions whose answer changed the plan, so repaired is at most questions")
    if fields["root"] + fields["layer"] > fields["repaired"]:
        raise SettingsError(
            f"{form}: a repair either changed a decision of the plan (root) or put a mechanism over a decision with a cite (layer), "
            "or neither, so root and layer add up to at most repaired",
        )
    # No check of the rules themselves: a talk over its bound of turns, or one whose second question on
    # a decision did not close as a design choice, is a fact, and a record refused for it would leave
    # the companion open and the request unproposed for ever.


def ticket_owed(status: str | None, steps: list[str], tracker: dict | None) -> list[str]:
    """The steps a ticket still waits for, now that its task has ended. A session may be cut off
    between a task's last state and the tracker, and this is how the next one sees it."""
    if tracker is None:
        return []
    if status == "landed":
        wanted = ["commented", *(["landed"] if tracker["moves"] == "lem" else [])]
    elif status in RETURNED:
        # the comment of the tracker's "drop" or "answer", and no status: where it goes is the owner's call
        wanted = [status]
    else:
        wanted = []
    return [step for step in wanted if step not in steps]


def proposal(directory: Path) -> dict | None:
    """What `lem land propose` kept for a task: the pull request's address, when there is one, and green or the reasons it is not."""
    kept_file = directory / "landing.json"
    if not kept_file.is_file():
        return None
    # every task's record is read here, so one that does not read stops `tasks` for all: the message says how to start that landing over
    way_out = (
        f"land.py writes it whole, so something else wrote it. Move it aside, then `lem project state {directory.name} ready --start-over \"WHY\"` "
        f"and `lem land start {directory.name}` start the landing over: its checks and its review run again"
    )
    try:
        kept = json.loads(kept_file.read_bytes().decode("utf-8"))
    except ValueError as error:
        raise SettingsError(f"{kept_file} does not read as JSON ({error}); {way_out}") from error
    if not isinstance(kept, dict):
        raise SettingsError(f"{kept_file} is not an object, as the landing's record is; {way_out}")
    if not kept.get("proposed"):
        return None
    reasons = kept.get("not_green", [])
    # Whether the forge called the pull request conflicting with the base when `lem land merged` last
    # asked, on the head Lem pushed: null when nothing asked, the forge did not know, or the head moved since.
    forge = kept.get("forge") if isinstance(kept.get("forge"), dict) else {}
    pushed = kept.get("pushed") or kept.get("proposed")
    conflict = {"CONFLICTING": True, "MERGEABLE": False}.get(forge.get("mergeable")) if pushed and forge.get("head") == pushed else None
    return {"pull_request": (kept.get("pr") or {}).get("url"), "green": not reasons, "not_green": reasons, "conflict": conflict}


def newest_events(root: Path, event: str) -> dict[str, dict]:
    """Each task's newest event of one name in the event log. Lem closes a talk's companion, and a
    builder leads the build of a careful or large plan, only on the newest `plan.talk`, never on a
    line that says so; Lem takes a bug's next path on the newest `investigation`."""
    log, found = state_root(root) / "events.jsonl", {}
    if not log.is_file():
        return found
    for number, line in enumerate(text_of(log).splitlines(), 1):
        if f'"{event}"' not in line:
            continue
        try:
            record = json.loads(line)
        except ValueError as error:
            raise SettingsError(f"{log}:{number} does not read as JSON ({error}); the log is written by project.py, never by hand") from error
        if record.get("event") == event:
            found[record.get("task")] = record
    return found


def type_of(text: str) -> dict | None:
    """The newest type of the request that a block of state.md names (newest block first). A `kind:`
    line that an older Lem wrote reads as the type its kind maps to."""
    for line in text.splitlines():
        try:
            found = type_line(line)
        except SettingsError:
            # state wrote every type line in its form; a line written by hand that is not is no type,
            # and a kind line of an older Lem is read as its type
            found = old_kind_line(line)
        if found:
            return found
    return None


def read_tasks(root: Path) -> list[dict]:
    tasks = []
    talks = newest_events(root, "plan.talk")
    investigations = newest_events(root, "investigation")
    parent = state_root(root) / "tasks"
    for directory in sorted(d for d in (parent.iterdir() if parent.is_dir() else ()) if d.is_dir()):
        state = directory / "state.md"
        # state.md is newest block first; a block ends at the first blank line
        written = text_of(state) if state.is_file() else ""
        block = written.strip().split("\n\n")[0] if written.strip() else None
        first = STATE_LINE.fullmatch(block.splitlines()[0]) if block else None
        known = first is not None and first["status"] in STATES
        tasks.append({
            "slug": directory.name,
            "ask": ask_of(directory),
            # the tracker's ticket the ask came from; a dropped or answered task gives its ticket back
            "ticket": text_of(directory / "ticket.txt").strip() or None if (directory / "ticket.txt").is_file() else None,
            # what Lem did to that ticket so far (TICKET_STEPS)
            "ticket_steps": text_of(directory / "ticket-steps.txt").split() if (directory / "ticket-steps.txt").is_file() else [],
            "ticket_owed": [],
            # null when no block was written through `project.py state`: nobody can tell who acts next
            "status": first["status"] if known else None,
            "since": first["since"] if known else None,
            "state": block,
            # what the landing proposed to the owner, for the status and the board: where, and green or why not
            "proposal": proposal(directory),
            # the newest record of its plan talk, as `log plan.talk` wrote it, or null when it had none
            "talk": talks.get(directory.name),
            # the type of the request with its reason, from the newest block that names it, or null
            "type": type_of(written),
            # what the investigation of a fix or a question found, as `log investigation` wrote it last, or null
            "investigation": investigation_now(investigations.get(directory.name)),
        })
    if any(task["ticket"] for task in tasks):
        # only a project with a ticket needs its settings here; a broken settings file then stops this, loudly
        tracker = load(root)["tracker"]
        for task in tasks:
            if task["ticket"]:
                task["ticket_owed"] = ticket_owed(task["status"], task["ticket_steps"], tracker)
    return tasks


def cmd_may_start(settings: dict, root: Path, slug: str) -> None:
    """Exit 1 when as many other tasks build or land as the project allows at one time. The task
    whose lead starts is not counted: when it builds already (its investigator called the path, or
    its lead stopped and starts again), the place it holds is the one its next lead takes. A task in
    the landing, proposed or ended gets no lead at all: a stale wake-up must not start one."""
    task_directory(root, slug)
    limit = settings["flow"]["max_tasks"]
    tasks = read_tasks(root)
    status = next((task["status"] for task in tasks if task["slug"] == slug), None)
    if status in ENDED:
        raise SettingsError(f"the task {slug!r} is {status}: an ended task gets no lead, and new work for it is a new ask (`/lem new`) with a slug of its own")
    if status in ("landing", "open"):
        raise SettingsError(
            f"the task {slug!r} is {status}: its build is done, and it gets no lead. Its landing goes on with `land.py` "
            f"(`stages/land.md`; an open task takes the line again with `lem land start {slug}`), and a change the owner asks for now is a new ask",
        )
    # A task queued behind another (`after: OTHER`, which Lem writes for an ask that needs another's
    # result, and a lead for a plan that does) starts when that task has ended, so that it builds on
    # what the other one changed.
    mine = next((task for task in tasks if task["slug"] == slug), None)
    after = next((line.split(":", 1)[1].strip() for line in (mine["state"] or "").splitlines()[1:] if line.startswith("after:")), None) if mine and status == "queued" else None
    if after:
        other = next((task["status"] for task in tasks if task["slug"] == after), None)
        if other not in ENDED:
            raise SettingsError(
                f"the task {slug!r} is queued after {after!r}, which is {other or 'no task'}: it starts when {after} is landed, answered or dropped, "
                f"so that it builds on what {after} changes; when it no longer needs that, write its state `queued` again without the `after:` line",
            )
    running = [task["slug"] for task in tasks if task["status"] in RUNNING and task["slug"] != slug]
    if len(running) >= limit:
        raise SettingsError(
            f"{len(running)} tasks build or land ({', '.join(running)}) and flow.max_tasks is {limit}: "
            f"write the state of {slug} as `queued` and start it when one of them stops; "
            f"only the owner raises the limit, in {SETTINGS}",
        )
    print(json.dumps({"running": running, "limit": limit}))


# The state line of a task whose criteria wait for the owner's yes, and the one an older Lem wrote.
CRITERIA_WAIT = ("the criteria wait for the owner", "the stories wait for the owner")
# Where a retro started with nobody at the terminal keeps its proposals: one file a retro, in the
# state folder, named by its day.
RETROS = "retros"


def retro_proposals(file: Path) -> dict:
    """One retro's file of proposals, as the list of what waits says it: its day, its path and how
    many proposals still wait (the questions of the page's spec). A file that does not read says why."""
    entry: dict = {"date": file.stem, "file": str(file)}
    try:
        spec = json.loads(text_of(file))
    except (ValueError, SettingsError) as error:
        return {**entry, "proposals": None, "problem": f"it does not read as JSON ({error}); the retro writes it again"}
    questions = spec.get("questions") if isinstance(spec, dict) else None
    if isinstance(questions, list):
        return {**entry, "proposals": len(questions)}
    if isinstance(spec, dict) and "prompt" in spec:
        return {**entry, "proposals": 1}
    return {**entry, "proposals": None, "problem": "it holds no question in the form of the question page (`questions`, or one `prompt`)"}


def cmd_waiting(root: Path) -> dict:
    """Everything that waits for the owner, from the files that hold it: nothing here decides or writes."""
    settings = load(root)
    tasks = read_tasks(root)
    asked = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve().parent / "decisions.py"), "--repo", str(root), "pending"],
                           capture_output=True, text=True, check=False)
    if asked.returncode != 0:
        raise SettingsError(asked.stderr.strip().removeprefix("decisions.py: ") or "decisions.py pending failed")
    main = main_checkout(root)
    worktrees = main / Path(settings["paths"]["worktrees"]["path"]).relative_to(root.resolve())
    plans = Path(settings["paths"]["plans"]["path"]).relative_to(root.resolve())

    def line(task: dict) -> str:
        return STATE_LINE.fullmatch(task["state"].splitlines()[0])["text"]

    def brief(task: dict) -> dict:
        return {"task": task["slug"], "ask": task["ask"], "since": task["since"]}

    held = [task for task in tasks if task["status"] == "held"]
    found = {
        "choices": json.loads(asked.stdout)["waiting"],
        "criteria": [{**brief(task), "line": line(task)} for task in held if line(task).startswith(CRITERIA_WAIT)],
        "held": [{**brief(task), "line": line(task)} for task in held if not line(task).startswith(CRITERIA_WAIT)],
        "pull_requests": [
            {**brief(task), "pull_request": task["proposal"]["pull_request"], "green": task["proposal"]["green"], "not_green": task["proposal"]["not_green"],
             "conflict": task["proposal"]["conflict"]}
            for task in tasks if task["status"] == "open" and task["proposal"]
        ],
        "drafts": [
            {**brief(task), "plan": str(plan) if (plan := lem_plans.found(worktrees / task["slug"] / plans, settings["paths"]["plan_file"]["pattern"], task["slug"])) else None}
            for task in tasks if task["status"] == "drafted"
        ],
        "retros": [retro_proposals(file) for file in sorted((state_root(root) / RETROS).glob("*.json"))],
    }
    found["count"] = sum(len(found[key]) for key in ("choices", "criteria", "held", "pull_requests", "drafts")) + sum(
        entry["proposals"] or 1 for entry in found["retros"]
    )
    return found


def cmd_alone(root: Path, words: list[str]) -> int:
    """Run one command under the repository's lock for commands that need the machine to
    themselves, and give its exit status back. Another run that holds the lock is waited for."""
    words = words[1:] if words[:1] == ["--"] else words
    if not words or not any(word.strip() for word in words):
        raise SettingsError("alone takes the command to run: `lem project alone -- COMMAND ...`, or one quoted line for the shell")
    shown = words[0] if len(words) == 1 else " ".join(words)
    path = state_root(root) / ALONE_LOCK
    try:
        handle = path.open("a+", encoding="utf-8")
    except OSError as error:
        raise SettingsError(f"the lock {path} cannot be opened ({error.strerror}); it holds no state, so remove it (`rm -r {path}`) and run this again") from error
    with handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            handle.seek(0)
            holder = handle.read().strip() or "its holder wrote no line yet"
            print(f"project.py: the machine is held by a command that needs it alone ({holder}); this one waits", file=sys.stderr, flush=True)
            fcntl.flock(handle, fcntl.LOCK_EX)
        handle.seek(0)
        handle.truncate()
        handle.write(f"pid {os.getpid()}, since {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}, in {os.getcwd()}: {shown}\n")
        handle.flush()
        proc: subprocess.Popen | None = None

        def stopped(number: int, _frame: object) -> None:
            raise InterruptedError(number)

        before = {sign: signal.signal(sign, stopped) for sign in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP)}
        try:
            # a group of its own, so that what the command starts ends with it when this run is stopped
            proc = subprocess.Popen(words[0] if len(words) == 1 else words, shell=len(words) == 1, start_new_session=True)  # noqa: S602
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
                    # the leader ended; a process it left in the group gets the next signal too
                    try:
                        os.killpg(proc.pid, 0)
                    except (ProcessLookupError, PermissionError):
                        break
            for sign, handler in before.items():
                signal.signal(sign, handler)
            # the holder's line goes with the hold, so that a waiting run never names a run that ended
            handle.seek(0)
            handle.truncate()
    return code if code >= 0 else 128 - code
def nap_time(name: str) -> datetime | None:
    """When the nap of a folder started, from its name; None for a name that holds no such time."""
    found = NAP_NAME.fullmatch(name)
    if not found:
        return None
    try:
        return datetime.strptime(found["time"], NAP_TIME).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def hours(seconds: float) -> str:
    return f"{seconds / 3600:.1f} hours"


def cmd_may_nap(root: Path) -> None:
    """Whether a nap may start now, from the settings and the naps folder. A yes writes the nap
    down as started; every call removes the naps older than `naps.keep_days`."""
    settings = load(root)
    naps = settings["naps"]
    folder = state_root(root) / "naps"
    folder.mkdir(exist_ok=True)
    now = datetime.now(timezone.utc)
    removed, kept = [], []
    for entry in sorted(folder.iterdir()):
        when = nap_time(entry.name)
        if when is None or entry.is_symlink() or not entry.is_dir():
            continue
        if (now - when).total_seconds() > naps["keep_days"] * 86400:
            shutil.rmtree(entry)
            removed.append(entry.name)
        else:
            kept.append((when, entry))
    marker = folder / ASLEEP
    asleep = None
    if marker.is_file():
        try:
            asleep = json.loads(text_of(marker))
            since = datetime.strptime(asleep["since"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            started = asleep["time"]
            if not isinstance(started, str) or not NAP_NAME.fullmatch(started):
                raise ValueError(f"time = {started!r}")
        except (ValueError, KeyError, TypeError) as error:
            raise SettingsError(f"{marker} is not the record may-nap writes ({error}); remove the file, and the next call writes it again") from error
    answer = {"may": False, "why": "", "folder": str(folder), "time": None, "removed": removed,
              "newest": max(kept)[1].name if kept else None}
    # a nap runs until its folder holds waking.md, the last file it writes, and for an hour at most
    woke = asleep is not None and any((nap / "waking.md").is_file() for _when, nap in kept if nap.name.startswith(started))
    if asleep is not None and not woke and (now - since).total_seconds() < ASLEEP_MINUTES * 60:
        answer["why"] = f"a nap runs since {asleep['since']}: it ends when naps/{started}-... holds waking.md, or {ASLEEP_MINUTES} minutes after its start"
    elif not naps["on"]:
        answer["why"] = (f"the naps are off on this machine (naps.on = false in {LOCAL})" if "naps.on" in settings["local"]["overrides"]
                         else f"the naps are off (naps.on = false in {SETTINGS})")
    else:
        last = max([when for when, _nap in kept] + ([since] if asleep is not None else []), default=None)
        age = (now - last).total_seconds() if last else None
        if age is not None and age < naps["gap_hours"] * 3600:
            answer["why"] = f"the newest nap started {hours(age)} ago, and naps.gap_hours is {naps['gap_hours']}"
        else:
            answer["may"] = True
            answer["why"] = "there is no nap yet" if age is None else f"the newest nap started {hours(age)} ago"
            answer["time"] = now.strftime(NAP_TIME)
            record = {"since": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "time": answer["time"]}
            # written whole under another name first, so that a reader never finds half of it
            staging = folder / f"{ASLEEP}.{os.getpid()}"
            staging.write_text(json.dumps(record) + "\n", encoding="utf-8")
            os.replace(staging, marker)
    print(json.dumps(answer, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(prog="lem project", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=".", help="a directory inside the checkout (default: the current one)")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("show")
    commands.add_parser("path").add_argument("name")
    commands.add_parser("may-land").add_argument("branch")
    commands.add_parser("worktree-dir").add_argument("slug")
    worktree = commands.add_parser("worktree", help="make a task's worktree, a new branch from origin's base branch")
    worktree.add_argument("slug")
    worktree.add_argument("branch")
    init = commands.add_parser("init")
    init.add_argument("--base")
    init.add_argument("--existing", choices=("link", "new"))
    init.add_argument("--reviewer", choices=REVIEWERS)
    commands.add_parser("existing")
    commands.add_parser("reviewer").add_argument("words", nargs="+", metavar="AGENT[/MODEL[:EFFORT]]|default")
    plan_file = commands.add_parser("plan-file", help="the name a task's plan takes, and the plan the plans folder holds")
    plan_file.add_argument("slug")
    plan_file.add_argument("--date", metavar="YYYY-MM-DD", help="the day the plan is written (default: today, in UTC)")
    rules = commands.add_parser("rules")
    rules.add_argument("files", nargs="*", metavar="FILE")
    rules.add_argument("--range", dest="commits", metavar="BASE..TIP", help="also the files this range of commits changes")
    task_dir = commands.add_parser("task-dir")
    task_dir.add_argument("slug")
    task_dir.add_argument("--ask", help="the owner's words for this task, as given")
    task_dir.add_argument("--ticket", help="the id of the tracker's ticket the ask came from, e.g. MBZ-12")
    task_dir.add_argument("--branch", help="the branch the task takes, when it is not TYPE/SLUG (a tracker's name, the project's own scheme)")
    state = commands.add_parser("state")
    state.add_argument("slug")
    state.add_argument("status")
    state.add_argument("lines", nargs="+", metavar="LINE")
    state.add_argument("--start-over", action="store_true", help="ready over a task in landing or open: its landing starts over, as land.py's message says")
    commands.add_parser("tasks")
    step = commands.add_parser("ticket-step")
    step.add_argument("slug")
    step.add_argument("step")
    log = commands.add_parser("log")
    log.add_argument("slug")
    log.add_argument("event")
    log.add_argument("fields", nargs="*", metavar="key=value")
    commands.add_parser("may-start").add_argument("slug")
    commands.add_parser("state-dir")
    commands.add_parser("waiting", help="everything that waits for the owner, as JSON")
    alone = commands.add_parser("alone", help="run one command that needs the machine to itself, under the repository's one lock")
    alone.add_argument("words", nargs=argparse.REMAINDER, metavar="-- COMMAND")
    commands.add_parser("may-nap")
    args = parser.parse_args()
    if problem := unreadable_argument(sys.argv[1:]):
        sys.exit(f"project.py: {problem}")
    try:
        root = repo_root(Path(args.repo))
        if args.command == "init":
            cmd_init(root, args.base, args.existing, args.reviewer)
            return
        if args.command == "reviewer":
            cmd_reviewer(root, args.words)
            return
        if args.command == "existing":
            print(json.dumps(older_folders(root), indent=2))
            return
        if args.command == "task-dir":
            cmd_task_dir(root, args.slug, args.ask, args.ticket, args.branch)
            return
        if args.command == "state":
            cmd_state(root, args.slug, args.status, args.lines, args.start_over)
            return
        if args.command == "tasks":
            print(json.dumps(read_tasks(root), indent=2))
            return
        if args.command == "log":
            cmd_log(root, args.slug, args.event, args.fields)
            return
        if args.command == "ticket-step":
            cmd_ticket_step(root, args.slug, args.step)
            return
        if args.command == "state-dir":
            print(state_root(root))
            return
        if args.command == "waiting":
            print(json.dumps(cmd_waiting(root), indent=2))
            return
        if args.command == "alone":
            sys.exit(cmd_alone(root, args.words))
        if args.command == "may-nap":
            cmd_may_nap(root)
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
            cmd_worktree(root, settings, args.slug, args.branch)
        elif args.command == "plan-file":
            cmd_plan_file(settings, args.slug, args.date)
        elif args.command == "may-land":
            cmd_may_land(settings, args.branch)
        else:
            cmd_may_start(settings, root, args.slug)
    except SettingsError as error:
        sys.exit(f"project.py: {error}")


if __name__ == "__main__":
    main()
