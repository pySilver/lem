# The brief of the owner's page of a full change

`stages/pages.md` fills it, after `propose` wrote `built.md` and `decisions.md`, and `make-page`
passes the text in the fence as it is. The `{{...}}` values are the task's, from the table under
the fence; the rest is fixed. The page has one design for every task, so that the owner finds the red
block and the decisions to check at the same place each time. The owner saw a sample of it and said
"sample page is fine" (2026-11-18).

```text
Subject: the task "{{TITLE}}" of this repository, for its owner before the merge of {{PULL_REQUEST}}.
Source: two files, and nothing else: {{TASK_DIR}}/built.md and {{TASK_DIR}}/decisions.md. Read them; fetch nothing (no pull request, no diff, no other file). Every fact on the page comes from them; add none, and drop none.
Angle: reviewer. The reader is a senior developer with little time, who reads English as a second language. Keep the files' sentences as they are: short, active, plain words.
Design: classic.

Layout, which overrides the classic outline:
1. When the files open with a "> [!CAUTION]" block, that block is the first element inside main.doc, before header.top: a div.callout.risk with style="border: 2px solid var(--bad); border-left-width: 8px; background: color-mix(in srgb, var(--bad) 16%, transparent); padding: 14px 18px", whose first child is <b style="font-size: 18px; color: var(--bad)"> with the block's first line, then its numbered list as an <ol>, then its last line as a <p>. A decision or a choice named in it by its number is a link to that decision on the page. Nothing comes before it. When the files have no such block, the page has no callout before the header.
2. header.top: .kind is "Lem · before the merge"; h1 is the title after "What was built:"; .sub is the line under the title in built.md; .meta has the pull request as a link when there is one, the branch in <code>, and a pill: ".pill.ok" "green" or ".pill.bad" "not green".
3. .tldr: the first sentence under "What was built" and the first sentence under "Why the owner wants it", each only when the file has it.
4. nav.toc: one link for each h2 section that the page has, in its order, and "top" last.
5. The sections of built.md as h2 sections, in their order, with their lists, quotes and code blocks as they are. The criteria stay a numbered list.
6. One h2 "Decisions" section from decisions.md: its first line as a <p>, then its table, with each number a link to its decision's id and each "Who decided" cell as a pill: "waits for the owner", "no level", "taken without the owner", "the timeout" .pill.bad; "two expert models" .pill.warn; "the dialectic" .pill.alt; "the personas" .pill.info; "the gate", "the owner" .pill.ok; "the lead", "Lem" .pill.muted. A "not green" in a cell is a ".pill.bad" "not green" after the first pill.
7. Then each decision as a div.callout with id "d{{N}}" for its number N, and --c set to the color of its pill (var(--bad), var(--warn), var(--alt), var(--info), var(--ok), var(--muted)). Its first child is <b> with its heading; a "Not green." line follows as a <p><strong>; then the decision's list as a <ul> with each label in <b>.
8. Footer: "Sources: built.md and decisions.md in {{TASK_DIR}}, written by Lem from the task's records · generated {{DATE}}".

Save the page as {{TASK_DIR}}/page.html, and its markdown translation as {{TASK_DIR}}/page.md, then embed it as the skill says. Do not show the page: Lem opens it when the owner asks for it (/lem status {{SLUG}}). Reply with the path of the page only.
```

| Value | From |
| --- | --- |
| `{{TITLE}}` | the first heading of `built.md`, after "What was built:" |
| `{{PULL_REQUEST}}` | "pull request #N" from `pull_request` in the output of `propose`, or "its branch" where there is none |
| `{{TASK_DIR}}` | the task directory, `.lem/state/tasks/SLUG` in the main checkout, as an absolute path |
| `{{SLUG}}` | the task's slug |
| `{{DATE}}` | the time of `propose`, as `YYYY-MM-DD HH:MM` in the machine's zone |
