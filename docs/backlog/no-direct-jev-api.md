---
worth: yes
where: skills/lem/scripts/jev.py
added: 2026-11-15
---
# no direct Jev API

`jev.py` reaches the Jev decision model through OpenRouter only, with `OPENROUTER_API_KEY`. The
owner raised a second way on 2026-11-15 ("some people prefer direct Jev API, we can support it
via settings file?") and then kept the one way: "Ok. Lets keep that way for now".

What a second way needs, when a developer asks for it: where the choice lives (the key is a
machine's, so `.lem/project.local.toml` or the environment, not the project's settings), the
request and the reply of the direct API mapped to what `jev.py` prints today, and a row of the
machine check for the second key. Nobody read the direct API's documentation for this entry.
