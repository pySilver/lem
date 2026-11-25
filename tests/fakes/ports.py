"""`Ports` of fakes for a use case's test: the git and the forge the test made, and a fresh fake
of every other port unless the test names its own."""

from typing import TYPE_CHECKING

from fakes.harness import FakeHarness
from fakes.outside import FakeJudge, FakeTracker, RecordingNotifier
from fakes.terminal import FakeTerminal
from lem.app.wiring import Ports

if TYPE_CHECKING:
    from fakes.forge import LocalForge
    from fakes.git import ModelGit


def fake_ports(
    git: ModelGit,
    forge: LocalForge,
    terminal: FakeTerminal | None = None,
    harness: FakeHarness | None = None,
) -> Ports:
    """The ports over `git` and `forge`, with fresh fakes for the rest."""
    return Ports(
        git=git,
        forge=forge,
        terminal=terminal or FakeTerminal(),
        harness=harness or FakeHarness(),
        tracker=FakeTracker(),
        notifier=RecordingNotifier(),
        judge=FakeJudge(),
    )
