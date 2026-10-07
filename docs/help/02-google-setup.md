# 02 — Google setup (Gmail drafts, Drive, Sheets)

Back to [index](index.md). Command reference: `docs/EXTERNAL_TOOLS.md` §§3.2–3.3, §6.

Every skill talks to Google through one interface, `skills/job-apply-core/scripts/jak_google.py`.
It can use either of two backends, and `doctor.sh` accepts either one:

## Option A — `gog` (primary)

A single Go binary (upstream: `steipete/gogcli` releases) covering Gmail, Drive, Sheets and more.
Windows amd64/arm64 builds ship with every release, alongside Linux and macOS.

```bash
gog auth add you@example.com   # interactive OAuth in your browser, stores a refresh token
gog auth list                  # must succeed — doctor checks this, not just the binary
```

Config: `gog_account` selects which identity to use. If `gog auth list` fails with a keyring error,
see `docs/EXTERNAL_TOOLS.md` §3.2 (re-configure the keyring, or export a short-lived
`GOG_ACCESS_TOKEN` for headless runs — the kit treats a set token as "usable" without touching the
keyring).

To get your own OAuth credentials for either backend, create a Google Cloud project, enable the Gmail,
Drive and Sheets APIs, and download an OAuth client-secret JSON (type: Desktop app). The secret file
itself is never committed and never stored in this repo. The exact click path — project create/select,
the three library links, consent screen in testing mode with yourself as test user, Desktop client,
download, and where the file goes — is [02b-cloud-console](02-cloud-console.md), written so an agent
can drive it in the debug browser for the user.

## Option B — bundled Python backend (fallback)

No extra install: `skills/job-apply-core/scripts/google_setup.py` runs the OAuth flow with the
`google-auth-oauthlib` package from `requirements.txt`, storing one token file per account under
`google_token_dir` (default `~/.config/job-apply-kit/google/`).

```bash
python3 skills/job-apply-core/scripts/google_setup.py --client-secret /path/to/client_secret.json --account you@example.com
python3 skills/job-apply-core/scripts/google_setup.py --auth-url --account you@example.com
# open the URL, approve, copy the code back:
python3 skills/job-apply-core/scripts/google_setup.py --auth-code "PASTED_CODE_OR_URL" --account you@example.com
python3 skills/job-apply-core/scripts/google_setup.py --check --account you@example.com
```

Already have a token from another tool with the same scopes? Import it instead of re-authorizing:
`google_setup.py --import-token /path/to/token.json --account you@example.com`.

## Prove it works (right after auth)

Run the read-only verification and SHOW the output to the user as the
"connection is live" evidence — newest Gmail messages, newest Drive files,
newest spreadsheets:

```bash
python3 skills/job-apply-core/scripts/google_verify.py
```

Exit 0 = all three answered. A FAILED section names its error (wrong account,
missing scope, network) so you know what to fix before touching real data.

Scopes requested: `gmail.readonly`, `gmail.compose` (drafts only — `gmail.send` is never requested),
`drive`, `spreadsheets`. Config key `google_backend: gog` forces A, `python` forces B, `auto`
prefers A and falls back to B.

## Account roles (never conflated)

- `email_google`: signs into the debug browser, authenticates `gog`/the Python backend. Drafts live here.
- `email_header`: printed on resumes, cover letters and portals. May be the same address or a separate one.

## What the kit does with Google

Create Gmail **drafts with attachments** (never send), upload PDFs to your Drive folder and share them
anyone-with-link, create folders, append guarded 15-column tracker rows. Details:
[Email and tracking](06-email-and-tracking.md).
