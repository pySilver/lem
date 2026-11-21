---
decided: 2026-11-18
area: The review, the pull request and the merge
---

# Two things a real run showed on 2026-11-18

## Changed in part

The title is the rule as it stands. Where the paragraph below says otherwise, the line here holds.

- 2026-11-20, [GitHub pull requests are the one way to land](../../docs/rulings/github-pull-requests-are-the-one-way-to-land.md): "`lem land land --by agent`": the session's sentences on it are replaced, the merge is `lem land merge SLUG --by owner|merger`

## As decided on 2026-11-18, changed in part since

On 2026-11-16 the owner gave the design to the session that builds Lem: "You are the owner and
long-term maintainer of this codebase, and its design is up to you. Pick recommended action if
you still see it as best oucome." Two reviews of Lem, by Codex and by Fable, had left the points
below open, and that session decided each under his sentence. None of them is his ruling: each
is the session's, and open to him.

The final round of 2026-11-17 took the decisions below, after two real runs of the plugin form in a
scratch repository (R1 to R6) and the final audit of `636b24c` (A1 to A15).

**Two things a real run showed on 2026-11-18** (pySilver/lem-scratch#5 and #6, with the stage
texts split by path). Lem tried `lem land land --by agent` after a proposal where
`branch.land` is `owner`, because `stages/land.md` told it to try and let the script refuse;
Claude Code's classifier blocked the call and showed the owner "2 actions blocked". The text
now has Lem run it only where the settings say `agent`. And Lem did not know that the watch
covers a pull request opened after it started; `SKILL.md` says so now. The same session
refused a merge on the owner's words as relayed by its operator, as the text asks: nobody
else's word is his.
