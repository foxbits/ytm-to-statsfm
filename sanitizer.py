import json
import re

from objects.constants import FORBIDDEN_STRINGS, RG_SPLIT_CHARS, YT_MUSIC_TRACK_IDENTIFIER
import argparse

from objects.ytm_processed_track import YTMProcessedResults, YTMProcessedTrack

from utils.file_utils import export_to_json
from utils.simple_logger import print_log
from utils.timestamps import convert_to_unix_timestamp
from ytm.ytm_watch_history import YTMWatchHistoryEntry

def sanitize_video_track_info(track_name: str, artist_name: str) -> tuple[str, str]:
    """
    Sanitize track name and artist name for video entries by removing official tags
    and extracting artist information from the title.
    
    Returns:
        tuple: (track_name, artist_name)
    """
    original_channel = artist_name
    
    # Remove official tags from title
    officialTagsStripping = [
        r"([-|]\s*)?\((?:Official.*)\)(?:\s*[-|])?",
        r"([-|]\s*)?\(?(?:Official Video|Official Audio|Official)\)?(?:\s*[-|])?"
    ]
    for pattern in officialTagsStripping:
        track_name = re.sub(pattern, "", track_name, flags=re.IGNORECASE).strip()
    
    # Match channel name against title and clean
    artistTagsStripping = [
        r"(" + original_channel + r")(\s" + RG_SPLIT_CHARS + r"\s)",
        r"(\s" + RG_SPLIT_CHARS + r"\s)(" + original_channel + ")",
    ]
    channelMatched = False
    originalTrackName = track_name
    for pattern in artistTagsStripping:
        track_name = re.sub(pattern, "", track_name, flags=re.IGNORECASE|re.UNICODE).strip()
        channelMatched = channelMatched or track_name != originalTrackName

    # extract artist from title if different from channel, format <artist><separator><track>
    # (can't match other way since can't know what part is artist what part is track)
    if not channelMatched:
        artistTagsStripping = r"(.+)(\s" + RG_SPLIT_CHARS + r"\s)(.+)"

        artistmatch = re.match(artistTagsStripping, track_name, flags=re.IGNORECASE)
        if artistmatch:
            artist_name = artistmatch.group(1).strip()
            track_name = artistmatch.group(3).strip()
    
    # remove unwanted extra characters
    for pattern in FORBIDDEN_STRINGS:
        track_name = re.sub(pattern, " ", track_name, flags=re.IGNORECASE|re.UNICODE).strip()
        artist_name = re.sub(pattern, " ", artist_name, flags=re.IGNORECASE|re.UNICODE).strip()

    return track_name, artist_name

def process_youtube_music_entries(input_file="watch-history.json", ignore_videos=False) -> YTMProcessedResults:
    """
    Read YTM input format, filter and process YTM entries, return formatted output object
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            data_raw = json.load(file)
            data = [YTMWatchHistoryEntry.from_dict(item) for item in data_raw]
        
        # Filter entries where header is "YouTube Music"
        processed = YTMProcessedResults(songs=[], music_videos=[], errors=[], skipped=[])
        for entry in data:
            if not entry.is_youtube_music_entry():
                continue

            track = YTMProcessedTrack()

            # Extract relevant fields
            # Timestamp (ISO standard) + Unix timestamp
            track.timestamp_iso = entry.time
            track.timestamp_unix = convert_to_unix_timestamp(track.timestamp_iso)

            # URL + decode (remove stuff like \u003d)
            track.metadata.ytm_url = entry.titleUrl
            if track.metadata.ytm_url:
                track.metadata.ytm_url = track.metadata.ytm_url.encode().decode('unicode_escape')

            # Artist
            track.artist = entry.subtitles[0].name if entry.subtitles else None
            track.metadata.original_channel = track.artist

            # Title
            track.title = entry.title[8:] # remove the "Watched " from the beginning
            track.metadata.original_title = track.title

            is_valid = track.artist and track.title
            if not is_valid:
                print_log(f"Skipping invalid entry (cannot identify track/artist): [{entry.title}][{track.metadata.ytm_url}]")
                processed.errors.append(entry)
                continue

            # videos watched on YT Music are those not part of artist accounts (e.g. Artist - Topic format);
            # if the flag to ignore them is true, then do not consider them
            is_video = track.is_valid() and track.is_music_video()
            if is_video and ignore_videos:
                print_log(f"Ignoring video due to setting: [{entry.title}][{track.metadata.ytm_url}]")
                processed.skipped.append(entry)
                continue

            if track.is_valid() and track.is_track():
                track.artist = track.artist.replace(YT_MUSIC_TRACK_IDENTIFIER, "").strip()

            # Cleanup track names which use YouTube video format (only applies to videos watched on YT music, standard music tracks do not need it)
            if is_video and not ignore_videos:
                track.title, track.artist = sanitize_video_track_info(track.title, track.artist)

            track.metadata.is_video = is_video
            if is_video:
                processed.music_videos.append(track)
            else:
                processed.songs.append(track)

        return processed
    
    except FileNotFoundError:
        print_log(f"Error: {input_file} not found")
        return []
    except json.JSONDecodeError:
        print_log(f"Error: Invalid JSON in {input_file}")
        return []

if __name__ == "__main__":
    # Arguments
    parser = argparse.ArgumentParser(description="Process YouTube Music history")
    parser.add_argument("--file", default="watch-history.json", help="Input file path (default: watch-history.json)")
    parser.add_argument("--ignore-videos", action="store_true", help="Specify in order to ignore videos watched on YouTube Music and process only songs")
    args = parser.parse_args()
    
    input_file = args.file
    ignore_videos = args.ignore_videos

    # Process
    ytm_entries = process_youtube_music_entries(input_file, ignore_videos)

    # Post-process
    if not ytm_entries or len(ytm_entries.songs) + len(ytm_entries.music_videos) + len(ytm_entries.errors) == 0:
        print_log("No valid entries found for export.")
        exit(0)

    # Print summary
    print_log(f"Found {len(ytm_entries.songs)} songs, {len(ytm_entries.music_videos)} music videos (skipped {len(ytm_entries.skipped)} entries)")
    print_log(f"Found {len(ytm_entries.errors)} errors")

    # Export to json
    export_to_json(ytm_entries.songs, input_file, "songs")
    export_to_json(ytm_entries.music_videos, input_file, "videos")
    export_to_json(ytm_entries.errors, input_file, "errors", parent_directory="output\\errors")
    export_to_json(ytm_entries.skipped, input_file, "skipped")

    print_log("Processing complete. Songs and videos exported into separate files.")
    print_log("Double check the music videos file since the processing is not fully deterministic, everybody names their songs in various formats, some might be unsupported.")
    print_log("Check the errors and the skipped files - those tracks could not be processed, might have missing information. If you can fix them, you can re-process them again later")