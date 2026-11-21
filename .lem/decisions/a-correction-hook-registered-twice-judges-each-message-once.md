---
decided: 2026-11-17
area: The lessons, the correction queue, the naps, the night and the free hour
---

# A correction hook registered twice judges each message once

## Changed in part

The title is the rule as it stands. Where the paragraph below says otherwise, the line here holds.

- 2026-11-17, [Lem is a plugin, and nothing else](../../docs/rulings/lem-is-a-plugin-and-nothing-else.md): "`--corrections on` registers nothing where the plugin or the other scope already starts it": there is no setup script and no `--corrections`

## As decided on 2026-11-17, changed in part since

On 2026-11-16 the owner gave the design to the session that builds Lem: "You are the owner and
long-term maintainer of this codebase, and its design is up to you. Pick recommended action if
you still see it as best oucome." Two reviews of Lem, by Codex and by Fable, had left the points
below open, and that session decided each under his sentence. None of them is his ruling: each
is the session's, and open to him.

The final round of 2026-11-17 took the decisions below, after two real runs of the plugin form in a
scratch repository (R1 to R6) and the final audit of `636b24c` (A1 to A15).

**A correction hook registered twice judges each message once** (2026-11-17). A scratch
repository moved from the links to the plugin and kept the hook that `setup.py --corrections
on` had written, beside the plugin's own: two calls of the model and two queue entries for
each message, and nothing said so. The maintaining session listed it for the owner as a thing
to clean in that repository and called the pass done; he asked "so we need to fix that?". It
is a class: three places can register the hook (the home's settings, a repository's, the
plugin), and any two double it. So the hook claims each message (the session and the words,
for `CLAIM_SECONDS`) before it hands it on, and a second copy exits; the machine check has a
row when more than one place registers the hook, with the command that removes one; and
`--corrections on` registers nothing where the plugin or the other scope already starts it.
One run of Claude Code with two registrations in a throwaway repository: 2 calls and 2 entries
with the script before the change, 1 and 1 after it (2026-11-17). A defect of Lem that a run
shows is fixed in Lem, also when one repository can be cleaned by hand.
