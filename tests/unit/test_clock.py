"""clock.py's rules: each of the three forms of a UTC time, of a moment given as a
datetime or as seconds, or of now; a moment given is written as it is.

    .venv/bin/python -B -m unittest discover -s tests/unit
"""

import sys
import unittest
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from pathlib import Path
from typing import Self
from unittest import mock

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from lem import clock as lem_clock

# the late `date` of tests/clock, which a block puts first on PATH
CLOCK = Path(__file__).resolve().parents[1] / "clock"
MOMENT = datetime(2026, 11, 24, 10, 18, 18, 987654, tzinfo=UTC)


class Forms(unittest.TestCase):
    def test_a_datetime_in_each_form(self) -> None:
        self.assertEqual(lem_clock.stamp(MOMENT), "2026-11-24T10:18:18Z")
        self.assertEqual(lem_clock.stamp_minute(MOMENT), "2026-11-24T10:18Z")
        self.assertEqual(lem_clock.iso(MOMENT), "2026-11-24T10:18:18+00:00")

    def test_seconds_with_a_fraction_and_whole_ones_are_the_same_utc_moment(
        self,
    ) -> None:
        seconds = MOMENT.timestamp()
        for given in (seconds, int(seconds)):
            self.assertEqual(lem_clock.stamp(given), "2026-11-24T10:18:18Z")
            self.assertEqual(lem_clock.stamp_minute(given), "2026-11-24T10:18Z")
            self.assertEqual(lem_clock.iso(given), "2026-11-24T10:18:18+00:00")

    def test_none_is_now_in_utc(self) -> None:
        before = datetime.now(UTC).replace(microsecond=0)
        said = {
            "stamp": lem_clock.stamp(),
            "minute": lem_clock.stamp_minute(),
            "iso": lem_clock.iso(),
        }
        after = datetime.now(UTC)
        self.assertRegex(said["stamp"], r"\A\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ\Z")
        self.assertRegex(said["minute"], r"\A\d{4}-\d\d-\d\dT\d\d:\d\dZ\Z")
        self.assertRegex(said["iso"], r"\A\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\+00:00\Z")
        read = datetime.strptime(said["stamp"], "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=UTC
        )
        self.assertTrue(before <= read <= after)

    def test_a_moment_in_another_zone_or_none_is_written_as_it_is(self) -> None:
        east = MOMENT.astimezone(timezone(timedelta(hours=2)))
        self.assertEqual(lem_clock.stamp(east), "2026-11-24T12:18:18Z")
        self.assertEqual(lem_clock.iso(east), "2026-11-24T12:18:18+02:00")
        plain = MOMENT.replace(tzinfo=None)
        self.assertEqual(lem_clock.stamp(plain), "2026-11-24T10:18:18Z")
        self.assertEqual(lem_clock.iso(plain), "2026-11-24T10:18:18")

    def test_the_clock_of_tests_clock_moves_now_and_a_moment_made_before_stays(
        self,
    ) -> None:
        class Later(datetime):
            @classmethod
            def now(cls, tz: tzinfo | None = None) -> Self:
                return cls(2030, 1, 2, 3, 4, 5, tzinfo=tz)

        with mock.patch.object(lem_clock, "datetime", Later):
            self.assertEqual(lem_clock.stamp(), "2030-01-02T03:04:05Z")
            self.assertEqual(lem_clock.stamp(MOMENT), "2026-11-24T10:18:18Z")


class LateDate(unittest.TestCase):
    """tests/clock/date runs on the suites' Python, the checkout's .venv
    (tests/python.sh), never on a python3 that comes first on PATH."""

    def test_it_runs_with_a_python3_first_on_path_that_fails(self) -> None:
        import subprocess
        import tempfile

        with tempfile.TemporaryDirectory() as folder:
            standin = Path(folder) / "bin"
            standin.mkdir()
            python3 = standin / "python3"
            python3.write_text("#!/bin/sh\necho 'another python3' >&2\nexit 9\n")
            python3.chmod(0o755)
            ran = subprocess.run(
                [str(CLOCK / "date"), "-u", "+%Y-%m-%d"],
                env={
                    "PATH": f"{standin}:{CLOCK}:/usr/bin:/bin",
                    "LEM_TEST_DATE_STEP": "86400",
                    "XDG_CONFIG_HOME": folder,
                },
                capture_output=True,
                text=True,
                check=False,
            )
            # the stand-in's own count of its calls: the late clock answered, not the
            # system's date
            counted = Path(folder) / "date-calls"
            calls = counted.read_text() if counted.exists() else None
        self.assertEqual((ran.returncode, ran.stderr, calls), (0, "", "1"))
        self.assertRegex(ran.stdout, r"\A\d{4}-\d{2}-\d{2}\n\Z")


if __name__ == "__main__":
    unittest.main()
