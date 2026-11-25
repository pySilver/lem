"""Why the phone cannot open the Inbox, in the page's words (`board_model.INBOX_WHY`,
`INBOX_WHY_SENT` and `INBOX_UNSENT` on `main`), by the `why` of the server's record."""

from types import MappingProxyType

NO_ADDRESS = "The Inbox has no tailnet address, so the phone cannot open it."
WENT = "A message of this task went to the Inbox, but"
PHONE = "so the phone cannot open it."
WHY = MappingProxyType(
    {
        "not installed": (
            "The Inbox is not installed on this Mac, so no question went there."
        ),
        "not running": "The Inbox does not run on this Mac, so no question went there.",
        "not answering": (
            "The Inbox on this Mac does not answer, so no question went there."
        ),
        "no tailnet address": NO_ADDRESS,
        "failed": (
            "The board’s server could not ask the Inbox on this Mac, "
            "so no question went there."
        ),
    }
)
# The same, for a task whose message went to the Inbox before its door closed: it is there,
# and the phone cannot reach it now.
WHY_SENT = MappingProxyType(
    {
        "not installed": f"{WENT} the Inbox is not installed on this Mac now, {PHONE}",
        "not running": f"{WENT} the Inbox does not run on this Mac now, {PHONE}",
        "not answering": f"{WENT} the Inbox on this Mac does not answer now, {PHONE}",
        "no tailnet address": NO_ADDRESS,
        "failed": (
            f"{WENT} the board’s server could not ask the Inbox on this Mac now, {PHONE}"
        ),
    }
)
# A thing the record keeps with no answer of the Inbox yet while a call failed: the next look
# sends it again.
UNSENT = "The board’s server could not send this to the Inbox yet; its next look tries again."
