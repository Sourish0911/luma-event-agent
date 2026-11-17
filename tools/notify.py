#!/usr/bin/env python3
"""macOS-native notifications and feedback prompts (no email, no passwords).
  notify.py send "<title>" "<message>"      banner notification
  notify.py ask <event_id> "<title>"        popup: rating 1-5 then one-line comment -> prints JSON, or [] if ignored
"""
import sys, subprocess, json

def osa(script):
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return r.stdout.strip()

def q(s): return s.replace("\\", "\\\\").replace('"', '\\"')

def send(title, msg):
    osa(f'display notification "{q(msg)}" with title "{q(title)}"')

def ask(eid, title):
    r = osa(f'choose from list {{"5","4","3","2","1"}} with title "Luma feedback" with prompt "How was: {q(title)}? (5 = great)" default items {{"4"}}')
    if r in ("", "false"):
        print("[]"); return
    c = osa(f'text returned of (display dialog "One line of feedback (optional):" default answer "" with title "{q(title)}" giving up after 120)')
    print(json.dumps([{"event": eid, "rating": int(r), "comment": c[:500]}]))

if __name__ == "__main__":
    a = sys.argv[1:]
    {"send": lambda: send(a[1], a[2]), "ask": lambda: ask(a[1], a[2])}[a[0]]()
