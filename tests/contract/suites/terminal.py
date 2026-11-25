"""The contract of the `Terminal` port: `FakeTerminal` now, the agterm adapter when `sessions`
builds it (against a stand-in for agtermctl)."""

from typing import TYPE_CHECKING

import pytest

from lem.ports.terminal import Opening, Unreadable

if TYPE_CHECKING:
    from pathlib import Path

    from lem.ports.terminal import Terminal


class TerminalContract:
    """The cases every implementation of `Terminal` passes."""

    def terminal(self, folder: Path) -> Terminal:
        """A terminal with no session yet."""
        raise NotImplementedError

    def test_an_opened_session_is_listed_and_never_selected(
        self, tmp_path: Path
    ) -> None:
        terminal = self.terminal(tmp_path)
        made = terminal.open(
            Opening(name="fix-the-login", cwd=str(tmp_path), command=("claude",))
        )
        listed = terminal.sessions()
        assert not isinstance(listed, Unreadable)
        assert [(pane.id, pane.name, pane.selected) for pane in listed] == [
            (made, "fix-the-login", False)
        ]

    def test_a_companion_of_a_session_that_is_gone_is_a_fault(
        self, tmp_path: Path
    ) -> None:
        terminal = self.terminal(tmp_path)
        with pytest.raises(Exception, match="no session"):
            terminal.open(
                Opening(
                    name="c", cwd=str(tmp_path), command=("x",), companion_of="gone"
                )
            )

    def test_a_line_or_a_mark_to_a_gone_session_is_a_fault(
        self, tmp_path: Path
    ) -> None:
        terminal = self.terminal(tmp_path)
        made = terminal.open(Opening(name="t", cwd=str(tmp_path), command=("x",)))
        terminal.tell(made, "go on")
        terminal.mark(made, "working")
        terminal.close(made, when_unselected=False)
        with pytest.raises(Exception, match="no session"):
            terminal.tell(made, "go on")

    def test_a_close_when_unselected_keeps_the_session_he_looks_at(
        self, tmp_path: Path
    ) -> None:
        terminal = self.terminal(tmp_path)
        made = terminal.open(Opening(name="t", cwd=str(tmp_path), command=("x",)))
        terminal.select(made)
        terminal.close(made, when_unselected=True)
        listed = terminal.sessions()
        assert not isinstance(listed, Unreadable)
        assert [pane.id for pane in listed] == [made]
