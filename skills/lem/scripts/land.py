#!/usr/bin/env python3
"""Take one task's branch from `ready` to a pull request and to the base branch, one step at a time.

Nothing reaches the base branch without the machine checks and a review by an agent that did not
build it, and a task ends as a pull request where there is a forge and the project wants one.
Each step here is one command, prints JSON, and refuses with exit 1 and the reason when the step
may not run; nothing is retried and nothing is forced. Every step first asks `project.py
may-land` about the settings' base branch, so a protected branch is never reached, whoever asks.

    land.py start SLUG     the task takes the landing line: its state becomes `landing`
    land.py base SLUG      bring the base branch in by a rebase; a conflict is reported, not resolved
    land.py polish SLUG    the polish pass starts: what its builder gets, and the tip it starts at
    land.py polish SLUG --done
                           after the polish builder: what it committed is checked, and logged
    land.py gate SLUG      the machine checks on the tip: every gate command, each story's tests,
                           the bar, the size
    land.py read SLUG      whether a review is due, the least it may be, and what a reviewer gets
    land.py read SLUG --record FILE
                           write down what the review was and what it found
    land.py file SLUG [--again]
                           file each defect a review saw outside the change as an item of the
                           backlog, and commit the items on the task's branch
    land.py propose SLUG --title SUBJECT --notes FILE
                           open the pull request, or mark the branch ready where the remote is not
                           GitHub or `branch.propose` is `merge`: the state becomes `open`
    land.py land SLUG --by owner|agent [--message SUBJECT]
                           merge the pull request, or put a ready branch on the base branch
    land.py merged SLUG    the owner merged the pull request on the forge: finish the bookkeeping
    land.py clean SLUG     remove the task's worktree and its branch after the merge

What each step keeps for the next is in `landing.json` in the task's directory: the task's
branch, the base it was rebased on, the commit and tree the checks passed on, each review, and
the pull request. Three steps log the start of what they start, so that the board's time card has
a start and an end for each: `polish` logs `polish.start` when a pass starts (not again for a
second start of the same pass), `gate` logs `gate.start` before its first command, and `read`
logs `review.start` once for the attempt that is due; `polish --done`, the gate's results and
`read --record` are their ends.

A small change has no plan: its one story is `stories.md` in the task directory (`stories.py`
gives `small`), which the steps read in the plan's place. It is one task and never gets a polish
pass (`polish` refuses it): its builder files each defect it saw outside the change in the backlog
folder, in a commit of its own, and the pull request lists each file the branch adds there. It has
no reason for a lowered bar (the gate refuses one: a lowered bar is a feature's), and its pull
request's text is short. One that is careful after all is not green, since it took the short path
with no interview, read or plan.

The machine checks have no model in them. `gate` runs the settings' `gate.commands`, then
`stories.py red` (each story's tests pass on the branch and fail on the base commit), then the
bar. A change lowers the bar when it adds a lint or type suppression, a skipped test or a mark
that runs one test alone, deletes a test file or moves it out of the tests, or leaves fewer
assertions in one (counted by the words `assert` and `expect` on the lines it adds and removes, in a test file and in every Rust file, where unit tests sit beside
the code). A mark counts when the change leaves more of it in a file than the file had, so a
line that only moved is no new mark; a mark whose own text changed is a new one. A lowered bar passes only with a reason for that file under
`## The bar` in the task's plan, as `- PATH: REASON`. The marks looked for are those of Python, JavaScript and
TypeScript, Go, Rust, Java and Kotlin, and shell, and the settings' `gate.bar` patterns for any
file that is not a document. A changed file of another language gets no such check, and the
result says which (`not_covered`). The size of the change is counted, for the reviewer.

A gate with no command to run is refused, since a gate that ran nothing shows nothing; so is one
whose command changed a tracked file or made a commit on the branch, since its result is then
about another tree. A file its commands wrote that git neither tracks nor ignores (Python's bytecode
in a repository with no rule for it) is the run's output, and nothing of it lands: the gate notes
what git does not know before its first command, removes after its last each such file that was
not there before and each folder that leaves empty, names them in its output (`removed_untracked`)
and in one line of the last command's output file, and goes on. What the gate keeps is the tip it
ran on and that tip's tree.

`start` refuses a worktree on no branch: `propose` pushes the task's branch and `clean` deletes
it. With no gate command it writes the task's state `blocked`, and a later `start` takes that task
back once the commands are there. A task in `landing` holds the line for every other; each
refusal on the way names the step out, also when its worktree is gone.

The gate is the main checkout's. One task may bring its own: when the main checkout's settings
name no gate command and the task's branch adds them to its `.lem/project.toml` (they are not on
the base commit), `start` and `gate` take those commands, as for the first task of a new
repository, "set up the checks"; the request is then not green, so that a person reads the
checks once. The rest of the branch's settings, its `gate.ignores`, `gate.bar` and `gate.setup`
too, are not read. A branch that changes a gate the main checkout has is gated by the main
checkout's.

The polish pass comes after the task's own work and before the machine checks, so that the
review reads the code as it will merge. A fresh builder looks for a short fixed list (a comment
the change made false, a leftover, code that reads badly, a document the change made false, and
the defects outside the task that the lead's report and the interview named) and changes no
behavior. `polish` prints what that builder gets: the range of the task's own commits from the
base, the plan, the report, `outside.md` of the interview when the task has one, the backlog
folder, and the files the pass may not change. It keeps the tip the pass starts at; a second
start before `--done` keeps the same one. `polish --done` refuses a worktree with changes
nobody committed, a branch that no longer holds that tip, a pass that leaves a story's test
file or the plan other than it found them, and stories' tests that no longer pass on the branch and fail on
the base commit (`stories.py red`, run when the pass committed anything). Otherwise it logs one
`polish` event (the tip before and after, the count of commits, the items it added to the
backlog folder). `gate` refuses a feature with no pass of this landing whose last commit the
tip holds, and any task whose pass started and is not done. Every task with a plan is a feature:
`stories.py` refuses a plan that says `Kind: correction`, and so does every step here that reads
the stories. The commits
that come after the pass, a repair, a fix of a review's findings, the items `file` writes, are
on top of it, and a rebase by `base` gives the pass's commits their new names; any other rewrite
of the branch asks for the pass again. The pass is one of this landing: `start` of a `ready`
task forgets it with the rest of `landing.json`.

A review comes before anything is proposed. There are three kinds: one read, which is the
review tool's smallest profile, for a small and simple change; a round of the review tool with
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
later task, what is careful, what the gate runs, who merges and where a task lands, and the reason
names each table whose values the change edits, or that only its text changed. The review is the look at the diff itself, by
an agent that did not build it: its record makes the call, and a careful call takes the full set.

The record of a review is a JSON file:

    {"attempt": N,
     "kind": "read" | "round" | "full",
     "ran": [{"name": PROFILE OR LENS, "why": WHY IT FITS THIS CHANGE}],
     "left_out": [{"name": PROFILE OR LENS, "why": WHY IT DOES NOT}],
     "answered": [SOURCE, ...],
     "silent": [{"name": SOURCE, "why": WHAT STOPPED IT}],
     "bar": [{"name": FILE, "why": WHAT THE REVIEW SAYS OF THE REASON GIVEN FOR IT}],
     "must_fix": N, "should": N, "nit": N,
     "outside": [{"where": PATH OR PATH:SYMBOL, "title": ONE LINE, "what": THE RUN THAT SHOWS IT}],
     "careful": true | false, "careful_why": ONE LINE}

`attempt`, `kind`, `answered`, `careful` and `careful_why` are always there. `careful` is the
review's own reading of the diff against each topic, and `careful_why` names the topic the change
reaches, or what was checked to say that it reaches none; `careful: true` comes with `kind: full`. `bar` has one entry for each file in which
the change lowers the bar, and is left out otherwise. `outside` names each defect the review saw
that the base commit already has: it is no finding of the change, and it goes to the backlog.
`what` is the concrete run: what happens, with the input. A count in its place is refused, and
`0` reads as none.

A review in which a source did not answer is still a review: the record names who answered and
who did not. One in which nobody answered is none; it is started once more, and a second such
record sends the request on as not reviewed. A review is of a change, known by the content of
each file it touches, before and after: a rebase onto a base that left those files alone does
not undo it, and a change of one space does. The one addition a review still covers is a new file
in the backlog folder (the settings' `paths.backlog`, a path and not a pattern), when every file
the review saw is as it saw it: that is where the defects outside the change are filed after the
review. An edit or a deletion of an item that was there before is a change like any other, and a
backlog folder that is the root of the repository gives no such exception.
Two rounds at most: after that the request is proposed as it is, green when the second round
left nothing open and not green otherwise. `attempt` in a record is the number `read` printed
for it, so a record that is sent twice is written down once.

No defect outside the change gets lost. `file` writes one item in the settings' backlog folder
for each such defect of a review that has none yet, in the item format of the `lem-backlog` skill
(`worth: later`, its `where`, the day it was filed; its title; its run and where it was seen),
commits the new items on the task's branch, one commit for each round, and keeps the path of
each defect's item in `landing.json`. A second run files nothing new. Those commits ask for no
gate again: `read` and `propose` take the gate's result for a tip whose commits after the gated
one only add items whose paths `landing.json` keeps, and keep the result for that tip, so that
`land` finds what it checks. An item written by hand is a commit like any other. `read` names
the defects that have no item yet (`to_file`), and `propose` refuses while one has none or while an item is
gone from the tip; the owner's "not wanted" is `worth: no` in the item, never its deletion.
The file name is the slug of the title. A file of that name that holds the same defect (the same
`where` and title, and its run word for word as paragraphs of the body, whatever else the body
says, such as the owner's reason for `worth: no`) is its item, and nothing is written twice; a
file that holds another takes the next name, with a suffix from the `where`, then a number. One defect that two rounds
describe in other words gets two items: an extra item costs a merge in the backlog's sorting, and
a lost one costs the defect. The review is asked to repeat an earlier round's words for a defect
it sees again.

`propose` writes the text of the pull request to `pr.md` in the task's directory, from what the
steps kept, from the record of the task's decisions (`decisions.py list`) and from the notes
file, whose headings it checks. The text opens with green or not green, in one wording for a
small change and a feature. Green says that the
checks passed with the bar where it was, a review with at least one source left no
must-fix, no story changed during the build, and no decision was taken by timeout or by the
experts. A story changed, added or removed after the newest approval is one line each, from its
record (`decisions.py story`), with what it was, what it is and why. The text lists every story
change of the task, under every approval; one that a later approval of the owner's took over says
so and is no cause of not green, since that approval made it the owner's. A lowered bar is not
green with a reason either: its line holds the builder's reason and what the review said of it. A choice
taken by timeout is a line of its own, and so is a choice the experts took (their shared pick,
while the owner was away or at the end of the wait), with their pick and both their reasons; so
is an answer of the owner's that came after either and differs. Each reason a request is not
green stands before everything else, one line each; each decision of the record is one line
before the notes. `propose` is refused while a choice of the task waits for the owner. A plan
that calls itself careful (`careful: yes`) or has more than three tasks was talked through by
its defender and the reviewer in the plan talk's companion before any code, and the defender
wrote it down as one `plan.talk` event in the log `project.py` keeps: `propose` refuses such a
request with none, and the text's checks hold one line from the newest, with who argued the plan
with its defender, the turns (with the bound of its rules, when the talk went over it), the
positions settled and left open, and every other count the event holds, in words where Lem
knows the count (`TALK_SAYS`) and by its name where it does not. An event of the older form,
with no counts but those three, reads as before. A talk is a step before the build, so a request
that is careful only by the owner's later word, by its review or by its edit of the settings gets
the full set and no talk; it is not asked for one, and its checks say in words that it had none
and why, which is no cause of not green. A careful request says so in the line after green or not
green, with each reason, and its checks hold the call in one line, with the newest review's call
and reason beside it. A usual request gets
neither line. The checks also hold one line on the personas' read of the stories, from the
newest `stories.read` event (`project.py log` gives its form): how many of the personas asked
answered, in which model families, who did not answer and why, how many stories they flagged,
whether the families split, and when the owner approved them (`stories.py approve`), or that the
build started with no wait for the owner.
When the stories the read names by their digest are not the plan's (which the gate makes the expected
ones), one more line says that they changed after the read, by a later approval of the owner's or by
a change of the build, and that the change was not read; that line is no cause of not green. A scout's report in the task's directory is named there as a file.
A request that came from a bug has one more line with the cause its investigation found, the
cause's place and the report, from the newest `investigation` event; a question's has none.
`propose` refuses a feature with no `stories.read`, unless the owner skipped the read: that word
of the owner's, which Lem asks for only when every story names only the developer, is a decision
of the owner's with the two texts of `READ_SKIP`, and it counts only with a later approval of
the owner's, both before the first state that names a lead. A word or an approval after a lead started is the rare path's,
where the read always runs, and is refused. Then the checks say "the stories: not read by the
personas, on the owner's word (DATE); the owner approved them", which is no cause of not green, since the
decision was the owner's. It also refuses one whose newest read flagged a story or
showed a split between the families with no approval of the owner's at or after it; the rare
path's freeze of a read (`stories.py approve --read`) is no approval of the owner's. A read in which nobody
answered is written down too: `propose` refuses while the newest one is the first such read in a
row, so that the read is started once more, and after the second in a row the request is not
green, with "the stories were not read" first, and its checks say so in place of the read's line. A
change the review calls careful and the plan did not is a lesson about the plan's call: `read
--record` writes one `careful.missed` event with the round and the review's reason, the first time
a review finds it, for the retro. With a GitHub remote `propose` pushes the task's branch
and opens the pull request with the `gh` command; a second run updates it. The `proposed` event
is written after that step: a proposal that the push or the forge refused is none. With any other
remote, or none, the branch is marked ready. So it is with a GitHub remote when the settings'
`branch.propose` is `merge`, for a developer who wants no pull requests: the remote is then one
like any other, no task branch is pushed, and `merged` is refused. GitLab is not built: nobody
checked its command.

`land --by owner` is the owner's word. `land --by agent` is refused unless the settings'
`branch.land` is `agent`, and then still for a careful request, for one that is not green (one
that is not reviewed among them), and for one whose newest review that answered made no careful
call. A
pull request is merged through the forge, so the forge's own rules hold; `merged` is for one the
owner merged by hand. What lands is the tree the checks passed on: when the tip is another tree,
or the base moved by more than the paths the settings' `gate.ignores` name, `land` refuses and
says which steps run again.

A step that was cut off is run again. `land` writes down the commit it is about to put on the base
before it does, so a second run that finds that commit on the base only finishes the bookkeeping.
`clean` knows the branch from `landing.json`, so it finds it after the worktree is gone. It
takes a landed, a dropped or an answered task. The branch of the last two goes when the base
holds it whole, and stays when it has commits of its own, with what it holds and how to delete
it. `landing.json`, `pr.md` and each item of the backlog are written whole, through a new file
that takes the old one's place, so that a run cut off in the middle leaves no half of one.

The landing of a ready branch is a fast-forward and nothing else. With a remote named `origin`
the tip is pushed to the base branch there with a plain push, which the remote refuses when
someone else pushed first;
then the checkout that holds the base branch is fast-forwarded when it is clean, and left alone
with a note when it is not. With no remote, the base branch itself is fast-forwarded. The base
branch is never force-pushed and a ref is never moved behind a checkout's back. The task's own
branch on the forge is the one ref pushed with force, and with a lease: a rebase rewrites it,
and a commit somebody else pushed there stops the push.
"""

from __future__ import annotations

import sys

if sys.version_info < (3, 11):
    # an old python3 must still load this file, so that it can say what it needs and not a traceback
    sys.exit(f"land.py: Lem needs Python 3.11 or newer, and this python3 is {sys.version.split()[0]}; put a newer one first on PATH, or run this file with it")

import argparse
import fnmatch
import hashlib
import json
import re
import shutil
import subprocess
import tomllib
from datetime import date
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
BY = ("owner", "agent")
# The review a change gets, from the least to the most: one read by one agent, a round of the
# project's review tool with the profiles that fit the change, the project's full set.
KINDS = ("read", "round", "full")
KIND_SAYS = {"read": "one read", "round": "a review round with the profiles that fit", "full": "the project's full set"}
# The line Lem writes into a task's brief when the owner says that the task is careful.
OVERRULED = "careful: the owner says so"
# The state line `start` writes when the project has no gate command; a task blocked with it is
# the one `start` takes back once the commands are there.
NO_GATE = "the project has no gate command"
# The steps that take a tip from the start to a proposal, which a refusal of `land` names when the
# tip, the base or the tree is not the one on record.
AGAIN = "run `land.py start`, `land.py base`, `land.py gate` and `land.py propose` again"
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
# Lem's own settings: what must never go wrong, what the gate runs, who merges, where a task lands.
# Any edit of the file is careful by this script, not by a judgment: the file is Lem's, a task
# rarely edits it, and every table of it guards something for every later task (audit A1,
# 2026-11-17: a branch that set `branch.land` to "agent" got one read and a green pull request).
SETTINGS_FILE = ".lem/project.toml"
# What a decision of the build did to its story, as a line of the pull request says it.
STORY_HOW = {"changed": "changed", "added": "was added", "removed": "was removed"}
# The form of the one event that records the personas' read of a task's stories.
READ_FORM = "`by=lem|lead asked:=N answered:=N families:='[...]' silent:='[...]' stories:=N flagged:=N split:=true|false digest=DIGEST`"
# The owner's word that the personas do not read the stories, which Lem asks for only when every
# story names only the developer (`stages/new.md`, "The interview and the stories", step 5): one
# decision of his that `decisions.py log --by owner` writes, known by these two texts word for word.
READ_SKIP = {"what": "the personas' read of the stories", "chose": "no read: the stories name only the developer"}
# How many model families read the stories, in the words of the pull request.
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
TAKEN_BY = {"lead": "the lead", "personas": "the personas", "owner": "the owner", "lem": "Lem", "timeout": "the timeout", "experts": "the experts"}
# The first line of a green pull request, one wording for a small change and a feature.
GREEN = "**Green.** The checks passed with the bar where it was, the review left no must-fix, no story changed, and no decision was taken by timeout or by the experts."
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
# others out, after an audit of the bar (2026-11-17); not measured.
BAR = {
    (".py",): (r"#\s*noqa", r"#\s*type:\s*ignore", r"#\s*pyright:\s*ignore", r"#\s*pylint:\s*disable", r"#\s*nosec", r"\bpytest\.mark\.(skip|xfail)", r"\bunittest\.skip", r"\bpytest\.skip\("),
    (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"): (r"eslint-disable", r"@ts-ignore", r"@ts-expect-error", r"@ts-nocheck", r"\b(it|test|describe)\.(skip|todo|only)\(", r"\bx(it|test|describe)\(", r"\bf(it|describe)\("),
    (".go",): (r"//\s*nolint", r"\bt\.Skip(f|Now)?\("),
    (".rs",): (r"#!?\[allow\(", r"#\[ignore\b"),
    (".java", ".kt"): (r"@Disabled", r"@Ignore", r"@SuppressWarnings"),
    (".sh", ".bash"): (r"#\s*shellcheck\s+disable",),
}
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


def run(args: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    ran = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)
    if check and ran.returncode != 0:
        raise LandError(f"{' '.join(args[:4])} failed: {(ran.stderr or ran.stdout).strip()}")
    return ran


def git(where: Path, *args: str, check: bool = True) -> str:
    return run(["git", "-C", str(where), *args], check=check).stdout.strip()


def write_whole(file: Path, text: str) -> None:
    """Write a file whole or not at all: a run cut off in the middle leaves the old file, never half of one."""
    fresh = file.with_name(file.name + ".new")
    fresh.write_text(text, encoding="utf-8")
    fresh.replace(file)


def script(name: str, repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    """One command of a sibling script, so this one reads a repository the way every stage does."""
    ran = subprocess.run(
        [sys.executable, "-B", str(SCRIPTS / name), "--repo", str(repo), *args], capture_output=True, text=True, check=False,
    )
    if check and ran.returncode != 0:
        raise LandError(ran.stderr.strip().removeprefix(f"{name}: ") or f"{name} {args[0]} failed")
    return ran


class Task:
    """One task as the landing needs it: its settings, its worktree, its branch and what it kept."""

    def __init__(self, repo: Path, slug: str) -> None:
        self.settings = json.loads(script("project.py", repo, "show").stdout)
        if Path(self.settings["root"]).resolve() != Path(self.settings["main"]).resolve():
            # Run from a task's worktree, the landing still reads the main checkout's settings:
            # the branch it lands does not get to choose its gate or what is careful.
            self.settings = json.loads(script("project.py", Path(self.settings["main"]), "show").stdout)
        if self.settings["settings"] is None:
            raise LandError("this repository has no .lem/project.toml; `/lem init` writes it")
        self.slug = slug
        self.base = self.settings["branch"]["base"]
        # Refused here, before anything else: a protected branch, a missing base, a wrong target.
        script("project.py", repo, "may-land", str(self.base))
        tasks = json.loads(script("project.py", repo, "tasks").stdout)
        self.record = next((task for task in tasks if task["slug"] == slug), None)
        if self.record is None:
            raise LandError(f"no task {slug!r}; the tasks are: {', '.join(task['slug'] for task in tasks) or 'none yet'}")
        self.others_landing = [task["slug"] for task in tasks if task["status"] == "landing" and task["slug"] != slug]
        self.directory = Path(script("project.py", repo, "state-dir").stdout.strip()) / "tasks" / slug
        # -z: a NUL ends each field and an empty field ends each worktree, so a path with a line break stays whole
        listed = run(["git", "-C", str(repo), "worktree", "list", "--porcelain", "-z"]).stdout
        entries = [block.split("\0") for block in listed.split("\0\0") if block.strip("\0")]
        self.main = Path(self.settings["main"])
        relative = Path(self.settings["paths"]["worktrees"]["path"]).relative_to(Path(self.settings["root"]).resolve())
        self.worktree = self.main / relative / slug
        # the checkout that holds the base branch, when one does
        self.base_checkout = next(
            (Path(entry[0].removeprefix("worktree ")) for entry in entries if f"branch refs/heads/{self.base}" in entry), None,
        )
        self.remote = git(self.main, "remote", "get-url", "origin", check=False) != ""
        self.onto = f"origin/{self.base}" if self.remote else str(self.base)
        self.kept_file = self.directory / "landing.json"
        self.recorded: list[dict] | None = None
        self.stories: dict | None = None
        self.plan_said: bool | None = None
        self.branch_gate: list[str] | None = None
        # The address as the repository has it, before any rewrite of it: the forge is known by its host.
        # A project that wants no pull requests (`branch.propose = "merge"`) has no forge here: its
        # remote is one like any other, and its task lands on the remote's base branch.
        url = git(self.main, "config", "--get", "remote.origin.url", check=False)
        github = re.match(r"(https://|ssh://git@|git@)github\.com[:/]", url)
        self.merges = self.settings["branch"]["propose"] == "merge"
        self.forge = "github" if github and not self.merges else None

    def need_worktree(self) -> None:
        if not (self.worktree / ".git").exists():
            branch = self.kept().get("branch") or "BRANCH"
            raise LandError(
                f"the task has no worktree at {self.worktree}: `git -C {self.main} worktree prune` forgets a worktree whose folder was removed by hand, "
                f"and `git -C {self.main} worktree add {self.worktree} {branch}` puts the task's branch back in it, then this step runs again; "
                f"when the work is gone with it, `project.py state {self.slug} dropped \"WHY\"` ends the task",
            )
        dirty = git(self.worktree, "status", "--porcelain")
        if dirty:
            raise LandError(f"the worktree has changes nobody committed:\n{dirty}\ncommit them or remove them before this step")

    def blocked_by_start(self) -> bool:
        """Whether the task is `blocked` by `start` itself, for want of a gate command."""
        block = self.record.get("state") or ""
        return self.record["status"] == "blocked" and block.splitlines()[0].endswith(f" blocked: {NO_GATE}")

    def need_landing(self) -> None:
        if self.record["status"] != "landing":
            if self.record["status"] in ("ready", "open") or self.blocked_by_start():
                raise LandError(f"the task is {self.record['status']!r}, not `landing`; `land.py start {self.slug}` comes first")
            raise LandError(f"the task is {self.record['status']!r}, not `landing`: `land.py start` takes a `ready` or an `open` task into it, and this one is neither")

    def kept(self) -> dict:
        if not self.kept_file.is_file():
            return {}
        try:
            return json.loads(self.kept_file.read_text(encoding="utf-8"))
        except ValueError as error:
            raise LandError(
                f"{self.kept_file} does not read as JSON ({error}); land.py writes it whole, so something else wrote it. "
                f"Move it aside, then `project.py state {self.slug} ready \"WHY\"` and `land.py start {self.slug}` start the landing over: "
                "its checks and its review run again, and `propose` finds a pull request the task has on the forge",
            ) from error

    def keep(self, **values: object) -> None:
        write_whole(self.kept_file, json.dumps({**self.kept(), **values}, indent=2) + "\n")

    def state(self, status: str, *lines: str) -> None:
        script("project.py", self.worktree if self.worktree.exists() else self.main, "state", self.slug, status, *lines)

    def decisions(self) -> list[dict]:
        """Each decision of the task as it stands, through the one script that writes them."""
        if self.recorded is None:
            self.recorded = json.loads(script("decisions.py", self.main, "list", self.slug).stdout)
        return self.recorded

    def gate(self) -> tuple[list[str], bool]:
        """The gate commands of this task, and whether its own branch brought them: the main
        checkout's, unless those are none and the branch adds some to its `.lem/project.toml`."""
        own = self.settings["gate"]["commands"]
        if own or not (self.worktree / ".git").exists():
            return own, False
        if self.branch_gate is None:
            # asked twice by one proposal (the text and its reasons), and kept: no step writes the branch's settings
            self.branch_gate = json.loads(script("project.py", self.worktree, "show").stdout)["gate"]["commands"]
        tip = self.branch_gate
        if not tip:
            return [], False
        base = git(self.worktree, "merge-base", "HEAD", self.onto, check=False)
        before = git(self.worktree, "show", f"{base}:.lem/project.toml", check=False) if base else ""
        try:
            on_base = tomllib.loads(before).get("gate", {}).get("commands", []) if before else []
        except tomllib.TOMLDecodeError:
            on_base = []
        return (tip, True) if not on_base else ([], False)

    def fetch(self) -> None:
        if self.remote:
            git(self.main, "fetch", "origin", str(self.base))


def cmd_start(task: Task) -> dict:
    if task.others_landing:
        other = task.others_landing[0]
        raise LandError(
            f"{other} is in `landing`: one branch lands at a time, so finish that one first. When it cannot go on (its worktree or its work is gone), "
            f"`project.py state {other} ready \"WHY\"` gives the line back and its landing starts over, or `project.py state {other} dropped \"WHY\"` ends it",
        )
    # a task `start` blocked for want of a gate command is taken back as a `ready` one
    again = task.blocked_by_start()
    if task.record["status"] not in ("ready", "landing", "open") and not again:
        raise LandError(f"the task is {task.record['status']!r}; only a `ready` task, or an `open` one whose base moved, takes the landing line")
    if not task.gate()[0]:
        if not again:
            task.state("blocked", NO_GATE)
        raise LandError(
            f"{NO_GATE}, so nothing would show that the change works; the task is `blocked`. "
            "Add the commands to gate.commands in .lem/project.toml, or, for the task that sets up the checks, in its own branch's, "
            f"then run `land.py start {task.slug}` again",
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
        # A task that was built further starts over, with new checks and new reads. Its pull request stays its own.
        pr = task.kept().get("pr")
        task.kept_file.unlink(missing_ok=True)
        if pr:
            task.keep(pr=pr)
    if task.record["status"] != "landing":
        # kept here because `clean` needs the branch after the worktree, which names it, is gone
        task.keep(branch=git(task.worktree, "branch", "--show-current"))
        task.state("landing", "the checks start" if task.record["status"] == "ready" or again else "the base moved: the checks run again")
    return {"task": task.slug, "base": task.base, "worktree": str(task.worktree), "remote": task.remote, "forge": task.forge}


def cmd_base(task: Task) -> dict:
    task.need_landing()
    task.need_worktree()
    task.fetch()
    onto = git(task.worktree, "rev-parse", task.onto)
    before = git(task.worktree, "rev-parse", "HEAD")
    rebased = run(["git", "-C", str(task.worktree), "rebase", task.onto], check=False)
    if rebased.returncode != 0:
        conflicts = git(task.worktree, "diff", "--name-only", "--diff-filter=U", check=False).splitlines()
        git(task.worktree, "rebase", "--abort", check=False)
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
            f"or there is none, `project.py state {task.slug} dropped \"WHY\"` ends the task",
        )
    if tip != before and task.kept().get("polish"):
        # The rebase rewrote the commits the polish pass names; each takes its new name, so that
        # the gate still finds the pass on the tip it checks.
        task.keep(polish=through_rebase(task, task.kept()["polish"], before, tip, onto))
    # a new base or a new tip means the gate's last result is about another tree
    task.keep(base=onto, gated=None, tree=None)
    return {"task": task.slug, "onto": task.onto, "base": onto, "tip": tip, "moved": tip != before, "ahead": ahead}


def holds_commit(task: Task, commit: str | None, tip: str) -> bool:
    """Whether the branch at `tip` holds `commit`."""
    return bool(commit) and run(["git", "-C", str(task.worktree), "merge-base", "--is-ancestor", str(commit), tip], check=False).returncode == 0


def through_rebase(task: Task, polish: dict, before: str, tip: str, onto: str) -> dict:
    """The polish pass's record after a rebase by `base`: each commit it names, by its place from
    the tip. A rebase keeps the branch's commits one for one, unless one became empty and was
    dropped; then no place is sure, the names are dropped, and the gate asks for the pass again."""
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
    """The files that hold a story's test, as the plan names them."""
    return sorted({file for story in found["stories"] for test in story["tests"] for file in test["files"]})


def cmd_polish(task: Task, done: bool) -> dict:
    """The polish pass: what its builder gets, and after the builder, the check of what it did."""
    task.need_landing()
    task.need_worktree()
    found = stories_of(task)
    if found["small"]:
        raise LandError(
            f"a small change has no polish pass: its builder filed in the backlog what it saw outside the change, in a commit of its own, "
            f"and the review reads every line of it. `land.py gate {task.slug}` is the next step",
        )
    kept = task.kept()
    if "base" not in kept:
        raise LandError(f"`land.py base {task.slug}` comes first: the polish pass works on the branch as it will be checked")
    tip = git(task.worktree, "rev-parse", "HEAD")
    # what the pass may not change: the stories' test files and the plan that names them; a small
    # change's story file is in the task directory, which no commit holds
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
            "task": task.slug, "kind": found["kind"], "done": polish["done"], "before": polish["before"],
            # the task's own commits, which the pass reads; what it commits comes after `before`
            "range": f"{base}..{polish['before']}",
            "commits": git(task.worktree, "log", "--format=%h %s", f"{base}..{polish['before']}").splitlines(),
            "plan": found["plan"], "report": str(report) if report.is_file() else None, "outside": str(outside) if outside.is_file() else None,
            "backlog": backlog_of(task),
            "frozen": frozen,
        }
    if not polish:
        raise LandError(f"no polish pass started for this landing; `land.py polish {task.slug}` starts it and prints what its builder gets")
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
    # What counts is what the pass leaves: a commit that changed a story's test and one that put it back leave the contract as it was.
    differs = set(changed(task, before, tip))
    wrong = [f"{file} (by {', '.join(touched.get(file, []))})" for file in frozen if file in differs]
    if wrong:
        raise LandError(
            f"the polish pass changed what it may not: {'; '.join(wrong)}. A story's test and the plan are the task's contract, and the pass changes no behavior: "
            f"a builder reverts those commits (`git revert`), and this step runs again",
        )
    result: dict = {"task": task.slug, "before": before, "after": tip, "commits": [line.split(" ", 1)[1] if " " in line else "" for line in commits]}
    if commits:
        held = script("stories.py", task.main, "red", task.slug, check=False)
        if held.returncode != 0:
            raise LandError(
                f"after the polish pass the stories' tests do not hold: {held.stderr.strip().removeprefix('stories.py: ')}. "
                "The pass changes no behavior: a builder finds the commit of the pass that broke it and takes it out, and this step runs again",
            )
        result["stories"] = json.loads(held.stdout)
    else:
        result["stories"] = None
    folder = backlog_of(task)
    added = [row.split("\t", 1)[1] for row in git(task.worktree, "diff", "--name-status", "--no-renames", before, tip).splitlines() if row.startswith("A\t")]
    result["filed"] = [path for path in added if path.startswith(folder + "/")]
    script("project.py", task.worktree, "log", task.slug, "polish", f"before={before[:9]}", f"after={tip[:9]}", f"commits:={len(commits)}", f"filed:={json.dumps(result['filed'])}")
    task.keep(polish={"before": before, "after": tip, "done": True, "commits": len(commits), "filed": result["filed"]})
    return result


def polish_missing(task: Task, tip: str, found: dict) -> str | None:
    """Why the gate may not run on this tip for want of the polish pass; none when it may. A feature,
    which is every task with a plan, needs a pass of this landing whose last commit the tip holds,
    and a pass that started and is not done stops it: a builder may still be at work. A small
    change never has one."""
    if found["small"]:
        return None
    polish = task.kept().get("polish")
    if polish and not polish.get("done"):
        return f"the polish pass started at {str(polish.get('before'))[:9]} and is not done: after its builder, `land.py polish {task.slug} --done` checks what it did"
    if not polish:
        return f"{task.slug} is a feature, and no polish pass is on record for this landing: `land.py polish {task.slug}` starts it, a builder does it, and `--done` checks it"
    if not holds_commit(task, polish.get("after"), tip):
        return (
            f"the tip does not hold the polish pass's last commit ({str(polish.get('after'))[:9]}): the branch was rewritten after the pass by something else than `land.py base`. "
            f"The pass runs again: `land.py polish {task.slug}`, its builder, and `--done`"
        )
    return None


def stories_of(task: Task) -> dict:
    """The task's stories and its plan, through the one script that reads them. A step asks for
    them many times, and no step writes the plan, the approval or a story's record, so the first
    answer is kept for the life of this process."""
    if task.stories is None:
        task.stories = json.loads(script("stories.py", task.main, "show", task.slug).stdout)
    return task.stories


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
    """The backlog folder, relative to the root of the repository: a path, never a pattern, and never the root,
    which the settings refuse."""
    return Path(task.settings["paths"]["backlog"]["path"]).relative_to(Path(task.settings["root"]).resolve()).as_posix()


def covers(task: Task, read: dict, now: dict) -> bool:
    """Whether a review that was recorded still covers the change as it is now. It does when the
    change is the same, or when the change is the reviewed one plus new files of the backlog
    folder and nothing else: `file` writes the defects a review saw outside the change there after
    the review, and that asks for no other review. Any other file does, an item that was on the
    base too. A record that kept no contents covers only the same change."""
    if read["patch"] == now["patch"]:
        return True
    was = read.get("contents")
    folder = backlog_of(task)
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


def holds(file: Path, defect: dict) -> bool:
    """Whether an item file is this defect: the same `where`, the same title, and the defect's run
    as paragraphs of the body, word for word. Any other text of the body, the owner's reason for a
    `worth: no` or a later note, leaves it the same defect."""
    try:
        text = file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    front: dict[str, str] = {}
    head = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if head:
        for line in head.group(1).splitlines():
            key, _, value = line.partition(":")
            front[key.strip()] = value.strip()
        text = text[head.end():]
    lines = text.strip().splitlines()
    if not lines or not lines[0].startswith("# "):
        return False
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
    if task.plan_said is None and stories_of(task)["small"]:
        # a small change has no plan: its story file is in the task directory, with no history in git
        task.plan_said = plan_call(Path(stories_of(task)["plan"]).read_text(encoding="utf-8"))
    if task.plan_said is None:
        plan = Path(stories_of(task)["plan"])
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
    whose tables, once landed, say for every later task what is careful, what the gate runs, who
    merges and where a task lands. The reason names each table whose values change, or says that
    only the file's text does. None when the change leaves the file alone."""
    if SETTINGS_FILE not in now["files"]:
        return None

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
    return f"the change edits {what}, Lem's own settings, which say for every later task what is careful, what the gate runs, who merges and where a task lands"


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
    Lem's own settings is the one rule this script matches by itself."""
    why = []
    if owner_says_careful(task):
        why.append("the owner says so")
    if plan_careful(task):
        why.append("the plan says so")
    edited = settings_edit(task, now)
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
    extra = [re.compile(pattern) for pattern in task.settings["gate"]["bar"]]
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
    file = old = ""
    marks: list[re.Pattern] = []
    # -M: a file that moved is one file, so its tests are not counted as gone and come again
    for line in git(task.worktree, "diff", "-U0", "-M", base, tip).splitlines():
        if line.startswith("--- "):
            old = line[6:] if line.startswith("--- a/") else ""
        elif line.startswith("+++ "):
            # a file that is gone has its lines counted under the name it had
            file = line[6:] if line.startswith("+++ b/") else old
            if Path(file).suffix.lower() in DOCS:
                # a document may quote a mark, the plan's own reason for one too
                file = ""
            marks = [*extra, *(re.compile(mark) for suffixes, found in BAR.items() if Path(file).suffix.lower() in suffixes for mark in found)] if file else []
        elif not file or line[:1] not in "+-":
            continue
        else:
            hit = next((found for mark in marks if (found := mark.search(line[1:]))), None)
            key = (file, hit.re.pattern, " ".join(line[1:][hit.start():].split())) if hit else None
            if hit and line.startswith("+"):
                came.setdefault(key, []).append({"file": file, "what": hit.group(0), "line": line[1:].strip()[:160]})
            elif hit:
                went[key] = went.get(key, 0) + 1
            if (TEST_FILE.search(file) or Path(file).suffix.lower() in INLINE_TESTS) and ASSERTS.search(line[1:]):
                asserts[file] = asserts.get(file, 0) + (1 if line.startswith("-") else -1)
    for key, entries in came.items():
        lowered += entries[went.get(key, 0):]
    for name, fewer in sorted(asserts.items()):
        if fewer > 0:
            lowered.append({"file": name, "what": f"{fewer} assertion(s) fewer", "line": ""})
    for row in git(task.worktree, "diff", "--name-status", "-M", base, tip).splitlines():
        status, name, *moved = row.split("\t")
        # a test file that moved out of the tests is one the tests no longer run, as a deleted one
        gone = status == "D" or (status.startswith("R") and moved and not TEST_FILE.search(moved[0]))
        if gone and TEST_FILE.search(name):
            lowered = [entry for entry in lowered if entry["file"] != name]
            lowered.append({"file": name, "what": "a test file is deleted" if status == "D" else f"a test file is moved out of the tests, to {moved[0]}", "line": ""})
    for entry in lowered:
        entry["reason"] = reasons.get(entry["file"])
    covered = {suffix for suffixes in BAR for suffix in suffixes}
    not_covered = sorted({Path(name).suffix.lower() for name in changed(task, base, tip)} - covered - set(DOCS) - set(DATA))
    return {"lowered": lowered, "not_covered": not_covered, "own_patterns": len(extra)}


def cmd_gate(task: Task) -> dict:
    task.need_landing()
    task.need_worktree()
    if "base" not in task.kept():
        raise LandError(f"`land.py base {task.slug}` comes first: the gate runs on the tip that will land")
    tip = git(task.worktree, "rev-parse", "HEAD")
    # Before any command runs: the review reads the code as it will merge, so the polish pass comes first.
    try:
        found = stories_of(task)
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
            f"the gate has no command to run, and a gate that ran nothing shows nothing: {NO_GATE} in the main checkout's .lem/project.toml, "
            f"and the branch brings none that the base commit lacks. Add the commands to gate.commands there, then run `land.py gate {task.slug}` again",
        )
    logs = task.directory / "gate"
    logs.mkdir(exist_ok=True)
    # What git does not know before the first command. `need_worktree` refused any such file, so
    # this is empty unless something wrote one since; it is taken all the same, so that the
    # removal after the run can never reach a file that was there before it.
    there = untracked(task)
    # the start of the checks: the board draws them from here to their last result
    script("project.py", task.worktree, "log", task.slug, "gate.start", f"tip={tip[:9]}", f"commands:={len(commands)}")
    results = []
    for number, command in enumerate(commands, start=1):
        output = logs / f"{number:02d}.log"
        with output.open("w", encoding="utf-8") as handle:
            code = subprocess.run(command, shell=True, cwd=task.worktree, stdout=handle, stderr=subprocess.STDOUT, check=False).returncode
        lines = [line for line in output.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]
        last = lines[-1].strip() if lines else ""
        results.append({"command": command, "exit": code, "last": last, "output": str(output)})
        script("project.py", task.worktree, "log", task.slug, "gate", f"command={command}", f"exit:={code}", f"last={last}", f"tip={tip[:9]}")
    green = all(result["exit"] == 0 for result in results)
    # A file the commands wrote that git neither tracks nor ignores (Python's bytecode in a
    # repository with no rule for it) is the run's output, and nothing of it lands: it goes, with
    # the folders it leaves empty, red or green, so that the next step finds the worktree clean.
    # The worktree is the task's own, made by Lem.
    removed = sorted(set(untracked(task)) - set(there))
    for path in removed:
        remove_left(task, path)
    if removed:
        with output.open("a", encoding="utf-8") as handle:
            handle.write(f"land.py removed what the gate's commands left untracked: {', '.join(removed)}\n")
    # A gate command that changed a tracked file, or made a commit, changed the tree it just judged.
    dirty = git(task.worktree, "status", "--porcelain")
    if green and dirty:
        task.keep(gated=None, tree=None)
        raise LandError(
            f"a gate command changed what git tracks, so its result is about another tree:\n{dirty}\n"
            f"put the files back (`git -C {task.worktree} checkout -- FILE`) and make the gate command change no tracked file, then run this again",
        )
    moved = git(task.worktree, "rev-parse", "HEAD")
    if green and moved != tip:
        task.keep(gated=None, tree=None)
        raise LandError(
            f"a gate command made a commit on the branch ({tip[:9]}..{moved[:9]}), so its result is about another tree: "
            f"make the gate command commit nothing, put the branch back with `git -C {task.worktree} reset --hard {tip}`, then run this again",
        )
    result = {"task": task.slug, "tip": tip, "green": green, "commands": results, "removed_untracked": removed, "polish": task.kept().get("polish")}
    if not green:
        task.keep(gated=None, tree=None)
        print(json.dumps(result, indent=2))
        red = [r["command"] for r in results if r["exit"] != 0]
        raise LandError(f"the gate is red on {len(red)} command(s): {'; '.join(red)}. A builder reads the output files; the gate is never edited to pass")
    # The gate's commands are green. Now what no command of the project checks: that each story is
    # held by a test that fails without the change, and that the change did not lower the bar.
    task.keep(gated=None, tree=None)
    held = script("stories.py", task.main, "red", task.slug, check=False)
    try:
        result["stories"] = json.loads(held.stdout)
    except ValueError:
        result["stories"] = None
    if held.returncode != 0:
        print(json.dumps(result, indent=2))
        raise LandError(f"{held.stderr.strip().removeprefix('stories.py: ')}. A builder repairs the test or the plan; the check is never edited to pass")
    # A small change gives no reason for a lowered bar: it has no plan, and a lowered bar is never a small change.
    plan = "" if found["small"] else Path(found["plan"]).read_text(encoding="utf-8")
    now = change(task)
    result["bar"] = bar(task, now["base"], tip, plan)
    result["size"] = {"files": len(now["files"]), "lines": now["lines"], "in_parts": now["lines"] > READ_AT}
    unexplained = [entry for entry in result["bar"]["lowered"] if not entry["reason"]]
    if unexplained:
        print(json.dumps(result, indent=2))
        named = "; ".join(f"{entry['file']} ({entry['what']})" for entry in unexplained[:5])
        if found["small"]:
            raise LandError(
                f"a small change does not lower the bar: {named}. Take the mark out; when the change needs it, it is a feature, "
                f"and Lem tells the developer so and takes the feature path, whose plan gives the reason under `## The bar`",
            )
        raise LandError(
            f"the change lowers the bar with no reason given: {named}. Take the mark out, or give the reason in the task's plan "
            "under `## The bar` as `- PATH: REASON`, where the one who reads the change sees it",
        )
    task.keep(gated=tip, tree=git(task.worktree, "rev-parse", f"{tip}^{{tree}}"), checks={"commands": results, "stories": result["stories"], "bar": result["bar"], "size": result["size"]})
    return result


def untracked(task: Task) -> list[str]:
    """Each file of the worktree that git neither tracks nor ignores, one by one, a file in a new folder too."""
    listed = run(["git", "-C", str(task.worktree), "status", "--porcelain", "--untracked-files=all", "-z"]).stdout.split("\0")
    return [entry[3:] for entry in listed if entry.startswith("?? ")]


def remove_left(task: Task, path: str) -> None:
    """Remove one file a gate command left untracked, and each folder above it that it leaves
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


def ignored(task: Task, files: list[str]) -> bool:
    patterns = task.settings["gate"]["ignores"]
    return all(any(fnmatch.fnmatchcase(file, pattern) for pattern in patterns) for file in files)


def changed(task: Task, old: str, new: str) -> list[str]:
    """Every path that differs between two trees. A rename counts as the path that went and the path that came."""
    return git(task.worktree, "diff", "--name-only", "--no-renames", old, new).splitlines()


def due(task: Task) -> dict:
    """Whether a review is due now, and the least it may be. Within that, the one who starts the review chooses."""
    now = change(task)
    found = stories_of(task)
    reads = task.kept().get("reads", [])
    answered = [read for read in reads if read["answered"]]
    why_careful = careful(task, now)
    # a small change has no plan, and is the one task of its builder
    tasks = 1 if found["small"] else tasks_of(Path(found["plan"]).read_text(encoding="utf-8"))
    facts = {"round": len(answered) + 1, "careful": why_careful, "tasks": tasks, "small": found["small"], "lines": now["lines"], "in_parts": now["lines"] > READ_AT, **now}
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
        if not covers(task, last, now):
            unmet.append("nobody reviewed what changed after it")
        if KINDS.index(last["kind"]) < KINDS.index(floor):
            unmet.append(f"it was {KIND_SAYS[last['kind']]}, and this change gets {KIND_SAYS[floor]} at the least ({why})")
    if last and not unmet:
        return {"due": "none", "why": f"round {last['round']} reviewed this change and left no must-fix", **facts}
    if len(answered) >= 2:
        return {"due": "owner", "why": f"two rounds reviewed it: {', and '.join(unmet)}", **facts}
    silent = len(reads) - max((index for index, read in enumerate(reads) if read["answered"]), default=-1) - 1
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
    lines = log.read_text(encoding="utf-8").splitlines() if log.is_file() else []
    for number, line in enumerate(lines, start=1):
        if f'"task": {json.dumps(task.slug)}' not in line:
            continue
        try:
            record = json.loads(line)
        except ValueError as error:
            raise LandError(f"line {number} of {log} is not JSON ({error}); the log is written by `project.py log`, never by hand") from error
        if record.get("task") == task.slug:
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
        *(["by its change to the settings"] if settings_edit(task, state) else []),
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
    event's order. An event of the older form has none."""
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


def polished(polish: dict | None) -> str:
    """The polish pass as one line of the pull request's checks, from what `polish --done` logged."""
    if polish and polish.get("done"):
        commits, filed = polish["commits"], len(polish["filed"])
        return f"- the polish pass: {commits} commit{'' if commits == 1 else 's'}, {filed} item{'' if filed == 1 else 's'} filed in the backlog"
    # the gate refuses a feature with no pass, so only a record from before the pass existed is here
    return "- the polish pass: none on record"


def story_read_of(task: Task) -> dict | None:
    """The newest record of the personas' read of the task's stories in the event log."""
    return next((record for record in reversed(events_of(task)) if record.get("event") == "stories.read"), None)


def unanswered(task: Task) -> int:
    """How many reads of the stories in a row, the newest last, nobody answered."""
    count = 0
    for record in reversed(events_of(task)):
        if record.get("event") != "stories.read":
            continue
        if record.get("answered") != 0:
            break
        count += 1
    return count


def read_form(read: dict) -> bool:
    """Whether a `stories.read` event has the form `project.py log` gives it; one that nobody
    answered names no family."""
    counts = ("asked", "answered", "stories", "flagged")
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
    return f"`decisions.py log {slug} --by owner --what \"{READ_SKIP['what']}\" --chose \"{READ_SKIP['chose']}\" --why \"THE OWNER'S ANSWER\"`"


def read_skipped(task: Task) -> tuple[dict | None, str | None]:
    """The owner's newest word to skip the personas' read, when an approval of his follows it and both
    came before any lead of the task started; or why the word on record does not count. A lead writes
    the stories on the rare path, where the read is the only approval and always runs, so a word or an
    approval after the first state that names a lead is the rare path's. Neither, with no word of his."""
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
    approval = next((index for index in range(word + 1, len(events)) if events[index].get("event") == "stories.approved" and events[index].get("by") == "owner"), None)
    rare = (
        "the lead wrote the stories, and on the rare path the read always runs, as the only approval there "
        f"(`stages/plan.md`, step 1): the lead runs it and writes `project.py log {task.slug} stories.read` with the form {READ_FORM}"
    )
    if lead is not None and lead < word:
        return None, f"a lead of {task.slug} started before the owner's word to skip the personas' read: {rare}"
    if lead is not None and (approval is None or lead < approval):
        return None, f"a lead of {task.slug} started before the owner's approval that came after the word to skip the personas' read: {rare}"
    if approval is None:
        return None, (
            f"the owner's word to skip the personas' read of {task.slug}'s stories is on record, and no approval of the owner's came after it: "
            f"the owner's yes to the stories is kept with `stories.py approve {task.slug} --file FILE` (`stages/new.md`, \"The interview and the stories\", step 7)"
        )
    return {"word": events[word], "approval": events[approval]}, None


def approved_after(found: dict, read: dict) -> bool:
    """Whether the owner himself approved the stories at the read's time or after it. A freeze of
    the rare path's read (`by: read`) and Lem's approval of a correction are not his yes."""
    return any(approval["by"] == "owner" and approval["at"] >= read["ts"] for approval in found.get("approvals", []))


def read_line(read: dict | None, found: dict, quiet_reads: int = 0, skipped: dict | None = None) -> str:
    """The personas' read of the stories and his approval, as one line of the pull request's checks;
    `skipped` is his word to skip the read with his approval after it, as `read_skipped` gives them."""
    approval = found.get("approved")
    # a plan is a feature's: its stories are the owner's approval, or the rare path's freeze by a read, which is not his
    approved = f"the owner approved them on {approval['at'][:10]}" if approval and approval["by"] == "owner" else ""
    if read and not read["answered"]:
        # propose refuses the first such read, so this is the second in a row at the least
        return (
            f"- the stories were not read by the personas: {quiet_reads} reads in a row, and none of the {read['asked']} personas asked answered"
            + (f"; {approved}" if approved else "; the build started with no wait for the owner")
        )
    if read:
        count = len(read["families"])
        line = (
            f"- the stories were read by {read['answered']} of {read['asked']} personas asked, {FAMILIES.get(count, f'{count} model families')} ({', '.join(read['families'])}); "
            + ("nobody confused" if not read["flagged"] else f"{read['flagged']} of {read['stories']} stor{'y' if read['stories'] == 1 else 'ies'} flagged")
            + ("; the two families split" if read["split"] else "")
            + "".join(f"; no answer from {source['name']} ({source['why']})" for source in read["silent"])
        )
        if approved:
            return f"{line}; {approved}"
        return line + "; the build started with no wait for the owner"
    if skipped:
        return f"- the stories: not read by the personas, on the owner's word ({skipped['word']['at'][:10]}); the owner approved them"
    return "- the stories: no read by the personas is on record" + (f"; {approved}" if approved else "")


def unread(read: dict | None, found: dict) -> str | None:
    """The line that says the stories are not the ones the personas read, and what changed them.
    The plan's stories are the expected ones (the gate refuses any other), so they are compared."""
    if read is None or not read["answered"] or found["stories_digest"] == read["digest"]:
        return None
    # an approval of his after the read changed the stories only when it holds other stories than the read did
    his = [approval for approval in found.get("approvals", []) if approval["by"] == "owner" and approval["at"] >= read["ts"] and approval["digest"] != read["digest"]]
    what = [*([f"by the owner's approval {his[-1]['number']}"] if his else []), *(["by a change of the build"] if any(change["at"] >= read["ts"] for change in found.get("history", [])) else [])]
    return f"- the stories changed after the personas' read{', ' + ' and '.join(what) if what else ''}, and the change was not read"


def named(value: object, where: str) -> list[dict]:
    """A list of names, each with its why: the profiles of a round, or the sources that did not answer."""
    if not isinstance(value, list) or not all(
        isinstance(item, dict) and set(item) == {"name", "why"} and all(isinstance(text, str) and text.strip() for text in item.values()) for item in value
    ):
        raise LandError(f"`{where}` is a list of {{\"name\": ..., \"why\": ...}}, each with both as text")
    return value


def gate_holds(task: Task, tip: str) -> bool:
    """Whether the gate's result holds for `tip`: the tip is the commit it passed on, or that commit
    with commits after it that only add the backlog items `file` wrote for this landing's reviews.
    Those hold no code and no test, so they ask for no gate again; the result is then kept for the
    tip, so that `land` finds what it checks. Any other commit, an item written by hand among them,
    asks for the gate."""
    kept = task.kept()
    gated = kept.get("gated")
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


def cmd_file(task: Task, again: bool) -> dict:
    """File each defect a review saw outside the change as an item of the backlog, and commit the items."""
    task.need_landing()
    task.need_worktree()
    reads = task.kept().get("reads", [])
    tip = git(task.worktree, "rev-parse", "HEAD")
    folder = backlog_of(task)
    today = date.today().isoformat()
    filed, same, gone, written = [], [], [], {}
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
    # One commit for each round, of its new items and nothing else: the worktree was clean.
    for number, paths in written.items():
        git(task.worktree, "add", "--", *paths)
        git(task.worktree, "commit", "-q", "-m", f"docs(backlog): what review round {number} saw outside {task.slug}", "--", *paths)
    tip = git(task.worktree, "rev-parse", "HEAD")
    if filed or same:
        items = [{**entry, "new": True} for entry in filed] + [{**entry, "new": False} for entry in same]
        script("project.py", task.worktree, "log", task.slug, "review.filed", f"items:={json.dumps(items)}", f"tip={tip[:9]}")
    # A run cut off after its commit finds each item again by its defect, so this write comes last.
    task.keep(reads=reads)
    return {"task": task.slug, "filed": filed, "same": same, "gone": gone, "tip": tip}


def cmd_read(task: Task, record: str | None) -> dict:
    task.need_landing()
    task.need_worktree()
    state = due(task)
    if not gate_holds(task, state["tip"]):
        raise LandError(f"the review is of the tip the checks passed on, and no check is on record for this tip; `land.py gate {task.slug}` comes first")
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
            # the number the record of this review carries, so that the same record is never written down twice
            "attempt": state["attempt"],
            # the defects outside the change that reviews saw and that have no item yet: `land.py file` files them
            "to_file": to_file(reads),
            "careful": state["careful"], "tasks": state["tasks"], "small": state["small"], "lines": state["lines"], "in_parts": state["in_parts"],
            "reads": [{key: value for key, value in read.items() if key != "contents"} for read in reads],
            # what a reviewer gets, and nothing of the builder's reasoning
            "inputs": {
                # the owner's words as given, and the request as Lem wrote it down, where the task has them
                **{name: str(task.directory / file) for name, file in (("words", "ask.txt"), ("request", "task.md")) if (task.directory / file).is_file()},
                "plan": stories_of(task)["plan"], "range": f"{state['base']}..{state['tip']}",
                "worktree": str(task.worktree), "rules": [rule["file"] for rule in rules], "bar": task.kept().get("checks", {}).get("bar"),
                # what must never go wrong, from the main checkout's settings: the review reads the diff against each
                "topics": task.settings["flow"]["topics"],
                # where the project's review tool keeps each profile and lens, with what each is for
                "review": task.settings["paths"]["review"]["path"],
            },
        }
    if state["due"] != "review":
        raise LandError(f"no review is due: {state['why']}")
    try:
        said = json.loads(Path(record).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise LandError(f"{record} does not read as JSON ({error}); --record names the file that says what the review was and what it found") from error
    known = {"attempt", "kind", "ran", "left_out", "answered", "silent", "bar", "must_fix", "should", "nit", "outside", "careful", "careful_why"}
    if not isinstance(said, dict) or set(said) - known or not {"attempt", "kind", "answered"} <= set(said):
        raise LandError(f"the record is one object with `attempt`, `kind` and `answered`, and of the others what applies: {', '.join(sorted(known))}")
    # A record that is sent again, after a run that was cut off or by mistake, must not count as
    # a second review: it says which start of the review it is, and only the next one is taken.
    if said["attempt"] != state["attempt"]:
        raise LandError(
            f"the record says attempt {said['attempt']!r}, and the next review of this task is attempt {state['attempt']}: "
            + ("that review is written down already" if said["attempt"] in [read.get("attempt") for read in reads] else "`land.py read` prints the number a record carries"),
        )
    kind = said["kind"]
    if kind not in KINDS:
        raise LandError(f"`kind` is one of {', '.join(KINDS)}: {'; '.join(f'{name} is {says}' for name, says in KIND_SAYS.items())}")
    if KINDS.index(kind) < KINDS.index(state["floor"]):
        raise LandError(f"this change gets {KIND_SAYS[state['floor']]} at the least ({state['why']}), and the record says {KIND_SAYS[kind]}")
    # The careful call is the review's own reading of the diff against the project's topics, by an
    # agent that did not build it: it is what lets an agent merge, or keeps the merge a person's.
    call, call_why = said.get("careful"), said.get("careful_why")
    if not isinstance(call, bool) or not isinstance(call_why, str) or not call_why.strip() or "\n" in call_why.strip():
        raise LandError(
            "the record makes the careful call: \"careful\": true or false, the review's own reading of the diff against each of the project's topics "
            "(`topics` in what `land.py read` printed), and \"careful_why\": one line that names the topic the change reaches, or what was checked to say that it reaches none",
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
    if kind != "read" and not ran:
        raise LandError("a round names each profile it ran in `ran`, with why that profile fits this change")
    if kind == "full" and left_out:
        raise LandError("the project's full set leaves no profile out: a profile may be added to it, never dropped")
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
        "careful": call, "careful_why": call_why.strip(),
        "date": date.today().isoformat(), "verdict": "not reviewed" if not answered else "must-fix" if counts["must_fix"] else "clean", "tip": state["tip"][:9], "patch": state["patch"],
    }
    # The event first: a run that is cut off between the two writes the review down at its next
    # run, and the second event has the same attempt, by which a reader of the log knows it.
    script("project.py", task.worktree, "log", task.slug, "review", *(f"{key}:={json.dumps(value)}" for key, value in entry.items()))
    # The contents of the change stay out of the log: only `covers` reads them, from the kept record.
    task.keep(reads=[*reads, {**entry, "contents": state["contents"]}])
    # A change the review calls careful and the plan did not is a lesson about the plan's call: one
    # event for the retro, the first time a review finds it.
    if answered and call and not plan_careful(task) and not any(record.get("event") == "careful.missed" for record in events_of(task)):
        script("project.py", task.worktree, "log", task.slug, "careful.missed", f"round:={state['round']}", f"why={call_why.strip()}")
    return {"task": task.slug, "recorded": entry, "next": due(task)["due"], "to_file": to_file(task.kept()["reads"])}


def not_green(task: Task, state: dict) -> list[str]:
    """Each reason for which this request is not green, one line each; none when it is green."""
    reasons = []
    # A small change took the short path: no interview, no read of its story, no plan. One that is
    # careful after all is read by a person, whatever its checks and its review say.
    if stories_of(task)["small"] and state["careful"]:
        reasons.append(
            f"a small change that is careful ({reason(state['careful'][0])}): it took the short path, with no interview, "
            "no personas' read of its story and no plan, so a person reads it",
        )
    # the personas' read of the stories, started twice with no answer: the stories went on unread
    read = story_read_of(task)
    if read is not None and unanswered(task) >= 2:
        quiet = "".join(f"; no answer from {source['name']} ({source['why']})" for source in read.get("silent", []))
        reasons.append(f"the stories were not read: the personas' read was started twice and nobody answered{quiet}")
    commands, brought = task.gate()
    if brought:
        reasons.append(
            "the gate came with this change: the main checkout's settings name no gate command, and the branch's .lem/project.toml brings "
            + ", ".join(f"`{command}`" for command in commands) + ". Read the checks once: every later task is gated on them",
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
    for change in (change for change in stories_of(task)["history"] if change["taken_over_by"] is None):
        reasons.append(f"story {change['story']} {STORY_HOW[change['how']]} during the build: {story_why(task, change)}")
    for decision in task.decisions():
        # the experts' shared pick, taken while he was away (`settled`) or at the end of his wait
        if decision.get("by") == "experts":
            when = "while the owner was away, before the wait ended" if decision["state"] == "settled" else f"after the owner's wait of {decision['wait_minutes']} minutes ended with no answer"
            reasons.append(
                f"choice {decision['id']} was taken by the experts ({decision['what']}): \"{decision['chose']}\", the option both picked, {when}. "
                f"{experts_said(decision)}{later(decision, '; the owner answered later with')}",
            )
        elif decision["state"] == "timeout":
            reasons.append(
                f"choice {decision['id']} was taken by timeout ({decision['what']}): \"{decision['chose']}\", the recommended option, "
                f"after the owner's wait of {decision['wait_minutes']} minutes ended with no answer{later(decision, '; the owner answered later with')}",
            )
    return reasons


def story_why(task: Task, change: dict) -> str:
    """Why a story changed: the reason the record gives, and the choice that led to it, when one did."""
    if "choice" not in change:
        return change["why"]
    choice = next(decision for decision in task.decisions() if decision["id"] == change["choice"])
    how = "which the owner settled with" if choice.get("instead") else f"where {TAKEN_BY[choice['by']]} took"
    return f"{reason(change['why'])}, after choice {choice['id']} ({choice['what']}), {how} \"{choice['chose']}\""


def story_line(task: Task, change: dict) -> str:
    """One recorded change of a story as one line of the pull request: what it was, what it is, why, and who."""
    said = {
        "changed": f"was \"{change.get('was')}\", now \"{change.get('now')}\"",
        "added": f"added, \"{change.get('now')}\"",
        "removed": f"removed, was \"{change.get('was')}\"",
    }[change["how"]]
    who = "" if "choice" in change else " By the lead." if change["by"] == "lead" else f" By the personas: {change['said']}"
    later = f" Approved by the owner afterwards (approval {change['taken_over_by']})." if change.get("taken_over_by") else ""
    return f"- story {change['story']}: {said}. {reason(story_why(task, change))}.{who}{later}"


def reason(text: str) -> str:
    """A reason as written, without its own full stop, for a sentence around it."""
    return text.rstrip(".")


def experts_said(decision: dict) -> str:
    """Both experts' reasons for the pick they shared, as the record keeps them."""
    return f"Fable: {reason(decision['experts']['fable'])}. Astra: {reason(decision['experts']['astra'])}"


def later(decision: dict, lead: str) -> str:
    """What the owner answered after the timeout or the experts' pick, when he did: the same or what differs, with his
    own words when they are not the option's text, and his reason, whichever it is."""
    if "late" not in decision:
        return ""
    late = decision["late"]
    said = []
    if late.get("words", late["chose"]) != late["chose"]:
        said.append(f"the owner's words: \"{late['words']}\"")
    if "why" in late:
        said.append(f"the owner's reason: {reason(late['why'])}")
    told = f" ({'; '.join(said)})" if said else ""
    if late.get("instead"):
        return f"{lead} \"{late['chose']}\", none of the options{told}"
    if late["chose"] == decision["chose"]:
        return f"{lead} the same{told}"
    return f"{lead} \"{late['chose']}\", which differs{told}"


def decided(decision: dict) -> str:
    """One decision of the record as one line of the pull request: what, what was chosen, by whom, why."""
    head = f"- {decision['what']}: "
    if decision["state"] == "waits":
        return head + "waits for the owner."
    line = head + f"\"{decision['chose']}\", by {TAKEN_BY[decision['by']]}"
    if decision["state"] == "answered" and decision.get("instead"):
        # his own decision, which none of the options says: the recommendation is named as such
        line += f", none of the options; the recommended was \"{decision['recommended']}\" (recommended because: {reason(decision['why'])})."
        line += "" if "owner_why" in decision else " The owner gave no reason."
    elif decision["state"] == "answered" and decision["chose"] == decision["recommended"]:
        # the recommendation's reason is the reason of the option he took; his own, when he gave one, follows
        line += f", as recommended. {decision['why']}"
    elif decision["state"] == "answered":
        # the recommendation's reason is about the option he did not take: it is named as such, never as his
        line += f", over the recommended \"{decision['recommended']}\" (recommended because: {reason(decision['why'])})."
        line += "" if "owner_why" in decision else " The owner gave no reason."
    elif decision["by"] == "experts":
        # their reasons are the reasons of the option taken; the recommendation's is about another one, or the same
        when = "while the owner was away" if decision["state"] == "settled" else f"after the owner's wait of {decision['wait_minutes']} minutes"
        also = "it is also the recommended" if decision["chose"] == decision["recommended"] else f"the recommended was \"{decision['recommended']}\""
        line += f", the option both picked, {when}; {also}. {experts_said(decision)}." + (f" {later(decision, 'The owner answered later with')}." if "late" in decision else "")
    elif decision["state"] == "timeout":
        line += f", after the owner's wait of {decision['wait_minutes']} minutes. {decision['why']}" + (f" {later(decision, 'The owner answered later with')}." if "late" in decision else "")
    else:
        line += f" ({decision['said']}). {decision['why']}" if decision["by"] == "personas" else f". {decision['why']}"
    if decision.get("owner_words", decision["chose"]) != decision["chose"]:
        line += f" The owner's words: \"{decision['owner_words']}\""
    if "owner_why" in decision:
        line += f" The owner's reason: {decision['owner_why']}"
    return line


def builder_filed(task: Task) -> list[str]:
    """The items a small change's builder filed: each file the branch adds to the backlog folder,
    other than those `file` wrote for a review, which the review's own line names."""
    folder = backlog_of(task)
    base = git(task.worktree, "merge-base", "HEAD", task.onto)
    reviews = {defect["item"] for read in task.kept().get("reads", []) for defect in outside_of(read) if defect.get("item")}
    rows = [row.split("\t", 1) for row in git(task.worktree, "diff", "--name-status", "--no-renames", "--diff-filter=A", base, "HEAD").splitlines()]
    return [path for _, path in rows if path.startswith(folder + "/") and path not in reviews]


def small_text(task: Task, notes: str, state: dict) -> str:
    """The text of a small change's pull request: green or not, the story, the checks, the read.
    What a small change does not have (a plan, a personas' read, a polish pass, a talk) gets no line;
    what its builder filed in the backlog gets one."""
    kept = task.kept()
    checks = kept.get("checks") or {}
    found = stories_of(task)
    ask = (task.directory / "ask.txt").read_text(encoding="utf-8").strip() if (task.directory / "ask.txt").is_file() else ""
    held = {(test["story"], test["command"]): test for test in (checks.get("stories") or {}).get("tests", [])}
    reasons = not_green(task, state)
    out = ["**Not green.**", "", *(f"- {why}" for why in reasons), ""] if reasons else [GREEN, ""]
    if state["careful"]:
        out += [f"**Careful**, so a person merges it: {'; '.join(reason(why) for why in state['careful'])}.", ""]
    out += ["## The request", "", *(f"> {line}" for line in (ask or "(the owner's words were not kept for this task)").splitlines()), ""]
    approval = found.get("approved") or {}
    by = f" Lem approved it in the owner's name on {approval['at'][:10]}; the personas did not read it." if approval.get("by") == "correction" else ""
    out += ["## The story", "", f"A small change, because {reason(found['why'])}.{by}", ""]
    for story in found["stories"]:
        out.append(f"{story['n']}. {story['text']}")
        for test in story["tests"]:
            proof = held.get((story["n"], test["command"]))
            out.append(f"   - `{test['command']}`: {'passes on the branch, fails on the base commit' if proof and not proof['problem'] else 'not checked'}")
        if story["no_test"]:
            out.append(f"   - no test: {story['no_test']}")
    out += [story_line(task, change) for change in found["history"]]
    out += ["", "## Checks", ""]
    out += [f"- gate, `{command['command']}`: {command['last'] or 'exit ' + str(command['exit'])}" for command in checks.get("commands", [])]
    own = builder_filed(task)
    if own:
        out.append("- filed in the backlog by the builder: " + ", ".join(f"`{path}`" for path in own))
    cause = task.record.get("investigation")
    if cause and cause.get("kind") == "bug":
        where = f" ({cause['where']})" if cause.get("where") else ""
        out.append(f"- the cause, as the investigation found it: {cause['line']}{where}")
    lowered = (checks.get("bar") or {}).get("lowered", [])
    out.append("- the bar: not lowered" if not lowered else "- the bar is lowered: " + "; ".join(f"`{entry['file']}` ({entry['what']})" for entry in lowered))
    for read in kept.get("reads", []):
        who = f"answered: {', '.join(read['answered'])}" if read["answered"] else "no source answered"
        said = f"{read['verdict']}, {read['must_fix']} must-fix, {read['should']} should, {read['nit']} nit" if read["answered"] else "not reviewed"
        defects = outside_of(read)
        if defects:
            said += "; filed outside the change: " + ", ".join(f"`{defect['item']}`" for defect in defects)
        out.append(f"- the review, round {read['round']} ({KIND_SAYS[read['kind']]}; {who}): {said}")
    out.append(careful_line(task, state))
    decisions = [decided(decision) for decision in task.decisions()]
    if decisions:
        out += ["", "## Decisions", "", *decisions]
    rest = notes.strip()
    return "\n".join(out) + ("\n\n" + rest if rest and rest.lower() != "none" else "") + "\n"


def pr_text(task: Task, notes: str, state: dict) -> str:
    """The text of the pull request, in the order the owner reads it."""
    if stories_of(task)["small"]:
        return small_text(task, notes, state)
    kept = task.kept()
    checks = kept.get("checks") or {}
    found = stories_of(task)
    ask = (task.directory / "ask.txt").read_text(encoding="utf-8").strip() if (task.directory / "ask.txt").is_file() else ""
    held = {(test["story"], test["command"]): test for test in (checks.get("stories") or {}).get("tests", [])}
    out: list[str] = []
    reasons = not_green(task, state)
    if reasons:
        out += ["**Not green.**", "", *(f"- {reason}" for reason in reasons), ""]
    else:
        out += [GREEN, ""]
    if state["careful"]:
        # a careful request is a person's to merge, green or not, and he reads why first
        out += [f"**Careful**, so a person merges it: {'; '.join(reason(why) for why in state['careful'])}.", ""]
    out += ["## The request", "", *(f"> {line}" for line in (ask or "(the owner's words were not kept for this task)").splitlines()), ""]
    out += ["## Stories", "", f"{found['kind'].capitalize()}, because {found['why']}", ""]
    for story in found["stories"]:
        out.append(f"{story['n']}. {story['text']}")
        for test in story["tests"]:
            proof = held.get((story["n"], test["command"]))
            out.append(f"   - `{test['command']}`: {'passes on the branch, fails on the base commit' if proof and not proof['problem'] else 'not checked'}")
        if story["no_test"]:
            out.append(f"   - no test: {story['no_test']}")
    if found["history"]:
        out += ["", "Stories that changed during the build, in the order of the record:", ""]
        out += [story_line(task, change) for change in found["history"]]
    out += ["", "## Checks", ""]
    for command in checks.get("commands", []):
        code = command["exit"]
        out.append(f"- gate, `{command['command']}`: {command['last'] or f'exit {code}'}")
    tests = (checks.get("stories") or {}).get("tests", [])
    without = (checks.get("stories") or {}).get("without_a_test", [])
    out.append(f"- the stories' tests: {len(tests)} pass on the branch and fail on the base commit" + (f"; {len(without)} stor{'y has' if len(without) == 1 else 'ies have'} no test" if without else ""))
    out.append(polished(kept.get("polish")))
    read = story_read_of(task)
    out.append(read_line(read, found, unanswered(task), read_skipped(task)[0] if read is None else None))
    if unread(read, found):
        out.append(unread(read, found))
    scout = task.directory / "scout.md"
    if scout.is_file():
        out.append(f"- the scout's report, the facts of the code the stories were written from: `{scout}`")
    cause = task.record.get("investigation")
    if cause and cause.get("kind") == "bug":
        # a feature that came from a bug names the cause its investigation found
        where = f" ({cause['where']})" if cause.get("where") else ""
        out.append(f"- the cause, as the investigation before the build found it: {cause['line']}{where}; its report: `{task.directory / 'investigation.md'}`")
    lowered = (checks.get("bar") or {}).get("lowered", [])
    out.append("- the bar: not lowered" if not lowered else "- the bar is lowered, with these reasons:")
    out += [f"  - `{entry['file']}` ({entry['what']}): {entry['reason']}" for entry in lowered]
    if (checks.get("bar") or {}).get("not_covered"):
        own = checks["bar"].get("own_patterns", 0)
        out.append(f"- the bar has no marks of its own for files of these kinds: {', '.join(checks['bar']['not_covered'])}" + (f" (the project's {own} pattern(s) in gate.bar were looked for)" if own else ""))
    size = checks.get("size") or {}
    out.append(f"- size: {size.get('files', '?')} files, {size.get('lines', '?')} changed lines")
    for read in kept.get("reads", []):
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
    out += ["", "## Decisions of the build", "", *([decided(decision) for decision in task.decisions()] or ["none"])]
    return "\n".join(out) + "\n\n" + notes.strip() + "\n"


def gh(task: Task, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    if not shutil.which("gh"):
        raise LandError("the remote is GitHub and the `gh` command is not on PATH: install it and sign in, then run this again")
    ran = subprocess.run(["gh", *args], cwd=task.worktree if task.worktree.exists() else task.main, capture_output=True, text=True, check=False)
    if check and ran.returncode != 0:
        raise LandError(f"gh {' '.join(args[:2])} failed: {(ran.stderr or ran.stdout).strip()}")
    return ran


def cmd_propose(task: Task, title: str, notes_file: str) -> dict:
    task.need_landing()
    task.need_worktree()
    tip = git(task.worktree, "rev-parse", "HEAD")
    if not gate_holds(task, tip):
        raise LandError(f"no green check is on record for this tip; `land.py gate {task.slug}` comes first")
    kept = task.kept()
    reads = kept.get("reads", [])
    unfiled = to_file(reads)
    state = due(task)
    if state["due"] == "review":
        raise LandError(f"a review is due before anything is proposed, {KIND_SAYS[state['floor']]} at the least ({state['why']}); `land.py read {task.slug}` says what a reviewer gets")
    # A careful or large plan is talked through by its defender and the reviewer, in the plan
    # talk's companion, before any code. The talk leaves one event, and a request without it
    # skipped that step.
    needs_talk = talk_due(task, state)
    talk = talk_of(task) if needs_talk else None
    if needs_talk and talk is None:
        raise LandError(
            f"{needs_talk}, so its defender and the reviewer talk its plan through in the plan talk's companion before any code (`stages/talk.md`), "
            f"and the event log has no `plan.talk` of {task.slug}. The defender writes it after the talk: "
            f"`project.py log {task.slug} plan.talk {TALK_FORM}`; for a plan that had no talk, Lem opens the companion first, as for `needs a session` (`stages/new.md`)",
        )
    if talk is not None and not (
        isinstance(talk.get("reviewer"), str) and talk["reviewer"].strip()
        and all(isinstance(talk.get(key), int) and not isinstance(talk.get(key), bool) for key in ("turns", "settled", "open"))
    ):
        raise LandError(f"the newest `plan.talk` of {task.slug} does not have the form `{TALK_FORM}`; its defender writes it again with `project.py log`")
    read = story_read_of(task)
    if read is not None and not read_form(read):
        raise LandError(f"the newest `stories.read` of {task.slug} does not have the form {READ_FORM}; whoever ran the read writes it again with `project.py log`")
    # The personas read a feature's stories before the build, and a doubt of theirs reaches him:
    # a request is not proposed over stories nobody read, or over a doubt he never saw.
    found = stories_of(task)
    if read is None and not found["small"]:
        # his word to skip the read, with his approval after it and both before any lead started, is the one way past it
        skipped, why_not = read_skipped(task)
        if why_not:
            raise LandError(why_not)
        if skipped is None:
            raise LandError(
                f"{task.slug} is a feature, and the event log has no `stories.read`: the personas read its stories before the build "
                "(`stages/new.md`, \"The interview and the stories\", step 5; on the rare path `stages/plan.md`, step 1), "
                f"and whoever ran the read writes `project.py log {task.slug} stories.read` with the form {READ_FORM}. "
                f"Only the owner skips a read, at the interview and when every story names only the developer: Lem writes the owner's word with {read_skip_form(task.slug)}, "
                "and the owner approves the stories after it, both before a lead starts",
            )
    if read is not None and not read["answered"] and unanswered(task) < 2:
        raise LandError(
            f"nobody answered the newest read of {task.slug}'s stories: it is started once more, and its record written again with `project.py log {task.slug} stories.read` "
            "(`stages/new.md`, \"The interview and the stories\", step 5; on the rare path `stages/plan.md`, step 1). "
            "After a second read in a row that nobody answered, the request is proposed as not green",
        )
    if read is not None and (read["flagged"] or read["split"]) and not approved_after(found, read):
        doubt = f"{read['flagged']} flagged stor{'y' if read['flagged'] == 1 else 'ies'}" if read["flagged"] else "a split between the two families"
        raise LandError(
            f"the newest read of {task.slug}'s stories found {doubt}, and no approval of the owner's came after it: the stories with the personas' answers "
            "on top go to the owner (`stages/new.md`, \"The interview and the stories\", step 6), and the owner's yes is kept with "
            f"`stories.py approve {task.slug} --file FILE`",
        )
    # Each defect a review saw outside the change has its item in the tip, so that none is lost: one
    # that a session never filed, and one whose item a later commit took out.
    if unfiled:
        raise LandError(
            f"{len(unfiled)} defect(s) a review saw outside the change have no item in the backlog: "
            + "; ".join(f"\"{defect['title']}\" (round {defect['round']})" for defect in unfiled)
            + f". `land.py file {task.slug}` files them, then this step runs again",
        )
    gone = [(read, defect) for read in reads if read["answered"] for defect in outside_of(read) if not in_tree(task, tip, defect["item"])]
    if gone:
        read, defect = gone[0]
        raise LandError(
            f"the item {defect['item']} of the defect \"{defect['title']}\" (review round {read['round']}) was removed after it was filed"
            + (f", and {len(gone) - 1} more" if len(gone) > 1 else "")
            + f": a builder puts it back with `land.py file {task.slug} --again`, then this step runs again; when the owner does not want it, "
            "the item stays with `worth: no` and the owner's reason in it, never deleted",
        )
    # A request is never proposed over an open question of the owner's.
    waiting = next((decision for decision in task.decisions() if decision["state"] == "waits"), None)
    if waiting:
        ends = (
            "it is a step that a later \"no\" cannot reverse, so only the owner's answer ends it"
            if waiting["irreversible"] else f"or, after its wait ends at {waiting['deadline']}, `decisions.py timeout {task.slug} {waiting['id']}` takes the experts' shared pick, or the recommended option when they split"
        )
        raise LandError(
            f"choice {waiting['id']} of {task.slug} waits for the owner ({waiting['what']}): a request is never proposed over an open question of the owner's. "
            f"Lem writes the owner's answer with `decisions.py answer {task.slug} {waiting['id']} --chose OPTION --words TEXT`, the option word for word and the owner's own words beside it, or `--instead TEXT` "
            f"for a decision of the owner's that is none of the options; {ends}",
        )
    notes = Path(notes_file).read_text(encoding="utf-8") if Path(notes_file).is_file() else None
    if notes is None:
        raise LandError(f"{notes_file} is not a file; --notes names the notes of the pull request")
    # A small change's notes are what the review left open, in a few lines, or `none`: it has no
    # plan to decide from, no polish pass to file from, and nothing it set out of scope.
    wanted = [*([] if stories_of(task)["small"] else NOTES), *(["## Migration"] if state["careful"] else [])]
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
    pr = kept.get("pr")
    if task.forge == "github":
        if not pr:
            # a run that was cut off after the forge made the pull request wrote none down: the forge knows it
            there = json.loads(gh(task, "pr", "list", "--head", branch, "--base", str(task.base), "--state", "open", "--json", "number,url").stdout)
            pr = {"number": there[0]["number"], "url": there[0]["url"]} if there else None
        elif (state_now := viewed(task, pr)["state"]) != "OPEN":
            raise LandError(
                f"the pull request {pr['url']} is {state_now.lower()}: " + ("`land.py merged` finishes the task" if state_now == "MERGED" else "whether the task is dropped or goes on is the owner's call"),
            )
        # with lease: after a rebase the remote branch is behind, and nobody else pushes to a task's branch
        git(task.worktree, "push", "--force-with-lease", "origin", f"HEAD:refs/heads/{branch}")
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
    if task.forge == "github":
        task.keep(pr=pr, proposed=tip, title=title, not_green=reasons)
        task.state("open", f"pull request {pr['url']}", says)
    else:
        task.keep(proposed=tip, title=title, not_green=reasons)
        task.state("open", f"ready to land on {task.base} at {tip[:9]}", says)
    return {"task": task.slug, "text": str(body), "pull_request": pr, "green": not reasons, "not_green": reasons, "branch": branch, "tip": tip}


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


def finish(task: Task, tip: str, landed: str, arrived: list[str]) -> dict:
    """The bookkeeping after the base holds the tip: the base checkout follows, the state says landed."""
    left_behind = follow(task)
    task.keep(landed=landed)
    task.state("landed", f"{task.base} {landed}")
    # Dropped last: until the state says `landed`, a run that is cut off must find the record again.
    task.keep(intent=None)
    return {"task": task.slug, "base": task.base, "range": landed, "tip": tip, "pushed": task.remote, "arrived": arrived, "left_behind": left_behind}


def may_merge(task: Task, by: str) -> None:
    """Who may merge. The owner's word is enough; an agent merges only what nobody has a reason to look at first."""
    if by == "owner":
        return
    if task.settings["branch"]["land"] != "agent":
        raise LandError("branch.land is \"owner\" in .lem/project.toml: a person merges; the task waits as `open` for the owner's word")
    state = due(task)
    if state["careful"]:
        raise LandError(f"a careful request is merged by a person, whatever the settings say ({state['careful'][0]}); it waits as `open` for the owner's word")
    reasons = not_green(task, state)
    if reasons:
        raise LandError(f"the request is not green ({'; '.join(reasons)}), so a person merges it, whatever the settings say; it waits as `open` for the owner's word")
    # An agent merges only on the newest review's "not careful": a record with no call, as one
    # written before the call was asked, is no such word.
    if review_call(task) is None:
        raise LandError("no review that answered made the careful call for this change, so a person merges it, whatever the settings say; it waits as `open` for the owner's word")


def forge_done(task: Task, view: dict) -> dict:
    task.fetch()
    pr = task.kept()["pr"]
    merged = (view.get("mergeCommit") or {}).get("oid")
    # the commit of the branch that the forge merged: `clean` removes the branch only when it holds nothing after it
    task.keep(merged=merged or True, merged_head=view["headRefOid"])
    left_behind = follow(task)
    task.state("landed", f"{task.base}: pull request {pr['url']} is merged")
    return {"task": task.slug, "base": task.base, "pull_request": pr, "merged": merged, "left_behind": left_behind}


def viewed(task: Task, pr: dict | None = None) -> dict:
    pr = pr or task.kept()["pr"]
    return json.loads(gh(task, "pr", "view", str(pr["number"]), "--json", "state,headRefOid,mergeCommit").stdout)


def cmd_merged(task: Task) -> dict:
    if task.merges:
        raise LandError(
            f'branch.propose is "merge" in .lem/project.toml: no pull request is opened, so none is merged on the forge; '
            f"`land.py land {task.slug} --by owner|agent` puts the ready branch on the base branch",
        )
    # `landing` too: the owner may merge on the forge while an open task runs its checks again
    if task.record["status"] not in ("open", "landing") or not task.kept().get("pr"):
        raise LandError(f"the task is {task.record['status']!r} and has {'a' if task.kept().get('pr') else 'no'} pull request; this step is for a task whose pull request the owner merged")
    view = viewed(task)
    if view["state"] == "MERGED":
        return forge_done(task, view)
    if view["state"] == "CLOSED":
        raise LandError("the pull request was closed without a merge: whether the task is dropped or goes on is the owner's call")
    raise LandError("the pull request is not merged yet")


def cmd_land(task: Task, by: str, message: str | None) -> dict:
    if task.record["status"] != "open":
        raise LandError(f"the task is {task.record['status']!r}, not `open`; `land.py propose {task.slug}` comes first")
    task.need_worktree()
    kept = task.kept()
    intent = kept.get("intent")
    if intent and not kept.get("pr"):
        task.fetch()
        if run(["git", "-C", str(task.worktree), "merge-base", "--is-ancestor", intent["tip"], task.onto], check=False).returncode == 0:
            # An earlier run put this commit on the base and was cut off before the bookkeeping. Who
            # may merge was settled by that run, so this one only finishes.
            if git(task.worktree, "rev-parse", "HEAD") == intent["tip"]:
                return finish(task, intent["tip"], intent["range"], intent["arrived"])
            # The branch got more work since. What landed then is written down, and what the branch
            # holds now lands like any tip: through its own base, checks and read.
            task.keep(intent=None, landed_before=[*kept.get("landed_before", []), intent["range"]])
            raise LandError(f"{intent['range']} is on {task.onto} from a landing that was cut off, and the branch has more work since: {AGAIN} for it")
    view = viewed(task) if kept.get("pr") else None
    if view and view["state"] == "MERGED":
        # the forge already holds the merge, whoever made it: only the bookkeeping is left
        return forge_done(task, view)
    may_merge(task, by)
    if not kept.get("gated"):
        raise LandError(f"no green check is on record for this tip; {AGAIN}")
    squash = task.settings["branch"]["history"] == "squash"
    if squash and not message:
        raise LandError("branch.history is \"squash\": pass --message with the one commit's subject, from the task's report")
    if not squash and message:
        raise LandError("branch.history is \"keep\": the branch's own commits land, so --message has nothing to name")
    if view:
        # A pull request is merged by the forge, under the forge's own rules, and only at the commit that was proposed.
        if view["state"] != "OPEN":
            raise LandError("the pull request was closed without a merge: whether the task is dropped or goes on is the owner's call")
        tip = git(task.worktree, "rev-parse", "HEAD")
        if view["headRefOid"] != tip or kept.get("proposed") != tip:
            raise LandError(f"the pull request's head is not the tip that was proposed; {AGAIN}")
        task.fetch()
        base_now = git(task.worktree, "rev-parse", task.onto)
        moved = changed(task, kept["base"], base_now) if base_now != kept["base"] else []
        if not ignored(task, moved):
            raise LandError(
                f"{task.onto} moved after the checks ran, by files the gate reads ({', '.join(moved[:5])}{', ...' if len(moved) > 5 else ''}); {AGAIN}",
            )
        how = ["--squash", "--subject", message] if squash else ["--rebase"]
        gh(task, "pr", "merge", str(kept["pr"]["number"]), "--match-head-commit", tip, *how)
        view = viewed(task)
        if view["state"] != "MERGED":
            raise LandError("the forge took the merge and the pull request is not merged yet (a queue, or a check it waits for); run `land.py merged` when it is")
        return forge_done(task, view)
    if kept.get("proposed") != git(task.worktree, "rev-parse", "HEAD"):
        raise LandError(f"the branch's tip is not the tip that was proposed; {AGAIN}")

    task.fetch()
    base_now = git(task.worktree, "rev-parse", task.onto)
    arrived: list[str] = []
    if base_now != kept["base"]:
        # The base moved after the gate ran. The result stands only when every file that arrived is
        # one the project says the gate does not read.
        arrived = changed(task, kept["base"], base_now)
        if not ignored(task, arrived):
            raise LandError(
                f"{task.onto} moved after the gate ran, by files the gate reads ({', '.join(arrived[:5])}"
                f"{', ...' if len(arrived) > 5 else ''}); {AGAIN}",
            )
        if run(["git", "-C", str(task.worktree), "rebase", task.onto], check=False).returncode != 0:
            git(task.worktree, "rebase", "--abort", check=False)
            raise LandError(f"{task.onto} moved after the gate ran and the rebase onto it stopped, and the branch is as it was; {AGAIN}, where `base` names the files that meet")
    elif git(task.worktree, "rev-parse", "HEAD") != kept["gated"]:
        raise LandError(f"the branch's tip is not the commit the gate passed on; {AGAIN}")
    # What lands is the tree the gate saw, plus only the ignored files that arrived on the base.
    differs = changed(task, kept["tree"], "HEAD^{tree}")
    if not set(differs) <= set(arrived):
        raise LandError(f"the tree that would land differs from the tree the gate passed on in {', '.join(differs[:5])}; {AGAIN}")

    if squash:
        # A commit runs the project's hooks, and a hook may change what is committed. The one commit
        # must hold the tree that was just checked, so the branch is put back when it does not.
        before = git(task.worktree, "rev-parse", "HEAD")
        checked = git(task.worktree, "rev-parse", "HEAD^{tree}")
        git(task.worktree, "reset", "--soft", base_now)
        made = run(["git", "-C", str(task.worktree), "commit", "-m", message], check=False)
        if made.returncode != 0:
            git(task.worktree, "reset", "--soft", before)
            raise LandError(
                f"the one commit was refused, and the branch is as it was: {(made.stderr or made.stdout).strip()}. "
                f"A hook that refused the subject takes another --message to `land.py land {task.slug}`; one that refused the files, "
                f"a commit on the branch that meets it, then {AGAIN}",
            )
        if git(task.worktree, "rev-parse", "HEAD^{tree}") != checked:
            git(task.worktree, "reset", "--hard", before)
            raise LandError(
                "a commit hook changed the files of the one commit, so it is not the tree the gate passed on; the branch is as it was. "
                f"Commit what the hook changes on the branch, then {AGAIN}",
            )
    tip = git(task.worktree, "rev-parse", "HEAD")
    landed = f"{base_now[:9]}..{tip[:9]}"
    # Written before the base moves: a run that is cut off after it finds this and only finishes.
    task.keep(intent={"tip": tip, "range": landed, "arrived": arrived})
    if task.remote:
        # A plain push: the remote refuses it when someone else pushed first, which is the answer wanted.
        git(task.worktree, "push", "origin", f"HEAD:{task.base}")
    elif task.base_checkout is not None:
        # A fast-forward in the checkout that holds the base: git refuses it when a file there is in the way.
        git(task.base_checkout, "merge", "--ff-only", tip)
    else:
        # No checkout holds the base branch, so its ref may move; without `+` git allows a fast-forward only.
        git(task.worktree, "fetch", ".", f"HEAD:{task.base}")
    return finish(task, tip, landed, arrived)


def cmd_clean(task: Task) -> dict:
    if task.record["status"] not in ("landed", "dropped", "answered"):
        raise LandError(f"the task is {task.record['status']!r}; only a landed, dropped or answered task loses its worktree")
    removed: dict = {"worktree": False, "branch": None, "branch_left": None, "remote": None, "remote_left": None}
    # The worktree names its branch while it is there; after it, what `start` wrote down does.
    branch = task.kept().get("branch")
    if (task.worktree / ".git").exists():
        branch = git(task.worktree, "branch", "--show-current") or branch
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
        after = f"; the forge merged {kept['merged_head'][:9]}, and the branch has commits after it" if kept.get("merged") else ""
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=".", help="a directory inside the checkout (default: the current one)")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("start", "base", "gate", "merged", "clean"):
        commands.add_parser(name).add_argument("slug")
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
    land = commands.add_parser("land")
    land.add_argument("slug")
    land.add_argument("--by", required=True, choices=BY, help="who merges: the owner's word, or the agent where the settings and the request allow it")
    land.add_argument("--message", help="the subject of the one commit, when branch.history is \"squash\"")
    args = parser.parse_args()
    try:
        task = Task(Path(args.repo), args.slug)
        if args.command == "start":
            result = cmd_start(task)
        elif args.command == "base":
            result = cmd_base(task)
        elif args.command == "polish":
            result = cmd_polish(task, args.done)
        elif args.command == "gate":
            result = cmd_gate(task)
        elif args.command == "read":
            result = cmd_read(task, args.record)
        elif args.command == "file":
            result = cmd_file(task, args.again)
        elif args.command == "propose":
            result = cmd_propose(task, args.title, args.notes)
        elif args.command == "land":
            result = cmd_land(task, args.by, args.message)
        elif args.command == "merged":
            result = cmd_merged(task)
        else:
            result = cmd_clean(task)
    except LandError as error:
        sys.exit(f"land.py: {error}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
