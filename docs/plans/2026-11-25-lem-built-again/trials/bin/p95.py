"""Measure the five installed hook lines on a quiet Mac."""

import argparse
import json
import math
import os
import re
import subprocess
import time
from pathlib import Path
from typing import TypedDict

SELECTORS = {
    "corrections": "UserPromptSubmit",
    "serve": "SessionStart",
    "session-start": "SessionStart",
    "precompact": "PreCompact",
    "stop": "Stop",
}
LINE = re.compile(
    r'/bin/sh "\$CLAUDE_PLUGIN_ROOT/hooks/run" ([a-z-]+) 2>/dev/null \|\| :'
)
# The design's part 5 sets the budget. The hook cost test sets the sample count and quiet load.
BUDGET_MS = 55.0
SAMPLES = 30
QUIET = 4.0


class Timing(TypedDict):
    p95_ms: float
    samples_ms: list[float]


def percentile(samples: list[float]) -> float:
    return sorted(samples)[math.ceil(0.95 * len(samples)) - 1]


def lines(manifest: Path) -> dict[str, str]:
    found: dict[str, str] = {}
    for event, groups in json.loads(manifest.read_bytes())["hooks"].items():
        for group in groups:
            for hook in group["hooks"]:
                command = hook["command"]
                match = LINE.fullmatch(command)
                if not match or SELECTORS.get(match[1]) != event or match[1] in found:
                    raise ValueError(f"unexpected hook under {event}: {command}")
                found[match[1]] = command
    if found.keys() != SELECTORS.keys():
        raise ValueError(f"expected every selector: {', '.join(SELECTORS)}")
    return found


def event(selector: str, repo: Path, transcript: Path, session: str) -> bytes:
    return json.dumps(
        {
            "cwd": str(repo),
            "hook_event_name": SELECTORS[selector],
            "session_id": session,
            "transcript_path": str(transcript),
            "source": "manual" if selector == "precompact" else "startup",
            "trigger": "manual",
            "prompt": "Check the word list.",
            "stop_hook_active": False,
        }
    ).encode()


def measure(folder: Path, args: argparse.Namespace) -> dict[str, object]:
    repo = args.repo.resolve()
    transcript = folder / "tmp" / "p4-transcript.jsonl"
    transcript.touch()
    session = "p4-installed-hook"
    task = repo / ".lem" / "state" / "tasks" / args.task
    sessions = task / "sessions.jsonl"
    if (
        not repo.is_relative_to(folder)
        or not task.is_dir()
        or task.parent.name != "tasks"
    ):
        raise ValueError("use a task in a trial checkout")
    commands = lines(args.plugin / "hooks" / "hooks.json")
    hint = folder / "tmp" / "p4-claude-env"
    # The installed launcher resolves the keg's hook with only the GUI PATH.
    environ = {
        **os.environ,
        "CLAUDE_PLUGIN_ROOT": str(args.plugin.resolve()),
        "CLAUDE_ENV_FILE": str(hint),
        "LEM_TASK": args.task,
    }
    before = os.getloadavg()[0]
    if before > QUIET:
        return {"ok": False, "status": "load-too-high", "load_before": before}
    previous = sessions.read_bytes() if sessions.exists() else b""
    results: dict[str, Timing] = {}
    for selector, command in commands.items():
        stdin = event(selector, repo, transcript, session)
        samples = []
        for _ in range(SAMPLES):
            began = time.perf_counter()
            ran = subprocess.run(
                ["/bin/sh", "-c", command],
                cwd=repo,
                env=environ,
                input=stdin,
                capture_output=True,
                timeout=10,
                check=False,
            )
            samples.append((time.perf_counter() - began) * 1000)
            expected = (
                args.task.encode() in ran.stdout
                if selector == "precompact"
                else not ran.stdout
            )
            if ran.returncode or not expected or ran.stderr:
                raise ValueError(
                    f"{selector}: exit {ran.returncode}, "
                    f"stdout {ran.stdout!r}, stderr {ran.stderr!r}"
                )
        results[selector] = {"p95_ms": percentile(samples), "samples_ms": samples}
    after = os.getloadavg()[0]
    frames = (
        sessions.read_bytes()[len(previous) :].splitlines() if sessions.exists() else []
    )
    written = sum(
        json.loads(line).get("claude") == session for line in frames if line.strip()
    )
    return {
        "ok": after <= QUIET
        and written == SAMPLES
        and hint.is_file()
        and all(row["p95_ms"] <= BUDGET_MS for row in results.values()),
        "budget_ms": BUDGET_MS,
        "load_before": before,
        "load_after": after,
        "session_frames": written,
        "env_file_written": hint.is_file(),
        "selectors": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--plugin", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--task", required=True)
    args = parser.parse_args()
    try:
        found = measure(args.folder, args)
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as error:
        found = {"ok": False, "error": str(error)}
    print(json.dumps(found))
    raise SystemExit(int(not found["ok"]))


if __name__ == "__main__":
    main()
