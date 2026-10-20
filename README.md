# Reel Factory

Faceless Telugu channel automation, 100% free tiers:
Telugu emotional reels (Instagram) · daily Shorts · weekly long videos (mythology, tech-as-story, kids rhymes).

```
research → script (Gemini + hook formula) → voice (edge-tts Telugu) → footage (your clips / Pexels) → render (FFmpeg) → publish (YouTube / Instagram) → analytics → better hooks
```
Every stage logs to `data/<stage>_log.json`; the dashboard (`docs/index.html`) reads those logs.

## Setup (about 30 minutes, once)
1. Create a GitHub **public** repo (Instagram needs a public video URL; secrets stay private), push this folder.
2. Settings → Pages → deploy from branch `main`, folder `/docs`. Settings → Actions → Workflow permissions → Read and write.
3. Add Secrets (Settings → Secrets → Actions):
   - `GEMINI_API_KEY` (aistudio.google.com, free)
   - `PEXELS_API_KEY` (pexels.com/api, free)
   - `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`: Google Cloud project, enable YouTube Data API v3, OAuth client, authorize once with scopes `youtube.upload` + `youtube.readonly`. New API projects start with unverified-app upload limits (videos may be locked private until audited), so keep `youtube_privacy: private` while testing.
   - `IG_ACCESS_TOKEN`, `IG_USER_ID`: Instagram Business/Creator account linked to a Facebook Page, Meta developer app with `instagram_content_publish`.
4. Actions tab → **pipeline** → Run workflow (target `short`) to test. Open the dashboard: `https://<you>.github.io/<repo>/`.

## Local test (no keys needed for the script stage)
```
pip install -r requirements.txt   # + ffmpeg and a Telugu font (fonts-noto-core)
python run.py make --target reel --theme sad
```
Without `GEMINI_API_KEY` it uses a built-in Telugu fallback script (marked dry-run in the dashboard).
Output lands in `output/<run-id>/final.mp4`.

## Your AI clips
Generate 1-3 clips a day in Kling / Veo / Pika / Luma free credits, drop `.mp4` files in `assets/clips/` (or `assets/clips/<theme>/`). They are used before stock footage. Add royalty-free `.mp3` to `assets/music/` for background music.

## Movie clips
`use_movie_clips: false` by default. Film footage/audio is copyrighted; Instagram and YouTube both issue claims and strikes. Only enable it for clips you license, in `assets/licensed_clips/<theme>/`.

## Weekly routine (15 min)
Run the prompts in `research/perplexity_weekly_prompt.md`, paste results into `research/reference_notes.md`. Every script prompt reads it.

## Known limits
- Public-repo releases hold reel videos for Instagram; delete old releases monthly.
- No thumbnails yet (long videos: add custom thumbnails in YouTube Studio).
- YouTube may require disclosing AI-generated voice/visuals (Studio upload settings), and rewards original angles over templated uploads.
- Tune `gemini_model` in `config.yaml` if the model name changes.
