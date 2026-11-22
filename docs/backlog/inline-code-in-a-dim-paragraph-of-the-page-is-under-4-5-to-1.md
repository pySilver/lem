---
worth: later
where: site/style.css:p code, li code
added: 2026-11-22
---
# Inline code in a dim paragraph of the page is under 4.5 to 1

The rule `p code, li code` in `site/style.css` gives inline code a `--card-hi` box and a border, but
no color of its own, so the code takes the color of its paragraph. In a paragraph drawn in `--dim`,
in the light theme, the text on that box is weaker than 4.5 to 1: the agterm note's `/lem init` in
the opening measured about 4.4 to 1 on main (the build of the task hero-logo-animated-background,
2026-11-21). That task gave `.needs code` the full text color, so the opening is fixed. The other
inline code of `site/index.html` stands on the same box and was not measured: `/lem serve join
HOST`, `/lem serve tailscale`, `branch.land = "owner"`, the `/lem init` of the install section and
`.lem/` in the line on what Lem keeps. Measure each in both themes, as `tests/test-site.sh` measures
the hero's texts, and give the rule a color that holds 4.5 to 1 where one is under it.
