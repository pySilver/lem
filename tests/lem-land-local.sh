#!/usr/bin/env bash
# The landing, part one: decisions, criteria and the personas' read in the pull request's text, on an
# origin that the stand-in for `gh` answers for (lib.sh). tests/lem-land-review.sh is part two, on a
# repository of its own.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

LOCAL=$WORK/local
git init -q -b main "$LOCAL" && ident "$LOCAL"
project --repo "$LOCAL" init --base main >/dev/null
printf '%s\n' '[branch]' 'base = "main"' 'history = "keep"' 'land = "agent"' '[checks]' 'commands = ["true"]' '[flow]' 'topics = ["a customer is charged the wrong price"]' > "$LOCAL/.lem/settings.toml"
mkdir -p "$LOCAL/tests" "$LOCAL/docs" && printf '%s\n' 'def test_base():' '    assert 1 + 1 == 2' '    assert 2 + 2 == 4' > "$LOCAL/tests/test_base.py" && echo guide > "$LOCAL/docs/guide.md"
printf '%s\n' 'import plugin # noqa: F401' 'import other  # noqa: E402' > "$LOCAL/plug.py"
# app_py FIRST SECOND: two functions alike in every line but their names, each longer than the
# three lines of context a diff shows, so the same edit in either gives the same lines of a diff
app_py() {
  printf '%s\n' 'def first():' '    a = 1' '    b = 2' '    c = 3' "    return \"$1\"" '    # the end' '' '' \
    'def second():' '    a = 1' '    b = 2' '    c = 3' "    return \"$2\"" '    # the end' '' '' 'def third():' '    return 3'
}
app_py old old > "$LOCAL/app.py"
printf '%s\n' 'pub fn one() -> i32 { 1 }' '#[cfg(test)]' 'mod tests {' '    #[test]' '    fn it_is_one() { assert_eq!(super::one(), 1); }' '}' > "$LOCAL/lib.rs"
git -C "$LOCAL" add -A && git -C "$LOCAL" commit -q -m "chore: start" && on_github "$LOCAL"
local_land() { land --repo "$LOCAL" "$@"; }
task_in "$LOCAL" local-change x.txt x
# A criterion that changed during the build is written down by the build, as a record of its own with its text before and after; the text shows it, and a person merges.
printf '%s\n' '## Acceptance criteria' '' 'Size: full, because the ticket names the word and the file.' '' '1. The file holds the word y.' > "$WORK/local-approved.md"
"$PY" -B "$CRITERIA" --repo "$LOCAL" approve local-change --file "$WORK/local-approved.md" >/dev/null 2>&1 || true
"$PY" -B "$DECISIONS" --repo "$LOCAL" criterion local-change --changed 1 --was "The file holds the word y." --now "The file holds the word the owner asked for." \
  --why "y is taken by another file." --by personas --said "Both personas picked x." >/dev/null 2>&1 || true
read_in "$LOCAL" local-change
local_land start local-change >/dev/null && local_land base local-change >/dev/null && polish_in "$LOCAL" local-change && local_land checks local-change >/dev/null && local_land read local-change --record "$(clean local-change 1)" >/dev/null
local_land propose local-change --title "fix: x" --notes "$NOTES" >/dev/null
err=$(local_land merge local-change --by merger 2>&1 || true)
# an agent's merge of it would leave nothing for the owner's: that is this check's FAIL, not a stop of the block
out=$(local_land merge local-change --by owner) || true
if grep -q "the request is not green (criterion 1 changed during the build: y is taken by another file.), so the owner merges it" <<<"$err" \
  && [ "$(sed -n 1p "$LOCAL/.lem/state/tasks/local-change/pr.md")" = '**Not green.**' ] && [ "$(sed -n 3p "$LOCAL/.lem/state/tasks/local-change/pr.md")" = '- criterion 1 changed during the build: y is taken by another file.' ] \
  && grep -qxF -- '- criterion 1: was "The file holds the word y.", now "The file holds the word the owner asked for.". y is taken by another file. By the personas: Both personas picked x.' "$LOCAL/.lem/state/tasks/local-change/pr.md" \
  && [ ! -e "$LOCAL/.lem/state/tasks/local-change/criterion-changes.jsonl" ] \
  && [ "$(field 'd["pull_request"]["number"]' <<<"$out")" = 1 ] && [ -f "$LOCAL/x.txt" ] && [ "$(git -C "$LOCAL" log -1 --format=%s main)" = "fix: local-change" ] && [ "$(status_in "$LOCAL" local-change)" = landed ]; then
  pass "a request with a changed criterion is not green: its text says so first and shows the change, with what the criterion was and is, and the owner merges it whatever the settings say, through its pull request, and the main checkout follows"
else
  fail "local landing: $err / $out"
fi
local_land clean local-change >/dev/null
# The decisions of one task through the real commands: a breaker that waits holds the proposal, also under a `ready`
# written over it; the owner's help settles it and is no cause of not green; a pick of the dialectic and a decision of
# one expert alone (no Codex on the machine) make the request not green, and the merge agent does not merge it. What
# each line of the text says, for each kind of record, is a case of tests/unit/test_land_text.py; here the writers and
# the real pr.md meet.
task_in "$LOCAL" waited-change w.txt w
read_in "$LOCAL" waited-change
wdec() { "$PY" -B "$DECISIONS" --repo "$LOCAL" "$@"; }
wdec log waited-change --what "The name of the file" --chose w.txt --why "The other files have one letter." --by lead >/dev/null
breaker_doc "$LOCAL/.lem/state/tasks/waited-change" && wdec breaker waited-change --cause irreversible --irreversible person >/dev/null
project --repo "$LOCAL" state waited-change ready "the report is written" >/dev/null
local_land start waited-change >/dev/null && local_land base waited-change >/dev/null && polish_in "$LOCAL" waited-change && local_land checks waited-change >/dev/null && local_land read waited-change --record "$(clean waited-change 1)" >/dev/null
waiting=$(local_land propose waited-change --title "fix: w" --notes "$NOTES" 2>&1 || true)
wdec log waited-change --by owner --breaker 2 --what "Tell the merchants" --chose "send nothing" --why "Nothing they see changes." --words "no email, they read the export" >/dev/null
wdec log waited-change "${CASE[@]}" --what "Where the word goes" --chose "the first line" --by dialectic --option "the first line" --option "the last line" \
  --level "personas=1 for the first line, 1 for the last line" --level "dialectic=no break" --why "A reader sees it at once." >/dev/null
alone_log=$(env PATH="$NOCODEX" "$PY" -B "$DECISIONS" --repo "$LOCAL" log waited-change "${CASE[@]}" --what "The word's line ending" --chose "a line break" --by experts \
  --why "Fable: every file ends so." --option "a line break" --option "no line break" | field 'd["advisers"]' 2>&1 || true)
local_land propose waited-change --title "fix: w" --notes "$NOTES" >/dev/null
text=$LOCAL/.lem/state/tasks/waited-change/pr.md
agent=$(local_land merge waited-change --by merger 2>&1 || true)
if grep -qF "breaker 2 of waited-change waits for the owner (The gift note has no place that keeps the last column for the total): its build stopped there, and a request is never proposed over it" <<<"$waiting" \
  && grep -qF "lem decisions log waited-change --by owner --breaker 2" <<<"$waiting" \
  && [ "$alone_log" = "['fable']" ] && [ "$(status_in "$LOCAL" waited-change)" = open ] \
  && [ "$(sed -n 1p "$text")" = '**Not green.**' ] \
  && [ "$(sed -n '3,4p' "$text" | cut -c1-38 | tr '\n' '|')" = "- decision 4 was taken without the own|- decision 5 was taken without the own|" ] \
  && [ -z "$(sed -n 5p "$text")" ] \
  && [ "$(sed -n '/^## Decisions of the build$/,/^## Decisions$/p' "$text" | grep -c '^- ')" = 5 ] \
  && grep -qF -- "- the build stopped at breaker 2, " "$text" && grep -qF "; the owner helped, decision 3." "$text" \
  && grep -qF -- '- Tell the merchants: "send nothing", by the owner, his help on breaker 2.' "$text" \
  && grep -qF -- "- decision 5 was taken without the owner (The word's line ending): \"a line break\", by one expert" "$text" \
  && grep -qF "the request is not green (decision 4 was taken without the owner" <<<"$agent"; then
  pass "a request is never proposed over a breaker that waits, also under a ready written over it; the owner's help settles it and is no cause; a pick of the dialectic and a decision of one expert alone are each a line of the text that is not green, the text lists the breaker and each decision of the record and names the one expert, and the merge agent does not merge it"
else
  fail "decisions in the landing: $waiting / $alone_log / $agent / $(cat "$text" 2>/dev/null)"
fi
project --repo "$LOCAL" state waited-change dropped "the test is over" >/dev/null

# Approved criteria in the landing: a criterion the build added or removed is not green, like a changed one; and the
# checks hold one line on the personas' read of the criteria, from its event, with his approval.
lcriteria() { "$PY" -B "$CRITERIA" --repo "$LOCAL" "$@"; }
ldecide() { "$PY" -B "$DECISIONS" --repo "$LOCAL" "$@"; }
# polish_local SLUG: a polish pass that finds nothing to change, as a full change's checks needs one
polish_local() { polish_in "$LOCAL" "$1"; }
# to_open SLUG: the machine steps with a polish pass, a clean read and the proposal of a task of the local repository
to_open() {
  local_land start "$1" >/dev/null && local_land base "$1" >/dev/null && polish_local "$1" && local_land checks "$1" >/dev/null \
    && local_land read "$1" --record "$(clean "$1" 1)" >/dev/null && local_land propose "$1" --title "fix: $1" --notes "$NOTES" >/dev/null
}
approved_day() { "$PY" -c 'import json, sys; print(json.load(open(sys.argv[1]))["at"][:10])' "$LOCAL/.lem/state/tasks/$1/criteria.json" 2>/dev/null || true; }
task_in "$LOCAL" criterion-departs d.txt d
tree=$(project --repo "$LOCAL" worktree-dir criterion-departs)
printf '%s\n' '## Acceptance criteria' '' 'Size: full, because the file gets a word and a rule of its own.' '' '1. The file holds the word the owner asked for.' '2. The file has one line.' > "$WORK/approved.md"
# the read comes first, of the criteria file that he then approves
read_digest=$(lcriteria digest criterion-departs --file "$WORK/approved.md" 2>/dev/null | field 'd["digest"]' 2>/dev/null || true)
project --repo "$LOCAL" log criterion-departs criteria.read by=lem asked:=2 answered:=2 'families:=["opus", "sol"]' 'silent:=[]' criteria:=2 flagged:=0 split:=false "digest=$read_digest" >/dev/null 2>&1 || true
lcriteria approve criterion-departs --file "$WORK/approved.md" >/dev/null 2>&1 || true
# shellcheck disable=SC2016
printf '%s\n' '# criterion-departs' '' '## Acceptance criteria' '' 'Size: full, because the file gets a word and a rule of its own.' '' '1. The file holds the word the owner asked for.' \
  '   - test: `sh tests/criterion-departs.sh` in `tests/criterion-departs.sh`' '2. The file ends with a line break.' '   - no test: printf ends every line so.' '' '## Tasks' '' '1. The change.' \
  > "$tree/docs/plans/2026-11-15-criterion-departs.md"
git -C "$tree" commit -q -am "docs: the criteria as they are built"
unrecorded=$(local_land start criterion-departs >/dev/null && local_land base criterion-departs >/dev/null && local_land checks criterion-departs 2>&1 || true)
# a criterion that a pick of the dialectic removes; and one the lead adds
ldecide log criterion-departs "${CASE[@]}" --what "The one-line rule" --option "keep the rule" --option "no such rule" --chose "no such rule" --by dialectic \
  --why "A second line holds the date." >/dev/null 2>&1 || true
nodecision=$(ldecide criterion criterion-departs --removed 2 --was "The file has one line." --why "A second line holds the date now." --decision 7 2>&1 || true)
ldecide criterion criterion-departs --removed 2 --was "The file has one line." --why "A second line holds the date now." --decision 1 >/dev/null 2>&1 || true
ldecide criterion criterion-departs --added 2 --now "The file ends with a line break." --why "The importer reads whole lines only." --by lead >/dev/null 2>&1 || true
polish_local criterion-departs 2>/dev/null && local_land checks criterion-departs >/dev/null 2>&1 && local_land read criterion-departs --record "$(clean criterion-departs 1)" >/dev/null 2>&1 \
  && local_land propose criterion-departs --title "fix: criterion-departs" --notes "$NOTES" >/dev/null 2>&1 || true
text=$LOCAL/.lem/state/tasks/criterion-departs/pr.md
agent=$(local_land merge criterion-departs --by merger 2>&1 || true)
if grep -qF "criterion 2 of 2026-11-15-criterion-departs.md says 'The file ends with a line break.', and the expected criterion 2 is 'The file has one line.'" <<<"$unrecorded" \
  && grep -qF "no decision 7 in criterion-departs" <<<"$nodecision" \
  && [ "$(sed -n 1p "$text" 2>/dev/null)" = '**Not green.**' ] \
  && [ "$(sed -n 3p "$text")" = '- criterion 2 was removed during the build: A second line holds the date now, after decision 1 (The one-line rule), where the dialectic took "no such rule"' ] \
  && [ "$(sed -n 4p "$text")" = '- criterion 2 was added during the build: The importer reads whole lines only.' ] \
  && grep -qxF -- '- criterion 2: removed, was "The file has one line.". A second line holds the date now, after decision 1 (The one-line rule), where the dialectic took "no such rule".' "$text" \
  && grep -qxF -- '- criterion 2: added, "The file ends with a line break.". The importer reads whole lines only. By the lead.' "$text" \
  && [ -n "$(approved_day criterion-departs)" ] \
  && grep -qxF -- "- the criteria were read by 2 of 2 personas asked, two model families (opus, sol); nobody confused; the owner approved them on $(approved_day criterion-departs)" "$text" \
  && grep -qxF -- "- the criteria changed after the personas' read, by a change of the build, and the change was not read" "$text" \
  && grep -qF "the request is not green (criterion 2 was removed during the build" <<<"$agent"; then
  pass "a criterion a pick of the dialectic removed and one the lead added are not green, each with its line first, what it was or is, its reason and the decision that led to it, which is on record; the gate refuses the plan until both are recorded; and the checks say that two model families read the criteria, when he approved them, and that a change of the build came after the read"
else
  fail "an added and a removed criterion in the landing: $unrecorded / $nodecision / $agent / $(cat "$text" 2>/dev/null)"
fi
project --repo "$LOCAL" state criterion-departs dropped "the test is over" >/dev/null
# A full change is not proposed without a read of its criteria, nor over a doubt of the personas that no approval of his followed.
task_in "$LOCAL" read-doubt r.txt r
tree=$(project --repo "$LOCAL" worktree-dir read-doubt)
printf '%s\n' '## Acceptance criteria' '' 'Size: full, because the ticket names the word and the file.' '' '1. The file holds the word the owner asked for.' > "$WORK/doubt.md"
plan_digest=$(lcriteria digest read-doubt 2>/dev/null | field 'd["digest"]' 2>/dev/null || true)
local_land start read-doubt >/dev/null && local_land base read-doubt >/dev/null && polish_local read-doubt && local_land checks read-doubt >/dev/null && local_land read read-doubt --record "$(clean read-doubt 1)" >/dev/null
unread_feature=$(local_land propose read-doubt --title "fix: r" --notes "$NOTES" 2>&1 || true)
project --repo "$LOCAL" log read-doubt criteria.read by=lead asked:=2 answered:=2 'families:=["opus", "sol"]' 'silent:=[]' criteria:=1 flagged:=0 split:=true "digest=$plan_digest" >/dev/null 2>&1 || true
split_unseen=$(local_land propose read-doubt --title "fix: r" --notes "$NOTES" 2>&1 || true)
freeze_split=$(lcriteria approve read-doubt --read 2>&1 || true)
project --repo "$LOCAL" log read-doubt criteria.read by=lead asked:=2 answered:=2 'families:=["opus"]' 'silent:=[]' criteria:=1 flagged:=1 split:=false "digest=$plan_digest" >/dev/null 2>&1 || true
flag_unseen=$(local_land propose read-doubt --title "fix: r" --notes "$NOTES" 2>&1 || true)
# the newest read: partial, one criterion flagged, the families split, and of other criteria than he then approved
project --repo "$LOCAL" log read-doubt criteria.read by=lem asked:=3 answered:=2 'families:=["opus", "sol"]' \
  'silent:=[{"name": "the accountant, sol", "why": "the model was at capacity"}]' criteria:=1 flagged:=1 split:=true "digest=$read_digest" >/dev/null 2>&1 || true
lcriteria approve read-doubt --file "$WORK/doubt.md" >/dev/null 2>&1 || true
local_land propose read-doubt --title "fix: r" --notes "$NOTES" >/dev/null 2>&1 || true
text=$LOCAL/.lem/state/tasks/read-doubt/pr.md
if grep -qF "read-doubt takes the standard track, and the event log has no \`criteria.read\`" <<<"$unread_feature" && grep -qF 'stages/interview.md' <<<"$unread_feature" \
  && grep -qF "the newest read of read-doubt's criteria found a split between the two families, and no approval of the owner's came after it" <<<"$split_unseen" \
  && grep -qF "found 1 flagged criterion, and no approval of the owner's came after it" <<<"$flag_unseen" && grep -qF "lem criteria approve read-doubt --file FILE" <<<"$flag_unseen" \
  && grep -qF "the newest read of read-doubt's criteria found a split between the families: the criteria wait for the owner, and only the owner's approval freezes them" <<<"$freeze_split" \
  && [ "$(sed -n 1p "$text" 2>/dev/null | cut -c1-10)" = '**Green.**' ] \
  && grep -qxF -- "- the criteria were read by 2 of 3 personas asked, two model families (opus, sol); 1 of 1 criterion flagged; the two families split; no answer from the accountant, sol (the model was at capacity); the owner approved them on $(approved_day read-doubt)" "$text" \
  && grep -qxF -- "- the criteria changed after the personas' read, by the owner's approval 1, and the change was not read" "$text"; then
  pass "a full change with no read of its criteria is not proposed, nor one whose newest read flagged a criterion or split the families with no approval of his after it; a partial read counts and says who did not answer and why; and criteria he changed after the read are one line that is no cause of not green"
else
  fail "the read before a proposal: $unread_feature / $split_unseen / $freeze_split / $flag_unseen / $(cat "$text" 2>/dev/null)"
fi
project --repo "$LOCAL" state read-doubt dropped "the test is over" >/dev/null
# A request that had an interview ends it with his yes: after a read that found nobody confused, with no approval of his,
# or with only the lead's freeze of the read, it is not proposed; his approval lets it go, green.
task_in "$LOCAL" asked-first f.txt f
project --repo "$LOCAL" log asked-first interview.start >/dev/null
read_in "$LOCAL" asked-first
local_land start asked-first >/dev/null && local_land base asked-first >/dev/null && polish_local asked-first && local_land checks asked-first >/dev/null \
  && local_land read asked-first --record "$(clean asked-first 1)" >/dev/null
unasked=$(local_land propose asked-first --title "fix: f" --notes "$NOTES" 2>&1 || true)
lcriteria approve asked-first --read >/dev/null 2>&1 || true
frozen=$(local_land propose asked-first --title "fix: f" --notes "$NOTES" 2>&1 || true)
printf '%s\n' '## Acceptance criteria' '' 'Size: full, because the ticket names the word and the file.' '' '1. The file holds the word the owner asked for.' > "$WORK/asked.md"
lcriteria approve asked-first --file "$WORK/asked.md" >/dev/null 2>&1 || true
yes=$(local_land propose asked-first --title "fix: f" --notes "$NOTES" 2>/dev/null | field 'd["green"]' 2>/dev/null || true)
if grep -qF "asked-first had an interview (\`interview.start\` in the event log), and its criteria carry no approval of the owner's" <<<"$unasked" \
  && grep -qF "lem criteria approve asked-first --file FILE" <<<"$unasked" && grep -qF "had an interview" <<<"$frozen" && [ "$yes" = True ] && [ "$(status_in "$LOCAL" asked-first)" = open ]; then
  pass "a request that had an interview is not proposed without the owner's approval of its criteria, also after a read that found nobody confused and the lead's freeze of it; his approval lets it go, green"
else
  fail "an interview with no approval of his: $unasked / $frozen / $yes"
fi
project --repo "$LOCAL" state asked-first dropped "the test is over" >/dev/null
# The read is compared with the criteria as they are now, and the history of criterion changes stays in the pull request:
# approval 1, the personas change its criterion, a clean read of the changed criterion, then his approval of it.
task_in "$LOCAL" after-change a.txt a
tree=$(project --repo "$LOCAL" worktree-dir after-change)
printf '%s\n' '## Acceptance criteria' '' 'Size: full, because the ticket names the word and the file.' '' '1. The file holds the word y.' > "$WORK/first.md"
printf '%s\n' '## Acceptance criteria' '' 'Size: full, because the ticket names the word and the file.' '' '1. The file holds the word the owner asked for.' > "$WORK/changed.md"
lcriteria approve after-change --file "$WORK/first.md" >/dev/null 2>&1 || true
ldecide criterion after-change --changed 1 --was "The file holds the word y." --now "The file holds the word the owner asked for." --why "y is taken by another file." \
  --by personas --said "Both personas picked the owner's word." >/dev/null 2>&1 || true
digest=$(lcriteria digest after-change 2>/dev/null | field 'd["digest"]' 2>/dev/null || true)
project --repo "$LOCAL" log after-change criteria.read by=lem asked:=2 answered:=2 'families:=["opus", "sol"]' 'silent:=[]' criteria:=1 flagged:=0 split:=false "digest=$digest" >/dev/null 2>&1 || true
to_open after-change || true
text=$LOCAL/.lem/state/tasks/after-change/pr.md
cp "$text" "$WORK/first-pr.md" 2>/dev/null || : > "$WORK/first-pr.md"
# he approves the changed criterion; the proposal is made again
project --repo "$LOCAL" state after-change landing "he approved the changed criterion" >/dev/null
lcriteria approve after-change --file "$WORK/changed.md" >/dev/null 2>&1 || true
local_land propose after-change --title "fix: a" --notes "$NOTES" >/dev/null 2>&1 || true
history_line='- criterion 1: was "The file holds the word y.", now "The file holds the word the owner asked for.". y is taken by another file. By the personas: Both personas picked the owner'"'"'s word.'
if [ "$(sed -n 1p "$WORK/first-pr.md")" = '**Not green.**' ] && [ "$(sed -n 3p "$WORK/first-pr.md")" = '- criterion 1 changed during the build: y is taken by another file.' ] \
  && grep -qxF -- "$history_line" "$WORK/first-pr.md" && ! grep -q "after the personas' read" "$WORK/first-pr.md" \
  && [ "$(sed -n 1p "$text" | cut -c1-10)" = '**Green.**' ] \
  && grep -qxF -- "$history_line Approved by the owner afterwards (approval 2)." "$text" \
  && ! grep -qiwE 'you|your' "$WORK/first-pr.md" "$text" \
  && grep -qxF -- "- the criteria were read by 2 of 2 personas asked, two model families (opus, sol); nobody confused; the owner approved them on $(approved_day after-change)" "$text" \
  && ! grep -q "after the personas' read" "$text"; then
  pass "a read of the criteria as a recorded change made them is the read of the criteria now, and no line says otherwise; a change he approved afterwards stays in the pull request with its reason and the personas' answer, marked as approved by him, and is no cause of not green"
else
  fail "the read and the history after a later approval: $(cat "$WORK/first-pr.md") / $(cat "$text" 2>/dev/null)"
fi
project --repo "$LOCAL" state after-change dropped "the test is over" >/dev/null
# A full change from a complete request: the lead ran the read with one model family, nobody was confused, and there is no approval; a scout's report is named.
task_in "$LOCAL" ticket-word t.txt t
tree=$(project --repo "$LOCAL" worktree-dir ticket-word)
digest=$(lcriteria digest ticket-word 2>/dev/null | field 'd["digest"]' 2>/dev/null || true)
read_with() { project --repo "$LOCAL" log ticket-word criteria.read "$@" 2>&1 || true; }
bad_by=$(read_with by=owner asked:=2 answered:=2 'families:=["opus"]' 'silent:=[]' criteria:=1 flagged:=0 split:=false "digest=$digest")
bad_one=$(read_with by=lead asked:=1 answered:=1 'families:=["opus"]' 'silent:=[]' criteria:=1 flagged:=0 split:=false "digest=$digest")
bad_none=$(read_with by=lead asked:=2 answered:=0 'families:=["opus"]' 'silent:=[{"name": "a", "why": "b"}]' criteria:=1 flagged:=0 split:=false "digest=$digest")
bad_more=$(read_with by=lead asked:=2 answered:=3 'families:=["opus"]' 'silent:=[]' criteria:=1 flagged:=0 split:=false "digest=$digest")
bad_quiet=$(read_with by=lead asked:=3 answered:=2 'families:=["opus"]' 'silent:=[]' criteria:=1 flagged:=0 split:=false "digest=$digest")
bad_families=$(read_with by=lead asked:=2 answered:=2 families=opus 'silent:=[]' criteria:=1 flagged:=0 split:=false "digest=$digest")
bad_flagged=$(read_with by=lead asked:=2 answered:=2 'families:=["opus"]' 'silent:=[]' criteria:=1 flagged:=2 split:=false "digest=$digest")
bad_split=$(read_with by=lead asked:=2 answered:=2 'families:=["opus"]' 'silent:=[]' criteria:=1 flagged:=0 split:=true "digest=$digest")
bad_digest=$(read_with by=lead asked:=2 answered:=2 'families:=["opus"]' 'silent:=[]' criteria:=1 flagged:=0 split:=false digest=abc)
bad_missing=$(read_with by=lead asked:=2 answered:=2 'families:=["opus"]' criteria:=1 flagged:=0 split:=false "digest=$digest")
project --repo "$LOCAL" log ticket-word criteria.read by=lead asked:=2 answered:=2 'families:=["opus"]' 'silent:=[]' criteria:=1 flagged:=0 split:=false "digest=$digest" >/dev/null 2>&1 || true
# the lead freezes what the personas read: another text is refused, the plan's own criteria are kept with `by: read`
printf '%s\n' '## Acceptance criteria' '' 'Size: full, because the ticket names the word and the file.' '' '1. The file holds another word.' > "$WORK/other.md"
freeze_other=$(lcriteria approve ticket-word --file "$WORK/other.md" --read 2>&1 || true)
lcriteria approve ticket-word --read >/dev/null 2>&1 || true
frozen=$("$PY" -c 'import json, sys; d = json.load(open(sys.argv[1])); print((d["by"], d["number"]))' "$LOCAL/.lem/state/tasks/ticket-word/criteria.json" 2>&1 || true)
recorded=$(ldecide criterion ticket-word --changed 1 --was "Not the criterion." --now "x" --why "w" --by lead 2>&1 || true)
echo '1. t.txt does not exist on the base branch (git ls-files).' > "$LOCAL/.lem/state/tasks/ticket-word/scout.md"
to_open ticket-word || true
text=$LOCAL/.lem/state/tasks/ticket-word/pr.md
if [ "$(sed -n 1p "$text" 2>/dev/null | cut -c1-10)" = '**Green.**' ] \
  && grep -qxF -- "- the criteria were read by 2 of 2 personas asked, one model family (opus); nobody confused; the build started with no wait for the owner" "$text" \
  && ! grep -q "after the personas' read" "$text" \
  && grep -qxF -- "- the criteria were written from the scout's facts of the code, read during the interview" "$text" && ! grep -qF "$LOCAL" "$text" \
  && grep -q "by is lem, when Lem ran the read" <<<"$bad_by" && grep -q "a read asks two personas at the least" <<<"$bad_one" \
  && grep -q "a read in which nobody answered has families:='\[\]'" <<<"$bad_none" && grep -q "answered is at most asked" <<<"$bad_more" \
  && grep -q "silent names each source that did not, with why" <<<"$bad_quiet" \
  && grep -q "families is the list of the model families that answered" <<<"$bad_families" && grep -q "no more criteria flagged than it read" <<<"$bad_flagged" \
  && grep -q "a split is between two model families, and families names one" <<<"$bad_split" && grep -q "digest is the twelve characters" <<<"$bad_digest" \
  && grep -q "criteria.read takes by=lem|lead asked:=N answered:=N" <<<"$bad_missing" \
  && [ "$(grep -c '"event": "criteria.read", "task": "ticket-word"' "$LOCAL/.lem/state/events.jsonl")" = 1 ] \
  && grep -qF -- "--read freezes the plan's own criteria, the ones the read named: it takes no --file" <<<"$freeze_other" \
  && [ "$frozen" = "('read', 1)" ] && grep -qF "criterion 1 is 'The file holds the word the owner asked for.' after every earlier change" <<<"$recorded"; then
  pass "a read by the lead with one model family in which nobody was confused is one line of the checks, which says the build did not wait for him, and the scout's facts are named with no path of this machine; a read's event without its form, with fewer than two personas asked, with nobody or more than were asked answering, or with a missing source unnamed is refused, and nothing is written for it; the lead freezes the plan's criteria the read named, with no file of other criteria, and from then on a change of them has its record, while the line still says the build did not wait for him"
else
  fail "the read of a full change from a complete request: $freeze_other / $frozen / $recorded / $bad_by / $bad_one / $bad_none / $bad_more / $bad_quiet / $bad_families / $bad_flagged / $bad_split / $bad_digest / $bad_missing / $(cat "$text" 2>/dev/null)"
fi
# A read freezes only the first contract of a task: a second clean read of other criteria does not replace the frozen
# ones, and a read does not replace his own approval, whose size is his.
other_digest=$(lcriteria digest ticket-word --file "$WORK/other.md" 2>/dev/null | field 'd["digest"]' 2>/dev/null || true)
project --repo "$LOCAL" log ticket-word criteria.read by=lead asked:=2 answered:=2 'families:=["opus"]' 'silent:=[]' criteria:=1 flagged:=0 split:=false "digest=$other_digest" >/dev/null 2>&1 || true
refile=$(lcriteria approve ticket-word --read --file "$WORK/other.md" 2>&1 || true)
refreeze=$(lcriteria approve ticket-word --read 2>&1 || true)
printf '%s\n' '## Acceptance criteria' '' 'Size: small, because it is one sentence.' '' '1. The file holds the word the owner asked for.' > "$WORK/as-correction.md"
correction_digest=$(lcriteria digest after-change --file "$WORK/as-correction.md" 2>/dev/null | field 'd["digest"]' 2>/dev/null || true)
project --repo "$LOCAL" log after-change criteria.read by=lead asked:=2 answered:=2 'families:=["opus"]' 'silent:=[]' criteria:=1 flagged:=0 split:=false "digest=$correction_digest" >/dev/null 2>&1 || true
over_his=$(lcriteria approve after-change --read 2>&1 || true)
over_his_file=$(lcriteria approve after-change --read --file "$WORK/as-correction.md" 2>&1 || true)
kept_contracts=$("$PY" -c 'import json, sys; print([(json.load(open(f))["number"], json.load(open(f))["by"], json.load(open(f))["size"]) for f in sys.argv[1:]])' \
  "$LOCAL/.lem/state/tasks/ticket-word/criteria.json" "$LOCAL/.lem/state/tasks/after-change/criteria.json" 2>&1 || true)
if grep -qF "ticket-word has approval 1 of its criteria already (by read): a read freezes only the first contract" <<<"$refreeze" \
  && grep -qF "A criterion changes through its record, \`lem decisions criterion ticket-word ...\`, and the track only through the owner's own approval" <<<"$refreeze" \
  && grep -qF "after-change has approval 2 of its criteria already (by owner): a read freezes only the first contract" <<<"$over_his" \
  && grep -qF "it takes no --file" <<<"$over_his_file" && grep -qF "it takes no --file" <<<"$refile" \
  && [ "$kept_contracts" = "[(1, 'read', 'full'), (2, 'owner', 'full')]" ]; then
  pass "a read freezes only the first contract of a task: a second clean read of other criteria freezes nothing over a read's contract, and a read never replaces his approval or its size"
else
  fail "a second freeze by a read: $refile / $refreeze / $over_his / $over_his_file / $kept_contracts"
fi
project --repo "$LOCAL" state ticket-word dropped "the test is over" >/dev/null
# A complete request that someone else wrote waits for the owner's yes to its criteria, also when nobody was confused:
# a freeze by the read is not proposed, whether the brief or a state line says whose request it is; his approval after
# the read is, and the checks say that he approved them.
task_in "$LOCAL" their-ticket h.txt h
printf '%s\n' 'slug: their-ticket' 'request by: someone else' > "$LOCAL/.lem/state/tasks/their-ticket/brief.md"
digest=$(lcriteria digest their-ticket 2>/dev/null | field 'd["digest"]' 2>/dev/null || true)
project --repo "$LOCAL" log their-ticket criteria.read by=lead asked:=2 answered:=2 'families:=["opus"]' 'silent:=[]' criteria:=1 flagged:=0 split:=false "digest=$digest" >/dev/null 2>&1 || true
lcriteria approve their-ticket --read >/dev/null 2>&1 || true
local_land start their-ticket >/dev/null && local_land base their-ticket >/dev/null && polish_local their-ticket && local_land checks their-ticket >/dev/null \
  && local_land read their-ticket --record "$(clean their-ticket 1)" >/dev/null
by_brief=$(local_land propose their-ticket --title "fix: h" --notes "$NOTES" 2>&1 || true)
# the same task with the line in a state block and not in the brief
printf '%s\n' 'slug: their-ticket' > "$LOCAL/.lem/state/tasks/their-ticket/brief.md"
project --repo "$LOCAL" state their-ticket landing "the lead's report is in" "request by: someone else" >/dev/null
by_state=$(local_land propose their-ticket --title "fix: h" --notes "$NOTES" 2>&1 || true)
printf '%s\n' '## Acceptance criteria' '' 'Size: full, because the ticket names the word and the file.' '' '1. The file holds the word the owner asked for.' > "$WORK/their.md"
# the criteria wait for his yes, he gives it, and the landing goes on
project --repo "$LOCAL" state their-ticket held "the criteria wait for the owner: a request someone else wrote" >/dev/null
lcriteria approve their-ticket --file "$WORK/their.md" >/dev/null 2>&1 || true
project --repo "$LOCAL" state their-ticket landing "the owner approved the criteria" >/dev/null
proposed_their=$(local_land propose their-ticket --title "fix: h" --notes "$NOTES" 2>&1 || true)
text=$LOCAL/.lem/state/tasks/their-ticket/pr.md
if grep -qF "their-ticket is a complete request that someone else wrote, and no approval of the owner's came after the newest read of its criteria" <<<"$by_brief" \
  && grep -qF "a freeze by the read is not his yes" <<<"$by_brief" && grep -qF "lem criteria approve their-ticket --file FILE" <<<"$by_brief" \
  && grep -qF "their-ticket is a complete request that someone else wrote" <<<"$by_state" \
  && [ "$(status_in "$LOCAL" their-ticket)" = open ] && [ "$(sed -n 1p "$text" 2>/dev/null | cut -c1-10)" = '**Green.**' ] \
  && grep -qxE -- "- the criteria were read by 2 of 2 personas asked, one model family \(opus\); nobody confused; the criteria waited for the owner's yes from [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2} UTC, and the owner gave it on $(approved_day their-ticket) [0-9]{2}:[0-9]{2} UTC" "$text"; then
  pass "a complete request that someone else wrote, by its brief or a state line, is not proposed with only the lead's freeze of a read in which nobody was confused; the owner's approval after the read lets it through, and the checks say that the criteria waited for his yes and when he gave it"
else
  fail "a complete request of someone else's: $by_brief / $by_state / $proposed_their / $(cat "$text" 2>/dev/null)"
fi
project --repo "$LOCAL" state their-ticket dropped "the test is over" >/dev/null
# A read in which nobody answered is written down too, and started once more: after the first one the
# request is not proposed and the lead's freeze is refused; after the second the build goes on,
# the freeze takes the criteria, and the request is not green for it, with the reason first.
task_in "$LOCAL" nobody-read n.txt n
tree=$(project --repo "$LOCAL" worktree-dir nobody-read)
digest=$(lcriteria digest nobody-read 2>/dev/null | field 'd["digest"]' 2>/dev/null || true)
quiet='silent:=[{"name": "the buyer, opus", "why": "the model was at capacity"}, {"name": "the clerk, opus", "why": "the model was at capacity"}]'
empty_with() { project --repo "$LOCAL" log nobody-read criteria.read by=lead asked:=2 answered:=0 "$@" criteria:=1 split:=false "digest=$digest" 2>&1 || true; }
empty_family=$(empty_with 'families:=["opus"]' "$quiet" flagged:=0)
empty_unnamed=$(empty_with 'families:=[]' 'silent:=[{"name": "the buyer, opus", "why": "the model was at capacity"}]' flagged:=0)
empty_flagged=$(empty_with 'families:=[]' "$quiet" flagged:=1)
first_empty=$(empty_with 'families:=[]' "$quiet" flagged:=0)
local_land start nobody-read >/dev/null && local_land base nobody-read >/dev/null && polish_local nobody-read && local_land checks nobody-read >/dev/null \
  && local_land read nobody-read --record "$(clean nobody-read 1)" >/dev/null
once=$(local_land propose nobody-read --title "fix: n" --notes "$NOTES" 2>&1 || true)
freeze_once=$(lcriteria approve nobody-read --read 2>&1 || true)
second_empty=$(empty_with 'families:=[]' "$quiet" flagged:=0)
freeze_twice=$(lcriteria approve nobody-read --read 2>&1 || true)
local_land propose nobody-read --title "fix: n" --notes "$NOTES" >/dev/null 2>&1 || true
text=$LOCAL/.lem/state/tasks/nobody-read/pr.md
twice_agent=$(local_land merge nobody-read --by merger 2>&1 || true)
if grep -q "a read in which nobody answered has families:='\[\]'" <<<"$empty_family" && grep -q "a read in which nobody answered has families:='\[\]'" <<<"$empty_unnamed" \
  && grep -q "a read in which nobody answered has families:='\[\]'" <<<"$empty_flagged" \
  && grep -q '"event": "criteria.read"' <<<"$first_empty" && grep -q '"event": "criteria.read"' <<<"$second_empty" \
  && grep -qF "nobody answered the newest read of nobody-read's criteria: it is started once more" <<<"$once" \
  && grep -qF "nobody answered the newest read of nobody-read's criteria: it is started once more" <<<"$freeze_once" \
  && grep -q '"by": "read"' <<<"$freeze_twice" \
  && [ "$(sed -n 1p "$text" 2>/dev/null)" = '**Not green.**' ] \
  && [ "$(sed -n 3p "$text")" = "- the criteria were not read: the personas' read was started twice and nobody answered; no answer from the buyer, opus (the model was at capacity); no answer from the clerk, opus (the model was at capacity)" ] \
  && grep -qxF -- "- the criteria were not read by the personas: 2 reads in a row, and none of the 2 personas asked answered; the build started with no wait for the owner" "$text" \
  && grep -qF "the request is not green (the criteria were not read" <<<"$twice_agent"; then
  pass "a read in which nobody answered is written down with no family and each source named, and started once more: after one the request is not proposed and the criteria are not frozen; after the second the build goes on, the criteria are frozen as read, and the request is not green with that reason first"
else
  fail "a read nobody answered, twice: $empty_family / $empty_unnamed / $empty_flagged / $first_empty / $once / $freeze_once / $second_empty / $freeze_twice / $twice_agent / $(cat "$text" 2>/dev/null)"
fi
project --repo "$LOCAL" state nobody-read dropped "the test is over" >/dev/null
# A plan never makes a change small: one plain change is a small change, whose one criterion is in the task directory
# and which has no plan. A plan that says `Size: small`, as a lead of a full change from a complete request or of a
# night could write it, is refused by the criteria and by every step of the landing that reads them, with or without
# Lem's approval of a small change in the owner's name, and the refusal names the small change.
task_in "$LOCAL" one-word o.txt o
tree=$(project --repo "$LOCAL" worktree-dir one-word)
"$PY" -c 'import sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(s.replace("Size: full, because the ticket names the word and the file.", "Size: small, because the request is one sentence."))' "$tree/docs/plans/2026-11-15-one-word.md"
git -C "$tree" commit -q -am "docs: the plan of a small change"
as_plan=$(lcriteria show one-word 2>&1 || true)
local_land start one-word >/dev/null && local_land base one-word >/dev/null
as_polish=$(local_land polish one-word 2>&1 || true)
as_gate=$(local_land checks one-word 2>&1 || true)
printf '%s\n' '## Acceptance criteria' '' 'Size: small, because the request is one sentence.' '' '1. The file holds the word the owner asked for.' > "$WORK/correction.md"
lcriteria approve one-word --file "$WORK/correction.md" --small >/dev/null 2>&1 || true
approved_plan=$(lcriteria red one-word 2>&1 || true)
never="2026-11-15-one-word.md says \`Size: small\`, and a plan never puts a task on the fast track"
if grep -qF "$never" <<<"$as_plan" && grep -qF "one plain change takes the fast track, whose one criterion is \`criteria.md\` in the task directory" <<<"$as_plan" \
  && grep -qF "Size: full, because" <<<"$as_plan" && grep -qF "$never" <<<"$as_polish" && grep -qF "$never" <<<"$as_gate" && grep -qF "$never" <<<"$approved_plan" \
  && [ "$(kept_in "$LOCAL" one-word gated)" = None ] && [ "$(kept_in "$LOCAL" one-word polish)" = None ] \
  && ! grep -q '"event": "gate.start", "task": "one-word"' "$LOCAL/.lem/state/events.jsonl"; then
  pass "a plan that says Size: small is refused by the criteria, the polish pass and the gate, also with Lem's approval of a small change in the owner's name; the refusal names the small change, which has no plan, and the full change's Size line"
else
  fail "a plan of a small change: $as_plan / $as_polish / $as_gate / $approved_plan"
fi
project --repo "$LOCAL" state one-word dropped "the test is over" >/dev/null
# The owner's word to skip the personas' read, when every criterion names only the developer: the record of his word and
# his approval after it let a full change land with no read, green, with one line that says so. Lem's word is not his;
# a full change with no read and no such record is refused as before; and from a complete request the read always runs.
# skip_read SLUG BY: the word to skip the personas' read, in the form the landing reads
skip_read() { ldecide log "$1" --by "$2" --what "the personas' read of the criteria" --chose "no read: the criteria name only the developer" --why "y" 2>&1 || true; }
# checked_local SLUG: the machine steps, a polish pass and a clean read, up to the proposal
checked_local() {
  local_land start "$1" >/dev/null && local_land base "$1" >/dev/null && polish_local "$1" && local_land checks "$1" >/dev/null \
    && local_land read "$1" --record "$(clean "$1" 1)" >/dev/null
}
printf '%s\n' '## Acceptance criteria' '' 'Size: full, because the ticket names the word and the file.' '' '1. The file holds the word the owner asked for.' > "$WORK/mine.md"
task_in "$LOCAL" only-me m.txt m
skip_read only-me owner >/dev/null
checked_local only-me
unapproved=$(local_land propose only-me --title "feat: m" --notes "$NOTES" 2>&1 || true)
lcriteria approve only-me --file "$WORK/mine.md" >/dev/null 2>&1 || true
local_land propose only-me --title "feat: m" --notes "$NOTES" >/dev/null 2>&1 || true
text=$LOCAL/.lem/state/tasks/only-me/pr.md
skipped_day=$("$PY" -c 'import json, sys; print(json.loads(open(sys.argv[1]).readline())["at"][:10])' "$LOCAL/.lem/state/tasks/only-me/decisions.jsonl" 2>/dev/null || true)
if grep -qF "the owner's word to skip the personas' read of only-me's criteria is on record, and no approval of the owner's came after it" <<<"$unapproved" \
  && grep -qF "lem criteria approve only-me --file FILE" <<<"$unapproved" \
  && [ "$(sed -n 1p "$text" 2>/dev/null | cut -c1-10)" = '**Green.**' ] && [ -n "$skipped_day" ] \
  && grep -qxF -- "- the criteria: not read by the personas, on the owner's word ($skipped_day); the owner approved them" "$text" \
  && ! grep -q 'the criteria were read by\|no read by the personas is on record' "$text" \
  && grep -q '"event": "proposed", "task": "only-me".*"green": true' "$LOCAL/.lem/state/events.jsonl"; then
  pass "a full change whose criteria name only the developer lands with no read on his recorded word and his approval after it: green, with the line that the personas did not read them on his word and that he approved them; his word with no approval after it is refused"
else
  fail "the owner's skip of the read: $unapproved / $skipped_day / $(cat "$text" 2>/dev/null)"
fi
project --repo "$LOCAL" state only-me dropped "the test is over" >/dev/null
task_in "$LOCAL" no-word w.txt w
checked_local no-word
lcriteria approve no-word --file "$WORK/mine.md" >/dev/null 2>&1 || true
no_word=$(local_land propose no-word --title "feat: w" --notes "$NOTES" 2>&1 || true)
skip_read no-word lem >/dev/null
lem_word=$(local_land propose no-word --title "feat: w" --notes "$NOTES" 2>&1 || true)
if grep -qF "no-word takes the standard track, and the event log has no \`criteria.read\`" <<<"$no_word" \
  && grep -qF "lem decisions log no-word --by owner --what \"the personas' read of the criteria\" --chose \"no read: the criteria name only the developer\"" <<<"$no_word" \
  && grep -qF "no-word takes the standard track, and the event log has no \`criteria.read\`" <<<"$lem_word" \
  && [ ! -e "$LOCAL/.lem/state/tasks/no-word/pr.md" ]; then
  pass "a full change with his approval and no read is refused when no word of his to skip the read is on record, and a word of Lem's in the same form is no such word"
else
  fail "a full change with no read and no word of his: $no_word / $lem_word"
fi
project --repo "$LOCAL" state no-word dropped "the test is over" >/dev/null
task_in "$LOCAL" rare-word r2.txt r
skip_read rare-word owner >/dev/null
project --repo "$LOCAL" state rare-word building "the lead writes the plan" "lead: builder" >/dev/null
lcriteria approve rare-word --file "$WORK/mine.md" >/dev/null 2>&1 || true
project --repo "$LOCAL" state rare-word ready "the report is written" >/dev/null
checked_local rare-word
approved_late=$(local_land propose rare-word --title "feat: r" --notes "$NOTES" 2>&1 || true)
skip_read rare-word owner >/dev/null
lcriteria approve rare-word --file "$WORK/mine.md" >/dev/null 2>&1 || true
said_late=$(local_land propose rare-word --title "feat: r" --notes "$NOTES" 2>&1 || true)
if grep -qF "a lead of rare-word started before the owner's approval that came after the word to skip the personas' read" <<<"$approved_late" \
  && grep -qF "on the standard track from a complete request the read always runs" <<<"$approved_late" && grep -qF "stages/plan.md" <<<"$approved_late" \
  && grep -qF "a lead of rare-word started before the owner's word to skip the personas' read" <<<"$said_late" \
  && [ ! -e "$LOCAL/.lem/state/tasks/rare-word/pr.md" ]; then
  pass "for a full change from a complete request his word to skip the read is refused: a lead that started before his word, or before his approval after it, wrote the criteria, and the personas read them"
else
  fail "a skip of the read of a full change from a complete request: $approved_late / $said_late"
fi
project --repo "$LOCAL" state rare-word dropped "the test is over" >/dev/null

# Without the owner, Lem or the lead approves the criteria itself (`approve --alone`), here in tasks a night marked:
# refused while the task runs with him, for a small change's file and over his approval, taken over Lem's approval of a
# small change; and a request that someone else wrote, whose read flagged a criterion, is proposed with such an approval
# after the read.
task_in "$LOCAL" gone-out g.txt g
printf '%s\n' '## Acceptance criteria' '' 'Size: full, because the ticket names the word and the file.' '' '1. The file holds the word the owner asked for.' > "$WORK/gone.md"
printf '%s\n' 'slug: gone-out' 'request by: someone else' > "$LOCAL/.lem/state/tasks/gone-out/brief.md"
digest=$(lcriteria digest gone-out 2>/dev/null | field 'd["digest"]' 2>/dev/null || true)
project --repo "$LOCAL" log gone-out criteria.read by=lead asked:=2 answered:=2 'families:=["opus"]' 'silent:=[]' criteria:=1 flagged:=1 split:=false "digest=$digest" >/dev/null 2>&1 || true
with_him=$(lcriteria approve gone-out --file "$WORK/gone.md" --alone 2>&1 || true)
# the night's mark on a task that has its words: the same words again, since a task's words are written once
project --repo "$LOCAL" task-dir gone-out --ask "Put g into g.txt." --night 2026-11-18 >/dev/null
# the fast track's criterion of the owner's own request is approved in his name, never --alone (a night's or someone else's is: tests/unit/test_criteria.py)
project --repo "$LOCAL" task-dir own-small --ask "Put the word into o.txt." >/dev/null
small_file=$(lcriteria approve own-small --file "$WORK/as-correction.md" --alone 2>&1 || true)
two_kinds=$(status_of lcriteria approve gone-out --file "$WORK/gone.md" --alone --small)
checked_local gone-out
flagged=$(local_land propose gone-out --title "feat: g" --notes "$NOTES" 2>&1 || true)
by_alone=$(lcriteria approve gone-out --file "$WORK/gone.md" --alone 2>&1 | field 'd["by"]' 2>&1 || true)
local_land propose gone-out --title "feat: g" --notes "$NOTES" >/dev/null 2>&1 || true
proposed_alone=$(status_in "$LOCAL" gone-out)
project --repo "$LOCAL" task-dir grew-up >/dev/null
printf '%s\n' '## Acceptance criteria' '' 'Size: small, because the request is one sentence.' '' '1. The file holds the word the owner asked for.' > "$LOCAL/.lem/state/tasks/grew-up/criteria.md"
lcriteria approve grew-up --small >/dev/null 2>&1 || true
project --repo "$LOCAL" task-dir grew-up --ask "Put the word into the file." --night 2026-11-18 >/dev/null
over_small=$(lcriteria approve grew-up --file "$WORK/gone.md" --alone 2>&1 | field '(d["by"], d["number"])' 2>&1 || true)
lcriteria approve grew-up --file "$WORK/gone.md" >/dev/null 2>&1 || true
over_his=$(lcriteria approve grew-up --file "$WORK/gone.md" --alone 2>&1 || true)
if grep -qF "gone-out runs with the owner: the owner's yes approves its criteria" <<<"$with_him" && grep -qF "the fast track's criterion is approved in the owner's name with --small" <<<"$small_file" \
  && [ "$two_kinds" = 1 ] && grep -qF "found 1 flagged criterion, and no approval of the owner's came after it" <<<"$flagged" \
  && [ "$by_alone" = alone ] && [ "$proposed_alone" = open ] \
  && [ "$over_small" = "('alone', 2)" ] && grep -qF "grew-up has approval 3 of its criteria already (by owner)" <<<"$over_his"; then
  pass "without the owner the criteria are approved by:alone, never while the task runs with him, for the small change of his own request or over his approval; a flagged read of someone else's request with such an approval after it is proposed"
else
  fail "criteria approved without the owner: $with_him / $small_file / $two_kinds / $flagged / $by_alone / $proposed_alone / $over_small / $over_his"
fi
project --repo "$LOCAL" state gone-out dropped "the test is over" >/dev/null

# Without the owner a criterion the personas flagged climbs the ladder (`stages/away.md`): the dialectic rewrites it, and
# `approve --alone` takes the criteria as the ladder left them, which differ from the ones the personas read; the request
# is proposed, not green, with the decision and the change after the read each on a line.
task_in "$LOCAL" settled-out s.txt s
printf '%s\n' '## Acceptance criteria' '' 'Size: full, because the ticket names the word and the file.' '' '1. The file holds a word.' > "$WORK/settled-read.md"
read_digest=$(lcriteria digest settled-out --file "$WORK/settled-read.md" 2>/dev/null | field 'd["digest"]' 2>/dev/null || true)
project --repo "$LOCAL" log settled-out criteria.read by=lem asked:=2 answered:=2 'families:=["opus"]' 'silent:=[]' criteria:=1 flagged:=1 split:=false "digest=$read_digest" >/dev/null 2>&1 || true
project --repo "$LOCAL" task-dir settled-out --ask "Put s into s.txt." --night 2026-11-18 >/dev/null
ldecide log settled-out "${CASE[@]}" --what "criterion 1" --option "The file holds a word." --option "The file holds the word the owner asked for." \
  --chose "The file holds the word the owner asked for." --by dialectic --level "personas=one flagged it" --why "no break against the persona's reading" >/dev/null 2>&1 || true
settled_by=$(lcriteria approve settled-out --file "$WORK/gone.md" --alone 2>&1 | field 'd["by"]' 2>&1 || true)
checked_local settled-out
local_land propose settled-out --title "feat: s" --notes "$NOTES" >/dev/null 2>&1 || true
text=$LOCAL/.lem/state/tasks/settled-out/pr.md
if [ "$settled_by" = alone ] && [ "$(status_in "$LOCAL" settled-out)" = open ] && [ "$(sed -n 1p "$text" 2>/dev/null)" = '**Not green.**' ] \
  && grep -qF -- '- decision 1 was taken without the owner (criterion 1): "The file holds the word the owner asked for.", by the dialectic' "$text" \
  && grep -qF -- "- the criteria changed after the personas' read" "$text"; then
  pass "without the owner a flagged criterion the dialectic rewrote is approved by:alone as the ladder left it, and the request is proposed not green, with the decision and the change after the read"
else
  fail "a flagged criterion settled by the ladder without the owner: $settled_by / $(status_in "$LOCAL" settled-out) / $(cat "$text" 2>/dev/null)"
fi
project --repo "$LOCAL" state settled-out dropped "the test is over" >/dev/null

finish
