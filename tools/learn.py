#!/usr/bin/env python3
"""Learn interest weights from the graph. Writes learned.json (committed; interests.json stays your hand-edited seed).
boost = (avg rating - 3) * 1.0, clipped to [-3, +3], per Topic/Host rated by feedback. Needs >=1 rating.
Topics with avg>=4 not already in interests.json keywords are listed as suggested_keywords.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import graph
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.environ.get("LEARNED", os.path.join(ROOT, "learned.json"))
SEED = os.path.join(ROOT, "interests.json")

def run():
    w = graph.weights()
    boosts = {k: max(-3, min(3, round(v - 3, 2))) for k, v in w.items()}
    kws = {k.lower() for k in json.load(open(SEED))["keywords"]} if os.path.exists(SEED) else set()
    sugg = [k.split(":", 1)[1] for k, v in w.items()
            if k.startswith("topic:") and v >= 4 and k.split(":", 1)[1].lower() not in kws]
    res = {"boosts": boosts, "suggested_keywords": sugg}
    json.dump(res, open(OUT, "w"), indent=1)
    print(json.dumps(res))
    if sugg and not os.environ.get('LEARNED'):
        import notify; notify.send('Luma agent: new interests?', 'Add to interests.json: ' + ', '.join(sugg))

if __name__ == "__main__":
    run()
