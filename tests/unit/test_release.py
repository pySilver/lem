"""A release names one number in three places: the `version` of `.claude-plugin/plugin.json`, and the
`version` and the `ref` of the `lem` entry of `.claude-plugin/marketplace.json`, whose source is the
GitHub repository at the tag `vNUMBER`. An install and an update take the plugin from that source, so
they get the commit of the release tag and never the head of `main`.

    python3 -B -m unittest discover -s tests/unit -p test_release.py
"""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# The repository every install of the `lem` entry takes the plugin from.
REPO = "pySilver/lem"


def release_places(plugin: dict, market: dict) -> list[tuple[str, str]]:
    """Each place of the two manifests that does not name the release of `plugin.json`, as (the place,
    what is wrong there and what it expects). Empty when the three places name one release."""
    number = plugin.get("version")
    if not isinstance(number, str) or not re.fullmatch(r"\d+\.\d+\.\d+", number):
        return [("plugin.json version", f"plugin.json's version is {number!r}, and a release names three numbers, as \"0.4.0\"")]
    tag = f"v{number}"
    entries = [entry for entry in market.get("plugins") or [] if isinstance(entry, dict) and entry.get("name") == "lem"]
    if len(entries) != 1:
        return [("marketplace.json plugins", f"marketplace.json has {len(entries)} entries named lem, and it needs one, at the release {tag}")]
    entry = entries[0]
    found = []
    source = entry.get("source")
    want = {"source": "github", "repo": REPO, "ref": tag}
    if not isinstance(source, dict) or source.get("source") != "github" or source.get("repo") != REPO:
        found.append(("lem entry source", f"the lem entry's source is {json.dumps(source)}, and plugin.json's version {number} expects {json.dumps(want)}"))
    elif "ref" not in source:
        found.append(("lem entry ref", f"the lem entry's source has no ref, and plugin.json's version {number} expects \"ref\": \"{tag}\""))
    elif source["ref"] != tag:
        found.append(("lem entry ref", f"the lem entry's ref is {json.dumps(source['ref'])}, and plugin.json's version {number} expects \"{tag}\""))
    if entry.get("version") != number:
        found.append(("lem entry version", f"the lem entry's version is {json.dumps(entry.get('version'))}, and plugin.json's version {number} expects \"{number}\""))
    return found


def manifests(number: str = "0.4.0", ref: str | None = "v0.4.0", version: str | None = "0.4.0", source: object = None) -> tuple[dict, dict]:
    """A plugin.json of NUMBER and a marketplace.json whose lem entry has REF and VERSION (left out when None)."""
    if source is None:
        source = {"source": "github", "repo": REPO, **({"ref": ref} if ref is not None else {})}
    entry = {"name": "lem", "source": source, "description": "Lem.", **({"version": version} if version is not None else {})}
    return {"name": "lem", "version": number}, {"name": "lem", "plugins": [entry]}


class Places(unittest.TestCase):
    def test_three_places_that_name_one_release_pass(self):
        self.assertEqual(release_places(*manifests()), [])

    def test_a_ref_of_the_release_before_fails_and_names_the_ref_and_the_number_it_expects(self):
        self.assertEqual(release_places(*manifests(ref="v0.3.0")),
                         [("lem entry ref", 'the lem entry\'s ref is "v0.3.0", and plugin.json\'s version 0.4.0 expects "v0.4.0"')])

    def test_an_entry_version_of_another_release_fails(self):
        self.assertEqual(release_places(*manifests(version="0.3.0")),
                         [("lem entry version", 'the lem entry\'s version is "0.3.0", and plugin.json\'s version 0.4.0 expects "0.4.0"')])
        self.assertEqual([place for place, _ in release_places(*manifests(version=None))], ["lem entry version"])

    def test_an_entry_with_no_ref_fails(self):
        self.assertEqual(release_places(*manifests(ref=None)),
                         [("lem entry ref", 'the lem entry\'s source has no ref, and plugin.json\'s version 0.4.0 expects "ref": "v0.4.0"')])

    def test_a_source_that_is_not_the_github_repository_fails(self):
        for source in ("./", {"source": "github", "repo": "someone/lem", "ref": "v0.4.0"}, {"source": "url", "url": f"https://github.com/{REPO}.git", "ref": "v0.4.0"}):
            with self.subTest(source=source):
                found = release_places(*manifests(source=source))
                self.assertEqual([place for place, _ in found], ["lem entry source"])
                self.assertIn('expects {"source": "github", "repo": "pySilver/lem", "ref": "v0.4.0"}', found[0][1])

    def test_a_plugin_version_that_is_no_release_fails(self):
        self.assertEqual([place for place, _ in release_places({"name": "lem"}, manifests()[1])], ["plugin.json version"])


class Repository(unittest.TestCase):
    def read(self) -> tuple[dict, dict]:
        folder = ROOT / ".claude-plugin"
        return (json.loads((folder / "plugin.json").read_text(encoding="utf-8")), json.loads((folder / "marketplace.json").read_text(encoding="utf-8")))

    def test_the_lem_entry_takes_the_plugin_from_the_release_tag_and_not_from_main(self):
        plugin, market = self.read()
        entry = next(entry for entry in market["plugins"] if entry["name"] == "lem")
        self.assertEqual(entry["source"], {"source": "github", "repo": REPO, "ref": f"v{plugin['version']}"})

    def test_the_repository_names_one_release_in_three_places(self):
        self.assertEqual(release_places(*self.read()), [])


if __name__ == "__main__":
    unittest.main()
