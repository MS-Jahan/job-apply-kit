# Tracker columns (A..O)

One row per application, 15 columns. Append only with `sheet_append.py append '<json-row>'`; the
JSON keys below are the contract. Missing keys become empty cells; unknown keys are rejected.

| Col | JSON key | Header | Content |
|---|---|---|---|
| A | `date` | Date | processing date, `YYYY-MM-DD` |
| B | `company` | Company | employer name |
| C | `position` | Position | job title |
| D | `drive_link` | Resume Drive | link(s) to the uploaded document(s); `[template] <link>` when a template was used as-is; comma-separated if CV + resume + cover letter |
| E | `job_nature` | Job Nature | full-time, part-time, internship, contract |
| F | `job_type` | Job Type | onsite, remote, hybrid |
| G | `location` | Location | city or "Remote" |
| H | `job_link` | Job Link | post or apply URL |
| I | `job_desc` | Job Description | the FULL job description text (never a summary) |
| J | `status` | Job Status | Drafted, Staged, Applied, Skipped, Closed, ... (never overwrite what the user set by hand) |
| K | `how_applied` | How Applied | email draft, portal, Google Form, ... |
| L | `contact` | Contact/Email | contact info from the post |
| M | `salary` | Salary/Budget | advertised salary or "Negotiable" (not our own input value) |
| N | `deadline` | Deadline | application deadline |
| O | `comments` | Comments | extra info ONLY: message id, draft id, staged-form notes, resume file reference; skip reasons may start with a bracket tag such as `[Worth Checking]` |

Rules:
- Never put job-description text in O, and never put notes in I.
- Writes are RAW text: a phone number starting with `+` or text starting with `=` is stored literally.
- The live header row must have exactly 15 columns; the helper aborts otherwise. `sheet_init.py`
  creates a new sheet with these headers.
