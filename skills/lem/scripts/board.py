#!/usr/bin/env python3
"""Open Lem's board in agterm: every task of the repository, or one task.

    board.py [--repo DIR] [--follow]               the board of all tasks
    board.py [--repo DIR] [--follow] --task SLUG   the board of one task
    board.py [--repo DIR] [--task SLUG] --no-open  write the page's files and print where; open nothing

The page is `assets/board.html`. It draws the files beside it in the state folder: `events.js`
and `review-queue.js`, which `project.py` and `review_queue.py` append to, and `meta.js`, which
this script writes (the repository's name, the base branch, the session that opened the board). A
file:// page cannot read a file with fetch and it can load a script, so each of the three is one.
The page is copied into the state folder at every open, so an older checkout gets the current one.
A copy named `task-SLUG.html` opens on that task.

It opens as a page companion of the session that asks, the top one of its group: it sits indented
under Lem's session, closes with it, and covers no pane. A board that is already there is
reloaded. agterm never saves a page companion, so after a relaunch of agterm the board is gone
until this runs again.

It runs from an agent's session, which has the AGTERM_* variables, and from an agterm keymap
command, which has AGT_* instead.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ASSET = SCRIPTS.parent / "assets" / "board.html"
SLUG = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
TINT = "green"


class BoardError(Exception):
    pass


def env(*names: str) -> str:
    return next((os.environ[name] for name in names if os.environ.get(name)), "")


def project(repo: str, *args: str) -> str:
    """One command of project.py, so the board reads a repository the way every stage does."""
    ran = subprocess.run(
        [sys.executable, "-B", str(SCRIPTS / "project.py"), "--repo", repo, *args], capture_output=True, text=True, check=False,
    )
    if ran.returncode != 0:
        raise BoardError(ran.stderr.strip().removeprefix("project.py: ") or f"project.py {args[0]} failed")
    return ran.stdout.strip()


def prepare(repo: str, slug: str | None, session: str) -> Path:
    """Write the page and meta.js into the state folder, and return the page's path."""
    if not ASSET.is_file():
        raise BoardError(f"{ASSET} is missing")
    state = Path(project(repo, "state-dir"))
    settings = json.loads(project(repo, "show"))
    if slug is not None:
        if not SLUG.fullmatch(slug):
            raise BoardError(f"slug {slug!r} must be lower-case words joined by hyphens")
        if not (state / "tasks" / slug).is_dir():
            known = ", ".join(task["slug"] for task in json.loads(project(repo, "tasks"))) or "none yet"
            raise BoardError(f"no task {slug!r}; the tasks are: {known}")
    # The main checkout names the repository; a worktree's folder is named after its task.
    listed = subprocess.run(["git", "-C", repo, "worktree", "list", "--porcelain"], capture_output=True, text=True, check=False)
    main = next((line.removeprefix("worktree ") for line in listed.stdout.splitlines() if line.startswith("worktree ")), settings["root"])
    meta = {"repo": Path(main).name, "base": settings["branch"]["base"], "session": session}
    (state / "meta.js").write_text(f"lemMeta({json.dumps(meta, ensure_ascii=False)});\n", encoding="utf-8")
    page = state / (f"task-{slug}.html" if slug else "board.html")
    shutil.copyfile(ASSET, page)
    return page


def ctl(socket: str, *args: str) -> str:
    # agtermctl never reads the socket from the environment, and a bare call may reach another
    # agterm than the one that hosts this session.
    ran = subprocess.run(["agtermctl", *args, "--socket", socket], capture_output=True, text=True, check=False)
    if ran.returncode != 0:
        raise BoardError(f"agtermctl {' '.join(args[:3])} failed: {(ran.stderr or ran.stdout).strip()}")
    return ran.stdout


def show(page: Path, name: str, session: str, socket: str, window: str, follow: bool) -> dict:
    """Open the page as a companion of the session's group, or reload the one that is there."""
    in_window = ["--window", window] if window else []
    tree = json.loads(ctl(socket, "tree", "--json", *in_window))["result"]["tree"]
    live = [s for workspace in tree.get("workspaces", []) for s in workspace.get("sessions", [])]
    owner = next((s for s in live if s["id"].upper() == session.upper()), None)
    if owner is None:
        raise BoardError(f"this session ({session}) is not in the window agterm answered for")
    # A companion's companion becomes its sibling, so the parent is the top of the group.
    parent = (owner.get("parent") or owner["id"]).upper()
    named = [s for s in live if s.get("name") == name]
    kept = next((s for s in named if s.get("content") == "page" and (s.get("parent") or "").upper() == parent), None)
    stale = [s for s in named if s is not kept and s.get("content") == "page"]
    if stale:
        ctl(socket, "session", "close", *[arg for s in stale for arg in ("--target", s["id"])])
    if kept:
        target = kept["id"]
        ctl(socket, "session", "overlay", "reload", "--target", target)
    else:
        opened = ctl(
            socket, "session", "overlay", "open", "--html", str(page), "--cwd", str(page.parent),
            "--js", "--companion", "--target", parent, "--json",
        )
        target = json.loads(opened)["result"]["id"]
        ctl(socket, "session", "rename", name, "--target", target)
    ctl(socket, "session", "tint", TINT, "--on", "icon,name", "--target", target)
    if follow:
        ctl(socket, "session", "select", "--target", target)
    return {"companion": target, "parent": parent, "reloaded": kept is not None}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=env("AGT_SESSION_PWD") or ".", help="a directory inside the checkout (default: the current one)")
    parser.add_argument("--task", metavar="SLUG", help="open the board of this task instead of the board of all tasks")
    parser.add_argument("--follow", action="store_true", help="switch to the board after it opens")
    parser.add_argument("--no-open", action="store_true", help="write the files and print the page's path; open nothing")
    args = parser.parse_args()
    session = env("AGT_SESSION_ID", "AGTERM_SESSION_ID")
    socket = env("AGT_SOCKET", "AGTERM_SOCKET")
    try:
        if not args.no_open and not (session and socket):
            raise BoardError("not inside an agterm session; --no-open writes the page without one")
        page = prepare(args.repo, args.task, session)
        result: dict = {"page": str(page), "name": f"{args.task} board" if args.task else "Lem board"}
        if not args.no_open:
            result |= show(page, result["name"], session, socket, env("AGT_WINDOW_ID", "AGTERM_WINDOW_ID"), args.follow)
    except BoardError as error:
        sys.exit(f"board.py: {error}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
