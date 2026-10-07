# job-apply-kit configuration

Copy this file to `~/.config/job-apply-kit/config.md` (or point `$JAK_CONFIG` at it) and fill it in.
Easiest way: tell your agent "set up my job-apply-kit config from my CV <url or file path>".
Set up the debug browser first (`docs/help/03-browser-setup.md`) — CVs in Google Docs are read through it.

Rules for this file:
- Script-read values are bullets written exactly as `- **key:** value` under the headings below.
- Lists are comma separated. Leave a value empty or as `<placeholder>` to mean "not set".
- Never commit this file. It contains personal data. Keep it outside the repository.

## Identity

- **name:** <Your Full Name>
- **name_file:** <Your_Full_Name>
- **phone:** <+000000000000>
- **location:** <City, Country>
- **timezone:** <Area/City>
- **website:** <https://example.com>
- **github:** <https://github.com/username>
- **linkedin:** <https://linkedin.com/in/username>
- **email_header:** <name@yourdomain.example>
- **email_google:** <you@gmail.example>

`email_header` is the address shown on resumes, cover letters and portals.
`email_google` is the account used for Google sign-in, Google Forms and Gmail drafts. They may be the same.

## Sources

- **cv_source:** <https://example.com/cv, https://example.com/resume>
- **projects_source:** <https://example.com/projects>
- **certifications_url:** <https://linkedin.com/in/username>

`cv_source` accepts URLs or local file paths (comma separated). It is the only source of candidate facts.

## Paths

- **workspace:**
- **templates_dir:**
- **cache_dir:**

Defaults: workspace = current directory (or `$JAK_WORKSPACE`), templates_dir = `<workspace>/templates`, cache_dir = `<workspace>/.cache`.

## Google

- **gog_account:** <you@gmail.example>
- **google_backend:** auto
- **google_token_dir:**
- **drive_folder_id:**
- **drive_templates_folder_id:**
- **sheet_id:**
- **sheet_tab:** Sheet1

`google_backend` is `auto`, `gog` or `python`. The three ids are written by the `sheet_init` script.

## Browser

- **cdp_port:** 9222

Start your own browser in debug mode on this port and log in once (see docs/EXTERNAL_TOOLS.md).

## Truth gates

- **banned_claims:**
- **unproven_claims:**

Skills the candidate must never claim, and skills not yet proven. Your agent asks you; it never guesses.

## Application defaults

- **default_doc:** resume
- **template_default:** true

## Auto-skip

- **max_experience_years:** 5
- **min_salary:** 15000
- **currency:** BDT
- **onsite_locations:** <City1, City2>
- **remote_ok:** true
- **salary_floor_remote:**
- **salary_floor_onsite:**

## Search terms

- **bdjobs_terms:** <Software Engineer, Backend>
- **linkedin_queries:**
    <one LinkedIn post-search query per indented line, e.g. "Software Engineer" AND (hiring OR vacancy)>
- **fb_saved_urls:** https://www.facebook.com/saved/
- **discord_channels:**
- **discord_cache_dir:** JDs/discord

## Signature

- **email_signature:**

Leave empty to build the signature from Identity.

## Resume preferences

Free-form notes for the resume skills (bullet variants, fixed sections, role types, claim framing).
These are prose, read by the agent, not by scripts.
