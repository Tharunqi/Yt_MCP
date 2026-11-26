"""Parsing and validation helpers for public YouTube identifiers."""

import re
from urllib.parse import parse_qs, urlparse

from youtube_mcp.common.errors import InvalidIdentifierError

_VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
_CHANNEL_ID = re.compile(r"^UC[A-Za-z0-9_-]{22}$")


def parse_video_id(value: str) -> str:
    """Extract an 11-character video ID from an ID or common YouTube URL."""
    value = value.strip()
    candidate = value
    if "://" in value:
        parsed = urlparse(value)
        host = parsed.netloc.lower().removeprefix("www.")
        if host in {"youtube.com", "m.youtube.com", "music.youtube.com"}:
            if parsed.path == "/watch":
                candidate = parse_qs(parsed.query).get("v", [""])[0]
            elif parsed.path.startswith(("/shorts/", "/embed/", "/live/")):
                candidate = parsed.path.split("/")[2]
        elif host == "youtu.be":
            candidate = parsed.path.strip("/").split("/")[0]
        else:
            candidate = ""
    if not _VIDEO_ID.fullmatch(candidate):
        raise InvalidIdentifierError("Expected a YouTube video ID or supported video URL.")
    return candidate


def parse_channel_identifier(value: str) -> tuple[str, str]:
    """Return (kind, value), where kind is channel_id, handle, or username."""
    value = value.strip()
    if _CHANNEL_ID.fullmatch(value):
        return "channel_id", value
    if value.startswith("@") and re.fullmatch(r"@[A-Za-z0-9._-]{3,30}", value):
        return "handle", value
    candidate = value
    if "://" in value:
        parsed = urlparse(value)
        host = parsed.netloc.lower().removeprefix("www.")
        if host not in {"youtube.com", "m.youtube.com"}:
            raise InvalidIdentifierError("Expected a YouTube channel ID, handle, or URL.")
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) >= 2 and parts[0] == "channel":
            candidate = parts[1]
        elif parts and parts[0].startswith("@"):
            candidate = parts[0]
        elif len(parts) >= 2 and parts[0] == "user":
            candidate = parts[1]
        else:
            candidate = ""
    if _CHANNEL_ID.fullmatch(candidate):
        return "channel_id", candidate
    if candidate.startswith("@") and re.fullmatch(r"@[A-Za-z0-9._-]{3,30}", candidate):
        return "handle", candidate
    if re.fullmatch(r"[A-Za-z0-9_-]{1,100}", candidate):
        return "username", candidate
    raise InvalidIdentifierError("Expected a YouTube channel ID, handle, or URL.")
