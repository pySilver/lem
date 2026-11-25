"""Where the texts of Lem give a command line, and whether the tree takes it.

Every `lem NOUN ...` in a code span or a code block of the skills (`skills/**/*.md`), the agents
(`agents/*.md`), the guides (`docs/*.md`, not `docs/plans/`) and README.md, and in a `<code>`
of the site (`site/*.html`), read against the shape of the tree (`shapes.py`).

Where a command line is:

- a code span whose text starts with `lem` and a word after it; a span may run over a line
  break, never over an empty line (`lem land` at the end of a line and `merge-review SLUG
  --no-answer` on the next are one call);
- a line of a code block marked `bash`, `sh`, `shell`, `console` or nothing that starts so,
  with the lines after a trailing backslash joined to it;
- a code span inside any line of any code block, or inside a span of two backticks. A block
  marked `text` or anything else is a transcript or an output: its lines are not calls
  (README.md's `lem  docs: "the footer says Terms"`, where lem is the one who speaks);
- the text of a `<code>` element of a page of the site, as a span.

How a line is read:

- A word that has capitals and no small letter, or that stands in angle brackets, is a
  placeholder for one word: `SLUG`, `"WHY"`, `SLUG-2`, `<pageID>`. In the place of a verb it
  stands for any of them, and the line is right when one of them takes the rest
  (`lem issue STEP SLUG`, `lem NAME ARGS...`). A value with small letters is the word itself,
  and where the slot has choices it must be one of them.
- `A|B` as one word is a choice of values, each a choice of its slot or a placeholder
  (`lem land merge SLUG --by owner|merger`).
- Words in `[...]` may be left out: the line is right both with them and without them.
  `(... | ...)` groups alternatives, and a lone `|` divides them; both are only marks, and
  each option inside is checked.
- `...`, `…` and a placeholder that ends in `...` say that words were left out: the count of
  positional words is not checked where one stands. As an option's value it is the value.
- A code span that gives no positional word after its verb, or gives only the word of a slot
  that has choices, names the command in prose and is not a whole call: its names, options and
  values are checked, and the count is not (`lem land merged`). A code span may also name an
  option without its value (`lem land read --record`). A line of a code block is always a
  whole call.
- From `#` after a space, and from a `<`, `>`, `;` or `&` that is not in quotes, the rest is a
  comment, a redirection or a heredoc, and not read.
- An option is checked at the level it stands. `--flag=value` is the flag and its value. After
  an option the level does not take, the count is not checked: nobody knows whether a value
  follows it. A required option the line leaves out is not a fault: a text gives what it is
  about.
- `lem ask` and `lem jev` put their default verb before a first word that is no verb
  (`lem ask /tmp/session-storage.json`); `--` ends the options (`lem serial -- CMD`).

A text whose lines the tree does not all take yet carries the mark `<!-- lem: old form -->` as
its first line, or as the first line after its front matter, which must stay first for Claude
Code to read a skill. The step that rewrites the text removes the mark.
"""

import html
import re
import shlex
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
# The texts that give command lines to agents and people.
TEXTS = ("skills/**/*.md", "agents/*.md", "docs/*.md", "README.md", "site/*.html")
MARK = "<!-- lem: old form -->"
# The marks of a code block whose lines are shell lines.
SHELL = ("", "bash", "sh", "shell", "console")
CALL = re.compile(r"lem\s+\S")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})\s*([\w+-]*)")
# A code span, over line breaks but not over an empty line (the paragraph is cut at them
# first).
SPAN = re.compile(r"(?<!`)(`+)(?!`)(.+?)(?<!`)\1(?!`)", re.DOTALL)
CODE = re.compile(r"<code[^>]*>(.*?)</code>", re.DOTALL)
TAG = re.compile(r"<[^>]+>")
PLACEHOLDER = re.compile(r"[^a-z]*[A-Z][^a-z]*|<[^<>\s]+>")
# a placeholder in angle brackets, which is no redirection
ANGLE = re.compile(r"<[^<>\s]+>")
LEFT_OUT = ("...", "…")
CANNOT = "cannot judge: "
# The marks of a synopsis, as the scanner writes them in the place of `[`, `]`, `(`, `)` and
# a lone `|` that stand outside quotes.
OPEN, CLOSE, GROUP, UNGROUP, OR = "\x01", "\x02", "\x03", "\x04", "\x05"
MARKS = {"[": OPEN, "]": CLOSE, "(": GROUP, ")": UNGROUP}

type Shape = dict


@dataclass(frozen=True)
class Line:
    path: str
    number: int
    text: str
    # a code span, which may name a command in prose; a line of a code block is a call
    span: bool


@dataclass(frozen=True)
class Word:
    text: str
    # inside `[...]`: the line is right without it too
    optional: bool


def is_call(text: str) -> bool:
    return CALL.match(text) is not None


def spans(text: str, path: str, first: int) -> list[Line]:
    """The command lines in the code spans of TEXT, which starts at line FIRST, and in the
    spans a span of two backticks quotes."""
    found = []
    for match in SPAN.finditer(text):
        said = " ".join(match.group(2).split())
        number = first + text.count("\n", 0, match.start())
        if is_call(said):
            found.append(Line(path, number, said, span=True))
        elif len(match.group(1)) > 1:
            found += spans(match.group(2), path, number)
    return found


def prose(lines: list[tuple[int, str]], path: str) -> list[Line]:
    """The command lines in the code spans of prose LINES, cut at each empty line."""
    found: list[Line] = []
    block: list[tuple[int, str]] = []
    for number, line in [*lines, (0, "")]:
        if line.strip():
            block.append((number, line))
            continue
        if block:
            found += spans("\n".join(text for _, text in block), path, block[0][0])
        block = []
    return found


def lines_of(text: str, path: str) -> list[Line]:
    """Every command line of the Markdown TEXT, in its order."""
    found: list[Line] = []
    outside: list[tuple[int, str]] = []
    rows = text.split("\n")
    fence: tuple[str, str] | None = None
    index = 0
    while index < len(rows):
        number, row = index + 1, rows[index]
        index += 1
        opened = FENCE.match(row)
        if fence is None and opened:
            fence = (opened.group(1), opened.group(2).lower())
            outside.append((number, ""))
            continue
        if fence is not None and row.strip().startswith(fence[0][0] * len(fence[0])):
            fence = None
            outside.append((number, ""))
            continue
        if fence is None:
            outside.append((number, row))
            continue
        outside.append((number, ""))
        whole = row.strip()
        while whole.endswith("\\") and index < len(rows):
            whole = whole[:-1] + " " + rows[index].strip()
            index += 1
        if fence[1] in SHELL and is_call(whole):
            found.append(Line(path, number, " ".join(whole.split()), span=False))
        else:
            found += spans(row, path, number)
    found += prose(outside, path)
    return sorted(found, key=lambda line: line.number)


def page_lines(text: str, path: str) -> list[Line]:
    """Every command line of the HTML page TEXT: the text of each `<code>`, as a span."""
    found = []
    for match in CODE.finditer(text):
        said = " ".join(html.unescape(TAG.sub("", match.group(1))).split())
        if is_call(said):
            number = 1 + text.count("\n", 0, match.start())
            found.append(Line(path, number, said, span=True))
    return found


def texts() -> list[Path]:
    found: set[Path] = set()
    for pattern in TEXTS:
        found.update(path for path in ROOT.glob(pattern) if path.is_file())
    return sorted(found)


def lines_in(path: Path) -> list[Line]:
    """Every command line of the text at PATH."""
    text = path.read_text(encoding="utf-8")
    named = str(path.relative_to(ROOT))
    return page_lines(text, named) if path.suffix == ".html" else lines_of(text, named)


def mark_line(text: str) -> int:
    """The index of the line where the old-form mark stands: the first, or the first after
    the front matter."""
    rows = text.split("\n")
    if rows[0] == "---" and "---" in rows[1:]:
        return rows.index("---", 1) + 1
    return 0


def marked(text: str) -> bool:
    """Whether TEXT carries the old-form mark in its place."""
    rows = text.split("\n")
    at = mark_line(text)
    return at < len(rows) and rows[at] == MARK


def closing(text: str, index: int) -> int:
    """The index after the quote that closes the one at INDEX of TEXT, or its end when none
    does (shlex then refuses the line)."""
    quote = text[index]
    at = index + 1
    while at < len(text) and text[at] != quote:
        at += 2 if quote == '"' and text[at] == "\\" else 1
    return min(at + 1, len(text))


def ends(text: str, index: int, out: list[str]) -> bool:
    """Whether the line's call ends at INDEX: a comment, a redirection or a heredoc starts
    there, or another command."""
    char = text[index]
    return char in "<>;&" or (char == "#" and (not out or out[-1].isspace()))


def mark(text: str, index: int) -> str:
    """The character at INDEX, or the mark of a synopsis it stands for."""
    char = text[index]
    if char in MARKS:
        return f" {MARKS[char]} "
    if char == "|" and text[index - 1 : index + 2].strip() == "|":
        return f" {OR} "
    return char


def scanned(text: str) -> str:
    """TEXT up to its comment, redirection or heredoc, with the marks of a synopsis that
    stand outside quotes written as words of their own."""
    out: list[str] = []
    index = 0
    while index < len(text):
        angle = ANGLE.match(text, index)
        if text[index] in "'\"":
            end = closing(text, index)
        elif text[index] == "\\" or angle:
            end = angle.end() if angle else index + 2
        elif ends(text, index, out):
            # the number of a stream before its redirection, as in 2>&1
            while text[index] in "<>" and out and out[-1].isdigit():
                out.pop()
            break
        else:
            out.append(mark(text, index))
            index += 1
            continue
        out.append(text[index:end])
        index = end
    return "".join(out)


def words_of(text: str) -> list[Word]:
    """The words of TEXT after its command's name; ValueError when its quotes do not close."""
    words: list[Word] = []
    depth: list[str] = []
    for token in shlex.split(scanned(text))[1:]:
        if token in (OPEN, GROUP):
            depth.append(token)
        elif token in (CLOSE, UNGROUP):
            if depth:
                depth.pop()
        elif token != OR:
            words.append(Word(token, optional=OPEN in depth))
    return words


def is_placeholder(text: str) -> bool:
    return PLACEHOLDER.fullmatch(text) is not None


def left_out(text: str) -> bool:
    return text in LEFT_OUT or (is_placeholder(text) and text.endswith(LEFT_OUT))


def is_option(text: str) -> bool:
    return text.startswith("-") and text not in ("-", "--") and not left_out(text)


def bounds(positionals: list[dict]) -> tuple[int, float]:
    low, high = 0, 0.0
    for item in positionals:
        counted = item["count"]
        low += counted in ("1", "+")
        high = float("inf") if counted in ("*", "+") else high + 1
    return low, high


def unchosen(value: str, choices: list[str] | None, where: str) -> list[str]:
    """The parts of VALUE that are no choice of WHERE."""
    if choices is None or is_placeholder(value) or left_out(value):
        return []
    return [
        f"{where} takes {' or '.join(choices)}, not {part}"
        for part in value.split("|")
        if part not in choices and not is_placeholder(part)
    ]


def option_of(level: Shape, flag: str) -> dict | None:
    for name, option in level["options"].items():
        if flag == name or flag in option["aliases"]:
            return option
    return None


def taken(
    level: Shape, words: list[Word], at: int, where: str, *, span: bool
) -> tuple[int, list[str], bool]:
    """The option at AT of WORDS: the index after it and its value, what is wrong, and whether
    LEVEL knows the option (when not, nobody knows whether a value follows)."""
    flag, equal, attached = words[at].text.partition("=")
    option = option_of(level, flag)
    if option is None:
        return at + 1, [f"`{where}` takes no option {flag}"], False
    if not option["value"]:
        return at + 1, [f"{flag} of `{where}` takes no value"] if equal else [], True
    if equal:
        return at + 1, unchosen(attached, option.get("choices"), flag), True
    end = at + 1
    if end < len(words) and not is_option(words[end].text):
        end += 1
    if end == at + 1 and not span:
        return (
            end,
            [f"{flag} of `{where}` takes a value, and the line gives none"],
            True,
        )
    wrong = [
        problem
        for word in words[at + 1 : end]
        for problem in unchosen(word.text, option.get("choices"), flag)
    ]
    return end, wrong, True


def counted(level: Shape, given: list[Word], where: str, *, mention: bool) -> list[str]:
    """What is wrong with GIVEN as the positional words of LEVEL."""
    positionals = level["positionals"]
    wrong = []
    for item, word in zip(positionals, given, strict=False):
        if item["count"] != "1":
            break
        wrong += unchosen(word.text, item.get("choices"), f"`{where}` {item['name']}")
    if mention:
        return wrong
    low, high = bounds(positionals)
    if high == float("inf"):
        takes = f"{low} or more"
    else:
        takes = str(low) if low == high else f"{low} to {int(high)}"
    for number in sorted({len(given), sum(not word.optional for word in given)}):
        if not low <= number <= high:
            wrong.append(
                f"the line gives `{where}` {number} positional words, and it takes {takes}"
            )
    return wrong


def any_of(level: Shape, words: list[Word], where: str, *, span: bool) -> list[str]:
    """What is wrong when the first of WORDS, a placeholder, names a verb: nothing when one of
    the verbs takes the rest."""
    for name, child in level["subcommands"].items():
        if not judge(child, words[1:], f"{where} {name}", span=span):
            return []
    rest = " ".join(word.text for word in words)
    return [f"no subcommand of `{where}` takes `{rest}`"]


def subcommand(
    level: Shape, words: list[Word], at: int, where: str, *, span: bool
) -> list[str] | None:
    """What is wrong when the word at AT of WORDS names a verb of LEVEL; None when it is a
    positional word of LEVEL itself."""
    text = words[at].text
    if text in level["subcommands"]:
        child = level["subcommands"][text]
        return judge(child, words[at + 1 :], f"{where} {text}", span=span)
    if level["positionals"]:
        return None
    if left_out(text):
        return [f"{CANNOT}`{where}` leaves out its subcommand"]
    if is_placeholder(text):
        return any_of(level, words[at:], where, span=span)
    return [f"`{where}` has no subcommand {text}"]


def judge(level: Shape, words: list[Word], where: str, *, span: bool) -> list[str]:
    """What is wrong with WORDS as the words of LEVEL, the shape of the command WHERE."""
    subcommands = level.get("subcommands", {})
    if "default" in level and (not words or words[0].text not in subcommands):
        words = [Word(level["default"], optional=False), *words]
    wrong: list[str] = []
    given: list[Word] = []
    omitted = False
    at = 0
    while at < len(words):
        text = words[at].text
        if text == "--":
            given += words[at + 1 :]
            break
        if is_option(text):
            at, said, known = taken(level, words, at, where, span=span)
            wrong += said
            omitted = omitted or not known
            continue
        chosen = (
            subcommand(level, words, at, where, span=span)
            if subcommands and not given
            else None
        )
        if chosen is not None:
            return wrong + chosen
        omitted = omitted or left_out(text)
        given += [] if left_out(text) else [words[at]]
        at += 1
    if subcommands and level.get("subcommand_required") and not given:
        return wrong if span else [*wrong, f"`{where}` needs a subcommand"]
    mention = span and all(
        n < len(level["positionals"]) and "choices" in level["positionals"][n]
        for n in range(len(given))
    )
    return wrong + counted(level, given, where, mention=mention or omitted)


def verdict(line: Line, tree: Shape) -> list[str]:
    """What is wrong with LINE against the TREE: nothing when the command takes it."""
    try:
        words = words_of(line.text)
    except ValueError as error:
        return [f"{CANNOT}{error}"]
    return judge(tree, words, "lem", span=line.span)
