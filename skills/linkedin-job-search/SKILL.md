---
name: linkedin-job-search
description: Search LinkedIn feed posts via agent-browser over CDP using the configured list of search queries (filters Posts + Latest), evaluate each post against the candidate's live skills, and SAVE matching job posts through the post's 3-dot menu (click Save only if it says Save; skip if it says Unsave). Check about 20 posts per query. Only saves posts: no resumes, drafts or applications. Invoke with /linkedin-job-search.
user-invocable: true
---

# LinkedIn job post search and save

Universal rules: `{{CORE_DIR}}/OPERATIONS.md` (#sources #truth #browser). Config keys read: `linkedin_queries`, `cv_source`, `projects_source`, `onsite_locations`, `remote_ok`, `cdp_port`, `workspace`.

## Scope boundary (read first)
This skill only **saves posts on LinkedIn**. It does not create or edit CVs, resumes or cover letters, write drafts or emails, fill or stage forms, or apply in any way. Saved posts are processed later by `/check-li-saved`.

## Inputs
- `$ARGUMENTS`: optional custom search queries; if given, use them instead of `linkedin_queries`.

## Search queries
`linkedin_queries` holds one query per line. Good queries combine the role, a hiring word and a place, for example:
- `"Software Engineer" AND (hiring OR vacancy) AND (<city> OR <country>)`
- `(Fullstack OR "Full stack") AND developer AND (hiring OR vacancy) AND <city>`
- `developer AND (remote OR hybrid) AND (hiring OR vacancy) AND <country>`
Run them in the order listed; each is a separate search pass. Without configured queries the skill asks the user for some.

## Skill-specific rules
1. Open LinkedIn searches in a NEW tab (inventory existing tabs first). Close only tabs this run opened; never a pre-existing feed or session tab.
2. **Save-only interaction.** The only mutating action on a post is 3-dot menu then Save. Never comment, react, follow, message or apply. Menu says **"Save"**: click it. Menu says **"Unsave"**: the post is already saved, do not click, move on.
3. Login wall: hard stop, leave the tab open, report.
4. **Skill facts only from the live sources** (OPERATIONS #sources): at the start fetch `cv_source` (and `projects_source`) and write a summary of skills and projects to the temp context file below. Match posts against that file, never against memory or stale local caches.
5. **Post = job post only.** Hiring, vacancy, role, deadline or apply keywords, or JD-shaped text. Articles, polls, celebratory posts and course promos are skipped without opening the 3-dot menu.

## Workflow

### Step 1: skills context file
- Temp file `<workspace>/JDs/linkedin-job-search/<today>/skills_context.md`.
- Read the live sources and write: the full skills list (languages, frameworks, tools, domains), the project catalog with one-line tech summaries, and anything that clearly marks what the candidate does NOT have (`banned_claims`, `unproven_claims`).

### Step 2: open LinkedIn and run the first query
- New tab at `https://www.linkedin.com/search/results/content/?keywords=<url-encoded query>`; confirm login (a redirect to login is a hard stop).
- Set the filters: first filter **Posts**, second **Latest** (sort by date). Verify both chips before evaluating posts; navigation resets them, so re-apply after every navigation. (`li-full-run` sets the same two filters through URL parameters, which is more reliable.)

### Step 3: evaluate and save (about 20 posts per query)
- Scroll in steps (about 2000 px, wait 2 to 3 seconds, re-snapshot) until about 20 posts are evaluated or the feed ends.
- For each post: read its text; job post? (rule 5); real overlap between the required stack and `skills_context.md`, with a location that fits the user (check `onsite_locations` and remote); if it matches, click the **3-dot** button, snapshot the menu, click **Save** (or press Escape on **Unsave**).
- **Early stop:** while scrolling, more than 2 already-saved posts (menu shows "Unsave") below the fresh results means this query was checked in an earlier run: stop it and record `already-checked`.
- Keep a tally per query: evaluated, job posts, matched and saved, already saved, skipped.

### Step 4: remaining queries
Run the next query, re-verify the Posts + Latest filters, repeat Step 3. The same post may surface under several queries: track seen post links in memory or in `<workspace>/JDs/linkedin-job-search/<today>/seen.json` and skip handled posts.

### Step 5: report
A compact table: query | evaluated | job posts | saved now | already saved | skipped. Total saves, ambiguous matches (for example the menu failed to open), login or timeout issues. Close the tabs this run opened.

## Notes
LinkedIn markup changes often: prefer snapshot refs over brittle CSS selectors; fall back to scripted extraction with broad selectors.
