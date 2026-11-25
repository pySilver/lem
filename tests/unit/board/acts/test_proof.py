"""The board's ledger points to a check of the act each row names."""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
FATES = ROOT / "tests/ledger/fates/board-acts.tsv"
SURFACES = ROOT / "docs/plans/2026-11-25-lem-built-again/surfaces.md"
CONFIRM = (
    "check:tests/lem-board-act.sh:"
    "a-merge-runs-only-from-its-confirm-step-whic-19fa3f5502064637"
)


def proof_of(key: str) -> str:
    with FATES.open() as stream:
        return next(
            row["proof"]
            for row in csv.DictReader(stream, delimiter="\t")
            if row["id"] == key
        )


def test_the_merge_confirmation_row_cites_the_refusal_without_confirmation() -> None:
    assert proof_of(CONFIRM).endswith(
        "test_a_merge_runs_only_from_its_confirm_step_and_for_the_tip_proposed_now"
        "[fields0-A merge runs only from its confirm step]"
    )


def test_the_board_surface_has_no_old_release_approval() -> None:
    act = next(
        line for line in SURFACES.read_text().splitlines() if "Plan Build/Drop" in line
    )
    assert "prior-release Approve" not in act
