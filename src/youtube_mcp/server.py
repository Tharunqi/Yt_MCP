import os

from google.auth.exceptions import GoogleAuthError
from googleapiclient.errors import HttpError
from mcp.server.fastmcp import FastMCP
from oauthlib.oauth2 import OAuth2Error

from youtube_mcp.auth.youtube import (
    YOUTUBE_PLAYLIST_WRITE_SCOPE,
    YOUTUBE_READ_ONLY_SCOPE,
    build_youtube_client,
)
from youtube_mcp.engagement.analysis import (
    analyze_engagement_data,
    fetch_engagement_data,
    parse_period,
    validate_playlist_ids,
)
from youtube_mcp.playlists.planner import (
    build_playlist_plan,
    preview_result,
    validate_request,
)
from youtube_mcp.playlists.previews import PlaylistPreviewStore
from youtube_mcp.providers.youtube import (
    YouTubeDataProvider,
    youtube_error_reason,
)

mcp = FastMCP(
    "youtube-video-intelligence",
    host="0.0.0.0",
    port=int(os.getenv("MCP_PORT", "8000")),
)
playlist_previews = PlaylistPreviewStore()


def _channel_setup_result() -> dict[str, object]:
    return {
        "status": "needs_youtube_channel",
        "message": (
            "This Google account does not have a YouTube channel yet. "
            "Create a YouTube channel, then preview and confirm the playlist again."
        ),
        "playlist_created": False,
    }


@mcp.tool()
def health_check() -> str:
    """Check whether the YouTube MCP server is running."""
    return "YouTube Video Intelligence MCP Server is running."


@mcp.tool()
def analyze_engagement(
    start_date: str,
    end_date: str,
    selected_playlist_ids: list[str] | None = None,
    comparison_start_date: str | None = None,
    comparison_end_date: str | None = None,
) -> dict[str, object]:
    """Analyze likes, subscriptions and selected playlists for a date range."""
    start, end = parse_period(start_date, end_date)
    if (comparison_start_date is None) != (comparison_end_date is None):
        raise ValueError("Provide both comparison dates or leave both empty.")

    comparison_start = comparison_end = None
    if comparison_start_date is not None and comparison_end_date is not None:
        comparison_start, comparison_end = parse_period(
            comparison_start_date, comparison_end_date
        )

    playlist_ids = validate_playlist_ids(selected_playlist_ids)
    provider = YouTubeDataProvider(build_youtube_client())
    data = fetch_engagement_data(provider, playlist_ids)
    return analyze_engagement_data(
        data, start, end, comparison_start, comparison_end
    )


@mcp.tool()
def preview_playlist(
    topic: str,
    total_duration_minutes: int,
    playlist_title: str,
    visibility: str,
    max_video_length_minutes: int | None = None,
    language: str | None = None,
) -> dict[str, object]:
    """Search and preview a playlist plan without changing YouTube."""
    request = validate_request(
        topic,
        total_duration_minutes,
        max_video_length_minutes,
        language,
        playlist_title,
        visibility,
    )
    provider = YouTubeDataProvider(build_youtube_client())
    candidates = provider.search_videos(request.topic, request.language_code)
    video_ids = list(dict.fromkeys(candidate.video_id for candidate in candidates))
    videos = provider.get_videos(video_ids)
    plan = build_playlist_plan(request, candidates, videos)
    preview_id = playlist_previews.create(plan)
    return preview_result(plan, preview_id)


@mcp.tool()
def create_playlist_from_preview(
    preview_id: str, confirmed_by_user: bool
) -> dict[str, object]:
    """Create a reviewed playlist only after the user confirms the preview."""
    if confirmed_by_user is not True:
        return {
            "status": "confirmation_required",
            "message": "No changes were made. Ask the user to review and confirm the preview.",
            "playlist_created": False,
        }

    plan = playlist_previews.take(preview_id)
    if plan is None:
        return {
            "status": "preview_expired",
            "message": "This preview expired or was already used. Make a new preview first.",
            "playlist_created": False,
        }
    if not plan.items:
        return {
            "status": "not_creatable",
            "message": "The preview has no videos that meet the requested limits.",
            "playlist_created": False,
        }

    try:
        client = build_youtube_client(
            scopes=[YOUTUBE_READ_ONLY_SCOPE, YOUTUBE_PLAYLIST_WRITE_SCOPE]
        )
    except (GoogleAuthError, OAuth2Error, PermissionError):
        return {
            "status": "authorization_required",
            "message": "Playlist write access was not granted. No playlist was created.",
            "playlist_created": False,
        }

    provider = YouTubeDataProvider(client)
    try:
        channel_id = provider.get_my_channel_id()
    except HttpError as error:
        if youtube_error_reason(error) == "youtubeSignupRequired":
            return _channel_setup_result()
        return {
            "status": "failed",
            "message": "YouTube could not check whether this account has a channel.",
            "playlist_created": False,
        }
    if not channel_id:
        return _channel_setup_result()

    try:
        playlist_id = provider.create_playlist(
            plan.request.title, plan.request.visibility
        )
    except HttpError as error:
        if youtube_error_reason(error) == "youtubeSignupRequired":
            return _channel_setup_result()
        return {
            "status": "failed",
            "message": "YouTube could not create the playlist.",
            "playlist_created": False,
        }
    except RuntimeError:
        return {
            "status": "failed",
            "message": "YouTube did not confirm that the playlist was created.",
            "playlist_created": False,
        }

    added_video_ids: list[str] = []
    failed_items: list[dict[str, str]] = []
    for item in plan.items:
        video_id = str(item["video_id"])
        try:
            provider.add_video_to_playlist(playlist_id, video_id)
        except HttpError as error:
            reason = youtube_error_reason(error)
            if reason == "youtubeSignupRequired":
                message = "The account needs a YouTube channel to add playlist videos."
            else:
                message = "YouTube rejected this video."
            failed_items.append({"video_id": video_id, "message": message})
        else:
            added_video_ids.append(video_id)

    status = "completed" if not failed_items else "partial"
    return {
        "status": status,
        "playlist_created": True,
        "playlist_id": playlist_id,
        "playlist_url": f"https://www.youtube.com/playlist?list={playlist_id}",
        "playlist_title": plan.request.title,
        "visibility": plan.request.visibility,
        "added_video_ids": added_video_ids,
        "failed_items": failed_items,
        "message": (
            "Playlist created and all planned videos were added."
            if not failed_items
            else "Playlist created, but some videos were not added. See failed_items."
        ),
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
