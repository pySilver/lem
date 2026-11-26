"""Links to pull requests in the Markdown of the task panel."""

from lem.board.views.panel import pulls


def test_pull_links_leave_code_existing_links_and_fenced_blocks_whole() -> None:
    forge = "https://github.com/acme/shop"
    text = "See #41, `#5`, [#3](https://other.example/pull/3).\n```\n#7\n```\n# Head"
    assert pulls.linked(text, forge) == (
        "See [#41](https://github.com/acme/shop/pull/41), `#5`, "
        "[#3](https://other.example/pull/3).\n```\n#7\n```\n# Head"
    )
