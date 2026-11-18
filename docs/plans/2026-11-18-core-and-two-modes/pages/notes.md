# Notes for the builder of plan task 4

## The real task, and why that one

All four tasks of `lem-scratch` are small changes. The plan (task 4) gives a small change no pages,
so no real task is the case the pages are for. The sample is `report-heading-names-both-months`
(pull request #4, open, green): it has the most records (an investigation, four decisions, one of
them the owner's, a conflict with another task). `readme-names-the-test-command` ended with no
change, and the other two have one decision each.

## What the records lack, or hold in a form that is hard to use

1. **A taken decision has no options.** `decisions.jsonl` keeps `options` only on `kind: asked`. A
   `taken` line has `what`, `chose`, `why`, `by`, `undo`. The options of the three real decisions
   in `decisions.md` come from the `why` text and from `investigation.md` ("A fix that adds only the
   month would give 29 Dec-2 Jan 2026"). The builder needs a key `options` on `log`, required for
   every level above the task's agent, or the file writes only "Taken" for such a decision.
2. **No level and no trace.** `by` has `lead`, `personas`, `owner`, `lem`, `timeout`, `experts`.
   There is no `gate` and no `dialectic`, and no record of the levels that did not settle a decision.
   Plan task 3 adds `level`; "How it went" needs, for each level below the one that settled it,
   what it said (a vote such as 2 to 1, or "no clear result") and whether it changed the pick.
3. **The gate's ruling is not cited.** A decision that the gate takes from a ruling must keep the
   ruling's file and its sentence, or "your ruling of DATE in FILE" cannot be written.
4. **`by: lem` hides who chose.** Real decision 4 is `by: lem`, but its `why` says "the
   investigator's pick". The file says "an agent, the one that found the cause" only from the text.
5. **Nothing marks a decision to check.** `investigation.md` says "Not verified: the heading form the
   owner wants ... I chose one", and no key of the decision carries it. The shape marks "check this
   one" when one agent alone took a choice that sets the text of a criterion. Today no `criterion`
   line links decision 4, because the stories were approved in the same second with the form in
   them; the link exists only in `undo` ("change the story's examples and the test's expected
   strings").
6. **A replaced decision has no link.** Real decision 3 (the owner's "start now") undoes decision 1,
   and `readme-names-the-test-command` decision 3 says "(replaces decision 2)" inside `what`. A key
   `replaces: ID` lets the file fold the old one into the new one.
7. **`what` is a noun phrase.** "the heading form of a range across two months or two years". The
   file needs a question. Either the record keeps a `question`, or the file's writer rewrites
   `what`, which needs a model, not a script. A key is cheaper and predictable.
8. **The owner's words sit in `why`.** For `by: owner`, real decision 3's `why` is his sentence in
   the imperative. `answer` keeps `words` and `why` apart; `log --by owner` does not.
9. **No interview record.** With the owner, his interview answers are in no file; `task.md` holds
   only Lem's summary (`## Outcome`, `## Done when`). The full sample's "In the interview you also
   said" needs his answers, verbatim, from a record of the interview.
10. **No "see it" line.** No record holds one command that shows the change to a person. For the real
    sample I wrote the command by hand and ran it against the branch's `shop/dates.py` (fetched with
    `gh api` into a folder under `/tmp/lem-pages`, then removed): it printed `28 Feb-3 Mar 2026` and
    `29 Dec 2025-2 Jan 2026`. A line "See it: COMMAND -> OUTPUT" in the builder's report, which the
    checks run once, closes this.
11. **"What was built" is in the builder's words.** `report.md` "Changed" names the function and the
    commit. The file wants what a person can now see, which is the criteria's text more than the
    report's. For a full change the criteria are enough; for the "code is in" sentence, the diff's
    file names are enough.
12. **The task's notes have no headings in the small path.** `notes.md` of the real task is one line,
    not the `NOTES` headings of `land.py`. "Delete the backlog item after the merge" came from that
    line only.
13. **The mode is not recorded yet** (plan task 2), and neither is the moment he said "go alone",
    which the line under the title names.
14. **Two record forms live side by side.** Older tasks keep `stories.json`, `stories.md` and
    `checks.stories`; newer keep `criteria.*`. The writer reads both, as `land.py`'s
    `checked_criteria` does.

## The choices of form I am least sure of

1. **The merge of a green pull request gets no red block.** The owner said of the two things that
   always wait (a step that cannot be reversed, and the merge): "It can be described as big red
   flag". I read "the merge" as "a merge he must not do blindly": a task that ran alone is never
   green (plan task 2), so its merge is always in the red block, as item text ("Merge it only when
   you agree with both"). A green pull request with him there says "It waits for your merge" in the
   plain line under the title. The alternative: every file opens with a red block that names the
   merge. Then the block is always there, and a block that is always there stops being seen.
2. **A pick of the two expert models is not a cause of "not green".** Plan task 3 makes only the last
   level ("the lead's pick stands") not green. Today `land.py` `not_green` makes every experts' pick
   not green. The sample follows the plan. The alternative keeps today's rule; then decision 3 of the
   full sample moves into the red block as a fourth item.
3. **Classic, with a louder red block.** Classic's own `.callout.risk` was too quiet in the first
   render, so the brief adds one style attribute (colors from `--bad` only). The alternative is
   Custom with a fixed description in the brief; it gives agdoc more room for "beautiful", but agdoc
   designs it again for each page, and two tasks then look different.

Smaller ones, each easy to change: the red block in the files is GitHub's `> [!CAUTION]`, which
GitHub and most viewers show in red (the alternative is a `## Waits for you` heading); the order of
decisions is by how likely he wants to change one, so his own decision comes last; "the task's agent"
stands for the lead.

## What I could not check

- The page outside agterm only. In headless Chrome with no `--agterm-*` values, the light theme's
  page is gray (`#ccc`): the classic template mixes the background 80 % with black. In agterm the
  terminal's own colors set it. `page-light.png` and `page-dark.png` show the first screen of each.
- Whether agdoc honors "Do not run show.sh" and the save path in a brief. Its step 1 lets a brief
  override the outline; it says nothing of steps 5 and 7. A real call is the test.
