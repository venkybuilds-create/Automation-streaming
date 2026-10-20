"""Stage 3: Telugu TTS per line (edge-tts, free) -> one WAV + exact per-line timings + SRT."""
import asyncio, subprocess, pathlib
import edge_tts
from .common import cfg, stage

def sh(*a):
    subprocess.run(a, check=True, capture_output=True)

def dur(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         check=True, capture_output=True, text=True).stdout
    return float(out.strip())

def srt_time(t):
    h, m, s = int(t // 3600), int(t % 3600 // 60), t % 60
    return f"{h:02}:{m:02}:{int(s):02},{int((s % 1) * 1000):03}"

async def _tts(lines, voice, rate, d):
    for i, l in enumerate(lines):
        await edge_tts.Communicate(l["text"], voice, rate=rate).save(str(d / f"l{i}.mp3"))

def run(run_id, script, d: pathlib.Path):
    c = cfg()
    with stage("voice", run_id, kind=script["kind"]) as rec:
        voice = c["voices"][c["language"]][c["voice_gender"][script["kind"]]]
        asyncio.run(_tts(script["lines"], voice, c["voice_rate"][script["kind"]], d))
        t, srt, lst = 0.0, [], []
        for i, l in enumerate(script["lines"]):
            sh("ffmpeg", "-y", "-i", str(d / f"l{i}.mp3"), "-af", "apad=pad_dur=0.3", str(d / f"l{i}.wav"))
            l["start"], l["dur"] = t, dur(d / f"l{i}.wav")
            srt.append(f"{i+1}\n{srt_time(t)} --> {srt_time(t + l['dur'] - 0.2)}\n{l['text']}\n")
            lst.append(f"file 'l{i}.wav'")
            t += l["dur"]
        (d / "list.txt").write_text("\n".join(lst))
        sh("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(d / "list.txt"), str(d / "voice.wav"))
        (d / "subs.srt").write_text("\n".join(srt), encoding="utf-8")
        rec.update(voice=voice, seconds_audio=round(t, 1))
    script["total"] = t
    return script
