# Lem beside your own setup

This page tells you where Lem meets your own skills, hooks, rules, permissions and models.

## Permissions

Builders run in the background. A permission question stops a builder until somebody answers it
in Lem's session. Keep the allow list that `/lem init` proposes
([install.md](install.md#the-permissions-that-lem-init-proposes)). The rule `Bash(lem *)` still
works after each update of the plugin.

## Skills

Each skill that Lem ships, except `lem`, starts only by its `/lem` name or from a stage of Lem. So
your own skills with similar names do not conflict with them. A stage of Lem loads only the
skills that it names. A rule of yours that says "load every relevant skill" does not apply to Lem
and its agents.

## Hooks

- A `PreToolUse` hook sees `lem land propose SLUG`, not the push or the merge that the script runs.
  `branch.land` and `branch.protected` control a merge by Lem.
- A `Stop` or `SubagentStop` hook that blocks the end of a turn does not let Lem or a builder
  stop. Let such a hook pass in a repository with `.lem/project.toml`.
- If you have your own correction hook, keep only one of the two.

## Rules and CLAUDE.md

Your `CLAUDE.md` and your personal rules also apply inside Lem. Where they disagree with Lem, the
agent decides, and the result can change from turn to turn. To make it certain, write
what you want in one of three places: `tools.ask` for the tool that asks you questions,
`.lem/lessons.md` for a stage of Lem (a line that starts with the name of the stage), and the
`AGENTS.md` of the project for all other rules.

## Commit messages

A builder writes `type(scope): subject`. If the project's `AGENTS.md` or its commit hook gives
another form, that form wins.

## Models

The builder runs on Opus at high effort. The experts are Fable and, through Codex, GPT-6 Astra.
The second family of a persona panel is Codex. `[seats]` changes the reviewer, the defender and
the experts ([settings.md](settings.md#seats)). Without Codex, one expert does not answer, so a
choice with no answer from you always ends with the recommended option.

## Folders, the builder and the scope

- `[paths]` moves `docs/plans`, `docs/backlog` and the worktrees, if another tool uses them.
- A file `.claude/agents/lem-builder.md` in the repository replaces the builder of Lem.
- Install Lem with `--scope project`. An install at the user scope puts the hook and the skills of
  Lem into every repository, and the machine check tells you so.
