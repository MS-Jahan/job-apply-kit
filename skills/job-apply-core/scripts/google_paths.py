"""Token and secret locations for the python Google backend.

Directory: config `google_token_dir`, else $JAK_GOOGLE_DIR, else ~/.config/job-apply-kit/google
Files:     google_client_secret.json, google_oauth_pending.json, google_token_<account-slug>.json
Account:   --account / $JAK_GOOGLE_ACCOUNT, else config `email_google`, else "default".
Everything in this directory is secret: chmod 700 dir, 600 files, never commit.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

DEFAULT_DIR = "~/.config/job-apply-kit/google"


def _cfg():
    try:
        import jak_config
        return jak_config.load()
    except Exception:  # noqa: BLE001
        return None


def token_dir() -> Path:
    """Resolve the token directory WITHOUT creating it (lookups must have no side effects)."""
    cfg = _cfg()
    explicit = cfg.values.get("google_token_dir") if cfg else None  # not Config.get(): its default must not beat the env var
    raw = explicit or os.environ.get("JAK_GOOGLE_DIR") or DEFAULT_DIR
    return Path(os.path.expanduser(raw))


def ensure_dir() -> Path:
    """Create the token directory (mode 700). Call before writing a token or secret."""
    d = token_dir()
    d.mkdir(parents=True, exist_ok=True)
    try:
        d.chmod(0o700)
    except OSError:
        pass
    return d


def default_account() -> str:
    cfg = _cfg()
    return os.environ.get("JAK_GOOGLE_ACCOUNT") or (cfg.get("email_google") if cfg else None) or "default"


def slug(account: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", account).strip("_").lower() or "default"


def token_path(account: str | None = None) -> Path:
    return token_dir() / f"google_token_{slug(account or default_account())}.json"


def client_secret_path() -> Path:
    return token_dir() / "google_client_secret.json"


def pending_path() -> Path:
    return token_dir() / "google_oauth_pending.json"


def list_accounts() -> list[str]:
    d = token_dir()
    return sorted(p.name[len("google_token_"):-len(".json")] for p in d.glob("google_token_*.json")) if d.is_dir() else []
