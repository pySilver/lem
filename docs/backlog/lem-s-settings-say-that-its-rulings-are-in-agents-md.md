---
worth: later
where: .lem/project.toml
added: 2026-11-21
---
# Lem's settings say that its rulings are in AGENTS.md

The comment above `paths.rulings` in Lem's own `.lem/project.toml` ends with "Lem's own rulings are
in AGENTS.md.", and the topic "A change bends a ruling of the owner: a ruling in AGENTS.md is
reopened only by asking him." names the same place. Since the task agents-md-read-on-demand,
`AGENTS.md` holds one linked sentence for each ruling and the ruling whole is a file of
`docs/rulings/`, the folder `paths.rulings` names, so the comment is half true. That task left the
file as it was on purpose (decision 11 of its record): a diff that touches `.lem/project.toml` is
careful, and a topic is the owner's words. A fix changes the comment, and the topic only on his
word, for example "Lem's own rulings are in docs/rulings, and AGENTS.md has a sentence for each."
