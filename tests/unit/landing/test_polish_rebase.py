"""A rebase that drops a patch must also drop the old polish start."""

from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

from msgspec.structs import replace

from lem.app.landing import base_polish, polish, polish_done
from lem.model.landing import base_kept
from lem.records.landing.start import Polished
from unit.landing.proposals import full, with_landing
from unit.landing.worlds import BASE, BASED, MOMENT, TIP, world

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

    from lem.app.landing.frame import Context

START = "a" * 40
NEW_BASE = "b" * 39 + "c"
REBASED = "c" * 40


def test_a_dropped_patch_makes_polish_start_at_the_rebased_tip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    record = with_landing(
        full(), polished=Polished(before=START, after=TIP, at=MOMENT, commits=1)
    )
    git = SimpleNamespace(
        merge_base=lambda *_: BASE,
        commits=lambda _, older, tip: (
            (START, TIP) if (older, tip) == (BASE, TIP) else (REBASED,)
        ),
        is_ancestor=lambda _, older, tip: older == tip or (older, tip) == (START, TIP),
    )
    context = SimpleNamespace(
        record=record,
        world=world(base=NEW_BASE),
        worktree=tmp_path,
        ports=SimpleNamespace(git=git),
    )
    landing = cast("Context", context)
    remapped = base_polish.polish(landing, REBASED, TIP)
    based = replace(BASED, tip=REBASED, base=NEW_BASE)
    context.record = base_kept.kept(record, based, remapped)
    context.world = world(base=NEW_BASE, tip=REBASED)
    context.write = lambda record, change: setattr(context, "record", change(record))
    monkeypatch.setattr(polish.polish_brief, "brief_of", lambda _, kept: kept)
    monkeypatch.setattr(polish_done, "touched", lambda *_: ())

    polish.started(landing)
    assert polish_done.before_of(landing) == REBASED
