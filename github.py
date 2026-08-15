"""Small GitHub Actions API client with no third-party dependencies."""

from __future__ import annotations

from io import BytesIO
import re
from typing import Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zipfile import BadZipFile, ZipFile


class GithubApiError(RuntimeError):
    """Raised when GitHub cannot provide the requested run logs."""


def parse_run_url(run_url: str) -> Dict[str, str]:
    """Extract owner, repository, and run ID from a GitHub Actions URL."""
    pattern = r"^https?://github\.com/([^/]+)/([^/]+)/actions/runs/(\d+)(?:/.*)?/?$"
    match = re.match(pattern, run_url.strip())
    if not match:
        raise ValueError("Expected https://github.com/OWNER/REPO/actions/runs/RUN_ID")
    return {"owner": match.group(1), "repo": match.group(2), "run_id": match.group(3)}


def _request_logs(url: str, token: Optional[str]) -> bytes:
    """Download the ZIP log archive from GitHub."""
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "gha-run-parser/0.1"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with urlopen(Request(url, headers=headers), timeout=30) as response:
            return response.read()
    except (HTTPError, URLError) as exc:
        raise GithubApiError(f"GitHub log download failed: {exc}") from exc


def download_run_logs(run_url: str, token: Optional[str] = None) -> str:
    """Download and combine all text files from a workflow run's log ZIP."""
    parts = parse_run_url(run_url)
    endpoint = (
        f"https://api.github.com/repos/{parts['owner']}/{parts['repo']}"
        f"/actions/runs/{parts['run_id']}/logs"
    )
    try:
        archive = ZipFile(BytesIO(_request_logs(endpoint, token)))
    except BadZipFile as exc:
        raise GithubApiError("GitHub returned an invalid log archive") from exc

    with archive:
        names = sorted(name for name in archive.namelist() if not name.endswith("/"))
        if not names:
            raise GithubApiError("GitHub returned an empty log archive")
        chunks = []
        for name in names:
            content = archive.read(name).decode("utf-8", errors="replace")
            chunks.append(f"##[group]{name}\n{content}\n##[endgroup]")
        return "\n".join(chunks)


def report_metadata(run_url: str) -> Dict[str, str]:
    """Return normalized metadata useful for downstream integrations."""
    return parse_run_url(run_url)
