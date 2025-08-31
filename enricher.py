import argparse
import json
import os
from typing import List

from dotenv import load_dotenv
from matcher import score_spotify_entries
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
    output = SpotifyProcessedTracks(processed=[], doubt=[], errors=[])

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

    # Get Spotify API calls settings
    search_results_limit = int(os.getenv('SPOTIFY_SEARCH_RESULTS_LIMIT', 5))
    max_retries = int(os.getenv('SPOTIFY_MAX_RETRIES', 10))

    # Get scoring settings
    score_tracks_by = os.getenv('SCORE_TRACKS_BY', 'equal_weight')
    minimum_match_decision_score = float(os.getenv('MINIMUM_MATCH_DECISION_SCORE', 0.9)) * 100

    # Initialize Spotify enricher
    spoticlient = SpotifyClient(client_id, client_secret, market, search_results_limit, max_retries)

    # Read Spotify entries
    entries = read_spotify_entries(input_file)
    
    if not entries:
        print_log("No entries to process")
        exit(1)
    
    # Enrich entries with Spotify metadata
    processed_entries = enrich_spotify_entries(entries, spoticlient)

    # Assign scores to tracks and sort by score
    score_spotify_entries(processed_entries.processed, score_tracks_by)

    # split into sure scores and scores in doubt
    matched = []
    doubt = []
    for entry in processed_entries.processed:
        entry.metadata.match_score = getattr(entry.metadata.tracks[0].match_score, score_tracks_by)

        if entry.metadata.tracks and entry.metadata.match_score >= minimum_match_decision_score:
            # set metadata as matched
            entry.metadata.status = ProcessingStatus.OK
            entry.metadata.status_message = f"Trusted match with score {entry.metadata.match_score:.2f}"
            if entry.metadata.tracks[0].exact_search_match:
                entry.metadata.status_message += " (exact API search match, not calculated)"

            # save new track details
            entry.spotify_track_uri = entry.metadata.tracks[0].uri
            entry.ms_played = entry.metadata.tracks[0].duration_ms

            # replace track details and save original
            entry.metadata.original_master_metadata_track_name = entry.master_metadata_track_name
            entry.metadata.original_master_metadata_album_artist_name = entry.master_metadata_album_artist_name

            entry.master_metadata_track_name = entry.metadata.tracks[0].name
            entry.master_metadata_album_artist_name = entry.metadata.tracks[0].artist_name
            entry.master_metadata_album_album_name = entry.metadata.tracks[0].album_name

            matched.append(entry)
        else:
            entry.metadata.status = ProcessingStatus.DOUBT
            entry.metadata.status_message = f"In doubt - score {entry.metadata.match_score:.2f} - needs review"
            doubt.append(entry)

    # Export enriched data
    export_to_json(matched, input_file, "enricher.matched")
    export_to_json(doubt, input_file, "enricher.doubt")
    export_to_json(processed_entries.errors, input_file, "enricher.errors")

    print_log("Enrichment process complete!")