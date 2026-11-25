"""The `Judge` port's contract (`tests/contract/suites/outside.py`) on Jev's adapter, with a
stand-in transport for the provider: nothing leaves the machine, and no key of the owner's
environment is read."""

import json
from typing import TYPE_CHECKING

import httpx
import pytest

from contract.suites.outside import JudgeContract
from lem.adapters import judge_jev
from lem.ports.place import Place

if TYPE_CHECKING:
    from pathlib import Path


def standin(request: httpx.Request) -> httpx.Response:
    """Jev's answer to every question: a score of 0.7."""
    asked = json.loads(request.content)["questions"]
    answers = {name: {"type": "noul", "noul": 0.7} for name in asked}
    return httpx.Response(200, json={"model": "stand-in", "answers": answers})


class TestJevWithAKey(JudgeContract):
    @pytest.fixture(autouse=True)
    def folder(self, tmp_path: Path) -> None:
        self.root = tmp_path

    def judge(self) -> judge_jev.JevJudge:
        place = Place(
            checkout=self.root,
            home=self.root,
            environ={"JEV_API_KEY": "not-a-real-key"},
        )
        return judge_jev.bind(place, transport=httpx.MockTransport(standin))


class TestJevWithNoKey(JudgeContract):
    @pytest.fixture(autouse=True)
    def folder(self, tmp_path: Path) -> None:
        self.root = tmp_path

    def judge(self) -> judge_jev.JevJudge:
        place = Place(checkout=self.root, home=self.root, environ={})
        return judge_jev.bind(place, transport=httpx.MockTransport(standin))
