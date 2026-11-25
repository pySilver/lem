"""The review's files on the map: a review and its record, a round of the review tool with its
report as the document and the rest of its archive as working files, and the files of the tool's
own run beside them."""

import re

from lem.board.views.artifacts.spots import CHECKS, REVIEW, WORK, Spot

REVIEW_FILE = re.compile(r"reviews/review-0*(\d+)\.(md|json)")
ARCHIVE = re.compile(r"reviews/[^/]+/(\d+-[^/]+)/(.+)")
RUN = re.compile(r"reviews/[a-z]+-(\d+-[^/]+)\.(json|log)")
ROUND = "Review round"


def review(path: str) -> Spot | None:
    """`reviews/review-N.md` and its record `.json`."""
    found = REVIEW_FILE.fullmatch(path)
    if found is None:
        return None
    if found[2] == "md":
        return Spot(group=REVIEW, title=f"Review {found[1]}")
    stem = path.removesuffix(".json")
    return Spot(
        group=REVIEW,
        title=f"Review {found[1]} (record)",
        role="record",
        of=f"{stem}.md",
        label="record",
        tab=CHECKS,
    )


def archive(path: str) -> Spot | None:
    """A file of one round of the review tool, `reviews/TASK/NN-LABEL/...`."""
    found = ARCHIVE.fullmatch(path)
    if found is None:
        return None
    named = f"{ROUND} {found[1]}"
    if found[2] == "report.md":
        return Spot(group=REVIEW, title=named)
    return Spot(group=WORK, title=found[2], role="work", folder=named)


def run(path: str) -> Spot | None:
    """A file of the review tool's own run, `reviews/TOOL-NN-LABEL.json`."""
    found = RUN.fullmatch(path)
    if found is None:
        return None
    name = path.rpartition("/")[2]
    named = f"{ROUND} {found[1]}"
    return Spot(group=WORK, title=name, role="work", folder=named)
