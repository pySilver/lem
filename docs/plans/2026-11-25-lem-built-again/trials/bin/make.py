"""Make a private trial folder and the entry to its empty environment."""

import argparse
import json
import re
import shlex
import shutil
import sys
from pathlib import Path

NAME = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.-]*")
FOLDERS = ("home", "config", "tmp", "cache", "bin", "evidence")
SCRIPTS = ("step", "p95", "merge_calls", "index")


def tool_link(word: str) -> tuple[str, Path]:
    name, _, target = word.partition("=")
    path = Path(target)
    if not NAME.fullmatch(name) or not path.is_absolute() or not path.is_file():
        raise ValueError(f"use NAME=/absolute/path/to/tool: {word}")
    return name, path


def entry(folder: Path, user: str, *, gui_path: bool = False) -> str:
    """The command line of the environment all trial commands start with."""
    path = "/usr/bin:/bin" if gui_path else f"{folder / 'bin'}:/usr/bin:/bin"
    environ = {
        "HOME": folder / "home",
        "USER": user,
        "PATH": path,
        "XDG_CONFIG_HOME": folder / "config",
        "XDG_CACHE_HOME": folder / "cache",
        "TMPDIR": folder / "tmp",
        "GH_CONFIG_DIR": folder / "config" / "gh",
        "CLAUDE_CONFIG_DIR": folder / "home" / ".claude",
        "GIT_CONFIG_NOSYSTEM": 1,
        "GIT_TERMINAL_PROMPT": 0,
        "GH_PROMPT_DISABLED": 1,
        "LEM_SERVE": "off",
        "LC_ALL": "C",
    }
    words = shlex.join([f"{key}={value}" for key, value in environ.items()])
    return f'#!/bin/sh\numask 077\nexec /usr/bin/env -i {words} "$@"\n'


def write_executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o700)


def make(folder: Path, user: str, links: list[tuple[str, Path]]) -> None:
    if (
        not folder.is_relative_to(Path("/", "tmp").resolve())
        or folder == Path("/", "tmp").resolve()
    ):
        raise ValueError("name a new trial folder below /tmp")
    if len(dict(links)) != len(links):
        raise ValueError("give each tool link one name")
    folder.mkdir(mode=0o700)
    for name in FOLDERS:
        (folder / name).mkdir()
    for name, target in links:
        (folder / "bin" / name).symlink_to(target)
    write_executable(folder / "enter", entry(folder, user))
    write_executable(folder / "enter-gui", entry(folder, user, gui_path=True))
    for name in SCRIPTS:
        script = folder / f"{name}.py"
        shutil.copyfile(Path(__file__).with_name(script.name), script)
        words = [sys.executable, "-I", "-B", str(script), str(folder)]
        if name == "p95":
            words.insert(0, str(folder / "enter-gui"))
        command = shlex.join(words)
        write_executable(folder / name, f'#!/bin/sh\numask 077\nexec {command} "$@"\n')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--user", required=True)
    parser.add_argument("--tool", action="append", default=[])
    args = parser.parse_args()
    folder = args.folder.resolve()
    try:
        make(folder, args.user, [tool_link(word) for word in args.tool])
    except (OSError, ValueError) as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        raise SystemExit(1) from error
    print(
        json.dumps({"ok": True, "folder": str(folder), "enter": str(folder / "enter")})
    )


if __name__ == "__main__":
    main()
