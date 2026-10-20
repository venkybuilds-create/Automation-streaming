"""Stage 7: pull YouTube stats for published videos -> data/analytics.json (feeds hook leaderboard)."""
from .common import read_json, write_json, stage, now
from .publish import _yt

def run(run_id):
    with stage("analytics", run_id) as rec:
        pubs = [p for p in read_json("publish_log.json", []) if p.get("video_id") and p.get("status") == "ok"]
        out = []
        yt = _yt()
        for i in range(0, len(pubs), 50):
            batch = pubs[i:i + 50]
            res = yt.videos().list(part="statistics", id=",".join(p["video_id"] for p in batch)).execute()
            st = {v["id"]: v["statistics"] for v in res.get("items", [])}
            for p in batch:
                s = st.get(p["video_id"], {})
                out.append({"video_id": p["video_id"], "title": p["title"], "kind": p["kind"], "target": p["target"],
                            "formula": p["formula"], "views": int(s.get("viewCount", 0)), "likes": int(s.get("likeCount", 0)),
                            "comments": int(s.get("commentCount", 0)), "updated": now()})
        write_json("analytics.json", out)
        rec["videos"] = len(out)
