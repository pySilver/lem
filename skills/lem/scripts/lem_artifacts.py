"""The files of a task, as the board's artifacts explorer reads them, in one map for
every project.

`files` lists a task's files with no text: an entry for each file of the task directory
and for the task's plan, with the file's path, its section, a title a person reads, its
role, its kind, its size and its time. `one` gives one of them with its text, only by a
path the list holds, so that a request reads nothing outside the task's files. An HTML
page carries no text but `href`, its path in the task directory, since the board shows
it in a frame from the server's raw route; a picture carries neither, and the board
shows it from the media route, after `image_type` says it is one.

`arrange` puts the entries on the map: the seven sections, always all of them, in the
order a task runs and with the same names (SECTIONS), then the working files. A file is
one of three roles:

- a document, which a person reads: a row of its section;
- a record, the machine's JSON that a tab of the board already shows readable: a small
  link in the row of the document it belongs to (`criteria.json` beside "Acceptance
  criteria", `decisions.jsonl` beside "Decisions"), with the tab that shows it (`tab`);
  a record whose document is not there is a working file;
- a working file: an agent's scratch, the review tool's archive of a round, a record
  with no document, a picture no document shows, and every file this map does not know.
  They are one folded group at the end, by their folder, so nothing is unreachable and
  nothing new makes a section of its own.

A review round of the review tool is one document of "Review", its own `report.md`, and
the rest of its archive is a folder of "Working files". A picture of `media/` belongs to
the document whose text names it (`shows`).

`outside_record` gives what a task loses once it ended long ago (`lem project prune`):
every path of its folder but its small record (SMALL_RECORD), the few files that a
reader of Lem still reads of an ended task, and the lock files at the top of the folder.
Its documents, its records and its pictures go with the rest: the owner's word
(2026-11-21, confirmed on 2026-11-23) is that the machine keeps no whole history of
a task.

The plan is no file of the task directory: it lives in the task's worktree, on its
branch. The caller finds it (`project.py`'s `task_plan`) and passes it in, so this file
imports nothing of Lem's but the one form of a time (`lem_clock`). A task with no
worktree or no plan has no plan entry.
"""

import contextlib
import os
import re
from pathlib import Path

import lem_clock

# A file over this many bytes is listed with no text: the page draws each file it shows,
# and a review tool's log can be megabytes. A guess, not a measurement.
CAP = 300_000
# The sections of every task's map, in their order, and the group of the working files
# after them.
SECTIONS = (
    ("request", "Request"),
    ("criteria", "Criteria"),
    ("plan", "Plan"),
    ("build", "Build"),
    ("checks", "Checks"),
    ("review", "Review"),
    ("pr", "Pull request"),
)
WORK = "work"
GROUPS = (*(key for key, _ in SECTIONS), WORK)

# The documents of a task directory, by their name: their section and their title.
DOCS = {
    "ask.txt": ("request", "The request"),
    "ticket.txt": ("request", "The ticket"),
    "task.md": ("request", "The task"),
    "brief.md": ("request", "The brief"),
    "talk.md": ("request", "The talk that led to the request"),
    "interview-notes.md": ("request", "Interview notes"),
    "session.md": ("request", "The task session's first read"),
    "outside.md": ("request", "Outside the change"),
    "criteria.md": ("criteria", "Acceptance criteria"),
    "criteria-read.md": ("criteria", "The personas' read of the criteria"),
    "criteria-page.html": ("criteria", "The criteria page"),
    # the changed criteria the task's session writes from the owner's note, which
    # `lem criteria change --file` takes
    "criteria-change.md": (
        "criteria",
        "The changed criteria, as the session wrote them for the change",
    ),
    "design.md": ("plan", "Design"),
    "directions.md": ("plan", "The owner's directions"),
    "scout.md": ("plan", "The scout's report"),
    "investigation.md": ("plan", "Investigation"),
    "handoff.md": ("plan", "Handoff"),
    "talk-list.md": ("plan", "The plan talk's list"),
    "report.md": ("build", "Report"),
    "breaker.md": ("build", "What stopped the build"),
    "setup.log": ("checks", "Worktree setup output"),
    "pr.md": ("pr", "Pull request text"),
    "notes.md": ("pr", "Notes for the pull request"),
    "merge-review.md": ("pr", "The merge review"),
    "handover.html": ("pr", "The hand-over page"),
}
# The records, by their name: the document they belong to, the word of their link, and
# the tab of the board that shows them readable.
RECORDS = {
    "criteria.json": ("criteria.md", "record", "criteria"),
    # the text the owner answered, which `lem criteria change` keeps before
    # criteria.md moves
    "criteria-before.json": ("criteria.md", "text before the change", "criteria"),
    "decisions.jsonl": ("pr.md", "decisions", "criteria"),
    "polish.json": ("report.md", "polish pass", "checks"),
    "landing.json": ("pr.md", "landing", "checks"),
    "read.json": ("pr.md", "review's read", "checks"),
    # the task's state, newest block first, which `lem project tasks`, the nap and a
    # session read
    "state.md": ("ask.txt", "state", "timeline"),
    # what Lem did to the task's ticket, which `lem project tasks` reads to say what is
    # still owed
    "ticket-steps.txt": ("ticket.txt", "ticket steps", None),
    # the repository of a GitHub issue, which each write of `lem issue` compares
    # with origin's
    "ticket-repo.txt": ("ticket.txt", "ticket repository", None),
    # the task a resumed one came from, which a resume and a plan's name follow back
    "resumed-from.txt": ("ask.txt", "resumed from", None),
    # the release the task began on, which each command of Lem for the task reads
    # first (lem_release)
    "release.txt": ("ask.txt", "release", None),
}
# The small record of a task: what stays of its folder once it ended long ago
# (`outside_record`), each file for the readers that need it after the end.
SMALL_RECORD = (
    # its status, which `lem project tasks`, `may-start`, a task queued behind it and
    # `task-dir` read, and which a second prune reads to find it ended
    "state.md",
    # its ask, and the first line of task.md for a task with no ask.txt: `tasks`, and
    # the line of `/lem` that a refused resume ends with
    "ask.txt",
    "task.md",
    # its pull request, which `lem project tasks` shows (`proposal`)
    "landing.json",
    # its ticket, the issue's repository and what Lem did to it: the steps it still owes
    # (`ticket_owed`) and the task that holds the ticket now (`ticket_held_by`)
    "ticket.txt",
    "ticket-repo.txt",
    "ticket-steps.txt",
    # the task a resumed one came from, which a resume's new name and the ticket's
    # holder follow back
    "resumed-from.txt",
)
# The tabs, by their key, as a record's line names them.
TAB_NAMES = {
    "criteria": "Criteria and decisions",
    "checks": "Checks and review",
    "timeline": "Timeline",
}
# The pictures a document may show, and their types; an SVG is no picture here, since it
# can carry a script.
IMAGES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
}
# A path in a document's text that names a picture of the task's media folder.
MEDIA_REF = re.compile(
    r"(?:^|[(\s\"'/])(media/[A-Za-z0-9._/-]+\.(?:png|jpe?g|gif|webp))\b", re.IGNORECASE
)


KINDS = {
    ".md": "markdown",
    ".markdown": "markdown",
    ".txt": "text",
    ".py": "text",
    ".js": "text",
    ".css": "text",
    ".toml": "text",
    ".yaml": "text",
    ".yml": "text",
    ".sh": "text",
    ".diff": "text",
    ".patch": "text",
    ".csv": "text",
    ".svg": "text",
    ".json": "json",
    ".jsonl": "jsonl",
    ".log": "log",
    ".out": "log",
    ".err": "log",
    ".html": "html",
    ".htm": "html",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".gif": "image",
    ".webp": "image",
    ".ico": "binary",
    ".pdf": "binary",
    ".zip": "binary",
    ".gz": "binary",
    ".tar": "binary",
    ".sqlite": "binary",
    ".db": "binary",
}


def image_type(name: str, head: bytes) -> str | None:
    """The type of a picture the board shows: by its extension AND its first bytes,
    which must be the same format; None for anything else (an SVG, a text with a
    picture's name)."""
    want = IMAGES.get(Path(name).suffix.lower())
    if want is None:
        return None
    found = (
        "image/png"
        if head.startswith(b"\x89PNG\r\n\x1a\n")
        else "image/jpeg"
        if head.startswith(b"\xff\xd8\xff")
        else "image/gif"
        if head[:6] in (b"GIF87a", b"GIF89a")
        else "image/webp"
        if head[:4] == b"RIFF" and head[8:12] == b"WEBP"
        else None
    )
    return found if found == want else None


def place(path: str) -> dict:  # noqa: C901, PLR0911, PLR0912 - over the limit before the limit was set
    """Where a file of the task directory goes on the map, from its path relative to it:
    its section (`group`), its title, its role (`doc`, `record` or `work`), and for a
    record the document it belongs to (`of`), its link's word (`label`) and its tab; for
    a working file its folder (`folder`)."""
    name = path.rpartition("/")[2]
    _, _, suffix = name.rpartition(".")
    suffix = suffix.lower()
    if path in DOCS:
        group, title = DOCS[path]
        return {"group": group, "title": title, "role": "doc"}
    if path in RECORDS:
        of, label, tab = RECORDS[path]
        return {
            "group": DOCS[of][0],
            "title": f"{DOCS[of][1]} ({label})",
            "role": "record",
            "of": of,
            "label": label,
            "tab": tab,
        }
    # the merge agent's brief of one proposed tip on one base (land.py `brief_file`)
    brief = re.fullmatch(r"merge-brief-([0-9a-f]+)-([0-9a-f]+)\.md", path)
    if brief:
        return {
            "group": "pr",
            "title": (
                f"The merge agent's brief of {brief.group(1)[:9]} on "
                f"{brief.group(2)[:9]}"
            ),
            "role": "doc",
        }
    breaker = re.fullmatch(r"breaker-(\d+)\.md", path)
    if breaker:
        return {
            "group": "build",
            "title": f"What stopped the build: breaker {breaker.group(1)}",
            "role": "doc",
        }
    if path.startswith("reports/") and suffix == "md":
        return {
            "group": "build",
            "title": f"Report: {path.removeprefix('reports/').removesuffix('.md')}",
            "role": "doc",
        }
    if path.startswith("gate/"):
        number = re.fullmatch(r"0*(\d+)\.log", path.removeprefix("gate/"))
        return {
            "group": "checks",
            "title": f"Check {number.group(1)} output"
            if number
            else f"Check output: {path.removeprefix('gate/')}",
            "role": "doc",
        }
    if re.fullmatch(r"red(-.+)?\.json", path):
        return {
            "group": "criteria",
            "title": "Criteria fail on the base (record)",
            "role": "record",
            "of": "criteria.md",
            "label": "red on the base",
            "tab": "criteria",
        }
    review = re.fullmatch(r"reviews/review-0*(\d+)\.(md|json)", path)
    if review:
        if review.group(2) == "md":
            return {
                "group": "review",
                "title": f"Review {review.group(1)}",
                "role": "doc",
            }
        return {
            "group": "review",
            "title": f"Review {review.group(1)} (record)",
            "role": "record",
            "of": path[:-5] + ".md",
            "label": "record",
            "tab": "checks",
        }
    # the review tool's archive of one round: reviews/TASK/NN-LABEL/..., and its run's
    # own files beside them
    archive = re.fullmatch(r"reviews/[^/]+/(\d+-[^/]+)/(.+)", path)
    if archive:
        if archive.group(2) == "report.md":
            return {
                "group": "review",
                "title": f"Review round {archive.group(1)}",
                "role": "doc",
            }
        return {
            "group": WORK,
            "title": archive.group(2),
            "role": "work",
            "folder": f"Review round {archive.group(1)}",
        }
    run = re.fullmatch(r"reviews/[a-z]+-(\d+-[^/]+)\.(json|log)", path)
    if run:
        return {
            "group": WORK,
            "title": name,
            "role": "work",
            "folder": f"Review round {run.group(1)}",
        }
    if "/" not in path and suffix in ("html", "htm"):
        return {"group": "pr", "title": name, "role": "doc"}
    if path.startswith("media/"):
        return {
            "group": WORK,
            "title": path.removeprefix("media/"),
            "role": "work",
            "folder": "Pictures",
        }
    if path.startswith("ladder/"):
        return {
            "group": WORK,
            "title": path.removeprefix("ladder/"),
            "role": "work",
            "folder": "The ladder's notes",
        }
    folder = path.rpartition("/")[0]
    return {
        "group": WORK,
        "title": name if folder else path,
        "role": "work",
        "folder": folder or None,
    }


def arrange(entries: list[dict], shows: dict[str, list[str]] | None = None) -> dict:
    """The map of a task's entries (`files`): `sections`, the seven in their order, each
    with its documents and each document with what belongs to it (`attached`: its
    records, its source, the pictures it shows); and `work`, the working files by their
    folder. A record whose document is not listed, and a picture that no document shows,
    is a working file. `shows` gives the pictures each document's text names, by the
    document's path. `count` is the number of documents."""
    by_path = {e["path"]: e for e in entries}
    shown_by = {}
    for doc, pictures in (shows or {}).items():
        for picture in pictures:
            if picture in by_path and doc in by_path:
                shown_by.setdefault(picture, doc)
    attached: dict[str, list[dict]] = {}
    work: list[dict] = []
    docs = []
    for e in entries:
        role = e.get("role", "doc")
        if role == "record" and e.get("of") in by_path:
            attached.setdefault(e["of"], []).append(e)
        elif e["path"] in shown_by:
            attached.setdefault(shown_by[e["path"]], []).append(
                {**e, "label": e["path"].removeprefix("media/")}
            )
        elif role == "doc":
            docs.append(e)
        else:
            folder = e.get("folder") or (
                "Records with no document" if role == "record" else None
            )
            work.append({**e, "folder": folder})
    sections = [
        {
            "key": key,
            "name": name,
            "docs": [
                {**d, "attached": attached.get(d["path"], [])}
                for d in docs
                if d["group"] == key
            ],
        }
        for key, name in SECTIONS
    ]
    folders: dict = {}
    for e in work:
        folders.setdefault(e["folder"], []).append(e)
    return {
        "sections": sections,
        "work": [
            {"folder": f, "files": files_}
            for f, files_ in sorted(
                folders.items(), key=lambda x: (x[0] is not None, x[0] or "")
            )
        ],
        "count": len(docs),
        "work_count": len(work),
    }


def kind_of(file: Path) -> str:
    """The kind of a file, from its extension; one with an unknown extension is binary
    when its first bytes hold a NUL, and text otherwise."""
    known = KINDS.get(file.suffix.lower())
    if known:
        return known
    try:
        with file.open("rb") as handle:
            return "binary" if b"\0" in handle.read(8192) else "text"
    except OSError:
        return "binary"


def entry(
    file: Path, path: str, where: dict, href: str | None, *, read: bool = True
) -> dict | None:
    """One file's entry; None for an empty file, which shows nothing, and for a link to
    a file that is gone. A file that cannot be read is listed with no text, and the
    others are still read. With `read` false the entry has no text: the board lists the
    files and reads only the one shown."""
    try:
        facts = file.stat()
    except OSError:
        return None
    if facts.st_size == 0:
        return None
    kind = kind_of(file)
    found: dict = {
        "path": path,
        **where,
        "kind": kind,
        "bytes": facts.st_size,
        "mtime": lem_clock.stamp(facts.st_mtime),
        "text": None,
    }
    if facts.st_size > CAP and kind not in ("html", "binary", "image"):
        found["cut"] = True
    if kind == "html":
        found["href"] = href
    elif kind not in ("binary", "image") and read:
        if facts.st_size > CAP:
            found["cut"] = True
        else:
            with contextlib.suppress(OSError):
                found["text"] = file.read_bytes().decode("utf-8", errors="replace")
    return found


def files(
    directory: Path,
    slug: str,
    plan: tuple[Path, str] | None = None,
    *,
    read: bool = True,
) -> list[dict]:
    """The entries of a task's files: each file of its directory but a lock, an empty
    file and a hidden one, and its plan when `plan` gives the file and its path from the
    repository root; with `read` false, with no text (`entry`)."""
    found = []
    for at, folders, names in os.walk(directory):
        folders[:] = sorted(name for name in folders if not name.startswith("."))
        for name in sorted(names):
            if name.startswith(".") or name.endswith(".lock"):
                continue
            file = Path(at) / name
            path = file.relative_to(directory).as_posix()
            made = entry(file, path, place(path), path, read=read)
            if made:
                found.append(made)
    if plan is not None:
        made = entry(
            plan[0],
            plan[1],
            {"group": "plan", "title": "The plan", "role": "doc", "first": True},
            None,
            read=read,
        )
        if made:
            found.append(made)
    return sorted(
        found,
        key=lambda item: (
            GROUPS.index(item["group"]),
            not item.get("first"),
            item["path"],
        ),
    )


def one(
    directory: Path, slug: str, path: str, plan: tuple[Path, str] | None = None
) -> tuple[dict, Path] | None:
    """The entry of one file of a task, with its text, and the file itself: `path` as
    `files` names it (from the task directory, or the plan's path from the repository
    root); None for a path that is no entry of the task's, so that nothing outside its
    files is ever read by a name a request gives."""
    listed = {item["path"]: item for item in files(directory, slug, plan, read=False)}
    if path not in listed:
        return None
    if plan is not None and path == plan[1]:
        file = plan[0]
    else:
        file = directory / path
        try:
            if not file.resolve().is_relative_to(directory.resolve()):
                return None
        except OSError:
            return None
    where = {
        key: value
        for key, value in listed[path].items()
        if key not in ("path", "kind", "bytes", "mtime", "text", "cut", "href")
    }
    found = entry(file, path, where, listed[path].get("href"))
    return (found, file) if found else None


def pictures_named(directory: Path, entries: list[dict]) -> dict[str, list[str]]:
    """The pictures of `media/` each markdown document of the task names, by the
    document's path: read only when the task has a picture, and only the documents of
    the task directory."""
    if not any(e["path"].startswith("media/") for e in entries):
        return {}
    named = {}
    for e in entries:
        if (
            e["kind"] != "markdown"
            or e.get("role") != "doc"
            or e.get("cut")
            or e["path"].startswith("/")
            or e.get("first")
        ):
            continue
        try:
            text = (directory / e["path"]).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        found = sorted({m.group(1) for m in MEDIA_REF.finditer(text)})
        if found:
            named[e["path"]] = found
    return named


def outside_record(directory: Path) -> list[str]:
    """The paths of a task's folder that are not its small record, from the folder,
    sorted: each path at any depth that is no folder, but the files of SMALL_RECORD and
    the lock files at the top of the folder. A lock file stays, since one removed while
    another process holds it lets a second writer lock a new file of the same name. No
    link is followed: a link, to a file or to a folder, is a path of its own, and so is
    a file that is not plain and a folder that does not list, so that the one who
    removes them names each one it cannot remove. None of them is opened."""
    found = []

    def unlisted(error: OSError) -> None:
        if error.filename and Path(error.filename) != directory:
            found.append(Path(error.filename).relative_to(directory).as_posix())

    for at, folders, names in os.walk(directory, onerror=unlisted):
        top = Path(at) == directory
        found.extend(
            (Path(at) / name).relative_to(directory).as_posix()
            for name in folders
            if (Path(at) / name).is_symlink()
        )
        for name in names:
            if top and (name in SMALL_RECORD or name.endswith(".lock")):
                continue
            found.append((Path(at) / name).relative_to(directory).as_posix())
    return sorted(found)
