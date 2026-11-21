---
decided: 2026-11-17
area: The settings, the seats and the tracker
---

# Onboarding asks three questions

## Changed in part

The title is the rule as it stands. Where the paragraph below says otherwise, the line here holds.

- 2026-11-18, [Not every section of the settings stays](../../docs/rulings/not-every-section-of-the-settings-stays.md): "the folders already there, linked": Lem's own files and the folders of other tools have one place each
- 2026-11-20, [A fresh merge agent reads every proposed task, and merges it or calls him](../../docs/rulings/a-fresh-merge-agent-reads-every-proposed-task-and-merges-it-or-calls-him.md): "who lands (`owner`)": the default is `"agent"`
- 2026-11-20, [GitHub pull requests are the one way to land](../../docs/rulings/github-pull-requests-are-the-one-way-to-land.md): "a pull request where the remote is GitHub": GitHub pull requests are the one way to land

## As decided on 2026-11-17, changed in part since

On 2026-11-16 the owner gave the design to the session that builds Lem: "You are the owner and
long-term maintainer of this codebase, and its design is up to you. Pick recommended action if
you still see it as best oucome." Two reviews of Lem, by Codex and by Fable, had left the points
below open, and that session decided each under his sentence. None of them is his ruling: each
is the session's, and open to him.

**Onboarding asks three questions** (2026-11-17). The audit counted about ten questions and
several offers before the first task, each a page, and 20 to 40 minutes to it (F10, an
unmeasured estimate). `/lem init` asks only what only the developer knows: what the product is
and who it is for, the people a change affects (two or more, his ruling), and what must never
go wrong, each with Lem's proposal from the code. Every other setting is read from the
repository or defaulted and shown on the hand-over page as an assumption he corrects with
"change ...": who lands (`owner`), a pull request where the remote is GitHub, what lands, the
closed branches, the tracker (none, or Linear when the repository shows it, after the
tracker's check), the reviewer and the defender with their models, and the folders already
there, linked: shown on the page with the word that changes it, so the choice is the owner's and
no default is silent. The offers (the correction queue, with what he agrees to, the
recommended tools, cronn and the scheduled jobs) are one short list at the end of the page,
never a question each. The reviewer seat's `effort` for a diff and the diff half of
`prompts/reviewer.md` are gone (W7).
