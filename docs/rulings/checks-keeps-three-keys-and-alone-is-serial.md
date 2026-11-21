---
ruled: 2026-11-18
area: The settings, the seats and the tracker
---

# `[checks]` keeps three keys, and `alone` is `serial`.

His review of the README and of each guide on 2026-11-18, after that build; a quote is his words.
Where a note replaces an earlier ruling, this is the ruling now.

**`[checks]` keeps three keys, and `alone` is `serial`.** "I'm a bit confused with this
section. Yes its Lead who usually run tests, and e2e local tests are usually needs to run in
queue. Then maybe we need to name `alone` differently? Should Lem support something like merge
train or test train? Ask Fable for opinion for that section". Fable's answer, which the session
took: no train; `checks.serial` names the tests that two tasks cannot run at the same time, and
they run one at a time for all tasks. `checks.setup` runs once in each new worktree.
