---
name: check-discord-jobs
description: Scan Discord job channels via agent-browser over CDP, cache every post by Discord message id for instant seen or not-seen dedup, cross-check the tracker, and process NEW jobs end to end (template resume, email draft or staged form, tracker row; never submit). Invoke with /check-discord-jobs, optionally followed by channel URLs.
user-invocable: true
---

# Discord job channel scanner

Path placeholders: `{{SKILL_DIR}}` = this skill's base directory, `{{CORE_DIR}}` = the `job-apply-core` skill directory (sibling install).

Universal rules: `{{CORE_DIR}}/OPERATIONS.md`. Per-job procedure: `{{CORE_DIR}}/references/new-job-procedure.md`.
Config keys read: `discord_channels`, `discord_cache_dir` (default `JDs/discord`), `cv_source`, `templates_dir`, `sheet_id`, `drive_folder_id`, `cdp_port`, `workspace`.
Scripts: `{{SKILL_DIR}}/scripts/discord_api.py` (primary, REST API — `references/discord-api-notes.md`), `{{SKILL_DIR}}/scripts/scan_channel.py` (DOM fallback).

## Inputs
- `$ARGUMENTS`: optional space or newline separated `https://discord.com/channels/<server>/<channel>` URLs.
- Without URLs, use `discord_channels` from the config. When a new job channel is discovered, add its URL there.

## Skill-specific rules
1. Open every channel in a NEW tab (inventory existing tabs first). Close only the Discord tabs this run opened; never a pre-existing Discord tab. Sub-agents close only pages they opened.
2. Login wall (Discord or an application link): hard stop, leave the tab open, record it.
3. If the page is already on a listed channel (a pre-existing tab or the tab this run opened): do NOT deep-scroll history — collect the last 20 messages and settle. Start at the bottom (where Discord opens), extract and count; if fewer than 20, scroll up step by step and keep counting until 20 unique messages are collected or the top is reached, then stop. The scroll-back sweep (`--stop-date`) is only for a first-time pass over a long channel with no already-open page.

## Cache
Root `<workspace>/<discord_cache_dir>/`.
- `seen_messages.json`: array of `{ "message_id": "<discord snowflake>", "channel_id", "url", "company", "position", "deadline", "apply_method": "email|link|form", "contact", "verdict": "new|applied|drafted|skipped-duplicate|expired|not-a-job", "sheet_row", "output_dir", "first_seen", "processed_at" }`. The message id makes dedup instant across runs.
- `applied_cache.json`: `{ "company+position": { sheet_row, date, how } }`.

## Step 1: extract posts
- For each channel URL: it must have a tab; if none exists, open one in a NEW tab, wait for load, confirm the channel rendered.

### Token (capture once, then the script handles it)
- **Where it lives:** `~/.config/job-apply-kit/discord_token` — one raw line, no quotes (or `$JAK_DISCORD_TOKEN`). Secret: handle like the Google tokens.
- **How the script uses it:** `discord_api.py` reads the file automatically and sends `Authorization: <token>` on an in-page `fetch` of `/api/v9/channels/<id>/messages` (same-origin, so the HttpOnly Cloudflare cookies ride along by themselves). If the API answers `401: Unauthorized` mid-run, the script recaptures the token itself and retries once.
- **How to capture (Route A — preferred, no reload):** the token is already in the network log of any loaded channel tab. With the chrome-devtools MCP: `list_pages` → pick the Discord channel page → `list_network_requests` (resourceTypes fetch/xhr) → find a `/api/v9/channels/.../messages` request (if none, click between two channels) → `get_network_request` → copy the `authorization` **request** header → save it to the token file.
- **How to capture (Route B — agent-browser only):** `python3 {{SKILL_DIR}}/scripts/discord_api.py <slug> --url <channel> --capture-token` records a HAR while reloading the channel tab and pulls `Authorization` out of the app's own `/api/v9` traffic. Heavier (full SPA reload); use when the MCP is unavailable.
- Never paste the token into docs, sheets, or reports. Details: `references/discord-api-notes.md` ("Capturing the token").

- **Primary method — REST API** (fast, complete, see `references/discord-api-notes.md`):
  `python3 {{SKILL_DIR}}/scripts/discord_api.py <slug> --url <channel url> --tab <t<N>> --last 20`
  (bottom-first last-20 settle) or `--after-date YYYY-MM-DD` for a catch-up sweep since the last run. The
  channel id is matched from the `--url` against the tab URL; Authorization comes from
  `~/.config/job-apply-kit/discord_token`. On `401: Unauthorized`, recapture the token (above).
- **Fallback — DOM scraping** (no token needed): `python3 {{SKILL_DIR}}/scripts/scan_channel.py <slug> --tab <t<N>> [--last 20 | --stop-date <YYYY-MM-DD>]` — extracts the visible messages, scrolls the chat scroller, merges by message id, writes `<today>/raw_<slug>.json`. Quirks (single-line JS, explicit `--tab`, chat-scroller target) are in the notes doc. Extraction script (the same one the helper embeds):
  ```js
  () => [...document.querySelectorAll('[id^="message-content-"], [data-list-item-id^="chat-messages"]')].map(el => ({
    id: (el.id.match(/message-content-(\d+)/) || [,''])[1] || (el.getAttribute('data-list-item-id') || '').split('-').pop(),
    author: el.querySelector('h3, [class*="header"] [class*="name"]')?.innerText || '',
    time: el.querySelector('time')?.getAttribute('datetime') || '',
    text: el.innerText,
    links: [...el.querySelectorAll('a')].map(a => a.href)
  })).filter(m => m.id)
  ```
- Persist to `<today>/messages.json` and a readable `messages.md` (per channel: message_id | date | company or role | link). Merging into the root `seen_messages.json` is what makes future runs fast.

## Step 2: dedup verdicts
For every extracted post (skip obvious chat noise; keep anything with a link, an email address or JD-shaped text):
- Seen in `seen_messages.json` or `applied_cache.json`: mark the verdict, done.
- Otherwise fuzzy-check company + position against the tracker snapshot.
- Write every verdict back to `seen_messages.json` before doing any work.

## Step 3: process NEW jobs
Follow `{{CORE_DIR}}/references/new-job-procedure.md`. The `comments` value for the sheet row is the Discord message id.
