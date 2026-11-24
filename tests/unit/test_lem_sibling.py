"""sibling.py's `checked`: a sibling that failed is the caller's own refusal, of the
class it names, with the sibling's message less its name, unless the caller reads the
exit itself; what a sibling that succeeded wrote on stderr is said again. The sibling is
a stand-in module in the place of `project`'s, which `checked` runs in this process.

    python3 -B -m unittest discover -s tests/unit
"""

import contextlib
import io
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from lem import sibling as lem_sibling  # noqa: E402 - after the line that puts src on sys.path


def main(argv: list[str]) -> None:
    """The `main(argv)` of a sibling in the form a call in this process needs: it says
    on stderr and exits as its first argument asks."""
    word = argv[2]
    if word == "fails":
        sys.exit("project.py: no task 'x'; make it first")
    if word == "silent":
        sys.exit(3)
    print("out")
    if word == "says":
        print("project.py: settings read from main", file=sys.stderr)


class Refused(Exception):
    pass


class Checked(unittest.TestCase):
    def setUp(self) -> None:
        made = tempfile.TemporaryDirectory()
        self.addCleanup(made.cleanup)
        self.folder = Path(made.name)
        standin = types.SimpleNamespace(main=main)
        for patch in (
            mock.patch.object(lem_sibling, "loaded", lambda name: standin),
            mock.patch.object(lem_sibling, "in_form", lambda name: True),
        ):
            patch.start()
            self.addCleanup(patch.stop)

    def call(self, *args: str, check: bool = True) -> tuple[object, str]:
        said = io.StringIO()
        with contextlib.redirect_stderr(said):
            ran = lem_sibling.checked(
                "project", self.folder, *args, error=Refused, check=check
            )
        return ran, said.getvalue()

    def test_a_failure_is_the_callers_class_with_the_message_less_the_name(
        self,
    ) -> None:
        with self.assertRaises(Refused) as caught:
            self.call("fails")
        self.assertEqual(str(caught.exception), "no task 'x'; make it first")

    def test_a_failure_with_no_message_names_the_command(self) -> None:
        with self.assertRaises(Refused) as caught:
            self.call("silent")
        self.assertEqual(str(caught.exception), "project.py silent failed")

    def test_with_check_off_a_failure_comes_back_and_nothing_is_said(self) -> None:
        ran, said = self.call("fails", check=False)
        self.assertEqual(getattr(ran, "returncode", None), 1)
        self.assertEqual(said, "")

    def test_a_success_comes_back_and_its_stderr_is_said_again(self) -> None:
        ran, said = self.call("says")
        self.assertEqual(getattr(ran, "stdout", None), "out\n")
        self.assertEqual(said, "project.py: settings read from main\n")
        _, quiet = self.call("ok")
        self.assertEqual(quiet, "")


if __name__ == "__main__":
    unittest.main()
