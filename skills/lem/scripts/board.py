#!/usr/bin/env python3
"""Open Lem's board in agterm: every task of the repository, or one task.

    lem board [--repo DIR] [--follow]               the board of all tasks
    lem board [--repo DIR] [--follow] --task SLUG   the board of one task
    lem board [--repo DIR] [--task SLUG] --no-open  write the page's files and print where; open nothing
    lem board ... --demo                            mark the state folder's tasks as examples, for good
    lem board --page FILE [--name NAME] [--follow]  open any page of Lem to read, as a companion the same way

Every page of Lem that the owner reads (the board, the page of a task, the hand-over page of the
onboarding) opens this way, as a companion, and never as an overlay over Lem's session (the owner,
2026-11-18: "Command like this and possibly others that opens html overlay should be opened in
companion"). A page that waits for an answer is no such page: a question and a text to mark up
open over the session, which waits for their result.

The page is `assets/board.html`. It draws the files beside it in the state folder: `events.js`,
which `project.py` appends to, and `meta.js`, which this script writes (the repository's name,
the base branch, the session that opened the board, and how many commands one run of
the checks has, `gates`, so the page knows when a run is complete). A file:// page cannot read a file with
fetch and it can load a script, so each of them is one.

The board's second tab is the backlog, from `backlog.js`, which this script writes at every run:
each item of the settings' backlog folder in the main checkout, with its `worth`, its `where` and
whether that still resolves, and whether git has it committed. Items change rarely, so the page reads that file when
the tab opens and on a key, and it says when the file was written. A run with `--no-open` writes
it again without touching agterm, and keeps the session the board already names: the tab's one
action types an ask into that session, so only a run that opens the board says which one it is.

The page, the stylesheet it links (`assets/lem.css`, the look every page of Lem shares) and the
script that gives that look Lem's light or dark palette (`assets/lem.js`) are copied into the
state folder at every open, so an older checkout gets the current ones.
A copy named `task-SLUG.html` opens on that task.

It opens as a page companion of the top session of the asking session's group: it sits indented
under Lem's session, or beside it when Lem's session is itself a companion, closes with that top
session, and covers no pane. A board that is already there is reloaded. It is known by the file
it shows, which agterm reports for a page, so the boards of two repositories under one top
session stay two. agterm never saves a page companion, so after a relaunch of agterm the board
is gone until this runs again.

It runs from an agent's session, which has the AGTERM_* variables, and from an agterm keymap
command, which has AGT_* instead.
"""

from __future__ import annotations

import sys

if sys.version_info < (3, 11):
    # an old python3 must still load this file, so that it can say what it needs and not a traceback
    sys.exit(f"board.py: Lem needs Python 3.11 or newer, and this python3 is {sys.version.split()[0]}; put a newer one first on PATH, or run this file with it")

import argparse
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ASSET = SCRIPTS.parent / "assets" / "board.html"
# the look every page of Lem shares, and the script that picks its palette; the board links both,
# so they go beside the page
STYLE = SCRIPTS.parent / "assets" / "lem.css"
PALETTE = SCRIPTS.parent / "assets" / "lem.js"
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
    # a line project.py writes on stderr when it succeeds (the settings read from the base branch) is this script's to say too
    if ran.returncode == 0 and ran.stderr:
        sys.stderr.write(ran.stderr)
    return ran.stdout.strip()


def where_problem(root: Path, where: str) -> str:
    """What of an item's `where` no longer resolves, or "": the check the backlog skill makes before it reports an item."""
    path, _, symbol = where.partition(":")
    path, symbol = path.strip(), symbol.strip()
    if not path:
        return ""
    target = root / path
    if not target.resolve().is_relative_to(root.resolve()):
        return "the path leaves the repository"
    if not target.exists():
        return "the file is not there"
    if not symbol or target.is_dir():
        return ""
    try:
        text = target.read_text(encoding="utf-8", errors="replace")
    except OSError:
        # a file nobody may read (mode 000) is a problem of this item, not a reason to stop the board
        return "the file cannot be read"
    if target.suffix == ".md":
        return "" if symbol in text else "the heading is not in the file"
    missing = [part for part in symbol.split(".") if part and not re.search(rf"\b{re.escape(part)}\b", text)]
    return f"not in the file: {'.'.join(missing)}" if missing else ""


def backlog(settings: dict) -> dict:
    """The items of the backlog folder, as the board's second tab shows them. It reads and changes nothing."""
    main = Path(settings["main"])
    # the main checkout's copy: a task's worktree has the backlog as its branch left it
    folder = main / Path(settings["places"]["backlog"]["path"]).relative_to(settings["root"])
    relative = folder.relative_to(main).as_posix()
    feed: dict = {"folder": relative, "read": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "items": []}
    if not folder.is_dir():
        return feed

    def git(*args: str) -> str:
        ran = subprocess.run(["git", "-C", str(main), *args], capture_output=True, text=True, check=False)
        return ran.stdout if ran.returncode == 0 else ""

    # what git does not have committed yet: an item the closing pass filed a minute ago is `new`
    changed = {}
    # --untracked-files=all: a folder git does not know yet is listed file by file, not as one line
    for entry in git("status", "--porcelain", "--untracked-files=all", "-z", "--", relative).split("\0"):
        if len(entry) > 3:
            code = entry[:2]
            changed[entry[3:]] = "new" if code == "??" or "A" in code else "edited"
    for file in sorted(folder.glob("*.md")):
        rel = f"{relative}/{file.name}"
        try:
            text = file.read_text(encoding="utf-8", errors="replace")
        except OSError as error:
            # A link to a file that moved, or a folder with an item's name: shown, not hidden, and
            # the other items are still read.
            feed["items"].append({
                "slug": file.stem, "path": rel, "title": file.stem, "worth": "unset", "where": "", "where_problem": "", "added": "",
                "state": "unreadable", "body": f"This item cannot be read: {error.strerror or error}.",
            })
            continue
        fields: dict[str, str] = {}
        body = text
        if text.startswith("---"):
            head, mark, rest = text[3:].partition("\n---")
            if mark:
                body = rest.split("\n", 1)[1] if "\n" in rest else ""
                for line in head.splitlines():
                    key, colon, value = line.partition(":")
                    if colon and key.strip() in ("worth", "where", "added"):
                        fields[key.strip()] = value.strip().strip("\"'")
        title = re.search(r"(?m)^#\s+(.+)$", body)
        if title:
            body = body[: title.start()] + body[title.end():]
        where = fields.get("where", "")
        feed["items"].append({
            "slug": file.stem, "path": rel, "title": (title.group(1) if title else file.stem).replace("`", "").strip(),
            "worth": fields.get("worth") if fields.get("worth") in ("yes", "later", "no") else "unset",
            "where": where, "where_problem": where_problem(main, where) if where else "",
            "added": fields.get("added", ""), "state": changed.get(rel, ""),
            "body": body.strip(),
        })
    return feed


def prepare(repo: str, slug: str | None, session: str, demo: bool = False, keep_session: bool = False) -> tuple[Path, str]:
    """Write the page and meta.js into the state folder, and return the page's path and the repository's name."""
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
    # `gates` is how many commands one run of the checks has, so the page knows when a run is complete;
    # `serial` how many of them are `checks.serial`, which do not run after a red command.
    meta = {
        "repo": Path(settings["main"]).name, "base": settings["branch"]["base"], "session": session,
        "gates": len(settings["checks"]["commands"]) + len(settings["checks"]["serial"]),
        # the commands of `checks.serial`, which run last and only when the others passed
        "serial": len(settings["checks"]["serial"]),
    }
    if keep_session:
        # A run that opens nothing only writes the files again. The session the board names is the
        # one that opened it: the page types an ask into it, so a run from another session, a
        # lead's or none at all, must not change where that ask goes.
        known = re.fullmatch(r"lemMeta\((.*)\);\n", (state / "meta.js").read_text(encoding="utf-8"), re.S) if (state / "meta.js").is_file() else None
        try:
            before = json.loads(known.group(1)) if known else {}
        except ValueError:
            before = {}
        if isinstance(before, dict) and isinstance(before.get("session"), str) and before["session"]:
            meta["session"] = before["session"]
    # A board of made-up tasks must say so itself: a line under "Waits for you" reads as a call to
    # act. The mark is a file beside the events, because it is a fact about the data and not about
    # one open: `/lem status` opens the same folder later with no flag, and the page must still say it.
    marker = state / "demo"
    if demo:
        marker.write_text("The tasks in this folder are examples, written by a fixture. board.py --demo made this file.\n")
    if marker.is_file():
        meta["demo"] = True
    (state / "meta.js").write_text(f"lemMeta({json.dumps(meta, ensure_ascii=False)});\n", encoding="utf-8")
    # `</` is split so that no item's text can end the script tag the page loads this file with
    items = json.dumps(backlog(settings), ensure_ascii=False).replace("</", "<\\/")
    (state / "backlog.js").write_text(f"lemBacklog({items});\n", encoding="utf-8")
    page = state / (f"task-{slug}.html" if slug else "board.html")
    shutil.copyfile(ASSET, page)
    shutil.copyfile(STYLE, state / STYLE.name)
    shutil.copyfile(PALETTE, state / PALETTE.name)
    return page, meta["repo"]


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
    # A board is known by the file it shows, under this session's own group. Its name is not enough:
    # two Lems of two repositories may be companions of one top session, and each has a board. The
    # file is in its repository's own state folder, so it tells them apart.
    def shows(node: dict) -> bool:
        files = [overlay.get("file") or overlay.get("page") or "" for overlay in node.get("htmlOverlays") or []]
        return any(file and os.path.realpath(file) == os.path.realpath(page) for file in files)

    named = [s for s in live if s.get("content") == "page" and (s.get("parent") or "").upper() == parent and shows(s)]
    kept = named[0] if named else None
    stale = named[1:]
    if stale:
        ctl(socket, "session", "close", *[arg for s in stale for arg in ("--target", s["id"])])
    if kept:
        target = kept["id"]
        ctl(socket, "session", "overlay", "reload", "--target", target)
        if kept.get("name") != name:
            ctl(socket, "session", "rename", name, "--target", target)
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


def open_page(page: Path, args: argparse.Namespace, session: str, socket: str) -> dict:
    """One page of Lem to read, opened as the board opens: a page companion of the session's group,
    known by the file it shows, so the same file shown again reloads its companion."""
    if args.task or args.demo or args.no_open:
        raise BoardError("--page opens one file; --task, --demo and --no-open belong to the board")
    page = page.resolve()
    if not page.is_file() or page.suffix.lower() not in (".html", ".htm"):
        raise BoardError(f"--page {page} is not an HTML file: give the page to open")
    if not (session and socket):
        raise BoardError("not inside an agterm session, so no companion can open; give the owner the file's path instead")
    name = args.name or page.stem
    return {"page": str(page), "name": name, **show(page, name, session, socket, env("AGT_WINDOW_ID", "AGTERM_WINDOW_ID"), args.follow)}


def main() -> None:
    parser = argparse.ArgumentParser(prog="lem board", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=env("AGT_SESSION_PWD") or ".", help="a directory inside the checkout (default: the current one)")
    parser.add_argument("--task", metavar="SLUG", help="open the board of this task instead of the board of all tasks")
    parser.add_argument("--follow", action="store_true", help="switch to the board after it opens")
    parser.add_argument("--no-open", action="store_true", help="write the files and print the page's path; open nothing")
    parser.add_argument("--demo", action="store_true", help="the state folder holds example tasks: every board of it says so from now on")
    parser.add_argument("--page", metavar="FILE", help="open this HTML file as a page companion, as the board opens, or reload the one that shows it")
    parser.add_argument("--name", help="with --page: the companion's name (default: the file's name)")
    args = parser.parse_args()
    session = env("AGT_SESSION_ID", "AGTERM_SESSION_ID")
    socket = env("AGT_SOCKET", "AGTERM_SOCKET")
    try:
        if args.page is not None:
            print(json.dumps(open_page(Path(args.page), args, session, socket), indent=2))
            return
        if args.name is not None:
            raise BoardError("--name goes with --page: the board names itself")
        if not args.no_open and not (session and socket):
            raise BoardError("not inside an agterm session; --no-open writes the page without one")
        page, repo = prepare(args.repo, args.task, session, args.demo, keep_session=args.no_open)
        # the repository's name is in the name of its board of all tasks, so two boards in one sidebar read apart
        result: dict = {"page": str(page), "name": f"{args.task} board" if args.task else f"Lem board · {repo}"}
        if not args.no_open:
            result |= show(page, result["name"], session, socket, env("AGT_WINDOW_ID", "AGTERM_WINDOW_ID"), args.follow)
    except BoardError as error:
        sys.exit(f"board.py: {error}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
