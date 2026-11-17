#!/usr/bin/env python3
"""Credential watchdog. Sends a macOS notification (max 1/day per item) saying where to renew.
Checks: GitHub token, Luma + in the agent Brave profile. Claude failures are reported by run.sh.
  healthcheck.py            run all checks
  healthcheck.py fail <key> "<msg>"   raise an alert from another script
"""
import sys, os, json, re, subprocess, shutil, sqlite3, tempfile, time, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
STATE = os.path.join(ROOT, "logs", "alerts.json"); WARN_DAYS = 7
sys.path.insert(0, HERE); import notify

def alert(key, msg):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    s = json.load(open(STATE)) if os.path.exists(STATE) else {}
    today = str(datetime.date.today())
    if s.get(key) == today: return
    s[key] = today; json.dump(s, open(STATE, "w"))
    notify.send("Luma agent: action needed", msg); print("ALERT", key, msg)

def github():
    r = subprocess.run(["gh", "api", "-i", "user"], capture_output=True, text=True)
    if not r.stdout.startswith("HTTP/2.0 200") and "200 OK" not in r.stdout[:40]:
        return alert("github", "GitHub login failed. Run: gh auth login -h github.com")
    m = re.search(r"(?i)github-authentication-token-expiration: (.+)", r.stdout)
    if m:
        d = datetime.datetime.strptime(m[1].strip()[:19], "%Y-%m-%d %H:%M:%S")
        left = (d - datetime.datetime.utcnow()).days
        if left < WARN_DAYS:
            alert("github", f"GitHub token expires in {left} days. Renew at github.com/settings/tokens then run: gh auth login")

def cookies(domain):
    for p in ("Default/Network/Cookies", "Default/Cookies"):
        f = os.path.expanduser(f"~/.luma-agent/brave-profile/{p}")
        if os.path.exists(f): break
    else: return None
    t = os.path.join(tempfile.mkdtemp(), "c"); shutil.copy(f, t)
    rows = sqlite3.connect(t).execute(
        "select expires_utc, has_expires from cookies where host_key like ?", (f"%{domain}",)).fetchall()
    return rows

def session(key, domain, label, url, how):
    rows = cookies(domain)
    if not rows: return alert(key, f"{label} is not logged in in the agent Brave profile. {how}")
    now = int(time.time()) + 11644473600  # unix -> webkit epoch
    exp = [r[0] // 1_000_000 for r in rows if r[1] and r[0]]
    if exp and max(exp) - now < WARN_DAYS * 86400:
        days = max(0, (max(exp) - now) // 86400)
        alert(key, f"{label} session expires in {days} days. {how}")

def main():
    github()
    session("luma", "luma.com", "Luma", "https://luma.com", "Open Brave with --user-data-dir ~/.luma-agent/brave-profile and log into luma.com")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "fail": alert(sys.argv[2], sys.argv[3])
    else: main()
