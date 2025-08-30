import json
import os
import argparse
import time
from typing import List, Optional, Dict
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from objects.spotify_listening_history import SpotifyStreamingEntry, SpotifyAdditionalYTMData

class SpotifyEnricher:
    def __init__(self, client_id: str, client_secret: str):
        """
        Initialize Spotify API client
        """
        client_credentials_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        self.cache = {}  # Cache to avoid duplicate API calls
        
    def search_track(self, track_name: str, artist_name: str) -> Optional[Dict]:
        """
        Search for track on Spotify API
        """
        # Create cache key
        cache_key = f"{track_name.lower()}||{artist_name.lower()}"
        
        # Check cache first
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # Clean search query
            query = f'track:"{track_name}" artist:"{artist_name}"'
            
            # Search on Spotify
            results = self.spotify.search(q=query, type='track', limit=1)
            
            if results['tracks']['items']:
                track = results['tracks']['items'][0]
                track_info = {
                    'id': track['id'],
                    'name': track['name'],
                    'album_name': track['album']['name'],
                    'duration_ms': track['duration_ms'],
                    'artist_name': track['artists'][0]['name'] if track['artists'] else artist_name
                }
                
                # Cache the result
                self.cache[cache_key] = track_info
                return track_info
            else:
                # Try a broader search if exact match fails
                query = f"{track_name} {artist_name}"
                results = self.spotify.search(q=query, type='track', limit=1)
                
                if results['tracks']['items']:
                    track = results['tracks']['items'][0]
                    track_info = {
                        'id': track['id'],
                        'name': track['name'],
                        'album_name': track['album']['name'],
                        'duration_ms': track['duration_ms'],
                        'artist_name': track['artists'][0]['name'] if track['artists'] else artist_name
                    }
                    
                    # Cache the result
                    self.cache[cache_key] = track_info
                    return track_info
                else:
                    # Cache negative result
                    self.cache[cache_key] = None
                    return None
                    
        except Exception as e:
            print(f"Error searching for track '{track_name}' by '{artist_name}': {e}")
            # Cache negative result to avoid retrying
            self.cache[cache_key] = None
            return None

def read_spotify_entries(input_file: str) -> List[SpotifyStreamingEntry]:
    """
    Read Spotify streaming entries from JSON file
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # Convert JSON data to SpotifyStreamingEntry objects
        entries = []
        for item in data:
            # Create entry directly from dict
            entry = SpotifyStreamingEntry(
                timestamp_iso=item.get('ts', ''),
                track_name=item.get('master_metadata_track_name', ''),
                artist=item.get('master_metadata_album_artist_name', ''),
                timestamp_unix=item.get('offline_timestamp', 0),
                additional_data=SpotifyAdditionalYTMData(
                    ms_played=item.get('ms_played', 0),
                    conn_country=item.get('conn_country', ''),
                    platform=item.get('platform', ''),
                    ip_addr=item.get('ip_addr', '')
                )
            )
            
            # Set existing spotify_track_uri and album name if available
            entry.spotify_track_uri = item.get('spotify_track_uri', '')
            entry.master_metadata_album_album_name = item.get('master_metadata_album_album_name', '')
            
            entries.append(entry)
        
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

def enrich_spotify_entries(entries: List[SpotifyStreamingEntry], enricher: SpotifyEnricher) -> List[SpotifyStreamingEntry]:
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
            # Update entry with found information
            entry.spotify_track_uri = f"spotify:track:{track_info['id']}"
            entry.master_metadata_album_album_name = track_info['album_name']
            entry.ms_played = track_info['duration_ms']  # Use actual duration instead of estimated
            
            print(f"  ✓ Found: {track_info['name']} from album '{track_info['album_name']}'")
            enriched_count += 1
        else:
            print(f"  ✗ Not found on Spotify")
            failed_count += 1
        
        # Add delay to respect rate limits
        time.sleep(0.1)
    
    print(f"\nEnrichment complete:")
    print(f"  Successfully enriched: {enriched_count}")
    print(f"  Failed to find: {failed_count}")
    print(f"  Already had data: {total_entries - enriched_count - failed_count}")
    
    return entries

def export_enriched_entries(entries: List[SpotifyStreamingEntry], input_filename: str) -> str:
    """
    Export enriched Spotify streaming entries to JSON file
    """
    # Create output filename
    base_name = os.path.splitext(input_filename)[0]
    extension = os.path.splitext(input_filename)[1]
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{base_name}-enriched{extension}")
    
    try:
        # Convert objects to dictionaries for JSON serialization
        json_data = [entry.to_dict() for entry in entries]
        
        # Write to output file
        with open(output_file, 'w', encoding='utf-8') as output:
            json.dump(json_data, output, indent=2, ensure_ascii=False)
        
        print(f"Enriched data written to: {output_file}")
        return output_file
    
    except Exception as e:
        print(f"Error writing to {output_file}: {e}")
        return ""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enrich Spotify streaming entries with metadata from Spotify API")
    parser.add_argument("--file", required=True, help="Input JSON file with Spotify streaming entries")
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Get Spotify API credentials
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("Error: SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set in .env file")
        print("Get your credentials from: https://developer.spotify.com/dashboard/applications")
        exit(1)
    
    input_file = args.file
    
    # Initialize Spotify enricher
    enricher = SpotifyEnricher(client_id, client_secret)
    
    # Read Spotify entries
    entries = read_spotify_entries(input_file)
    
    if not entries:
        print("No entries to process")
        exit(1)
    
    # Enrich entries with Spotify metadata
    enriched_entries = enrich_spotify_entries(entries, enricher)
    
    # Export enriched data
    export_enriched_entries(enriched_entries, input_file)
    
    print("Enrichment process complete!")
