#!/usr/bin/env python3
"""The decisions of one task: each one taken without the owner, and each choice put to the owner.

A build meets choices its plan did not see. Most are the lead's own: the acceptance criteria stay
true, so the lead decides and writes the decision down. A choice that changes a criterion, or whose
options each cost a person something, climbs a ladder of opinions (`stages/ladder.md`): the gate,
the personas, the dialectic, the experts, each only when the one before left it open; the lead
applies its counts, since the lead reads the code. Without the owner, its result is logged here.
With the owner, a decision the gate or the personas settled is logged too, and one that went past
the personas goes to him: it waits for his answer, with no time limit, while the rest of the task
goes on. When he says he is away (`lem project owner away`), the ladder's pick is taken at once,
and the pull request is not green for it. One kind of step never goes that way: a step that a
later "no" cannot reverse waits for the owner's word however long that takes.

    lem decisions log SLUG --what TEXT --chose TEXT --why TEXT
                 --by lead|gate|personas|dialectic|experts|owner|lem
                 [--said TEXT] [--undo TEXT] [--option TEXT ...] [--vote "PERSONA, FAMILY=OPTION" ...]
                 [--level NAME=ANSWER ...] [--unsettled]
                            a decision that was taken, and by which level of the ladder: --why
                            holds the gate's cite, --said what the personas answered. --option is
                            each option the decision had, --vote each persona's answer, one for
                            each model family, and --level what each level that ran answered.
                            `--by personas` takes two votes or more, each for the option --chose
                            names (one of an older lead, with --said and no --vote, is taken as
                            before). `--unsettled` goes with `--by lead`: no level settled it, and
                            the lead's pick stands. `owner` is a word of the owner's that nobody
                            asked for (the task is careful), or the owner's yes to skip the
                            personas' read of criteria that name only the developer, in the form
                            `land.py` reads (`READ_SKIP`); `lem` one that Lem took before the task
                            had a lead (out of scope)
    lem decisions criterion SLUG (--changed N --was TEXT --now TEXT | --added N --now TEXT
                 | --removed N --was TEXT) --why TEXT (--choice ID | --by lead|personas [--said TEXT])
                            a change of a criterion the owner approved, with its text before and
                            after: N is its number in the criteria as they stand after every
                            earlier change. --choice names the choice of the build that led to
                            it, answered or taken without the owner; without one, the lead's own change
                            or the personas' clear pick
    lem decisions changes SLUG
                            the approved criteria, each recorded change of them in order, and the
                            criteria they give, which the plan's criteria must be
    lem decisions ask SLUG --what TEXT --case STEPS --case-was reproduced|derived --cause TEXT
                 --option TEXT --option TEXT [...] --recommended TEXT --why TEXT --said TEXT
                 [--irreversible data|system|person|money]
                            a choice for the owner, of the plan or of the build: it gets a number,
                            and while the task runs without the owner the ladder's pick is taken
                            at once, unless it is irreversible. --case is one concrete case that ends
                            badly, in numbered steps, one to a line, and --cause one line on why it
                            became possible and how far that reaches: the owner's card tells one
                            run.
    lem decisions pending [SLUG]
                            the choices that wait, of one task or of every task (`waiting`). A task that is dropped,
                            landed or answered has none: its choices that never got an answer are named
                            under `ended`, with the task's status, and need no answer
    lem decisions wait SLUG ID [--seconds N]
                            return when the choice is answered, when the task runs without the
                            owner (then the ladder's pick is taken now), or after N seconds, and
                            say which
    lem decisions answer SLUG ID --chose OPTION [--words TEXT] [--why TEXT]
                            the owner's answer: the option it takes, word for word, the owner's
                            own words when they are not that text, and the reason when one was
                            given.
                            Lem writes it down. Text that is no option is refused here
    lem decisions answer SLUG ID --instead TEXT [--words TEXT] [--why TEXT]
                            the owner decided what none of the options says: TEXT settles the
                            choice, an irreversible one too
    lem decisions advise SLUG ID --expert fable|astra (--pick OPTION | --none) --why TEXT
                            one expert's advice on a choice that waits: the option it picks, word
                            for word, or none of them, with its reasons. One advice of each expert,
                            while the choice waits; an irreversible step takes advice too
    lem decisions away
                            what `lem project owner away` runs: each choice that waits, of each
                            task that runs without the owner now, and that is no irreversible
                            step, is taken now: the experts' shared pick when both picked the
                            same option, the ladder's pick (`--recommended`) otherwise
    lem decisions list SLUG  every decision of the task, each as it stands now

The record is `decisions.jsonl` in the task's directory, one line for each thing that happened;
a decision is the lines with its number. Each line is also an event in the log the board draws.

A criterion change is a line of the same record, with a number of its own (`change`). It applies
to the newest approval of the criteria (`criteria.json`, which `lem criteria approve` writes) and names
that approval by its number, so a later approval starts from its criteria again, also when its text
is one approved before. `changes` keeps every change in `history`: one that a later approval of
the owner's took over is the owner's, and the pull request shows it as approved by the owner
afterwards. `criterion` computes the criteria as they stand after every earlier change, and refuses a change whose criterion N is not the
text `--was` names: a wrong record never enters. Texts are compared with each run of spaces as
one, as a criterion written over two lines reads; they are kept as typed. A choice carries no
criterion: when the option taken changes one, the lead records that with `criterion --choice ID`,
and the check of the criteria refuses the plan until it does. A task with no approved criteria has
no criterion changes: its plan's criteria are their one source. A change an older Lem recorded is
a line with `"kind": "story"` and its number under `story`, and an approval it kept is
`stories.json`: both read as the lines and the file of now. A later change may drop the old forms
once no task that has them is open.

A choice has no time limit: "Lets remove this 15min automatic timeout - to have more explicit: Owner
either tells dnd or not, no assumptions" (the owner, 2026-11-18). A choice taken because the task
ran without the owner is a line `timeout` with `early: true`, the form an older Lem wrote for its
"go alone", so that one reader reads both. A choice an older Lem asked has a `deadline` and its
`wait_minutes`; the deadline no longer ends its wait, and a `timeout` line with no `early`, which
the clock of an older Lem took, still reads as taken after that wait. `timeout` itself is refused
with what holds now. `--said` is not optional for `ask`:
the levels of the ladder answer before the owner is asked, and their answers go with the question;
`--recommended` is the ladder's pick.

A count decides each level, not a model, and the lead applies it: the script checks one count
only, two persona votes or more, all for the option taken. It reads no answer of an agent, and
it moves another count in only when a real run shows a lead that records a level wrongly.

`--irreversible` names why a later "no" cannot undo the step, by one of four kinds and no other:
`data` (it destroys or rewrites data outside the worktree), `system` (it writes to a system
outside the repository, beyond what the settings already allow, such as the tracker's ticket),
`person` (it sends something to a person), `money` (it spends money). The lead says which; no
code can tell.

The experts are two agents of two model families, the settings' `seats.experts`; the owner asked
for them as the way out when the owner is not there to answer (2026-11-16). On the ladder they are
a level before any card, and their shared pick is logged `--by experts`. `advise` keeps their
advice on a choice that waits, in two places, `fable` for the first seat and `astra` for the
second, whatever model sits there: when the owner asks for all opinions on a card, and on a choice
an older lead asked. When the owner goes away their shared pick is taken (`by: experts`, with both
reasons), and the recommended option when they split or one is missing (`by: timeout`). Either way
the pull request is not green for it. A `settled` line, which an older Lem wrote when
the owner was away, still reads as the experts' pick; a later change may drop it once no task with
such a line is open.

An answer to a choice that was taken without the owner is written down as late. What was taken
stands; when the answer differs from it, that is a correction, for the lead while the task builds
and a new ask after that.

Every write reads the record and checks the state under one lock, so an answer and the owner's
"away" that come at one time leave one outcome, and two writers never take one number. A task that is
dropped, landed or answered takes no write at all, read under the same lock: nobody builds it,
and its record stays as it ended.
"""

from __future__ import annotations

import sys

if sys.version_info < (3, 11):
    # an old python3 must still load this file, so that it can say what it needs and not a traceback
    sys.exit(f"decisions.py: Lem needs Python 3.11 or newer, and this python3 is {sys.version.split()[0]}; put a newer one first on PATH, or run this file with it")

import argparse
import fcntl
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
# How this script calls a sibling: in this process, as one command of it.
sys.dont_write_bytecode = True
sys.path.insert(0, str(SCRIPTS))
import lem_sibling  # noqa: E402

# Who took a decision: the lead, a level of the ladder (`stages/ladder.md`), the owner, or Lem.
BY = ("lead", "gate", "personas", "dialectic", "experts", "owner", "lem")
# The task states in which nothing of a task waits any more, as project.py's ENDED.
ENDED = ("dropped", "landed", "answered")
# The two places in which the record keeps the experts' advice, as project.py's EXPERT_PLACES: the
# first seat of the settings' `seats.experts` answers in `fable`, the second in `astra`, whatever
# model sits there, so a record written under any seats reads the same.
EXPERTS = ("fable", "astra")
# How the case of a choice is known: the lead ran it, or read it out of the code.
CASE_WAS = ("reproduced", "derived")
# Why a later "no" cannot undo a step. A fixed list: see the text above.
IRREVERSIBLE = {
    "data": "it destroys or rewrites data outside the worktree",
    "system": "it writes to a system outside the repository, beyond what the settings allow",
    "person": "it sends something to a person",
    "money": "it spends money",
}


class DecisionError(Exception):
    pass


def script(name: str, repo: Path, *args: str) -> str:
    ran = lem_sibling.run(SCRIPTS / name, repo, *args)
    if ran.returncode != 0:
        raise DecisionError(ran.stderr.strip().removeprefix(f"{name}: ") or f"{name} {args[0]} failed")
    # a line project.py writes on stderr when it succeeds (the move of an older state folder) is this script's to say too
    if ran.returncode == 0 and ran.stderr:
        sys.stderr.write(ran.stderr)
    return ran.stdout


def now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def stamp(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


class Task:
    def __init__(self, repo: Path, slug: str, tasks: list[dict] | None = None, state: Path | None = None) -> None:
        """`tasks` and `state`, when given, are `lem project tasks` and `state-dir` as this process
        read them already: `pending` reads them once for every task it lists."""
        self.repo = repo
        self.slug = slug
        self.mode = "with-owner"
        self.status = self.read_status(tasks)
        self.directory = (state or Path(script("project.py", repo, "state-dir").strip())) / "tasks" / slug
        self.file = self.directory / "decisions.jsonl"

    def read_status(self, tasks: list[dict] | None = None) -> str | None:
        """The task's status now, from its state file: a task may be dropped while a command runs.
        Its mode comes with it: the owner may say that he is away while a command runs."""
        if tasks is None:
            tasks = json.loads(script("project.py", self.repo, "tasks"))
        record = next((task for task in tasks if task["slug"] == self.slug), None)
        if record is None:
            raise DecisionError(f"no task {self.slug!r}; the tasks are: {', '.join(task['slug'] for task in tasks) or 'none yet'}")
        self.mode = record.get("mode", "with-owner")
        return record["status"]

    def lines(self) -> list[dict]:
        if not self.file.is_file():
            return []
        out = []
        try:
            written = self.file.read_text(encoding="utf-8")
        except UnicodeDecodeError as error:
            raise DecisionError(f"{self.file} is not UTF-8 text (byte {error.start} does not read); the file is written by this script only") from error
        for number, line in enumerate(written.splitlines(), start=1):
            if line.strip():
                try:
                    out.append(json.loads(line))
                except ValueError as error:
                    raise DecisionError(f"{self.file}:{number} does not read as JSON ({error}); the file is written by this script only") from error
        return out

    def decisions(self) -> list[dict]:
        """Each decision as it stands now: its first line, with what came after under the same number."""
        found: dict[int, dict] = {}
        for line in self.lines():
            if line["kind"] in ("taken", "asked"):
                found[line["id"]] = {**line, "state": "taken" if line["kind"] == "taken" else "waits"}
            elif line["kind"] == "answered":
                found[line["id"]].update(
                    state="answered", chose=line["chose"], by="owner", answered=line["at"],
                    **{f"owner_{key}": line[key] for key in ("words", "why") if key in line},
                    **({"instead": True} if line.get("instead") else {}),
                )
            elif line["kind"] == "advised":
                found[line["id"]].setdefault("advice", {})[line["expert"]] = {key: line[key] for key in ("pick", "none", "why", "at") if key in line}
            elif line["kind"] == "timeout":
                # a timeout before the experts existed has no `by`: it took the recommended option
                found[line["id"]].update(
                    state="timeout", chose=line["chose"], by=line.get("by", "timeout"), taken=line["at"],
                    **({"experts": line["experts"]} if "experts" in line else {}), **({"early": True} if line.get("early") else {}),
                )
            elif line["kind"] == "settled":
                found[line["id"]].update(state="settled", chose=line["chose"], by="experts", taken=line["at"], experts=line["experts"], away=True)
            elif line["kind"] == "late":
                found[line["id"]].update(late={"chose": line["chose"], "at": line["at"], **{key: line[key] for key in ("words", "why", "instead") if key in line}})
        return [found[key] for key in sorted(found)]

    def approved(self) -> dict | None:
        """The criteria the owner approved, as `lem criteria approve` kept them; none for a task without.
        An approval an older Lem kept names its kind (`feature`, `correction`) and not its `size`, and
        Lem's own approval on the fast track as `by: correction`: each reads in the form of now. A
        later change may drop the old form once no task with such an approval is open."""
        kept = self.directory / "criteria.json"
        if not kept.is_file():
            # where an older Lem kept them
            kept = self.directory / "stories.json"
        if not kept.is_file():
            return None
        try:
            record = json.loads(kept.read_text(encoding="utf-8"))
        except ValueError as error:
            raise DecisionError(f"{kept} does not read as JSON ({error}); it is written by `lem criteria approve` only") from error
        return {**now_form(record), "history": [now_form(old) for old in record.get("history", [])]}

    def changes(self, lines: list[dict] | None = None) -> dict:
        """The approvals, the recorded changes of the criteria in order, and the criteria they give.

        An approval is known by its number, not by its text: one of a text approved before is still
        a new one. The expected criteria are the newest approval's with the changes recorded after
        it. Every change of the task stays in `history`, each with the approval it applied to and,
        when an approval of the owner's came after it, that approval's number (`taken_over_by`): his
        approval of the criteria made the change his."""
        approved = self.approved()
        if approved is None:
            return {"task": self.slug, "approved": None, "approvals": [], "changes": [], "history": [], "expected": None}
        keys = ("number", "at", "by", "size", "digest")
        approvals = [{key: old.get(key) for key in keys} for old in approved.get("history", [])] + [{key: approved.get(key) for key in keys}]
        # a file an approve before numbered approvals wrote has one approval, the first
        approvals[-1]["number"] = approvals[-1]["number"] or len(approvals)
        newest = approvals[-1]["number"]
        everything = [changed(line) for line in (self.lines() if lines is None else lines) if line["kind"] in CHANGE_KINDS]
        history = []
        for line in everything:
            later = next((old["number"] for old in approvals if old["number"] > line.get("approval", 0) and old["by"] == "owner"), None)
            history.append({**line, "taken_over_by": later})
        changes = [line for line in everything if line.get("approval") == newest]
        expected = [criterion["text"] for criterion in approved["criteria"]]
        for change in changes:
            expected = applied(expected, change)
        return {
            "task": self.slug, "approved": {key: approved.get(key) for key in keys} | {"number": newest}, "approvals": approvals,
            "changes": changes, "history": history, "expected": expected,
        }

    def one(self, number: int, known: list[dict] | None = None) -> dict:
        known = self.decisions() if known is None else known
        decision = next((d for d in known if d["id"] == number), None)
        if decision is None or decision["kind"] != "asked":
            asked = [str(d["id"]) for d in known if d["kind"] == "asked"]
            raise DecisionError(f"no choice {number} went to the owner in {self.slug}; those that did: {', '.join(asked) or 'none'}")
        return decision

    def add(self, make) -> list[dict]:
        """Write the lines `make` gives for the record as it is under the lock, so a state is
        checked and changed in one step and two writers never take one number; then each line
        as an event. `make` refuses by raising, and then nothing is written. A task that ended
        takes no write: nobody builds it, so nothing of it is decided or waits any more."""
        self.directory.mkdir(parents=True, exist_ok=True)
        with (self.directory / "decisions.lock").open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            # read again under the lock: the task may have ended while this command waited for it
            self.status = self.read_status()
            if self.status in ENDED:
                raise DecisionError(
                    f"{self.slug} is {self.status}: nothing of it is decided or waits any more, so this is not written. "
                    f"Its record stays as it is (`lem decisions list {self.slug}`); new work is a new ask",
                )
            lines = make(self.decisions())
            with self.file.open("a", encoding="utf-8") as handle:
                handle.write("".join(json.dumps(line) + "\n" for line in lines))
        for line in lines:
            script("project.py", self.repo, "log", self.slug, f"decision.{line['kind']}", *(f"{key}:={json.dumps(value)}" for key, value in line.items() if key != "kind"))
        return lines


# The kinds an older Lem gave an approval of its stories, by the `size` word each is now, and who approved
# for its `by: correction`. A later change may drop them once no task with such an approval is open.
OLD_SIZES = {"feature": "full", "correction": "small"}
OLD_BY = {"correction": "lem"}


def now_form(approval: dict) -> dict:
    """One approval of criteria in the form of now: its `size`, its texts under `criteria`, and Lem as who
    approved on the fast track."""
    out = {key: value for key, value in approval.items() if key not in ("kind", "history", "stories")}
    if "criteria" not in out and "stories" in approval:
        out["criteria"] = approval["stories"]
    if "size" not in out and "kind" in approval:
        out["size"] = OLD_SIZES.get(approval["kind"], approval["kind"])
    if out.get("by") in OLD_BY:
        out["by"] = OLD_BY[out["by"]]
    return out


# The kind of a line that changes a criterion, and the kind an older Lem wrote for it (`story`, with
# the number under `story`). A later change may drop the old one once no task with such a line is open.
CHANGE_KINDS = ("criterion", "story")


def changed(line: dict) -> dict:
    """A line that changes a criterion, in the form of now."""
    if line["kind"] != "story":
        return line
    return {("criterion" if key == "story" else key): ("criterion" if key == "kind" else value) for key, value in line.items()}


def shared(decision: dict) -> str | None:
    """The option both experts picked, or None: one is missing, one found none fits, or they split."""
    advice = decision.get("advice", {})
    picks = {advice[name].get("pick") for name in EXPERTS if name in advice}
    if len(advice) < len(EXPERTS) or len(picks) != 1 or None in picks:
        return None
    return picks.pop()


def ending(number: int, decision: dict, at: str) -> dict:
    """The line that takes a choice without the owner, as the task runs without him: the experts'
    shared pick, or the recommended option. Its form is the one an older Lem wrote for its "go
    alone" (`early`), so that one reader reads both."""
    pick = shared(decision)
    if pick is None:
        return {"id": number, "at": at, "kind": "timeout", "chose": decision["recommended"], "by": "timeout", "early": True}
    return {"id": number, "at": at, "kind": "timeout", "chose": pick, "by": "experts", "experts": {name: decision["advice"][name]["why"] for name in EXPERTS}, "early": True}


def text(value: str | None, flag: str) -> str:
    if value is None or not value.strip():
        raise DecisionError(f"{flag} needs its text: one sentence in plain words")
    return " ".join(value.split())


def typed(value: str | None, flag: str) -> str:
    """A criterion's text as typed: two spaces in a literal value stay two."""
    if value is None or not value.strip():
        raise DecisionError(f"{flag} needs the criterion's text, word for word")
    return value.strip()


def same(one: str, other: str) -> bool:
    """Two texts of a criterion are the same when they differ only in runs of spaces, as a criterion
    written over two lines reads as one line with one space."""
    return one.split() == other.split()


def applied(criteria: list[str], change: dict) -> list[str]:
    """The criteria after one change; a change whose criterion N is not the text it names is refused."""
    number, out = change["criterion"], list(criteria)
    if change["how"] == "added":
        if not 1 <= number <= len(out) + 1:
            raise DecisionError(f"an added criterion goes at a number from 1 to {len(out) + 1}, and this one is {number}")
        out.insert(number - 1, change["now"])
        return out
    if not 1 <= number <= len(out):
        raise DecisionError(f"there is no criterion {number}: the criteria are 1 to {len(out)} after every earlier change")
    if not same(out[number - 1], change["was"]):
        raise DecisionError(f"criterion {number} is {out[number - 1]!r} after every earlier change, and --was says {change['was']!r}; `lem decisions changes SLUG` gives the criteria as they stand")
    if change["how"] == "changed":
        out[number - 1] = change["now"]
    else:
        out.pop(number - 1)
    return out


def pairs(values: list[str] | None, flag: str, form: str) -> list[list[str]]:
    """Each `NAME=TEXT` of a repeated flag, as typed, split at its first `=`."""
    out = []
    for value in values or []:
        name, sign, said = value.partition("=")
        if not sign or not name.strip() or not said.strip():
            raise DecisionError(f"{flag} is {form}, and {value!r} is not")
        out.append([" ".join(name.split()), " ".join(said.split())])
    return out


def cmd_log(task: Task, args: argparse.Namespace) -> dict:
    chose = text(args.chose, "--chose")
    votes = pairs(args.vote, "--vote", "\"PERSONA, FAMILY=OPTION\", one for each answer of a persona")
    if args.by == "personas" and not votes and not args.said:
        raise DecisionError("--by personas needs a --vote for each answer of a persona, \"PERSONA, FAMILY=OPTION\", and --said: who answered and what each picked")
    # The one count the script checks (`stages/ladder.md`, level 2). A log with --said and no vote is
    # the form a lead of the stage text before wrote, and is taken as it was: a later change may drop
    # it once no such lead runs.
    if args.by == "personas" and votes:
        other = [name for name, option in votes if option != chose]
        if len(votes) < 2 or other:
            raise DecisionError(
                f"the personas settle a decision with two votes or more, all for the option taken ({chose!r}); "
                + (f"{', '.join(other)} voted otherwise" if other else f"this one has {len(votes)}")
                + ": the ladder goes on to the dialectic (`stages/ladder.md`)",
            )
    if args.unsettled and args.by != "lead":
        raise DecisionError("--unsettled is the lead's pick that no level settled: it goes with --by lead")
    line = {"at": stamp(now()), "kind": "taken", "what": text(args.what, "--what"), "chose": chose, "why": text(args.why, "--why"), "by": args.by}
    for key in ("said", "undo"):
        # an empty value is refused, never dropped
        if getattr(args, key) is not None:
            line[key] = text(getattr(args, key), f"--{key}")
    if args.option:
        line["options"] = [text(option, "--option") for option in args.option]
    if votes:
        line["votes"] = votes
    if args.level:
        line["levels"] = dict(pairs(args.level, "--level", "NAME=ANSWER, one for each level that ran"))
    if args.unsettled:
        line["unsettled"] = True
    return task.add(lambda known: [{"id": len(known) + 1, **line}])[0]


def cmd_criterion(task: Task, args: argparse.Namespace) -> dict:
    """Record one change of an approved criterion, checked against the criteria as they stand."""
    how = [name for name in ("changed", "added", "removed") if getattr(args, name) is not None]
    if len(how) != 1:
        raise DecisionError("a criterion change is one of --changed N, --added N or --removed N")
    how = how[0]
    wants = {"changed": ("was", "now"), "added": ("now",), "removed": ("was",)}[how]
    for key in ("was", "now"):
        if key in wants and getattr(args, key) is None:
            raise DecisionError(f"--{how} needs --{key}: the criterion's text {'before' if key == 'was' else 'after'} the change, word for word")
        if key not in wants and getattr(args, key) is not None:
            raise DecisionError(f"--{how} takes no --{key}: " + ("an added criterion had no text before" if how == "added" else "a removed criterion has no text after"))
    if (args.choice is None) == (args.by is None):
        raise DecisionError("a criterion change names --choice ID, the choice of the build that led to it, or --by lead|personas when no choice did: one of the two")
    if args.by == "personas" and not args.said:
        raise DecisionError("--by personas needs --said: who answered and what each picked, in one or two sentences")
    if args.said is not None and args.by != "personas":
        raise DecisionError("--said is what the personas answered: it goes with --by personas")
    approved = task.approved()
    if approved is None:
        raise DecisionError(
            f"{task.slug} has no approved criteria, so no change of them is recorded: its plan's criteria are their one source. "
            "Approved criteria are kept by `lem criteria approve`",
        )
    line = {"at": stamp(now()), "kind": "criterion", "how": how, "criterion": getattr(args, how), "why": text(args.why, "--why"), "approval": approved.get("number") or 1 + len(approved.get("history", []))}
    for key in wants:
        line[key] = typed(getattr(args, key), f"--{key}")
    if args.choice is not None:
        line["choice"] = args.choice
    else:
        line["by"] = args.by
        if args.said is not None:
            line["said"] = text(args.said, "--said")

    def make(known: list[dict]) -> list[dict]:
        if args.choice is not None:
            choice = task.one(args.choice, known)
            if choice["state"] not in ("answered", "timeout", "settled"):
                # the state as a verb: a choice that "waits", a decision that "is taken"
                said = "waits" if choice["state"] == "waits" else f"is {choice['state']}"
                raise DecisionError(f"choice {args.choice} {said}: a criterion changes after a choice that was answered or taken by timeout, or that the experts settled")
        lines = task.lines()
        # the same computation the check of the criteria makes, with this change last: a wrong record never enters
        task.changes([*lines, line])
        return [{"change": sum(1 for old in lines if old["kind"] in CHANGE_KINDS) + 1, **line}]

    made = task.add(make)[0]
    return {**made, "criteria": task.changes()["expected"]}


def steps(value: str | None) -> str:
    """The case of a choice as typed, one step to a line: two numbered steps at the least."""
    lines = [line.rstrip() for line in (value or "").strip().splitlines() if line.strip()]
    numbered = [line for line in lines if re.match(r"\s*\d+[.)]\s+\S", line)]
    if len(numbered) < 2:
        raise DecisionError(
            "--case is one concrete case that ends badly, in numbered steps, one to a line (\"1. ...\", \"2. ...\"), "
            f"with real names and values and where each step was read; this one has {len(numbered)} numbered step{'' if len(numbered) == 1 else 's'}",
        )
    return "\n".join(lines)


def cmd_ask(task: Task, args: argparse.Namespace) -> dict:
    case = steps(args.case)
    if args.case_was not in CASE_WAS:
        raise DecisionError(f"--case-was says how the case is known: {' or '.join(CASE_WAS)}")
    cause = text(args.cause, "--cause")
    options = [text(option, "--option") for option in args.option or []]
    if len(options) < 2:
        raise DecisionError("a choice has two options or more: --option for each")
    recommended = text(args.recommended, "--recommended")
    if recommended not in options:
        raise DecisionError(f"--recommended is one of the options, word for word: {'; '.join(options)}")
    line = {
        "at": stamp(now()), "kind": "asked", "what": text(args.what, "--what"), "case": case, "case_was": args.case_was, "cause": cause,
        "options": options, "recommended": recommended,
        "why": text(args.why, "--why"), "said": text(args.said, "--said"), "irreversible": args.irreversible,
    }

    def make(known: list[dict]) -> list[dict]:
        asked = {"id": len(known) + 1, **line}
        # while the task runs without the owner (read again under the lock), nothing waits for him but an irreversible step
        return [asked] if args.irreversible or task.mode != "alone" else [asked, ending(asked["id"], {**asked, "advice": {}}, asked["at"])]

    made = task.add(make)
    if len(made) > 1:
        return {**made[0], "taken": made[1]["chose"], "next": "the task runs without the owner: the ladder's pick is taken now, the pull request is not green for it, and nothing waits"}
    # the experts answer on the ladder before any card (`stages/ladder.md`), so the next step names only Lem
    told = f"tell Lem that choice {made[0]['id']} of {task.slug} waits; "
    return {**made[0], "next": told + (
        "it waits for the owner's word, however long: the rest of the plan goes on" if args.irreversible
        else f"go on with what does not depend on it; `lem decisions wait {task.slug} {made[0]['id']}` says when it is answered, or taken because the owner went away"
    )}


def cmd_advise(task: Task, number: int, args: argparse.Namespace) -> dict:
    """One expert's advice on a choice that waits, checked against the record under the lock."""
    if (args.pick is None) == (not args.none):
        raise DecisionError("an expert's advice is --pick OPTION, one of the choice's options word for word, or --none when it found that none fits: one of the two")
    line = {"id": number, "at": stamp(now()), "kind": "advised", "expert": args.expert}
    if args.none:
        line["none"] = True
    else:
        line["pick"] = text(args.pick, "--pick")
    line["why"] = text(args.why, "--why")

    def make(known: list[dict]) -> list[dict]:
        decision = task.one(number, known)
        if decision["state"] != "waits":
            raise DecisionError(f"choice {number} does not wait: it is {decision['state']}, with {decision['chose']!r}; advice on it changes nothing")
        if args.expert in decision.get("advice", {}):
            raise DecisionError(f"choice {number} has the advice of {args.expert} already: one advice of each expert, and `lem decisions list {task.slug}` shows it")
        if "pick" in line and line["pick"] not in decision["options"]:
            raise DecisionError(
                f"the pick of an expert is one of the options of choice {number}, word for word: {'; '.join(decision['options'])}. "
                "An answer that fits none of them is --none, with its reasons in --why",
            )
        return [line]

    made = task.add(make)[0]
    advised = task.one(number)
    return {**made, "advised": sorted(advised.get("advice", {})), "experts_pick": shared(advised)}


def shown(task: Task, decision: dict) -> dict:
    out = {"task": task.slug, **{key: value for key, value in decision.items() if key != "kind"}}
    if decision["kind"] == "asked" and decision["state"] == "waits":
        if "advice" in decision:
            out["experts_pick"] = shared(decision)
    return out


def cmd_pending(repo: Path, slug: str | None) -> dict:
    """The choices that wait for the owner. A dropped, landed or answered task has none: nobody
    needs his answer there, and the record stays for `list`."""
    # Every task, from one read of the tasks and of the state folder: nothing here writes either.
    listed = json.loads(script("project.py", repo, "tasks")) if not slug else None
    state = Path(script("project.py", repo, "state-dir").strip()) if listed else None
    slugs = [slug] if slug else [task["slug"] for task in listed]
    waiting: list[dict] = []
    ended: list[dict] = []
    for task in (Task(repo, name, listed, state) for name in slugs):
        open_ones = [decision for decision in task.decisions() if decision["state"] == "waits"]
        if task.status in ENDED:
            if open_ones or slug:
                ended.append({
                    "task": task.slug, "status": task.status, "choices": [decision["id"] for decision in open_ones],
                    "says": f"the task is {task.status}: its choices no longer wait for an answer",
                })
        else:
            waiting += [shown(task, decision) for decision in open_ones]
    return {"waiting": waiting, "ended": ended}


def cmd_wait(task: Task, number: int, seconds: int) -> dict:
    until = time.monotonic() + seconds
    while True:
        decision = task.one(number)
        if decision["state"] != "waits":
            ended = {"answered": "answered", "settled": "settled by the experts while the owner was away"}.get(
                decision["state"], "taken without the owner" if decision.get("early") else "taken by the timeout of an older Lem",
            )
            return {**shown(task, decision), "ended": ended}
        if task.status in ENDED:
            return {**shown(task, decision), "ended": f"the task is {task.status}: the choice no longer waits", "status": task.status}
        # the owner went away, or the task is a night's: nothing waits for him any more but an irreversible step
        if not decision["irreversible"] and task.mode == "alone":
            taken = take(task, [number])
            if taken:
                return {**shown(task, task.one(number)), "ended": "taken without the owner: the task runs without him now"}
            continue
        if time.monotonic() >= until:
            return {**shown(task, decision), "ended": "still waits"}
        # A short step, so that an answer or a drop ends the wait within two seconds or so; the
        # status is read again with the choice, because a task dropped or landed during the wait ends it.
        time.sleep(min(2, max(0.5, until - time.monotonic())))
        task.status = task.read_status()


def cmd_answer(task: Task, number: int, args: argparse.Namespace) -> dict:
    if (args.chose is None) == (args.instead is None):
        raise DecisionError("--chose names one of the options and --instead a decision of the owner's that is none of them: give one of the two")
    instead = args.instead is not None
    chose = text(args.instead, "--instead") if instead else text(args.chose, "--chose")
    reason = {key: text(value, f"--{key}") for key, value in (("words", args.words), ("why", args.why)) if value is not None}
    if instead:
        reason["instead"] = True
    taken: dict = {}

    def make(known: list[dict]) -> list[dict]:
        decision = task.one(number, known)
        at = stamp(now())
        if decision["state"] == "answered":
            raise DecisionError(f"choice {number} has the owner's answer already: {decision['chose']!r}")
        # The option is what the record and the pull request read; his own words stay beside it. A decision of his that is none of the options is --instead.
        if not instead and chose not in decision["options"]:
            raise DecisionError(
                f"the answer to choice {number} is one of its options, word for word: {'; '.join(decision['options'])}. "
                "Put the owner's own words in --words. When what the owner decided fits none of them, settle the choice with "
                "--instead TEXT, never with a new `lem decisions log`, so it does not wait for ever",
            )
        # A choice that waits takes his answer, however long it waited: an older Lem's deadline ends no wait now.
        if decision["state"] == "waits":
            return [{"id": number, "at": at, "kind": "answered", "chose": chose, **reason}]
        # Taken without him (or by an older Lem's timeout, or settled by the experts while he was away): what was taken stands.
        taken.update(chose=decision["chose"], state=decision["state"])
        return [{"id": number, "at": at, "kind": "late", "chose": chose, **reason}]

    made = task.add(make)[-1]
    if made["kind"] == "answered":
        return made
    return {**made, "state": taken["state"], "taken": taken["chose"], "next": (
        "the answer is the action that was taken: nothing more to do" if chose == taken["chose"]
        else f"\"{taken['chose']}\" was taken without the owner, and the answer differs: it is a correction. Tell the lead while the task builds; after that it is a new ask"
    )}


def take(task: Task, numbers: list[int] | None = None) -> list[dict]:
    """Take each choice of the task that waits and is no irreversible step (only those of `numbers`,
    when given), as the task runs without the owner: one line each, under the lock, where the mode is
    read again. Nothing when the owner is there."""
    def make(known: list[dict]) -> list[dict]:
        if task.mode != "alone":
            return []
        at = stamp(now())
        return [ending(decision["id"], decision, at) for decision in known
                if decision["kind"] == "asked" and decision["state"] == "waits" and not decision["irreversible"] and (numbers is None or decision["id"] in numbers)]

    return task.add(make)


def cmd_away(repo: Path) -> dict:
    """Each choice that waits, of each task that runs without the owner now: taken now, except an
    irreversible step, which waits for him in every case."""
    listed = json.loads(script("project.py", repo, "tasks"))
    state = Path(script("project.py", repo, "state-dir").strip())
    taken: list[dict] = []
    for record in listed:
        if record["status"] in ENDED or record.get("mode") != "alone":
            continue
        task = Task(repo, record["slug"], listed, state)
        if any(decision["state"] == "waits" for decision in task.decisions()):
            taken += [{"task": task.slug, "id": line["id"], "chose": line["chose"], "by": line["by"]} for line in take(task)]
    return {"taken": taken}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="lem decisions", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=".", help="a directory inside the checkout (default: the current one)")
    commands = parser.add_subparsers(dest="command", required=True)
    log = commands.add_parser("log")
    log.add_argument("slug")
    for flag in ("--what", "--chose", "--why"):
        log.add_argument(flag, required=True)
    log.add_argument("--by", required=True, choices=BY)
    log.add_argument("--said", help="what the personas answered: who, which option, in one or two sentences")
    log.add_argument("--undo", help="what it would take to undo the decision")
    log.add_argument("--option", action="append", metavar="TEXT", help="each option the decision had, word for word")
    log.add_argument("--vote", action="append", metavar="PERSONA, FAMILY=OPTION", help="one persona's answer in one model family")
    log.add_argument("--level", action="append", metavar="NAME=ANSWER", help="what one level of the ladder answered")
    log.add_argument("--unsettled", action="store_true", help="with --by lead: no level settled it, and the lead's pick stands")
    criterion = commands.add_parser("criterion")
    criterion.add_argument("slug")
    criterion.add_argument("--changed", type=int, metavar="N", help="criterion N changed: --was is its text before, --now its text after")
    criterion.add_argument("--added", type=int, metavar="N", help="a criterion the build adds at number N, with --now its text")
    criterion.add_argument("--removed", type=int, metavar="N", help="criterion N leaves the criteria, with --was its text")
    criterion.add_argument("--was", help="the criterion's text before the change, word for word")
    criterion.add_argument("--now", help="the criterion's text after the change, word for word")
    criterion.add_argument("--why", required=True, help="why the criterion changed, in one sentence")
    criterion.add_argument("--choice", type=int, metavar="ID", help="the choice of the build that led to the change")
    criterion.add_argument("--by", choices=("lead", "personas"), help="who changed it, when no choice did")
    criterion.add_argument("--said", help="with --by personas: who answered and what each picked")
    commands.add_parser("changes").add_argument("slug")
    ask = commands.add_parser("ask")
    ask.add_argument("slug")
    ask.add_argument("--what", required=True)
    ask.add_argument("--case", metavar="STEPS", help="one concrete case that ends badly, in numbered steps, one to a line")
    ask.add_argument("--case-was", metavar="HOW", help="reproduced, or derived from the code")
    ask.add_argument("--cause", help="one line: why the case became possible, and how far the same cause reaches")
    ask.add_argument("--option", action="append", metavar="TEXT")
    ask.add_argument("--recommended", required=True)
    ask.add_argument("--why", required=True, help="why that option is recommended")
    ask.add_argument("--said", required=True, help="what the personas answered: who, which option, and why they do not agree")
    ask.add_argument("--irreversible", choices=tuple(IRREVERSIBLE), help="why a later \"no\" cannot undo the step")
    pending = commands.add_parser("pending")
    pending.add_argument("slug", nargs="?")
    wait = commands.add_parser("wait")
    wait.add_argument("slug")
    wait.add_argument("id", type=int)
    wait.add_argument("--seconds", type=int, default=540, help="how long this call stays at the most (default: 540)")
    answer = commands.add_parser("answer")
    answer.add_argument("slug")
    answer.add_argument("id", type=int)
    answer.add_argument("--chose", metavar="OPTION", help="the option the owner's answer takes, word for word")
    answer.add_argument("--instead", metavar="TEXT", help="the owner's decision, when it is none of the options; it settles the choice")
    answer.add_argument("--words", help="the owner's answer as given, when it is not the option's text")
    answer.add_argument("--why", help="the owner's own reason, in the owner's words, when one was given; never the recommendation's")
    commands.add_parser("away")
    # an older lead's text runs `timeout` after a wait that has no end now: it is told what holds
    timeout = commands.add_parser("timeout")
    timeout.add_argument("rest", nargs="*")
    advise = commands.add_parser("advise")
    advise.add_argument("slug")
    advise.add_argument("id", type=int)
    advise.add_argument("--expert", required=True, choices=EXPERTS)
    advise.add_argument("--pick", metavar="OPTION", help="the option the expert picked, word for word")
    advise.add_argument("--none", action="store_true", help="the expert found that none of the options fits")
    advise.add_argument("--why", required=True, help="the expert's reasons, in two to four sentences")
    commands.add_parser("list").add_argument("slug")
    args = parser.parse_args(argv)
    for arg in sys.argv[1:] if argv is None else argv:
        try:
            arg.encode("utf-8")
        except UnicodeEncodeError:
            # the record would hold it, and the event log and the pull request after it
            sys.exit(f"decisions.py: the argument {os.fsencode(arg)!r} is not UTF-8 text; give it in UTF-8")
    repo = Path(args.repo)
    try:
        if args.command == "timeout":
            raise DecisionError(
                "a choice has no time limit now: it waits for the owner's answer while he is there, and `lem project owner away` takes it at once "
                "when he says he is away. Go on with what does not depend on it; `lem decisions wait SLUG ID` returns when it is answered or taken",
            )
        if args.command == "pending":
            result: object = cmd_pending(repo, args.slug)
        elif args.command == "away":
            result = cmd_away(repo)
        else:
            task = Task(repo, args.slug)
            if args.command == "log":
                result = cmd_log(task, args)
            elif args.command == "criterion":
                result = cmd_criterion(task, args)
            elif args.command == "changes":
                result = task.changes()
            elif args.command == "ask":
                result = cmd_ask(task, args)
            elif args.command == "wait":
                result = cmd_wait(task, args.id, args.seconds)
            elif args.command == "answer":
                result = cmd_answer(task, args.id, args)
            elif args.command == "advise":
                result = cmd_advise(task, args.id, args)
            else:
                result = [shown(task, decision) for decision in task.decisions()]
    except DecisionError as error:
        sys.exit(f"decisions.py: {error}")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
