import argparse
import json

from utils.file_utils import export_to_json
from utils.simple_logger import print_log
from ytm.constants import YTM_URL_PLAY_STATUS_OK
from ytm.yt_client import YouTubeClient
from ytm.ytm_watch_history import YTMWatchHistoryEntry


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process YouTube Music watch history errors and fetch song details.")
    parser.add_argument("--file", required=True, help="Input JSON file containing watch history errors.")
    args = parser.parse_args()

    input_file = args.file
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading file {input_file}: {e}")
        exit(1)

    entries = [YTMWatchHistoryEntry.from_dict(row) for row in data]

    client = YouTubeClient()

    output_errors = []
    output_ok = []

    for entry in entries:
        if entry.titleUrl:
            print_log(f"Processing URL: {entry.titleUrl}")

            song_details = client.extract_song_details(entry.titleUrl)
            status = song_details.get("playabilityStatus", {}).get("status", "UNKNOWN")
            status_reason = song_details.get("playabilityStatus", {}).get("reason", "")

            if status != YTM_URL_PLAY_STATUS_OK:
                print_log(f"  ✗ Failed to fetch song details for URL {entry.titleUrl} with status {status} and reason: {status_reason}")
                entry.set_metadata_error(status_reason)
                output_errors.append(entry)
                continue

            title = song_details.get("videoDetails", {}).get("title", "")
            artist = song_details.get("videoDetails", {}).get("author", "")
            entry.set_track_data(title, artist)
            output_ok.append(entry)

            print_log(f"  ✓ Fetched song details: Title='{title}', Artist='{artist}'")
    
    print_log(f"Processed {len(entries)} entries: {len(output_ok)} OK, {len(output_errors)} errors")
    export_to_json(output_ok, input_file, "fixed")
    export_to_json(output_errors, input_file, "errors", parent_directory="output\\errors")

    print_log("Finished. Now you can use the *.fixed.json file as input for the all-in-one script, starting from sanitization. The items from the *.errors.json cannot be worked with, as most of the errors state that the video is permanently unavailable.")