# Raw CDP tools (last resort)

Order of browser tools (OPERATIONS.md#browser): `agent-browser` first, the chrome-devtools MCP
second, these scripts last. Use them when both fail to drive a page, for example when an MCP
tool accepts calls but receives empty parameters, or for the Google Picker upload (below).

They talk to the SAME debug browser over `http://127.0.0.1:<cdp_port>` (env `JAK_CDP_PORT`, else
config `cdp_port`, else 9222). Same profile, cookies and logins. Needs `websocket-client`.

```bash
python3 {{CORE_DIR}}/scripts/cdp.py list                          # targetId  url | title
python3 {{CORE_DIR}}/scripts/cdp.py newtab <url>                  # prints the new targetId
python3 {{CORE_DIR}}/scripts/cdp.py nav <targetId> <url> --wait 7
python3 {{CORE_DIR}}/scripts/cdp.py eval <targetId> "document.title"
python3 {{CORE_DIR}}/scripts/cdp.py eval <targetId> --await path/to/script.js    # async IIFE
python3 {{CORE_DIR}}/scripts/cdp.py text <targetId> --max 3500    # visible innerText
python3 {{CORE_DIR}}/scripts/cdp.py shot <targetId> output/<company-slug>/evidence.png
python3 {{CORE_DIR}}/scripts/cdp.py upload <targetId> "<css>" /abs/file.pdf   # existing <input type=file>
python3 {{CORE_DIR}}/scripts/cdp.py setfile <targetId> "<css>" /abs/file.pdf  # click control, intercept chooser
python3 {{CORE_DIR}}/scripts/cdp.py close <targetId>             # ONLY tabs you opened
python3 {{CORE_DIR}}/scripts/picker_upload.py <target-needle> /abs/file.pdf    # Google Picker iframe
```

Notes:
- The target can be a full id or a substring of the id, URL or title. Use full ids in scripts.
- `eval` prints JSON; for JS objects `JSON.stringify` inside the page and parse once more outside.
- Synthetic `el.click()` and synthetic key events are untrusted: Angular/React validation and
  Google Forms may ignore them. Use real CDP input events (`Input.dispatchMouseEvent`,
  `Input.dispatchKeyEvent`) when a control stays disabled or keeps stale state.
- Google Forms "Add file" opens the Picker in a cross-origin iframe. There is no native chooser, so
  use `picker_upload.py`: it walks the pierced DOM, finds the hidden file input and sets the file in
  one connection (node ids do not survive a reconnect). Verify afterwards: the file name is in the
  form text and no progressbar remains.
- Recent Chromium builds may need `--remote-allow-origins=*` for websocket clients; `cdp.py`
  suppresses the Origin header, which also works.
- Never close tabs you did not open. Never submit anything (OPERATIONS.md#accounts).
