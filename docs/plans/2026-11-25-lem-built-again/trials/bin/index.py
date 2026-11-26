"""Index trial evidence, including raw files and steps that did not finish."""

import argparse
import hashlib
import json
from pathlib import Path


def index(folder: Path) -> dict[str, object]:
    evidence = folder / "evidence"
    steps = {}
    files = {}
    for path in sorted(evidence.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"keep a copy of the evidence, not a link: {path}")
        if not path.is_file():
            continue
        name = path.relative_to(evidence).as_posix()
        with path.open("rb") as stream:
            files[name] = {
                "sha256": hashlib.file_digest(stream, "sha256").hexdigest(),
                "bytes": stream.tell(),
            }
        if path.parent == evidence and name.endswith(".meta.json"):
            steps[name.removesuffix(".meta.json")] = json.loads(path.read_bytes())
    return {"folder": str(folder), "steps": steps, "files": files}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    args = parser.parse_args()
    try:
        found = index(args.folder)
    except (OSError, ValueError) as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        raise SystemExit(1) from error
    print(json.dumps({"ok": True, **found}))


if __name__ == "__main__":
    main()
