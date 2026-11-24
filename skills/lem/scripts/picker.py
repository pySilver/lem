"""The task picker's old place: a keymap line that `lem doctor` printed before it gave
`bin/lem picker` names this file, mostly in Lem's marketplace clone
(`PLUGINS/marketplaces/NAME`), and such lines stay on the machines that have them. The
picker is the module `picker` of Lem's package now, so this file runs nothing of its
own: it becomes the `bin/lem picker` of the plugin's folder it sits in, with the same
arguments, which in the clone runs the newest installed release.

It loads under any python3, the system's 3.9 on a Mac too, since `bin/lem` finds the
newer Python itself, and it imports nothing of Lem's.
"""

import os
import sys
from pathlib import Path

# this file is ROOT/skills/lem/scripts/picker.py: the plugin's folder is three up
os.execv(
    sys.executable,
    [
        sys.executable,
        str(Path(os.path.realpath(__file__)).parents[3] / "bin" / "lem"),
        "picker",
        *sys.argv[1:],
    ],
)
