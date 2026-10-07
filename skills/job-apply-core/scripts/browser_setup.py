#!/usr/bin/env python3
"""Detect Chromium-based browsers and generate debug-mode launchers.

Firefox is intentionally out of scope: the kit only drives Chromium-based
browsers over CDP (Chrome, Edge, Brave, Chromium).

Agent workflow (also works for humans):
  1. browser_setup.py --list            # detect + suggest (exit 0 if any found)
  2. Ask the user which browser(s) to use (suggest the marked default; several allowed).
  3. browser_setup.py --browser chrome,brave --create
     Writes browser-debug-<name>.bat (.sh on Linux/macOS) into --out-dir
     (default: the kit repo root) plus a double-clickable shortcut for each on
     the desktop. By default the launcher reuses the browser's EXISTING
     default profile (no --user-data-dir): the user closes normal browser
     windows first, starts the debug shortcut, and is already logged in.
     Only when the user explicitly asks for a separate profile, pass
     --profile <dir> (or --isolated for the legacy jak-browser-<name> dir).
     agent-browser and the chrome-devtools MCP attach to it on --port
     (default: config cdp_port, else 9222).

Only the standard library is used. No hardcoded /tmp, no shell=True.
Env overrides (tests, custom installs): JAK_BROWSER_BIN_CHROME / _EDGE /
_BRAVE / _CHROMIUM point at an executable and win over auto-detection.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent.parent

BROWSERS: dict[str, dict] = {
    "chrome": {
        "label": "Google Chrome",
        "priority": 10,
        "which": ["google-chrome", "google-chrome-stable", "chrome"],
        "win_paths": [
            r"%ProgramFiles%\Google\Chrome\Application\chrome.exe",
            r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe",
            r"%LocalAppData%\Google\Chrome\Application\chrome.exe",
        ],
        "mac_paths": ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"],
    },
    "edge": {
        "label": "Microsoft Edge",
        "priority": 20,
        "which": ["microsoft-edge", "microsoft-edge-stable", "msedge"],
        "win_paths": [
            r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe",
            r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe",
        ],
        "mac_paths": ["/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"],
    },
    "brave": {
        "label": "Brave",
        "priority": 30,
        "which": ["brave-browser", "brave", "brave-browser-stable"],
        "win_paths": [
            r"%ProgramFiles%\BraveSoftware\Brave-Browser\Application\brave.exe",
            r"%ProgramFiles(x86)%\BraveSoftware\Brave-Browser\Application\brave.exe",
            r"%LocalAppData%\BraveSoftware\Brave-Browser\Application\brave.exe",
        ],
        "mac_paths": ["/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"],
    },
    "chromium": {
        "label": "Chromium",
        "priority": 40,
        "which": ["chromium", "chromium-browser"],
        "win_paths": [r"%ProgramFiles%\Chromium\Application\chrome.exe"],
        "mac_paths": ["/Applications/Chromium.app/Contents/MacOS/Chromium"],
    },
}

DOWNLOADS = {
    "chrome": "https://www.google.com/chrome/",
    "edge": "https://www.microsoft.com/edge/download",
    "brave": "https://brave.com/download/",
    "chromium": "https://www.chromium.org/getting-involved/download-chromium/",
}


def _which(name: str) -> str | None:
    extra = os.pathsep.join(
        [os.path.expanduser("~/.npm-global/bin"), os.path.expanduser("~/.local/bin")]
    )
    return shutil.which(name, path=os.environ.get("PATH", "") + os.pathsep + extra)


def find_binary(name: str) -> str | None:
    """Return the executable path for a known browser, or None."""
    override = os.environ.get(f"JAK_BROWSER_BIN_{name.upper()}")
    if override and Path(os.path.expandvars(os.path.expanduser(override))).is_file():
        return str(Path(os.path.expandvars(os.path.expanduser(override))))
    spec = BROWSERS[name]
    system = platform.system()
    if system == "Windows":
        for raw in spec["win_paths"]:
            p = Path(os.path.expandvars(raw))
            if p.is_file():
                return str(p)
    elif system == "Darwin":
        for raw in spec["mac_paths"]:
            if Path(raw).is_file():
                return raw
    for cmd in spec["which"]:
        hit = _which(cmd)
        if hit:
            return hit
    return None


def detect() -> list[dict]:
    """Detect installed browsers, sorted by preference (chrome first)."""
    found = []
    for name in sorted(BROWSERS, key=lambda n: BROWSERS[n]["priority"]):
        binary = find_binary(name)
        if binary:
            found.append({"name": name, "label": BROWSERS[name]["label"], "path": binary})
    return found


def suggest(found: list[dict]) -> dict | None:
    """The browser to suggest: highest-priority detected one, else None."""
    return found[0] if found else None


def default_port() -> int:
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import jak_config

        return int(jak_config.load().int("cdp_port") or 9222)
    except Exception:  # noqa: BLE001
        return 9222


def default_profile_base() -> Path:
    if platform.system() == "Windows":
        return Path(os.path.expandvars(r"%USERPROFILE%"))
    return Path(os.path.expanduser("~/.config"))


def profile_for(base: Path, name: str) -> str:
    """Legacy isolated per-browser profile dir (opt-in via --isolated)."""
    if platform.system() == "Windows":
        return str(base / f"jak-browser-{name}")
    return str(base / f"jak-browser-{name}")


def launcher_name(name: str) -> str:
    return f"browser-debug-{name}.bat" if platform.system() == "Windows" else f"browser-debug-{name}.sh"


def render_launcher(name: str, binary: str, port: int, profile: str | None) -> str:
    """Launcher text. profile=None reuses the default profile (no --user-data-dir)."""
    label = BROWSERS[name]["label"]
    data_arg_win = f' --user-data-dir="%JAK_PROFILE%"' if profile else ""
    data_arg_sh = ' --user-data-dir="$JAK_PROFILE"' if profile else ""
    profile_block_win = (
        f'set "JAK_PROFILE={profile}"\r\n'
        'if not exist "%JAK_PROFILE%" mkdir "%JAK_PROFILE%"\r\n'
        if profile else ""
    )
    profile_block_sh = (
        f'JAK_PROFILE="{profile}"\n'
        'mkdir -p "$JAK_PROFILE"\n'
        if profile else ""
    )
    if platform.system() == "Windows":
        return (
            "@echo off\r\n"
            f"REM Generated by job-apply-kit browser_setup.py - launches {label} with remote debugging.\r\n"
            "REM Close normal browser windows first, then double-click the desktop shortcut.\r\n"
            f'set "JAK_PORT={port}"\r\n'
            f"{profile_block_win}"
            f'start "JAK {label} (debug)" "{binary}" --remote-debugging-port=%JAK_PORT%{data_arg_win}\r\n'
        )
    return (
        "#!/usr/bin/env bash\n"
        f"# Generated by job-apply-kit browser_setup.py - launches {label} with remote debugging.\n"
        "# Close normal browser windows first, then run this (or the desktop shortcut).\n"
        f'JAK_PORT="{port}"\n'
        f"{profile_block_sh}"
        f'exec "{binary}" --remote-debugging-port="$JAK_PORT"{data_arg_sh}\n'
    )


def default_desktop() -> Path:
    home = Path(os.path.expanduser("~"))
    candidates = [home / "Desktop"]
    if platform.system() == "Windows":
        candidates.append(home / "OneDrive" / "Desktop")
    for d in candidates:
        if d.is_dir():
            return d
    return candidates[0]


def shortcut_name(name: str) -> str:
    label = BROWSERS[name]["label"]
    if platform.system() == "Windows":
        return f"JAK {label} (debug).lnk"
    if platform.system() == "Darwin":
        return f"JAK {label} (debug).command"
    return f"jak-{name}-debug.desktop"


def create_shortcut(name: str, launcher: Path, desktop: Path, dry: bool) -> str:
    """Create a desktop shortcut to a launcher. Returns what was created."""
    label = BROWSERS[name]["label"]
    link = desktop / shortcut_name(name)
    if dry:
        return str(link)
    desktop.mkdir(parents=True, exist_ok=True)
    if platform.system() == "Windows":
        if dry:
            return str(link)
        ps = (
            "$ws = New-Object -ComObject WScript.Shell; "
            f"$s = $ws.CreateShortcut('{link}'); "
            f"$s.TargetPath = '{launcher}'; "
            f"$s.WorkingDirectory = '{launcher.parent}'; "
            f"$s.Description = 'Launch {label} with remote debugging for job-apply-kit'; "
            "$s.Save()"
        )
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps],
                capture_output=True, text=True, timeout=60, check=True,
            )
            return str(link)
        except Exception:  # noqa: BLE001  PowerShell/COM unavailable: plain .bat fallback
            fallback = desktop / f"JAK {label} (debug).bat"
            fallback.write_text(
                "@echo off\r\n"
                f'call "{launcher}"\r\n', encoding="utf-8",
            )
            return str(fallback)
    if platform.system() == "Darwin":
        if not dry:
            link.write_text(launcher.read_text(encoding="utf-8"), encoding="utf-8")
            link.chmod(link.stat().st_mode | stat.S_IEXEC)
        return str(link)
    content = (
        "[Desktop Entry]\n"
        "Type=Application\n"
        f"Name=JAK {label} (debug)\n"
        f"Comment=Launch {label} with remote debugging for job-apply-kit\n"
        f"Exec={launcher}\n"
        "Terminal=false\n"
        "Categories=Network;WebBrowser;\n"
    )
    if not dry:
        link.write_text(content, encoding="utf-8")
        link.chmod(link.stat().st_mode | stat.S_IEXEC)
    return str(link)


def parse_browsers(arg: str, found: list[dict]) -> list[dict]:
    want = [b.strip().lower() for b in arg.split(",") if b.strip()]
    if want == ["all"]:
        return found
    known = {f["name"] for f in found}
    for b in want:
        if b not in BROWSERS:
            raise SystemExit(f"unknown browser: {b} (choose from: {', '.join(BROWSERS)} or 'all')")
        if b not in known:
            raise SystemExit(f"{BROWSERS[b]['label']} was not detected on this machine (--list to check)")
    return [f for f in found if f["name"] in want]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true", help="detect browsers, print table + suggestion (exit 1 if none)")
    ap.add_argument("--json", action="store_true", help="with --list: machine-readable output")
    ap.add_argument("--browser", default="", help="'all' or comma-separated names (chrome,edge,brave,chromium)")
    ap.add_argument("--create", action="store_true", help="write launchers (+ desktop shortcuts) for --browser")
    ap.add_argument("--port", type=int, default=None, help="CDP port (default: config cdp_port, else 9222)")
    ap.add_argument("--out-dir", default=str(REPO), help="where to write launchers (default: kit repo root)")
    ap.add_argument("--profile", default="", help="explicit profile dir (adds --user-data-dir); default: reuse the browser's own default profile (recommended, already logged in)")
    ap.add_argument("--isolated", action="store_true", help="use a separate jak-browser-<name> profile instead of the default (only when the user asks for one)")
    ap.add_argument("--profile-base", default=str(default_profile_base()), help="parent dir for --isolated profiles")
    ap.add_argument("--desktop-dir", default=str(default_desktop()), help="where to create shortcuts")
    ap.add_argument("--no-shortcuts", action="store_true", help="write launchers only, no desktop shortcuts")
    ap.add_argument("--dry-run", action="store_true", help="print actions only")
    a = ap.parse_args(argv)

    found = detect()
    if a.json:
        print(json.dumps({"browsers": found, "suggested": (suggest(found) or {}).get("name")}, indent=2))
        return 0
    if a.list or (not a.create):
        if not found:
            print("no Chromium-based browser detected (looked for Chrome, Edge, Brave, Chromium).")
            print("Install one, then re-run --list. Downloads:")
            for n, url in DOWNLOADS.items():
                print(f"  {BROWSERS[n]['label']:15}{url}")
            return 1
        for f in found:
            mark = "  <-- suggested" if suggest(found)["name"] == f["name"] else ""
            print(f"{f['name']:10}{f['label']:18}{f['path']}{mark}")
        return 0

    if not a.browser:
        raise SystemExit("--create needs --browser <names|all> (see --list)")
    if not found:
        raise SystemExit("no Chromium-based browser detected; install one first (see --list)")
    if a.profile and a.isolated:
        raise SystemExit("--profile and --isolated cannot be combined (pick one)")
    port = a.port or default_port()
    out_dir = Path(os.path.expanduser(a.out_dir))
    desktop = Path(os.path.expanduser(a.desktop_dir))
    profile_base = Path(os.path.expanduser(a.profile_base))
    if not a.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
    for f in parse_browsers(a.browser, found):
        if a.profile:
            profile: str | None = str(Path(os.path.expandvars(os.path.expanduser(a.profile))))
        elif a.isolated:
            profile = profile_for(profile_base, f["name"])
        else:
            profile = None
        launcher = out_dir / launcher_name(f["name"])
        print(f"write {launcher}")
        print(f"  binary : {f['path']}")
        print(f"  port   : {port}")
        print(f"  profile: {profile if profile else '(browser default — already logged in)'}")
        if not a.dry_run:
            launcher.write_text(
                render_launcher(f["name"], f["path"], port, profile),
                encoding="utf-8", newline="",
            )
            if platform.system() != "Windows":
                launcher.chmod(launcher.stat().st_mode | stat.S_IEXEC)
        if not a.no_shortcuts:
            link = create_shortcut(f["name"], launcher.resolve(), desktop, a.dry_run)
            print(f"  shortcut: {link}")
    if a.profile or a.isolated:
        print("\nNext: double-click the desktop shortcut, log in once, leave the browser running.")
    else:
        print("\nNext: close normal browser windows first, then double-click the desktop")
        print("shortcut — it opens with your existing default profile (already logged in).")
        print("Leave the browser running.")
    print(f"Verify: curl http://127.0.0.1:{port}/json/version")
    return 0


if __name__ == "__main__":
    sys.exit(main())
