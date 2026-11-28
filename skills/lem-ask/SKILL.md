---
name: lem-ask
description: "Lem's question page: shows one question as a page in agterm and returns the answer as JSON. Lem opens it by itself each time it asks the owner to choose or to approve; it is no call of the owner's."
disable-model-invocation: true
allowed-tools: Bash(lem ask *)
---

# lem-ask — the question page

One command opens the question over **your own** agterm session, waits for the answer, and prints it as
JSON. The runtime (layout, styles, charts, diagrams, sliders, keyboard) is prebuilt; you describe the
question. The command is `lem ask`, a name of Lem's command `lem`.

Run it with the Bash tool's `timeout: 600000`. It waits up to 570 s, then returns `result.outcome: "pending"` with the page still open
(see [Waiting](#waiting)).

## When to ask with a page

- **Ask with a page** whenever the user has to choose or approve: a design fork, a sequencing call, a plan
  or its parts, and a choice between just two options too. A short list of labels is where the user stops
  understanding the difference; on a page each option carries what it changes and what it costs. Pictures,
  code, tuned values and related decisions on one page come on top of that.
- **Ask in the terminal** only when the user answers by typing (a name, a path, a number), or for a bare
  "go ahead?" on a step you just described.
- **The user's own instructions win.** When their `CLAUDE.md` or `AGENTS.md` says how to ask questions,
  follow it; this section is the default, not an override.
- **Don't check for agterm first.** Run `lem ask`: outside agterm it returns `result.outcome: "no-agterm"`, and you ask in the terminal instead.
- **Only the agent talking with the user asks.** A subagent, a plan executor or a background worker returns
  its question to whoever started it. In an unattended run (`claude -p`, where Claude Code sets
  `CLAUDE_CODE_SESSION_ATTENDED=0`) `lem ask` returns `result.outcome: "unattended"` and opens nothing.

## Fastest: one line

```bash
lem ask q "Which store for sessions?" "*Redis|already runs the job queue|no new service" "Postgres table|one table, expiry index" "Stateless JWT|cannot revoke"
```

Each option is `Label|subtitle`; a leading `*` marks it recommended, and a third field says why
(`*Label|subtitle|why`). `--multi` for multi-select, `--context "markdown"` for a paragraph under the
question, `--title` for the topic line above it.

## Normal: a JSON spec in a file

Write the spec with your file-writing tool, to an absolute path in a scratch directory:

```json
{
  "title": "Session storage",
  "prompt": "Where should sessions live?",
  "context": "Sessions live in process memory, so every deploy logs everyone out.",
  "options": [
    {"id": "redis", "label": "Redis", "subtitle": "Managed, TTL per key",
     "recommended": "Already running for the job queue",
     "pros": ["Sub-ms reads"], "cons": ["Another moving part"]},
    {"id": "pg", "label": "Postgres table", "subtitle": "One table, expiry index"}
  ]
}
```

```bash
lem ask ask /tmp/session-storage.json
```

Relative paths inside the spec (images, `file` blocks) resolve beside the spec file.

`lem ask ask -` reads the same spec from stdin and resolves those paths from the working directory. Keep it
for a terminal. From an agent it needs a heredoc, and in a Claude Code worktree session the Bash guard
reads a heredoc body as shell and refuses a `{` followed by a quote, which every spec holds: 16 of 17
`lem ask ask - <<'JSON'` calls were refused in the author's worktree sessions (Claude Code 2.1.319 to 2.1.322).

## Write the question first

The prompt is the biggest thing on the page; everything else supports it.

- `prompt`: **one short, direct question**, ideally under 12 words, ending in `?` or an imperative
  ("Tune the card style until it looks right"). The user should know what to do from it alone.
- `title`: the topic in two to five words ("Session storage"). Shown small above the prompt.
- `hint`: one line under the prompt saying what matters or how to answer. Not a second question.
- `context` (top level, shared by every question) or `body` (one question's own; `context` on a question
  means the same): the evidence — numbers, a diagram, a diff. Shown under the prompt.
- `header`: one or two words per question, for the tabs and the review list.

## Carry the context

A page is worth opening only when it shows more than a numbered list would. The user answers from the page
alone: the plan, the code and your last terminal message are not in front of them.

- **What is being decided lives on the option.** Approving acceptance criteria, tasks, findings or plan sections: one
  option each, labeled by what it says rather than by its number ("4 · an unplaceable brand stays pending",
  never "Criterion 4"), the gist in `subtitle`, the full text in `detail` (or
  `{"md": {"file": "docs/plans/x.md", "lines": "40-52"}}`), and `expanded: true` so the text is open without
  a click. `lem ask` refuses an option whose label only counts and that carries nothing else.
- **What several options share goes above them**: the example from the eval, the numbers, today's flow as a
  diagram, in `context` or the question's `body`.
- **Before you send**, read the page as the user will: could they answer without opening anything else? If
  not, it is missing the thing they need to judge.

## Pick the component for the question

| The answer is… | Use | Template |
| --- | --- | --- |
| one of a few alternatives | options, `layout: "list"` | `pick` |
| alternatives whose trade-offs matter | `layout: "compare"` (side by side, pros/cons visible) | `tradeoffs` |
| a visual (a diagram, a layout, a sample) | options with `preview` → `grid` | `architecture`, `layouts`, `design-tokens` |
| a judgement on code the user must read | `code` / `diff` blocks from `{"file": …}` in `context` | — |
| yes / no / later | `layout: "inline"` | `confirm` |
| several items from a list | `mode: "multi"`, `min`/`max` | `checklist` |
| a number or color that is a matter of taste, with no standard step to choose from (radius, gap, hue, speed, size, weight, delay) | **`controls`** — sliders with a live preview | `tune` |
| words | `mode: "text"` | `text` |
| several related decisions | `questions: [...]` — tabs, then a review of every answer | `design-tokens` |

When there *are* standard values (4/8/16 px, a design-system scale), offer them as options with previews.
When the value is continuous or purely taste, give sliders: the user sees the result while dragging.
Combine them: options to pick a direction, then a `controls` question to fine-tune it (see `demos/ui-kit`).

`lem ask templates` gives the templates and their directory in `result`; read one and fill it. `lem ask demo NAME`
opens one, as do the larger showcases in `demos/` (`motion`, `ui-kit`, `auth-flow`, `rollout`, `pricing`) —
read those for combinations.

## Show the real code

Never paste source into a spec by hand: escaping it into JSON is where a spec breaks or a snippet drifts
from the file. Point at the file instead and `lem ask` reads it when it builds the page:

```json
{"code": {"file": "src/session/store.py", "lines": "40-62"}}
{"diff": {"file": "/tmp/change.patch"}}
{"md": {"file": "docs/plans/sessions.md"}}
{"mermaid": {"file": "docs/flow.mmd"}}
```

- `lines` is `"40-62"`, `"40"` or `[40, 62]`; omit it for the whole file. A `code` block from a file gets its
  path and range as its title, numbered lines (so a note can say "line 47"), and its extension as `lang`;
  a `title`, `start` or `lang` you set yourself wins.
- For a diff, write it to a file first (`git diff main -- src/session > /tmp/s.patch`), then name that
  file in the spec.
- A missing file or a range past its end is an error (exit 1): the user is deciding on that code, so a page
  without it would mislead. So is a whole file of more than 300 lines as `code` — name the lines the question
  is about.

## The answer

```json
{"ok": true, "result": {"outcome": "answered", "pageID": "…",
 "answers": {"answer": {"selected": ["redis"], "labels": ["Redis"], "text": "but only for prod"}}}}
```

- `answers` is keyed by question id (`answer` for a single-question spec, `q1`, `q2`… when unnamed).
- `selected` lists option ids in display order; `text` is present only when the user typed something —
  it may come **alone** (their own answer) or **with** a selection (a note on it). Read both.
- A `controls` question adds `values` (`{"radius": 12, "hue": 174, "shadow": true}`). `selected` holds a
  preset only if the user kept it untouched; `from` names the preset they started from and then changed.
- `extra` appears when page JavaScript called `api.setExtra(...)`.
- `from` appears on the answer of a card in a task's session of Lem: `session` for a pick on the card,
  `board` for the owner's answer on Lem's board (see [A card of a task's session](#a-card-of-a-tasks-session)).
Every page outcome has exit 0. Read `result.outcome`:

- `chat` with `text`: the owner pressed **Discuss in chat**. Take the question back to the terminal.
- `dismissed`: the owner closed the page without an answer (⌘W).
- `no-agterm`: ask in the terminal, or use the browser when the owner wants it.
- `unattended`: leave the question for an attended session.
- `pending`: the overlay stays up after the wait. Run `lem ask wait PAGEID`.
- `busy`: the session already shows an overlay. If the result names a question page, run
  `lem ask wait PAGEID`. If it gives no page id, ask in the terminal.
- `refused`: the task cannot take the card's answer. Read `result.said` for the reason.
- `unavailable`: the terminal or browser could not show or read the page. Read the result's reason.

A refused spec has exit 1 and `refusal.why` with the reason. Exit 2 is a wrong command line.

## Spec reference

Top level: `title`, `subtitle`, `source` (replaces "Claude is asking"), `context` (blocks),
`width: "narrow"` (for short questions), `submitLabel`, `chat: false` (hide Discuss in chat), `script`
(JS, see [Extending](#extending)), `style`, `review`, `size` (see [Look, size and review](#look-size-and-review)),
and **either** the fields of one question **or** `questions: [...]` (tabs, answered in order).

Question: `id`, `header`, `prompt`, `hint`, `body` (blocks; `context` works too), `recommendation` (markdown banner naming the
overall pick), `mode` (`single` default · `multi` · `text`; `tune` is implied by `controls`), `min`/`max`
(multi), `layout` (`list` · `grid` · `compare` · `inline`; default `grid` when any option has a
`preview`, `inline` for presets, else `list`), `columns`, `expanded: true` (open every option's details),
`optional: true` (may submit empty), `text` (`false` to drop the free-text box, or
`{label, placeholder, required, multiline, value}`).

Any other key, at any of these levels, is an error that names the nearest valid one, since the page would
drop it without a word. A key starting with `_` is yours (data for a `script`) and passes. A value of
another type than the page reads is an error too, since the page would show it wrong: a text field (`prompt`, `label`,
`header`, `subtitle`…) that is not a string, a flag that is not `true` or `false`, a `mode`, `layout`,
`width`, `style` or control `type` the page does not know, and `tags`, `pros` or `cons` that are not a
list of strings.

Option: `id`, `label`, `subtitle` (gray line), `recommended` (`true`, or a string = the reason, shown
under it), `badge` (replaces the "Recommended" word), `tags` (small chips: effort, risk), `pros`, `cons`,
`detail` (blocks, behind "details"), `preview` (a block shown as the card's visual), `default: true`
(preselected), `values` (on a `controls` question: a preset). Strings may stand in for options:
`"options": ["Yes", "No"]`.

### Controls (sliders with a live preview)

```json
{
  "title": "Dashboard cards",
  "prompt": "Tune the card style until it looks right",
  "controls": [
    {"id": "radius", "label": "Corner radius", "min": 0, "max": 28, "value": 8, "unit": "px"},
    {"id": "hue", "label": "Accent", "type": "hue", "value": 220},
    {"id": "speed", "label": "Duration", "min": 100, "max": 1200, "step": 20, "value": 300, "unit": "ms"},
    {"id": "weight", "label": "Title weight", "type": "select", "options": ["500", "600", "700"], "value": "600"},
    {"id": "shadow", "label": "Shadow", "type": "toggle", "value": false, "on": "0 6px 18px rgba(0,0,0,.3)", "off": "none"},
    {"id": "brand", "label": "Brand color", "type": "color", "value": "#0d9488"}
  ],
  "preview": {"html": "<div style='border-radius:var(--radius);background:hsl({hue} 65% 45%);box-shadow:{shadow};font-weight:{weight};transition:all var(--speed)'>Sample</div>"},
  "baseline": true,
  "options": [{"id": "soft", "label": "Soft", "values": {"radius": 14, "shadow": true}}]
}
```

- Control `type`: `range` (default; `min`, `max`, `step`, `unit`) · `hue` (0–360, rainbow track) ·
  `color` (picker, `#rrggbb`) · `select` (segmented, `options`) · `toggle` (`on`/`off` are the strings it
  substitutes; default `"1"`/`"0"`).
- In `preview` (any block), `{id}` is replaced by the raw value (`12`, `#0d9488`, `600`) and `var(--id)`
  carries the unit (`12px`, `300ms`). The preview re-renders on every change, which also replays CSS
  animations; `r` or the ⟳ button replays without a change.
- `baseline: true` (or a label string) shows the starting values beside the live one ("Now" | "Yours").
- `options` with `values` are presets: picking one moves the sliders.
- Each slider has ↺ to return to its starting value.
- Optional linking: a `preview` may read earlier answers on the same page — `{@qid}` is the option id
  chosen on question `qid` (comma-joined for multi), `{@qid.label}` its label, `{@qid.ctl}` a slider value
  from another controls question. Use it when the fine-tuning should apply to what was just picked
  (`demos/motion`); skip it when the questions are independent.

### Blocks

Used in `context`, `body`, `detail`, `preview`. A plain string is markdown (`**bold**`, `*em*`,
`~~strike~~`, `` `code` ``, `[link](https://…)`, headings `#` to `######`, lists with `-`, `*`, `+` or
`1.`, nested by indent, `- [ ]` task items, `> quote`, `---` rules, fenced code with ```` ``` ```` or
`~~~`, and GFM pipe tables with a `|---|` delimiter line and `:` alignment marks). A table whose header
cells are all empty renders with no header row; a pipe inside a code span stays in its cell, and `\|`
is a pipe in the text; a cell past the header's count is dropped, as in GFM. HTML in markdown shows as
text, and so do `_em_`, `__bold__` and a link that is not `http(s)`; `![alt](url)` shows as a link, so
use the image block. Any block takes `title`, `caption` and `card: true`.

| Block | Shape |
| --- | --- |
| markdown | `"text"` or `{"md": "text"}` |
| diagram | `{"mermaid": "flowchart LR\n A --> B"}`, or a ` ```mermaid ` fence in markdown — the local chart library draws Mermaid syntax and leaves the source visible if a chart cannot draw |
| chart | `{"chart": {"type": "bar"\|"line"\|"area"\|"hbar"\|"donut"\|"pie", "labels": [...], "series": [{"name", "values", "color"}], "unit": " ms"}}` — `values` alone for one series. Optional: `title`, `highlight` (index or label; not donut/pie), `marks: [{"value", "label"}]` (threshold lines), `min`, `max`, `height`; donut/pie `colors`, `center`, `size`; hbar `labelWidth` |
| stat tiles | `{"stats": [{"label", "value", "delta", "good": true\|false\|null, "sub"}]}` |
| image | `{"image": "/abs/or/relative.png", "height": 160, "fit": "cover", "alt": "…"}` — local files are embedded (up to 8 MB); a missing one shows its alt text |
| code / diff | `{"code": "…", "lang": "ts", "start": 40}` (`start` numbers the lines), `{"diff": "@@ …\n+added\n-removed"}` |
| from a file | `{"file": "path", "lines": "40-62"}` in place of the text of `code`, `diff`, `md` or `mermaid` — see [Show the real code](#show-the-real-code) |
| table | `{"table": {"columns": [...], "rows": [[...]]}}`, `{"kv": {"key": "value"}}` |
| callout | `{"callout": "markdown", "tone": "ok"\|"warn"\|"bad"}` |
| design samples | `{"radius": 12}`, `{"gap": 16, "items": 4, "direction": "column"}`, `{"colors": ["#hex", {"name", "value"}]}`, `{"type": {"family", "size", "weight", "tracking", "text"}}`, `{"style": {css}, "text": "…"}` |
| layout | `{"row": [block, block]}` side by side; a list of blocks stacks |
| svg / html / js | see [Extending](#extending) |

## Extending

The standard components cover most questions. When a question needs something they don't — a real
component rendered in the user's product style, an animation, typography in a particular script, a
filterable list — build it into that question, not into the skill:

- `{"html": "…"}` / `{"svg": "…"}` — raw markup as a block or an option's `preview`. `<style>` and CSS
  animations work. Use the theme variables inside `style=`: `--fg`, `--bg`, `--accent`, `--ok`,
  `--warn`, `--bad`, `--magenta`, `--cyan`, `--muted`, `--line`, `--line-strong`, `--panel`, `--panel-2`.
  They follow the user's terminal theme; hardcode colors only when the color *is* the question.
- `{"js": "code"}` — runs as `function(el, api)`; draw into `el`. The top-level `script` runs once with
  `api`. `api.setExtra(questionId, value)` (returned as `extra`), `api.setText(questionId, text)`,
  `api.select(questionId, optionId)`, `api.submit()`, `api.block(spec)` / `api.chart(spec)` (render a
  standard block), `api.md(text)`, `api.css("--accent")` (resolved color).
- Prefer `controls` over hand-written sliders: they come with keyboard, reset, presets, baseline and the
  review screen for free.
- Escape nothing in normal fields — the runtime escapes text. `html`, `svg` and `js` are raw, and the page
  runs with agterm's bridge, which can type into terminals: never paste outside text (an issue body, a log
  line, a file you did not write) into them; put it in markdown or `code`. Source code goes in through
  `{"file": …}`, never pasted into `html`.

## How the user answers

Keys `1`–`9`, arrows, `Space`, `Enter`, `Tab` into the note; the page lists them in its footer and `?`
shows the rest. ⌘W dismisses. Nothing here needs explaining to the user.

## Look, size and review

Defaults come from `defaults.json` beside this file, overlaid by the table `[ask]` of the user's own
`~/.config/lem/settings.toml` (`$XDG_CONFIG_HOME/lem/settings.toml` when that variable is set) — the
user's file is where their preferences live, so don't override them unless a question needs it. A value
of the wrong type there (`style = "minmal"`, `browser = 2026-11-23`) is an error that names the file, the
key and the value. Per call, a flag or the same key in the spec wins:

- `style`: `refined` (soft cards) · `minimal` (hairline rows) · `bold` (big type, filled choice) ·
  `terminal` (monospace). `--style NAME`.
- `size`: percent of the session pane as a floating panel, `"auto"` (66–90% by content) or `"full"`.
  `--size N`, `--full`.
- `status`: a table of `asking = [...]` and `answered = [...]` — the `agtermctl session status` arguments set while
  the question is open and after it is answered (default `blocked` / `active`; add `--color`, `--shape`,
  or `--sound default` to hear a question arrive while you are in another session).
- `review`: the answer list shown before sending — each choice, a thumbnail of a visual one, slider
  values with the live preview, and the user's note. `auto` = when the page has several questions, or a
  note was typed on a choice question · `always` · `never`. `--review MODE`. Question tabs also show the
  answer so far ("Radius · 14 px + note").

## Behavior you can rely on

- Opens over **your** session (`$AGTERM_SESSION_ID`), never the one the user is looking at, and does not
  switch them to it unless you pass `--follow`. While it waits, the sidebar shows the amber blinking
  "asking" triangle (the same glyph a built-in question gets); it goes back to "working" when answered.
  `--no-status` leaves the glyph alone. The last call of `lem ask wait PAGEID` sets the choice.
- `--chromeless` hides the overlay's title strip.
- Outside agterm it returns the outcome `no-agterm`. With `--browser` it serves the page on `127.0.0.1`
  and opens the default browser instead, inside agterm too; `browser = true` under `[ask]` in the user's
  defaults does the same outside agterm only. The answer comes back the same way, and closing the tab gives the outcome `dismissed`. That path lives only as
  long as the command: no `--no-wait`, and a timed-out browser question cannot be resumed.
- `AGTERMCTL` names the `agtermctl` executable when it is not on `PATH`.
- The page carries the bundled chart library when a block uses Mermaid. A rendered file needs no
  download to draw a chart.
- Generated pages land in `$TMPDIR/lem-ask/` and are pruned after a day. `lem ask render spec.json -o out.html`
  builds one without opening it (for checking a spec).

## Waiting

The default wait is 570 s so it fits one Bash call. The outcome `pending` gives a page id;
run `lem ask wait PAGEID` to resume the wait. A command with `--no-wait` gives the
outcome `open` and its page id immediately. To wait in the background, set the Bash tool's
`run_in_background: true` and give the command `--timeout 86400`. The 570 s limit is for
foreground calls. The overlay remains open after the wait ends, until an answer or a close.

Run `lem ask close PAGEID` to close one question this session shows. Run `lem ask close` to
close the current question. The result is `closed` or `gone`. If an answer already counted,
the command gives that answer.

## A card of a task's session

If `LEM_TASK` names a task in the repository, Lem keeps the page and its questions in the task's
`cards/` folder. It adds the card's question and digest to `task.json`. The same page opens from
the board's **Waits for you** list. A question from an ordinary terminal session has no task card.

The board takes a choice with a note, a text answer to a text question, or the values of a tune
question. On a touch screen the page hides the keyboard hints. Save questions for the conversation
for the task's session, where the page offers **Discuss in chat**.

A card ends once. The overlay wait and the board both read the first end on the task record.

- `result.from` is `session` for the overlay or `board` for the board.
- A board answer also gives `via` (`local` or `door`), `device` (`phone` or `computer`), and
  a `said` line. When the board's answer is the first end, the board server closes the card's
  page in the session at once, also with no wait (after `--no-wait`, or after a wait that
  returned `pending`). A wait that still runs reads the same answer.
- If the owner answers on the board after a wait returns `pending`, `lem ask wait PAGEID` reads
  the answer from the task record. A later answer or close leaves the first result in place.

## Recommending

- Recommend when you have a view, and say **why** in the `recommended` string; mark more than one when
  more than one is genuinely good. Use `recommendation` for a one-line verdict above the options.
- Up to 6 options reads well; 7–9 only for lists of peers (versions, files).
- Subtitles carry the one fact that distinguishes an option; pros/cons carry the rest.
- Batch related questions into one page (`questions`) rather than opening several in a row.
