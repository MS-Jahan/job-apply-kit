# Bootstrap runbook (humans and agents)

Zero-to-working setup for job-apply-kit. Humans read it top to bottom; an agent
treats section 0 as its standing procedure and uses the tables as its install
index. Command reference stays in `docs/EXTERNAL_TOOLS.md`; this page is the
order of operations.

## 0. Agent procedure (standing instructions)

When the user asks you to set up, fix, or verify their environment:

1. **Detect the OS** (section 1). Every install command below is OS-specific —
   never run an `apt` command on Windows or a `winget` command on Linux.
   On Windows, run everything in **Git Bash**, never PowerShell
   (`OPERATIONS.md#shell`): `;` chains, `& 'path'`, `$LASTEXITCODE` and
   `2>&1` behave differently there and stall or fail unix-style commands.
2. **Run the status check first, always:**
   `python doctor.py --mode all` (on Windows use `py -3`; the `.sh` wrappers
   need Git Bash or WSL). Work through each `MISSING` line top to bottom.
3. **For each missing tool, in this order:**
   a. Use the OS package manager command from section 2. On Windows 11,
      `winget` is built in — always try it first; reach for
      choco/scoop/conda only when winget has no package. On macOS use
      Homebrew, on Linux the distro manager (apt/dnf/pacman).
   b. If no package exists, download from the **official source URL** in
      section 2 — never from a random blog, mirror, or video description.
   c. If the URL or command no longer works (projects move), run a web search
      with the **fallback query** from section 2 and re-anchor on the official
      domain (python.org, nodejs.org, tectonic-typesetting.github.io,
      pandoc.org, github.com/openclaw/gogcli, github.com/jgm/pandoc,
      github.com/oschwartz10612/poppler-windows,
      github.com/vercel-labs/agent-browser, google.com/chrome,
      microsoft.com, brave.com, code.claude.com, opencode.ai).
4. **Verify after every install** with the Verify command in the table before
   moving on. A tool is done only when `doctor.py` flips it to OK.
5. **Browsers (section 3):** detect with `browser_setup.py --list`, tell the
   user what was found and which one you suggest, ask which to use (several
   allowed), then generate launchers + desktop shortcuts with `--create`.
   Never launch or kill the user's everyday browser yourself — hand them the
   shortcut and let them click it.
6. **Finish the kit:** `./install.sh` (or `python install.py`) registers MCP + PATH,
   then config — which asks for the CV and the tracker Sheet URL together (adopt or create) —
   see section 4. Skills run from this repo; nothing is copied anywhere.

Rules: ask before installing anything system-wide the user did not request;
prefer user-scope installs (pip `--user`, npm global prefix, portable zips,
winget user-scope packages). If an install needs admin rights or a reboot,
say so instead of pushing ahead.

### 0.1 Elevation (UAC) on Windows — what the agent needs to know

Windows has no always-on `sudo`. Elevation happens through a UAC consent
prompt: a command that needs admin rights either pops the prompt by itself
(machine-scope installers do this automatically) or fails with "access
denied". The agent **cannot click that prompt** — so:

- Default to installs that never elevate: `winget` user-scope packages,
  `scoop`, portable zips, `pip`/`npm -g` (both user-local), and anything under
  `%USERPROFILE%`. Avoid Chocolatey when winget/scoop cover the package —
  Chocolatey installs machine-wide and always needs elevation.
- Windows 11 ships a real `sudo.exe`, but it must first be enabled in
  Settings > System > For developers, and each use still shows a UAC prompt.
  Treat it as a user-side tool, not an agent tool.
- If a command fails with access denied, stop and tell the user exactly what
  to do: right-click Windows Terminal > Run as administrator, re-run the one
  command, then close that window. Never ask the user to turn UAC off.
- For this project specifically, nothing requires admin: Python/Node
  (user PATH), `pip`/`npm -g`, tectonic (zip into `%USERPROFILE%\.local\bin`),
  poppler/pandoc (winget user scope), `gog` (single binary), browsers
  (per-user install), launchers/shortcuts (repo dir + Desktop), and all kit
  scripts. Verified unelevated on the author's machine.

## 1. Detect the OS

```bash
python3 -c "import platform; print(platform.system(), platform.machine())"
# Windows -> install with winget (preferred) or Chocolatey, download .exe/.msi/.zip
# Darwin  -> install with Homebrew (https://brew.sh)
# Linux   -> install with the distro manager (apt, dnf, pacman)
```

## 2. Tool catalog

| Tool | Why the kit needs it | Official source | Verify |
|---|---|---|---|
| Python 3.9+ | every script | https://www.python.org/downloads/ | `python3 -V` (Windows: `py -3 -V`) |
| Python packages | Google backend, CDP scripts | `requirements.txt` (PyPI) | `python3 -c "import googleapiclient, google.oauth2, websocket"` |
| Node (latest LTS via a version manager) | runs `agent-browser` + MCP servers | https://github.com/nvm-windows/nvm (Windows) | `node -v` vs latest LTS |
| `agent-browser` | drives the debug browser | npm: `vercel-labs/agent-browser` | `agent-browser --version` |
| `tectonic` | compiles CV/resume/CL PDFs | https://tectonic-typesetting.github.io | `tectonic --version` |
| `poppler-utils` (`pdfinfo`) | page-budget checks | OS package (below) | `pdfinfo -v` |
| `pandoc` | Markdown to DOCX/PDF path | https://pandoc.org/installing.html | `pandoc --version` |
| `gog` | Gmail drafts, Drive, Sheets | https://github.com/openclaw/gogcli (docs: https://gogcli.sh) | `gog --version`; `gog auth list` |
| Chromium browser | debug-mode browsing | https://www.google.com/chrome/ etc. (section 3) | `browser_setup.py --list` |
| Claude Code or OpenCode | runs the skills | https://code.claude.com/docs/en/setup, https://opencode.ai/docs (section 2.6) | `claude --version` / `opencode --version` |

### 2.1 Python 3.9+

- Windows: `winget install Python.Python.3.12` (or the python.org installer;
  tick "Add python.exe to PATH"). Fallback query: `site:python.org downloads windows`.
- macOS: `brew install python@3.12`. Fallback query: `python macos homebrew install`.
- Linux: `sudo apt install python3 python3-pip` (Debian/Ubuntu) or
  `sudo dnf install python3 python3-pip` (Fedora).
- Then: `python3 -m pip install -r requirements.txt` (Windows: `py -3 -m pip install -r requirements.txt`).

### 2.2 Node (always latest LTS, via a version manager) and agent-browser

Standing rule: install Node through a version manager and always use the latest LTS —
never a frozen distro package or a one-off manual install, which rots (e.g. Node 20.15
broke `chrome-devtools-mcp`, which needs Node 20.19+). Verify with `node -v` against
https://nodejs.org/download/release/index.json (first entry with an `lts` codename).

- Windows: nvm for Windows v2 (https://github.com/nvm-windows/nvm, Microsoft/Google
  recommended; needs no admin for user scope): run the setup exe, then
  `nvm install lts && nvm use <version>`. The installer refuses while a manually
  placed Node exists (e.g. `D:\Program Files\nodejs` with no uninstaller): exit the
  installer, delete that folder (admin), remove its PATH entries (HKLM needs admin,
  HKCU does not), re-run setup. Never leave two Nodes on PATH — the stale one shadows
  the managed one, including for MCP servers spawned by agent hosts. Fallback query:
  `nvm windows install latest LTS`.
- macOS: `brew install node@22` only as fallback; preferred is nvm
  (https://github.com/nvm-sh/nvm): `nvm install --lts`. Fallback query:
  `nodejs macos install`.
- Linux: nvm (https://github.com/nvm-sh/nvm): `nvm install --lts` (distro packages
  freeze old minors — avoid). Fallback query: `nodejs linux install nvm`.
- After any Node/PATH change: already-running agent hosts keep their old environment
  (a child MCP spawn then fails with `'npx' is not recognized`). Fully restart agent
  hosts from a fresh terminal, or harden the MCP registration by replacing the bare
  `npx` command with the absolute npx path (nvm's `.nodejs` shim dir is stable across
  version switches). Verification flow: `docs/EXTERNAL_TOOLS.md` §5.1.
- Then, always **globally** (`-g`; the per-project local install is
  known-broken on Windows): `npm install -g agent-browser@latest` and put the
  global bin dir on PATH (`~/.npm-global/bin` on Linux/macOS; automatic on
  Windows). If npm blocks the postinstall (allowScripts policy), re-run with
  `npm install -g --allow-scripts=agent-browser` (or
  `npm config set allow-scripts=agent-browser --location=user` first). Optionally
  `agent-browser install` for a bundled Chrome (Chrome-for-Testing channel) — the kit
  attaches to your own debug browser anyway. If Windows Defender quarantines the
  binary, restore/allow it and re-run. Details: `docs/EXTERNAL_TOOLS.md` section 3.4.
  Upstream repo for flag changes: https://github.com/vercel-labs/agent-browser.

### 2.3 tectonic, poppler-utils, pandoc (all available on Windows)

- `tectonic` (single static binary, no TeX Live needed): Windows:
  `winget install --id tectonic.tectonic -e`, `conda install tectonic`, or the
  `x86_64-pc-windows-msvc.zip` from
  https://github.com/tectonic-typesetting/tectonic/releases
  (move `tectonic.exe` onto PATH). Unix: the `drop-sh` one-liner at
  https://tectonic-typesetting.github.io/en-US/install.html.
  Fallback (any OS): `pdflatex` — Windows via MiKTeX
  (https://miktex.org/download or `choco install miktex`), macOS via MacTeX,
  Linux via TeX Live.
- `poppler-utils` (`pdfinfo`, required for page budgets): Windows:
  `winget install --id oschwartz10612.Poppler -e`, `scoop install poppler`,
  `conda install poppler`, `choco install poppler` (if choco leaves an
  unextracted archive, use one of the others), or the portable zip from
  https://github.com/oschwartz10612/poppler-windows/releases.
  macOS: `brew install poppler`. Linux: `sudo apt install poppler-utils`.
  Without it, page counts fall back to reading the PDF directly.
- `pandoc` (optional): Windows: `winget install --exact --id JohnMacFarlane.Pandoc`,
  `choco install pandoc`, or the MSI from https://github.com/jgm/pandoc/releases
  (guide: https://pandoc.org/installing.html). macOS/Linux: OS package.

### 2.4 gog (primary Google backend)

- Docs: https://gogcli.sh (install page: https://gogcli.sh/install.html).
  Releases (Windows `gogcli_*_windows_amd64.zip`, macOS, Linux):
  https://github.com/openclaw/gogcli/releases/latest.
- macOS: `brew install openclaw/tap/gogcli`. Any OS with Go:
  `go install github.com/openclaw/gogcli/cmd/gog@latest`.
- After install: needs a Google Cloud Desktop OAuth client + `gog auth add`
  (interactive, user does this). The bundled Python backend
  (`google_setup.py`) is the no-binary alternative — see
  `docs/EXTERNAL_TOOLS.md` section 3.3.
- Fallback query: `gogcli github releases install gog`.

### 2.5 Chromium browsers

Covered in section 3 below. Firefox is not supported (no CDP driver in the
kit). If no browser is found, point the user at the official download pages
and re-run detection afterwards.

### 2.6 Claude Code / OpenCode on Windows (both run natively, no WSL needed)

- Claude Code — PowerShell: `irm https://claude.ai/install.ps1 | iex`;
  or `winget install Anthropic.ClaudeCode` (no auto-update — re-run
  `winget upgrade Anthropic.ClaudeCode` periodically). Also install
  Git for Windows so Claude Code gets its Bash tool; without it, shell
  commands run via PowerShell. Reference: https://code.claude.com/docs/en/setup.
- OpenCode — `winget install --id SST.OpenCodeDesktop -e`, or
  `npm i -g opencode-ai@latest`, or `scoop install opencode` /
  `choco install opencode`. Reference: https://opencode.ai/docs.
- Verify in a fresh terminal (installers extend PATH mid-session):
  `claude --version` / `opencode --version`.

## 3. Debug browser (agent-driven setup)

The kit never launches or kills the user's browser. It attaches to a browser
the user started with remote debugging. The agent sets this up with:

```bash
python3 skills/job-apply-core/scripts/browser_setup.py --list
```

- Prints every Chromium-based browser found (Chrome, Edge, Brave, Chromium)
  with install paths and marks the suggested one (Chrome first, then Edge,
  Brave, Chromium). Exit 1 + download links when none is found.
- The agent tells the user what was found, recommends the suggested browser,
  and asks which to use. Several may be selected.
- Then, for the chosen names:

```bash
python3 skills/job-apply-core/scripts/browser_setup.py --browser chrome,brave --create
```

This writes one launcher per browser into the kit directory
(`browser-debug-chrome.bat` on Windows, `browser-debug-chrome.sh` on
Linux/macOS — port defaults to config `cdp_port`, override with `--port`),
each starting its browser with `--remote-debugging-port` on the user's
EXISTING default profile (no `--user-data-dir`, no fresh profile, no second
login), plus a double-clickable shortcut for each on the desktop
(`JAK <label> (debug).lnk` / `.desktop` / `.command`).
`--dry-run` previews, `--no-shortcuts` skips the desktop links,
`--desktop-dir` / `--out-dir` relocate the outputs. Only when the user
explicitly asks for a separate profile, regenerate with `--profile <dir>`
(or `--isolated` for the legacy `jak-browser-<name>` dir) — the agent edits
the launcher/shortcut, never the user.

The user closes normal browser windows first, clicks the shortcut (it opens
with the existing default profile, already logged in), and leaves the
browser running. The agent verifies with
`curl http://127.0.0.1:9222/json/version` (Windows: `curl.exe`) and
`agent-browser connect 9222 && agent-browser tab list`.

**Never start the debug session while the user's normal browser is still
running** — the flag is silently ignored by the live instance and the agent
ends up attached to the wrong window (or nothing). The guard flow is:

1. `browser_setup.py --browser <name> --check-running` (exit 2 = running).
   `--create` prints the same WARNING automatically.
2. When it reports RUNNING, relay the script's message: the browser may be
   running with unsaved work — ask the user to save everything, close ALL
   its windows, and confirm. Wait for that confirmation; never kill the
   browser yourself.
3. Only then start it: `browser_setup.py --browser <name> --launch`
   (refuses with exit 2 while running, starts the launcher detached when
   closed), or tell the user to double-click the desktop shortcut.
4. Verify with `curl http://127.0.0.1:9222/json/version`.

Manual commands for every OS are in `docs/EXTERNAL_TOOLS.md` section 4;
the click-through guide is in `docs/help/03-browser-setup.md`.

## 4. Finish the kit

```bash
./install.sh                    # or: python install.py  (registers MCP servers, PATH, tools.json)
python doctor.py --mode all     # or: py -3 doctor.py --mode all
```

Then the personal config (`config.example.md` is the template; easiest is
telling the agent "set up my job-apply-kit config from my CV at <file/url>").
The debug browser (§3 above) must be running BEFORE the config step — CVs
living in Google Docs can only be read through it (plain web fetch returns a
truncated page), so the agent routes every CV through
`cv_fetch.py` first. That same flow then asks for the tracker Sheet URL (adopted via
`sheet_init.py --adopt`, or created fresh with `sheet_init.py` when the user has none —
pasted into config `sheet_url`), then `/create-template`.

Later, to pull new kit code and re-run setup in one step:
`python install.py --update` (refuses when the checkout is dirty — rules in
the README "Updating the kit" section). Skills run in place, so no reinstall step exists.

## 5. When the internet moves on

Every URL above was live when written. If one rots, the agent procedure is:
search the fallback query, pick the official domain result, and update this
file plus `docs/EXTERNAL_TOOLS.md` so the next run works. `install.py` reads
server definitions from `mcp/servers.json` (never hardcode them), and
`doctor.py` is the ground truth for "what is still missing".
