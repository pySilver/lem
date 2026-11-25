"""The rows of this machine's settings: the load gate, the handoff's tokens and the Jev key,
which the correction queue needs where the machine turns it on."""

from typing import TYPE_CHECKING

import pytest

from lem.cli.doctor.jev_row import jev_row
from lem.cli.doctor.machine_rows import handoff_row, load_row
from lem.cli.doctor.rows import gathered
from unit.settings.doctor.stage import Stage, named

if TYPE_CHECKING:
    from pathlib import Path

KEY = "sk-or-v1-a-key-nobody-reads"


@pytest.fixture
def stage(tmp_path: Path) -> Stage:
    """A machine of its own for each case."""
    return Stage(tmp_path)


def machine(stage: Stage, text: str) -> None:
    """This machine's settings file."""
    stage.write("config/lem/machine.toml", text)


def test_the_load_gate_is_lems_default_a_number_set_here_or_away(stage: Stage) -> None:
    default = load_row(stage.look())
    assert (default.need, default.found) == ("optional", True)
    assert default.detail is not None
    assert "below a load average of 40, Lem's default" in default.detail
    assert default.line == "lem settings set load.start N --machine"
    machine(stage, "[load]\nstart = 12.5\n")
    written = load_row(stage.look())
    assert written.detail is not None
    assert "below a load average of 12.5; it is" in written.detail
    machine(stage, "[load]\nstart = 0\n")
    away = load_row(stage.look())
    assert away.found is False
    assert (away.detail or "").startswith("no gate on this machine (load.start = 0)")
    assert "lem settings set load.start N --machine" in (away.without_it or "")


def test_the_handoff_tokens_are_the_default_a_number_set_here_or_claude_codes_own(
    stage: Stage,
) -> None:
    assert handoff_row(stage.look()).detail == "handoff tokens: 600000 (default)"
    machine(stage, "[handoff]\ntokens = 250000\n")
    row = handoff_row(stage.look())
    assert row.detail == (
        f"handoff tokens: 250000 (set in {stage.lem_home / 'machine.toml'})"
    )
    assert row.line == "lem settings set handoff.tokens N --machine"
    machine(stage, "[handoff]\ntokens = 0\n")
    assert (handoff_row(stage.look()).detail or "").startswith(
        "handoff tokens: 0, so Lem"
    )


def test_a_machine_file_that_does_not_read_is_the_rows_detail_and_fails_nothing(
    stage: Stage,
) -> None:
    machine(stage, "[load\n")
    rows = gathered(stage.look())
    for name in ("load gate", "handoff tokens", "board door"):
        row = named(rows, name)
        assert (row.need, row.found) == ("optional", False)
        assert "machine.toml is not TOML" in (row.detail or ""), name
    assert "lem on PATH" in [row.name for row in rows]


def test_the_jev_key_row_names_the_one_variable_and_its_provider_and_no_key(
    stage: Stage,
) -> None:
    absent = jev_row(stage.look(JEV_KEY=KEY))
    assert (absent.need, absent.found) == ("optional", False)
    assert absent.detail == (
        "JEV_API_KEY is not set, and it is the one name Lem reads for the key"
    )
    said = absent.without_it or ""
    assert "OpenRouter" in said
    assert "Jev: not asked (no key)" in said
    given = jev_row(stage.look(JEV_API_KEY=KEY))
    assert (given.found, given.detail) == (True, "JEV_API_KEY, to OpenRouter")
    other = jev_row(stage.look(JEV_API_KEY=KEY, JEV_API_URL="https://x.example/v1"))
    assert other.detail == "JEV_API_KEY, to https://x.example/v1"
    assert KEY not in str([absent, given, other])
    assert "lem jev" not in str([absent, given, other])


def test_where_the_machine_collects_corrections_the_key_is_required_in_a_lem_repository(
    stage: Stage,
) -> None:
    checkout = stage.repository()
    machine(stage, "[corrections]\ncollect = true\n")
    row = jev_row(stage.look(checkout))
    assert (row.need, row.found) == ("required", False)
    assert "machine.toml" in (row.detail or "")
    assert "collect = true under [corrections]" in (row.detail or "")
    assert "lem settings set corrections.collect no --machine" in (row.without_it or "")
    assert jev_row(stage.look(checkout, JEV_API_KEY=KEY)).found
    assert jev_row(stage.look()).need == "optional"
    machine(stage, "[corrections]\ncollect = false\n")
    assert jev_row(stage.look(checkout)).need == "optional"
    machine(stage, "")
    assert jev_row(stage.look(checkout)).need == "optional"
