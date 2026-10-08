# Job Apply Kit — Workshop Plan

Audience: people who joined the session and want to run the kit themselves.
Goal: after reading this, a newcomer can explain what the kit does, set it up
from zero, run their first scan, and review the results safely.
Source material: the session transcripts (2026-10-07), `README.md`, `docs/help/*`.

> **One rule behind everything:** the agent fills, stages, and *stops* at the final
> Submit button. Emails are Gmail **drafts**, never sent. You review every one.

---

## 1. What this is (the 60-second pitch)

A skill kit for an AI coding agent (Claude Code or OpenCode). It does the boring
daily job-hunt grind:

1. **Scan** job sources (Facebook saved, LinkedIn, BDJobs, Discord, screenshots).
2. **De-duplicate** against your Google Sheet tracker (never process a job twice).
3. **Pick a template** (CV / resume / cover letter) closest to the job.
4. **Draft** a Gmail message or fill the application form, stopping before Submit.
5. **Record** a row in the tracker + upload the PDFs to Drive.
6. **You** review the Sheet, the drafts and the forms, then press send.

Three parts inside the repo: **email drafting**, **browser automation**,
**CV/resume/cover-letter generation**.

## 2. How a human does it by hand (and what the agent copies)

The automation mirrors the manual routine. Understand this first.

| Source | Manual routine | What is automated |
|---|---|---|
| **Facebook saved** | While scrolling, *Save* every job post you see. Later, open the saved list and apply one by one. | `check-facebook-saved` reads the last ~20-25 saved items, skips ones already in the Sheet, processes new ones. |
| **Facebook groups** | Search "career", "job vacancy", "CSC jobs"; join 20-30 job groups; open each group once a day and *Save* good posts. | **Not automated** — you do the daily group visit, but saving feeds the automation above. |
| **LinkedIn** | Post search with Google-Dork-style boolean keywords, sorted by **Latest**. | `linkedin-full-run` runs your keyword list; `check-linkedin-saved` processes saved posts. |
| **BDJobs** | Category browsing misses jobs (posted in wrong category). Search by **keywords** instead — many new jobs daily. | `bdjobs-full-run` runs your keyword list: search, save, decide, apply/draft. |
| **Discord** | Job channels you follow. | `check-discord-jobs` reads the last N messages. |
| **Screenshots** | Job posts you screenshot. | `check-image-batch`. |

### 2.1 LinkedIn keyword ("dork") tips
- Example: `Software Developer AND (Hiring OR Vacancy) AND (Dhaka OR Bangladesh)`.
- Remote seekers: add `(Remote OR Hybrid)`.
- On the results page choose **Posts** and sort **Latest**.
- **Do not** chain every query with AND into one huge string — LinkedIn has a
  length limit and returns nothing. Keep several short queries and run them one by one.
- Easy way to make them: upload your CV to any chat model (Gemini etc.), give it
  the example above, ask it to generate dork queries for your roles. Paste the
  result into `config.md`.

### 2.2 BDJobs keyword tips
- Use many variants: "Software Engineer", "Software Developer", "Full Stack" and
  "Fullstack", "Front End"/"Frontend", "Backend", "MERN", "Trainee Engineer"...
- Top results can be paid/priority ads; scroll past them.

## 3. Setup from zero (the path to teach)

Order matters. The agent can do most steps — say *"install everything you can"*.

1. **Install a harness**: OpenCode (free models, app or CLI) or Claude Code.
2. **Pick a model** (see §6 for free options).
3. **Clone the repo**, open the folder in the harness (OpenCode app: *Add Project*).
4. **First prompt** (generic is fine):
   *"I am new to this project. What should I install or customize, and how do I get started?"*
   Then: *"Install everything you can."* The agent reads `docs/BOOTSTRAP.md`.
5. **Prerequisites** (agent installs): Python 3.9+, Node 18+ (LTS), `tectonic` +
   `poppler-utils` (PDFs), `agent-browser`. **Windows:** install Git for Windows
   (Git Bash) — agents work much better with Unix commands than PowerShell.
   **Linux is smoothest.** Details: `docs/help/01-prerequisites.md`, `08-compatibility.md`.
6. **Debug browser** (before the CV step — CV in Google Docs is read through it):
   - Agent asks which browser you use, makes a desktop shortcut that starts it in
     remote-debug mode (port **9222**).
   - Close the normal browser first, start via the shortcut, log in once to
     Facebook, LinkedIn, BDJobs, Google. Sessions persist.
   - **Security:** debug port exposes cookies to local malware. Use the shortcut
     only while running the agent; otherwise browse normally.
   - If missed, say: *"Please do the browser debug setup."* See `docs/help/03-browser-setup.md`.
7. **Google Cloud credentials** (§4 — the part people find hardest).
8. **Give your CV** (PDF path, drag-and-drop, or Google Doc URL). The agent writes
   `~/.config/job-apply-kit/config.md` (Windows: `C:\Users\<you>\.config\job-apply-kit\`).
9. **Fill the config** (§5). Tip: say *"Ask me questions to fill the config"*.
10. **Create templates**: agent offers `/create-template` — proposes role categories
    (e.g. Full-Stack MERN, Frontend, Backend Node), builds CV + resume + cover letter
    per category as PDF/Markdown/LaTeX in your `templates` folder.
11. **Review every template PDF.** Models hallucinate (wrong projects, wrong claims).
    Write issues into a Markdown note, tell the agent *"fix these"*.
12. **Validate**: ask *"is setup finished?"* / run `./doctor.sh --mode all`.
13. **Start a fresh session**, then run a skill (§7).

## 4. Google Cloud Console — click path

Needed so the agent can **draft Gmail, upload to Drive, write to Sheets**.
Full text: `docs/help/02-cloud-console.md`. Summary:

1. https://console.cloud.google.com → **New project** (`job-apply-kit`).
2. **APIs & Services → Library**: enable **Gmail API**, **Google Drive API**,
   **Google Sheets API** (shows *Manage* if already on).
3. **OAuth consent screen**: External, app name, your email; add the 4 scopes
   (gmail.readonly, gmail.compose, drive, spreadsheets — `gmail.send` is
   deliberately absent); add **yourself as Test user**. Stay in *Testing*.
4. **Credentials → Create credentials → OAuth client ID → Desktop app → Create →
   Download JSON**.
5. Tell the agent where the JSON is. It stores it outside the repo.
6. Complete the browser sign-in (`--auth-code` step) once.

Gotchas to say out loud:
- **Never share or commit** the client-secret JSON or tokens.
- Testing-mode tokens **expire after 7 days unused**; re-auth, daily use keeps it alive.
- Create/choose a **Drive folder** and **Google Sheet**; their IDs are in the URLs
  (`/folders/<ID>`, `/d/<ID>/edit`). If missing, the agent offers to create them
  (`sheet_init.py`).

## 5. The config file (what to fill)

Location: `~/.config/job-apply-kit/config.md` (override with `$JAK_CONFIG`).
Template: `config.example.md`; reference: `docs/help/00-config.md`.

| Group | Keys (examples) | Note |
|---|---|---|
| Identity | name, email, phone | agent fills from CV; **check phone/email** |
| Sources | CV URL, projects URL, certifications URL | CV source = always-up-to-date Google Doc |
| Google | Drive folder ID, Sheet ID, tab name | required |
| Filters | max experience (default 5), salary floor, currency, on-site locations, remote ok + remote floor | missing salary floors = hard error |
| Search | BDJobs terms, LinkedIn dorks | from §2 |
| Sources URLs | Facebook saved URL, Discord channel URLs | add by hand |
| Truth gates | skills you do NOT have | never claimed |

Review it manually once after the agent writes it.

A sanitized, real working example (search lists, tracker columns) is in `docs/workshop/example-config.md` — show it on a slide.

## 6. Getting free (or cheap) tokens — verified 2026-10-08

Browser automation uses a lot of tokens. Options:

| Option | Status | Verified how |
|---|---|---|
| **OpenCode free models** | Works. Local `opencode models` lists `opencode/muse-spark-1.3-contributor-free`, `opencode/mimo-v2.6-flash-free`, `nemotron-3-ultra-free`, `longcat-2.5-preview-free`, etc. In the app search "free". | Ran `opencode models` on 2026-10-08. The public Zen docs page lags the live list (shows MiMo-V2.5 Free, DeepSeek V4 Flash Free, Nemotron 3 Ultra Free) — trust your own `opencode models`. https://opencode.ai/docs/zen |
| **Muse Spark 1.3** (Meta) | Fast. | **Privacy caveat:** "contributor-free" models may use your prompts for training; your CV and email content go through it. Use a paid/other model if that matters. |
| **MiMo V2.6 Flash** (Xiaomi) | Free in OpenCode. | Good alternative. |
| **Compare models** | https://artificialanalysis.ai → Models | Search each model name, compare intelligence; for coding check coding benchmarks. Lists change, re-check. |
| **Gemini for students** | Google announced (2026-08-19) 1 free year of Google AI Pro (US) / AI Plus (other countries), claim by **2026-12-31** via SheerID at one.google.com/ai-student; auto-renews to paid, cancel in time. | Web search: Google blog, Tom's Guide, MacRumors. Eligibility varies by country — check the official page. |
| **Caveman skill** | Cuts verbose output. | GitHub `JuliusBrussee/caveman`. Independent tests show ~15-30% output savings, not the viral 75% — output is a small slice of total tokens. Cheap and harmless; don't expect miracles. Install from the GitHub URL, not copy-paste. |
| **Paid** | Claude Code subscription is smoothest. | Highest token use; pick for convenience. |

Weaker models: slower, retry more, make more form mistakes. Smarter model = fewer
errors and faster runs.

## 7. Daily run (what to say)

Run one skill at a time; type `run` then `@` to pick the skill *folder* (keeps all
its files in context).

| Say | Skill |
|---|---|
| "check FB saved" | `check-facebook-saved` |
| "run LinkedIn" | `linkedin-full-run` |
| "check LinkedIn saved" | `check-linkedin-saved` |
| "run BDJobs" | `bdjobs-full-run` |
| "check Discord jobs" | `check-discord-jobs` |
| "here are screenshots" | `check-image-batch` |

Typical full session: ~1-2 h, can run in the background while you do other work.
Each skill does: read config → download local tracker snapshot (fast dedupe) →
open browser tab → extract → verdicts (`new / applied / drafted / skipped-duplicate /
expired / not-a-job`) → process **new only** → Sheet row + Drive upload + Gmail draft.
Example real run (2026-10-07): 61 saved items → 26 not-a-job, 20 duplicate,
4 expired, 4 drafted, 7 left manual.

## 8. Your review checklist (the human job)

Do this after every run — agents make mistakes:

- [ ] Open the Sheet; read each new row's job description once.
- [ ] Open each Gmail draft: right company, right role, **phone number present**, sensible body.
- [ ] Posts with a **Google Form** or portal link: the agent may have drafted an email anyway — apply via the form.
- [ ] Wrong template chosen? Tell the agent; it can redo.
- [ ] Bad email style? Put a sample body in a text/Markdown file, tell the agent to follow it (and save it as a preference).
- [ ] Only then send drafts / press Submit.
- [ ] Close the debug browser.

## 9. Windows / known problems

- PowerShell syntax errors → install Git Bash; agents write helper scripts to files to dodge it.
- "Node not found" → fix PATH (`node -v` must work in the terminal that launched the agent).
- Slow on small models; Linux/WSL2/VM is faster. See `docs/help/08-compatibility.md`.
- Lost tabs / stuck run → start a new session and re-run; dedupe prevents repeats.

## 10. Safety and privacy summary

Never-submit rule; drafts only; secrets live outside the repo; debug-browser
exposure; free "contributor" models may train on data; always review.
(BDJobs portal Apply is the single documented exception, inside `bdjobs-full-run`.)

---

## Appendix A — Session outline (for the presentation, ~45 min)

| Min | Slide group |
|---|---|
| 0-3 | Problem + one rule |
| 3-10 | Manual routine → what is automated (§2) |
| 10-15 | Architecture: 3 parts, skills map |
| 15-30 | Setup walk-through (§3-5), Google console live/screens |
| 30-35 | Free tokens (§6) |
| 35-42 | Demo run + review checklist (§7-8) |
| 42-45 | Safety, Q&A, links |

## Appendix B — Open items for polish (assigned to the delegate agent)

- B1: Make a tidy, beginner-friendly `GUIDE.md` from this plan (short sentences,
  numbered steps, callout boxes), keep all facts.
- B2: Build the presentation `docs/workshop/slides/index.html` (self-contained HTML,
  arrow-key navigation, ~25 slides, speaker notes), following Appendix A.
- B3: Cross-check every file path/command against the repo; fix mismatches.
- B4: Never invent facts; mark anything unverified as "check yourself".
