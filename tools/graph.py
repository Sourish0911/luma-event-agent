#!/usr/bin/env python3
"""Tiny graph DB: append-only JSONL. Latest record per node id wins.
CLI:
  graph.py node <id> <type> '<json props>'   upsert node (props merged)
  graph.py edge <from> <rel> <to>            add edge (deduped)
  graph.py list [type] [status]              print nodes as JSON lines
  graph.py weights                           topic/host avg rating
  graph.py selftest
"""
import json, sys, os
D = os.environ.get("GRAPH_DIR", os.path.join(os.path.dirname(__file__), "..", "data"))
N, E = os.path.join(D, "nodes.jsonl"), os.path.join(D, "edges.jsonl")

def _read(p):
    return [json.loads(l) for l in open(p)] if os.path.exists(p) else []

def nodes():
    out = {}
    for r in _read(N):
        cur = out.setdefault(r["id"], {"id": r["id"], "type": r["type"], "props": {}})
        cur["props"].update(r["props"])
    return out

def edges():
    return _read(E)

def add_node(id, type, props=None):
    os.makedirs(D, exist_ok=True)
    with open(N, "a") as f:
        f.write(json.dumps({"id": id, "type": type, "props": props or {}}) + "\n")

def add_edge(a, rel, b):
    e = {"from": a, "rel": rel, "to": b}
    if e in edges():
        return
    os.makedirs(D, exist_ok=True)
    with open(E, "a") as f:
        f.write(json.dumps(e) + "\n")

def find(type=None, status=None):
    return [n for n in nodes().values()
            if (not type or n["type"] == type) and (not status or n["props"].get("status") == status)]

def weights():
    """avg rating per Topic/Host, via Event -RATED-> Feedback and Event -ABOUT/HOSTED_BY-> X"""
    ns, es = nodes(), edges()
    rating = {e["from"]: ns[e["to"]]["props"].get("rating") for e in es if e["rel"] == "RATED"}
    acc = {}
    for e in es:
        if e["rel"] in ("ABOUT", "HOSTED_BY") and rating.get(e["from"]):
            acc.setdefault(e["to"], []).append(rating[e["from"]])
    return {k: round(sum(v) / len(v), 2) for k, v in acc.items()}

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    if a[0] == "node": add_node(a[1], a[2], json.loads(a[3]) if len(a) > 3 else {})
    elif a[0] == "edge": add_edge(a[1], a[2], a[3])
    elif a[0] == "list":
        for n in find(a[1] if len(a) > 1 else None, a[2] if len(a) > 2 else None):
            print(json.dumps(n))
    elif a[0] == "weights": print(json.dumps(weights(), indent=1))
    elif a[0] == "selftest":
        import tempfile; D = tempfile.mkdtemp(); N, E = D + "/n", D + "/e"
        add_node("ev1", "Event", {"status": "seen"}); add_node("ev1", "Event", {"status": "booked"})
        add_node("t:ai", "Topic"); add_edge("ev1", "ABOUT", "t:ai"); add_edge("ev1", "ABOUT", "t:ai")
        add_node("fb1", "Feedback", {"rating": 4}); add_edge("ev1", "RATED", "fb1")
        assert find("Event", "booked") and not find("Event", "seen")
        assert len(edges()) == 2 and weights() == {"t:ai": 4.0}
        print("ok")
