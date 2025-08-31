import argparse
import json
from typing import List
from dotenv import load_dotenv
from rapidfuzz import fuzz

from objects.score_metadata import MatchScore
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


def calculate_track_similarity(original_track: str, original_artist: str, 
                             found_track: str, found_artist: str) -> MatchScore:
    """
    Calculate similarity between original and found track/artist combination
    Returns detailed similarity scores
    """
    track_score = fuzz.token_set_ratio(original_track.lower(), found_track.lower())
    artist_score = fuzz.token_set_ratio(original_artist.lower(), found_artist.lower())
    
    # Different weighting strategies
    equal_weight = (track_score + artist_score) / 2
    track_heavy = (track_score * 0.7) + (artist_score * 0.3)
    artist_heavy = (track_score * 0.3) + (artist_score * 0.7)

    return MatchScore(
        track_score=track_score,
        artist_score=artist_score,
        equal_weight=equal_weight,
        track_heavy=track_heavy,
        artist_heavy=artist_heavy,
        min_score=min(track_score, artist_score),  # Both must be decent
        max_score=max(track_score, artist_score)   # At least one must be good
    )

def score_spotify_entries(tracks: List[SpotifyStreamingEntry], score_by: str):
    """
    Match original track artist and title with found entries in spotify and calculate similarity scores.
    If the tracks are marked as exact_search_match, it does nothing, only marks them with 100% score.
    Otherwise it does fuzzy matching and orders them by score
    
    Args:
        tracks (List[SpotifyStreamingEntry]): List of Spotify streaming entries containing
            original track metadata and potential matches to score.
        score_by (str): The scoring method to use for ranking matches: track_score, artist_score, equal_weight, track_heavy, artist_heavy, min_score, max_score
    """
    if not tracks:
        print_log("No entries to process")
        return
    
    for track in tracks:
        for match in track.metadata.tracks:
            if match.exact_search_match:
                match.match_score = MatchScore.max_score()
            else:
                match.match_score = calculate_track_similarity(
                    track.master_metadata_track_name,
                    track.master_metadata_album_artist_name,
                    match.name,
                    match.artist_name
            )
        
        # Sort tracks by best match score (using equal_weight as default)
        track.metadata.tracks.sort(key=lambda x: getattr(x.match_score, score_by), reverse=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enrich Spotify streaming entries with metadata from Spotify API")
    parser.add_argument("--file", required=True, help="Input JSON file with Spotify streaming entries")
    args = parser.parse_args()

    # input file
    input_file = args.file
    
    # Load environment variables
    load_dotenv()
    
    # Read Spotify entries
    entries = read_spotify_entries(input_file)

    # Process scores
    score_spotify_entries(entries)

    # Export scores to json
    export_to_json(entries, input_file, "scored")