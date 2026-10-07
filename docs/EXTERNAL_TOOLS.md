# External tools

Nothing below is vendored in this repository. Install what your chosen mode needs (`./doctor.sh --mode
tailor|apply|all` tells you exactly what is missing) and verify with the commands in each row.

## 1. Tool matrix

| Tool | Needed by | Required for | Install | Auth / config | Verify |
|---|---|---|---|---|---|
| Python 3.9+ | every script | all | see §3.5 (full agent runbook: `docs/BOOTSTRAP.md`) | — | `python3 -V` |
| Python packages (`requirements.txt`) | `jak_google.py`, python Google backend, CDP scripts | all | `pip install -r requirements.txt` | — | `python3 -c "import googleapiclient, google.oauth2, websocket"` |
| `tectonic` | compiling CV/resume/CL PDFs | tailor, apply | see §3.1 | — | `tectonic --version` |
| `pdflatex` (TeX Live) | fallback compiler | optional | distro TeX Live | — | `pdflatex --version` |
| `pandoc` | Markdown to DOCX/PDF path (resume-kit) | optional | see §3.7 | — | `pandoc --version` |
| `poppler-utils` (`pdfinfo`) | page-budget checks everywhere | tailor, apply | see §3.7 | — | `pdfinfo -v` |
| `gog` (gogcli) | primary Google backend: Gmail drafts, Drive, Sheets | apply (or use the python backend instead) | see §3.8 | `gog auth add <email>` | `gog --version`; `gog auth list` |
| Google account(s) | Gmail drafts, Drive uploads, Sheets tracker | apply | — | see §6 (account roles) | `./doctor.sh --mode apply` |
| Node 18+ | `agent-browser` | apply | see §3.6 | — | `node -v` |
| `agent-browser` (npm) | default browser driver for every apply/search skill | apply | `npm install -g agent-browser@latest`; put `~/.npm-global/bin` on `PATH` | attaches to your already-running debug browser | `agent-browser --version` |
| Debug browser (Chrome/Edge/Brave/Chromium) | agent-browser, chrome-devtools MCP, raw CDP | apply | see §3.9 + §4 (`browser_setup.py --create`) | start with remote debugging (see §4) | `curl -s http://127.0.0.1:<cdp_port>/json/version` |
| `chrome-devtools` MCP | fallback browser driver (console/network/performance/Lighthouse, uid-targeted work) | optional | `npx -y chrome-devtools-mcp@latest`; `install.sh` registers it automatically (see §5) | points at the same debug port | MCP tool list shows `mcp__chrome-devtools__*` |
| SearXNG MCP | JD/company search, first choice | optional | self-host or hosted instance + MCP config | instance URL | a search tool call returns results |
| Claude Code or OpenCode | runs the skills | all | see §3.10 | — | `claude --version` / `opencode --version` |

## 2. Install order (clean Linux box)

Per-OS commands, official download URLs, and the agent self-install procedure
live in `docs/BOOTSTRAP.md` — start there on Windows/macOS. The Linux fast path:

```bash
# 1. Python + pip deps
python3 -m pip install -r requirements.txt

# 2. LaTeX toolchain
# tectonic (see §3.1), or: sudo apt install texlive-latex-base poppler-utils pandoc

# 3. Node + agent-browser (only if you plan to run apply/search skills)
# install Node 18+ via your distro or nvm
npm install -g agent-browser@latest
echo 'export PATH="$HOME/.npm-global/bin:$PATH"' >> ~/.bashrc

# 4. Google backend: EITHER gog (see §3.2) OR the bundled python backend (see §3.3) — doctor.sh
#    accepts either one.

# 5. Install the kit's skills and register the fallback MCP server
./install.sh
./doctor.sh --mode all
```

macOS: the same steps work with Homebrew in place of `apt`. Windows: use WSL for the shell scripts
(`install.sh`, `doctor.sh`); `install.py`/`doctor.py` are plain Python and also run under native
Windows Python if you invoke them directly.

## 3. Install notes

### 3.1 tectonic

Single static binary; see [tectonic-typesetting.github.io](https://tectonic-typesetting.github.io) for
the current install command for your platform. No TeX Live install required. `pdflatex` (from a TeX
Live install) works as a fallback if `tectonic` is unavailable.

Windows options (pick one, then move `tectonic.exe` onto PATH and run
`tectonic --version` to verify):

- `winget install --id tectonic.tectonic -e` (same `-windows-msvc` zip as below)
- conda: `conda install tectonic`
- Direct zip from https://github.com/tectonic-typesetting/tectonic/releases
  (look for `x86_64-pc-windows-msvc.zip`), or the PowerShell drop script on the
  install page linked above.
- Fallback compiler on Windows: MiKTeX from https://miktex.org/download
  (or `choco install miktex`); macOS: MacTeX; Linux: TeX Live.

### 3.2 gog (primary Google backend)

A single Go binary that talks to Gmail, Drive, Sheets, Calendar, Docs and more. Get it from its
release page, then:

```bash
gog auth add you@example.com      # interactive OAuth, stores a refresh token
gog auth list                     # confirm it unlocked
```

Config keys: `gog_account` (which identity to use), `google_backend: gog` (or `auto`, which prefers
`gog` and falls back to the python backend).

**Known keyring issue**: `gog` stores its refresh tokens in a local keyring (`file` backend by
default). If `gog auth list` fails with something like `aes.KeyUnwrap(): integrity check failed`, the
keyring is locked or its password is unavailable in the current shell. Two ways around it:
- Run `gog auth keyring` to re-configure the backend (`auto`, `keychain` on macOS, or `file` with its
  password available in the environment).
- For headless/CI use, skip the keyring entirely: mint a short-lived access token and export
  `GOG_ACCESS_TOKEN` (valid about 1 hour, no auto-refresh). `jak_google.py` treats a set
  `GOG_ACCESS_TOKEN` as "gog is usable" without checking the keyring.

**Two flags the kit always passes** that are easy to miss if you call `gog` by hand: `drive share
--to anyone` and `gmail drafts delete` both refuse to run non-interactively without `--force`.
`jak_google.py` already passes it where needed; the kit never deletes a draft itself (only its own
tests do, during cleanup).

### 3.3 Python Google backend (bundled fallback)

`skills/job-apply-core/scripts/google_setup.py` is a self-contained OAuth setup script (ported from an
upstream Google-Workspace helper) that stores one token file per account under `google_token_dir`
(config key; default `~/.config/job-apply-kit/google/`).

```bash
python3 skills/job-apply-core/scripts/google_setup.py --client-secret /path/to/client_secret.json --account you@example.com
python3 skills/job-apply-core/scripts/google_setup.py --auth-url --account you@example.com
# open the URL, approve, copy the redirected code
python3 skills/job-apply-core/scripts/google_setup.py --auth-code "PASTED_CODE_OR_URL" --account you@example.com
python3 skills/job-apply-core/scripts/google_setup.py --check --account you@example.com
```

Already have a token from another tool (same Google API scopes)? Import it directly instead of
re-authorizing: `google_setup.py --import-token /path/to/token.json --account you@example.com`.

Scopes requested: `gmail.readonly`, `gmail.compose` (drafts only — never `gmail.send`), `drive`,
`spreadsheets`, plus optional `gmail.modify`/`calendar`/`contacts.readonly`/`documents` for the
general-purpose `google_api.py` tool. Config key `google_backend: python` forces this backend; `auto`
falls back to it when `gog` cannot unlock.

### 3.4 agent-browser

```bash
npm install -g agent-browser@latest
export PATH="$HOME/.npm-global/bin:$PATH"
agent-browser --version
```

Install **globally** (`-g`): the local-dependency path (`npm install
agent-browser` inside a project) is known-broken on Windows (postinstall never
downloads the native binary). After install, `agent-browser install` downloads
a bundled Chrome from Google's Chrome-for-Testing channel — optional for this
kit (we attach to your own debug browser via `agent-browser connect`), but it
is the upstream-supported way to get a working browser on a bare machine, and
`agent-browser doctor` diagnoses install problems. Docs:
https://agent-browser.dev/installation, repo:
https://github.com/vercel-labs/agent-browser.

Windows notes: supported (native x64 binary + Node.js fallback). If Windows
Defender quarantines the binary (a known ML-heuristic false positive on some
releases), restore/allow it and re-run; fallback search:
`agent-browser windows defender false positive github vercel-labs`.

Expect an `EBADENGINE` warning on Node < 24; the CLI still works. See
`skills/job-apply-core/references/agent-browser.md` for the full usage guide (connect, tab hygiene,
the never-kill-the-user's-browser rule, Google Picker file-upload workaround, daemon recovery).
Upstream repo (flag/source of truth when `--help` and our docs disagree):
https://github.com/vercel-labs/agent-browser.

### 3.5 Python 3.9+

- Windows: `winget install Python.Python.3.12`, or the installer from
  https://www.python.org/downloads/ (tick "Add python.exe to PATH"). Run
  everything in this repo with `py -3` wherever docs say `python3`.
- macOS: `brew install python@3.12` (https://brew.sh).
- Linux: `sudo apt install python3 python3-pip` (Debian/Ubuntu) or
  `sudo dnf install python3 python3-pip` (Fedora).
- Then: `python3 -m pip install -r requirements.txt`.
- Web-search fallback: `site:python.org downloads windows`, `python macos homebrew install`.

### 3.6 Node 18+

- Windows: `winget install OpenJS.NodeJS.LTS`, or the LTS installer from
  https://nodejs.org/en/download (sets PATH itself).
- macOS: `brew install node@22`.
- Linux: distro package or nvm — https://github.com/nvm-sh/nvm, then
  `nvm install --lts`.
- Web-search fallback: `nodejs download LTS windows`, `nodejs linux install nvm`.

### 3.7 poppler-utils (pdfinfo) and pandoc

- `pdfinfo` (required for page-budget checks): `sudo apt install poppler-utils`
  (Debian/Ubuntu), `brew install poppler` (macOS). Windows — any one of:
  `winget install --id oschwartz10612.Poppler -e`, `scoop install poppler`,
  `conda install poppler`, `choco install poppler` (if choco leaves only an
  unextracted archive, prefer one of the others), or the portable zip from
  https://github.com/oschwartz10612/poppler-windows/releases (unzip, add its
  `bin/` to PATH). Without `pdfinfo`, page counts fall back to reading the PDF
  directly. Fallback query: `poppler pdfinfo windows install`.
- `pandoc` (optional): OS package, or on Windows
  `winget install --exact --id JohnMacFarlane.Pandoc`, `choco install pandoc`,
  or the MSI/zip from https://github.com/jgm/pandoc/releases (full guide:
  https://pandoc.org/installing.html). Fallback query: `pandoc install download`.

### 3.8 gog binaries (primary Google backend)

Docs: https://gogcli.sh (install: https://gogcli.sh/install.html). Source and
release zips (including `gogcli_*_windows_amd64.zip` / `windows_arm64`):
https://github.com/openclaw/gogcli/releases/latest.

- macOS: `brew install openclaw/tap/gogcli`.
- Any OS with Go: `go install github.com/openclaw/gogcli/cmd/gog@latest`.
- Windows (no package manager): download the `windows_amd64` (or
  `windows_arm64`) zip from the releases page, extract `gog.exe`, put that
  directory on PATH.
- Then `gog auth add you@example.com` (interactive OAuth; needs a Google Cloud
  Desktop OAuth client — see §3.2). Fallback query: `gogcli github releases install gog`.

### 3.9 Chromium browsers (what browser_setup.py looks for)

Only Chromium-based browsers are supported (Firefox has no CDP driver in this
kit). Detection order and download pages:

| Browser | Download | Notes |
|---|---|---|
| Google Chrome | https://www.google.com/chrome/ | suggested when present |
| Microsoft Edge | https://www.microsoft.com/edge/download | preinstalled on most Windows machines |
| Brave | https://brave.com/download/ | — |
| Chromium | https://www.chromium.org/getting-involved/download-chromium/ | no auto-update; last resort |

`doctor.py` reports which of these it finds. `browser_setup.py --list` does the
detection for the agent; `--create` writes the debug-mode launchers (see §4).
Re-run detection after installing. Fallback query: `download chrome windows`,
`download brave browser`, etc.

### 3.10 Claude Code / OpenCode (the agent host)

Both run natively on Windows — no WSL required (WSL2 remains the only Windows
option with sandboxing support for Claude Code; OpenCode upstream notes rough
edges natively, so keep `docs/help/08-compatibility.md` translations in mind).

- Claude Code — PowerShell: `irm https://claude.ai/install.ps1 | iex`;
  CMD: `curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd`;
  or `winget install Anthropic.ClaudeCode` (does not auto-update — re-run
  `winget upgrade Anthropic.ClaudeCode` periodically). Install
  Git for Windows as well so Claude Code gets its Bash tool; without it, shell
  commands run via PowerShell instead. Reference: https://code.claude.com/docs/en/setup.
- OpenCode — `winget install --id SST.OpenCodeDesktop -e`, or
  `npm i -g opencode-ai@latest` (needs Node), or `scoop install opencode` /
  `choco install opencode`. Reference: https://opencode.ai/docs.
- Verify: `claude --version` / `opencode --version` in a fresh terminal
  (installers extend PATH mid-session, so open a new window first).

## 4. Starting your debug browser

Preferred (agent or human): generate launchers instead of typing commands.

```bash
python3 skills/job-apply-core/scripts/browser_setup.py --list
python3 skills/job-apply-core/scripts/browser_setup.py --browser chrome --create
```

`--list` prints every Chromium-based browser found and marks the suggestion.
`--create` writes one launcher per chosen browser into the kit directory
(`browser-debug-<name>.bat` on Windows, `.sh` elsewhere; `--port` overrides
the config `cdp_port`) plus a double-clickable desktop shortcut per browser.
The user clicks the shortcut, logs into LinkedIn/Facebook/Discord/BDJobs/Google
once in that profile, and leaves it running. Several browsers may be selected
(`--browser chrome,brave` or `--browser all`). Details and flags:
`docs/help/03-browser-setup.md`, `docs/BOOTSTRAP.md` §3.

Manual fallback (the launchers do exactly this). The kit never launches or
manages your browser. Start your own with remote debugging enabled, log in
to LinkedIn/Facebook/Discord/BDJobs/Google once in that profile, and leave it running.

| OS | Example |
|---|---|
| Linux | `google-chrome --remote-debugging-port=9222 --user-data-dir=$HOME/.config/jak-browser` (swap the binary for Chromium/Brave) |
| macOS | `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222 --user-data-dir="$HOME/.config/jak-browser"` |
| Windows | `"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\jak-browser"` |

Use `cdp_port` from your config (default 9222). Chrome requires a non-default `--user-data-dir` when
the debugging port is enabled, for your own security — use a persistent directory (not `/tmp`) so
logins survive restarts. Some Chromium-family browsers work without a dedicated profile; if attach
fails, add one. Raw-CDP scripts may also need `--remote-allow-origins=*` on older/stricter builds;
`cdp.py` already suppresses the Origin header, which works around this in most cases.

The macOS and Windows commands above are from upstream documentation and have not been tested by the
kit's author (Linux-only development machine) — if attach fails, check the debug port is actually
listening (`curl http://127.0.0.1:<port>/json/version`) before anything else.

## 5. chrome-devtools MCP (fallback browser driver)

`agent-browser` is the default for every skill; the chrome-devtools MCP is the fallback
(OPERATIONS.md#browser). The single source of truth for the server definition is
`mcp/servers.json` in this repo — `install.py` only renders the CDP port from your
config (`cdp_port`, default 9222) into it. Do not hardcode the command/args elsewhere;
if the upstream format changes, update `mcp/servers.json` and re-run
`./install.sh --setup-mcp-only`.

`install.sh` registers it automatically, creating the config files when they are
missing and never overwriting an existing entry (a `.jak-backup` copy is kept
before every merge). Re-run any time with `./install.sh --setup-mcp-only`
(`--no-mcp` skips it, `--dry-run` previews it).

Where the entries live (researched from the official docs, Oct 2026):

| Client | File | Key | Sources |
|---|---|---|---|
| Claude Code, user scope (all projects) | `~/.claude.json` (Windows `%USERPROFILE%\.claude.json`; `$CLAUDE_CONFIG_DIR/.claude.json` when that env var is set) | top-level `mcpServers` | `code.claude.com/docs/en/mcp-quickstart`, `code.claude.com/docs/en/mcp-servers.md` |
| Claude Code, project scope (team-shared) | `.mcp.json` in the project root (shipped in this repo) | top-level `mcpServers` | same as above |
| OpenCode, global | `~/.config/opencode/opencode.json` (`$OPENCODE_CONFIG` overrides) | `mcp` (v1) / `mcp.servers` (v2) | `opencode.ai/docs/config/`, `opencode.ai/docs/mcp-servers/` (v1), `opencode.ai/v2/docs/mcp-servers/` (v2) |

Do NOT put Claude Code servers in `~/.claude/settings.json`, `settings.local.json`,
`~/.claude/mcp.json`, or `%APPDATA%\Claude\mcp.json` (Claude Desktop path) — Claude
Code ignores them there. The preferred hands-off route is always
`claude mcp add -s user`, which is what `install.sh` uses when the `claude` CLI
exists; the direct file edit is only its fallback.

To do it by hand:

```bash
claude mcp add chrome-devtools -s user -- npx -y chrome-devtools-mcp@latest --browserUrl http://127.0.0.1:9222
```

Or as JSON (Claude Code `.mcp.json` / `~/.claude.json` top-level `mcpServers`):

```json
{"mcpServers": {"chrome-devtools": {"command": "npx", "args": ["-y", "chrome-devtools-mcp@latest", "--browserUrl", "http://127.0.0.1:9222"]}}}
```

OpenCode v1 (`opencode.json`):

```json
{"mcp": {"chrome-devtools": {"type": "local", "command": ["npx", "-y", "chrome-devtools-mcp@latest", "--browserUrl", "http://127.0.0.1:9222"]}}}
```

OpenCode v2 (same entry under `mcp.servers`):

```json
{"mcp": {"servers": {"chrome-devtools": {"type": "local", "command": ["npx", "-y", "chrome-devtools-mcp@latest", "--browserUrl", "http://127.0.0.1:9222"]}}}}
```

Both `--browserUrl` and the upstream-documented `--browser-url` spelling are accepted. `--autoConnect`
(Chrome 144+) exists upstream but is not used by the kit (it prompts for permission in a browser
dialog, which does not fit a headless/automated flow). Run `./install.sh --setup-mcp-only` any time to
(re-)register without touching skill files.

## 6. Account discipline

Two roles, never conflated (OPERATIONS.md#accounts):
- **`email_google`**: the account signed into the debug browser for Google Forms, and the account
  `gog`/the python backend authenticates as. Gmail drafts are created here.
- **`email_header`**: shown on resumes, cover letters, company portals and direct web forms. May be the
  same address as `email_google`, or a separate one.

If a Google Form shows the wrong account in its banner, use "Switch account" and pick `email_google`
before filling anything — uploads and submissions record the logged-in identity. A page reload can
silently revert the account; re-check the banner after every reload.

## 7. What this repo never stores

Tokens, keyring data, cookies, `.env` files, OAuth client secrets, Drive/Sheet ids. These live outside
the repo: `~/.config/job-apply-kit/` (config, Google tokens), your own browser profile (cookies,
logins), and `<workspace>/JDs/*/​.env` (site credentials, e.g. BDJobs). `.gitignore` excludes all of
them; `test_no_pii.py` scans for them before every commit when given a private pattern file.

## 8. Never-submit invariant

No tool choice changes it: every external application is filled and staged at the final Submit/Apply
button for the user to click, and every email is a Gmail draft, never sent. The one documented
exception (completing the BDJobs portal's own "Apply" button and its salary-warning "Apply Anyway"
modal) lives only in `bdjobs-full-run`'s SKILL.md, worded as an explicit, narrow, user-authorized
exception — not a general license to submit things.

## 9. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `gog auth list` fails with a keyring/decrypt error | keyring locked or password unavailable in this shell | `gog auth keyring`, or use `GOG_ACCESS_TOKEN` for this session |
| `doctor.sh` says no usable Google backend | neither `gog` unlocks nor a python-backend token exists | run `gog auth add` or `google_setup.py --auth-url` |
| `agent-browser tab list` shows only `about:blank` | attached to a fresh browser instead of your debug one | re-run `agent-browser connect <cdp_port>`; confirm the debug browser is actually listening on that port |
| chrome-devtools MCP calls fail with "received undefined" | known MCP parameter bug on some builds | fall back to `skills/job-apply-core/scripts/cdp.py` (raw CDP, last resort) |
| Sheet row lands in the wrong columns | a hand-rolled append instead of `sheet_append.py` | always use `python3 skills/job-apply-core/scripts/sheet_append.py append '<json-row>'` |
| A phone number or formula-looking cell shows `#ERROR!` in the tracker sheet | a write that used `USER_ENTERED` instead of `RAW` | shouldn't happen through this kit's scripts (they always write RAW); if you wrote the cell by hand, re-enter it as text |
| PDF won't compile | `tectonic` missing | install it (§3.1), or rely on the `pdflatex` fallback |
| Page count is off by one | spacing/density issue, not missing/extra content | tune `\linespread`/`itemsep`/`titlespacing` first (OPERATIONS.md#format); never invent content to fill a page or cut real content to shrink it |
