"""`LookingTerminal`: the core's `FakeTerminal` with the looks a task's session needs beside the
port (`app/sessions/beside.py`): a name, the program in each main pane, and the mailbox, which
keeps each line told until the test takes it."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from msgspec.structs import replace

from fakes.terminal import FakeTerminal
from lem.ports.terminal import Opening, Pane

if TYPE_CHECKING:
    from lem.app.sessions.beside import Foreground

# The program a session Lem opened runs: the agent of its launch line.
AGENT = ("/bin/zsh", "-l", "-c", "LEM_TASK=x claude 'Read x and follow it.'")
CALLER = Pane(id="S-MINE", name="main", workspace="W-1")


@dataclass
class LookingTerminal(FakeTerminal):
    """Sessions, with the program in each main pane, the mailbox, and the names given."""

    grounds: dict[str, Foreground] = field(default_factory=dict)
    renamed: list[tuple[str, str]] = field(default_factory=list)
    taken: set[str] = field(default_factory=set)

    def open(self, opening: Opening) -> str:
        made = super().open(opening)
        self.grounds[made] = AGENT
        return made

    def rename(self, session: str, name: str) -> None:
        pane = self.known(session)
        self.panes[session] = replace(pane, name=name)
        self.renamed.append((session, name))

    def foregrounds(self) -> dict[str, Foreground]:
        return {key: self.grounds.get(key, ()) for key in self.panes}

    def waiting(self, session: str, line: str) -> bool:
        self.known(session)
        return (session, line) in self.told and line not in self.taken

    def end_agent(self, session: str) -> None:
        """The agent of the session ends, and leaves its shell."""
        self.grounds[session] = ()


def with_caller() -> LookingTerminal:
    """A terminal with the owner's own session, in which the command runs."""
    return LookingTerminal(panes={CALLER.id: CALLER})
