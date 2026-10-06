#!/usr/bin/env python3
"""Set a file on an <input type=file> inside a cross-origin Google Picker iframe (or any page).

Usage:
  python3 picker_upload.py <target-needle> <abs-file> [--css SELECTOR_HINT]

Google Forms / Drive's "Add file" opens the Picker in a cross-origin iframe, so there is no native
file chooser. This walks the PIERCED DOM (children + shadowRoots + contentDocument) of the page
matched by <target-needle> (target id, URL or title substring), picks the file input (preferring
one whose accept= mentions pdf/document), and calls DOM.setFileInputFiles on the SAME connection
(nodeIds are per connection, so walk and set must share one).

Verify afterwards by reading the form text: the file name must appear and no progressbar remains.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Conn, find  # noqa: E402


def _attrs(node: dict) -> dict:
    raw = node.get("attributes", []) or []
    it = iter(raw)
    return dict(zip(it, it))


def walk(node, out: list) -> None:
    if not isinstance(node, dict):
        return
    if node.get("nodeType") == 1 and str(node.get("nodeName", "")).upper() == "INPUT":
        a = _attrs(node)
        if "file" in a.get("type", "").lower():
            out.append((node.get("nodeId"), a))
    for key in ("children", "shadowRoots"):
        for ch in node.get(key) or []:
            walk(ch, out)
    cd = node.get("contentDocument")
    if isinstance(cd, dict):
        walk(cd, out)
    elif isinstance(cd, list):
        for ch in cd:
            walk(ch, out)


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if len(a) < 2 or a[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if a and a[0] in ("-h", "--help") else 1
    needle, path = a[0], os.path.abspath(a[1])
    if not os.path.isfile(path):
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 1
    c = Conn(find(needle))
    c.cmd("Page.enable")
    c.cmd("DOM.enable")
    root = c.cmd("DOM.getDocument", depth=-1, pierce=True)["root"]
    inputs: list = []
    walk(root, inputs)
    if not inputs:
        print("ERROR: no file input found in the pierced DOM", file=sys.stderr)
        return 1
    pick = next((nid for nid, at in inputs if any(w in at.get("accept", "").lower() for w in ("pdf", "document"))), inputs[0][0])
    c.cmd("DOM.setFileInputFiles", files=[path], nodeId=pick)
    print(json.dumps({"picked_nodeId": pick, "candidates": len(inputs), "file": path}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
