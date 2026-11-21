---
ruled: 2026-11-20
area: The board and the pages for him
---

# Tailscale is the way from his phone, and nothing supervises the server

His rulings of 2026-11-20 and 2026-11-21, while his interview redesigned how a task runs and the
board became a served app; a quote is his words. His answers Q7 to Q11 and notes P1 to P9 are in
`.lem/state/tasks/one-lem-parallel-landings/`, which git ignores. Where a note replaces an earlier
ruling, this is the ruling now.

The board, whose form is the session's decision "The board is served, and the server draws it":

**Tailscale is the way from his phone, and nothing supervises the server**: "Server: I want
tailscale usage be the first class citizen. Thats my opionated choice. Obviosly if one does not
need it - then fine, DIY". The door lets in only his tailscale login, never through Funnel. "I'd
rather keep the Plannotator approach and avoid polluting launchd. I can always remote login to the
machine and start the server manually." So the plugin's SessionStart hook and `lem board` start
it, and no login item does.
