#!/usr/bin/env python3
"""Daily graph compaction. Keeps booked/rated events + their relations; drops stale noise; archives old history.
  compact.py [--force]
Rules: dedupe -> prune past seen/skipped/needs_user events -> archive booked/done events older than archive_days
into month:YYYY-MM summaries -> sweep orphan Topic/Host/Venue (except interests.json keywords / learned.json keys).
"""
import json, os, sys, datetime, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import graph
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOISE = {"seen", "skipped", "needs_user"}; KEEP = {"booked", "done", "awaiting_feedback"}

def load(p, d):
    return json.load(open(p)) if os.path.exists(p) else d

def start(n):
    try:
        t = datetime.datetime.fromisoformat(n["props"]["start"])
        return t if t.tzinfo else t.replace(tzinfo=datetime.timezone.utc)
    except Exception:
        return None

def compact(now=None):
    now = now or datetime.datetime.now(datetime.timezone.utc)
    cfg = load(os.path.join(ROOT, "interests.json"), {}); ret = cfg.get("retention", {})
    noise_d, arch_d = ret.get("noise_days", 14), ret.get("archive_days", 365)
    ns, es = graph.nodes(), graph.edges()
    es = [dict(t) for t in {tuple(sorted(e.items())) for e in es}]  # dedupe edges
    drop = set(); stats = ns.get("stats:seen", {"props": {}})["props"]
    seen_n, skip_n = stats.get("total_seen", 0), stats.get("total_skipped", 0)
    months = collections.defaultdict(lambda: {"events": 0, "ratings": [], "topics": collections.Counter(), "hosts": collections.Counter()})
    rating = {e["from"]: ns[e["to"]]["props"].get("rating") for e in es if e["rel"] == "RATED" and e["to"] in ns}
    for id, n in ns.items():
        if n["type"] != "Event": continue
        st, t = n["props"].get("status"), start(n)
        if t is None: continue
        age = (now - t).days
        if st in NOISE and age > noise_d:
            drop.add(id); seen_n += 1; skip_n += st == "skipped"
        elif st in {"booked", "done"} and age > arch_d:
            m = months[t.strftime("%Y-%m")]; m["events"] += 1
            if rating.get(id): m["ratings"].append(rating[id])
            for e in es:
                if e["from"] == id and e["rel"] == "ABOUT": m["topics"][e["to"]] += 1
                if e["from"] == id and e["rel"] == "HOSTED_BY": m["hosts"][e["to"]] += 1
            drop.add(id); drop |= {e["to"] for e in es if e["from"] == id and e["rel"] == "RATED"}
    es = [e for e in es if e["from"] not in drop and e["to"] not in drop]
    for k, m in months.items():
        r = m["ratings"]; old = ns.get("month:" + k, {"props": {}})["props"]
        ns["month:" + k] = {"id": "month:" + k, "type": "MonthSummary", "props": {
            "events": old.get("events", 0) + m["events"],
            "avg_rating": round(sum(r) / len(r), 2) if r else old.get("avg_rating"),
            "top_topics": [x for x, _ in m["topics"].most_common(3)], "top_hosts": [x for x, _ in m["hosts"].most_common(3)]}}
    ns["stats:seen"] = {"id": "stats:seen", "type": "Stats", "props": {"total_seen": seen_n, "total_skipped": skip_n}}
    protect = {"topic:" + k.lower() for k in cfg.get("keywords", {})} | set(load(os.path.join(ROOT, "learned.json"), {}).get("boosts", {}))
    linked = {e["from"] for e in es} | {e["to"] for e in es}
    for id, n in ns.items():
        if n["type"] in ("Topic", "Host", "Venue") and id not in linked and id.lower() not in protect: drop.add(id)
    ns = {k: v for k, v in ns.items() if k not in drop}
    es = [e for e in es if e["from"] in ns and e["to"] in ns]
    for path, rows in ((graph.N, [{"id": n["id"], "type": n["type"], "props": n["props"]} for n in ns.values()]), (graph.E, es)):
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            f.writelines(json.dumps(r, sort_keys=True) + "\n" for r in sorted(rows, key=lambda r: json.dumps(r, sort_keys=True)))
        os.replace(tmp, path)
    return len(ns), len(es)

if __name__ == "__main__":
    stamp = os.path.join(graph.D, ".last_compact"); today = str(datetime.date.today())
    if "--force" not in sys.argv and os.path.exists(stamp) and open(stamp).read() == today: sys.exit(0)
    print("nodes, edges:", compact()); open(stamp, "w").write(today)
