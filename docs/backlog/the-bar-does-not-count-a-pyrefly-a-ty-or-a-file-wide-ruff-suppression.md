---
worth: yes
where: src/lem/land.py:BAR
added: 2026-11-24
---
# The bar does not count a pyrefly, a ty or a file-wide ruff suppression

The marks of `.py` in `BAR` count `# noqa`, `# type: ignore` and `# pyright: ignore`, but not
`# pyrefly: ignore`, `# ty: ignore` or `# ruff: noqa` (`#\s*noqa` needs `noqa` right after the `#`).
Run at c674b18d: `bar_of` on a diff that adds `x = f()  # pyrefly: ignore[bad-assignment]`,
`# ty: ignore` or `# ruff: noqa: E501` to `m.py` names no lowered mark, and names `# noqa` and
`# type: ignore` for those forms. The three should count as a `# noqa` does. A fix of `BAR` reaches
"the bar went lower" in `.lem/settings.toml`, so its task is careful.

Seen in the night of 2026-11-24, when pyrefly and ruff came to this repository.
