import argparse
import json
import os
from typing import List

from dotenv import load_dotenv
from objects.process_metadata import ProcessingStatus
from objects.spotify_processed_track import SpotifyProcessedTracks
from spotify.spotify_client import SpotifyClient
from spotify.spotify_listening_history import SpotifyStreamingEntry
from utils.file_utils import export_to_json
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


def enrich_spotify_entries(entries: List[SpotifyStreamingEntry], spoticlient: SpotifyClient) -> SpotifyProcessedTracks:
    """
    Enrich Spotify entries with metadata from Spotify API
    """
    total_entries = len(entries)
    output = SpotifyProcessedTracks(processed=[], errors=[])

    print_log(f"Starting enrichment of {total_entries} entries...")
    
    for i, entry in enumerate(entries):

        # Skip if already has Spotify track URI
        if entry.has_spotify_data():
            message = "Already has Spotify Data - skipping any API calls"
            print_log(f"Entry {i+1}/{total_entries}: {message}")
            entry.metadata.status = ProcessingStatus.SKIPPED
            entry.metadata.status_message = message
            output.processed.append(entry)
            continue

        try:
            
            # Skip if missing required fields
            if not entry.has_basic_info():
                raise Exception("Missing track name or artist - skipping")

            # Search for track (catches not found / rate limiting / unknown ex)
            print_log(f"Entry {i+1}/{total_entries}: Searching for '{entry.master_metadata_track_name}' by '{entry.master_metadata_album_artist_name}'")

            # Call Spotify Client 
            tracks = spoticlient.search_track(entry.master_metadata_track_name, entry.master_metadata_album_artist_name)
            
            if len(tracks) > 0:
                print_log(f"Entry {i+1}/{total_entries}:  ✓ Found {len(tracks)} tracks. First: {tracks[0].name} from album '{tracks[0].album_name}' with duration '{tracks[0].duration_ms}'")
                entry.metadata.tracks = tracks
                output.processed.append(entry)

            else:
                raise Exception("  ✗ Track not found")
        except Exception as e:
            print_log(f"Entry {i+1}/{total_entries}: Error - {e}")
            entry.metadata.status = ProcessingStatus.ERROR
            entry.metadata.status_message = str(e)
            output.errors.append(entry)

    print_log(f"\nEnrichment complete:")
    print_log(f"  Successfully enriched / have data: {len(output.processed)}")
    print_log(f"  Failed to find: {len(output.errors)}")

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
    search_results_limit = os.getenv('SPOTIFY_SEARCH_RESULTS_LIMIT', 5)
    max_retries = os.getenv('SPOTIFY_MAX_RETRIES', 10)

    # Initialize Spotify enricher
    spoticlient = SpotifyClient(client_id, client_secret, market, search_results_limit, max_retries)

    # Read Spotify entries
    entries = read_spotify_entries(input_file)
    
    if not entries:
        print_log("No entries to process")
        exit(1)
    
    # Enrich entries with Spotify metadata
    processed_entries = enrich_spotify_entries(entries, spoticlient)
    
    # Export enriched data
    export_to_json(processed_entries.processed, input_file, "enriched-ok")
    export_to_json(processed_entries.errors, input_file, "enriched-errors")

    print_log("Enrichment process complete!")