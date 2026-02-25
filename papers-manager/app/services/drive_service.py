import io
import json
import os
import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parent.parent.parent
_SETTINGS_FILE = _DATA_DIR / "drive_settings.json"
_CLIENT_SECRET_FILE = _DATA_DIR / "drive_client_secret.json"
_TOKEN_FILE = _DATA_DIR / "drive_token.json"

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def _load_settings() -> dict:
    """Load Drive settings from JSON file."""
    if _SETTINGS_FILE.is_file():
        try:
            return json.loads(_SETTINGS_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_settings_data(data: dict) -> None:
    """Write settings dict to file."""
    _SETTINGS_FILE.write_text(json.dumps(data))


def save_client_secret(client_secret_bytes: bytes, folder_id: str) -> None:
    """Save OAuth client secret JSON and folder ID."""
    _CLIENT_SECRET_FILE.write_bytes(client_secret_bytes)
    _save_settings_data({
        "client_secret_path": str(_CLIENT_SECRET_FILE),
        "folder_id": folder_id.strip(),
    })


def get_auth_url() -> Optional[str]:
    """Generate Google OAuth2 authorization URL."""
    settings = _load_settings()
    client_secret_path = settings.get("client_secret_path", "")
    if not client_secret_path or not os.path.isfile(client_secret_path):
        return None

    from google_auth_oauthlib.flow import Flow

    flow = Flow.from_client_secrets_file(
        client_secret_path,
        scopes=SCOPES,
        redirect_uri="http://localhost:8000/settings/drive/callback",
    )
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
    )
    return auth_url


def exchange_code(code: str) -> bool:
    """Exchange authorization code for tokens and save them."""
    settings = _load_settings()
    client_secret_path = settings.get("client_secret_path", "")
    if not client_secret_path or not os.path.isfile(client_secret_path):
        return False

    try:
        from google_auth_oauthlib.flow import Flow

        flow = Flow.from_client_secrets_file(
            client_secret_path,
            scopes=SCOPES,
            redirect_uri="http://localhost:8000/settings/drive/callback",
        )
        flow.fetch_token(code=code)
        creds = flow.credentials

        # Save token
        token_data = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": list(creds.scopes or []),
        }
        _TOKEN_FILE.write_text(json.dumps(token_data))
        return True
    except Exception:
        logger.exception("Failed to exchange OAuth code")
        return False


def clear_settings() -> None:
    """Remove all saved Drive settings, credentials and tokens."""
    for f in [_SETTINGS_FILE, _CLIENT_SECRET_FILE, _TOKEN_FILE]:
        if f.is_file():
            f.unlink()


def _get_credentials():
    """Load OAuth2 credentials from saved token file."""
    if not _TOKEN_FILE.is_file():
        return None

    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    token_data = json.loads(_TOKEN_FILE.read_text())
    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri"),
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=token_data.get("scopes"),
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # Update saved token
        token_data["token"] = creds.token
        _TOKEN_FILE.write_text(json.dumps(token_data))

    return creds


def _get_drive_service():
    """Build and return a Google Drive API service client."""
    from googleapiclient.discovery import build

    creds = _get_credentials()
    if not creds:
        raise RuntimeError("Not authenticated with Google Drive")
    return build("drive", "v3", credentials=creds)


def is_configured() -> bool:
    """Check if Google Drive integration is fully configured (authorized)."""
    settings = _load_settings()
    folder_id = settings.get("folder_id", "")
    return bool(folder_id and _TOKEN_FILE.is_file())


def get_settings_info() -> dict:
    """Return current settings status for the UI."""
    settings = _load_settings()
    has_client_secret = _CLIENT_SECRET_FILE.is_file()
    has_token = _TOKEN_FILE.is_file()
    folder_id = settings.get("folder_id", "")
    return {
        "configured": bool(folder_id and has_token),
        "has_client_secret": has_client_secret,
        "needs_auth": has_client_secret and not has_token,
        "folder_id": folder_id,
    }


def test_connection() -> Tuple[bool, str]:
    """Test Drive connection by listing files in the folder."""
    if not is_configured():
        return False, "Google Drive is not configured"
    try:
        settings = _load_settings()
        folder_id = settings.get("folder_id", "")
        service = _get_drive_service()
        service.files().list(
            q=f"'{folder_id}' in parents",
            pageSize=1,
            fields="files(id)",
        ).execute()
        return True, "Connected successfully"
    except Exception as e:
        return False, str(e)


def upload_pdf(file_bytes: bytes, filename: str) -> Optional[str]:
    """Upload a PDF to Google Drive and return the file ID."""
    if not is_configured():
        return None
    try:
        from googleapiclient.http import MediaIoBaseUpload

        settings = _load_settings()
        folder_id = settings.get("folder_id", "")
        service = _get_drive_service()
        file_metadata = {
            "name": filename,
            "parents": [folder_id],
        }
        media = MediaIoBaseUpload(
            io.BytesIO(file_bytes), mimetype="application/pdf", resumable=True
        )
        file = service.files().create(
            body=file_metadata, media_body=media, fields="id"
        ).execute()
        return file.get("id")
    except Exception:
        logger.exception("Failed to upload PDF to Google Drive")
        return None


def download_pdf(file_id: str) -> Optional[bytes]:
    """Download a PDF from Google Drive by file ID."""
    if not is_configured():
        return None
    try:
        from googleapiclient.http import MediaIoBaseDownload

        service = _get_drive_service()
        request = service.files().get_media(fileId=file_id)
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        return buffer.getvalue()
    except Exception:
        logger.exception("Failed to download PDF from Google Drive")
        return None


def delete_pdf(file_id: str) -> bool:
    """Delete a PDF from Google Drive by file ID."""
    if not is_configured():
        return False
    try:
        service = _get_drive_service()
        service.files().delete(fileId=file_id).execute()
        return True
    except Exception:
        logger.exception("Failed to delete PDF from Google Drive")
        return False
