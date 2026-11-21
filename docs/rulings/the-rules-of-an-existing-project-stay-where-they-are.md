---
ruled: 2026-11-15
area: What Lem is, and who it is for
---

# The rules of an existing project stay where they are

His ruling of 2026-11-15. It is reopened only by asking him. A quote is his words.

**The rules of an existing project stay where they are**: "ok rules stays for now"
(2026-11-15). An adopted project's style guide is the folder its agent loads by itself
(`.claude/rules`); Lem reads it and never moves or links a file of it, because "being able to
share project rules between Codex and Claude Code is a huge benefit, especially for review
rounds". Lem has no command that moves linked settings: `/lem migrate` "becomes pointless as
personas is used in one or two of our projects so we can move those ad-hoc there", and
`init --existing link` was how an adopted project named its folders until 2026-11-18, when
every place became fixed (his interview, below): a project moves its personas and its profile
into `.lem/`, and `.claude/rules` is the one place Lem reads the rules for the code. "For now"
is his: a move of the rules is a new decision of his, and nothing here prepares one. The form built from it
is the session's design: `project.py rules`, the one match of a change against the files'
`paths:` scopes, whose answer goes to a builder's brief, the reviewer's message and a review
round; one format, Claude Code's, until a project needs another.
