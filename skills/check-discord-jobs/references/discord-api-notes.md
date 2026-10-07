# Discord REST API from the browser console (fast message fetch)

The DOM scraper (`scan_channel.py`) works but is slow and lossy (scroll races, virtualized
lists, embed text missing). Discord's own REST API, called from inside an open Discord tab,
is faster and complete: no scrolling, embeds included, exact date bounds via snowflakes.
Verified live 2026-10-07 on discord.com (Chrome 154, web client).

## Endpoint

```
GET https://discord.com/api/v9/channels/<channel_id>/messages?limit=<1..100>[&before=<snowflake>][&after=<snowflake>]
```

- Returns a JSON array, **newest first**. Empty array = no more history in that direction.
- `before` paginates backwards (older), `after` paginates forwards (newer, for catch-up),
  `around` is a window. One of the three per request.
- Overwrite-embeds and link-only posts come through in `embeds` / `attachments`, which the
  DOM scrape often misses.

## Request format (captured from the live session)

Essential headers:

| Header | Value |
|---|---|
| `Authorization` | the user token (raw string, no `Bot` prefix). **Required.** |
| `Cookie` | HttpOnly Cloudflare ids (`__dcfduid`, `__sdcfduid`, `_cfuvid`). Sent automatically by a same-origin `fetch` — never handle them manually. |

Optional but observed on real traffic (replay works without them): `x-super-properties`
(base64 client info), `x-discord-locale`, `x-discord-timezone`, `x-installation-id`,
`x-debug-options: bugReporterEnabled`, `referer`.

Cookie-only (no `Authorization`) returns `401`. The token is the only secret that matters.

## Capturing the token

`document.cookie` is empty (HttpOnly) and `localStorage` is **not available** in the
agent-browser eval realm; the webpack `getToken()` hunt is unreliable (locale modules
match too — it returns `{locale, ast}`). Capture from the network log. Two routes:

**Route A — chrome-devtools MCP (preferred: easiest, no page reload).** The channel tab
has usually already fetched `/api/v9/channels/.../messages`, so the request is sitting in
the log:
1. `list_pages` → pick the Discord channel page (pageId).
2. `list_network_requests { pageId, resourceTypes: ["fetch","xhr"] }` → find the
   `/api/v9/channels/.../messages` reqid (if none, click between two channels and retry).
3. `get_network_request { pageId, reqid }` → read the `authorization` **request** header.
4. Save the raw token to `~/.config/job-apply-kit/discord_token` (one line, no quotes).

This is an MCP-only capability (network inspection), which is exactly when OPERATIONS §11
allows the MCP fallback — no need to touch the page at all.

**Route B — agent-browser only (no MCP): HAR capture with a reload.** Heavier (full SPA
reload) but fully scripted:
```
python3 discord_api.py <slug> --url <channel> --capture-token
```
starts a HAR recording, reloads the channel tab, waits for the app's own `/api/v9` calls,
reads the `Authorization` header out of the HAR, stores the token, and continues with the
fetch. `discord_api.py` also auto-recaptures this way on a mid-run `401`.

Token lifetime is long (weeks+) but it dies on logout, password change, or token refresh —
a sudden `401: Unauthorized` means recapture (Route A), not a code bug.

## Snowflake ↔ timestamp

Discord ids are ms since the Discord epoch `1420070400000` shifted left 22 bits:

```
ms        = (id >> 22) + 1420070400000
id        = (ms - 1420070400000) << 22
after=S   = messages newer than timestamp S (e.g. UTC midnight of a date)
```

`discord_api.py --after-date 2026-10-01` uses this to fetch only what is newer than the
last sweep — that is the "latest updates using timestamp" catch-up mode.

## In-page fetch snippet

Run inside the Discord tab (single line — see the eval quirk below):

```js
(async (ch, token, qs) => { const r = await fetch('/api/v9/channels/' + ch + '/messages?' + qs, { headers: { Authorization: token } }); const j = await r.json(); const retry = r.headers.get('Retry-After'); return JSON.stringify({ status: r.status, retry: retry ? parseFloat(retry) : null, body: j }); })('1551244952821039155', 'TOKEN_HERE', 'limit=50')
```

- The channel id in the URL of the request must be matched against the page URL
  (`location.pathname` last segment) before trusting results — a tab the user navigated
  mid-run must not silently feed the wrong channel's data.
- 429: read the `Retry-After` response header (float seconds), sleep, retry once.

## Script

```
python3 {{SKILL_DIR}}/scripts/discord_api.py <slug> \
  --url https://discord.com/channels/<server>/<channel> --tab t14 \
  [--last 20 | --after-date YYYY-MM-DD] [--limit 50] [--out PATH]
```

Writes `raw_<slug>.json` in the same message shape as the DOM scraper
(`{id, author, time, text, links}`), so dedup and verdict code are unchanged.
Read-only GETs only; never POST/send; only channels listed in config `discord_channels`.

## Fallback: DOM scraping quirks (scan_channel.py)

- **Single-line JS only**: multiline eval args hit `InvalidBatchScriptArg` from the
  agent-browser launcher on Windows — the script's `EXTRACT`/`SCROLL` strings must stay
  one line, and eval failures must be surfaced (`ab()` prints rc≠0), not swallowed.
- **Select the tab explicitly** (`--tab t<N>`): evals land on the currently selected tab,
  and the user may have switched tabs mid-run.
- **Channel id from the URL**, never from assumed tab state; validate every extracted id
  is numeric (`data-list-item-id="chat-messages-<channel_id>-<message_id>"` — date dividers
  otherwise leak in as junk ids like "October 7, 2026").
- **Scroll the chat scroller inside `[class*="chatContent"]`**, not the document-wide
  largest scroller (members list wins that sort). Discord collapses the scroller while
  fetching history: treat `none` as "retry", not "top reached".
- **`--last N` mode ignores `--stop-date`** (bottom-first fill); the default 7-day
  `--stop-date` otherwise ends the sweep early.
