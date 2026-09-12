"""
End-to-end test: get Stephanie Soo's video links for her Nikocado controversy window,
then pull metadata + comments for each video.

Run from src/ingestion/:
    python test_ingest_pipeline.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from bronze_youtube_ingest_creator_videos import get_video_links_for_creator, API_KEY
from bronze_youtube_ingest_comments import ingest_video

STEPHANIE_SOO = {
    "channel_id": "UCo9ZZ04kIhN_8xGxvnjaduQ",
    "start_date": "2019-12-10",
    "end_date": "2020-01-31",
}

if __name__ == "__main__":
    if not API_KEY:
        raise SystemExit("Set YOUTUBE_API_KEY as an environment variable first.")

    print("=== Step 1: Fetching Stephanie Soo video links ===")
    links = get_video_links_for_creator(
        STEPHANIE_SOO["channel_id"],
        STEPHANIE_SOO["start_date"],
        STEPHANIE_SOO["end_date"],
    )
    print(f"Found {len(links)} videos in window.\n")

    print("=== Step 2: Ingesting metadata + comments for each video ===")
    for url in links:
        video_id = url.split("v=")[-1]
        print(f"\n--- {video_id} ---")
        try:
            ingest_video(video_id)
        except RuntimeError as e:
            print(f"SKIPPED {video_id}: {e}")

    print("\n=== Done ===")
