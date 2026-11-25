"""Read the review agent's answer once and publish the exact bytes Lem accepts."""

from typing import TYPE_CHECKING

import msgspec

from lem.app.landing import review_files
from lem.kernel import files
from lem.kernel.errors import Refusal
from lem.model.landing.review_said import Said

if TYPE_CHECKING:
    from pathlib import Path

FORM = (
    "write the record as prompts/review.md, step 8, says: attempt, tip, kind, answered, and of "
    "ran, left_out, silent, bar, must_fix, should, nit, outside, careful and careful_why what "
    "applies"
)
ACCEPTED = "review-records"
type Answer = tuple[Said, bytes]


def decoded(body: bytes) -> Answer:
    """Decode the answer and keep the bytes that the decoder read."""
    return msgspec.json.decode(body, type=Said), body


def said(path: Path) -> Answer:
    """The review agent's record and its bytes; bad JSON is refused with its form."""
    try:
        return decoded(path.read_bytes())
    except (OSError, msgspec.DecodeError) as error:
        raise Refusal(
            "review-file", f"{path} is not the review's record: {error}", FORM
        ) from error


def active(folder: Path, slug: str, given: str) -> Answer:
    """Read the submitted answer, which must be the agent's own file."""
    path = review_files.task_file(given, folder)
    archived = review_files.landing_before(folder, path, slug)
    if archived is not None:
        raise archived
    kept = review_files.looks_of(folder / ACCEPTED, path)
    if any(answer.is_relative_to(root) for root, answer in kept):
        raise Refusal(
            "kept-review",
            f"{path} is a review Lem accepted already",
            f"lem land read {slug} names the review whose answer the agent submits",
        )
    return said(path)


def published(folder: Path, body: bytes) -> str:
    """Publish the accepted bytes at a path of their own, relative to the task's folder."""
    named = f"{ACCEPTED}/review-{files.digest(body)}.json"
    files.publish(folder / named, body)
    return named
