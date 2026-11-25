"""What a command of Lem ends with when it does not succeed."""


class Refusal(Exception):
    """A step that may not run now: a short code, why, and the fix that names the way on."""

    def __init__(self, code: str, why: str, fix: str) -> None:
        """Keep the three parts of the refusal."""
        super().__init__(why)
        self.code = code
        self.why = why
        self.fix = fix


class Fault(Exception):
    """A failure of Lem itself: its traceback goes to `lem.log`, the owner reads one line."""
