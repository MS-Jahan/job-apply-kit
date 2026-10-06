#!/usr/bin/env python3
"""General Google Workspace CLI for agents (python backend). JSON on stdout.

Ported in spirit from the Hermes google-workspace tool, rebuilt on google_auth.py. Differences:
  * NO mail send or reply. Mail is read, searched, labelled, and drafted (never sent).
  * Public sharing goes through jak_google.share_anyone (configured Drive folder only).
  * Sheet writes are RAW.
Account: --account EMAIL, else $JAK_GOOGLE_ACCOUNT, else config email_google.

  gmail    search QUERY [--max N] | get ID | labels | modify ID [--add L ...] [--remove L ...] | draft ... (see jak_google.py)
  calendar list [--from ISO] [--to ISO] [--calendar ID] | create --summary S --start ISO --end ISO [--location L] [--description D] [--attendees a,b] | delete EVENT_ID
  drive    search QUERY [--max N] [--raw] | get ID | upload FILE [--name N] [--parent ID] | download ID [--output P] [--export-mime M]
           | create-folder NAME [--parent ID] | share ID --email E [--role reader|writer] | delete ID [--permanent]
  contacts list [--max N]
  sheets   get ID RANGE | update ID RANGE --values-json J | append ID RANGE --values-json J | create TITLE
  docs     get ID | create TITLE [--body T] | append ID --text T
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import google_auth  # noqa: E402


def out(obj) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def _iso(v: str) -> str:
    return v if ("+" in v[10:] or v.endswith("Z") or "-" in v[10:]) else v + "Z"


def _hdr(msg: dict) -> dict:
    return {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}


def _body(payload: dict) -> str:
    import base64
    data = payload.get("body", {}).get("data")
    if data and payload.get("mimeType", "").startswith("text/"):
        return base64.urlsafe_b64decode(data).decode("utf-8", "replace")
    for part in payload.get("parts", []) or []:
        t = _body(part)
        if t:
            return t
    return ""


def run(a) -> None:
    acct = a.account
    svc = lambda api, ver: google_auth.service(api, ver, acct)  # noqa: E731
    s, c = a.service, a.action
    if s == "gmail":
        g = svc("gmail", "v1")
        if c == "search":
            ids = g.users().messages().list(userId="me", q=a.query, maxResults=a.max).execute().get("messages", [])
            res = []
            for m in ids:
                full = g.users().messages().get(userId="me", id=m["id"], format="metadata",
                                                metadataHeaders=["From", "To", "Subject", "Date"]).execute()
                h = _hdr(full)
                res.append({"id": m["id"], "threadId": m["threadId"], "from": h.get("from"), "subject": h.get("subject"),
                            "date": h.get("date"), "snippet": full.get("snippet"), "labels": full.get("labelIds", [])})
            out(res)
        elif c == "get":
            m = g.users().messages().get(userId="me", id=a.id, format="full").execute()
            h = _hdr(m)
            out({"id": m["id"], "from": h.get("from"), "to": h.get("to"), "subject": h.get("subject"),
                 "date": h.get("date"), "labels": m.get("labelIds", []), "body": _body(m["payload"])})
        elif c == "labels":
            out(g.users().labels().list(userId="me").execute().get("labels", []))
        elif c == "modify":
            out(g.users().messages().modify(userId="me", id=a.id, body={"addLabelIds": a.add, "removeLabelIds": a.remove}).execute())
    elif s == "calendar":
        cal = svc("calendar", "v3")
        if c == "list":
            now = datetime.now(timezone.utc)
            start = _iso(a.frm) if a.frm else now.isoformat()
            end = _iso(a.to) if a.to else (now + timedelta(days=7)).isoformat()
            ev = cal.events().list(calendarId=a.calendar, timeMin=start, timeMax=end, singleEvents=True, orderBy="startTime").execute()
            out([{"id": e["id"], "summary": e.get("summary"), "start": e["start"], "end": e["end"], "location": e.get("location")}
                 for e in ev.get("items", [])])
        elif c == "create":
            body = {"summary": a.summary, "start": {"dateTime": _iso(a.start)}, "end": {"dateTime": _iso(a.end)}}
            if a.location:
                body["location"] = a.location
            if a.description:
                body["description"] = a.description
            if a.attendees:
                body["attendees"] = [{"email": x.strip()} for x in a.attendees.split(",") if x.strip()]
            out(cal.events().insert(calendarId=a.calendar, body=body).execute())
        elif c == "delete":
            cal.events().delete(calendarId=a.calendar, eventId=a.event_id).execute()
            out({"deleted": a.event_id})
    elif s == "drive":
        d = svc("drive", "v3")
        if c == "search":
            q = a.query if a.raw else f"fullText contains '{a.query}' and trashed=false"
            out(d.files().list(q=q, pageSize=a.max, fields="files(id,name,mimeType,webViewLink,modifiedTime,parents)").execute().get("files", []))
        elif c == "get":
            out(d.files().get(fileId=a.id, fields="id,name,mimeType,webViewLink,parents,modifiedTime,size").execute())
        elif c == "upload":
            import mimetypes
            from googleapiclient.http import MediaFileUpload
            meta = {"name": a.name or Path(a.file).name}
            if a.parent:
                meta["parents"] = [a.parent]
            media = MediaFileUpload(a.file, mimetype=mimetypes.guess_type(a.file)[0] or "application/octet-stream")
            out(d.files().create(body=meta, media_body=media, fields="id,name,webViewLink").execute())
        elif c == "download":
            import io
            from googleapiclient.http import MediaIoBaseDownload
            meta = d.files().get(fileId=a.id, fields="name,mimeType").execute()
            req = d.files().export_media(fileId=a.id, mimeType=a.export_mime) if a.export_mime else d.files().get_media(fileId=a.id)
            buf = io.BytesIO()
            dl = MediaIoBaseDownload(buf, req)
            done = False
            while not done:
                _, done = dl.next_chunk()
            target = Path(a.output or meta["name"])
            target.write_bytes(buf.getvalue())
            out({"saved": str(target), "bytes": len(buf.getvalue())})
        elif c == "create-folder":
            meta = {"name": a.name, "mimeType": "application/vnd.google-apps.folder"}
            if a.parent:
                meta["parents"] = [a.parent]
            out(d.files().create(body=meta, fields="id,name,webViewLink").execute())
        elif c == "share":
            out(d.permissions().create(fileId=a.id, body={"type": "user", "role": a.role, "emailAddress": a.email}, sendNotificationEmail=False).execute())
        elif c == "delete":
            if a.permanent:
                d.files().delete(fileId=a.id).execute()
            else:
                d.files().update(fileId=a.id, body={"trashed": True}).execute()
            out({"deleted": a.id, "permanent": a.permanent})
    elif s == "contacts":
        p = svc("people", "v1")
        r = p.people().connections().list(resourceName="people/me", pageSize=a.max, personFields="names,emailAddresses,phoneNumbers").execute()
        out([{"name": (x.get("names") or [{}])[0].get("displayName"), "emails": [e["value"] for e in x.get("emailAddresses", [])],
              "phones": [t["value"] for t in x.get("phoneNumbers", [])]} for x in r.get("connections", [])])
    elif s == "sheets":
        sh = svc("sheets", "v4").spreadsheets()
        if c == "get":
            out(sh.values().get(spreadsheetId=a.id, range=a.range).execute().get("values", []))
        elif c == "update":
            out(sh.values().update(spreadsheetId=a.id, range=a.range, valueInputOption="RAW", body={"values": json.loads(a.values_json)}).execute())
        elif c == "append":
            out(sh.values().append(spreadsheetId=a.id, range=a.range, valueInputOption="RAW", insertDataOption="INSERT_ROWS",
                                   body={"values": json.loads(a.values_json)}).execute())
        elif c == "create":
            r = sh.create(body={"properties": {"title": a.title}}).execute()
            out({"id": r["spreadsheetId"], "url": r.get("spreadsheetUrl")})
    elif s == "docs":
        dc = svc("docs", "v1").documents()
        if c == "get":
            doc = dc.get(documentId=a.id).execute()
            text = "".join(e.get("textRun", {}).get("content", "") for b in doc.get("body", {}).get("content", [])
                           for e in b.get("paragraph", {}).get("elements", []))
            out({"id": a.id, "title": doc.get("title"), "text": text})
        elif c == "create":
            doc = dc.create(body={"title": a.title}).execute()
            if a.body:
                dc.batchUpdate(documentId=doc["documentId"], body={"requests": [{"insertText": {"location": {"index": 1}, "text": a.body}}]}).execute()
            out({"id": doc["documentId"], "title": a.title})
        elif c == "append":
            doc = dc.get(documentId=a.id).execute()
            end = doc["body"]["content"][-1]["endIndex"] - 1
            dc.batchUpdate(documentId=a.id, body={"requests": [{"insertText": {"location": {"index": end}, "text": a.text}}]}).execute()
            out({"appended": len(a.text)})


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--account")
    sv = ap.add_subparsers(dest="service", required=True)

    def grp(name):
        return sv.add_parser(name).add_subparsers(dest="action", required=True)

    g = grp("gmail")
    p = g.add_parser("search"); p.add_argument("query"); p.add_argument("--max", type=int, default=10)
    p = g.add_parser("get"); p.add_argument("id")
    g.add_parser("labels")
    p = g.add_parser("modify"); p.add_argument("id"); p.add_argument("--add", nargs="*", default=[]); p.add_argument("--remove", nargs="*", default=[])
    cal = grp("calendar")
    p = cal.add_parser("list"); p.add_argument("--from", dest="frm"); p.add_argument("--to"); p.add_argument("--calendar", default="primary")
    p = cal.add_parser("create"); [p.add_argument(f"--{k}") for k in ("summary", "start", "end", "location", "description", "attendees")]; p.add_argument("--calendar", default="primary")
    p = cal.add_parser("delete"); p.add_argument("event_id"); p.add_argument("--calendar", default="primary")
    d = grp("drive")
    p = d.add_parser("search"); p.add_argument("query"); p.add_argument("--max", type=int, default=10); p.add_argument("--raw", action="store_true")
    p = d.add_parser("get"); p.add_argument("id")
    p = d.add_parser("upload"); p.add_argument("file"); p.add_argument("--name"); p.add_argument("--parent")
    p = d.add_parser("download"); p.add_argument("id"); p.add_argument("--output"); p.add_argument("--export-mime")
    p = d.add_parser("create-folder"); p.add_argument("name"); p.add_argument("--parent")
    p = d.add_parser("share"); p.add_argument("id"); p.add_argument("--email", required=True); p.add_argument("--role", default="reader", choices=["reader", "writer"])
    p = d.add_parser("delete"); p.add_argument("id"); p.add_argument("--permanent", action="store_true")
    p = grp("contacts").add_parser("list"); p.add_argument("--max", type=int, default=20)
    sh = grp("sheets")
    p = sh.add_parser("get"); p.add_argument("id"); p.add_argument("range")
    for n in ("update", "append"):
        p = sh.add_parser(n); p.add_argument("id"); p.add_argument("range"); p.add_argument("--values-json", required=True)
    p = sh.add_parser("create"); p.add_argument("title")
    dc = grp("docs")
    p = dc.add_parser("get"); p.add_argument("id")
    p = dc.add_parser("create"); p.add_argument("title"); p.add_argument("--body")
    p = dc.add_parser("append"); p.add_argument("id"); p.add_argument("--text", required=True)
    return ap


def main(argv=None) -> int:
    a = parser().parse_args(argv)
    try:
        run(a)
    except google_auth.AuthError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: {type(e).__name__}: {str(e)[:400]}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
