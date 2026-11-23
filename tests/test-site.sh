#!/usr/bin/env bash
# Lem's page on GitHub Pages: site/index.html and site/style.css, and the workflow that publishes them
# by hand, .github/workflows/pages.yml. The suite takes the workflow's own copy step out of pages.yml
# by its name, runs it in a throwaway folder that holds a copy of site/ and assets/, and reads the page
# there, as Pages would serve it. The checks of the text, the links, the colors and the workflow run
# everywhere; the checks of a drawn page (the first screen at 1280 px, the scene behind the hero, a phone
# at 390 px, each hero text's contrast, the copy buttons, the light and the dark theme) need headless Chrome,
# and print SKIP lines where none starts.
# LEM_SITE_SHOTS=DIR also writes pictures of the page there: 1280 x 800 and the whole page, light and dark.
set -eEuo pipefail

cd "$(dirname "$0")/.."
# shellcheck source-path=SCRIPTDIR source=checks.sh
. tests/checks.sh
collected
ROOT=$PWD
WORK=$(cd "$(mktemp -d)" && pwd -P)
export XDG_CONFIG_HOME="$WORK/config"  # the owner's status (`lem_state.owner_mark`) of this run, never the home directory's
trap 'stopped; rm -rf "$WORK"' EXIT
PY=$(python3 -I -c 'import sys; print(sys.executable)')
STEP_NAME="Make the folder to publish"

# The workflow's copy step, run as it is written, in a folder with the repository's site/ and assets/
mkdir -p "$WORK/repo"
cp -R site assets "$WORK/repo/"
"$PY" -I -B -c '
import re, sys, textwrap
text, name = open(sys.argv[1], encoding="utf-8").read(), sys.argv[2]
found = re.search(r"(?m)^(\s*)- name: " + re.escape(name) + r"\n\1  run: \|\n((?:\1    .*\n|\s*\n)+)", text)
if not found:
    sys.exit(f"pages.yml has no step named {name!r} with a run block")
print(textwrap.dedent(found.group(2)), end="")' .github/workflows/pages.yml "$STEP_NAME" > "$WORK/step.sh"
copy_said=""
if ! copy_said=$(cd "$WORK/repo" && bash -euo pipefail "$WORK/step.sh" 2>&1); then copy_said="the step failed: $copy_said"; fi
SITE=$WORK/repo/_site

# ---- the checks that read files: one Python run, one verdict for each check ----
STATIC=$(cat <<'PY'
import json, re, subprocess, sys
from html.parser import HTMLParser
from pathlib import Path

root, site, workflow = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
page_file = site / "index.html"
page = page_file.read_text(encoding="utf-8") if page_file.is_file() else ""
css_file = site / "style.css"
css = css_file.read_text(encoding="utf-8") if css_file.is_file() else ""
flow = workflow.read_text(encoding="utf-8")
verdict = {}
LINES = ["claude plugin marketplace add pySilver/lem --scope project", "claude plugin install lem@lem --scope project"]
REPO = "https://github.com/pySilver/lem"
GUIDE = re.compile(re.escape(REPO) + r"/blob/main/(docs/[\w.-]+\.md)(?:#([^\"'\s]*))?$")
IMAGES = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".avif", ".ico", ".bmp")

# A small tree of the page: each element with its tag, attributes, children and text.
class Node:
    def __init__(self, tag, attrs, parent):
        self.tag, self.attrs, self.parent, self.kids = tag, dict(attrs), parent, []
    def classes(self):
        return (self.attrs.get("class") or "").split()
    def walk(self):
        for kid in self.kids:
            if isinstance(kid, Node):
                yield kid
                yield from kid.walk()
    def find(self, test):
        return [node for node in self.walk() if test(node)]
    def text(self, blocks=False):
        out = []
        for kid in self.kids:
            if isinstance(kid, str):
                out.append(kid)
            elif kid.tag not in ("script", "style", "head", "title"):
                inner = kid.text(blocks)
                out.append(f"\n{inner}\n" if blocks and kid.tag in BLOCK else inner)
        return "".join(out)
BLOCK = {"p", "li", "h1", "h2", "h3", "h4", "figcaption", "div", "section", "footer", "nav", "ol", "ul", "figure", "main", "pre", "br", "picture"}
VOID = {"meta", "link", "img", "source", "br", "hr", "input"}
class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.top = Node("#root", [], None)
        self.at = self.top
    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.at)
        self.at.kids.append(node)
        if tag not in VOID:
            self.at = node
    def handle_endtag(self, tag):
        node = self.at
        while node is not self.top and node.tag != tag:
            node = node.parent
        if node is not self.top:
            self.at = node.parent
    def handle_data(self, data):
        self.at.kids.append(data)
tree = Tree()
tree.feed(page)
top = tree.top
body = next(iter(top.find(lambda n: n.tag == "body")), top)
flat = lambda text: re.sub(r"\s+", " ", text).strip()
visible = body.text()
lines = [flat(line) for line in body.text(blocks=True).split("\n") if flat(line)]
alts = " ".join(node.attrs.get("alt", "") for node in body.find(lambda n: n.tag == "img"))
words = [word for word in visible.split() if re.search(r"[A-Za-z0-9]", word)]
sections = body.find(lambda n: n.tag == "section")
footer = next(iter(body.find(lambda n: n.tag == "footer")), None)
links = [node.attrs.get("href", "") for node in body.find(lambda n: n.tag == "a")]

def heading_slugs(path):
    """The anchors GitHub makes for the headings of a markdown file."""
    slugs = set()
    fence = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("```"):
            fence = not fence
        found = None if fence else re.match(r"#{1,6}\s+(.*?)\s*#*\s*$", line)
        if found:
            title = re.sub(r"[`*_]|\[([^\]]*)\]\([^)]*\)", lambda m: m.group(1) or "", found.group(1))
            slugs.add(re.sub(r" ", "-", re.sub(r"[^\w\- ]", "", title.lower())))
    return slugs

def install_block(section):
    blocks = section.find(lambda n: "install" in n.classes()) if section else []
    if not blocks:
        return "it has no install block"
    rows = blocks[0].find(lambda n: "cmd" in n.classes())
    got = [flat(next(iter(row.find(lambda n: n.tag == "code")), Node("x", [], None)).text()) for row in rows]
    if got != LINES:
        return f"its install lines are {got}, not {LINES}"
    if any(len(row.find(lambda n: n.tag == "button" and "copy" in n.classes())) != 1 for row in rows):
        return "a line has no copy button of its own"
    return ""

# 1: the first screen, in the markup (where each part is drawn is a check of the drawn page)
first = sections[0] if sections else None
problems = []
if first is not None:
    problems.append(install_block(first))
    if not first.find(lambda n: n.tag == "picture" and n.find(lambda s: s.tag == "img" and s.attrs.get("src") == "assets/lem.svg")):
        problems.append("it has no logo")
    if "Type a request in plain words, and get a pull request whose first line says green or not green." not in flat(first.text()):
        problems.append("it has not the README's line")
    needs = first.find(lambda n: "needs" in n.classes())
    needs_text = flat(needs[0].text()) if needs else ""
    if not needs_text.startswith("Lem needs agterm.") or "Run the two lines in your repository, then type /lem init." not in needs_text:
        problems.append(f"the line under the install reads {needs_text!r}")
    if not needs or "https://agterm.com" not in [a.attrs.get("href") for a in needs[0].find(lambda n: n.tag == "a")]:
        problems.append("the line under the install has no link to https://agterm.com")
else:
    problems.append("the page has no section")
verdict["first"] = "; ".join(p for p in problems if p)

# 2: six sections in order, each known by its id, then a footer; the nav at the top links four of them
order = [section.attrs.get("id", "") for section in sections]
want = ["start", "board", "flow", "phone", "parallel", "install"]
footer_last = footer is not None and page.rfind("</section>") < page.find("<footer")
problems = [] if order == want and footer_last else [f"the sections read as {order}, the footer after them: {footer_last}"]
nav = [a.attrs.get("href", "") for a in body.find(lambda n: n.tag == "a" and n.parent is not None and "top" in n.parent.classes())]
missing_nav = [f"#{name}" for name in ("board", "flow", "phone", "install") if f"#{name}" not in nav]
if missing_nav:
    problems.append(f"the nav does not link {missing_nav}")
verdict["sections"] = "; ".join(problems)
verdict["words"] = "" if 800 <= len(words) <= 1200 else f"{len(words)} words"
verdict["words_count"] = str(len(words))

# 2: the diagram, one row for each track, the steps of the developer marked with the class you
def you_steps(track):
    rows = body.find(lambda n: "track" in n.classes() and track in n.classes())
    if not rows:
        return None
    return [flat(step.text()) for step in rows[0].find(lambda n: "step" in n.classes() and "you" in n.classes())]
fast, standard = you_steps("fast"), you_steps("standard")
problems = []
if fast is None or standard is None:
    problems.append("the diagram has no row for the fast track or the standard track")
else:
    if len(fast) != 1 or "merge" not in fast[0]:
        problems.append(f"the fast track's steps for the developer are {fast}")
    if len(standard) != 3 or not ("Interview" in standard[0] and "criteria" in standard[1] and "merge" in standard[2]):
        problems.append(f"the standard track's steps for the developer are {standard}")
verdict["diagram"] = "; ".join(problems)
verdict["green"] = "" if "Green means you can merge without a read." in flat(visible) else "the sentence is not on the page"

# 2: the install again, with what Lem keeps and the way to remove it
last = sections[-1] if sections else None
problems = [install_block(last)] if last is not None else ["no last section"]
if last is not None:
    keeps = [node for node in last.find(lambda n: n.tag == "p") if ".lem/" in node.text()]
    removal = [a.attrs.get("href", "") for node in keeps for a in node.find(lambda n: n.tag == "a")]
    if not keeps:
        problems.append("no sentence names .lem/")
    elif not any(GUIDE.match(href) and href.split("#")[0].endswith("docs/install.md") and href.endswith("#remove") for href in removal):
        problems.append(f"the sentence that names .lem/ links {removal}, not the removal steps of docs/install.md")
verdict["again"] = "; ".join(p for p in problems if p)

# 2: the footer links the seven guides, the settings and the repository
need = {"docs/flow.md", "docs/when-lem-needs-you.md", "docs/board.md", "docs/pull-request.md", "docs/install.md", "docs/linear.md", "docs/github-issues.md", "docs/settings.md"}
footer_links = [a.attrs.get("href", "") for a in footer.find(lambda n: n.tag == "a")] if footer else []
linked = {GUIDE.match(href).group(1) for href in footer_links if GUIDE.match(href)}
missing = sorted(need - linked) + ([] if REPO in footer_links else [REPO])
verdict["footer"] = "" if not missing else f"the footer does not link {missing}"

# 3: sentences, in the README's STE: 25 words at most, 20 for an instruction
IMPERATIVE = {"Type", "Run", "Answer", "Read", "Install", "Start", "Say", "Open", "Copy", "See", "Follow", "Remove", "Pick", "Use", "Merge", "Land", "Drop", "Ask", "Add", "Put", "Delete", "Commit", "Set", "Let"}
long = []
for line in lines:
    for sentence in re.split(r"(?<=[.!?])\s+", line):
        count = len([w for w in sentence.split() if re.search(r"[A-Za-z0-9]", w)])
        first_word = re.sub(r"\W", "", sentence.split()[0]) if sentence.split() else ""
        limit = 20 if first_word in IMPERATIVE else 25
        if count > limit:
            long.append(f"{count} words (at most {limit}): {sentence!r}")
verdict["sentences"] = "; ".join(long)
oses = sorted(set(re.findall(r"\b(macOS|Mac|Linux|Windows)\b", page)))
verdict["os"] = "" if not oses else f"it names {oses}"
history = sorted(set(re.findall(r"(?i)\b(proven|not run|previously|no longer|new in)\b", visible + " " + alts) + re.findall(r"\b(?:19|20)\d\d\b", visible + " " + alts)))
verdict["history"] = "" if not history else f"it says {history}"
problems = []
if "Lem is a plugin for Claude Code that works closely with agterm." not in flat(visible):
    problems.append("it does not call Lem a plugin for Claude Code that works closely with agterm")
if "Lem needs agterm." not in flat(visible):
    problems.append("it does not say that Lem needs agterm")
verdict["plugin"] = "; ".join(problems)
problems = []
dialogs = body.find(lambda n: "dialog" in n.classes())
if not dialogs:
    problems.append("the page marks no example dialog")
for number, dialog in enumerate(dialogs, 1):
    caption = dialog.find(lambda n: n.tag == "figcaption")
    if not caption or "illustration" not in caption[0].text():
        problems.append(f"example dialog {number} has no caption that says illustration")
shots = body.find(lambda n: n.tag == "figure" and n.find(lambda i: i.tag == "img" and i.attrs.get("src", "").startswith("assets/screens/")))
if not shots:
    problems.append("no figure shows a picture of the board")
for shot in shots:
    names = [i.attrs.get("src") for i in shot.find(lambda n: n.tag == "img")]
    if not any("demo data" in c.text() for c in shot.find(lambda n: n.tag == "figcaption")):
        problems.append(f"the caption of {names} does not say demo data")
verdict["captions"] = "; ".join(problems)

# 4: the pictures for each theme, the hues and the other colors, and no switch
def picture_of(light, dark):
    for picture in body.find(lambda n: n.tag == "picture"):
        img = picture.find(lambda n: n.tag == "img")
        source = picture.find(lambda n: n.tag == "source")
        if img and img[0].attrs.get("src") == light:
            if source and source[0].attrs.get("media") == "(prefers-color-scheme: dark)" and source[0].attrs.get("srcset") == dark:
                return ""
            return f"the picture of {light} has no dark source {dark}"
    return f"no picture shows {light}"
verdict["pictures"] = "; ".join(p for p in (picture_of("assets/lem.svg", "assets/lem-night.svg"),
                                             picture_of("assets/screens/board-light.png", "assets/screens/board-dark.png"),
                                             picture_of("assets/screens/phone-light.png", "assets/screens/phone-dark.png"),
                                             picture_of("assets/screens/task-light.png", "assets/screens/task-dark.png")) if p)
# each picture of the board says its size in CSS pixels, half the file's pixels (the pictures are drawn at
# two device pixels for each pixel), so the page keeps its place before the picture loads
def png_size(path):
    head = path.read_bytes()[:24]
    return (int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")) if head[:8] == b"\x89PNG\r\n\x1a\n" else None
problems = []
for img in body.find(lambda n: n.tag == "img" and n.attrs.get("src", "").startswith("assets/screens/")):
    src = img.attrs["src"]
    files = [root / src] + [root / s.attrs["srcset"] for s in img.parent.find(lambda n: n.tag == "source")] if img.parent else [root / src]
    said = (int(img.attrs.get("width") or 0), int(img.attrs.get("height") or 0))
    for file in files:
        real = png_size(file) if file.is_file() else None
        if real != (said[0] * 2, said[1] * 2):
            problems.append(f"{src} says {said[0]} x {said[1]}, and {file.relative_to(root)} is {real}")
verdict["sizes"] = "; ".join(problems)
hues = dict(re.findall(r"--(lead|lem|you|bad|gate|ok):\s*(#[0-9a-fA-F]{6})", (root / "skills/lem/assets/lem.css").read_text(encoding="utf-8")))
bare = re.sub(r"(?s)/\*.*?\*/", "", css)
mine = dict(re.findall(r"--(lead|lem|you|bad|gate|ok):\s*(#[0-9a-fA-F]{3,8})", bare))
problems = [] if len(hues) == 6 and mine == hues else [f"the six hues are {mine}, and lem.css has {hues}"]
allowed = {value.lower() for value in hues.values()}
for color in re.findall(r"#[0-9a-fA-F]{3,8}\b", bare):
    value = color.lower()
    full = "".join(c * 2 for c in value[1:4]) if len(value) in (4, 5) else value[1:7]
    if value not in allowed and not (full[0:2] == full[2:4] == full[4:6]):
        problems.append(f"{color} is not a hue of lem.css and not a grey")
for function in re.findall(r"\b(?:rgba?|hsla?|hwb|lab|lch|oklab|oklch)\([^)]*\)", bare):
    parts = re.findall(r"[\d.]+%?", function)
    if not (function.startswith("rgb") and len(parts) >= 3 and parts[0] == parts[1] == parts[2]):
        problems.append(f"{function} is not a grey")
NAMED = ("red", "green", "blue", "orange", "yellow", "purple", "pink", "brown", "teal", "navy", "olive", "maroon", "lime", "aqua", "fuchsia",
         "cyan", "magenta", "gold", "coral", "salmon", "indigo", "violet", "crimson", "tomato", "khaki", "beige", "ivory", "lavender", "orchid",
         "plum", "tan", "turquoise", "chocolate", "sienna", "peru", "wheat", "skyblue", "steelblue", "seagreen", "goldenrod")
for name in NAMED:
    if re.search(r"(?<![\w-])" + name + r"(?![\w-])", bare, re.I):
        problems.append(f"the named color {name}")
verdict["colors"] = "; ".join(problems)
problems = []
for button in body.find(lambda n: n.tag in ("button", "input", "select")):
    if not (button.tag == "button" and "copy" in button.classes()):
        problems.append(f"a {button.tag} that is no copy button: {flat(button.text()) or button.attrs}")
script = " ".join(node.text() for node in top.find(lambda n: n.tag == "script"))
for word in ("prefers-color-scheme", "colorScheme", "color-scheme", "localStorage", "dataset.theme", "theme"):
    if word in script:
        problems.append(f"the script names {word}")
verdict["switch"] = "; ".join(problems)

# the page draws nothing from another host: no script, stylesheet, picture or font from a URL
problems = []
for node in top.find(lambda n: n.tag in ("script", "link", "img", "source", "iframe", "video", "audio")):
    for key in ("src", "srcset", "href"):
        if re.match(r"(https?:)?//", node.attrs.get(key, "")):
            problems.append(f"<{node.tag} {key}={node.attrs[key]}>")
problems += re.findall(r"@import[^;]*|url\(\s*['\"]?(?:https?:)?//[^)]*\)", bare)
verdict["local"] = "; ".join(problems)

# 5: what site/ holds, in git and on the disk
tracked = subprocess.run(["git", "-C", str(root), "ls-files", "site"], capture_output=True, text=True, check=True).stdout.split()
verdict["tracked"] = "" if tracked == ["site/index.html", "site/style.css"] else f"git ls-files site gives {tracked}"
images = sorted(str(path.relative_to(root)) for path in (root / "site").rglob("*") if path.is_file() and path.suffix.lower() in IMAGES)
verdict["no_image"] = "" if not images else f"{images} under site/"

# 6: the workflow, the copied folder and the links to the guides
problems = []
on = re.search(r"(?m)^on:[ \t]*\n((?:[ \t]+.*\n|[ \t]*\n)*)", flow)
triggers = re.findall(r"(?m)^  (\w[\w-]*):", on.group(1)) if on else []
if triggers != ["workflow_dispatch"]:
    problems.append(f"its triggers are {triggers or 'not a block'}")
inline = re.search(r"(?m)^on:[ \t]*\S", flow)
if inline:
    problems.append("its on: names triggers on one line")
for key in ("push", "pull_request", "pull_request_target", "schedule", "workflow_run"):
    if re.search(r"(?m)^\s*" + key + r"\s*:", flow):
        problems.append(f"it names {key}")
verdict["trigger"] = "; ".join(problems)
problems = []
for line in ("pages: write", "id-token: write", "name: github-pages"):
    if not re.search(r"(?m)^\s*" + re.escape(line) + r"\s*$", flow):
        problems.append(f"it has no {line!r}")
for action in ("actions/checkout@", "actions/configure-pages@", "actions/upload-pages-artifact@", "actions/deploy-pages@"):
    if action not in flow:
        problems.append(f"it uses no {action}")
verdict["workflow"] = "; ".join(problems)
published = sorted(str(path.relative_to(site)) for path in site.rglob("*") if path.is_file()) if site.is_dir() else []
want = ["assets/lem-mark.svg", "assets/lem-night.svg", "assets/lem.svg", "assets/screens/board-dark.png", "assets/screens/board-light.png", "assets/screens/phone-dark.png",
        "assets/screens/phone-light.png", "assets/screens/task-dark.png", "assets/screens/task-light.png", "index.html", "style.css"]
named = sorted({node.attrs.get(key) for node in top.find(lambda n: n.tag in ("img", "source", "link")) for key in ("src", "srcset", "href")
                if node.attrs.get(key) and not re.match(r"(https?:)?//", node.attrs.get(key))})
absent = [path for path in named if not (site / path).is_file()]
problems = []
if published != want:
    problems.append(f"the copied folder holds {published}")
if absent:
    problems.append(f"the page names {absent}, which the copied folder does not hold")
verdict["copied"] = "; ".join(problems)
problems = []
guides = [href for href in links if href.startswith(REPO + "/blob/")]
if not guides:
    problems.append("the page links no guide")
for href in guides:
    found = GUIDE.match(href)
    if not found or not (root / found.group(1)).is_file():
        problems.append(f"{href} names no file of docs/ in the checkout")
    elif found.group(2) and found.group(2) not in heading_slugs(root / found.group(1)):
        problems.append(f"{href}: {found.group(1)} has no heading #{found.group(2)}")
verdict["guides"] = "; ".join(problems)

# 7: the scene, assets/lem.svg, and the night file assets/night.py writes from it; the README and the page show both
SCENES = {"day": root / "assets/lem.svg", "night": root / "assets/lem-night.svg"}
scenes = {theme: path.read_text(encoding="utf-8") if path.is_file() else "" for theme, path in SCENES.items()}
def attrs_of(tag):
    return dict(re.findall(r'([\w:-]+)="([^"]*)"', tag))
def seconds(value):
    found = re.fullmatch(r"(-?[\d.]+)(m?s)", value.strip())
    return float(found.group(1)) / (1000 if found.group(2) == "ms" else 1) if found else None
def rules(svg):
    """Each rule of the scene's style outside its keyframes and media rules: selector to its declarations."""
    style = "\n".join(re.findall(r"(?s)<style>(.*?)</style>", svg))
    flat_style = re.sub(r"@(?:keyframes|media)[^{]*\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}", "", style)
    return {sel.strip(): dict((k.strip(), v.strip()) for k, v in re.findall(r"([\w-]+)\s*:\s*([^;]+)", body))
            for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", flat_style)}
def frames(svg, name):
    """The keyframes NAME as a list of (percent, declarations)."""
    found = re.search(r"@keyframes\s+" + re.escape(name) + r"\s*\{((?:[^{}]*\{[^{}]*\})*)[^{}]*\}", svg)
    out = []
    for stops, body in re.findall(r"([^{}]+)\{([^{}]*)\}", found.group(1) if found else ""):
        decl = dict((k.strip(), v.strip()) for k, v in re.findall(r"([\w-]+)\s*:\s*([^;]+)", body))
        for stop in stops.split(","):
            stop = stop.strip()
            out.append((0.0 if stop == "from" else 100.0 if stop == "to" else float(stop.rstrip("%")), decl))
    return sorted(out, key=lambda pair: pair[0])
def animation(rule):
    """The name, the duration and the delay of a rule's animation shorthand."""
    parts = (rule or {}).get("animation", "").split()
    times = [seconds(p) for p in parts if seconds(p) is not None]
    names = [p for p in parts if seconds(p) is None and p not in ("linear", "ease-in-out", "ease", "infinite", "alternate", "none", "!important")]
    return (names[0] if names else None, times[0] if times else None, times[1] if len(times) > 1 else 0.0)
def elements(svg, cls):
    return [attrs_of(tag) for tag in re.findall(r"<\w+\b[^>]*\bclass=\"" + re.escape(cls) + r"\"[^>]*>", svg)]
def inline(attrs, key):
    found = re.search(re.escape(key) + r"\s*:\s*([^;]+)", attrs.get("style", ""))
    return found.group(1).strip() if found else None
def hexes(svg):
    return set(re.findall(r"#[0-9a-f]{6}\b", svg))

# The logo's signal (docs/plans/2026-11-23-logo-eyes-signal-and-favicon.md, its criteria 1 to 5): Lem's hands, the
# four agents' strands and their red eyes. An agent is a group under a translate and a scale that holds a hood's
# opening, a path from 4 -47 or -4 -47; the agents' strands are the first path under <!-- strands from the line -->,
# the word's the second.
NUMBER = r"-?(?:\d+\.?\d*|\.\d+)"
SEGMENT = re.compile(r"M(" + NUMBER + r") (" + NUMBER + r")L(" + NUMBER + r") (" + NUMBER + r")")
ANIMATED = {"stars", "haze", "hazein", "fan", "ray", "heat1", "heat2", "star", "band1", "band2", "breathe1", "breathe2", "eye", "hand", "spark", "wake"}
GONE = ("pulse", "flash", "drip", "glow", "tile", "flare", "lit")
LEM_X = 130  # the coat's middle: the two agents whose strands are nearest to it are the inner pair
def agents(svg):
    """Each small agent: its translate and scale, the box of its hood's opening, its red dots and its lit eyes."""
    out = []
    for tx, ty, scale, body in re.findall(r'(?s)<g transform="translate\((' + NUMBER + r") (" + NUMBER + r")\) scale\((" + NUMBER + r')\)">((?:(?!</?g\b).)*)</g>', svg):
        hood = re.search(r'<path d="M(-?4 -47C[^"]*)"', body)
        if not hood:
            continue
        nums = [float(n) for n in re.findall(NUMBER, hood.group(1))]
        circles = [attrs_of(tag) for tag in re.findall(r"<circle\b[^>]*>", body)]
        out.append({"x": float(tx), "y": float(ty), "scale": float(scale),
                    "box": (min(nums[0::2]), max(nums[0::2]), min(nums[1::2]), max(nums[1::2])),
                    "dots": [c for c in circles if c.get("fill") == "#ff2a1a"], "lit": [c for c in circles if c.get("class") == "wake"]})
    return out
def strands(svg):
    """The segments (x1, y1, x2, y2) of the agents' strands and of the word's."""
    at = svg.find("<!-- strands from the line -->")
    paths = re.findall(r'<path d="([^"]*)"', svg[at:])[:2] if at >= 0 else []
    return tuple([tuple(float(n) for n in s) for s in SEGMENT.findall(d)] for d in paths) if len(paths) == 2 else ([], [])
def delay_of(attrs, rule):
    own = inline(attrs, "animation-delay")
    return seconds(own) if own else animation(rule)[2]
def eye_colors(svg, part):
    gradient = re.search(r'(?s)<radialGradient id="c2n?-eye">.*?</radialGradient>', svg)
    return hexes(part) | hexes(gradient.group(0) if gradient else "")
def red(colors):
    return bool(colors) and all(int(c[1:3], 16) > 200 and int(c[3:5], 16) < 80 and int(c[5:7], 16) < 80 for c in colors)

# criterion 1 of the signal's plan: a red eye in the hood of each of the four agents: a dot that nothing animates, no
# smaller than the core of Lem's own eye, and over it a light of its own; the red of Lem's eye, the same day and night
problems, reds = [], {}
for theme, svg in scenes.items():
    found, eye = agents(svg), re.search(r'<g class="eye">(.*?)</g>', svg)
    cores = [float(c["r"]) for c in map(attrs_of, re.findall(r"<circle\b[^>]*>", eye.group(1) if eye else "")) if c.get("fill") == "#ff2a1a" and "r" in c]
    frame = re.search(r'</defs>\s*<g transform="translate\([^)]*\) scale\((' + NUMBER + r')\)">', svg)
    readme = float(frame.group(1)) * 720 / 1600 if frame else 0.0  # px for one unit of the scene in the README, 720 px wide
    if len(found) != 4 or not cores:
        problems.append(f"the {theme} scene has {len(found)} agents with a hood, not 4, and {len(cores)} red cores in Lem's eye")
        continue
    colors = set()
    for agent in found:
        where = f"the {theme} scene's agent at x {agent['x']:g}"
        if len(agent["dots"]) != 1 or len(agent["lit"]) != 1:
            problems.append(f"{where} has {len(agent['dots'])} red dots and {len(agent['lit'])} lit eyes in its hood, not one of each")
            continue
        dot, lit = agent["dots"][0], agent["lit"][0]
        cx, cy, r = (float(dot.get(key, "nan")) for key in ("cx", "cy", "r"))
        left, right, top, bottom = agent["box"]
        if not (left < cx < right and top < cy < bottom):
            problems.append(f"{where}: its red dot at {cx:g}, {cy:g} is outside its hood's opening")
        if "class" in dot or "style" in dot:
            problems.append(f"{where}: an animation touches its red dot")
        if not r * agent["scale"] >= max(cores):
            problems.append(f"{where}: its red dot is {2 * r * agent['scale'] * readme:.2f} px wide in the README, smaller than Lem's eye ({2 * max(cores) * readme:.2f} px)")
        if (lit.get("cx"), lit.get("cy")) != (dot.get("cx"), dot.get("cy")) or not float(lit.get("r", "0")) > r or not re.fullmatch(r"url\(#c2n?-eye\)", lit.get("fill", "")):
            problems.append(f"{where}: its light is not the eye's gradient over its red dot")
        colors |= eye_colors(svg, dot.get("fill", ""))
    reds[theme] = colors
    if not red(colors) or colors != eye_colors(svg, eye.group(1)):
        problems.append(f"the {theme} scene's agents' eyes are {sorted(colors)}, not the red of Lem's eye, {sorted(eye_colors(svg, eye.group(1)))}")
if reds.get("day") != reds.get("night"):
    problems.append(f"the agents' eyes are {sorted(reds.get('day', []))} by day and {sorted(reds.get('night', []))} at night")
verdict["scene_eyes"] = "; ".join(problems)

# criterion 2 of the signal's plan: in one cycle of 8 s both hands glow at one moment; then a glow runs down the
# strands of the two inner agents from their tops, and later down the two outer ones'. Each agent's eye starts to light
# when its strand's glow reaches the strand's lower end, computed from the glow's delay, duration and keyframes, within
# 0.2 s (a guess, not measured: a check of the order alone passes an eye that lights a second late).
problems = []
for theme, svg in scenes.items():
    style, (mine, words) = rules(svg), strands(svg)
    names = {}
    for cls in (".hand", ".spark", ".wake"):
        name, duration, _ = animation(style.get(cls))
        names[cls] = name or ""
        if duration != 8 or not frames(svg, name or "") or "linear" not in style.get(cls, {}).get("animation", "").split():
            problems.append(f"the {theme} scene's {cls} runs {name} in {duration} s, not linear keyframes in the cycle of 8 s")
    if len(mine) != 4 or len(words) != 4:
        problems.append(f"the {theme} scene has {len(mine)} strands of the agents and {len(words)} of the word, not 4 of each")
        continue
    hands = elements(svg, "hand")
    left = sorted({delay_of(hand, style.get(".hand")) for hand in hands})
    if len(hands) != 2 or len(left) != 1:
        problems.append(f"the {theme} scene glows {len(hands)} hands from {left} s, not 2 at one moment")
    for hand in hands:
        cx, cy, r = (float(hand.get(key, "nan")) for key in ("cx", "cy", "r"))
        if not (cx - r >= 117 and cx + r <= 143 and abs(cy - 105.5) <= 3):
            problems.append(f"the {theme} scene's glow at {cx:g}, {cy:g}, r {r:g} reaches past the hands (x 118 to 142, y 105.5)")
    for cls, then in ((".hand", "glow"), (".wake", "light")):
        keys = frames(svg, names[cls])
        if len(keys) < 2 or float(keys[0][1].get("opacity", 1)) != 0 or float(keys[1][1].get("opacity", 0)) <= 0 or max(float(d.get("opacity", 0)) for _, d in keys) < .8 or float(keys[-1][1].get("opacity", 1)) != 0:
            problems.append(f"the {theme} scene's {cls} does not {then} up from unlit and fade: {keys}")
    dash = float((style.get(".spark", {}).get("stroke-dasharray") or "nan").split()[0])
    edges = [(at, dash - float(d["stroke-dashoffset"])) for at, d in frames(svg, names[".spark"]) if "stroke-dashoffset" in d]
    if not edges or edges[0] != (0.0, 0.0) or edges != sorted(edges, key=lambda pair: pair[1]):
        problems.append(f"the {theme} scene's glow does not start at its strand's top and run down: its front at {edges}")
    share = next((a0 + (a1 - a0) * (100 - e0) / (e1 - e0) for (a0, e0), (a1, e1) in zip(edges, edges[1:]) if e0 < 100 <= e1), None)
    starts, arrive = {}, {}
    for spark in elements(svg, "spark"):
        seg = SEGMENT.fullmatch(spark.get("d", ""))
        on = [s for s in mine if seg and all(abs(a - float(b)) <= .2 for a, b in zip(s, seg.groups()))]
        if not on or spark.get("pathLength") != "100":
            problems.append(f"the {theme} scene runs a glow on {spark.get('d')}, not down one agent's strand with pathLength 100")
            continue
        begin = delay_of(spark, style.get(".spark"))
        starts.setdefault(on[0], set()).add(begin)
        arrive.setdefault(on[0], set()).add(None if share is None else round(begin + 8 * share / 100, 3))
    if sorted(starts) != sorted(mine) or any(len(v) != 1 for v in starts.values()) or None in set().union(*arrive.values()):
        problems.append(f"the {theme} scene's glows start at {starts} and reach the strands' ends at {arrive}, not once on each of the 4 strands")
        continue
    inner = sorted(mine, key=lambda s: abs(s[0] - LEM_X))[:2]
    if left and left[0] > min(min(starts[s]) for s in inner):
        problems.append(f"the {theme} scene's hands glow at {left[0]} s, after the glow starts down the inner strands")
    lights = []
    for agent in agents(svg):
        for lit in agent["lit"]:
            x = agent["x"] + agent["scale"] * float(lit.get("cx", "nan"))
            strand = min(mine, key=lambda s: abs(s[0] - x))
            begin, reached = delay_of(lit, style.get(".wake")), min(arrive[strand])
            lights.append((strand in inner, begin))
            if abs(begin - reached) > .2:
                problems.append(f"the {theme} scene's agent at x {x:.1f} lights its eye at {begin} s, but the glow reaches its strand's end at {reached} s")
    near, far = sorted({b for i, b in lights if i}), sorted({b for i, b in lights if not i})
    if len(lights) != 4 or len(near) != 1 or len(far) != 1 or not near[0] < far[0]:
        problems.append(f"the {theme} scene lights the inner eyes at {near} s and the outer ones at {far} s, not the inner pair at one moment and the outer pair at one later")
verdict["scene_signal"] = "; ".join(problems)

# criterion 3 of the signal's plan: nothing else lights up or moves: the old lights are gone, every animated rule is
# the sky's, Lem's eye's or the signal's, no element carries an animation of its own, and nothing lies on the wire or
# on the word's strands
problems = []
for theme, svg in scenes.items():
    style, (mine, words) = rules(svg), strands(svg)
    left = [f".{cls}" for cls in GONE if elements(svg, cls)] + [f"@keyframes {name}" for name in ("run0", "run1", "run2", "flash", "drip", "glow", "tile", "flare") if frames(svg, name)]
    if left:
        problems.append(f"the {theme} scene still holds {left}")
    stray = sorted(sel for sel, decl in style.items() if any(key.startswith("animation") for key in decl)
                   and not set(re.findall(r"\.([\w-]+)", sel)) <= ANIMATED)
    if stray:
        problems.append(f"the {theme} scene animates {stray}")
    outside_stars = re.sub(r'(?s)<g class="stars">.*?</g>', "", svg)
    own = sorted({attrs.get("class", "no class") for attrs in map(attrs_of, re.findall(r"<\w+\b[^>]*>", outside_stars))
                  if "animation" in attrs.get("style", "") and (attrs.get("class") not in ANIMATED or "animation-name" in attrs["style"])})
    if own:
        problems.append(f"the {theme} scene's elements of {own} carry an animation of their own")
    wire = re.search(r'<!-- the line -->\s*<path d="([^"]*)"', svg)
    drawn = svg.count(f'd="{wire.group(1)}"') if wire else 0
    if drawn != 1:
        problems.append(f"the {theme} scene draws {drawn} paths along the wire, not the wire alone")
    tops = {round(s[0], 1) for s in words}
    on_word = [spark.get("d") for spark in elements(svg, "spark") if SEGMENT.match(spark.get("d", "")) and round(float(SEGMENT.match(spark["d"]).group(1)), 1) in tops]
    if len(words) != 4 or on_word:
        problems.append(f"the {theme} scene has {len(words)} strands of the word, and a glow runs on {on_word}")
verdict["scene_quiet"] = "; ".join(problems)

# criterion 4: about a hundred stars, each on its own timing, and the aurora by night; haze, rays and a shimmer by day
problems = []
for theme, svg in scenes.items():
    style, prefix = rules(svg), "c2n" if theme == "night" else "c2"
    hidden = [sel for sel, decl in style.items() if decl.get("display") == "none"]
    want = [f".{prefix}-sky-day"] if theme == "night" else [f".{prefix}-sky-night"]
    if hidden != want:
        problems.append(f"the {theme} scene hides {hidden}, not {want}")
    stars = re.search(r'<g class="stars">(.*?)</g>', svg)
    timings = re.findall(r'<circle\b[^>]*style="animation-duration:([\d.]+s);animation-delay:(-?[\d.]+s)"', stars.group(1)) if stars else []
    if not 90 <= len(timings) <= 120 or len(set(timings)) < 0.9 * len(timings):
        problems.append(f"the {theme} scene has {len(timings)} stars, {len(set(timings))} timings of their own")
    for cls, name in ((".band1", "drift1"), (".band2", "drift2"), (".haze", "haze"), (".heat1", "heat1"), (".heat2", "heat2"),
                      (".ray", "ray"), (".stars circle, .star", "twinkle")):
        got, duration, _ = animation(style.get(cls))
        if got != name or not duration or not frames(svg, name):
            problems.append(f"the {theme} scene's {cls} runs {got} in {duration} s, not the keyframes {name}")
    for cls in ("band1", "band2"):
        if not elements(svg, cls):
            problems.append(f"the {theme} scene draws no aurora band .{cls}")
    if not re.search(r'<feTurbulence\b', svg) or not elements(svg, "fan") or not elements(svg, "haze"):
        problems.append(f"the {theme} scene draws no shimmer, rays or haze")
verdict["scene_sky"] = "; ".join(problems)

# criterion 4 of the signal's plan: Lem's one red eye glows and blinks every 5 to 7 seconds, in one red day and night
problems, reds = [], {}
for theme, svg in scenes.items():
    style = rules(svg)
    eye = re.search(r'<g class="eye">(.*?)</g>', svg)
    name, blink, _ = animation(style.get(".eye"))
    if not eye or not (5 <= (blink or 0) <= 7) or not frames(svg, name or ""):
        problems.append(f"the {theme} scene's eye blinks {name} every {blink} s, not every 5 to 7 s")
    elif not any(float(d.get("opacity", 1)) < .5 for _, d in frames(svg, name)) or any(float(d.get("opacity", 1)) < 1 for at, d in frames(svg, name) if at in (0, 100)):
        problems.append(f"the {theme} scene's eye does not glow and dim for a moment: {frames(svg, name)}")
    colors = eye_colors(svg, eye.group(1) if eye else "")
    reds[theme] = colors
    if not red(colors):
        problems.append(f"the {theme} scene's eye is {sorted(colors)}, not a red")
if reds.get("day") != reds.get("night"):
    problems.append(f"the eye is {sorted(reds.get('day', []))} by day and {sorted(reds.get('night', []))} at night")
verdict["scene_eye"] = "; ".join(problems)

# criterion 5 of the signal's plan: one rule stops every animation, nothing animates past it, and each light rests
# unlit, so the scene under reduce motion shows the agents' red dots and no glow
problems = []
for theme, svg in scenes.items():
    style, media = rules(svg), re.findall(r"@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{\s*([^{}]*)\{([^{}]*)\}\s*\}", svg)
    if len(re.findall(r"@media", svg)) != 1 or media != [("* ", " animation: none !important; ")]:
        problems.append(f"the {theme} scene's rules for reduce motion are {media}, not the one * {{ animation: none !important; }}")
    smil = sorted(set(re.findall(r"<(animate\w*|set)\b", svg)))
    if smil:
        problems.append(f"the {theme} scene animates with {smil}, which the rule does not stop")
    for cls in ("hand", "wake"):
        if style.get("." + cls, {}).get("opacity") != "0":
            problems.append(f"the {theme} scene's .{cls} does not rest unlit")
    spark = style.get(".spark", {})
    if not spark or spark.get("stroke-dashoffset") != (spark.get("stroke-dasharray", "") + " -").split()[0]:
        problems.append(f"the {theme} scene's .spark does not rest before its strand's top: {spark}")
verdict["scene_still"] = "; ".join(problems)

# criteria 8 and 9: the files are pictures with nothing to fetch and no script, of the scene's frame, each under 50 KB
problems = []
for theme, svg in scenes.items():
    size = len(svg.encode("utf-8"))
    if not svg or size >= 50000:
        problems.append(f"the {theme} scene is {size} bytes, not under 50,000")
    head = attrs_of(re.match(r"<svg\b[^>]*>", svg).group(0)) if re.match(r"<svg\b[^>]*>", svg) else {}
    if (head.get("viewBox"), head.get("width"), head.get("height")) != ("0 0 1600 640", "1600", "640"):
        problems.append(f"the {theme} scene's frame is {head.get('viewBox')} at {head.get('width')} x {head.get('height')}")
    outside = re.findall(r"<script\b|<foreignObject\b|<image\b|\son\w+=|@import|(?:href|src)=\"(?!#)[^\"]*\"|url\((?!#)[^)]*\)", svg)
    if outside:
        problems.append(f"the {theme} scene holds {sorted(set(outside))}")
verdict["scene_file"] = "; ".join(problems)

# every color of the scene a six-digit lowercase hex, no name and no function
PAINT = re.compile(r'\b(fill|stroke|stop-color|flood-color|lighting-color|color)(?:="([^"]*)"|\s*:\s*([^;}"]*))')
problems = []
for theme, svg in scenes.items():
    wrong = [c for c in re.findall(r"#[0-9A-Fa-f]{3,8}\b", svg) if not re.fullmatch(r"#[0-9a-f]{6}", c)]
    for found in PAINT.finditer(svg):
        value = (found.group(2) if found.group(2) is not None else found.group(3)).strip()
        if not re.fullmatch(r"#[0-9a-f]{6}|none|url\(#[\w-]+\)", value) and not re.fullmatch(r"#[0-9A-Fa-f]{3,8}", value):
            wrong.append(f"{found.group(1)} {value}")
    if wrong:
        problems.append(f"the {theme} scene has {sorted(set(wrong))}")
verdict["scene_hex"] = "; ".join(problems)

# criterion 6, its static half (decision 9): one bound color for each theme from every color the scene holds, the
# lightest red, green and blue at night and the darkest by day, and nothing in the file that paints outside it. A mix,
# an opacity, a blur and a mask stay inside; a filter may add only a constant color, which joins the bound.
CHILDREN = ("feMergeNode", "feFuncR", "feFuncG", "feFuncB", "feFuncA")
def paint_rule(svg):
    """What can paint outside the bound, and the constant colors the scene's filters add to it."""
    problems, constants = [], []
    for found in re.findall(r"(?i)mix-blend-mode|background-blend-mode|plus-lighter|\b(?:brightness|contrast|saturate|invert|sepia|hue-rotate|grayscale|drop-shadow)\(", svg):
        problems.append(f"the blend or the filter {found}")
    for fid, body in re.findall(r'(?s)<filter\b[^>]*?\bid="([^"]*)"[^>]*>(.*?)</filter>', svg):
        tags = [(tag, attrs_of(rest)) for tag, rest in re.findall(r"<(fe\w+)\b([^>]*)>", body)]
        chain, inputs, made = [], [], {}
        for tag, attrs in tags:
            if tag == "feMergeNode" and chain and chain[-1][0] == "feMerge":
                inputs[-1].append(("in", attrs.get("in")))
                continue
            if tag in CHILDREN:
                continue
            k = len(chain)
            chain.append((tag, attrs))
            inputs.append([] if tag in ("feMerge", "feTurbulence", "feFlood", "feImage") else [("in", attrs.get("in"))])
            if tag in ("feComposite", "feBlend", "feDisplacementMap"):
                inputs[-1].append(("in2", attrs.get("in2")))
        consumers = {k: [] for k in range(len(chain))}
        for k, slots in enumerate(inputs):
            for slot, name in slots:
                source = k - 1 if name is None else max((j for j in range(k) if chain[j][1].get("result") == name), default=None)
                if source is not None and source >= 0:
                    consumers[source].append((k, slot))
        def constant(attrs):
            values = [float(v) for v in attrs.get("values", "").replace(",", " ").split()]
            if attrs.get("type", "matrix") != "matrix" or len(values) != 20 or any(values[r * 5 + c] for r in range(3) for c in range(4)):
                return None
            return "#" + "".join(f"{round(min(max(values[r * 5 + 4], 0), 1) * 255):02x}" for r in range(3))
        for k, (tag, attrs) in enumerate(chain):
            if tag in ("feGaussianBlur", "feOffset", "feMerge", "feDisplacementMap", "feTile"):
                continue
            if tag == "feComposite" and attrs.get("operator", "over") != "arithmetic":
                continue
            if tag == "feFlood" and re.fullmatch(r"#[0-9a-f]{6}", attrs.get("flood-color", "")):
                continue
            if tag == "feColorMatrix" and constant(attrs):
                constants.append(constant(attrs))
                continue
            if tag == "feTurbulence":
                fine = all((chain[j][0] == "feColorMatrix" and slot == "in" and constant(chain[j][1])) or (chain[j][0] == "feDisplacementMap" and slot == "in2")
                           for j, slot in consumers[k])
                if fine and k != len(chain) - 1:
                    continue
                problems.append(f"the filter {fid}: an feTurbulence that paints its own colors")
                continue
            problems.append(f"the filter {fid}: {tag}{' ' + attrs.get('operator', '') if tag == 'feComposite' else ''}")
    return problems, constants
def bound(svg, dark):
    colors = hexes(svg) | set(paint_rule(svg)[1])
    pick = max if dark else min
    return "#" + "".join(f"{pick(int(c[i:i + 2], 16) for c in colors):02x}" for i in (1, 3, 5)) if colors else ""
SHIMMER = '<filter id="f"><feTurbulence type="fractalNoise" baseFrequency=".018 .32" numOctaves="2" seed="4"/><feColorMatrix type="matrix" values="0 0 0 0 1  0 0 0 0 .95  0 0 0 0 .8  0 0 0 2.6 -1.25"/></filter>'
BARE = '<filter id="f"><feTurbulence type="fractalNoise" baseFrequency=".02" numOctaves="2"/></filter>'
problems = []
if paint_rule(SHIMMER) != ([], ["#fff2cc"]):
    problems.append(f"the owner's shimmer filter gives {paint_rule(SHIMMER)}, not a pass with #fff2cc")
if not paint_rule(BARE)[0]:
    problems.append("a bare feTurbulence passes")
for theme, svg in scenes.items():
    problems += [f"the {theme} scene: {p}" for p in paint_rule(svg)[0]]
verdict["scene_paint"] = "; ".join(problems)
verdict["bound_day"], verdict["bound_night"] = bound(scenes["day"], False), bound(scenes["night"], True)

# criterion 2, the file's half: where the figure starts and the word with its cursor ends, in the frame's units,
# for the drawn check at 390 px. The figure is the paths under <!-- the coat --> and <!-- the cowl ... -->, the word
# the paths of its drawn letters and its cursor under <!-- the word ... -->, each through the translate and scale of
# every group around it.
def path_xs(d):
    """Every x a path's points and control points reach, in its own units; refuses an arc and a smooth curve,
    whose reach its own numbers do not show."""
    if re.search(r"[AaSsTt]", d):
        raise ValueError("an arc or a smooth curve")
    xs, x, y, start = [], 0.0, 0.0, (0.0, 0.0)
    for cmd, args in re.findall(r"([MmLlHhVvCcQqZz])([^MmLlHhVvCcQqZz]*)", d):
        nums = [float(n) for n in re.findall(r"-?(?:\d+\.?\d*|\.\d+)(?:[eE]-?\d+)?", args)]
        kind, rel = cmd.upper(), cmd.islower()
        if kind == "Z":
            x, y = start
            continue
        step = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "Q": 4}[kind]
        for i in range(0, len(nums) - step + 1, step):
            chunk = nums[i:i + step]
            if kind == "H":
                x = x + chunk[0] if rel else chunk[0]
            elif kind == "V":
                y = y + chunk[0] if rel else chunk[0]
            else:
                points = [(chunk[j] + (x if rel else 0), chunk[j + 1] + (y if rel else 0)) for j in range(0, step, 2)]
                xs += [px for px, _ in points]
                x, y = points[-1]
                if kind == "M" and i == 0:
                    start = (x, y)
            xs.append(x)
    return xs
def transform_of(attrs):
    """A transform of translates and scales as (scale, dx, dy); None for any other."""
    text, out = attrs.get("transform", ""), (1.0, 0.0, 0.0)
    for name, args in re.findall(r"(\w+)\(([^)]*)\)", text):
        nums = [float(n) for n in re.findall(r"-?(?:\d+\.?\d*|\.\d+)", args)]
        if name == "translate" and nums:
            out = (out[0], out[1] + out[0] * nums[0], out[2] + out[0] * (nums[1] if len(nums) > 1 else 0))
        elif name == "scale" and len(nums) == 1:
            out = (out[0] * nums[0], out[1], out[2])
        else:
            return None
    return out
def frame_span(svg):
    stack, section, figure, word, problems = [(1.0, 0.0, 0.0)], None, [], [], []
    for found in re.finditer(r"(?s)<!--(.*?)-->|<(/?)(\w+)\b([^>]*?)(/?)>", svg):
        if found.group(1) is not None:
            note = found.group(1).strip()
            section = "figure" if note.startswith(("the coat", "the cowl")) else "word" if note.startswith("the word") else None
            continue
        closing, tag, rest, lone = found.group(2), found.group(3), found.group(4), found.group(5)
        if tag != "g" and tag != "path":
            continue
        if closing:
            if tag == "g" and len(stack) > 1:
                stack.pop()
            continue
        attrs, outer = attrs_of(rest), stack[-1]
        own = transform_of(attrs)
        whole = None if outer is None or own is None else (outer[0] * own[0], outer[1] + outer[0] * own[1], outer[2] + outer[0] * own[2])
        if tag == "g":
            if not lone:
                stack.append(whole)
            continue
        into = figure if section == "figure" else word if section == "word" else None
        if into is None:
            continue
        if whole is None:
            problems.append("a path of the figure or the word under a transform other than translate and scale")
            continue
        try:
            into += [whole[1] + whole[0] * x for x in path_xs(attrs.get("d", ""))]
        except ValueError as error:
            problems.append(f"a path of the figure or the word with {error}")
    if not figure:
        problems.append("no path under <!-- the coat --> or <!-- the cowl -->")
    if not word:
        problems.append("no path under <!-- the word -->")
    return problems, (round(min(figure), 1) if figure else None, round(max(word), 1) if word else None)
problems, span = frame_span(scenes["day"])
verdict["scene_span"], verdict["span"] = "; ".join(problems), list(span)
print(json.dumps(verdict))
PY
)
if [ -s "$SITE/index.html" ]; then
  "$PY" -I -B -c "$STATIC" "$ROOT" "$SITE" "$ROOT/.github/workflows/pages.yml" > "$WORK/static.json"
else
  echo '{}' > "$WORK/static.json"
fi
# ok KEY: true when the check KEY found nothing wrong; WHY then holds what it found
WHY=""
ok() {
  WHY=$("$PY" -I -c 'import json, sys; d = json.load(open(sys.argv[1])); print(d.get(sys.argv[2], "the page was not copied, so it was not read"))' "$WORK/static.json" "$1")
  [ -z "$WHY" ]
}

# criterion 6: the workflow and the folder its step makes
if ok trigger; then pass "pages.yml runs only on Run workflow (workflow_dispatch), never on a push, a pull request or a schedule"; else fail "pages.yml's triggers: $WHY"; fi
if ok workflow; then pass "pages.yml has the Pages permissions, the github-pages environment, and GitHub's Pages actions"; else fail "pages.yml: $WHY"; fi
if [ -z "$copy_said" ] && ok copied; then pass "the step \"$STEP_NAME\" of pages.yml makes a folder of index.html, style.css, the logo for each theme, its figure alone for the tab and the six pictures of the board, at the paths the page names"; else fail "the step \"$STEP_NAME\": ${copy_said:-$WHY}"; fi
if ok guides; then pass "every guide link of the page names a file of docs/ in the checkout, and each # part a heading of that file"; else fail "the guide links: $WHY"; fi
# criterion 5: what site/ holds
if ok tracked; then pass "git tracks index.html and style.css under site/, and nothing else"; else fail "site/ in git: $WHY"; fi
if ok no_image; then pass "no file under site/ is a picture"; else fail "site/: $WHY"; fi
if ok local; then pass "the page draws nothing from another host: no script, stylesheet, picture or font from a URL"; else fail "the page loads from another host: $WHY"; fi
# criterion 1, in the markup
if ok first; then pass "the opening has the logo, the README's line, the two install lines exact with a copy button each, and \"Lem needs agterm.\" with its link and the line to run them"; else fail "the opening: $WHY"; fi
# criterion 2
if ok sections; then pass "the page is six sections in order (the opening, the board, the flow, the phone, many tasks at once, the install) and a footer, and the nav links the board, the flow, the phone and the install"; else fail "the sections: $WHY"; fi
if ok words; then ok words_count || true; pass "the page has 800 to 1200 words of visible text ($WHY)"; else fail "the visible text: $WHY, not 800 to 1200"; fi
if ok diagram; then pass "the diagram's fast track has one step for the developer, the merge; the standard track three: the interview, the criteria, the merge"; else fail "the diagram: $WHY"; fi
if ok green; then pass "the page says \"Green means you can merge without a read.\""; else fail "the green sentence: $WHY"; fi
if ok again; then pass "the second install block has the two lines, and a sentence that names .lem/ links the removal steps of docs/install.md"; else fail "the second install block: $WHY"; fi
if ok footer; then pass "the footer links the seven guides, the settings and the repository"; else fail "the footer: $WHY"; fi
# criterion 3
if ok sentences; then pass "no sentence of the page has more than 25 words, and no instruction more than 20"; else fail "the sentences: $WHY"; fi
if ok os; then pass "the page names no operating system"; else fail "an operating system: $WHY"; fi
if ok history; then pass "the page says nothing of what ran and nothing of history"; else fail "what ran or history: $WHY"; fi
if ok plugin; then pass "the page calls Lem a plugin for Claude Code that works closely with agterm, and says that Lem needs agterm"; else fail "the plugin: $WHY"; fi
if ok captions; then pass "every example dialog has a caption that says illustration, and every caption of a picture of the board says demo data"; else fail "the captions: $WHY"; fi
# criterion 4, in the files
if ok pictures; then pass "the logo and the pictures of the board, the phone and a task each have a dark source"; else fail "the pictures: $WHY"; fi
if ok sizes; then pass "each picture of the board says its size as half the pixels of its files, light and dark"; else fail "the sizes of the pictures: $WHY"; fi
if ok colors; then pass "style.css has the six hues of lem.css with the same values, and every other color is a grey or a mix of those"; else fail "the colors: $WHY"; fi
if ok switch; then pass "the page has no control that switches the theme: its one kind of button copies a line"; else fail "a theme switch: $WHY"; fi
# the scene, assets/lem.svg and assets/lem-night.svg, in the files
if ok scene_eyes; then pass "in both scene files each of the four small agents has a red dot in its hood, no smaller than the core of Lem's eye and untouched by any animation, with a light of its own over it, in the red of Lem's eye, the same day and night"; else fail "the agents' eyes: $WHY"; fi
if ok scene_signal; then pass "in both scene files, in a cycle of 8 s, both hands glow at one moment, a glow runs down the two inner agents' strands and later the two outer ones', and each agent's eye starts to light within 0.2 s of the glow reaching its strand's end"; else fail "the signal: $WHY"; fi
if ok scene_quiet; then pass "in both scene files nothing else lights up or moves: no pulse, flash, lit tile, yellow glow or flare, no animation but the sky's, Lem's eye's and the signal's, and nothing on the wire or the word's strands"; else fail "what else moves: $WHY"; fi
if ok scene_sky; then pass "the day scene shows its sky with haze, rays and a shimmer, the night scene its sky with about a hundred stars on timings of their own and two drifting aurora bands"; else fail "the sky: $WHY"; fi
if ok scene_eye; then pass "in both scene files Lem's one red eye glows and blinks every 5 to 7 s, in the same red"; else fail "Lem's eye: $WHY"; fi
if ok scene_still; then pass "each scene file has one rule for reduce motion that stops every animation, no animation it would not stop, and each light of the signal rests unlit"; else fail "reduce motion: $WHY"; fi
if ok scene_file; then pass "each scene file is 1600 x 640, under 50,000 bytes, with no script and nothing from another file or host"; else fail "the scene files: $WHY"; fi
if ok scene_hex; then pass "every color of each scene file is a six-digit lowercase hex"; else fail "the scene's colors: $WHY"; fi
if ok scene_paint; then ok bound_day || true; bound="day $WHY"; ok bound_night || true; pass "nothing in a scene file paints outside its bound color ($bound, night $WHY), and the rule passes the owner's shimmer filter and refuses a bare feTurbulence"; else fail "the paint of the scene: $WHY"; fi

# ---- the checks of a drawn page ----
chrome=""
for c in google-chrome chromium chromium-browser "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"; do
  if command -v "$c" >/dev/null 2>&1 || [ -x "$c" ]; then chrome=$c; break; fi
done
# Chrome's temporary folders go into the work folder, which the run removes. On macOS Chrome reads
# MAC_CHROMIUM_TMPDIR, not TMPDIR (measured on 2026-11-17); elsewhere it reads TMPDIR.
mkdir -p "$WORK/chrome-tmp"
headless() { TMPDIR="$WORK/chrome-tmp" MAC_CHROMIUM_TMPDIR="$WORK/chrome-tmp" "$chrome" --headless=new --disable-gpu --no-sandbox --no-first-run --use-mock-keychain --user-data-dir="$WORK/chrome" --hide-scrollbars "$@" 2>/dev/null || true; }
# probe NAME SCRIPT: a copy of the page with SCRIPT at the end of its body, beside it in the folder. SCRIPT
# calls report(out): the JSON goes into a <pre> of the page, and to the page around it when it is framed.
REPORT='const report = out => { const text = JSON.stringify(out); document.body.insertAdjacentHTML("beforeend", "<pre id=\"probe-out\"></pre>"); document.getElementById("probe-out").textContent = text; if (parent !== window) parent.postMessage(text, "*"); };'
probe() {
  "$PY" -I -c 'import sys; page, out, script = sys.argv[1:]; text = open(page, encoding="utf-8").read(); open(out, "w", encoding="utf-8").write(text.replace("</body>", f"<script>{script}</script>\n</body>", 1))' \
    "$SITE/index.html" "$SITE/$1.html" "$REPORT
$2"
}
# result FILE: the JSON a probe wrote into the page Chrome printed
result() { "$PY" -I -c 'import html, re, sys; found = re.search(r"<pre id=\"probe-out\">(.*?)</pre>", open(sys.argv[1], encoding="utf-8").read(), re.S); print(html.unescape(found.group(1)) if found else "")' "$1"; }
# A phone's window: headless Chrome draws no window under 500 px wide (measured on 2026-11-22), so phone.html
# frames a probe at 390 px from the top left corner, with the probe's own query, and prints what it reports.
[ -d "$SITE" ] && cat > "$SITE/phone.html" <<'HTML'
<!doctype html>
<html><head><meta charset="utf-8"><style>body { margin: 0; } iframe { display: block; border: 0; width: 390px; height: 1400px; }</style></head>
<body><script>
addEventListener("message", event => { const out = document.createElement("pre"); out.id = "probe-out"; out.textContent = event.data; document.body.append(out); });
const frame = document.createElement("iframe");
frame.src = new URLSearchParams(location.search).get("page") + location.search;
document.body.prepend(frame);
</script></body></html>
HTML
# The probe of the first screen and the copy buttons. Each button is clicked with a stand-in for the
# clipboard, which notes what it was given. It also notes the scene: its box and its layer's (the picture
# around it), how it is fitted, and for each hero text whether a point at its middle hits the text, on top.
probe screen '
window.addEventListener("load", async () => {
  const copied = [];
  Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText: async text => { copied.push(text); } } });
  const box = el => { const r = el.getBoundingClientRect(); return { left: r.left, right: r.right, top: r.top + scrollY, bottom: r.bottom + scrollY }; };
  const first = document.querySelector("section");
  const scene = first.querySelector("picture img");
  const out = { width: innerWidth, client: document.documentElement.clientWidth };
  const texts = { headline: first.querySelector(".lead"), lead: first.querySelector(".sub"), "agterm note": first.querySelector(".needs") };
  first.querySelectorAll(".cmd code").forEach((code, i) => { texts["install line " + (i + 1)] = code; });
  first.querySelectorAll("button.copy").forEach((button, i) => { texts["copy button " + (i + 1)] = button; });
  out.parts = { scene: Math.ceil(box(scene).bottom) };
  out.texts = {};
  out.onTop = {};
  for (const [name, el] of Object.entries(texts)) {
    out.parts[name] = el ? Math.ceil(box(el).bottom) : null;
    if (!el) continue;
    out.texts[name] = box(el);
    el.scrollIntoView({ block: "center", behavior: "instant" });
    const r = el.getBoundingClientRect(), hit = document.elementFromPoint((r.left + r.right) / 2, (r.top + r.bottom) / 2);
    out.onTop[name] = !!hit && el.contains(hit);
  }
  scrollTo({ top: 0, behavior: "instant" });
  const style = getComputedStyle(scene);
  out.scene = Object.assign(box(scene), { natural: [scene.naturalWidth, scene.naturalHeight], fit: style.objectFit, position: style.objectPosition,
    radius: style.borderTopLeftRadius, shadow: style.boxShadow });
  out.layer = box(scene.parentElement);
  const buttons = [...document.querySelectorAll("button.copy")];
  for (const button of buttons) { button.click(); await new Promise(done => setTimeout(done, 20)); }
  out.copied = copied;
  out.own = buttons.map(button => button.parentElement.querySelector("code").textContent);
  report(out);
});'
# The probe of a theme: which picture each <picture> took, whether it loaded, and the background.
probe theme '
window.addEventListener("load", () => {
  const img = selector => document.querySelector(selector);
  const logo = img("section picture img"), board = img("img[src*=board]");
  report({
    dark: matchMedia("(prefers-color-scheme: dark)").matches,
    background: getComputedStyle(document.body).backgroundColor,
    logo: logo.currentSrc.replace(/^.*?\/_site\//, ""), logoWidth: logo.naturalWidth,
    board: board.currentSrc.replace(/^.*?\/_site\//, ""), boardWidth: board.naturalWidth,
  });
});'
# The probe of the contrast (criterion 6): the scene drawn as one solid color, the bound of its theme from the
# query (?bound=RRGGBB), which is the worst any moment of the motion can paint behind a text. It notes the color
# and the boxes of each run of hero text, then hides the text itself, so that a picture of the window shows what
# stands behind each run: the bound under the page shade, or the solid box of an install line or a button.
probe contrast '
const first = document.querySelector("section");
const scene = first.querySelector("picture img");
const bound = "#" + new URLSearchParams(location.search).get("bound");
scene.parentElement.querySelectorAll("source").forEach(source => source.remove());
scene.src = "data:image/svg+xml," + encodeURIComponent("<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1600\" height=\"640\"><rect width=\"1600\" height=\"640\" fill=\"" + bound + "\"/></svg>");
window.addEventListener("load", () => {
  const runs = [];
  const add = (name, el) => {
    if (!el) { runs.push({ name, color: null, rects: [] }); return; }
    const walk = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    for (let node = walk.nextNode(); node; node = walk.nextNode()) {
      if (!node.textContent.trim()) continue;
      const range = document.createRange();
      range.selectNodeContents(node);
      runs.push({ name, text: node.textContent.trim().slice(0, 40), color: getComputedStyle(node.parentElement).color,
        rects: [...range.getClientRects()].map(r => [r.left, r.top, r.right, r.bottom]) });
    }
  };
  add("the headline", first.querySelector(".lead"));
  add("the lead", first.querySelector(".sub"));
  first.querySelectorAll(".cmd code").forEach((code, i) => {
    add("install line " + (i + 1), code);
    const r = code.getClientRects()[0];
    runs.push({ name: "install line " + (i + 1), text: "its $", color: getComputedStyle(code, "::before").color, rects: r ? [[r.left, r.top, r.right, r.bottom]] : [] });
  });
  first.querySelectorAll("button.copy").forEach((button, i) => add("copy button " + (i + 1), button));
  add("the agterm note", first.querySelector(".needs"));
  document.head.insertAdjacentHTML("beforeend", "<style>section:first-of-type *, section:first-of-type *::before, section:first-of-type *::after { -webkit-text-fill-color: transparent !important; text-decoration-color: transparent !important; text-shadow: none !important; }</style>");
  report({ width: innerWidth, dpr: devicePixelRatio, bound, runs });
});'

# DRAWN MODE FILE...: the verdict on what a probe printed, empty when nothing is wrong, exit 1 when something is
DRAWN=$(cat <<'PY'
import json, re, sys, zlib
mode, *files = sys.argv[1:]
def load(path):
    try:
        return json.load(open(path))
    except ValueError:
        sys.exit("the probe printed nothing")
def png(path):
    """The rows of an 8-bit RGB or RGBA picture, each a bytearray, and the bytes of one pixel."""
    data = open(path, "rb").read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        sys.exit(f"{path} is no PNG picture")
    at, chunks, head = 8, [], None
    while at < len(data):
        size, kind = int.from_bytes(data[at:at + 4], "big"), data[at + 4:at + 8]
        if kind == b"IHDR":
            head = data[at + 8:at + 8 + size]
        elif kind == b"IDAT":
            chunks.append(data[at + 8:at + 8 + size])
        at += 12 + size
    width, height, depth, kind, laced = int.from_bytes(head[0:4], "big"), int.from_bytes(head[4:8], "big"), head[8], head[9], head[12]
    if depth != 8 or kind not in (2, 6) or laced:
        sys.exit(f"{path} is a PNG of depth {depth}, color type {kind}, interlace {laced}, which this check does not read")
    step = 3 if kind == 2 else 4
    raw, stride, rows, prev = zlib.decompress(b"".join(chunks)), width * step, [], bytearray(width * step)
    for y in range(height):
        kind_of_row, line = raw[y * (stride + 1)], bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        if kind_of_row == 1:
            for i in range(step, stride):
                line[i] = (line[i] + line[i - step]) & 255
        elif kind_of_row == 2:
            line = bytearray((a + b) & 255 for a, b in zip(line, prev))
        elif kind_of_row == 3:
            for i in range(stride):
                line[i] = (line[i] + ((line[i - step] if i >= step else 0) + prev[i]) // 2) & 255
        elif kind_of_row == 4:
            for i in range(stride):
                a, b, c = (line[i - step] if i >= step else 0), prev[i], (prev[i - step] if i >= step else 0)
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(line)
        prev = line
    return width, height, step, rows
def color(text):
    """A computed CSS color as red, green, blue in 0 to 1 and an alpha."""
    found = re.fullmatch(r"rgba?\(([\d.]+),\s*([\d.]+),\s*([\d.]+)(?:,\s*([\d.]+))?\)", text or "")
    if found:
        return [float(found.group(i)) / 255 for i in (1, 2, 3)], float(found.group(4) or 1)
    found = re.fullmatch(r"color\(srgb ([-\d.e]+) ([-\d.e]+) ([-\d.e]+)(?: / ([\d.]+))?\)", text or "")
    if found:
        return [min(max(float(found.group(i)), 0), 1) for i in (1, 2, 3)], float(found.group(4) or 1)
    return None
def luminance(rgb):
    return sum(w * (c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4) for w, c in zip((0.2126, 0.7152, 0.0722), rgb))
def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)
wrong, said = [], ""
if mode == "screen":
    d = load(files[0])
    wrong = [f"{name} ends at {end} px" for name, end in d["parts"].items() if end is None or end > 800]
    if d["width"] != 1280:
        wrong.append(f"the window is {d['width']} px wide")
elif mode == "layer":
    # criterion 1: the scene from edge to edge, from the top of the page, unboxed, with every hero text inside its layer and on top
    d = load(files[0])
    scene, layer = d["scene"], d["layer"]
    if scene["left"] > 0 or scene["right"] < d["client"] or scene["top"] > 0:
        wrong.append(f"the scene spans x {scene['left']} to {scene['right']} from y {scene['top']}, not the window's {d['client']} px from its top")
    if layer["left"] > 0 or layer["right"] < d["client"] or layer["top"] > 0:
        wrong.append(f"the scene's layer spans x {layer['left']} to {layer['right']} from y {layer['top']}")
    if scene["radius"] not in ("0px", "") or scene["shadow"] != "none":
        wrong.append(f"the scene is boxed: corner {scene['radius']}, shadow {scene['shadow']}")
    for name, box in d["texts"].items():
        if box["top"] < layer["top"] or box["bottom"] > layer["bottom"]:
            wrong.append(f"{name} (y {box['top']:.0f} to {box['bottom']:.0f}) is outside the layer (y {layer['top']:.0f} to {layer['bottom']:.0f})")
    wrong += [f"{name} is under something else at its middle" for name, top in d["onTop"].items() if not top]
    if len(d["texts"]) != 7:
        wrong.append(f"the probe found {sorted(d['texts'])}, not the 7 hero texts")
elif mode == "phone":
    # criterion 2: at 390 px the figure and the word with its cursor are inside the window, and the scene keeps its ratio
    d, static = load(files[0]), load(files[1])
    scene, (left, right) = d["scene"], static.get("span") or [None, None]
    natural, box_w, box_h = scene["natural"], scene["right"] - scene["left"], scene["bottom"] - scene["top"]
    if static.get("scene_span") or left is None:
        wrong.append(f"the scene file: {static.get('scene_span')}")
    elif d["width"] != 390 or d["client"] != 390:
        wrong.append(f"the frame is {d['width']} px wide, {d['client']} px inside, not 390")
    elif natural != [1600, 640]:
        wrong.append(f"the scene loaded at {natural}, not 1600 x 640")
    else:
        if scene["fit"] == "cover":
            scale_x = scale_y = max(box_w / 1600, box_h / 640)
        elif scene["fit"] == "contain":
            scale_x = scale_y = min(box_w / 1600, box_h / 640)
        else:
            scale_x, scale_y = box_w / 1600, box_h / 640
        place = re.match(r"([\d.]+)%", scene["position"] or "")
        if abs(scale_x - scale_y) > 0.002:
            wrong.append(f"the scene is squeezed: {scale_x:.3f} across and {scale_y:.3f} down")
        elif not place:
            wrong.append(f"the scene is placed at {scene['position']}, not at a share of the window across")
        else:
            shift = scene["left"] + (box_w - 1600 * scale_x) * float(place.group(1)) / 100
            seen = (shift + left * scale_x, shift + right * scale_x)
            if seen[0] < 0 or seen[1] > d["client"]:
                wrong.append(f"the figure starts at x {seen[0]:.1f} and the word ends at x {seen[1]:.1f} of the {d['client']} px window")
            said = f"the scene is {box_h:.0f} px high, the figure starts at x {seen[0]:.0f} and the word ends at x {seen[1]:.0f}"
elif mode == "contrast":
    # criterion 6: each run of hero text against what stands behind it, at its weakest pixel, with the scene at its bound
    d, picture, static, theme = load(files[0]), files[1], load(files[2]), files[3]
    width, height, step, rows = png(picture)
    want = "#" + static.get(f"bound_{theme}", "").lstrip("#")
    if d["bound"] != want:
        wrong.append(f"the probe drew the scene as {d['bound']}, not the {theme} bound {want}")
    if d["dpr"] != 1:
        wrong.append(f"the window draws {d['dpr']} pixels to the px")
    names = {run["name"] for run in d["runs"]}
    if len(names) != 7:
        wrong.append(f"the probe found {sorted(names)}, not the 7 hero texts")
    weakest = (99.0, "")
    for run in d["runs"]:
        ink, cache = color(run["color"]), {}
        if ink is None or not run["rects"]:
            wrong.append(f"{run['name']}: no text or the color {run['color']}")
            continue
        worst = 99.0
        for x0, y0, x1, y1 in run["rects"]:
            # one px in from each side, off the edge of a box around the text
            for y in range(int(y0) + 1, min(int(y1 + 0.999) - 1, height)):
                line = rows[y]
                for x in range(int(x0) + 1, min(int(x1 + 0.999) - 1, width)):
                    pixel = bytes(line[x * step:x * step + 3])
                    if pixel not in cache:
                        back = [c / 255 for c in pixel]
                        cache[pixel] = contrast([ink[1] * f + (1 - ink[1]) * b for f, b in zip(ink[0], back)], back)
                    worst = min(worst, cache[pixel])
        if worst == 99.0:
            wrong.append(f"{run['name']}: its boxes hold no pixel of the picture")
        elif worst < 4.5:
            wrong.append(f"{run['name']} ({run['text']!r}) reaches {worst:.2f} to 1")
        if worst < weakest[0]:
            weakest = (worst, run["name"])
    said = f"the weakest is {weakest[1]} at {weakest[0]:.1f} to 1"
elif mode == "copy":
    d = load(files[0])
    lines = ["claude plugin marketplace add pySilver/lem --scope project", "claude plugin install lem@lem --scope project"]
    if not (d["copied"] == d["own"] == lines * 2):
        wrong.append(f"the buttons copied {d['copied']}, and their rows hold {d['own']}")
elif mode in ("light", "dark"):
    d, dark = load(files[0]), mode == "dark"
    want = ("assets/lem-night.svg", "assets/screens/board-dark.png") if dark else ("assets/lem.svg", "assets/screens/board-light.png")
    if d["dark"] != dark:
        wrong.append(f"the page drew with prefers-color-scheme dark = {d['dark']}")
    if (d["logo"], d["board"]) != want:
        wrong.append(f"it took {d['logo']} and {d['board']}, not {want}")
    if not (d["logoWidth"] > 0 and d["boardWidth"] > 0):
        wrong.append(f"a picture did not load: widths {d['logoWidth']} and {d['boardWidth']}")
elif mode == "differ":
    light, dark = (load(path)["background"] for path in files)
    if light == dark:
        wrong.append(f"both draws have the background {light}")
print("; ".join(wrong) if wrong else said)
sys.exit(bool(wrong))
PY
)
drawn() { "$PY" -I -B -c "$DRAWN" "$@" 2>&1; }

# contrast_of THEME: the contrast probe drawn at 1280 x 800 and at 390 px in THEME (day or night), the scene at
# the bound color of that theme from the static checks; prints the weakest run of each, or what fell short
contrast_of() {
  local theme=$1 scheme=1 bound width size url why said=""
  [ "$theme" = night ] && scheme=0
  ok "bound_$theme" || true
  bound=${WHY#\#}
  for place in "1280 1280,800 contrast.html?bound=$bound" "390 500,1400 phone.html?page=contrast.html&bound=$bound"; do
    read -r width size url <<< "$place"
    headless --window-size="$size" --force-device-scale-factor=1 --blink-settings=preferredColorScheme=$scheme --virtual-time-budget=5000 --dump-dom "file://$SITE/$url" > "$WORK/contrast-$theme-$width.dom"
    headless --window-size="$size" --force-device-scale-factor=1 --blink-settings=preferredColorScheme=$scheme --virtual-time-budget=5000 --screenshot="$WORK/contrast-$theme-$width.png" "file://$SITE/$url"
    result "$WORK/contrast-$theme-$width.dom" > "$WORK/contrast-$theme-$width.json"
    if ! why=$(drawn contrast "$WORK/contrast-$theme-$width.json" "$WORK/contrast-$theme-$width.png" "$WORK/static.json" "$theme"); then
      echo "at $width px: $why"
      return 1
    fi
    said="$said${said:+; }at $width px $why"
  done
  echo "bound #$bound; $said"
}

drawn_checks() {
  # criterion 1: the first screen at 1280 px. The height of the window takes no part: the page uses no
  # height of the viewport, so a part drawn above 800 px is in the first screen of a 1280 x 800 window.
  headless --window-size=1280,800 --virtual-time-budget=5000 --dump-dom "file://$SITE/screen.html" > "$WORK/screen.dom"
  result "$WORK/screen.dom" > "$WORK/screen.json"
  if why=$(drawn screen "$WORK/screen.json"); then
    pass "at 1280 x 800 the scene, the headline, the lead, both install lines, both copy buttons and the line \"Lem needs agterm.\" are in the first screen"
  else
    fail "the first screen at 1280 x 800: $why"
  fi
  if why=$(drawn layer "$WORK/screen.json"); then
    pass "at 1280 x 800 the scene reaches the window's left and right edge from the top of the page, with no box, and its layer holds the seven hero texts, each on top of it"
  else
    fail "the scene behind the hero at 1280 x 800: $why"
  fi
  if why=$(drawn copy "$WORK/screen.json"); then
    pass "each of the four copy buttons copies the install line of its own row"
  else
    fail "the copy buttons: $why"
  fi
  # criterion 2: a phone, 390 px wide, in a frame (phone.html)
  headless --window-size=500,1400 --virtual-time-budget=5000 --dump-dom "file://$SITE/phone.html?page=screen.html" > "$WORK/phone.dom"
  result "$WORK/phone.dom" > "$WORK/phone.json"
  if why=$(drawn phone "$WORK/phone.json" "$WORK/static.json"); then
    pass "at 390 px the scene is cut at its sides around its center and keeps its ratio, and the hooded figure and the word Lem with its cursor are inside the window ($why)"
  else
    fail "the scene at 390 px: $why"
  fi
  # criterion 6: each hero text against the scene at its theme's bound color, under the page's shade, at 1280 x 800 and at 390 px
  if why=$(contrast_of day); then
    pass "in the day theme every hero text keeps 4.5 to 1 against the scene at its bound color under the page's shade, or against its own solid box: $why"
  else
    fail "the contrast in the day theme: $why"
  fi
  if why=$(contrast_of night); then
    pass "in the night theme every hero text keeps 4.5 to 1 against the scene at its bound color under the page's shade, or against its own solid box: $why"
  else
    fail "the contrast in the night theme: $why"
  fi
  # criterion 4: the page drawn in the light and in the dark theme, by Chrome's preferred color scheme
  headless --window-size=1280,800 --blink-settings=preferredColorScheme=1 --virtual-time-budget=5000 --dump-dom "file://$SITE/theme.html" > "$WORK/light.dom"
  headless --window-size=1280,800 --blink-settings=preferredColorScheme=0 --virtual-time-budget=5000 --dump-dom "file://$SITE/theme.html" > "$WORK/dark.dom"
  result "$WORK/light.dom" > "$WORK/light.json"
  result "$WORK/dark.dom" > "$WORK/dark.json"
  if why=$(drawn light "$WORK/light.json"); then
    pass "in the light theme the page shows assets/lem.svg and assets/screens/board-light.png, and both load"
  else
    fail "the light theme: $why"
  fi
  if why=$(drawn dark "$WORK/dark.json"); then
    pass "in the dark theme the page shows assets/lem-night.svg and assets/screens/board-dark.png, and both load"
  else
    fail "the dark theme: $why"
  fi
  if why=$(drawn differ "$WORK/light.json" "$WORK/dark.json"); then
    pass "the light and the dark draw differ in their background, so the theme took"
  else
    fail "the themes: $why"
  fi
}

if [ -z "$chrome" ]; then
  skip_function drawn_checks "no Chrome or Chromium found"
elif [ ! -s "$SITE/index.html" ]; then
  skip_function drawn_checks "the workflow's step made no page to draw"
else
  headless --window-size=1280,800 --virtual-time-budget=3000 --dump-dom "file://$SITE/theme.html" > "$WORK/start.dom"
  if [ ! -s "$WORK/start.dom" ]; then
    skip_function drawn_checks "$chrome printed no page"
  else
    drawn_checks
  fi
fi

if [ -n "${LEM_SITE_SHOTS:-}" ] && [ -n "$chrome" ]; then
  mkdir -p "$LEM_SITE_SHOTS"
  for theme in light dark; do
    scheme=1
    [ "$theme" = dark ] && scheme=0
    headless --window-size=1280,800 --blink-settings=preferredColorScheme=$scheme --virtual-time-budget=4000 --screenshot="$LEM_SITE_SHOTS/page-$theme-1280x800.png" "file://$SITE/index.html"
    headless --window-size=1280,4400 --blink-settings=preferredColorScheme=$scheme --virtual-time-budget=4000 --screenshot="$LEM_SITE_SHOTS/page-$theme-full.png" "file://$SITE/index.html"
  done
fi

results_add_up
finished=yes
[ "$fails" -eq 0 ]
