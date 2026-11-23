"""limit.py SECONDS NAME -- COMMAND...: run COMMAND with a time limit, for the runners
of the suites.

COMMAND runs in a process group of its own, with this process's stdin, stdout and
stderr, and the exit is COMMAND's. When it runs longer than SECONDS, the group gets
TERM, and 10 seconds later KILL for whatever of it is still there; then the line `FAIL
NAME did not end in SECONDS s, and was stopped` is printed and the exit is 124. A
suite's EXIT trap runs on TERM, so a suite cut off this way still removes its folder. A
TERM or an INT to this process goes on to the group.
"""

import contextlib
import os
import signal
import subprocess
import sys

GRACE = 10


def signal_group(group: int, sign: int) -> None:
    with contextlib.suppress(ProcessLookupError):
        os.killpg(group, sign)


def main() -> int:
    args = sys.argv[1:]
    if len(args) < 4 or args[2] != "--" or not args[0].isdigit():
        sys.exit("limit.py: usage: limit.py SECONDS NAME -- COMMAND...")
    seconds, name, command = int(args[0]), args[1], args[3:]
    proc = subprocess.Popen(command, start_new_session=True)
    for sign in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sign, lambda got, _frame: signal_group(proc.pid, got))
    try:
        code = proc.wait(timeout=seconds)
        # a suite ended by a signal exits as a shell says it: 128 and the
        # signal's number
        return 128 - code if code < 0 else code
    except subprocess.TimeoutExpired:
        pass
    signal_group(proc.pid, signal.SIGTERM)
    with contextlib.suppress(subprocess.TimeoutExpired):
        proc.wait(timeout=GRACE)
    signal_group(proc.pid, signal.SIGKILL)
    proc.wait()
    print(f"FAIL {name} did not end in {seconds} s, and was stopped", flush=True)
    return 124


if __name__ == "__main__":
    sys.exit(main())
