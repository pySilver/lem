"""The agent's last text in a Claude Code transcript: what a message of the owner answers.

A transcript is JSON lines; an agent's message is a line of `type` `assistant`, whose
`message.content` holds blocks, the text ones of `type` `text`. Only its end is read: a message
is judged against what the agent said just before it.
"""

import io
import json
import os

# The end of a transcript that is read (`corrections.TRANSCRIPT_TAIL_BYTES` on `main`).
TAIL = 4_000_000


def last_text(transcript: str) -> str:
    """The newest text an agent wrote in the Claude Code transcript `transcript`; empty when
    there is none or the file does not read. Lines are split at a line end only: a text may
    hold a line separator of Unicode."""
    try:
        with io.FileIO(transcript) as stream:
            size = os.fstat(stream.fileno()).st_size
            stream.seek(max(0, size - TAIL))
            tail = stream.read().decode(errors="replace")
    except OSError:
        return ""
    texts = (agent_text(line) for line in reversed(tail.split("\n")))
    return next((text for text in texts if text), "")


def agent_text(line: str) -> str:
    """The text blocks of an agent's message on one line of a transcript, joined; empty for
    any other line."""
    try:
        entry = json.loads(line)
    except ValueError:
        return ""
    if not isinstance(entry, dict) or entry.get("type") != "assistant":
        return ""
    said = entry.get("message")
    blocks = said.get("content") if isinstance(said, dict) else None
    if not isinstance(blocks, list):
        return ""
    texts = [
        block.get("text")
        for block in blocks
        if isinstance(block, dict) and block.get("type") == "text"
    ]
    return "\n".join(text for text in texts if isinstance(text, str)).strip()
