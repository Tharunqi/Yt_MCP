import json
import stat
from pathlib import Path

import youtube_mcp.auth.youtube as youtube_auth


class FakeCredentials:
    valid = True
    expired = False
    refresh_token = None

    def to_json(self) -> str:
        return json.dumps({"token": "saved"})


class FakeFlow:
    def __init__(self, credentials: FakeCredentials) -> None:
        self.credentials = credentials
        self.run_options: dict[str, object] = {}

    def run_local_server(self, **kwargs: object) -> FakeCredentials:
        self.run_options = kwargs
        return self.credentials


def test_first_sign_in_saves_token_with_private_permissions(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("YOUTUBE_OAUTH_PORT", "1234")
    secrets_file = tmp_path / "client_secret.json"
    secrets_file.write_text("{}")
    token_file = tmp_path / "tokens" / "token.json"
    credentials = FakeCredentials()
    flow = FakeFlow(credentials)
    calls: list[tuple[str, list[str]]] = []

    def create_flow(path: str, scopes: list[str]) -> FakeFlow:
        calls.append((path, scopes))
        return flow

    monkeypatch.setattr(
        youtube_auth.InstalledAppFlow, "from_client_secrets_file", create_flow
    )

    result = youtube_auth.load_youtube_credentials(secrets_file, token_file)

    assert result is credentials
    assert calls == [(str(secrets_file), [youtube_auth.YOUTUBE_READ_ONLY_SCOPE])]
    assert flow.run_options == {
        "host": "localhost",
        "bind_addr": "0.0.0.0",
        "port": 1234,
        "open_browser": False,
    }
    assert json.loads(token_file.read_text()) == {"token": "saved"}
    assert stat.S_IMODE(token_file.stat().st_mode) == 0o600


def test_saved_valid_token_skips_sign_in(
    monkeypatch, tmp_path: Path
) -> None:
    token_file = tmp_path / "token.json"
    token_file.write_text("{}")
    credentials = FakeCredentials()
    monkeypatch.setattr(
        youtube_auth.Credentials,
        "from_authorized_user_file",
        lambda path, scopes: credentials,
    )

    result = youtube_auth.load_youtube_credentials("unused.json", token_file)

    assert result is credentials


def test_client_uses_the_only_downloaded_oauth_file(
    monkeypatch, tmp_path: Path
) -> None:
    credentials_folder = tmp_path / "credentials"
    credentials_folder.mkdir()
    downloaded_file = credentials_folder / "client_secret_downloaded.json"
    downloaded_file.write_text("{}")
    credentials = FakeCredentials()
    monkeypatch.setattr(
        youtube_auth,
        "load_youtube_credentials",
        lambda secrets_path, token_path: credentials,
    )
    monkeypatch.setattr(
        youtube_auth,
        "build",
        lambda service, version, **kwargs: (service, version, kwargs),
    )

    result = youtube_auth.build_youtube_client(
        credentials_folder / "client_secret.json", tmp_path / "token.json"
    )

    assert result == (
        "youtube",
        "v3",
        {"credentials": credentials, "cache_discovery": False},
    )
