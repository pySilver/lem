"""A stand-in for the `tailscale` CLI: its status, its serve status, and `serve --bg` and `serve
--https=N off`, which change the serve status it keeps in a file beside it. Each call is a line
of `calls.txt` there. The real CLI is never run by a case."""

import json
import os
import stat
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

NAME = "studio.example.ts.net"
LOGIN = "owner@example.com"
SCRIPT = """
import json, os, sys
from pathlib import Path

here = Path(__file__).parent
if Path(__file__).name == "Tailscale" and os.environ.get("TAILSCALE_BE_CLI") != "1":
    print("The Tailscale GUI failed to start")
    sys.exit(0)
words = sys.argv[1:]
(here / "calls.txt").open("a").write(" ".join(words) + "\\n")
status = json.loads((here / "status.json").read_text())
served = here / "served.json"
web = json.loads(served.read_text()) if served.exists() else {}
if words == ["status", "--json"]:
    print(json.dumps(status))
elif words == ["serve", "status", "--json"]:
    print(json.dumps(web))
elif words[:2] == ["serve", "--bg"]:
    port = words[2].split("=")[1]
    web = {"TCP": {port: {"HTTPS": True}}, "Web": {f"NAME:{port}": {"Handlers": {"/": {"Proxy": words[3]}}}}}
    served.write_text(json.dumps(web))
elif words[0] == "serve" and words[-1] == "off":
    served.unlink(missing_ok=True)
else:
    sys.exit("unknown call: " + " ".join(words))
"""


def status(**changes: object) -> dict[str, object]:
    """A status of a connected Mac signed in with the owner's login."""
    found: dict[str, object] = {
        "BackendState": "Running",
        "Self": {"DNSName": f"{NAME}.", "UserID": 7},
        "User": {"7": {"LoginName": LOGIN}},
        "CertDomains": [NAME],
    }
    found.update(changes)
    return found


def made(folder: Path, name: str = "tailscale", /, **changes: object) -> Path:
    """The stand-in in `folder`, answering with the status `changes` make."""
    folder.mkdir(parents=True, exist_ok=True)
    cli = folder / name
    body = SCRIPT.replace("NAME", NAME)
    cli.write_text(f"#!{sys.executable} -I\n{body}")
    cli.chmod(cli.stat().st_mode | stat.S_IXUSR)
    (folder / "status.json").write_text(json.dumps(status(**changes)))
    return cli


def calls(cli: Path) -> list[str]:
    """Each call the stand-in got, in order."""
    found = cli.parent / "calls.txt"
    return found.read_text().splitlines() if found.exists() else []


def environ(cli: Path) -> dict[str, str]:
    """The environment that names the stand-in."""
    return {**os.environ, "LEM_TAILSCALE": str(cli)}
