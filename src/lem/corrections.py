"""A project's queue of the owner's corrections: the hook that fills it, and what the
retro reads.

A correction that the owner gave once and that came back is what `/lem retro` looks for.
The sessions that got the correction do not record it reliably, so a hook records it for
them: it asks a small decision model about each message the owner types, and queues the
ones an agent should learn a lesson from. The retro, a big model, decides about each.

    lem corrections hook                the hook an agent runs on each message of the owner
    lem corrections collect yes|no      the machine's yes or no to the queue, for every repository on it
    lem corrections list                unreviewed groups as JSON, most sessions first
    lem corrections show ID             every entry of one group in full
    lem corrections lessons             the lessons earlier retros recorded, with their targets
    lem corrections record ID --decision lesson|not_lesson --verdict VERDICT [--target PATH --lesson TEXT]   (a lesson needs both)
                                        write down what was decided about a group

A retro changes no file and asks the owner nothing: a lesson it finds, the first time or
one that came back, becomes a proposal of the retro's day, which a fresh reviewer reads
before the owner (`stages/learn.md`). Its group is recorded with the verdict `proposed`,
`--target` the file the proposal would change, and the proposal's name
(`retro of 2026-11-24 #3`) in its `--lesson` line, and `lessons` gives it with that
verdict: a lesson in no file yet, which the retro never proposes to remove.

It is an optional part, and the developer's choice for his machine. The hook sends the
message he types and the agent message it answers to the Jev decision model, through
`jev.py` beside this file, so it runs only where `collect = true` under `[corrections]`
in `machine.toml` of Lem's home folder (`lem_state.machine_file()`) says yes, and only
in a repository that uses Lem (`.lem/settings.toml`). The switch is the machine's alone:
it holds in every repository on the machine, no file of a repository can hold it
(`project.py` refuses the table there), and `lem corrections collect yes|no` writes it,
through `lem_state.write_machine`, which keeps the other tables of the file. With no
such line, or a file that does not read, the hook sends nothing: a message leaves the
machine only on his yes. The hook comes with Lem's plugin (`hooks/hooks.json`), and
nobody registers it. A settings file that names the hook too makes a second place; the
machine check (`doctor.py`) names such a file with the entry to delete from it by hand.
Anywhere else the hook exits at once.

A hook that starts twice for one message (the plugin's, and an entry in a settings file)
still judges each message once. Claude Code starts one copy for each place, at the same
moment. The first copy claims the message (the session and the words, for CLAIM_SECONDS)
with an atomic create in `corrections-claims/` beside the queue, and a later copy of the
same message exits with no call and no entry. A claim that cannot be made costs a double
judgment and a line in the log, never the message.

The hook does not wait for Jev: it hands the message to a detached copy of itself and
exits 0 with no output. Its own waits are bounded: it gives up the read of the event and
each of its git calls (two on a machine that says yes, none on one that does not) after
WAIT_SECONDS each. The copy checks the machine's yes again, asks Jev, and appends the
message to the queue when Jev's probability of "lesson" is at least FLAG_AT. Jev is a
pre-filter, and a loose one on purpose. With this question at 0.3, on 150 replies their
owner had labeled, it caught 22 of 27 lessons and flagged 67 of the 123 replies that
were none (mybaze's replies, measured 2026-11-23; FLAG_AT was tuned on that same sample
on 2026-11-07, so the true rate is lower). Jev does not give the same number twice: the
same 150 requests sent again moved the probability of 109 replies, by 0.01 at the median
and 0.11 at the most, and 4 replies crossed FLAG_AT. The question stays one question,
though Jev's docs say to ask one condition in each: in that same run, one yes/no
question for each reason, flagged when any was at FLAG_AT, caught 26 or 27 lessons and
flagged 111 to 116 of the 123, and with the threshold chosen on one half of the sample
and scored on the other, no such rule beat the one question both ways.

The queue is one file for one project: `corrections.jsonl` in Lem's state folder
(`.lem/state/` of the main checkout, as `state.py` names it), shared by every
worktree and never committed. What a retro decided is in `corrections-reviews.jsonl`
beside it. A failure (no key, a failed request) goes to `corrections.log` there and
never to the conversation, and `list` reports it first: a message the hook failed on was
never judged.

The hook half speaks Claude Code's hook contract: the event on stdin with `prompt`,
`cwd`, `session_id` and `transcript_path`. It asks Jev through Lem's own `jev.py`, by
its path: a hook has no `PATH` to count on. LEM_JEV, when set, names another command
with the same contract.

The plugin starts the hook through `python.py` beside this file, which runs it under
a Python of 3.14 or newer when the first `python3` is older, and leaves the session
silent when the machine has none.
"""  # noqa: E501 - the usage table of `--help` keeps its columns

import argparse
import contextlib
import hashlib
import json
import os
import select
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# The one place that says where the state is.
from lem import state as lem_state

FLAG_AT = 0.3
# How long the hook waits for the event on its input, and for git, before it gives up
# without a word. A guess (2026-11-15), not a measurement: long for a local git call,
# short for a person.
WAIT_SECONDS = 2
# How long a claim of one message holds. The copies of a hook registered twice start for
# the same event: Claude Code runs an event's hooks in parallel, each under its own
# timeout from its own start (code.claude.com/docs/en/hooks, read 2026-11-17), and that
# timeout is 10 seconds in `hooks/hooks.json`. A copy claims before that timeout ends
# it, so two claims of one event are less than 10 seconds apart. Twice that is a guess
# at the margin, for copies that start late on a loaded machine. The same words typed
# again in one session inside it count as one message.
CLAIM_SECONDS = 20
# jev.py's exit status for a message too long to judge
JEV_TOO_LONG = 3
DECISIONS = ("lesson", "not_lesson")
# accepted, changed, rejected: the owner's answer to a move a session put to him.
# proposed: the lesson went into a proposal of the retro, for the reviewer and then the
# owner, so no file holds it yet. missed: the owner said that a "not a lesson" entry was
# a lesson after all. unasked: nothing was put to the owner, and no proposal was made.
VERDICTS = ("accepted", "changed", "rejected", "proposed", "missed", "unasked")
# Text an agent's own machinery puts into a user turn; none of it is the owner's words.
INJECTED = (
    "<",
    "[peer chat]",
    "[agterm mailbox",
    "Caveat:",
    "This session is being continued",
    "[Request interrupted",
    "Base directory for this skill",
    "Stop hook",
    "[SYSTEM",
    "Another Claude session",
)
TRANSCRIPT_TAIL_BYTES = 4_000_000
OWNER_TRIM = 500
PREVIOUS_TRIM = 300
QUESTION = {
    "type": "choice",
    "instructions": (
        "This is one exchange between a coding agent and the project's owner: "
        "the agent's last message, then the owner's reply. Decide whether an agent "
        "should remember a lesson from the owner's reply for later work."
    ),
    "choices": {
        "lesson": (
            "An agent should remember something from this reply. The owner corrects it "
            "or disagrees with its approach or assumption; tells it to take a step it "
            "should have taken on its own, such as cleaning up, getting a second "
            "opinion, running work in parallel, interviewing the owner, or saying what "
            "is next; asks for more context or a simpler explanation because the "
            "agent's message was unclear; tells it something it was waiting on has "
            "already happened; or states a lasting preference or rule for how "
            "the work should be done."
        ),
        "no_lesson": (
            "The reply only moves the work on and teaches nothing for later: "
            "it approves or answers the agent's question as asked, picks one of the "
            "options it offered, asks for a retry, or gives a one-off instruction that "
            "is about this moment only."
        ),
    },
}


class QueueError(Exception):
    pass


def git(cwd: str, *args: str) -> str | None:
    try:
        ran = subprocess.run(
            ["git", "-C", cwd, *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=WAIT_SECONDS,
        )
    except OSError, subprocess.TimeoutExpired:
        return None
    return ran.stdout.strip() if ran.returncode == 0 and ran.stdout.strip() else None


def folder(cwd: str, *, quiet: bool = False) -> Path | None:
    """Lem's state folder, which every worktree shares; None outside a checkout. It is
    an error for the retro's commands, and no folder at all for a quiet caller (the hook
    and its detached half)."""
    try:
        return lem_state.folder(Path(cwd), timeout=WAIT_SECONDS)
    except lem_state.StateError as error:
        if quiet:
            return None
        raise QueueError(str(error)) from error


def uses_lem(cwd: str) -> bool:
    """Whether the main checkout of this repository has Lem's settings; no answer from
    git is a no."""
    try:
        return (
            lem_state.main_checkout(Path(cwd), timeout=WAIT_SECONDS)
            / lem_state.TEAM_SETTINGS
        ).is_file()
    except lem_state.StateError:
        return False


def settings_refused(cwd: str) -> str | None:
    """Why `project.py` refuses this repository's settings, or None when it reads them.
    The retro's `list` asks it first, so that a settings file Lem cannot read stops it
    as it stops every command that reads the settings; the hook never asks it, since a
    settings error must not stop the developer's session, and reads the machine's switch
    through `collects`."""
    from lem import project

    try:
        project.load(project.repo_root(Path(cwd)))
    except project.SettingsError as error:
        return str(error)
    return None


def machine_says_yes() -> bool:
    """Whether `machine.toml` of Lem's home folder says `collect = true` under
    `[corrections]`. It is read as `lem project show` reads it, so the two never
    disagree; but where `show` refuses a file that does not read, or one with a table or
    a value that is not valid there, this is a no, and so is a file with no such line
    (the plan of one-home-folder-for-lem, 2026-11-23, decision 6)."""
    try:
        return lem_state.machine_table("corrections").get("collect") is True
    # StateError: a file that does not read or holds what is not valid there, or a
    # relative XDG_CONFIG_HOME; the others are a guard, since a hook's failure must not
    # reach the message
    except lem_state.StateError, OSError, ValueError:
        return False


def collects(cwd: str) -> bool:
    """Whether the hook sends the messages typed in this directory: the machine says
    yes, and the repository uses Lem. The machine's file is read first, so that a
    machine that says no costs no git call. Anything that cannot be read is a no."""
    if not machine_says_yes():
        return False
    top = git(cwd, "rev-parse", "--show-toplevel")
    return top is not None and (Path(top) / lem_state.TEAM_SETTINGS).is_file()


def append(path: Path, record: dict) -> None:
    path.parent.mkdir(exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    """Every record of one of the queue's files. A line that does not read (cut off by a
    full disk, edited by hand) is named with its file and number: the rest of the file
    is not guessed at."""
    if not path.is_file():
        return []
    records = []
    for number, raw in enumerate(path.read_bytes().splitlines(), 1):
        try:
            line = raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise QueueError(
                f"{path}:{number} is not UTF-8 text (byte {error.start} does not "
                "read); this script writes the file, so correct or remove that line"
            ) from error
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except ValueError as error:
            raise QueueError(
                f"{path}:{number} does not read as JSON ({error}); this script writes "
                "the file, so correct or remove that line"
            ) from error
    return records


# ---- the hook ----


def last_agent_text(transcript: str) -> str:
    """The newest text an agent wrote in a Claude Code transcript; empty when there
    is none."""
    path = Path(transcript)
    if not transcript or not path.is_file():
        return ""
    with path.open("rb") as handle:
        handle.seek(max(0, path.stat().st_size - TRANSCRIPT_TAIL_BYTES))
        lines = lem_state.jsonl_lines(handle.read().decode("utf-8", errors="replace"))
    for line in reversed(lines):
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if not isinstance(record, dict) or record.get("type") != "assistant":
            continue
        content = (record.get("message") or {}).get("content")
        if isinstance(content, list):
            text = "\n".join(
                block.get("text", "")
                for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            ).strip()
            if text:
                return text
    return ""


def read_event() -> dict:
    """The hook's event from its input. It does not wait for the input to close: it
    stops at the first whole JSON object, or after WAIT_SECONDS."""
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


def set_aside_if_stale(path: Path) -> bool:
    """Remove a claim older than CLAIM_SECONDS: True when it is gone, False when it is a
    fresh one. It is moved aside before its age is read, so that a claim another copy
    made at that moment is never removed by a look at the one before it: a fresh claim
    moved aside goes back."""
    aside = path.with_name(f"{path.name}.aside-{os.getpid()}-{time.monotonic_ns()}")
    try:
        path.rename(aside)
    except FileNotFoundError:
        return True
    if time.time() - aside.stat().st_mtime < CLAIM_SECONDS:
        aside.rename(path)
        return False
    aside.unlink(missing_ok=True)
    return True


def claim(where: Path, session: str, prompt: str) -> Path | None:
    """Claim one message for this copy of the hook: the claim's file, or None when
    another copy claimed the same words of the same session less than CLAIM_SECONDS ago.
    The claim is an atomic create, so of two copies that look at the same moment one
    wins. Raises OSError when no claim can be made. Each run removes the stale claims it
    sees, so the folder holds a few files at most."""
    claims = where / "corrections-claims"
    claims.mkdir(parents=True, exist_ok=True)
    for entry in claims.iterdir():
        try:
            stale = time.time() - entry.stat().st_mtime >= CLAIM_SECONDS
        except FileNotFoundError:
            continue
        if stale:
            set_aside_if_stale(entry)
    path = (
        claims
        / hashlib.sha256(
            f"{session}\0{prompt}".encode("utf-8", "surrogatepass")
        ).hexdigest()
    )
    # a stale claim of the same words is replaced; three tries are for copies that
    # replace it together
    for _ in range(3):
        try:
            os.close(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600))
        except FileExistsError:
            try:
                fresh = time.time() - path.stat().st_mtime < CLAIM_SECONDS
            except FileNotFoundError:
                continue
            if fresh or not set_aside_if_stale(path):
                return None
        else:
            return path
    return None


def cmd_hook() -> None:  # noqa: C901, PLR0912 - over the limit before the limit was set
    """Return at once. Whatever goes wrong here must not reach the owner's prompt."""
    cwd = None
    path = None
    claimed = None
    where = None
    try:
        event = read_event()
        prompt = (event.get("prompt") or "").strip()
        # the event's directory first: the hook's own may be a worktree that is
        # already removed
        cwd = event.get("cwd") or str(Path.cwd())
        if (
            not prompt
            or prompt.startswith(INJECTED)
            or prompt.startswith("/")
            or not collects(cwd)
        ):
            return
        # One message, one judgment, however many places registered the hook. The event
        # names no message, so the claim is of the session and the words. With no
        # session id nothing tells this message from the same words of another session:
        # it is judged with no claim.
        session = event.get("session_id")
        if isinstance(session, str) and session:
            where = folder(cwd, quiet=True)
            try:
                if where is None:
                    raise OSError("git names no directory of the repository")
                claimed = claim(where, session, prompt)
            except Exception as error:  # noqa: BLE001 - a claim that fails costs a double judgment, never the message
                if where is not None:
                    # a note, not an error: the message is judged, so `list` does not
                    # count it among the failures
                    with contextlib.suppress(Exception):
                        append(
                            where / "corrections.log",
                            {
                                "ts": now(),
                                "session": session,
                                "note": (
                                    f"the hook could not claim the message ({error}); "
                                    "it was judged as usual, and a second registration "
                                    "of the hook may queue it twice"
                                ),
                            },
                        )
            else:
                if claimed is None:
                    return
        payload = {
            "prompt": prompt,
            "cwd": cwd,
            "session": session,
            "transcript": event.get("transcript_path", ""),
        }
        # Through a file only the owner can read, not a pipe: a long message would fill
        # a pipe and hold this hook until the copy reads it.
        handle, path = tempfile.mkstemp(prefix="lem-correction-", suffix=".json")
        with os.fdopen(handle, "w", encoding="utf-8") as file:
            json.dump(payload, file)
        from lem import paths

        subprocess.Popen(
            [sys.executable, "-B", str(paths.MAIN), "corrections", "worker", path],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception as error:  # noqa: BLE001 - a hook failure is logged where the retro reads it, never shown
        try:
            if path is not None:
                # no copy will read it: the owner's words do not stay in a file
                # nobody removes
                Path(path).unlink(missing_ok=True)
            if claimed is not None:
                # this copy cannot judge the message, so it does not keep another from
                # judging it
                claimed.unlink(missing_ok=True)
            # the log of the repository the message was typed in, which is the one that
            # lost it; a repository that does not use Lem gets no state folder for it
            if where is None and uses_lem(cwd or str(Path.cwd())):
                where = folder(cwd or str(Path.cwd()), quiet=True)
            if where is not None:
                append(
                    where / "corrections.log",
                    {
                        "ts": now(),
                        "error": (
                            f"the hook failed before it could judge a message: {error}"
                        ),
                    },
                )
        except Exception:  # noqa: BLE001, S110 - the hook never fails the owner's prompt, not even for its own log
            pass


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def cmd_worker(path: str) -> None:
    file = Path(path)
    payload = json.loads(file.read_text(encoding="utf-8"))
    file.unlink(missing_ok=True)
    where = folder(payload["cwd"], quiet=True)
    # The machine's yes is checked here again, at the last moment before anything is
    # sent: the owner may have turned the queue off since the hook looked, and this half
    # can be run alone.
    if where is None or not collects(payload["cwd"]):
        return
    log = where / "corrections.log"
    stamp = now()
    other = os.environ.get("LEM_JEV")
    from lem import paths

    jev = [other] if other else [sys.executable, "-B", str(paths.MAIN), "jev"]
    previous = (
        last_agent_text(payload.get("transcript", ""))
        or "(no agent message before this one)"
    )
    state = (
        f"--- the agent's last message ---\n{previous}\n\n"
        f"--- the owner's reply ---\n{payload['prompt']}"
    )
    try:
        ran = subprocess.run(
            [*jev, "-"],
            input=json.dumps({"state": state, "questions": {"lesson": QUESTION}}),
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        append(
            log,
            {
                "ts": stamp,
                "session": payload.get("session"),
                "error": f"jev did not run: {error}",
            },
        )
        return
    entry = {
        "ts": stamp,
        "session": payload.get("session"),
        "cwd": payload["cwd"],
        "owner": payload["prompt"],
        "previous": previous,
    }
    if ran.returncode == JEV_TOO_LONG:
        # too long for Jev to judge well: the retro reads it instead
        append(
            where / "corrections.jsonl",
            {**entry, "p_lesson": None, "why": "too long for Jev"},
        )
        return
    try:
        if ran.returncode:
            raise ValueError(ran.stderr.strip()[:500] or f"jev exited {ran.returncode}")
        p_lesson = (
            json.loads(ran.stdout)["answers"]["lesson"].get("probabilities") or {}
        ).get("lesson", 0)
    except (ValueError, KeyError, TypeError, AttributeError) as error:
        append(
            log,
            {
                "ts": stamp,
                "session": payload.get("session"),
                "error": f"jev gave no answer: {error}",
            },
        )
        return
    if p_lesson >= FLAG_AT:
        append(where / "corrections.jsonl", {**entry, "p_lesson": p_lesson})


# ---- what the retro reads ----


def group_id(owner: str) -> str:
    return hashlib.sha1(
        " ".join(owner.split()).encode(), usedforsecurity=False
    ).hexdigest()[:8]


def unreviewed(where: Path) -> dict[str, list[dict]]:
    """Every entry no retro decided about, grouped by the owner's text: one sentence
    sent to eight sessions is one group of eight, not eight things to judge. An entry is
    known by its time, its session and its words together: two messages of one second in
    one session are two entries."""
    reviewed = {
        (review["ts"], review["session"], review.get("group"))
        for review in read_jsonl(where / "corrections-reviews.jsonl")
    }
    groups: dict[str, list[dict]] = {}
    for entry in read_jsonl(where / "corrections.jsonl"):
        gid = group_id(entry["owner"])
        if (entry["ts"], entry["session"], gid) not in reviewed:
            groups.setdefault(gid, []).append(entry)
    return groups


def trimmed(text: str, limit: int) -> str:
    flat = " ".join(text.split())
    return (
        flat
        if len(flat) <= limit
        else f"{flat[:limit]} ... [{len(flat) - limit} more characters]"
    )


def cmd_collect(answer: str) -> None:
    """Write the developer's yes or no to the queue as `collect` under `[corrections]`
    of the machine's file, and nothing else: `write_machine` keeps every other table,
    and refuses a file it cannot keep."""
    collect = answer == "yes"
    try:
        lem_state.write_machine("corrections", {"collect": collect})
    except OSError as error:
        raise QueueError(
            f"{lem_state.machine_file()} was not written ({error.strerror}); "
            "make its folder writable, then run this again"
        ) from error
    except lem_state.StateError as error:
        raise QueueError(str(error)) from error
    print(json.dumps({"collect": collect, "file": str(lem_state.machine_file())}))


def cmd_list(where: Path, cwd: str) -> None:
    groups = unreviewed(where)
    ordered = sorted(
        groups.items(),
        key=lambda item: (
            -len({e["session"] for e in item[1]}),
            max(e["ts"] for e in item[1]),
        ),
    )
    # a line with a note is of a message that was judged: only an error is a message
    # nobody judged
    failures = [
        line for line in read_jsonl(where / "corrections.log") if "error" in line
    ]
    print(
        json.dumps(
            {
                "collect": collects(cwd),
                # messages the hook failed on were never judged: say this before
                # anything else
                "failures": {
                    "count": len(failures),
                    "newest": failures[-1] if failures else None,
                },
                "entries": sum(len(entries) for entries in groups.values()),
                "groups": [
                    {
                        "id": gid,
                        "entries": len(entries),
                        "sessions": len({e["session"] for e in entries}),
                        "days": sorted({e["ts"][:10] for e in entries}),
                        "p_lesson_max": max(
                            (
                                e["p_lesson"]
                                for e in entries
                                if e["p_lesson"] is not None
                            ),
                            default=None,
                        ),
                        "owner": trimmed(entries[0]["owner"], OWNER_TRIM),
                        "answered": trimmed(
                            entries[0].get("previous") or "", PREVIOUS_TRIM
                        ),
                    }
                    for gid, entries in ordered
                ],
            },
            indent=2,
            ensure_ascii=False,
        )
    )


def cmd_show(where: Path, gid: str) -> None:
    entries = unreviewed(where).get(gid)
    if not entries:
        raise QueueError(
            f"no unreviewed group {gid}; `lem corrections list` gives the ids"
        )
    print(json.dumps(entries, indent=2, ensure_ascii=False))


def cmd_lessons(where: Path) -> None:
    seen: dict[tuple[str, str, str], dict] = {}
    for review in read_jsonl(where / "corrections-reviews.jsonl"):
        if review["decision"] == "lesson":
            key = (
                review.get("lesson") or "",
                review.get("target") or "",
                review["verdict"],
            )
            row = seen.setdefault(
                key,
                {
                    "lesson": key[0],
                    "target": key[1] or None,
                    "verdict": key[2],
                    "entries": 0,
                    "days": set(),
                },
            )
            row["entries"] += 1
            row["days"].add(review["ts"][:10])
    rows = sorted(seen.values(), key=lambda row: -row["entries"])
    print(
        json.dumps(
            [{**row, "days": sorted(row["days"])} for row in rows],
            indent=2,
            ensure_ascii=False,
        )
    )


def cmd_record(  # noqa: PLR0913, PLR0917 - over the limit before the limit was set
    where: Path,
    gid: str,
    decision: str,
    verdict: str,
    target: str | None,
    lesson: str | None,
) -> None:
    if decision == "lesson" and not (lesson or "").strip():
        raise QueueError(
            "a lesson needs --lesson: the sentence an agent could follow next time"
        )
    # A lesson with no file is read by no later session, and the retro's list then
    # counts it as kept: two such rows were recorded before this refusal
    # (corrections-reviews.jsonl, 2026-11-20 and 2026-11-21 UTC).
    if decision == "lesson" and not (target or "").strip():
        raise QueueError(
            "a lesson needs --target: the file the lesson went to, the one that "
            "already holds it, or the file its proposal would change"
        )
    entries = unreviewed(where).get(gid)
    if not entries:
        raise QueueError(
            f"no unreviewed group {gid}; `lem corrections list` gives the ids"
        )
    for entry in entries:
        append(
            where / "corrections-reviews.jsonl",
            {
                "ts": entry["ts"],
                "session": entry["session"],
                "group": gid,
                "p_lesson": entry["p_lesson"],
                "reviewed": now(),
                "decision": decision,
                "verdict": verdict,
                "target": target,
                "lesson": lesson,
            },
        )
    print(
        json.dumps(
            {
                "group": gid,
                "entries": len(entries),
                "decision": decision,
                "verdict": verdict,
            }
        )
    )


def arguments() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lem corrections",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="a directory inside the checkout (default: the current one)",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("hook", "list", "lessons"):
        commands.add_parser(name)
    commands.add_parser("worker").add_argument(
        "payload", help="the file the hook wrote; internal"
    )
    commands.add_parser(
        "collect",
        help="the owner's yes or no to the queue, for every repository on this machine",
    ).add_argument(
        "answer",
        choices=("yes", "no"),
        help=(
            "yes: the hook sends each message the owner types to the Jev model; no: "
            "it sends nothing"
        ),
    )
    commands.add_parser("show").add_argument("id")
    record = commands.add_parser("record")
    record.add_argument("id")
    record.add_argument("--decision", required=True, choices=DECISIONS)
    record.add_argument(
        "--verdict",
        required=True,
        choices=VERDICTS,
        help=(
            "the owner's answer to a move put to him (accepted, changed, rejected); "
            "proposed, for a lesson that went into a proposal of the retro; "
            'missed, for a "not a lesson" entry the owner said was one; '
            "unasked, for a group nothing was asked about"
        ),
    )
    record.add_argument(
        "--target",
        help=(
            "the file the lesson went to, the one that already holds it, or for "
            "proposed the file the proposal would change"
        ),
    )
    record.add_argument(
        "--lesson",
        help=(
            "the lesson in one sentence; for proposed, with the proposal's name "
            "(retro of 2026-11-24 #3)"
        ),
    )
    return parser


def main() -> None:  # noqa: C901, PLR0912 - over the limit before the limit was set
    args = arguments().parse_args()
    if args.command == "hook":
        cmd_hook()
        return
    if args.command == "worker":
        cmd_worker(args.payload)
        return
    if args.command == "collect":
        # the machine's, so it needs no repository
        try:
            cmd_collect(args.answer)
        except QueueError as error:
            sys.exit(f"corrections.py: {error}")
        return
    for arg in sys.argv[1:]:
        try:
            arg.encode("utf-8")
        except UnicodeEncodeError:
            sys.exit(
                f"corrections.py: the argument {os.fsencode(arg)!r} is not UTF-8 text; "
                "give it in UTF-8"
            )
    if git(args.repo, "rev-parse", "--git-dir") is None:
        sys.exit(f"corrections.py: {args.repo} is not inside a git checkout")
    if args.command == "list" and (refused := settings_refused(args.repo)):
        sys.exit(f"corrections.py: {refused}")
    try:
        # a caller that is not quiet gets the folder or the QueueError
        where: Path = folder(args.repo)  # pyrefly: ignore[bad-assignment]
        if args.command == "list":
            cmd_list(where, args.repo)
        elif args.command == "show":
            cmd_show(where, args.id)
        elif args.command == "lessons":
            cmd_lessons(where)
        else:
            cmd_record(
                where, args.id, args.decision, args.verdict, args.target, args.lesson
            )
    except QueueError as error:
        sys.exit(f"corrections.py: {error}")


if __name__ == "__main__":
    main()
