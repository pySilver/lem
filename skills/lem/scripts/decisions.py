#!/usr/bin/env python3
"""The decisions of one task, each taken without the owner, and the breakers that stopped it.

A build meets choices its plan did not see. Most are the lead's own: the acceptance criteria stay
true, so the lead decides and writes the decision down. A choice that changes a criterion, or whose
options each cost a person something, climbs a ladder of opinions (`stages/ladder.md`): the gate,
the personas, the dialectic, the experts, each only when the one before left it open; the lead
applies its counts, since the lead reads the code. The ladder always decides: its pick is taken at
once and logged here, with the owner there or away, and nothing waits for him. A pick past the
personas makes the pull request not green, and he reads it there. "I'd rather review the PR and
request a fix then find a work blocked on some question that automated anwers could answer right"
(the owner, 2026-11-20).

Only the circuit breaker stops a task, for two causes and no others: the next step cannot be
reversed by a later "no" (`irreversible`), or no option of the ladder keeps the outcome the owner
approved (`criteria`: a changed rule of an approved criterion; a changed example is a criterion
change of `criterion`). The lead commits what it has, writes `handoff.md` and `breaker.md` in the
task directory, and `breaker` records it, keeps the document under the breaker's number
(`breaker-N.md`, so that a second breaker of the task never writes over the first one's), and holds
the task. The owner reads the document and helps
(his decision is `log --by owner --breaker N`), parks the task or drops it.

    lem decisions log SLUG --what TEXT --chose TEXT --why TEXT
                 --by lead|gate|personas|dialectic|experts|owner|lem
                 [--said TEXT] [--undo TEXT] [--option TEXT ...] [--vote "PERSONA, FAMILY=OPTION" ...]
                 [--level NAME=ANSWER ...] [--unsettled] [--breaker N] [--words TEXT]
                 [--case STEPS --case-was reproduced|derived --cause TEXT] [--chart FILE]
                            a decision that was taken, and by which level of the ladder: --why
                            holds the gate's cite, --said what the personas answered. --option is
                            each option the decision had, "LABEL: what the person sees after it",
                            --vote each persona's answer, one for each model family, and --level
                            what each level that ran answered. `--by personas` takes two votes or
                            more, each for the option --chose names. `--unsettled` goes with `--by
                            lead`: no level settled it, and the lead's pick stands. `owner` is a
                            word of the owner's: his help on breaker N (`--breaker N`, which settles
                            it, with his own words in --words), a word nobody asked for (the task is
                            careful), or his yes to skip the personas' read of criteria that name
                            only the developer, in the form `land.py` reads (`READ_SKIP`); `lem` one
                            that Lem took before the task had a lead. An important decision, `--by
                            dialectic`, `--by experts` or `--unsettled`, carries its story: --case,
                            --case-was and --cause, which any other decision may carry too
    lem decisions criterion SLUG (--changed N --was TEXT --now TEXT | --added N --now TEXT
                 | --removed N --was TEXT) --why TEXT (--decision ID | --by lead|personas [--said TEXT])
                            a change of a criterion the owner approved, with its text before and
                            after: N is its number in the criteria as they stand after every
                            earlier change. --decision names the decision of the record that led
                            to it (a pick of the ladder, or the owner's help on a breaker, which
                            makes the change his); without one, the lead's own change or the
                            personas' clear pick
    lem decisions changes SLUG
                            the approved criteria, each recorded change of them in order, and the
                            criteria they give, which the plan's criteria must be
    lem decisions breaker SLUG --cause irreversible|criteria [--irreversible data|system|person|money]
                 [--document FILE]
                            the circuit breaker: it records the stop with its number, its cause and
                            its document, and writes the task's state `held` with the line
                            `breaker N waits for the owner`. FILE is `breaker.md` of the task
                            directory unless named, a file there in the form of
                            `templates/breaker.md`, which it keeps as `breaker-N.md`: refused
                            without one of its parts, without
                            `handoff.md` beside it, with an uncommitted change of a tracked file
                            in the worktree, while another breaker of the task waits, and for a
                            task that is with its landing or ended
    lem decisions pending [SLUG]
                            the breakers that wait, of one task or of every task (`waiting`): a
                            parked task's under `parked`; a task that is dropped, landed or answered
                            has none waiting, and its breakers are named under `ended`
    lem decisions list SLUG  every decision and breaker of the task, each as it stands now

`--chart FILE`, on `log`, is one mermaid chart of the decision, in a file because a chart's text
does not pass through every shell: the text of the chart, with or without its ```mermaid fence,
kept with its line breaks. A flowchart's node and edge texts are each in double quotes (the owner's
rule for every chart); a file that is empty, longer than CHART_MOST characters, of no chart type
mermaid draws, or a flowchart with a text out of quotes is refused.

The record is `decisions.jsonl` in the task's directory, one line for each thing that happened;
each line is also an event in the log the board draws. A decision and a breaker share one row of
numbers, so "decision 3" and "breaker 4" never name the same line.

A criterion change is a line of the same record, with a number of its own (`change`). It applies
to the newest approval of the criteria (`criteria.json`, which `lem criteria approve` writes) and names
that approval by its number, so a later approval starts from its criteria again, also when its text
is one approved before. `changes` keeps every change in `history`: one that a later approval of
the owner's took over is the owner's, and the pull request shows it as approved by the owner
afterwards. `criterion` computes the criteria as they stand after every earlier change, and refuses a change whose criterion N is not the
text `--was` names: a wrong record never enters. Texts are compared with each run of spaces as
one, as a criterion written over two lines reads; they are kept as typed. A task with no approved
criteria has no criterion changes: its plan's criteria are their one source.

A count decides each level, not a model, and the lead applies it: the script checks one count
only, two persona votes or more, all for the option taken. It reads no answer of an agent, and
it moves another count in only when a real run shows a lead that records a level wrongly.

`--irreversible` names why a later "no" cannot undo the step, by one of four kinds and no other:
`data` (it destroys or rewrites data outside the worktree), `system` (it writes to a system
outside the repository, beyond what the settings already allow, such as the tracker's ticket),
`person` (it sends something to a person), `money` (it spends money). The lead says which; no
code can tell.

The experts are the settings' `seats.experts` whose agent is on this machine (`here` in `lem
project show`): two agents of two model families, or, on a machine with one of the agents, one
expert alone; the owner asked for them as the way out when the owner is not there to answer
(2026-11-16). On the ladder they are its last level, and their pick is logged `--by experts`:
both picked it, or the one expert did. `log --by experts` writes which places answer on this
machine (`advisers`), so that the record says one expert or two. The pull request is not green for
their pick.

Every write reads the record and checks the state under one lock, so two writers never take one
number. A task that is dropped, landed or answered takes no write at all, read under the same lock:
nobody builds it, and its record stays as it ended.
"""

import sys

if sys.version_info < (3, 11):
    # an old python3 must still load this file, so that it can say what it needs and not a traceback
    sys.exit(f"decisions.py: Lem needs Python 3.11 or newer, and this python3 is {sys.version.split()[0]}; put a newer one first on PATH, or run this file with it")

import argparse
import fcntl
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
# How this script calls a sibling: in this process, as one command of it.
sys.dont_write_bytecode = True
sys.path.insert(0, str(SCRIPTS))
import lem_sibling  # noqa: E402
import lem_state  # noqa: E402  (how a JSON-lines file is split into its lines)

# Who took a decision: the lead, a level of the ladder (`stages/ladder.md`), the owner, or Lem.
BY = ("lead", "gate", "personas", "dialectic", "experts", "owner", "lem")
# The task states in which nothing of a task waits any more, as project.py's ENDED.
ENDED = ("dropped", "landed", "answered")
# The states of a task that is with its landing: its build is done, and no breaker stops it there.
WITH_LANDING = ("landing", "open")
# The task state that put a task aside on the owner's word (`/lem park`): its breaker still waits, for nobody now.
PARKED = "parked"
# How the case of a decision is known: the lead ran it, or read it out of the code.
CASE_WAS = ("reproduced", "derived")
# Who took a decision that went past the personas: a log by one of them is important and carries its story.
PAST_PERSONAS = ("dialectic", "experts")
# The longest chart a record keeps, in characters: about a dozen nodes is the form's own bound
# (`prompts/writing.md`), and this is a guess at three times that, not a measurement.
CHART_MOST = 4000
# The first word of a chart mermaid draws (mermaid 11, its diagram types); the record takes no other.
CHART_TYPES = (
    "flowchart", "graph", "sequenceDiagram", "stateDiagram", "stateDiagram-v2", "classDiagram", "erDiagram", "journey",
    "gantt", "pie", "quadrantChart", "requirementDiagram", "gitGraph", "mindmap", "timeline", "sankey-beta", "xychart-beta",
    "block-beta", "packet-beta", "architecture-beta", "kanban", "radar-beta", "C4Context", "C4Container", "C4Component", "C4Dynamic", "C4Deployment",
)
# The two causes of the circuit breaker, and no others: see the text above.
CAUSES = {
    "irreversible": "the next step cannot be reversed by a later no",
    "criteria": "no option of the ladder keeps the outcome the owner approved",
}
# The breaker's document and the handoff beside it, by their names in the task directory. The record keeps
# the document under the breaker's number (`kept_document`), so each breaker of a task has its own.
BREAKER_DOC = "breaker.md"
BREAKER_KEPT = "breaker-{id}.md"
HANDOFF = "handoff.md"
# The parts of the breaker's document, as `templates/breaker.md` has them: each a `## ` heading
# that opens with these words, in any case, and what its text must hold.
BREAKER_PARTS = {
    "today and after": "the run of Today and the run of After, each in numbered steps",
    "the case": "the case that broke, in numbered steps, with its chart in a ```mermaid block",
    "the root cause": "why the case became possible, and how far the same cause reaches",
    "the options": "the options as this or that, in a table, with what each leads to",
    "the recommendation": "the option you would take, and why",
    "the assumptions": "what the document takes as true, one item each",
}
# The state line of a task that a breaker holds, which project.py, session.py and the board read.
BREAKER_WAIT = re.compile(r"breaker ([1-9]\d*) waits for the owner")
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
    # a line project.py writes on stderr when it succeeds (the settings read from the base branch) is this script's to say too
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
        self.status = self.read_status(tasks)
        self.directory = (state or Path(script("project.py", repo, "state-dir").strip())) / "tasks" / slug
        self.file = self.directory / "decisions.jsonl"

    def read_status(self, tasks: list[dict] | None = None) -> str | None:
        """The task's status now, from its state file: a task may be dropped while a command runs."""
        if tasks is None:
            tasks = json.loads(script("project.py", self.repo, "tasks"))
        record = next((task for task in tasks if task["slug"] == self.slug), None)
        if record is None:
            raise DecisionError(f"no task {self.slug!r}; the tasks are: {', '.join(task['slug'] for task in tasks) or 'none yet'}")
        return record["status"]

    def lines(self) -> list[dict]:
        if not self.file.is_file():
            return []
        out = []
        try:
            written = self.file.read_text(encoding="utf-8")
        except UnicodeDecodeError as error:
            raise DecisionError(f"{self.file} is not UTF-8 text (byte {error.start} does not read); the file is written by this script only") from error
        for number, line in enumerate(lem_state.jsonl_lines(written), start=1):
            if line.strip():
                try:
                    out.append(json.loads(line))
                except ValueError as error:
                    raise DecisionError(f"{self.file}:{number} does not read as JSON ({error}); the file is written by this script only") from error
        return out

    def decisions(self) -> list[dict]:
        """Each decision and each breaker as it stands now: its first line, and a breaker with the
        owner's help that settled it (`helped`, by the number of his decision)."""
        found: dict[int, dict] = {}
        for line in self.lines():
            if line["kind"] == "taken":
                found[line["id"]] = {**line, "state": "taken"}
                if "breaker" in line and line["breaker"] in found:
                    found[line["breaker"]].update(state="helped", help=line["id"], helped=line["at"])
            elif line["kind"] == "breaker":
                found[line["id"]] = {**line, "state": "waits"}
        return [found[key] for key in sorted(found)]

    def approved(self) -> dict | None:
        """The criteria the owner approved, as `lem criteria approve` kept them; none for a task without."""
        kept = self.directory / "criteria.json"
        if not kept.is_file():
            return None
        try:
            return json.loads(kept.read_text(encoding="utf-8"))
        except ValueError as error:
            raise DecisionError(f"{kept} does not read as JSON ({error}); it is written by `lem criteria approve` only") from error

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
        newest = approvals[-1]["number"]
        everything = [line for line in (self.lines() if lines is None else lines) if line["kind"] == "criterion"]
        history = []
        for line in everything:
            later = next((old["number"] for old in approvals if old["number"] > line["approval"] and old["by"] == "owner"), None)
            history.append({**line, "taken_over_by": later})
        changes = [line for line in everything if line.get("approval") == newest]
        expected = [whole(criterion) for criterion in approved["criteria"]]
        for change in changes:
            expected = applied(expected, change)
        return {
            "task": self.slug, "approved": {key: approved.get(key) for key in keys} | {"number": newest}, "approvals": approvals,
            "changes": changes, "history": history, "expected": expected,
        }

    def one(self, number: int, known: list[dict] | None = None, kind: str = "taken") -> dict:
        """Decision NUMBER of the record, or breaker NUMBER with `kind="breaker"`."""
        known = self.decisions() if known is None else known
        found = next((d for d in known if d["id"] == number and d["kind"] == kind), None)
        if found is None:
            word = "breaker" if kind == "breaker" else "decision"
            those = [str(d["id"]) for d in known if d["kind"] == kind]
            raise DecisionError(f"no {word} {number} in {self.slug}; its {word}s: {', '.join(those) or 'none'} (`lem decisions list {self.slug}`)")
        return found

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


def text(value: str | None, flag: str) -> str:
    if value is None or not value.strip():
        raise DecisionError(f"{flag} needs its text: one sentence in plain words")
    return " ".join(value.split())


def typed(value: str | None, flag: str) -> str:
    """A criterion's text as typed: two spaces in a literal value stay two."""
    if value is None or not value.strip():
        raise DecisionError(f"{flag} needs the criterion's text, word for word")
    return value.strip()


def whole(criterion: dict) -> str:
    """An approved criterion as `lem criteria` compares it: its sentence and the steps of its case,
    one to a line (criteria.py's `whole`). A change of a step is a change of the criterion."""
    return "\n".join([criterion["text"], *criterion.get("case", [])])


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
    if args.by == "personas" and not votes:
        raise DecisionError("--by personas needs a --vote for each answer of a persona, \"PERSONA, FAMILY=OPTION\", and --said: who answered and what each picked")
    # The one count the script checks (`stages/ladder.md`, level 2).
    if args.by == "personas":
        other = [name for name, option in votes if option != chose]
        if len(votes) < 2 or other:
            raise DecisionError(
                f"the personas settle a decision with two votes or more, all for the option taken ({chose!r}); "
                + (f"{', '.join(other)} voted otherwise" if other else f"this one has {len(votes)}")
                + ": the ladder goes on to the dialectic (`stages/ladder.md`)",
            )
    if args.unsettled and args.by != "lead":
        raise DecisionError("--unsettled is the lead's pick that no level settled: it goes with --by lead")
    breaker = getattr(args, "breaker", None)
    words = getattr(args, "words", None)
    if (breaker is not None or words is not None) and args.by != "owner":
        raise DecisionError("--breaker and --words are the owner's: his help on a breaker, in his own words, goes with --by owner")
    line = {"at": stamp(now()), "kind": "taken", "what": text(args.what, "--what"), "chose": chose, "why": text(args.why, "--why"), "by": args.by}
    important = args.by in PAST_PERSONAS or args.unsettled
    if important or any(value is not None for value in (args.case, args.case_was, args.cause)):
        who = "the lead's pick that no level settled" if args.unsettled else f"a decision --by {args.by}"
        line.update(story(args, f"{who} is important, and carries its story, which the owner reads at the pull request" if important else "a story"))
    if args.by == "experts":
        line["advisers"] = experts_here(task.repo)
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
    if args.chart is not None:
        line["chart"] = chart(args.chart)
    if words is not None:
        line["words"] = text(words, "--words")
    if breaker is not None:
        line["breaker"] = breaker

    def make(known: list[dict]) -> list[dict]:
        if breaker is not None:
            stopped = task.one(breaker, known, "breaker")
            if stopped["state"] != "waits":
                raise DecisionError(f"breaker {breaker} of {task.slug} is helped already, by decision {stopped['help']}: a later word of the owner's is a decision of its own, with no --breaker")
            if task.status == PARKED:
                raise DecisionError(f"{task.slug} is parked: `lem project resume {task.slug}` brings its breaker back first, then his help settles it")
        return [{"id": len(known) + 1, **line}]

    return task.add(make)[0]


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
    if (args.decision is None) == (args.by is None):
        raise DecisionError("a criterion change names --decision ID, the decision of the record that led to it, or --by lead|personas when none did: one of the two")
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
    line = {"at": stamp(now()), "kind": "criterion", "how": how, "criterion": getattr(args, how), "why": text(args.why, "--why"), "approval": approved["number"]}
    for key in wants:
        line[key] = typed(getattr(args, key), f"--{key}")
    if args.decision is not None:
        line["decision"] = args.decision
    else:
        line["by"] = args.by
        if args.said is not None:
            line["said"] = text(args.said, "--said")

    def make(known: list[dict]) -> list[dict]:
        if args.decision is not None:
            # a decision that is on record: a pick of the ladder, or the owner's help on a breaker
            task.one(args.decision, known)
        lines = task.lines()
        # the same computation the check of the criteria makes, with this change last: a wrong record never enters
        task.changes([*lines, line])
        return [{"change": sum(1 for old in lines if old["kind"] == "criterion") + 1, **line}]

    made = task.add(make)[0]
    return {**made, "criteria": task.changes()["expected"]}


def steps(value: str | None) -> str:
    """The case of a decision as typed, one step to a line: two numbered steps at the least."""
    lines = [line.rstrip() for line in (value or "").strip().splitlines() if line.strip()]
    numbered = [line for line in lines if re.match(r"\s*\d+[.)]\s+\S", line)]
    if len(numbered) < 2:
        raise DecisionError(
            "--case is one concrete case that ends badly, in numbered steps, one to a line (\"1. ...\", \"2. ...\"), "
            f"with real names and values and where each step was read; this one has {len(numbered)} numbered step{'' if len(numbered) == 1 else 's'}",
        )
    return "\n".join(lines)


def story(args: argparse.Namespace, what: str | None = None) -> dict:
    """The case of a decision: --case in numbered steps, --case-was, --cause. WHAT names a log's
    story, whose missing fields are named first."""
    missing = [flag for flag, value in (("--case", args.case), ("--case-was", args.case_was), ("--cause", args.cause)) if value is None]
    if missing and what:
        raise DecisionError(
            f"{what}: --case, one concrete run in numbered steps, one to a line, --case-was reproduced|derived, and --cause, one line on why it "
            f"became possible and how far that reaches (`prompts/writing.md`); this one has no {', no '.join(missing)}",
        )
    case = steps(args.case)
    if args.case_was not in CASE_WAS:
        raise DecisionError(f"--case-was says how the case is known: {' or '.join(CASE_WAS)}")
    return {"case": case, "case_was": args.case_was, "cause": text(args.cause, "--cause")}


def chart(file: str) -> str:
    """The text of one mermaid chart, from FILE, with its line breaks and without its fence."""
    source = Path(file)
    if not source.is_file():
        raise DecisionError(f"--chart names a file that holds one mermaid chart, and {file} is not a file; write the chart into a file first")
    try:
        written = source.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise DecisionError(f"{file} is not UTF-8 text (byte {error.start} does not read); write the chart in UTF-8") from error
    rows = written.strip("\n").splitlines()
    fence = re.match(r"\s*(`{3,}|~{3,})\s*(\w*)\s*$", rows[0]) if rows else None
    if fence:
        if fence.group(2) not in ("", "mermaid"):
            raise DecisionError(f"{file} holds a ```{fence.group(2)} block, and --chart takes one mermaid chart: its text, or its text in a ```mermaid fence")
        rows = rows[1:]
        if rows and rows[-1].strip() == fence.group(1):
            rows = rows[:-1]
    body = "\n".join(row.rstrip() for row in rows).strip("\n")
    if not body.strip():
        raise DecisionError(f"{file} holds no chart: --chart takes one mermaid chart, its text or its text in a ```mermaid fence")
    if len(body) > CHART_MOST:
        raise DecisionError(f"the chart in {file} has {len(body)} characters, and a record keeps {CHART_MOST} at the most: one chart for one idea, about a dozen nodes (`prompts/writing.md`)")
    head = chart_type(body)
    if head not in CHART_TYPES:
        raise DecisionError(f"the chart in {file} opens with {head!r}, which is no chart type mermaid draws; it opens with one of them, as `flowchart TD` or `sequenceDiagram`")
    if head in ("flowchart", "graph"):
        bare = unquoted(body)
        if bare:
            raise DecisionError(
                f"the chart in {file} has a text out of double quotes, {bare!r}: every node's and edge's text of a flowchart is in double quotes, "
                'as A["The total shows 0"] -->|"yes"| B["A credit note"]',
            )
    return body


def chart_type(body: str) -> str:
    """The first word of a chart, after its front matter and its `%%` lines."""
    rows = body.splitlines()
    if rows and rows[0].strip() == "---":
        ends = next((i for i in range(1, len(rows)) if rows[i].strip() == "---"), len(rows) - 1)
        rows = rows[ends + 1:]
    first = next((row.strip() for row in rows if row.strip() and not row.strip().startswith("%%")), "")
    return first.split()[0] if first else ""


# The rows of a flowchart that hold no node's or edge's text, by their first word.
NO_TEXT = ("flowchart", "graph", "classDef", "class", "style", "linkStyle", "click", "direction", "subgraph", "end")
# A node's shape opening right after its id, and an edge's text between pipes or between `--` and its arrow.
SHAPE = re.compile(r"[A-Za-z0-9_]+(\[\[|\[\(|\(\[|\(\(\(|\(\(|\{\{|\[/|\[\\|\[|\(|\{|>)")
PIPED = re.compile(r"\|([^|]*)\|")
SPOKEN = re.compile(r"(?<![-=])(?:--|==)\s+([^\s\->=][^>]*?)\s+(?:-->|==>|---|===)")


def unquoted(body: str) -> str | None:
    """The first node or edge text of a flowchart that is not in double quotes; none when each is.
    A check of the common forms, not a parser: it reads a row with its quoted texts taken out."""
    rows = body.splitlines()
    # the rows after the one that names the chart's type: front matter before it holds no node
    start = next(i for i, row in enumerate(rows) if row.split()[:1] and row.split()[0] in ("flowchart", "graph"))
    for row in rows[start + 1:]:
        words = row.split()
        if not words or words[0] in NO_TEXT or words[0].startswith("%%"):
            continue
        bare = re.sub(r'"[^"]*"', '""', row)
        for found in SHAPE.finditer(bare):
            after = bare[found.end():].lstrip()
            if not after.startswith('"'):
                return row.strip()
        for found in [*PIPED.finditer(bare), *SPOKEN.finditer(bare)]:
            if found.group(1).strip() != '""':
                return row.strip()
    return None


def experts_here(repo: Path) -> list[str]:
    """The places of the settings' experts whose agent is on this machine: both, or the one that can
    answer (`here` in `lem project show`)."""
    found = [expert["place"] for expert in json.loads(script("project.py", repo, "show"))["seats"]["experts"] if expert.get("here", True)]
    if not found:
        raise DecisionError("no expert of the settings' seats.experts can answer on this machine: name a seat of an agent it has, as experts = [\"claude/fable:high\"]")
    return found


def breaker_document(file: Path) -> str:
    """The title of a breaker's document, after a check of its parts (BREAKER_PARTS); refused with
    each part it lacks, so the owner never reads a bare question."""
    try:
        written = file.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise DecisionError(f"{file} is not UTF-8 text (byte {error.start} does not read); write it in UTF-8") from error
    title = next((line[2:].strip() for line in written.splitlines() if line.startswith("# ")), None)
    sections: dict[str, list[str]] = {}
    current = None
    for line in written.splitlines():
        if line.startswith("## "):
            head = " ".join(line[3:].lower().split())
            current = next((part for part in BREAKER_PARTS if head.startswith(part)), None)
            if current is not None:
                sections.setdefault(current, [])
        elif current is not None:
            sections[current].append(line)
    missing = []
    for part, holds in BREAKER_PARTS.items():
        body = "\n".join(sections.get(part, []))
        numbered = len(re.findall(r"(?m)^\s*\d+[.)]\s+\S", body))
        lacks = (
            part not in sections or not body.strip()
            or (part == "today and after" and (numbered < 2 or not re.search(r"\btoday\b", body, re.I) or not re.search(r"\bafter\b", body, re.I)))
            or (part == "the case" and (numbered < 2 or "```mermaid" not in body))
            or (part == "the options" and len([row for row in body.splitlines() if row.strip().startswith("|")]) < 3)
            or (part == "the assumptions" and not re.search(r"(?m)^\s*(?:[-*]|\d+[.)])\s+\S", body))
        )
        if lacks:
            missing.append(f"## {part[0].upper()}{part[1:]} ({holds})")
    if not title:
        missing.insert(0, "a first line `# ` that says what stopped the task, in one sentence")
    if missing:
        raise DecisionError(
            f"{file} is no breaker's document yet: it lacks " + "; ".join(missing)
            + ". `templates/breaker.md` of the skill is its form: the owner reads it far from the task, so it brings the context back",
        )
    return " ".join(title.split())


def kept_document(document: Path, number: int) -> str:
    """Keep the breaker's document under its number, `breaker-N.md` beside it, and give that name: the
    agent writes `breaker.md` each time, and a later breaker of the task never writes over this one's."""
    kept = document.with_name(BREAKER_KEPT.format(id=number))
    document.replace(kept)
    return kept.name


def cmd_breaker(task: Task, args: argparse.Namespace) -> dict:
    """The circuit breaker: record it with its cause and its document, then hold the task."""
    if args.cause == "irreversible" and args.irreversible is None:
        raise DecisionError("--cause irreversible names its kind: --irreversible data|system|person|money")
    if args.cause != "irreversible" and args.irreversible is not None:
        raise DecisionError("--irreversible goes with --cause irreversible; the cause criteria is a rule of an approved criterion that no option keeps")
    if task.status in WITH_LANDING:
        raise DecisionError(f"{task.slug} is {task.status}: its build is done, and no breaker stops a landing. A step of the landing that only the owner may take is his word, as `stages/land.md` says")
    document = Path(args.document) if args.document else task.directory / BREAKER_DOC
    if not document.is_absolute():
        document = Path.cwd() / document
    if not document.is_file():
        raise DecisionError(f"{document} is not a file: write the breaker's document first, {BREAKER_DOC} in the task directory, in the form of `templates/breaker.md`")
    if document.resolve().parent != task.directory.resolve():
        raise DecisionError(f"{document} is not in the task directory {task.directory}: the board and a fresh agent read the breaker's document there")
    title = breaker_document(document)
    handoff = task.directory / HANDOFF
    if not handoff.is_file() or not handoff.read_text(encoding="utf-8").strip():
        raise DecisionError(
            f"{handoff} is missing: the agent that stops writes the handoff beside the document (what is settled, what is open, the next step, "
            "what was tried and failed), so that a fresh agent goes on from it a week later",
        )
    dirty = subprocess.run(["git", "-C", str(task.repo), "status", "--porcelain", "--untracked-files=no"], capture_output=True, text=True, check=False)
    if dirty.returncode == 0 and dirty.stdout.strip():
        raise DecisionError(
            f"the worktree {task.repo} has uncommitted changes of tracked files ({len(dirty.stdout.splitlines())}): commit what the task has first, "
            "since a dropped task's worktree goes and only its branch stays",
        )
    line = {"at": stamp(now()), "kind": "breaker", "cause": args.cause, "what": title, "handoff": HANDOFF}
    if args.irreversible:
        line["irreversible"] = args.irreversible

    def make(known: list[dict]) -> list[dict]:
        waiting = next((d for d in known if d["kind"] == "breaker" and d["state"] == "waits"), None)
        if waiting:
            raise DecisionError(f"breaker {waiting['id']} of {task.slug} waits for the owner already: one breaker holds a task at a time, and its document says it")
        number = len(known) + 1
        return [{"id": number, **line, "document": kept_document(document, number)}]

    made = task.add(make)[0]
    why = CAUSES[args.cause] + (f" ({IRREVERSIBLE[args.irreversible]})" if args.irreversible else "")
    script("project.py", task.repo, "state", task.slug, "held", f"breaker {made['id']} waits for the owner", f"{title}: {why}")
    return {**made, "next": "the task stops here, and the other tasks build on. Stop as `stages/build.md` ends: the report, then your reply; "
                            "Lem puts the document to the owner, who helps, parks the task or drops it"}


def shown(task: Task, decision: dict) -> dict:
    return {"task": task.slug, **{key: value for key, value in decision.items() if key != "kind"}, "kind": decision["kind"]}


def cmd_pending(repo: Path, slug: str | None) -> dict:
    """The breakers that wait for the owner. A parked task's wait for nobody now; a dropped, landed or
    answered task has none: nobody builds it, and the record stays for `list`."""
    # Every task, from one read of the tasks and of the state folder: nothing here writes either.
    listed = json.loads(script("project.py", repo, "tasks")) if not slug else None
    state = Path(script("project.py", repo, "state-dir").strip()) if listed else None
    slugs = [slug] if slug else [task["slug"] for task in listed]
    out: dict[str, list[dict]] = {"waiting": [], "parked": [], "ended": []}
    for task in (Task(repo, name, listed, state) for name in slugs):
        open_ones = [d for d in task.decisions() if d["kind"] == "breaker" and d["state"] == "waits"]
        if task.status in ENDED:
            if open_ones or slug:
                out["ended"].append({"task": task.slug, "status": task.status, "breakers": [d["id"] for d in open_ones],
                                     "says": f"the task is {task.status}: its breakers no longer wait for anybody"})
        else:
            out["parked" if task.status == PARKED else "waiting"] += [{**shown(task, d), "status": task.status} for d in open_ones]
    return out


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
    log.add_argument("--option", action="append", metavar="TEXT", help="each option the decision had, word for word, as \"LABEL: what the person sees after it\"")
    log.add_argument("--vote", action="append", metavar="PERSONA, FAMILY=OPTION", help="one persona's answer in one model family")
    log.add_argument("--level", action="append", metavar="NAME=ANSWER", help="what one level of the ladder answered")
    log.add_argument("--unsettled", action="store_true", help="with --by lead: no level settled it, and the lead's pick stands")
    log.add_argument("--case", metavar="STEPS", help="one concrete run in numbered steps, one to a line: required --by dialectic, --by experts and with --unsettled")
    log.add_argument("--case-was", metavar="HOW", help="reproduced, or derived from the code")
    log.add_argument("--cause", help="one line: why the case became possible, and how far the same cause reaches")
    log.add_argument("--chart", metavar="FILE", help="a file that holds one mermaid chart of the decision")
    log.add_argument("--breaker", type=int, metavar="N", help="with --by owner: his help on breaker N, which settles it")
    log.add_argument("--words", help="with --by owner: his words as given, when they are not the --chose text")
    criterion = commands.add_parser("criterion")
    criterion.add_argument("slug")
    criterion.add_argument("--changed", type=int, metavar="N", help="criterion N changed: --was is its text before, --now its text after")
    criterion.add_argument("--added", type=int, metavar="N", help="a criterion the build adds at number N, with --now its text")
    criterion.add_argument("--removed", type=int, metavar="N", help="criterion N leaves the criteria, with --was its text")
    criterion.add_argument("--was", help="the criterion's text before the change, word for word")
    criterion.add_argument("--now", help="the criterion's text after the change, word for word")
    criterion.add_argument("--why", required=True, help="why the criterion changed, in one sentence")
    criterion.add_argument("--decision", type=int, metavar="ID", help="the decision of the record that led to the change")
    criterion.add_argument("--by", choices=("lead", "personas"), help="who changed it, when no decision of the record did")
    criterion.add_argument("--said", help="with --by personas: who answered and what each picked")
    commands.add_parser("changes").add_argument("slug")
    breaker = commands.add_parser("breaker", help="the circuit breaker: record the stop with its cause and its document, and hold the task")
    breaker.add_argument("slug")
    breaker.add_argument("--cause", required=True, choices=tuple(CAUSES), help="the next step cannot be reversed, or no option keeps the approved criteria")
    breaker.add_argument("--irreversible", choices=tuple(IRREVERSIBLE), help="with --cause irreversible: why a later \"no\" cannot undo the step")
    breaker.add_argument("--document", metavar="FILE", help=f"the breaker's document, {BREAKER_DOC} of the task directory unless named")
    pending = commands.add_parser("pending")
    pending.add_argument("slug", nargs="?")
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
        if args.command == "pending":
            result: object = cmd_pending(repo, args.slug)
        else:
            task = Task(repo, args.slug)
            if args.command == "log":
                result = cmd_log(task, args)
            elif args.command == "criterion":
                result = cmd_criterion(task, args)
            elif args.command == "changes":
                result = task.changes()
            elif args.command == "breaker":
                result = cmd_breaker(task, args)
            else:
                result = [shown(task, decision) for decision in task.decisions()]
    except DecisionError as error:
        sys.exit(f"decisions.py: {error}")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
