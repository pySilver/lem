---
worth: later
where: skills/lem/assets/board.css
added: 2026-11-22
---
# In a window 700px wide or less, a folded sidebar has no control that unfolds it

Fold the sidebar in a wide window, so the cookie keeps rail: true, then make the window 700px wide or less and open the drawer: .shell.railed .side hides all but the mark and the rail, the media rule hides #side-fold, and the rail's fold#side buttons show only for demo data, away or a stopped task; the base e86389c has the same two rules.

Seen outside the change by review round 1 of task sidebar-fold-arrow (2026-11-22); the base commit has it.
