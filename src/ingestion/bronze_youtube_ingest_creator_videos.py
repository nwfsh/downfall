# Ingestion layer: creator -> list of video links.
# This is deliberately separate from bronze_youtube_ingest.py's per-video
# comment/metadata pulling — this layer's only job is figuring out WHICH
# videos exist for a creator (full history or a bounded date window), and
# landing that list as its own artifact. The next layer (ingest_video)
# consumes this list; it doesn't need to know how the list was built.

import json
from datetime import datetime, timezone
from pathlib import Path
import requests
import os 

from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("YOUTUBE_API_KEY")  
BASE_URL = "https://www.googleapis.com/youtube/v3"
OUTPUT_DIR = Path("bronze/video_links")

def get_channel_video_count(channel_id: str) -> int:
    """Check how many public videos a channel has before deciding whether to
    run full-history or date-windowed mode. Costs 1 quota unit."""
    resp = requests.get(
        f"{BASE_URL}/channels",
        params={"part": "statistics", "id": channel_id, "key": API_KEY},
    )
    resp.raise_for_status()
    items = resp.json().get("items", [])
    if not items:
        raise ValueError(f"Channel not found: {channel_id}")
    count = int(items[0]["statistics"].get("videoCount", 0))
    print(f"{channel_id} has {count} public videos.")
    return count


#playlistItems.list (uploads playlist) → 1 quota unit per page of 50 videos
# search.list with channelId filter → 100 quota units per page — the only other way to list all channel videos
# using youtube's already made playlist for a creator is much cheaper for token use 

def _get_uploads_playlist_id(channel_id: str) -> str:
    resp = requests.get(
        f"{BASE_URL}/channels",
        params={"part": "contentDetails", "id": channel_id, "key": API_KEY},
    )
    resp.raise_for_status()
    items = resp.json().get("items", [])
    if not items:
        raise ValueError(f"Channel not found: {channel_id}")
    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

# helper function 
def get_all_channel_video_ids(channel_id: str) -> list[str]:
    """Page through the full uploads playlist and return every video ID."""
    playlist_id = _get_uploads_playlist_id(channel_id)
    video_ids = []
    page_token = None

    while True:
        params = {
            "part": "contentDetails",
            "playlistId": playlist_id,
            "maxResults": 50,
            "key": API_KEY,
        }
        if page_token:
            params["pageToken"] = page_token
        resp = requests.get(f"{BASE_URL}/playlistItems", params=params)
        resp.raise_for_status()
        data = resp.json()
        video_ids.extend(item["contentDetails"]["videoId"] for item in data.get("items", []))
        page_token = data.get("nextPageToken")
        if not page_token:
            break

    print(f"Found {len(video_ids)} total videos for channel {channel_id}.")
    return video_ids

# helper function 
def get_channel_video_ids_in_window(channel_id: str, start_date: str, end_date: str) -> list[str]:
    """
    Return video IDs published between start_date and end_date (inclusive, YYYY-MM-DD).
    playlist list videos by newest first u so can stop paging once u pass the start date
    """
    playlist_id = _get_uploads_playlist_id(channel_id)
    video_ids = []
    page_token = None
    start_dt = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
    end_dt = datetime.fromisoformat(end_date).replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)

    while True:
        params = {
            "part": "contentDetails,status,snippet",
            "playlistId": playlist_id,
            "maxResults": 50, # youtube will give u maximum 50 anwaysy 
            "key": API_KEY,
        }
        if page_token:
            params["pageToken"] = page_token
        resp = requests.get(f"{BASE_URL}/playlistItems", params=params)
        resp.raise_for_status()
        data = resp.json()

        done = False
        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            published_str = snippet.get("publishedAt") or item.get("contentDetails", {}).get("videoPublishedAt")
            title = snippet.get("title", "")

            if title in ("Private video", "Deleted video") or not published_str:
                continue

            published = datetime.fromisoformat(published_str.replace("Z", "+00:00"))

            if published < start_dt:
                done = True
                continue  # finish the page, don't exit mid-page

            if published <= end_dt:
                video_ids.append(item["contentDetails"]["videoId"])

        page_token = data.get("nextPageToken")
        if done or not page_token:
            break

    print(f"Found {len(video_ids)} videos for channel {channel_id} between {start_date} and {end_date}.")
    return video_ids


# helper function 
def video_id_to_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def get_video_links_for_creator(channel_id: str, start_date: str = None, end_date: str = None) -> list[str]:
    """
    all video links from one creator
    if there is a start_date & end_date, only collect videos between that
    """
    if start_date and end_date:
        video_ids = get_channel_video_ids_in_window(channel_id, start_date, end_date)
    else:
        video_ids = get_all_channel_video_ids(channel_id)
    return [video_id_to_url(vid) for vid in video_ids]


def land_video_links(channel_id: str, label: str, links: list[str]):
    """writes list of video links to the disk as a JSON file"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_label = label.lower().replace(" ", "_") if label else channel_id
    out_path = OUTPUT_DIR / f"video_links_{safe_label}_{ts}.json"
    payload = {
        "channel_id": channel_id,
        "label": label,
        "video_count": len(links),
        "video_links": links,
    }
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"Landed {len(links)} video links for {label or channel_id} → {out_path}")
    return out_path


def process_creators(creators: list[dict]) -> dict:
    """ run get_video_links_for_creator + land_video_links(aka turning them into json)
    over a bunch of creators. 
    this returns a dict in json ( called results ), where the key is the creator, and the 
    value is list of the links to all the videos, """
    results = {}
    for creator in creators: # taking from the calibration set 
        channel_id = creator["channel_id"]
        label = creator.get("label", channel_id)
        start_date = creator.get("start_date")
        end_date = creator.get("end_date")

        print(f"=== {label} ===")
        links = get_video_links_for_creator(channel_id, start_date, end_date)
        land_video_links(channel_id, label, links)
        results[label] = links

    return results


if __name__ == "__main__":
    # Calibration set — see project description §8 and downfall ADR-007.
    # channel_id is the UCxxxx-format ID, NOT the @handle — find it via
    # the channel's About page ("Share channel" > copy channel ID).
    # TODO: fill in real channel IDs. Trisha Paytas and Ryan Higa have no
    # single clean event date — decide their windows before running, or
    # leave start_date/end_date out entirely to pull full channel history.
    # CALIBRATION_SET = [
    #     {"label": "James Charles", "channel_id": "TODO_channel_id", "start_date": "2019-04-01", "end_date": "2019-08-01"},
    #     {"label": "PewDiePie", "channel_id": "TODO_channel_id", "start_date": "2016-12-01", "end_date": "2017-04-01"},
    #     {"label": "Trisha Paytas", "channel_id": "TODO_channel_id", "start_date": "TODO_start", "end_date": "TODO_end"},
    #     {"label": "Ryan Higa", "channel_id": "TODO_channel_id", "start_date": "TODO_start", "end_date": "TODO_end"},
    #     {"label": "Stephanie Soo", "channel_id": "TODO_channel_id", "start_date": "2019-11-01", "end_date": "2020-03-01"},
    #     {"label": "Logan Paul", "channel_id": "TODO_channel_id", "start_date": "2017-11-01", "end_date": "2018-03-01"},
    # ]



    # quick test
    # count = get_channel_video_count("UCenxjWEkb0Sv67vejOgZ3Tg")
    # ids = get_channel_video_ids_in_window("UCenxjWEkb0Sv67vejOgZ3Tg", "2026-05-01", "2026-06-01")
    # print(ids[:5])

    CALIBRATION_SET = [
    # Multiple controversies. Tati Westbrook "Bye Sister" May 10 2019; James lost ~3M subs in days;
    # "No More Lies" response May 18. Baseline before, spike, early recovery — all inside 6 weeks.
    {"label": "James Charles", "channel_id": "UCucot-Zp428OwkyRm2I7v2Q",
     "start_date": "2019-05-01", "end_date": "2019-06-15"},   # ~6-8 videos

    # Known downfall, subscriber-immune. WSJ article + Disney/YouTube Red drop Feb 13-14 2017;
    # "My Response" Feb 16. Daily uploader then — window kept tight on purpose.
    {"label": "PewDiePie", "channel_id": "UC-lHJZR3Gqxm24_Vd_AJ5Yw",
     "start_date": "2017-02-01", "end_date": "2017-03-05"},   # ~30 videos

    # Single event, best-documented recovery mechanism. Aokigahara video Dec 31 2017; removed +
    # apologies Jan 1-2; ~3 weeks of silence; suicide-prevention return video Jan 24 2018.
    {"label": "Logan Paul", "channel_id": "UCG8rbF3g2AMX70yOd8vqIZg",
     "start_date": "2017-12-15", "end_date": "2018-02-10"},   # ~15-25 videos

    # Single event, recovered — mechanism deliberately left for the pipeline to find.
    # Her Nikocado video ~Dec 21 2019; his rebuttal shifted backlash onto her late Dec.
    {"label": "Stephanie Soo", "channel_id": "UCo9ZZ04kIhN_8xGxvnjaduQ",
     "start_date": "2019-12-10", "end_date": "2020-01-31"},   # ~15-20 videos

    # Controversial-by-design, chronic — NEGATIVE test for false change-points on a
    # naturally-hot baseline. Window around Frenemies podcast ending (~June 8 2021), one of many.
    {"label": "Trisha Paytas", "channel_id": "UCF2oW5-MO8dB6ul9WH9xi0A",
     "start_date": "2021-05-25", "end_date": "2021-07-05"},   # posts multiple/day — cap matters most here

    # Vanilla, never cancelled — NEGATIVE control, expect ~zero change points.
    # No event; any active-posting window works. Pre-2020 hiatus.
    {"label": "Ryan Higa", "channel_id": "UCSAUGyc_xA8uYzaIVG6MESQ",
     "start_date": "2019-05-01", "end_date": "2019-06-30"},   # ~8 videos
]
    process_creators(CALIBRATION_SET)

    # trisha_paytas = get_channel_video_count("UCy2A0jf5lYUYQxi7iKHmHhQ")
    # james_charles = get_channel_video_count("UCucot-Zp428OwkyRm2I7v2Q")
    # pewdiepie = get_channel_video_count("UC-lHJZR3Gqxm24_Vd_AJ5Yw")
    # ryan_higa = get_channel_video_count("UCSAUGyc_xA8uYzaIVG6MESQ")
    # stephanie_soo = get_channel_video_count("UCo9ZZ04kIhN_8xGxvnjaduQ")
    # logan_paul = get_channel_video_count("UCG8rbF3g2AMX70yOd8vqIZg")

#     UCy2A0jf5lYUYQxi7iKHmHhQ has 394 public videos.
# UCucot-Zp428OwkyRm2I7v2Q has 726 public videos.
# UC-lHJZR3Gqxm24_Vd_AJ5Yw has 4665 public videos.
# UCSAUGyc_xA8uYzaIVG6MESQ has 403 public videos.
# UCo9ZZ04kIhN_8xGxvnjaduQ has 376 public videos.
# UCG8rbF3g2AMX70yOd8vqIZg has 802 public videos.




