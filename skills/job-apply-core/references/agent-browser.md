# agent-browser + CDP: agent guidelines

How AI agents should use `agent-browser` to drive an already-running browser
via CDP (Chrome DevTools Protocol). 

> **When to use it:** by DEFAULT for all browser work (saved feeds, portals, Google Forms, page
> reading). The chrome-devtools MCP is the fallback: reach for it only when `agent-browser` hits
> difficulty (attach keeps failing, the daemon cannot be recovered, commands cannot drive the page)
> or the step needs an MCP-only capability (console/network inspection, performance trace,
> Lighthouse audit, uid-targeted element work). If this guide and `agent-browser --help` ever
> disagree, trust `--help` (the CLI is the source of truth) and fix this file. See OPERATIONS.md#browser.

## 1. Install / update

```bash
export PATH="$HOME/.npm-global/bin:$PATH"
agent-browser --version          # check installed version
npm list -g agent-browser        # check registered version
npm install -g agent-browser@latest   # update
```

- On Windows, run every command below in **Git Bash** (`OPERATIONS.md#shell`),
  never PowerShell: PowerShell converts the CLI's stderr notices (for example
  `[agent-browser] launched browser`) into `NativeCommandError` failures and
  stalls unix-style chains. First line in Git Bash:
  `export PATH="$(cygpath "$APPDATA/npm"):$PATH"` (replaces the
  `~/.npm-global/bin` export above — same idea, Windows npm location).

- `which agent-browser` may fail if `~/.npm-global/bin` is not on PATH — always
  export PATH first (binary lives at `~/.npm-global/bin/agent-browser`).
- Expect an `EBADENGINE` warning if node < 24; the CLI still works.
- Refresh command knowledge after an update: `agent-browser --help`,
  `agent-browser state --help`. Prefer `agent-browser skills get core --full`
  over guessing flags.

## 2. Golden rule: never kill the user's browser

- Before doing anything, confirm the debug browser is alive and identify it:
  ```bash
  ss -tlnp | grep <cdp_port>
  ps -o pid,comm,args -p <BROWSER_PID>
  ```
- The user's debug browser (for example `chrome --remote-debugging-port=9222` on
  their default profile, already logged in)
  must never receive `kill`, `pkill`, or `agent-browser close --all`.
- `close --all` and `pkill -f agent-browser-chrome-` are only safe against
  agent-owned Chromium (`--user-data-dir=/tmp/agent-browser-chrome-*`,
  `--remote-debugging-port=0`). Always verify the PID/cmdline first.

## 3. Connect via CDP (reuse logins, extensions, VPN)

You do **not** need to export cookies/state to reuse a logged-in profile.
Attach to the running browser instead — extensions, VPN, and sessions stay intact.

**Chain commands.** Run related `agent-browser` steps in a single shell call
with `&&` instead of one command per bash invocation:

```bash
export PATH="$HOME/.npm-global/bin:$PATH"
agent-browser connect <cdp_port> && agent-browser tab list && agent-browser tab new && timeout 60 agent-browser open https://example.com && timeout 30 agent-browser snapshot -c
```

```bash
# Bind once per session (recommended); later commands target it automatically
agent-browser connect <cdp_port>

# Then work as usual
agent-browser tab list
agent-browser open https://example.com
agent-browser snapshot
```

Per-command alternative (no persistent bind):

```bash
agent-browser --cdp <cdp_port> open https://example.com
agent-browser --cdp <cdp_port> snapshot
# or: --cdp "http://localhost:<cdp_port>"
```

Auto-detect alternative: `agent-browser --auto-connect <command>`
finds a browser on the default debug ports (incl. 9222).

Verify the attach actually landed on the user's browser:

```bash
curl -s http://localhost:<cdp_port>/json/version | head -c 500
agent-browser tab list   # should show the user's real tabs
```

If `tab list` shows only `about:blank`, you launched a fresh browser —
re-run `connect <cdp_port>`.

## 3b. Google Docs: always read the lightweight view

A `/edit` URL loads a JS canvas editor — snapshots come back near-empty and
plain fetches return a truncated shell (verified live: 181 KB of JS, words
missing). Rewrite EVERY Google Doc link before reading:

```
https://docs.google.com/document/d/<DOC_ID>/edit...
→ https://docs.google.com/document/d/<DOC_ID>/mobilebasic
```

`agent-browser tab new` → `open <mobilebasic-url>` → `snapshot` to the last
line. The mobile view is plain HTML holding the full text (verified: strips
to the same words as the txt export). Plain-fetch fallback for public docs:
`https://docs.google.com/document/d/<DOC_ID>/export?format=txt` returns the
whole document as text (private docs need the logged-in browser instead).
This applies everywhere — CV setup, web search results, any doc reading —
not just one skill. `cv_fetch.py` prints both URLs for any doc link.

## 4. Tab hygiene — don't hijack the user's tabs

- `open <url>` navigates the **currently selected tab**. Always open a fresh tab
  first when the user is active:
  ```bash
  agent-browser tab new        # creates + selects a blank tab (→ [tN])
  agent-browser open <url>
  ```
- Confirm selection with `agent-browser tab list` (selected tab is marked `→`).
- To work in the background without stealing focus, add `--pin-tab`:
  ```bash
  agent-browser --cdp <cdp_port> --pin-tab open https://example.com
  ```
- Leave verification tabs open at the end (report their IDs) or close only tabs
  you created: `agent-browser tab close <n>`.

## 5. State save/load vs CDP attach — pick correctly

| Goal | Method |
|---|---|
| Reuse a live logged-in browser right now | CDP attach (`connect <cdp_port>` / `--cdp <cdp_port>`) |
| Persist auth for later / headless replay | `agent-browser --auto-connect state save ./auth.json`, then `agent-browser --state ./auth.json open <url>` |
| Survive restarts in one project | `--session <name> --restore` auto-save/restore |

State commands: `state save <path>`, `state load <path>`, `state list`,
`state show <file>`. A healthy save is tens–hundreds of KB (empty ≈ problem).

## 6. Checking login state (Facebook / LinkedIn pattern)

1. `tab new` → `open <url>` → wait for navigation (`✓ Title` + URL line).
2. `get url` + `get title` — logged-in Facebook stays at
   `https://www.facebook.com/` ("Facebook"); logged-out redirects to a login
   page. Logged-in LinkedIn lands on `https://www.linkedin.com/feed/...`
   ("Feed | LinkedIn").
3. `snapshot -c` (compact) — look for positive signals, never type into forms:
   - Facebook: "Search Facebook", Home/Reels/Marketplace/Groups/Gaming nav,
     Messenger, Notifications, "Your profile", profile name link.
   - LinkedIn: Home/My Network/Jobs/Messaging/Notifications/Me nav, profile
     sidebar with name + headline.
4. Read-only: `snapshot`, `get`, `find`, `screenshot`. Do not click Like/Post/
   Connect/Submit or change any setting during a login check.

## 7. Timeouts and troubleshooting

- Wrap every call: `timeout 30 agent-browser <cmd>` (60s for `open`).
  Bare calls can hang indefinitely on a stuck daemon/navigation.
- Daemon stuck (even `example.com` times out)? Restart **only** the agent daemon:
  ```bash
  ps -o pid,comm,args -p <AGENT_PID>   # confirm it's agent-browser, NOT the user's browser
  kill <AGENT_PID>                     # escalate to kill -9 only if needed
  rm -f ~/.agent-browser/default.sock  # clear stale socket
  ```
  Then re-`connect <cdp_port>` and re-verify with `tab list`.
- `agent-browser doctor` can itself hang behind a stuck daemon — restart first.
- Avoid full `ps aux` scans on loaded machines; use targeted
  `ps -o pid,comm -p <PID>`.
- Every mutating step gets a read-back: after `open`, run `get url`;
  after `connect`, run `tab list`.

## 8. Google Forms file upload (Google Picker workaround)

The "Add file" button opens the Google Picker in a **cross-origin iframe** — not a
native file chooser, so `Page.fileChooserOpened` never fires and `upload` on the
Browse button fails ("Node is not a file input element"). Also `<input type=file>`
is 0x0 / hidden inside the picker iframe.

Working method (use `{{CORE_DIR}}/scripts/picker_upload.py`, or `cdp.py` directly; CDP to 127.0.0.1:<cdp_port>):

1. Click "Add file" with real mouse events (scripted `.click()` is untrusted):
   scroll the button into view, then `Input.dispatchMouseEvent` mousePressed/mouseReleased.
   (Optional hardening: `Page.setInterceptFileChooserDialog enabled=true` first.)
2. Find the file input in the **pierced** DOM — `DOM.getDocument(depth=-1, pierce=True)`
   then walk `children` + `shadowRoots` + `contentDocument` for `INPUT[type=file]`.
3. `DOM.setFileInputFiles(files=[abs_path], nodeId=nid)` — resolve nid and set files
   in ONE connection (nodeIds are per-connection; a stale id raises "Could not find node").
4. Verify: read `document.body.innerText` for the filename chip (tooltip shows full name).

```python
from cdp import Conn, find          # {{CORE_DIR}}/scripts/cdp.py
c = Conn(find("<tab title substring>"))
c.cmd("Page.enable"); c.cmd("DOM.enable")

# click Add file (coords from getBoundingClientRect after scrollIntoView)
for kind in ("mousePressed", "mouseReleased"):
    c.cmd("Input.dispatchMouseEvent", type=kind, x=pt["x"], y=pt["y"],
          button="left", clickCount=1)
time.sleep(3)

doc = c.cmd("DOM.getDocument", depth=-1, pierce=True)["root"]
def walk(node):
    if node.get("nodeName") == "INPUT":
        a = node.get("attributes", []); d = dict(zip(a[::2], a[1::2]))
        if d.get("type") == "file": return node["nodeId"]
    for ch in (node.get("children") or []) + (node.get("shadowRoots") or []):
        if (r := walk(ch)): return r
    if (cd := node.get("contentDocument")): return walk(cd)
nid = walk(doc)
c.cmd("DOM.setFileInputFiles", files=["/abs/path/CV.pdf"], nodeId=nid)
```

- `nodeId` changes each connection — always re-resolve, never reuse.
- To replace the file: click the chip's "Remove file" X (mouse events) first, then re-set.
- Blocked alternatives: fetching the PDF from localhost inside the https page (mixed
  content), and `DataTransfer` + `input.files = dt.files` via `agent-browser eval`
  (argument too long / fetch blocked).

## 9. Quick reference

```bash
agent-browser connect <cdp_port>        # attach to user's browser
agent-browser tab list            # verify attach + selection
agent-browser tab new             # safe blank tab
agent-browser open <url>          # navigate selected tab
agent-browser get url             # confirm navigation
agent-browser get title
agent-browser snapshot -c         # compact a11y tree (login signals)
agent-browser screenshot shot.png # visual proof when needed
agent-browser tab close <n>       # close only tabs you created
agent-browser --help              # full flag reference
```
