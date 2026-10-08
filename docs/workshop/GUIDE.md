# Job Apply Kit — Beginner's Guide (Windows, macOS, Linux)

> Online version of the workshop slides: https://job-apply-kit.pages.dev/
> This kit is a starting point, not a finished product: expect to give your agent instructions as you use it so it fits your own workflow and job platforms.
> Facts come from `docs/workshop/PLAN.md`, `README.md`, `docs/BOOTSTRAP.md` and `docs/help/*`.
> If this guide disagrees with those files, trust those files.
> Reading time for sections 0–15: about 40 minutes.

> **The one rule behind everything:** the agent fills, stages, and *stops* at the final Submit button.
> Emails are Gmail **drafts**, never sent. You review every one before anything goes out.

## Contents

0. [Start here](#0-start-here)
1. [What the kit does](#1-what-the-kit-does)
2. [Your manual routine (what the agent copies)](#2-your-manual-routine-what-the-agent-copies)
3. [Before you start](#3-before-you-start)
4. [Setup A — install the tools](#4-setup-a--install-the-tools)
5. [Setup B — get the kit and start the agent](#5-setup-b--get-the-kit-and-start-the-agent)
6. [Setup C — the debug browser](#6-setup-c--the-debug-browser)
7. [Setup D — Google access (click path)](#7-setup-d--google-access-click-path)
8. [Setup E — your CV and the config file](#8-setup-e--your-cv-and-the-config-file)
9. [Setup F — templates and review](#9-setup-f--templates-and-review)
10. [Check your setup](#10-check-your-setup)
11. [Daily run](#11-daily-run)
12. [Your review checklist](#12-your-review-checklist)
13. [Free or cheap tokens](#13-free-or-cheap-tokens)
14. [Safety and privacy](#14-safety-and-privacy)
15. [If it breaks](#15-if-it-breaks)
- [Appendix A — paths per OS](#appendix-a--paths-per-os) · [B — glossary](#appendix-b--glossary) · [C — FAQ](#appendix-c--faq) · [D — worked example](#appendix-d--worked-example)

---

## 0. Start here

### Pick your OS. Each step below has a row for it.

- **Windows 10/11:** install **Git for Windows**, then use **Git Bash** for every kit command. Use **PowerShell** only for `winget install …` lines. Python is `py -3`, never `python`. Your home folder is `C:\Users\<you>` (`%USERPROFILE%`). *(Sources: `skills/job-apply-core/OPERATIONS.md` §0, `docs/BOOTSTRAP.md` §0.)*
- **macOS:** use the **Terminal** app. Install tools with **Homebrew** (`brew`). Python is `python3`. Home is `/Users/<you>`.
- **Linux:** use your terminal and your package manager (`apt`, `dnf`, `pacman`). Python is `python3`. Home is `/home/<you>`. This is the author's own platform and the smoothest (`docs/help/08-compatibility.md`).
- **Not sure?** Ask the agent: *"Which OS am I on?"*

### How to read the commands

- Lines labelled **PowerShell** start in the Windows PowerShell window. Lines labelled **Git Bash** or **Terminal** start in that terminal.
- Do not type a prompt sign (`$` or `PS>`). Type only the command.
- `<you>` and `<repo-url>` are placeholders. Replace them, including the angle brackets. The presenter gives the repo link in the chat.

### Five words you will hear

| Word | Plain meaning |
|---|---|
| **Agent app** | The program where you chat with the AI and it runs commands. Here: OpenCode or Claude Code. |
| **Skill** | A folder with instructions for one job, like `check-facebook-saved`. |
| **Debug browser** | Your normal browser started with a special switch (port 9222) so the agent can see your open tabs. |
| **Google sign-in key** | A JSON file you download from Google Cloud. It lets the kit talk to *your* Gmail, Drive and Sheets. |
| **Search query** | A short search line with AND / OR, for LinkedIn and BDJobs. |

More words: [Appendix B](#appendix-b--glossary).

---

## 1. What the kit does

An AI agent does the boring daily job-hunt grind. It works in 6 steps:

1. **Scan** job sources (Facebook saved, LinkedIn, BDJobs, Discord, screenshots).
2. **De-duplicate** against your Google Sheet tracker (never process a job twice).
3. **Pick a template** (CV / resume / cover letter) closest to the job.
4. **Draft** a Gmail message or fill the application form, stopping before Submit.
5. **Record** a row in the tracker and upload the PDFs to Drive.
6. **You** review the Sheet, the drafts and the forms, then press send.

> [Figure D-1: pipeline diagram — see slide 4 of `slides/index.html`.]

| Part | What it does |
|---|---|
| Email drafting | Writes a Gmail draft for each new job |
| Browser automation | Opens job sites, reads posts, fills forms |
| CV / resume / cover-letter generation | Builds your application documents from your templates |

> **Tip:** You stay in control. The agent never sends or submits. You press every final button.

---

## 2. Your manual routine (what the agent copies)

Learn the manual routine first. Then the agent version makes sense.

| Source | Manual routine | What is automated |
|---|---|---|
| **Facebook saved** | While scrolling, *Save* every job post. Later open the saved list and apply one by one. | `check-facebook-saved` reads the last ~20–25 saved items, skips ones already in the Sheet, and processes the new ones. |
| **Facebook groups** | Search "career", "job vacancy", "CSC jobs". Join 20–30 job groups. Open each once a day and *Save* good posts. | **Not automated.** You visit the groups. Saving feeds the automation above. |
| **LinkedIn** | Post search with short AND / OR queries, sorted by **Latest**. | `linkedin-full-run` runs your query list. `check-linkedin-saved` processes your saved posts. |
| **BDJobs** | Category browsing misses jobs posted in the wrong category. Search by **keyword** instead. | `bdjobs-full-run` runs your keyword list: search, save, decide, apply or draft. |
| **Discord** | Job channels you follow. | `check-discord-jobs` reads the last N messages. |
| **Screenshots** | Job posts you screenshot. | `check-image-batch` processes the batch. |

### 2.1 LinkedIn search queries

1. Start from this example: `Software Developer AND (Hiring OR Vacancy) AND (Dhaka OR Bangladesh)`.
2. For remote jobs, add `(Remote OR Hybrid)`.
3. On the results page, choose **Posts**, then sort by **Latest**.
4. Keep each query short. Run them one by one.

> **Warning:** Do not chain every query with AND into one huge line. LinkedIn has a length limit and returns nothing.

5. To make queries fast, upload your CV to any chat model, give it the example above, and ask for queries for your roles. Paste them into your config.

### 2.2 BDJobs keywords

1. Use many spellings of each title: "Software Engineer", "Software Developer", "Full Stack" and "Fullstack", "Front End" and "Frontend", "Backend", "MERN", "Trainee Engineer".
2. Scroll past the top results. They can be paid or priority ads.

---

## 3. Before you start

- [ ] A laptop with Windows 10/11, macOS or Linux, and an internet connection.
- [ ] A Google account (the one you will use for the kit).
- [ ] Your CV as a PDF or a Google Doc.
- [ ] Logins for Facebook, LinkedIn and BDJobs.
- [ ] About 2 hours for the first setup *(estimate; the repo gives no figure)*.

---

## 4. Setup A — install the tools

> **The agent can do this for you.** Open your agent app and say *"Install everything you can."* The commands below are here so you recognise them. Source: `docs/BOOTSTRAP.md` §2.

| Tool | Windows (PowerShell) | macOS (Terminal) | Linux (Terminal) |
|---|---|---|---|
| Git (includes Git Bash on Windows) | `winget install --id Git.Git -e` *(verify)* | `brew install git` *(verify)* | your package manager *(verify)* |
| Python 3.9+ | `winget install Python.Python.3.12` | `brew install python@3.12` | `sudo apt install python3 python3-pip` |
| Python packages (from the kit folder) | Git Bash: `py -3 -m pip install -r requirements.txt` | `python3 -m pip install -r requirements.txt` | same as macOS |
| Node, **latest LTS** via nvm | nvm-windows installer, then `nvm install lts` and `nvm use <version>` | `nvm install --lts` | `nvm install --lts` |
| agent-browser | Git Bash: `npm install -g agent-browser@latest` | `npm install -g agent-browser@latest` | same |
| tectonic (PDF maker) | `winget install --id tectonic.tectonic -e` | drop-sh one-liner at tectonic-typesetting.github.io | same as macOS |
| poppler (`pdfinfo`) | `winget install --id oschwartz10612.Poppler -e` | `brew install poppler` | `sudo apt install poppler-utils` |
| pandoc (optional) | `winget install --exact --id JohnMacFarlane.Pandoc` | `brew install pandoc` *(verify)* | your package manager |
| Agent app | `winget install --id SST.OpenCodeDesktop -e` · or `irm https://claude.ai/install.ps1 \| iex` | `npm i -g opencode-ai@latest` | `npm i -g opencode-ai@latest` |

Notes:

- **Windows Git Bash first line** (once per window): `export PATH="$(cygpath "$APPDATA/npm"):$PATH"` (`OPERATIONS.md`).
- **Node 18 is not enough.** Install the latest LTS with nvm (`docs/BOOTSTRAP.md` §2.2). `winget install OpenJS.NodeJS.LTS` is a fallback (`docs/help/01-prerequisites.md`).
- Rows marked *(verify)* are not in the repo docs. Check them on the official site before the workshop.
- Claude Code install: see https://code.claude.com/docs/en/setup.

> **If it breaks**
> | You see | Do this |
> |---|---|
> | `'npx' is not recognized` | Close the agent app and open it again from a **new** terminal (`docs/EXTERNAL_TOOLS.md` §5.1) |
> | `python` opens the Microsoft Store (Windows) | Use `py -3`, never bare `python` |
> | `winget` not found | Update "App Installer" from the Microsoft Store |

---

## 5. Setup B — get the kit and start the agent

1. Open a terminal: **Git Bash** on Windows (Start menu), **Terminal** on macOS, your terminal on Linux.
2. Clone the kit into your home folder.

| Step | Windows Git Bash | Windows PowerShell (fallback) | macOS / Linux |
|---|---|---|---|
| Clone | `cd ~ && git clone <repo-url> job-apply-kit && cd job-apply-kit` | `cd $env:USERPROFILE; git clone <repo-url> job-apply-kit; cd job-apply-kit` | `cd ~ && git clone <repo-url> job-apply-kit && cd job-apply-kit` |
| Register tools | `./install.sh` | `py -3 install.py` | `./install.sh` |

3. Open the folder in your agent app. OpenCode app: **Add Project**. Claude Code: run `claude` inside the folder.
4. Send two prompts:
   1. *"I am new to this project. What should I install or customize, and how do I get started?"*
   2. *"Install everything you can."*

The agent then follows `docs/BOOTSTRAP.md`. It will ask, in order: browser, Google key file, your CV.

Kit folder on Windows: `C:\Users\<you>\job-apply-kit`.

> **If it breaks**
> | You see | Do this |
> |---|---|
> | `git: command not found` | Install Git (section 4), then open a new terminal |
> | PowerShell shows weird syntax errors | Use **Git Bash** for kit commands (`OPERATIONS.md`) |

---

## 6. Setup C — the debug browser

The agent uses *your* logged-in browser through port **9222**, so you log in once.

1. The agent creates a desktop shortcut (it asks which browser you use).
2. **Close all browser windows** (including tray icons).
3. Double-click the shortcut.
4. Log in once to Facebook, LinkedIn, BDJobs and Google.

| | Windows | macOS | Linux |
|---|---|---|---|
| Desktop shortcut | `JAK Google Chrome (debug).lnk` (Brave: `JAK Brave (debug).lnk`) | `JAK Google Chrome (debug).command` | `jak-chrome-debug.desktop` |
| Launcher in the kit folder | `browser-debug-chrome.bat` / `browser-debug-brave.bat` | `browser-debug-chrome.sh` | same as macOS |
| List browsers | `py -3 skills/job-apply-core/scripts/browser_setup.py --list` | `python3 skills/job-apply-core/scripts/browser_setup.py --list` | same |
| Make the shortcut | `py -3 skills/job-apply-core/scripts/browser_setup.py --browser chrome --create` | `python3 … --browser chrome --create` | same |
| Check it works | PowerShell: `curl.exe http://127.0.0.1:9222/json/version` · Git Bash: `curl http://127.0.0.1:9222/json/version` | `curl http://127.0.0.1:9222/json/version` | same |

> [Figure S-2: the desktop shortcut. Figure S-3: terminal output of the check.]

> **Warning:** the debug port lets any local program read your browser cookies. Use the shortcut only while the agent runs. Browse normally the rest of the time.

> **If it breaks**
> | You see | Do this |
> |---|---|
> | Only `about:blank` tabs | Your normal browser was still open. Close **all** windows, start the shortcut again |
> | `curl` fails | The browser is not running in debug mode. Use the shortcut, not the normal icon |
> | Shortcut name differs | The Linux name in the code is `jak-chrome-debug.desktop`; some docs say "JAK … (debug)" |

Sources: `skills/job-apply-core/scripts/browser_setup.py`, `docs/BOOTSTRAP.md` §3, `docs/help/03-browser-setup.md`.

---

## 7. Setup D — Google access (click path)

The kit needs Gmail (drafts), Drive (PDFs) and Sheets (tracker). Full page: `docs/help/02-cloud-console.md`. It is free and needs no billing.

1. Go to https://console.cloud.google.com and sign in with your kit Google account.
2. **New project**, name it `job-apply-kit`, then select it in the top bar.
3. **APIs & Services → Library**: enable **Gmail API**, **Google Drive API**, **Google Sheets API**. ("Manage" means already on.)
4. **OAuth consent screen**: user type **External**; app name and your email; add four scopes: `gmail.readonly`, `gmail.compose`, `drive`, `spreadsheets`; add **yourself as a test user**; leave it in **Testing**.
5. **Credentials → Create credentials → OAuth client ID → Desktop app → Create → Download JSON.**
6. Tell the agent where the JSON file is. It stores it outside the repo and finishes the browser sign-in (the `--auth-code` step in `docs/help/02-google-setup.md`).

> [Figures S-4 to S-7: New project, API Library, consent screen scopes, Create OAuth client.]

| Gotcha | What to know |
|---|---|
| **Never share or commit the JSON or tokens** | They are password-equivalent. |
| **7 days** | Testing-mode tokens expire after 7 days unused. Sign in again. Daily use keeps it alive. |
| **IDs are in URLs** | Drive folder: `/folders/<ID>`. Sheet: `/d/<ID>/edit`. |
| **No folder or Sheet yet?** | The agent offers to create them (`sheet_init.py`). |

> **Warning:** `gmail.send` is deliberately missing from the scopes, so the kit can only draft. Keep it that way.

Where the key and tokens live: see [Appendix A](#appendix-a--paths-per-os).

> **If it breaks**
> | You see | Do this |
> |---|---|
> | "Access blocked" at sign-in | Add your own address under **Test users** |
> | Auth worked last week, fails now | The 7-day token expired: sign in again |
> | Signed in with the wrong account | Use the same Google account as `email_google` in the config |

---

## 8. Setup E — your CV and the config file

1. Give the agent your CV: a PDF path, drag-and-drop, or a Google Doc link. A Google Doc is read through the debug browser (section 6), so do that first.
2. The agent writes your config. Where it lives:

| OS | Config file |
|---|---|
| Windows | `C:\Users\<you>\.config\job-apply-kit\config.md` (same as `%USERPROFILE%\.config\job-apply-kit\config.md`) |
| macOS | `/Users/<you>/.config/job-apply-kit/config.md` |
| Linux | `/home/<you>/.config/job-apply-kit/config.md` |

Override with the `JAK_CONFIG` variable. Template: `config.example.md`. Reference: `docs/help/00-config.md`.

3. Tip: say *"Ask me questions to fill the config"* and answer in chat.
4. Review the file once by hand. Check phone and email especially.

| Group | Keys (examples) | Note |
|---|---|---|
| Identity | name, email, phone | filled from your CV; **check them** |
| Sources | CV URL, projects URL, certifications URL | the CV source is your always-up-to-date Google Doc |
| Google | Drive folder ID, Sheet ID, tab name | required |
| Filters | max experience (default 5), salary floor, currency, on-site locations, remote OK | missing salary floors are a hard error |
| Search | BDJobs keywords, LinkedIn queries | from section 2 |
| Source URLs | Facebook saved URL, Discord channel URLs | add by hand |
| Truth gates | skills you do **not** have | never claimed |

Check the config:

| Windows Git Bash / PowerShell | macOS / Linux |
|---|---|
| `py -3 skills/job-apply-core/scripts/jak_config.py --check` | `python3 skills/job-apply-core/scripts/jak_config.py --check` |
| `py -3 skills/job-apply-core/scripts/jak_config.py --show` (masks phone and email) | `python3 skills/job-apply-core/scripts/jak_config.py --show` |

A full sanitised example is in [Appendix D](#appendix-d--worked-example).

---

## 9. Setup F — templates and review

1. The agent offers `/create-template`. It proposes role categories from your CV (for example Full-Stack MERN, Frontend, Backend Node).
2. Say yes, or name your own categories.
3. It builds a CV, a resume and a cover letter per category (PDF, Markdown, LaTeX) in the `templates` folder inside the kit folder.
4. **Open every PDF and read it.** Models sometimes invent projects or claims.
5. Write each problem in a note. Tell the agent *"fix these"*.

> **Warning:** one wrong claim in a template is copied into every application. Check it now.

---

## 10. Check your setup

| Windows Git Bash | Windows PowerShell | macOS / Linux |
|---|---|---|
| `./doctor.sh --mode all` | `py -3 doctor.py --mode all` | `./doctor.sh --mode all` |

- Green means go. A `MISSING` line names its own fix.
- Or ask the agent: *"Is setup finished?"*
- Start a **fresh session** afterwards, then run a skill.

> [Figure S-8: doctor output with OK and MISSING lines.]

---

## 11. Daily run

Run one skill at a time. Type `run`, then `@`, and pick the skill **folder** so all its files are in context.

| Say | Skill |
|---|---|
| "check FB saved" | `check-facebook-saved` |
| "run LinkedIn" | `linkedin-full-run` |
| "check LinkedIn saved" | `check-linkedin-saved` |
| "run BDJobs" | `bdjobs-full-run` |
| "check Discord jobs" | `check-discord-jobs` |
| "here are screenshots" | `check-image-batch` |

What a run does: read config → download a local Sheet snapshot → open a browser tab → extract posts → give each a verdict (`new`, `applied`, `drafted`, `skipped-duplicate`, `expired`, `not-a-job`) → process **new only** → Sheet row + Drive upload + Gmail draft.

A full session takes about 1–2 hours and can run in the background. Real example (2026-10-07, Facebook saved): 61 items → 26 not-a-job, 20 duplicate, 4 expired, **4 drafted**, 7 left for the user.

> [Figure D-2: the run loop — see slide 25.]

---

## 12. Your review checklist

The agent makes mistakes. After every run:

- [ ] Open the Sheet and read each new row's job description once.
- [ ] Open each Gmail draft: right company and role, **phone number present**, sensible body.
- [ ] Post has a Google Form or portal link? The agent may have drafted an email anyway. Apply through the form.
- [ ] Wrong template? Tell the agent to redo it.
- [ ] Bad email style? Put a sample body in a text file and tell the agent to follow it.
- [ ] Only then send the drafts or press Submit.
- [ ] Close the debug browser.

---

## 13. Free or cheap tokens

Browser automation uses many tokens. Options (verified 2026-10-08):

| Option | Status |
|---|---|
| **OpenCode free models** | Run `opencode models` and look for `free`. Listed on the author's machine: `opencode/muse-spark-1.3-contributor-free`, `opencode/mimo-v2.6-flash-free`, `nemotron-3-ultra-free`, `longcat-2.5-preview-free`. The public docs page (https://opencode.ai/docs/zen) lags, so trust your own list. |
| **Privacy catch** | "Contributor" free models may train on your prompts. Your CV and email text go through them. Use a non-training model for real data. *(Third-party analysis; check OpenCode's terms.)* |
| **Compare models** | https://artificialanalysis.ai → Models. For coding, check coding scores. |
| **Gemini for students** | Google announced (2026-08-19) one free year of AI Pro (US) or AI Plus (other countries). Claim by **2026-12-31** at one.google.com/ai-student. It auto-renews to paid, so cancel in time. Eligibility varies by country. |
| **Caveman skill** | GitHub `JuliusBrussee/caveman`. Independent tests show about 15–30% fewer output tokens, not the viral 75%. Cheap and harmless. |
| **Paid Claude Code** | Smoothest, and the most token-hungry. |

A smarter model makes fewer form mistakes and finishes faster.

---

## 14. Safety and privacy

1. **Never-submit:** drafts and staged forms only. One documented exception: the BDJobs portal Apply button, inside `bdjobs-full-run`.
2. Secrets live **outside** the repo. Never commit the Google JSON, tokens or your CV file.
3. Seven risks from `docs/workshop/SECURITY_REVIEW.md`:

| Risk | What you do |
|---|---|
| **High:** your CV text file in the repo root is not git-ignored | Add it to `.gitignore` before any push |
| **Medium:** hostile job posts (indirect prompt injection) | Review every draft; never grant send permission |
| **Medium:** debug port exposes cookies | Use the shortcut only while running |
| **Medium:** free contributor models may train on prompts | Use a non-training model for real data |
| **Medium:** Google key file | Keep outside the repo; never share |
| **Low–Medium:** unpinned `npx chrome-devtools-mcp@latest` | Pin a version |
| **Low:** testing-mode tokens expire in 7 days | Sign in again |

A scan of the workshop files, transcripts, MCP config and skills found **no prompt injection or attack**. The risks above are practical.

---

## 15. If it breaks

| Symptom | Fix | OS |
|---|---|---|
| PowerShell syntax errors | Use Git Bash for kit commands | Windows |
| `'npx' is not recognized` / "Node not found" | Fix PATH; open a **new** terminal; `node -v` must work there | all |
| `python` opens the Store | Use `py -3` | Windows |
| `curl` fails in PowerShell | Use `curl.exe` | Windows |
| Only `about:blank` in the debug browser | Close all browser windows, restart the shortcut | all |
| Google sign-in stopped working | 7-day token expired: sign in again | all |
| Run is slow or stuck | Start a fresh session and re-run (the Sheet check prevents repeats); use a stronger model | all |
| Slow on a weak laptop | Try Linux, WSL2 or a VM (`docs/help/08-compatibility.md`) | all |
| Lost tabs | Re-run the same skill | all |

---

## Appendix A — paths per OS

| What | Windows | macOS | Linux |
|---|---|---|---|
| Kit folder (recommended) | `C:\Users\<you>\job-apply-kit` (Git Bash: `~/job-apply-kit`) | `/Users/<you>/job-apply-kit` | `/home/<you>/job-apply-kit` |
| Config file | `C:\Users\<you>\.config\job-apply-kit\config.md` | `/Users/<you>/.config/job-apply-kit/config.md` | `/home/<you>/.config/job-apply-kit/config.md` |
| Google key + tokens | `C:\Users\<you>\.config\job-apply-kit\google\` | `~/.config/job-apply-kit/google/` | `~/.config/job-apply-kit/google/` |
| Templates | `<kit folder>\templates\` (git-ignored) | `<kit folder>/templates/` | same |
| Run history | `<kit folder>\JDs\`, `<kit folder>\output\` (git-ignored) | same, with `/` | same |
| Debug launcher | `browser-debug-chrome.bat` / `browser-debug-brave.bat` in the kit folder | `browser-debug-chrome.sh` | same as macOS |
| Desktop shortcut | `%USERPROFILE%\Desktop\JAK Google Chrome (debug).lnk` (or `OneDrive\Desktop`) | `~/Desktop/JAK Google Chrome (debug).command` | `~/Desktop/jak-chrome-debug.desktop` |
| Claude Code MCP config | `%USERPROFILE%\.claude.json` | `~/.claude.json` | `~/.claude.json` |
| OpenCode MCP config | `%USERPROFILE%\.config\opencode\opencode.json` *(verify)* | `~/.config/opencode/opencode.json` | same |
| Python command | `py -3` | `python3` | `python3` |
| Git Bash program | `%ProgramFiles%\Git\bin\bash.exe` (**not** `System32\bash.exe`, which is WSL) | n/a | n/a |

Sources: `skills/job-apply-core/scripts/jak_config.py`, `browser_setup.py`, `OPERATIONS.md`, `docs/EXTERNAL_TOOLS.md`, `docs/AGENTS.md`, `.gitignore`.

---

## Appendix B — glossary

| Term | Meaning |
|---|---|
| **Agent app** (harness) | The app that runs the AI agent. OpenCode or Claude Code. |
| **Skill** | A folder like `skills/check-facebook-saved/` with a `SKILL.md` contract. Invoke it by name or pick the folder with `@`. |
| **OAuth** | The Google sign-in flow that gives the kit limited access. You approve 4 scopes. No password is stored; the approval is a token file outside the repo. |
| **Debug port** | Port **9222** on your own machine. The agent attaches to your browser there with `agent-browser`. |
| **Search query** (dork) | A short boolean search like `Software Developer AND (Hiring OR Vacancy)`. People call these "dorks". |
| **MCP** | A plug-in channel that lets the agent app use a tool, here Chrome DevTools. `install.sh` registers it. |
| **Token file** | The saved Google approval. Expires after 7 days unused in Testing mode. |
| **Workspace** | The folder the agent runs in, normally the kit folder. |
| **PATH** | The list of folders where your terminal looks for programs. "Node not found" usually means PATH. |
| **Git Bash** | A Unix-style terminal that comes with Git for Windows. |
| **PowerShell** | The default Windows command window. Fine for `winget`, not for kit commands. |
| **winget** | Windows' built-in installer: `winget install …`. |
| **Homebrew** | The macOS package installer: `brew install …`. |
| **nvm** | A tool that installs and switches Node versions. |

---

## Appendix C — FAQ

**1. Does the agent send emails or submit applications?**
No. It drafts Gmail messages and stages forms at the final Submit button. You press send. The single exception is the BDJobs portal Apply button, only inside `bdjobs-full-run`.

**2. Where does my personal data live?**
Outside the repo. Config: `~/.config/job-apply-kit/config.md` (Windows: `C:\Users\<you>\.config\job-apply-kit\config.md`; override: `$JAK_CONFIG`). Tokens: config `google_token_dir`, else `~/.config/job-apply-kit/google/`. Templates, run history (`JDs/`, `output/`), and the workspace also live outside. Never commit these.

**3. Which APIs and scopes does Google need?**
Three APIs: Gmail, Drive, Sheets. Four scopes: `gmail.readonly`, `gmail.compose`, `drive`, `spreadsheets`. `gmail.send` is deliberately absent.

**4. My testing-mode token stopped working. What now?**
Testing tokens expire after 7 days unused. Re-run the `--auth-code` step in `docs/help/02-google-setup.md` (Windows: `py -3` instead of `python3`). Daily use keeps the token alive.

**5. Where do I find my Drive folder ID and Sheet ID?**
They are in the URLs: `/folders/<ID>` for Drive, `/d/<ID>/edit` for Sheets. If you have none, the agent creates them with `sheet_init.py`.

**6. How do I pick a model?**
Run `opencode models` and look for `free`. Compare names on https://artificialanalysis.ai. Smarter models make fewer form mistakes. Free "contributor" models may train on your prompts.

**7. The agent attached to the wrong browser (only `about:blank`). What happened?**
You started the debug browser while the normal browser was still running. The flag was silently ignored. Close ALL browser windows first, then start via the shortcut, then `agent-browser connect 9222`.

**8. It is slow / stuck / lost tabs. What do I do?**
Start a fresh session and re-run the same skill. Dedupe against the Sheet prevents repeats. On Windows, use Git Bash. On weak models, switch to a stronger one.

**9. How do I make LinkedIn queries?**
Upload your CV to any chat model, give it the example dork, and ask for queries for your roles. Paste them into the config. Keep each query short. Sort results by Posts + Latest.

**10. How do I know setup is finished?**
Ask the agent *"is setup finished?"* or run `./doctor.sh --mode all` (Windows PowerShell: `py -3 doctor.py --mode all`). Green means go.

---

---

## Appendix D — worked example

1. This section is copied from `docs/workshop/example-config.md`.
2. That file is a sanitized real working setup. Values are placeholders.
3. The search lists below are real. Copy them and adapt.
4. The real file lives at `~/.config/job-apply-kit/config.md`. On Windows: `C:\Users\<you>\.config\job-apply-kit\config.md`.

Identity (placeholders only):

- **name:** \<Your Full Name\>
- **phone:** \<+880...\>
- **timezone:** Asia/Dhaka
- **email_google:** \<you@gmail.com\>

Sources (placeholders only):

- **cv_source:** \<Google Doc / site URL of your always-up-to-date CV\>
- **projects_source:** \<portfolio / GitHub README URLs, comma separated\>
- **certifications_url:** \<LinkedIn certifications page URL\>

Google (placeholders only):

- **google_backend:** auto
- **drive_folder_id:** \<ID after /folders/ in the Drive URL\>
- **sheet_id:** \<ID between /d/ and /edit in the Sheet URL\>
- **sheet_tab:** Sheet1

Browser:

- **cdp_port:** 9222

Auto-skip:

- **max_experience_years:** 5
- **min_salary:** 15000
- **currency:** BDT
- **remote_ok:** true

Search terms (copy these exactly, then adapt):

- **bdjobs_terms:** Software Engineer, Software Developer, Fullstack, Full stack, Frontend, Front end, Backend, Python, PHP, Android Developer, Flutter Developer, MERN, WordPress, DevOps
- **linkedin_queries:**
    "Software Engineer" AND (hiring OR vacancy) AND (Dhaka OR Bangladesh),
    "Software Developer" AND (hiring OR vacancy) AND (Dhaka OR Bangladesh),
    (Fullstack OR "Full stack") AND developer AND (hiring OR vacancy) AND Dhaka,
    Backend AND (developer OR engineer) AND (hiring OR vacancy) AND Dhaka,
    developer AND (remote OR hybrid) AND (hiring OR vacancy) AND Bangladesh,
    (DevOps OR Android) AND (remote OR hybrid) AND Bangladesh
- **fb_saved_urls:** https://www.facebook.com/saved/
- **discord_channels:** \<channel URLs, comma separated\>
- **discord_cache_dir:** JDs/discord

Tracker columns (15, created by `sheet_init.py`):

Date, Company, Position, Resume Drive, Job Nature, Job Type, Company Location, Job Link,
Job Description, Job Status, How Applied, Contact / Email, Salary / Budget, Deadline, Comments

Notes from the example:

- One short query per line group. Never AND-chain all of them (LinkedIn length limit).
- Leave `templates_dir` empty to use the default. Salary floors empty = hard error only if you enable the filter.
- Fields the agent left blank (truth gates, signature, templates_dir) are normal on day one.

> **Tip:** Start with these lists unchanged. Trim them after your first week of runs.

