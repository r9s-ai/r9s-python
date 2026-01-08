"""Tests for r9s.skills.github module."""

import pytest

from r9s.skills.github import GitHubRef, parse_github_url


class TestParseGitHubUrl:
    """Tests for parse_github_url function."""

    def test_shorthand_basic(self):
        """Test basic github: shorthand format."""
        ref = parse_github_url("github:owner/repo/path/to/skill")
        assert ref.owner == "owner"
        assert ref.repo == "repo"
        assert ref.path == "path/to/skill"
        assert ref.branch == "main"
        assert ref.skill_name == "skill"

    def test_shorthand_with_branch(self):
        """Test github: shorthand with @branch suffix."""
        ref = parse_github_url("github:owner/repo/skills/test@develop")
        assert ref.owner == "owner"
        assert ref.repo == "repo"
        assert ref.path == "skills/test"
        assert ref.branch == "develop"
        assert ref.skill_name == "test"

    def test_full_url_tree(self):
        """Test full GitHub URL with /tree/ path."""
        ref = parse_github_url(
            "https://github.com/anthropics/skills/tree/main/skills/pptx"
        )
        assert ref.owner == "anthropics"
        assert ref.repo == "skills"
        assert ref.path == "skills/pptx"
        assert ref.branch == "main"
        assert ref.skill_name == "pptx"

    def test_full_url_blob(self):
        """Test full GitHub URL with /blob/ path."""
        ref = parse_github_url(
            "https://github.com/user/repo/blob/feature/path/skill"
        )
        assert ref.owner == "user"
        assert ref.repo == "repo"
        assert ref.path == "path/skill"
        assert ref.branch == "feature"

    def test_full_url_with_trailing_slash(self):
        """Test full URL with trailing slash is handled."""
        ref = parse_github_url(
            "https://github.com/owner/repo/tree/main/skills/test/"
        )
        assert ref.path == "skills/test"

    def test_invalid_shorthand_no_path(self):
        """Test that shorthand without path raises error."""
        with pytest.raises(ValueError, match="Invalid github: URL format"):
            parse_github_url("github:owner/repo")

    def test_invalid_url_no_path(self):
        """Test that URL without path raises error."""
        with pytest.raises(ValueError, match="must include a path"):
            parse_github_url("https://github.com/owner/repo")

    def test_invalid_url_unrecognized(self):
        """Test that unrecognized URL format raises error."""
        with pytest.raises(ValueError, match="Unrecognized GitHub URL format"):
            parse_github_url("not-a-url")

    def test_whitespace_trimmed(self):
        """Test that whitespace is trimmed from URL."""
        ref = parse_github_url("  github:owner/repo/skill  ")
        assert ref.owner == "owner"
        assert ref.path == "skill"


class TestGitHubRef:
    """Tests for GitHubRef dataclass."""

    def test_archive_url(self):
        """Test archive URL generation."""
        ref = GitHubRef(owner="owner", repo="repo", path="path", branch="main")
        assert ref.archive_url == (
            "https://github.com/owner/repo/archive/refs/heads/main.zip"
        )

    def test_api_contents_url(self):
        """Test API contents URL generation."""
        ref = GitHubRef(
            owner="anthropics", repo="skills", path="skills/pptx", branch="main"
        )
        assert ref.api_contents_url == (
            "https://api.github.com/repos/anthropics/skills/contents/skills/pptx?ref=main"
        )

    def test_skill_name_simple(self):
        """Test skill name extraction from simple path."""
        ref = GitHubRef(owner="o", repo="r", path="skill-name", branch="main")
        assert ref.skill_name == "skill-name"

    def test_skill_name_nested_path(self):
        """Test skill name extraction from nested path."""
        ref = GitHubRef(owner="o", repo="r", path="a/b/c/my-skill", branch="main")
        assert ref.skill_name == "my-skill"
