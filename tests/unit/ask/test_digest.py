"""A board answer carries the digest the browser received with its page."""

import json
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from lem.kernel import paths
from unit.ask.test_card import ROUTE, show

if TYPE_CHECKING:
    import pytest

    from unit.ask.conftest import Agterm
    from unit.board.service.given import Board


def test_card_navigation_reports_the_verified_page_digest(
    board: Board, terminal: Agterm, capsys: pytest.CaptureFixture[str]
) -> None:
    show(terminal, capsys)
    with board.main() as client:
        page = client.get(ROUTE + "/")
        head = client.head(ROUTE + "/")
    assert page.status_code == head.status_code == 200
    assert head.headers["content-length"] == str(len(page.content))
    assert page.headers["server-timing"] == f"card-digest;desc={page.headers['etag']}"


def test_runtime_posts_the_original_navigation_digest() -> None:
    runtime = paths.root() / "skills/lem-ask/runtime/ask.js"
    source = runtime.read_text(encoding="utf-8")
    setup = source.split("// ---------- markdown", 1)[0]
    delivery = source[source.index("  function answerURL") :].split(
        "// ---------- keyboard", 1
    )[0]
    script = (
        """
    const location = new URL('http://localhost/tasks/t/cards/P1/');
    const performance = {
      getEntriesByType: type => {
        if (type !== 'navigation') throw new Error(type);
        return [{serverTiming: [{name: 'card-digest', description: 'original'}]}];
      }
    };
    const window = {};
    const document = {
      getElementById: () => ({textContent: '{}'}),
      createElement: () => ({}),
      body: {appendChild: () => {}},
    };
    const fetch = async (_url, req) => {
      if (req.method === 'HEAD') return {ok: true, headers: new Headers({etag: '"new"'})};
      console.log(req.body);
      return {ok: true, text: async () => '{}'};
    };
    """
        + setup
        + delivery
        + """
    let finished = false;
    deliver({status: 'answered'}).catch(error => { throw error; });
    }());
    """
    )
    ran = subprocess.run(
        ["node", "-"],
        input=script,
        text=True,
        capture_output=True,
        check=True,
        cwd=Path(__file__).parent,
    )
    assert json.loads(ran.stdout) == {"status": "answered", "digest": "original"}
