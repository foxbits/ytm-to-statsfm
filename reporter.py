import argparse
import json
import os
from typing import List
from spotify.spotify_listening_history import SpotifyStreamingEntry
from utils.file_utils import export_to_csv
from utils.simple_logger import print_log


def read_spotify_entries(input_file: str) -> List[SpotifyStreamingEntry]:
    """
    Read Spotify streaming entries from JSON file
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
            entries = [SpotifyStreamingEntry.from_dict(item) for item in data]
        
        return entries
    
    except FileNotFoundError:
        print_log(f"Error: {input_file} not found")
        return []
    except json.JSONDecodeError:
        print_log(f"Error: Invalid JSON in {input_file}")
        return []
    except Exception as e:
        print_log(f"Error processing file: {e}")
        return []

def sanitize_for_csv(text: str) -> str:
    return text.replace(",", " ").replace('"', "")

def build_choice_report_clear(entries: List[SpotifyStreamingEntry], score_by: str) -> dict:
    """
    Build a report of best matching track choice (CSV)
    """

    if not entries or len(entries) == 0:
        print_log("No entries available for building an output report file")
        return None

    report = ""

    # Add header
    header = "id," \
    "original_track," \
    "original_artist," \
    "your_choice," \
    "choices"

    report += f"{header}\n"

    # Add rows
    for i in range(len(entries)):
        entry = entries[i]
        row = f"{i + 1}," \
              f"{sanitize_for_csv(entry.metadata.original_master_metadata_track_name)}," \
              f"{sanitize_for_csv(entry.metadata.original_master_metadata_album_artist_name)}," \
              f"," # empty choice

        row_choices = ""
        for j in range(len(entry.metadata.tracks)):
            track = entry.metadata.tracks[j]
            score = str(round(getattr(track.match_score, score_by), 2))
            row_choices += f"{j + 1}. ({sanitize_for_csv(score)})" \
                f"{sanitize_for_csv(track.artist_name)} - " \
                f"{sanitize_for_csv(track.name)}\n"

        row += f"\"{row_choices}\""

        report += f"{row}\n"

    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enrich Spotify streaming entries with metadata from Spotify API")
    parser.add_argument("--file", required=True, help="Input JSON file with Spotify streaming entries")
    parser.add_argument("--export", action="store_true", help="Specify in order to run an export job")
    parser.add_argument("--import", action="store_true", help="Specify in order to run an import job")
    args = parser.parse_args()

    # input parameters
    input_file = args.file
    do_import = getattr(args, "import");
    do_export = args.export
    
    # Get scoring settings
    score_tracks_by = os.getenv('SCORE_TRACKS_BY', 'equal_weight')
    
    if do_export:
        # Read Spotify entries
        entries = read_spotify_entries(input_file)
        
        if not entries:
            print_log("No entries to process")
            exit(1)
        
        # Build CSV with choices
        csv = build_choice_report_clear(entries, score_tracks_by)

        # Export to file
        export_to_csv(csv, input_file, suffix="validator")
    
    if do_import:
        # Read CSV file