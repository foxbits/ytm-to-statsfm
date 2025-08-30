import argparse
import json
import os
from typing import List

from dotenv import load_dotenv
from objects.spotify_processed_track import SpotifyProcessedTracks
from spotify.spotify_client import SpotifyClient
from spotify.spotify_listening_history import SpotifyStreamingEntry
from utils.file_utils import export_to_csv, export_to_json
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


def enrich_spotify_entries(entries: List[SpotifyStreamingEntry], enricher: SpotifyClient) -> SpotifyProcessedTracks:
    """
    Enrich Spotify entries with metadata from Spotify API
    """
    total_entries = len(entries)
    output = SpotifyProcessedTracks(processed=[], skipped=[], errors=[], logs=[])

    print_log(f"Starting enrichment of {total_entries} entries...")
    
    for i, entry in enumerate(entries):
        # build csv status row
        row_log = f"{entry.master_metadata_track_name.replace(',', ' ')},{entry.master_metadata_album_artist_name.replace(',', ' ')}"

        # Skip if already has Spotify track URI
        if entry.spotify_track_uri and entry.spotify_track_uri.startswith('spotify:track:'):
            print_log(f"Entry {i+1}/{total_entries}: Already has Spotify URI - skipping")
            output.skipped.append(entry)
            row_log += f",{entry.master_metadata_track_name.replace(',', ' ')},{entry.master_metadata_album_artist_name.replace(',', ' ')},{entry.spotify_track_uri},{entry.ms_played},{entry.master_metadata_album_album_name},skipped,Track already has a Spotify URI"
            continue
            
        # Skip if missing required fields
        if not entry.master_metadata_track_name or not entry.master_metadata_album_artist_name:
            print_log(f"Entry {i+1}/{total_entries}: Missing track name or artist - skipping")
            output.errors.append(entry)
            row_log += f",,,,{entry.ms_played},,error,Missing track name or artist, cannot do search"
            continue

        print_log(f"Entry {i+1}/{total_entries}: Searching for '{entry.master_metadata_track_name}' by '{entry.master_metadata_album_artist_name}'")

        # Search for track (catches not found / rate limiting / unknown ex)
        try:
            track_info = enricher.search_track(entry.master_metadata_track_name, entry.master_metadata_album_artist_name)
            
            if track_info:
                print_log(f"  ✓ Found: {track_info.name} from album '{track_info.album_name}' with duration '{track_info.duration_ms}'")

                # Update entry with found information (including artist + name)
                entry.master_metadata_track_name = track_info.name
                entry.master_metadata_album_artist_name = track_info.artist_name
                entry.master_metadata_album_album_name = track_info.album_name
                entry.ms_played = track_info.duration_ms  # Use actual duration instead of estimated
                entry.spotify_track_uri = track_info.uri

                output.processed.append(entry)
                row_log += f",{entry.master_metadata_track_name.replace(',', ' ')},{entry.master_metadata_album_artist_name.replace(',', ' ')},{entry.spotify_track_uri},{entry.ms_played},{entry.master_metadata_album_album_name.replace(',', ' ')},ok,OK"

            else:
                print_log(f"  ✗ Not found on Spotify")
                raise Exception("Track not found")
        except Exception as e:
            print_log(f"Error enriching entry {i+1}/{total_entries}: {e}")
            output.errors.append(entry)
            row_log += f",,{entry.ms_played},,error,{e}"

        output.logs.append(row_log)

    print_log(f"\nEnrichment complete:")
    print_log(f"  Successfully enriched: {len(output.processed)}")
    print_log(f"  Failed to find: {len(output.errors)}")
    print_log(f"  Already had data: {len(output.skipped)}")

    return output

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enrich Spotify streaming entries with metadata from Spotify API")
    parser.add_argument("--file", required=True, help="Input JSON file with Spotify streaming entries")
    args = parser.parse_args()

    # input file
    input_file = args.file
    
    # Load environment variables
    load_dotenv()
    
    # Get Spotify API credentials
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    market = os.getenv('CONN_COUNTRY')

    # Initialize Spotify enricher
    enricher = SpotifyClient(client_id, client_secret, market)

    # Read Spotify entries
    entries = read_spotify_entries(input_file)
    
    if not entries:
        print_log("No entries to process")
        exit(1)
    
    # Enrich entries with Spotify metadata
    processed_entries = enrich_spotify_entries(entries, enricher)
    
    # Export enriched data
    export_to_json(processed_entries.processed, input_file, "enricher-ok")
    export_to_json(processed_entries.skipped, input_file, "enricher-skipped")
    export_to_json(processed_entries.errors, input_file, "enricher-errors")

    # export csv log
    header_row = "initial_master_metadata_track_name,initial_master_metadata_album_artist_name,master_metadata_track_name,master_metadata_album_artist_name,spotify_track_uri,ms_played,master_metadata_album_name,status,message"
    export_to_csv(processed_entries.logs, header_row, input_file, "enricher-log")

    print_log("Enrichment process complete!")