"""The GitHub tracker's check: origin on GitHub, `gh` installed and signed in, the issues on, and
whether the repository holds an issue of any state. It writes nothing and needs no `[tracker]`
table, so onboarding runs it before the table is written."""

import msgspec

from lem.adapters.forge_gh_shell import last_words
from lem.adapters.tracker_gh_facts import Checked, Missing
from lem.adapters.tracker_gh_shell import INSTALL, SET_ORIGIN, GhRun, origin_of


class Enabled(msgspec.Struct, frozen=True, rename="camel"):
    """`gh repo view REPO --json hasIssuesEnabled`."""

    has_issues_enabled: bool


class Number(msgspec.Struct, frozen=True):
    """One row of `gh issue list --json number`."""

    number: int


def joined(one: Checked, other: Checked) -> Checked:
    """Two parts of the check as one: each fact from the part that found it, and every missing
    thing of both."""
    return Checked(
        repository=one.repository or other.repository,
        gh=one.gh or other.gh,
        signed_in=other.signed_in if one.signed_in is None else one.signed_in,
        issues_on=other.issues_on if one.issues_on is None else one.issues_on,
        has_issues=other.has_issues if one.has_issues is None else one.has_issues,
        missing=(*one.missing, *other.missing),
    )


def missing(what: str, fix: str) -> Checked:
    """A part of the check that found one thing missing."""
    return Checked(missing=(Missing(what=what, fix=fix),))


class TrackerChecks(GhRun):
    """The check, one part at a time."""

    def check(self) -> Checked:
        """Every part of the check, the issues only when origin is on GitHub and gh is in."""
        found = joined(self.origin_part(), self.gh_part())
        if found.repository and found.signed_in:
            return joined(found, self.issues_part(found.repository))
        return found

    def origin_part(self) -> Checked:
        """Origin's repository on GitHub, or what is missing."""
        url = self.origin_url()
        if not url:
            fix = "git remote add origin https://github.com/OWNER/REPO.git"
            return missing("this repository has no origin", fix)
        repo = origin_of(url)
        if repo is None:
            what = f"origin is {url}, which is not a repository on GitHub"
            return missing(
                what, f"point origin at the repository on GitHub: {SET_ORIGIN}"
            )
        return Checked(repository=repo)

    def gh_part(self) -> Checked:
        """Where gh is, and whether it is signed in to github.com."""
        where = self.where()
        if where is None:
            return missing("gh is not installed", INSTALL)
        ran = self.tried("auth", "status", "--hostname", "github.com")
        if ran.returncode:
            gone = missing("gh is not signed in to github.com", "gh auth login")
            return joined(Checked(gh=where, signed_in=False), gone)
        return Checked(gh=where, signed_in=True)

    def issues_part(self, repo: str) -> Checked:
        """Whether the issues of `repo` are on, and whether it holds one, open or closed."""
        ran = self.tried("repo", "view", repo, "--json", "hasIssuesEnabled")
        try:
            on = msgspec.json.decode(ran.stdout, type=Enabled).has_issues_enabled
        except msgspec.DecodeError:
            what = f"gh cannot read the repository {repo} ({last_words(ran)})"
            fix = f"check that the account gh is signed in to can see {repo} (gh auth status)"
            return missing(what, fix)
        if not on:
            fix = f"turn Issues on under Settings, General, Features of https://github.com/{repo}"
            off = missing(f"the issues of {repo} are off in its settings", fix)
            return joined(Checked(issues_on=False), off)
        return joined(Checked(issues_on=True), self.listed(repo))

    def listed(self, repo: str) -> Checked:
        """Whether `repo` holds one issue of any state: gh lists the open ones alone unless
        it is told `--state all`."""
        listing = ("--state", "all", "--limit", "1", "--json", "number")
        ran = self.tried("issue", "list", "--repo", repo, *listing)
        try:
            found = msgspec.json.decode(ran.stdout, type=list[Number])
        except msgspec.DecodeError:
            what = f"gh cannot list the issues of {repo} ({last_words(ran)})"
            fix = f"check that the account gh is signed in to can see the issues of {repo}"
            return missing(what, f"{fix} (gh auth status)")
        return Checked(has_issues=bool(found))
