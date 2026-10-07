#!/usr/bin/env python3
"""Single Google interface for job-apply-kit skills. Two backends, same results.

  gog     the `gog` CLI (user installs it)       -a <account>, or GOG_ACCESS_TOKEN
  python  Google client libraries + token files  (google_setup.py authorizes / imports tokens)

Backend choice: config `google_backend` (auto|gog|python). `auto` = gog when it can read its
keyring (or GOG_ACCESS_TOKEN is set), else python.

Safety rules enforced here:
  * There is NO send function. Drafts are created, never sent. (tests/test_never_submit.py greps for it.)
  * Public ("anyone with the link") sharing only for files whose parent is a configured Drive folder
    (`drive_folder_id` or `drive_templates_folder_id`).
  * Sheet writes use RAW input and a JSON array, never comma/pipe strings, so JD text, phone numbers
    starting with + or text starting with = are stored literally.

CLI (JSON on stdout, errors on stderr, exit 1):
  jak_google.py backend
  jak_google.py accounts                       (python-backend token files found)
  jak_google.py draft --to A --subject S (--body T | --body-file F) [--cc X] [--bcc Y] [--attach P ...]
  jak_google.py drive-upload FILE [--name N] [--parent ID] [--no-share]
  jak_google.py drive-mkdir NAME [--parent ID]
  jak_google.py drive-share-anyone FILE_ID
  jak_google.py sheet-create TITLE
  jak_google.py sheet-get SHEET_ID RANGE
  jak_google.py sheet-append SHEET_ID RANGE --values-json '[[...]]'          (sheet_append.py guards the 15 columns)
  jak_google.py sheet-update SHEET_ID RANGE --values-json '[[...]]'          (sheet_update.py guards keys + statuses)
  jak_google.py gmail-list [--limit 3]                                       (read-only verification)
  jak_google.py drive-list [--limit 3] [--query Q]                           (read-only verification)
"""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import shutil
import subprocess
import sys
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


class GoogleError(RuntimeError):
    pass


# --------------------------------------------------------------------------- config helpers

def _cfg():
    try:
        import jak_config
        return jak_config.load()
    except Exception:  # noqa: BLE001
        return None


def configured_folders() -> set[str]:
    cfg = _cfg()
    if not cfg:
        return set()
    return {v for v in (cfg.get("drive_folder_id"), cfg.get("drive_templates_folder_id")) if v}


def default_account() -> str | None:
    cfg = _cfg()
    return (cfg.get("gog_account") or cfg.get("email_google")) if cfg else None


# --------------------------------------------------------------------------- gog backend

class GogBackend:
    name = "gog"

    def __init__(self, account: str | None = None):
        self.account = account or default_account()
        self.bin = os.environ.get("JAK_GOG_BIN") or shutil.which("gog")
        if not self.bin:
            raise GoogleError("gog not found on PATH")

    def _run(self, args: list[str]):
        cmd = [self.bin, "--no-input", "-j", "--results-only"]
        if self.account and not os.environ.get("GOG_ACCESS_TOKEN"):
            cmd += ["-a", self.account]
        cmd += args
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if p.returncode != 0:
            raise GoogleError((p.stderr or p.stdout).strip()[:500] or f"gog failed: {' '.join(args[:3])}")
        out = p.stdout.strip()
        return json.loads(out) if out else {}

    def usable(self) -> bool:
        if os.environ.get("GOG_ACCESS_TOKEN"):
            return True
        p = subprocess.run([self.bin, "--no-input", "auth", "list"], capture_output=True, text=True, timeout=30)
        return p.returncode == 0 and (not self.account or self.account in p.stdout + p.stderr)

    def draft(self, to, subject, body, attachments, cc="", bcc=""):
        args = ["gmail", "drafts", "create", "--to", to, "--subject", subject, "--body", body]
        if cc:
            args += ["--cc", cc]
        if bcc:
            args += ["--bcc", bcc]
        for a in attachments:
            args += ["--attach", a]
        r = self._run(args)
        return {"draft_id": r.get("draftId") or r.get("id")}

    def drive_upload(self, path, name=None, parent=None):
        args = ["drive", "upload", path]
        if name:
            args += ["--name", name]
        if parent:
            args += ["--parent", parent]
        r = self._run(args)
        return {"id": r["id"], "link": f"https://drive.google.com/file/d/{r['id']}/view"}

    def drive_mkdir(self, name, parent=None):
        args = ["drive", "mkdir", name]
        if parent:
            args += ["--parent", parent]
        r = self._run(args)
        return {"id": r["id"], "link": r.get("webViewLink", "")}

    def drive_parents(self, file_id):
        return self._run(["drive", "get", file_id]).get("parents", [])

    def drive_share_anyone(self, file_id):
        self._run(["drive", "share", file_id, "--to", "anyone", "--role", "reader", "--force"])

    def sheet_create(self, title):
        r = self._run(["sheets", "create", title])
        return {"id": r["spreadsheetId"], "url": r.get("spreadsheetUrl", "")}

    def sheet_get(self, sheet_id, rng):
        r = self._run(["sheets", "get", sheet_id, rng])
        return r.get("values", []) if isinstance(r, dict) else r

    def sheet_append(self, sheet_id, rng, rows):
        r = self._run(["sheets", "append", sheet_id, rng, "--values-json", json.dumps(rows),
                       "--input", "RAW", "--insert", "INSERT_ROWS"])
        return {"range": r.get("updatedRange", "")}

    def sheet_update(self, sheet_id, rng, rows):
        r = self._run(["sheets", "update", sheet_id, rng, "--values-json", json.dumps(rows),
                       "--input", "RAW"])
        return {"range": r.get("updatedRange", rng)}

    def gmail_list(self, limit=3):
        r = self._run(["gmail", "list", "--limit", str(limit)])
        items = []
        if isinstance(r, dict):
            for m in r.get("messages", []) or r.get("threads", []) or r.get("items", []):
                if isinstance(m, dict):
                    items.append({"id": m.get("id", ""),
                                  "subject": m.get("subject", "") or m.get("snippet", "")})
                else:
                    items.append({"id": str(m), "subject": ""})
        return items[:limit]

    def drive_list(self, limit=3, query=""):
        args = ["drive", "ls", "--max", str(limit)]
        if query:
            args += ["--query", query]
        r = self._run(args)
        files = r.get("files", []) if isinstance(r, dict) else (r if isinstance(r, list) else [])
        return [{"id": f.get("id", ""), "name": f.get("name", ""),
                 "mimeType": f.get("mimeType", "")} for f in files[:limit] if isinstance(f, dict)]

    # test/cleanup helpers (the kit itself never deletes)
    def _delete_file(self, file_id):
        self._run(["drive", "delete", file_id, "--permanent", "--force"])


# --------------------------------------------------------------------------- python backend

class PythonBackend:
    name = "python"

    def __init__(self, account: str | None = None):
        import google_auth
        import google_paths
        self.account = account or google_paths.default_account()
        if not google_paths.token_path(self.account).exists():
            raise GoogleError(f"no python-backend token for {self.account} in {google_paths.token_dir()}")
        self._auth = google_auth

    def _svc(self, api, version):
        return self._auth.service(api, version, self.account)

    def usable(self) -> bool:
        return True

    def draft(self, to, subject, body, attachments, cc="", bcc=""):
        msg = MIMEMultipart()
        msg["To"], msg["Subject"] = to, subject
        if cc:
            msg["Cc"] = cc
        if bcc:
            msg["Bcc"] = bcc
        msg.attach(MIMEText(body, "plain", "utf-8"))
        for a in attachments:
            ctype = mimetypes.guess_type(a)[0] or "application/octet-stream"
            part = MIMEApplication(Path(a).read_bytes(), _subtype=ctype.split("/", 1)[1])
            part.add_header("Content-Disposition", "attachment", filename=os.path.basename(a))
            msg.attach(part)
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        d = self._svc("gmail", "v1").users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()
        return {"draft_id": d["id"]}

    def drive_upload(self, path, name=None, parent=None):
        from googleapiclient.http import MediaFileUpload
        meta = {"name": name or os.path.basename(path)}
        if parent:
            meta["parents"] = [parent]
        media = MediaFileUpload(path, mimetype=mimetypes.guess_type(path)[0] or "application/octet-stream")
        f = self._svc("drive", "v3").files().create(body=meta, media_body=media, fields="id").execute()
        return {"id": f["id"], "link": f"https://drive.google.com/file/d/{f['id']}/view"}

    def drive_mkdir(self, name, parent=None):
        meta = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
        if parent:
            meta["parents"] = [parent]
        f = self._svc("drive", "v3").files().create(body=meta, fields="id,webViewLink").execute()
        return {"id": f["id"], "link": f.get("webViewLink", "")}

    def drive_parents(self, file_id):
        return self._svc("drive", "v3").files().get(fileId=file_id, fields="parents").execute().get("parents", [])

    def drive_share_anyone(self, file_id):
        self._svc("drive", "v3").permissions().create(fileId=file_id, body={"type": "anyone", "role": "reader"}).execute()

    def sheet_create(self, title):
        r = self._svc("sheets", "v4").spreadsheets().create(body={"properties": {"title": title}}).execute()
        return {"id": r["spreadsheetId"], "url": r.get("spreadsheetUrl", "")}

    def sheet_get(self, sheet_id, rng):
        return self._svc("sheets", "v4").spreadsheets().values().get(spreadsheetId=sheet_id, range=rng).execute().get("values", [])

    def sheet_append(self, sheet_id, rng, rows):
        r = self._svc("sheets", "v4").spreadsheets().values().append(
            spreadsheetId=sheet_id, range=rng, valueInputOption="RAW", insertDataOption="INSERT_ROWS",
            body={"values": rows}).execute()
        return {"range": r.get("updates", {}).get("updatedRange", "")}

    def sheet_update(self, sheet_id, rng, rows):
        r = self._svc("sheets", "v4").spreadsheets().values().update(
            spreadsheetId=sheet_id, range=rng, valueInputOption="RAW",
            body={"values": rows}).execute()
        return {"range": r.get("updatedRange", rng)}

    def gmail_list(self, limit=3):
        svc = self._svc("gmail", "v1").users().messages()
        ids = [m["id"] for m in svc.list(userId="me", maxResults=limit).execute().get("messages", [])]
        out = []
        for mid in ids[:limit]:
            meta = svc.get(userId="me", id=mid, format="METADATA",
                           metadataHeaders=["Subject", "From"]).execute()
            heads = {h["name"].lower(): h.get("value", "")
                     for h in meta.get("payload", {}).get("headers", [])}
            out.append({"id": mid, "subject": heads.get("subject", ""),
                        "from": heads.get("from", "")})
        return out

    def drive_list(self, limit=3, query=""):
        q = query or "'me' in owners and trashed=false"
        r = self._svc("drive", "v3").files().list(
            q=q, orderBy="createdTime desc", pageSize=limit,
            fields="files(id,name,mimeType,createdTime)").execute()
        return [{"id": f.get("id", ""), "name": f.get("name", ""),
                 "mimeType": f.get("mimeType", "")} for f in r.get("files", [])[:limit]]

    def _delete_file(self, file_id):
        self._svc("drive", "v3").files().delete(fileId=file_id).execute()


# --------------------------------------------------------------------------- selection and API

_backend = None


def backend(name: str | None = None, account: str | None = None):
    """Return the chosen backend instance (cached for the default arguments)."""
    global _backend
    if _backend is not None and name is None and account is None:
        return _backend
    cfg = _cfg()
    want = name or (cfg.get("google_backend") if cfg else None) or "auto"
    errors = []
    candidates = {"gog": ["gog"], "python": ["python"], "auto": ["gog", "python"]}.get(want)
    if candidates is None:
        raise GoogleError(f"google_backend must be auto, gog or python (got {want!r})")
    for c in candidates:
        try:
            b = GogBackend(account) if c == "gog" else PythonBackend(account)
            if b.usable():
                if name is None and account is None:
                    _backend = b
                return b
            errors.append("gog is installed but cannot unlock its keyring (set its keyring password env or GOG_ACCESS_TOKEN)")
        except GoogleError as e:
            errors.append(f"{c}: {e}")
    raise GoogleError("no usable Google backend. " + " | ".join(errors))


def draft(to, subject, body, attachments=(), cc="", bcc="", **kw):
    for a in attachments:
        if not Path(a).is_file():
            raise GoogleError(f"attachment not found: {a}")
    return backend(**kw).draft(to, subject, body, list(attachments), cc, bcc)


def share_anyone(file_id, **kw):
    b = backend(**kw)
    allowed = configured_folders()
    if not allowed:
        raise GoogleError("refusing public share: drive_folder_id is not configured (run sheet_init)")
    if not (set(b.drive_parents(file_id)) & allowed):
        raise GoogleError("refusing public share: file is not inside the configured Drive folder")
    b.drive_share_anyone(file_id)
    return {"id": file_id, "shared": "anyone-reader"}


def drive_upload(path, name=None, parent=None, share=True, **kw):
    if not Path(path).is_file():
        raise GoogleError(f"file not found: {path}")
    cfg = _cfg()
    parent = parent or (cfg.get("drive_folder_id") if cfg else None)
    res = backend(**kw).drive_upload(path, name, parent)
    if share:
        share_anyone(res["id"], **kw)
        res["shared"] = "anyone-reader"
    return res


def drive_mkdir(name, parent=None, **kw):
    return backend(**kw).drive_mkdir(name, parent)


def sheet_create(title, **kw):
    return backend(**kw).sheet_create(title)


def sheet_get(sheet_id, rng, **kw):
    return backend(**kw).sheet_get(sheet_id, rng)


def sheet_append(sheet_id, rng, rows, **kw):
    if not (isinstance(rows, list) and rows and all(isinstance(r, list) for r in rows)):
        raise GoogleError("rows must be a JSON array of arrays")
    rows = [[str(c) if c is not None else "" for c in r] for r in rows]
    return backend(**kw).sheet_append(sheet_id, rng, rows)


def sheet_update(sheet_id, rng, rows, **kw):
    """Overwrite cells in rng (single cells or a block). RAW input, like append."""
    if not (isinstance(rows, list) and rows and all(isinstance(r, list) for r in rows)):
        raise GoogleError("rows must be a JSON array of arrays")
    rows = [[str(c) if c is not None else "" for c in r] for r in rows]
    return backend(**kw).sheet_update(sheet_id, rng, rows)


def gmail_list(limit=3, **kw):
    """Newest Gmail message ids + subjects (read-only, for post-auth verification)."""
    return backend(**kw).gmail_list(limit)


def drive_list(limit=3, query="", **kw):
    """Newest Drive files (id, name, mimeType). Empty query = own files, newest first."""
    return backend(**kw).drive_list(limit, query)


# --------------------------------------------------------------------------- CLI

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--backend", choices=["auto", "gog", "python"])
    ap.add_argument("--account")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("backend")
    sub.add_parser("accounts")
    p = sub.add_parser("draft")
    p.add_argument("--to", required=True)
    p.add_argument("--subject", required=True)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--body")
    g.add_argument("--body-file")
    p.add_argument("--cc", default="")
    p.add_argument("--bcc", default="")
    p.add_argument("--attach", action="append", default=[])
    p = sub.add_parser("drive-upload")
    p.add_argument("file")
    p.add_argument("--name")
    p.add_argument("--parent")
    p.add_argument("--no-share", action="store_true")
    p = sub.add_parser("drive-mkdir")
    p.add_argument("name")
    p.add_argument("--parent")
    p = sub.add_parser("drive-share-anyone")
    p.add_argument("file_id")
    p = sub.add_parser("sheet-create")
    p.add_argument("title")
    p = sub.add_parser("sheet-get")
    p.add_argument("sheet_id")
    p.add_argument("range")
    p = sub.add_parser("sheet-append")
    p.add_argument("sheet_id")
    p.add_argument("range")
    p.add_argument("--values-json", required=True)
    p = sub.add_parser("sheet-update")
    p.add_argument("sheet_id")
    p.add_argument("range")
    p.add_argument("--values-json", required=True)
    p = sub.add_parser("gmail-list")
    p.add_argument("--limit", type=int, default=3)
    p = sub.add_parser("drive-list")
    p.add_argument("--limit", type=int, default=3)
    p.add_argument("--query", default="")
    a = ap.parse_args(argv)
    kw = {k: v for k, v in (("name", a.backend if a.backend and a.backend != "auto" else None), ("account", a.account)) if v}
    try:
        if a.cmd == "backend":
            out = {"backend": backend(**kw).name}
        elif a.cmd == "accounts":
            import google_paths
            out = {"accounts": google_paths.list_accounts(), "default": google_paths.default_account()}
        elif a.cmd == "draft":
            body = a.body if a.body is not None else (sys.stdin.read() if a.body_file == "-" else Path(a.body_file).read_text(encoding="utf-8"))
            out = draft(a.to, a.subject, body, a.attach, a.cc, a.bcc, **kw)
        elif a.cmd == "drive-upload":
            out = drive_upload(a.file, a.name, a.parent, share=not a.no_share, **kw)
        elif a.cmd == "drive-mkdir":
            out = drive_mkdir(a.name, a.parent, **kw)
        elif a.cmd == "drive-share-anyone":
            out = share_anyone(a.file_id, **kw)
        elif a.cmd == "sheet-create":
            out = sheet_create(a.title, **kw)
        elif a.cmd == "sheet-get":
            out = sheet_get(a.sheet_id, a.range, **kw)
        elif a.cmd == "sheet-update":
            out = sheet_update(a.sheet_id, a.range, json.loads(a.values_json), **kw)
        elif a.cmd == "gmail-list":
            out = {"messages": gmail_list(a.limit, **kw)}
        elif a.cmd == "drive-list":
            out = {"files": drive_list(a.limit, a.query, **kw)}
        else:
            out = sheet_append(a.sheet_id, a.range, json.loads(a.values_json), **kw)
    except (GoogleError, json.JSONDecodeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
