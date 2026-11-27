"""One build of the site for the cases of this folder in a worker."""

from typing import TYPE_CHECKING

import pytest

from unit.guides import built

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture(scope="session")
def site_build(tmp_path_factory: pytest.TempPathFactory) -> built.Build:
    """The site, built once in a copy of the checkout."""
    folder: Path = tmp_path_factory.mktemp("site")
    return built.build(folder)


@pytest.fixture(scope="session")
def site(site_build: built.Build) -> Path:
    """The built site's folder; a build that failed fails the case that asks for it."""
    assert site_build.code == 0, site_build.said
    return site_build.site


@pytest.fixture(scope="session")
def landing(site_build: built.Build) -> Path:
    """The whole built site: the landing page at its root, and the docs under docs/."""
    assert site_build.code == 0, site_build.said
    return site_build.root
