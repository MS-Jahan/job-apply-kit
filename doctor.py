#!/usr/bin/env python3
"""Check the tools job-apply-kit needs.

  ./doctor.sh [--mode tailor|apply|all] [--config PATH]

Prints OK / MISSING / WARN per check with an install hint. Exit 1 if a required
check for the chosen mode fails.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "skills" / "job-apply-core" / "scripts"))

results: list[tuple[str, str, str]] = []  # (status, label, hint)


def add(status: str, label: str, hint: str = "") -> None:
    results.append((status, label, hint))


def which(cmd: str) -> str | None:
    extra = os.pathsep.join([os.path.expanduser("~/.npm-global/bin"), os.path.expanduser("~/.local/bin")])
    hit = shutil.which(cmd, path=os.environ.get("PATH", "") + os.pathsep + extra)
    return hit or saved_tool_path(cmd)


def saved_tool_path(cmd: str) -> str | None:
    """Direct binary path recorded by install.py (tools.json)."""
    f = Path(os.path.expanduser(os.environ.get("JAK_TOOLS_FILE") or "~/.config/job-apply-kit/tools.json"))
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    base = cmd.lower().removesuffix(".exe")
    for tool, p in data.items():
        try:
            pp = Path(str(p))
        except Exception:  # noqa: BLE001
            continue
        if tool == cmd or pp.stem.lower() == base:
            if pp.is_file():
                return str(pp)
    return None


def on_path(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def show(cmd: str, hit: str) -> str:
    if on_path(cmd):
        return hit
    return hit + "  [not on PATH yet: open a fresh terminal]"


def run(cmd: list[str], timeout: int = 15) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip()
    except Exception as e:  # noqa: BLE001
        return 1, str(e)


def check_python() -> None:
    ok = sys.version_info >= (3, 9)
    add("OK" if ok else "MISSING", f"Python {sys.version.split()[0]}", "" if ok else "install Python 3.9+")
    for mod, pip in [("websocket", "websocket-client"), ("googleapiclient", "google-api-python-client"),
                     ("google.oauth2", "google-auth"), ("google_auth_oauthlib", "google-auth-oauthlib")]:
        try:
            found = importlib.util.find_spec(mod) is not None
        except ModuleNotFoundError:
            found = False
        add("OK" if found else "MISSING", f"python module {pip}", "" if found else f"pip install {pip}  (or: pip install -r requirements.txt)")


def check_latex() -> None:
    win = platform.system() == "Windows"
    t = which("tectonic")
    if t:
        add("OK", "tectonic", show("tectonic", t))
    elif which("pdflatex"):
        add("WARN", "tectonic missing, pdflatex found (fallback)", "winget install --id tectonic.tectonic -e" if win else "install tectonic: https://tectonic-typesetting.github.io")
    else:
        add("MISSING", "tectonic (or pdflatex)", "winget install --id tectonic.tectonic -e" if win else "install tectonic: https://tectonic-typesetting.github.io")
    if which("pdfinfo"):
        add("OK", "pdfinfo (poppler-utils)", show("pdfinfo", which("pdfinfo")))
    elif win:
        add("MISSING", "pdfinfo (poppler-utils)", "winget install --id oschwartz10612.Poppler -e  (or scoop/conda; see docs/BOOTSTRAP.md 2.3)")
    else:
        add("MISSING", "pdfinfo (poppler-utils)", "apt install poppler-utils | brew install poppler")
    pd = which("pandoc")
    add("OK" if pd else "WARN", "pandoc (optional, Markdown to DOCX/PDF)", show("pandoc", pd) if pd else "winget install --exact --id JohnMacFarlane.Pandoc" if win else "see docs/BOOTSTRAP.md 2.3 or https://pandoc.org/installing.html")


def check_config(cfg_path: str | None):
    try:
        import jak_config
    except Exception as e:  # noqa: BLE001
        add("MISSING", "jak_config.py importable", str(e))
        return None
    try:
        cfg = jak_config.load(cfg_path)
    except jak_config.ConfigError as e:
        add("MISSING", "config file", str(e))
        return None
    errors, warnings = cfg.check()
    for e in errors:
        add("MISSING", f"config: {e}", "edit your config.md (or ask your agent to fill it from your CV)")
    for w in warnings:
        add("WARN", f"config: {w}")
    if not errors:
        add("OK", f"config valid ({cfg.source})")
    return cfg


def skills_dirs() -> list[Path]:
    return [Path(os.path.expanduser(p)) for p in ("~/.claude/skills", "~/.config/opencode/skills", "~/.agents/skills")]


def check_skills() -> None:
    for name in ("job-apply-core", "humanizer"):
        found = any((d / name / "SKILL.md").is_file() for d in skills_dirs())
        add("OK" if found else "MISSING", f"skill {name} installed", "" if found else "run ./install.sh")


def check_google(cfg) -> None:
    gog = which("gog")
    token = os.environ.get("GOG_ACCESS_TOKEN")
    gog_ok = False
    if gog:
        acct = cfg.get("gog_account") if cfg else None
        if token:
            gog_ok = True
            add("OK", "gog found, GOG_ACCESS_TOKEN set (keyring bypassed)")
        else:
            cmd = [gog, "--no-input", "auth", "list"]
            code, out = run(cmd)
            if code == 0 and (not acct or acct in out):
                gog_ok = True
                add("OK", "gog can read its keyring" + (f" and knows {acct}" if acct else ""))
            else:
                add("WARN", "gog installed but cannot unlock/list accounts",
                    "file keyring needs its password env, or export GOG_ACCESS_TOKEN (1h) for headless use; see docs/EXTERNAL_TOOLS.md")
    else:
        add("WARN", "gog not found", "install gog (see docs/EXTERNAL_TOOLS.md) or rely on the python backend")
    tok_dir = Path(os.path.expanduser((cfg.get("google_token_dir") if cfg else None) or "~/.config/job-apply-kit/google"))
    py_ok = tok_dir.is_dir() and any(tok_dir.glob("*token*.json"))
    add("OK" if py_ok else "WARN", f"python Google backend token in {tok_dir}",
        "" if py_ok else "run google_setup.py to authorize (see docs/EXTERNAL_TOOLS.md)")
    backend = (cfg.get("google_backend") if cfg else "auto") or "auto"
    usable = (backend == "gog" and gog_ok) or (backend == "python" and py_ok) or (backend == "auto" and (gog_ok or py_ok))
    add("OK" if usable else "MISSING", f"a usable Google backend (google_backend={backend})",
        "" if usable else "set up gog or the python backend")


def check_browser(cfg) -> None:
    win = platform.system() == "Windows"
    node = which("node")
    node_hint = "winget install OpenJS.NodeJS.LTS (see docs/BOOTSTRAP.md 2.2)" if win else "install Node 18+ (see docs/BOOTSTRAP.md 2.2)"
    if node:
        code, out = run([node, "-v"])
        try:
            major = int(out.lstrip("v").split(".")[0])
        except ValueError:
            major = 0
        add("OK" if major >= 18 else "MISSING", f"Node {out}", "" if major >= 18 else node_hint)
    else:
        add("MISSING", "Node", node_hint)
    ab = which("agent-browser")
    add("OK" if ab else "MISSING", "agent-browser", show("agent-browser", ab) if ab else "npm install -g agent-browser@latest  (and put ~/.npm-global/bin on PATH)")
    try:
        import browser_setup
        found = browser_setup.detect()
    except Exception:  # noqa: BLE001
        found = []
    if found:
        names = ", ".join(f"{f['label']}" for f in found)
        add("OK", f"Chromium browser(s): {names}", "run browser_setup.py --create to make debug-mode shortcuts")
    else:
        add("WARN", "no Chromium browser found (Chrome/Edge/Brave/Chromium)",
            "install one (see docs/BOOTSTRAP.md §2) or set JAK_BROWSER_BIN_<NAME>; Firefox is not supported")
    port = (cfg.int("cdp_port") if cfg else None) or 9222
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=3) as r:
            ver = json.loads(r.read().decode()).get("Browser", "browser")
        add("OK", f"debug browser answers on port {port} ({ver})")
    except Exception:  # noqa: BLE001
        add("MISSING", f"debug browser on port {port}", "double-click a JAK debug shortcut (browser_setup.py --create) or start it by hand: --remote-debugging-port=%d (see docs/EXTERNAL_TOOLS.md §4)" % port)
    mcp = False
    candidates = [Path(os.path.expanduser("~/.claude.json")), Path(os.path.expanduser("~/.config/opencode/opencode.json"))]
    if os.environ.get("CLAUDE_CONFIG_DIR"):
        candidates.append(Path(os.path.expanduser(os.environ["CLAUDE_CONFIG_DIR"])) / ".claude.json")
    for override in ("JAK_CLAUDE_CONFIG", "JAK_OPENCODE_CONFIG", "OPENCODE_CONFIG"):
        if os.environ.get(override):
            candidates.append(Path(os.path.expanduser(os.environ[override])))
    for f in candidates:
        try:
            if "chrome-devtools" in f.read_text():
                mcp = True
        except OSError:
            pass
    add("OK" if mcp else "WARN", "chrome-devtools MCP registered (fallback)", "" if mcp else "optional: run ./install.sh --setup-mcp-only (creates the config when missing) or see docs/EXTERNAL_TOOLS.md §5")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", choices=["tailor", "apply", "all"], default="all")
    ap.add_argument("--config")
    a = ap.parse_args(argv)
    check_python()
    check_latex()
    cfg = check_config(a.config)
    check_skills()
    if a.mode in ("apply", "all"):
        check_google(cfg)
        check_browser(cfg)
    width = max(len(l) for _, l, _ in results) + 2
    for status, label, hint in results:
        print(f"{status:8}{label:{width}}{hint}")
    bad = [r for r in results if r[0] == "MISSING"]
    print(f"\n{len(bad)} required item(s) missing" if bad else "\nall required checks passed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
