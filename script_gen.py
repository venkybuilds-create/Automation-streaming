"""Stage 2: topic pick + hook formula + Gemini script. Falls back to a template if no API key (dry-run)."""
import random
from .common import cfg, gemini, parse_json, pick_formula, read_json, write_json, stage
from .research import notes

LANG = {"te": "Telugu (written in Telugu script, natural spoken style)", "en": "simple Indian English"}
SCHEMA = ('Return ONLY JSON: {"title": str (curiosity title, native language, <90 chars), '
          '"lines": [{"text": str (spoken line, native language), "visual": str (2-4 word ENGLISH stock-footage search, concrete and filmable)}], '
          '"caption": str, "hashtags": [str]}')

def pick_topic(kind, theme):
    c, used = cfg(), read_json("used_topics.json", [])
    if kind == "reel":
        return theme or random.choice(c["reel_themes"])
    pool = {"myth": c["myth_seeds"], "rhyme": c["rhyme_seeds"], "tech": c["tech_seeds"]}[kind]
    fresh = [t for t in pool if t not in used[-len(pool) // 2:]] or pool
    return random.choice(fresh)

def build_prompt(kind, target, topic, formula, fdesc):
    n = {"reel": 9, "short": 11, "long": 70}[target]
    lang = LANG[cfg()["language"]]
    base = {
      "reel": f"Write a deeply emotional motivational reel voice-over about '{topic}'. Original words ONLY: never quote film dialogues or songs. Calm, intimate, ends with a quiet turn to hope.",
      "myth": f"Retell a story from Indian mythology ({topic}) as gripping storytelling, with cliffhangers, vivid scenes, and a closing life lesson. Stay faithful to the traditional story.",
      "tech": f"Explain the latest in '{topic}' as a story with a human character and a problem; make complex ideas obvious through one analogy. Use only verifiable facts.",
      "rhyme": f"Write ORIGINAL kids rhymes about '{topic}' (do not copy existing rhymes): short, rhythmic, repeating, with simple imagery children can picture.",
    }[kind]
    return (f"{base}\nLanguage: {lang}.\nLines: exactly about {n}. Line 1 is the HOOK, spoken in the first 2 seconds, formula '{formula}': {fdesc}\n"
            f"Short lines (under 14 words). Reference style notes:\n{notes()}\n{SCHEMA}")

def fallback(kind, topic):
    lines = ["ఈ రోజు నీకు ఎవరూ చెప్పని నిజం ఇది.", "ఓడిపోయావని ఆగిపోకు.", "ప్రతి కష్టం నిన్ను బలంగా మారుస్తుంది.",
             "ఈ రోజు నీ మొదటి అడుగు వెయ్యి.", "కలలు నిజమవుతాయి, నువ్వు ఆగకపోతే."]
    return {"title": f"{topic} | తెలుగు", "lines": [{"text": t, "visual": "sunrise mountain"} for t in lines],
            "caption": topic, "hashtags": ["telugu", "motivation"]}

def run(run_id, kind, target, theme=None):
    with stage("script", run_id, kind=kind, target=target) as rec:
        topic = pick_topic(kind, theme)
        formula, fdesc = pick_formula(kind)
        txt = gemini(build_prompt(kind, target, topic, formula, fdesc),
                     "You are a viral short-form scriptwriter for a faceless Telugu channel.", search=(kind == "tech"))
        script = parse_json(txt) if txt else fallback(kind, topic)
        script.update(kind=kind, target=target, topic=topic, formula=formula)
        rec.update(topic=topic, formula=formula, lines=len(script["lines"]), dry_run=txt is None)
        write_json("used_topics.json", (read_json("used_topics.json", []) + [topic])[-60:])
    return script
