"""Run one trial command and keep its standard streams and outcome."""

import argparse
import json
import os
import re
import signal
import subprocess
import time
from contextlib import suppress
from pathlib import Path

NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*")


def inside(folder: Path, path: Path) -> Path:
    resolved = (folder / path).resolve()
    if not resolved.is_relative_to(folder):
        raise ValueError(f"{path} must be in {folder}")
    return resolved


def run(folder: Path, args: argparse.Namespace) -> dict[str, object]:
    if not NAME.fullmatch(args.name) or not args.argv:
        raise ValueError("give a new step name and a command")
    cwd = inside(folder, args.cwd)
    given = inside(folder, args.stdin).read_bytes() if args.stdin else None
    entry = "enter-gui" if args.gui_path else "enter"
    prefix = folder / "evidence" / args.name
    began = time.monotonic()
    meta = prefix.with_suffix(".meta.json")
    exit_code = None
    error = None
    # Claim the name before any effect. Keep the initial row even if the recorder stops.
    with meta.open("x", encoding="utf-8") as stream:
        json.dump({"name": args.name, "state": "started"}, stream)
    with (
        prefix.with_suffix(".out").open("xb") as out,
        prefix.with_suffix(".err").open("xb") as err,
    ):
        try:
            with subprocess.Popen(
                [folder / entry, *args.argv],
                cwd=cwd,
                stdin=subprocess.PIPE if given is not None else subprocess.DEVNULL,
                stdout=out,
                stderr=err,
                start_new_session=True,
            ) as child:
                prefix.with_suffix(".pid").write_text(
                    f"{child.pid}\n", encoding="ascii"
                )
                try:
                    child.communicate(given, timeout=args.timeout)
                except (KeyboardInterrupt, subprocess.TimeoutExpired) as stop:
                    error = type(stop).__name__
                    with suppress(ProcessLookupError):
                        os.killpg(child.pid, signal.SIGTERM)
                    try:
                        child.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid, signal.SIGKILL)
                        child.wait()
                exit_code = child.returncode
        except OSError as failure:
            error = str(failure)
    row = {
        "name": args.name,
        "state": "finished",
        "argv": args.argv,
        "cwd": str(cwd),
        "entry": entry,
        "stdin": args.stdin,
        "exit": exit_code,
        "seconds": time.monotonic() - began,
        "error": error,
    }
    pending = meta.with_suffix(".tmp")
    pending.write_text(json.dumps(row) + "\n", encoding="utf-8")
    pending.replace(meta)
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--cwd", type=Path, default=Path())
    parser.add_argument("--stdin")
    parser.add_argument("--timeout", type=float)
    parser.add_argument("--gui-path", action="store_true")
    parser.add_argument("name")
    parser.add_argument("argv", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.argv[:1] == ["--"]:
        args.argv.pop(0)
    try:
        row = run(args.folder, args)
    except (OSError, ValueError) as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        raise SystemExit(1) from error
    print(json.dumps(row))
    code = row["exit"]
    raise SystemExit(
        128 - code
        if isinstance(code, int) and code < 0
        else code or int(row["error"] is not None)
    )


if __name__ == "__main__":
    main()
