# Example config (sanitized from a real working setup)

Real file lives at `~/.config/job-apply-kit/config.md` (Windows: `C:\Users\<you>\.config\job-apply-kit\config.md`).
Values below are placeholders; the search lists are a real, working example to copy and adapt.

## Identity
- **name:** <Your Full Name>
- **phone:** <+880...>
- **timezone:** Asia/Dhaka
- **email_google:** <you@gmail.com>

## Sources
- **cv_source:** <Google Doc / site URL of your always-up-to-date CV>
- **projects_source:** <portfolio / GitHub README URLs, comma separated>
- **certifications_url:** <LinkedIn certifications page URL>

## Google
- **google_backend:** auto
- **drive_folder_id:** <ID after /folders/ in the Drive URL>
- **sheet_id:** <ID between /d/ and /edit in the Sheet URL>
- **sheet_tab:** Sheet1

## Browser
- **cdp_port:** 9222

## Auto-skip
- **max_experience_years:** 5
- **min_salary:** 15000
- **currency:** BDT
- **remote_ok:** true

## Search terms
- **bdjobs_terms:** Software Engineer, Software Developer, Fullstack, Full stack, Frontend, Front end, Backend, Python, PHP, Android Developer, Flutter Developer, MERN, WordPress, DevOps
- **linkedin_queries:**
    "Software Engineer" AND (hiring OR vacancy) AND (Dhaka OR Bangladesh),
    "Software Developer" AND (hiring OR vacancy) AND (Dhaka OR Bangladesh),
    (Fullstack OR "Full stack") AND developer AND (hiring OR vacancy) AND Dhaka,
    Backend AND (developer OR engineer) AND (hiring OR vacancy) AND Dhaka,
    developer AND (remote OR hybrid) AND (hiring OR vacancy) AND Bangladesh,
    (DevOps OR Android) AND (remote OR hybrid) AND Bangladesh
- **fb_saved_urls:** https://www.facebook.com/saved/
- **discord_channels:** <channel URLs, comma separated>
- **discord_cache_dir:** JDs/discord

## Tracker columns (15, created by sheet_init.py)
Date, Company, Position, Resume Drive, Job Nature, Job Type, Company Location, Job Link,
Job Description, Job Status, How Applied, Contact / Email, Salary / Budget, Deadline, Comments

## Notes
- One short query per line group; never AND-chain all of them (LinkedIn length limit).
- Leave `templates_dir` empty to use the default; salary floors empty = hard error only if you enable the filter.
- Fields the agent left blank (truth gates, signature, templates_dir) are normal on day one.

## Where this file lives
| OS | Path |
|---|---|
| Windows | `C:\Users\<you>\.config\job-apply-kit\config.md` (= `%USERPROFILE%\.config\job-apply-kit\config.md`) |
| macOS | `/Users/<you>/.config/job-apply-kit/config.md` |
| Linux | `/home/<you>/.config/job-apply-kit/config.md` |
Override with the `JAK_CONFIG` environment variable.
