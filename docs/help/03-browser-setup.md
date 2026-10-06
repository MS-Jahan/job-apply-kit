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

## Step 1 — start your own debug browser

The kit never launches or kills your browser. Start it yourself with remote debugging, log into your
sites once in that profile, and leave it running:

| OS | Example |
|---|---|
| Linux | `google-chrome --remote-debugging-port=9222 --user-data-dir=$HOME/.config/jak-browser` |
| macOS | `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222 --user-data-dir="$HOME/.config/jak-browser"` |
| Windows | `"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\jak-browser"` |

Use a persistent profile directory (not a temp dir) so logins survive restarts. The macOS/Windows
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
(applies to every project) and in OpenCode's config when that file exists. It never overwrites an
existing registration. Re-run any time with `./install.sh --setup-mcp-only`. So in the normal flow
there is nothing to configure by hand.

**Manual** (if you skipped it with `--no-mcp`, or want to verify):

```bash
claude mcp add chrome-devtools -s user -- npx -y chrome-devtools-mcp@latest --browserUrl http://127.0.0.1:9222
```

JSON equivalents for `.mcp.json` / `opencode.json` are in `docs/EXTERNAL_TOOLS.md` §5. Point it at the
same debug port as `agent-browser`.
