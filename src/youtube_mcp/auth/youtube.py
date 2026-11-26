import os
from pathlib import Path

from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

YOUTUBE_READ_ONLY_SCOPE = "https://www.googleapis.com/auth/youtube.readonly"
YOUTUBE_PLAYLIST_WRITE_SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"


def _has_scopes(credentials: Credentials, scopes: list[str]) -> bool:
    granted = getattr(credentials, "granted_scopes", None)
    if granted is None:
        granted = getattr(credentials, "scopes", None)
    return set(scopes).issubset(set(granted or []))


def _save_credentials(credentials: Credentials, token_path: Path) -> None:
    token_path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor = os.open(
        token_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600
    )
    with os.fdopen(file_descriptor, "w") as token_file_handle:
        token_file_handle.write(credentials.to_json())
    os.chmod(token_path, 0o600)


def load_youtube_credentials(
    client_secrets_file: str | Path,
    token_file: str | Path,
    scopes: list[str] | None = None,
) -> Credentials:
    """Load saved credentials, refresh them, or request the needed scopes."""
    requested_scopes = scopes or [YOUTUBE_READ_ONLY_SCOPE]
    token_path = Path(token_file).expanduser()
    credentials = None
    if token_path.is_file():
        credentials = Credentials.from_authorized_user_file(str(token_path))

    if credentials and credentials.valid and _has_scopes(credentials, requested_scopes):
        return credentials

    if credentials and credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
        except GoogleAuthError:
            credentials = None
        if credentials and credentials.valid and _has_scopes(credentials, requested_scopes):
            _save_credentials(credentials, token_path)
            return credentials

    flow = InstalledAppFlow.from_client_secrets_file(
        str(Path(client_secrets_file).expanduser()), requested_scopes
    )
    credentials = flow.run_local_server(
        host="localhost",
        bind_addr="0.0.0.0",
        port=int(os.getenv("YOUTUBE_OAUTH_PORT", "8080")),
        open_browser=False,
        include_granted_scopes="true",
    )
    if not _has_scopes(credentials, requested_scopes):
        raise PermissionError("The requested YouTube access was not granted.")

    _save_credentials(credentials, token_path)
    return credentials


def build_youtube_client(
    client_secrets_file: str | Path | None = None,
    token_file: str | Path | None = None,
    scopes: list[str] | None = None,
):
    """Build a YouTube API client using saved or newly granted access."""
    secrets_path = Path(
        client_secrets_file
        or os.getenv("YOUTUBE_CLIENT_SECRETS_FILE", "client_secret.json")
    ).expanduser()
    if not secrets_path.is_file():
        candidates = tuple(secrets_path.parent.glob("client_secret*.json"))
        if len(candidates) == 1:
            secrets_path = candidates[0]
        else:
            raise FileNotFoundError(
                "Add one Google Desktop OAuth JSON file to the credentials folder."
            )

    token_path = Path(
        token_file
        or os.getenv(
            "YOUTUBE_TOKEN_FILE", "~/.config/youtube-mcp/token.json"
        )
    ).expanduser()
    credentials = load_youtube_credentials(secrets_path, token_path, scopes)
    return build(
        "youtube",
        "v3",
        credentials=credentials,
        cache_discovery=False,
    )


def main() -> None:
    build_youtube_client()
    print("YouTube sign-in is ready.")


if __name__ == "__main__":
    main()
