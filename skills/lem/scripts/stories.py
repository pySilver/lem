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
exact. Lem calls it a small change, and a small change has no plan: its story is the same section
in `stories.md` in the task's directory, which no commit holds, and the builder adds its test line
there. A branch's plan comes first when it has one, and only a correction is read from that file:
a feature's stories are at the top of its plan, and a feature with no plan is refused. A story's test is a command and the files that hold the test, each in backticks. A story
that no test can hold (a sentence of a document) says so, and that is shown wherever the stories
are:

       - no test: the change is one paragraph of the README.

    stories.py approve SLUG --file FILE [--correction]
    stories.py approve SLUG --read
                              keep the stories the owner approved, as FILE has them: the same
                              section with no test lines, which the lead adds. --correction: Lem
                              approves a correction's one story in his name, as the task's first
                              contract only, and he may still say "this is a feature". --read: the lead of the rare path freezes
                              the plan's stories, which a read found nobody confused by, as the
                              task's first contract; refused when the task has any approval, and
                              after one read in which nobody answered, until a second such read
                              in a row lets the build go on. It
                              counts for the plan's check and for `decisions.py story`, and never
                              as his yes
    stories.py approved SLUG  the approved stories of the task, or null when it has none
    stories.py digest SLUG [--file FILE]
                              the digest of the stories' kind and texts, without tests: of FILE,
                              or of the task's plan
    stories.py show SLUG      the stories of the task's plan, or of a small change's `stories.md`, as
                              JSON; `small` says which, and `plan` names the file
    stories.py record SLUG    the same, and one event for the board
    stories.py red SLUG       each story's tests pass on the branch and fail on the base commit

Approved stories are frozen as written. `approve` keeps them in `stories.json` in the task's
directory, with their text, a digest and a number of their own (approval 1, 2, ...), the earlier
approvals under `history`, and logs one `stories.approved` event. An approval of a text approved
before is still a new approval, with no change after it. From then on the
plan's stories are the expected ones: the newest approval's stories with each change of them that
`decisions.py story` recorded after it applied in the order of the record (`decisions.py changes
SLUG` gives them). They are compared text for text and in order, with each run of spaces as one, so
how a story is broken into lines does not count; the plan's `Kind:` is the approved kind, which
only his next approval changes. `show`, `record` and `red` refuse a plan that differs, and name
the first story that does. So the lead can neither reword, drop nor add a story without the
record saying so, and the pull request is not green for each such change. A task with no
approved stories (a plan written before this rule, a night plan, a request whose whole context
was written) has the plan's stories as their one source.

`digest` gives the digest of a set of stories without their tests: a file's, or the plan's. It
is what an approval keeps and what the record of the personas' read names, so that a read of
other stories than the approved ones shows.

`red` is a machine check with no model in it. A test that also passes on the base commit does
not test the change, and a story with no test at the end of a build is refused.

It never moves the task's worktree. It makes two worktrees of its own beside it, each with the
commands of the settings' `gate.setup` run in it first (what a fresh worktree of this project
needs before its tests can start), so that nothing one run writes reaches the other:

- one at the branch's tip, where each test must pass. A test that passes in the task's worktree
  and not here needs something a fresh worktree lacks, and the check says so: a failure on the
  base commit would then prove nothing;
- one at the base commit with only the named test files of the branch laid over it, where each
  test must fail. A command that does not start there is no proof: one that exits 126 or 127,
  the codes a shell gives for a program it cannot find or run, and one that starts a shell
  (`sh`, `bash`, `dash`, `ksh`, `zsh`) on a script file the base commit lacks, which bash ends
  with 127 and dash with 2. A helper that a test's own script starts is caught only by the code
  its shell gives, so a test starts its helpers by their path (`./tests/helper.sh`): every shell
  ends that with 127 when the file is not there.

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
import shlex
import shutil
import signal
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
KINDS = ("feature", "correction")
HEADING = re.compile(r"^##\s+Stories\s*$")
KIND = re.compile(r"^Kind:\s*(\w+)\s*(?:,\s*because|:|—|-)\s*(.+)$", re.IGNORECASE)
STORY = re.compile(r"^(\d+)\.\s+(.+)$")
TEST = re.compile(r"^\s+-\s+test:\s+`([^`]+)`\s+in\s+(.+)$")
NO_TEST = re.compile(r"^\s+-\s+no test:\s+(.+)$")
FILES = re.compile(r"`([^`]+)`")
# The shells a test command may start a script with, by the name of the program.
SHELLS = ("sh", "bash", "dash", "ksh", "zsh")


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


def text_digest(kind: str, texts: list[str]) -> str:
    """One mark for a set of stories without their tests: their kind and their texts, with each run
    of spaces as one. An approval keeps it, and the record of the personas' read names it."""
    return hashlib.sha256(json.dumps([kind, [" ".join(text.split()) for text in texts]], ensure_ascii=False).encode()).hexdigest()[:12]


def against(read: dict, changes: dict, name: str, slug: str) -> None:
    """Refuse a plan whose stories are not the expected ones: the approved stories with every
    recorded change applied, text for text and in order, and of the approved kind."""
    fix = (
        f"The plan's stories are the approved ones with each recorded change (`decisions.py changes {slug}` gives them), word for word, "
        f"with only the test lines added. A story the build changes, adds or removes is recorded first: `decisions.py story {slug} "
        "--changed N --was TEXT --now TEXT`, `--added N --now TEXT` or `--removed N --was TEXT`, with --why and --choice ID or --by lead|personas"
    )
    if read["kind"] != changes["approved"]["kind"]:
        raise StoriesError(
            f"{name} says `Kind: {read['kind']}`, and the owner approved its stories as a {changes['approved']['kind']}: a change of the kind is the owner's only, "
            f"by the owner's approval of the stories again (`stories.py approve {slug} --file FILE`)",
        )
    expected = changes["expected"]
    now = [story["text"] for story in read["stories"]]
    for number, (want, have) in enumerate(zip(expected, now), start=1):
        if want.split() != have.split():
            raise StoriesError(f"story {number} of {name} says {have!r}, and the expected story {number} is {want!r}. {fix}")
    if len(now) > len(expected):
        raise StoriesError(f"story {len(expected) + 1} of {name}, {now[len(expected)]!r}, is not among the expected stories, which end at {len(expected)}. {fix}")
    if len(now) < len(expected):
        raise StoriesError(f"{name} lacks story {len(now) + 1}, {expected[len(now)]!r}, which the expected stories hold. {fix}")


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
        self.directory = Path(script("project.py", repo, "state-dir").strip()) / "tasks" / slug
        self.plans = self.worktree / Path(self.settings["paths"]["plans"]["path"]).relative_to(root)
        self.approved_file = self.directory / "stories.json"
        # a small change's one story, with its test line: it has no plan, and no commit holds this file
        self.small_file = self.directory / "stories.md"

    def need_worktree(self) -> None:
        # the stories are approved before the task has a worktree; its plan is read from one
        if not (self.worktree / ".git").exists():
            raise StoriesError(f"the task has no worktree at {self.worktree}")

    def approved(self) -> dict | None:
        """The stories the owner approved, as `approve` kept them; none for a task without."""
        if not self.approved_file.is_file():
            return None
        try:
            return json.loads(self.approved_file.read_text(encoding="utf-8"))
        except ValueError as error:
            raise StoriesError(f"{self.approved_file} does not read as JSON ({error}); it is written by `stories.py approve` only") from error

    def stories(self) -> dict:
        self.need_worktree()
        # the plan of this task and of no other: a date, a hyphen and the task's whole name
        named = re.compile(rf"\d{{8}}-{re.escape(self.slug)}\.md")
        found = sorted(file for file in self.plans.iterdir() if named.fullmatch(file.name)) if self.plans.is_dir() else []
        small = not found and self.small_file.is_file()
        if not found and not small:
            raise StoriesError(f"no plan of this task in {self.plans}: its name is YYYYMMDD-{self.slug}.md; only a small change keeps its story in the task directory instead, in {self.small_file}")
        plan = self.small_file if small else found[-1]
        read = parse(plan.read_text(encoding="utf-8"), plan.name)
        if small and read["kind"] != "correction":
            raise StoriesError(
                f"{plan} says `Kind: {read['kind']}`: only a small change (`Kind: correction`) keeps its story in the task directory. "
                f"A feature's stories are at the top of its plan, and the branch has none in {self.plans}: its lead writes YYYYMMDD-{self.slug}.md",
            )
        changes = self.changes()
        digest = text_digest(read["kind"], [story["text"] for story in read["stories"]])
        if small and changes["approved"] is None:
            raise StoriesError(f"the small change's story in {plan} has no approval: Lem approves it in the owner's name before its builder starts, `stories.py approve {self.slug} --file {plan} --correction`")
        if changes["approved"] is None:
            return {"task": self.slug, "plan": str(plan), "small": small, **read, "stories_digest": digest, "approved": None, "approvals": [], "changes": [], "history": []}
        against(read, changes, plan.name, self.slug)
        return {
            "task": self.slug, "plan": str(plan), "small": small, **read, "stories_digest": digest,
            **{key: changes[key] for key in ("approved", "approvals", "changes", "history")},
        }

    def changes(self) -> dict:
        """The approved stories and their recorded changes, through the one script that writes them."""
        return json.loads(script("decisions.py", self.repo, "changes", self.slug))

    def log(self, event: str, **fields: object) -> None:
        script("project.py", self.repo, "log", self.slug, event, *(f"{key}:={json.dumps(value, ensure_ascii=False)}" for key, value in fields.items()))


def unstarted(command: str, where: Path) -> bool:
    """Whether the command starts a shell on a script file that is not in `where`. Its exit does
    not say so in every shell: bash ends `sh FILE` with no FILE with 127, dash with 2."""
    try:
        words = shlex.split(command)
    except ValueError:
        return False
    if not words or Path(words[0]).name not in SHELLS:
        return False
    rest = iter(words[1:])
    for word in rest:
        if word in ("-o", "+o"):
            next(rest, None)
        elif word == "--":
            file = next(rest, None)
            break
        elif word in ("-", "+") or word.startswith("--") or (word.startswith("-") and "c" in word):
            # standard input, a long option of one shell, or `-c TEXT`, whose operand is a command:
            # no script file to look for
            return False
        elif not word.startswith(("-", "+")):
            file = word
            break
    else:
        return False
    return file is not None and not (where / file).is_file()


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
            f"Add `- test: `COMMAND` in `FILE`` under it in {'the small change`s stories.md' if found['small'] else 'the plan'}, or `- no test: REASON` when no test can hold it",
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
            # What git says goes to a file, not a pipe: a process that a hook left behind holds a
            # pipe open, and a read of it would wait for that process and never reach stop().
            with tempfile.TemporaryFile() as said:
                proc = subprocess.Popen(["git", "-C", str(where), *args], stdout=subprocess.DEVNULL, stderr=said, stdin=subprocess.DEVNULL, start_new_session=True)
                child.append(proc)
                code = proc.wait()
                stop()
                said.seek(0)
                if code != 0:
                    raise StoriesError(f"git {' '.join(args[:2])} failed: {said.read().decode(errors='replace').strip()}")

        def ended(*_: object) -> None:
            raise KeyboardInterrupt

        before = signal.signal(signal.SIGTERM, ended)
        codes: dict[str, list[int]] = {}
        absent: list[bool] = []
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
                if name == "base":
                    # looked for before any test runs there, which might write the file
                    absent = [unstarted(test["command"], place) for _, test in tests]
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
        for (number, test), green, red, lacked in zip(tests, codes["branch"], codes["base"], absent):
            problem = None
            if green != 0:
                problem = (
                    f"fails in a fresh worktree of the branch (exit {green}). If it passes in the task's worktree, it needs something a fresh one "
                    "lacks: put the commands that make it into gate.setup of .lem/project.toml"
                )
            elif red == 0:
                problem = "passes on the base commit too, so it does not test the change"
            elif red in (126, 127) or lacked:
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


def reads_of(task: Task) -> list[dict]:
    """The task's `stories.read` events, oldest first, from the log `project.py` writes."""
    log = task.directory.parent.parent / "events.jsonl"
    found = []
    for line in (log.read_text(encoding="utf-8").splitlines() if log.is_file() else []):
        if '"stories.read"' in line:
            record = json.loads(line)
            if record.get("event") == "stories.read" and record.get("task") == task.slug:
                found.append(record)
    return found


# The automatic approvals, which no word of his gave in the moment: the rare path's read, and Lem's
# approval of a correction in his name. Each is a task's first contract only.
AUTOMATIC = {"read": "a read freezes only the first contract", "correction": "Lem approves a correction in the owner's name only as the first contract"}


def first_contract(task: Task, by: str) -> None:
    """An automatic approval is only the first contract of a task: once stories are approved, by
    him, as a correction or by a read, a story changes only through its record and the kind only
    through his own approval, which is always allowed and always makes a new number."""
    kept = task.approved()
    if kept is not None:
        number = kept.get("number") or 1 + len(kept.get("history", []))
        raise StoriesError(
            f"{task.slug} has approval {number} of its stories already (by {kept['by']}): {AUTOMATIC[by]}. "
            f"A story changes through its record, `decisions.py story {task.slug} ...`, and the kind only through the owner's own approval, "
            f"`stories.py approve {task.slug} --file FILE`",
        )


def cmd_approve(task: Task, file: str, by: str, plan: bool = False) -> dict:
    """Keep the stories that were approved, word for word, with a digest and a number of their own,
    and log the event. Each approval is a new one, also of a text approved before. The check of
    what is approved already and the write are one step under the task's lock, so an approval of
    his and an automatic one that come at one time never both pass."""
    source = Path(file)
    if not source.is_file():
        raise StoriesError(f"{file} is not a file; --file names the stories the owner approved, in the form `stories.py --help` shows")
    text = source.read_text(encoding="utf-8")
    read = parse(text, source.name)
    tested = [story["n"] for story in read["stories"] if story["tests"] or story["no_test"]]
    # the plan's own stories carry the lead's test lines, which are no part of a story's text
    if tested and not plan:
        raise StoriesError(f"story {tested[0]} of {source.name} has a test line: the stories the owner approves have none, and the lead adds them in the plan")
    if by == "correction" and read["kind"] != "correction":
        raise StoriesError(f"--correction approves a correction's one story in the owner's name, and {source.name} says `Kind: {read['kind']}`: a feature waits for the owner's own yes")
    stories = [{"n": story["n"], "text": story["text"]} for story in read["stories"]]
    # one mark for this exact set of approved texts; the approval itself is known by its number
    digest = text_digest(read["kind"], [story["text"] for story in stories])
    task.directory.mkdir(parents=True, exist_ok=True)
    with (task.directory / "stories.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if by in AUTOMATIC:
            first_contract(task, by)
        if by == "read":
            # the rare path: the lead freezes the stories the personas read, and only when nobody was confused
            reads = reads_of(task)
            last = reads[-1] if reads else None
            if last is None or last.get("digest") != digest:
                raise StoriesError(
                    f"--read freezes the stories the newest `stories.read` of {task.slug} read, and "
                    + ("there is none" if last is None else f"that read was of the stories with digest {last.get('digest')}, and {source.name} has {digest}")
                    + ": run the read over these stories first (`stages/plan.md`, step 1)",
                )
            # a read nobody answered is started once more; after the second in a row the build goes on
            if last["answered"] == 0 and (len(reads) < 2 or reads[-2].get("answered") != 0):
                raise StoriesError(
                    f"nobody answered the newest read of {task.slug}'s stories: it is started once more (`stages/plan.md`, step 1); "
                    "after a second read in a row that nobody answered, the build goes on with the stories as they are",
                )
            if last["flagged"] or last["split"]:
                raise StoriesError(
                    f"the newest read of {task.slug}'s stories found {'a flagged story' if last['flagged'] else 'a split between the families'}: "
                    "the stories wait for the owner, and only the owner's approval freezes them",
                )
        before = task.approved()
        history = [*before.get("history", []), {key: value for key, value in before.items() if key not in ("history", "task", "text")}] if before else []
        record = {
            "task": task.slug, "number": len(history) + 1, "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            # who approved: the owner; Lem in his name, for a correction that does not wait; or the
            # lead's read of the rare path, which counts for the plan's check and never as his yes
            "by": by, "kind": read["kind"], "why": read["why"], "digest": digest, "stories": stories, "text": text,
            **({"replaces": before["number"]} if before else {}), "history": history,
        }
        task.approved_file.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        task.log("stories.approved", by=by, number=record["number"], kind=record["kind"], why=record["why"], digest=digest, stories=stories, **({"replaces": before["number"]} if before else {}))
    return {**record, "file": str(task.approved_file)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=".", help="a directory inside the repository (default: the current one)")
    parser.add_argument("step", choices=("approve", "approved", "digest", "show", "record", "red"))
    parser.add_argument("slug")
    parser.add_argument("--file", help="with approve: the stories the owner approved, in the form above and with no test lines; with digest: the stories to mark")
    parser.add_argument("--correction", action="store_true", help="with approve: Lem approves a correction's one story in the owner's name")
    parser.add_argument("--read", action="store_true", help="with approve: the lead of the rare path freezes the stories a read in which nobody was confused read")
    args = parser.parse_args()
    try:
        if args.file is not None and args.step not in ("approve", "digest"):
            raise StoriesError("--file goes with `approve` and `digest`")
        if (args.correction or args.read) and args.step != "approve":
            raise StoriesError("--correction and --read go with `approve`")
        if args.correction and args.read:
            raise StoriesError("an approval is Lem's for a correction or the read's on the rare path, not both: --correction or --read")
        task = Task(Path(args.repo).resolve(), args.slug)
        if args.step == "approve":
            if args.read:
                if args.file is not None:
                    raise StoriesError("--read freezes the plan's own stories, the ones the read named: it takes no --file; a file of stories is approved by the owner, without --read")
                # refused before the plan is read, and again under the lock: a task with a contract keeps it
                first_contract(task, "read")
                result = cmd_approve(task, task.stories()["plan"], "read", plan=True)
            elif args.file is None:
                raise StoriesError("approve needs --file: the stories the owner approved, in the form `stories.py --help` shows, with no test lines")
            else:
                result = cmd_approve(task, args.file, "correction" if args.correction else "owner")
        elif args.step == "approved":
            kept = task.approved()
            result = {"task": task.slug, "approved": kept} if kept else {
                "task": task.slug, "approved": None, "says": "no approved stories: the plan's own stories are their one source",
            }
        elif args.step == "digest":
            if args.file is None:
                found = task.stories()
                result = {"task": task.slug, "of": found["plan"], "digest": found["stories_digest"]}
            else:
                if not Path(args.file).is_file():
                    raise StoriesError(f"{args.file} is not a file; --file names the stories to mark, in the form `stories.py --help` shows")
                read = parse(Path(args.file).read_text(encoding="utf-8"), Path(args.file).name)
                result = {"task": task.slug, "of": args.file, "digest": text_digest(read["kind"], [story["text"] for story in read["stories"]])}
        elif args.step == "red":
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
