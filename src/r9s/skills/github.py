"""GitHub skill installation support.

Supports installing skills from GitHub repositories using URLs like:
- github:owner/repo/path/to/skill
- github:owner/repo/path/to/skill@branch
- https://github.com/owner/repo/tree/branch/path/to/skill
"""

from __future__ import annotations

import io
import os
import re
import shutil
import stat
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from r9s.skills.local_store import skills_root
from r9s.skills.validator import validate_skill_name


@dataclass
class GitHubRef:
    """Parsed GitHub reference."""

    owner: str
    repo: str
    path: str
    branch: str = "main"

    @property
    def skill_name(self) -> str:
        """Extract skill name from path (last component)."""
        return Path(self.path).name

    @property
    def archive_url(self) -> str:
        """URL to download repository archive."""
        return f"https://github.com/{self.owner}/{self.repo}/archive/refs/heads/{self.branch}.zip"

    @property
    def api_contents_url(self) -> str:
        """GitHub API URL to check if path exists."""
        return f"https://api.github.com/repos/{self.owner}/{self.repo}/contents/{self.path}?ref={self.branch}"


def parse_github_url(url: str) -> GitHubRef:
    """Parse a GitHub URL or shorthand into a GitHubRef.

    Supported formats:
    - github:owner/repo/path/to/skill
    - github:owner/repo/path/to/skill@branch
    - https://github.com/owner/repo/tree/branch/path/to/skill
    - https://github.com/owner/repo/blob/branch/path/to/skill

    Args:
        url: GitHub URL or shorthand

    Returns:
        GitHubRef with parsed components

    Raises:
        ValueError: If URL format is not recognized
    """
    url = url.strip()

    # Format: github:owner/repo/path[@branch]
    if url.startswith("github:"):
        rest = url[7:]  # Remove "github:" prefix

        # Check for @branch suffix
        branch = "main"
        if "@" in rest:
            rest, branch = rest.rsplit("@", 1)

        parts = rest.split("/", 2)
        if len(parts) < 3:
            raise ValueError(
                f"Invalid github: URL format. Expected github:owner/repo/path, got: {url}"
            )

        owner, repo, path = parts[0], parts[1], parts[2]
        return GitHubRef(owner=owner, repo=repo, path=path, branch=branch)

    # Format: https://github.com/owner/repo/tree/branch/path
    # or: https://github.com/owner/repo/blob/branch/path
    match = re.match(
        r"https?://github\.com/([^/]+)/([^/]+)/(tree|blob)/([^/]+)/(.+)",
        url,
    )
    if match:
        owner, repo, _, branch, path = match.groups()
        # Remove trailing slash if present
        path = path.rstrip("/")
        return GitHubRef(owner=owner, repo=repo, path=path, branch=branch)

    # Format: https://github.com/owner/repo (assumes root, no path)
    match = re.match(r"https?://github\.com/([^/]+)/([^/]+)/?$", url)
    if match:
        raise ValueError(
            f"URL must include a path to a skill directory: {url}"
        )

    raise ValueError(
        f"Unrecognized GitHub URL format: {url}\n"
        "Expected formats:\n"
        "  github:owner/repo/path/to/skill\n"
        "  github:owner/repo/path/to/skill@branch\n"
        "  https://github.com/owner/repo/tree/branch/path/to/skill"
    )


def _make_executable(path: Path) -> None:
    """Make a file executable."""
    current = path.stat().st_mode
    path.chmod(current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _download_and_extract(
    ref: GitHubRef,
    target_dir: Path,
    *,
    timeout: int = 60,
) -> None:
    """Download and extract a skill from GitHub.

    Args:
        ref: Parsed GitHub reference
        target_dir: Directory to extract skill into
        timeout: HTTP timeout in seconds

    Raises:
        RuntimeError: If download or extraction fails
    """
    # Download the repository archive
    archive_url = ref.archive_url
    request = Request(
        archive_url,
        headers={"User-Agent": "r9s-cli/1.0"},
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            archive_data = response.read()
    except HTTPError as exc:
        if exc.code == 404:
            raise RuntimeError(
                f"Repository not found: {ref.owner}/{ref.repo} (branch: {ref.branch})"
            ) from exc
        raise RuntimeError(f"Failed to download from GitHub: {exc}") from exc
    except URLError as exc:
        raise RuntimeError(f"Network error: {exc}") from exc

    # Extract to temporary directory first
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Extract ZIP archive
        try:
            with zipfile.ZipFile(io.BytesIO(archive_data)) as zf:
                zf.extractall(tmp_path)
        except zipfile.BadZipFile as exc:
            raise RuntimeError(f"Invalid ZIP archive from GitHub: {exc}") from exc

        # Find the extracted directory (repo-branch/)
        extracted_dirs = list(tmp_path.iterdir())
        if len(extracted_dirs) != 1:
            raise RuntimeError("Unexpected archive structure from GitHub")

        repo_root = extracted_dirs[0]
        skill_source = repo_root / ref.path

        if not skill_source.exists():
            raise RuntimeError(
                f"Path not found in repository: {ref.path}\n"
                f"Make sure the path exists in the {ref.branch} branch."
            )

        if not skill_source.is_dir():
            raise RuntimeError(
                f"Path is not a directory: {ref.path}\n"
                "Skills must be directories containing SKILL.md"
            )

        # Check for SKILL.md
        skill_md = skill_source / "SKILL.md"
        if not skill_md.exists():
            raise RuntimeError(
                f"No SKILL.md found in {ref.path}\n"
                "Valid skills must contain a SKILL.md file."
            )

        # Copy to target directory
        if target_dir.exists():
            shutil.rmtree(target_dir)

        shutil.copytree(skill_source, target_dir)

        # Make scripts executable
        scripts_dir = target_dir / "scripts"
        if scripts_dir.exists():
            for script in scripts_dir.rglob("*"):
                if script.is_file():
                    _make_executable(script)


def install_skill_from_github(
    url: str,
    *,
    name: Optional[str] = None,
    force: bool = False,
    timeout: int = 60,
) -> Path:
    """Install a skill from a GitHub URL.

    Args:
        url: GitHub URL or shorthand (github:owner/repo/path)
        name: Override skill name (default: derived from path)
        force: Overwrite existing skill without prompting
        timeout: HTTP timeout in seconds

    Returns:
        Path to installed skill directory

    Raises:
        ValueError: If URL format is invalid
        RuntimeError: If download or installation fails
    """
    ref = parse_github_url(url)

    # Determine skill name
    skill_name = name or ref.skill_name
    try:
        skill_name = validate_skill_name(skill_name)
    except Exception as exc:
        raise ValueError(f"Invalid skill name '{skill_name}': {exc}") from exc

    # Determine target directory
    target_dir = skills_root() / skill_name

    # Check if already exists
    if target_dir.exists() and not force:
        raise RuntimeError(
            f"Skill '{skill_name}' already exists at {target_dir}\n"
            "Use --force to overwrite."
        )

    # Ensure skills root exists
    skills_root().mkdir(parents=True, exist_ok=True)

    # Download and extract
    _download_and_extract(ref, target_dir, timeout=timeout)

    return target_dir


def check_and_install_dependencies(skill_dir: Path) -> list[str]:
    """Check for and optionally install skill dependencies.

    Looks for requirements.txt in the skill directory.

    Args:
        skill_dir: Path to skill directory

    Returns:
        List of installed packages (empty if none)
    """
    requirements = skill_dir / "requirements.txt"
    if not requirements.exists():
        return []

    # Read requirements
    packages = [
        line.strip()
        for line in requirements.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    return packages
