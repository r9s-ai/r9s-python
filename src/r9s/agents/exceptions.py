from __future__ import annotations


class AgentError(Exception):
    """Base exception for agent operations."""


class AgentNotFoundError(AgentError):
    """Raised when an agent cannot be found."""


class VersionNotFoundError(AgentError):
    """Raised when a specific agent version cannot be found."""


class InvalidVersionError(AgentError):
    """Raised when a version string is invalid."""


class AgentExistsError(AgentError):
    """Raised when attempting to create an agent that already exists."""
