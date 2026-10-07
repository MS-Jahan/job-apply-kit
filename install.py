#!/usr/bin/env python3
"""Install job-apply-kit skills into an agent skills directory.

  ./install.sh [skill ...]            install named skills (default: all) plus their requires.txt closure
  --target claude|opencode|agents     claude -> ~/.claude/skills (default; OpenCode reads it too)
                                      opencode -> ~/.config/opencode/skills, agents -> ~/.agents/skills
  --dest DIR                          explicit destination (overrides --target; used by tests)
  --link                              symlink files instead of copying (SKILL.md and docs are still rendered)
  --uninstall [skill ...]             remove what this installer put there (default: all in the manifest)
  --force                             overwrite a same-named skill not installed by this tool
  --dry-run                           print actions only
  --with-examples                     copy examples/templates into an empty templates dir
  --list                              list available skills
  --no-mcp                            skip MCP registration
  --setup-mcp-only                    only register MCP servers (no skill install)
  --update                            git pull --ff-only first, then install (refuses when
                                      the checkout is dirty; see "Updating the kit" in README.md)

MCP registration (mcp/servers.json is the single source of truth for the server
definitions; install.py only renders {{CDP_PORT}} into it and never hardcodes
server commands/args): for every server not already registered, run
`claude mcp add -s user ...` when the claude CLI exists (otherwise create or
merge ~/.claude.json directly, user scope), and create or merge the OpenCode
global config (~/.config/opencode/opencode.json) whether or not that file
already exists. Existing entries are never changed or overwritten.
Env overrides (used by tests): JAK_CLAUDE_BIN, JAK_CLAUDE_CONFIG,
JAK_OPENCODE_CONFIG (else OPENCODE_CONFIG), JAK_MANIFEST.

Tokens replaced in SKILL.md and other *.md files inside an installed skill:
  {{SKILL_DIR}}  absolute path of that installed skill
  {{CORE_DIR}}   absolute path of the installed job-apply-core skill (alias for job-apply-core)
  {{<NAME>_DIR}} absolute path of any OTHER installed skill in this run, NAME = the skill's directory
                 name upper-cased with hyphens turned to underscores (e.g. resume-kit -> RESUME_KIT_DIR)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
SKILLS_SRC = REPO / "skills"
TARGETS = {
    "claude": "~/.claude/skills",
    "opencode": "~/.config/opencode/skills",
    "agents": "~/.agents/skills",
}
MANIFEST = Path(os.path.expanduser(os.environ.get("JAK_MANIFEST") or "~/.config/job-apply-kit/installed.json"))
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
CORE = "job-apply-core"


def available() -> list[str]:
    if not SKILLS_SRC.is_dir():
        return []
    return sorted(p.name for p in SKILLS_SRC.iterdir() if (p / "SKILL.md").is_file())


def frontmatter(skill_md: Path) -> dict[str, str]:
    text = skill_md.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        raise SystemExit(f"{skill_md}: missing frontmatter")
    out: dict[str, str] = {}
    for line in m.group(1).splitlines():
        k = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if k:
            out[k.group(1)] = k.group(2).strip().strip("'\"")
    return out


def validate(name: str) -> None:
    fm = frontmatter(SKILLS_SRC / name / "SKILL.md")
    if fm.get("name") != name:
        raise SystemExit(f"{name}: frontmatter name {fm.get('name')!r} must equal the directory name")
    if not NAME_RE.match(name) or not (1 <= len(name) <= 64):
        raise SystemExit(f"{name}: invalid skill name (lowercase letters, digits, single hyphens)")
    d = fm.get("description", "")
    if not (1 <= len(d) <= 1024):
        raise SystemExit(f"{name}: description must be 1-1024 characters (got {len(d)})")


def requires(name: str) -> list[str]:
    f = SKILLS_SRC / name / "requires.txt"
    if not f.is_file():
        return []
    return [l.strip() for l in f.read_text().splitlines() if l.strip() and not l.startswith("#")]


def closure(names: list[str]) -> list[str]:
    seen: list[str] = []
    def visit(n: str) -> None:
        if n in seen:
            return
        if n not in available():
            raise SystemExit(f"unknown skill or missing dependency: {n}")
        for r in requires(n):
            visit(r)
        seen.append(n)
    for n in names:
        visit(n)
    return seen


def token_name(skill_name: str) -> str:
    if skill_name == CORE:
        return "CORE_DIR"
    return skill_name.upper().replace("-", "_") + "_DIR"


def render(text: str, skill_dir: Path, tokens: dict[str, str]) -> str:
    text = text.replace("{{SKILL_DIR}}", str(skill_dir))
    for token, path in tokens.items():
        text = text.replace("{{%s}}" % token, path)
    return text


def load_manifest() -> dict:
    if MANIFEST.is_file():
        return json.loads(MANIFEST.read_text())
    return {}


def save_manifest(m: dict) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(m, indent=2, sort_keys=True))


def install_one(name: str, dest: Path, tokens: dict[str, str], link: bool, force: bool, dry: bool, manifest: dict) -> None:
    src = SKILLS_SRC / name
    out = dest / name
    key = str(out)
    if (out.exists() or out.is_symlink()) and key not in manifest and not force:
        raise SystemExit(f"{out} exists and was not installed by job-apply-kit (use --force to replace)")
    print(f"install {name} -> {out}{' (link)' if link else ''}")
    if dry:
        return
    if out.exists() or out.is_symlink():
        shutil.rmtree(out) if out.is_dir() and not out.is_symlink() else out.unlink()
    files = []
    for p in sorted(src.rglob("*")):
        if p.is_dir() or "__pycache__" in p.parts:
            continue
        rel = p.relative_to(src)
        target = out / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if p.suffix == ".md":
            target.write_text(render(p.read_text(encoding="utf-8"), out, tokens), encoding="utf-8")
        elif link:
            target.symlink_to(p)
        else:
            shutil.copy2(p, target)
        files.append(str(rel))
    manifest[key] = {"skill": name, "files": files}


def uninstall(names: list[str], manifest: dict, dry: bool) -> None:
    keys = [k for k, v in manifest.items() if not names or v["skill"] in names]
    if not keys:
        print("nothing to uninstall")
    for k in keys:
        print(f"remove {k}")
        if not dry:
            p = Path(k)
            if p.is_dir() and not p.is_symlink():
                shutil.rmtree(p)
            elif p.exists() or p.is_symlink():
                p.unlink()
            del manifest[k]


def _templates_dir() -> Path:
    if os.environ.get("JAK_TEMPLATES_DIR"):
        return Path(os.environ["JAK_TEMPLATES_DIR"])
    try:
        sys.path.insert(0, str(SKILLS_SRC / CORE / "scripts"))
        import jak_config
        return jak_config.load().path("templates_dir")
    except Exception:  # noqa: BLE001
        return Path(os.environ.get("JAK_WORKSPACE") or os.getcwd()) / "templates"


def with_examples(dry: bool) -> None:
    ex = REPO / "examples" / "templates"
    tpl = _templates_dir()
    if not ex.is_dir():
        print("no examples/templates in this checkout")
        return
    if tpl.exists() and any(tpl.iterdir()):
        print(f"templates dir not empty, skipping examples: {tpl}")
        return
    print(f"copy example templates -> {tpl}")
    if not dry:
        shutil.copytree(ex, tpl, dirs_exist_ok=True)


def cdp_port() -> str:
    """Port from the user's config if readable, else 9222."""
    try:
        sys.path.insert(0, str(SKILLS_SRC / CORE / "scripts"))
        import jak_config
        return str(jak_config.load().int("cdp_port") or 9222)
    except Exception:  # noqa: BLE001
        return "9222"


def mcp_servers(port: str) -> dict:
    f = REPO / "mcp" / "servers.json"
    if not f.is_file():
        return {}
    data = json.loads(f.read_text())
    out = {}
    for name, spec in data.items():
        if name.startswith("_"):
            continue
        spec = json.loads(json.dumps(spec).replace("{{CDP_PORT}}", port))
        out[name] = spec
    return out


def claude_config_path() -> Path:
    """User-scope Claude Code config.

    Official docs (code.claude.com/docs/en/mcp-quickstart): user scope lives in
    ~/.claude.json under the top-level ``mcpServers`` key (Windows:
    %USERPROFILE%\\.claude.json). When $CLAUDE_CONFIG_DIR is set, Claude Code
    reads .claude.json from inside that directory instead.
    """
    override = os.environ.get("JAK_CLAUDE_CONFIG")
    if override:
        return Path(os.path.expanduser(override))
    cfg_dir = os.environ.get("CLAUDE_CONFIG_DIR")
    if cfg_dir:
        return Path(os.path.expanduser(cfg_dir)) / ".claude.json"
    return Path(os.path.expanduser("~/.claude.json"))


def opencode_config_path() -> Path:
    """Global OpenCode config.

    Official docs (opencode.ai/docs/config): global config is
    ~/.config/opencode/opencode.json. $OPENCODE_CONFIG points at a custom
    config file instead.
    """
    override = os.environ.get("JAK_OPENCODE_CONFIG") or os.environ.get("OPENCODE_CONFIG")
    if override:
        return Path(os.path.expanduser(override))
    return Path(os.path.expanduser("~/.config/opencode/opencode.json"))


def _claude_entry(spec: dict) -> dict:
    """Claude Code entry shape: {command, args[, env]} (stdio server).

    Same shape as the project-scope .mcp.json in this repo; Claude Code also
    accepts it under the top-level ``mcpServers`` key of ~/.claude.json.
    """
    entry: dict = {"command": spec["command"], "args": list(spec["args"])}
    if "env" in spec:
        entry["env"] = spec["env"]
    return entry


def _opencode_entry(spec: dict) -> dict:
    """OpenCode v1 entry shape: {type: local, command: [...], ...}."""
    return {"type": "local", "command": [spec["command"], *spec["args"]]}


def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError:
        return None
    except ValueError:
        return "INVALID"


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def register_claude_file(name: str, spec: dict, dry: bool) -> bool:
    """Create/merge ~/.claude.json directly. Returns True when handled."""
    path = claude_config_path()
    entry = _claude_entry(spec)
    cfg = _read_json(path)
    if cfg == "INVALID":
        print(f"mcp {name}: {path} is not plain JSON, add this by hand under top-level mcpServers: "
              + json.dumps({name: entry}))
        return True
    if cfg is None:
        print(f"mcp {name}: creating {path} (user scope, top-level mcpServers)")
        if not dry:
            _write_json(path, {"mcpServers": {name: entry}})
        return True
    if not isinstance(cfg, dict):
        print(f"mcp {name}: {path} has an unexpected shape, add this by hand under top-level mcpServers: "
              + json.dumps({name: entry}))
        return True
    if name in (cfg.get("mcpServers") or {}):
        print(f"mcp {name}: already registered in Claude Code ({path})")
        return True
    print(f"mcp {name}: registering in Claude Code ({path}; backup kept)")
    if not dry:
        shutil.copy2(path, str(path) + ".jak-backup")
        cfg.setdefault("mcpServers", {})[name] = entry
        _write_json(path, cfg)
    return True


def register_opencode_file(name: str, spec: dict, dry: bool) -> None:
    """Create/merge the OpenCode global config. Never overwrites entries.

    Supports both the v1 shape (mcp.<name>) from opencode.ai/docs/mcp-servers
    and the v2 shape (mcp.servers.<name>) from opencode.ai/v2/docs/mcp-servers:
    when the file already uses one shape, the entry goes there.
    """
    path = opencode_config_path()
    entry = _opencode_entry(spec)
    cfg = _read_json(path)
    if cfg == "INVALID":
        print(f"mcp {name}: {path} is not plain JSON (maybe JSONC with comments?), add this by hand: "
              + json.dumps({"mcp": {name: entry}}))
        return
    if cfg is None:
        print(f"mcp {name}: creating {path} (global config)")
        if not dry:
            _write_json(path, {"$schema": "https://opencode.ai/config.json",
                               "mcp": {name: entry}})
        return
    if not isinstance(cfg, dict):
        print(f"mcp {name}: {path} has an unexpected shape, add this by hand: "
              + json.dumps({"mcp": {name: entry}}))
        return
    mcp = cfg.setdefault("mcp", {})
    if not isinstance(mcp, dict):
        print(f"mcp {name}: {path} has a non-object 'mcp' key, add this by hand: "
              + json.dumps({"mcp": {name: entry}}))
        return
    if isinstance(mcp.get("servers"), dict):
        if name in mcp["servers"]:
            print(f"mcp {name}: already registered in OpenCode ({path})")
        else:
            print(f"mcp {name}: registering in OpenCode ({path}; backup kept)")
            if not dry:
                shutil.copy2(path, str(path) + ".jak-backup")
                mcp["servers"][name] = entry
                _write_json(path, cfg)
    else:
        if name in mcp:
            print(f"mcp {name}: already registered in OpenCode ({path})")
        else:
            print(f"mcp {name}: registering in OpenCode ({path}; backup kept)")
            if not dry:
                shutil.copy2(path, str(path) + ".jak-backup")
                mcp[name] = entry
                _write_json(path, cfg)


def _run(cmd: list[str]) -> int:
    import subprocess
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=60).returncode
    except Exception:  # noqa: BLE001
        return 1


def git_status(repo: Path) -> tuple[bool, list[str]]:
    """(is_git_checkout, dirty_paths). Never mutates anything."""
    import subprocess
    try:
        p = subprocess.run(["git", "-C", str(repo), "status", "--porcelain"],
                           capture_output=True, text=True, timeout=30)
    except Exception:  # noqa: BLE001
        return False, []
    if p.returncode != 0:
        return False, []
    return True, [l for l in p.stdout.splitlines() if l.strip()]


def git_update(dry: bool) -> int:
    """Pull latest kit code without clobbering local edits. Returns exit code."""
    import subprocess
    is_repo, dirty = git_status(REPO)
    if not is_repo:
        print("not a git checkout: update by downloading a fresh copy, or run plain ./install.sh")
        return 1
    if dirty:
        print("refusing to pull: this checkout has local changes:")
        for line in dirty[:20]:
            print(f"  {line}")
        if len(dirty) > 20:
            print(f"  ... and {len(dirty) - 20} more")
        print("Rules: never edit kit files in place. Personal data already lives outside")
        print("the repo (config.md, workspace templates/JDs). To update: commit your work,")
        print("move it out, or `git stash`, then re-run --update.")
        return 1
    print("git pull --ff-only")
    if dry:
        return 0
    try:
        p = subprocess.run(["git", "-C", str(REPO), "pull", "--ff-only"],
                           capture_output=True, text=True, timeout=120)
    except Exception as e:  # noqa: BLE001
        print(f"pull failed to start: {e}")
        return 1
    if p.returncode != 0:
        print((p.stdout + p.stderr).strip())
        print("pull failed (diverged branches?). Rebase or merge by hand, then run ./install.sh")
        return 1
    print((p.stdout.strip() or "already up to date."))
    return 0


def setup_mcp(dry: bool) -> None:
    servers = mcp_servers(cdp_port())
    if not servers:
        return
    if not shutil.which("npx"):
        print("WARN  npx not found: MCP servers registered here need Node/npx (install Node 18+)")
    claude = os.environ.get("JAK_CLAUDE_BIN") or shutil.which("claude")
    for name, spec in servers.items():
        if claude:
            base = [sys.executable, claude] if claude.endswith(".py") else [claude]
            if _run([*base, "mcp", "get", name]) == 0:
                print(f"mcp {name}: already registered in Claude Code")
            else:
                cmd = [*base, "mcp", "add", name, "-s", "user", "--", spec["command"], *spec["args"]]
                print(f"mcp {name}: registering in Claude Code (user scope)")
                if not dry:
                    if _run(cmd) == 0:
                        print("   ok")
                    else:
                        print("   CLI failed, falling back to direct file edit")
                        register_claude_file(name, spec, dry)
        else:
            register_claude_file(name, spec, dry)
        register_opencode_file(name, spec, dry)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("skills", nargs="*")
    ap.add_argument("--target", choices=TARGETS, default="claude")
    ap.add_argument("--dest")
    ap.add_argument("--link", action="store_true")
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--with-examples", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--no-mcp", action="store_true")
    ap.add_argument("--setup-mcp-only", action="store_true")
    ap.add_argument("--update", action="store_true")
    a = ap.parse_args(argv)

    if a.list:
        for n in available():
            print(n + ("  (requires: " + ", ".join(requires(n)) + ")" if requires(n) else ""))
        return 0
    if a.update and (a.uninstall or a.dest):
        raise SystemExit("--update cannot be combined with --uninstall or --dest")
    if a.setup_mcp_only:
        setup_mcp(a.dry_run)
        return 0
    if a.update:
        rc = git_update(a.dry_run)
        if rc != 0:
            return rc
    dest = Path(os.path.expanduser(a.dest or TARGETS[a.target]))
    manifest = load_manifest()
    if a.uninstall:
        uninstall(a.skills, manifest, a.dry_run)
        if not a.dry_run:
            save_manifest(manifest)
        return 0
    names = closure(a.skills or available())
    if not names:
        print("no skills found under skills/")
        return 1
    for n in names:
        validate(n)
    if CORE not in names and CORE in available():
        names.insert(0, CORE)
    tokens = {token_name(n): str(dest / n) for n in names}
    dest.mkdir(parents=True, exist_ok=True) if not a.dry_run else None
    for n in names:
        install_one(n, dest, tokens, a.link, a.force, a.dry_run, manifest)
    if not a.dry_run:
        save_manifest(manifest)
    if a.with_examples:
        with_examples(a.dry_run)
    if not a.no_mcp and not a.dest:
        setup_mcp(a.dry_run)
    print("\nNext: create your config (see config.example.md), then run ./doctor.sh")
    return 0


if __name__ == "__main__":
    sys.exit(main())
