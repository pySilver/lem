---
ruled: 2026-11-15
area: The lessons, the correction queue, the naps, the night and the free hour
---

# The correction hook is an optional part.

## Changed in part

The title is the rule as it stands. Where the paragraph below says otherwise, the line here holds.

- 2026-11-15, [As a plugin, the correction hook comes with the install, and the repository says yes for all](as-a-plugin-the-correction-hook-comes-with-the-install-and-the-repository-says-yes-for-all.md): "the owner registers the hook with Lem's setup": the hook comes with the plugin's install, and the repository says yes for all
- 2026-11-17, [Lem is a plugin, and nothing else](lem-is-a-plugin-and-nothing-else.md): "the owner registers the hook with Lem's setup": there is no setup script and no `--corrections`; the repository's tracked `corrections.collect = true` turns the queue on

## As ruled on 2026-11-15, changed in part since

His ruling of 2026-11-15. It is reopened only by asking him. A quote is his words.

**The correction hook is an optional part.** Lem recommends the correction queue and uses it
only when the owner agrees. The hook and the client of its model are Lem's code, with no path
into another tool's folder, and the owner registers the hook with Lem's setup: "I guess this
should not be a cc-tools behaviour but Lem code instead … and it should be possible to setup
during installation of the skill if needed or any time later" (2026-11-15). The form built from
it is the session's design: `skills/lem/scripts/jev.py`, on the `PATH` as the `lem-jev`
command, and the hook that the plugin brings, which the tracked `corrections.collect` turns on.
