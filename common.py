import contextlib, datetime, json, os, pathlib, random, re, time
import requests, yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA, OUT = ROOT / "data", ROOT / "output"

def cfg():
    return yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")

def read_json(name, default):
    p = DATA / name
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default

def write_json(name, obj):
    DATA.mkdir(exist_ok=True)
    (DATA / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")

def append_log(stage, rec):
    log = read_json(f"{stage}_log.json", [])
    log.append(rec)
    write_json(f"{stage}_log.json", log[-200:])

@contextlib.contextmanager
def stage(name, run_id, **meta):
    """Every pipeline stage runs inside this: it records status, duration, errors to data/<stage>_log.json."""
    rec = {"run_id": run_id, "stage": name, "ts": now(), **meta}
    t0 = time.time()
    try:
        yield rec
        rec["status"] = "ok"
    except Exception as e:
        rec["status"] = "fail"
        rec["error"] = f"{type(e).__name__}: {e}"[:600]
        raise
    finally:
        rec["seconds"] = round(time.time() - t0, 1)
        append_log(name, rec)

def gemini(prompt, system, search=False):
    """Returns text, or None if GEMINI_API_KEY is missing (dry-run mode)."""
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{cfg()['gemini_model']}:generateContent"
    body = {"systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 1.0}}
    if search:
        body["tools"] = [{"google_search": {}}]
    r = requests.post(url, params={"key": key}, json=body, timeout=180)
    r.raise_for_status()
    parts = r.json()["candidates"][0]["content"]["parts"]
    return "".join(p.get("text", "") for p in parts)

def parse_json(text):
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M)
    return json.loads(text[text.index("{"): text.rindex("}") + 1])

def pick_formula(kind):
    formulas = yaml.safe_load((ROOT / "prompts/hooks.yaml").read_text(encoding="utf-8"))["formulas"]
    stats = {}
    for v in read_json("analytics.json", []):
        if v.get("formula") in formulas:
            stats.setdefault(v["formula"], []).append(v.get("views", 0))
    if stats and random.random() < 0.7:
        best = max(stats, key=lambda k: sum(stats[k]) / len(stats[k]))
        return best, formulas[best]
    name = random.choice(list(formulas))
    return name, formulas[name]
