#!/usr/bin/env python3
"""The stories of a task: what the owner approved, and the tests that hold each one.

A story is one business rule of a request in plain language with one concrete example. The
stories are the owner's document: he reads them and not the plan, and they become the tests. They
have one source, the top of the task's plan file, so that the board, the checks and the text of
the pull request cannot drift apart:

    ## Stories

    Kind: feature, because the export gets a new column and two readers of it.

    1. A CSV export holds the gift note of an order: order 1042 with the note "for Ania" has
       that text in its row.
       - test: `python3 -m unittest tests.test_export.GiftNote` in `tests/test_export.py`
    2. An order with no gift note has an empty cell, not the word "None".
       - test: `python3 -m unittest tests.test_export.NoNote` in `tests/test_export.py`

`Kind` is `feature` or `correction`, with the reason after `because`. A correction is a request
that yields one story and touches nothing careful; its story is the owner's own sentence made
exact. A story's test is a command and the files that hold the test, each in backticks. A story
that no test can hold (a sentence of a document) says so, and that is shown wherever the stories
are:

       - no test: the change is one paragraph of the README.

    stories.py show SLUG      the stories of the task's plan, as JSON
    stories.py record SLUG    the same, and one event for the board
    stories.py red SLUG       each story's tests pass on the branch and fail on the base commit

`red` is a machine check with no model in it. A test that also passes on the base commit does
not test the change, and a story with no test at the end of a build is refused.

It never moves the task's worktree. It makes two worktrees of its own beside it, each with the
commands of the settings' `gate.setup` run in it first (what a fresh worktree of this project
needs before its tests can start), so that nothing one run writes reaches the other:

- one at the branch's tip, where each test must pass. A test that passes in the task's worktree
  and not here needs something a fresh worktree lacks, and the check says so: a failure on the
  base commit would then prove nothing;
- one at the base commit with only the named test files of the branch laid over it, where each
  test must fail. A command that does not start there (exit 126 or 127) is no proof.

What the check cannot tell: whether a file of the branch that the base run lacked is the change
or a helper of the test. A test of a new module fails on the base commit because the module is
absent, and that is the proof wanted; a test whose new helper was not named fails the same way
and proves nothing. Only the story's own list of files tells the two apart, so the result names
every file the base run lacked (`run_without`), for the one who reads the change.

One check of a task runs at a time. The two worktrees are removed afterwards, also when a
command fails or the check is stopped, with every process a command left behind; what a killed
run left is removed by the next run. A worktree that cannot be removed is an error with its path.
"""

from __future__ import annotations

import sys

if sys.version_info < (3, 11):
    # an old python3 must still load this file, so that it can say what it needs and not a traceback
    sys.exit(f"stories.py: Lem needs Python 3.11 or newer, and this python3 is {sys.version.split()[0]}; put a newer one first on PATH, or run this file with it")

import argparse
import fcntl
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
KINDS = ("feature", "correction")
HEADING = re.compile(r"^##\s+Stories\s*$")
KIND = re.compile(r"^Kind:\s*(\w+)\s*(?:,\s*because|:|—|-)\s*(.+)$", re.IGNORECASE)
STORY = re.compile(r"^(\d+)\.\s+(.+)$")
TEST = re.compile(r"^\s+-\s+test:\s+`([^`]+)`\s+in\s+(.+)$")
NO_TEST = re.compile(r"^\s+-\s+no test:\s+(.+)$")
FILES = re.compile(r"`([^`]+)`")


class StoriesError(Exception):
    pass


def run(args: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    ran = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)
    if check and ran.returncode != 0:
        raise StoriesError(f"{' '.join(args[:4])} failed: {(ran.stderr or ran.stdout).strip()}")
    return ran


def git(where: Path, *args: str, check: bool = True) -> str:
    return run(["git", "-C", str(where), *args], check=check).stdout.strip()


def script(name: str, repo: Path, *args: str) -> str:
    ran = subprocess.run([sys.executable, "-B", str(SCRIPTS / name), "--repo", str(repo), *args], capture_output=True, text=True, check=False)
    if ran.returncode != 0:
        raise StoriesError(ran.stderr.strip().removeprefix(f"{name}: ") or f"{name} {args[0]} failed")
    return ran.stdout


def parse(text: str, name: str) -> dict:
    """The stories section of a plan as a dict; a section that does not have the form is refused with the line."""
    lines = text.splitlines()
    # A plan may show the form in a code fence: what is inside one is an example, never the section.
    # A fence closes only on a line of its own character, at least as long as the one that opened
    # it, with nothing after it: a shorter fence inside is a part of the example.
    fenced: set[int] = set()
    opened: tuple[str, int] | None = None
    for i, line in enumerate(lines):
        mark = re.match(r" {0,3}(`{3,}|~{3,})(.*)$", line)
        if opened is None:
            if mark and not (mark.group(1)[0] == "`" and "`" in mark.group(2)):
                opened = (mark.group(1)[0], len(mark.group(1)))
                fenced.add(i)
            continue
        fenced.add(i)
        if mark and mark.group(1)[0] == opened[0] and len(mark.group(1)) >= opened[1] and not mark.group(2).strip():
            opened = None
    start = next((i for i, line in enumerate(lines) if i not in fenced and HEADING.match(line)), None)
    if start is None:
        raise StoriesError(f"{name} has no `## Stories` section; the plan opens with it, as `stories.py --help` shows")
    end = next((i for i in range(start + 1, len(lines)) if i not in fenced and lines[i].startswith("## ")), len(lines))
    lines = [("" if i in fenced else line) for i, line in enumerate(lines)]
    kind = why = None
    stories: list[dict] = []
    for number, line in enumerate(lines[start + 1:end], start + 2):
        where = f"{name}:{number}"
        if not line.strip():
            continue
        if kind is None:
            found = KIND.match(line.strip())
            if not found or found.group(1).lower() not in KINDS or not found.group(2).strip():
                raise StoriesError(f"{where}: the section starts with `Kind: feature, because ...` or `Kind: correction, because ...`, and this line is {line.strip()!r}")
            kind, why = found.group(1).lower(), found.group(2).strip()
            continue
        story = STORY.match(line)
        if story:
            if int(story.group(1)) != len(stories) + 1:
                raise StoriesError(f"{where}: the stories are numbered 1, 2, 3 in order, and this one is {story.group(1)} after {len(stories)}")
            stories.append({"n": len(stories) + 1, "text": story.group(2).strip(), "tests": [], "no_test": None})
            continue
        if not stories:
            raise StoriesError(f"{where}: a story starts a line with its number, as in `1. A rule, with one example.`, and this line is {line.strip()!r}")
        test, none = TEST.match(line), NO_TEST.match(line)
        if test:
            files = FILES.findall(test.group(2))
            if not files:
                raise StoriesError(f"{where}: a test names its command and its files in backticks, as in - test: `COMMAND` in `FILE`")
            stories[-1]["tests"].append({"command": test.group(1).strip(), "files": files})
        elif none:
            stories[-1]["no_test"] = none.group(1).strip()
        elif line.lstrip().startswith("- "):
            raise StoriesError(f"{where}: under a story a line is `- test: `COMMAND` in `FILE`` or `- no test: REASON`, and this one is {line.strip()!r}")
        elif stories[-1]["tests"] or stories[-1]["no_test"]:
            raise StoriesError(f"{where}: the text of a story comes before its tests; this line comes after them: {line.strip()!r}")
        else:
            stories[-1]["text"] += " " + line.strip()
    if kind is None or not stories:
        raise StoriesError(f"{name}: the `## Stories` section holds no {'story' if kind else 'Kind line'}")
    if kind == "correction" and len(stories) != 1:
        raise StoriesError(f"{name}: a correction has one story, and this plan has {len(stories)}: it is a feature")
    both = [s["n"] for s in stories if s["tests"] and s["no_test"]]
    if both:
        raise StoriesError(f"{name}: story {both[0]} names a test and says that it has none; keep one of the two")
    # one mark for this exact set of stories and tests: a result of the check belongs to the set it ran on
    digest = hashlib.sha256(json.dumps([kind, stories], sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]
    return {"kind": kind, "why": why, "digest": digest, "stories": stories}


class Task:
    def __init__(self, repo: Path, slug: str) -> None:
        self.settings = json.loads(script("project.py", repo, "show"))
        if self.settings["settings"] is None:
            raise StoriesError("this repository has no .lem/project.toml; `/lem init` writes it")
        tasks = json.loads(script("project.py", repo, "tasks"))
        if not any(task["slug"] == slug for task in tasks):
            raise StoriesError(f"no task {slug!r}; the tasks are: {', '.join(task['slug'] for task in tasks) or 'none yet'}")
        self.slug = slug
        self.repo = repo
        self.main = Path(self.settings["main"])
        root = Path(self.settings["root"]).resolve()
        self.worktree = self.main / Path(self.settings["paths"]["worktrees"]["path"]).relative_to(root) / slug
        if not (self.worktree / ".git").exists():
            raise StoriesError(f"the task has no worktree at {self.worktree}")
        self.directory = Path(script("project.py", repo, "state-dir").strip()) / "tasks" / slug
        self.plans = self.worktree / Path(self.settings["paths"]["plans"]["path"]).relative_to(root)

    def stories(self) -> dict:
        # the plan of this task and of no other: a date, a hyphen and the task's whole name
        named = re.compile(rf"\d{{8}}-{re.escape(self.slug)}\.md")
        found = sorted(file for file in self.plans.iterdir() if named.fullmatch(file.name)) if self.plans.is_dir() else []
        if not found:
            raise StoriesError(f"no plan of this task in {self.plans}: its name is YYYYMMDD-{self.slug}.md")
        plan = found[-1]
        return {"task": self.slug, "plan": str(plan), **parse(plan.read_text(encoding="utf-8"), plan.name)}

    def log(self, event: str, **fields: object) -> None:
        script("project.py", self.repo, "log", self.slug, event, *(f"{key}:={json.dumps(value, ensure_ascii=False)}" for key, value in fields.items()))


def remove(task: Task, place: Path) -> str | None:
    """Remove one worktree of this check, a locked one too. Returns what is in the way when it stays."""
    def listed() -> bool:
        return f"worktree {place}\0" in run(["git", "-C", str(task.main), "worktree", "list", "--porcelain", "-z"], check=False).stdout

    if not place.exists() and not listed():
        return None
    run(["git", "-C", str(task.main), "worktree", "unlock", str(place)], check=False)
    # twice --force: a worktree with changes, and one that a command locked
    run(["git", "-C", str(task.main), "worktree", "remove", "--force", "--force", str(place)], check=False)
    if place.exists():
        shutil.rmtree(place, ignore_errors=True)
    run(["git", "-C", str(task.main), "worktree", "prune"], check=False)
    if place.exists() or listed():
        return f"{place} could not be removed; remove it yourself: git -C {task.main} worktree remove --force --force {place}"
    return None


def cmd_red(task: Task) -> dict:
    found = task.stories()
    untested = [story["n"] for story in found["stories"] if not story["tests"] and not story["no_test"]]
    if untested:
        raise StoriesError(
            f"story {untested[0]} names no test: every story is held by a test at the end of a build. "
            "Add `- test: `COMMAND` in `FILE`` under it in the plan, or `- no test: REASON` when no test can hold it",
        )
    dirty = git(task.worktree, "status", "--porcelain")
    if dirty:
        raise StoriesError(f"the worktree has changes nobody committed:\n{dirty}\ncommit them or remove them: this check runs what the branch holds, and they are not in it")
    base_branch = task.settings["branch"]["base"]
    onto = f"origin/{base_branch}" if git(task.main, "remote", "get-url", "origin", check=False) else str(base_branch)
    tip = git(task.worktree, "rev-parse", "HEAD")
    base = git(task.worktree, "merge-base", tip, onto)
    if base == tip:
        raise StoriesError(f"the branch has no commit beyond {onto}, so there is no change for a test to hold")
    tests = [(story["n"], test) for story in found["stories"] for test in story["tests"]]
    for number, test in tests:
        for file in test["files"]:
            # --: a name that starts with a hyphen is still a name
            kind = run(["git", "-C", str(task.worktree), "cat-file", "-t", "--", f"{tip}:{file}"], check=False).stdout.strip()
            if kind != "blob":
                raise StoriesError(
                    f"story {number}: {file!r} is {'a folder' if kind == 'tree' else 'not a file'} on the branch. Name each file that holds the test, "
                    "one by one and relative to the root: a folder would lay the change itself over the base commit",
                )
    without = [{"story": story["n"], "why": story["no_test"]} for story in found["stories"] if story["no_test"]]
    laid = sorted({file for _, test in tests for file in test["files"]})
    # what the base run lacks: every file the branch changed that is not a named test file
    changed = [name for name in git(task.worktree, "diff", "--name-only", "--no-renames", "-z", base, tip).split("\0") if name]
    run_without = sorted(set(changed) - set(laid))
    results: list[dict] = []
    setup: list[dict] = []
    if tests:
        # One check of a task at a time. The lock is the kernel's, and it goes when its process
        # goes, however that is; so whoever holds it knows that a worktree it finds is a dead run's.
        lock = (task.directory / "red.lock").open("w")
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise StoriesError("another check of this task's stories runs now; wait for it to end") from error
        places = {"branch": task.worktree.parent / f"{task.slug}.red-tip", "base": task.worktree.parent / f"{task.slug}.red-base"}
        # every worktree of this check for this task, whatever its last word: a slug holds no dot,
        # so the pattern is this task's alone
        for place in sorted({*places.values(), *task.worktree.parent.glob(f"{task.slug}.red-*")}):
            stuck = remove(task, place)
            if stuck:
                raise StoriesError(stuck)
        child: list[subprocess.Popen] = []

        def stop() -> None:
            """End the command that runs and everything it started: each command is a process group of its own."""
            for proc in child:
                for sign in (signal.SIGTERM, signal.SIGKILL):
                    try:
                        os.killpg(proc.pid, sign)
                    except (ProcessLookupError, PermissionError):
                        break
                    try:
                        proc.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        continue
            child.clear()

        def outcome(command: str, where: Path) -> int:
            # through a shell, as the gate's commands run: a test command is a line the project would type
            proc = subprocess.Popen(command, shell=True, cwd=where, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, start_new_session=True)  # noqa: S602
            child.append(proc)
            code = proc.wait()
            # a command that ended may have left a process behind (a server a test started)
            stop()
            return code

        def grouped(where: Path, *args: str) -> None:
            """A git command that may run a hook of the repository: in a group of its own, like every other command here."""
            proc = subprocess.Popen(["git", "-C", str(where), *args], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL, text=True, start_new_session=True)
            child.append(proc)
            _, said = proc.communicate()
            stop()
            if proc.returncode != 0:
                raise StoriesError(f"git {' '.join(args[:2])} failed: {said.strip()}")

        def ended(*_: object) -> None:
            raise KeyboardInterrupt

        before = signal.signal(signal.SIGTERM, ended)
        codes: dict[str, list[int]] = {}
        failure: str | None = None
        try:
            for name, place in places.items():
                grouped(task.main, "worktree", "add", "-q", "--detach", str(place), tip if name == "branch" else base)
                if name == "base":
                    grouped(place, "checkout", tip, "--", *laid)
                for command in task.settings["gate"]["setup"]:
                    code = outcome(command, place)
                    setup.append({"on": name, "command": command, "exit": code})
                    if code != 0:
                        where = "a fresh worktree of the branch" if name == "branch" else "a fresh worktree of the base commit, with the test files laid over it"
                        raise StoriesError(f"`{command}` of gate.setup failed in {where} (exit {code}), so no test could run there; correct that command in .lem/project.toml")
                codes[name] = [outcome(test["command"], place) for _, test in tests]
        except KeyboardInterrupt:
            failure = "the check was stopped, and its commands are ended"
        except StoriesError as error:
            failure = str(error)
        finally:
            stop()
            signal.signal(signal.SIGTERM, before)
            stuck = [problem for problem in (remove(task, place) for place in places.values()) if problem]
            lock.close()
        # A worktree that stayed is said whatever else went wrong: the first failure does not hide it.
        if failure or stuck:
            raise StoriesError("; ".join([*([failure] if failure else []), *(stuck or ["its worktrees are removed"] if failure else stuck)]))
        for (number, test), green, red in zip(tests, codes["branch"], codes["base"]):
            problem = None
            if green != 0:
                problem = (
                    f"fails in a fresh worktree of the branch (exit {green}). If it passes in the task's worktree, it needs something a fresh one "
                    "lacks: put the commands that make it into gate.setup of .lem/project.toml"
                )
            elif red == 0:
                problem = "passes on the base commit too, so it does not test the change"
            elif red in (126, 127):
                problem = (
                    f"does not start on the base commit (exit {red}), so its failure there proves nothing. If a file it needs is a helper of the test, "
                    "name it among the story's files; if what is absent is the change itself, make the test fail on it and not stop before it"
                )
            results.append({"story": number, "command": test["command"], "files": test["files"], "on_branch": green, "on_base": red, "problem": problem})
    ok = not any(result["problem"] for result in results)
    task.log("task.red", ok=ok, digest=found["digest"], base=base[:9], tip=tip[:9], tests=results, without_a_test=without, run_without=run_without)
    return {
        "task": task.slug, "ok": ok, "digest": found["digest"], "base": base[:9], "tip": tip[:9], "setup": setup, "tests": results,
        "without_a_test": without, "run_without": run_without,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=".", help="a directory inside the repository (default: the current one)")
    parser.add_argument("step", choices=("show", "record", "red"))
    parser.add_argument("slug")
    args = parser.parse_args()
    try:
        task = Task(Path(args.repo).resolve(), args.slug)
        if args.step == "red":
            result = cmd_red(task)
        else:
            result = task.stories()
            if args.step == "record":
                task.log("task.stories", kind=result["kind"], why=result["why"], digest=result["digest"], stories=result["stories"])
    except StoriesError as error:
        sys.exit(f"stories.py: {error}")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.step == "red" and not result["ok"]:
        bad = next(test for test in result["tests"] if test["problem"])
        sys.exit(f"stories.py: story {bad['story']}: `{bad['command']}` {bad['problem']}")


if __name__ == "__main__":
    main()
