---
name: check-facebook-saved
description: Scan Facebook saved items (https://www.facebook.com/saved/) via agent-browser over CDP, extract at least 50 saved posts with scrolling, open only posts that look like job posts, cross-check the tracker and local caches, and process NEW jobs end to end (template resume, email draft or staged form, tracker row; never submit). Invoke with /check-facebook-saved.
user-invocable: true
---

# Facebook saved jobs scanner

Universal rules: `{{CORE_DIR}}/OPERATIONS.md`. Per-job procedure: `{{CORE_DIR}}/references/new-job-procedure.md`.
Config keys read: `fb_saved_urls`, `cv_source`, `templates_dir`, `sheet_id`, `drive_folder_id`, `cdp_port`, `workspace`.

## Inputs
- `$ARGUMENTS`: optional alternative saved-collection URL. Default: the URLs in `fb_saved_urls` (usually `https://www.facebook.com/saved/`; add a specific collection URL there to scan an extra list or when the default dashboard is empty).

## Skill-specific rules
1. Open the saved page and every job post in NEW tabs (inventory existing tabs first). Close only the Facebook tabs this run opened; never a pre-existing Facebook session tab. Sub-agents close only pages they opened.
2. Login wall (Facebook or the application link): hard stop, leave the tab open, record it in cache and sheet.

## Cache
Root `JDs/facebook-saved/`.
- `seen_posts.json`: array of `{ "post_url": "<permalink or external link>", "title", "subtitle", "company", "position", "deadline", "apply_method": "email|link|form", "contact", "verdict": "new|applied|drafted|skipped-duplicate|expired|not-a-job", "sheet_row", "output_dir", "first_seen", "processed_at" }`.
- `applied_cache.json`: `{ "company+position": { sheet_row, date, how } }`.

## Step 1: extract saved items
- Open the saved page in a new tab; confirm the logged-in feed rendered.
- Extract with a script, for example:
  ```js
  () => [...document.querySelectorAll('a[href]')].map(a => {
    const card = a.closest('div[role="article"], div[role="link"]') || a;
    return {
      url: a.href,
      title: (card.querySelector('a span, h2, h3, [role="heading"]')?.innerText || '').trim(),
      subtitle: (card.querySelector('span[dir="auto"] + span, div[class*="subtitle"], span[id^="feed_subtitle"]')?.innerText || '').trim(),
      text: card.innerText
    };
  }).filter(i => i.url && i.title)
  ```
- Dedup by `url`. Facebook virtualizes the list: scroll in steps (about 2000 px), wait 2 to 3 seconds after each scroll, re-extract and merge until at least **50 unique items** are collected or the list ends.
- Persist at once to `JDs/facebook-saved/<today>/items.json` and a readable `items.md` (url | title | subtitle | job-post? verdict).

## Step 2: job-post filter and dedup verdicts (before opening anything)
- A job post has hiring, vacancy, position, role, deadline or apply keywords, or JD-shaped text. Plain articles, videos, reels, marketplace items and groups are `not-a-job`: do not open them.
- Seen in `seen_posts.json` or `applied_cache.json`: mark the verdict, do not open.
- Otherwise fuzzy-check company + position against the tracker snapshot.
- Write every verdict back to `seen_posts.json` before doing any work. Only NEW job posts are opened (one new tab each).

## Step 3: process NEW jobs
Follow `{{CORE_DIR}}/references/new-job-procedure.md`. The `comments` value for the sheet row is the Facebook post URL.
