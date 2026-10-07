#!/usr/bin/env python3
"""Remember where tools live and keep user-local bin dirs on PATH.

Two jobs, both without admin rights:

1. Record: scan PATH plus well-known user-local install locations and save
   absolute binary paths to tools.json (default
   ~/.config/job-apply-kit/tools.json, override with $JAK_TOOLS_FILE).
   doctor.py consults this file when a tool is not on PATH, so a working
   install is recognized even before the user opens a fresh terminal.
2. PATH: on Windows, append missing user-local bin dirs to the *user* PATH
   (HKCU, no elevation needed). On Linux/macOS, print the export lines for
   the user to add (shell rc files are never edited automatically).

Commands:
  tool_paths.py --record [--tools-file PATH]
  tool_paths.py --ensure-path [--dry-run] [--tools-file PATH]
  tool_paths.py --list   # print what would be recorded (no writes)
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import sys
from pathlib import Path

# tool -> executable names to look for (first hit wins).
TOOLS: dict[str, list[str]] = {
    "python": ["python3", "python"],
    "node": ["node"],
    "npm": ["npm"],
    "agent-browser": ["agent-browser"],
    "tectonic": ["tectonic"],
    "pdfinfo": ["pdfinfo"],
    "pandoc": ["pandoc"],
    "gog": ["gog"],
}


def tools_file() -> Path:
    override = os.environ.get("JAK_TOOLS_FILE")
    if override:
        return Path(os.path.expanduser(override))
    return Path(os.path.expanduser("~/.config/job-apply-kit/tools.json"))


def load(path: Path | None = None) -> dict:
    """Saved {tool: absolute path} mapping (empty when none)."""
    f = path or tools_file()
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def save(mapping: dict, path: Path | None = None) -> Path:
    f = path or tools_file()
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(mapping, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return f


def user_bin_dirs() -> list[Path]:
    """User-local bin dirs worth having on PATH (no admin needed)."""
    home = Path(os.path.expanduser("~"))
    if platform.system() == "Windows":
        candidates = [
            home / ".local" / "bin",
            Path(os.path.expandvars(r"%APPDATA%\npm")),
            Path(os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Links")),
            home / "scoop" / "shims",
        ]
    else:
        candidates = [
            home / ".local" / "bin",
            home / ".npm-global" / "bin",
        ]
    return [d for d in candidates if d.is_dir()]


def _which(cmd: str) -> str | None:
    extra = os.pathsep.join([str(d) for d in user_bin_dirs()])
    path = os.environ.get("PATH", "")
    if extra:
        path = path + os.pathsep + extra
    return shutil.which(cmd, path=path)


def scan() -> dict:
    """Find each known tool: PATH first, then user-local dirs. Returns {tool: path}."""
    found: dict[str, str] = {}
    for tool, names in TOOLS.items():
        for name in names:
            hit = _which(name)
            if hit:
                found[tool] = hit
                break
    return found


def record(path: Path | None = None, dry: bool = False) -> dict:
    """Merge a fresh scan into tools.json. Returns the merged mapping."""
    merged = {**load(path), **scan()}
    if not dry:
        save(merged, path)
    return merged


def missing_from_path() -> list[Path]:
    """User-local bin dirs that exist but are not on PATH."""
    current = [p.lower() for p in os.environ.get("PATH", "").split(os.pathsep) if p]
    return [d for d in user_bin_dirs() if str(d).lower() not in current]


def ensure_on_path(dry: bool = False) -> tuple[bool, list[str]]:
    """Add missing user-local bin dirs to the *user* PATH.

    Windows: edits HKCU\\Environment\\Path (no admin). Other OSes: prints
    export lines (rc files are never touched). Returns (changed, messages).
    """
    missing = missing_from_path()
    msgs = []
    if not missing:
        return False, ["user PATH already covers all user-local bin dirs"]
    if platform.system() == "Windows":
        msgs.append("adding to user PATH (HKCU, no admin needed): " + ", ".join(str(d) for d in missing))
        if dry:
            return True, msgs
        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ) as k:
                try:
                    cur, _ = winreg.QueryValueEx(k, "Path")
                except OSError:
                    cur = ""
            new = cur + (";" if cur and not cur.endswith(";") else "") + ";".join(str(d) for d in missing)
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE) as k:
                winreg.SetValueEx(k, "Path", 0, winreg.REG_EXPAND_SZ, new)
            try:  # tell running programs to re-read the environment
                import ctypes

                ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x1A, 0, "Environment", 0x02, 5000, None)
            except Exception:  # noqa: BLE001
                pass
        except Exception as e:  # noqa: BLE001
            return True, [f"could not update user PATH ({e}); add these dirs by hand: " + ", ".join(str(d) for d in missing)]
        msgs.append("done — open a fresh terminal to pick it up")
        return True, msgs
    for d in missing:
        msgs.append(f'add to PATH, e.g. in ~/.bashrc: export PATH="$HOME/{d.relative_to(Path.home())}:$PATH"')
    return True, msgs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--record", action="store_true")
    ap.add_argument("--ensure-path", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--tools-file", default=None)
    a = ap.parse_args(argv)
    tools = Path(os.path.expanduser(a.tools_file)) if a.tools_file else None
    if a.list or (not a.record and not a.ensure_path):
        print(json.dumps(scan(), indent=2))
        return 0
    if a.record:
        merged = record(tools, a.dry_run)
        print(("would save " if a.dry_run else "saved ") + json.dumps(merged))
    if a.ensure_path:
        _, msgs = ensure_on_path(a.dry_run)
        for m in msgs:
            print(("would: " if a.dry_run else "") + m)
    return 0


if __name__ == "__main__":
    sys.exit(main())
