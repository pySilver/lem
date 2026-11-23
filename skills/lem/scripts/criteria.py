"""The acceptance criteria of a task: what the owner approved, and the tests that hold
each one.

An acceptance criterion is one business rule of a request in plain language with one
concrete example. The criteria are the owner's document: the owner reads them and not
the plan, and they become the tests. They have one source, the top of the task's plan
file, so that the board, the checks and the text of the pull request cannot drift apart:

    ## Acceptance criteria

    Size: full, because the export gets a new column and two readers of it.

    1. A CSV export holds the gift note of an order: order 1042 with the note "for Ania" has
       that text in its row.
       - test: `python3 -m unittest tests.test_export.GiftNote` in `tests/test_export.py`
    2. An order with no gift note has an empty cell, not the word "None".
       - test: `python3 -m unittest tests.test_export.NoNote` in `tests/test_export.py`

`Size` names the task's track, with the reason after `because`: `full` for the standard
track and `small` for the fast track. A task on the fast track is a request that yields
one criterion and touches nothing careful; its criterion is the owner's own sentence
made exact, and it has no plan: its criterion is the same section in `criteria.md` in
the task's directory, which no commit holds, and the builder adds its test line there. A
branch's plan comes first when it has one, and only a task on the fast track is read
from that file: the criteria of a task on the standard track are at the top of its plan,
and such a task with no plan is refused. A plan never puts a task on the fast track: a
plan that says `Size: small` is refused, with the fast track named as the way for one
plain change, since a fast-track task in a plan would take the standard track with none
of what that path gives (the owner's approval, the personas' read, the polish pass). A
criterion's test is a command and the files that hold the test, each in backticks. A
criterion that no test can hold (a sentence of a document) says so, and that is shown
wherever the criteria are:

       - no test: the change is one paragraph of the README.

A criterion with more than one condition carries its case, numbered steps under its
sentence and before its tests; a criterion with branches may carry its chart, a fenced
`mermaid` block under it at any indent; and a chart of several criteria goes under
`## How it works`, after the section:

    1. A refund lowers the invoice's total, and never below 0:
       1. Invoice 1042 is 100 EUR.
       2. A refund of 130 EUR comes in.
       3. The invoice shows 0, and a credit note holds the other 30 EUR.
       ```mermaid
       flowchart TD
         A["A refund comes in"] --> B{"Larger than the total?"}
       ```
       - test: `python3 -m unittest tests.test_refund` in `tests/test_refund.py`

The case is a part of the criterion, approved with it word for word: a change of a step
is a change of the criterion, which `lem decisions criterion` records with the whole
criterion, its sentence and its steps, in `--was` and `--now`. The chart and
`## How it works` are no part of it: the digests leave them out, and they change with no
record. Each criterion in the JSON carries `case`, its steps, and `chart`, the block's
text without its fences, and the read carries `how`, the body of `## How it works`.

    lem criteria approve SLUG --file FILE [--shown DIGEST]
    lem criteria approve SLUG --small [--file FILE]
    lem criteria approve SLUG --read
    lem criteria approve SLUG --file FILE --alone
                              keep the criteria the owner approved, as FILE has them: the same
                              section with no test lines, which the lead adds. --shown: the
                              digest of FILE's bytes as the owner's page showed them (the board
                              gives it); FILE is read once, and a file that changed since is
                              refused with nothing approved. --small: Lem
                              approves the one criterion of a task on the fast track in the owner's name, as the task's
                              first contract only, and the owner may still say "standard"; its file is
                              `criteria.md` in the task directory unless --file names another. --read: the lead of a
                              task on the standard track from a complete request freezes
                              the plan's criteria, which a read found nobody confused by, as the
                              task's first contract; refused when the task has any approval, and
                              after one read in which nobody answered, until a second such read
                              in a row lets the build go on. It
                              counts for the plan's check and for `lem decisions criterion`, and never
                              as the owner's yes. --alone: Lem or the lead approves the criteria of a task
                              on the standard track while the task runs without the owner (`lem project owner away`, a night),
                              as `by: alone`; refused while it runs with him and after any approval
                              but a fast-track one, Lem's or an `alone` one (a night's task that
                              grew into a full change: both stay in the history). On the fast track a
                              request that is not the owner's own sentence (the night's mark, or
                              `request by: someone else` in its brief or its state) gets no --small:
                              while the task runs with him its criterion waits for his own approval
                              (--file), and --alone is refused; while it runs without him --alone
                              approves it. --alone is never his yes either: the pull
                              request is not green for it, and his own approval after it takes over
    lem criteria approved SLUG the approved criteria of the task, or null when it has none
    lem criteria digest SLUG [--file FILE]
                              the digest of the `Size` line and the texts of the criteria, without tests: of FILE,
                              or of the task's plan
    lem criteria show SLUG    the criteria of the task's plan, or the `criteria.md` of a task on the fast track, as
                              JSON; `small` says which, and `plan` names the file
    lem criteria record SLUG  the same, and one event for the board
    lem criteria red SLUG     each criterion's tests pass on the branch and fail on the base commit
    lem criteria inputs SLUG  what a run of `red` depends on, as it stands now, without a run: the tip, the
                              base commit, the plan file, and the settings' checks.setup and checks.serial

Approved criteria are frozen as written. `approve` keeps them in `criteria.json` in the
task's directory, with their text, a digest and a number of their own (approval 1, 2,
...), the earlier approvals under `history`, and logs one `criteria.approved` event. An
approval of a text approved before is still a new approval, with no change after it.
From then on the plan's criteria are the expected ones: the newest approval's criteria
with each change of them that `lem decisions criterion` recorded after it applied in the
order of the record (`lem decisions changes SLUG` gives them). They are compared text
for text and in order, with each run of spaces as one, so how a criterion is broken into
lines does not count; the plan's `Size:` is the approved track, which only the owner's
next approval changes. `show`, `record` and `red` refuse a plan that differs, and name
the first criterion that does. So the lead can neither reword, drop nor add a criterion
without the record saying so, and the pull request is not green for each such change. A
task with no approved criteria (a task on the standard track from a complete request)
has the plan's criteria as their one source.

`digest` gives the digest of a set of criteria without their tests: a file's, or the
plan's. It is what an approval keeps and what the record of the personas' read names, so
that a read of other criteria than the approved ones shows.

`red` is a machine check with no model in it. A test that also passes on the base commit
does not test the change, and a criterion with no test at the end of a build is refused.

What a run of `red` gives depends on five inputs, and on nothing else: the branch's tip;
the base commit, the merge-base of the tip and origin's base branch at the time of the
run; the plan file the read of the criteria chose, by the settings' `paths.plans` and
`paths.plan_file`; and the settings' `checks.setup` and `checks.serial`. `red` reports
them whole as `inputs`, and `inputs` gives them as they stand now, after the same read
of the criteria, which refuses as `red` would: two runs with the same five ran the same
tests on the same trees, under the same approved criteria.

It never moves the task's worktree. It makes two worktrees of its own beside it, each
with the commands of the settings' `checks.setup` run in it first (what a fresh worktree
of this project needs before its tests can start), so that nothing one run writes
reaches the other:

- one at the branch's tip, where each test must pass. A test that passes in the task's
  worktree and not here needs something a fresh worktree lacks, and the check says so: a
  failure on the base commit would then prove nothing;
- one at the base commit with only the named test files of the branch laid over it,
  where each test must fail. A command that does not start there is no proof: one that
  exits 126 or 127, the codes a shell gives for a program it cannot find or run, and one
  that starts a shell (`sh`, `bash`, `dash`, `ksh`, `zsh`) or Python (`python`,
  `python3`, `python3.N`) on a script file the base commit lacks, which bash ends with
  127, and dash and Python with 2; the refusal names that file. `python3 -m MODULE` and
  `-c TEXT` start no script file, and are not looked at. An exit of 2 by itself is no
  such sign: an assertion may end a test with it. A helper that a test's own script
  starts is caught only by the code its shell gives, so a test starts its helpers by
  their path (`./tests/helper.sh`): every shell ends that with 127 when the file is
  not there.

What the check cannot tell: whether a file of the branch that the base run lacked is the
change or a helper of the test. A test of a new module fails on the base commit because
the module is absent, and that is the proof wanted; a test whose new helper was not
named fails the same way and proves nothing. Only the criterion's own list of files
tells the two apart, so the result names every file the base run lacked (`run_without`),
for the one who reads the change.

A test that needs the machine to itself runs under the repository's one lock for such
commands, through `lem project serial`: a test whose command starts with the words of a
command of the settings' `checks.serial`, whose last word may be a folder of the test's
path (`npx playwright test e2e/export.spec.ts` under `npx playwright test`, `sh
tests/e2e/b.sh` under `sh tests/e2e`), so that two checks of two tasks, or a check and a
builder, never run such a suite at one moment.

One check of a task runs at a time. The two worktrees are removed afterwards, also when
a command fails or the check is stopped, with every process a command left behind; what
a killed run left is removed by the next run. A worktree that cannot be removed is an
error with its path.
"""

import sys

if sys.version_info < (3, 11):
    # an old python3 must still load this file, so that it can say what it needs and not
    # a traceback
    sys.exit(
        "criteria.py: Lem needs Python 3.11 or newer, and this python3 is "
        f"{sys.version.split()[0]}; put a newer one first on PATH, "
        "or run this file with it"
    )

import argparse
import fcntl
import hashlib
import importlib
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCRIPTS = Path(__file__).resolve().parent
# The one place that builds and finds a plan's name, shared with project.py.
sys.dont_write_bytecode = True
sys.path.insert(0, str(SCRIPTS))
import lem_plans  # noqa: E402

# How this script calls a sibling: in this process, as one command of it.
import lem_sibling  # noqa: E402
import lem_state  # noqa: E402  (how a JSON-lines file is split into its lines)

# The release a task began on, and the rule that stops a command for a task two
# releases back.
lem_release = importlib.import_module("lem_release")
# How long a command of the check gets after each signal of a stop, in seconds, and how
# long a serial test's wrapper (`project.py serial`) gets after its term: its own
# cleanup sends its command a term, waits 3 s, sends a kill and waits 3 s more
# (`cmd_serial`), and one second is left for its exit, as land.py's SERIAL_GRACE gives a
# serial command of the checks. A wrapper killed before its cleanup ends leaves a test
# that ignores a term running, with the lock free.
GRACE = 3.0
SERIAL_GRACE = 7.0
# The track of a task, as the `Size:` line names it: `full`, the standard track with its
# plan and lead, or `small`, the fast track of one builder.
SIZES = ("full", "small")
# The line of a task's brief, or of a block of its state, that says someone else wrote
# its complete request (land.py's SOMEONE_ELSE).
SOMEONE_ELSE = "request by: someone else"
HEADING = re.compile(r"^##\s+Acceptance criteria\s*$")
SIZE = re.compile(r"^Size:\s*(\w+)\s*(?:,\s*because|:|—|-)\s*(.+)$", re.IGNORECASE)
CRITERION = re.compile(r"^(\d+)\.\s+(.+)$")
TEST = re.compile(r"^\s+-\s+test:\s+`([^`]+)`\s+in\s+(.+)$")
NO_TEST = re.compile(r"^\s+-\s+no test:\s+(.+)$")
FILES = re.compile(r"`([^`]+)`")
# A step of a criterion's case: a numbered line under its sentence, indented.
STEP = re.compile(r"^\s+\d+[.)]\s+\S")
HOW = re.compile(r"^##\s+How it works\s*$")
# The shells a test command may start a script with, by the name of the program.
SHELLS = ("sh", "bash", "dash", "ksh", "zsh")
# Python, by the name of the program: `python`, `python3` and `python3.N`, which end
# with exit 2 when their script file is not there (`python3 -I -B missing.py`, checked
# on 2026-11-21).
PYTHON = re.compile(r"python(3(\.\d+)?)?")


class CriteriaError(Exception):
    pass


def run(
    args: list[str], cwd: Path | None = None, *, check: bool = True
) -> subprocess.CompletedProcess:
    ran = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)
    if check and ran.returncode != 0:
        raise CriteriaError(
            f"{' '.join(args[:4])} failed: {(ran.stderr or ran.stdout).strip()}"
        )
    return ran


def git(where: Path, *args: str, check: bool = True) -> str:
    return run(["git", "-C", str(where), *args], check=check).stdout.strip()


def script(name: str, repo: Path, *args: str) -> str:
    ran = lem_sibling.run(SCRIPTS / name, repo, *args)
    if ran.returncode != 0:
        raise CriteriaError(
            ran.stderr.strip().removeprefix(f"{name}: ") or f"{name} {args[0]} failed"
        )
    # a line project.py writes on stderr when it succeeds (the settings read from the
    # base branch) is this script's to say too
    if ran.returncode == 0 and ran.stderr:
        sys.stderr.write(ran.stderr)
    return ran.stdout


def whole(criterion: dict) -> str:
    """A criterion as the owner approved it: its sentence and the steps of its case, one
    to a line. What a digest marks and what a recorded change names; its chart is no
    part of it."""
    return "\n".join([criterion["text"], *criterion.get("case", [])])


def fences(lines: list[str]) -> list[tuple[int, int, str, int]]:
    """Each fenced block of a text, at any indent: its first and last line, its info
    word, its indent. A fence closes only on a line of its own character, at least as
    long as the one that opened it, with nothing after it: a shorter fence inside is a
    part of the block. One that never closes runs to the end of the text."""
    found: list[tuple[int, int, str, int]] = []
    opened: tuple[str, int, int, str, int] | None = None
    for i, line in enumerate(lines):
        mark = re.match(r"( *)(`{3,}|~{3,})(.*)$", line)
        if opened is None:
            if mark and not (mark.group(2)[0] == "`" and "`" in mark.group(3)):
                info = mark.group(3).strip().split()
                opened = (
                    mark.group(2)[0],
                    len(mark.group(2)),
                    i,
                    info[0].lower() if info else "",
                    len(mark.group(1)),
                )
            continue
        if (
            mark
            and mark.group(2)[0] == opened[0]
            and len(mark.group(2)) >= opened[1]
            and not mark.group(3).strip()
        ):
            found.append((opened[2], i, opened[3], opened[4]))
            opened = None
    if opened is not None:
        found.append((opened[2], len(lines) - 1, opened[3], opened[4]))
    return found


def parse(text: str, name: str) -> dict:
    """The criteria section of a plan as a dict; a section that does not have the form
    is refused with the line."""
    lines = text.splitlines()
    # A plan may show the form in a code fence: what is inside one is an example, never
    # the section.
    blocks = fences(lines)
    fenced = {i for first, last, _, _ in blocks for i in range(first, last + 1)}
    start = next(
        (i for i, line in enumerate(lines) if i not in fenced and HEADING.match(line)),
        None,
    )
    if start is None:
        raise CriteriaError(
            f"{name} has no `## Acceptance criteria` section; the plan opens with it, "
            "as `lem criteria --help` shows"
        )
    end = next(
        (
            i
            for i in range(start + 1, len(lines))
            if i not in fenced and lines[i].startswith("## ")
        ),
        len(lines),
    )
    # a `mermaid` block in the section is the chart of the criterion above it, at any
    # indent; any other block is an example
    charts = {
        first: (last, indent)
        for first, last, info, indent in blocks
        if info == "mermaid" and start < first < end
    }
    size = why = None
    criteria: list[dict] = []
    for number, line in enumerate(lines[start + 1 : end], start + 2):
        i = number - 1
        where = f"{name}:{number}"
        if i in charts and criteria:
            if criteria[-1]["chart"] is not None:
                raise CriteriaError(
                    f"{where}: criterion {criteria[-1]['n']} has a chart already; "
                    "one chart for one criterion, and a chart of several goes under "
                    "`## How it works`, after the section"
                )
            last, indent = charts[i]
            body = [
                row[min(indent, len(row) - len(row.lstrip(" "))) :]
                for row in lines[i + 1 : last]
            ]
            criteria[-1]["chart"] = "\n".join(body).strip("\n") or None
        if i in fenced or not line.strip():
            continue
        if size is None:
            found = SIZE.match(line.strip())
            word = found.group(1).lower() if found else None
            if not found or word not in SIZES or not found.group(2).strip():
                raise CriteriaError(
                    f"{where}: the section starts with `Size: full, because ...` or "
                    f"`Size: small, because ...`, and this line is {line.strip()!r}"
                )
            size, why = word, found.group(2).strip()
            continue
        criterion = CRITERION.match(line)
        if criterion:
            if int(criterion.group(1)) != len(criteria) + 1:
                raise CriteriaError(
                    f"{where}: the criteria are numbered 1, 2, 3 in order, and this "
                    f"one is {criterion.group(1)} after {len(criteria)}; "
                    "the steps of a criterion's case are indented under its sentence",
                )
            criteria.append(
                {
                    "n": len(criteria) + 1,
                    "text": criterion.group(2).strip(),
                    "case": [],
                    "chart": None,
                    "tests": [],
                    "no_test": None,
                }
            )
            continue
        if not criteria:
            raise CriteriaError(
                f"{where}: a criterion starts a line with its number, as in "
                f"`1. A rule, with one example.`, and this line is {line.strip()!r}"
            )
        test, none = TEST.match(line), NO_TEST.match(line)
        if test:
            files = FILES.findall(test.group(2))
            if not files:
                raise CriteriaError(
                    f"{where}: a test names its command and its files in backticks, as "
                    "in - test: `COMMAND` in `FILE`"
                )
            criteria[-1]["tests"].append(
                {"command": test.group(1).strip(), "files": files}
            )
        elif none:
            criteria[-1]["no_test"] = none.group(1).strip()
        elif line.lstrip().startswith("- "):
            raise CriteriaError(
                f"{where}: under a criterion a line is `- test: `COMMAND` in `FILE`` "
                f"or `- no test: REASON`, and this one is {line.strip()!r}"
            )
        elif criteria[-1]["tests"] or criteria[-1]["no_test"]:
            raise CriteriaError(
                f"{where}: the text of a criterion comes before its tests; "
                f"this line comes after them: {line.strip()!r}"
            )
        elif STEP.match(line) or (criteria[-1]["case"] and line.rstrip().endswith(":")):
            # a step of its case, or a label between two runs of it ("After:"), is a
            # line of its own
            criteria[-1]["case"].append(line.strip())
        elif criteria[-1]["case"]:
            # a step written over two lines
            criteria[-1]["case"][-1] += " " + line.strip()
        else:
            criteria[-1]["text"] += " " + line.strip()
    if size is None or not criteria:
        raise CriteriaError(
            f"{name}: the `## Acceptance criteria` section holds no "
            f"{'criterion' if size else 'Size line'}"
        )
    if size == "small" and len(criteria) != 1:
        raise CriteriaError(
            f"{name}: a task on the fast track has one criterion, and this one has "
            f"{len(criteria)}: it takes the standard track"
        )
    both = [s["n"] for s in criteria if s["tests"] and s["no_test"]]
    if both:
        raise CriteriaError(
            f"{name}: criterion {both[0]} names a test and says that it has none; "
            "keep one of the two"
        )
    # one mark for this exact set of criteria and tests, their cases with them and their
    # charts not: a result of the check belongs to the set it ran on
    marked = [
        {key: value for key, value in criterion.items() if key != "chart"}
        for criterion in criteria
    ]
    digest = hashlib.sha256(
        json.dumps([size, marked], sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()[:12]
    return {
        "size": size,
        "why": why,
        "digest": digest,
        "criteria": criteria,
        "how": how_it_works(lines, fenced),
    }


def how_it_works(lines: list[str], fenced: set[int]) -> str | None:
    """The body of the plan's `## How it works`, as markdown: the chart of several
    criteria and the sentence it shows. None when the plan has none."""
    start = next(
        (i for i, line in enumerate(lines) if i not in fenced and HOW.match(line)), None
    )
    if start is None:
        return None
    end = next(
        (
            i
            for i in range(start + 1, len(lines))
            if i not in fenced and re.match(r"#{1,2}\s", lines[i])
        ),
        len(lines),
    )
    return "\n".join(lines[start + 1 : end]).strip() or None


def text_digest(size: str, texts: list[str]) -> str:
    """One mark for a set of criteria without their tests: the word of their `Size` line
    and their texts, with each run of spaces as one. An approval keeps it, and the
    record of the personas' read names it."""
    return hashlib.sha256(
        json.dumps(
            [size, [" ".join(text.split()) for text in texts]], ensure_ascii=False
        ).encode()
    ).hexdigest()[:12]


def against(read: dict, changes: dict, name: str, slug: str) -> None:
    """Refuse a plan whose criteria are not the expected ones: the approved criteria
    with every recorded change applied, text for text and in order, and of the
    approved track."""
    fix = (
        "The plan's criteria are the approved ones with each recorded change "
        f"(`lem decisions changes {slug}` gives them), word for word, with only the "
        "test lines added. A criterion the build changes, adds or removes is recorded "
        f"first: `lem decisions criterion {slug} --changed N --was TEXT --now TEXT`, "
        "`--added N --now TEXT` or `--removed N --was TEXT`, with --why and --decision "
        "ID or --by lead|personas"
    )
    approved = changes["approved"]["size"]
    if read["size"] != approved:
        raise CriteriaError(
            f"{name} says `Size: {read['size']}`, and the owner approved its criteria "
            f"with `Size: {approved}`: a change of the track is the owner's only, by "
            "the owner's approval of the criteria again "
            f"(`lem criteria approve {slug} --file FILE`)",
        )
    expected = changes["expected"]
    now = [whole(criterion) for criterion in read["criteria"]]
    for number, (want, have) in enumerate(zip(expected, now, strict=False), start=1):
        if want.split() != have.split():
            raise CriteriaError(
                f"criterion {number} of {name} says {have!r}, and the expected "
                f"criterion {number} is {want!r}. {fix}"
            )
    if len(now) > len(expected):
        raise CriteriaError(
            f"criterion {len(expected) + 1} of {name}, {now[len(expected)]!r}, is not "
            f"among the expected criteria, which end at {len(expected)}. {fix}"
        )
    if len(now) < len(expected):
        raise CriteriaError(
            f"{name} lacks criterion {len(now) + 1}, {expected[len(now)]!r}, which the "
            f"expected criteria hold. {fix}"
        )


def project_now(repo: Path) -> tuple[dict, list[dict], Path]:
    """The settings, every task as the state files say now, and the state folder, with
    the settings loaded once and handed to the functions of `project.py` that
    need them."""
    path = SCRIPTS / "project.py"
    if not lem_sibling.in_form(path):
        # a stand-in in project.py's place (a test's copy of the scripts) answers each
        # command as a process
        settings = json.loads(script("project.py", repo, "show"))
        if settings["settings"] is None:
            raise CriteriaError(
                "this repository has no .lem/settings.toml; `/lem init` writes it"
            )
        return (
            settings,
            json.loads(script("project.py", repo, "tasks")),
            Path(script("project.py", repo, "state-dir").strip()),
        )
    project = lem_sibling.module(path)
    try:
        root = project.repo_root(repo)
        settings = project.load(root)
        if settings["settings"] is None:
            raise CriteriaError(
                "this repository has no .lem/settings.toml; `/lem init` writes it"
            )
        return settings, project.read_tasks(root, settings), project.state_root(root)
    except project.SettingsError as error:
        raise CriteriaError(str(error)) from error


class Task:
    def __init__(self, repo: Path, slug: str) -> None:
        self.settings, tasks, state = project_now(repo)
        record = next((task for task in tasks if task["slug"] == slug), None)
        if record is None:
            raise CriteriaError(
                f"no task {slug!r}; the tasks are: "
                f"{', '.join(task['slug'] for task in tasks) or 'none yet'}"
            )
        self.mode = record.get("mode", "with-owner")
        # the date of the night that opened the task (its mark), or None for a task of
        # the day
        self.night = record.get("night")
        self.slug = slug
        self.repo = repo
        self.main = Path(self.settings["main"])
        root = Path(self.settings["root"]).resolve()
        self.worktree = (
            self.main
            / Path(self.settings["places"]["worktrees"]["path"]).relative_to(root)
            / slug
        )
        self.directory = state / "tasks" / slug
        self.plans = self.worktree / Path(
            self.settings["paths"]["plans"]["path"]
        ).relative_to(root)
        self.approved_file = self.directory / "criteria.json"
        # the one criterion of a task on the fast track, with its test line: it has no
        # plan, and no commit holds this file
        self.small_file = self.directory / "criteria.md"

    def not_his(self) -> str | None:
        """Why the task's request is not the owner's own sentence, or None when it is:
        the night opened it (its mark, `task-dir --night`), or its brief or a block of
        its state says `request by: someone else`. Never the mode: a request he types
        while his mark says away is his own."""
        if self.night:
            return f"the night of {self.night} opened it"
        for file in (self.directory / "brief.md", self.directory / "state.md"):
            if file.is_file() and SOMEONE_ELSE in [
                line.strip()
                for line in file.read_text(
                    encoding="utf-8", errors="replace"
                ).splitlines()
            ]:
                return "someone else wrote its request"
        return None

    def read_mode(self) -> str:
        """The task's mode as the state files and the owner's mark say now: another
        repository's session may mark the owner away or back while a command of this
        one runs."""
        _, tasks, _ = project_now(self.repo)
        record = next((task for task in tasks if task["slug"] == self.slug), None)
        if record is None:
            raise CriteriaError(
                f"the task {self.slug!r} is gone from the state folder while this "
                "command ran; nothing was approved"
            )
        self.mode = record.get("mode", "with-owner")
        return self.mode

    def need_worktree(self) -> None:
        # the criteria are approved before the task has a worktree; its plan is read
        # from one
        if not (self.worktree / ".git").exists():
            raise CriteriaError(f"the task has no worktree at {self.worktree}")

    def approved(self) -> dict | None:
        """The criteria the owner approved, as `approve` kept them; none for a
        task without."""
        kept = self.approved_file
        if not kept.is_file():
            return None
        try:
            return json.loads(kept.read_text(encoding="utf-8"))
        except ValueError as error:
            raise CriteriaError(
                f"{kept} does not read as JSON ({error}); it is written by "
                "`lem criteria approve` only"
            ) from error

    def criteria(self) -> dict:
        self.need_worktree()
        # the plan of this task and of no other: the name `paths.plan_file` gives, with
        # the task's whole slug, or for a task resumed from a dropped one
        # (`lem project resume`) the old task's plan, which its branch holds until its
        # lead writes one of its own
        pattern = self.settings["paths"]["plan_file"]["pattern"]
        found = lem_plans.found(
            self.plans,
            pattern,
            self.slug,
            lem_plans.resumed_from(self.directory.parent, self.slug),
        )
        small = not found and self.small_file.is_file()
        if not found and not small:
            raise CriteriaError(
                f"no plan of this task in {self.plans}: "
                f"its name is {pattern.replace('<slug>', self.slug)} "
                f"(`lem project plan-file {self.slug}` prints it); only a task on the "
                "fast track keeps its criterion in the task directory instead, "
                f"in {self.small_file}",
            )
        plan = self.small_file if small or found is None else found
        read = parse(plan.read_text(encoding="utf-8"), plan.name)
        if small and read["size"] != "small":
            raise CriteriaError(
                f"{plan} says `Size: {read['size']}`: only a task on the fast track "
                "(`Size: small`) keeps its criterion in the task directory. "
                "The criteria of a task on the standard track are at the top of its "
                f"plan, and the branch has none in {self.plans}: its "
                f"lead writes {pattern.replace('<slug>', self.slug)}",
            )
        changes = self.changes()
        digest = text_digest(
            read["size"], [whole(criterion) for criterion in read["criteria"]]
        )
        if small and changes["approved"] is None:
            raise CriteriaError(
                f"the fast track's criterion in {plan} has no approval: "
                "Lem approves it in the owner's name before its builder starts, `lem "
                f"criteria approve {self.slug} --file {plan} --small`"
            )
        if changes["approved"] is None:
            self.no_small_plan(read, plan, small=small)
            return {
                "task": self.slug,
                "plan": str(plan),
                "small": small,
                **read,
                "criteria_digest": digest,
                "approved": None,
                "approvals": [],
                "changes": [],
                "history": [],
            }
        # the approved track first: a plan of another track than the owner approved
        # says that
        against(read, changes, plan.name, self.slug)
        self.no_small_plan(read, plan, small=small)
        return {
            "task": self.slug,
            "plan": str(plan),
            "small": small,
            **read,
            "criteria_digest": digest,
            **{
                key: changes[key]
                for key in ("approved", "approvals", "changes", "history")
            },
        }

    def no_small_plan(self, read: dict, plan: Path, *, small: bool) -> None:
        """Refuse a plan file that says `Size: small`: a plan never puts a task on the
        fast track. One plain change takes the fast track, with its criterion in the
        task directory and no plan; a fast-track task in a plan would land with no
        approval of the owner's, no read and no polish pass."""
        if small or read["size"] != "small":
            return
        raise CriteriaError(
            f"{plan.name} says `Size: small`, and a plan never puts a task on the fast "
            "track: one plain change takes the fast track, whose one criterion is "
            "`criteria.md` in the task directory and which has no plan "
            '(`stages/new.md`, "The fast track"). A plan\'s criteria are the standard '
            "track's: its lead writes `Size: full, because ...`, and the personas read "
            "them (`stages/plan.md`, step 1)",
        )

    def changes(self) -> dict:
        """The approved criteria and their recorded changes, through the one script that
        writes them."""
        return json.loads(script("decisions.py", self.repo, "changes", self.slug))

    def log(self, event: str, **fields: object) -> None:
        script(
            "project.py",
            self.repo,
            "log",
            self.slug,
            event,
            *(
                f"{key}:={json.dumps(value, ensure_ascii=False)}"
                for key, value in fields.items()
            ),
        )


def unstarted(command: str, where: Path) -> str | None:
    """The script file the command starts a shell or Python on, when it is not in
    `where`; None when the command starts no such file or the file is there. Its exit
    does not say so: bash ends `sh FILE` with no FILE with 127, dash with 2, and Python
    with 2, which an assertion's exit may be too."""
    try:
        words = shlex.split(command)
    except ValueError:
        return None
    if not words:
        return None
    program = Path(words[0]).name
    file = (
        shell_script(words[1:])
        if program in SHELLS
        else python_script(words[1:])
        if PYTHON.fullmatch(program)
        else None
    )
    return file if file is not None and not (where / file).is_file() else None


def shell_script(words: list[str]) -> str | None:
    """The script file a shell's arguments start, or None for standard input
    and `-c TEXT`."""
    rest = iter(words)
    for word in rest:
        if word in ("-o", "+o"):
            next(rest, None)
        elif word == "--":
            return next(rest, None)
        elif (
            word in ("-", "+")
            or word.startswith("--")
            or (word.startswith("-") and "c" in word)
        ):
            # standard input, a long option of one shell, or `-c TEXT`, whose operand is
            # a command: no script file to look for
            return None
        elif not word.startswith(("-", "+")):
            return word
    return None


def python_script(words: list[str]) -> str | None:
    """The script file Python's arguments start, or None for `-m MODULE`, `-c TEXT`,
    standard input and a long option. Short options may share one word (`-IB`), and `-W`
    and `-X` take the rest of their word or the next one."""
    rest = iter(words)
    for word in rest:
        if word == "--":
            return next(rest, None)
        if word == "--check-hash-based-pycs":
            next(rest, None)
            continue
        if word == "-" or word.startswith("--"):
            return None
        if not word.startswith("-"):
            return word
        for i, letter in enumerate(word[1:], start=1):
            if letter in "cm":
                # the module or the command is the operand: no script file to look for
                return None
            if letter in "WX":
                if i == len(word) - 1:
                    next(rest, None)
                break
    return None


def needs_serial(command: str, serial: list[str]) -> bool:
    """Whether a test belongs to a suite that needs the machine to itself: its command
    starts with the words of one of the settings' `checks.serial`, the last of which may
    also be a folder of the test's path (`sh tests/e2e` holds `sh tests/e2e/export.sh`).
    Words, so that a test's own file or filter after the suite's command still counts,
    and `npx playwright` never matches `npx play`."""
    try:
        words = shlex.split(command)
    except ValueError:
        return False
    for line in serial:
        try:
            own = shlex.split(line)
        except ValueError:
            continue
        if not own or len(words) < len(own) or words[: len(own) - 1] != own[:-1]:
            continue
        word, last = words[len(own) - 1], own[-1]
        if word == last or word.startswith(last.rstrip("/") + "/"):
            return True
    return False


def remove(task: Task, place: Path) -> str | None:
    """Remove one worktree of this check, a locked one too. Returns what is in the way
    when it stays."""

    def listed() -> bool:
        return (
            f"worktree {place}\0"
            in run(
                ["git", "-C", str(task.main), "worktree", "list", "--porcelain", "-z"],
                check=False,
            ).stdout
        )

    if not place.exists() and not listed():
        return None
    run(["git", "-C", str(task.main), "worktree", "unlock", str(place)], check=False)
    # twice --force: a worktree with changes, and one that a command locked
    run(
        [
            "git",
            "-C",
            str(task.main),
            "worktree",
            "remove",
            "--force",
            "--force",
            str(place),
        ],
        check=False,
    )
    if place.exists():
        shutil.rmtree(place, ignore_errors=True)
    run(["git", "-C", str(task.main), "worktree", "prune"], check=False)
    if place.exists() or listed():
        return (
            f"{place} could not be removed; remove it yourself: git -C {task.main} "
            f"worktree remove --force --force {place}"
        )
    return None


def onto_of(task: Task) -> str:
    """What the branch is measured against: origin's base branch, or the base branch
    itself in a repository with no origin."""
    base_branch = task.settings["branch"]["base"]
    return (
        f"origin/{base_branch}"
        if git(task.main, "remote", "get-url", "origin", check=False)
        else str(base_branch)
    )


def inputs(task: Task, found: dict) -> dict:
    """The five inputs a run of the criteria's tests depends on, as they stand now: the
    tip, the base commit, the plan file of FOUND (the read of the criteria, which
    `paths.plans` and `paths.plan_file` chose), and the settings' `checks.setup` and
    `checks.serial`. The settings are the ones this read loaded, the main checkout's
    when the landing runs it."""
    tip = git(task.worktree, "rev-parse", "HEAD")
    return {
        "tip": tip,
        "base": git(task.worktree, "merge-base", tip, onto_of(task)),
        "plan": found["plan"],
        "setup": list(task.settings["checks"]["setup"]),
        "serial": list(task.settings["checks"]["serial"]),
    }


def cmd_inputs(task: Task) -> dict:
    """What a run of `red` would depend on now, without the run: the read of the
    criteria first, which refuses in the words `red` gives, then its five inputs."""
    return {"task": task.slug, "inputs": inputs(task, task.criteria())}


def cmd_red(task: Task) -> dict:
    found = task.criteria()
    untested = [
        criterion["n"]
        for criterion in found["criteria"]
        if not criterion["tests"] and not criterion["no_test"]
    ]
    if untested:
        raise CriteriaError(
            f"criterion {untested[0]} names no test: every criterion is held by a test "
            "at the end of a build. "
            f"Add `- test: `COMMAND` in `FILE`` under it in {'the criteria.md of the task on the fast track' if found['small'] else 'the plan'}, or `- no test: REASON` when no test can hold it",
        )
    dirty = git(task.worktree, "status", "--porcelain")
    if dirty:
        raise CriteriaError(
            f"the worktree has changes nobody committed:\n{dirty}\n"
            "commit them or remove them: this check runs what the branch holds, "
            "and they are not in it"
        )
    # what this run depends on, reported whole: the run below uses these values and
    # no others
    ran = inputs(task, found)
    tip, base = ran["tip"], ran["base"]
    if base == tip:
        raise CriteriaError(
            f"the branch has no commit beyond {onto_of(task)}, "
            "so there is no change for a test to hold"
        )
    tests = [
        (criterion["n"], test)
        for criterion in found["criteria"]
        for test in criterion["tests"]
    ]
    for number, test in tests:
        for file in test["files"]:
            # --: a name that starts with a hyphen is still a name
            kind = run(
                [
                    "git",
                    "-C",
                    str(task.worktree),
                    "cat-file",
                    "-t",
                    "--",
                    f"{tip}:{file}",
                ],
                check=False,
            ).stdout.strip()
            if kind != "blob":
                raise CriteriaError(
                    f"criterion {number}: {file!r} is "
                    f"{'a folder' if kind == 'tree' else 'not a file'} on the branch. "
                    "Name each file that holds the test, one by one and relative to "
                    "the root: a folder would lay the change "
                    "itself over the base commit",
                )
    without = [
        {"criterion": criterion["n"], "why": criterion["no_test"]}
        for criterion in found["criteria"]
        if criterion["no_test"]
    ]
    laid = sorted({file for _, test in tests for file in test["files"]})
    # what the base run lacks: every file the branch changed that is not a named
    # test file
    changed = [
        name
        for name in git(
            task.worktree, "diff", "--name-only", "--no-renames", "-z", base, tip
        ).split("\0")
        if name
    ]
    run_without = sorted(set(changed) - set(laid))
    results: list[dict] = []
    setup: list[dict] = []
    if tests:
        # One check of a task at a time. The lock is the kernel's, and it goes when its
        # process goes, however that is; so whoever holds it knows that a worktree it
        # finds is a dead run's.
        lock = (task.directory / "red.lock").open("w")
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise CriteriaError(
                "another check of this task's criteria runs now; wait for it to end"
            ) from error
        places = {
            "branch": task.worktree.parent / f"{task.slug}.red-tip",
            "base": task.worktree.parent / f"{task.slug}.red-base",
        }
        # every worktree of this check for this task, whatever its last word: a slug
        # holds no dot, so the pattern is this task's alone
        for place in sorted(
            {*places.values(), *task.worktree.parent.glob(f"{task.slug}.red-*")}
        ):
            stuck = remove(task, place)
            if stuck:
                raise CriteriaError(stuck)
        child: list[subprocess.Popen] = []
        # the serial wrappers among them, which get the time of their own cleanup after
        # a term
        wrappers: set[int] = set()

        def stop() -> None:
            """End the command that runs and everything it started: each command is a
            process group of its own."""
            for proc in child:
                for sign, wait in (
                    (signal.SIGTERM, SERIAL_GRACE if proc.pid in wrappers else GRACE),
                    (signal.SIGKILL, GRACE),
                ):
                    try:
                        os.killpg(proc.pid, sign)
                    except (ProcessLookupError, PermissionError):
                        break
                    try:
                        proc.wait(timeout=wait)
                    except subprocess.TimeoutExpired:
                        continue
            child.clear()
            wrappers.clear()

        serial = ran["serial"]

        def outcome(command: str, where: Path, *, test: bool = False) -> int:
            # through a shell, as the commands of the checks run: a test command is a
            # line the project would type; a test of a suite that needs the machine to
            # itself runs under its lock, which project.py holds
            line: str | list[str] = command
            if test and needs_serial(command, serial):
                line = [
                    sys.executable,
                    "-B",
                    str(SCRIPTS / "project.py"),
                    "--repo",
                    str(task.main),
                    "serial",
                    "--",
                    command,
                ]
            proc = subprocess.Popen(
                line,
                shell=isinstance(line, str),
                cwd=where,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
            )
            child.append(proc)
            if isinstance(line, list):
                wrappers.add(proc.pid)
            code = proc.wait()
            # a command that ended may have left a process behind (a server a
            # test started)
            stop()
            return code

        def grouped(where: Path, *args: str) -> None:
            """A git command that may run a hook of the repository: in a group of its
            own, like every other command here."""
            # What git says goes to a file, not a pipe: a process that a hook left
            # behind holds a pipe open, and a read of it would wait for that process and
            # never reach stop().
            with tempfile.TemporaryFile() as said:
                proc = subprocess.Popen(
                    ["git", "-C", str(where), *args],
                    stdout=subprocess.DEVNULL,
                    stderr=said,
                    stdin=subprocess.DEVNULL,
                    start_new_session=True,
                )
                child.append(proc)
                code = proc.wait()
                stop()
                said.seek(0)
                if code != 0:
                    raise CriteriaError(
                        f"git {' '.join(args[:2])} failed: "
                        f"{said.read().decode(errors='replace').strip()}"
                    )

        def ended(*_: object) -> None:
            raise KeyboardInterrupt

        before = signal.signal(signal.SIGTERM, ended)
        codes: dict[str, list[int]] = {}
        absent: list[str | None] = []
        failure: str | None = None
        try:
            for name, place in places.items():
                grouped(
                    task.main,
                    "worktree",
                    "add",
                    "-q",
                    "--detach",
                    str(place),
                    tip if name == "branch" else base,
                )
                if name == "base":
                    grouped(place, "checkout", tip, "--", *laid)
                for command in ran["setup"]:
                    code = outcome(command, place)
                    setup.append({"on": name, "command": command, "exit": code})
                    if code != 0:
                        where = (
                            "a fresh worktree of the branch"
                            if name == "branch"
                            else (
                                "a fresh worktree of the base commit, "
                                "with the test files laid over it"
                            )
                        )
                        raise CriteriaError(
                            f"`{command}` of checks.setup failed in {where} (exit "
                            f"{code}), so no test could run there; "
                            "correct that command in .lem/settings.toml"
                        )
                if name == "base":
                    # looked for before any test runs there, which might write the file
                    absent = [unstarted(test["command"], place) for _, test in tests]
                codes[name] = [
                    outcome(test["command"], place, test=True) for _, test in tests
                ]
        except KeyboardInterrupt:
            failure = "the check was stopped, and its commands are ended"
        except CriteriaError as error:
            failure = str(error)
        finally:
            stop()
            signal.signal(signal.SIGTERM, before)
            stuck = [
                problem
                for problem in (remove(task, place) for place in places.values())
                if problem
            ]
            lock.close()
        # A worktree that stayed is said whatever else went wrong: the first failure
        # does not hide it.
        if failure or stuck:
            raise CriteriaError(
                "; ".join(
                    [
                        *([failure] if failure else []),
                        *(stuck or ["its worktrees are removed"] if failure else stuck),
                    ]
                )
            )
        for (number, test), green, red, lacked in zip(
            tests, codes["branch"], codes["base"], absent, strict=True
        ):
            problem = None
            if green != 0:
                problem = (
                    f"fails in a fresh worktree of the branch (exit {green}). "
                    "If it passes in the task's worktree, it needs something a fresh "
                    "one lacks: put the commands that make it into "
                    "checks.setup of .lem/settings.toml"
                )
            elif red == 0:
                problem = (
                    "passes on the base commit too, so it does not test the change"
                )
            elif red in (126, 127) or lacked:
                missing = (
                    f": its script file {lacked} is not on the base commit"
                    if lacked
                    else ""
                )
                problem = (
                    f"does not start on the base commit (exit {red}{missing}), so its "
                    "failure there proves nothing. If a file it needs is a helper of "
                    "the test, name it among the criterion's files; if what is absent "
                    "is the change itself, make the test fail on it "
                    "and not stop before it"
                )
            results.append(
                {
                    "criterion": number,
                    "command": test["command"],
                    "files": test["files"],
                    "on_branch": green,
                    "on_base": red,
                    "problem": problem,
                }
            )
    ok = not any(result["problem"] for result in results)
    task.log(
        "task.red",
        ok=ok,
        digest=found["digest"],
        base=base[:9],
        tip=tip[:9],
        tests=results,
        without_a_test=without,
        run_without=run_without,
    )
    return {
        "task": task.slug,
        "ok": ok,
        "digest": found["digest"],
        "base": base[:9],
        "tip": tip[:9],
        "setup": setup,
        "tests": results,
        "without_a_test": without,
        "run_without": run_without,
        "inputs": ran,
    }


def reads_of(task: Task) -> list[dict]:
    """The task's reads of its criteria, oldest first, from the log `project.py` writes:
    its `criteria.read` events."""
    log = task.directory.parent.parent / "events.jsonl"
    found = []
    for line in (
        lem_state.jsonl_lines(log.read_text(encoding="utf-8")) if log.is_file() else []
    ):
        if '"criteria.read"' in line:
            record = json.loads(line)
            if (
                record.get("event") == "criteria.read"
                and record.get("task") == task.slug
            ):
                found.append(record)
    return found


# The automatic approvals, which no word of his gave in the moment: the read of a task
# on the standard track from a complete request, and Lem's approval on the fast track in
# his name (`by: lem`). Each is a task's first contract only.
AUTOMATIC = {
    "read": "a read freezes only the first contract",
    "lem": (
        "Lem approves the fast track's criterion in the owner's name "
        "only as the first contract"
    ),
}


def first_contract(task: Task, by: str) -> None:
    """An automatic approval is only the first contract of a task: once criteria are
    approved, by him, by Lem on the fast track or by a read, a criterion changes only
    through its record and the track only through his own approval, which is always
    allowed and always makes a new number."""
    kept = task.approved()
    if kept is not None:
        raise CriteriaError(
            f"{task.slug} has approval {kept['number']} of its criteria already (by "
            f"{kept['by']}): {AUTOMATIC[by]}. A criterion changes through its record, "
            f"`lem decisions criterion {task.slug} ...`, and the track only through "
            f"the owner's own approval, `lem criteria approve {task.slug} --file FILE`",
        )


def shown_digest(data: bytes) -> str:
    """The digest of a criteria file's bytes as the owner's page showed them, which the
    board's form carries back (`serve.py`, `criteria_waiting`): sha256, its first 16
    hex digits."""
    return hashlib.sha256(data).hexdigest()[:16]


def waits_for_him(task: Task, other: str, source: Path) -> str:
    """The refusal of an automatic approval of the fast track's criterion of a request
    that is not the owner's own sentence, while the task runs with him: the criterion
    waits for his yes."""
    return (
        f"{task.slug} is not the owner's own request ({other}), so its criterion waits "
        "for the owner's yes while the task runs with him: show it to him before its "
        f"builder starts, and on his yes `lem criteria approve {task.slug} --file "
        f'{source}` keeps it as his (`stages/new.md`, "The fast track", step 1); '
        "--alone is for a task that runs without the owner"
    )


def cmd_approve(
    task: Task, file: str, by: str, *, plan: bool = False, shown: str | None = None
) -> dict:
    """Keep the criteria that were approved, word for word, with a digest and a number
    of their own, and log the event. Each approval is a new one, also of a text approved
    before. The check of what is approved already and the write are one step under the
    task's lock, so an approval of his and an automatic one that come at one time never
    both pass. SHOWN is the digest of the bytes the owner's page showed
    (`shown_digest`): the file is read once, and those bytes are approved or
    nothing is."""
    source = Path(file)
    if not source.is_file():
        raise CriteriaError(
            f"{file} is not a file; --file names the criteria the owner approved, in "
            "the form `lem criteria --help` shows"
        )
    data = source.read_bytes()
    if shown is not None and shown_digest(data) != shown:
        raise CriteriaError(
            f"{source.name} changed since the page showed them (the page showed "
            f"{shown}, the file is {shown_digest(data)} now): nothing was approved. "
            "Read the criteria again, then approve",
        )
    # the line ends a read in text mode gives, from the same bytes
    text = data.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    read = parse(text, source.name)
    tested = [
        criterion["n"]
        for criterion in read["criteria"]
        if criterion["tests"] or criterion["no_test"]
    ]
    # the plan's own criteria carry the lead's test lines, which are no part of a
    # criterion's text
    if tested and not plan:
        raise CriteriaError(
            f"criterion {tested[0]} of {source.name} has a test line: the criteria the "
            "owner approves have none, and the lead adds them in the plan"
        )
    if by == "lem" and read["size"] != "small":
        raise CriteriaError(
            "--small approves the one criterion of a task on the fast track in the "
            f"owner's name, and {source.name} says `Size: {read['size']}`: "
            "the standard track waits for the owner's own yes"
        )
    # The fast track's criterion is approved in his name only when the request is his
    # own sentence. A request someone else wrote waits for his own yes while he is there
    # (the ruling "a complete ticket that someone else wrote needs his yes to its
    # criteria"); a night's task, and such a request while he is away, are approved
    # without him, and are not green for it.
    other = task.not_his() if read["size"] == "small" else None
    if by == "lem" and other:
        if task.read_mode() != "alone":
            raise CriteriaError(waits_for_him(task, other, source))
        raise CriteriaError(
            f"{task.slug} is not the owner's own request ({other}), so Lem does not "
            "approve its criterion in the owner's name: `lem criteria approve "
            f"{task.slug} --file {source} --alone` approves it without the owner while "
            "the task runs without him, and its pull request is not green for it",
        )
    if by == "alone" and read["size"] == "small" and not other:
        raise CriteriaError(
            f"{source.name} says `Size: small`, and the request is the owner's own: "
            "the fast track's criterion is approved in the owner's name with --small, "
            "in either mode; --alone is for a night's task or a request someone else "
            "wrote, while the task runs without the owner",
        )
    criteria = [
        {key: criterion[key] for key in ("n", "text", "case", "chart")}
        for criterion in read["criteria"]
    ]
    # one mark for this exact set of approved texts, each with its case; the approval
    # itself is known by its number
    digest = text_digest(read["size"], [whole(criterion) for criterion in criteria])
    task.directory.mkdir(parents=True, exist_ok=True)
    with (task.directory / "criteria.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if by in AUTOMATIC:
            first_contract(task, by)
        if by == "alone":
            # the mode at the approval, under the lock: the owner may have come back
            # since the task was read
            if task.read_mode() != "alone":
                if other:
                    raise CriteriaError(waits_for_him(task, other, source))
                raise CriteriaError(
                    f"{task.slug} runs with the owner: the owner's yes approves its "
                    "criteria (`stages/interview.md`, step 7), and --alone is for a "
                    "task that runs without the owner"
                )
            kept = task.approved()
            # a fast-track task that turned out to need the standard track needs that
            # path's approval, also when its first was made without the owner (a night's
            # task, a request someone else wrote, while it still runs without him: the
            # check above); any other approval stands
            grew = (
                kept is not None
                and kept["by"] == "alone"
                and kept.get("size") == "small"
                and read["size"] == "full"
            )
            if kept is not None and kept["by"] != "lem" and not grew:
                raise CriteriaError(
                    f"{task.slug} has approval {kept['number']} of its criteria "
                    f"already (by {kept['by']}): a criterion changes through its "
                    f"record, `lem decisions criterion {task.slug} ...`",
                )
        if by == "read":
            # the standard track from a complete request: the lead freezes the criteria
            # the personas read, and only when nobody was confused
            reads = reads_of(task)
            last = reads[-1] if reads else None
            if last is None or last.get("digest") != digest:
                raise CriteriaError(
                    (
                        "--read freezes the criteria the newest `criteria.read` of "
                        f"{task.slug} read, and "
                    )
                    + (
                        "there is none"
                        if last is None
                        else (
                            "that read was of the criteria with digest "
                            f"{last.get('digest')}, and {source.name} has {digest}"
                        )
                    )
                    + (
                        ": run the read over these criteria first (`stages/plan.md`, "
                        "step 1)"
                    ),
                )
            # a read nobody answered is started once more; after the second in a row the
            # build goes on
            if last["answered"] == 0 and (
                len(reads) < 2  # noqa: PLR2004 - the newest read and the one before it
                or reads[-2].get("answered") != 0
            ):
                raise CriteriaError(
                    f"nobody answered the newest read of {task.slug}'s criteria: "
                    "it is started once more (`stages/plan.md`, step 1); "
                    "after a second read in a row that nobody answered, the build goes "
                    "on with the criteria as they are",
                )
            if last["flagged"] or last["split"]:
                raise CriteriaError(
                    f"the newest read of {task.slug}'s criteria found {'a flagged criterion' if last['flagged'] else 'a split between the families'}: "
                    "the criteria wait for the owner, and only the "
                    "owner's approval freezes them",
                )
        before = task.approved()
        history = (
            [
                *before.get("history", []),
                {
                    key: value
                    for key, value in before.items()
                    if key not in ("history", "task", "text")
                },
            ]
            if before
            else []
        )
        record = {
            "task": task.slug,
            "number": len(history) + 1,
            "at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            # who approved: the owner; Lem in his name, for a task on the fast track,
            # which does not wait; the lead's read on the standard track from a complete
            # request, which counts for the plan's check and never as his yes; or Lem or
            # the lead while the task runs without the owner (`alone`), which is never
            # his yes either
            "by": by,
            "size": read["size"],
            "why": read["why"],
            "digest": digest,
            "criteria": criteria,
            "how": read["how"],
            "text": text,
            **({"replaces": before["number"]} if before else {}),
            "history": history,
        }
        task.approved_file.write_text(
            json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        task.log(
            "criteria.approved",
            by=by,
            number=record["number"],
            size=record["size"],
            why=record["why"],
            digest=digest,
            criteria=criteria,
            **({"replaces": before["number"]} if before else {}),
        )
    return {**record, "file": str(task.approved_file)}


@lem_release.one_command
def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="lem criteria",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="a directory inside the repository (default: the current one)",
    )
    parser.add_argument(
        "step",
        choices=("approve", "approved", "digest", "show", "record", "red", "inputs"),
    )
    parser.add_argument("slug")
    parser.add_argument(
        "--file",
        help=(
            "with approve: the criteria the owner approved, in the form above and with "
            "no test lines; with digest: the criteria to mark"
        ),
    )
    parser.add_argument(
        "--small",
        action="store_true",
        help=(
            "with approve: Lem approves the one criterion of a task on the fast "
            "track in the owner's name"
        ),
    )
    parser.add_argument(
        "--read",
        action="store_true",
        help=(
            "with approve: the lead of a task on the standard track from a complete "
            "request freezes the criteria a read in which nobody was confused read"
        ),
    )
    parser.add_argument(
        "--alone",
        action="store_true",
        help=(
            "with approve: Lem or the lead approves the criteria of a task while the "
            "task runs without the owner"
        ),
    )
    parser.add_argument(
        "--shown",
        metavar="DIGEST",
        help=(
            "with approve --file: the digest of the file's bytes as the owner's page "
            "showed them (the board's form gives it); the file changed "
            "since is approved by nobody"
        ),
    )
    args = parser.parse_args(argv)
    result: dict[str, Any]
    try:
        if args.file is not None and args.step not in ("approve", "digest"):
            raise CriteriaError("--file goes with `approve` and `digest`")
        if args.shown is not None and (
            args.step != "approve"
            or args.file is None
            or args.small
            or args.read
            or args.alone
        ):
            raise CriteriaError(
                "--shown goes with `approve --file FILE`, the owner's own approval of "
                "the file his page showed"
            )
        if (args.small or args.read or args.alone) and args.step != "approve":
            raise CriteriaError("--small, --read and --alone go with `approve`")
        if args.small + args.read + args.alone > 1:
            raise CriteriaError(
                "an approval is Lem's on the fast track, the read's on the standard "
                "track from a complete request, or one made without the owner: "
                "one of --small, --read and --alone"
            )

        if args.alone and args.file is None:
            raise CriteriaError(
                "--alone needs --file: the criteria approved without the owner, the "
                "interview's file or the plan"
            )
        task = Task(Path(args.repo).resolve(), args.slug)
        stopped = lem_release.check(task.directory)
        if stopped:
            raise CriteriaError(stopped)
        if args.step == "approve":
            if args.read:
                if args.file is not None:
                    raise CriteriaError(
                        "--read freezes the plan's own criteria, the ones the read "
                        "named: it takes no --file; a file of criteria is approved by "
                        "the owner, without --read"
                    )
                # refused before the plan is read, and again under the lock: a task with
                # a contract keeps it
                first_contract(task, "read")
                result = cmd_approve(task, task.criteria()["plan"], "read", plan=True)
            elif args.file is None and args.small:
                # Lem's approval in his name has one place, the task directory's
                # criteria.md
                result = cmd_approve(task, str(task.small_file), "lem")
            elif args.file is None:
                raise CriteriaError(
                    "approve needs --file: the criteria the owner approved, in the "
                    "form `lem criteria --help` shows, with no test lines"
                )
            elif args.alone:
                # the plan's own criteria carry the lead's test lines, which are no part
                # of a criterion's text
                result = cmd_approve(task, args.file, "alone", plan=True)
            else:
                result = cmd_approve(
                    task, args.file, "lem" if args.small else "owner", shown=args.shown
                )
        elif args.step == "approved":
            kept = task.approved()
            result = (
                {"task": task.slug, "approved": kept}
                if kept
                else {
                    "task": task.slug,
                    "approved": None,
                    "says": (
                        "no approved criteria: the plan's own "
                        "criteria are their one source"
                    ),
                }
            )
        elif args.step == "digest":
            if args.file is None:
                found = task.criteria()
                result = {
                    "task": task.slug,
                    "of": found["plan"],
                    "digest": found["criteria_digest"],
                }
            else:
                if not Path(args.file).is_file():
                    raise CriteriaError(
                        f"{args.file} is not a file; --file names the criteria to "
                        "mark, in the form `lem criteria --help` shows"
                    )
                read = parse(
                    Path(args.file).read_text(encoding="utf-8"), Path(args.file).name
                )
                result = {
                    "task": task.slug,
                    "of": args.file,
                    "digest": text_digest(
                        read["size"],
                        [whole(criterion) for criterion in read["criteria"]],
                    ),
                }
        elif args.step == "red":
            result = cmd_red(task)
        elif args.step == "inputs":
            result = cmd_inputs(task)
        else:
            result = task.criteria()
            if args.step == "record":
                task.log(
                    "task.criteria",
                    size=result["size"],
                    why=result["why"],
                    digest=result["digest"],
                    criteria=result["criteria"],
                )
    except CriteriaError as error:
        sys.exit(f"criteria.py: {error}")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.step == "red" and not result["ok"]:
        bad = next(test for test in result["tests"] if test["problem"])
        sys.exit(
            f"criteria.py: criterion {bad['criterion']}: "
            f"`{bad['command']}` {bad['problem']}"
        )


if __name__ == "__main__":
    main()
