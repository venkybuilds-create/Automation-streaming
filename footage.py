"""Stage 4: pick a clip per line. Priority: your AI clips/licensed clips -> Pexels (free API) -> solid colour."""
import os, random, pathlib, requests
from .common import ROOT, cfg, stage

def local_clip(theme):
    c = cfg()
    dirs = [ROOT / "assets/clips" / theme, ROOT / "assets/clips"]  # drop Kling/Veo/Pika clips here
    if c["use_movie_clips"]:
        dirs.insert(0, ROOT / "assets/licensed_clips" / theme)
    for d in dirs:
        files = [f for f in d.glob("*.mp4")] if d.exists() else []
        if files:
            return random.choice(files)

def pexels(query, orient, dest):
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        return None
    r = requests.get("https://api.pexels.com/videos/search", headers={"Authorization": key}, timeout=30,
                     params={"query": query, "orientation": "portrait" if orient == "v" else "landscape", "per_page": 6})
    vids = r.json().get("videos", [])
    if not vids:
        return None
    files = sorted(random.choice(vids)["video_files"], key=lambda f: abs((f.get("height") or 0) - 1080))
    dest.write_bytes(requests.get(files[0]["link"], timeout=120).content)
    return dest

def run(run_id, script, d: pathlib.Path):
    orient = "h" if script["target"] == "long" else "v"
    with stage("footage", run_id, kind=script["kind"]) as rec:
        hits = {"local": 0, "pexels": 0, "fallback": 0}
        for i, l in enumerate(script["lines"]):
            p = local_clip(script["topic"] if script["kind"] == "reel" else "")
            src = "local"
            if not p:
                try:
                    p, src = pexels(l["visual"], orient, d / f"c{i}.mp4"), "pexels"
                except Exception:
                    p = None
            if not p:
                src = "fallback"
            l["clip"] = str(p) if p else None
            hits[src] += 1
        rec.update(hits)
    script["orient"] = orient
    return script
