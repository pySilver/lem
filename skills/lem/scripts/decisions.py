#!/usr/bin/env python3
"""The decisions of one task: each one taken without the owner, and each choice that went to him.

A build meets choices its plan did not see. Most are the lead's own: the stories stay true, so
the lead decides and writes the decision down. A choice that changes a story, or whose options
each cost a person something, goes to the personas first; a clear answer of theirs is taken and
written down. Only an unclear one goes to the owner, and it waits for him a fixed time and no
longer: after that the recommended action is taken, and the pull request is not green for it.
One kind of step never goes that way: a step that a later "no" cannot reverse waits for his word
however long that takes.

    decisions.py log SLUG --what TEXT --chose TEXT --why TEXT --by lead|personas|owner|lem
                 [--said TEXT] [--undo TEXT]
                            a decision that was taken; --said is what the personas answered.
                            `owner` is a word of his that nobody asked for (the task is careful),
                            `lem` one that Lem took before the task had a lead (out of scope)
    decisions.py story SLUG (--changed N --was TEXT --now TEXT | --added N --now TEXT
                 | --removed N --was TEXT) --why TEXT (--choice ID | --by lead|personas [--said TEXT])
                            a change of a story the owner approved, with its text before and
                            after: N is its number in the stories as they stand after every
                            earlier change. --choice names the choice of the build that led to
                            it, answered or taken by timeout; without one, the lead's own change
                            or the personas' clear pick
    decisions.py changes SLUG
                            the approved stories, each recorded change of them in order, and the
                            stories they give, which the plan's stories must be
    decisions.py ask SLUG --what TEXT --option TEXT --option TEXT [...] --recommended TEXT
                 --why TEXT --said TEXT [--irreversible data|system|person|money]
                            a choice for the owner: it gets a number and the time its wait ends
    decisions.py pending [SLUG]
                            the choices that wait, of one task or of every task, each with the
                            seconds its wait has left (`waiting`). A task that is dropped or
                            landed has none: its choices that never got an answer are named
                            under `ended`, with the task's status, and need no answer
    decisions.py wait SLUG ID [--seconds N]
                            return when the choice is answered, when its wait ends, or after N
                            seconds, and say which
    decisions.py answer SLUG ID --chose OPTION [--words TEXT] [--why TEXT]
                            the owner's answer: the option it takes, word for word, his own
                            words when they are not that text, and his reason when he gave one.
                            Lem writes it down. Text that is no option is refused here
    decisions.py answer SLUG ID --instead TEXT [--words TEXT] [--why TEXT]
                            the owner decided what none of the options says: TEXT settles the
                            choice, an irreversible one too
    decisions.py timeout SLUG ID
                            the wait ended with no answer: the recommended action is taken.
                            Refused while the wait runs, and always for an irreversible step
    decisions.py list SLUG  every decision of the task, each as it stands now

The record is `decisions.jsonl` in the task's directory, one line for each thing that happened;
a decision is the lines with its number. Each line is also an event in the log the board draws.

A story change is a line of the same record, with a number of its own (`change`). It applies to
the stories the owner approved (`stories.json`, which `stories.py approve` writes) and names
their digest, so a later approval of his starts from his stories again. `story` computes the
stories as they stand after every earlier change, and refuses a change whose story N is not the
text `--was` names: a wrong record never enters. Texts are compared with each run of spaces as
one, as a story written over two lines reads; they are kept as typed. A choice carries no story:
when the option taken changes one, the lead records that with `story --choice ID`, and the
stories' check refuses the plan until it does. A task with no approved stories has no story
changes: its plan's stories are their one source.

The wait is the settings' `flow.decision_wait`, in minutes. Its default, 15, is the owner's own
number ("if there is decision taken in 15 min", 2026-11-16). `--said` is not optional for `ask`:
the personas answer before the owner is asked, and their answers go to him with the question.

`--irreversible` names why a later "no" cannot undo the step, by one of four kinds and no other:
`data` (it destroys or rewrites data outside the worktree), `system` (it writes to a system
outside the repository, beyond what the settings already allow, such as the tracker's ticket),
`person` (it sends something to a person), `money` (it spends money). The lead says which; no
code can tell.

An answer that comes after the wait is written down as late, also when nobody wrote the timeout
yet: then the timeout and the late answer are written together. The recommended action stands;
when the answer differs from it, that is a correction, for the lead while the task builds and a
new ask after that.

Every write reads the record and checks the state under one lock, so an answer and a timeout that
come at one time leave one outcome, and two writers never take one number.
"""

from __future__ import annotations

import sys

if sys.version_info < (3, 11):
    # an old python3 must still load this file, so that it can say what it needs and not a traceback
    sys.exit(f"decisions.py: Lem needs Python 3.11 or newer, and this python3 is {sys.version.split()[0]}; put a newer one first on PATH, or run this file with it")

import argparse
import fcntl
import json
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
BY = ("lead", "personas", "owner", "lem")
# The task states in which nothing of a task waits any more.
ENDED = ("dropped", "landed")
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
    ran = subprocess.run([sys.executable, "-B", str(SCRIPTS / name), "--repo", str(repo), *args], capture_output=True, text=True, check=False)
    if ran.returncode != 0:
        raise DecisionError(ran.stderr.strip().removeprefix(f"{name}: ") or f"{name} {args[0]} failed")
    return ran.stdout


def now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def stamp(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def read(moment: str) -> datetime:
    return datetime.strptime(moment, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


class Task:
    def __init__(self, repo: Path, slug: str) -> None:
        self.repo = repo
        self.slug = slug
        self.status = self.read_status()
        self.directory = Path(script("project.py", repo, "state-dir").strip()) / "tasks" / slug
        self.file = self.directory / "decisions.jsonl"

    def read_status(self) -> str | None:
        """The task's status now, from its state file: a task may be dropped while a command runs."""
        tasks = json.loads(script("project.py", self.repo, "tasks"))
        record = next((task for task in tasks if task["slug"] == self.slug), None)
        if record is None:
            raise DecisionError(f"no task {self.slug!r}; the tasks are: {', '.join(task['slug'] for task in tasks) or 'none yet'}")
        return record["status"]

    def lines(self) -> list[dict]:
        if not self.file.is_file():
            return []
        out = []
        for number, line in enumerate(self.file.read_text(encoding="utf-8").splitlines(), start=1):
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
            elif line["kind"] == "timeout":
                found[line["id"]].update(state="timeout", chose=line["chose"], by="timeout", taken=line["at"])
            elif line["kind"] == "late":
                found[line["id"]].update(late={"chose": line["chose"], "at": line["at"], **{key: line[key] for key in ("words", "why", "instead") if key in line}})
        return [found[key] for key in sorted(found)]

    def approved(self) -> dict | None:
        """The stories the owner approved, as `stories.py approve` kept them; none for a task without."""
        kept = self.directory / "stories.json"
        if not kept.is_file():
            return None
        try:
            return json.loads(kept.read_text(encoding="utf-8"))
        except ValueError as error:
            raise DecisionError(f"{kept} does not read as JSON ({error}); it is written by `stories.py approve` only") from error

    def changes(self, lines: list[dict] | None = None) -> dict:
        """The approved stories, the recorded changes of them in order, and the stories they give.
        A change made under an earlier approval is his no longer: his later approval replaced it."""
        approved = self.approved()
        if approved is None:
            return {"task": self.slug, "approved": None, "changes": [], "expected": None}
        changes = [line for line in (self.lines() if lines is None else lines) if line["kind"] == "story" and line["approved"] == approved["digest"]]
        expected = [story["text"] for story in approved["stories"]]
        for change in changes:
            expected = applied(expected, change)
        return {
            "task": self.slug, "approved": {key: approved[key] for key in ("at", "by", "kind", "digest")},
            "changes": changes, "expected": expected,
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
        as an event. `make` refuses by raising, and then nothing is written."""
        self.directory.mkdir(parents=True, exist_ok=True)
        with (self.directory / "decisions.lock").open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            lines = make(self.decisions())
            with self.file.open("a", encoding="utf-8") as handle:
                handle.write("".join(json.dumps(line) + "\n" for line in lines))
        for line in lines:
            script("project.py", self.repo, "log", self.slug, f"decision.{line['kind']}", *(f"{key}:={json.dumps(value)}" for key, value in line.items() if key != "kind"))
        return lines


def left(decision: dict) -> int:
    return int((read(decision["deadline"]) - now()).total_seconds())


def text(value: str | None, flag: str) -> str:
    if value is None or not value.strip():
        raise DecisionError(f"{flag} needs its text: one sentence in plain words")
    return " ".join(value.split())


def typed(value: str | None, flag: str) -> str:
    """A story's text as typed: two spaces in a literal value stay two."""
    if value is None or not value.strip():
        raise DecisionError(f"{flag} needs the story's text, word for word")
    return value.strip()


def same(one: str, other: str) -> bool:
    """Two texts of a story are the same when they differ only in runs of spaces, as a story
    written over two lines reads as one line with one space."""
    return one.split() == other.split()


def applied(stories: list[str], change: dict) -> list[str]:
    """The stories after one change; a change whose story N is not the text it names is refused."""
    number, out = change["story"], list(stories)
    if change["how"] == "added":
        if not 1 <= number <= len(out) + 1:
            raise DecisionError(f"an added story goes at a number from 1 to {len(out) + 1}, and this one is {number}")
        out.insert(number - 1, change["now"])
        return out
    if not 1 <= number <= len(out):
        raise DecisionError(f"there is no story {number}: the stories are 1 to {len(out)} after every earlier change")
    if not same(out[number - 1], change["was"]):
        raise DecisionError(f"story {number} is {out[number - 1]!r} after every earlier change, and --was says {change['was']!r}; `decisions.py changes SLUG` gives the stories as they stand")
    if change["how"] == "changed":
        out[number - 1] = change["now"]
    else:
        out.pop(number - 1)
    return out


def cmd_log(task: Task, args: argparse.Namespace) -> dict:
    if args.by == "personas" and not args.said:
        raise DecisionError("--by personas needs --said: who answered and what each picked, in one or two sentences")
    line = {"at": stamp(now()), "kind": "taken", "what": text(args.what, "--what"), "chose": text(args.chose, "--chose"), "why": text(args.why, "--why"), "by": args.by}
    for key in ("said", "undo"):
        # an empty value is refused, never dropped
        if getattr(args, key) is not None:
            line[key] = text(getattr(args, key), f"--{key}")
    return task.add(lambda known: [{"id": len(known) + 1, **line}])[0]


def cmd_story(task: Task, args: argparse.Namespace) -> dict:
    """Record one change of an approved story, checked against the stories as they stand."""
    how = [name for name in ("changed", "added", "removed") if getattr(args, name) is not None]
    if len(how) != 1:
        raise DecisionError("a story change is one of --changed N, --added N or --removed N")
    how = how[0]
    wants = {"changed": ("was", "now"), "added": ("now",), "removed": ("was",)}[how]
    for key in ("was", "now"):
        if key in wants and getattr(args, key) is None:
            raise DecisionError(f"--{how} needs --{key}: the story's text {'before' if key == 'was' else 'after'} the change, word for word")
        if key not in wants and getattr(args, key) is not None:
            raise DecisionError(f"--{how} takes no --{key}: " + ("an added story had no text before" if how == "added" else "a removed story has no text after"))
    if (args.choice is None) == (args.by is None):
        raise DecisionError("a story change names --choice ID, the choice of the build that led to it, or --by lead|personas when no choice did: one of the two")
    if args.by == "personas" and not args.said:
        raise DecisionError("--by personas needs --said: who answered and what each picked, in one or two sentences")
    if args.said is not None and args.by != "personas":
        raise DecisionError("--said is what the personas answered: it goes with --by personas")
    approved = task.approved()
    if approved is None:
        raise DecisionError(
            f"{task.slug} has no approved stories, so no change of them is recorded: its plan's stories are their one source. "
            "Approved stories are kept by `stories.py approve`",
        )
    line = {"at": stamp(now()), "kind": "story", "how": how, "story": getattr(args, how), "why": text(args.why, "--why"), "approved": approved["digest"]}
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
            if choice["state"] not in ("answered", "timeout"):
                raise DecisionError(f"choice {args.choice} is {choice['state']}: a story changes after a choice that was answered or taken by timeout")
        lines = task.lines()
        # the same computation the stories' check makes, with this change last: a wrong record never enters
        task.changes([*lines, line])
        return [{"change": sum(1 for old in lines if old["kind"] == "story") + 1, **line}]

    made = task.add(make)[0]
    return {**made, "stories": task.changes()["expected"]}


def cmd_ask(task: Task, args: argparse.Namespace) -> dict:
    options = [text(option, "--option") for option in args.option or []]
    if len(options) < 2:
        raise DecisionError("a choice has two options or more: --option for each")
    recommended = text(args.recommended, "--recommended")
    if recommended not in options:
        raise DecisionError(f"--recommended is one of the options, word for word: {'; '.join(options)}")
    wait = json.loads(script("project.py", task.repo, "show"))["flow"]["decision_wait"]
    asked = now()
    line = {
        "at": stamp(asked), "kind": "asked", "what": text(args.what, "--what"), "options": options, "recommended": recommended,
        "why": text(args.why, "--why"), "said": text(args.said, "--said"), "irreversible": args.irreversible,
        "wait_minutes": wait, "deadline": stamp(asked + timedelta(minutes=wait)),
    }
    made = task.add(lambda known: [{"id": len(known) + 1, **line}])[0]
    return {**made, "next": (
        "this step waits for the owner's word, however long: the rest of the plan goes on, and no timeout takes it" if args.irreversible
        else f"tell Lem that choice {made['id']} of {task.slug} waits; go on with what does not depend on it; `decisions.py wait {task.slug} {made['id']}` says when it is answered or its wait ends"
    )}


def shown(task: Task, decision: dict) -> dict:
    out = {"task": task.slug, **{key: value for key, value in decision.items() if key != "kind"}}
    if decision["kind"] == "asked" and decision["state"] == "waits":
        out["seconds_left"] = None if decision["irreversible"] else max(0, left(decision))
    return out


def cmd_pending(repo: Path, slug: str | None) -> dict:
    """The choices that wait for the owner. A dropped or landed task has none: nobody needs his
    answer there, and the record stays for `list`."""
    slugs = [slug] if slug else [task["slug"] for task in json.loads(script("project.py", repo, "tasks"))]
    waiting: list[dict] = []
    ended: list[dict] = []
    for task in (Task(repo, name) for name in slugs):
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
            return {**shown(task, decision), "ended": "answered" if decision["state"] == "answered" else "taken by timeout"}
        if task.status in ENDED:
            return {**shown(task, decision), "ended": f"the task is {task.status}: the choice no longer waits", "status": task.status}
        if not decision["irreversible"] and left(decision) <= 0:
            return {**shown(task, decision), "ended": "the wait is over", "next": f"`decisions.py timeout {task.slug} {number}` takes the recommended action"}
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
                "Put the owner's own words in --words. When what he decided fits none of them, settle the choice with "
                "--instead TEXT, never with a new `decisions.py log`, so it does not wait for ever",
            )
        if decision["state"] == "waits" and (decision["irreversible"] or left(decision) > 0):
            return [{"id": number, "at": at, "kind": "answered", "chose": chose, **reason}]
        # After the wait the recommended option stands. When nobody wrote the timeout yet, it is
        # written here with the answer, in the same write, so nothing reads one without the other.
        lines = [] if decision["state"] == "timeout" else [{"id": number, "at": at, "kind": "timeout", "chose": decision["recommended"]}]
        taken.update(chose=decision["chose"] if decision["state"] == "timeout" else decision["recommended"], timeout_written=bool(lines))
        return [*lines, {"id": number, "at": at, "kind": "late", "chose": chose, **reason}]

    made = task.add(make)[-1]
    if made["kind"] == "answered":
        return made
    return {**made, "state": "timeout", "taken": taken["chose"], "timeout_written": taken["timeout_written"], "next": (
        "the answer is the action that was taken: nothing more to do" if chose == taken["chose"]
        else "the recommended action was taken when the wait ended, and the answer differs: it is a correction. Tell the lead while the task builds; after that it is a new ask"
    )}


def cmd_timeout(task: Task, number: int) -> dict:
    def make(known: list[dict]) -> list[dict]:
        decision = task.one(number, known)
        if decision["state"] != "waits":
            raise DecisionError(f"choice {number} does not wait: it is {decision['state']}, with {decision['chose']!r}")
        if decision["irreversible"]:
            raise DecisionError(
                f"choice {number} is a step that a later \"no\" cannot reverse ({IRREVERSIBLE[decision['irreversible']]}): "
                "no timeout takes it. It waits for the owner's word, and the rest of the plan goes on",
            )
        if left(decision) > 0:
            raise DecisionError(f"the wait of choice {number} has {left(decision)} seconds left (until {decision['deadline']}); the owner may still answer")
        return [{"id": number, "at": stamp(now()), "kind": "timeout", "chose": decision["recommended"]}]

    return task.add(make)[0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=".", help="a directory inside the checkout (default: the current one)")
    commands = parser.add_subparsers(dest="command", required=True)
    log = commands.add_parser("log")
    log.add_argument("slug")
    for flag in ("--what", "--chose", "--why"):
        log.add_argument(flag, required=True)
    log.add_argument("--by", required=True, choices=BY)
    log.add_argument("--said", help="what the personas answered: who, which option, in one or two sentences")
    log.add_argument("--undo", help="what it would take to undo the decision")
    story = commands.add_parser("story")
    story.add_argument("slug")
    story.add_argument("--changed", type=int, metavar="N", help="story N changed: --was is its text before, --now its text after")
    story.add_argument("--added", type=int, metavar="N", help="a story the build adds at number N, with --now its text")
    story.add_argument("--removed", type=int, metavar="N", help="story N leaves the stories, with --was its text")
    story.add_argument("--was", help="the story's text before the change, word for word")
    story.add_argument("--now", help="the story's text after the change, word for word")
    story.add_argument("--why", required=True, help="why the story changed, in one sentence")
    story.add_argument("--choice", type=int, metavar="ID", help="the choice of the build that led to the change")
    story.add_argument("--by", choices=("lead", "personas"), help="who changed it, when no choice did")
    story.add_argument("--said", help="with --by personas: who answered and what each picked")
    commands.add_parser("changes").add_argument("slug")
    ask = commands.add_parser("ask")
    ask.add_argument("slug")
    ask.add_argument("--what", required=True)
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
    answer.add_argument("--words", help="the owner's answer as he gave it, when it is not the option's text")
    answer.add_argument("--why", help="the owner's own reason, in his words, when he gave one; never the recommendation's")
    timeout = commands.add_parser("timeout")
    timeout.add_argument("slug")
    timeout.add_argument("id", type=int)
    commands.add_parser("list").add_argument("slug")
    args = parser.parse_args()
    repo = Path(args.repo)
    try:
        if args.command == "pending":
            result: object = cmd_pending(repo, args.slug)
        else:
            task = Task(repo, args.slug)
            if args.command == "log":
                result = cmd_log(task, args)
            elif args.command == "story":
                result = cmd_story(task, args)
            elif args.command == "changes":
                result = task.changes()
            elif args.command == "ask":
                result = cmd_ask(task, args)
            elif args.command == "wait":
                result = cmd_wait(task, args.id, args.seconds)
            elif args.command == "answer":
                result = cmd_answer(task, args.id, args)
            elif args.command == "timeout":
                result = cmd_timeout(task, args.id)
            else:
                result = [shown(task, decision) for decision in task.decisions()]
    except DecisionError as error:
        sys.exit(f"decisions.py: {error}")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
