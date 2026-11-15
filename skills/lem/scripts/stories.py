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

It never moves the task's worktree. It makes a worktree of its own beside it, at the branch's
tip, runs the commands of the settings' `gate.setup` there (what a fresh worktree of this
project needs before its tests can start), and runs each story's tests twice in it:

- on the branch's tip, where each must pass. A test that passes in the task's worktree and not
  here needs something a fresh worktree lacks, and the check says so: a failure on the base
  commit would then prove nothing;
- on the base commit with only the named test files of the branch laid over it, where each must
  fail. A command that does not start there (exit 126 or 127) is no proof: a file the test
  needs is not among the files the story names.

The worktree is removed afterwards, also when a command fails, and one that a killed run left
behind is removed by the next run.
"""

from __future__ import annotations

import sys

if sys.version_info < (3, 11):
    # an old python3 must still load this file, so that it can say what it needs and not a traceback
    sys.exit(f"stories.py: Lem needs Python 3.11 or newer, and this python3 is {sys.version.split()[0]}; put a newer one first on PATH, or run this file with it")

import argparse
import hashlib
import json
import os
import re
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
    fenced, inside = set(), False
    for i, line in enumerate(lines):
        if line.lstrip().startswith(("```", "~~~")):
            inside = not inside
            fenced.add(i)
        elif inside:
            fenced.add(i)
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


def leftovers(task: Task) -> None:
    """Remove a worktree of this check that a killed run left behind. One whose run still lives stays."""
    for old in sorted(task.worktree.parent.glob(f"{task.slug}.red-*")):
        pid = old.name.rsplit("-", 1)[-1]
        try:
            os.kill(int(pid), 0)
        except (ValueError, ProcessLookupError):
            run(["git", "-C", str(task.main), "worktree", "remove", "--force", str(old)], check=False)
        except PermissionError:
            continue


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
    results: list[dict] = []
    setup: list[dict] = []
    if tests:
        leftovers(task)
        scratch = task.worktree.parent / f"{task.slug}.red-{os.getpid()}"

        def outcome(command: str) -> int:
            # through a shell, as the gate's commands run: a test command is a line the project would type
            return subprocess.run(command, shell=True, cwd=scratch, capture_output=True, text=True, check=False).returncode  # noqa: S602

        git(task.main, "worktree", "add", "-q", "--detach", str(scratch), tip)
        try:
            for command in task.settings["gate"]["setup"]:
                code = outcome(command)
                setup.append({"command": command, "exit": code})
                if code != 0:
                    raise StoriesError(f"`{command}` of gate.setup failed in a fresh worktree (exit {code}), so no test could run there; correct that command in .lem/project.toml")
            on_branch = [outcome(test["command"]) for _, test in tests]
            # What a test changed in a tracked file on the branch must not reach its run on the
            # base commit. Files git does not track stay: what gate.setup made is among them, and
            # without it every test would fail on the base commit for no reason of the story's.
            git(scratch, "reset", "-q", "--hard")
            git(scratch, "checkout", "-q", "--detach", base)
            files = sorted({file for _, test in tests for file in test["files"]})
            git(scratch, "checkout", tip, "--", *files)
            on_base = [outcome(test["command"]) for _, test in tests]
        finally:
            run(["git", "-C", str(task.main), "worktree", "remove", "--force", str(scratch)], check=False)
        for (number, test), green, red in zip(tests, on_branch, on_base):
            problem = None
            if green != 0:
                problem = (
                    f"fails in a fresh worktree of the branch (exit {green}). If it passes in the task's worktree, it needs something a fresh one "
                    "lacks: put the commands that make it into gate.setup of .lem/project.toml"
                )
            elif red == 0:
                problem = "passes on the base commit too, so it does not test the change"
            elif red in (126, 127):
                problem = f"does not start on the base commit (exit {red}): a file it needs is not among the files the story names, so its failure there proves nothing"
            results.append({"story": number, "command": test["command"], "files": test["files"], "on_branch": green, "on_base": red, "problem": problem})
    ok = not any(result["problem"] for result in results)
    task.log("task.red", ok=ok, digest=found["digest"], base=base[:9], tip=tip[:9], tests=results, without_a_test=without)
    return {"task": task.slug, "ok": ok, "digest": found["digest"], "base": base[:9], "tip": tip[:9], "setup": setup, "tests": results, "without_a_test": without}


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
