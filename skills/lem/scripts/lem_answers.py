"""The owner's answer to a row of "Waits for you" that the board answers with its own buttons.

Four waits of a task get their answers on the board (`lem_board_model.answer_row`): a plan that waits
for his read (Build or Drop), a breaker (Help, Park or Drop), "Skip the persona read?" of an interview
(Yes or No), and "Approve this criterion?" of a small change that someone else asked for (Yes or No).
Each row's key names the state block it waits on, by the time of that block's `task.state` event to
the second (`stamp`): `plan:SLUG:STAMP`, `breaker:SLUG:N:STAMP`, `skip:SLUG:STAMP` and
`criterion:SLUG:STAMP`. A new block of the same wait is a new key, so an answer on record applies to
the block it answered and no later one.

The answer is `answers/KEY.json` in the task's folder, a link of a finished file as the one end of a
card is (`lem_cards.link_whole`): of two answers to one key, the one linked first counts, and every
act of the board on that row (the answer route, a park, a yes to the criterion, a drop) links the
record before it acts and refuses with what the record says when the link fails. The record holds the
key, the row's kind and question, the option and its label, the owner's note, `from: board`, `via`
(`local` or `door`), `device` (`phone` or `computer`), `agent` (the request's User-Agent, whole), the
time, and for the criterion the digest of the text the page showed. His No to the standard track's
criteria typed in the task's session is recorded on the same row's key, with `from: session` and no
`via`, `device` or `agent` (`lem criteria change --typed`), so that of his typed word and his answer
on the board the first counts. The task's session reads it on its
wake as `board_answer` of `lem project tasks` (`answer_of_block`).
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import lem_cards

ANSWERS = "answers"
# Each wait the board answers, its options in the order the buttons show them, and each option's label.
OPTIONS = {
    "plan": {"build": "Build", "drop": "Drop"},
    "breaker": {"help": "Help", "park": "Park", "drop": "Drop"},
    "skip": {"yes": "Yes", "no": "No"},
    "criterion": {"yes": "Yes", "no": "No"},
}
# The stamp of a state block in a key: its event's time in UTC, to the second.
STAMP = "%Y%m%dT%H%M%SZ"
KEY = re.compile(r"(?P<kind>plan|skip|criterion|breaker):(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)(?::(?P<number>[1-9]\d*))?:(?P<stamp>\d{8}T\d{6}Z)")


class AnswerError(Exception):
    pass


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def stamp(ms: int) -> str:
    """The stamp of a state block whose event's time is MS (ms since the epoch), to the second."""
    return datetime.fromtimestamp(ms // 1000, timezone.utc).strftime(STAMP)


def stamp_of(ts: str) -> str | None:
    """The stamp of a state block from its event's `ts` (ISO 8601, `Z` for UTC), or None when it does not read as a time."""
    try:
        moment = datetime.fromisoformat(ts)
    except (TypeError, ValueError):
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).strftime(STAMP)


def key_of(kind: str, slug: str, block_ms: int, number: int | None = None) -> str:
    """The key of the row of KIND of the task SLUG, for the state block whose event's time is BLOCK_MS."""
    middle = f":{number}" if kind == "breaker" else ""
    return f"{kind}:{slug}{middle}:{stamp(block_ms)}"


def parse(key: object) -> dict:
    """The parts of a row's key, KIND, SLUG, NUMBER (a breaker's) and STAMP; AnswerError for any other text."""
    found = KEY.fullmatch(key) if isinstance(key, str) else None
    if not found or (found["kind"] == "breaker") != (found["number"] is not None):
        raise AnswerError(f"{key!r} names no row of the board that takes an answer")
    return {"kind": found["kind"], "slug": found["slug"], "number": int(found["number"]) if found["number"] else None, "stamp": found["stamp"]}


def answer_file(task: Path, key: str) -> Path:
    parse(key)
    return task / ANSWERS / f"{key}.json"


def on_record(task: Path, key: str) -> dict | None:
    """The answer on record for KEY in the task's folder TASK, or None."""
    try:
        return json.loads(answer_file(task, key).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as error:
        raise AnswerError(f"{answer_file(task, key)} cannot be read as an answer ({error})") from error


def record(task: Path, key: str, question: str, option: str, note: str, **more) -> tuple[bool, dict]:
    """Record the owner's OPTION and NOTE to the row KEY of the task's folder TASK, only when no answer is
    on record for it: (True, the record) when this call made it, else (False, the answer on record). MORE
    are the board's fields (`via`, `device`, `agent`, and `digest` for the criterion)."""
    kind = parse(key)["kind"]
    if option not in OPTIONS[kind]:
        raise AnswerError(f"the row {key} takes {', '.join(OPTIONS[kind])}, not {option!r}")
    made = {"key": key, "kind": kind, "question": question, "option": option, "label": OPTIONS[kind][option], "note": note, "from": "board", "at": now(), **more}
    if lem_cards.link_whole(answer_file(task, key), (json.dumps(made, ensure_ascii=False, indent=1) + "\n").encode("utf-8")):
        return True, made
    found = on_record(task, key)
    if found is None:
        raise AnswerError(f"{answer_file(task, key)} was there and is gone: something removed an answer of the owner's")
    return False, found


def withdraw(task: Path, made: dict) -> None:
    """Remove the record MADE, which this server linked, when the act it stood for did not run (the
    script of a park or of a yes refused): the row is the owner's again, as before his tap."""
    file = answer_file(task, made["key"])
    try:
        if json.loads(file.read_text(encoding="utf-8")) == made:
            file.unlink()
    except (OSError, ValueError):
        pass


def answer_of_block(task: Path, slug: str, ts: str | None) -> dict | None:
    """The answer on record for the state block of the task SLUG whose event's time is TS (its newest, for
    `board_answer` of `lem project tasks`), or None: the record whose key names that block. Of two, which
    two rows of one block could only be, the one recorded first."""
    block = stamp_of(ts) if ts else None
    folder = task / ANSWERS
    if block is None or not folder.is_dir():
        return None
    found = []
    for file in folder.glob("*.json"):
        try:
            parts = parse(file.name.removesuffix(".json"))
        except AnswerError:
            continue
        if parts["slug"] != slug or parts["stamp"] != block:
            continue
        try:
            found.append(json.loads(file.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
    return min(found, key=lambda r: str(r.get("at") or "")) if found else None


def took_effect(made: dict) -> str:
    """What the answer on record says, in one sentence: "You picked Drop for breaker 1 at 15:40, from the phone"."""
    try:
        parts = parse(made.get("key"))
    except AnswerError:
        parts = {"kind": made.get("kind"), "number": None}
    what = {"plan": "for the plan", "breaker": f"for breaker {parts['number']}", "skip": "on “Skip the persona read?”",
            "criterion": "on “Approve this criterion?”"}.get(parts["kind"], "")
    device = f", from the {made['device']}" if made.get("device") else ""
    return f"You picked {made.get('label') or made.get('option')} {what} at {lem_cards.local_time(made.get('at'))}{device}".replace("  ", " ")
