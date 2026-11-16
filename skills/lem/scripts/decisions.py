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
                 [--said TEXT] [--undo TEXT] [--story N --was TEXT]
                            a decision that was taken; --said is what the personas answered,
                            and --story with --was is the story it changed, with its old text.
                            `owner` is a word of his that nobody asked for (the task is careful),
                            `lem` one that Lem took before the task had a lead (out of scope)
    decisions.py ask SLUG --what TEXT --option TEXT --option TEXT [...] --recommended TEXT
                 --why TEXT --said TEXT [--irreversible data|system|person|money]
                            a choice for the owner: it gets a number and the time its wait ends
    decisions.py pending [SLUG]
                            the choices that wait, of one task or of every task, each with the
                            seconds its wait has left
    decisions.py wait SLUG ID [--seconds N]
                            return when the choice is answered, when its wait ends, or after N
                            seconds, and say which
    decisions.py answer SLUG ID --chose TEXT
                            the owner's answer, in his words; Lem writes it down
    decisions.py timeout SLUG ID
                            the wait ended with no answer: the recommended action is taken.
                            Refused while the wait runs, and always for an irreversible step
    decisions.py list SLUG  every decision of the task, each as it stands now

The record is `decisions.jsonl` in the task's directory, one line for each thing that happened;
a decision is the lines with its number. Each line is also an event in the log the board draws.

The wait is the settings' `flow.decision_wait`, in minutes. Its default, 15, is the owner's own
number ("if there is decision taken in 15 min", 2026-11-16). `--said` is not optional for `ask`:
the personas answer before the owner is asked, and their answers go to him with the question.

`--irreversible` names why a later "no" cannot undo the step, by one of four kinds and no other:
`data` (it destroys or rewrites data outside the worktree), `system` (it writes to a system
outside the repository, beyond what the settings already allow, such as the tracker's ticket),
`person` (it sends something to a person), `money` (it spends money). The lead says which; no
code can tell.

An answer that comes after the timeout is written down as late. The recommended action stands;
when the answer differs from it, that is a correction, for the lead while the task builds and a
new ask after that.
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
        tasks = json.loads(script("project.py", repo, "tasks"))
        if not any(task["slug"] == slug for task in tasks):
            raise DecisionError(f"no task {slug!r}; the tasks are: {', '.join(task['slug'] for task in tasks) or 'none yet'}")
        self.directory = Path(script("project.py", repo, "state-dir").strip()) / "tasks" / slug
        self.file = self.directory / "decisions.jsonl"

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
                found[line["id"]].update(state="answered", chose=line["chose"], by="owner", answered=line["at"])
            elif line["kind"] == "timeout":
                found[line["id"]].update(state="timeout", chose=line["chose"], by="timeout", taken=line["at"])
            elif line["kind"] == "late":
                found[line["id"]].update(late={"chose": line["chose"], "at": line["at"]})
        return [found[key] for key in sorted(found)]

    def one(self, number: int) -> dict:
        decision = next((d for d in self.decisions() if d["id"] == number), None)
        if decision is None or decision["kind"] != "asked":
            asked = [str(d["id"]) for d in self.decisions() if d["kind"] == "asked"]
            raise DecisionError(f"no choice {number} went to the owner in {self.slug}; those that did: {', '.join(asked) or 'none'}")
        return decision

    def add(self, make) -> dict:
        """Write one line under a lock, so two writers never take one number; then the same as an event."""
        self.directory.mkdir(parents=True, exist_ok=True)
        with (self.directory / "decisions.lock").open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            line = make(self.decisions())
            with self.file.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(line) + "\n")
        script("project.py", self.repo, "log", self.slug, f"decision.{line['kind']}", *(f"{key}:={json.dumps(value)}" for key, value in line.items() if key != "kind"))
        return line


def left(decision: dict) -> int:
    return int((read(decision["deadline"]) - now()).total_seconds())


def text(value: str | None, flag: str) -> str:
    if value is None or not value.strip():
        raise DecisionError(f"{flag} needs its text: one sentence in plain words")
    return " ".join(value.split())


def cmd_log(task: Task, args: argparse.Namespace) -> dict:
    if args.by == "personas" and not args.said:
        raise DecisionError("--by personas needs --said: who answered and what each picked, in one or two sentences")
    if (args.story is None) != (args.was is None):
        raise DecisionError("a story that changed is named by both --story N and --was, its text before the change")
    line = {"at": stamp(now()), "kind": "taken", "what": text(args.what, "--what"), "chose": text(args.chose, "--chose"), "why": text(args.why, "--why"), "by": args.by}
    for key in ("said", "undo", "was"):
        if getattr(args, key):
            line[key] = text(getattr(args, key), f"--{key}")
    if args.story is not None:
        line["story"] = args.story
    return task.add(lambda known: {"id": len(known) + 1, **line})


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
    made = task.add(lambda known: {"id": len(known) + 1, **line})
    return {**made, "next": (
        "this step waits for the owner's word, however long: the rest of the plan goes on, and no timeout takes it" if args.irreversible
        else f"tell Lem that choice {made['id']} of {task.slug} waits; go on with what does not depend on it; `decisions.py wait {task.slug} {made['id']}` says when it is answered or its wait ends"
    )}


def shown(task: Task, decision: dict) -> dict:
    out = {"task": task.slug, **{key: value for key, value in decision.items() if key != "kind"}}
    if decision["kind"] == "asked" and decision["state"] == "waits":
        out["seconds_left"] = None if decision["irreversible"] else max(0, left(decision))
    return out


def cmd_pending(repo: Path, slug: str | None) -> list[dict]:
    slugs = [slug] if slug else [task["slug"] for task in json.loads(script("project.py", repo, "tasks"))]
    return [shown(task, decision) for task in (Task(repo, name) for name in slugs) for decision in task.decisions() if decision["state"] == "waits"]


def cmd_wait(task: Task, number: int, seconds: int) -> dict:
    until = time.monotonic() + seconds
    while True:
        decision = task.one(number)
        if decision["state"] != "waits":
            return {**shown(task, decision), "ended": "answered" if decision["state"] == "answered" else "taken by timeout"}
        if not decision["irreversible"] and left(decision) <= 0:
            return {**shown(task, decision), "ended": "the wait is over", "next": f"`decisions.py timeout {task.slug} {number}` takes the recommended action"}
        if time.monotonic() >= until:
            return {**shown(task, decision), "ended": "still waits"}
        time.sleep(min(5, max(1, until - time.monotonic())))


def cmd_answer(task: Task, number: int, chose: str) -> dict:
    decision = task.one(number)
    chose = text(chose, "--chose")
    if decision["state"] == "answered":
        raise DecisionError(f"choice {number} has the owner's answer already: {decision['chose']!r}")
    if decision["state"] == "timeout":
        made = task.add(lambda known: {"id": number, "at": stamp(now()), "kind": "late", "chose": chose})
        same = chose == decision["chose"]
        return {**made, "state": "timeout", "taken": decision["chose"], "next": (
            "the answer is the action that was taken: nothing more to do" if same
            else "the recommended action was taken when the wait ended, and the answer differs: it is a correction. Tell the lead while the task builds; after that it is a new ask"
        )}
    return task.add(lambda known: {"id": number, "at": stamp(now()), "kind": "answered", "chose": chose})


def cmd_timeout(task: Task, number: int) -> dict:
    decision = task.one(number)
    if decision["state"] != "waits":
        raise DecisionError(f"choice {number} does not wait: it is {decision['state']}, with {decision['chose']!r}")
    if decision["irreversible"]:
        raise DecisionError(
            f"choice {number} is a step that a later \"no\" cannot reverse ({IRREVERSIBLE[decision['irreversible']]}): "
            "no timeout takes it. It waits for the owner's word, and the rest of the plan goes on",
        )
    if left(decision) > 0:
        raise DecisionError(f"the wait of choice {number} has {left(decision)} seconds left (until {decision['deadline']}); the owner may still answer")
    return task.add(lambda known: {"id": number, "at": stamp(now()), "kind": "timeout", "chose": decision["recommended"]})


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
    log.add_argument("--story", type=int, metavar="N", help="the number of the story this decision changed")
    log.add_argument("--was", help="that story's text before the change")
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
    answer.add_argument("--chose", required=True)
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
            elif args.command == "ask":
                result = cmd_ask(task, args)
            elif args.command == "wait":
                result = cmd_wait(task, args.id, args.seconds)
            elif args.command == "answer":
                result = cmd_answer(task, args.id, args.chose)
            elif args.command == "timeout":
                result = cmd_timeout(task, args.id)
            else:
                result = [shown(task, decision) for decision in task.decisions()]
    except DecisionError as error:
        sys.exit(f"decisions.py: {error}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
