"""Prepare a message before saving it, and withdraw with its own stable key."""

from secrets import token_hex
from typing import TYPE_CHECKING

from lem.addons.inbox import body, note
from lem.addons.inbox.messages import Payload
from lem.addons.inbox.records import Entry

if TYPE_CHECKING:
    from lem.addons.inbox.records import Wait
    from lem.addons.inbox.source import RowFacts

WITHDRAWN = "This question no longer waits for the owner."
REPLACED = (
    "This question no longer applies. A newer question will follow in this thread."
)


def message(
    wait: Wait,
    found: RowFacts,
    project: str,
    link: str,
    plan: str | None,
) -> Entry:
    """Build the note or question and include the task's own board link."""
    attachment = plan if wait.session and wait.kind == "plan" else None
    words = body.question(found, attachment) if wait.session else note.note(found)
    key = f"lem-{wait.key}-{token_hex(6)}"
    payload = Payload(
        body=f"{words}\n\n[Open the task on the board]({link})",
        idempotency_key=key,
        project_path=project,
        thread=wait.task,
        subject=f"{wait.task}: {wait.kind}",
        attachments=(attachment,) if attachment else (),
    )
    return Entry(wait=wait, key=key, payload=payload)


def withdrawal(entry: Entry, *, replaced: bool) -> Payload:
    """Withdraw the same question as the session that sent it."""
    message_id = entry.sent.message_id if entry.sent else ""
    return Payload(
        body=REPLACED if replaced else WITHDRAWN,
        idempotency_key=f"{entry.key}-withdrawn",
        reply_to=message_id,
        supersedes=(message_id,),
    )


def answered(message_id: str, why: str) -> bool:
    """Only an Inbox refusal about this closed question counts as an answer."""
    sentence = f"supersedes {message_id}: that message has no open question"
    if not why.startswith("invalid_supersedes: "):
        return False
    return f"{sentence}." in why or f"{sentence}s." in why
