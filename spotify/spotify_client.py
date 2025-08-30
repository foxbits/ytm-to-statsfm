from typing import Optional, Dict
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotify.spotify_listening_history import SpotifyStreamingEntry

class SpotifyClient:
    def __init__(self, client_id: str, client_secret: str):
        """
        Initialize Spotify API client
        """
        
        if not client_id or not client_secret:
            print("Error: SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set in .env file")
            print("Get your credentials from: https://developer.spotify.com/dashboard/applications")
            exit(1)
        
        client_credentials_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )

        self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

        self.cache = {}  # Local cache to avoid duplicate API calls
  
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
