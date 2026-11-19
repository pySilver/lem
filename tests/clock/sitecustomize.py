"""A clock that a minute passed on, for a test that must not read its ages from the real clock.

With this folder on PYTHONPATH and LEM_TEST_LATER=SECONDS, a Python process that runs with
`--list` (the task picker's list) reads `datetime.now()` that many seconds late, as if a minute
boundary fell between a block's state writes and its list. Every other process reads the real
clock. `PYTHONPATH=tests/clock LEM_TEST_LATER=60 bash tests/lem-picker.sh` holds that the
picker's block fixes every age it expects.
"""

import datetime
import os
import sys

_later = os.environ.get("LEM_TEST_LATER")

if _later and "--list" in sys.argv:
    _shift = datetime.timedelta(seconds=int(_later))

    class _Later(datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            return super().now(tz) + _shift

    datetime.datetime = _Later
