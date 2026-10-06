---
name: check-discord-jobs
description: Scan Discord job channels via agent-browser over CDP, cache every post by Discord message id for instant seen or not-seen dedup, cross-check the tracker, and process NEW jobs end to end (template resume, email draft or staged form, tracker row; never submit). Invoke with /check-discord-jobs, optionally followed by channel URLs.
user-invocable: true
---

# Discord job channel scanner

Universal rules: `{{CORE_DIR}}/OPERATIONS.md`. Per-job procedure: `{{CORE_DIR}}/references/new-job-procedure.md`.
Config keys read: `discord_channels`, `discord_cache_dir` (default `JDs/discord`), `cv_source`, `templates_dir`, `sheet_id`, `drive_folder_id`, `cdp_port`, `workspace`.
Script: `{{SKILL_DIR}}/scripts/scan_channel.py`.

## Inputs
- `$ARGUMENTS`: optional space or newline separated `https://discord.com/channels/<server>/<channel>` URLs.
- Without URLs, use `discord_channels` from the config. When a new job channel is discovered, add its URL there.

## Skill-specific rules
1. Open every channel in a NEW tab (inventory existing tabs first). Close only the Discord tabs this run opened; never a pre-existing Discord tab. Sub-agents close only pages they opened.
2. Login wall (Discord or an application link): hard stop, leave the tab open, record it.

## Cache
Root `<workspace>/<discord_cache_dir>/`.
- `seen_messages.json`: array of `{ "message_id": "<discord snowflake>", "channel_id", "url", "company", "position", "deadline", "apply_method": "email|link|form", "contact", "verdict": "new|applied|drafted|skipped-duplicate|expired|not-a-job", "sheet_row", "output_dir", "first_seen", "processed_at" }`. The message id makes dedup instant across runs.
- `applied_cache.json`: `{ "company+position": { sheet_row, date, how } }`.

## Step 1: extract posts
- For each channel URL: open a new tab, wait for load, confirm the channel rendered.
- Long channels: run `python3 {{SKILL_DIR}}/scripts/scan_channel.py <slug> --stop-date <YYYY-MM-DD>` with the channel tab selected. It extracts the visible messages, scrolls up, merges by message id and writes `<today>/raw_<slug>.json`. Short channels: a single extraction is enough. Extraction script (the same one the helper embeds):
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
