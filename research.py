"""Stage 1: free trend signals (YouTube autocomplete) + your manual reference notes."""
import requests
from .common import ROOT, cfg, stage, write_json, read_json

def suggest(q):
    try:
        r = requests.get("https://suggestqueries.google.com/complete/search",
                         params={"client": "firefox", "ds": "yt", "q": q}, timeout=15)
        return r.json()[1][:8]
    except Exception:
        return []

def notes():
    p = ROOT / "research/reference_notes.md"
    return p.read_text(encoding="utf-8")[:3000] if p.exists() else ""

def run(run_id):
    c = cfg()
    with stage("research", run_id) as rec:
        topics = {}
        for seed in c["tech_seeds"][:4]:
            topics[seed] = suggest(seed + " 2026")
        for seed in ["telugu motivational", "telugu mythology stories", "telugu rhymes for kids"]:
            topics[seed] = suggest(seed)
        write_json("topics.json", topics)
        rec["seeds"] = len(topics)
    return topics
