#!/usr/bin/env bash
# The landing with no remote: decisions, stories and the personas' read in the pull request's
# text, a review of the change as it is, and the bar.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

LOCAL=$WORK/local
git init -q -b main "$LOCAL" && ident "$LOCAL"
project --repo "$LOCAL" init --base main >/dev/null
printf '%s\n' '[branch]' 'base = "main"' 'land = "agent"' '[gate]' 'commands = ["true"]' 'bar = ["rubocop:disable"]' '[flow]' 'topics = ["a customer is charged the wrong price"]' > "$LOCAL/.lem/project.toml"
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
git -C "$LOCAL" add -A && git -C "$LOCAL" commit -q -m "chore: start"
local_land() { land --repo "$LOCAL" "$@"; }
task_in "$LOCAL" local-change x.txt x
# A story that changed during the build is written down by the build, as a record of its own with its text before and after; the text shows it, and a person merges.
printf '%s\n' '## Stories' '' 'Kind: feature, because the ticket names the word and the file.' '' '1. The file holds the word y.' > "$WORK/local-approved.md"
"$PY" -B "$STORIES" --repo "$LOCAL" approve local-change --file "$WORK/local-approved.md" >/dev/null 2>&1 || true
"$PY" -B "$DECISIONS" --repo "$LOCAL" story local-change --changed 1 --was "The file holds the word y." --now "The file holds the word the owner asked for." \
  --why "y is taken by another file." --by personas --said "Both personas picked x." >/dev/null 2>&1 || true
read_in "$LOCAL" local-change
local_land start local-change >/dev/null && local_land base local-change >/dev/null && polish_in "$LOCAL" local-change && local_land gate local-change >/dev/null && local_land read local-change --record "$(clean 1)" >/dev/null
local_land propose local-change --title "fix: x" --notes "$NOTES" >/dev/null
err=$(local_land land local-change --by agent 2>&1 || true)
out=$(local_land land local-change --by owner)
if grep -q "the request is not green (story 1 changed during the build: y is taken by another file.), so a person merges it" <<<"$err" \
  && [ "$(sed -n 1p "$LOCAL/.git/lem/tasks/local-change/pr.md")" = '**Not green.**' ] && [ "$(sed -n 3p "$LOCAL/.git/lem/tasks/local-change/pr.md")" = '- story 1 changed during the build: y is taken by another file.' ] \
  && grep -qxF -- '- story 1: was "The file holds the word y.", now "The file holds the word the owner asked for.". y is taken by another file. By the personas: Both personas picked x.' "$LOCAL/.git/lem/tasks/local-change/pr.md" \
  && [ ! -e "$LOCAL/.git/lem/tasks/local-change/story-changes.jsonl" ] \
  && [ "$(field 'd["pushed"]' <<<"$out")" = False ] && [ -f "$LOCAL/x.txt" ] && [ "$(git -C "$LOCAL" log -1 --format=%s main)" = "fix: local-change" ] && [ "$(status_in "$LOCAL" local-change)" = landed ]; then
  pass "a request with a changed story is not green: its text says so first and shows the change, with what the story was and is, and a person merges it whatever the settings say; with no remote the base branch is fast-forwarded in the checkout that holds it"
else
  fail "local landing: $err / $out"
fi
local_land clean local-change >/dev/null
# A choice that waits for the owner holds the proposal; one taken by timeout is not green, and a late answer that differs is said.
task_in "$LOCAL" waited-change w.txt w
read_in "$LOCAL" waited-change
local_land start waited-change >/dev/null && local_land base waited-change >/dev/null && polish_in "$LOCAL" waited-change && local_land gate waited-change >/dev/null && local_land read waited-change --record "$(clean 1)" >/dev/null
wdec() { "$PY" -B "$DECISIONS" --repo "$LOCAL" "$@"; }
wfile=$LOCAL/.git/lem/tasks/waited-change/decisions.jsonl
wdec log waited-change --what "The name of the file" --chose w.txt --why "The other files have one letter." --by lead >/dev/null
wdec ask waited-change "${CASE[@]}" --what "Where the word goes" --option "the first line" --option "the last line" --recommended "the first line" --why "A reader sees it at once." --said "The two personas split." >/dev/null
waiting=$(local_land propose waited-change --title "fix: w" --notes "$NOTES" 2>&1 || true)
past "$wfile" 2 && wdec timeout waited-change 2 >/dev/null
wdec ask waited-change "${CASE[@]}" --what "Tell the merchants" --option "send the email" --option "send nothing" --recommended "send nothing" --why "Nothing they see changes." --said "The two personas split." --irreversible person >/dev/null
forever=$(local_land propose waited-change --title "fix: w" --notes "$NOTES" 2>&1 || true)
wdec answer waited-change 3 --chose "send the email" --words "Yes, send it." --why "The merchants asked for it." >/dev/null
wdec ask waited-change "${CASE[@]}" --what "The case of the word" --option "lower case" --option "upper case" --recommended "lower case" --why "The test reads it so." --said "The two personas split." >/dev/null
past "$wfile" 4 && wdec timeout waited-change 4 >/dev/null && wdec answer waited-change 4 --chose "upper case" --words "Make it upper case." --why "The header is in upper case." >/dev/null
wdec answer waited-change 2 --chose "the first line" --why "The importer reads the first line." >/dev/null
# a choice the personas left unclear: the owner takes the recommended option in time
wdec ask waited-change "${CASE[@]}" --what "Which line holds the word" --option "the only line" --option "the second line" --recommended "the second line" --why "A header goes first." \
  --said "The two personas split." >/dev/null
wdec answer waited-change 5 --chose "the second line" >/dev/null
# the owner decides what none of the options says: an irreversible step that would otherwise wait for ever, and one more
wdec ask waited-change "${CASE[@]}" --what "Email the customers" --option "email all customers" --option "email nobody" --recommended "email nobody" --why "Nobody asked for it." \
  --said "The two personas split." --irreversible person >/dev/null
wdec answer waited-change 6 --instead "Email only the beta testers." --why "They asked to hear first." >/dev/null
wdec ask waited-change "${CASE[@]}" --what "The word's line ending" --option "a line break" --option "no line break" --recommended "a line break" --why "Every file ends so." \
  --said "The two personas split." >/dev/null
wdec answer waited-change 7 --instead "A line break, and a second line with the date." >/dev/null
instead_pending=$(wdec pending waited-change | field '[c["id"] for c in d["waiting"]]')
local_land propose waited-change --title "fix: w" --notes "$NOTES" >/dev/null
text=$LOCAL/.git/lem/tasks/waited-change/pr.md
agent=$(local_land land waited-change --by agent 2>&1 || true)
if grep -qF "choice 2 of waited-change waits for the owner (Where the word goes): a request is never proposed over an open question of the owner's" <<<"$waiting" \
  && grep -qF "decisions.py answer waited-change 2 --chose OPTION --words TEXT" <<<"$waiting" && grep -qF "decisions.py timeout waited-change 2" <<<"$waiting" \
  && grep -qF "choice 3 of waited-change waits for the owner (Tell the merchants)" <<<"$forever" && grep -qF "decisions.py answer waited-change 3 --chose OPTION --words TEXT" <<<"$forever" \
  && ! grep -qF "timeout waited-change 3" <<<"$forever" && [ "$(status_in "$LOCAL" waited-change)" = open ] \
  && [ "$(sed -n 1p "$text")" = '**Not green.**' ] \
  && [ "$(sed -n 3p "$text")" = "- choice 2 was taken by timeout (Where the word goes): \"the first line\", the recommended option, after the owner's wait of 15 minutes ended with no answer; the owner answered later with the same (the owner's reason: The importer reads the first line)" ] \
  && [ "$(sed -n 4p "$text")" = "- choice 4 was taken by timeout (The case of the word): \"lower case\", the recommended option, after the owner's wait of 15 minutes ended with no answer; the owner answered later with \"upper case\", which differs (the owner's words: \"Make it upper case.\"; the owner's reason: The header is in upper case)" ] \
  && [ -z "$(sed -n 5p "$text")" ] && [ "$instead_pending" = "[]" ] \
  && [ "$(grep '^## ' "$text" | tr '\n' '|')" = "## The request|## Stories|## Checks|## Decisions of the build|## Decisions|## Left open|## Worth a look|## Filed in the backlog|## Not done|" ] \
  && [ "$(sed -n '/^## Decisions of the build$/,/^## Decisions$/p' "$text" | grep '^- ')" = "- The name of the file: \"w.txt\", by the lead. The other files have one letter.
- Where the word goes: \"the first line\", by the timeout, after the owner's wait of 15 minutes. A reader sees it at once. The owner answered later with the same (the owner's reason: The importer reads the first line).
- Tell the merchants: \"send the email\", by the owner, over the recommended \"send nothing\" (recommended because: Nothing they see changes). The owner's words: \"Yes, send it.\" The owner's reason: The merchants asked for it.
- The case of the word: \"lower case\", by the timeout, after the owner's wait of 15 minutes. The test reads it so. The owner answered later with \"upper case\", which differs (the owner's words: \"Make it upper case.\"; the owner's reason: The header is in upper case).
- Which line holds the word: \"the second line\", by the owner, as recommended. A header goes first.
- Email the customers: \"Email only the beta testers.\", by the owner, none of the options; the recommended was \"email nobody\" (recommended because: Nobody asked for it). The owner's reason: They asked to hear first.
- The word's line ending: \"A line break, and a second line with the date.\", by the owner, none of the options; the recommended was \"a line break\" (recommended because: Every file ends so). The owner gave no reason." ] \
  && grep -qF "the request is not green (choice 2 was taken by timeout" <<<"$agent"; then
  pass "a request is never proposed over a choice that waits for the owner, irreversible or not; each choice taken by timeout is a line of its own that is not green, with a late answer, the same or not, and his own words and reason; an answered choice is no cause of not green by itself; a decision of the owner's that is none of the options settles its choice, also an irreversible one, so the request is proposed; and the text lists each decision of the record with who took it and its reason, the recommendation's reason never as the owner's"
else
  fail "decisions in the landing: $waiting / $forever / $agent / $(cat "$text" 2>/dev/null)"
fi
project --repo "$LOCAL" state waited-change dropped "the test is over" >/dev/null

# A choice the experts took is not green, while the owner was away or at the end of his wait: its line names
# their pick and both reasons. A timeout whose experts split takes the recommended option, as before.
task_in "$LOCAL" expert-change e.txt e
read_in "$LOCAL" expert-change
local_land start expert-change >/dev/null && local_land base expert-change >/dev/null && polish_in "$LOCAL" expert-change && local_land gate expert-change >/dev/null && local_land read expert-change --record "$(clean 1)" >/dev/null
efile=$LOCAL/.git/lem/tasks/expert-change/decisions.jsonl
# eask WHAT FIRST SECOND RECOMMENDED WHY: a choice for the owner that the personas left unclear
eask() { wdec ask expert-change "${CASE[@]}" --what "$1" --option "$2" --option "$3" --recommended "$4" --why "$5" --said "The two personas split." >/dev/null; }
# eadvise ID FABLE_PICK FABLE_WHY ASTRA_PICK ASTRA_WHY: both experts' advice on choice ID
eadvise() {
  wdec advise expert-change "$1" --expert fable --pick "$2" --why "$3" >/dev/null
  wdec advise expert-change "$1" --expert astra --pick "$4" --why "$5" >/dev/null
}
eask "Where the word goes" "the first line" "the last line" "the first line" "A reader sees it at once."
eadvise 1 "the last line" "A reader of the file looks at its end first." "the last line" "The importer reads the last line."
held=$(local_land propose expert-change --title "fix: e" --notes "$NOTES" 2>&1 || true)
wdec settle expert-change 1 --away >/dev/null
eask "The case of the word" "lower case" "upper case" "lower case" "The test reads it so."
eadvise 2 "upper case" "The header is in upper case." "upper case" "The other words of the header are in upper case."
past "$efile" 2 && wdec timeout expert-change 2 >/dev/null && wdec answer expert-change 2 --chose "lower case" --why "The test reads it so." >/dev/null
eask "The word's line ending" "a line break" "no line break" "a line break" "Every file ends so."
eadvise 3 "a line break" "Every file ends so." "no line break" "The importer reads the last byte."
past "$efile" 3 && wdec timeout expert-change 3 >/dev/null
eask "The name of the file" "e.txt" "word.txt" "word.txt" "A name says what the file holds."
eadvise 4 "word.txt" "A name says what the file holds." "word.txt" "Nobody guesses what e.txt holds."
wdec settle expert-change 4 --away >/dev/null
local_land propose expert-change --title "fix: e" --notes "$NOTES" >/dev/null
text=$LOCAL/.git/lem/tasks/expert-change/pr.md
agent=$(local_land land expert-change --by agent 2>&1 || true)
if grep -qF "choice 1 of expert-change waits for the owner (Where the word goes)" <<<"$held" \
  && grep -qF "\`decisions.py timeout expert-change 1\` takes the experts' shared pick, or the recommended option when they split" <<<"$held" \
  && [ "$(sed -n 1p "$text")" = '**Not green.**' ] \
  && [ "$(sed -n 3p "$text")" = "- choice 1 was taken by the experts (Where the word goes): \"the last line\", the option both picked, while the owner was away, before the wait ended. Fable: A reader of the file looks at its end first. Astra: The importer reads the last line" ] \
  && [ "$(sed -n 4p "$text")" = "- choice 2 was taken by the experts (The case of the word): \"upper case\", the option both picked, after the owner's wait of 15 minutes ended with no answer. Fable: The header is in upper case. Astra: The other words of the header are in upper case; the owner answered later with \"lower case\", which differs (the owner's reason: The test reads it so)" ] \
  && [ "$(sed -n 5p "$text")" = "- choice 3 was taken by timeout (The word's line ending): \"a line break\", the recommended option, after the owner's wait of 15 minutes ended with no answer" ] \
  && [ "$(sed -n 6p "$text")" = "- choice 4 was taken by the experts (The name of the file): \"word.txt\", the option both picked, while the owner was away, before the wait ended. Fable: A name says what the file holds. Astra: Nobody guesses what e.txt holds" ] \
  && [ -z "$(sed -n 7p "$text")" ] \
  && [ "$(sed -n '/^## Decisions of the build$/,/^## Decisions$/p' "$text" | grep '^- ')" = "- Where the word goes: \"the last line\", by the experts, the option both picked, while the owner was away; the recommended was \"the first line\". Fable: A reader of the file looks at its end first. Astra: The importer reads the last line.
- The case of the word: \"upper case\", by the experts, the option both picked, after the owner's wait of 15 minutes; the recommended was \"lower case\". Fable: The header is in upper case. Astra: The other words of the header are in upper case. The owner answered later with \"lower case\", which differs (the owner's reason: The test reads it so).
- The word's line ending: \"a line break\", by the timeout, after the owner's wait of 15 minutes. Every file ends so.
- The name of the file: \"word.txt\", by the experts, the option both picked, while the owner was away; it is also the recommended. Fable: A name says what the file holds. Astra: Nobody guesses what e.txt holds." ] \
  && grep -qF "the request is not green (choice 1 was taken by the experts" <<<"$agent" && [ "$(status_in "$LOCAL" expert-change)" = open ]; then
  pass "a choice the experts took, while the owner was away or at the end of his wait, is a line of its own that is not green, with their pick, both reasons and a late answer of his; the text lists it as taken by the experts; a timeout whose experts split takes the recommended option as before; and a request held by a choice that waits says what the end of the wait takes"
else
  fail "the experts' choices in the landing: $held / $agent / $(cat "$text" 2>/dev/null)"
fi
project --repo "$LOCAL" state expert-change dropped "the test is over" >/dev/null

# Approved stories in the landing: a story the build added or removed is not green, like a changed one; and the
# checks hold one line on the personas' read of the stories, from its event, with his approval.
lstories() { "$PY" -B "$STORIES" --repo "$LOCAL" "$@"; }
ldecide() { "$PY" -B "$DECISIONS" --repo "$LOCAL" "$@"; }
# polish_local SLUG: a polish pass that finds nothing to change, as a feature's gate needs one
polish_local() { polish_in "$LOCAL" "$1"; }
# to_open SLUG: the machine steps with a polish pass, a clean read and the proposal of a task of the local repository
to_open() {
  local_land start "$1" >/dev/null && local_land base "$1" >/dev/null && polish_local "$1" && local_land gate "$1" >/dev/null \
    && local_land read "$1" --record "$(clean 1)" >/dev/null && local_land propose "$1" --title "fix: $1" --notes "$NOTES" >/dev/null
}
approved_day() { "$PY" -c 'import json, sys; print(json.load(open(sys.argv[1]))["at"][:10])' "$LOCAL/.git/lem/tasks/$1/stories.json" 2>/dev/null || true; }
task_in "$LOCAL" story-departs d.txt d
tree=$(project --repo "$LOCAL" worktree-dir story-departs)
printf '%s\n' '## Stories' '' 'Kind: feature, because the file gets a word and a rule of its own.' '' '1. The file holds the word the owner asked for.' '2. The file has one line.' > "$WORK/approved.md"
# the read comes first, of the stories file that he then approves
read_digest=$(lstories digest story-departs --file "$WORK/approved.md" 2>/dev/null | field 'd["digest"]' 2>/dev/null || true)
project --repo "$LOCAL" log story-departs stories.read by=lem asked:=2 answered:=2 'families:=["opus", "sol"]' 'silent:=[]' stories:=2 flagged:=0 split:=false "digest=$read_digest" >/dev/null 2>&1 || true
lstories approve story-departs --file "$WORK/approved.md" >/dev/null 2>&1 || true
# shellcheck disable=SC2016
printf '%s\n' '# story-departs' '' '## Stories' '' 'Kind: feature, because the file gets a word and a rule of its own.' '' '1. The file holds the word the owner asked for.' \
  '   - test: `sh tests/story-departs.sh` in `tests/story-departs.sh`' '2. The file ends with a line break.' '   - no test: printf ends every line so.' '' '## Tasks' '' '1. The change.' \
  > "$tree/docs/plans/20261115-story-departs.md"
git -C "$tree" commit -q -am "docs: the stories as they are built"
unrecorded=$(local_land start story-departs >/dev/null && local_land base story-departs >/dev/null && local_land gate story-departs 2>&1 || true)
# a story that a choice of the build removes, once the choice is answered; and one the lead adds
ldecide ask story-departs "${CASE[@]}" --what "The one-line rule" --option "keep the rule" --option "no such rule" --recommended "keep the rule" --why "A reader counts on it." \
  --said "The two personas split." >/dev/null 2>&1 || true
early=$(ldecide story story-departs --removed 2 --was "The file has one line." --why "A second line holds the date now." --choice 1 2>&1 || true)
ldecide answer story-departs 1 --chose "no such rule" >/dev/null 2>&1 || true
ldecide story story-departs --removed 2 --was "The file has one line." --why "A second line holds the date now." --choice 1 >/dev/null 2>&1 || true
ldecide story story-departs --added 2 --now "The file ends with a line break." --why "The importer reads whole lines only." --by lead >/dev/null 2>&1 || true
polish_local story-departs 2>/dev/null && local_land gate story-departs >/dev/null 2>&1 && local_land read story-departs --record "$(clean 1)" >/dev/null 2>&1 \
  && local_land propose story-departs --title "fix: story-departs" --notes "$NOTES" >/dev/null 2>&1 || true
text=$LOCAL/.git/lem/tasks/story-departs/pr.md
agent=$(local_land land story-departs --by agent 2>&1 || true)
if grep -qF "story 2 of 20261115-story-departs.md says 'The file ends with a line break.', and the expected story 2 is 'The file has one line.'" <<<"$unrecorded" \
  && grep -qF "choice 1 is waits: a story changes after a choice that was answered or taken by timeout" <<<"$early" \
  && [ "$(sed -n 1p "$text" 2>/dev/null)" = '**Not green.**' ] \
  && [ "$(sed -n 3p "$text")" = '- story 2 was removed during the build: A second line holds the date now, after choice 1 (The one-line rule), where the owner took "no such rule"' ] \
  && [ "$(sed -n 4p "$text")" = '- story 2 was added during the build: The importer reads whole lines only.' ] \
  && grep -qxF -- '- story 2: removed, was "The file has one line.". A second line holds the date now, after choice 1 (The one-line rule), where the owner took "no such rule".' "$text" \
  && grep -qxF -- '- story 2: added, "The file ends with a line break.". The importer reads whole lines only. By the lead.' "$text" \
  && [ -n "$(approved_day story-departs)" ] \
  && grep -qxF -- "- the stories were read by 2 of 2 personas asked, two model families (opus, sol); nobody confused; the owner approved them on $(approved_day story-departs)" "$text" \
  && grep -qxF -- "- the stories changed after the personas' read, by a change of the build, and the change was not read" "$text" \
  && grep -qF "the request is not green (story 2 was removed during the build" <<<"$agent"; then
  pass "a story a choice of the build removed and one the lead added are not green, each with its line first, what it was or is, its reason and the choice that led to it; a story changes only after its choice is answered; the gate refuses the plan until both are recorded; and the checks say that two model families read the stories, when he approved them, and that a change of the build came after the read"
else
  fail "an added and a removed story in the landing: $unrecorded / $early / $agent / $(cat "$text" 2>/dev/null)"
fi
project --repo "$LOCAL" state story-departs dropped "the test is over" >/dev/null
# A feature is not proposed without a read of its stories, nor over a doubt of the personas that no approval of his followed.
task_in "$LOCAL" read-doubt r.txt r
tree=$(project --repo "$LOCAL" worktree-dir read-doubt)
printf '%s\n' '## Stories' '' 'Kind: feature, because the ticket names the word and the file.' '' '1. The file holds the word the owner asked for.' > "$WORK/doubt.md"
plan_digest=$(lstories digest read-doubt 2>/dev/null | field 'd["digest"]' 2>/dev/null || true)
local_land start read-doubt >/dev/null && local_land base read-doubt >/dev/null && polish_local read-doubt && local_land gate read-doubt >/dev/null && local_land read read-doubt --record "$(clean 1)" >/dev/null
unread_feature=$(local_land propose read-doubt --title "fix: r" --notes "$NOTES" 2>&1 || true)
project --repo "$LOCAL" log read-doubt stories.read by=lead asked:=2 answered:=2 'families:=["opus", "sol"]' 'silent:=[]' stories:=1 flagged:=0 split:=true "digest=$plan_digest" >/dev/null 2>&1 || true
split_unseen=$(local_land propose read-doubt --title "fix: r" --notes "$NOTES" 2>&1 || true)
freeze_split=$(lstories approve read-doubt --read 2>&1 || true)
project --repo "$LOCAL" log read-doubt stories.read by=lead asked:=2 answered:=2 'families:=["opus"]' 'silent:=[]' stories:=1 flagged:=1 split:=false "digest=$plan_digest" >/dev/null 2>&1 || true
flag_unseen=$(local_land propose read-doubt --title "fix: r" --notes "$NOTES" 2>&1 || true)
# the newest read: partial, one story flagged, the families split, and of other stories than he then approved
project --repo "$LOCAL" log read-doubt stories.read by=lem asked:=3 answered:=2 'families:=["opus", "sol"]' \
  'silent:=[{"name": "the accountant, sol", "why": "the model was at capacity"}]' stories:=1 flagged:=1 split:=true "digest=$read_digest" >/dev/null 2>&1 || true
lstories approve read-doubt --file "$WORK/doubt.md" >/dev/null 2>&1 || true
local_land propose read-doubt --title "fix: r" --notes "$NOTES" >/dev/null 2>&1 || true
text=$LOCAL/.git/lem/tasks/read-doubt/pr.md
if grep -qF "read-doubt is a feature, and the event log has no \`stories.read\`" <<<"$unread_feature" && grep -qF 'stages/new.md' <<<"$unread_feature" \
  && grep -qF "the newest read of read-doubt's stories found a split between the two families, and no approval of the owner's came after it" <<<"$split_unseen" \
  && grep -qF "found 1 flagged story, and no approval of the owner's came after it" <<<"$flag_unseen" && grep -qF "stories.py approve read-doubt --file FILE" <<<"$flag_unseen" \
  && grep -qF "the newest read of read-doubt's stories found a split between the families: the stories wait for the owner, and only the owner's approval freezes them" <<<"$freeze_split" \
  && [ "$(sed -n 1p "$text" 2>/dev/null | cut -c1-10)" = '**Green.**' ] \
  && grep -qxF -- "- the stories were read by 2 of 3 personas asked, two model families (opus, sol); 1 of 1 story flagged; the two families split; no answer from the accountant, sol (the model was at capacity); the owner approved them on $(approved_day read-doubt)" "$text" \
  && grep -qxF -- "- the stories changed after the personas' read, by the owner's approval 1, and the change was not read" "$text"; then
  pass "a feature with no read of its stories is not proposed, nor one whose newest read flagged a story or split the families with no approval of his after it; a partial read counts and says who did not answer and why; and stories he changed after the read are one line that is no cause of not green"
else
  fail "the read before a proposal: $unread_feature / $split_unseen / $freeze_split / $flag_unseen / $(cat "$text" 2>/dev/null)"
fi
project --repo "$LOCAL" state read-doubt dropped "the test is over" >/dev/null
# The read is compared with the stories as they are now, and the history of story changes stays in the pull request:
# approval 1, the personas change its story, a clean read of the changed story, then his approval of it.
task_in "$LOCAL" after-change a.txt a
tree=$(project --repo "$LOCAL" worktree-dir after-change)
printf '%s\n' '## Stories' '' 'Kind: feature, because the ticket names the word and the file.' '' '1. The file holds the word y.' > "$WORK/first.md"
printf '%s\n' '## Stories' '' 'Kind: feature, because the ticket names the word and the file.' '' '1. The file holds the word the owner asked for.' > "$WORK/changed.md"
lstories approve after-change --file "$WORK/first.md" >/dev/null 2>&1 || true
ldecide story after-change --changed 1 --was "The file holds the word y." --now "The file holds the word the owner asked for." --why "y is taken by another file." \
  --by personas --said "Both personas picked the owner's word." >/dev/null 2>&1 || true
digest=$(lstories digest after-change 2>/dev/null | field 'd["digest"]' 2>/dev/null || true)
project --repo "$LOCAL" log after-change stories.read by=lem asked:=2 answered:=2 'families:=["opus", "sol"]' 'silent:=[]' stories:=1 flagged:=0 split:=false "digest=$digest" >/dev/null 2>&1 || true
to_open after-change || true
text=$LOCAL/.git/lem/tasks/after-change/pr.md
cp "$text" "$WORK/first-pr.md" 2>/dev/null || : > "$WORK/first-pr.md"
# he approves the changed story; the proposal is made again
project --repo "$LOCAL" state after-change landing "he approved the changed story" >/dev/null
lstories approve after-change --file "$WORK/changed.md" >/dev/null 2>&1 || true
local_land propose after-change --title "fix: a" --notes "$NOTES" >/dev/null 2>&1 || true
history_line='- story 1: was "The file holds the word y.", now "The file holds the word the owner asked for.". y is taken by another file. By the personas: Both personas picked the owner'"'"'s word.'
if [ "$(sed -n 1p "$WORK/first-pr.md")" = '**Not green.**' ] && [ "$(sed -n 3p "$WORK/first-pr.md")" = '- story 1 changed during the build: y is taken by another file.' ] \
  && grep -qxF -- "$history_line" "$WORK/first-pr.md" && ! grep -q "after the personas' read" "$WORK/first-pr.md" \
  && [ "$(sed -n 1p "$text" | cut -c1-10)" = '**Green.**' ] \
  && grep -qxF -- "$history_line Approved by the owner afterwards (approval 2)." "$text" \
  && ! grep -qiwE 'you|your' "$WORK/first-pr.md" "$text" \
  && grep -qxF -- "- the stories were read by 2 of 2 personas asked, two model families (opus, sol); nobody confused; the owner approved them on $(approved_day after-change)" "$text" \
  && ! grep -q "after the personas' read" "$text"; then
  pass "a read of the stories as a recorded change made them is the read of the stories now, and no line says otherwise; a change he approved afterwards stays in the pull request with its reason and the personas' answer, marked as approved by him, and is no cause of not green"
else
  fail "the read and the history after a later approval: $(cat "$WORK/first-pr.md") / $(cat "$text" 2>/dev/null)"
fi
project --repo "$LOCAL" state after-change dropped "the test is over" >/dev/null
# The rare path: the lead ran the read with one model family, nobody was confused, and there is no approval; a scout's report is named.
task_in "$LOCAL" ticket-word t.txt t
tree=$(project --repo "$LOCAL" worktree-dir ticket-word)
digest=$(lstories digest ticket-word 2>/dev/null | field 'd["digest"]' 2>/dev/null || true)
read_with() { project --repo "$LOCAL" log ticket-word stories.read "$@" 2>&1 || true; }
bad_by=$(read_with by=owner asked:=2 answered:=2 'families:=["opus"]' 'silent:=[]' stories:=1 flagged:=0 split:=false "digest=$digest")
bad_one=$(read_with by=lead asked:=1 answered:=1 'families:=["opus"]' 'silent:=[]' stories:=1 flagged:=0 split:=false "digest=$digest")
bad_none=$(read_with by=lead asked:=2 answered:=0 'families:=["opus"]' 'silent:=[{"name": "a", "why": "b"}]' stories:=1 flagged:=0 split:=false "digest=$digest")
bad_more=$(read_with by=lead asked:=2 answered:=3 'families:=["opus"]' 'silent:=[]' stories:=1 flagged:=0 split:=false "digest=$digest")
bad_quiet=$(read_with by=lead asked:=3 answered:=2 'families:=["opus"]' 'silent:=[]' stories:=1 flagged:=0 split:=false "digest=$digest")
bad_families=$(read_with by=lead asked:=2 answered:=2 families=opus 'silent:=[]' stories:=1 flagged:=0 split:=false "digest=$digest")
bad_flagged=$(read_with by=lead asked:=2 answered:=2 'families:=["opus"]' 'silent:=[]' stories:=1 flagged:=2 split:=false "digest=$digest")
bad_split=$(read_with by=lead asked:=2 answered:=2 'families:=["opus"]' 'silent:=[]' stories:=1 flagged:=0 split:=true "digest=$digest")
bad_digest=$(read_with by=lead asked:=2 answered:=2 'families:=["opus"]' 'silent:=[]' stories:=1 flagged:=0 split:=false digest=abc)
bad_missing=$(read_with by=lead asked:=2 answered:=2 'families:=["opus"]' stories:=1 flagged:=0 split:=false "digest=$digest")
project --repo "$LOCAL" log ticket-word stories.read by=lead asked:=2 answered:=2 'families:=["opus"]' 'silent:=[]' stories:=1 flagged:=0 split:=false "digest=$digest" >/dev/null 2>&1 || true
# the lead freezes what the personas read: another text is refused, the plan's own stories are kept with `by: read`
printf '%s\n' '## Stories' '' 'Kind: feature, because the ticket names the word and the file.' '' '1. The file holds another word.' > "$WORK/other.md"
freeze_other=$(lstories approve ticket-word --file "$WORK/other.md" --read 2>&1 || true)
lstories approve ticket-word --read >/dev/null 2>&1 || true
frozen=$("$PY" -c 'import json, sys; d = json.load(open(sys.argv[1])); print((d["by"], d["number"]))' "$LOCAL/.git/lem/tasks/ticket-word/stories.json" 2>&1 || true)
recorded=$(ldecide story ticket-word --changed 1 --was "Not the story." --now "x" --why "w" --by lead 2>&1 || true)
echo '1. t.txt does not exist on the base branch (git ls-files).' > "$LOCAL/.git/lem/tasks/ticket-word/scout.md"
to_open ticket-word || true
text=$LOCAL/.git/lem/tasks/ticket-word/pr.md
if [ "$(sed -n 1p "$text" 2>/dev/null | cut -c1-10)" = '**Green.**' ] \
  && grep -qxF -- "- the stories were read by 2 of 2 personas asked, one model family (opus); nobody confused; the build started with no wait for the owner" "$text" \
  && ! grep -q "after the personas' read" "$text" \
  && grep -qxF -- "- the stories were written from the scout's facts of the code, read before the interview" "$text" && ! grep -qF "$LOCAL" "$text" \
  && grep -q "by is lem, when Lem ran the read" <<<"$bad_by" && grep -q "a read asks two personas at the least" <<<"$bad_one" \
  && grep -q "a read in which nobody answered has families:='\[\]'" <<<"$bad_none" && grep -q "answered is at most asked" <<<"$bad_more" \
  && grep -q "silent names each source that did not, with why" <<<"$bad_quiet" \
  && grep -q "families is the list of the model families that answered" <<<"$bad_families" && grep -q "no more stories flagged than it read" <<<"$bad_flagged" \
  && grep -q "a split is between two model families, and families names one" <<<"$bad_split" && grep -q "digest is the twelve characters" <<<"$bad_digest" \
  && grep -q "stories.read takes by=lem|lead asked:=N answered:=N" <<<"$bad_missing" \
  && [ "$(grep -c '"event": "stories.read", "task": "ticket-word"' "$LOCAL/.git/lem/events.jsonl")" = 1 ] \
  && grep -qF -- "--read freezes the plan's own stories, the ones the read named: it takes no --file" <<<"$freeze_other" \
  && [ "$frozen" = "('read', 1)" ] && grep -qF "story 1 is 'The file holds the word the owner asked for.' after every earlier change" <<<"$recorded"; then
  pass "a read by the lead with one model family in which nobody was confused is one line of the checks, which says the build did not wait for him, and the scout's facts are named with no path of this machine; a read's event without its form, with fewer than two personas asked, with nobody or more than were asked answering, or with a missing source unnamed is refused, and nothing is written for it; the lead freezes the plan's stories the read named, with no file of other stories, and from then on a change of them has its record, while the line still says the build did not wait for him"
else
  fail "the read of the rare path: $freeze_other / $frozen / $recorded / $bad_by / $bad_one / $bad_none / $bad_more / $bad_quiet / $bad_families / $bad_flagged / $bad_split / $bad_digest / $bad_missing / $(cat "$text" 2>/dev/null)"
fi
# A read freezes only the first contract of a task: a second clean read of other stories does not replace the frozen
# ones, and a read does not replace his own approval, whose kind is his.
other_digest=$(lstories digest ticket-word --file "$WORK/other.md" 2>/dev/null | field 'd["digest"]' 2>/dev/null || true)
project --repo "$LOCAL" log ticket-word stories.read by=lead asked:=2 answered:=2 'families:=["opus"]' 'silent:=[]' stories:=1 flagged:=0 split:=false "digest=$other_digest" >/dev/null 2>&1 || true
refile=$(lstories approve ticket-word --read --file "$WORK/other.md" 2>&1 || true)
refreeze=$(lstories approve ticket-word --read 2>&1 || true)
printf '%s\n' '## Stories' '' 'Kind: correction, because it is one sentence.' '' '1. The file holds the word the owner asked for.' > "$WORK/as-correction.md"
correction_digest=$(lstories digest after-change --file "$WORK/as-correction.md" 2>/dev/null | field 'd["digest"]' 2>/dev/null || true)
project --repo "$LOCAL" log after-change stories.read by=lead asked:=2 answered:=2 'families:=["opus"]' 'silent:=[]' stories:=1 flagged:=0 split:=false "digest=$correction_digest" >/dev/null 2>&1 || true
over_his=$(lstories approve after-change --read 2>&1 || true)
over_his_file=$(lstories approve after-change --read --file "$WORK/as-correction.md" 2>&1 || true)
kept_contracts=$("$PY" -c 'import json, sys; print([(json.load(open(f))["number"], json.load(open(f))["by"], json.load(open(f))["kind"]) for f in sys.argv[1:]])' \
  "$LOCAL/.git/lem/tasks/ticket-word/stories.json" "$LOCAL/.git/lem/tasks/after-change/stories.json" 2>&1 || true)
if grep -qF "ticket-word has approval 1 of its stories already (by read): a read freezes only the first contract" <<<"$refreeze" \
  && grep -qF "A story changes through its record, \`decisions.py story ticket-word ...\`, and the kind only through the owner's own approval" <<<"$refreeze" \
  && grep -qF "after-change has approval 2 of its stories already (by owner): a read freezes only the first contract" <<<"$over_his" \
  && grep -qF "it takes no --file" <<<"$over_his_file" && grep -qF "it takes no --file" <<<"$refile" \
  && [ "$kept_contracts" = "[(1, 'read', 'feature'), (2, 'owner', 'feature')]" ]; then
  pass "a read freezes only the first contract of a task: a second clean read of other stories freezes nothing over a read's contract, and a read never replaces his approval or its kind"
else
  fail "a second freeze by a read: $refile / $refreeze / $over_his / $over_his_file / $kept_contracts"
fi
project --repo "$LOCAL" state ticket-word dropped "the test is over" >/dev/null
# A read in which nobody answered is written down too, and started once more: after the first one the
# request is not proposed and the rare path's freeze is refused; after the second the build goes on,
# the freeze takes the stories, and the request is not green for it, with the reason first.
task_in "$LOCAL" nobody-read n.txt n
tree=$(project --repo "$LOCAL" worktree-dir nobody-read)
digest=$(lstories digest nobody-read 2>/dev/null | field 'd["digest"]' 2>/dev/null || true)
quiet='silent:=[{"name": "the buyer, opus", "why": "the model was at capacity"}, {"name": "the clerk, opus", "why": "the model was at capacity"}]'
empty_with() { project --repo "$LOCAL" log nobody-read stories.read by=lead asked:=2 answered:=0 "$@" stories:=1 split:=false "digest=$digest" 2>&1 || true; }
empty_family=$(empty_with 'families:=["opus"]' "$quiet" flagged:=0)
empty_unnamed=$(empty_with 'families:=[]' 'silent:=[{"name": "the buyer, opus", "why": "the model was at capacity"}]' flagged:=0)
empty_flagged=$(empty_with 'families:=[]' "$quiet" flagged:=1)
first_empty=$(empty_with 'families:=[]' "$quiet" flagged:=0)
local_land start nobody-read >/dev/null && local_land base nobody-read >/dev/null && polish_local nobody-read && local_land gate nobody-read >/dev/null \
  && local_land read nobody-read --record "$(clean 1)" >/dev/null
once=$(local_land propose nobody-read --title "fix: n" --notes "$NOTES" 2>&1 || true)
freeze_once=$(lstories approve nobody-read --read 2>&1 || true)
second_empty=$(empty_with 'families:=[]' "$quiet" flagged:=0)
freeze_twice=$(lstories approve nobody-read --read 2>&1 || true)
local_land propose nobody-read --title "fix: n" --notes "$NOTES" >/dev/null 2>&1 || true
text=$LOCAL/.git/lem/tasks/nobody-read/pr.md
twice_agent=$(local_land land nobody-read --by agent 2>&1 || true)
if grep -q "a read in which nobody answered has families:='\[\]'" <<<"$empty_family" && grep -q "a read in which nobody answered has families:='\[\]'" <<<"$empty_unnamed" \
  && grep -q "a read in which nobody answered has families:='\[\]'" <<<"$empty_flagged" \
  && grep -q '"event": "stories.read"' <<<"$first_empty" && grep -q '"event": "stories.read"' <<<"$second_empty" \
  && grep -qF "nobody answered the newest read of nobody-read's stories: it is started once more" <<<"$once" \
  && grep -qF "nobody answered the newest read of nobody-read's stories: it is started once more" <<<"$freeze_once" \
  && grep -q '"by": "read"' <<<"$freeze_twice" \
  && [ "$(sed -n 1p "$text" 2>/dev/null)" = '**Not green.**' ] \
  && [ "$(sed -n 3p "$text")" = "- the stories were not read: the personas' read was started twice and nobody answered; no answer from the buyer, opus (the model was at capacity); no answer from the clerk, opus (the model was at capacity)" ] \
  && grep -qxF -- "- the stories were not read by the personas: 2 reads in a row, and none of the 2 personas asked answered; the build started with no wait for the owner" "$text" \
  && grep -qF "the request is not green (the stories were not read" <<<"$twice_agent"; then
  pass "a read in which nobody answered is written down with no family and each source named, and started once more: after one the request is not proposed and the stories are not frozen; after the second the build goes on, the stories are frozen as read, and the request is not green with that reason first"
else
  fail "a read nobody answered, twice: $empty_family / $empty_unnamed / $empty_flagged / $first_empty / $once / $freeze_once / $second_empty / $freeze_twice / $twice_agent / $(cat "$text" 2>/dev/null)"
fi
project --repo "$LOCAL" state nobody-read dropped "the test is over" >/dev/null
# A plan's kind is never correction: one plain change is a small change, whose one story is in the task directory
# and which has no plan. A plan that says `Kind: correction`, as a lead of the rare path or of a night could write
# it, is refused by the stories and by every step of the landing that reads them, with or without Lem's approval of
# a correction in the owner's name, and the refusal names the small change.
task_in "$LOCAL" one-word o.txt o
tree=$(project --repo "$LOCAL" worktree-dir one-word)
"$PY" -c 'import sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(s.replace("Kind: feature, because the ticket names the word and the file.", "Kind: correction, because the request is one sentence."))' "$tree/docs/plans/20261115-one-word.md"
git -C "$tree" commit -q -am "docs: the plan of a correction"
as_plan=$(lstories show one-word 2>&1 || true)
local_land start one-word >/dev/null && local_land base one-word >/dev/null
as_polish=$(local_land polish one-word 2>&1 || true)
as_gate=$(local_land gate one-word 2>&1 || true)
printf '%s\n' '## Stories' '' 'Kind: correction, because the request is one sentence.' '' '1. The file holds the word the owner asked for.' > "$WORK/correction.md"
lstories approve one-word --file "$WORK/correction.md" --correction >/dev/null 2>&1 || true
approved_plan=$(lstories red one-word 2>&1 || true)
never="20261115-one-word.md says \`Kind: correction\`, and a plan's kind is never correction"
if grep -qF "$never" <<<"$as_plan" && grep -qF "a small change, whose one story is \`stories.md\` in the task directory" <<<"$as_plan" \
  && grep -qF "Kind: feature, because" <<<"$as_plan" && grep -qF "$never" <<<"$as_polish" && grep -qF "$never" <<<"$as_gate" && grep -qF "$never" <<<"$approved_plan" \
  && [ "$(kept_in "$LOCAL" one-word gated)" = None ] && [ "$(kept_in "$LOCAL" one-word polish)" = None ] \
  && ! grep -q '"event": "gate.start", "task": "one-word"' "$LOCAL/.git/lem/events.jsonl"; then
  pass "a plan that says Kind: correction is refused by the stories, the polish pass and the gate, also with Lem's approval of a correction in the owner's name, and the refusal names the small change, which has no plan, and the feature's Kind line"
else
  fail "a plan of a correction: $as_plan / $as_polish / $as_gate / $approved_plan"
fi
project --repo "$LOCAL" state one-word dropped "the test is over" >/dev/null
# The owner's word to skip the personas' read, when every story names only the developer: the record of his word and
# his approval after it let a feature land with no read, green, with one line that says so. Lem's word is not his;
# a feature with no read and no such record is refused as before; and on the rare path the read always runs.
# skip_read SLUG BY: the word to skip the personas' read, in the form the landing reads
skip_read() { ldecide log "$1" --by "$2" --what "the personas' read of the stories" --chose "no read: the stories name only the developer" --why "y" 2>&1 || true; }
# checked_local SLUG: the machine steps, a polish pass and a clean read, up to the proposal
checked_local() {
  local_land start "$1" >/dev/null && local_land base "$1" >/dev/null && polish_local "$1" && local_land gate "$1" >/dev/null \
    && local_land read "$1" --record "$(clean 1)" >/dev/null
}
printf '%s\n' '## Stories' '' 'Kind: feature, because the ticket names the word and the file.' '' '1. The file holds the word the owner asked for.' > "$WORK/mine.md"
task_in "$LOCAL" only-me m.txt m
skip_read only-me owner >/dev/null
checked_local only-me
unapproved=$(local_land propose only-me --title "feat: m" --notes "$NOTES" 2>&1 || true)
lstories approve only-me --file "$WORK/mine.md" >/dev/null 2>&1 || true
local_land propose only-me --title "feat: m" --notes "$NOTES" >/dev/null 2>&1 || true
text=$LOCAL/.git/lem/tasks/only-me/pr.md
skipped_day=$("$PY" -c 'import json, sys; print(json.loads(open(sys.argv[1]).readline())["at"][:10])' "$LOCAL/.git/lem/tasks/only-me/decisions.jsonl" 2>/dev/null || true)
if grep -qF "the owner's word to skip the personas' read of only-me's stories is on record, and no approval of the owner's came after it" <<<"$unapproved" \
  && grep -qF "stories.py approve only-me --file FILE" <<<"$unapproved" \
  && [ "$(sed -n 1p "$text" 2>/dev/null | cut -c1-10)" = '**Green.**' ] && [ -n "$skipped_day" ] \
  && grep -qxF -- "- the stories: not read by the personas, on the owner's word ($skipped_day); the owner approved them" "$text" \
  && ! grep -q 'the stories were read by\|no read by the personas is on record' "$text" \
  && grep -q '"event": "proposed", "task": "only-me".*"green": true' "$LOCAL/.git/lem/events.jsonl"; then
  pass "a feature whose stories name only the developer lands with no read on his recorded word and his approval after it: green, with the line that the personas did not read them on his word and that he approved them; his word with no approval after it is refused"
else
  fail "the owner's skip of the read: $unapproved / $skipped_day / $(cat "$text" 2>/dev/null)"
fi
project --repo "$LOCAL" state only-me dropped "the test is over" >/dev/null
task_in "$LOCAL" no-word w.txt w
checked_local no-word
lstories approve no-word --file "$WORK/mine.md" >/dev/null 2>&1 || true
no_word=$(local_land propose no-word --title "feat: w" --notes "$NOTES" 2>&1 || true)
skip_read no-word lem >/dev/null
lem_word=$(local_land propose no-word --title "feat: w" --notes "$NOTES" 2>&1 || true)
if grep -qF "no-word is a feature, and the event log has no \`stories.read\`" <<<"$no_word" \
  && grep -qF "decisions.py log no-word --by owner --what \"the personas' read of the stories\" --chose \"no read: the stories name only the developer\"" <<<"$no_word" \
  && grep -qF "no-word is a feature, and the event log has no \`stories.read\`" <<<"$lem_word" \
  && [ ! -e "$LOCAL/.git/lem/tasks/no-word/pr.md" ]; then
  pass "a feature with his approval and no read is refused when no word of his to skip the read is on record, and a word of Lem's in the same form is no such word"
else
  fail "a feature with no read and no word of his: $no_word / $lem_word"
fi
project --repo "$LOCAL" state no-word dropped "the test is over" >/dev/null
task_in "$LOCAL" rare-word r2.txt r
skip_read rare-word owner >/dev/null
project --repo "$LOCAL" state rare-word building "the lead writes the plan" "lead: builder" >/dev/null
lstories approve rare-word --file "$WORK/mine.md" >/dev/null 2>&1 || true
project --repo "$LOCAL" state rare-word ready "the report is written" >/dev/null
checked_local rare-word
approved_late=$(local_land propose rare-word --title "feat: r" --notes "$NOTES" 2>&1 || true)
skip_read rare-word owner >/dev/null
lstories approve rare-word --file "$WORK/mine.md" >/dev/null 2>&1 || true
said_late=$(local_land propose rare-word --title "feat: r" --notes "$NOTES" 2>&1 || true)
if grep -qF "a lead of rare-word started before the owner's approval that came after the word to skip the personas' read" <<<"$approved_late" \
  && grep -qF "on the rare path the read always runs" <<<"$approved_late" && grep -qF "stages/plan.md" <<<"$approved_late" \
  && grep -qF "a lead of rare-word started before the owner's word to skip the personas' read" <<<"$said_late" \
  && [ ! -e "$LOCAL/.git/lem/tasks/rare-word/pr.md" ]; then
  pass "on the rare path his word to skip the read is refused: a lead that started before his word, or before his approval after it, wrote the stories, and the personas read them"
else
  fail "a skip of the read on the rare path: $approved_late / $said_late"
fi
project --repo "$LOCAL" state rare-word dropped "the test is over" >/dev/null
# The polish pass: after the task's own work and before the machine checks, a fresh builder takes out
# what the change left behind, and the script checks what it committed. Here the test is the builder.
task_in "$LOCAL" polish-me p.txt p
tree=$(project --repo "$LOCAL" worktree-dir polish-me)
pdir=$LOCAL/.git/lem/tasks/polish-me
# the lead's change leaves a false comment, a debug line and a name nothing uses
printf '%s\n' '# writes q into p.txt' 'echo "debug: here" >&2' 'unused=1' 'echo p > p.txt' > "$tree/tool.sh"
git -C "$tree" add -A && git -C "$tree" commit -q -m "feat: the tool"
lead_tip=$(git -C "$tree" rev-parse HEAD)
echo '- docs/guide.md: says nothing of p.txt' > "$pdir/outside.md"
echo '## Outside defects' > "$pdir/report.md"
local_land start polish-me >/dev/null && local_land base polish-me >/dev/null
no_pass=$(local_land gate polish-me 2>&1 || true)
first=$(local_land polish polish-me)
echo '# writes p into p.txt' > "$tree/tool.sh"
dirty=$(local_land polish polish-me --done 2>&1 || true)
echo 'echo p > p.txt' >> "$tree/tool.sh" && git -C "$tree" commit -q -am "refactor: the tool says what it writes, and nothing else"
started=$(local_land gate polish-me 2>&1 || true)
again=$(local_land polish polish-me)
if grep -qF "polish-me is a feature, and no polish pass is on record for this landing: \`land.py polish polish-me\` starts it" <<<"$no_pass" \
  && [ "$(field '(d["kind"], d["done"], d["before"], d["range"].split("..")[1], d["commits"], d["plan"].endswith("docs/plans/20261115-polish-me.md"), d["report"], d["outside"], d["backlog"], d["frozen"])' <<<"$first")" \
  = "('feature', False, '$lead_tip', '$lead_tip', ['$(git -C "$tree" rev-parse --short "$lead_tip") feat: the tool', '$(git -C "$tree" log -1 --format='%h %s' "$lead_tip~1")'], True, '$pdir/report.md', '$pdir/outside.md', 'docs/backlog', ['tests/polish-me.sh', 'docs/plans/20261115-polish-me.md'])" ] \
  && [ "$(field '(d["before"], d["range"])' <<<"$again")" = "$(field '(d["before"], d["range"])' <<<"$first")" ] && [ "$(kept_in "$LOCAL" polish-me polish)" = "{'before': '$lead_tip', 'done': False}" ]; then
  pass "a feature's gate waits for the polish pass; polish prints the range of the task's own commits from the base, the plan, the report, the interview's outside.md, the backlog folder and the files the pass may not change, and keeps the tip it starts at, also when it is started again after the builder's first commit"
else
  fail "polish: $no_pass / $first / $again"
fi
if [ "$(grep '"event": "polish.start", "task": "polish-me"' "$LOCAL/.git/lem/events.jsonl" | field 'd["before"]' 2>&1)" = "${lead_tip:0:9}" ]; then
  pass "polish logs polish.start once, with the tip the pass starts at, and not again when it is started a second time before --done"
else
  fail "polish.start: $(grep '"polish.start"' "$LOCAL/.git/lem/events.jsonl")"
fi
# What --done refuses: a worktree with changes, a story's test changed, stories' tests that no longer hold.
echo '# and a note' >> "$tree/tests/polish-me.sh" && git -C "$tree" commit -q -am "test: a note"
frozen=$(local_land polish polish-me --done 2>&1 || true)
git -C "$tree" revert --no-edit HEAD >/dev/null
echo q > "$tree/p.txt" && git -C "$tree" commit -q -am "refactor: the word"
broken=$(local_land polish polish-me --done 2>&1 || true)
git -C "$tree" revert --no-edit HEAD >/dev/null
mkdir -p "$tree/docs/backlog" && printf '%s\n' '---' 'worth: later' 'where: docs/guide.md' 'added: 2026-11-16' '---' '# The guide says nothing of p.txt' > "$tree/docs/backlog/the-guide-says-nothing-of-p-txt.md"
git -C "$tree" add -A && git -C "$tree" commit -q -m "docs(backlog): the guide says nothing of p.txt"
done_out=$(local_land polish polish-me --done)
after_tip=$(git -C "$tree" rev-parse HEAD)
twice=$(local_land polish polish-me --done 2>&1 || true)
if grep -qF "the worktree has changes nobody committed" <<<"$dirty" && grep -qF "the polish pass started at $(git -C "$tree" rev-parse --short=9 "$lead_tip") and is not done" <<<"$started" \
  && grep -qF "the polish pass changed what it may not: tests/polish-me.sh (by " <<<"$frozen" \
  && grep -qF "after the polish pass the stories' tests do not hold" <<<"$broken" \
  && [ "$(field '(d["before"], d["after"], len(d["commits"]), d["filed"], d["stories"]["ok"])' <<<"$done_out")" = "('$lead_tip', '$after_tip', 6, ['docs/backlog/the-guide-says-nothing-of-p-txt.md'], True)" ] \
  && grep -qF '"event": "polish", "task": "polish-me", "before": "'"${lead_tip:0:9}"'", "after": "'"${after_tip:0:9}"'", "commits": 6, "filed": ["docs/backlog/the-guide-says-nothing-of-p-txt.md"]' "$LOCAL/.git/lem/events.jsonl" \
  && grep -qF "the polish pass of this landing is done already" <<<"$twice" && [ "$(head -1 "$tree/tool.sh")" = '# writes p into p.txt' ]; then
  pass "polish --done refuses a worktree with changes, a pass that changed a story's test file, and one after which the stories' tests no longer hold; otherwise it runs them, logs one polish event with the tips, the commits and the items filed, and a pass is done once"
else
  fail "polish --done: $dirty / $started / $frozen / $broken / $done_out / $twice"
fi
# The gate: the pass is on the tip it checks while the commits after it are on top, and a rebase by `base` keeps it.
gated=$(local_land gate polish-me | field 'd["polish"]["after"]')
echo '# a fix' >> "$tree/tool.sh" && git -C "$tree" commit -q -am "fix: what a review found"
on_top=$(status_of local_land gate polish-me)
git -C "$tree" reset -q --hard "$after_tip~1" && echo 'echo p > p.txt' > "$tree/tool.sh" && git -C "$tree" commit -q -am "refactor: written again"
rewritten=$(local_land gate polish-me 2>&1 || true)
git -C "$tree" reset -q --hard "$after_tip" && echo '# a fix' >> "$tree/tool.sh" && git -C "$tree" commit -q -am "fix: what a review found"
echo late > "$LOCAL/polish-late.txt" && git -C "$LOCAL" add polish-late.txt && git -C "$LOCAL" commit -q -m "chore: a late file"
local_land base polish-me >/dev/null
moved=$(local_land gate polish-me | field 'd["polish"]["after"]')
if [ "$gated" = "$after_tip" ] && [ "$on_top" = 0 ] && grep -qF "the tip does not hold the polish pass's last commit (${after_tip:0:9})" <<<"$rewritten" \
  && [ "$moved" = "$(git -C "$tree" rev-parse HEAD~1)" ] && [ "$moved" != "$after_tip" ] && [ "$(git -C "$tree" log -1 --format=%s "$moved")" = "docs(backlog): the guide says nothing of p.txt" ]; then
  pass "the gate finds the polish pass on its tip with a fix on top of it, refuses a branch rewritten under the pass, and after a rebase by base knows the pass's last commit by its new name"
else
  fail "the gate and the polish pass: $gated / $on_top / $rewritten / $moved"
fi
# The pull request's checks hold one line from the pass.
digest=$(lstories digest polish-me 2>/dev/null | field 'd["digest"]' 2>/dev/null || true)
project --repo "$LOCAL" log polish-me stories.read by=lead asked:=2 answered:=2 'families:=["opus"]' 'silent:=[]' stories:=1 flagged:=0 split:=false "digest=$digest" >/dev/null 2>&1 || true
local_land read polish-me --record "$(clean 1)" >/dev/null 2>&1 && local_land propose polish-me --title "feat: p" --notes "$NOTES" >/dev/null 2>&1 || true
project --repo "$LOCAL" state polish-me dropped "the test is over" >/dev/null
if grep -qxF -- "- the polish pass: 6 commits, 1 item filed in the backlog" "$pdir/pr.md"; then
  pass "the pull request's checks say how many commits the polish pass made and how many items it filed"
else
  fail "the polish pass in the pull request: $(cat "$pdir/pr.md" 2>/dev/null)"
fi

# No path rule lets a change skip its review: documentation gets one read at the least. A review that no
# source answered is none; it is started once more, and then the request goes on as not reviewed.
project --repo "$LOCAL" task-dir guide-change --ask "Say more in the guide." >/dev/null
tree=$(project --repo "$LOCAL" worktree-dir guide-change)
git -C "$LOCAL" worktree add -q "$tree" -b docs/guide-change main
plan_in "$tree" guide-change "no test: a sentence of the guide, which a person reads"
echo more >> "$tree/docs/guide.md" && git -C "$tree" add -A && git -C "$tree" commit -q -m "docs: more"
project --repo "$tree" state guide-change ready "the report is written" >/dev/null
read_in "$LOCAL" guide-change
local_land start guide-change >/dev/null && local_land base guide-change >/dev/null && polish_in "$LOCAL" guide-change
gate=$(local_land gate guide-change)
out=$(local_land read guide-change)
early=$(status_of local_land propose guide-change --title "docs: more" --notes "$NOTES")
quiet='{"kind": "read", "answered": [], "silent": [{"name": "codex", "why": "the model was at capacity"}]}'
once=$(local_land read guide-change --record "$(record 1 "$quiet")" | field '(d["recorded"]["verdict"], d["next"])')
twice=$(local_land read guide-change --record "$(record 2 "$quiet")" | field 'd["next"]')
local_land propose guide-change --title "docs: more" --notes "$NOTES" >/dev/null
text=$LOCAL/.git/lem/tasks/guide-change/pr.md
agent=$(local_land land guide-change --by agent 2>&1 || true)
if [ "$(field '(d["stories"]["ok"], [w["story"] for w in d["stories"]["without_a_test"]])' <<<"$gate")" = "(True, [1])" ] \
  && [ "$(field '(d["due"], d["floor"])' <<<"$out")" = "('review', 'read')" ] && [ "$early" = 1 ] && [ "$once" = "('not reviewed', 'review')" ] && [ "$twice" = owner ] \
  && [ "$(sed -n 1p "$text")" = '**Not green.**' ] && [ "$(sed -n 3p "$text")" = '- not reviewed: the review was started twice and no source answered' ] \
  && grep -q '^- the review, round 1 (one read; no source answered; no answer from codex (the model was at capacity)): not reviewed$' "$text" \
  && grep -q '^   - no test: a sentence of the guide, which a person reads$' "$text" \
  && grep -q "^- the stories' tests: 0 pass on the branch and fail on the base commit; 1 story has no test$" "$text" \
  && grep -q "the request is not green (not reviewed" <<<"$agent"; then
  pass "a change of documentation only is not proposed without a review; a review that nobody answered is started once more, and after the second the request is proposed as not reviewed, which no agent merges"
else
  fail "a documentation change and a review with no answer: $gate / $out / $once / $twice / $agent / $(cat "$text" 2>/dev/null)"
fi
local_land land guide-change --by owner >/dev/null && local_land clean guide-change >/dev/null

# A review is of the change as it is: a change of one space is another change. And a floor that rises
# after a review, because the owner says careful, asks for the larger review.
task_in "$LOCAL" spaces s.txt word
tree=$(project --repo "$LOCAL" worktree-dir spaces)
echo 'value = "a b"' > "$tree/v.py" && app_py new old > "$tree/app.py"
git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: a value"
local_land start spaces >/dev/null && local_land base spaces >/dev/null && polish_in "$LOCAL" spaces && local_land gate spaces >/dev/null
local_land read spaces --record "$(clean 1)" >/dev/null
same=$(local_land read spaces | field 'd["due"]')
# the same edit in the next function of the file: every line of the diff is the same, with its
# context, and only its place is not
app_py old new > "$tree/app.py"
git -C "$tree" commit -q -am "fix: the other function" && local_land gate spaces >/dev/null
moved=$(local_land read spaces | field '(d["due"], d["round"])')
git -C "$tree" revert --no-edit HEAD >/dev/null && local_land gate spaces >/dev/null
back=$(local_land read spaces | field 'd["due"]')
task_dir=$(project --repo "$LOCAL" task-dir spaces)
printf '%s\n' 'slug: spaces' 'careful: the owner says so' > "$task_dir/brief.md"
raised=$(local_land read spaces | field '(d["due"], d["floor"])')
rm "$task_dir/brief.md"
echo 'value = "ab"' > "$tree/v.py" && git -C "$tree" commit -q -am "fix: no space" && local_land gate spaces >/dev/null
spaced=$(local_land read spaces | field '(d["due"], d["round"])')
local_land read spaces --record "$(clean 2)" >/dev/null
printf '%s\n' 'slug: spaces' 'careful: the owner says so' > "$task_dir/brief.md"
late=$(local_land read spaces | field 'd["due"] + ": " + d["why"]')
if [ "$same" = none ] && [ "$moved" = "('review', 2)" ] && [ "$back" = none ] && [ "$raised" = "('review', 'full')" ] && [ "$spaced" = "('review', 2)" ] \
  && [ "$late" = "owner: two rounds reviewed it: it was one read, and this change gets the project's full set at the least (the request is careful: the owner says so)" ]; then
  pass "a change of one space after a review, or the same edit in another place of the file, is a change nobody reviewed, and a change that came back to what was reviewed is not; and when the owner calls a reviewed task careful, the one read no longer counts: the full set is due, or after two rounds the request is not green for it"
else
  fail "a review is of the change as it is: $same / $moved / $back / $raised / $spaced / $late"
fi
project --repo "$LOCAL" state spaces dropped "the test is over" >/dev/null

# The bar: a suppression, a pattern of the project's own, a skipped module, fewer assertions, a test
# that goes out of a Rust module and a deleted test file, each refused until the plan gives the
# file's reason. A suppression that only got another space is not a new one.
task_in "$LOCAL" bar-change calc.py one
read_in "$LOCAL" bar-change
tree=$(project --repo "$LOCAL" worktree-dir bar-change)
echo 'import os  # noqa: F401' > "$tree/calc.py" && echo 'test -f calc.py' > "$tree/tests/bar-change.sh" && echo 'puts 1 # rubocop:disable Style/X' > "$tree/x.rb"
printf '%s\n' 'import pytest' 'pytestmark = pytest.mark.skip(reason="later")' 'def test_base():' '    assert 1 + 1 == 2' > "$tree/tests/test_base.py"
printf '%s\n' 'import plugin  # noqa: F401' 'import other  # noqa' > "$tree/plug.py" && echo 'pub fn one() -> i32 { 1 }' > "$tree/lib.rs"
git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: with marks"
local_land start bar-change >/dev/null && local_land base bar-change >/dev/null && polish_in "$LOCAL" bar-change
out=$(local_land gate bar-change 2>/dev/null || true)
err=$(local_land gate bar-change 2>&1 >/dev/null || true)
git -C "$tree" rm -q tests/test_base.py && git -C "$tree" commit -q -m "fix: the old test goes"
gone=$(local_land gate bar-change 2>/dev/null || true)
if [ "$(field '(sorted((e["file"], e["what"], e["reason"]) for e in d["bar"]["lowered"]), d["bar"]["not_covered"], d["bar"]["own_patterns"])' <<<"$out")" \
  = "([('calc.py', '# noqa', None), ('lib.rs', '1 assertion(s) fewer', None), ('plug.py', '# noqa', None), ('tests/test_base.py', '1 assertion(s) fewer', None), ('tests/test_base.py', 'pytest.mark.skip', None), ('x.rb', 'rubocop:disable', None)], ['.rb'], 1)" ] \
  && grep -q "the change lowers the bar with no reason given" <<<"$err" && grep -q "## The bar" <<<"$err" && [ "$(kept_in "$LOCAL" bar-change gated)" = None ] \
  && [ "$(field 'sorted((e["file"], e["what"]) for e in d["bar"]["lowered"] if e["file"].startswith("tests/"))' <<<"$gone")" = "[('tests/test_base.py', 'a test file is deleted')]" ] \
  && [ "$(field '[e["line"] for e in d["bar"]["lowered"] if e["file"] == "plug.py"]' <<<"$out")" = "['import other  # noqa']" ] \
  && [ "$(status_of local_land read bar-change)" = 1 ]; then
  pass "a change that adds a suppression, a mark the project named, a skip of a whole module, fewer assertions, a test taken out of a Rust module or a deleted test file is refused until a reason is given; a suppression that was there and only got a space is none, and one that got wider is one; and the result names the kind of file the bar has no marks for"
else
  fail "the bar: $out / $err / $gone"
fi
plan=$tree/docs/plans/20261115-bar-change.md
# shellcheck disable=SC2016  # the backticks are the plan's own marks around a path
printf '%s\n' '' '## The bar' '' '- calc.py: the import registers a plugin.' '- `x.rb`: the cop reads this line wrong.' '- tests/test_base.py: the sum moved to another module with its test.' '- lib.rs: one() has its test in tests/one.rs now.' '- plug.py: E402 and F401 both hold for that import.' >> "$plan"
git -C "$tree" commit -q -am "docs: why the bar is lower"
out=$(local_land gate bar-change)
small=$(local_land read bar-change | field 'd["floor"]')
unsaid=$(local_land read bar-change --record "$(clean 1)" 2>&1 || true)
local_land read bar-change --record "$(record 1 '{"kind": "read", "answered": ["codex"], "bar": [{"name": "calc.py", "why": "the plugin is loaded by that import."}, {"name": "x.rb", "why": "the cop is wrong here."}, {"name": "tests/test_base.py", "why": "the sum and its test are in the other module."}, {"name": "lib.rs", "why": "tests/one.rs is not in this change."}, {"name": "plug.py", "why": "name the two codes."}]}')" >/dev/null
proposed=$(local_land propose bar-change --title "fix: marks" --notes "$NOTES")
agent=$(local_land land bar-change --by agent 2>&1 || true)
text=$LOCAL/.git/lem/tasks/bar-change/pr.md
# shellcheck disable=SC2016
if [ "$(field 'sorted(e["reason"] for e in d["bar"]["lowered"])' <<<"$out")" = "['E402 and F401 both hold for that import.', 'one() has its test in tests/one.rs now.', 'the cop reads this line wrong.', 'the import registers a plugin.', 'the sum moved to another module with its test.']" ] \
  && [ "$small" = read ] && grep -q "the change lowers the bar in calc.py, lib.rs, plug.py, tests/test_base.py, x.rb and the record says nothing of it" <<<"$unsaid" \
  && [ "$(field '(d["green"], len(d["not_green"]))' <<<"$proposed")" = "(False, 5)" ] && [ "$(sed -n 1p "$text")" = '**Not green.**' ] \
  && grep -q '^- the bar is lower in `calc.py` (# noqa)\. The builder: the import registers a plugin\. The review: the plugin is loaded by that import\.$' "$text" \
  && grep -q '^- the bar is lowered, with these reasons:$' "$text" && grep -q '^  - `calc.py` (# noqa): the import registers a plugin\.$' "$text" \
  && grep -q "^- the bar has no marks of its own for files of these kinds: .rb (the project's 1 pattern(s) in gate.bar were looked for)$" "$text" \
  && grep -q "the request is not green (the bar is lower in" <<<"$agent" \
  && [ "$(grep -c '"event": "proposed", "task": "bar-change", "green": false' "$LOCAL/.git/lem/events.jsonl")" = 1 ]; then
  pass "with a reason for each file in the plan the gate passes, and the request is still not green: the review says what it thinks of each reason, the text opens with each lowered bar, its reason and the review's word, the event log counts it, and no agent merges it"
else
  fail "the bar with reasons: $out / $unsaid / $proposed / $agent / $(cat "$text" 2>/dev/null)"
fi
# What makes a request large or careful, read from its plan: its own call stands under its title,
# where `stages/plan.md` puts it, never in a line the plan quotes further down, and a later commit
# that takes a yes back leaves the request careful, since the talk was due when the plan said it.
local_land start bar-change >/dev/null
"$PY" -c 'import sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(s.replace("1. The change.", "1. The change.\n2. Its test.\n3. Its page.\n4. Its note."))' "$plan"
git -C "$tree" commit -q -am "docs: four tasks" && local_land gate bar-change >/dev/null
large=$(local_land read bar-change | field '(d["floor"], d["why"])')
# shellcheck disable=SC2016  # the backticks are the plan's own fence
"$PY" -c 'import sys; p = sys.argv[1]; s = open(p).read().replace("\n2. Its test.\n3. Its page.\n4. Its note.", "").replace("\n## Stories", "careful: no, nothing here reaches a price.\n\n## Stories", 1)
open(p, "w").write(s + "\n## Plan talk\n\nThe reviewer asked whether the plan should open with this line:\n\n```\ncareful: yes\n```\n")' "$plan"
git -C "$tree" commit -q -am "docs: one task, not careful, and a talk that quotes the line" && local_land gate bar-change >/dev/null
quoted=$(local_land read bar-change | field '(d["floor"], d["careful"])')
"$PY" -c 'import sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(s.replace("careful: no, nothing here reaches a price.", "careful: yes, a price is rounded here."))' "$plan"
git -C "$tree" commit -q -am "docs: careful" && local_land gate bar-change >/dev/null
said=$(local_land read bar-change | field '(d["floor"], d["why"])')
"$PY" -c 'import sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(s.replace("careful: yes, a price is rounded here.", "careful: no, the price is not rounded after all."))' "$plan"
git -C "$tree" commit -q -am "docs: not careful after all" && local_land gate bar-change >/dev/null
taken_back=$(local_land read bar-change | field '(d["floor"], d["why"])')
"$PY" -c 'import sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(s.replace("## Tasks\n\n1. The change.\n", ""))' "$plan"
git -C "$tree" commit -q -am "docs: no tasks" && local_land gate bar-change >/dev/null
err=$(local_land read bar-change 2>&1 || true)
if [ "$large" = "('round', 'the plan has 4 tasks, more than three')" ] && [ "$quoted" = "('read', [])" ] && [ "$said" = "('full', 'the request is careful: the plan says so')" ] \
  && [ "$taken_back" = "('full', 'the request is careful: the plan says so')" ] && grep -q "has no .## Tasks. section with numbered tasks" <<<"$err"; then
  pass "a plan of more than three tasks gets a round at the least; the plan's careful call is read under its title only, never from a line its plan talk quotes, a yes gets the full set, and a later commit that takes the yes back leaves it; a plan with no task list is refused, not taken for a small one"
else
  fail "large and careful: $large / $quoted / $said / $taken_back / $err"
fi
project --repo "$LOCAL" state bar-change dropped "the test is over" >/dev/null

# Careful by its review: the plan called the request plain, and the fresh agent that read the diff
# against the topics calls it careful. A record with no call is refused, and so is a careful call
# with less than the full set. No talk was due, the text says why it had none and why it is
# careful, the miss of the plan's call is one event for the retro, and no agent merges it.
task_in "$LOCAL" price-change seven.txt seven
read_in "$LOCAL" price-change
tree=$(project --repo "$LOCAL" worktree-dir price-change)
mkdir -p "$tree/billing" && echo 'PRICE = 7' > "$tree/billing/price.py" && git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: a price"
local_land start price-change >/dev/null && local_land base price-change >/dev/null && polish_in "$LOCAL" price-change && local_land gate price-change >/dev/null
printf '%s\n' '{"attempt": 1, "kind": "full", "ran": [{"name": "default", "why": "a price changes"}], "answered": ["codex"]}' > "$WORK/no-call.json"
nocall=$(local_land read price-change --record "$WORK/no-call.json" 2>&1 || true)
priced="billing/price.py:PRICE is what a customer pays, so a customer is charged the wrong price"
# the review's call, as JSON: the same record as a round and as the full set
called() { printf '{"kind": "%s", "ran": [{"name": "default", "why": "a price changes"}], "answered": ["codex"], "careful": true, "careful_why": "%s"}' "$1" "$priced"; }
less=$(local_land read price-change --record "$(record 1 "$(called round)")" 2>&1 || true)
local_land read price-change --record "$(record 1 "$(called full)")" >/dev/null
local_land propose price-change --title "fix: seven" --notes "$MIG" >/dev/null
text=$LOCAL/.git/lem/tasks/price-change/pr.md
first=$(grep -c '"event": "careful.missed", "task": "price-change"' "$LOCAL/.git/lem/events.jsonl" || true)
agent=$(local_land land price-change --by agent 2>&1 || true)
local_land start price-change >/dev/null && local_land base price-change >/dev/null && local_land gate price-change >/dev/null && local_land propose price-change --title "fix: seven" --notes "$MIG" >/dev/null
if grep -qF "the record makes the careful call" <<<"$nocall" && grep -qF '"careful": true or false' <<<"$nocall" && grep -qF '"careful_why"' <<<"$nocall" \
  && grep -qF "a change the review calls careful gets the project's full set" <<<"$less" \
  && grep -q '^- no plan talk: the request became careful after its plan, by its review$' "$text" && grep -qxF -- "- careful: yes, the review says so: $priced" "$text" \
  && [ "$(head -1 "$text" | cut -c1-10)" = '**Green.**' ] && [ "$(sed -n 3p "$text")" = "**Careful**, so a person merges it: the review says so: $priced." ] && [ "$first" = 1 ] \
  && [ "$(grep -c '"event": "careful.missed", "task": "price-change"' "$LOCAL/.git/lem/events.jsonl")" = 1 ] \
  && grep -qF "\"event\": \"careful.missed\", \"task\": \"price-change\", \"round\": 1, \"why\": \"$priced\"" "$LOCAL/.git/lem/events.jsonl" \
  && grep -qF "a careful request is merged by a person, whatever the settings say (the review says so: $priced)" <<<"$agent" && [ "$(status_in "$LOCAL" price-change)" = open ]; then
  pass "a request the review calls careful and its plan did not gets the full set, its text says first that a person merges it and why, says in its checks that it had no plan talk and why, the plan's miss is one event with the review's reason, and no agent merges it; a record with no careful call is refused"
else
  fail "a request careful by its review: $nocall / $less / first $first / $agent / $(grep careful.missed "$LOCAL/.git/lem/events.jsonl") / $(cat "$text" 2>/dev/null)"
fi
project --repo "$LOCAL" state price-change dropped "the test is over" >/dev/null

# An agent merges a green request only on the newest review's "not careful": a record that holds no
# call, as a review written down before the call was asked holds none, leaves the merge to a person.
task_in "$LOCAL" call-kept eight.txt eight
read_in "$LOCAL" call-kept
local_land start call-kept >/dev/null && local_land base call-kept >/dev/null && polish_in "$LOCAL" call-kept && local_land gate call-kept >/dev/null && local_land read call-kept --record "$(clean 1)" >/dev/null
local_land propose call-kept --title "fix: eight" --notes "$NOTES" >/dev/null
text=$LOCAL/.git/lem/tasks/call-kept/pr.md
kept_file=$LOCAL/.git/lem/tasks/call-kept/landing.json
cp "$kept_file" "$WORK/call-kept.json"
"$PY" -c 'import json, sys; p = sys.argv[1]; d = json.load(open(p))
for read in d["reads"]:
    read.pop("careful"); read.pop("careful_why")
json.dump(d, open(p, "w"))' "$kept_file"
uncalled=$(local_land land call-kept --by agent 2>&1 || true)
cp "$WORK/call-kept.json" "$kept_file"
merged=$(local_land land call-kept --by agent 2>&1 || true)
if grep -qxF -- "- careful: no; the review says no: $NOT_CAREFUL" "$text" && [ "$(head -1 "$text" | cut -c1-10)" = '**Green.**' ] && ! grep -q '^\*\*Careful\*\*' "$text" \
  && grep -qF "no review that answered made the careful call for this change, so a person merges it" <<<"$uncalled" \
  && [ "$(status_in "$LOCAL" call-kept)" = landed ] && [ "$(git -C "$LOCAL" show main:eight.txt)" = eight ]; then
  pass "an agent merges a green request whose newest review says not careful, and its text says the review's call with its reason; a newest review with no call leaves the merge to a person"
else
  fail "the agent's merge and the review's call: $uncalled / $merged / $(cat "$text" 2>/dev/null)"
fi
local_land clean call-kept >/dev/null

# A branch cannot lift what guards it: one that edits the flow table of its own .lem/project.toml is
# careful by the script, which says why, and the landing reads the topics of the main checkout's
# settings, also when it runs from the task's worktree.
task_in "$LOCAL" lift-topics nine.txt nine
read_in "$LOCAL" lift-topics
tree=$(project --repo "$LOCAL" worktree-dir lift-topics)
"$PY" -c 'import sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(s.replace("topics = [\"a customer is charged the wrong price\"]", "topics = []"))' "$tree/.lem/project.toml"
git -C "$tree" commit -q -am "chore: no topics"
local_land start lift-topics >/dev/null && local_land base lift-topics >/dev/null && polish_in "$LOCAL" lift-topics && local_land gate lift-topics >/dev/null
lifted=$(local_land read lift-topics | field '(d["floor"], d["why"], d["inputs"]["topics"])')
from_tree=$(land --repo "$tree" read lift-topics | field '(d["floor"], d["inputs"]["topics"])')
local_land read lift-topics --record "$(record 1 '{"kind": "full", "ran": [{"name": "default", "why": "the settings change"}], "answered": ["codex"]}')" >/dev/null
local_land propose lift-topics --title "chore: no topics" --notes "$MIG" >/dev/null
agent=$(local_land land lift-topics --by agent 2>&1 || true)
text=$LOCAL/.git/lem/tasks/lift-topics/pr.md
settings_why="the change edits [flow] of .lem/project.toml, Lem's own settings, which say for every later task what is careful, what the gate runs, who merges and where a task lands"
# the reason holds an apostrophe, so Python's repr of it is in double quotes
if [ "$lifted" = "('full', \"the request is careful: $settings_why\", ['a customer is charged the wrong price'])" ] \
  && [ "$from_tree" = "('full', ['a customer is charged the wrong price'])" ] \
  && grep -qxF -- "- careful: yes, $settings_why; the review says no: $NOT_CAREFUL" "$text" \
  && grep -qF "a careful request is merged by a person, whatever the settings say ($settings_why)" <<<"$agent" && [ "$(status_in "$LOCAL" lift-topics)" = open ]; then
  pass "a branch that edits the flow table of its own settings is careful by the script, which says why, gets the full set and a person's merge, and the landing reads the main checkout's topics, also when it runs from the task's worktree"
else
  fail "a branch that lifts its own topics: $lifted / $from_tree / $agent / $(cat "$text" 2>/dev/null)"
fi
project --repo "$LOCAL" state lift-topics dropped "the test is over" >/dev/null

# Every edit of Lem's own settings is careful by the script, not only one of [flow] or [gate]: a branch that
# changes how its tasks land, and one that changes no value and only the file's text, each get the full set,
# with the tables named, and a person's merge.
task_in "$LOCAL" lands-alone ten.txt ten
read_in "$LOCAL" lands-alone
tree=$(project --repo "$LOCAL" worktree-dir lands-alone)
"$PY" -c 'import sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(s.replace("land = \"agent\"", "land = \"agent\"\nhistory = \"squash\""))' "$tree/.lem/project.toml"
git -C "$tree" commit -q -am "chore: one commit for each task"
local_land start lands-alone >/dev/null && local_land base lands-alone >/dev/null && polish_in "$LOCAL" lands-alone && local_land gate lands-alone >/dev/null
branch_floor=$(local_land read lands-alone | field '(d["floor"], d["why"])')
local_land read lands-alone --record "$(record 1 '{"kind": "full", "ran": [{"name": "default", "why": "the settings change"}], "answered": ["codex"]}')" >/dev/null
local_land propose lands-alone --title "chore: squash" --notes "$MIG" >/dev/null
branch_agent=$(local_land land lands-alone --by agent 2>&1 || true)
project --repo "$LOCAL" state lands-alone dropped "the test is over" >/dev/null
task_in "$LOCAL" settings-note eleven.txt eleven
tree=$(project --repo "$LOCAL" worktree-dir settings-note)
printf '%s\n' '# the owner keeps the topics short' >> "$tree/.lem/project.toml"
git -C "$tree" commit -q -am "docs: a note in the settings"
local_land start settings-note >/dev/null && local_land base settings-note >/dev/null && polish_in "$LOCAL" settings-note && local_land gate settings-note >/dev/null
note_floor=$(local_land read settings-note | field '(d["floor"], d["why"])')
project --repo "$LOCAL" state settings-note dropped "the test is over" >/dev/null
branch_why="the change edits [branch] of .lem/project.toml, Lem's own settings, which say for every later task what is careful, what the gate runs, who merges and where a task lands"
note_why="the change edits the text of .lem/project.toml, and no value in it, Lem's own settings, which say for every later task what is careful, what the gate runs, who merges and where a task lands"
if [ "$branch_floor" = "('full', \"the request is careful: $branch_why\")" ] && grep -qF "a careful request is merged by a person, whatever the settings say ($branch_why)" <<<"$branch_agent" \
  && grep -qxF -- "- careful: yes, $branch_why; the review says no: $NOT_CAREFUL" "$LOCAL/.git/lem/tasks/lands-alone/pr.md" \
  && [ "$note_floor" = "('full', \"the request is careful: $note_why\")" ]; then
  pass "every edit of Lem's own settings is careful by the script: one of [branch] gets the full set, a line of the pull request with the table named and a person's merge, and one of the file's text alone is careful too"
else
  fail "an edit of the settings beyond flow and gate: $branch_floor / $branch_agent / $note_floor / $(grep careful "$LOCAL/.git/lem/tasks/lands-alone/pr.md" 2>/dev/null)"
fi

finish
