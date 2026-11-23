# The logo's signal: from Lem's hands to the red eyes of its four agents, and a tab icon for each theme

careful: yes, because "A change bends a ruling of the owner" is in reach: task 1 redraws the logo, which the ruling "The logo is the owner's pick" lets change only on his word, and four new eyes and a new glow that drift from what he approved would change his pick without it; the plan of 2026-11-21 for the same scene made the same call.

## Acceptance criteria

Size: full, because the change redraws the animation of both scenes, links a second tab icon and changes the texts and the ruling that describe the logo.

1. Each of the four small agents has a small red eye in its hood, in the day scene and in the night scene. It is the same red as Lem's own eye, so the night scene needs no new color: a visitor in a dark theme sees four red eyes in the same red as in a light theme. Each eye is large enough to see in the README's logo without a zoom.
   - test: `bash tests/test-site.sh` in `tests/test-site.sh` (the check scene_eyes, the four agents' red eyes in the eye's red, day and night)
2. In each cycle of 8 s, a small glow leaves both of Lem's hands at once and runs down the four strings of the agents, and no other string. The two agents nearest to Lem light up first, then the two outer ones. When the glow reaches an agent, that agent's red eye lights up and then fades:
   1. A visitor opens the README on GitHub, or https://pysilver.github.io/lem/.
   2. A small glow leaves Lem's two hands.
   3. It runs down the strings of the two agents nearest to Lem, and their red eyes light up.
   4. It runs on down the strings of the two outer agents, and their red eyes light up.
   5. Each eye fades, and the cycle starts again after 8 s.
   - test: `bash tests/test-site.sh` in `tests/test-site.sh` (the check scene_signal, the hands, the four strands and each eye's time)
3. Nothing else in the scene lights up or moves along the wire: no pulse runs along the wire, no peg flashes, no agent glows yellow, no light runs down the four strings of the word, and none of the 42 tiles of "Lem" lights up. The letters stay as still as the rest of the drawing. The sky moves as it does today.
   - test: `bash tests/test-site.sh` in `tests/test-site.sh` (the check scene_quiet, nothing else animated)
4. Lem's own red eye blinks as it does today, about every 6 s.
   - no test: the change keeps behavior; the suite holds it (the check scene_eye of `tests/test-site.sh`, which passes on the base too)
5. A visitor whose browser asks for less motion sees the scene still: no glow moves, and no eye lights up or blinks.
   - test: `bash tests/test-site.sh` in `tests/test-site.sh` (the check scene_still, the one rule for reduce motion and each light at rest unlit)
6. The tab icon follows the visitor's theme: a browser with a light theme shows `assets/lem-mark.svg`, and one with a dark theme shows `assets/lem-mark-night.svg`. A browser that does not choose a tab icon by theme shows `assets/lem-mark.svg`. The published site holds both files: today `assets/lem-mark-night.svg` gives 404 there. The tab icon itself stays as it is, the figure with no red eye.
   - test: `bash tests/test-site.sh` in `tests/test-site.sh` (the check icons, the three icon lines in order, and the copy step's published list)
7. Each text that describes the logo's animation says what the new scene does: the scene's own description, the alt text in `README.md` and in `site/index.html`, and the logo's bullet in `docs/rulings/rulings.md`. The alt text says first that it is Lem's logo, and stays short. That bullet today says "the current on the wire" and "one red eye"; after the change it names the signal from Lem's hands and the red eyes of its four agents, and it carries the day of the owner's word, 2026-11-23.
   - no test: the change is the words of the scene's description, two alt texts and one ruling bullet

## Tasks

1. **The scene.** Criteria 1 to 5, and the scene's own description of criterion 7. In `assets/lem.svg`:
   - Give each of the four small agents a red eye in its hood (the dark path `M4 -47C8 -46…` of each, `#2a1d18`), drawn with the existing `#ff2a1a` and the gradient `c2-eye`, so `assets/night.py` needs no new color. Each eye is two parts: an unlit dot of `#ff2a1a` that no animation touches, so the hood shows its red eye at rest and in the still scene of reduce motion (criteria 1 and 5), and over it a lit element of its own (`c2-eye`) that rests at `opacity: 0`. The dot's size is the builder's, as it reads best at the README's width of 720 px.
   - Remove the three `.pulse` paths, the eight `.flash` circles, the four `.drip` paths of the word's strands (x 324.5, 445.5, 519.5, 606.5), the four `.glow` groups, the 42 `.tile` paths and Lem's `.flare`, with their rules and keyframes.
   - Add the signal: in one 8 s cycle both hands (x about 120 to 140, y 105.5) glow at once for a moment; then a small glow starts at the top of each of the two inner strands (x 81.5 and 178.5) and runs down it, and a moment later the same on the two outer strands (x 42 and 218); each agent's eye lights as the glow reaches it, then fades. Nothing moves along the wire, and the short pieces of wire between the hands and the strands' tops never light (decision 4 of the task's record, by the experts). Colors from the existing glow palette (`#ffe7a0`, `#f39a2d`, `#cf6a1c`), which `NIGHT` maps already.
   - Lem's `.eye` keeps its blink of 6 s. The reduce-motion rule stays the one `@media` of the file.
   - Rewrite the `<desc>` to say what the new scene does.
   - Run `python3 assets/night.py assets/lem.svg assets/lem-night.svg` (its `main()` takes the source and the target, as `tests/lem-settings.sh` runs it), and fix the comment in `NIGHT` that names the pulse, the pegs' flash and the tiles.
   - Rewrite the checks of `tests/test-site.sh` that lock the old animation (its criteria 3, 5 and 7: `scene_wire`, `scene_eye`, `scene_still`) into checks of criteria 1 to 5 of this plan, in both scene files: four agents' eyes in the eye's red, the same red day and night; the hands' glow and the glow's elements on the four agents' strands only, with nothing animated on the wire, all in an 8 s cycle; the two hands glow at the same moment; the two inner eyes start to light at one moment and the two outer eyes at one later moment; each agent's eye starts to light when its strand's glow reaches the strand's lower end, which the check computes from the glow's delay, duration and keyframes, within 0.2 s (a guess, not measured; a check of order alone passes an eye that lights a second late); no `.pulse`, `.flash`, `.tile`, `.glow` or `.flare` and nothing animated on the word's strands; the blink of 5 to 7 s; each light at rest unlit, the one reduce-motion rule, no SMIL. Keep `scene_file` (under 50,000 bytes), `scene_sky`, `scene_hex` and `scene_paint` passing. `frame_span()` of the same file finds where the word ends from the `class="tile"` paths alone, for the drawn check at 390 px; with the tiles gone it finds no word, so it reads the word's end from the drawn letters and their cursor instead.
   - Files: `assets/lem.svg`, `assets/lem-night.svg`, `assets/night.py`, `tests/test-site.sh`.
2. **The tab icon, and the page on a narrow phone.** Criterion 6, and decision 5. In `site/index.html` the icon lines give `assets/lem-mark.svg` to a light theme and to a browser that does not choose by theme, and `assets/lem-mark-night.svg` to a dark theme. Three lines, in this order, each `type="image/svg+xml"`: first `assets/lem-mark.svg` with no `media`, then `assets/lem-mark-night.svg` with `media="(prefers-color-scheme: dark)"`, then `assets/lem-mark.svg` with `media="(prefers-color-scheme: light)"` (decision 3 of the task's record, by the gate, from criterion 6). The HTML standard (link type "icon") says that the user agent selects "the most appropriate icon according to the type, media, and sizes attributes", and "If there are multiple equally appropriate icons, user agents must use the last one declared in tree order". So in a dark theme the first and the second line apply and the second wins; in a light theme the first and the third apply and the third wins; a browser that ignores `media` finds three equal icons and takes the last, the day mark; and a browser that reads `media` but does not know the feature (Firefox 41 to 66) finds only the first, the day mark. A day line with no `media` placed last would apply in a dark theme too and win there. The board's two lines in `skills/lem/scripts/lem_board_pages.py` take the same form, one `media` on each, with the light line first. The check of the page's icon lines holds this order and these `media` values. `.github/workflows/pages.yml` copies `assets/lem-mark-night.svg` too. `tests/test-site.sh`: the published list (`want`) holds `assets/lem-mark-night.svg`, and a check reads the page's icon lines. The two marks themselves do not change, so `skills/lem/assets/handover.html` and the board's inlined marks stay. The page on a narrow phone (decision 5 of the task's record, by the dialectic): `.hero`'s `--scene` in `site/style.css` becomes `max(40vw, min(260px, 60vw))`, so below about 433 px the scene is 60% of the window's width high and shows frame x 266.7 to 1333.3 at every such width, which holds all four agents (the left outer one from x about 268.8), Lem and the word; from 433 px up nothing changes, and the `max(40vw, …)` keeps the whole frame from 650 px up. The comment above the rule says the new numbers. The drawn phone check of `tests/test-site.sh` (mode `phone`) also holds the four agents inside the window at 390 px, and a second frame at 360 px holds the same. Files: `site/index.html`, `site/style.css`, `.github/workflows/pages.yml`, `tests/test-site.sh`.
3. **The documents.** Criterion 7, the rest. The alt text of the logo in `README.md` and in `site/index.html`, the same words in both, says first that it is Lem's logo and stays short. The logo's bullet in `docs/rulings/rulings.md` names the signal from Lem's hands and the red eyes of its four agents in place of "the current on the wire" and "one red eye", and gains the day 2026-11-23. The status line of `docs/plans/2026-11-21-hero-logo-animated-background.md` names this plan where it changed that plan's criteria 3, 5 and 7, and its decision 18 (the scene's 260 px on a phone). A sweep of `README.md`, `docs/`, `site/`, `AGENTS.md` and `skills/` for any other text that describes the pulse, the lit tiles or one red eye, each corrected. Files: `README.md`, `site/index.html`, `docs/rulings/rulings.md`, `docs/plans/2026-11-21-hero-logo-animated-background.md`.

## Plan talk

Argued by the reviewer, Codex `gpt-6.2-sol` at high effort as its pane's status line showed them
("GPT 6.2 Sol high"), and the defender, Claude Opus 5.5 at high effort (the `defender:` line of
the task's state). Seven turns: the request, the reviewer's list of six questions, one answer of
each side on each question, a second answer of each side on questions 1 and 3, and the close.
The repairs are commit 9d5ad0ca.

1. **The page's crop at 390 px cuts the left outer agent.** The left outer hood is at frame x 280
   to 288 (`translate(34 204) scale(.6)` inside `translate(224 40) scale(1.6)`, `assets/lem.svg`),
   and `.hero`'s `--scene` in `site/style.css` shows x 320 to 1280 at 390 px, so a Pages visit on
   a phone loses that agent's signal and eye. Repaired with the decision "The page's crop stays as
   it is", which names the limit. The reviewer held: the earlier plan's criterion 2 asks for a side
   crop, not for its amount, and this task's criterion 2 names a Pages visit and the outer eyes.
   The defender refuted: the amount is set, `docs/plans/2026-11-21-hero-logo-animated-background.md`
   task 2 ("the page uses 260 px (decision 18)"), and this task's criteria name no width; showing
   the outer agent at 390 px takes a hero of about 240 px, which reopens that decision and its
   contrast checks. Held a second time: a design choice, the kept crop against a lower hero.
   `stages/plan.md`, step 5, took it. The gate held it; a check of the personas' brief found that the
   crop cuts more than the talk said (half of the inner left agent at 375 px, both left agents at
   360 px), so the lower hero became 60% of the window's width; the newcomer leaned to it, the
   developer was not affected, and the dialectic found no break of it, since decision 18 was the
   earlier plan's lead's: decision 5, by the dialectic, now in task 2 and the decisions.
2. **The short run from the hands to the pegs moves light along the wire.** The plan's first
   decision runs the glow on the wire between the hands (x 118 to 142) and the pegs (x 81.5 and
   178.5, then 42 and 218). The reviewer: criterion 3's "no pulse runs along the wire" bans that
   too; the other route is a glow at the hands, then a glow that starts at the top of each string.
   The plan: criterion 3 opens "Nothing else", which leaves out criterion 2's glow, and criterion
   2's "leaves both of Lem's hands … runs down the four strings" needs a path from the hands to the
   pegs. What a visitor sees under each route is not the two agents' to settle: open, not argued
   further; `stages/plan.md`, step 5, took it with both positions. The ladder: the gate held it,
   the personas leaned to A, the dialectic confirmed a break of A in the owner's outcome ("The
   wire, the word's strings and the letters "Lem" stay still and unlit", `task.md`), and both
   experts picked the reviewer's route: decision 4, by the experts, now the plan's first decision.
3. **The icon order.** The plan's guess, a day line with no `media` and a dark line after it,
   gives a browser that ignores `media` the night mark, since the HTML standard (link type
   "icon") has the user agent "use the last one declared in tree order" among equal icons.
   Repaired at the cause: the night mark with `media="(prefers-color-scheme: dark)"` first, the
   day mark with `media="(prefers-color-scheme: light)"` last. The reviewer held on the repair's
   new text: a browser that reads `media` and does not know the feature matches neither line, and
   criterion 6 gives such a browser the day mark. The defender refuted with the input priced: in
   the Can I Use data (`caniuse-lite` 1.0.30001547, features `link-icon-svg` and
   `prefers-color-scheme`) that browser is Firefox 41 to 66 alone, out of support since 2019, and
   it would show no tab icon. The reviewer held: the gap is real though cheap, and that copy of
   the data ends its Safari entries at 17.1, so it shows nothing of current Safari. Held a second
   time: a design choice, the two lines against three (the day mark with no `media` first, then
   the two lines of the repair). `stages/plan.md`, step 5, took it: the gate judged it checkable
   from criterion 6 ("A browser that does not choose a tab icon by theme shows
   `assets/lem-mark.svg`"), so three lines: decision 3, by the gate, now in task 2.
4. **The still scene with no unlit dot has no agents' eyes.** The plan let the builder draw no
   unlit dot, and under reduce motion the lit eyes rest at `opacity: 0`, so criterion 1 fails in
   the still scene of criterion 5. Repaired at the cause: each eye has an unlit dot of `#ff2a1a`
   that no animation touches, under its lit element. Settled (the reviewer: closed, at the cause),
   settled by the two, not checked by the review.
5. **A check of order alone passes an eye that lights late.** Repaired at the cause: the check
   holds one departure moment for both hands, one moment for the inner pair and a later one for
   the outer pair, and each eye's start within 0.2 s of its strand's computed arrival. Settled
   (closed, at the cause), settled by the two, not checked by the review.
6. **`python3 assets/night.py` with no paths exits with its usage line.** Repaired: the command
   is `python3 assets/night.py assets/lem.svg assets/lem-night.svg`, as `tests/lem-settings.sh`
   runs it; the reviewer ran it and its output matched the committed night scene byte for byte.
   Settled, settled by the two, not checked by the review.

No mechanism was added: the repairs changed decisions of the plan (3, 4 and 5 at the cause) or
named one (1). No question was raised after the first turn in the talk, and no addition was
refused. After the talk, the check of a persona brief of the ladder found that `frame_span()` in
`tests/test-site.sh` reads the word's end from the lit tiles that task 1 removes: raised, not
argued; task 1 now names it, and the review before the pull request checks it as a claim.

What changed in the plan, by task: task 1, the agents' eyes (question 4), the checks of the
signal's times (question 5), the night command (question 6), the signal's route with nothing on
the wire (question 2, by the ladder) and `frame_span()` (after the talk); task 2, the icon lines
and their check (question 3, three lines by the ladder) and the page's scene on a narrow phone
(question 1, by the ladder); the decisions, the first one turned to the route of question 2, and
the one on the page's scene on a narrow phone (question 1).

## Decisions

- **Nothing moves along the wire: the hands glow, then the strands light from their tops.** The strands hang from pegs on the wire (x 42, 81.5, 178.5, 218), and the hands hold the wire at x 118 to 142, so the signal has a gap of 36.5 and 76 units to cross. It crosses it in time, not on the wire: the hands glow, then the inner strands, then the outer ones. It rests on the owner's outcome, "The wire, the word's strings and the letters "Lem" stay still and unlit" (`task.md`, and the case of the criteria page he approved), with criterion 3's "no pulse runs along the wire". Decision 4 of the task's record, by the experts (fable and astra both); the personas leaned to a short run on the wire, for a path with no gap, and the timing that makes the hands and the strands read as one signal is the builder's.
- **Lem's flare goes.** It marked the pulse that passed the figure; criterion 3 says nothing else lights up, and criterion 4 keeps only the blink.
- **No new color.** The eyes take `#ff2a1a`, and the glow the colors `NIGHT` maps today, so the owner's night palette does not change.
- **The times of the cycle are the builder's**, within criterion 2's order: inner pair, then outer pair, then a rest to 8 s.
- **On a narrow phone the page's scene gets smaller, so all four agents show.** Today `.hero`'s `--scene` in `site/style.css` keeps the scene 260 px high from about 350 to 650 px wide, so a phone cuts the left agents: at 390 px the outer one is gone, at 375 px half of the inner one shows with its face at the edge, at 360 px both are gone (the left outer agent spans frame x 269.8 to 292.3, its `translate(34 204) scale(.6)` inside `translate(224 40) scale(1.6)` in `assets/lem.svg`). With `max(40vw, min(260px, 60vw))` the window shows frame x 266.7 to 1333.3 below about 433 px. It keeps the earlier plan's approved criterion 2 ("at 390 px wide the hooded figure and the word "Lem" both show, and the scene is cut at its sides, not squeezed") and changes that plan's decision 18, its lead's choice of 260 px. Decision 5 of the task's record, by the dialectic; the newcomer persona leaned to it, and the numbers are computed from the two files, not measured in a browser.

## What this plan will not verify

- Which tab icon Safari and Firefox show in each theme: no test here drives a real browser's tab. Task 2 reads the sources, and the report says what they say; the owner's own look in each browser is the check.
- That an agent's eye is "large enough to see without a zoom": the builder takes a screenshot of the README's width in each theme for the report, and the owner judges it at the merge.
