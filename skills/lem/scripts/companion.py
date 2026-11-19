#!/usr/bin/env python3
"""The companion of one need: a session under Lem's own in which the owner answers Lem.

    lem companion talk SLUG --from TEXT [--leave TEXT ...]
                                 copy the turns of Lem's own session into the task's talk.md
    lem companion open SLUG --need interview|criteria|choice [--choice N] [--asked]
                                 open the companion of the need that waits for the owner
    lem companion close SLUG --need ... [--choice N] --why answered|dismissed|gone|dropped
                                 log why it ends, then close its session when it runs
    lem companion told-away SLUG --need ... [--choice N]
                                 log that Lem told a companion that the owner is away
    lem companion list           each companion that runs, with its task, need and name
    lem companion due            what Lem owes, from the files: what to open, start and close

A need is one of three, and each has one fixed name in agterm's sidebar: `interview` (`SLUG ·
interview`), `criteria` (`SLUG · criteria`) and `choice N` (`SLUG · choice N`). Which need waits
is read from the task's newest state block: `held` with `the interview waits for the owner`, or with
`the criteria wait for the owner: the small change is a full change`, is an interview; `held` with
any other line that starts `the criteria wait for the owner` is criteria; `held` with `choice N
waits for the owner`, and every choice that `lem decisions pending` lists, is choice N. A wait is
answered when the record holds his word after the block that opened it: an approval of the criteria
by `owner` or `alone` (the `criteria.approved` event, or `criteria.json` of the task directory), or
choice N that no longer waits in `lem decisions list`. An answered wait opens nothing.

`talk` copies the turns of Lem's Claude Code session word for word: from the newest owner turn
whose text starts with TEXT to the newest turn, each with who said it and only its text, less each
owner turn that a `--leave` text starts (another topic) with the turns of Lem that answer it. It
copies only what the owner typed (a `/lem` line as he typed it) and what Lem wrote; the skill's text
that `/lem` loads, a task's notification and agterm's mail are no turn of his.

`open` refuses with exit 1 and the fix: a task on the fast track, a task that ended, a need that
does not wait or is answered, an interview with no talk.md, any need while the owner is away, a
need of a task that runs without him while he is there (a night's) unless it is an irreversible
choice, and a need whose companion the owner closed with no answer, unless `--asked` says that he
asked for it (bare `/lem`, `/lem status SLUG`, a row of the board). A need whose companion runs is
not opened twice: `open` prints that one. A companion opens with no focus, under Lem's session (or
beside it, when Lem's session is a companion itself), in the main checkout, and runs the owner's
default Claude with the brief `companion-NEED.md` of the task directory.

`due` opens nothing and starts nothing:
  open     each need that waits, is not answered, has no companion that runs, and `open` would open
  talk     each interview that would open but has no talk.md yet: `talk` first, then `open`
  start    each task whose newest block is the wait and whose wait is answered: its lead starts
  close    each companion that runs and whose need no longer waits
  gone     each companion that is no longer in agterm's tree and has no `close`: log `--why gone`
  away     while the owner is away, each companion that runs and was not told since he went away
"""

from __future__ import annotations

import sys

if sys.version_info < (3, 11):
    # an old python3 must still load this file, so that it can say what it needs and not a traceback
    sys.exit(f"companion.py: Lem needs Python 3.11 or newer, and this python3 is {sys.version.split()[0]}; put a newer one first on PATH")

import argparse
import json
import os
import pwd
import re
import shutil
import subprocess
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
SKILL = SCRIPTS.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(SCRIPTS))
import lem_sibling  # noqa: E402
import project  # noqa: E402

NEEDS = ("interview", "criteria", "choice")
CHOICE_WAIT = re.compile(r"choice ([1-9]\d*) waits for the owner")
CLOSES = ("answered", "dismissed", "gone", "dropped")
# a companion that ended this way opens again only on the owner's word (`--asked`)
ON_HIS_WORD = ("dismissed", "gone")
# whose approval answers the wait of an interview or criteria: his own, or one made while the task ran without him
APPROVERS = ("owner", "alone")
EVENTS = ("companion.open", "companion.close", "companion.away")
TALK = "talk.md"
# the characters that the launch line cannot carry inside its two levels of quotes
UNQUOTABLE = re.compile(r"['\"\\$`\n]")
# how many words of a turn name it, in talk.md and in the companion's first words
FIRST_WORDS = 8


class CompanionError(Exception):
    pass


# ---- the rules, over facts ----

def need_name(need: str, choice: int | None) -> str:
    return f"choice {choice}" if need == "choice" else need


def sidebar_name(slug: str, need: str, choice: int | None) -> str:
    """The companion's name in agterm's sidebar, one fixed name for each need."""
    return f"{slug} · {need_name(need, choice)}"


def key_of(slug: str, need: str, choice: int | None) -> str:
    return f"{slug}/{need_name(need, choice)}"


def held_need(line: str | None) -> tuple[str, int | None] | None:
    """The need that the first line of a `held` block opens, or None for a hold that is no need of a companion."""
    if not line:
        return None
    if line.startswith(project.INTERVIEW_WAIT) or project.FAST_GREW.search(line):
        return ("interview", None)
    if line.startswith(project.CRITERIA_WAIT):
        return ("criteria", None)
    found = CHOICE_WAIT.fullmatch(line.strip())
    return ("choice", int(found[1])) if found else None


def needs_of(task: dict) -> list[dict]:
    """Each need of the task, waiting or answered. `task` holds the facts `gather` reads: `status`,
    `line` (the newest block's first line), `held_at`, `approvals`, `choices` (each decision of the
    task that matters here, by its id: its `state`, `irreversible` and `at`)."""
    out: list[dict] = []
    if task["status"] == "held" and (found := held_need(task["line"])):
        need, number = found
        if need == "choice":
            record = task["choices"].get(number)
            # a line that names a choice the record does not have opens no card
            if record is not None:
                out.append({"need": need, "choice": number, "since": task["held_at"], "irreversible": bool(record["irreversible"]),
                            "answered": record["state"] != "waits", "held": True})
        else:
            answered = any(approval["by"] in APPROVERS and approval["at"] >= (task["held_at"] or "") for approval in task["approvals"])
            out.append({"need": need, "choice": None, "since": task["held_at"], "irreversible": False, "answered": answered, "held": True})
    for number, record in sorted(task["choices"].items()):
        if record["state"] == "waits" and not any(item["need"] == "choice" and item["choice"] == number for item in out):
            out.append({"need": "choice", "choice": number, "since": record["at"], "irreversible": bool(record["irreversible"]), "answered": False, "held": False})
    return out


def companions_of(events: list[dict], live: set[str]) -> dict[str, dict]:
    """Each need's companion as the log and agterm's tree say: its newest `companion.open`, the
    `companion.close` after it, the times Lem told it that the owner is away, and whether it runs.
    One that is gone from the tree with no close ended as `gone`."""
    found: dict[str, dict] = {}
    for record in events:
        key = key_of(record.get("task", ""), record.get("need", ""), record.get("choice"))
        if record.get("event") == "companion.open":
            found[key] = {"open": record, "close": None, "told": []}
        elif key in found and record.get("event") == "companion.close" and found[key]["close"] is None:
            found[key]["close"] = record
        elif key in found and record.get("event") == "companion.away" and record.get("session") == found[key]["open"].get("session"):
            found[key]["told"].append(record["ts"])
    for companion in found.values():
        opened = companion["open"]
        companion["live"] = companion["close"] is None and str(opened.get("session", "")).upper() in live
        if companion["close"] is not None:
            companion["ended"], companion["ended_at"] = companion["close"].get("why"), companion["close"]["ts"]
        elif not companion["live"]:
            companion["ended"], companion["ended_at"] = "gone", opened["ts"]
        else:
            companion["ended"] = companion["ended_at"] = None
    return found


def on_his_word(need: dict, companion: dict | None, back_at: str | None) -> bool:
    """Whether the need opens again only when the owner asks: its companion ended with no answer
    (he closed the card, or the session is gone) after the wait began. An irreversible choice opens
    again by itself once he is back after that end, since `/lem im-back` opens each such step."""
    if not companion or companion["ended"] not in ON_HIS_WORD or companion["ended_at"] < (need["since"] or ""):
        return False
    return not (need["need"] == "choice" and need["irreversible"] and back_at and back_at > companion["ended_at"])


def refusal(task: dict, need: str, choice: int | None, facts: dict, asked: bool) -> tuple[str, str] | None:
    """Why `open` refuses this need, as (a code, the message with its fix), or None when it opens."""
    slug, name = task["slug"], need_name(need, choice)
    if task["status"] in project.ENDED:
        return ("ended", f"the task {slug!r} is {task['status']}: an ended task waits for nobody, and no companion opens for it")
    if task["track"] == "fast":
        return ("fast", f"{slug} is on the fast track: its one builder asks the owner nothing, so no companion opens for it; "
                        "a builder that found a full change writes the interview's line, and the interview opens then")
    owner = facts["owner"]
    if owner["away"]:
        return ("away", f"the owner is away (since {owner['since']}, in the words {owner.get('words')!r}): no companion opens while he is away, "
                        "since the ladder takes every choice and `--alone` approves held criteria; at `/lem im-back` `lem companion due` gives each one to open")
    found = next((item for item in needs_of(task) if item["need"] == need and item["choice"] == choice), None)
    if found is None:
        line = task["line"] or "none"
        return ("none", f"no {name} of {slug} waits for the owner: its newest state is {task['status'] or 'none'} ({line!r}); "
                        "`lem companion due` lists what waits")
    if found["answered"]:
        return ("answered", f"the {name} of {slug} is answered on record: nothing waits for the owner there, and `lem companion due` gives its start")
    if task["mode"] == "alone" and not (need == "choice" and found["irreversible"]):
        return ("alone", f"{slug} runs without the owner (a night's task): its criteria and its choices are taken without him, "
                         "and only an irreversible choice opens a companion while he is there")
    if need == "interview" and not task["talk"]:
        return ("talk", f"the interview of {slug} has no {TALK} in its task directory: run `lem companion talk {slug} --from \"TEXT\"` "
                        "with the first words of the owner's turn where the topic began, then open it")
    companion = facts["companions"].get(key_of(slug, need, choice))
    if not asked and on_his_word(found, companion, facts["back_at"]):
        return ("asked", f"the owner closed the companion of {slug}'s {name} with no answer ({companion['ended']}), so it opens again on his word only: "
                         f"a row of the board's Waits for you, or `/lem` in Lem's session, which runs `lem companion open {slug} --need {need}"
                         + (f" --choice {choice}" if choice is not None else "") + " --asked`")
    return None


def entry(slug: str, item: dict, **more: object) -> dict:
    return {"task": slug, "need": item["need"], "choice": item["choice"], "name": sidebar_name(slug, item["need"], item["choice"]), **more}


def due(facts: dict) -> dict:
    """What Lem owes, from the facts `gather` reads; nothing here opens, starts or writes."""
    owner = facts["owner"]
    out: dict = {"owner": owner, "open": [], "talk": [], "start": [], "close": [], "gone": [], "away": []}
    wanted: set[str] = set()
    for task in facts["tasks"]:
        slug = task["slug"]
        items = needs_of(task) if task["status"] not in project.ENDED else []
        for item in items:
            key = key_of(slug, item["need"], item["choice"])
            companion = facts["companions"].get(key)
            if item["answered"]:
                if item["held"]:
                    # the newest block is the wait, and the record holds his word after it: the lead starts
                    out["start"].append(entry(slug, item))
                continue
            wanted.add(key)
            if companion and companion["live"]:
                continue
            refused = refusal(task, item["need"], item["choice"], facts, asked=False)
            if refused is None:
                out["open"].append(entry(slug, item, irreversible=item["irreversible"]))
            elif refused[0] == "talk":
                out["talk"].append(entry(slug, item))
    statuses = {task["slug"]: task["status"] for task in facts["tasks"]}
    for key, companion in facts["companions"].items():
        opened = companion["open"]
        slug = opened.get("task")
        item = {"need": opened.get("need"), "choice": opened.get("choice")}
        if companion["live"] and key not in wanted:
            out["close"].append(entry(slug, item, session=opened.get("session"), why="dropped" if statuses.get(slug) == "dropped" else "answered"))
        elif companion["close"] is None and not companion["live"]:
            out["gone"].append(entry(slug, item, session=opened.get("session")))
        # a companion that is due its close gets no message: the away took its choice
        if owner["away"] and companion["live"] and key in wanted and not any(told >= owner["since"] for told in companion["told"]):
            out["away"].append(entry(slug, item, session=opened.get("session")))
    return out


# ---- the transcript ----

COMMAND_NAME = re.compile(r"<command-name>(.*?)</command-name>", re.S)
COMMAND_ARGS = re.compile(r"<command-args>(.*?)</command-args>", re.S)


def typed_text(content: object) -> tuple[str, str | None]:
    """The text of a record the owner typed, and a slash command's arguments alone: a `/lem` line
    is kept as the command line he typed, `/lem ARGS` (Claude Code names a plugin's skill `/lem:lem`)."""
    if isinstance(content, list):
        text = "\n".join(block.get("text", "") for block in content if isinstance(block, dict) and block.get("type") == "text")
    else:
        text = content if isinstance(content, str) else ""
    text = text.strip()
    if text.startswith(("<command-message>", "<command-name>")) and (name := COMMAND_NAME.search(text)):
        command = name[1].strip()
        plugin, colon, skill = command.lstrip("/").partition(":")
        if colon and plugin == skill:
            command = "/" + plugin
        args = (COMMAND_ARGS.search(text)[1] if COMMAND_ARGS.search(text) else "").strip()
        return (f"{command} {args}" if args else command), args
    return text, None


def transcript_turns(path: Path) -> list[dict]:
    """The turns of a Claude Code session's transcript, oldest first, each {"who": "owner" or
    "lem", "at": its first record's time, "text": its words}. The form is the harness's
    (`skills/lem/harness/claude-code.md`): one JSON record a line. The owner's turn is a `user`
    record whose `origin.kind` is `human`, with no `isMeta` (the text `/lem` loads) and no
    `isCompactSummary`; a task's notification, agterm's mail and a peer's message have another
    origin. Lem's turn is the text blocks of the `assistant` records between two prompts; a tool's
    call and its result are no words. A record of a subagent (`isSidechain`) is no turn of this
    session, and a `compact_boundary` ends nothing: the records before it are kept."""
    turns: list[dict] = []
    lem_open = False
    prompts = origins = 0
    for raw in path.read_bytes().splitlines():
        try:
            record = json.loads(raw.decode("utf-8", errors="replace"))
        except ValueError:
            continue
        if not isinstance(record, dict) or record.get("isSidechain"):
            continue
        kind = record.get("type")
        content = (record.get("message") or {}).get("content") if isinstance(record.get("message"), dict) else None
        if kind == "assistant":
            texts = [block.get("text", "") for block in content if isinstance(block, dict) and block.get("type") == "text"] if isinstance(content, list) else []
            words = "\n\n".join(text.strip() for text in texts if text.strip())
            if not words:
                continue
            if lem_open:
                turns[-1]["text"] += "\n\n" + words
            else:
                turns.append({"who": "lem", "at": record.get("timestamp"), "text": words})
                lem_open = True
            continue
        if kind != "user":
            continue
        if isinstance(content, list) and any(isinstance(block, dict) and block.get("type") == "tool_result" for block in content):
            continue
        # any other prompt ends Lem's turn: the owner's, a notification, a mail
        lem_open = False
        prompts += 1
        if "origin" in record:
            origins += 1
        origin = record.get("origin")
        if record.get("isMeta") or record.get("isCompactSummary") or not (isinstance(origin, dict) and origin.get("kind") == "human"):
            continue
        text, args = typed_text(content)
        if text:
            turns.append({"who": "owner", "at": record.get("timestamp"), "text": text, "args": args})
    if prompts and not origins:
        raise CompanionError(
            f"{path} names no prompt's origin, so the owner's turns cannot be told from the rest: this Claude Code writes its transcript "
            "in another form than harness/claude-code.md names; give the companion the talk by hand",
        )
    return turns


def flat(text: str) -> str:
    return " ".join(text.split())


def starts(turn: dict, start: str) -> bool:
    words = flat(start)
    return flat(turn["text"]).startswith(words) or (turn.get("args") is not None and flat(turn["args"]).startswith(words))


def first_words(text: str) -> str:
    words = flat(text).split(" ")
    return " ".join(words[:FIRST_WORDS]) + (" …" if len(words) > FIRST_WORDS else "")


def talk_range(turns: list[dict], start: str, leave: list[str]) -> tuple[list[dict], list[dict]]:
    """The turns from the newest owner turn that `start` starts to the newest turn, and what was
    left out: each owner turn that a text of `leave` starts (the newest one after the first turn),
    with the turns of Lem after it until the next owner turn."""
    if not flat(start):
        raise CompanionError("--from is the first words of the owner's turn where the topic began, and it is empty")
    begin = next((index for index in range(len(turns) - 1, -1, -1) if turns[index]["who"] == "owner" and starts(turns[index], start)), None)
    if begin is None:
        raise CompanionError(f"no turn of the owner starts with {start!r}: give the first words of his turn where the topic began, as he typed them")
    kept = turns[begin:]
    out: set[int] = set()
    left: list[dict] = []
    for text in leave:
        if not flat(text):
            raise CompanionError("a --leave text is the first words of an owner turn to leave out, and it is empty")
        at = next((index for index in range(len(kept) - 1, 0, -1) if kept[index]["who"] == "owner" and starts(kept[index], text)), None)
        if at is None:
            raise CompanionError(f"no turn of the owner after the first one starts with {text!r}: --leave names an owner turn of the copy, as he typed it")
        if at in out:
            continue
        span = [at]
        while at + len(span) < len(kept) and kept[at + len(span)]["who"] == "lem":
            span.append(at + len(span))
        out.update(span)
        left.append({"at": kept[at]["at"], "words": first_words(kept[at]["text"]), "lem_turns": len(span) - 1})
    return [turn for index, turn in enumerate(kept) if index not in out], sorted(left, key=lambda item: item["at"] or "")


def when(stamp: str | None) -> str:
    """`2026-11-19T14:17:34.495Z` as `2026-11-19 14:17 UTC`."""
    return f"{stamp[:10]} {stamp[11:16]} UTC" if stamp and len(stamp) >= 16 else "an unknown time"


def talk_text(slug: str, kept: list[dict], left: list[dict], source: Path) -> str:
    owners = sum(1 for turn in kept if turn["who"] == "owner")
    lines = [
        f"# The talk that led to the ask of {slug}", "",
        f"Copied word for word from Lem's session ({source.name}): {len(kept)} turns, {owners} of the owner and {len(kept) - owners} of Lem, "
        f"from the owner's turn of {when(kept[0]['at'])} that starts \"{first_words(kept[0]['text'])}\" to the newest turn.", "",
    ]
    if left:
        lines += ["Left out as another topic:", ""]
        lines += [f"- the owner's turn of {when(item['at'])} that starts \"{item['words']}\", with {item['lem_turns']} turn{'s' if item['lem_turns'] != 1 else ''} of Lem after it"
                  for item in left]
        lines.append("")
    for turn in kept:
        lines += [f"## {'The owner' if turn['who'] == 'owner' else 'Lem'}, {when(turn['at'])}", "", turn["text"], ""]
    return "\n".join(lines)


def transcript_file() -> Path:
    """Lem's own transcript: `~/.claude/projects/*/ID.jsonl`, with ID the session's
    `CLAUDE_CODE_SESSION_ID`, which Claude Code gives the Bash tool (`harness/claude-code.md`).
    `CLAUDE_CONFIG_DIR`, when set, stands for `~/.claude`."""
    session = os.environ.get("CLAUDE_CODE_SESSION_ID", "").strip()
    if not session:
        raise CompanionError("CLAUDE_CODE_SESSION_ID is not set: run `lem companion talk` from Lem's own Claude Code session, whose Bash tool has it")
    if not re.fullmatch(r"[A-Za-z0-9-]+", session):
        raise CompanionError(f"CLAUDE_CODE_SESSION_ID {session!r} is no session id of Claude Code: run this from Lem's own session")
    home = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    found = sorted((home / "projects").glob(f"*/{session}.jsonl"))
    if not found:
        raise CompanionError(f"no transcript {session}.jsonl under {home / 'projects'}: run this from Lem's own Claude Code session, whose transcript Claude Code keeps there")
    if len(found) > 1:
        raise CompanionError(f"two transcripts carry the session {session}: {', '.join(map(str, found))}; move the one that is not Lem's aside")
    return found[0]


def cmd_talk(root: Path, slug: str, start: str, leave: list[str]) -> dict:
    directory = project.task_directory(root, slug)
    source = transcript_file()
    kept, left = talk_range(transcript_turns(source), start, leave)
    file = directory / TALK
    file.write_text(talk_text(slug, kept, left, source), encoding="utf-8")
    owners = sum(1 for turn in kept if turn["who"] == "owner")
    return {"task": slug, "file": str(file), "transcript": str(source), "turns": len(kept), "owner_turns": owners, "lem_turns": len(kept) - owners,
            "first": {"at": kept[0]["at"], "words": first_words(kept[0]["text"])}, "left_out": left}


# ---- agterm ----

def agterm() -> dict:
    """This session's place in agterm, from the variables agterm gives a session's commands."""
    def env(*names: str) -> str:
        return next((os.environ[name] for name in names if os.environ.get(name)), "")

    found = {"session": env("AGTERM_SESSION_ID", "AGT_SESSION_ID"), "pane": env("AGTERM_PANE_ID"), "socket": env("AGTERM_SOCKET", "AGT_SOCKET"),
             "window": env("AGTERM_WINDOW_ID", "AGT_WINDOW_ID")}
    if not (found["session"] and found["socket"]):
        raise CompanionError("not inside an agterm session (AGTERM_SESSION_ID and AGTERM_SOCKET are not set): a companion is a session of agterm, which Lem needs")
    if not shutil.which("agtermctl"):
        raise CompanionError("agtermctl is not on the PATH: install agterm's command line tool (Help > Install Command Line Tool)")
    return found


def ctl(place: dict, *args: str) -> str:
    # agtermctl never reads the socket from the environment
    ran = subprocess.run(["agtermctl", *args, "--socket", place["socket"]], capture_output=True, text=True, check=False)
    if ran.returncode != 0:
        raise CompanionError(f"agtermctl {' '.join(args[:2])} failed: {(ran.stderr or ran.stdout).strip() or f'exit {ran.returncode}'}")
    return ran.stdout


def sessions(place: dict) -> list[dict]:
    window = ["--window", place["window"]] if place["window"] else []
    try:
        tree = json.loads(ctl(place, "tree", "--json", *window))["result"]["tree"]
    except (ValueError, KeyError, TypeError) as error:
        raise CompanionError(f"agtermctl tree answered no tree ({error})") from error
    return [node for workspace in tree.get("workspaces", []) for node in workspace.get("sessions", [])]


# ---- the facts ----

def sibling(root: Path, *args: str) -> object:
    ran = lem_sibling.run(SCRIPTS / "decisions.py", root, *args)
    if ran.returncode != 0:
        raise CompanionError((ran.stderr.strip().splitlines() or [f"lem decisions {args[0]} failed"])[-1].removeprefix("decisions.py: "))
    return json.loads(ran.stdout)


def approvals_of(directory: Path, events: list[dict]) -> list[dict]:
    """Every approval of the task's criteria, with its time and who: the `criteria.approved` events,
    and `criteria.json`, which `lem criteria approve` writes before it logs the event."""
    found = [{"at": record["ts"], "by": record.get("by")} for record in events]
    kept = directory / "criteria.json"
    if kept.is_file():
        try:
            record = json.loads(kept.read_text(encoding="utf-8"))
        except ValueError as error:
            raise CompanionError(f"{kept} does not read as JSON ({error}); it is written by `lem criteria approve` only") from error
        for approval in [record, *record.get("history", [])]:
            if isinstance(approval, dict) and approval.get("at"):
                found.append({"at": approval["at"], "by": approval.get("by")})
    return found


def gather(root: Path, live: set[str]) -> dict:
    """The facts every rule here reads, from the task files, the event log and the decisions."""
    tasks = project.read_tasks(root)
    events = project.events_named(root, "task.state", "criteria.approved", project.OWNER, *EVENTS)
    waiting = sibling(root, "pending")["waiting"]
    state = project.state_root(root)
    facts_tasks = []
    for task in tasks:
        slug = task["slug"]
        first = project.STATE_LINE.fullmatch(task["state"].splitlines()[0]) if task["state"] else None
        line = first["text"] if first else None
        # the block's time to the second, from its event when the log has it, else its minute
        newest = next((record for record in reversed(events) if record.get("event") == "task.state" and record.get("task") == slug), None)
        held_at = newest["ts"] if newest and newest.get("status") == task["status"] and newest.get("text") == line else (f"{task['since'][:-1]}:00Z" if task["since"] else None)
        choices = {item["id"]: {"state": "waits", "irreversible": item.get("irreversible"), "at": item.get("at")} for item in waiting if item["task"] == slug}
        held = held_need(line) if task["status"] == "held" else None
        if held and held[0] == "choice" and held[1] not in choices:
            for item in sibling(root, "list", slug):
                if item.get("id") == held[1]:
                    choices[held[1]] = {"state": item.get("state"), "irreversible": item.get("irreversible"), "at": item.get("at")}
        directory = state / "tasks" / slug
        facts_tasks.append({
            "slug": slug, "status": task["status"], "track": task["track"], "mode": task["mode"], "line": line, "held_at": held_at,
            "approvals": approvals_of(directory, [record for record in events if record.get("event") == "criteria.approved" and record.get("task") == slug]),
            "choices": choices, "talk": (directory / TALK).is_file(),
        })
    owners = [record for record in events if record.get("event") == project.OWNER and record.get("task") is None]
    back = next((record["ts"] for record in reversed(owners) if not record.get("away")), None)
    return {"tasks": facts_tasks, "owner": project.owner_now(owners), "back_at": back,
            "companions": companions_of([record for record in events if record.get("event") in EVENTS], live)}


def live_ids(nodes: list[dict]) -> set[str]:
    return {str(node.get("id", "")).upper() for node in nodes}


# ---- the commands ----

def say(slug: str, need: str, choice: int | None, beside: bool) -> str:
    where = f"`{sidebar_name(slug, need, choice)}` {'beside' if beside else 'under'} this session"
    if need == "interview":
        return f"the interview of {slug} is open in {where}"
    if need == "criteria":
        return f"the criteria of {slug} are open in {where}"
    return f"choice {choice} of {slug} is open in {where}"


def brief_text(slug: str, need: str, choice: int | None, directory: Path, main: Path, place: dict, lem_name: str) -> str:
    return "\n".join([
        f"Read {SKILL / 'prompts' / 'companion.md'} and follow it.", "",
        f"task: {slug}",
        f"need: {need_name(need, choice)}",
        f"task directory: {directory}",
        f"main checkout: {main}",
        f"coordinator: {place['session']}:{place['pane']}",
        f"socket: {place['socket']}",
        f"lem session: {lem_name}", "",
    ])


def login_shell() -> str:
    shell = pwd.getpwuid(os.getuid()).pw_shell
    if not shell or not os.path.isabs(shell):
        raise CompanionError("the owner's login shell is not known to the system (no absolute path in the user database): agterm needs it to find claude")
    return shell


def task_of(facts: dict, slug: str) -> dict:
    task = next((task for task in facts["tasks"] if task["slug"] == slug), None)
    if task is None:
        known = ", ".join(task["slug"] for task in facts["tasks"]) or "none yet"
        raise CompanionError(f"no task {slug!r}; the tasks are: {known}")
    return task


def cmd_open(root: Path, slug: str, need: str, choice: int | None, asked: bool) -> dict:
    place = agterm()
    nodes = sessions(place)
    facts = gather(root, live_ids(nodes))
    task = task_of(facts, slug)
    refused = refusal(task, need, choice, facts, asked)
    if refused:
        raise CompanionError(refused[1])
    name = sidebar_name(slug, need, choice)
    companion = facts["companions"].get(key_of(slug, need, choice))
    if companion and companion["live"]:
        opened = companion["open"]
        return {"task": slug, "need": need, "choice": choice, "name": name, "session": opened.get("session"), "already": True,
                "say": f"the {need_name(need, choice)} of {slug} is already open in `{name}`"}
    if not place["pane"]:
        raise CompanionError("AGTERM_PANE_ID is not set, so the companion has no address to tell Lem at: run this from Lem's own pane")
    mine = next((node for node in nodes if str(node.get("id", "")).upper() == place["session"].upper()), None)
    if mine is None:
        raise CompanionError(f"this session ({place['session']}) is not in the window agterm answered for: run this from Lem's own session")
    # a companion's companion becomes its sibling, so the parent is the top of the group (as board.py's show)
    parent = str(mine.get("parent") or mine["id"])
    lem_name = str(mine.get("name") or mine.get("title") or mine["id"])
    directory = project.task_directory(root, slug)
    main = project.main_checkout(root)
    brief = directory / f"companion-{need_name(need, choice).replace(' ', '-')}.md"
    shell = login_shell()
    for what, value in (("the brief's path", str(brief)), ("the owner's login shell", shell)):
        if UNQUOTABLE.search(value):
            raise CompanionError(f"{what} {value!r} holds a quote, a backslash, a $ or a line break, which the launch line cannot carry: move the checkout to a path without them")
    brief.write_text(brief_text(slug, need, choice, directory, main, place, lem_name), encoding="utf-8")
    line = f"{shell} -l -c 'claude \"Read {brief} and follow it.\"'"
    made = ctl(place, "session", "new", "--parent", parent, "--cwd", str(main), "--name", name, "--no-select", "--command", line, "--json")
    try:
        session = str(json.loads(made)["result"]["id"])
    except (ValueError, KeyError, TypeError) as error:
        raise CompanionError(f"agtermctl session new answered no session id ({error}): {made.strip()[:200]}") from error
    project.append_event(root, "companion.open", slug, {"need": need, **({"choice": choice} if choice is not None else {}), "session": session, "name": name})
    return {"task": slug, "need": need, "choice": choice, "name": name, "session": session, "parent": parent, "brief": str(brief),
            "already": False, "say": say(slug, need, choice, beside=parent.upper() != place["session"].upper())}


def cmd_close(root: Path, slug: str, need: str, choice: int | None, why: str) -> dict:
    place = agterm()
    project.task_directory(root, slug)
    live = live_ids(sessions(place))
    companions = companions_of(project.events_named(root, *EVENTS), live)
    companion = companions.get(key_of(slug, need, choice))
    if companion is None or companion["close"] is not None:
        return {"task": slug, "need": need, "choice": choice, "closed": False, "says": f"no companion of {slug}'s {need_name(need, choice)} is open"}
    session = companion["open"].get("session")
    # the log first: a companion that closes itself ends with its own session
    project.append_event(root, "companion.close", slug, {"need": need, **({"choice": choice} if choice is not None else {}), "session": session, "why": why})
    if companion["live"]:
        ctl(place, "session", "close", "--target", str(session))
    return {"task": slug, "need": need, "choice": choice, "closed": True, "session": session, "why": why, "ran": companion["live"]}


def cmd_told_away(root: Path, slug: str, need: str, choice: int | None) -> dict:
    place = agterm()
    project.task_directory(root, slug)
    owner = project.owner_now([record for record in project.events_named(root, project.OWNER) if record.get("task") is None])
    if not owner["away"]:
        raise CompanionError("the owner is not away: Lem tells a companion only while his status says away (`lem project waiting` gives it)")
    companion = companions_of(project.events_named(root, *EVENTS), live_ids(sessions(place))).get(key_of(slug, need, choice))
    if not companion or not companion["live"]:
        raise CompanionError(f"no companion of {slug}'s {need_name(need, choice)} runs: there is nobody to tell")
    session = companion["open"].get("session")
    record = project.append_event(root, "companion.away", slug, {"need": need, **({"choice": choice} if choice is not None else {}), "session": session})
    return {"task": slug, "need": need, "choice": choice, "session": session, "since": owner["since"], "at": record["ts"]}


def cmd_list(root: Path) -> list[dict]:
    live = live_ids(sessions(agterm()))
    out = []
    for companion in companions_of(project.events_named(root, *EVENTS), live).values():
        if companion["live"]:
            opened = companion["open"]
            out.append({"task": opened.get("task"), "need": opened.get("need"), "choice": opened.get("choice"), "name": opened.get("name"),
                        "session": opened.get("session"), "since": opened["ts"]})
    return out


def need_argument(args: argparse.Namespace) -> tuple[str, int | None]:
    if args.need == "choice" and args.choice is None:
        raise CompanionError("--need choice names its number: --choice N, as `lem decisions pending` gives it")
    if args.need != "choice" and args.choice is not None:
        raise CompanionError(f"--choice N goes with --need choice, and the need is {args.need}")
    return args.need, args.choice


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="lem companion", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=".", help="a directory inside the checkout (default: the current one)")
    commands = parser.add_subparsers(dest="command", required=True)
    talk = commands.add_parser("talk", help="copy the turns of Lem's session about the task's ask into its talk.md")
    talk.add_argument("slug")
    talk.add_argument("--from", dest="start", required=True, metavar="TEXT", help="the first words of the owner's turn where the topic began")
    talk.add_argument("--leave", action="append", default=[], metavar="TEXT", help="the first words of an owner turn of another topic, left out with Lem's turns after it")

    def need(sub: argparse.ArgumentParser) -> None:
        sub.add_argument("slug")
        sub.add_argument("--need", required=True, choices=NEEDS)
        sub.add_argument("--choice", type=int, metavar="N", help="with --need choice: the choice's number")

    opened = commands.add_parser("open", help="open the companion of a need that waits for the owner")
    need(opened)
    opened.add_argument("--asked", action="store_true", help="the owner asked for it: bare /lem, /lem status SLUG, a row of the board")
    closed = commands.add_parser("close", help="log why a need's companion ends, and close its session when it runs")
    need(closed)
    closed.add_argument("--why", required=True, choices=CLOSES)
    need(commands.add_parser("told-away", help="log that Lem told a need's companion that the owner is away"))
    commands.add_parser("list", help="each companion that runs")
    commands.add_parser("due", help="what Lem owes: the companions to open and close, and the leads to start")
    args = parser.parse_args(argv)
    try:
        root = project.repo_root(Path(args.repo))
        if args.command == "talk":
            result: object = cmd_talk(root, args.slug, args.start, args.leave)
        elif args.command == "list":
            result = cmd_list(root)
        elif args.command == "due":
            result = due(gather(root, live_ids(sessions(agterm()))))
        else:
            which, number = need_argument(args)
            if args.command == "open":
                result = cmd_open(root, args.slug, which, number, args.asked)
            elif args.command == "close":
                result = cmd_close(root, args.slug, which, number, args.why)
            else:
                result = cmd_told_away(root, args.slug, which, number)
    except (CompanionError, project.SettingsError) as error:
        sys.exit(f"lem companion: {error}")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
