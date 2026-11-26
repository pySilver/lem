"""Count calls to the real gh merge and hold or lose its reply for R5."""

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

REPO = "pySilver/lem-scratch"
BRANCH = re.compile(r"trial-[a-z0-9][a-z0-9-]*")
MODES = ("normal", "before", "after", "lost")
CASE = "TRIAL_MERGE_CASE"
MODE = "TRIAL_MERGE_MODE"


def merge_target(words: list[str], number: str) -> str:
    """Refuse a merge unless its PR and repository match the case and it pins a head."""
    if words[:3] != ["pr", "merge", number] or words[-2:] != ["--repo", REPO]:
        raise ValueError("only the named PR of pySilver/lem-scratch can merge")
    tip = words[words.index("--match-head-commit") + 1]
    if (
        not re.fullmatch(r"[0-9a-f]{40}", tip)
        or "--delete-branch" in words
        or "--auto" in words
        or "--admin" in words
    ):
        raise ValueError("use a pinned direct merge without branch deletion")
    return tip


def checked(request: dict[str, str], tip: str) -> None:
    head, base = request["headRefName"], request["baseRefName"]
    if not BRANCH.fullmatch(head) or not BRANCH.fullmatch(base) or head == base:
        raise ValueError("the pull request must join two different trial-* branches")
    if request["state"] != "OPEN" or request["headRefOid"] != tip:
        raise ValueError("the pull request must still be open at the pinned head")


def note(case: Path, event: str, **fields: object) -> None:
    with (case / "calls.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(
            json.dumps({"event": event, "at": datetime.now(UTC).isoformat(), **fields})
            + "\n"
        )
        stream.flush()
        os.fsync(stream.fileno())


def count(case: Path) -> dict[str, object]:
    log = case / "calls.jsonl"
    events = (
        [json.loads(line) for line in log.read_bytes().splitlines()]
        if log.exists()
        else []
    )
    return {
        "ok": True,
        "sent": sum(row["event"] == "sending" for row in events),
        "events": events,
    }


def hold(case: Path, phase: str) -> None:
    """Do not continue to the next effect even if the trial operator misses the barrier."""
    note(case, phase, pid=os.getpid())
    deadline = time.monotonic() + 110
    while time.monotonic() < deadline:
        time.sleep(0.1)
    raise ValueError(f"R5 {phase} barrier timed out")


def invoke(real: Path, case: Path, mode: str, words: list[str]) -> int:
    number = (case / "pr").read_text(encoding="ascii").strip()
    if mode not in MODES or not number.isdecimal():
        raise ValueError("use an R5 mode and a case with a numeric PR")
    if words[:2] != ["pr", "merge"]:
        # The adapter reads via GraphQL immediately after `pr merge`. Lose that read as well
        # so the original call cannot settle the intent before the reconcile under trial.
        if (
            mode == "lost"
            and words[:2] == ["api", "graphql"]
            and (case / "lost").is_file()
        ):
            note(case, "read-reply-lost")
            print("trial: connection lost after the merge", file=sys.stderr)
            return 1
        os.execv(real, [str(real), *words])
    tip = merge_target(words, number)
    viewed = subprocess.run(
        [
            real,
            "pr",
            "view",
            number,
            "--repo",
            REPO,
            "--json",
            "headRefName,baseRefName,headRefOid,state",
        ],
        capture_output=True,
        check=True,
    )
    checked(json.loads(viewed.stdout), tip)
    if mode == "before":
        hold(case, "before-send")
    stdin = sys.stdin.buffer.read()
    note(case, "sending", pr=number, tip=tip)
    sent = subprocess.run([real, *words], input=stdin, capture_output=True, check=False)
    note(case, "reply", exit=sent.returncode)
    if sent.returncode == 0:
        if mode == "after":
            hold(case, "after-reply")
        if mode == "lost":
            (case / "lost").touch(exist_ok=False)
            note(case, "merge-reply-lost")
            print("trial: merge reply lost", file=sys.stderr)
            return 1
    sys.stdout.buffer.write(sent.stdout)
    sys.stderr.buffer.write(sent.stderr)
    return sent.returncode


def install(folder: Path, real: Path) -> None:
    if (
        not real.is_absolute()
        or not real.is_file()
        or real.resolve().is_relative_to(folder)
    ):
        raise ValueError("give the absolute path of real gh outside the trial folder")
    words = shlex.join(
        [
            sys.executable,
            "-I",
            "-B",
            str(folder / "merge_calls.py"),
            str(folder),
            "gh",
            str(real),
        ]
    )
    target = folder / "bin" / "gh"
    with target.open("x", encoding="utf-8") as stream:
        stream.write(f'#!/bin/sh\nexec {words} "$@"\n')
    target.chmod(0o700)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("action", choices=("install", "count", "gh"))
    parser.add_argument("path", type=Path)
    parser.add_argument("words", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        if args.action == "install":
            install(args.folder, args.path)
            found = {"ok": True, "wrapper": str(args.folder / "bin" / "gh")}
        elif args.action == "count":
            found = count(args.path)
        elif CASE in os.environ:
            case = Path(os.environ[CASE]).resolve()
            if not case.is_dir() or not case.is_relative_to(args.folder / "evidence"):
                raise ValueError("use an R5 case folder below evidence")
            raise SystemExit(
                invoke(args.path, case, os.environ.get(MODE, "normal"), args.words)
            )
        elif args.words[:2] == ["pr", "merge"]:
            raise ValueError("set the R5 case even for a normal merge")
        else:
            os.execv(args.path, [str(args.path), *args.words])
    except (
        OSError,
        ValueError,
        IndexError,
        KeyError,
        subprocess.CalledProcessError,
    ) as error:
        print(json.dumps({"ok": False, "error": str(error)}), file=sys.stderr)
        raise SystemExit(1) from error
    print(json.dumps(found))


if __name__ == "__main__":
    main()
