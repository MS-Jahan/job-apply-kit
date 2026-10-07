# job-apply-kit

A Claude Code / OpenCode skill kit for tailoring resumes and CVs, and for automating the job-search and
application grind: scanning BDJobs, LinkedIn, Facebook, Discord and pasted job-post screenshots, then
staging an application for your review — never submitting or sending anything without you.

Two tracks:

- **Template-first (the default)**: pick the closest-fit template from your own `templates_dir` and
  attach it as-is, or build one with `/create-template` from your own CV. Fast, consistent, truthful.
- **Deep-tailoring** (`make-resume` / `make-cl` / `critique` / `edit-resume`, backed by a knowledge
  base built with `setup-extract` / `setup-build-kb`): a gap-analysis, character-budget-gated system
  originally built for academic/research CVs, also usable for a from-scratch industry resume. Run it
  on explicit request, or when a job needs a combined skill set no single template covers.

Everything that touches an external site or account follows one rule, everywhere: fill it in, stage it
at the final Submit/Apply button, and stop. Draft emails, never send them. See
`skills/job-apply-core/OPERATIONS.md` for the complete rule set every skill follows.

## Who this is for

Anyone job-hunting who wants an agent to do the repetitive parts — scanning sources, drafting emails,
filling forms, tracking applications in a spreadsheet — while keeping every factual claim traceable to
their own CV and every submission under their own final control.

## Prerequisites

Setting up from scratch (or driving the agent to do it)? Follow
`docs/BOOTSTRAP.md` — per-OS commands, official download sources, and the
agent self-install procedure. Short version
(full matrix in `docs/EXTERNAL_TOOLS.md`):

- Python 3.9+ and its packages (`pip install -r requirements.txt`)
- `tectonic` (PDF compiler) and `poppler-utils` (`pdfinfo`)
- For the apply/search skills: Node 18+, `agent-browser`, a debug-mode browser
  (the agent detects yours and makes desktop shortcuts via `browser_setup.py`),
  and either `gog` or the bundled Python OAuth backend for Google
- Claude Code or OpenCode

## Install

```bash
git clone <this-repo> job-apply-kit
cd job-apply-kit
./install.sh              # installs every skill + registers the chrome-devtools MCP fallback
./doctor.sh --mode all    # reports what's missing for your mode (tailor / apply / all)
```

Install only what you need: `./install.sh make-resume` pulls in just the resume-kit dependency chain;
`./install.sh bdjobs-full-run` pulls in only `job-apply-core` + `humanizer`. Run `./install.sh --list`
to see every skill and its dependencies, `--uninstall` to remove what you installed, `--link` for a
symlinked dev setup that stays in sync with this checkout.

## Updating the kit

One command, run inside this checkout:

```bash
./install.sh --update        # or: python install.py --update
```

It runs `git pull --ff-only` and then reinstalls every skill + MCP entry from
the fresh code. Three rules make this conflict-free:

1. **Never edit kit files in place.** Installed skills under
   `~/.claude/skills` (or the OpenCode/agents equivalents) are generated
   copies — reinstalling overwrites them, by design. Propose changes via a
   branch/PR instead.
2. **Personal data already lives outside the repo** (config file, workspace
   templates, `JDs/`, tracker) — pulling can never touch it.
3. **If the checkout is dirty, `--update` refuses** and lists the changed
   files. Commit your work, move it out, or `git stash`, then re-run. It never
  force-pulls over your edits. `--dry-run` previews the pull without running it.

## Configure

Everything personal lives in one file, outside this repository: `~/.config/job-apply-kit/config.md`
(or wherever `$JAK_CONFIG` points). Copy the template and fill it in, or — easier — once the kit is
installed, just tell your agent:

> "Set up my job-apply-kit config from my CV at \<url or file path\>."

The `job-apply-core` skill walks through it: identity, your CV/resume source URLs, truth-gate lists
(skills you don't actually have, so they're never claimed), and leaves Google/Sheet ids for the next
step. Set up the debug browser first — CVs living in Google Docs are read through it, and a plain
web fetch only returns a truncated page. Then run the one-time setup that creates your tracker:

```bash
python3 skills/job-apply-core/scripts/sheet_init.py
```

This creates a Drive folder, a `templates` subfolder inside it, and a tracker spreadsheet with the 15
required columns, and writes their ids back into your config.

Validate any time:

```bash
python3 skills/job-apply-core/scripts/jak_config.py --check
python3 skills/job-apply-core/scripts/jak_config.py --show   # masks your phone/email in the output
```

## First run (on the shipped fictional example)

No templates yet? Try the kit immediately on three ready-made fictional templates before building your
own:

```bash
./install.sh --with-examples   # copies examples/templates/ into your templates_dir, if it's empty
```

Then build your own set from your real CV:

```
/create-template
```

This proposes role categories from your CV, generates a CV/resume/cover-letter set per category, runs
every truth and format gate, compiles each to the right page count, and registers them in
`templates_dir/INDEX.md` — the file every apply skill reads to pick a template automatically.

## Skill index

| Skill | What it does |
|---|---|
| `job-apply-core` | shared rules (`OPERATIONS.md`), config setup, Google interface, tracker scripts |
| `humanizer` | strips AI writing patterns from emails, cover letters and resume prose |
| `create-template` | generate your own CV/resume/cover-letter templates per role category |
| `make-resume`, `make-cl`, `critique`, `edit-resume` | deep-tailoring track for a specific job post |
| `setup-extract`, `setup-build-kb` | build the optional knowledge base the deep-tailoring track reads |
| `bdjobs-full-run` | BDJobs: search, save, decide, apply or draft — a 3-script scripted pipeline |
| `li-full-run` | LinkedIn post-search: sweep, review, enrich, stage |
| `linkedin-job-search` | save matching LinkedIn posts (save-only, no drafts or applications) |
| `check-li-saved` | process LinkedIn's own saved-posts list end to end |
| `check-fb-saved` | process Facebook saved items end to end |
| `check-discord-jobs` | process Discord job-channel posts end to end |
| `check-image-batch` | process a batch of pasted job-post screenshots end to end |

## Other agents (Codex, Gemini, Cursor, Kilo, Cline, Roo, Windsurf, Amp, Aider)

The installer targets Claude Code and OpenCode, but the skills are plain
`SKILL.md` folders and the MCP entry is standard stdio JSON — most harnesses
can consume both. `docs/AGENTS.md` lists where each agent keeps skills and MCP
config, with official doc links and copy-paste traps.

## Privacy

Nothing personal lives in this repository: no name, no contact details, no résumé content, no Drive or
Sheet ids, no API tokens. Your config, your generated knowledge base, your run history (`JDs/`,
`output/`), and your real templates all live in your own workspace and config directory, which you
never commit here. `.gitignore` and `tests/test_no_pii.py` (given a private pattern file) both guard
against that by default.

## Never-submit

Every external application is filled and left at the final Submit/Apply button. Every email is a
Gmail draft, never sent. The one documented, user-authorized exception (BDJobs's own portal Apply
button) lives only inside `bdjobs-full-run`'s own rules — nowhere else.

## Troubleshooting

New here? Start at `docs/help/index.md` — module walkthroughs (prerequisites, Google, browser,
searching, PDFs, email/tracker, templates) plus Windows/WSL compatibility notes.
See `docs/EXTERNAL_TOOLS.md` §9, or run `./doctor.sh --mode all` for a specific diagnosis.

## Credits and license

MIT licensed (`LICENSE`). Builds on two upstream MIT projects — see `docs/CREDITS.md`.
