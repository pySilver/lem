#!/usr/bin/env bash
# The landing's filing of what a review saw outside the change, as items of the backlog.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

# backlog_repo NAME: a repository with one item in its backlog folder, docs/backlog, on the base
backlog_repo() {
  local repo=$WORK/$1
  git init -q -b main "$repo" && ident "$repo" && project --repo "$repo" init --base main >/dev/null
  printf '%s\n' '[branch]' 'base = "main"' 'history = "keep"' 'land = "agent"' '[checks]' 'commands = ["true"]' > "$repo/.lem/project.toml"
  mkdir -p "$repo/docs/backlog" && echo '# an item from before' > "$repo/docs/backlog/existing.md" && echo one > "$repo/app.txt"
  git -C "$repo" add -A && git -C "$repo" commit -q -m "chore: start" && on_github "$repo"
}
# blg_task SLUG: a full change of the backlog repository, with the lead's read of its criteria
blg_task() { task_in "$BLG" "$1" app.txt two && read_in "$BLG" "$1"; }
# checked_in REPO SLUG: the task takes the landing line, its base, its polish pass and its gate
checked_in() { land --repo "$1" start "$2" >/dev/null && land --repo "$1" base "$2" >/dev/null && polish_in "$1" "$2" && land --repo "$1" checks "$2" >/dev/null; }
backlog_repo backlog-land
BLG=$WORK/backlog-land

# What a review saw outside the change is filed after it, as new items in the backlog folder: that asks
# for no other review. Any other file does, an item that was on the base included. One task is reviewed
# once, and each change after the review starts from the reviewed tip; the rest of the rule, a deletion
# and a new file outside the folder among it, is tests/unit/test_backlog.py's.
task_in "$BLG" after-review app.txt two
tree=$(project --repo "$BLG" worktree-dir after-review)
checked_in "$BLG" after-review
land --repo "$BLG" read after-review --record "$(clean after-review 1)" >/dev/null
reviewed=$(git -C "$tree" rev-parse HEAD)
# after_review CHANGE: CHANGE run in the reviewed worktree and committed, and the checks again; prints what is
# due, then puts the worktree back on the reviewed tip
after_review() {
  (cd "$tree" && sh -c "$1")
  git -C "$tree" add -A && git -C "$tree" commit -q -m "docs(backlog): after the review" && land --repo "$BLG" checks after-review >/dev/null
  land --repo "$BLG" read after-review | field 'd["due"]'
  git -C "$tree" reset -q --hard "$reviewed"
}
added=$(after_review 'echo "# a defect from before" > docs/backlog/new.md')
edited=$(after_review 'echo more >> docs/backlog/existing.md')
if [ "$added" = none ] && [ "$edited" = review ]; then
  pass "a new item in the backlog folder after a review keeps the review, and an edit of an item that was on the base asks for another"
else
  fail "backlog items after a review: $added / $edited"
fi
project --repo "$BLG" state after-review dropped "the test is over" >/dev/null

# One task, two rounds of its review, and the defects each saw outside the change and called over the bar, through
# the real commands: what decides an item's name and whether an item file is a defect is tests/unit/test_backlog.py's.
# The branch holds an item with no place before the review, under the name D's title gives. Round 1
# sees A and D; the owner then says no to A's item. Round 2 sees B, and A, D and E again: E has D's place
# and title and another run. A commit then removes B's item, and `file --again` puts it back. The name
# loop of `file` and propose's refusal of a removed item are inline in land.py, so the journey keeps them.
A='{"where": "src/json.py:parse", "title": "Empty input crashes the parser", "what": "parse with an empty string raises IndexError, on the base commit too.", "bar": "over"}'
B='{"where": "src/csv.py:read", "title": "A quoted comma splits the field", "what": "read of a line with a comma inside quotes gives three fields, on the base commit too.", "bar": "over"}'
D='{"where": "src/json.py:parse", "title": "An item from before", "what": "parse of a document with no root returns None, on the base commit too.", "bar": "over"}'
E='{"where": "src/json.py:parse", "title": "An item from before", "what": "parse of a document of one number returns a string, on the base commit too.", "bar": "over"}'
# the start of a record, and outside DEFECT...: its end, with the defects (bash 3.2 splits a quote escaped inside "$(...)")
a_read='{"kind": "read", "answered": ["codex"]'
read_must_fix='{"kind": "read", "answered": ["codex"], "must_fix": 1'
a_round='{"kind": "round", "ran": [{"name": "correctness", "why": "a file of the app changes"}], "answered": ["codex"]'
outside() { local IFS=,; printf '"outside": [%s]}' "$*"; }
blg_task two-defects
tree=$(project --repo "$BLG" worktree-dir two-defects)
echo '# An item from before' > "$tree/docs/backlog/an-item-from-before.md" && git -C "$tree" add -A && git -C "$tree" commit -q -m "docs(backlog): an item with no place"
checked_in "$BLG" two-defects
item_a=$tree/docs/backlog/empty-input-crashes-the-parser.md
item_b=docs/backlog/a-quoted-comma-splits-the-field.md
item_d=$tree/docs/backlog/an-item-from-before-json-parse.md
# the day before the review and after its filing: an item filed at midnight carries one of the two
day_from=$(date +%F)
first=$(land --repo "$BLG" read two-defects --record "$(record two-defects 1 "$read_must_fix, $(outside "$A" "$D")")" | field '(d["next"], [(f["round"], f["title"]) for f in d["to_file"]])')
filed_a=$(land --repo "$BLG" file two-defects | field '([(f["round"], f["item"]) for f in d["filed"]], d["same"])')
day_to=$(date +%F)
commit_a=$(git -C "$tree" show --name-only --format=%s HEAD | tr '\n' '|')
"$PY" -c 'import sys; p = sys.argv[1]; t = open(p).read().replace("worth: later", "worth: no").replace("\n\nSeen outside", "\n\nThe owner: an empty input never reaches parse, the reader refuses it first.\n\nSeen outside"); open(p, "w").write(t)' "$item_a"
echo fixed > "$tree/notes.txt" && git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: the must-fix, and the owner's no" && land --repo "$BLG" checks two-defects >/dev/null
second=$(land --repo "$BLG" read two-defects --record "$(record two-defects 2 "$a_round, $(outside "$B" "$A" "$D" "$E")")" | field '(d["next"], [(f["round"], f["title"]) for f in d["to_file"]])')
unfiled=$(land --repo "$BLG" propose two-defects --title "fix: two-defects" --notes "$NOTES" 2>&1 >/dev/null || true)
echo stray > "$tree/stray.txt"
dirty=$(land --repo "$BLG" file two-defects 2>&1 >/dev/null || true)
rm "$tree/stray.txt"
filed_b=$(land --repo "$BLG" file two-defects | field '([(f["round"], f["item"]) for f in d["filed"]], [f["item"] for f in d["same"]])')
commit_b=$(git -C "$tree" show --name-only --format=%s HEAD | tr '\n' '|')
tip_b=$(git -C "$tree" rev-parse HEAD)
rerun=$(land --repo "$BLG" file two-defects | field '(d["filed"], d["same"])')
[ "$(git -C "$tree" rev-parse HEAD)" = "$tip_b" ] || rerun="$rerun, and a commit"
listed=$(git -C "$tree" ls-files docs/backlog | tr '\n' ' ')
git -C "$tree" rm -q "$item_b" && git -C "$tree" commit -q -m "fix: an item less" && land --repo "$BLG" checks two-defects >/dev/null
gone=$(land --repo "$BLG" propose two-defects --title "fix: two-defects" --notes "$NOTES" 2>&1 >/dev/null || true)
back=$(land --repo "$BLG" file two-defects --again | field '[f["item"] for f in d["filed"]]')
after=$(land --repo "$BLG" read two-defects | field '(d["due"], d["to_file"])')
green=$(land --repo "$BLG" propose two-defects --title "fix: two-defects" --notes "$NOTES" | field 'd["green"]')
text=$BLG/.lem/state/tasks/two-defects/pr.md
logged=$("$PY" -c 'import json, sys; print([[i["item"] for i in e["items"]] for e in map(json.loads, open(sys.argv[1])) if e["event"] == "review.filed" and e["task"] == "two-defects"])' "$BLG/.lem/state/events.jsonl")
if [ "$first" = "('review', [(1, 'Empty input crashes the parser'), (1, 'An item from before')])" ] \
  && [ "$filed_a" = "([(1, 'docs/backlog/empty-input-crashes-the-parser.md'), (1, 'docs/backlog/an-item-from-before-json-parse.md')], [])" ] \
  && [ "$commit_a" = "docs(backlog): what review round 1 saw outside two-defects||docs/backlog/an-item-from-before-json-parse.md|docs/backlog/empty-input-crashes-the-parser.md|" ] \
  && [ "$commit_b" = "docs(backlog): what review round 2 saw outside two-defects||$item_b|docs/backlog/an-item-from-before-json-parse-2.md|" ] \
  && [ "$rerun" = "([], [])" ] && [ "$after" = "('none', [])" ] && [ "$green" = True ] \
  && sed -n 1,5p "$item_d" | tr '\n' '|' | grep -qxF -e "---|worth: later|where: src/json.py:parse|added: $day_from|---|" -e "---|worth: later|where: src/json.py:parse|added: $day_to|---|" \
  && [ "$(sed -n 6p "$item_d")" = "# An item from before" ] \
  && grep -qx "parse of a document with no root returns None, on the base commit too." "$item_d" \
  && grep -qxF -e "Seen outside the change by review round 1 of task two-defects ($day_from); the base commit has it." -e "Seen outside the change by review round 1 of task two-defects ($day_to); the base commit has it." "$item_d" \
  && grep -qF "(one read; answered: codex): must-fix, 1 must-fix, 0 should, 0 nit; it saw 2 defects outside the change, filed as \`docs/backlog/empty-input-crashes-the-parser.md\`, \`docs/backlog/an-item-from-before-json-parse.md\`" "$text" \
  && grep -qF "it saw 4 defects outside the change, filed as \`$item_b\`" "$text" \
  && [ "$logged" = "[['docs/backlog/empty-input-crashes-the-parser.md', 'docs/backlog/an-item-from-before-json-parse.md'], ['$item_b', 'docs/backlog/an-item-from-before-json-parse-2.md', 'docs/backlog/empty-input-crashes-the-parser.md', 'docs/backlog/an-item-from-before-json-parse.md'], ['$item_b']]" ]; then
  pass "two rounds that saw defects outside the change give their items in the backlog's format, each round's committed alone by land.py file; a second run files nothing; propose waits for each, and the pull request names each item"
else
  fail "the filing of two rounds: $first / $filed_a / $commit_a / $commit_b / $rerun / $after / $green / $logged / $(cat "$item_d" 2>/dev/null) / $(grep 'the review, round' "$text" 2>/dev/null)"
fi
if [ "$second" = "('none', [(2, 'A quoted comma splits the field'), (2, 'Empty input crashes the parser'), (2, 'An item from before'), (2, 'An item from before')])" ] \
  && grep -q "An item from before" <<<"$unfiled" && grep -q "lem land file two-defects" <<<"$unfiled" \
  && grep -q "$item_b" <<<"$gone" && grep -q "was removed after it was filed" <<<"$gone" && grep -q -- "--again" <<<"$gone" && grep -q "worth: no" <<<"$gone" \
  && [ "$back" = "['$item_b']" ] && [ "$green" = True ]; then
  pass "an item that was on the branch before the review proves nothing; an item that was filed and then removed stops propose with its path and the two ways on, and file --again puts it back"
else
  fail "an item that goes: $second / $unfiled / $gone / $back / $green"
fi
if [ "$filed_b" = "([(2, '$item_b'), (2, 'docs/backlog/an-item-from-before-json-parse-2.md')], ['docs/backlog/empty-input-crashes-the-parser.md', 'docs/backlog/an-item-from-before-json-parse.md'])" ] \
  && [ "$(cat "$tree/docs/backlog/an-item-from-before.md")" = "# An item from before" ] && grep -q "commit them or remove them" <<<"$dirty"; then
  pass "a defect that two rounds saw word for word is one item, also under the suffix of its place, and two defects of one place and title with two runs are two; file refuses a worktree with a change nobody committed"
else
  fail "the same defect twice: $filed_b / $dirty"
fi
if grep -qx "worth: no" "$item_a" && grep -q "^The owner: " "$item_a" \
  && [ "$listed" = "$item_b docs/backlog/an-item-from-before-json-parse-2.md docs/backlog/an-item-from-before-json-parse.md docs/backlog/an-item-from-before.md docs/backlog/empty-input-crashes-the-parser.md docs/backlog/existing.md " ] \
  && [ -z "$(git -C "$tree" status --porcelain)" ]; then
  pass "an item the owner set to worth: no, with his reason in it, is still the item of the same defect when the next round sees it again: nothing is filed over his no"
else
  fail "the owner's no and the same defect again: $filed_b / $listed / $(cat "$item_a")"
fi
project --repo "$BLG" state two-defects dropped "the test is over" >/dev/null

# The review is told of the items the branch filed before it (its builder's or the polish pass's), and leaves out a
# defect one of them names. A defect it lists at the place of such an item is one of its own, since one place holds
# many defects: it gets an item of its own, as a defect of another place does.
blg_task builder-filed
tree=$(project --repo "$BLG" worktree-dir builder-filed)
own=docs/backlog/the-parser-fails-on-an-empty-input.md
printf '%s\n' '---' 'worth: later' 'where: src/json.py:parse' 'added: 2026-11-17' '---' '# The parser fails on an empty input' '' 'parse("") raises IndexError, on the base commit too.' > "$tree/$own"
git -C "$tree" add -A && git -C "$tree" commit -q -m "docs(backlog): what the builder saw outside the change"
checked_in "$BLG" builder-filed
told=$(land --repo "$BLG" read builder-filed | field '[(i["item"], i["where"], i["title"]) for i in d["inputs"]["filed"]]')
land --repo "$BLG" read builder-filed --record "$(record builder-filed 1 "$a_read, $(outside "$A" "$B")")" >/dev/null
before_file=$(git -C "$tree" rev-parse HEAD)
filing=$(land --repo "$BLG" file builder-filed | field '([f["item"] for f in d["filed"]], d["same"], d["open"])')
land --repo "$BLG" checks builder-filed >/dev/null
green=$(land --repo "$BLG" propose builder-filed --title "fix: builder-filed" --notes "$NOTES" | field 'd["green"]')
text=$BLG/.lem/state/tasks/builder-filed/pr.md
if [ "$told" = "[('$own', 'src/json.py:parse', 'The parser fails on an empty input')]" ] \
  && [ "$filing" = "(['docs/backlog/empty-input-crashes-the-parser.md', 'docs/backlog/a-quoted-comma-splits-the-field.md'], [], [])" ] \
  && [ -e "$tree/docs/backlog/empty-input-crashes-the-parser.md" ] && [ -e "$tree/$own" ] && [ "$(git -C "$tree" rev-list --count "$before_file..HEAD")" = 1 ] && [ "$green" = True ] \
  && grep -qF "it saw 2 defects outside the change, filed as \`docs/backlog/empty-input-crashes-the-parser.md\`, \`docs/backlog/a-quoted-comma-splits-the-field.md\`" "$text"; then
  pass "the review is told of the branch's items, and a defect it lists at the place of an item the builder filed gets an item of its own, as a defect of another place does"
else
  fail "a defect the branch filed already: $told / $filing / $green / $(grep 'the review, round' "$text" 2>/dev/null)"
fi
# The merge agent reads each item the branch adds, whoever filed it, against the bar of rule 6 in the file the
# project's builders read, as spawn-builder picks it: Lem's by its place in the plugin, or the project's own
# lem-builder.md in the main checkout, where the task's session stands.
lems=$(land --repo "$BLG" merge-review builder-filed | field '(sorted((f["item"], f["title"]) for f in d["facts"]["filed"]), d["facts"]["bar"])')
mkdir -p "$BLG/.claude/agents" && printf '%s\n' '---' 'name: lem-builder' '---' > "$BLG/.claude/agents/lem-builder.md"
owns=$(land --repo "$BLG" merge-review builder-filed | field 'd["facts"]["bar"]')
rm "$BLG/.claude/agents/lem-builder.md"
if [ "$lems" = "([('docs/backlog/a-quoted-comma-splits-the-field.md', 'A quoted comma splits the field'), ('docs/backlog/empty-input-crashes-the-parser.md', 'Empty input crashes the parser'), ('$own', 'The parser fails on an empty input')], {'file': 'agents/lem-builder.md', 'of': 'lem'})" ] \
  && [ "$owns" = "{'file': '$(cd "$BLG" && pwd -P)/.claude/agents/lem-builder.md', 'of': 'project'}" ]; then
  pass "the merge agent's brief lists each item the branch adds to the backlog, the builder's and the review's, by its path and title, and names the file of the bar the project's builders read: Lem's in the plugin, or the project's own lem-builder.md"
else
  fail "the items and the bar in the merge brief: $lems / $owns"
fi
project --repo "$BLG" state builder-filed dropped "the test is over" >/dev/null

# The items `file` commits hold no code and no test, so they ask for no gate again: the request is
# proposed and lands on the gate's result. An item written by hand after the gate is a commit like
# any other, and asks for the gate. Last in this block: the landed item is on the base from here on.
blg_task by-hand
tree=$(project --repo "$BLG" worktree-dir by-hand)
checked_in "$BLG" by-hand
land --repo "$BLG" read by-hand --record "$(clean by-hand 1)" >/dev/null
echo '# found by hand' > "$tree/docs/backlog/found-by-hand.md" && git -C "$tree" add -A && git -C "$tree" commit -q -m "docs(backlog): found by hand"
hand=$(land --repo "$BLG" propose by-hand --title "fix: by-hand" --notes "$NOTES" 2>&1 || true)
project --repo "$BLG" state by-hand dropped "the test is over" >/dev/null
blg_task filed-only
tree=$(project --repo "$BLG" worktree-dir filed-only)
checked_in "$BLG" filed-only
gated=$(git -C "$tree" rev-parse HEAD)
land --repo "$BLG" read filed-only --record "$(record filed-only 1 "$a_read, $(outside "$A")")" >/dev/null
land --repo "$BLG" file filed-only >/dev/null
filed_tip=$(git -C "$tree" rev-parse HEAD)
carried=$(land --repo "$BLG" propose filed-only --title "fix: filed-only" --notes "$NOTES" 2>&1 || true)
merge_read "$BLG" filed-only >/dev/null 2>&1 || true
landed=$(land --repo "$BLG" merge filed-only --by merger 2>&1 || true)
if grep -qF "no green check is on record for this tip; \`lem land checks by-hand\` comes first" <<<"$hand" \
  && [ "$filed_tip" != "$gated" ] && [ "$(field '(d["green"], d["tip"])' <<<"$carried" 2>/dev/null)" = "(True, '$filed_tip')" ] \
  && [ "$(field 'd["merged"]' <<<"$landed" 2>/dev/null)" = "$filed_tip" ] && [ "$(status_in "$BLG" filed-only)" = landed ] \
  && [ "$(git -C "$BLG" show main:docs/backlog/empty-input-crashes-the-parser.md | sed -n 6p)" = "# Empty input crashes the parser" ] \
  && [ "$(grep -c '"event": "gate", "task": "filed-only"' "$BLG/.lem/state/events.jsonl")" = 1 ]; then
  pass "the items land.py file commits after the gate ask for no gate again: the request is proposed and lands with them on the gate's one run; an item written by hand after the gate asks for the gate"
else
  fail "the gate's result over the filed items: $hand / $carried / $landed"
fi

# A commit hook of the project that wants another message form refuses land.py's own commit of the items: the
# step says the hook's words and the fix, the items stay written, and after a builder's commit in the form the
# hook asks for, a second run finds each item by its defect.
task_in "$BLG" hook-form hook.txt three && read_in "$BLG" hook-form
tree=$(project --repo "$BLG" worktree-dir hook-form)
checked_in "$BLG" hook-form
H='{"where": "src/hook.py:check", "title": "A hook defect of its own", "what": "check with no subject returns True, on the base commit too.", "bar": "over"}'
land --repo "$BLG" read hook-form --record "$(record hook-form 1 "$a_read, $(outside "$H")")" >/dev/null
hooks=$(git -C "$BLG" rev-parse --path-format=absolute --git-path hooks)
mkdir -p "$hooks" && printf '%s\n' '#!/bin/sh' "grep -q '^ABC-[0-9]* ' \"\$1\" || { echo 'commit-msg: a subject starts with its ticket, as in ABC-12 fix' >&2; exit 1; }" > "$hooks/commit-msg" && chmod +x "$hooks/commit-msg"
refused=$(land --repo "$BLG" file hook-form 2>&1 || true)
code=$(status_of land --repo "$BLG" file hook-form)
staged=$(git -C "$tree" diff --cached --name-only)
git -C "$tree" commit -q -m "ABC-7 docs(backlog): what the review saw outside hook-form" -- docs/backlog/a-hook-defect-of-its-own.md
again=$(land --repo "$BLG" file hook-form 2>&1 | field '(d["filed"], [f["item"] for f in d["same"]])' 2>&1 || true)
rm "$hooks/commit-msg"
if grep -qF "the commit of the backlog items of review round 1 was refused, most likely by a commit hook of the project: commit-msg: a subject starts with its ticket, as in ABC-12 fix." <<<"$refused" \
  && grep -qF "a builder commits them with a message in the form the hook asks for (\`git -C $tree commit -m MESSAGE -- docs/backlog/a-hook-defect-of-its-own.md\`), never with --no-verify, then \`lem land file hook-form\` runs again" <<<"$refused" \
  && [ "$code" = 1 ] && [ "$staged" = docs/backlog/a-hook-defect-of-its-own.md ] && ! grep -q Traceback <<<"$refused" \
  && [ "$again" = "([], ['docs/backlog/a-hook-defect-of-its-own.md'])" ] && [ -z "$(git -C "$tree" status --porcelain)" ]; then
  pass "a commit hook that refuses land.py's commit of the backlog items is named with its own words and the fix; the items stay staged, and after a commit in the hook's form the next run finds each by its defect and records it"
else
  fail "a hook that refuses the items' commit: $refused / $code / $staged / $again"
fi
project --repo "$BLG" state hook-form dropped "the test is over" >/dev/null

# A review judges each defect outside the change by the bar of rule 6, and only what is over the bar becomes an item:
# one under the bar is a line of the pull request, one that an open item of the base holds names that item and files
# nothing, one whose open item the branch removed is filed, and of two cheap defects of one place and title that
# nobody's fix takes up, the one a fix line names by its number leaves the list and the other stays. No cheap defect
# runs the checks again. Last in this block: it reads the item that by-hand's landing put on the base.
O='{"where": "src/a.py:f", "title": "F crashes on None", "what": "f(None) raises TypeError, on the base commit too.", "bar": "over"}'
U='{"where": "tests/unit/test_board_model.py", "title": "two test classes come after the main guard", "what": "the two classes stand after the main guard of the file, on the base commit too.", "bar": "under", "why": "only a reader of the code meets it"}'
P='{"where": "src/json.py:parse", "title": "Empty input crashes the parser", "what": "parse with an empty string raises IndexError, on the base commit too.", "bar": "over", "open": "docs/backlog/empty-input-crashes-the-parser.md"}'
Q='{"where": "src/q.py:g", "title": "G loses the last row", "what": "g of three rows returns two, on the base commit too.", "bar": "over", "open": "docs/backlog/existing.md"}'
C1='{"where": "src/c.py:h", "title": "A comment says the opposite", "what": "the comment of h says it returns None, and h returns 0.", "bar": "cheap", "why": "a comment, no behavior"}'
C2='{"where": "src/c.py:h", "title": "A comment says the opposite", "what": "the comment of h says it raises, and h returns 0.", "bar": "cheap", "why": "a comment, no behavior"}'
NOWHERE='{"where": "src/q.py:g", "title": "G loses the last row", "what": "g of three rows returns two, on the base commit too.", "bar": "over", "open": "docs/backlog/nothing-of-the-base.md"}'
task_in "$BLG" judged judged.txt four && read_in "$BLG" judged
tree=$(project --repo "$BLG" worktree-dir judged)
git -C "$tree" rm -q docs/backlog/existing.md && git -C "$tree" commit -q -m "docs(backlog): the item from before is done"
checked_in "$BLG" judged
told=$(land --repo "$BLG" read judged | field 'sorted((i["item"], i["where"], i["title"]) for i in d["inputs"]["backlog"])')
nowhere=$(land --repo "$BLG" read judged --record "$(record judged 1 "$a_read, $(outside "$NOWHERE")")" 2>&1 || true)
judged=$(land --repo "$BLG" read judged --record "$(record judged 1 "$a_read, $(outside "$O" "$U" "$P" "$Q" "$C1" "$C2")")" | field '(d["next"], [f["number"] for f in d["to_file"]], [c["number"] for c in d["cheap"]])')
filing=$(land --repo "$BLG" file judged | field '([(f["number"], f["item"]) for f in d["filed"]], [(f["number"], f["item"]) for f in d["open"]])')
numbers=$(land --repo "$BLG" read judged | field '[f["number"] for f in d["reads"][0]["outside"]]')
printf '%s\n' '## Decisions' '' 'none' '' '## Left open' '' 'none' '' '## Worth a look' '' 'none' '' '## Filed in the backlog' '' 'none' '' \
  '## Fixed on the way' '' '- src/c.py (abc1234): r1.5, the comment of h said it returns None' '' '## Not done' '' 'none' > "$WORK/judged-notes.md"
green=$(land --repo "$BLG" propose judged --title "fix: judged" --notes "$WORK/judged-notes.md" | field 'd["green"]')
text=$BLG/.lem/state/tasks/judged/pr.md
seen=$(sed -n '/^## Seen, not filed$/,/^## Not done$/p' "$text")
if [ "$told" = "[('docs/backlog/empty-input-crashes-the-parser.md', 'src/json.py:parse', 'Empty input crashes the parser'), ('docs/backlog/existing.md', None, 'an item from before')]" ] \
  && grep -qF "\`open\` of the defect r1.1 outside the change (\"G loses the last row\") is 'docs/backlog/nothing-of-the-base.md', which is no file of the backlog folder docs/backlog at the base" <<<"$nowhere" \
  && [ "$judged" = "('none', ['r1.1', 'r1.4'], ['r1.5', 'r1.6'])" ] \
  && [ "$filing" = "([('r1.1', 'docs/backlog/f-crashes-on-none.md'), ('r1.4', 'docs/backlog/g-loses-the-last-row.md')], [('r1.3', 'docs/backlog/empty-input-crashes-the-parser.md')])" ] \
  && [ "$numbers" = "['r1.1', 'r1.2', 'r1.3', 'r1.4', 'r1.5', 'r1.6']" ] && [ "$green" = True ] \
  && [ "$(git -C "$tree" ls-files docs/backlog | tr '\n' ' ')" = "docs/backlog/empty-input-crashes-the-parser.md docs/backlog/f-crashes-on-none.md docs/backlog/g-loses-the-last-row.md " ] \
  && [ "$(grep '^## ' "$text" | tail -5 | tr '\n' '|')" = "## Worth a look|## Filed in the backlog|## Fixed on the way|## Seen, not filed|## Not done|" ] \
  && grep -qxF -- "- \`docs/backlog/f-crashes-on-none.md\`: F crashes on None" "$text" && grep -qxF -- "- \`docs/backlog/g-loses-the-last-row.md\`: G loses the last row" "$text" \
  && grep -qxF -- "- \`tests/unit/test_board_model.py\`: two test classes come after the main guard; only a reader of the code meets it" <<<"$seen" \
  && grep -qxF -- "- \`src/json.py:parse\`: Empty input crashes the parser; an open item holds it, \`docs/backlog/empty-input-crashes-the-parser.md\`" <<<"$seen" \
  && [ "$(grep -cxF -- "- \`src/c.py:h\`: A comment says the opposite; a comment, no behavior" <<<"$seen")" = 1 ] && [ "$(grep -c '^- ' <<<"$seen")" = 3 ] \
  && grep -qF "it saw 6 defects outside the change, filed as \`docs/backlog/f-crashes-on-none.md\`, \`docs/backlog/g-loses-the-last-row.md\`; 1 fixed on the way; 3 seen, not filed" "$text" \
  && [ "$(grep -c '"event": "gate", "task": "judged"' "$BLG/.lem/state/events.jsonl")" = 1 ] && [ -z "$(git -C "$tree" status --porcelain)" ]; then
  pass "a review judges each defect outside the change by the bar: only one over it with no open item in the tip is filed, and the pull request opens with each other one on a line under Seen, not filed, a cheap one that a fix line names by its number left out, and no new run of the checks"
else
  fail "the defects a review judged: $told / $nowhere / $judged / $filing / $numbers / $green / $(git -C "$tree" ls-files docs/backlog | tr '\n' ' ') / $(cat "$text" 2>/dev/null)"
fi
project --repo "$BLG" state judged dropped "the test is over" >/dev/null

# A task started from a backlog item, whose ask is the item's path alone as the board's "Start a task" writes it,
# removes that item on its branch: propose stops while the tip holds it and names it, and after a builder's git rm
# the checks run again, the review still covers the change, and the pull request opens. Which ask names an item,
# and what a review covers, is tests/unit/test_backlog.py's.
backlog_repo backlog-own
OWN=$WORK/backlog-own
task_in "$OWN" from-item app.txt two && read_in "$OWN" from-item
printf '%s\n' docs/backlog/existing.md > "$OWN/.lem/state/tasks/from-item/ask.txt"
tree=$(project --repo "$OWN" worktree-dir from-item)
polished=$(land --repo "$OWN" start from-item >/dev/null && land --repo "$OWN" base from-item >/dev/null && land --repo "$OWN" polish from-item | field 'd["item"]')
land --repo "$OWN" polish from-item --done >/dev/null && land --repo "$OWN" checks from-item >/dev/null
land --repo "$OWN" read from-item --record "$(clean from-item 1)" >/dev/null
stopped=$(land --repo "$OWN" propose from-item --title "fix: from-item" --notes "$NOTES" 2>&1 || true)
git -C "$tree" rm -q -- docs/backlog/existing.md && git -C "$tree" commit -q -m "docs(backlog): the task's item is done" -- docs/backlog/existing.md
unchecked=$(land --repo "$OWN" propose from-item --title "fix: from-item" --notes "$NOTES" 2>&1 || true)
land --repo "$OWN" checks from-item >/dev/null
due=$(land --repo "$OWN" read from-item | field 'd["due"]')
opened=$(land --repo "$OWN" propose from-item --title "fix: from-item" --notes "$NOTES" | field '(d["green"], d["tip"])')
if [ "$polished" = docs/backlog/existing.md ] \
  && grep -qF "from-item was started from the backlog item docs/backlog/existing.md (its ask is that path), and the branch still holds it" <<<"$stopped" \
  && grep -qF "\`git -C $tree rm -q -- docs/backlog/existing.md\`" <<<"$stopped" && ! grep -q Traceback <<<"$stopped" \
  && grep -qF "no green check is on record for this tip; \`lem land checks from-item\` comes first" <<<"$unchecked" \
  && [ "$due" = none ] && [ "$opened" = "(True, '$(git -C "$tree" rev-parse HEAD)')" ] \
  && [ -z "$(git -C "$tree" ls-files docs/backlog)" ] && [ "$(grep -c '"event": "gate", "task": "from-item"' "$OWN/.lem/state/events.jsonl")" = 2 ]; then
  pass "a task started from a backlog item stops at propose while its branch holds the item, and after a builder's git rm and a new run of the checks the review still covers it and the pull request opens"
else
  fail "the task's own item: $polished / $stopped / $unchecked / $due / $opened / $(git -C "$tree" ls-files docs/backlog | tr '\n' ' ')"
fi
project --repo "$OWN" state from-item dropped "the test is over" >/dev/null

finish
