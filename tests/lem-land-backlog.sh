#!/usr/bin/env bash
# The landing's filing of what a review saw outside the change, as items of the backlog.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

# What a review saw outside the change is filed after it, as new items in the backlog folder: that asks
# for no other review. Any other file does, an item that was on the base included.
# backlog_repo NAME: a repository with one item in its backlog folder, docs/backlog, on the base
backlog_repo() {
  local repo=$WORK/$1
  git init -q -b main "$repo" && ident "$repo" && project --repo "$repo" init --base main >/dev/null
  printf '%s\n' '[branch]' 'base = "main"' 'history = "keep"' 'land = "agent"' '[checks]' 'commands = ["true"]' > "$repo/.lem/project.toml"
  mkdir -p "$repo/docs/backlog" && echo '# an item from before' > "$repo/docs/backlog/existing.md" && echo one > "$repo/app.txt"
  git -C "$repo" add -A && git -C "$repo" commit -q -m "chore: start"
}
# blg_task SLUG: a full change of the backlog repository, with the lead's read of its criteria
blg_task() { task_in "$BLG" "$1" app.txt two && read_in "$BLG" "$1"; }
# checked_in REPO SLUG: the task takes the landing line, its base, its polish pass and its gate
checked_in() { land --repo "$1" start "$2" >/dev/null && land --repo "$1" base "$2" >/dev/null && polish_in "$1" "$2" && land --repo "$1" checks "$2" >/dev/null; }
# reviewed_then REPO SLUG CHANGE: a task whose change one read reviewed, then CHANGE run in its
# worktree and committed, and the checks again; prints what is due
reviewed_then() {
  local tree
  task_in "$1" "$2" app.txt two
  tree=$(project --repo "$1" worktree-dir "$2")
  checked_in "$1" "$2"
  land --repo "$1" read "$2" --record "$(clean 1)" >/dev/null
  (cd "$tree" && sh -c "$3")
  git -C "$tree" add -A && git -C "$tree" commit -q -m "docs(backlog): after the review" && land --repo "$1" checks "$2" >/dev/null
  land --repo "$1" read "$2" | field 'd["due"]'
  project --repo "$1" state "$2" dropped "the test is over" >/dev/null
}
backlog_repo backlog-land
BLG=$WORK/backlog-land
added=$(reviewed_then "$BLG" new-item 'echo "# a defect from before" > docs/backlog/new.md')
edited=$(reviewed_then "$BLG" edited-item 'echo more >> docs/backlog/existing.md')
removed=$(reviewed_then "$BLG" removed-item 'rm docs/backlog/existing.md')
if [ "$added" = none ] && [ "$edited" = review ] && [ "$removed" = review ]; then
  pass "a new item in the backlog folder after a review keeps the review, and an edit or a deletion of an item that was on the base asks for another"
else
  fail "backlog items after a review: $added / $edited / $removed"
fi
# Two rounds that saw two different defects give two items, each filed by the script in a commit of
# its own; a second run files nothing; propose waits for each one, and the pull request names them.
A='{"where": "src/json.py:parse", "title": "Empty input crashes the parser", "what": "parse with an empty string raises IndexError, on the base commit too."}'
B='{"where": "src/csv.py:read", "title": "A quoted comma splits the field", "what": "read of a line with a comma inside quotes gives three fields, on the base commit too."}'
# the start of a record, and outside DEFECT...: its end, with the defects (bash 3.2 splits a quote escaped inside "$(...)")
a_read='{"kind": "read", "answered": ["codex"]'
read_must_fix='{"kind": "read", "answered": ["codex"], "must_fix": 1'
a_round='{"kind": "round", "ran": [{"name": "correctness", "why": "a file of the app changes"}], "answered": ["codex"]'
outside() { local IFS=,; printf '"outside": [%s]}' "$*"; }
blg_task two-defects
tree=$(project --repo "$BLG" worktree-dir two-defects)
checked_in "$BLG" two-defects
# the day before the review and after its filing: an item filed at midnight carries one of the two
day_from=$(date +%F)
first=$(land --repo "$BLG" read two-defects --record "$(record 1 "$read_must_fix, $(outside "$A")")" | field '(d["next"], [(f["round"], f["title"]) for f in d["to_file"]])')
filed_a=$(land --repo "$BLG" file two-defects | field '([(f["round"], f["item"]) for f in d["filed"]], d["same"])')
day_to=$(date +%F)
echo fixed > "$tree/notes.txt" && git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: the must-fix" && land --repo "$BLG" checks two-defects >/dev/null
second=$(land --repo "$BLG" read two-defects --record "$(record 2 "$a_round, $(outside "$B")")" | field '(d["next"], [(f["round"], f["title"]) for f in d["to_file"]])')
unfiled=$(land --repo "$BLG" propose two-defects --title "fix: two-defects" --notes "$NOTES" 2>&1 >/dev/null || true)
filed_b=$(land --repo "$BLG" file two-defects | field '[(f["round"], f["item"]) for f in d["filed"]]')
commit_b=$(git -C "$tree" show --name-only --format=%s HEAD | tr '\n' '|')
tip_b=$(git -C "$tree" rev-parse HEAD)
rerun=$(land --repo "$BLG" file two-defects | field '(d["filed"], d["same"])')
[ "$(git -C "$tree" rev-parse HEAD)" = "$tip_b" ] || rerun="$rerun, and a commit"
land --repo "$BLG" checks two-defects >/dev/null
after=$(land --repo "$BLG" read two-defects | field '(d["due"], d["to_file"])')
green=$(land --repo "$BLG" propose two-defects --title "fix: two-defects" --notes "$NOTES" | field 'd["green"]')
text=$BLG/.lem/state/tasks/two-defects/pr.md
item="$tree/docs/backlog/empty-input-crashes-the-parser.md"
logged=$("$PY" -c 'import json, sys; print([[i["item"] for i in e["items"]] for e in map(json.loads, open(sys.argv[1])) if e["event"] == "review.filed" and e["task"] == "two-defects"])' "$BLG/.lem/state/events.jsonl")
if [ "$first" = "('review', [(1, 'Empty input crashes the parser')])" ] && [ "$filed_a" = "([(1, 'docs/backlog/empty-input-crashes-the-parser.md')], [])" ] \
  && [ "$second" = "('none', [(2, 'A quoted comma splits the field')])" ] && grep -q "A quoted comma splits the field" <<<"$unfiled" && grep -q "lem land file two-defects" <<<"$unfiled" \
  && [ "$filed_b" = "[(2, 'docs/backlog/a-quoted-comma-splits-the-field.md')]" ] \
  && [ "$commit_b" = "docs(backlog): what review round 2 saw outside two-defects||docs/backlog/a-quoted-comma-splits-the-field.md|" ] \
  && [ "$rerun" = "([], [])" ] && [ "$after" = "('none', [])" ] && [ "$green" = True ] \
  && sed -n 1,5p "$item" | tr '\n' '|' | grep -qxF -e "---|worth: later|where: src/json.py:parse|added: $day_from|---|" -e "---|worth: later|where: src/json.py:parse|added: $day_to|---|" \
  && [ "$(sed -n 6p "$item")" = "# Empty input crashes the parser" ] \
  && grep -qx "parse with an empty string raises IndexError, on the base commit too." "$item" \
  && grep -qxF -e "Seen outside the change by review round 1 of task two-defects ($day_from); the base commit has it." -e "Seen outside the change by review round 1 of task two-defects ($day_to); the base commit has it." "$item" \
  && grep -q '^- the review, round 1 (one read; answered: codex): must-fix, 1 must-fix, 0 should, 0 nit; it saw 1 defect outside the change, filed as .docs/backlog/empty-input-crashes-the-parser.md.$' "$text" \
  && grep -q '^- the review, round 2 .*: clean, 0 must-fix, 0 should, 0 nit; it saw 1 defect outside the change, filed as .docs/backlog/a-quoted-comma-splits-the-field.md.$' "$text" \
  && [ "$logged" = "[['docs/backlog/empty-input-crashes-the-parser.md'], ['docs/backlog/a-quoted-comma-splits-the-field.md']]" ]; then
  pass "two rounds that saw two different defects outside the change give two items in the backlog's format, each committed alone by land.py file; a second run files nothing; propose waits for each, and the pull request names each item"
else
  fail "the filing of two defects: $first / $filed_a / $second / $unfiled / $filed_b / $commit_b / $rerun / $after / $green / $logged / $(cat "$item" 2>/dev/null) / $(grep 'the review, round' "$text" 2>/dev/null)"
fi
project --repo "$BLG" state two-defects dropped "the test is over" >/dev/null

# An item that was on the branch before the review is no proof that a defect was filed; an item that
# was filed and then removed stops propose until it is back, and `file --again` puts it back.
blg_task item-goes
tree=$(project --repo "$BLG" worktree-dir item-goes)
echo '# a slow report' > "$tree/docs/backlog/first.md" && git -C "$tree" add -A && git -C "$tree" commit -q -m "docs(backlog): a slow report"
checked_in "$BLG" item-goes
land --repo "$BLG" read item-goes --record "$(record 1 "$a_read, $(outside "$A")")" >/dev/null
before=$(land --repo "$BLG" propose item-goes --title "fix: item-goes" --notes "$NOTES" 2>&1 >/dev/null || true)
land --repo "$BLG" file item-goes >/dev/null
rm "$tree/docs/backlog/empty-input-crashes-the-parser.md" && git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: an item less" && land --repo "$BLG" checks item-goes >/dev/null
gone=$(land --repo "$BLG" propose item-goes --title "fix: item-goes" --notes "$NOTES" 2>&1 >/dev/null || true)
back=$(land --repo "$BLG" file item-goes --again | field '[f["item"] for f in d["filed"]]')
land --repo "$BLG" checks item-goes >/dev/null
green=$(land --repo "$BLG" propose item-goes --title "fix: item-goes" --notes "$NOTES" | field 'd["green"]')
if grep -q "Empty input crashes the parser" <<<"$before" && grep -q "lem land file item-goes" <<<"$before" \
  && grep -q "docs/backlog/empty-input-crashes-the-parser.md" <<<"$gone" && grep -q "was removed after it was filed" <<<"$gone" && grep -q -- "--again" <<<"$gone" && grep -q "worth: no" <<<"$gone" \
  && [ "$back" = "['docs/backlog/empty-input-crashes-the-parser.md']" ] && [ "$green" = True ]; then
  pass "an item that was on the branch before the review proves nothing; an item that was filed and then removed stops propose with its path and the two ways on, and file --again puts it back"
else
  fail "an item that goes: $before / $gone / $back / $green"
fi
project --repo "$BLG" state item-goes dropped "the test is over" >/dev/null

# One defect seen word for word by two rounds is one item, also when its file name needed the suffix
# of its place; two defects of one place and one title, with two different runs, are two items. And a
# worktree with a change nobody committed is refused.
D='{"where": "src/json.py:parse", "title": "An item from before", "what": "parse of a document with no root returns None, on the base commit too."}'
E='{"where": "src/json.py:parse", "title": "An item from before", "what": "parse of a document of one number returns a string, on the base commit too."}'
blg_task same-defect
tree=$(project --repo "$BLG" worktree-dir same-defect)
echo '# An item from before' > "$tree/docs/backlog/an-item-from-before.md" && git -C "$tree" add -A && git -C "$tree" commit -q -m "docs(backlog): an item with no place"
checked_in "$BLG" same-defect
land --repo "$BLG" read same-defect --record "$(record 1 "$read_must_fix, $(outside "$D")")" >/dev/null
once=$(land --repo "$BLG" file same-defect | field '[f["item"] for f in d["filed"]]')
echo fixed > "$tree/notes.txt" && git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: the must-fix" && land --repo "$BLG" checks same-defect >/dev/null
land --repo "$BLG" read same-defect --record "$(record 2 "$a_round, $(outside "$D" "$E")")" >/dev/null
echo stray > "$tree/stray.txt"
dirty=$(land --repo "$BLG" file same-defect 2>&1 >/dev/null || true)
rm "$tree/stray.txt"
twice=$(land --repo "$BLG" file same-defect | field '([f["item"] for f in d["filed"]], [f["item"] for f in d["same"]])')
if [ "$once" = "['docs/backlog/an-item-from-before-json-parse.md']" ] \
  && [ "$twice" = "(['docs/backlog/an-item-from-before-json-parse-2.md'], ['docs/backlog/an-item-from-before-json-parse.md'])" ] \
  && [ "$(cat "$tree/docs/backlog/an-item-from-before.md")" = "# An item from before" ] && grep -q "commit them or remove them" <<<"$dirty"; then
  pass "a defect that two rounds saw word for word is one item, also under the suffix of its place, and two defects of one place and title with two runs are two; file refuses a worktree with a change nobody committed"
else
  fail "the same defect twice: $once / $twice / $dirty"
fi
project --repo "$BLG" state same-defect dropped "the test is over" >/dev/null

# The owner's "no" is `worth: no` and his reason in the item: the same defect seen again by the next
# round is still that item, and nothing is filed over his word.
blg_task owner-says-no
tree=$(project --repo "$BLG" worktree-dir owner-says-no)
checked_in "$BLG" owner-says-no
land --repo "$BLG" read owner-says-no --record "$(record 1 "$read_must_fix, $(outside "$A")")" >/dev/null
land --repo "$BLG" file owner-says-no >/dev/null
item=$tree/docs/backlog/empty-input-crashes-the-parser.md
"$PY" -c 'import sys; p = sys.argv[1]; t = open(p).read().replace("worth: later", "worth: no").replace("\n\nSeen outside", "\n\nThe owner: an empty input never reaches parse, the reader refuses it first.\n\nSeen outside"); open(p, "w").write(t)' "$item"
echo fixed > "$tree/notes.txt" && git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: the must-fix, and the owner's no" && land --repo "$BLG" checks owner-says-no >/dev/null
land --repo "$BLG" read owner-says-no --record "$(record 2 "$a_round, $(outside "$A")")" >/dev/null
again=$(land --repo "$BLG" file owner-says-no | field '([f["item"] for f in d["filed"]], [f["item"] for f in d["same"]])')
if [ "$again" = "([], ['docs/backlog/empty-input-crashes-the-parser.md'])" ] && grep -qx "worth: no" "$item" && grep -q "^The owner: " "$item" \
  && [ "$(git -C "$tree" ls-files docs/backlog | tr '\n' ' ')" = "docs/backlog/empty-input-crashes-the-parser.md docs/backlog/existing.md " ] && [ -z "$(git -C "$tree" status --porcelain)" ]; then
  pass "an item the owner set to worth: no, with his reason in it, is still the item of the same defect when the next round sees it again: nothing is filed over his no"
else
  fail "the owner's no and the same defect again: $again / $(git -C "$tree" ls-files docs/backlog) / $(cat "$item")"
fi
project --repo "$BLG" state owner-says-no dropped "the test is over" >/dev/null

# A defect whose place an item of the branch already names, one its builder or the polish pass filed before the
# review, is that item: the review is told of the items, `file` writes nothing for it and says what matched, and the
# pull request names the item once. A defect of another place gets an item of its own.
blg_task builder-filed
tree=$(project --repo "$BLG" worktree-dir builder-filed)
own=docs/backlog/the-parser-fails-on-an-empty-input.md
printf '%s\n' '---' 'worth: later' 'where: src/json.py:parse' 'added: 2026-11-17' '---' '# The parser fails on an empty input' '' 'parse("") raises IndexError, on the base commit too.' > "$tree/$own"
git -C "$tree" add -A && git -C "$tree" commit -q -m "docs(backlog): what the builder saw outside the change"
checked_in "$BLG" builder-filed
told=$(land --repo "$BLG" read builder-filed | field '[(i["item"], i["where"], i["title"]) for i in d["inputs"]["filed"]]')
land --repo "$BLG" read builder-filed --record "$(record 1 "$a_read, $(outside "$A" "$B")")" >/dev/null
before_file=$(git -C "$tree" rev-parse HEAD)
filing=$(land --repo "$BLG" file builder-filed | field '([f["item"] for f in d["filed"]], [(n["item"], n["where"]) for n in d["named"]])')
land --repo "$BLG" checks builder-filed >/dev/null
green=$(land --repo "$BLG" propose builder-filed --title "fix: builder-filed" --notes "$NOTES" | field 'd["green"]')
text=$BLG/.lem/state/tasks/builder-filed/pr.md
if [ "$told" = "[('$own', 'src/json.py:parse', 'The parser fails on an empty input')]" ] \
  && [ "$filing" = "(['docs/backlog/a-quoted-comma-splits-the-field.md'], [('$own', 'src/json.py:parse')])" ] \
  && [ ! -e "$tree/docs/backlog/empty-input-crashes-the-parser.md" ] && [ "$(git -C "$tree" rev-list --count "$before_file..HEAD")" = 1 ] && [ "$green" = True ] \
  && grep -qF "it saw 2 defects outside the change, filed as \`$own\`, \`docs/backlog/a-quoted-comma-splits-the-field.md\`" "$text"; then
  pass "a defect whose place an item of the branch names is that item: the review is told of the branch's items, file writes nothing for it and names the match, and a defect of another place gets its own item"
else
  fail "a defect the branch filed already: $told / $filing / $green / $(grep 'the review, round' "$text" 2>/dev/null)"
fi
project --repo "$BLG" state builder-filed dropped "the test is over" >/dev/null

# The items `file` commits hold no code and no test, so they ask for no gate again: the request is
# proposed and lands on the gate's result. An item written by hand after the gate is a commit like
# any other, and asks for the gate. Last in this block: the landed item is on the base from here on.
blg_task by-hand
tree=$(project --repo "$BLG" worktree-dir by-hand)
checked_in "$BLG" by-hand
land --repo "$BLG" read by-hand --record "$(clean 1)" >/dev/null
echo '# found by hand' > "$tree/docs/backlog/found-by-hand.md" && git -C "$tree" add -A && git -C "$tree" commit -q -m "docs(backlog): found by hand"
hand=$(land --repo "$BLG" propose by-hand --title "fix: by-hand" --notes "$NOTES" 2>&1 || true)
project --repo "$BLG" state by-hand dropped "the test is over" >/dev/null
blg_task filed-only
tree=$(project --repo "$BLG" worktree-dir filed-only)
checked_in "$BLG" filed-only
gated=$(git -C "$tree" rev-parse HEAD)
land --repo "$BLG" read filed-only --record "$(record 1 "$a_read, $(outside "$A")")" >/dev/null
land --repo "$BLG" file filed-only >/dev/null
filed_tip=$(git -C "$tree" rev-parse HEAD)
carried=$(land --repo "$BLG" propose filed-only --title "fix: filed-only" --notes "$NOTES" 2>&1 || true)
landed=$(land --repo "$BLG" land filed-only --by agent 2>&1 || true)
if grep -qF "no green check is on record for this tip; \`lem land checks by-hand\` comes first" <<<"$hand" \
  && [ "$filed_tip" != "$gated" ] && [ "$(field '(d["green"], d["tip"])' <<<"$carried" 2>/dev/null)" = "(True, '$filed_tip')" ] \
  && [ "$(field 'd["tip"]' <<<"$landed" 2>/dev/null)" = "$filed_tip" ] && [ "$(status_in "$BLG" filed-only)" = landed ] \
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
H='{"where": "src/hook.py:check", "title": "A hook defect of its own", "what": "check with no subject returns True, on the base commit too."}'
land --repo "$BLG" read hook-form --record "$(record 1 "$a_read, $(outside "$H")")" >/dev/null
hooks=$(git -C "$BLG" rev-parse --path-format=absolute --git-path hooks)
mkdir -p "$hooks" && printf '%s\n' '#!/bin/sh' "grep -q '^ABC-[0-9]* ' \"\$1\" || { echo 'commit-msg: a subject starts with its ticket, as in ABC-12 fix' >&2; exit 1; }" > "$hooks/commit-msg" && chmod +x "$hooks/commit-msg"
refused=$(land --repo "$BLG" file hook-form 2>&1 || true)
code=$(status_of land --repo "$BLG" file hook-form)
staged=$(git -C "$tree" diff --cached --name-only)
git -C "$tree" commit -q -m "ABC-7 docs(backlog): what the review saw outside hook-form" -- docs/backlog/a-hook-defect-of-its-own.md
again=$(land --repo "$BLG" file hook-form 2>&1 | field '(d["filed"], [f["item"] for f in d["same"] + d["named"]])' 2>&1 || true)
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

finish
