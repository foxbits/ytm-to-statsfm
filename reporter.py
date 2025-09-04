import argparse
import json
import os
import csv
from typing import List
from objects.process_metadata import ProcessingStatus
from spotify.spotify_listening_history import SpotifyStreamingEntry
from utils.file_utils import export_to_csv, export_to_json, generate_output_filename
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
    
def read_csv(input_file: str) -> List[str]:
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            return [row for row in reader if row and any(cell.strip() for cell in row)]
    except FileNotFoundError:
        print_log(f"Error: {input_file} not found")
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

def import_choices(entries: List[SpotifyStreamingEntry], choices: List[str]) -> List[SpotifyStreamingEntry]:
    if len(choices) != len(entries) + 1:  # +1 for header
        print_log(f"Error: Expected {len(entries) + 1} choices, got {len(choices)}")
        return []

    output_entries = []

    for i in range(len(entries)):
        entry = entries[i]
        choice_row = choices[i + 1]  # Skip header
        try:
            choice = int(choice_row[3])
            if choice != -1 and (choice < 1 or choice > len(entry.metadata.tracks)):
                raise ValueError(f"Choice out of range")
        except (ValueError, IndexError):
            print_log(f"Error: Invalid choice in row {i + 1}: '{choice_row[3]}'. Make sure it's a valid track number")
            exit(1)
        
        if choice  == -1:
            print_log(f"Row {i + 1} was marked as no valid choices. It will be skipped.")
            continue

        entry.set_status_as_matched(ProcessingStatus.FIXED, choice - 1)
        entry.set_info_from_track(choice - 1)
        output_entries.append(entry)

    return output_entries


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

    entries = []
    
    if do_export:
        # Read Spotify entries
        entries = read_spotify_entries(input_file)
        
        if not entries:
            print_log("No entries to process")
            exit(1)
        
        # Build CSV with choices
        report = build_choice_report_clear(entries, score_tracks_by)

        # Export to file
        export_to_csv(report, input_file, suffix="validator")

    # Wait for user input to continue
    print("Please make sure you have filled the choices in the 'validator' CSV.\n"
          "(make sure that both the original json and the CSV are in the same folder)")
    input("Press Enter to continue once that is done...")

    if do_import:
        # csv file uses name convention <input-file>.validator.csv
        csv_file = generate_output_filename(input_file, suffix="validator", new_extension=".csv")

        # Read CSV file
        rows = read_csv(csv_file)

        # Read json original entries (if export done, they are already read)
        if not do_export:
            entries = read_spotify_entries(input_file)
        
        # import the choices (with range validation)
        output_entries = import_choices(entries, rows)

        # save back to json
        export_to_json(output_entries, input_file, suffix="validated")

