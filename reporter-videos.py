import argparse
import json
import os
import csv
from typing import List, Dict, Tuple
from spotify.spotify_listening_history import SpotifyStreamingEntry
from utils.file_utils import export_to_csv, export_to_json, generate_output_filename, open_file
from utils.simple_logger import print_log
import subprocess
import platform


def read_video_entries(input_file: str) -> List[Dict]:
    """
    Read video entries from JSON file
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        return data
    
    except FileNotFoundError:
        print_log(f"Error: {input_file} not found")
        return []
    except json.JSONDecodeError:
        print_log(f"Error: Invalid JSON in {input_file}")
        return []
    except Exception as e:
        print_log(f"Error processing file: {e}")
        return []


def read_csv(input_file: str) -> List[List[str]]:
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
    """Sanitize text for CSV output"""
    if text is None:
        return ""
    return str(text).replace(",", " ").replace('"', "")


def get_unique_combinations(entries: List[Dict]) -> List[Dict]:
    """
    Extract unique (artist, title) combinations from video entries
    """
    unique_combinations = {}
    
    for entry in entries:
        # in order to match with CSV data, they need to be defined unique as exported in csv - e.g. no commas
        artist = sanitize_for_csv(entry.get('artist', ''))
        title = sanitize_for_csv(entry.get('title', ''))

        # Create a key for uniqueness
        key = (artist, title)
        
        # Only add if we haven't seen this combination before
        if key not in unique_combinations:
            unique_combinations[key] = {
                'original_title': entry.get('metadata', {}).get('original_title', ''),
                'original_channel': entry.get('metadata', {}).get('original_channel', ''),
                'title': title,
                'artist': artist,
                'new_title': title,  # Default to current title
                'new_artist': artist  # Default to current artist
            }
    
    return list(unique_combinations.values())


def build_video_report_csv(entries: List[Dict]) -> str:
    """
    Build a CSV report for unique video combinations
    """
    if not entries or len(entries) == 0:
        print_log("No entries available for building an output report file")
        return None
    
    # Get unique combinations
    unique_entries = get_unique_combinations(entries)
    
    if not unique_entries:
        print_log("No unique combinations found")
        return None
    
    print_log(f"Found {len(unique_entries)} unique (artist, title) combinations out of {len(entries)} total entries")
    
    report = ""
    
    # Add header
    header = "original_title,original_channel,title,artist,new_title,new_artist"
    report += f"{header}\n"
    
    # Add rows for unique combinations
    for entry in unique_entries:
        row = f'"{sanitize_for_csv(entry["original_title"])}","' \
              f'{sanitize_for_csv(entry["original_channel"])}","' \
              f'{sanitize_for_csv(entry["title"])}","' \
              f'{sanitize_for_csv(entry["artist"])}","' \
              f'{sanitize_for_csv(entry["new_title"])}","' \
              f'{sanitize_for_csv(entry["new_artist"])}"'
        
        report += f"{row}\n"
    
    return report


def apply_csv_changes(entries: List[Dict], csv_rows: List[List[str]]) -> List[Dict]:
    """
    Apply changes from CSV back to the original entries
    """
    if not csv_rows or len(csv_rows) < 2:  # At least header + 1 row
        print_log("No CSV data to process")
        return entries
    
    # Build a mapping from CSV data (skip header)
    artist_title_mapping = {}
    
    for row in csv_rows[1:]:  # Skip header
        if len(row) < 6:
            print_log(f"Invalid CSV row: {row}")
            exit(1)
        
        title = row[2]
        artist = row[3]
        new_title = row[4]
        new_artist = row[5]
        
        # Create mapping key using original artist and title
        key = (artist, title)
        artist_title_mapping[key] = {
            'new_title': new_title,
            'new_artist': new_artist
        }
    
    print_log(f"Built mapping for {len(artist_title_mapping)} combinations")
    
    # Apply changes to original entries
    updated_count = 0
    output_entries = [] # output only stuff found in CSV
    for entry in entries:
        # in order to match with CSV data, they need to be as exported in csv - e.g. no commas
        artist = sanitize_for_csv(entry.get('artist', '')) 
        title = sanitize_for_csv(entry.get('title', ''))
        key = (artist, title)
        
        if key in artist_title_mapping:
            mapping = artist_title_mapping[key]
            
            entry['artist'] = mapping['new_artist']
            entry['title'] = mapping['new_title']
            
            if artist != mapping['new_artist'] or title != mapping['new_title']:
                updated_count += 1
                print_log(f"Updated: '{artist} - {title}' -> '{mapping['new_artist']} - {mapping['new_title']}'")

            output_entries.append(entry)

    print_log(f"Applied changes to {updated_count} entries")
    return output_entries


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process video entries for artist/title corrections")
    parser.add_argument("--file", required=True, help="Input JSON file with video entries")
    parser.add_argument("--export", action="store_true", help="Export unique combinations to CSV")
    parser.add_argument("--import", action="store_true", help="Import corrections from CSV and apply to JSON")
    args = parser.parse_args()

    # Input parameters
    input_file = args.file
    do_import = getattr(args, "import")
    do_export = args.export
    
    entries = []
    
    if do_export:
        # Read video entries
        entries = read_video_entries(input_file)
        
        if not entries:
            print_log("No entries to process")
            exit(1)
        
        # Build CSV with unique combinations
        report = build_video_report_csv(entries)
        
        if report:
            # Export to file
            export_to_csv(report, input_file, suffix="validator")
            print_log("CSV export completed. You can now edit the 'new_title' and 'new_artist' columns.")
        else:
            print_log("Failed to generate report")
            exit(1)

    if do_import:
        # CSV file uses name convention <input-file>.validator.csv
        csv_file = generate_output_filename(input_file, suffix="validator", new_extension=".csv")

        # Open the CSV file in the default application
        open_file(csv_file)

        # Wait for user input to continue
        print("Please edit the 'new_title' and 'new_artist' columns in the validator CSV file.")
        print("Make sure to save the file after making your changes.")
        input("Press Enter to continue once you have finished editing...")
        
        # Read CSV file
        csv_rows = read_csv(csv_file)
        
        if not csv_rows:
            print_log("Failed to read CSV file")
            exit(1)

        # Read original JSON entries (if export was not done, read them now)
        if not do_export:
            entries = read_video_entries(input_file)
        
        if not entries:
            print_log("No entries to process")
            exit(1)
        
        # Apply CSV changes to entries
        updated_entries = apply_csv_changes(entries, csv_rows)

        # Save updated entries back to JSON
        export_to_json(updated_entries, input_file, suffix="reviewed")

        print_log(f"Processing complete. {len(updated_entries)} entries processed.")
