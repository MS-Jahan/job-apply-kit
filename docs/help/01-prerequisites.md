# 01 — Prerequisites

Back to [index](index.md). Full command reference: `docs/EXTERNAL_TOOLS.md` §§1–2.
Agent self-install runbook (official sources, per-OS commands, web-search
fallbacks): `docs/BOOTSTRAP.md`.

## What you need, by path

**Tailor-only** (resume/CV/cover-letter generation, no web automation):

- Python 3.9+ and `pip install -r requirements.txt` (all pure-Python packages, no compiler needed)
- `tectonic` (compiles the PDFs) and `pdfinfo` (verifies the 1-page / 2-page budgets)
- Claude Code or OpenCode to run the skills

**Full apply automation** needs everything above, plus:

- Node 18+ (24+ avoids an engine warning) and `agent-browser`
- A browser you start yourself with remote debugging on (Chrome, Chromium or Brave)
- A Google backend: either `gog`, or the bundled Python OAuth flow — [Google setup](02-google-setup.md)
- Accounts you log into inside that debug browser: Google, LinkedIn, Facebook, Discord, BDJobs

## Install per OS

**Linux** — system package manager for Python/Node, then follow `docs/EXTERNAL_TOOLS.md` §2 verbatim.

**macOS** — same steps with Homebrew in place of `apt`.

**Windows** — see [Compatibility](08-compatibility.md) first, then:

- Python: python.org installer or `winget install Python.Python.3.12`. Wherever any skill says
  `python3`, run `py -3` (or `python`) instead.
- Node: the nodejs.org LTS installer (adds `npm` to PATH automatically) or
  `winget install OpenJS.NodeJS.LTS`. Then `npm install -g agent-browser@latest`
  (global install only — the per-project local install is broken on Windows).
- PDFs: `winget install --id tectonic.tectonic -e`;
  `winget install --id oschwartz10612.Poppler -e` (or `scoop install poppler`);
  optional `winget install --exact --id JohnMacFarlane.Pandoc`.
- Agent host: Claude Code via `irm https://claude.ai/install.ps1 | iex` (plus Git
  for Windows for the Bash tool), or `winget install Anthropic.ClaudeCode`;
  OpenCode via `winget install --id SST.OpenCodeDesktop -e` or `npm i -g opencode-ai`.
  Full commands: `docs/BOOTSTRAP.md` §2.6.
- The `.sh` wrappers (`install.sh`, `doctor.sh`, `tests/run.sh`) need Git Bash or WSL. Without
  those, call the Python entry points directly: `python install.py`, `python doctor.py`.
- `curl.exe` ships with Windows 10/11, so the debug-port probe
  (`curl http://127.0.0.1:9222/json/version`) works in Command Prompt and PowerShell as written.

## Check your setup

```bash
./doctor.sh --mode tailor   # or: python doctor.py --mode tailor
./doctor.sh --mode apply    # everything, including Google + browser
```

Green means go. A MISSING line names the exact fix; a WARN line explains itself.
