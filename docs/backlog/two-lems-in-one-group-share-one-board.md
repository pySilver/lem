---
worth: yes
where: skills/lem/scripts/board.py:show
added: 2026-11-15
---
# two Lems in one group of sessions share one board

Derived from the code, not run. `show` looks for a board that is already open by three things:
the page's name, that it is a page, and its parent. The name of the board of all tasks is
`Lem board` in every repository (`main`), and the parent is the top session of the group, because
a companion's companion becomes its sibling. So when Lem of repository A and Lem of repository B
each run in a companion session of one top session, the second `board.py` finds the first one's
page, reloads it and prints `"reloaded": true`. The owner of B gets A's board and no board of B.

The case is close to one that ran: on 2026-11-15 Lem of the scratch repository ran in the session
`lem-smoke`, a companion of the session `build`, and its board got `build` as its parent. A Lem
in a second companion of `build`, for another repository, is the case above.

What a reader would get wrong: the comment in `show` ("another repository's Lem in the same
window has a board of the same name, and it is not this one's to reload or close") and the test
"another session's board of the same name is left alone" cover two Lems with different parents.
They say nothing of two Lems under one parent.

The fix keeps the two apart by something of the repository: the page's own path (each board is
`board.html` in its repository's state folder) or the repository's name in the page's name. Not
checked: whether `agtermctl tree --json` gives a page companion's path, which decides between
the two.

Surfaced by Lem of the scratch repository during the task `year-range-shows-both-years`, when
its board opened under another session than its own. That part is as designed, and `f5b611a`
made the skill's text say so.
