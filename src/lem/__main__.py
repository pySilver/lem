"""The one entry of Lem's package: `python -B src/lem/__main__.py NAME ARGS...` runs the
module that NAME stands for, a name of `lem NAME` or one of the commands `lem-ask` and
`lem-jev` (`names`), with ARGS as they came. `bin/lem` becomes this, and so does every
command of Lem that starts another as a process of its own.

The module runs as a script ran before it was one of this package: as `__main__`, with
its own `if __name__ == "__main__":` lines, and `sys.argv` holds its file and ARGS. Its
stdin, stdout, stderr and exit status are the module's own.

Run by its path, this file puts `src`, the folder of the package, first on `sys.path` in
place of its own folder, so that `lem` is the package and no module of it is found under
its bare name. No bytecode is written, as with -B. Under a Python older than 3.11 it
says in one line what Lem needs, with the name the command's script had before it
(`project.py: Lem needs Python 3.11 ...`): this file, and the two it imports first, load
under the system's 3.9 on a Mac, so an annotation that 3.9 cannot evaluate is a string.
"""

import os
import sys

sys.dont_write_bytecode = True
if not __package__:
    # run by its path: sys.path[0] is this folder, which holds the modules by their bare
    # names
    sys.path[0] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from lem import names  # noqa: E402 - after the line that puts src on sys.path

FLOOR = (3, 11)


def main(argv: "list[str]") -> None:
    if not argv or names.module(argv[0]) is None:
        sys.exit(
            f"lem: {argv[0]!r} is no command of Lem's; `lem help` lists the names"
            if argv
            else "lem: name a command of Lem's; `lem help` lists the names"
        )
    name, args = argv[0], argv[1:]
    module = str(names.module(name))
    if sys.version_info < FLOOR:
        sys.exit(
            f"{names.file_name(module)}: Lem needs Python 3.11 or newer, and this "
            f"python3 is {sys.version.split()[0]}; put a newer one first on PATH, "
            "or run this file with it"
        )
    import runpy

    sys.argv = [names.file_name(module), *args]
    runpy.run_module(f"lem.{module}", run_name="__main__", alter_sys=True)


if __name__ == "__main__":
    main(sys.argv[1:])
