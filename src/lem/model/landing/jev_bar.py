"""The bar of rule 6 of the builder's standing rules, as Jev reads a finding against it
(`land.bar_file` and `land.bar_condition` on `main`).

The file is the one whose rule 6 the builders read: the project's own
`.claude/agents/lem-builder.md` in the main checkout when it is there, else Lem's
`agents/lem-builder.md`. Its condition is the sentence "... is filed only for a defect over the
bar: CONDITION." of rule 6, read whole over its line breaks; a project that writes its bar in
its own words has none, and Jev is then not asked, since a question with no bar has no meaning.
"""

import re

# A project's own builder, which `spawn-builder` starts in place of Lem's.
OWN = ".claude/agents/lem-builder.md"
LEMS = "agents/lem-builder.md"
RULE = re.compile(r"(?ms)^6\.\s(.*?)(?=^7\.\s|\Z)")
SENTENCE = re.compile(r"filed only for a defect over the bar:\s*(.+?)\.(?=\s|$)")


def named(*, own: bool) -> str:
    """The name of the bar's file, as a line of the pull request gives it."""
    return OWN if own else LEMS


def condition(text: str) -> str | None:
    """The bar's condition in the text of a builder's standing rules; None when rule 6 has no
    sentence of that form."""
    rule = RULE.search(text)
    if rule is None:
        return None
    plain = rule.group(1).replace("**", "")
    found = SENTENCE.search(" ".join(plain.split()))
    return found.group(1).strip() if found else None
