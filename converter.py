import json
import argparse
import os
from typing import List
from dotenv import load_dotenv
from spotify.spotify_listening_history import SpotifyAdditionalYTMData, SpotifyStreamingEntry
from objects.ytm_processed_track import YTMProcessedTrack
from utils.json_exporter import export_to_json

def convert_ytm_to_spotify_format(input_file: str) -> List[SpotifyStreamingEntry]:
    """
    Read YTM processed tracks from JSON file and convert to Spotify streaming format
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
            ytm_tracks = [YTMProcessedTrack.from_dict(item) for item in data]

        # load additional data from environment
        additional_data = SpotifyAdditionalYTMData()
        additional_data.ms_played = int(os.getenv('MS_PLAYED'))
        additional_data.conn_country = os.getenv('CONN_COUNTRY')
        additional_data.platform = os.getenv('PLATFORM')
        additional_data.ip_addr = os.getenv('IP_ADDR')

        # Convert to Spotify format
        spotify_entries = []
        for ytm_track in ytm_tracks:
            spotify_entry = SpotifyStreamingEntry.from_ytm_track(ytm_track, additional_data)
            spotify_entries.append(spotify_entry)
        
        return spotify_entries
    
    except FileNotFoundError:
        print(f"Error: {input_file} not found")
        return []
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {input_file}")
        return []
    except Exception as e:
        print(f"Error processing file: {e}")
        return []

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert YTM processed tracks to Spotify streaming format")
    parser.add_argument("--file", required=True, help="Input JSON file with YTM processed tracks")
    args = parser.parse_args()
    
    input_file = args.file

    # load env variables from .env file
    load_dotenv()
    
    # Convert YTM tracks to Spotify format
    spotify_entries = convert_ytm_to_spotify_format(input_file)
    
    if spotify_entries:
        print(f"Successfully converted {len(spotify_entries)} YTM tracks to Spotify format")
        export_to_json(spotify_entries, input_file, "spotify-format")
        print("Conversion complete")
    else:
        print("No tracks converted or error occurred")
