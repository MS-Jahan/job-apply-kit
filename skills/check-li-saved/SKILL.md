---
name: check-li-saved
description: Scan LinkedIn saved posts (https://www.linkedin.com/my-items/saved-posts/) via agent-browser over CDP, extract at least 50 saved posts with scrolling, open only posts that look like job posts, cross-check the tracker and local caches, and process NEW jobs end to end (template resume, email draft or staged form, tracker row; never submit). Invoke with /check-li-saved.
user-invocable: true
---

# LinkedIn saved jobs scanner

Universal rules: `{{CORE_DIR}}/OPERATIONS.md`. Per-job procedure: `{{CORE_DIR}}/references/new-job-procedure.md`.
Config keys read: `cv_source`, `templates_dir`, `sheet_id`, `drive_folder_id`, `cdp_port`, `workspace`.

## Inputs
- `$ARGUMENTS`: optional alternative saved-items URL. Default `https://www.linkedin.com/my-items/saved-posts/`.

## Skill-specific rules
1. Open the saved-posts page and every job post in NEW tabs (inventory the existing tabs first). Close only the LinkedIn tabs this run opened; never a pre-existing feed or session tab. Sub-agents close only pages they opened.
2. LinkedIn Easy Apply is NEVER completed past the review step: stage and screenshot.
3. Login wall (LinkedIn or the application link): hard stop, leave the tab open, record it in cache and sheet.

## Cache
Root `JDs/linkedin-saved/`.
- `seen_posts.json` (this skill's file): array of `{ "post_url", "title", "subtitle", "company", "position", "deadline", "apply_method": "email|link|form|easy-apply", "contact", "verdict": "new|applied|drafted|skipped-duplicate|expired|not-a-job", "sheet_row", "output_dir", "first_seen", "processed_at" }`.
- `applied_cache.json`: SHARED with `li-full-run` (`{ "company+position": { sheet_row, date, how } }`); never delete another skill's entries.

## Step 1: extract saved items
- Open the saved-posts page in a new tab; confirm the list rendered (a redirect to login is a hard stop).
- Extract with a script, for example:
  ```js
  () => [...document.querySelectorAll('div[data-view-name="saved-item"], li.reusable-search__result-container, div.entity-result, div.feed-card')].map(card => {
    const a = card.querySelector('a[href]');
    return {
      url: a?.href || '',
      title: (card.querySelector('a span, h2, h3, [role="heading"]')?.innerText || '').trim(),
      subtitle: (card.querySelector('.entity-result__primary-subtitle, .feed-card__subtitle, .reusable-search__entity-result-primary-subtitle')?.innerText || '').trim(),
      text: card.innerText
    };
  }).filter(i => i.url)
  ```
  LinkedIn markup changes often; if the selectors miss, fall back to a compact snapshot and read the links and headings from it.
- Dedup by `url`. LinkedIn virtualizes the list: scroll in steps (about 2000 px), wait 2 to 3 seconds, re-extract and merge until at least **50 unique items** are collected or the list ends.
- Persist at once to `JDs/linkedin-saved/<today>/items.json` and a readable `items.md` (url | title | subtitle | job-post? verdict).

## Step 2: job-post filter and dedup verdicts (before opening anything)
- A job post has hiring, vacancy, position, role, deadline or apply keywords, "is hiring", or JD-shaped text. Saved job postings count too. Articles, celebrations, polls, photos and course items are `not-a-job`: do not open them.
- Seen in `seen_posts.json` or `applied_cache.json`: mark the verdict, do not open.
- Otherwise fuzzy-check company + position against the tracker snapshot.
- Write every verdict back to `seen_posts.json` before doing any work. Only NEW job posts are opened (one new tab each).

## Step 3: process NEW jobs
Follow `{{CORE_DIR}}/references/new-job-procedure.md`. The `comments` value for the sheet row is the LinkedIn post URL. Then report as described there.
