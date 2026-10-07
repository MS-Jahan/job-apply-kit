# 03 — Browser setup (agent-browser, debug browser, MCP fallback)

Back to [index](index.md). Command reference: `docs/EXTERNAL_TOOLS.md` §§3.4, 4, 5.

## The three layers (in the order skills use them)

1. **`agent-browser` (default).** A Node CLI (upstream: `vercel-labs/agent-browser`, ships Windows,
   macOS and Linux builds) that drives a browser over the Chrome DevTools Protocol: open tabs, read
   pages, click, type, upload files, screenshot. Every search/apply skill uses it first.
2. **chrome-devtools MCP (fallback).** Used only when `agent-browser` cannot drive the page, or for
   MCP-only capabilities (console/network inspection, performance trace, Lighthouse). Auto-registered
   or manual — see below.
3. **Raw CDP scripts (last resort).** `skills/job-apply-core/scripts/cdp.py` plus
   `picker_upload.py` for Google Picker file inputs. Plain Python, no extra install beyond
   `requirements.txt`.

## Step 1 — detect, choose, generate shortcuts (preferred)

The agent does this with you — Firefox is not supported, only Chromium-based
browsers (Chrome, Edge, Brave, Chromium):

```bash
python3 skills/job-apply-core/scripts/browser_setup.py --list
```

This prints every supported browser found on the machine and marks the
suggestion (Chrome first, then Edge, Brave, Chromium). Tell the agent which to
use — several allowed — then it runs:

```bash
python3 skills/job-apply-core/scripts/browser_setup.py --browser chrome --create
```

That writes one launcher per browser into the kit directory
(`browser-debug-<name>.bat` on Windows, `.sh` elsewhere) plus a
double-clickable desktop shortcut each (`JAK <label> (debug)`). The launcher
reuses the browser's existing default profile — no fresh profile, no second
login. Close normal browser windows first, click the shortcut, leave it
running. Only when the user explicitly asks for a separate profile, regenerate
with `--profile <dir>` (or `--isolated`) — the agent edits the launcher or
shortcut, never the user. Verify:

```bash
curl http://127.0.0.1:9222/json/version
agent-browser connect 9222 && agent-browser tab list   # your real tabs = attached
```

Flags: `--browser all` or `--browser chrome,brave`, `--port` (default: config
`cdp_port`), `--profile <dir>` / `--isolated` for a separate profile only when
the user asks, `--dry-run` to preview, `--no-shortcuts` for launchers only.
Full agent runbook: `docs/BOOTSTRAP.md` §3.

**Before starting: the browser must be fully closed.** Run
`browser_setup.py --browser <name> --check-running` — when it says RUNNING,
tell the user their browser appears to be running, ask them to save their
work and close ALL its windows, and wait for confirmation before continuing.
`--launch` enforces the same guard (refuses with exit 2 while running).
The agent never closes or kills the user's browser.

## Step 1b — manual start (fallback)

If you prefer typing the command yourself (this is exactly what the generated
launchers do — default profile, already logged in; close normal browser
windows first so the flag takes effect on the default profile):

| OS | Example |
|---|---|
| Linux | `google-chrome --remote-debugging-port=9222` |
| macOS | `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222` |
| Windows | `"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222` |

Only when the user asks for a separate profile, append
`--user-data-dir=<persistent-dir>` (not a temp dir, so logins survive
restarts): e.g. `$HOME/.config/jak-browser` on Linux,
`"%USERPROFILE%\jak-browser"` on Windows. The macOS/Windows
commands are untested by the kit's author — if attach fails, first check the port is listening:
`curl http://127.0.0.1:9222/json/version`. On Windows, close Chrome before reusing a named profile if
files are locked. Running the agent inside WSL2 while Chrome runs on Windows works: from WSL2,
`localhost:9222` reaches the Windows side — see [Compatibility](08-compatibility.md).

## Step 2 — install and attach agent-browser

```bash
npm install -g agent-browser@latest
export PATH="$HOME/.npm-global/bin:$PATH"   # Linux/macOS; the Windows installer sets PATH itself
agent-browser connect 9222
agent-browser tab list                       # your real tabs = attached to the right browser
```

If `tab list` shows only `about:blank`, you attached to a fresh browser instead of your debug one —
re-run `connect` against the right port. Agent rule, always: never close a tab you did not open,
never kill the user's browser. Full usage guide:
`skills/job-apply-core/references/agent-browser.md`.

## Step 3 — MCP fallback: auto-configured, with a manual path

**Auto:** `./install.sh` registers the chrome-devtools MCP for you — user scope in Claude Code
(`~/.claude.json`, top-level `mcpServers`) and global config in OpenCode
(`~/.config/opencode/opencode.json`). Missing files are created; existing entries are
never overwritten. Re-run any time with `./install.sh --setup-mcp-only`. So in the normal flow
there is nothing to configure by hand. The server definition always comes from
`mcp/servers.json` — that file is the JSON format source.

**Manual** (if you skipped it with `--no-mcp`, or want to verify):

```bash
claude mcp add chrome-devtools -s user -- npx -y chrome-devtools-mcp@latest --browserUrl http://127.0.0.1:9222
```

JSON equivalents for `.mcp.json` / `opencode.json` are in `docs/EXTERNAL_TOOLS.md` §5. Point it at the
same debug port as `agent-browser`.

**If the MCP fails to start** (toast/log like `MCP server process exited with code 1: 'npx' is not
recognized`, or tools never appear): the registration alone proves nothing — run the three-layer
check in `docs/EXTERNAL_TOOLS.md` §5.1 (config entry → binary launches → live handshake). The two
known causes, both hit in practice:
1. Node below the MCP's floor (`does not support Node vX`) — fix Node first (§3.6, latest LTS via
   nvm), never the MCP config.
2. `'npx' is not recognized` — the agent host was started before the Node PATH change, so its
   environment can't resolve the bare `npx`. Harden by replacing the bare `npx` command in both
   registrations with the absolute npx path (nvm's `.nodejs` shim dir is stable across version
   switches), then fully restart the host. A host restarted from a stale terminal keeps the old
   PATH — open a fresh terminal first.
