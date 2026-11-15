#!/usr/bin/env python3
"""The queue of landed changes that wait for a review.

Lem lands a change when the gate is green and reviews it afterwards. This queue is
what keeps "afterwards" from meaning "never": every landing adds an item, a high-risk item is due
the day it lands, and an item nobody read within EXPIRE_AFTER is closed as "not reviewed" so the
count of unread changes is a number someone sees instead of a backlog that only grows.

    review_queue.py add SLUG --range BASE..TIP --risk high|normal [--note TEXT]
    review_queue.py list                  open items as JSON, high first, then oldest first
    review_queue.py list --all            every item, closed ones too, by id
    review_queue.py close ID --outcome TEXT
    review_queue.py expire                close open normal items older than EXPIRE_AFTER

The queue is one JSON-lines file inside the git directory every worktree shares. Each line is an
event; an item's state is its newest event. Each event also goes to `review-queue.js` beside it,
as a `lemReview({...});` line: the board is a file:// page, which can load a script and cannot
read a file.
"""

from __future__ import annotations

import sys

if sys.version_info < (3, 11):
    # an old python3 must still load this file, so that it can say what it needs and not a traceback
    sys.exit(f"review_queue.py: Lem needs Python 3.11 or newer, and this python3 is {sys.version.split()[0]}; put a newer one first on PATH, or run this file with it")

import argparse
import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

RISKS = ("high", "normal")
# How long a normal item may wait. A guess, not a measurement: long enough for a quiet week to
# drain, short enough that an unread landing is reported while someone still remembers it.
EXPIRE_AFTER = timedelta(days=7)


def queue_file(repo: Path) -> Path:
    found = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--show-toplevel", "--git-common-dir"],
        capture_output=True, text=True, check=False,
    )
    if found.returncode != 0:
        sys.exit(f"review_queue.py: {repo} is not inside a git checkout")
    top, common = found.stdout.strip().splitlines()
    directory = (Path(top) / common).resolve() / "lem"
    directory.mkdir(exist_ok=True)
    return directory / "review-queue.jsonl"


def items(file: Path) -> dict[int, dict]:
    state: dict[int, dict] = {}
    if file.is_file():
        for line in file.read_text().splitlines():
            event = json.loads(line)
            state.setdefault(event["id"], {}).update(event)
    return state


def append(file: Path, event: dict) -> None:
    line = json.dumps(event, ensure_ascii=False)
    with file.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    with file.with_suffix(".js").open("a", encoding="utf-8") as feed:
        feed.write(f"lemReview({line});\n")


def now() -> datetime:
    return datetime.now(timezone.utc)


def cmd_add(file: Path, slug: str, landed: str, risk: str, note: str | None) -> None:
    item_id = max(items(file), default=0) + 1
    append(file, {"id": item_id, "slug": slug, "range": landed, "risk": risk, "note": note,
                  "added": now().isoformat(timespec="seconds"), "outcome": None})
    print(item_id)


def open_items(file: Path) -> list[dict]:
    pending = [item for item in items(file).values() if item["outcome"] is None]
    return sorted(pending, key=lambda item: (RISKS.index(item["risk"]), item["added"]))


def cmd_list(file: Path, everything: bool) -> None:
    if everything:
        # what a landing that was cut off asks: was this range queued before, whatever became of it
        print(json.dumps([item for _id, item in sorted(items(file).items())], indent=2))
        return
    today = now().date().isoformat()
    listed = []
    for item in open_items(file):
        age = now() - datetime.fromisoformat(item["added"])
        due = "today" if item["risk"] == "high" and item["added"][:10] == today else (
            "overdue" if item["risk"] == "high" else "when the day allows")
        listed.append({**item, "age_hours": round(age.total_seconds() / 3600, 1), "due": due})
    print(json.dumps(listed, indent=2))


def cmd_close(file: Path, item_id: int, outcome: str) -> None:
    item = items(file).get(item_id)
    if item is None:
        sys.exit(f"review_queue.py: no item {item_id}")
    if item["outcome"] is not None:
        sys.exit(f"review_queue.py: item {item_id} is already closed: {item['outcome']}")
    append(file, {"id": item_id, "outcome": outcome, "closed": now().isoformat(timespec="seconds")})


def cmd_expire(file: Path) -> None:
    expired = [item for item in open_items(file)
               if item["risk"] == "normal" and now() - datetime.fromisoformat(item["added"]) > EXPIRE_AFTER]
    for item in expired:
        append(file, {"id": item["id"], "outcome": "not reviewed", "closed": now().isoformat(timespec="seconds")})
    print(json.dumps({"expired": [item["id"] for item in expired]}))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=".", help="a directory inside the checkout (default: the current one)")
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("add")
    add.add_argument("slug")
    add.add_argument("--range", required=True, dest="landed", help="the landed commits, BASE..TIP")
    add.add_argument("--risk", required=True, choices=RISKS)
    add.add_argument("--note")
    commands.add_parser("list").add_argument("--all", action="store_true", dest="everything", help="closed items too")
    close = commands.add_parser("close")
    close.add_argument("id", type=int)
    close.add_argument("--outcome", required=True)
    commands.add_parser("expire")
    args = parser.parse_args()
    file = queue_file(Path(args.repo))
    if args.command == "add":
        cmd_add(file, args.slug, args.landed, args.risk, args.note)
    elif args.command == "list":
        cmd_list(file, args.everything)
    elif args.command == "close":
        cmd_close(file, args.id, args.outcome)
    else:
        cmd_expire(file)


if __name__ == "__main__":
    main()
