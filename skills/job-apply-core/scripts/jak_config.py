#!/usr/bin/env python3
"""Config loader for job-apply-kit.

One markdown file holds the configuration. Script-read values are bullets of
the form ``- **key:** value`` under ``##`` headings; everything else is prose
and is ignored. Lists are comma separated. A value that is empty or still a
``<placeholder>`` counts as unset.

Usage:
  python3 jak_config.py --check          # validate, exit 1 on any required miss
  python3 jak_config.py --show           # resolved config, phone/emails masked
  python3 jak_config.py --get KEY        # print one resolved value
  python3 jak_config.py --path           # print the config file path in use

As a module:
  from jak_config import load
  cfg = load()
  cfg.get("cv_source"); cfg.list("banned_claims"); cfg.path("templates_dir")
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

HEADING = re.compile(r"^##\s+(.+?)\s*$")
KEYVAL = re.compile(r"^\s*[-*]\s+\*\*([A-Za-z0-9_]+):\*\*\s*(.*)$")
PLACEHOLDER = re.compile(r"^<.*>$")
ID_LIKE = re.compile(r"^[A-Za-z0-9_-]{20,}$")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE = re.compile(r"\+?\d[\d\s().-]{7,}\d")

REQUIRED = ["name", "name_file", "email_header", "email_google", "cv_source"]
PATH_KEYS = ["workspace", "templates_dir", "cache_dir", "google_token_dir"]
ID_KEYS = ["drive_folder_id", "drive_templates_folder_id", "sheet_id"]
SECRET_KEYS = ["phone", "email_header", "email_google", "gog_account", "email_signature"]

DEFAULT_CONFIG_PATH = "~/.config/job-apply-kit/config.md"


class ConfigError(Exception):
    pass


def config_path(explicit: str | None = None) -> Path:
    raw = explicit or os.environ.get("JAK_CONFIG") or DEFAULT_CONFIG_PATH
    return Path(os.path.expanduser(raw))


def parse(text: str) -> dict[str, str]:
    """Return {key: value}. Later duplicates win. Indented lines continue a value."""
    values: dict[str, str] = {}
    current: str | None = None
    for line in text.splitlines():
        if HEADING.match(line):
            current = None
            continue
        m = KEYVAL.match(line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            values[key] = "" if PLACEHOLDER.match(val) else val
            current = key
            continue
        if current and line.startswith("    ") and line.strip():
            values[current] = (values[current] + "\n" + line.strip()).strip()
        elif not line.strip():
            continue
        else:
            current = None
    return {k: ("" if PLACEHOLDER.match(v.strip()) else v) for k, v in values.items()}


class Config:
    def __init__(self, values: dict[str, str], source: Path | None = None):
        self.values = values
        self.source = source

    # defaults depend on other keys, so resolve lazily
    def _default(self, key: str) -> str | None:
        ws = self.values.get("workspace") or os.environ.get("JAK_WORKSPACE") or os.getcwd()
        defaults = {
            "workspace": ws,
            "templates_dir": str(Path(os.path.expanduser(ws)) / "templates"),
            "cache_dir": str(Path(os.path.expanduser(ws)) / ".cache"),
            "google_token_dir": "~/.config/job-apply-kit/google",
            "cdp_port": "9222",
            "sheet_tab": "Sheet1",
            "default_doc": "resume",
            "template_default": "true",
            "google_backend": "auto",
            "remote_ok": "true",
        }
        return defaults.get(key)

    def get(self, key: str, default: str | None = None) -> str | None:
        val = self.values.get(key, "")
        if val:
            return val
        d = self._default(key)
        return d if d is not None else default

    def list(self, key: str) -> list[str]:
        raw = self.get(key, "") or ""
        return [p.strip() for p in re.split(r"[,\n]", raw) if p.strip()]

    def lines(self, key: str) -> list[str]:
        """Like list() but split on newlines only (for values that may contain commas, e.g. search queries)."""
        raw = self.get(key, "") or ""
        return [p.strip() for p in raw.split("\n") if p.strip()]

    def signature(self) -> str:
        """Email signature: `email_signature` if set, else built from the Identity keys."""
        custom = self.get("email_signature")
        if custom:
            return custom
        parts = [self.get("name"), self.get("phone"), self.get("email_header"), self.get("linkedin")]
        return "\n".join(p for p in parts if p)

    def bool(self, key: str) -> bool:
        return (self.get(key, "false") or "false").strip().lower() in ("1", "true", "yes", "on")

    def int(self, key: str) -> int | None:
        raw = self.get(key)
        try:
            return int(raw) if raw not in (None, "") else None
        except ValueError:
            raise ConfigError(f"{key}: expected an integer, got {raw!r}")

    def path(self, key: str) -> Path:
        raw = self.get(key)
        if not raw:
            raise ConfigError(f"{key}: not set")
        p = Path(os.path.expanduser(raw))
        if not p.is_absolute():
            base = Path(os.path.expanduser(self.get("workspace") or os.getcwd()))
            p = base / p
        return p

    def require(self, key: str) -> str:
        val = self.get(key)
        if not val:
            raise ConfigError(f"{key}: required but not set in {self.source or 'config'}")
        return val

    def check(self) -> tuple[list[str], list[str]]:
        """Return (errors, warnings)."""
        errors: list[str] = []
        warnings: list[str] = []
        for key in REQUIRED:
            if not self.get(key):
                errors.append(f"missing required key: {key}")
        for key in ID_KEYS:
            val = self.values.get(key, "")
            if val and not ID_LIKE.match(val):
                errors.append(f"{key}: does not look like a Google id")
        try:
            port = self.int("cdp_port")
            if port is not None and not (1 <= port <= 65535):
                errors.append("cdp_port: out of range")
        except ConfigError as e:
            errors.append(str(e))
        if self.get("google_backend") not in ("auto", "gog", "python"):
            errors.append("google_backend: must be auto, gog or python")
        if self.get("default_doc") not in ("resume", "cv"):
            errors.append("default_doc: must be resume or cv")
        for key in PATH_KEYS:
            try:
                p = self.path(key)
            except ConfigError:
                continue
            if key in ("workspace",) and not p.exists():
                warnings.append(f"{key}: {p} does not exist")
        for src in self.list("cv_source"):
            if not re.match(r"^https?://", src) and not Path(os.path.expanduser(src)).exists():
                warnings.append(f"cv_source: local path not found: {src}")
        for key in ("drive_folder_id", "gog_account"):
            if not self.get(key):
                warnings.append(f"{key}: not set (run sheet_init or set it for apply skills)")
        if not self.get("sheet_id") and not self.get("sheet_url"):
            warnings.append("sheet_id: not set (paste the tracker URL into sheet_url, or run sheet_init --adopt)")
        return errors, warnings


def load(explicit: str | None = None) -> Config:
    p = config_path(explicit)
    if not p.exists():
        raise ConfigError(f"config file not found: {p} (copy config.example.md there and fill it)")
    return Config(parse(p.read_text(encoding="utf-8")), p)


def update_keys(path, updates: dict[str, str], overwrite: bool = False) -> list[str]:
    """Set `- **key:** value` bullets in the config file. Only fills empty/placeholder values
    unless overwrite=True. Missing keys are appended under a trailing '## Generated' heading.
    Returns the keys written."""
    path = Path(path)
    lines = path.read_text(encoding="utf-8").splitlines()
    written: list[str] = []
    for key, val in updates.items():
        done = False
        for i, line in enumerate(lines):
            m = KEYVAL.match(line)
            if m and m.group(1) == key:
                cur = m.group(2).strip()
                if cur and not PLACEHOLDER.match(cur) and not overwrite:
                    done = True
                    break
                lines[i] = f"- **{key}:** {val}"
                written.append(key)
                done = True
                break
        if not done:
            if "## Generated" not in lines:
                lines += ["", "## Generated"]
            lines.append(f"- **{key}:** {val}")
            written.append(key)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return written


def mask(key: str, value: str) -> str:
    if key in SECRET_KEYS or EMAIL.search(value) or (key == "phone" and PHONE.search(value)):
        out = EMAIL.sub(lambda m: m.group(0)[0] + "***@" + m.group(0).split("@")[1], value)
        out = PHONE.sub(lambda m: m.group(0)[:3] + "***" + m.group(0)[-2:], out)
        return out
    return value


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", help="config file (default: $JAK_CONFIG or %s)" % DEFAULT_CONFIG_PATH)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--show", action="store_true")
    g.add_argument("--get", metavar="KEY")
    g.add_argument("--path", action="store_true")
    a = ap.parse_args(argv)
    if a.path:
        print(config_path(a.config))
        return 0
    try:
        cfg = load(a.config)
    except ConfigError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    if a.get:
        val = cfg.get(a.get)
        if val is None:
            print(f"ERROR: {a.get}: not set", file=sys.stderr)
            return 1
        print(val)
        return 0
    if a.show:
        for k in sorted(set(cfg.values) | {"workspace", "templates_dir", "cache_dir", "cdp_port", "sheet_tab", "default_doc", "google_backend"}):
            v = cfg.get(k)
            if v:
                print(f"{k}: {mask(k, v)}")
        return 0
    errors, warnings = cfg.check()
    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print("config OK" if not errors else f"config has {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
