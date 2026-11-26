"""The async Stop hook restores the waiting mark while its question is open."""

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Mapping


def answer(environ: Mapping[str, str], behind: str | None) -> str:
    """Start no work outside an attended agterm session and read no stdin."""
    session = environ.get("AGTERM_SESSION_ID")
    if (
        session
        and environ.get("AGTERM_ENABLED") == "1"
        and environ.get("CLAUDE_CODE_SESSION_ATTENDED") != "0"
    ):
        from lem.hooks.stop_agterm import restore

        restore(environ, session)
    return ""
