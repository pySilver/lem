#!/usr/bin/env python3
"""Sort a repository's backlog items into who can act on them, with Jev, and keep the verdicts out of git.

The items are the .md files of `docs/backlog/`, or of the folder a project's settings name for
its backlog (`paths.backlog` in `.lem/project.toml`).

Usage: triage.py refresh [--all] [--repo DIR]   judge what changed (--all: everything), then print the groups
       triage.py report [--repo DIR] [--json]
       triage.py item SLUG [--repo DIR]   judge one item now, whatever its record says

Each item gets one of three verdicts:

- owner    it needs a decision only the owner can take;
- agent    an agent can plan and do it without the owner's input;
- waiting  it waits on an outside event that has not happened yet;
- decided  `worth: no`, a decision already taken; it is never sent to Jev.

refresh judges an item when it has no verdict or its text changed since the last one, and
re-checks a "waiting" item when the default branch has moved since its last check, giving Jev
the subjects of the commits that landed in between: that is when most triggers fire. Nothing is
judged on a timer. The verdicts live in Lem's state folder, `.lem/state/backlog-triage.json` of
the main checkout (`lem_state.py` names it), so they are never committed, every worktree shares
them, and Lem's removal takes them; a record whose item is gone is dropped. A file an older copy of this
script kept in the git directory itself is moved there on the first run.

Jev is called through JEV_BIN when it names a command, else through Lem's own `jev.py` beside this
skill, by its path, which is the file the plugin's `lem-jev` command runs. A `jev` command on PATH
is a developer's own, and is never taken for Lem's. An input Jev refuses as too long is reported under
"unjudged" with the reason; it is never cut down to fit.
"""

# The macOS system python3 (3.9) runs this from a keymap command or a launchd job; it needs this
# for `str | None`.
from __future__ import annotations

import hashlib
import json
import re
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Lem's scripts, beside this skill in the same plugin: `lem_state` is the one place that says where the state is.
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lem" / "scripts"))
import lem_state  # noqa: E402

VERDICTS = {
    "owner": (
        "The item needs a ruling the owner has not given yet: it says so (nobody has ruled, the owner "
        "decides, undecided, a choice between options), or the open question is what the product should "
        "do, a matter of taste, or which cost to accept when the options cost users or the business "
        "something different. A `worth: later` whose open unknown is a value judgment belongs here."
    ),
    "agent": (
        "An agent could plan and do this now without asking the owner anything new: what is wrong and what "
        "done looks like are stated, and any ruling it needs is already recorded in the item. Being large, "
        "needing a plan rather than a single change, or including its own measurement, paid run or test as "
        "part of the work does not make it wait."
    ),
    "waiting": (
        "The item itself names an event outside the project's control as the condition for acting, and "
        "that event has not happened: production traffic, real usage data, another team's or a vendor's "
        "release, a separately tracked plan or branch landing first. A dependency the work can satisfy "
        "itself is not waiting. When the recent commits show the named event has happened, this is no "
        "longer the answer."
    ),
}
INSTRUCTIONS = (
    "This is one item from a software project's backlog of deferred work. Decide who can act on it next. "
    "Judge from the item's own text, and from the recent commits when they are listed."
)
CONTEXT = (
    "Backlog items record real deferred work: a defect, an open decision, a fix whose blast radius was "
    "too large for the change that found it. Its front matter `worth` is yes (agreed worth fixing), later "
    "(the value itself is undecided; the body names the unknown) or no (decided against, kept so it is not "
    "re-argued). The project has one owner who rules on product intent; agents plan and implement."
)
CONCURRENCY = 8


def fail(message: str) -> None:
    print(f"triage: {message}", file=sys.stderr)
    sys.exit(1)


def git(repo: Path, *args: str) -> str:
    done = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if done.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {done.stderr.strip()}")
    return done.stdout.strip()


def default_branch_head(repo: Path) -> str:
    try:
        ref = git(repo, "symbolic-ref", "refs/remotes/origin/HEAD")
    except RuntimeError:
        ref = ""
    candidates = [ref] if ref else []
    candidates += [f"refs/remotes/origin/{b}" for b in ("master", "main", "trunk")]
    candidates += [f"refs/heads/{b}" for b in ("master", "main", "trunk")]
    for candidate in candidates:
        try:
            return git(repo, "rev-parse", "--verify", "--quiet", candidate)
        except RuntimeError:
            continue
    fail(f"{repo} has no default branch to watch")
    raise AssertionError


class Store:
    def __init__(self, repo: Path) -> None:
        common = Path(git(repo, "rev-parse", "--git-common-dir"))
        git_dir = (common if common.is_absolute() else (repo / common)).resolve()
        try:
            self.path = lem_state.folder(repo) / "backlog-triage.json"
        except lem_state.StateError as error:
            fail(str(error))
        old = git_dir / "backlog-triage.json"
        if old.is_file() and not self.path.exists():
            # where an older copy kept it, outside the folder Lem's removal deletes: moved once, whole
            self.path.parent.mkdir(exist_ok=True)
            os.replace(old, self.path)
        self.records: dict = {}
        if self.path.is_file():
            try:
                self.records = json.loads(self.path.read_text(encoding="utf-8"))
            except ValueError as error:
                fail(f"{self.path} does not read as JSON ({error}); it holds only verdicts, so remove it and run refresh --all")
            if not isinstance(self.records, dict):
                fail(f"{self.path} is not an object of verdicts; remove it and run refresh --all")

    def save(self) -> None:
        self.path.parent.mkdir(exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.records, indent=1, sort_keys=True), encoding="utf-8")
        tmp.replace(self.path)


# Lem's own client of Jev, beside this skill in the same plugin
OWN_JEV = Path(__file__).resolve().parents[2] / "lem" / "scripts" / "jev.py"


def jev_bin() -> list[str]:
    """The command that asks Jev: JEV_BIN, or Lem's own jev.py by its path."""
    found = os.environ.get("JEV_BIN")
    if found:
        return [found]
    if not OWN_JEV.is_file():
        fail(f"no {OWN_JEV}, the client of Jev that comes with Lem; reinstall Lem's plugin, or set JEV_BIN to a command that answers as it does")
    return [sys.executable, "-B", str(OWN_JEV)]


def judge(jev: list[str], item_text: str, commits: list[str]) -> dict:
    state = f"{CONTEXT}\n\n--- the item ---\n{item_text}"
    if commits:
        state += "\n\n--- commits landed on the default branch since this item was last judged ---\n" + "\n".join(commits)
    spec = {"state": state, "questions": {"triage": {"instructions": INSTRUCTIONS, "choices": VERDICTS}}}
    done = subprocess.run([*jev, "-"], input=json.dumps(spec), capture_output=True, text=True)
    if done.returncode == 3:
        return {"unjudged": done.stderr.strip()}
    if done.returncode:
        raise RuntimeError(done.stderr.strip() or f"jev exited {done.returncode}")
    answer = json.loads(done.stdout)["answers"]["triage"]
    return {"verdict": answer["choice"], "confidence": answer["confidence"], "probabilities": answer["probabilities"]}


def backlog_folder(repo: Path) -> Path:
    """`docs/backlog`, or the folder the project's settings name for it."""
    if not (repo / ".lem" / "project.toml").is_file():
        return repo / "docs" / "backlog"
    settings = Path(__file__).resolve().parents[2] / "lem" / "scripts" / "project.py"
    done = subprocess.run([sys.executable, "-B", str(settings), "--repo", str(repo), "path", "backlog"], capture_output=True, text=True)
    if done.returncode != 0:
        fail(done.stderr.strip() or "could not read the project's settings")
    return Path(done.stdout.strip())


def items(repo: Path) -> dict[str, str]:
    folder = backlog_folder(repo)
    if not folder.is_dir():
        fail(f"{folder} does not exist")
    found = {}
    for path in sorted(folder.glob("*.md")):
        try:
            found[path.stem] = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as error:
            fail(f"{path} is not UTF-8 text (byte {error.start} does not read); save the item as UTF-8")
    return found


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def refresh(repo: Path, store: Store, only: str | None = None, force: bool = False) -> None:
    jev = jev_bin()
    head = default_branch_head(repo)
    current = items(repo)
    if only is not None and only not in current:
        fail(f"no item {only}.md in {backlog_folder(repo)}")
    for gone in set(store.records) - set(current):
        del store.records[gone]
    work = []
    for slug, text in current.items():
        if only is not None and slug != only:
            continue
        record = store.records.get(slug)
        if re.search(r"(?m)^worth:\s*no\s*$", text.split("\n---", 1)[0]):
            store.records[slug] = {"verdict": "decided", "hash": digest(text), "head": head, "checked": int(time.time())}
            continue
        if force or only is not None or record is None or record.get("hash") != digest(text):
            work.append((slug, text, []))
        elif record.get("verdict") == "waiting" and record.get("head") != head:
            log = git(repo, "log", "--format=%h %s", f"{record['head']}..{head}") if record.get("head") else ""
            work.append((slug, text, log.splitlines()))

    def run(job: tuple[str, str, list[str]]) -> tuple[str, dict]:
        slug, text, commits = job
        return slug, judge(jev, text, commits)

    with ThreadPoolExecutor(CONCURRENCY) as pool:
        for slug, result in pool.map(run, work):
            store.records[slug] = {**result, "hash": digest(current[slug]), "head": head, "checked": int(time.time())}
    store.save()
    print(f"judged {len(work)} of {len(current)} items", file=sys.stderr)


def report(store: Store, as_json: bool) -> None:
    groups: dict[str, list] = {"owner": [], "agent": [], "waiting": [], "decided": [], "unjudged": []}
    for slug, record in sorted(store.records.items()):
        key = record.get("verdict", "unjudged")
        groups[key].append({"slug": slug, "confidence": record.get("confidence"), "why_unjudged": record.get("unjudged")})
    if as_json:
        print(json.dumps(groups, indent=1))
        return
    titles = {"owner": "Needs the owner", "agent": "An agent can take it", "waiting": "Waiting on a trigger", "decided": "Decided against (worth: no)", "unjudged": "Not judged"}
    for key, title in titles.items():
        if not groups[key]:
            continue
        print(f"{title} ({len(groups[key])})")
        for entry in groups[key]:
            note = entry["why_unjudged"] or (f"{entry['confidence']:.2f}" if entry["confidence"] is not None else "")
            print(f"  {entry['slug']}  {note}")


def main(argv: list[str]) -> None:
    if not argv or argv[0] not in {"refresh", "report", "item"}:
        fail("usage: triage.py refresh|report [--json]|item SLUG [--repo DIR]")
    command, rest = argv[0], argv[1:]
    repo = Path.cwd()
    if "--repo" in rest:
        i = rest.index("--repo")
        repo = Path(rest[i + 1]).resolve()
        del rest[i : i + 2]
    repo = Path(git(repo, "rev-parse", "--show-toplevel"))
    store = Store(repo)
    if command == "item":
        if len(rest) != 1:
            fail("usage: triage.py item SLUG")
        refresh(repo, store, only=rest[0])
        report(store, as_json=False)
    elif command == "refresh":
        refresh(repo, store, force="--all" in rest)
        report(store, as_json="--json" in rest)
    else:
        report(store, as_json="--json" in rest)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except RuntimeError as error:
        fail(str(error))
