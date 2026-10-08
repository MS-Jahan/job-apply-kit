# Slides redesign spec (v2) — written by coordinator, built by delegate

Output: `slides/index.html` (overwrite; keep old as `slides/index.v1.html`). One file, inline CSS/JS, no network, no CDN, no external fonts (system fonts only).

## Navigation chrome (the user's explicit ask: total count + current slide)
- Always-visible bottom bar: **"Slide 7 of 30"** (large, >=22px, high contrast) on the right, section name on the left (e.g. "SETUP"), thin progress bar across the very top (width = current/total).
- Clickable dot/segment strip is optional; instead add an **Overview grid (key `O`)**: all slides as numbered cards with titles, click to jump.
- Keys: Right/Space/PageDown next, Left/PageUp prev, Home/End, `O` overview, `N` speaker notes, `F` fullscreen, `?` help, number + Enter = jump to slide. URL hash `#7` deep-links and updates on navigation.
- Click: only the on-screen Prev/Next buttons (bottom corners) advance; clicking text must NOT advance. Touch: swipe left/right.
- Print CSS: one slide per page, notes hidden.
- No JS errors with JS disabled for first slide (slide 1 visible by default).

## Visual design
- Dark theme default, `prefers-color-scheme: light` supported via CSS variables.
- 16:9 stage scaled to the window (CSS transform or vw/vh units), content never overflows at 1280x720, 1920x1080 and 390x844 (phone, stacked).
- Type: title 56-64px, body >=28px at 1080p, max 5 bullets/slide, <=18 words/bullet. Tables <=5 rows. Code in monospace pill.
- Section colour accent per section (Intro, Manual routine, Architecture, Setup, Google, Config, Tokens, Run, Safety, Wrap-up) shown in the bottom bar + a small label top-left.
- Callouts: Tip (green), Warning (amber), Danger (red) with icon glyph (unicode), not colour only.
- Simple inline SVG diagrams for: (a) 6-step pipeline flow, (b) 3-part architecture, (c) human-in-the-loop "agent stages -> you review -> you send".
- Subtle slide transition (fade, 150ms), disabled under `prefers-reduced-motion`.
- Accessibility: contrast AA, `aria-live` slide counter, focus-visible, semantic headings.

## Slide list (30)
| # | Section | Title | Content source |
|---|---|---|---|
| 1 | Intro | Job Apply Kit — stop the daily grind | PLAN §1 |
| 2 | Intro | Who this is for + what you will leave with | |
| 3 | Intro | The one rule: fill, stage, STOP | GUIDE |
| 4 | Intro | What the kit does — 6-step pipeline (SVG) | PLAN §1 |
| 5 | Manual | Manual routine vs automation (table: FB, LinkedIn, BDJobs, Discord, screenshots) | PLAN §2 |
| 6 | Manual | Facebook: save while scrolling, daily group visit (not automated) | |
| 7 | Manual | LinkedIn dork queries (example + length-limit warning) | PLAN §2.1 |
| 8 | Manual | BDJobs: keywords beat categories | PLAN §2.2 |
| 9 | Architecture | 3 parts: email, browser, CV generation (SVG) | |
| 10 | Architecture | Skills map: what to say -> which skill | PLAN §7 |
| 11 | Setup | Setup path at a glance (numbered 1-13 in 3 columns) | PLAN §3 |
| 12 | Setup | Pick a harness + model | |
| 13 | Setup | First prompt + "install everything you can" | |
| 14 | Setup | Prerequisites + Windows Git Bash note | |
| 15 | Setup | Debug browser on port 9222 | |
| 16 | Google | Why Google Cloud + what you create | PLAN §4 |
| 17 | Google | Console click path: project -> 3 APIs | |
| 18 | Google | Consent screen + Desktop OAuth client + download JSON | |
| 19 | Google | Gotchas: 7-day tokens, never share JSON, Drive/Sheet IDs from URL | |
| 20 | Config | Config file: location + key groups | PLAN §5 |
| 21 | Config | Worked example (from example-config.md, placeholders only) | |
| 22 | Config | Templates: create, then REVIEW every PDF | PLAN §3 steps 10-11 |
| 23 | Tokens | Free tokens: OpenCode free models (+ privacy caveat) | PLAN §6 |
| 24 | Tokens | Gemini student offer, Artificial Analysis, caveman (honest 15-30%) | |
| 25 | Run | Daily run: say this -> that happens | PLAN §7 |
| 26 | Run | What one run looks like (example numbers: 61 items -> 4 drafts) | |
| 27 | Run | Your review checklist (the human job) | PLAN §8 |
| 28 | Safety | Security: what can go wrong (7 risks from SECURITY_REVIEW.md, 1 line each) | SECURITY_REVIEW.md |
| 29 | Safety | Hostile job posts: indirect prompt injection and why drafts-only protects you | |
| 30 | Wrap | Recap, links (repo docs paths), Q&A | |

Every slide: speaker notes (2-4 sentences). No personal data (names, phone, IDs, emails). No unverified claims: mark "check yourself".

---
# Addendum: consulting-grade slide method (from ~/Downloads/claude-skills-for-consulting-slide-design-skills; scanned, benign)

Rules applied (action-title-writer, slide-density-balancer, flow-and-page-tracker-auditor, color-and-brand-discipline, partner-review-checklist):
1. **Action titles**: every slide title is ONE full-sentence claim (8-14 words, one line), not a topic. Read in order they must tell the story. Use the titles below verbatim (shorten only if they wrap to 2 lines). Never invent numbers; only use numbers already in PLAN/GUIDE.
2. **Density**: one message per slide, max 5 bullets, short lines. Detail goes to speaker notes or the guide.
3. **Page tracker**: top-of-slide tracker listing the 10 sections, current one highlighted in the accent colour (small, neutral). Add a **section divider slide** is NOT needed (keeps 30 slides); instead the tracker + section label in the bottom bar do the job. Footer on every slide: "Slide N of 30" + short deck title.
4. **Colour**: neutral base + ONE accent (green). Amber only for warnings, red only for danger. Same concept = same colour on every slide.
5. **Review pass** at the end (partner checklist): story clear? titles chain? one message each? numbers sourced? ask/next step at the end? Output Blockers/Majors/Minors into opencode/REVIEW.md and fix Blockers+Majors.

## Action titles (use these)
1 Stop doing the daily job-hunt grind by hand
2 After this session you can run the kit yourself
3 The agent fills and stages applications, but never submits
4 Six automated steps turn job posts into reviewed drafts
5 Every manual job-search habit has an automated counterpart
6 Saving Facebook posts while scrolling feeds the automation
7 Short LinkedIn dork queries find fresh posts; long ones return nothing
8 BDJobs keywords find jobs that category browsing misses
9 Email drafting, browser automation and CV generation work together
10 Say one phrase and the matching skill runs
11 Setup takes thirteen steps, and the agent does most of them
12 Any harness works; free OpenCode models cover small budgets
13 Two prompts start the whole setup
14 Python, Node, PDF tools and Git Bash are the prerequisites
15 A debug-mode browser lets the agent use your logged-in sessions
16 Google Cloud gives the agent safe access to Gmail, Drive and Sheets
17 Three enabled APIs are all the project needs
18 A Desktop OAuth client and its JSON file complete the credentials
19 Four Google gotchas cause most setup failures
20 One config file outside the repo holds everything personal
21 A real config shows how search terms and filters look
22 Templates are built once, then every PDF must be reviewed
23 OpenCode's free models are verified, with a privacy catch
24 Student Gemini, model benchmarks and Caveman each save a little
25 Each daily command triggers a complete scan-to-draft run
26 One real run turned 61 saved items into 4 drafts
27 Your review of every draft is the safety net
28 Seven risks exist; each has a simple mitigation
29 Hostile job posts cannot send anything because the agent only drafts
30 Start today: set up, run one skill, review, then send

---
# v3 changes (implemented 2026-10-08 from OPUS_PLAN.md)
- New titles: #7 (short LinkedIn queries), #11 (13 steps in 4 phases), #12 (install agent app + clone), #18 (Desktop sign-in key file).
- Layout templates: hero, focus, table, split, steps, stat, diagram, code-os, grid. Content fills the stage (container-query units on a 16:9-ish stage).
- Windows | macOS | Linux tabs on #12, #14, #15, #20, #30 (one global choice, remembered; auto-detected).
- Dark theme default; light only via `T` or `?theme=light`. No prefers-color-scheme auto switch.
- Rule: no slide leaves more than ~22% of the body area empty at 1280x720 and 1920x1080 (measured with Playwright).
- Mobile: single column, tables stack, only current section chip in the tracker.
