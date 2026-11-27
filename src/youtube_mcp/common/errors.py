"""Shared errors for validated identifiers and external providers."""


class YouTubeMCPError(Exception):
    """Base error suitable for translation at the MCP boundary."""


class InvalidIdentifierError(YouTubeMCPError, ValueError):
    """Raised when a YouTube video or channel identifier cannot be parsed."""


class ResourceNotFoundError(YouTubeMCPError):
    """Raised when YouTube returns no accessible resource for an identifier."""


class YouTubeAPIError(YouTubeMCPError):
    """Raised when the YouTube Data API request fails."""
