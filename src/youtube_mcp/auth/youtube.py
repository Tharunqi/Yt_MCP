import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

YOUTUBE_READ_ONLY_SCOPE = "https://www.googleapis.com/auth/youtube.readonly"


def load_youtube_credentials(
    client_secrets_file: str | Path, token_file: str | Path
) -> Credentials:
    """Load saved credentials or ask the user to sign in once."""
    token_path = Path(token_file).expanduser()
    credentials = None
    if token_path.is_file():
        credentials = Credentials.from_authorized_user_file(
            str(token_path), [YOUTUBE_READ_ONLY_SCOPE]
        )

    if credentials and credentials.valid:
        return credentials

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(Path(client_secrets_file).expanduser()), [YOUTUBE_READ_ONLY_SCOPE]
        )
        credentials = flow.run_local_server(
            host="localhost",
            bind_addr="0.0.0.0",
            port=int(os.getenv("YOUTUBE_OAUTH_PORT", "8080")),
            open_browser=False,
        )

    token_path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor = os.open(
        token_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600
    )
    with os.fdopen(file_descriptor, "w") as token_file_handle:
        token_file_handle.write(credentials.to_json())
    os.chmod(token_path, 0o600)
    return credentials


def build_youtube_client(
    client_secrets_file: str | Path | None = None,
    token_file: str | Path | None = None,
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
    credentials = load_youtube_credentials(secrets_path, token_path)
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
