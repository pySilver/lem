#!/usr/bin/env bash
# Lem's page on GitHub Pages: site/index.html and site/style.css, and the workflow that publishes them
# by hand, .github/workflows/pages.yml. The suite takes the workflow's own copy step out of pages.yml
# by its name, runs it in a throwaway folder that holds a copy of site/ and assets/, and reads the page
# there, as Pages would serve it. The checks of the text, the links, the colors and the workflow run
# everywhere; the checks of a drawn page (the first screen at 1280 px, the copy buttons, the light and
# the dark theme) need headless Chrome, and print SKIP lines where none starts.
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

# 2: the footer links the six guides, the settings and the repository
need = {"docs/flow.md", "docs/when-lem-needs-you.md", "docs/board.md", "docs/pull-request.md", "docs/install.md", "docs/linear.md", "docs/settings.md"}
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

# criterion 3: the pulse on the wire, the pegs' flash and the tiles, one cycle of 8 seconds with a rest
problems = []
for theme, svg in scenes.items():
    style = rules(svg)
    pulses = elements(svg, "pulse")
    if len(pulses) != 3:
        problems.append(f"the {theme} scene has {len(pulses)} paths of the pulse, not 3")
    for pulse in pulses:
        dash = [float(v) for v in (inline(pulse, "stroke-dasharray") or "0 0").split()]
        start, name = float(inline(pulse, "stroke-dashoffset") or "nan"), inline(pulse, "animation-name")
        keys = frames(svg, name or "")
        offsets = [(at, float(d["stroke-dashoffset"])) for at, d in keys if "stroke-dashoffset" in d]
        if pulse.get("pathLength") != "1000" or len(dash) != 2 or dash[1] < 1000 + dash[0] or start != dash[0]:
            problems.append(f"a pulse of the {theme} scene does not rest before the line's start: pathLength {pulse.get('pathLength')}, dash {dash}, offset {start}")
        elif not offsets or offsets[0] != (0.0, dash[0]) or -offsets[-1][1] < 1000 or min(at for at, off in offsets if -off >= 1000) > 90:
            problems.append(f"the pulse {name} of the {theme} scene does not run from the left edge past the right one with a rest: {offsets}")
    flashes, drips, tiles = elements(svg, "flash"), elements(svg, "drip"), elements(svg, "tile")
    if len(flashes) != 8 or len(drips) != 8:
        problems.append(f"the {theme} scene flashes {len(flashes)} pegs and runs down {len(drips)} strands, not the 8 of each")
    if len(tiles) != 42:
        problems.append(f"the {theme} scene lights {len(tiles)} tiles, not the 41 of the word and its cursor")
    letters = {"L": [], "e": [], "m": [], "cursor": []}
    for tile in tiles:
        x = float(re.match(r"M([\d.]+)", tile.get("d", "M0")).group(1))
        letters["L" if x < 400 else "e" if x < 490 else "m" if x < 580 else "cursor"].append(seconds(inline(tile, "animation-delay") or "0s"))
    means = [sum(v) / len(v) if v else None for v in letters.values()]
    if None in means or means != sorted(means):
        problems.append(f"the {theme} scene's letters do not light from left to right: mean delays {means}")
    for cls in ("pulse", "flash", "drip", "glow", "tile"):
        name, duration, _ = animation(style.get("." + cls))
        if duration != 8:
            problems.append(f"the {theme} scene's .{cls} runs {name} in {duration} s, not the cycle of 8 s")
verdict["scene_wire"] = "; ".join(problems)

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

# criterion 5: one red eye that glows, blinks every 5 to 7 seconds, flares as the pulse passes the figure; one red in both
problems, reds = [], {}
for theme, svg in scenes.items():
    style = rules(svg)
    eye = re.search(r'<g class="eye">(.*?)</g>', svg)
    name, blink, _ = animation(style.get(".eye"))
    if not eye or not (5 <= (blink or 0) <= 7) or not frames(svg, name or ""):
        problems.append(f"the {theme} scene's eye blinks {name} every {blink} s, not every 5 to 7 s")
    elif not any(float(d.get("opacity", 1)) < .5 for _, d in frames(svg, name)) or any(float(d.get("opacity", 1)) < 1 for at, d in frames(svg, name) if at in (0, 100)):
        problems.append(f"the {theme} scene's eye does not glow and dim for a moment: {frames(svg, name)}")
    name, period, delay = animation(style.get(".flare"))
    flash_at = sorted((float(f["cx"]), seconds(inline(f, "animation-delay") or "0s")) for f in elements(svg, "flash"))
    around = [t for x, t in flash_at if x < 130][-1:] + [t for x, t in flash_at if x > 130][:1]
    if not elements(svg, "flare") or period != 8 or style.get(".flare", {}).get("opacity") != "0" or len(around) != 2 or not around[0] <= delay <= around[1]:
        problems.append(f"the {theme} scene's eye flares {name} at {delay} s of {period} s, not as the pulse passes the figure between the flashes at {around}")
    colors = hexes(eye.group(1) if eye else "") | hexes(re.search(r'<radialGradient id="c2n?-eye">.*?</radialGradient>', svg).group(0) if re.search(r'<radialGradient id="c2n?-eye">', svg) else "")
    reds[theme] = colors
    if not colors or any(not (int(c[1:3], 16) > 200 and int(c[3:5], 16) < 80 and int(c[5:7], 16) < 80) for c in colors):
        problems.append(f"the {theme} scene's eye is {sorted(colors)}, not a red")
if reds.get("day") != reds.get("night"):
    problems.append(f"the eye is {sorted(reds.get('day', []))} by day and {sorted(reds.get('night', []))} at night")
verdict["scene_eye"] = "; ".join(problems)

# criterion 7: one rule stops every animation, nothing animates past it, and each light rests dark
problems = []
for theme, svg in scenes.items():
    style, media = rules(svg), re.findall(r"@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{\s*([^{}]*)\{([^{}]*)\}\s*\}", svg)
    if len(re.findall(r"@media", svg)) != 1 or media != [("* ", " animation: none !important; ")]:
        problems.append(f"the {theme} scene's rules for reduce motion are {media}, not the one * {{ animation: none !important; }}")
    smil = sorted(set(re.findall(r"<(animate\w*|set)\b", svg)))
    if smil:
        problems.append(f"the {theme} scene animates with {smil}, which the rule does not stop")
    for cls in ("flash", "glow", "tile", "flare"):
        if style.get("." + cls, {}).get("opacity") != "0":
            problems.append(f"the {theme} scene's .{cls} does not rest unlit")
    drip = style.get(".drip", {})
    if not drip or drip.get("stroke-dashoffset") != (drip.get("stroke-dasharray", "") + " -").split()[0]:
        problems.append(f"the {theme} scene's .drip does not rest before its strand: {drip}")
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
if ok footer; then pass "the footer links the six guides, the settings and the repository"; else fail "the footer: $WHY"; fi
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
if ok scene_wire; then pass "in both scene files a pulse runs along the wire from before its left end to past its right end in a cycle of 8 s with a rest, each of the 8 pegs flashes, and the 42 tiles light letter by letter"; else fail "the pulse on the wire: $WHY"; fi
if ok scene_sky; then pass "the day scene shows its sky with haze, rays and a shimmer, the night scene its sky with about a hundred stars on timings of their own and two drifting aurora bands"; else fail "the sky: $WHY"; fi
if ok scene_eye; then pass "in both scene files one red eye glows, blinks every 5 to 7 s and flares as the pulse passes the figure, in the same red"; else fail "the eye: $WHY"; fi
if ok scene_still; then pass "each scene file has one rule for reduce motion that stops every animation, no animation it would not stop, and each light rests unlit"; else fail "reduce motion: $WHY"; fi
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
# probe NAME SCRIPT: a copy of the page with SCRIPT at the end of its body, beside it in the folder
probe() {
  "$PY" -I -c 'import sys; page, out, script = sys.argv[1:]; text = open(page, encoding="utf-8").read(); open(out, "w", encoding="utf-8").write(text.replace("</body>", f"<script>{script}</script>\n</body>", 1))' \
    "$SITE/index.html" "$SITE/$1.html" "$2"
}
# result FILE: the JSON a probe wrote into the page Chrome printed
result() { "$PY" -I -c 'import html, re, sys; found = re.search(r"<pre id=\"probe-out\">(.*?)</pre>", open(sys.argv[1], encoding="utf-8").read(), re.S); print(html.unescape(found.group(1)) if found else "")' "$1"; }
# The probe of the first screen and the copy buttons. Each button is clicked with a stand-in for the
# clipboard, which notes what it was given.
probe screen '
window.addEventListener("load", async () => {
  const copied = [];
  Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText: async text => { copied.push(text); } } });
  const bottom = el => el ? Math.ceil(el.getBoundingClientRect().bottom + scrollY) : null;
  const first = document.querySelector("section");
  const out = { width: innerWidth };
  out.parts = {
    logo: bottom(first.querySelector("picture img")),
    line: bottom(first.querySelector(".lead")),
    needs: bottom(first.querySelector(".needs")),
  };
  first.querySelectorAll(".cmd code").forEach((code, i) => { out.parts["line " + (i + 1)] = bottom(code); });
  first.querySelectorAll("button.copy").forEach((button, i) => { out.parts["copy button " + (i + 1)] = bottom(button); });
  const buttons = [...document.querySelectorAll("button.copy")];
  for (const button of buttons) { button.click(); await new Promise(done => setTimeout(done, 20)); }
  out.copied = copied;
  out.own = buttons.map(button => button.parentElement.querySelector("code").textContent);
  document.body.insertAdjacentHTML("beforeend", "<pre id=\"probe-out\"></pre>");
  document.getElementById("probe-out").textContent = JSON.stringify(out);
});'
# The probe of a theme: which picture each <picture> took, whether it loaded, and the background.
probe theme '
window.addEventListener("load", () => {
  const img = selector => document.querySelector(selector);
  const logo = img("section picture img"), board = img("img[src*=board]");
  const out = {
    dark: matchMedia("(prefers-color-scheme: dark)").matches,
    background: getComputedStyle(document.body).backgroundColor,
    logo: logo.currentSrc.replace(/^.*?\/_site\//, ""), logoWidth: logo.naturalWidth,
    board: board.currentSrc.replace(/^.*?\/_site\//, ""), boardWidth: board.naturalWidth,
  };
  document.body.insertAdjacentHTML("beforeend", "<pre id=\"probe-out\"></pre>");
  document.getElementById("probe-out").textContent = JSON.stringify(out);
});'

# DRAWN MODE FILE...: the verdict on what a probe printed, empty when nothing is wrong, exit 1 when something is
DRAWN=$(cat <<'PY'
import json, sys
mode, *files = sys.argv[1:]
def load(path):
    try:
        return json.load(open(path))
    except ValueError:
        sys.exit("the probe printed nothing")
wrong = []
if mode == "screen":
    d = load(files[0])
    wrong = [f"{name} ends at {end} px" for name, end in d["parts"].items() if end is None or end > 800]
    if d["width"] != 1280:
        wrong.append(f"the window is {d['width']} px wide")
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
print("; ".join(wrong))
sys.exit(bool(wrong))
PY
)
drawn() { "$PY" -I -B -c "$DRAWN" "$@" 2>&1; }

drawn_checks() {
  # criterion 1: the first screen at 1280 px. The height of the window takes no part: the page uses no
  # height of the viewport, so a part drawn above 800 px is in the first screen of a 1280 x 800 window.
  headless --window-size=1280,800 --virtual-time-budget=5000 --dump-dom "file://$SITE/screen.html" > "$WORK/screen.dom"
  result "$WORK/screen.dom" > "$WORK/screen.json"
  if why=$(drawn screen "$WORK/screen.json"); then
    pass "at 1280 x 800 the logo, the line, both install lines, both copy buttons and the line \"Lem needs agterm.\" are in the first screen"
  else
    fail "the first screen at 1280 x 800: $why"
  fi
  if why=$(drawn copy "$WORK/screen.json"); then
    pass "each of the four copy buttons copies the install line of its own row"
  else
    fail "the copy buttons: $why"
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
