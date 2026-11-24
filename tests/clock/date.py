"""A `date` whose clock moves on between two calls, for a block that must name a dated
thing once: what tests/clock/date runs, on the suites' Python (tests/python.sh).

With this folder first on PATH and LEM_TEST_DATE_STEP=SECONDS, each `date -u +FORMAT`
reads the clock that many seconds later than the call before it, as if a minute or a UTC
midnight fell between the two: a block that makes a dated name with one call and looks
for it with another finds nothing. The count of calls is kept in
$XDG_CONFIG_HOME/date-calls, the folder tests/lib.sh makes for each run and removes at
its end. Every other call, and every call without the variable, is the system's own
`date`. `PATH=tests/clock:$PATH LEM_TEST_DATE_STEP=86460 bash tests/lem-state.sh` holds
that the prune's block looks for the nap and the experts folders it made.
"""

import os
import sys
import time
from pathlib import Path

here = Path(__file__).resolve().parent
args = sys.argv[1:]
step = os.environ.get("LEM_TEST_DATE_STEP")

if step and len(args) == 2 and args[0] == "-u" and args[1].startswith("+"):
    home = os.environ.get("XDG_CONFIG_HOME")
    if not home:
        sys.exit(
            "tests/clock/date: LEM_TEST_DATE_STEP needs the run's own XDG_CONFIG_HOME, "
            "which tests/lib.sh exports"
        )
    calls = Path(home) / "date-calls"
    done = int(calls.read_text()) if calls.exists() else 0
    calls.write_text(str(done + 1))
    print(time.strftime(args[1][1:], time.gmtime(time.time() + done * int(step))))
    sys.exit(0)

for folder in os.environ.get("PATH", "").split(os.pathsep):
    found = Path(folder or ".", "date")
    if found.is_file() and os.access(found, os.X_OK) and found.resolve().parent != here:
        os.execv(found, [str(found), *args])
sys.exit("tests/clock/date: no other date on PATH")
