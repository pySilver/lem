---
ruled: 2026-11-17
area: The settings, the seats and the tracker
---

# The state of Lem is not in the git directory

His review of the README and the docs on 2026-11-17, 27 notes; a quote is his words. Where a note
replaces an earlier ruling, this is the ruling now.

**The state of Lem is not in the git directory**: "Is that a best practice to keep things in
`.git/lem/`? It smells to me. Maybe it's better to keep those in untracked `.lem/something`
dir?" The session checked one more reason: Codex's sandbox keeps `.git` read-only
(`codex-rs/protocol/src/permissions.rs`, read 2026-11-17).
