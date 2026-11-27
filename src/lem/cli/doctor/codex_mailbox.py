"""The hooks and send rule a Codex reviewer needs for the plan talk's mailbox."""

from pathlib import Path
from typing import TYPE_CHECKING

from lem.cli.doctor import mailbox_hooks, mailbox_rules, tool_words
from lem.cli.doctor.checkouts import main_checkout
from lem.cli.doctor.row import REQUIRED, Row
from lem.settings import places
from lem.settings.load import settings_of

if TYPE_CHECKING:
    from lem.cli.doctor.look import Look

NAME = "Codex reviewer mailbox"
FIX = (
    "The owner adds `mailbox-chat.py codex-hook` to Codex's SessionStart hooks and trusts it "
    "in Codex's `/hooks` dialog. Add the recipe's `host_executable` and `prefix_rule` for "
    "`mailbox-chat.py say --file` to the Codex rules. Add `on message "
    "/full/path/to/mailbox-chat.py agterm-hook` to agterm's hooks.conf and run "
    "`agtermctl hooks reload`. Use the same temporary directory for agterm and the reviewer."
)


def codex_home(look: Look) -> Path:
    """The Codex configuration home of the session."""
    named = look.environ.get("CODEX_HOME")
    return Path(named) if named else look.home / ".codex"


def gaps(codex: Path, agterm: Path, program: Path) -> tuple[str, ...]:
    """The recipe's files that are missing a declaration."""
    config, rules = codex / "config.toml", codex / "rules"
    checks = (
        (mailbox_hooks.start_hook(config, program), f"SessionStart hook in {config}"),
        (
            mailbox_rules.configured(rules, program),
            f"send rule in {rules}/default.rules",
        ),
        (mailbox_hooks.message_hook(agterm, program), f"on message hook in {agterm}"),
    )
    return tuple(said for found, said in checks if not found)


def mailbox_rows(look: Look) -> tuple[Row, ...]:
    """Check the mailbox recipe for a repository whose plan reviewer is Codex."""
    root = main_checkout(look.folder)
    if root is None or not (root / places.TEAM).is_file():
        return ()
    if not settings_of(root, look.environ).settings.seats.reviewer.startswith("codex/"):
        return ()
    program = look.which(mailbox_rules.PROGRAM)
    agterm = look.home / ".config" / "agterm" / "hooks.conf"
    missing = (
        gaps(codex_home(look), agterm, program.absolute())
        if program
        else ("mailbox-chat.py on PATH",)
    )
    details = ", ".join(missing)
    return (
        Row(
            name=NAME,
            need=REQUIRED,
            found=not missing,
            detail=f"missing: {details}" if missing else "recipe files are in place",
            used_for="a Codex reviewer receives the plan talk and sends its replies",
            without_it=FIX,
            guide=tool_words.MAILBOX.guide,
            recipe=tool_words.MAILBOX.recipe,
        ),
    )
