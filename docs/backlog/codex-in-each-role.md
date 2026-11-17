---
worth: yes
where: skills/lem/harness/README.md
added: 2026-11-15
---
# Codex in each role

Lem runs in Claude Code only, and Codex can only be the reviewer of a plan talk. The owner wants
Codex in each role, Lem itself, a lead, a builder, the reviewer: "Lets put a backlog item to make
Codex work on any side. I'm not sure what blocks us, the Codex model would know best"
(2026-11-17). So the first step of this item is a Codex session that reads
`skills/lem/harness/README.md` and says, row by row, what it can do and what it cannot.

A Codex session in which someone types `/lem` reads `skills/lem/SKILL.md`, looks for
`harness/codex.md`, finds none, and stops, as the skill tells it to. That is right today: the
contract was checked in Claude Code only. Writing the file from what Claude Code does would be
the real defect.

What is known:

- Nobody checked a row of the contract in a Codex session: how Codex loads a skill of Lem's, how
  it starts a builder on another model and whether that builder can start builders, how it opens
  a session of its own with a reviewer beside it, how it tells Lem that it stopped, and how it
  asks the owner.
- Codex's sandbox keeps `.git`, and a worktree's git directory, read-only under a writable root
  (`default_read_only_subpaths_for_writable_root` in `codex-rs/protocol/src/permissions.rs`,
  read 2026-11-17). A Codex builder that commits needs that write granted, and nothing of Lem's
  may live in the git directory.
- One fact from another project's notes, not checked here: Codex 0.167 opened four agents,
  itself included (mybaze, 2026-11-07).
- How Lem installs for Codex is open. Lem is a plugin of Claude Code; whether Codex loads the
  same folder as a plugin of its own is the first thing to read in Codex's documentation.

The order the owner gave before: Claude Code first, then the harness file for Codex, then Codex
as the builder.
