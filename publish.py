"""Stage 6: YouTube upload (Data API v3) and Instagram Reels (Graph API, needs a public video URL)."""
import os, time, requests
from .common import cfg, stage

def _yt():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    creds = Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN"], client_id=os.environ["YT_CLIENT_ID"],
                        client_secret=os.environ["YT_CLIENT_SECRET"], token_uri="https://oauth2.googleapis.com/token",
                        scopes=["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.readonly"])
    return build("youtube", "v3", credentials=creds)

def youtube(run_id, script, path):
    from googleapiclient.http import MediaFileUpload
    with stage("publish", run_id, platform="youtube", kind=script["kind"], target=script["target"],
               formula=script["formula"], title=script["title"]) as rec:
        title = script["title"] + (" #Shorts" if script["target"] != "long" else "")
        tags = script.get("hashtags", [])
        body = {"snippet": {"title": title[:100], "description": script["caption"] + "\n\n" + " ".join("#" + t.lstrip("#") for t in tags),
                            "tags": tags, "categoryId": "22", "defaultLanguage": cfg()["language"]},
                "status": {"privacyStatus": cfg()["youtube_privacy"], "selfDeclaredMadeForKids": script["kind"] == "rhyme"}}
        res = _yt().videos().insert(part="snippet,status", body=body,
                                    media_body=MediaFileUpload(str(path), resumable=True)).execute()
        rec["video_id"] = res["id"]
    return res["id"]

def instagram(run_id, script, video_url):
    tok, ig = os.environ["IG_ACCESS_TOKEN"], os.environ["IG_USER_ID"]
    g = "https://graph.facebook.com/v21.0"
    with stage("publish", run_id, platform="instagram", kind=script["kind"], target="reel",
               formula=script["formula"], title=script["title"]) as rec:
        cap = script["caption"] + "\n\n" + " ".join("#" + t.lstrip("#") for t in script.get("hashtags", []))
        cid = requests.post(f"{g}/{ig}/media", data={"media_type": "REELS", "video_url": video_url, "caption": cap,
                                                     "access_token": tok}, timeout=60).json()["id"]
        for _ in range(30):
            st = requests.get(f"{g}/{cid}", params={"fields": "status_code", "access_token": tok}, timeout=30).json()
            if st.get("status_code") == "FINISHED":
                break
            if st.get("status_code") == "ERROR":
                raise RuntimeError(f"Instagram processing failed: {st}")
            time.sleep(10)
        pub = requests.post(f"{g}/{ig}/media_publish", data={"creation_id": cid, "access_token": tok}, timeout=60).json()
        rec["media_id"] = pub["id"]
