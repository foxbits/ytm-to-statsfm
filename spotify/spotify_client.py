import random
from time import time
from typing import Optional, Dict
from spotify.constants import DEFAULT_BASE_BACKOFF_SECONDS, DEFAULT_MAX_RETRIES, DEFAULT_MIN_INTERVAL_SECONDS
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.exceptions import SpotifyException

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

        # Local cache to avoid duplicate API calls
        self.cache = {}

        # Rate limiting variables
        self.last_request_time = 0
        self.min_request_interval = DEFAULT_MIN_INTERVAL_SECONDS  # Start with 100ms between requests
        self.max_retries = DEFAULT_MAX_RETRIES
        self.base_backoff = DEFAULT_BASE_BACKOFF_SECONDS  # Base backoff time in seconds

    def _adaptive_delay(self):
        """
        Implement adaptive delay between requests
        """
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()

    def _handle_rate_limit(self, retry_after: int = None, attempt: int = 0):
        """
        Handle rate limiting with exponential backoff
        """
        if retry_after:
            # Use the Retry-After header if provided
            sleep_time = retry_after + random.uniform(0.1, 0.5)  # Add small jitter
            print(f"Rate limited. Waiting {sleep_time:.1f} seconds...")
        else:
            # Exponential backoff with jitter
            sleep_time = (self.base_backoff * (2 ** attempt)) + random.uniform(0.1, 1.0)
            print(f"Rate limited. Backing off for {sleep_time:.1f} seconds...")
        
        time.sleep(sleep_time)
        
        # Increase minimum interval to be more conservative
        self.min_request_interval = min(self.min_request_interval * 1.5, 2.0)

    def _make_spotify_request(self, request_func, *args, **kwargs):
        """
        Make a Spotify API request with rate limiting and retry logic
        """
        for attempt in range(self.max_retries):
            try:
                # Apply adaptive delay
                self._adaptive_delay()
                
                # Make the request
                result = request_func(*args, **kwargs)
                
                # If successful, gradually reduce the request interval
                self.min_request_interval = max(self.min_request_interval * 0.95, 0.1)
                
                return result
                
            except SpotifyException as e:
                if e.http_status == 429:  # Too Many Requests
                    if attempt < self.max_retries - 1:
                        # Extract Retry-After header if available
                        retry_after = None
                        if hasattr(e, 'headers') and 'Retry-After' in e.headers:
                            retry_after = int(e.headers['Retry-After'])
                        
                        self._handle_rate_limit(retry_after, attempt)
                        continue
                    else:
                        print(f"Max retries exceeded for rate limiting")
                        raise Exception(f"Max retries ({self.max_retries}) exceeded due to rate limiting")
                else:
                    print(f"Unknown Spotify API error: {e}")
                    raise e
            except Exception as e:
                print(f"Unexpected error: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.base_backoff * (2 ** attempt))
                    continue
                raise e
        
        return None
    
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
            
            # Search on Spotify with rate limiting
            results = self._make_spotify_request(
                self.spotify.search, 
                q=query, 
                type='track', 
                limit=1
            )
            
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
                # Try a broader search if exact match fails (with rate limiting)
                query = f"{track_name} {artist_name}"
                results = self._make_spotify_request(
                    self.spotify.search,
                    q=query,
                    type='track',
                    limit=1
                )

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
