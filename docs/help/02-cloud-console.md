# 02b — Google Cloud Console: project, APIs, OAuth credentials

Back to [index](index.md). Sequel to [Google setup](02-google-setup.md): that page
says *what* the kit needs (an OAuth client secret); this page is *exactly where
to click* to make one. An agent with the debug browser can drive the whole flow
for the user — the click-by-click script is at the bottom.

## What you are making

One Google Cloud **project** (a free container for API quotas), three **enabled
APIs** (Gmail, Drive, Sheets), and one **OAuth client ID of type Desktop app**
whose downloaded JSON the kit stores locally. Nothing is hosted, nothing is
published, no billing is involved. Minimum required: the Gmail, Drive and
Sheets APIs — the kit drafts Gmail messages, uploads to Drive, and tracks in
Sheets.

## Step 1 — sign in and pick a project

1. Open https://console.cloud.google.com/ and sign in with the Google account
   the kit will use (`email_google` in the config).
2. If a project already exists for this: click the project name in the top bar
   (or open https://console.cloud.google.com/projectselector) and select it —
   skip to step 2.
3. New project: open https://console.cloud.google.com/projectcreate,
   name it `job-apply-kit` (the ID underneath auto-fills; leave it), no
   organization needed, click **Create**. Wait for the bell notification, then
   select the new project in the top bar.

## Step 2 — enable the three APIs

For each of these, open the link with the right project selected in the top
bar and click **Enable** (if it says **Manage** instead, it is already on):

| API | Library link |
|---|---|
| Gmail API | https://console.cloud.google.com/apis/library/gmail.googleapis.com |
| Google Drive API | https://console.cloud.google.com/apis/library/drive.googleapis.com |
| Google Sheets API | https://console.cloud.google.com/apis/library/sheets.googleapis.com |

## Step 3 — OAuth consent screen (External, testing)

Open https://console.cloud.google.com/apis/credentials/consent:

1. **User type:** External → **Create**. (Internal is only for Workspace
   organizations; External is correct for a personal Gmail.)
2. **App information:** app name `job-apply-kit`, user support email = your own
   address, developer contact = your own address. **Save and continue.**
3. **Scopes:** click **Add or remove scopes** and tick the four the kit uses:
   `.../auth/gmail.readonly`, `.../auth/gmail.compose`,
   `.../auth/drive`, `.../auth/spreadsheets`. (`gmail.send` is deliberately
   absent — the kit can only draft, never send.) **Save and continue.**
4. **Test users:** click **Add users**, add your own Gmail address, **Save**.
   Only listed addresses can authorize while the app is in testing mode.
5. Back on the consent overview you should see Publishing status **Testing**.

Two honest caveats, read before continuing:

- Testing-mode refresh tokens **expire after 7 days without use** — when auth
  goes stale, re-run the `--auth-code` step of [Google setup](02-google-setup.md).
  (Daily kit use keeps it alive.)
- Moving to Production needs Google verification for these restricted scopes
  (privacy policy, video, weeks of review) — out of scope for personal use.
  Stay in Testing with yourself as test user.

## Step 4 — create the OAuth client and download the secret

1. Open https://console.cloud.google.com/apis/credentials.
2. **Create Credentials → OAuth client ID.**
3. Application type: **Desktop app**, name `job-apply-kit-desktop`, **Create**.
4. Click **Download JSON** (the file is named like
   `client_secret_<id>.apps.googleusercontent.com.json`).

## Step 5 — store it where the kit looks

The secret lives OUTSIDE the repo, with the tokens: config `google_token_dir`,
else `~/.config/job-apply-kit/google/`, as `google_client_secret.json`
(600 permissions; never commit it — it is a password-equivalent). Then:

```bash
python3 skills/job-apply-core/scripts/google_setup.py --client-secret /path/to/downloaded.json --account you@gmail.com
python3 skills/job-apply-core/scripts/google_setup.py --auth-url --account you@gmail.com
# open the URL, approve as your test user, copy the code back:
python3 skills/job-apply-core/scripts/google_setup.py --auth-code "PASTED_CODE_OR_URL" --account you@gmail.com
python3 skills/job-apply-core/scripts/google_setup.py --check --account you@gmail.com
```

Already have a token from another tool with the same scopes? Skip all of the
above: `google_setup.py --import-token /path/to/token.json --account you@gmail.com`.

For the `gog` backend, `gog auth add you@gmail.com` uses its own bundled OAuth
client — check `gog auth add --help` for flags if you want it to use THIS
project's client instead.

## Agent runbook: driving this for the user

Open each console URL above in a NEW debug-browser tab (`agent-browser tab new`
then `open`; the user is signed in as Role A). Read each page with `snapshot`
before clicking — console markup shifts, so prefer snapshot refs over recorded
selectors. The consent-screen **Test users** step and the final **Download
JSON** need the user watching (they confirm the address, they see the file
land in Downloads). After download: move the file into the token dir yourself,
`--client-secret` it, and continue the OAuth dance from
[Google setup](02-google-setup.md). Never paste the secret's contents into
chat, logs or the repo.
