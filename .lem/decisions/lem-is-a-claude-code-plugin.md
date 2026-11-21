---
decided: 2026-11-15
area: What Lem needs on the machine
---

# Lem is a Claude Code plugin

## Changed in part

The title is the rule as it stands. Where the paragraph below says otherwise, the line here holds.

- 2026-11-20, [A release is a change of the plugin's `version`](../../docs/rulings/a-release-is-a-change-of-the-plugins-version.md): "no version": a release is a change of the plugin's `version`

## As decided on 2026-11-15, changed in part since

Designs taken on 2026-11-14 and 2026-11-15 after a question of the owner's. They are open to
him, and they are not his rulings until he says so:

**Lem is a Claude Code plugin**, after "can we make it more self contained? lem is aimed to be
per-project companion" and his "I agree" to a test first. The test ran on 2026-11-15; on
2026-11-17 he ruled that the plugin is the only form (above). The plugin's files are
`.claude-plugin/plugin.json`, whose `version` is the release since 2026-11-21 (an install takes
an update when it changes),
`.claude-plugin/marketplace.json`, `bin/` with `lem`, `lem-ask` and `lem-jev`, and
`hooks/hooks.json`. The builder is `lem:lem-builder`.
