import argparse
import json
import os
import csv
from typing import List
from objects.process_metadata import ProcessingStatus
from spotify.spotify_listening_history import SpotifyStreamingEntry
from utils.file_utils import export_to_csv, export_to_json, generate_output_filename, open_file
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
    header = "original_track," \
    "original_artist," \
    "your_choice," \
    "choices"

    report += f"{header}\n"

    # Store unique combos
    unique_combinations = {}

    # Add rows
    for i in range(len(entries)):
        entry = entries[i]
        
        # in order to match with CSV data, they need to be defined unique as exported in csv - e.g. no commas
        artist = sanitize_for_csv(entry.metadata.original_master_metadata_album_artist_name)
        title = sanitize_for_csv(entry.metadata.original_master_metadata_track_name)
        
        # Create a key for uniqueness
        key = (artist, title)

        if key in unique_combinations:
            print_log(f"Marking duplicate entry for report: [{title}][{artist}]")
            continue

        unique_combinations[key] = entry

        row = f"{title}," \
              f"{artist}," \
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

def import_choices(entries: List[SpotifyStreamingEntry], choices: List[str]) -> tuple[List[SpotifyStreamingEntry], List[SpotifyStreamingEntry]]:
    """
    Process user choices for Spotify streaming entries and categorize them.
    Args:
        entries (List[SpotifyStreamingEntry]): List of streaming entries to process
        choices (List[str]): List of user choices, where each choice contains track selection data.
                           Expected to have header row + one row per entry.
                           Choice value should be in index 3 of each row.
    Returns:
        tuple[List[SpotifyStreamingEntry], List[SpotifyStreamingEntry]]: 
            - First item: output_entries - Successfully matched entries with valid choices
            - Second item: invalid_entries - Entries that were skipped due to marked as invalid (choice = -1 / unmatched)
    Raises:
        SystemExit: If invalid choices are found (non-integer, out of range, or malformed data)
    Notes:
        - Choice value of -1 indicates no valid match and entry will be skipped
        - Choice values must be between 1 and the number of available tracks for the entry
        - Function modifies the status and metadata of processed entries
    """

    # Map CSV choices to (artist, title) entries
    artist_title_map = {}
    for i in range(1, len(choices)):  # Skip header
        choice_row = choices[i]
        title = choice_row[0]
        artist = choice_row[1]
        
        try:
            choice = int(choice_row[2])
        except (ValueError, IndexError):
            print_log(f"Error: Invalid choice in row {i + 1}: '{choice_row[2]}'. Make sure it's a valid track number")
            exit(1)
        
        artist_title_map[(artist, title)] = {
            "choice": choice
        }

    # Process JSON entries and process based on CSV choices
    output_entries = []
    invalid_entries = []

    for i in range(len(entries)):
        entry = entries[i]

        # in order to match with CSV data, they need to be defined unique as exported in csv - e.g. no commas
        artist = sanitize_for_csv(entry.metadata.original_master_metadata_album_artist_name)
        title = sanitize_for_csv(entry.metadata.original_master_metadata_track_name)

        # Create a key for uniqueness
        key = (artist, title)

        # Read choice from CSV mapping
        choice = -1
        if key in artist_title_map:
            choice = artist_title_map[key]["choice"]

        if choice  == -1:
            print_log(f"Row {i + 1} was marked as no valid choices. It will be skipped.")
            entry.set_status_as_unmatched()
            invalid_entries.append(entry)
            continue

        if choice < 1 or choice > len(entry.metadata.tracks):
            print_log(f"Error: Choice {choice} in row {i + 1} is out of range (1-{len(entry.metadata.tracks)})")
            exit(1)

        entry.set_status_as_matched(ProcessingStatus.FIXED, choice - 1)
        entry.set_info_from_track(choice - 1)
        output_entries.append(entry)

    return output_entries, invalid_entries


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enrich Spotify streaming entries with metadata from Spotify API")
    parser.add_argument("--file", required=True, help="Input JSON file with Spotify streaming entries")
    parser.add_argument("--export", action="store_true", help="Specify in order to run an export job")
    parser.add_argument("--import", action="store_true", help="Specify in order to run an import job")
    args = parser.parse_args()

    # input parameters
    input_file = args.file
    do_import = getattr(args, "import")
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

    if do_import:
        # csv file uses name convention <input-file>.validator.csv
        csv_file = generate_output_filename(input_file, suffix="validator", new_extension=".csv")

        # Open the CSV file in the default application
        open_file(csv_file)

        # Wait for user input to continue
        print("Please make sure you have filled the choices in the 'validator' CSV.\n"
            "(make sure that both the original json and the CSV are in the same folder)")
        input("Press Enter to continue once that is done...")
        
        # Read CSV file
        rows = read_csv(csv_file)

        # Read json original entries (if export done, they are already read)
        if not do_export:
            entries = read_spotify_entries(input_file)
        
        # import the choices (with range validation)
        output_entries, invalid_entries = import_choices(entries, rows)

        # save back to json
        export_to_json(output_entries, input_file, suffix="validated", parent_directory="output\\ok")
        export_to_json(invalid_entries, input_file, suffix="invalid", parent_directory="output\\errors")

