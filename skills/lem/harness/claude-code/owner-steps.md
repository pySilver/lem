# Claude Code: what the owner does himself

A part of `../claude-code.md`, read when a step waits for him that no agent may take.

## What the owner does himself

Some steps are not an agent's, with or without the owner's yes in the conversation.

- **A folder's trust.** Claude Code asks whether the owner trusts a folder the first time a
  session starts in it, and Codex asks the same. That holds for a repository an agent made
  minutes before. The answer is kept in the owner's configuration, so it is his: say which
  session waits and where, and go on with other work. Do not answer the prompt, and do not go
  around it. A task's session that opens in a folder never trusted shows the dialog with "No,
  exit" selected first (the trial of 2026-11-21), and waits there for him. A task's session opens in
  the main checkout, which he trusts, and works in the task's worktree by its path: a session started
  in the worktree itself has no plugin installed for the project and none of the folder's own
  Claude Code settings (lem-scratch, Claude Code 2.1.330, 2026-11-21).
- **agterm's keymap.** The line of the task picker (the `line` of the `task picker` row of
  `lem doctor`) goes into agterm's own file, `~/.config/agterm/keymap.conf`, and the owner adds
  it: another program's settings stay where that program keeps them (his ruling). Give him the
  line and `agtermctl keymap reload`, and do not edit the file, also on his yes.
- **A read outside the working directories.** Claude Code asks "Allow this read outside the
  working directories?" the first time a session reads a file of Lem's plugin or of its app
  (seen 2026-11-24). The answer goes into his settings, so it is his: say which session waits,
  and give him the allow rule that the row of `lem doctor` for this question names.
