"""The corrections no retro decided about, grouped by the owner's words: one sentence sent to
eight sessions is one group of eight, not eight things to judge (`corrections.unreviewed` on
`main`). An entry is known by its moment, its session and its group together: two messages of one
second in one session are two entries."""

import hashlib
from typing import TYPE_CHECKING

from lem.addons.corrections import queue
from lem.kernel.errors import Refusal
from lem.records.corrections import Correction, CorrectionReview

if TYPE_CHECKING:
    from pathlib import Path

type Groups = dict[str, list[Correction]]


def group_id(owner: str) -> str:
    """The group of the owner's words: their digest, with the spaces made one."""
    words = " ".join(owner.split()).encode()
    return hashlib.sha1(words, usedforsecurity=False).hexdigest()[:8]


def unreviewed(state: Path) -> Groups:
    """Every entry of the queue no retro decided about, by its group, oldest first."""
    reviewed = {
        (review.at, review.session, review.group)
        for review in queue.lines(state / queue.REVIEWS, CorrectionReview)
    }
    groups: Groups = {}
    for entry in queue.lines(state / queue.QUEUE, Correction):
        gid = group_id(entry.owner)
        if (entry.at, entry.session, gid) not in reviewed:
            groups.setdefault(gid, []).append(entry)
    return groups


def group_of(state: Path, gid: str) -> list[Correction]:
    """The entries of the unreviewed group `gid`; refused when there is none."""
    entries = unreviewed(state).get(gid)
    if not entries:
        raise Refusal(
            "no-group",
            f"there is no unreviewed group {gid}",
            "lem corrections list gives the ids",
        )
    return entries


def trimmed(text: str, limit: int) -> str:
    """`text` on one line, cut at `limit` characters with the count of the rest."""
    flat = " ".join(text.split())
    if len(flat) <= limit:
        return flat
    shown, rest = flat[:limit], len(flat) - limit
    return f"{shown} ... [{rest} more characters]"
