#!/usr/bin/env python3
"""Take one task's branch from `ready` to a pull request and to the base branch, one step at a time.

Nothing reaches the base branch without the machine checks and a review by an agent that did not
build it, and a task ends as a pull request. Each step here is one command, prints JSON, and
refuses with exit 1 and the reason when the step may not run; nothing is retried and nothing is
forced. Every step first asks `project.py may-land` about the settings' base branch, so a
protected branch is never reached, whoever asks.

    land.py start SLUG     the task takes the landing line: its state becomes `landing`
    land.py base SLUG      bring the base branch in by a rebase; a conflict is reported, not resolved
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
                           GitHub: the state becomes `open`
    land.py land SLUG --by owner|agent [--message SUBJECT]
                           merge the pull request, or put a ready branch on the base branch
    land.py merged SLUG    the owner merged the pull request on the forge: finish the bookkeeping
    land.py clean SLUG     remove the task's worktree and its branch after the merge

What each step keeps for the next is in `landing.json` in the task's directory: the task's
branch, the base it was rebased on, the commit and tree the checks passed on, each review, and
the pull request.

The machine checks have no model in them. `gate` runs the settings' `gate.commands`, then
`stories.py red` (each story's tests pass on the branch and fail on the base commit), then the
bar. A change lowers the bar when it adds a lint or type suppression or a skipped test, deletes
a test file, or leaves fewer assertions in one (counted by the words `assert` and `expect` on the
lines it adds and removes, in a test file and in every Rust file, where unit tests sit beside
the code). A mark counts when the change leaves more of it in a file than the file had, so a
line that only moved is no new mark; a mark whose own text changed is a new one. A lowered bar passes only with a reason for that file under
`## The bar` in the task's plan, as `- PATH: REASON`. The marks looked for are those of Python, JavaScript and
TypeScript, Go, Rust, Java and Kotlin, and shell, and the settings' `gate.bar` patterns for any
file that is not a document. A changed file of another language gets no such check, and the
result says which (`not_covered`). The size of the change is counted, for the reviewer.

A review comes before anything is proposed. There are three kinds: one read, which is the
review tool's smallest profile, for a small and simple change; a round of the review tool with
the profiles or lenses that fit the change; the project's full set. Which one a change gets, and which profiles fit it, is the
judgment of the agent that starts the review, from the diff and from what each profile is for:
no code and no list of words decides it. This script holds only the floor that no judgment goes
under: the full set for a careful request (a careful path, the plan's own `careful: yes`, or the
owner's word in the brief), and a round at the least for a plan of more than three tasks and
after a review that found a must-fix.

The record of a review is a JSON file:

    {"attempt": N,
     "kind": "read" | "round" | "full",
     "ran": [{"name": PROFILE OR LENS, "why": WHY IT FITS THIS CHANGE}],
     "left_out": [{"name": PROFILE OR LENS, "why": WHY IT DOES NOT}],
     "answered": [SOURCE, ...],
     "silent": [{"name": SOURCE, "why": WHAT STOPPED IT}],
     "bar": [{"name": FILE, "why": WHAT THE REVIEW SAYS OF THE REASON GIVEN FOR IT}],
     "must_fix": N, "should": N, "nit": N,
     "outside": [{"where": PATH OR PATH:SYMBOL, "title": ONE LINE, "what": THE RUN THAT SHOWS IT}]}

`attempt`, `kind` and `answered` are always there. `bar` has one entry for each file in which
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
each defect's item in `landing.json`. A second run files nothing new. `read` names the defects
that have no item yet (`to_file`), and `propose` refuses while one has none or while an item is
gone from the tip; the owner's "not wanted" is `worth: no` in the item, never its deletion.
The file name is the slug of the title. A file of that name that holds the same defect (the same
`where` and title, and its run word for word as paragraphs of the body, whatever else the body
says, such as the owner's reason for `worth: no`) is its item, and nothing is written twice; a
file that holds another takes the next name, with a suffix from the `where`, then a number. One defect that two rounds
describe in other words gets two items: an extra item costs a merge in the backlog's sorting, and
a lost one costs the defect. The review is asked to repeat an earlier round's words for a defect
it sees again.

A record that counts the defects outside the change and names none was written by b96ce79 or
8f7c106, which were never pushed, so it can only be in a throwaway repository: `read` and
`propose` refuse it and name the task's `landing.json`, and no step converts it, because a count
says nothing from which an item could be written.

`propose` writes the text of the pull request to `pr.md` in the task's directory, from what the
steps kept, from the record of the task's decisions (`decisions.py list`) and from the notes
file, whose headings it checks. The text opens with green or not green. Green says that the
machine checks passed with the bar where it was, a review with at least one source left no
must-fix, no story changed during the build, and no decision was taken by timeout. A lowered bar
is not green with a reason either: its line holds the builder's reason and what the review said
of it. A choice taken by timeout is a line of its own, and so is an answer of the owner's that
came after it and differs. Each reason a request is not green stands before everything else, one
line each; each decision of the record is one line before the notes. `propose` is refused while a
choice of the task waits for the owner. A plan that calls itself careful (`careful: yes`) or
has more than three tasks was talked through by its session lead and the reviewer before any
code, and the lead wrote it down as one `plan.talk` event in the log `project.py` keeps:
`propose` refuses such a request with none, and the text's checks hold one line from the newest,
with who argued the plan with the lead, the turns, and the positions settled and left open. A
talk is a step before the build, so a request that is careful only by the owner's later word or
by a path its diff matches gets the full set and no talk; it is not asked for one, and its checks
say in words that it had none and why, which is no cause of not green. A usual request gets
neither line. A careful path that the diff matches and the plan's own call missed is a lesson
about that call: `propose` writes one `careful.missed` event with the path and its pattern, the
first time it finds the case, for the retro. With a GitHub remote `propose` pushes the task's branch
and opens the pull request with the `gh` command; a second run updates it. With any other
remote, or none, the branch is marked ready. GitLab is not built: nobody checked its command.

`land --by owner` is the owner's word. `land --by agent` is refused unless the settings'
`branch.land` is `agent`, and then still for a careful request and for one that is not green. A
pull request is merged through the forge, so the forge's own rules hold; `merged` is for one the
owner merged himself. What lands is the tree the checks passed on: when the tip is another tree,
or the base moved by more than the paths the settings' `gate.ignores` name, `land` refuses and
says which steps run again.

A step that was cut off is run again. `land` writes down the commit it is about to put on the base
before it does, so a second run that finds that commit on the base only finishes the bookkeeping.
`clean` knows the branch from `landing.json`, so it finds it after the worktree is gone.

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
# How many changed lines one reader takes as one piece; a larger change is read task by task, in
# the plan's own cuts. A guess (2026-11-15), not a measurement.
READ_AT = 800
# A plan of more tasks than this is large: it gets a round at the least, and a plan talk before
# any code. The three-touches plan's own line (2026-11-15), not a measurement.
LARGE_AFTER = 3
# The plan's own call that the task is careful, as `stages/plan.md` step 2 has the lead write it.
PLAN_CAREFUL = re.compile(r"(?mi)^careful:\s*yes\b")
# Who took a decision of the record, as the text of a pull request names them.
TAKEN_BY = {"lead": "the lead", "personas": "the personas", "owner": "the owner", "lem": "Lem", "timeout": "the timeout"}
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
# the session that built this check (2026-11-15) from those tools' own syntax; not measured.
BAR = {
    (".py",): (r"#\s*noqa", r"#\s*type:\s*ignore", r"#\s*pyright:\s*ignore", r"#\s*pylint:\s*disable", r"#\s*nosec", r"\bpytest\.mark\.(skip|xfail)", r"\bunittest\.skip", r"\bpytest\.skip\("),
    (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"): (r"eslint-disable", r"@ts-ignore", r"@ts-expect-error", r"@ts-nocheck", r"\b(it|test|describe)\.(skip|todo)\(", r"\bx(it|test|describe)\("),
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
        # The address as the repository has it, before any rewrite of it: the forge is known by its host.
        url = git(self.main, "config", "--get", "remote.origin.url", check=False)
        self.forge = "github" if re.match(r"(https://|ssh://git@|git@)github\.com[:/]", url) else None

    def need_worktree(self) -> None:
        if not (self.worktree / ".git").exists():
            raise LandError(f"the task has no worktree at {self.worktree}")
        dirty = git(self.worktree, "status", "--porcelain")
        if dirty:
            raise LandError(f"the worktree has changes nobody committed:\n{dirty}\ncommit them or remove them before this step")

    def need_landing(self) -> None:
        if self.record["status"] != "landing":
            raise LandError(f"the task is {self.record['status']!r}, not `landing`; `land.py start {self.slug}` comes first")

    def kept(self) -> dict:
        return json.loads(self.kept_file.read_text()) if self.kept_file.is_file() else {}

    def keep(self, **values: object) -> None:
        self.kept_file.write_text(json.dumps({**self.kept(), **values}, indent=2) + "\n")

    def state(self, status: str, *lines: str) -> None:
        script("project.py", self.worktree if self.worktree.exists() else self.main, "state", self.slug, status, *lines)

    def decisions(self) -> list[dict]:
        """Each decision of the task as it stands, through the one script that writes them."""
        if self.recorded is None:
            self.recorded = json.loads(script("decisions.py", self.main, "list", self.slug).stdout)
        return self.recorded

    def fetch(self) -> None:
        if self.remote:
            git(self.main, "fetch", "origin", str(self.base))


def cmd_start(task: Task) -> dict:
    if task.others_landing:
        raise LandError(f"{task.others_landing[0]} is in `landing`: one branch lands at a time, so finish that one first")
    if task.record["status"] not in ("ready", "landing", "open"):
        raise LandError(f"the task is {task.record['status']!r}; only a `ready` task, or an `open` one whose base moved, takes the landing line")
    if not task.settings["gate"]["commands"]:
        task.state("blocked", "the project has no gate command")
        raise LandError(
            "the project has no gate command, so nothing would show that the change works; the task is now `blocked`. "
            "Add the commands to gate.commands in .lem/project.toml",
        )
    task.need_worktree()
    if task.record["status"] == "ready":
        # A task that was built further starts over, with new checks and new reads. Its pull request stays its own.
        pr = task.kept().get("pr")
        task.kept_file.unlink(missing_ok=True)
        if pr:
            task.keep(pr=pr)
    if task.record["status"] != "landing":
        # kept here because `clean` needs the branch after the worktree, which names it, is gone
        task.keep(branch=git(task.worktree, "branch", "--show-current"))
        task.state("landing", "the checks start" if task.record["status"] == "ready" else "the base moved: the checks run again")
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
        raise LandError(f"the branch has no commit that {task.onto} lacks: there is nothing to land")
    # a new base or a new tip means the gate's last result is about another tree
    task.keep(base=onto, gated=None, tree=None)
    return {"task": task.slug, "onto": task.onto, "base": onto, "tip": tip, "moved": tip != before, "ahead": ahead}


def stories_of(task: Task) -> dict:
    """The task's stories and its plan, through the one script that reads them."""
    return json.loads(script("stories.py", task.main, "show", task.slug).stdout)


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
    """The backlog folder, relative to the root of the repository: a path, never a pattern. `.` is the root."""
    return Path(task.settings["paths"]["backlog"]["path"]).relative_to(Path(task.settings["root"]).resolve()).as_posix()


def covers(task: Task, read: dict, now: dict) -> bool:
    """Whether a review that was recorded still covers the change as it is now. It does when the
    change is the same, or when the change is the reviewed one plus new files of the backlog
    folder and nothing else: `file` writes the defects a review saw outside the change there after
    the review, and that asks for no other review. Any other file does, an item that was on the
    base too. A folder that is the root gives no such exception, and a record that kept no
    contents covers only the same change."""
    if read["patch"] == now["patch"]:
        return True
    was = read.get("contents")
    folder = backlog_of(task)
    if was is None or folder == ".":
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


def outside_of(task: Task, read: dict) -> list[dict]:
    """The defects outside the change of one kept review, each with the path of its item once it has one."""
    value = read.get("outside", [])
    if isinstance(value, int) and not isinstance(value, bool):
        if value == 0:
            return []
        raise LandError(
            f"review round {read['round']} in {task.kept_file} counts {value} defect(s) outside the change and names none: "
            "a form of the record that was never released (b96ce79, 8f7c106), from which no item can be written, so no step converts it. "
            "Only a throwaway repository holds one: drop the task, or remove that file and start its landing again",
        )
    return value


def to_file(task: Task, reads: list[dict]) -> list[dict]:
    """Each defect outside the change of a review that answered, with no item yet."""
    return [
        {"round": read["round"], **{key: defect[key] for key in DEFECT}}
        for read in reads if read["answered"] for defect in outside_of(task, read) if not defect.get("item")
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


def careful_path(task: Task, files: list[str]) -> dict | None:
    """The first changed file that a careful pattern of the settings matches, with that pattern."""
    matched = json.loads(script("project.py", task.worktree, "careful", *files).stdout)["careful"] if files else []
    return matched[0] if matched else None


def careful(task: Task, files: list[str], plan: str) -> list[str]:
    """Each reason for which this request is careful; none when it is not."""
    why = []
    if owner_says_careful(task):
        why.append("the owner says so")
    if PLAN_CAREFUL.search(plan):
        why.append("the plan says so")
    matched = careful_path(task, files)
    if matched:
        why.append(f"{matched['file']} is a careful path ({matched['pattern']})")
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
        status, _, name = row.partition("\t")
        if status == "D" and TEST_FILE.search(name):
            lowered = [entry for entry in lowered if entry["file"] != name]
            lowered.append({"file": name, "what": "a test file is deleted", "line": ""})
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
    logs = task.directory / "gate"
    logs.mkdir(exist_ok=True)
    results = []
    for number, command in enumerate(task.settings["gate"]["commands"], start=1):
        output = logs / f"{number:02d}.log"
        with output.open("w", encoding="utf-8") as handle:
            code = subprocess.run(command, shell=True, cwd=task.worktree, stdout=handle, stderr=subprocess.STDOUT, check=False).returncode
        lines = [line for line in output.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]
        last = lines[-1].strip() if lines else ""
        results.append({"command": command, "exit": code, "last": last, "output": str(output)})
        script("project.py", task.worktree, "log", task.slug, "gate", f"command={command}", f"exit:={code}", f"last={last}", f"tip={tip[:9]}")
    green = all(result["exit"] == 0 for result in results)
    # A gate command that left a file behind changed the tree it just judged.
    dirty = git(task.worktree, "status", "--porcelain")
    if green and dirty:
        raise LandError(
            f"the gate left changes in the worktree, so its result is about another tree:\n{dirty}\n"
            "make the gate command clean up, or have the project ignore what it writes",
        )
    result = {"task": task.slug, "tip": tip, "green": green, "commands": results}
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
    plan = Path(stories_of(task)["plan"]).read_text(encoding="utf-8")
    now = change(task)
    result["bar"] = bar(task, now["base"], tip, plan)
    result["size"] = {"files": len(now["files"]), "lines": now["lines"], "in_parts": now["lines"] > READ_AT}
    unexplained = [entry for entry in result["bar"]["lowered"] if not entry["reason"]]
    if unexplained:
        print(json.dumps(result, indent=2))
        named = "; ".join(f"{entry['file']} ({entry['what']})" for entry in unexplained[:5])
        raise LandError(
            f"the change lowers the bar with no reason given: {named}. Take the mark out, or give the reason in the task's plan "
            "under `## The bar` as `- PATH: REASON`, where the one who reads the change sees it",
        )
    task.keep(gated=tip, tree=git(task.worktree, "rev-parse", "HEAD^{tree}"), checks={"commands": results, "stories": result["stories"], "bar": result["bar"], "size": result["size"]})
    return result


def ignored(task: Task, files: list[str]) -> bool:
    patterns = task.settings["gate"]["ignores"]
    return all(any(fnmatch.fnmatchcase(file, pattern) for pattern in patterns) for file in files)


def changed(task: Task, old: str, new: str) -> list[str]:
    """Every path that differs between two trees. A rename counts as the path that went and the path that came."""
    return git(task.worktree, "diff", "--name-only", "--no-renames", old, new).splitlines()


def due(task: Task) -> dict:
    """Whether a review is due now, and the least it may be. Within that, the one who starts the review chooses."""
    now = change(task)
    plan = Path(stories_of(task)["plan"]).read_text(encoding="utf-8")
    reads = task.kept().get("reads", [])
    answered = [read for read in reads if read["answered"]]
    why_careful = careful(task, now["files"], plan)
    facts = {"round": len(answered) + 1, "careful": why_careful, "tasks": tasks_of(plan), "lines": now["lines"], "in_parts": now["lines"] > READ_AT, **now}
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
    yes` line, or more than three tasks. The owner's later word, or a careful path that only the
    diff matches, gives the full review set at the landing and no talk after the code exists."""
    if PLAN_CAREFUL.search(Path(stories_of(task)["plan"]).read_text(encoding="utf-8")):
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


def missed(task: Task, state: dict) -> dict | None:
    """The careful path the plan's own call missed: the diff matches one, and the plan does not say
    careful. The plan-time call is the lead's, so the retro counts each such miss."""
    if PLAN_CAREFUL.search(Path(stories_of(task)["plan"]).read_text(encoding="utf-8")):
        return None
    return careful_path(task, state["files"])


def untalked(task: Task, state: dict) -> str | None:
    """Why a careful request had no plan talk, when none was due: it became careful after its plan."""
    if not state["careful"] or talk_due(task, state):
        return None
    how = [*(["by the owner's word"] if owner_says_careful(task) else []), *(["by its diff"] if missed(task, state) else [])]
    return f"- no plan talk: the request became careful after its plan, {' and '.join(how)}"


def talked(talk: dict) -> str:
    """The plan talk as one line of the pull request's checks."""
    def many(count: int, one: str, more: str) -> str:
        return f"{count} {one if count == 1 else more}"
    return (
        f"- the plan talk: {talk['reviewer']} argued the plan with the lead, {many(talk['turns'], 'turn', 'turns')}; "
        f"{many(talk['settled'], 'position', 'positions')} settled by the two, {talk['open']} left open"
    )


def named(value: object, where: str) -> list[dict]:
    """A list of names, each with its why: the profiles of a round, or the sources that did not answer."""
    if not isinstance(value, list) or not all(
        isinstance(item, dict) and set(item) == {"name", "why"} and all(isinstance(text, str) and text.strip() for text in item.values()) for item in value
    ):
        raise LandError(f"`{where}` is a list of {{\"name\": ..., \"why\": ...}}, each with both as text")
    return value


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
        for defect in outside_of(task, read):
            if defect.get("item"):
                if in_tree(task, tip, defect["item"]):
                    continue
                if not again:
                    gone.append({"round": read["round"], "title": defect["title"], "item": defect["item"]})
                    continue
            # The first name that holds this very defect is its item; the first that is free gets it.
            # A name that holds another defect is passed: an extra item is the price, never a lost one.
            for name in names_for(defect):
                path = name if folder == "." else f"{folder}/{name}"
                file = task.worktree / path
                if holds(file, defect):
                    same.append({"round": read["round"], "title": defect["title"], "item": path})
                    break
                if not (file.exists() or file.is_symlink()):
                    file.parent.mkdir(parents=True, exist_ok=True)
                    file.write_text(
                        f"---\nworth: later\nwhere: {defect['where']}\nadded: {today}\n---\n# {defect['title']}\n\n{defect['what']}\n\n"
                        f"Seen outside the change by review round {read['round']} of task {task.slug} ({read.get('date', today)}); the base commit has it.\n",
                        encoding="utf-8",
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
    if task.kept().get("gated") != state["tip"]:
        raise LandError(f"the review is of the tip the checks passed on, and no check is on record for this tip; `land.py gate {task.slug}` comes first")
    reads = task.kept().get("reads", [])
    if record is None:
        rules = json.loads(script("project.py", task.worktree, "rules", "--range", f"{state['base']}..{state['tip']}").stdout)["rules"]
        return {
            "task": task.slug, "due": state["due"], "why": state["why"], "floor": state["floor"], "kinds": KIND_SAYS, "round": state["round"],
            # the number the record of this review carries, so that the same record is never written down twice
            "attempt": state["attempt"],
            # the defects outside the change that reviews saw and that have no item yet: `land.py file` files them
            "to_file": to_file(task, reads),
            "careful": state["careful"], "tasks": state["tasks"], "lines": state["lines"], "in_parts": state["in_parts"],
            "reads": [{key: value for key, value in read.items() if key != "contents"} for read in reads],
            # what a reviewer gets, and nothing of the builder's reasoning
            "inputs": {
                # the owner's words as given, and the request as Lem wrote it down, where the task has them
                **{name: str(task.directory / file) for name, file in (("words", "ask.txt"), ("request", "task.md")) if (task.directory / file).is_file()},
                "plan": stories_of(task)["plan"], "range": f"{state['base']}..{state['tip']}",
                "worktree": str(task.worktree), "rules": [rule["file"] for rule in rules], "bar": task.kept().get("checks", {}).get("bar"),
                # where the project's review tool keeps each profile and lens, with what each is for
                "review": task.settings["paths"]["review"]["path"],
            },
        }
    # a kept review of a form that was never released stops this step too, before anything is written
    to_file(task, reads)
    if state["due"] != "review":
        raise LandError(f"no review is due: {state['why']}")
    try:
        said = json.loads(Path(record).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise LandError(f"{record} does not read as JSON ({error}); --record names the file that says what the review was and what it found") from error
    known = {"attempt", "kind", "ran", "left_out", "answered", "silent", "bar", "must_fix", "should", "nit", "outside"}
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
        "date": date.today().isoformat(), "verdict": "not reviewed" if not answered else "must-fix" if counts["must_fix"] else "clean", "tip": state["tip"][:9], "patch": state["patch"],
    }
    # The event first: a run that is cut off between the two writes the review down at its next
    # run, and the second event has the same attempt, by which a reader of the log knows it.
    script("project.py", task.worktree, "log", task.slug, "review", *(f"{key}:={json.dumps(value)}" for key, value in entry.items()))
    # The contents of the change stay out of the log: only `covers` reads them, from the kept record.
    task.keep(reads=[*reads, {**entry, "contents": state["contents"]}])
    return {"task": task.slug, "recorded": entry, "next": due(task)["due"], "to_file": to_file(task, task.kept()["reads"])}


def not_green(task: Task, state: dict) -> list[str]:
    """Each reason for which this request is not green, one line each; none when it is green."""
    reasons = []
    if state["due"] != "none":
        reasons.append(state["why"])
    # A lowered bar is never green, with a reason too: it is the one change that makes the other
    # green lines worth less, so the owner reads its line himself.
    kept = task.kept()
    said = {entry["name"]: entry["why"] for read in kept.get("reads", []) if read["answered"] for entry in read.get("bar", [])}
    for entry in (kept.get("checks") or {}).get("bar", {}).get("lowered", []):
        review = f"The review: {said[entry['file']]}" if entry["file"] in said else "No review said anything of it."
        reasons.append(f"the bar is lower in `{entry['file']}` ({entry['what']}). The builder: {entry['reason']} {review}")
    for decision in task.decisions():
        if "story" in decision:
            reasons.append(f"story {decision['story']} changed during the build: {story_why(decision)}")
        if decision["state"] == "timeout":
            reasons.append(
                f"choice {decision['id']} was taken by timeout ({decision['what']}): \"{decision['chose']}\", the recommended option, "
                f"after the owner's wait of {decision['wait_minutes']} minutes ended with no answer{later(decision, '; he answered later with')}",
            )
    return reasons


def story_why(decision: dict) -> str:
    """Why a story changed: the reason of a decision that was taken, or the choice that took the option that changes it."""
    if decision["state"] == "taken":
        return decision["why"]
    if decision.get("instead"):
        return f"choice {decision['id']} ({decision['what']}) was settled by the owner with \"{decision['chose']}\", none of the options"
    return f"choice {decision['id']} ({decision['what']}) took \"{decision['chose']}\", by {TAKEN_BY[decision['by']]}"


def reason(text: str) -> str:
    """A reason as written, without its own full stop, for a sentence around it."""
    return text.rstrip(".")


def later(decision: dict, lead: str) -> str:
    """What the owner answered after the timeout, when he did: the same or what differs, with his
    own words when they are not the option's text, and his reason, whichever it is."""
    if "late" not in decision:
        return ""
    late = decision["late"]
    said = []
    if late.get("words", late["chose"]) != late["chose"]:
        said.append(f"his words: \"{late['words']}\"")
    if "why" in late:
        said.append(f"his reason: {reason(late['why'])}")
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
        line += "" if "owner_why" in decision else " He gave no reason."
    elif decision["state"] == "answered" and decision["chose"] == decision["recommended"]:
        # the recommendation's reason is the reason of the option he took; his own, when he gave one, follows
        line += f", as recommended. {decision['why']}"
    elif decision["state"] == "answered":
        # the recommendation's reason is about the option he did not take: it is named as such, never as his
        line += f", over the recommended \"{decision['recommended']}\" (recommended because: {reason(decision['why'])})."
        line += "" if "owner_why" in decision else " He gave no reason."
    elif decision["state"] == "timeout":
        line += f", after the owner's wait of {decision['wait_minutes']} minutes. {decision['why']}" + (f" {later(decision, 'He answered later with')}." if "late" in decision else "")
    else:
        line += f" ({decision['said']}). {decision['why']}" if decision["by"] == "personas" else f". {decision['why']}"
    if decision.get("owner_words", decision["chose"]) != decision["chose"]:
        line += f" His words: \"{decision['owner_words']}\""
    if "owner_why" in decision:
        line += f" His reason: {decision['owner_why']}"
    return line + (f" Story {decision['story']} changed." if "story" in decision else "")


def pr_text(task: Task, notes: str, state: dict) -> str:
    """The text of the pull request, in the order the owner reads it."""
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
        out += ["**Green.** The machine checks passed with the bar where it was, the review left no must-fix, no story changed, and no decision was taken by timeout.", ""]
    out += ["## The request", "", *(f"> {line}" for line in (ask or "(the owner's words were not kept for this task)").splitlines()), ""]
    out += ["## Stories", "", f"{found['kind'].capitalize()}, because {found['why']}", ""]
    for story in found["stories"]:
        out.append(f"{story['n']}. {story['text']}")
        for test in story["tests"]:
            proof = held.get((story["n"], test["command"]))
            out.append(f"   - `{test['command']}`: {'passes on the branch, fails on the base commit' if proof and not proof['problem'] else 'not checked'}")
        if story["no_test"]:
            out.append(f"   - no test: {story['no_test']}")
    changed_stories = [decision for decision in task.decisions() if "story" in decision]
    if changed_stories:
        out += ["", "Stories that changed during the build:", ""]
        out += [f"- story {was['story']}: was \"{was['was']}\". {story_why(was)}{'' if was['state'] == 'taken' else '.'} {was.get('said', '')}".rstrip() for was in changed_stories]
    out += ["", "## Checks", ""]
    for command in checks.get("commands", []):
        code = command["exit"]
        out.append(f"- gate, `{command['command']}`: {command['last'] or f'exit {code}'}")
    tests = (checks.get("stories") or {}).get("tests", [])
    without = (checks.get("stories") or {}).get("without_a_test", [])
    out.append(f"- the stories' tests: {len(tests)} pass on the branch and fail on the base commit" + (f"; {len(without)} stor{'y has' if len(without) == 1 else 'ies have'} no test" if without else ""))
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
        defects = outside_of(task, read)
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
    out.append(f"- careful: {'yes, ' + '; '.join(state['careful']) if state['careful'] else 'no'}")
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
    kept = task.kept()
    tip = git(task.worktree, "rev-parse", "HEAD")
    if kept.get("gated") != tip:
        raise LandError(f"no green check is on record for this tip; `land.py gate {task.slug}` comes first")
    reads = kept.get("reads", [])
    # a kept review of a form that was never released stops this step before anything else
    unfiled = to_file(task, reads)
    state = due(task)
    if state["due"] == "review":
        raise LandError(f"a review is due before anything is proposed, {KIND_SAYS[state['floor']]} at the least ({state['why']}); `land.py read {task.slug}` says what a reviewer gets")
    # A careful or large plan is talked through by its session lead and the reviewer before any
    # code. The talk leaves one event, and a request without it skipped that step.
    needs_talk = talk_due(task, state)
    talk = talk_of(task) if needs_talk else None
    if needs_talk and talk is None:
        raise LandError(
            f"{needs_talk}, so its plan is talked through by a session lead and the reviewer before any code (`stages/plan.md`, step 4), "
            f"and the event log has no `plan.talk` of {task.slug}. The lead writes it after the talk: "
            f"`project.py log {task.slug} plan.talk reviewer=AGENT turns:=N settled:=N open:=N`; a plan that had no talk gets one from a session lead first",
        )
    if talk is not None and not (
        isinstance(talk.get("reviewer"), str) and talk["reviewer"].strip()
        and all(isinstance(talk.get(key), int) and not isinstance(talk.get(key), bool) for key in ("turns", "settled", "open"))
    ):
        raise LandError(f"the newest `plan.talk` of {task.slug} does not have the form `reviewer=AGENT turns:=N settled:=N open:=N`; the lead writes it again with `project.py log`")
    # Each defect a review saw outside the change has its item in the tip, so that none is lost: one
    # that a session never filed, and one whose item a later commit took out.
    if unfiled:
        raise LandError(
            f"{len(unfiled)} defect(s) a review saw outside the change have no item in the backlog: "
            + "; ".join(f"\"{defect['title']}\" (round {defect['round']})" for defect in unfiled)
            + f". `land.py file {task.slug}` files them, then `land.py gate {task.slug}`",
        )
    gone = [(read, defect) for read in reads if read["answered"] for defect in outside_of(task, read) if not in_tree(task, tip, defect["item"])]
    if gone:
        read, defect = gone[0]
        raise LandError(
            f"the item {defect['item']} of the defect \"{defect['title']}\" (review round {read['round']}) was removed after it was filed"
            + (f", and {len(gone) - 1} more" if len(gone) > 1 else "")
            + f": a builder puts it back with `land.py file {task.slug} --again`, then `land.py gate {task.slug}`; when the owner does not want it, "
            "the item stays with `worth: no` and his reason in it, never deleted",
        )
    # A request is never proposed over an open question of the owner's.
    waiting = next((decision for decision in task.decisions() if decision["state"] == "waits"), None)
    if waiting:
        ends = (
            "it is a step that a later \"no\" cannot reverse, so only his answer ends it"
            if waiting["irreversible"] else f"or, after its wait ends at {waiting['deadline']}, `decisions.py timeout {task.slug} {waiting['id']}` takes the recommended option"
        )
        raise LandError(
            f"choice {waiting['id']} of {task.slug} waits for the owner ({waiting['what']}): a request is never proposed over an open question of his. "
            f"Lem writes his answer with `decisions.py answer {task.slug} {waiting['id']} --chose OPTION --words TEXT`, the option word for word and his own words beside it, or `--instead TEXT` "
            f"for a decision of his that is none of the options; {ends}",
        )
    notes = Path(notes_file).read_text(encoding="utf-8") if Path(notes_file).is_file() else None
    if notes is None:
        raise LandError(f"{notes_file} is not a file; --notes names the notes of the pull request")
    wanted = [*NOTES, *(["## Migration"] if state["careful"] else [])]
    missing = [heading for heading in wanted if not re.search(rf"(?m)^{re.escape(heading)}\s*$", notes)]
    if missing:
        raise LandError(f"the notes lack {', '.join(missing)}: they hold {', '.join(wanted)}, each with what is true of this task or the one word `none`")
    if not title.strip() or "\n" in title:
        raise LandError("--title is one line: the subject of the change")
    body = task.directory / "pr.md"
    body.write_text(pr_text(task, notes, state), encoding="utf-8")
    reasons = not_green(task, state)
    says = "green" if not reasons else f"not green: {'; '.join(reasons)}"
    # A careful path that the plan's own call missed is a lesson about that call: one event for the
    # retro, written the first time a proposal finds it.
    path = missed(task, state)
    if path and not any(record.get("event") == "careful.missed" for record in events_of(task)):
        script("project.py", task.worktree, "log", task.slug, "careful.missed", f"path={path['file']}", f"pattern={path['pattern']}")
    # for the retro: how often a request is not green, and for which reason
    script("project.py", task.worktree, "log", task.slug, "proposed", f"green:={json.dumps(not reasons)}", f"not_green:={json.dumps(reasons)}", f"tip={tip[:9]}")
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
            raise LandError(f"{intent['range']} is on {task.onto} from a landing that was cut off, and the branch has more work since: run `land.py start`, `land.py base` and `land.py gate` again for it")
    view = viewed(task) if kept.get("pr") else None
    if view and view["state"] == "MERGED":
        # the forge already holds the merge, whoever made it: only the bookkeeping is left
        return forge_done(task, view)
    may_merge(task, by)
    if not kept.get("gated"):
        raise LandError("no green check is on record for this tip; `land.py start`, `base` and `gate` come first")
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
            raise LandError("the pull request's head is not the tip that was proposed; run `land.py start`, `land.py base`, `land.py gate` and `land.py propose` again")
        task.fetch()
        base_now = git(task.worktree, "rev-parse", task.onto)
        moved = changed(task, kept["base"], base_now) if base_now != kept["base"] else []
        if not ignored(task, moved):
            raise LandError(
                f"{task.onto} moved after the checks ran, by files the gate reads ({', '.join(moved[:5])}{', ...' if len(moved) > 5 else ''}); "
                "run `land.py start`, `land.py base`, `land.py gate` and `land.py propose` again",
            )
        how = ["--squash", "--subject", message] if squash else ["--rebase"]
        gh(task, "pr", "merge", str(kept["pr"]["number"]), "--match-head-commit", tip, *how)
        view = viewed(task)
        if view["state"] != "MERGED":
            raise LandError("the forge took the merge and the pull request is not merged yet (a queue, or a check it waits for); run `land.py merged` when it is")
        return forge_done(task, view)
    if kept.get("proposed") != git(task.worktree, "rev-parse", "HEAD"):
        raise LandError("the branch's tip is not the tip that was proposed; run `land.py start`, `land.py base`, `land.py gate` and `land.py propose` again")

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
                f"{', ...' if len(arrived) > 5 else ''}); run `land.py start`, `land.py base` and `land.py gate` again",
            )
        if run(["git", "-C", str(task.worktree), "rebase", task.onto], check=False).returncode != 0:
            git(task.worktree, "rebase", "--abort", check=False)
            raise LandError(f"{task.onto} moved after the gate ran and the rebase onto it stopped; run `land.py start` and `land.py base` again")
    elif git(task.worktree, "rev-parse", "HEAD") != kept["gated"]:
        raise LandError("the branch's tip is not the commit the gate passed on; run `land.py start`, `land.py base` and `land.py gate` again")
    # What lands is the tree the gate saw, plus only the ignored files that arrived on the base.
    differs = changed(task, kept["tree"], "HEAD^{tree}")
    if not set(differs) <= set(arrived):
        raise LandError(f"the tree that would land differs from the tree the gate passed on in {', '.join(differs[:5])}; run `land.py start`, `land.py base` and `land.py gate` again")

    if squash:
        # A commit runs the project's hooks, and a hook may change what is committed. The one commit
        # must hold the tree that was just checked, so the branch is put back when it does not.
        before = git(task.worktree, "rev-parse", "HEAD")
        checked = git(task.worktree, "rev-parse", "HEAD^{tree}")
        git(task.worktree, "reset", "--soft", base_now)
        made = run(["git", "-C", str(task.worktree), "commit", "-m", message], check=False)
        if made.returncode != 0:
            git(task.worktree, "reset", "--soft", before)
            raise LandError(f"the one commit was refused, and the branch is as it was: {(made.stderr or made.stdout).strip()}")
        if git(task.worktree, "rev-parse", "HEAD^{tree}") != checked:
            git(task.worktree, "reset", "--hard", before)
            raise LandError(
                "a commit hook changed the files of the one commit, so it is not the tree the gate passed on; the branch is as it was. "
                "Commit what the hook changes on the branch, then run `land.py start`, `land.py base` and `land.py gate` again",
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
    if task.record["status"] not in ("landed", "dropped"):
        raise LandError(f"the task is {task.record['status']!r}; only a landed or dropped task loses its worktree")
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
    if task.record["status"] != "landed":
        # A dropped task's commits are on no other branch: its branch is the owner's to delete.
        removed["branch_left"] = f"{branch} holds the dropped task's commits; `git branch -D {branch}` deletes them"
        return {"task": task.slug, **removed}
    # `branch -d` judges by the checkout it runs in, which may be behind. The proof wanted is that
    # the base holds the branch's tip, so that is what is checked before the branch goes.
    # A pull request that the forge merged as one commit, or as a merge commit, leaves no such
    # proof in git: there the proof is that the branch's tip is the commit the forge merged.
    kept = task.kept()
    tip = git(task.main, "rev-parse", branch)
    on_base = run(["git", "-C", str(task.main), "merge-base", "--is-ancestor", tip, task.onto], check=False).returncode == 0
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
