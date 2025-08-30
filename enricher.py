import argparse
from ast import List
import json
import os
from time import time

from dotenv import load_dotenv
from spotify.constants import DEFAULT_SLEEP_SECONDS
from spotify.spotify_client import SpotifyClient
from spotify.spotify_listening_history import SpotifyAdditionalYTMData, SpotifyStreamingEntry
from utils.json_exporter import export_to_json


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
        print(f"Error: {input_file} not found")
        return []
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {input_file}")
        return []
    except Exception as e:
        print(f"Error processing file: {e}")
        return []


def enrich_spotify_entries(entries: List[SpotifyStreamingEntry], enricher: SpotifyClient) -> List[SpotifyStreamingEntry]:
    """
    Enrich Spotify entries with metadata from Spotify API
    """
    total_entries = len(entries)
    enriched_count = 0
    failed_count = 0
    
    print(f"Starting enrichment of {total_entries} entries...")
    
    for i, entry in enumerate(entries):
        # Skip if already has Spotify track URI
        if entry.spotify_track_uri and entry.spotify_track_uri.startswith('spotify:track:'):
            print(f"Entry {i+1}/{total_entries}: Already has Spotify URI - skipping")
            continue
            
        # Skip if missing required fields
        if not entry.master_metadata_track_name or not entry.master_metadata_album_artist_name:
            print(f"Entry {i+1}/{total_entries}: Missing track name or artist - skipping")
            failed_count += 1
            continue
        
        print(f"Entry {i+1}/{total_entries}: Searching for '{entry.master_metadata_track_name}' by '{entry.master_metadata_album_artist_name}'")
        
        # Search for track
        track_info = enricher.search_track(entry.master_metadata_track_name, entry.master_metadata_album_artist_name)
        
        if track_info:
            print(f"  ✓ Found: {track_info['name']} from album '{track_info['album_name']}' with duration '{track_info['duration_ms']}'")
            
            # Update entry with found information
            entry.spotify_track_uri = f"spotify:track:{track_info['id']}"
            entry.master_metadata_album_album_name = track_info['album_name']
            entry.ms_played = track_info['duration_ms']  # Use actual duration instead of estimated
            
            enriched_count += 1
        else:
            print(f"  ✗ Not found on Spotify")
            failed_count += 1
        
        # Add delay to respect rate limits
        time.sleep(DEFAULT_SLEEP_SECONDS)
    
    print(f"\nEnrichment complete:")
    print(f"  Successfully enriched: {enriched_count}")
    print(f"  Failed to find: {failed_count}")
    print(f"  Already had data: {total_entries - enriched_count - failed_count}")
    
    return entries

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
    
    # Initialize Spotify enricher
    enricher = SpotifyClient(client_id, client_secret)
    
    # Read Spotify entries
    entries = read_spotify_entries(input_file)
    
    if not entries:
        print("No entries to process")
        exit(1)
    
    # Enrich entries with Spotify metadata
    enriched_entries = enrich_spotify_entries(entries, enricher)
    
    # Export enriched data
    export_to_json(enriched_entries, input_file, "enriched")

    print("Enrichment process complete!")