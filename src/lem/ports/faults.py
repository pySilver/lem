"""What a port raises when the tool behind it could not answer: git, gh or agtermctl did not
run, timed out, or said something no port reads. Nothing is kept on such a fault, and the step
or the duty tries again later (`landing.md` E, "Transport fault")."""

from lem.kernel.errors import Fault


class Unanswered(Fault):
    """A tool behind a port gave no usable answer: its name, and what it said."""

    def __init__(self, tool: str, said: str) -> None:
        """Keep the tool and its words."""
        super().__init__(f"{tool}: {said}")
        self.tool = tool
        self.said = said
