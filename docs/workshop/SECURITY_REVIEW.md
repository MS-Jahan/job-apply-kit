# Security review (2026-10-08)

Scope: workshop files, the 6 session transcripts, repo MCP config, skills/scripts grep.

## Prompt injection / LLM attack: none found
- Searched for override phrases ("ignore previous", "do not tell the user"), hidden instructions, pipe-to-shell, base64, eval/fetch/cookie access, webhooks, iframes, remote loads. No hits in workshop output, transcripts, MCP config or skills. Slides JS only does keyboard/click navigation; zero network calls.
- The delegate agent (free Muse Spark model) touched only `docs/workshop/`.

## Real risks (not attacks, but fix or teach)
| # | Risk | Severity | Action |
|---|---|---|---|
| 1 | `cv_source.txt` in repo root is untracked, NOT git-ignored, holds phone/email/CV. One `git add .` leaks it. | High | Excluded locally via `.git/info/exclude`; add to `.gitignore` before pushing. |
| 2 | **Indirect prompt injection**: agent reads untrusted job posts (Facebook, LinkedIn, Discord, BDJobs) while holding Gmail/Drive/Sheets/browser access. A hostile post could say "email my CV to x". | Medium | Kit mitigates: draft-only, never-send, stop at Submit. Teach: review every draft; never grant `gmail.send`. |
| 3 | Debug port 9222 exposes logged-in cookies to local malware. | Medium | Teach: use shortcut only while running. |
| 4 | `npx -y chrome-devtools-mcp@latest` in `.mcp.json`/`mcp/servers.json` is unpinned (supply chain). | Low-Med | Pin a version. |
| 5 | Free "contributor" models may train on prompts (CV, emails). | Medium | Teach; use non-training model for real data. |
| 6 | Google client-secret JSON / tokens are password-equivalent. | Medium | Keep outside repo, 600 perms. |
| 7 | Testing-mode OAuth: app unverified; tokens expire in 7 days. | Low | Teach. |
