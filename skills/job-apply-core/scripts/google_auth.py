"""Credentials and service builders for the python Google backend."""
from __future__ import annotations

import json
import sys

import google_paths

# Core scopes: everything the apply flow needs. gmail.compose creates drafts. The send scope is
# never requested, because the kit never sends mail.
CORE_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]
# Optional scopes: only for the general-purpose google_api.py commands (label changes, calendar,
# contacts, docs). Commands that need a missing scope fail with a 403 that names it.
OPTIONAL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/contacts.readonly",
    "https://www.googleapis.com/auth/documents",
]
SCOPES = CORE_SCOPES + OPTIONAL_SCOPES  # what google_setup.py asks for on a new authorization


class AuthError(RuntimeError):
    pass


def credentials(account: str | None = None):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    path = google_paths.token_path(account)
    if not path.exists():
        raise AuthError(f"no Google token for this account at {path}. Run: python3 google_setup.py --account <email> "
                        "(or --import-token <file>)")
    data = json.loads(path.read_text())
    scopes = data.get("scopes") if isinstance(data.get("scopes"), list) and data.get("scopes") else SCOPES
    creds = Credentials.from_authorized_user_file(str(path), scopes)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        payload = json.loads(creds.to_json())
        payload.setdefault("type", "authorized_user")
        path.write_text(json.dumps(payload, indent=2))
        try:
            path.chmod(0o600)
        except OSError:
            pass
    if not creds.valid:
        raise AuthError("token invalid; re-run google_setup.py for this account")
    return creds


def service(api: str, version: str, account: str | None = None):
    from googleapiclient.discovery import build
    return build(api, version, credentials=credentials(account), cache_discovery=False)


def access_token(account: str | None = None) -> str:
    """Short-lived access token (for GOG_ACCESS_TOKEN). Never print or store it."""
    return credentials(account).token
