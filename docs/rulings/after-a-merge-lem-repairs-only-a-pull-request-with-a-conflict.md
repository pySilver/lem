---
ruled: 2026-11-17
area: The review, the pull request and the merge
---

# After a merge, Lem repairs only a pull request with a conflict

His review of the README and the docs on 2026-11-17, 27 notes; a quote is his words. Where a note
replaces an earlier ruling, this is the ruling now.

**After a merge, Lem repairs only a pull request with a conflict**: the session had built a
rebase and a new check of every open pull request after each merge. Asked for options on a
page (2026-11-17), he asked "What is the typical strategry for teams that work via GitHub?";
the answer was that most teams update a branch only on a conflict, and that a pull request bot
does the same by default (Renovate's `rebaseWhen: auto`), and to "Lem repairs only a pull
request with a conflict" he wrote "Great!". Every other open pull request waits for `/lem
land` or for his click on the forge.
