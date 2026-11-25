"""The add-on skills reference the rebuilt envelope and command tree."""

from lem.kernel.paths import root


def test_expert_skill_and_harness_use_the_result_and_root_repo_option() -> None:
    skill = (root() / "skills/lem-ask-expert/SKILL.md").read_text()
    harness = (root() / "skills/lem/harness/claude-code/ask-experts.md").read_text()
    assert "lem --repo CHECKOUT experts brief --question" in skill
    assert "lem --repo CHECKOUT experts record --folder" in skill
    assert "JSON envelope's `result`" in skill
    assert "or none for an open question" in skill
    assert "Without Codex" in skill or "without Codex" in skill
    assert "lem --repo WORKTREE experts record --folder" in harness
    assert "`result` of `lem experts brief`" in harness
    assert "<!-- lem: old form -->" not in skill


def test_panel_skill_and_messages_use_the_cast_and_jev_results() -> None:
    root_dir = root() / "skills" / "lem-panel"
    skill = (root_dir / "SKILL.md").read_text()
    messages = (root_dir / "references/messages.md").read_text()
    assert "lem path rulings" in skill
    assert "`result.dir`" in skill
    assert "`result.profile.path`" in skill
    assert "`result.profile.path`" in messages
    assert "`result.answers`" in skill
    assert "<!-- lem: old form -->" not in skill


def test_shipped_skill_activation_and_description() -> None:
    for path in (root() / "skills").glob("*/SKILL.md"):
        text = path.read_text().split("---", 2)[1]
        if path.parent.name == "lem":
            assert "disable-model-invocation:" not in text
            continue
        assert "disable-model-invocation: true" in text, path
        description = next(
            line for line in text.splitlines() if line.startswith("description:")
        )
        words = description.partition(":")[2].strip().strip('"')
        assert "Lem" in words and len(words) < 300, path
