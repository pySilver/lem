# The brief Lem passes to agdoc

Lem loads the agdoc skill (the harness's `load-skill`) at `land.py propose`, after it wrote `built.md`
and `decisions.md`, and passes the text between the two lines below as the skill's arguments. The
`{{...}}` values are the task's; the rest is fixed. A small change makes no page.

## Which design, and why

**Classic** (`assets/classic.html`).

- The content is two short documents that he reads top to bottom, once, before a merge. Classic is
  agdoc's design for that: a plain page, a sticky contents bar, callouts and pills, no decoration
  that pushes the content down.
- Its `.callout.risk` is a red block made from the stylesheet's own `--bad`, so the red block needs no
  color of Lem's. Its pills (`.pill.ok`, `.bad`, `.warn`, `.info`, `.alt`, `.muted`) give each
  "who decided" one color with its words beside it, and its table gives the list of decisions.
- The plain `.callout.risk` is too quiet for "a big red flag": a 4 px red edge and a 7 % red tint.
  In the first render of the sample (dark theme), it looked like the other boxes. So the brief asks
  for a 2 px red frame, an 8 px edge, a 16 % tint and a red 18 px title, all from `--bad`. That is a
  style attribute on one element, not a change of the template.
- Its header is small (an eyebrow, a 26 px title, one line, one meta row), so a red block above it
  and the header both fit in the first screen.
- Like every agdoc template, it takes `--agterm-*` from the terminal and falls back to `Canvas` and
  `CanvasText` with `color-scheme: light dark`, so it reads in a light and in a dark theme.

Not the others:

- **Editorial**: its hero (a 60 px serif title, a lede, stats) fills the first screen, so the red
  block would not be the first thing he sees, and its left index column takes 210 px for two parts.
- **Brief**: one screen at most, with fact blocks of four short points and no paragraphs. The
  decisions, each with its options and its reason, do not fit, and agdoc drops what does not fit.
- **Custom**: agdoc designs a new view each time, so two tasks would get two different pages. A page
  that he reads after each task must look the same each time, so he finds the red block and the
  decision to check at the same place.

---

```text
Subject: the task "{{TITLE}}" of this repository, for its owner before he merges pull request #{{PR}}.
Source: two files, and nothing else: {{TASK_DIR}}/built.md and {{TASK_DIR}}/decisions.md. Read them; fetch nothing (no pull request, no diff, no other file). Every fact on the page comes from them; add none, and drop none.
Angle: reviewer. The reader is a senior developer with little time, who reads English as a second language. Keep the files' sentences as they are: short, active, plain words.
Design: classic.

Layout, which overrides the classic outline:
1. When the files open with a "> [!CAUTION]" block, that block is the first element inside main.doc, before header.top: a div.callout.risk with style="border: 2px solid var(--bad); border-left-width: 8px; background: color-mix(in srgb, var(--bad) 16%, transparent); padding: 14px 18px", whose first child is <b style="font-size: 18px; color: var(--bad)"> with the block's first line, then its numbered list as an <ol>, then its last line as a <p>. A reference to a decision or to the criteria in it is a link to that part of the page. Nothing comes before it. When the files have no such block, the page has no callout before the header.
{{ILLUSTRATION: when the files open with an "Illustration." line, put that line in a <p class="muted"> as the very first element, before the red block, and add a ".pill.warn" with the word "illustration" to the header's meta row.}}
2. header.top: .kind is "Lem · before you merge"; h1 is the title after "What was built:"; .sub is the line under the title in built.md (pull request, branch, green or not green, the mode); .meta has the pull request as a link, the branch in <code>, and a pill: ".pill.ok" "green" or ".pill.bad" "not green".
3. .tldr: the first sentence of "What was built" and the first sentence of "Why we want it", as two sentences.
4. nav.toc: "What you asked", "What was built", "Not built", "See it work", "Decisions", and "top" last.
5. The sections of built.md as h2 sections, in their order, with their lists, quotes and code blocks as they are. The criteria stay a numbered list.
6. One h2 "Decisions" section from decisions.md: its first line as a <p>, then its table, with each number a link to its decision's id and each "who decided" cell as a pill: "waits for you" .pill.bad, "nobody agreed" .pill.bad, "two expert models" .pill.warn, "a for-and-against test" .pill.alt, "the personas" .pill.info, "your ruling" .pill.ok, "you" .pill.ok, "an agent" and "the task's agent" .pill.muted. A "check this one" in a row is a .pill.warn after the first pill.
7. Then each decision as a div.callout with id "d{{N}}" and --c set to the color of its pill (var(--bad), var(--warn), var(--alt), var(--info), var(--ok), var(--muted)). Its first child is <b> with "N. the question"; a "Waits for you", "Not green" or "Check this one" line follows as a <p><strong>; then the decision's list as a <ul> with each label in <b>.
8. Footer: "Sources: built.md and decisions.md in {{TASK_DIR}}, written by Lem from the task's records · generated {{DATE}}".

Save the page as {{TASK_DIR}}/page.html, and its markdown translation as {{TASK_DIR}}/page.md, then embed it with embed-md.py. Do not run show.sh: Lem opens the page when the owner asks for it (/lem status {{SLUG}}). Reply with the path of the page only.
```

---

The values:

| Value | From |
| --- | --- |
| `{{TITLE}}` | the first heading of `task.md` |
| `{{PR}}` | `landing.json` `pr.number` |
| `{{TASK_DIR}}` | the task's folder, `.lem/state/tasks/{{SLUG}}` in the main checkout |
| `{{SLUG}}` | the task's slug |
| `{{DATE}}` | the time of `propose`, as `YYYY-MM-DD HH:MM` in the machine's zone |
| `{{ILLUSTRATION ...}}` | a sample made by hand only; Lem's own brief never has this line |
