import secrets
import threading
import time
from collections import OrderedDict

from youtube_mcp.playlists.planner import PlaylistPlan

_PREVIEW_LIFETIME_SECONDS = 15 * 60
_MAX_PREVIEWS = 100


class PlaylistPreviewStore:
    """Keep short-lived playlist previews in memory until they are confirmed."""

    def __init__(self) -> None:
        self._plans: OrderedDict[str, tuple[float, PlaylistPlan]] = OrderedDict()
        self._lock = threading.Lock()

    def create(self, plan: PlaylistPlan) -> str:
        now = time.monotonic()
        with self._lock:
            self._remove_expired(now)
            while len(self._plans) >= _MAX_PREVIEWS:
                self._plans.popitem(last=False)
            preview_id = secrets.token_urlsafe(18)
            self._plans[preview_id] = (now, plan)
        return preview_id

    def take(self, preview_id: str) -> PlaylistPlan | None:
        now = time.monotonic()
        with self._lock:
            self._remove_expired(now)
            entry = self._plans.pop(preview_id, None)
        if entry is None:
            return None
        created_at, plan = entry
        if now - created_at > _PREVIEW_LIFETIME_SECONDS:
            return None
        return plan

    def _remove_expired(self, now: float) -> None:
        expired = [
            preview_id
            for preview_id, (created_at, _) in self._plans.items()
            if now - created_at > _PREVIEW_LIFETIME_SECONDS
        ]
        for preview_id in expired:
            self._plans.pop(preview_id, None)
