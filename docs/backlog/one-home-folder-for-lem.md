---
worth: yes
where: skills/lem/scripts/project.py
added: 2026-11-19
---
# One home folder for Lem

Lem keeps what belongs to a person or a machine in more than one place, and two of them are not
Lem's name. On 2026-11-19 the owner wrote: "I think everything should be living under
`~/.config/lem` to avoid namespace pollution". That folder exists (`$XDG_CONFIG_HOME/lem` when the
variable is set, `lem_state.config()`): it holds the owner's away mark, `owner.jsonl`, and
`machine.toml`, with `[seats] merger` and `session`, `[load]`, `[serve]`, `[peers]` and
`[handoff]`. This item moves the rest into it.

What moves:

- **The reviewer seat of a machine.** `/lem reviewer AGENT/MODEL:EFFORT` runs `lem project
  reviewer`, which writes `[seats]` into `.lem/project.local.toml` of one repository
  (`LOCAL_TABLES` in `project.py`). The seat says that Codex is down or out of tokens on this Mac,
  which holds for every repository. The case: Codex stops in the morning, he types `/lem reviewer
  claude` in one repository, and a plan talk in a second repository opens Codex and fails.
- **A person's no to the correction queue**, `collect = false` under `[corrections]`, today in
  `.lem/project.local.toml` of each repository. A new repository sends his typed messages to the
  Jev model's provider until he writes it there too.
- **The question page's defaults**, `~/.config/lem-ask/defaults.json` (`skills/lem-ask/bin/lem-ask`,
  `LEM_ASK_CONFIG`).

What goes, and moves nowhere:

- **The user's cast of personas**, `~/.config/personas/cast/` (`skills/lem-panel/scripts/cast.py`,
  `starting`), the first place `cast.py init` copies a first cast from. It never answers a panel:
  each project's own cast in `.lem/personas/` does, and personas differ from project to project.
  The owner, on the proposal to remove it (2026-11-19): "Yes, this setup for personas matches my
  views". So `cast.py init` copies the built-in cast only, `/lem init` rewrites it for the project,
  and the user layer leaves `cast.py`, `skills/lem-panel/SKILL.md` and their tests.

What stays: the project's settings (topics, checks, who lands, branches), which are the team's;
`[naps] on = false`, which turns naps off for one repository; and the Jev key, which his ruling
keeps in the environment and never in a file.

Open before it is built:

- Whether `.lem/project.local.toml` keeps any table once `[seats]` and `[corrections]` move, or
  goes with `[naps]` moved into the tracked settings or the home folder.
- The question page's cache, `~/.cache/lem-ask/`. XDG keeps a cache apart from a configuration, so
  the session's reading is `~/.cache/lem`, not a folder under `~/.config/lem`; his words say
  "everything", so ask him.
- Whether `doctor.py` gets a row for the folder.

It reaches the topics "Lem writes over something of the developer's: a file in his home" (a move of
his page defaults) and "A developer's typed messages leave the machine without his
yes" (the move of his no to the queue), so it takes the careful flow when it is built.
