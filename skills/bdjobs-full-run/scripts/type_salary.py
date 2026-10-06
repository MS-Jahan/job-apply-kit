#!/usr/bin/env python3
"""Type salary using trusted CDP Input events (Angular-safe). Usage: type_salary.py <tabid> <salary>"""
import json, os, subprocess, sys, time

TAB, SAL = sys.argv[1], sys.argv[2]

def cdp_raw(js):
    r = subprocess.run(["python3", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "job-apply-core", "scripts", "cdp.py"), "eval", TAB, js],
                       capture_output=True, text=True, timeout=60)
    return r.stdout.strip().strip('"')

JS = r'''(() => {
  const inp = [...document.querySelectorAll('input')].find(i => i.placeholder === 'e.g. 50000');
  if (!inp) return 'NO_INPUT';
  inp.focus();
  const r = inp.getBoundingClientRect();
  return JSON.stringify({x: r.x + r.width / 2, y: r.y + r.height / 2});
})()'''

out = cdp_raw(JS)
print("focus:", out)
if out == "NO_INPUT":
    sys.exit(1)
try:
    pos = json.loads(out)
except Exception:
    pos = {"x": 0, "y": 0}

# Also clear the field first via triple-click select-all + delete handled below
clear_js = r'''(() => {
  const inp = [...document.querySelectorAll('input')].find(i => i.placeholder === 'e.g. 50000');
  inp.focus();
  inp.select();
  return 'SELECTED:' + (inp.value || 'empty');
})()'''
print(cdp_raw(clear_js))

import websocket
ws = websocket.create_connection(f"ws://127.0.0.1:{os.environ.get('JAK_CDP_PORT', '9222')}/devtools/page/{TAB}", timeout=30, suppress_origin=True)
mid = 0

def cmd(method, **params):
    global mid
    mid += 1
    ws.send(json.dumps({"id": mid, "method": method, "params": params}))
    deadline = time.time() + 15
    while time.time() < deadline:
        msg = json.loads(ws.recv())
        if msg.get("id") == mid:
            return msg.get("result", {})

# Select all then delete to clear
cmd("Input.dispatchKeyEvent", type="rawKeyDown", key="a", code="KeyA", windowsVirtualKeyCode=65, modifiers=2)
cmd("Input.dispatchKeyEvent", type="keyUp", key="a", code="KeyA", windowsVirtualKeyCode=65, modifiers=2)
cmd("Input.dispatchKeyEvent", type="rawKeyDown", key="Delete", code="Delete", windowsVirtualKeyCode=46)
cmd("Input.dispatchKeyEvent", type="keyUp", key="Delete", code="Delete", windowsVirtualKeyCode=46)
time.sleep(0.5)

for ch in SAL:
    kd = {"type": "keyDown", "text": ch, "unmodifiedText": ch, "key": ch}
    if ch.isdigit():
        kd["code"] = f"Digit{ch}"
        kd["windowsVirtualKeyCode"] = 48 + int(ch)
    cmd("Input.dispatchKeyEvent", **kd)
    cmd("Input.dispatchKeyEvent", type="keyUp", key=ch,
        code=kd.get("code", ""), windowsVirtualKeyCode=kd.get("windowsVirtualKeyCode", 0))
    time.sleep(0.08)

# blur: click elsewhere (page background)
cmd("Input.dispatchMouseEvent", type="mousePressed", x=10, y=400, button="left", clickCount=1)
cmd("Input.dispatchMouseEvent", type="mouseReleased", x=10, y=400, button="left", clickCount=1)
time.sleep(2)

val = cdp_raw(r'''(() => { const i=[...document.querySelectorAll('input')].find(i=>i.placeholder==='e.g. 50000'); const b=[...document.querySelectorAll('button[type=submit]')][0]; return JSON.stringify({val:i.value, disabled:b?b.disabled:'NOBTN'}); })()''')
print("after:", val)
