"""Stage 5: FFmpeg render. 9:16 for reels/shorts, 16:9 for long. Burns Telugu captions."""
import pathlib, subprocess, random
from .common import ROOT, stage
from .voice import sh

def run(run_id, script, d: pathlib.Path):
    W, H = (1080, 1920) if script["orient"] == "v" else (1920, 1080)
    with stage("render", run_id, kind=script["kind"], target=script["target"]) as rec:
        segs = []
        for i, l in enumerate(script["lines"]):
            seg = d / f"s{i}.mp4"
            vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps=30,setsar=1"
            src = (["-stream_loop", "-1", "-i", l["clip"]] if l["clip"] else ["-f", "lavfi", "-i", f"color=c=0x1b1b3a:s={W}x{H}:r=30"])
            sh("ffmpeg", "-y", *src, "-t", f"{l['dur']:.3f}", "-vf", vf, "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", str(seg))
            segs.append(f"file 's{i}.mp4'")
        (d / "segs.txt").write_text("\n".join(segs))
        sh("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(d / "segs.txt"), "-c", "copy", str(d / "video.mp4"))
        music = list((ROOT / "assets/music").glob("*.mp3"))
        size = 14 if script["orient"] == "v" else 10
        style = f"FontName=Noto Sans Telugu,FontSize={size * 2},Bold=1,Outline=3,Alignment=2,MarginV={160 if script['orient']=='v' else 60}"
        final = d / "final.mp4"
        cmd = ["ffmpeg", "-y", "-i", "video.mp4", "-i", "voice.wav"]
        if music:
            cmd += ["-stream_loop", "-1", "-i", str(random.choice(music))]
            fc = f"[0:v]subtitles=subs.srt:force_style='{style}'[v];[1:a]volume=1.0[a1];[2:a]volume=0.12[a2];[a1][a2]amix=inputs=2:duration=first[a]"
        else:
            fc = f"[0:v]subtitles=subs.srt:force_style='{style}'[v];[1:a]anull[a]"
        cmd += ["-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                "-c:a", "aac", "-b:a", "160k", "-shortest", "final.mp4"]
        subprocess.run(cmd, check=True, capture_output=True, cwd=d)
        rec.update(file=str(final), seconds_video=round(script["total"], 1))
    return final
