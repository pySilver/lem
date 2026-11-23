---
worth: later
where: skills/lem/scripts/serve.py:merge_in_thread
added: 2026-11-23
---
# A second press during the server's standing merge gets "Not done." when the base moves again

The safe read logs merge.stands and the server starts the owner's merge with --standing. The owner presses Merge from a page opened before, and act_merge gives him the token of that running merge. main moves again before the merge, so land.py refuses it with kind base and keeps his merge for another read. The note of that token then says "Not done." over land.py's line, although his merge still stands. On the base commit, the same press gets the same token and the same note.

Seen outside the change by review round 1 of task standing-merge-shows-as-waiting (2026-11-23); the base commit has it.
