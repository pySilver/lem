---
worth: yes
where: skills/lem/harness/README.md
added: 2026-11-15
---
# no harness file for Codex

A Codex session in which someone types `/lem` reads `skills/lem/SKILL.md`, looks for
`harness/codex.md`, finds none, and stops, as the skill tells it to. That is right today: the
contract was checked in Claude Code only. Reading that stop as a defect is the misreading this
entry exists to prevent; writing the file from what Claude Code does would be the real defect.

What the file needs is a check of each row of the contract in a Codex session, and nobody ran
one: how Codex loads a skill of Lem's, how it starts a builder on another model and whether that
builder can start builders, how it opens a session of its own with a reviewer beside it, how it
tells Lem that it stopped, and how it asks the owner. One fact is known from another project's
notes and is not checked here: Codex 0.167 opened four agents, itself included (mybaze,
2026-11-07).

What has to be settled with the owner first: where Lem is linked for Codex during the check.
`scripts/setup.py` links for Claude Code only, and a link in the owner's own Codex folder shows
Lem to every repository on the machine, as the home links did for Claude Code on 2026-11-15.

The owner's rulings give the order: Claude Code first, the harness file for Codex after that
works, and Codex as the builder is wanted later. Two tasks ran in Claude Code on 2026-11-15, so
this is next.
