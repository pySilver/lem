---
worth: later
where: tests/lem-settings.sh
added: 2026-11-22
---
# The night logo check says the whole drawing is in the night palette

The check in `tests/lem-settings.sh` that runs `assets/night.py` on `assets/lem.svg` and
`assets/lem-mark.svg` and compares each output with the committed night file passes with the line
"each night logo is the day logo's drawing in the night palette, as assets/night.py writes it".
Since the task hero-logo-animated-background (2026-11-21), the scene's night sky, the group
`c2-sky-night`, keeps the colors written in the day file and does not go through `NIGHT`, and the
rule that hides a sky is swapped. The check itself still holds, since it compares bytes; only its
words are nearly true. Say instead that each night logo is what `assets/night.py` writes from the
day file: the night palette, with the scene's night sky in its own colors.
