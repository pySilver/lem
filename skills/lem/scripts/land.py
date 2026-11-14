#!/usr/bin/env python3
"""Land one task's branch on the project's base branch, one step at a time.

Lem lands one branch at a time. Each step here is one command, prints JSON, and refuses with
exit 1 and the reason when the step may not run; nothing is retried and nothing is forced. Every
step first asks `project.py may-land` about the settings' base branch, so a protected branch is
never reached, whoever asks.

    land.py start SLUG     the task takes the landing line: its state becomes `landing`
    land.py base SLUG      bring the base branch in by a rebase; a conflict is reported, not resolved
    land.py gate SLUG      run every gate command on the tip, each with its output in a file
    land.py land SLUG --risk high|normal [--message SUBJECT]
                           put the gated tip on the base branch and queue its review
    land.py clean SLUG     remove the task's worktree and its branch after the landing

What each step keeps for the next is in `landing.json` in the task's directory: the task's
branch, the base it was rebased on, and the commit and tree the gate passed on. `land` lands only
that tree: when the tip is another tree than the gate saw, or the base moved by more than the
paths the settings' `gate.ignores` name, it refuses and says to run `base` and `gate` again.

A step that was cut off is run again. `land` writes down the commit it is about to put on the base
before it does, so a second run that finds that commit on the base only finishes the bookkeeping:
the review item and the state. `clean` knows the branch from `landing.json`, so it finds it after
the worktree is gone.

The landing is a fast-forward and nothing else. With a remote named `origin` the tip is pushed to
the base branch there with a plain push, which the remote refuses when someone else pushed first;
then the checkout that holds the base branch is fast-forwarded when it is clean, and left alone
with a note when it is not. With no remote, the base branch itself is fast-forwarded. A branch is
never force-pushed and a ref is never moved behind a checkout's back.
"""

import argparse
import fnmatch
import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
RISKS = ("high", "normal")
HISTORY = ("keep", "squash")


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
        listed = git(repo, "worktree", "list", "--porcelain")
        entries = [block.splitlines() for block in listed.split("\n\n") if block.strip()]
        self.main = Path(entries[0][0].removeprefix("worktree "))
        relative = Path(self.settings["paths"]["worktrees"]["path"]).relative_to(Path(self.settings["root"]).resolve())
        self.worktree = self.main / relative / slug
        # the checkout that holds the base branch, when one does
        self.base_checkout = next(
            (Path(entry[0].removeprefix("worktree ")) for entry in entries if f"branch refs/heads/{self.base}" in entry), None,
        )
        self.remote = git(self.main, "remote", "get-url", "origin", check=False) != ""
        self.onto = f"origin/{self.base}" if self.remote else str(self.base)
        self.kept_file = self.directory / "landing.json"

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

    def fetch(self) -> None:
        if self.remote:
            git(self.main, "fetch", "origin", str(self.base))


def cmd_start(task: Task) -> dict:
    if task.others_landing:
        raise LandError(f"{task.others_landing[0]} is in `landing`: one branch lands at a time, so finish that one first")
    if task.record["status"] not in ("ready", "landing"):
        raise LandError(f"the task is {task.record['status']!r}; only a `ready` task takes the landing line")
    if not task.settings["gate"]["commands"]:
        task.state("blocked", "the project has no gate command")
        raise LandError(
            "the project has no gate command, so nothing would show that the change works; the task is now `blocked`. "
            "Add the commands to gate.commands in .lem/project.toml",
        )
    task.need_worktree()
    if task.record["status"] != "landing":
        task.kept_file.unlink(missing_ok=True)
        # kept here because `clean` needs the branch after the worktree, which names it, is gone
        task.keep(branch=git(task.worktree, "branch", "--show-current"))
        task.state("landing", "the landing starts")
    return {"task": task.slug, "base": task.base, "worktree": str(task.worktree), "remote": task.remote}


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
    task.keep(gated=tip if green else None, tree=git(task.worktree, "rev-parse", "HEAD^{tree}") if green else None)
    result = {"task": task.slug, "tip": tip, "green": green, "commands": results}
    if not green:
        print(json.dumps(result, indent=2))
        red = [r["command"] for r in results if r["exit"] != 0]
        raise LandError(f"the gate is red on {len(red)} command(s): {'; '.join(red)}. A builder reads the output files; the gate is never edited to pass")
    return result


def ignored(task: Task, files: list[str]) -> bool:
    patterns = task.settings["gate"]["ignores"]
    return all(any(fnmatch.fnmatchcase(file, pattern) for pattern in patterns) for file in files)


def changed(task: Task, old: str, new: str) -> list[str]:
    """Every path that differs between two trees. A rename counts as the path that went and the path that came."""
    return git(task.worktree, "diff", "--name-only", "--no-renames", old, new).splitlines()


def queue_review(task: Task, landed: str, risk: str) -> int:
    """The review item of a landed range. A range is queued once, whatever became of its item since."""
    queued = json.loads(script("review_queue.py", task.main, "list", "--all").stdout)
    known = next((entry["id"] for entry in queued if entry["slug"] == task.slug and entry["range"] == landed), None)
    if known is not None:
        return known
    return int(script("review_queue.py", task.main, "add", task.slug, "--range", landed, "--risk", risk).stdout.strip())


def finish(task: Task, tip: str, landed: str, risk: str, arrived: list[str]) -> dict:
    """The bookkeeping after the base holds the tip: the base checkout follows, the review is queued, the state says landed."""
    left_behind = None
    if task.remote and task.base_checkout is not None:
        # The checkout that holds the base follows, so the next task's worktree starts from what just
        # landed. git refuses the fast-forward, and changes nothing, when a file with changes of its
        # own is in the way or the checkout has commits the remote lacks; then it stays as it is.
        followed = run(["git", "-C", str(task.base_checkout), "merge", "--ff-only", f"origin/{task.base}"], check=False)
        if followed.returncode != 0:
            why = [line for line in (followed.stderr or followed.stdout).strip().splitlines() if line.strip()]
            left_behind = f"{task.base_checkout} did not follow origin/{task.base}, and nothing in it was changed. git said: {why[-1] if why else 'nothing'}"
    item = queue_review(task, landed, risk)
    task.keep(landed=landed, review=item)
    task.state("landed", f"{task.base} {landed}", f"review item {item}, {risk}")
    # Dropped last: until the state says `landed`, a run that is cut off must find the record again.
    task.keep(intent=None)
    return {"task": task.slug, "base": task.base, "range": landed, "tip": tip, "pushed": task.remote, "review": item,
            "arrived": arrived, "left_behind": left_behind}


def cmd_land(task: Task, risk: str, message: str | None) -> dict:
    task.need_landing()
    task.need_worktree()
    if task.settings["branch"]["land"] != "agent":
        raise LandError("branch.land is \"owner\" in .lem/project.toml: the owner lands; report the gate's result and write the state `held`")
    kept = task.kept()
    if not kept.get("gated"):
        raise LandError(f"no green gate is on record for this tip; `land.py gate {task.slug}` comes first")
    squash = task.settings["branch"]["history"] == "squash"
    if squash and not message:
        raise LandError("branch.history is \"squash\": pass --message with the one commit's subject, from the task's report")
    if not squash and message:
        raise LandError("branch.history is \"keep\": the branch's own commits land, so --message has nothing to name")

    task.fetch()
    base_now = git(task.worktree, "rev-parse", task.onto)
    intent = kept.get("intent")
    if intent and run(["git", "-C", str(task.worktree), "merge-base", "--is-ancestor", intent["tip"], task.onto], check=False).returncode == 0:
        # An earlier run put this commit on the base and was cut off before the bookkeeping.
        if git(task.worktree, "rev-parse", "HEAD") == intent["tip"]:
            return finish(task, intent["tip"], intent["range"], risk, intent["arrived"])
        # The branch got more work since. What landed then is queued for its review, and what the
        # branch holds now lands like any tip: through its own base and gate.
        queue_review(task, intent["range"], risk)
        task.keep(intent=None)
    arrived: list[str] = []
    if base_now != kept["base"]:
        # The base moved after the gate ran. The result stands only when every file that arrived is
        # one the project says the gate does not read.
        arrived = changed(task, kept["base"], base_now)
        if not ignored(task, arrived):
            raise LandError(
                f"{task.onto} moved after the gate ran, by files the gate reads ({', '.join(arrived[:5])}"
                f"{', ...' if len(arrived) > 5 else ''}); run `land.py base` and `land.py gate` again",
            )
        if run(["git", "-C", str(task.worktree), "rebase", task.onto], check=False).returncode != 0:
            git(task.worktree, "rebase", "--abort", check=False)
            raise LandError(f"{task.onto} moved after the gate ran and the rebase onto it stopped; run `land.py base` again")
    elif git(task.worktree, "rev-parse", "HEAD") != kept["gated"]:
        raise LandError("the branch's tip is not the commit the gate passed on; run `land.py gate` again")
    # What lands is the tree the gate saw, plus only the ignored files that arrived on the base.
    differs = changed(task, kept["tree"], "HEAD^{tree}")
    if not set(differs) <= set(arrived):
        raise LandError(f"the tree that would land differs from the tree the gate passed on in {', '.join(differs[:5])}; run `land.py gate` again")

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
                "Commit what the hook changes on the branch, then run `land.py base` and `land.py gate` again",
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
    return finish(task, tip, landed, risk, arrived)


def cmd_clean(task: Task) -> dict:
    if task.record["status"] not in ("landed", "dropped"):
        raise LandError(f"the task is {task.record['status']!r}; only a landed or dropped task loses its worktree")
    removed: dict = {"worktree": False, "branch": None, "branch_left": None}
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
    if run(["git", "-C", str(task.main), "merge-base", "--is-ancestor", branch, task.onto], check=False).returncode != 0:
        raise LandError(f"{task.onto} does not hold the tip of {branch}, so the branch stays")
    git(task.main, "branch", "-D", branch)
    removed["branch"] = branch
    return {"task": task.slug, **removed}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=".", help="a directory inside the checkout (default: the current one)")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("start", "base", "gate", "clean"):
        commands.add_parser(name).add_argument("slug")
    land = commands.add_parser("land")
    land.add_argument("slug")
    land.add_argument("--risk", required=True, choices=RISKS)
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
        elif args.command == "land":
            result = cmd_land(task, args.risk, args.message)
        else:
            result = cmd_clean(task)
    except LandError as error:
        sys.exit(f"land.py: {error}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
