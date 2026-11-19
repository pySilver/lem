"""What a landing reads of a repository before its step, as calls of the functions it calls with the
settings it loaded once: `may_land`, which `lem project may-land` prints. Whether the base branch
exists is a fact only git shows, and tests/lem-settings.sh checks it in a real repository.

    python3 -B -m unittest discover -s tests/unit
"""

import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "lem" / "scripts"))
import project  # noqa: E402

# A checkout that is not on disk: the rules resolve paths under it and find nothing there.
ROOT = Path("/lem-unit/repo")


def settings(*lines: str) -> dict:
    """The settings of a main checkout on its base branch whose file holds these lines."""
    raw = project.settings_of("\n".join(lines) + "\n", ROOT / project.SETTINGS, tuple(project.TABLES))
    return project.decide(ROOT, ROOT, raw, {}, raw, None)


class MayLand(unittest.TestCase):
    """The refusals of `may-land` that the settings decide, before git is asked for the branch."""

    def refused(self, target: str, *lines: str) -> str:
        with self.assertRaises(project.SettingsError) as caught:
            project.may_land(settings(*lines), target)
        return str(caught.exception)

    def test_a_protected_branch(self):
        self.assertIn("'release' is protected", self.refused("release", "[branch]", 'base = "main"', 'protected = ["release"]'))

    def test_settings_that_name_no_base(self):
        self.assertIn("names no branch.base", self.refused("main"))

    def test_a_branch_that_is_not_the_base(self):
        self.assertIn("land on 'main', not on 'feature'", self.refused("feature", "[branch]", 'base = "main"'))


class TrackOf(unittest.TestCase):
    """The track of a task, from the newest of its state lines that tells it (state.md, newest block first)."""

    def test_an_interview_above_the_fast_tracks_builder_is_the_standard_track(self):
        # `/lem standard-track` of a task whose small change had started: its interview waits now
        state = "2026-11-19T10:00Z held: the interview waits for the owner\ntype: feat, because the export gets a note\n\n2026-11-19T09:50Z building: small change: one builder"
        self.assertEqual(project.track_of(state), "standard")

    def test_the_fast_tracks_builder_and_a_lead(self):
        self.assertEqual(project.track_of("2026-11-19T09:50Z building: small change: one builder"), "fast")
        self.assertEqual(project.track_of("2026-11-19T09:50Z building: lead: builder\n\n2026-11-19T09:40Z building: small change: one builder"), "standard")
        self.assertIsNone(project.track_of("2026-11-19T09:50Z queued: it waits for a free place"))


if __name__ == "__main__":
    unittest.main()
