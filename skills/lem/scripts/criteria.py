#!/usr/bin/env python3
"""The acceptance criteria of a task: what the owner approved, and the tests that hold each one.

An acceptance criterion is one business rule of a request in plain language with one concrete
example. The criteria are the owner's document: the owner reads them and not the plan, and they
become the tests. They have one source, the top of the task's plan file, so that the board, the checks and
the text of the pull request cannot drift apart:

    ## Acceptance criteria

    Size: full, because the export gets a new column and two readers of it.

    1. A CSV export holds the gift note of an order: order 1042 with the note "for Ania" has
       that text in its row.
       - test: `python3 -m unittest tests.test_export.GiftNote` in `tests/test_export.py`
    2. An order with no gift note has an empty cell, not the word "None".
       - test: `python3 -m unittest tests.test_export.NoNote` in `tests/test_export.py`

`Size` is `full` or `small`, with the reason after `because`. A small change is a request that
yields one criterion and touches nothing careful; its criterion is the owner's own sentence made
exact, and it has no plan: its criterion is the same section in `criteria.md` in the task's directory, which
no commit holds, and the builder adds its test line there. A branch's plan comes first when it has
one, and only a small change is read from that file: a full change's criteria are at the top of
its plan, and a full change with no plan is refused. A plan never makes a change small: a plan that
says `Size: small` is refused, with the small change named as the way for one plain change, since
a small change in a plan would take a full change's path with none of what a full change gets (the
owner's approval, the personas' read, the polish pass). The section of an older Lem, under `## Stories` with
the first line `Kind: feature` or `Kind: correction`, reads as `## Acceptance criteria` with
`Size: full` or `Size: small`, and its digests stay the ones that Lem wrote; a small change's
`stories.md` and an approval's `stories.json` of an older Lem are read where no `criteria.md` and
no `criteria.json` are. A criterion's test is a command and the files that hold the test, each in backticks. A
criterion that no test can hold (a sentence of a document) says so, and that is shown wherever
the criteria are:

       - no test: the change is one paragraph of the README.

    lem criteria approve SLUG --file FILE
    lem criteria approve SLUG --small [--file FILE]
    lem criteria approve SLUG --read
                              keep the criteria the owner approved, as FILE has them: the same
                              section with no test lines, which the lead adds. --small: Lem
                              approves a small change's one criterion in the owner's name, as the task's
                              first contract only, and the owner may still say "full"; its file is
                              `criteria.md` in the task directory unless --file names another. --read: the lead of a full change from a complete request freezes
                              the plan's criteria, which a read found nobody confused by, as the
                              task's first contract; refused when the task has any approval, and
                              after one read in which nobody answered, until a second such read
                              in a row lets the build go on. It
                              counts for the plan's check and for `lem decisions criterion`, and never
                              as the owner's yes
    lem criteria approved SLUG the approved criteria of the task, or null when it has none
    lem criteria digest SLUG [--file FILE]
                              the digest of the size and the texts of the criteria, without tests: of FILE,
                              or of the task's plan
    lem criteria show SLUG    the criteria of the task's plan, or of a small change's `criteria.md`, as
                              JSON; `small` says which, and `plan` names the file
    lem criteria record SLUG  the same, and one event for the board
    lem criteria red SLUG     each criterion's tests pass on the branch and fail on the base commit

Approved criteria are frozen as written. `approve` keeps them in `criteria.json` in the task's
directory, with their text, a digest and a number of their own (approval 1, 2, ...), the earlier
approvals under `history`, and logs one `criteria.approved` event. An approval of a text approved
before is still a new approval, with no change after it. From then on the
plan's criteria are the expected ones: the newest approval's criteria with each change of them that
`lem decisions criterion` recorded after it applied in the order of the record (`lem decisions changes
SLUG` gives them). They are compared text for text and in order, with each run of spaces as one, so
how a criterion is broken into lines does not count; the plan's `Size:` is the approved size, which
only the owner's next approval changes. `show`, `record` and `red` refuse a plan that differs, and name
the first criterion that does. So the lead can neither reword, drop nor add a criterion without
the record saying so, and the pull request is not green for each such change. A task with no
approved criteria (a plan written before this rule, a night plan, a full change from a complete
request) has the plan's criteria as their one source.

`digest` gives the digest of a set of criteria without their tests: a file's, or the plan's. It
is what an approval keeps and what the record of the personas' read names, so that a read of
other criteria than the approved ones shows.

`red` is a machine check with no model in it. A test that also passes on the base commit does
not test the change, and a criterion with no test at the end of a build is refused.

It never moves the task's worktree. It makes two worktrees of its own beside it, each with the
commands of the settings' `checks.setup` run in it first (what a fresh worktree of this project
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
and proves nothing. Only the criterion's own list of files tells the two apart, so the result names
every file the base run lacked (`run_without`), for the one who reads the change.

A test that needs the machine to itself runs under the repository's one lock for such commands,
through `lem project alone`: a test whose command starts with the words of a command of the
settings' `checks.alone`, whose last word may be a folder of the test's path (`npx playwright test
e2e/export.spec.ts` under `npx playwright test`, `sh tests/e2e/b.sh` under `sh tests/e2e`), so
that two checks of two tasks, or a check and a builder, never run such a suite at one moment.

One check of a task runs at a time. The two worktrees are removed afterwards, also when a
command fails or the check is stopped, with every process a command left behind; what a killed
run left is removed by the next run. A worktree that cannot be removed is an error with its path.
"""

from __future__ import annotations

import sys

if sys.version_info < (3, 11):
    # an old python3 must still load this file, so that it can say what it needs and not a traceback
    sys.exit(f"criteria.py: Lem needs Python 3.11 or newer, and this python3 is {sys.version.split()[0]}; put a newer one first on PATH, or run this file with it")

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
# The one place that builds and finds a plan's name, shared with project.py.
sys.dont_write_bytecode = True
sys.path.insert(0, str(SCRIPTS))
import lem_plans  # noqa: E402
# The size of a change: a full change, with its plan and lead, or a small change of one builder.
SIZES = ("full", "small")
# The heading of the section, and the heading an older Lem wrote, which still reads. A later change
# may drop the old one once no task whose plan or criteria.md says `## Stories` is open.
HEADING = re.compile(r"^##\s+(Acceptance criteria|Stories)\s*$")
SIZE = re.compile(r"^(Size|Kind):\s*(\w+)\s*(?:,\s*because|:|—|-)\s*(.+)$", re.IGNORECASE)
# The first line of a section an older Lem wrote, `Kind: feature|correction, because ...`, and the
# size each kind reads as. A digest is of the word as the file has it, so a digest an older Lem
# wrote of such a section still matches it. A later change may drop it once no task whose criteria
# say `Kind:` is open.
OLD_SIZES = {"feature": "full", "correction": "small"}
CRITERION = re.compile(r"^(\d+)\.\s+(.+)$")
TEST = re.compile(r"^\s+-\s+test:\s+`([^`]+)`\s+in\s+(.+)$")
NO_TEST = re.compile(r"^\s+-\s+no test:\s+(.+)$")
FILES = re.compile(r"`([^`]+)`")
# The shells a test command may start a script with, by the name of the program.
SHELLS = ("sh", "bash", "dash", "ksh", "zsh")


class CriteriaError(Exception):
    pass


def run(args: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    ran = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)
    if check and ran.returncode != 0:
        raise CriteriaError(f"{' '.join(args[:4])} failed: {(ran.stderr or ran.stdout).strip()}")
    return ran


def git(where: Path, *args: str, check: bool = True) -> str:
    return run(["git", "-C", str(where), *args], check=check).stdout.strip()


def script(name: str, repo: Path, *args: str) -> str:
    ran = subprocess.run([sys.executable, "-B", str(SCRIPTS / name), "--repo", str(repo), *args], capture_output=True, text=True, check=False)
    if ran.returncode != 0:
        raise CriteriaError(ran.stderr.strip().removeprefix(f"{name}: ") or f"{name} {args[0]} failed")
    # a line project.py writes on stderr when it succeeds (the move of an older state folder) is this script's to say too
    if ran.returncode == 0 and ran.stderr:
        sys.stderr.write(ran.stderr)
    return ran.stdout


def parse(text: str, name: str) -> dict:
    """The criteria section of a plan as a dict; a section that does not have the form is refused with the line."""
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
        raise CriteriaError(f"{name} has no `## Acceptance criteria` section; the plan opens with it, as `lem criteria --help` shows")
    end = next((i for i in range(start + 1, len(lines)) if i not in fenced and lines[i].startswith("## ")), len(lines))
    lines = [("" if i in fenced else line) for i, line in enumerate(lines)]
    size = mark = why = None
    criteria: list[dict] = []
    for number, line in enumerate(lines[start + 1:end], start + 2):
        where = f"{name}:{number}"
        if not line.strip():
            continue
        if size is None:
            found = SIZE.match(line.strip())
            label, word = (found.group(1).lower(), found.group(2).lower()) if found else (None, None)
            known = (label == "size" and word in SIZES) or (label == "kind" and word in OLD_SIZES)
            if not found or not known or not found.group(3).strip():
                raise CriteriaError(f"{where}: the section starts with `Size: full, because ...` or `Size: small, because ...`, and this line is {line.strip()!r}")
            size, mark, why = (word if label == "size" else OLD_SIZES[word]), word, found.group(3).strip()
            continue
        criterion = CRITERION.match(line)
        if criterion:
            if int(criterion.group(1)) != len(criteria) + 1:
                raise CriteriaError(f"{where}: the criteria are numbered 1, 2, 3 in order, and this one is {criterion.group(1)} after {len(criteria)}")
            criteria.append({"n": len(criteria) + 1, "text": criterion.group(2).strip(), "tests": [], "no_test": None})
            continue
        if not criteria:
            raise CriteriaError(f"{where}: a criterion starts a line with its number, as in `1. A rule, with one example.`, and this line is {line.strip()!r}")
        test, none = TEST.match(line), NO_TEST.match(line)
        if test:
            files = FILES.findall(test.group(2))
            if not files:
                raise CriteriaError(f"{where}: a test names its command and its files in backticks, as in - test: `COMMAND` in `FILE`")
            criteria[-1]["tests"].append({"command": test.group(1).strip(), "files": files})
        elif none:
            criteria[-1]["no_test"] = none.group(1).strip()
        elif line.lstrip().startswith("- "):
            raise CriteriaError(f"{where}: under a criterion a line is `- test: `COMMAND` in `FILE`` or `- no test: REASON`, and this one is {line.strip()!r}")
        elif criteria[-1]["tests"] or criteria[-1]["no_test"]:
            raise CriteriaError(f"{where}: the text of a criterion comes before its tests; this line comes after them: {line.strip()!r}")
        else:
            criteria[-1]["text"] += " " + line.strip()
    if size is None or not criteria:
        raise CriteriaError(f"{name}: the `## Acceptance criteria` section holds no {'criterion' if size else 'Size line'}")
    if size == "small" and len(criteria) != 1:
        raise CriteriaError(f"{name}: a small change has one criterion, and this one has {len(criteria)}: it is a full change")
    both = [s["n"] for s in criteria if s["tests"] and s["no_test"]]
    if both:
        raise CriteriaError(f"{name}: criterion {both[0]} names a test and says that it has none; keep one of the two")
    # one mark for this exact set of criteria and tests: a result of the check belongs to the set it ran on
    digest = hashlib.sha256(json.dumps([mark, criteria], sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]
    return {"size": size, "why": why, "digest": digest, "criteria": criteria, "mark": mark}


def text_digest(mark: str, texts: list[str]) -> str:
    """One mark for a set of criteria without their tests: the word of their size line as the file
    has it and their texts, with each run of spaces as one. An approval keeps it, and the record of
    the personas' read names it."""
    return hashlib.sha256(json.dumps([mark, [" ".join(text.split()) for text in texts]], ensure_ascii=False).encode()).hexdigest()[:12]


# Who approved, for an approval an older Lem kept: Lem's approval of a small change was `correction`.
OLD_BY = {"correction": "lem"}


def now_form(approval: dict) -> dict:
    """An approval in the form of now. One an older Lem kept names its kind (`feature`, `correction`)
    and not its size, holds its texts under `stories`, and names Lem's approval of a small change
    `by: correction`. A later change may drop the old form once no task with such an approval is open."""
    out = dict(approval)
    if "size" not in out and "kind" in out:
        out["size"] = OLD_SIZES.get(out.pop("kind"), approval["kind"])
    if "criteria" not in out and "stories" in out:
        out["criteria"] = out.pop("stories")
    if out.get("by") in OLD_BY:
        out["by"] = OLD_BY[out["by"]]
    if "history" in out:
        out["history"] = [now_form(old) for old in out["history"]]
    return out


def size_of(approval: dict) -> str | None:
    """The size an approval holds; one that an older Lem kept names its kind instead. A later change
    may drop the old form once no task whose approval names a kind is open."""
    return approval.get("size") or OLD_SIZES.get(approval.get("kind"))


def against(read: dict, changes: dict, name: str, slug: str) -> None:
    """Refuse a plan whose criteria are not the expected ones: the approved criteria with every
    recorded change applied, text for text and in order, and of the approved size."""
    fix = (
        f"The plan's criteria are the approved ones with each recorded change (`lem decisions changes {slug}` gives them), word for word, "
        f"with only the test lines added. A criterion the build changes, adds or removes is recorded first: `lem decisions criterion {slug} "
        "--changed N --was TEXT --now TEXT`, `--added N --now TEXT` or `--removed N --was TEXT`, with --why and --choice ID or --by lead|personas"
    )
    approved = size_of(changes["approved"])
    if read["size"] != approved:
        raise CriteriaError(
            f"{name} says `Size: {read['size']}`, and the owner approved its criteria as a {approved} change: a change of the size is the owner's only, "
            f"by the owner's approval of the criteria again (`lem criteria approve {slug} --file FILE`)",
        )
    expected = changes["expected"]
    now = [criterion["text"] for criterion in read["criteria"]]
    for number, (want, have) in enumerate(zip(expected, now), start=1):
        if want.split() != have.split():
            raise CriteriaError(f"criterion {number} of {name} says {have!r}, and the expected criterion {number} is {want!r}. {fix}")
    if len(now) > len(expected):
        raise CriteriaError(f"criterion {len(expected) + 1} of {name}, {now[len(expected)]!r}, is not among the expected criteria, which end at {len(expected)}. {fix}")
    if len(now) < len(expected):
        raise CriteriaError(f"{name} lacks criterion {len(now) + 1}, {expected[len(now)]!r}, which the expected criteria hold. {fix}")


class Task:
    def __init__(self, repo: Path, slug: str) -> None:
        self.settings = json.loads(script("project.py", repo, "show"))
        if self.settings["settings"] is None:
            raise CriteriaError("this repository has no .lem/project.toml; `/lem init` writes it")
        tasks = json.loads(script("project.py", repo, "tasks"))
        if not any(task["slug"] == slug for task in tasks):
            raise CriteriaError(f"no task {slug!r}; the tasks are: {', '.join(task['slug'] for task in tasks) or 'none yet'}")
        self.slug = slug
        self.repo = repo
        self.main = Path(self.settings["main"])
        root = Path(self.settings["root"]).resolve()
        self.worktree = self.main / Path(self.settings["paths"]["worktrees"]["path"]).relative_to(root) / slug
        self.directory = Path(script("project.py", repo, "state-dir").strip()) / "tasks" / slug
        self.plans = self.worktree / Path(self.settings["paths"]["plans"]["path"]).relative_to(root)
        self.approved_file = self.directory / "criteria.json"
        # a small change's one criterion, with its test line: it has no plan, and no commit holds this file
        self.small_file = self.directory / "criteria.md"
        # What an older Lem wrote in their place, read when the file of now is not there. A later change
        # may drop the two once no task with such a file is open.
        self.old_approved_file = self.directory / "stories.json"
        self.old_small_file = self.directory / "stories.md"

    def need_worktree(self) -> None:
        # the criteria are approved before the task has a worktree; its plan is read from one
        if not (self.worktree / ".git").exists():
            raise CriteriaError(f"the task has no worktree at {self.worktree}")

    def approved(self) -> dict | None:
        """The criteria the owner approved, as `approve` kept them; none for a task without. An
        approval an older Lem kept in `stories.json` reads in the form of now."""
        kept = self.approved_file if self.approved_file.is_file() else self.old_approved_file
        if not kept.is_file():
            return None
        try:
            return now_form(json.loads(kept.read_text(encoding="utf-8")))
        except ValueError as error:
            raise CriteriaError(f"{kept} does not read as JSON ({error}); it is written by `lem criteria approve` only") from error

    def criteria(self) -> dict:
        self.need_worktree()
        # the plan of this task and of no other: the name `paths.plan_file` gives, with the task's whole slug
        pattern = self.settings["paths"]["plan_file"]["pattern"]
        found = lem_plans.found(self.plans, pattern, self.slug)
        small_file = self.small_file if self.small_file.is_file() else self.old_small_file
        small = not found and small_file.is_file()
        if not found and not small:
            raise CriteriaError(
                f"no plan of this task in {self.plans}: its name is {pattern.replace('<slug>', self.slug)} (`lem project plan-file {self.slug}` prints it); "
                f"only a small change keeps its criterion in the task directory instead, in {self.small_file}",
            )
        plan = small_file if small else found
        read = parse(plan.read_text(encoding="utf-8"), plan.name)
        if small and read["size"] != "small":
            raise CriteriaError(
                f"{plan} says `Size: {read['size']}`: only a small change (`Size: small`) keeps its criterion in the task directory. "
                f"A full change's criteria are at the top of its plan, and the branch has none in {self.plans}: its lead writes {pattern.replace('<slug>', self.slug)}",
            )
        changes = self.changes()
        digest = text_digest(read["mark"], [criterion["text"] for criterion in read["criteria"]])
        if small and changes["approved"] is None:
            raise CriteriaError(f"the small change's criterion in {plan} has no approval: Lem approves it in the owner's name before its builder starts, `lem criteria approve {self.slug} --file {plan} --small`")
        if changes["approved"] is None:
            self.no_small_plan(read, plan, small)
            return {"task": self.slug, "plan": str(plan), "small": small, **read, "criteria_digest": digest, "approved": None, "approvals": [], "changes": [], "history": []}
        # the approved size first: a plan of another size than the owner approved says that
        against(read, changes, plan.name, self.slug)
        self.no_small_plan(read, plan, small)
        return {
            "task": self.slug, "plan": str(plan), "small": small, **read, "criteria_digest": digest,
            **{key: changes[key] for key in ("approved", "approvals", "changes", "history")},
        }

    def no_small_plan(self, read: dict, plan: Path, small: bool) -> None:
        """Refuse a plan file that says `Size: small` (or `Kind: correction`, as an older Lem wrote it):
        a plan never makes a change small. One plain change is a small change, with its criterion in the
        task directory and no plan; a small change in a plan would land with no approval of the
        owner's, no read and no polish pass."""
        if small or read["size"] != "small":
            return
        said = "Kind: correction" if read["mark"] == "correction" else "Size: small"
        raise CriteriaError(
            f"{plan.name} says `{said}`, and a plan never makes a change small: one plain change is a small change, whose one criterion is "
            f"`criteria.md` in the task directory and which has no plan (`stages/new.md`, \"A small change\"). A plan's criteria are a full change's: "
            f"its lead writes `Size: full, because ...`, and the personas read them (`stages/plan.md`, step 1)",
        )

    def changes(self) -> dict:
        """The approved criteria and their recorded changes, through the one script that writes them."""
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


def needs_alone(command: str, alone: list[str]) -> bool:
    """Whether a test belongs to a suite that needs the machine to itself: its command starts with
    the words of one of the settings' `checks.alone`, the last of which may also be a folder of the
    test's path (`sh tests/e2e` holds `sh tests/e2e/export.sh`). Words, so that a test's own file
    or filter after the suite's command still counts, and `npx playwright` never matches `npx play`."""
    try:
        words = shlex.split(command)
    except ValueError:
        return False
    for line in alone:
        try:
            own = shlex.split(line)
        except ValueError:
            continue
        if not own or len(words) < len(own) or words[:len(own) - 1] != own[:-1]:
            continue
        word, last = words[len(own) - 1], own[-1]
        if word == last or word.startswith(last.rstrip("/") + "/"):
            return True
    return False


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
    found = task.criteria()
    untested = [criterion["n"] for criterion in found["criteria"] if not criterion["tests"] and not criterion["no_test"]]
    if untested:
        raise CriteriaError(
            f"criterion {untested[0]} names no test: every criterion is held by a test at the end of a build. "
            f"Add `- test: `COMMAND` in `FILE`` under it in {'the small change`s criteria.md' if found['small'] else 'the plan'}, or `- no test: REASON` when no test can hold it",
        )
    dirty = git(task.worktree, "status", "--porcelain")
    if dirty:
        raise CriteriaError(f"the worktree has changes nobody committed:\n{dirty}\ncommit them or remove them: this check runs what the branch holds, and they are not in it")
    base_branch = task.settings["branch"]["base"]
    onto = f"origin/{base_branch}" if git(task.main, "remote", "get-url", "origin", check=False) else str(base_branch)
    tip = git(task.worktree, "rev-parse", "HEAD")
    base = git(task.worktree, "merge-base", tip, onto)
    if base == tip:
        raise CriteriaError(f"the branch has no commit beyond {onto}, so there is no change for a test to hold")
    tests = [(criterion["n"], test) for criterion in found["criteria"] for test in criterion["tests"]]
    for number, test in tests:
        for file in test["files"]:
            # --: a name that starts with a hyphen is still a name
            kind = run(["git", "-C", str(task.worktree), "cat-file", "-t", "--", f"{tip}:{file}"], check=False).stdout.strip()
            if kind != "blob":
                raise CriteriaError(
                    f"criterion {number}: {file!r} is {'a folder' if kind == 'tree' else 'not a file'} on the branch. Name each file that holds the test, "
                    "one by one and relative to the root: a folder would lay the change itself over the base commit",
                )
    without = [{"criterion": criterion["n"], "why": criterion["no_test"]} for criterion in found["criteria"] if criterion["no_test"]]
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
            raise CriteriaError("another check of this task's criteria runs now; wait for it to end") from error
        places = {"branch": task.worktree.parent / f"{task.slug}.red-tip", "base": task.worktree.parent / f"{task.slug}.red-base"}
        # every worktree of this check for this task, whatever its last word: a slug holds no dot,
        # so the pattern is this task's alone
        for place in sorted({*places.values(), *task.worktree.parent.glob(f"{task.slug}.red-*")}):
            stuck = remove(task, place)
            if stuck:
                raise CriteriaError(stuck)
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

        alone = task.settings["checks"]["alone"]

        def outcome(command: str, where: Path, test: bool = False) -> int:
            # through a shell, as the commands of the checks run: a test command is a line the project would type;
            # a test of a suite that needs the machine to itself runs under its lock, which project.py holds
            line: str | list[str] = command
            if test and needs_alone(command, alone):
                line = [sys.executable, "-B", str(SCRIPTS / "project.py"), "--repo", str(task.main), "alone", "--", command]
            proc = subprocess.Popen(line, shell=isinstance(line, str), cwd=where, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, start_new_session=True)  # noqa: S602
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
                    raise CriteriaError(f"git {' '.join(args[:2])} failed: {said.read().decode(errors='replace').strip()}")

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
                for command in task.settings["checks"]["setup"]:
                    code = outcome(command, place)
                    setup.append({"on": name, "command": command, "exit": code})
                    if code != 0:
                        where = "a fresh worktree of the branch" if name == "branch" else "a fresh worktree of the base commit, with the test files laid over it"
                        raise CriteriaError(f"`{command}` of checks.setup failed in {where} (exit {code}), so no test could run there; correct that command in .lem/project.toml")
                if name == "base":
                    # looked for before any test runs there, which might write the file
                    absent = [unstarted(test["command"], place) for _, test in tests]
                codes[name] = [outcome(test["command"], place, test=True) for _, test in tests]
        except KeyboardInterrupt:
            failure = "the check was stopped, and its commands are ended"
        except CriteriaError as error:
            failure = str(error)
        finally:
            stop()
            signal.signal(signal.SIGTERM, before)
            stuck = [problem for problem in (remove(task, place) for place in places.values()) if problem]
            lock.close()
        # A worktree that stayed is said whatever else went wrong: the first failure does not hide it.
        if failure or stuck:
            raise CriteriaError("; ".join([*([failure] if failure else []), *(stuck or ["its worktrees are removed"] if failure else stuck)]))
        for (number, test), green, red, lacked in zip(tests, codes["branch"], codes["base"], absent):
            problem = None
            if green != 0:
                problem = (
                    f"fails in a fresh worktree of the branch (exit {green}). If it passes in the task's worktree, it needs something a fresh one "
                    "lacks: put the commands that make it into checks.setup of .lem/project.toml"
                )
            elif red == 0:
                problem = "passes on the base commit too, so it does not test the change"
            elif red in (126, 127) or lacked:
                problem = (
                    f"does not start on the base commit (exit {red}), so its failure there proves nothing. If a file it needs is a helper of the test, "
                    "name it among the criterion's files; if what is absent is the change itself, make the test fail on it and not stop before it"
                )
            results.append({"criterion": number, "command": test["command"], "files": test["files"], "on_branch": green, "on_base": red, "problem": problem})
    ok = not any(result["problem"] for result in results)
    task.log("task.red", ok=ok, digest=found["digest"], base=base[:9], tip=tip[:9], tests=results, without_a_test=without, run_without=run_without)
    return {
        "task": task.slug, "ok": ok, "digest": found["digest"], "base": base[:9], "tip": tip[:9], "setup": setup, "tests": results,
        "without_a_test": without, "run_without": run_without,
    }


def reads_of(task: Task) -> list[dict]:
    """The task's reads of its criteria, oldest first, from the log `project.py` writes: its
    `criteria.read` events, and the `stories.read` events an older Lem wrote, whose count of what was
    read is `stories`. A later change may drop the old name once no task with such an event is open."""
    log = task.directory.parent.parent / "events.jsonl"
    found = []
    for line in (log.read_text(encoding="utf-8").splitlines() if log.is_file() else []):
        if '"criteria.read"' in line or '"stories.read"' in line:
            record = json.loads(line)
            if record.get("event") in READ_EVENTS and record.get("task") == task.slug:
                found.append(record)
    return found


# The events of a read of the criteria: the one of now, and the one an older Lem wrote.
READ_EVENTS = ("criteria.read", "stories.read")


# The automatic approvals, which no word of his gave in the moment: the read of a full change from a
# complete request, and Lem's approval of a small change in his name (`by: lem`; an older Lem kept it
# as `by: correction`). Each is a task's first contract only.
AUTOMATIC = {"read": "a read freezes only the first contract", "lem": "Lem approves a small change in the owner's name only as the first contract"}


def first_contract(task: Task, by: str) -> None:
    """An automatic approval is only the first contract of a task: once criteria are approved, by
    him, by Lem for a small change or by a read, a criterion changes only through its record and the size only
    through his own approval, which is always allowed and always makes a new number."""
    kept = task.approved()
    if kept is not None:
        number = kept.get("number") or 1 + len(kept.get("history", []))
        raise CriteriaError(
            f"{task.slug} has approval {number} of its criteria already (by {kept['by']}): {AUTOMATIC[by]}. "
            f"A criterion changes through its record, `lem decisions criterion {task.slug} ...`, and the size only through the owner's own approval, "
            f"`lem criteria approve {task.slug} --file FILE`",
        )


def cmd_approve(task: Task, file: str, by: str, plan: bool = False) -> dict:
    """Keep the criteria that were approved, word for word, with a digest and a number of their own,
    and log the event. Each approval is a new one, also of a text approved before. The check of
    what is approved already and the write are one step under the task's lock, so an approval of
    his and an automatic one that come at one time never both pass."""
    source = Path(file)
    if not source.is_file():
        raise CriteriaError(f"{file} is not a file; --file names the criteria the owner approved, in the form `lem criteria --help` shows")
    text = source.read_text(encoding="utf-8")
    read = parse(text, source.name)
    tested = [criterion["n"] for criterion in read["criteria"] if criterion["tests"] or criterion["no_test"]]
    # the plan's own criteria carry the lead's test lines, which are no part of a criterion's text
    if tested and not plan:
        raise CriteriaError(f"criterion {tested[0]} of {source.name} has a test line: the criteria the owner approves have none, and the lead adds them in the plan")
    if by == "lem" and read["size"] != "small":
        raise CriteriaError(f"--small approves a small change's one criterion in the owner's name, and {source.name} says `Size: {read['size']}`: a full change waits for the owner's own yes")
    criteria = [{"n": criterion["n"], "text": criterion["text"]} for criterion in read["criteria"]]
    # one mark for this exact set of approved texts; the approval itself is known by its number
    digest = text_digest(read["mark"], [criterion["text"] for criterion in criteria])
    task.directory.mkdir(parents=True, exist_ok=True)
    with (task.directory / "criteria.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if by in AUTOMATIC:
            first_contract(task, by)
        if by == "read":
            # a full change from a complete request: the lead freezes the criteria the personas read, and only when nobody was confused
            reads = reads_of(task)
            last = reads[-1] if reads else None
            if last is None or last.get("digest") != digest:
                raise CriteriaError(
                    f"--read freezes the criteria the newest `criteria.read` of {task.slug} read, and "
                    + ("there is none" if last is None else f"that read was of the criteria with digest {last.get('digest')}, and {source.name} has {digest}")
                    + ": run the read over these criteria first (`stages/plan.md`, step 1)",
                )
            # a read nobody answered is started once more; after the second in a row the build goes on
            if last["answered"] == 0 and (len(reads) < 2 or reads[-2].get("answered") != 0):
                raise CriteriaError(
                    f"nobody answered the newest read of {task.slug}'s criteria: it is started once more (`stages/plan.md`, step 1); "
                    "after a second read in a row that nobody answered, the build goes on with the criteria as they are",
                )
            if last["flagged"] or last["split"]:
                raise CriteriaError(
                    f"the newest read of {task.slug}'s criteria found {'a flagged criterion' if last['flagged'] else 'a split between the families'}: "
                    "the criteria wait for the owner, and only the owner's approval freezes them",
                )
        before = task.approved()
        history = [*before.get("history", []), {key: value for key, value in before.items() if key not in ("history", "task", "text")}] if before else []
        record = {
            "task": task.slug, "number": len(history) + 1, "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            # who approved: the owner; Lem in his name, for a small change that does not wait; or the
            # lead's read of a full change from a complete request, which counts for the plan's check and never as his yes
            "by": by, "size": read["size"], "why": read["why"], "digest": digest, "criteria": criteria, "text": text,
            **({"replaces": before["number"]} if before else {}), "history": history,
        }
        task.approved_file.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        task.log("criteria.approved", by=by, number=record["number"], size=record["size"], why=record["why"], digest=digest, criteria=criteria, **({"replaces": before["number"]} if before else {}))
    return {**record, "file": str(task.approved_file)}


def main() -> None:
    parser = argparse.ArgumentParser(prog="lem criteria", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=".", help="a directory inside the repository (default: the current one)")
    parser.add_argument("step", choices=("approve", "approved", "digest", "show", "record", "red"))
    parser.add_argument("slug")
    parser.add_argument("--file", help="with approve: the criteria the owner approved, in the form above and with no test lines; with digest: the criteria to mark")
    parser.add_argument("--small", action="store_true", help="with approve: Lem approves a small change's one criterion in the owner's name")
    parser.add_argument("--read", action="store_true", help="with approve: the lead of a full change from a complete request freezes the criteria a read in which nobody was confused read")
    args = parser.parse_args()
    try:
        if args.file is not None and args.step not in ("approve", "digest"):
            raise CriteriaError("--file goes with `approve` and `digest`")
        if (args.small or args.read) and args.step != "approve":
            raise CriteriaError("--small and --read go with `approve`")
        if args.small and args.read:
            raise CriteriaError("an approval is Lem's for a small change or the read's of a full change from a complete request, not both: --small or --read")
        task = Task(Path(args.repo).resolve(), args.slug)
        if args.step == "approve":
            if args.read:
                if args.file is not None:
                    raise CriteriaError("--read freezes the plan's own criteria, the ones the read named: it takes no --file; a file of criteria is approved by the owner, without --read")
                # refused before the plan is read, and again under the lock: a task with a contract keeps it
                first_contract(task, "read")
                result = cmd_approve(task, task.criteria()["plan"], "read", plan=True)
            elif args.file is None and args.small:
                # Lem's approval in his name has one place, the task directory's criteria.md
                result = cmd_approve(task, str(task.small_file), "lem")
            elif args.file is None:
                raise CriteriaError("approve needs --file: the criteria the owner approved, in the form `lem criteria --help` shows, with no test lines")
            else:
                result = cmd_approve(task, args.file, "lem" if args.small else "owner")
        elif args.step == "approved":
            kept = task.approved()
            result = {"task": task.slug, "approved": kept} if kept else {
                "task": task.slug, "approved": None, "says": "no approved criteria: the plan's own criteria are their one source",
            }
        elif args.step == "digest":
            if args.file is None:
                found = task.criteria()
                result = {"task": task.slug, "of": found["plan"], "digest": found["criteria_digest"]}
            else:
                if not Path(args.file).is_file():
                    raise CriteriaError(f"{args.file} is not a file; --file names the criteria to mark, in the form `lem criteria --help` shows")
                read = parse(Path(args.file).read_text(encoding="utf-8"), Path(args.file).name)
                result = {"task": task.slug, "of": args.file, "digest": text_digest(read["mark"], [criterion["text"] for criterion in read["criteria"]])}
        elif args.step == "red":
            result = cmd_red(task)
        else:
            result = task.criteria()
            if args.step == "record":
                task.log("task.criteria", size=result["size"], why=result["why"], digest=result["digest"], criteria=result["criteria"])
    except CriteriaError as error:
        sys.exit(f"criteria.py: {error}")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.step == "red" and not result["ok"]:
        bad = next(test for test in result["tests"] if test["problem"])
        sys.exit(f"criteria.py: criterion {bad['criterion']}: `{bad['command']}` {bad['problem']}")


if __name__ == "__main__":
    main()
