#!/usr/bin/env python3
"""Open Lem's board in agterm: every task of the repository, or one task.

    lem board [--repo DIR] [--follow]               the board of all tasks
    lem board [--repo DIR] [--follow] --task SLUG   the board of one task
    lem board [--repo DIR] [--task SLUG] --no-open  print the board's address; open nothing
    lem board ... --demo                            mark the state folder's tasks as examples, for good
    lem board --page FILE [--name NAME] [--follow]  open any page of Lem to read, as a companion the same way

Every page of Lem that the owner reads (the board, the hand-over page of the onboarding, the page of
a task) opens this way, as a companion, and never as an overlay over the session (the owner,
2026-11-18: "Command like this and possibly others that opens html overlay should be opened in
companion"). A page that waits for an answer is no such page: a question and a text to mark up
open over the session, which waits for their result.

The board is the machine's board server, `lem serve` (serve.py), which draws it from the state
folder's files at each request and tells an open page each change: this script writes no file of the
page. A run makes sure the server runs (`lem serve --ensure`, at most SERVE_WAIT), puts the
repository's main checkout into the machine's list of workspaces (`lem_state.workspaces_file()`,
which the server shows; a state folder of example tasks, `--demo`, stays out of it), and asks the
server the address of the repository's board, `http://127.0.0.1:PORT/HOST/WORKSPACE/`, or of one
task, `.../tasks/SLUG`. A server that does not run is a failure that says why: nothing else draws
the board. `--no-open` prints the address and opens nothing.

It opens as a page companion of the top session of the asking session's group, as an http page with
its scripts on and its cookies kept (`--persistent`, so that the folded columns outlive a relaunch of
agterm): it sits indented under the asking session, or beside it when that session is itself a companion,
closes with that top session, and covers no pane. A board is known by its address: one companion for
each workspace under the top session, so the boards of two repositories under one top session stay
two. A board that is there already is reloaded where it stands, or opened again at the task asked
for. agterm never saves a page companion, so after a relaunch of agterm the board is gone until this
runs again.

It runs from an agent's session, which has the AGTERM_* variables, and from an agterm keymap
command, which has AGT_* instead.
"""

import sys

if sys.version_info < (3, 11):
    # an old python3 must still load this file, so that it can say what it needs and not a traceback
    sys.exit(f"board.py: Lem needs Python 3.11 or newer, and this python3 is {sys.version.split()[0]}; put a newer one first on PATH, or run this file with it")

import argparse
import importlib
import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

SCRIPTS = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(SCRIPTS))
lem_project = importlib.import_module("project")
lem_state = importlib.import_module("lem_state")
# the look every page of Lem shares, and the script that picks its palette, which the board links
STYLE = SCRIPTS.parent / "assets" / "lem.css"
PALETTE = SCRIPTS.parent / "assets" / "lem.js"
# the board's own look
BOARD_STYLE = SCRIPTS.parent / "assets" / "board.css"
# the board's script and its icons, built by tools/board-kit
VENDOR = SCRIPTS.parent / "assets" / "vendor"
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


def parse_item(text: str) -> tuple[dict[str, str], str, str]:
    """A backlog item in its format (agents/lem-builder.md, rule 6): the fields of its head between two
    `---` lines that the board reads (`worth`, `where`, `added`), the title of its `# TITLE` line
    without backticks ("" with none), and its body without the head and the title line."""
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
    return fields, (title.group(1).replace("`", "").strip() if title else ""), body


# A line of markdown that starts a block of its own: a list item, a heading, a quote, a table row, a fence,
# a rule; and a label that ends with a colon ("Today:"), after which a line starts anew.
BLOCK = re.compile(r"^\s*([-*+]\s|\d+[.)]\s|#|>|\||```|~~~|---|\*\*\*)")


def unwrapped(lines: list[str]) -> list[str]:
    """Markdown lines with each line that only wraps a sentence joined to the line before it, so that the
    board's reader, which keeps a line break as one, shows a paragraph as one; a list, a table, a quote,
    a fence and a label stay as they were written."""
    out: list[str] = []
    fence = None
    for line in lines:
        mark = re.match(r"^\s*(```|~~~)", line)
        if fence is not None or mark:
            if mark:
                fence = mark[1] if fence is None else (None if line.strip().startswith(fence) else fence)
            out.append(line)
            continue
        prev = out[-1] if out else ""
        joins = line.strip() and prev.strip() and not BLOCK.match(line) and not prev.rstrip().endswith(":") \
            and not re.match(r"^\s*(```|~~~|\||#)", prev) and not prev.endswith("  ")
        if joins:
            out[-1] = f"{prev.rstrip()} {line.strip()}"
        else:
            out.append(line)
    return out


def outcome(text: str) -> str:
    """What the owner gets, from a task.md: its `## Outcome` section, to the next heading of the same
    level or above, as the markdown it was written in (a story's lines, a list, a table and a chart read
    only so), with each line that only wraps a sentence joined to its paragraph (`unwrapped`). "" when the
    file has no such section, or an empty one. A heading inside a fenced block is no end of the section."""
    found = re.search(r"(?m)^##[ \t]+Outcome[ \t]*\n", text)
    if not found:
        return ""
    out, fence = [], None
    for line in text[found.end():].splitlines():
        mark = re.match(r"^\s*(```|~~~)", line)
        if mark and fence is None:
            fence = mark[1]
        elif mark and line.strip().startswith(fence):
            fence = None
        elif fence is None and re.match(r"^#{1,2}[ \t]", line):
            break
        out.append(line)
    return "\n".join(unwrapped(out)).strip()


def filed(worktree: Path, onto: str, folder: str) -> list[dict] | None:
    """The backlog items the branch checked out in a task's worktree adds against its merge base with
    `onto`, each with its path and its title, as git has them in the branch's newest commit; None when
    the worktree is gone or git cannot tell (no base, no merge base): nothing then says that none was filed."""
    if not onto or not (worktree / ".git").exists():
        return None

    def git(*args: str) -> str | None:
        ran = subprocess.run(["git", "-C", str(worktree), *args], capture_output=True, text=True, check=False)
        return ran.stdout if ran.returncode == 0 else None

    base = git("merge-base", "HEAD", onto)
    added = git("diff", "--name-only", "--diff-filter=A", "--no-renames", "-z", base.strip(), "HEAD", "--", folder) if base else None
    if added is None:
        return None
    items = []
    # the items of the folder itself, as the board's tab "Backlog" reads them: a file in a folder under it is no item
    for path in sorted(name for name in added.split("\0") if name.endswith(".md") and name.rpartition("/")[0] == folder):
        text = git("show", f"HEAD:{path}") or ""
        items.append({"path": path, "title": parse_item(text)[1] or Path(path).stem})
    return items


def reviewer_folder(settings: dict) -> Path:
    """The folder of the reviewer's items: `.lem/state/backlog/` of the main checkout, which git never sees."""
    return Path(settings["main"]) / lem_state.STATE / lem_project.STATE_BACKLOG


def backlog(settings: dict) -> dict:
    """The items of the backlog folder, and beside them the reviewer's items of the state folder
    (`reviewer_folder`), as the board's tab "Backlog" shows them. Each item has its file's stem
    (`slug`), its path from the root of the main checkout, which "Start a task" posts, and its `key`,
    which names it on the page: the stem for an item of the backlog folder, `-STEM` for a reviewer's
    item, so that the two items of one stem stay two. A reviewer's item (`reviewer`) is `held` by the
    task that builds it, `{"task", "status"}` by project.py's holder rule, or undecided (None). It
    reads and changes nothing."""
    main = Path(settings["main"])
    # the main checkout's copy: a task's worktree has the backlog as its branch left it
    folder = main / Path(settings["places"]["backlog"]["path"]).relative_to(settings["root"])
    relative = folder.relative_to(main).as_posix()
    mine = reviewer_folder(settings)
    feed: dict = {"folder": relative, "reviewer_folder": mine.relative_to(main).as_posix(),
                  "read": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "items": []}

    def git(*args: str) -> str:
        ran = subprocess.run(["git", "-C", str(main), *args], capture_output=True, text=True, check=False)
        return ran.stdout if ran.returncode == 0 else ""

    # what git does not have committed yet: an item the closing pass filed a minute ago is `new`
    changed = {}
    if folder.is_dir():
        # --untracked-files=all: a folder git does not know yet is listed file by file, not as one line
        for entry in git("status", "--porcelain", "--untracked-files=all", "-z", "--", relative).split("\0"):
            if len(entry) > 3:
                code = entry[:2]
                changed[entry[3:]] = "new" if code == "??" or "A" in code else "edited"
    state = main / lem_state.STATE
    for place, reviewer in ((folder, False), (mine, True)):
        rel_place = place.relative_to(main).as_posix()
        for file in sorted(place.glob("*.md")) if place.is_dir() else ():
            rel = f"{rel_place}/{file.name}"
            if reviewer and lem_project.backlog_item_of(state, rel) is None:
                # a file named `.md` alone: no item by the rule the drop and the landing read
                continue
            whose = {"slug": file.stem, "key": f"-{file.stem}" if reviewer else file.stem, "path": rel, "reviewer": reviewer,
                     **({"held": lem_project.item_holder(state, rel)} if reviewer else {})}
            try:
                text = file.read_text(encoding="utf-8", errors="replace")
            except OSError as error:
                # A link to a file that moved, or a folder with an item's name: shown, not hidden, and
                # the other items are still read.
                feed["items"].append({
                    **whose, "title": file.stem, "worth": "unset", "where": "", "where_problem": "", "added": "",
                    "state": "unreadable", "body": f"This item cannot be read: {error.strerror or error}.",
                })
                continue
            fields, title, body = parse_item(text)
            where = fields.get("where", "")
            feed["items"].append({
                **whose, "title": title or file.stem,
                "worth": fields.get("worth") if fields.get("worth") in ("yes", "later", "no") else "unset",
                "where": where, "where_problem": where_problem(main, where) if where else "",
                "added": fields.get("added", ""), "state": "" if reviewer else changed.get(rel, ""),
                "body": body.strip(),
            })
    return feed


def meta_of(settings: dict, state: Path, demo: bool = False) -> dict:
    """The repository's facts the board shows beside its tasks: its name, the base branch, how many
    commands one run of the checks has (`gates`, so that a run is known complete) and how many of
    them are `checks.serial` (`serial`, which do not run after a red command), and whether the state
    folder holds example tasks (`demo`). With `demo`, the folder is marked so for good: a board of
    made-up tasks must say so itself, since a line under "Waits for you" reads as a call to act, and
    the mark is a file beside the events because it is a fact about the data and not about one open."""
    marker = state / "demo"
    if demo:
        marker.write_text("The tasks in this folder are examples, written by a fixture. board.py --demo made this file.\n")
    return {
        # the main checkout names the repository; a worktree's folder is named after its task
        "repo": Path(settings["main"]).name, "base": settings["branch"]["base"],
        "gates": len(settings["checks"]["commands"]) + len(settings["checks"]["serial"]),
        "serial": len(settings["checks"]["serial"]),
        "demo": marker.is_file(),
    }


def state_of(repo: str, slug: str | None, demo: bool) -> tuple[Path, dict]:
    """The repository's state folder and settings, with the task checked when one is asked for, and
    the folder marked as example tasks with `demo`."""
    state = Path(project(repo, "state-dir"))
    settings = json.loads(project(repo, "show"))
    if slug is not None:
        if not SLUG.fullmatch(slug):
            raise BoardError(f"slug {slug!r} must be lower-case words joined by hyphens")
        if not (state / "tasks" / slug).is_dir():
            known = ", ".join(task["slug"] for task in json.loads(project(repo, "tasks"))) or "none yet"
            raise BoardError(f"no task {slug!r}; the tasks are: {known}")
    meta_of(settings, state, demo)
    return state, settings


def register(state: Path) -> None:
    """Put the repository of the state folder into the machine's list of workspaces, unless the folder
    holds example tasks: the server shows only a workspace of the list."""
    if (state / "demo").is_file():
        return
    main = state
    for _ in lem_state.STATE.parts:
        main = main.parent
    try:
        lem_state.register(main)
    except (OSError, lem_state.StateError) as error:
        raise BoardError(f"{main} is not in the list of workspaces `lem serve` shows, so it has no board: {error}") from error


# How long a run that opens the board waits for `lem serve --ensure`: its longest path, a wait for
# another start, the stop of an old server and the start of a new one (serve.py's START_WAIT and
# STOP_WAIT), with a margin.
SERVE_WAIT = 35


# How long one question to the server (its workspaces) may take. A guess: it answers from memory and
# counts each workspace's tasks at most once in a few seconds.
ASK_WAIT = 10


def ensure_server() -> dict:
    """Make sure the board server runs, with `lem serve --ensure`, and return what it printed: the
    server's address in `url`. A server that does not run is a BoardError that says why."""
    try:
        ran = subprocess.run([sys.executable, "-B", str(SCRIPTS / "serve.py"), "--ensure"], capture_output=True, text=True, check=False, timeout=SERVE_WAIT)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise BoardError(f"`lem serve --ensure` did not finish ({error}), and the board is the server's page: run `lem serve --ensure` to see why") from error
    if ran.returncode != 0:
        raise BoardError(f"the board server does not run: {(ran.stderr or ran.stdout).strip().removeprefix('serve.py: ')}")
    try:
        found = json.loads(ran.stdout)
    except ValueError as error:
        raise BoardError(f"`lem serve --ensure` printed no JSON ({error}): {ran.stdout.strip()[:200]}") from error
    if not found.get("running") or not found.get("url"):
        raise BoardError(f"the board server does not run: {found.get('said') or 'lem serve --ensure started none'}; `lem serve --ensure` starts it")
    return found


def address(server: str, main: Path, slug: str | None) -> str:
    """The address of the repository's board, or of one task, as the server names it: its list of
    workspaces has the repository's main checkout with the board's path."""
    try:
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(f"{server.rstrip('/')}/api/workspaces", timeout=ASK_WAIT) as reply:
            spaces = json.loads(reply.read())
    except (urllib.error.URLError, OSError, ValueError) as error:
        raise BoardError(f"the board server at {server} did not list its workspaces ({error}): `lem serve --ensure` says whether it runs") from error
    found = next((space for space in spaces if isinstance(space, dict) and os.path.realpath(space.get("path", "")) == os.path.realpath(main)), None)
    if found is None:
        raise BoardError(f"the board server at {server} does not show {main}: `lem serve --list` names what it shows, and `lem serve --add {main}` adds it")
    url = server.rstrip("/") + found["url"]
    return url + (f"tasks/{quote(slug)}" if slug else "")


def ctl(socket: str, *args: str) -> str:
    # agtermctl never reads the socket from the environment, and a bare call may reach another
    # agterm than the one that hosts this session.
    ran = subprocess.run(["agtermctl", *args, "--socket", socket], capture_output=True, text=True, check=False)
    if ran.returncode != 0:
        raise BoardError(f"agtermctl {' '.join(args[:3])} failed: {(ran.stderr or ran.stdout).strip()}")
    return ran.stdout


def show(opens: list[str], shows, name: str, session: str, socket: str, window: str, follow: bool, again) -> dict:
    """Open a page as a companion of the session's group (`opens`: the flags of `session overlay open`
    that name the page), or keep the one that is there: `shows(overlay)` says whether a page companion
    is it, and `again(overlay)` whether it opens anew rather than reloads where it stands."""
    in_window = ["--window", window] if window else []
    tree = json.loads(ctl(socket, "tree", "--json", *in_window))["result"]["tree"]
    live = [s for workspace in tree.get("workspaces", []) for s in workspace.get("sessions", [])]
    owner = next((s for s in live if s["id"].upper() == session.upper()), None)
    if owner is None:
        raise BoardError(f"this session ({session}) is not in the window agterm answered for")
    # A companion's companion becomes its sibling, so the parent is the top of the group.
    parent = (owner.get("parent") or owner["id"]).upper()

    def overlay(node: dict) -> dict | None:
        return next((page for page in node.get("htmlOverlays") or [] if shows(page)), None)

    # A page is known by what it shows, under this session's own group. Its name is not enough: two
    # Lems of two repositories may be companions of one top session, and each has a board.
    named = [s for s in live if s.get("content") == "page" and (s.get("parent") or "").upper() == parent and overlay(s)]
    kept = named[0] if named and not again(overlay(named[0])) else None
    stale = [s for s in named if s is not kept]
    if stale:
        ctl(socket, "session", "close", *[arg for s in stale for arg in ("--target", s["id"])])
    if kept:
        target = kept["id"]
        ctl(socket, "session", "overlay", "reload", "--current", "--target", target)
        if kept.get("name") != name:
            ctl(socket, "session", "rename", name, "--target", target)
    else:
        opened = ctl(socket, "session", "overlay", "open", *opens, "--js", "--companion", "--target", parent, "--json")
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

    def shows(overlay: dict) -> bool:
        file = overlay.get("file") or ""
        return bool(file) and os.path.realpath(file) == os.path.realpath(page)

    return {"page": str(page), "name": name, **show(["--html", str(page), "--cwd", str(page.parent)], shows, name, session, socket,
                                                    env("AGT_WINDOW_ID", "AGTERM_WINDOW_ID"), args.follow, lambda overlay: False)}


def open_board(url: str, base: str, task: bool, name: str, session: str, socket: str, follow: bool) -> dict:
    """The board as a page companion of the session's group, known by the address of its workspace
    (`base`): the one that shows it is reloaded where it stands, or, for a task's board when it shows
    another page, opened again at the task's address."""
    def shows(overlay: dict) -> bool:
        return any(str(overlay.get(key) or "").startswith(base) for key in ("url", "page"))

    def again(overlay: dict) -> bool:
        return task and str(overlay.get("page") or overlay.get("url") or "").split("?")[0].rstrip("/") != url.rstrip("/")

    return show(["--url", url, "--persistent"], shows, name, session, socket, env("AGT_WINDOW_ID", "AGTERM_WINDOW_ID"), follow, again)


def main() -> None:
    parser = argparse.ArgumentParser(prog="lem board", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=env("AGT_SESSION_PWD") or ".", help="a directory inside the checkout (default: the current one)")
    parser.add_argument("--task", metavar="SLUG", help="open the board of this task instead of the board of all tasks")
    parser.add_argument("--follow", action="store_true", help="switch to the board after it opens")
    parser.add_argument("--no-open", action="store_true", help="make sure the server runs and print the board's address; open nothing")
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
            raise BoardError("not inside an agterm session; --no-open prints the board's address without one")
        state, settings = state_of(args.repo, args.task, args.demo)
        register(state)
        server = ensure_server()
        main_dir = Path(settings["main"])
        url = address(server["url"], main_dir, args.task)
        base = address(server["url"], main_dir, None)
        # the repository's name is in the board's name, so two boards in one sidebar read apart
        result: dict = {"url": url, "name": f"Lem board · {main_dir.name}"}
        if server.get("tailscale"):
            # the same board through the tailnet door, for the owner's phone
            result["tailnet_url"] = server["tailscale"].rstrip("/") + url.removeprefix(server["url"].rstrip("/"))
        if not args.no_open:
            result |= open_board(url, base, args.task is not None, result["name"], session, socket, args.follow)
    except BoardError as error:
        sys.exit(f"board.py: {error}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
