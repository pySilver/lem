"""A `lem-ask` card of a task's session, kept in the task's folder, and the one end of
each card.

A task's session runs with `LEM_TASK=SLUG` (`session_hook.py`). When `lem ask` puts up a
card there and the task's folder exists in the state folder of the repository it runs
in, it keeps the card in `cards/` of that folder (`keep`): `PAGEID.html`, a copy of the
page's exact bytes, written after agterm opened the page from its own file, and
`PAGEID.json`, what the card asks (the page id, the agterm session, the time it went up,
and for each question its id, prompt, mode, options and whether it may be left empty,
and whether the page offers to talk). It logs `card.asked`.

A card ends once, and every end goes through one file, `cards/PAGEID.end.json` (`end`):
an answer the owner picked on the card in the session, an answer the board's server
took, a dismissal agterm reported, or a `lem ask close`. The file is a link of a
finished file, as `link_mark` in `project.py` makes a mark: the record is written whole
under a name unique to its writer (the PID, the thread and a random token, since the
board server's threads share one PID), then linked to the name, which fails when the
name is there. So a reader never sees a part of it, a writer that stops leaves no empty
name, and of two writers at one moment one owns the end; the other reads what it says.
The file, not the event log, says whether a card is open. The owner of the end logs
`card.answered` or `card.closed` after the link, for the board's stream.

The board's server reads the same files and calls `end` with `source="board"` for an
answer the owner gave on the board, with `via`, `device` and `agent` (the
request's User-Agent).
"""

import json
import os
import re
import secrets
import sys
import threading
from datetime import UTC, datetime

from lem import clock as lem_clock
from lem import state as lem_state

# typing's flag, without the import of typing, which a hook's start does not pay
TYPE_CHECKING = False
if TYPE_CHECKING:
    from pathlib import Path

CARDS = "cards"
# a task's slug, as project.py's SLUG takes it
SLUG = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
# an agterm page id as a file name: letters, digits, `_` and `-`, never a path
PAGE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}")
# how a card ends, and where the end came from
STATUSES = ("answered", "dismissed", "closed")
SOURCES = ("session", "board")


class CardError(Exception):
    """A card or its record cannot be used."""


def task_folder(start: Path, slug: str | None) -> Path | None:
    """The folder of the task SLUG in the state folder of the repository START is in, or
    None when there is no such task: no slug, a slug that is no task's name, no
    repository, or no folder. It makes nothing: a run of `lem ask` outside a task keeps
    no card."""
    if not slug or not SLUG.fullmatch(slug):
        return None
    try:
        main = lem_state.main_checkout(start)
    except lem_state.StateError:
        return None
    folder = main / lem_state.STATE / "tasks" / slug
    return folder if folder.is_dir() else None


def page_name(page: str) -> str:
    if not isinstance(page, str) or not PAGE.fullmatch(page):
        raise CardError(
            f"{page!r} is no page id of agterm: letters, digits, `_` and `-`"
        )
    return page


def html_file(task: Path, page: str) -> Path:
    return task / CARDS / f"{page_name(page)}.html"


def card_file(task: Path, page: str) -> Path:
    return task / CARDS / f"{page_name(page)}.json"


def end_file(task: Path, page: str) -> Path:
    return task / CARDS / f"{page_name(page)}.end.json"


def questions_of(spec: dict) -> list[dict]:
    """Each question of a spec with the ids the page gives it and its
    options (`runtime/ask.js`)."""
    listed = spec.get("questions")
    out = []
    for number, question in enumerate(listed or [spec], 1):
        options = []
        for index, option in enumerate(question.get("options") or [], 1):
            if isinstance(option, str):
                options.append({"id": option, "label": option})
            else:
                given = option.get("id") or f"o{index}"
                options.append({"id": given, "label": option.get("label") or given})
        mode = question.get("mode")
        if not mode:
            if question.get("controls"):
                mode = "tune"
            elif options:
                mode = "single"
            else:
                mode = "text"
        question_id = question.get("id")
        if not question_id:
            question_id = f"q{number}" if listed else "answer"
        out.append(
            {
                "id": question_id,
                "prompt": question.get("prompt") or spec.get("title") or "",
                "mode": mode,
                "optional": question.get("optional") is True,
                "options": options,
            }
        )
    return out


def fresh_name(path: Path) -> Path:
    """A name beside PATH unique to its writer: the PID, the thread and a random token,
    since the board server's threads share one PID."""
    return path.with_name(
        f"{path.name}.{os.getpid()}.{threading.get_ident()}.{secrets.token_hex(8)}.new"
    )


def write_whole(path: Path, body: bytes) -> None:
    """Write BODY to PATH so that a reader sees the old file or the new one, never
    a part."""
    fresh = fresh_name(path)
    try:
        with fresh.open("xb") as out:
            out.write(body)
        fresh.replace(path)
    finally:
        fresh.unlink(missing_ok=True)


def link_whole(target: Path, body: bytes) -> bool:
    """Write BODY as TARGET only when no file of that name is there, as `link_mark` in
    `project.py` makes a mark: whole under a name unique to its writer (the PID, the
    thread and a random token), then linked to TARGET, which fails when the name is
    there. True when this call made TARGET, False when another writer had. A reader
    never sees a part of it, and a writer that stops leaves no empty name. The one end
    of a card (`end`) and the record of a row's answer (lem_answers) are written so."""
    target.parent.mkdir(exist_ok=True)
    fresh = fresh_name(target)
    try:
        with fresh.open("xb") as out:
            out.write(body)
        os.link(fresh, target)
    except FileExistsError:
        return False
    finally:
        fresh.unlink(missing_ok=True)
    return True


def keep(task: Path, page: str, html: bytes, spec: dict, session: str | None) -> dict:
    """Keep the card PAGE of the task's folder TASK: the page's bytes and what it asks;
    log `card.asked`."""
    (task / CARDS).mkdir(exist_ok=True)
    write_whole(html_file(task, page), html)
    card = {
        "page": page,
        "session": session,
        "at": lem_clock.stamp(),
        "chat": spec.get("chat") is not False,
        "questions": questions_of(spec),
    }
    write_whole(
        card_file(task, page),
        f"{json.dumps(card, ensure_ascii=False, indent=1)}\n".encode(),
    )
    log(task, "card.asked", {"page": page, "prompt": card["questions"][0]["prompt"]})
    return card


def card(task: Path, page: str) -> dict | None:
    """What the card PAGE asks, or None when the task's folder keeps no such card."""
    try:
        return json.loads(card_file(task, page).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as error:
        raise CardError(
            f"{card_file(task, page)} cannot be read as a card ({error})"
        ) from error


def ended(task: Path, page: str) -> dict | None:
    """The end of the card PAGE on record, or None while the card is open."""
    try:
        return json.loads(end_file(task, page).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as error:
        raise CardError(
            f"{end_file(task, page)} cannot be read as the end of a card ({error})"
        ) from error


# One half of a UTF-16 pair, alone in a string: what a page's script sends when it cuts
# a character in two ("🚀".slice(0, 1)), which UTF-8 cannot hold.
HALF = re.compile("[\ud800-\udfff]")


def whole(answer: object) -> object:
    """ANSWER, an answer as JSON reads it, with each half of a UTF-16 pair alone in one
    of its strings in the place of U+FFFD, as a browser's UTF-8 encoder writes it
    (WHATWG Encoding, "UTF-8 encode"): every other character of the answer stays, and
    the answer prints and writes as UTF-8."""
    if isinstance(answer, str):
        return HALF.sub("\ufffd", answer)
    if isinstance(answer, list):
        return [whole(one) for one in answer]
    if isinstance(answer, dict):
        return {whole(key): whole(one) for key, one in answer.items()}
    return answer


def end(
    task: Path,
    page: str,
    status: str,
    source: str,
    answer: dict | None = None,
    **more: object,
) -> tuple[bool, dict]:
    """End the card PAGE of the task's folder TASK, only when no end is on record:
    (True, the record) when this call owns the end, else (False, the end on record).
    STATUS is `answered` (with ANSWER, the JSON the page sends), `dismissed` or
    `closed`; SOURCE is `session` or `board`; MORE are the board's fields (`via`,
    `device`, `agent`). The owner of the end logs `card.answered` or `card.closed`."""
    if status not in STATUSES:
        allowed = ", ".join(STATUSES)
        raise CardError(f"a card ends as {allowed}, not {status!r}")
    if source not in SOURCES:
        allowed = " or ".join(SOURCES)
        raise CardError(f"a card's end comes from {allowed}, not {source!r}")
    if (status == "answered") != (answer is not None):
        raise CardError(
            "an answered card's end holds the answer, and only an answered one's"
        )
    record = {
        "page": page,
        "status": status,
        "from": source,
        "at": lem_clock.stamp(),
        **({} if answer is None else {"answer": whole(answer)}),
        **more,
    }
    target = end_file(task, page)
    if not link_whole(
        target,
        f"{json.dumps(record, ensure_ascii=False, indent=1)}\n".encode(),
    ):
        on_record = ended(task, page)
        if on_record is None:
            raise CardError(
                f"{target} was there and is gone: something removed the end of a card"
            )
        return False, on_record
    fields = {
        "page": page,
        "from": source,
        **({} if status == "answered" else {"status": status}),
        **{key: more[key] for key in ("via", "device") if key in more},
    }
    log(task, "card.answered" if status == "answered" else "card.closed", fields)
    return True, record


def log(task: Path, event: str, fields: dict) -> None:
    """Log EVENT of the task whose folder is TASK in its repository's event log. A log
    that fails is said on stderr: the card's files are the record, and the event only
    tells the board's stream."""
    # the settings' module is large, and only an end or an ask logs
    from lem import project

    try:
        project.append_event(task.parents[3], event, task.name, fields)
    except (OSError, project.SettingsError, lem_state.StateError) as error:
        print(
            (
                f"lem: the card {fields.get('page')} of {task.name} is on record, but "
                f"its event {event} is not in the log: {error}"
            ),
            file=sys.stderr,
        )


def words(answer: dict | None) -> str:
    """The answer the page sent, in a few words: the labels picked, else what kind of
    answer it was."""
    if not isinstance(answer, dict):
        return "an answer"
    if answer.get("status") == "chat":
        return "a wish to talk"
    labels = [
        str(label)
        for one in (answer.get("answers") or {}).values()
        if isinstance(one, dict)
        for label in one.get("labels") or []
    ]
    if labels:
        return ", ".join(labels)
    texts = [
        one
        for one in (answer.get("answers") or {}).values()
        if isinstance(one, dict) and one.get("text")
    ]
    return "an answer in words" if texts else "an answer"


def local_time(stamp: str | None) -> str:
    if not isinstance(stamp, str):
        return str(stamp)
    try:
        return (
            datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ")
            .replace(tzinfo=UTC)
            .astimezone()
            .strftime("%H:%M")
        )
    except ValueError:
        return stamp


def took_effect(record: dict) -> str:
    """What the end on record says, in one sentence: "B was taken on the board at 15:42,
    from the phone"."""
    at = local_time(record.get("at"))
    where = "on the board" if record.get("from") == "board" else "in the session"
    if record.get("status") == "answered":
        device = (
            f", from the {record['device']}"
            if record.get("from") == "board" and record.get("device")
            else ""
        )
        return f"{words(record.get('answer'))} was taken {where} at {at}{device}"
    how = "dismissed" if record.get("status") == "dismissed" else "closed"
    return f"the card was {how} {where} at {at}"
