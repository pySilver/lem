#!/usr/bin/env python3
"""A project's queue of the owner's corrections: the hook that fills it, and what the retro reads.

A correction that the owner gave once and that came back is what `/lem retro` looks for. The
sessions that got the correction do not record it reliably, so a hook records it for them: it
asks a small decision model about each message the owner types, and queues the ones an agent
should learn a lesson from. The retro, a big model, decides about each.

    corrections.py hook                 the hook an agent runs on each message of the owner
    corrections.py list                 unreviewed groups as JSON, most sessions first
    corrections.py show ID              every entry of one group in full
    corrections.py lessons              the lessons earlier retros recorded, with their targets
    corrections.py record ID --decision lesson|not_lesson --verdict VERDICT [--target PATH] [--lesson TEXT]
                                        write down what was decided about a group

It is an optional part, and it is the owner's choice twice. The hook sends the owner's message
and the agent message it answers to the Jev decision model, through `jev.py` beside this file, so
it runs only in a repository whose settings say `corrections.collect = true`: the tracked file, so the
yes is the repository's and everybody sees it. The hook is there where Lem is installed as a
plugin (`hooks/hooks.json` of the clone) or where the owner registered it for the link form
(`scripts/setup.py --corrections on`). One person keeps their own messages out with
`collect = false` under `[corrections]` in `.lem/project.local.toml`. In every other
repository the hook exits at once.

The hook does not wait for Jev: it hands the message to a detached copy of itself and exits 0
with no output. Its own waits are bounded: it gives up the read of the event and each of its git
calls (two in a repository that says yes) after WAIT_SECONDS each. The copy checks the project's yes again, asks Jev, and appends the
message to the queue when Jev's probability of "lesson" is at least FLAG_AT. Jev is a pre-filter, and a loose one on purpose. With this question
at 0.3, on 150 replies their owner had labeled, it caught 22 of 27 lessons and flagged 63 replies
that were none (mybaze, 2026-11-07, tuned on that same sample, so the true rate is lower).

The queue is one file for one project: `corrections.jsonl` in Lem's folder of the git directory,
shared by every worktree and never committed. What a retro decided is in
`corrections-reviews.jsonl` beside it. A failure (no key, a failed request) goes to
`corrections.log` there and never to the conversation, and `list` reports it first: a message
the hook failed on was never judged.

The hook half speaks Claude Code's hook contract: the event on stdin with `prompt`, `cwd`,
`session_id` and `transcript_path`. It asks Jev through Lem's own `jev.py`, by its path: a hook
has no `PATH` to count on. LEM_JEV, when set, names another command with the same contract.

The hook half must start under any `python3` an agent finds, an old one too, and stay silent
there: a Python before 3.11 has no tomllib, so the hook logs that and judges nothing.
"""

# An old python3 must still load this file, so that the hook can fail without a word.
from __future__ import annotations

import argparse
import hashlib
import json
import os
import select
import subprocess
import sys
import tempfile
import time
from pathlib import Path

FLAG_AT = 0.3
# How long the hook waits for the event on its input, and for git, before it gives up without a
# word. A guess (2026-11-15), not a measurement: long for a local git call, short for a person.
WAIT_SECONDS = 2
JEV = Path(__file__).resolve().with_name("jev.py")
DECISIONS = ("lesson", "not_lesson")
# accepted, changed, rejected: the owner's answer to a move the retro put to him. missed: the owner
# said that a "not a lesson" entry was a lesson after all. unasked: nothing was put to the owner.
VERDICTS = ("accepted", "changed", "rejected", "missed", "unasked")
# Text an agent's own machinery puts into a user turn; none of it is the owner's words.
INJECTED = (
    "<", "[peer chat]", "[agterm mailbox", "Caveat:", "This session is being continued", "[Request interrupted",
    "Base directory for this skill", "Stop hook", "[SYSTEM", "Another Claude session",
)
TRANSCRIPT_TAIL_BYTES = 4_000_000
OWNER_TRIM = 500
PREVIOUS_TRIM = 300
QUESTION = {
    "instructions": (
        "This is one exchange between a coding agent and the project's owner: the agent's last message, "
        "then the owner's reply. Decide whether an agent should remember a lesson from the owner's reply "
        "for later work."
    ),
    "choices": {
        "lesson": (
            "An agent should remember something from this reply. The owner corrects it or disagrees with its "
            "approach or assumption; tells it to take a step it should have taken on its own, such as cleaning "
            "up, getting a second opinion, running work in parallel, interviewing the owner, or saying what is "
            "next; asks for more context or a simpler explanation because the agent's message was unclear; "
            "tells it something it was waiting on has already happened; or states a lasting preference or rule "
            "for how the work should be done."
        ),
        "no_lesson": (
            "The reply only moves the work on and teaches nothing for later: it approves or answers the "
            "agent's question as asked, picks one of the options it offered, asks for a retry, or gives a "
            "one-off instruction that is about this moment only."
        ),
    },
}


class QueueError(Exception):
    pass


def git(cwd: str, *args: str) -> str | None:
    try:
        ran = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, check=False, timeout=WAIT_SECONDS)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return ran.stdout.strip() if ran.returncode == 0 and ran.stdout.strip() else None


def folder(cwd: str) -> Path | None:
    """Lem's folder in the git directory every worktree shares; None outside a checkout."""
    common = git(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir")
    return Path(common) / "lem" if common else None


def collects(cwd: str) -> bool:
    """Whether this repository's settings turn the queue on. Anything that cannot be read is a no."""
    import tomllib

    top = git(cwd, "rev-parse", "--show-toplevel")
    file = Path(top) / ".lem" / "project.toml" if top else None
    if file is None or not file.is_file():
        return False
    try:
        if tomllib.loads(file.read_text()).get("corrections", {}).get("collect") is not True:
            return False
    except (tomllib.TOMLDecodeError, OSError):
        return False
    # One person's no, in the file of this machine that git does not track. It is in the main
    # checkout, which a worktree has no copy of. A file there that cannot be read is a no too.
    common = git(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir")
    own = Path(common).parent / ".lem" / "project.local.toml" if common and Path(common).name == ".git" else Path(top) / ".lem" / "project.local.toml"
    if not own.is_file():
        return True
    try:
        return "collect" not in tomllib.loads(own.read_text()).get("corrections", {})
    except (tomllib.TOMLDecodeError, OSError, AttributeError):
        return False


def append(path: Path, record: dict) -> None:
    path.parent.mkdir(exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.is_file() else []


# ---- the hook ----

def last_agent_text(transcript: str) -> str:
    """The newest text an agent wrote in a Claude Code transcript; empty when there is none."""
    path = Path(transcript)
    if not transcript or not path.is_file():
        return ""
    with path.open("rb") as handle:
        handle.seek(max(0, path.stat().st_size - TRANSCRIPT_TAIL_BYTES))
        lines = handle.read().decode("utf-8", errors="replace").splitlines()
    for line in reversed(lines):
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if not isinstance(record, dict) or record.get("type") != "assistant":
            continue
        content = (record.get("message") or {}).get("content")
        if isinstance(content, list):
            text = "\n".join(block.get("text", "") for block in content if isinstance(block, dict) and block.get("type") == "text").strip()
            if text:
                return text
    return ""


def read_event() -> dict:
    """The hook's event from its input. It does not wait for the input to close: it stops at the
    first whole JSON object, or after WAIT_SECONDS."""
    deadline = time.monotonic() + WAIT_SECONDS
    data = b""
    fd = sys.stdin.fileno()
    while time.monotonic() < deadline:
        ready, _, _ = select.select([fd], [], [], max(0.0, deadline - time.monotonic()))
        if not ready:
            break
        chunk = os.read(fd, 1 << 16)
        if not chunk:
            break
        data += chunk
        try:
            value = json.loads(data)
        except ValueError:
            continue
        return value if isinstance(value, dict) else {}
    try:
        value = json.loads(data or b"{}")
    except ValueError:
        return {}
    return value if isinstance(value, dict) else {}


def cmd_hook() -> None:
    """Return at once. Whatever goes wrong here must not reach the owner's prompt."""
    cwd = None
    path = None
    try:
        event = read_event()
        prompt = (event.get("prompt") or "").strip()
        # the event's directory first: the hook's own may be a worktree that is already removed
        cwd = event.get("cwd") or os.getcwd()
        if not prompt or prompt.startswith(INJECTED) or prompt.startswith("/") or not collects(cwd):
            return
        payload = {"prompt": prompt, "cwd": cwd, "session": event.get("session_id"), "transcript": event.get("transcript_path", "")}
        # Through a file only the owner can read, not a pipe: a long message would fill a pipe
        # and hold this hook until the copy reads it.
        handle, path = tempfile.mkstemp(prefix="lem-correction-", suffix=".json")
        with os.fdopen(handle, "w", encoding="utf-8") as file:
            json.dump(payload, file)
        subprocess.Popen(
            [sys.executable, "-B", __file__, "worker", path], stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True,
        )
    except Exception as error:  # noqa: BLE001 - a hook failure is logged where the retro reads it, never shown
        try:
            if path is not None:
                # no copy will read it: the owner's words do not stay in a file nobody removes
                Path(path).unlink(missing_ok=True)
            # the log of the repository the message was typed in, which is the one that lost it
            where = folder(cwd or os.getcwd())
            if where is not None:
                append(where / "corrections.log", {"ts": now(), "error": f"the hook failed before it could judge a message: {error}"})
        except Exception:  # noqa: BLE001
            pass


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def cmd_worker(path: str) -> None:
    file = Path(path)
    payload = json.loads(file.read_text(encoding="utf-8"))
    file.unlink(missing_ok=True)
    where = folder(payload["cwd"])
    # The project's yes is checked here again, at the last moment before anything is sent: the
    # owner may have turned the queue off since the hook looked, and this half can be run alone.
    if where is None or not collects(payload["cwd"]):
        return
    log = where / "corrections.log"
    stamp = now()
    other = os.environ.get("LEM_JEV")
    jev = [other] if other else [sys.executable, "-B", str(JEV)]
    previous = last_agent_text(payload.get("transcript", "")) or "(no agent message before this one)"
    state = f"--- the agent's last message ---\n{previous}\n\n--- the owner's reply ---\n{payload['prompt']}"
    try:
        ran = subprocess.run([*jev, "-"], input=json.dumps({"state": state, "questions": {"lesson": QUESTION}}),
                             capture_output=True, text=True, timeout=180, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        append(log, {"ts": stamp, "session": payload.get("session"), "error": f"jev did not run: {error}"})
        return
    entry = {"ts": stamp, "session": payload.get("session"), "cwd": payload["cwd"], "owner": payload["prompt"], "previous": previous}
    if ran.returncode == 3:
        # too long for Jev to judge well: the retro reads it instead
        append(where / "corrections.jsonl", {**entry, "p_lesson": None, "why": "too long for Jev"})
        return
    try:
        if ran.returncode:
            raise ValueError(ran.stderr.strip()[:500] or f"jev exited {ran.returncode}")
        p_lesson = (json.loads(ran.stdout)["answers"]["lesson"].get("probabilities") or {}).get("lesson", 0)
    except (ValueError, KeyError, TypeError, AttributeError) as error:
        append(log, {"ts": stamp, "session": payload.get("session"), "error": f"jev gave no answer: {error}"})
        return
    if p_lesson >= FLAG_AT:
        append(where / "corrections.jsonl", {**entry, "p_lesson": p_lesson})


# ---- what the retro reads ----

def group_id(owner: str) -> str:
    return hashlib.sha1(" ".join(owner.split()).encode()).hexdigest()[:8]


def unreviewed(where: Path) -> dict[str, list[dict]]:
    """Every entry no retro decided about, grouped by the owner's text: one sentence sent to eight
    sessions is one group of eight, not eight things to judge. An entry is known by its time, its
    session and its words together: two messages of one second in one session are two entries."""
    reviewed = {(review["ts"], review["session"], review.get("group")) for review in read_jsonl(where / "corrections-reviews.jsonl")}
    groups: dict[str, list[dict]] = {}
    for entry in read_jsonl(where / "corrections.jsonl"):
        gid = group_id(entry["owner"])
        if (entry["ts"], entry["session"], gid) not in reviewed:
            groups.setdefault(gid, []).append(entry)
    return groups


def trimmed(text: str, limit: int) -> str:
    flat = " ".join(text.split())
    return flat if len(flat) <= limit else f"{flat[:limit]} ... [{len(flat) - limit} more characters]"


def cmd_list(where: Path, cwd: str) -> None:
    groups = unreviewed(where)
    ordered = sorted(groups.items(), key=lambda item: (-len({e["session"] for e in item[1]}), max(e["ts"] for e in item[1])))
    failures = read_jsonl(where / "corrections.log")
    print(json.dumps({
        "collect": collects(cwd),
        # messages the hook failed on were never judged: say this before anything else
        "failures": {"count": len(failures), "newest": failures[-1] if failures else None},
        "entries": sum(len(entries) for entries in groups.values()),
        "groups": [{
            "id": gid, "entries": len(entries), "sessions": len({e["session"] for e in entries}),
            "days": sorted({e["ts"][:10] for e in entries}),
            "p_lesson_max": max((e["p_lesson"] for e in entries if e["p_lesson"] is not None), default=None),
            "owner": trimmed(entries[0]["owner"], OWNER_TRIM), "answered": trimmed(entries[0].get("previous") or "", PREVIOUS_TRIM),
        } for gid, entries in ordered],
    }, indent=2, ensure_ascii=False))


def cmd_show(where: Path, gid: str) -> None:
    entries = unreviewed(where).get(gid)
    if not entries:
        raise QueueError(f"no unreviewed group {gid}; `corrections.py list` gives the ids")
    print(json.dumps(entries, indent=2, ensure_ascii=False))


def cmd_lessons(where: Path) -> None:
    seen: dict[tuple[str, str, str], dict] = {}
    for review in read_jsonl(where / "corrections-reviews.jsonl"):
        if review["decision"] == "lesson":
            key = (review.get("lesson") or "", review.get("target") or "", review["verdict"])
            row = seen.setdefault(key, {"lesson": key[0], "target": key[1] or None, "verdict": key[2], "entries": 0, "days": set()})
            row["entries"] += 1
            row["days"].add(review["ts"][:10])
    rows = sorted(seen.values(), key=lambda row: -row["entries"])
    print(json.dumps([{**row, "days": sorted(row["days"])} for row in rows], indent=2, ensure_ascii=False))


def cmd_record(where: Path, gid: str, decision: str, verdict: str, target: str | None, lesson: str | None) -> None:
    if decision == "lesson" and not (lesson or "").strip():
        raise QueueError("a lesson needs --lesson: the sentence an agent could follow next time")
    entries = unreviewed(where).get(gid)
    if not entries:
        raise QueueError(f"no unreviewed group {gid}; `corrections.py list` gives the ids")
    for entry in entries:
        append(where / "corrections-reviews.jsonl", {
            "ts": entry["ts"], "session": entry["session"], "group": gid, "p_lesson": entry["p_lesson"], "reviewed": now(),
            "decision": decision, "verdict": verdict, "target": target, "lesson": lesson,
        })
    print(json.dumps({"group": gid, "entries": len(entries), "decision": decision, "verdict": verdict}))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=".", help="a directory inside the checkout (default: the current one)")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("hook", "list", "lessons"):
        commands.add_parser(name)
    commands.add_parser("worker").add_argument("payload", help="the file the hook wrote; internal")
    commands.add_parser("show").add_argument("id")
    record = commands.add_parser("record")
    record.add_argument("id")
    record.add_argument("--decision", required=True, choices=DECISIONS)
    record.add_argument("--verdict", required=True, choices=VERDICTS)
    record.add_argument("--target", help="the file the lesson went to, or the one that already holds it")
    record.add_argument("--lesson", help="the lesson in one sentence")
    args = parser.parse_args()
    if args.command == "hook":
        cmd_hook()
        return
    if args.command == "worker":
        cmd_worker(args.payload)
        return
    where = folder(args.repo)
    if where is None:
        sys.exit(f"corrections.py: {args.repo} is not inside a git checkout")
    try:
        if args.command == "list":
            cmd_list(where, args.repo)
        elif args.command == "show":
            cmd_show(where, args.id)
        elif args.command == "lessons":
            cmd_lessons(where)
        else:
            cmd_record(where, args.id, args.decision, args.verdict, args.target, args.lesson)
    except QueueError as error:
        sys.exit(f"corrections.py: {error}")


if __name__ == "__main__":
    main()
