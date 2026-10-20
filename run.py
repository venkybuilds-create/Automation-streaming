#!/usr/bin/env python3
"""Reel Factory CLI.
  python run.py make --target short|reel|long [--kind myth|tech|rhyme|reel] [--theme sad] [--publish]
  python run.py publish-ig --run-id ID --url PUBLIC_VIDEO_URL
  python run.py analytics
"""
import argparse, datetime, json, os, sys
from src import analytics, common, footage, publish, render, research, script_gen, voice

def auto_kind(target):
    c, today = common.cfg(), datetime.date.today()
    if target == "reel":
        return "reel"
    if target == "short":
        return c["short_rotation"][today.weekday()]
    return c["long_rotation"][today.isocalendar()[1] % len(c["long_rotation"])]

def make(a):
    kind = a.kind or auto_kind(a.target)
    run_id = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S") + f"-{a.target}"
    d = common.OUT / run_id
    d.mkdir(parents=True, exist_ok=True)
    research.run(run_id)
    s = script_gen.run(run_id, kind, a.target, a.theme)
    s = voice.run(run_id, s, d)
    s = footage.run(run_id, s, d)
    final = render.run(run_id, s, d)
    (d / "meta.json").write_text(json.dumps({k: v for k, v in s.items() if k != "lines"}, ensure_ascii=False))
    (d / "script.json").write_text(json.dumps(s, ensure_ascii=False, indent=1))
    if a.publish and a.target != "reel" and os.environ.get("YT_REFRESH_TOKEN"):
        publish.youtube(run_id, s, final)
    print(run_id)
    if os.environ.get("GITHUB_OUTPUT"):
        open(os.environ["GITHUB_OUTPUT"], "a").write(f"run_id={run_id}\n")

def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("make")
    m.add_argument("--target", choices=["short", "reel", "long"], required=True)
    m.add_argument("--kind", choices=["myth", "tech", "rhyme", "reel"])
    m.add_argument("--theme")
    m.add_argument("--publish", action="store_true")
    i = sub.add_parser("publish-ig")
    i.add_argument("--run-id", required=True)
    i.add_argument("--url", required=True)
    sub.add_parser("analytics")
    a = p.parse_args()
    if a.cmd == "make":
        make(a)
    elif a.cmd == "publish-ig":
        s = json.loads((common.OUT / a.run_id / "script.json").read_text(encoding="utf-8"))
        publish.instagram(a.run_id, s, a.url)
    else:
        analytics.run(datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S") + "-analytics")

if __name__ == "__main__":
    main()
