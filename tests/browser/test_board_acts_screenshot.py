"""Take a phone screenshot by the DevTools steps in the Claude Code harness."""

import shutil
import subprocess
from pathlib import Path

import pytest


def test_the_harness_devtools_steps_capture_a_phone_screenshot(
    tmp_path: Path,
) -> None:
    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    node = shutil.which("node")
    if not node or not Path(chrome).is_file():
        pytest.skip("the screenshot trial needs Node.js and Chrome for macOS")
    script = Path(__file__).with_name("board-acts-screenshot.mjs")
    picture = tmp_path / "phone.png"
    ran = subprocess.run(
        [node, str(script), chrome, str(tmp_path / "profile"), str(picture)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert ran.returncode == 0, ran.stderr
    header = picture.read_bytes()[:24]
    assert header.startswith(b"\x89PNG\r\n\x1a\n")
    assert (int.from_bytes(header[16:20]), int.from_bytes(header[20:24])) == (780, 1688)
