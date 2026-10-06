#!/usr/bin/env python3
"""Minimal raw-CDP driver (last-resort browser tool; agent-browser is the default).

Talks to the debug browser at 127.0.0.1:<port>. Port: $JAK_CDP_PORT, else config `cdp_port`, else 9222.

Usage:
  cdp.py list
  cdp.py newtab <url>
  cdp.py close <targetId>
  cdp.py nav <targetId> <url> [--wait N]
  cdp.py eval <targetId> <js-file>      # result printed as JSON
  cdp.py text <targetId> [--max N]      # document.body.innerText
  cdp.py shot <targetId> <outfile.png>
  cdp.py upload <targetId> <css> <path> [<path>...]   # set existing file input(s)
  cdp.py setfile <targetId> <css> <path>   # click an upload control, intercept
                                           # the OS chooser, feed the file in
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

import websocket

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _port():
    if os.environ.get("JAK_CDP_PORT"):
        return int(os.environ["JAK_CDP_PORT"])
    try:
        import jak_config
        return jak_config.load().int("cdp_port") or 9222
    except Exception:  # noqa: BLE001
        return 9222


PORT = _port()
DEV = f"http://127.0.0.1:{PORT}"

def http(path, method="GET"):
    req = urllib.request.Request(DEV + path, method=method)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())

def sanitize(o):
    """Replace lone surrogates (e.g. split emoji in page text) so stdout stays valid UTF-8."""
    if isinstance(o, str):
        return o.encode("utf-8", "replace").decode("utf-8")
    if isinstance(o, list):
        return [sanitize(x) for x in o]
    if isinstance(o, dict):
        return {k: sanitize(v) for k, v in o.items()}
    return o


def targets():
    return [t for t in http("/json/list") if t.get("type") == "page"]

class Conn:
    def __init__(self, tid):
        self.ws = websocket.create_connection(
            f"ws://127.0.0.1:{PORT}/devtools/page/{tid}", timeout=30, suppress_origin=True)
        self.mid = 0
        self.events = []
    def cmd(self, method, **params):
        self.mid += 1
        self.ws.send(json.dumps({"id": self.mid, "method": method, "params": params}))
        deadline = time.time() + 30
        while time.time() < deadline:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == self.mid:
                if "error" in msg:
                    raise RuntimeError(msg["error"])
                return msg.get("result", {})
            if msg.get("method"):
                # Keep async events: a response can arrive after the event we
                # are waiting for, and dropping them loses it forever.
                self.events.append(msg)
        raise TimeoutError(method)

    def take_event(self, name, timeout=25):
        """Return the first buffered/incoming event with this method name."""
        deadline = time.time() + timeout
        while True:
            for i, ev in enumerate(self.events):
                if ev.get("method") == name:
                    return self.events.pop(i)
            if time.time() > deadline:
                return None
            try:
                msg = json.loads(self.ws.recv())
            except Exception:
                return None
            if msg.get("method"):
                self.events.append(msg)
    def eval_js(self, expr, await_promise=False):
        r = self.cmd("Runtime.evaluate", expression=expr, returnByValue=True,
                     awaitPromise=await_promise, timeout=25000)
        if r.get("exceptionDetails"):
            raise RuntimeError(json.dumps(r["exceptionDetails"])[:800])
        v = r.get("result", {})
        return v.get("value")

def find(needle):
    for t in targets():
        if needle in t["id"] or needle in t["url"] or needle.lower() in t["title"].lower():
            return t["id"]
    raise SystemExit(f"no target matching {needle}")

def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); return
    op = a[0]
    if op == "list":
        for t in targets():
            print(t["id"], t["url"][:90], "|", t["title"][:50])
    elif op == "newtab":
        # PUT /json/new is required since Chrome 111
        url = a[1]
        req = urllib.request.Request(DEV + "/json/new?" + urllib.parse.urlencode({"url": url}), method="PUT")
        t = json.loads(urllib.request.urlopen(req, timeout=15).read().decode())
        print(t["id"])
    elif op == "close":
        print(http(f"/json/close/{a[1]}"))
    elif op == "nav":
        c = Conn(find(a[1])); c.cmd("Page.enable"); c.cmd("Page.navigate", url=a[2])
        wait = int(a[a.index("--wait")+1]) if "--wait" in a else 4
        time.sleep(wait)
        print("navigated", a[2])
    elif op == "eval":
        c = Conn(find(a[1]))
        js = a[-1]
        if js.endswith(".js"):
            js = open(js).read()
        print(json.dumps(sanitize(c.eval_js(js, await_promise="--await" in a)),
                         ensure_ascii=False))
    elif op == "text":
        c = Conn(find(a[1]))
        mx = int(a[a.index("--max")+1]) if "--max" in a else 20000
        v = c.eval_js("document.body ? document.body.innerText : ''")
        print(sanitize(v)[:mx])
    elif op == "shot":
        c = Conn(find(a[1]))
        import base64
        r = c.cmd("Page.captureScreenshot", format="png")
        open(a[2], "wb").write(base64.b64decode(r["data"]))
        print("saved", a[2])
    elif op == "upload":
        # Set <input type=file> contents (the chrome-devtools MCP upload_file
        # equivalent). Files must be absolute paths on this host.
        import os
        c = Conn(find(a[1]))
        css, files = a[2], [os.path.abspath(p) for p in a[3:]]
        c.cmd("DOM.enable")
        root = c.cmd("DOM.getDocument", depth=-1)["root"]["nodeId"]
        node = c.cmd("DOM.querySelector", nodeId=root, selector=css)
        nid = node.get("nodeId")
        if not nid:
            raise SystemExit(f"no element matches {css}")
        c.cmd("DOM.setFileInputFiles", files=files, nodeId=nid)
        print(json.dumps({"uploaded": files, "nodeId": nid}))
    elif op == "setfile":
        # Google Forms creates its <input type=file> only while the OS chooser
        # is open, so: enable Page, intercept the chooser, click the control,
        # then feed the file using the backendNodeId from the event.
        import os
        c = Conn(find(a[1]))
        css, path = a[2], os.path.abspath(a[3])
        c.cmd("Page.enable")
        c.cmd("DOM.enable")
        c.cmd("Page.setInterceptFileChooserDialog", enabled=True)
        # A scripted .click() is not a trusted gesture, so dispatch real mouse
        # events at the element centre instead. The control must be inside the
        # viewport or the dispatched coordinates miss it entirely.
        c.eval_js("document.querySelector(%s)"
                  ".scrollIntoView({block:'center'}); 'scrolled'" % json.dumps(css))
        time.sleep(1.5)
        box = c.eval_js(
            "(function(){var e=document.querySelector(%s);"
            "var r=e.getBoundingClientRect();"
            "return JSON.stringify({x:r.left+r.width/2,y:r.top+r.height/2});})()"
            % json.dumps(css))
        pt = json.loads(box)
        for kind in ("mousePressed", "mouseReleased"):
            c.cmd("Input.dispatchMouseEvent", type=kind, x=pt["x"], y=pt["y"],
                  button="left", clickCount=1)
        ev = c.take_event("Page.fileChooserOpened", timeout=20)
        if not ev:
            raise SystemExit("file chooser never opened")
        backend = ev["params"].get("backendNodeId")
        c.cmd("DOM.setFileInputFiles", files=[path], backendNodeId=backend)
        c.cmd("Page.setInterceptFileChooserDialog", enabled=False)
        print(json.dumps({"uploaded": path, "backendNodeId": backend}))
    else:
        print(__doc__)

if __name__ == "__main__":
    main()
