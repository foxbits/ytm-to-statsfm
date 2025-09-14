import random
import time
from typing import List
from spotify.constants import DEFAULT_BASE_BACKOFF_SECONDS, DEFAULT_MIN_INTERVAL_SECONDS
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.exceptions import SpotifyException
from spotify.spotify_responses import TrackInfo
from utils.simple_logger import print_log

class SpotifyClient:
    def __init__(self, client_id: str, client_secret: str, market: str, search_results_limit: int, max_retries: int):
        """
        Initialize Spotify API client
        """
        if not client_id or not client_secret or not market:
            print_log("Error: SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, and CONN_COUNTRY must be set in .env file")
            print_log("Get your credentials from: https://developer.spotify.com/dashboard/applications")
            exit(1)
        
        client_credentials_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )

        self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        self.market = market
        self.search_results_limit = search_results_limit

        # Local cache to avoid duplicate API calls
        self.cache = {}

        # Rate limiting variables
        self.last_request_time = 0
        self.min_request_interval = DEFAULT_MIN_INTERVAL_SECONDS  # Start with 100ms between requests
        self.max_retries = max_retries
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
            print_log(f"Rate limited. Waiting Spotify's recommended {sleep_time:.1f} seconds...")
        else:
            # Exponential backoff with jitter
            sleep_time = (self.base_backoff * (2 ** attempt)) + random.uniform(0.1, 1.0)
            print_log(f"Rate limited. Backing off for {sleep_time:.1f} seconds...")

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
                        print_log(f"Max retries exceeded for rate limiting")
                        raise Exception(f"Max retries ({self.max_retries}) exceeded due to rate limiting")
                else:
                    print_log(f"Unknown Spotify API error: {e}")
                    raise e
            except Exception as e:
                print_log(f"Unexpected error: {e} (will not retry!)")
                raise e
        
        return None
    
    def search_track(self, track_name: str, artist_name: str) -> List[TrackInfo]:
        """
        Search for track on Spotify API.
        First tries to search by exact artist and track match. 
        If the API returns a result, it marks the resulted tracks as exact_search_match and returns them.
        In this case it is kindof safe to use the first result.
        Otherwise it falls back to a broader search and  returns the first search_results_limit results
        """
        # Create cache key
        cache_key = f"{track_name}||{artist_name}"

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
                limit=self.search_results_limit,
                market=self.market
            )
            
            tracks_raw = []
            exact_match = False
            if results['tracks']['items'] and len(results['tracks']['items']) > 0:
                tracks_raw = results['tracks']['items']
                exact_match = True
            else:
                # Try a broader search if exact match fails (with rate limiting)
                query = f"{artist_name} {track_name}"
                results = self._make_spotify_request(
                    self.spotify.search,
                    q=query,
                    type='track',
                    limit=self.search_results_limit,
                    market=self.market
                )

                if results['tracks']['items'] and len(results['tracks']['items']) > 0:
                    tracks_raw = results['tracks']['items']
            
            tracks = []
            if len(tracks_raw) > 0:
                tracks = [TrackInfo(
                    id=track['id'],
                    name=track['name'],
                    album_name=track['album']['name'],
                    duration_ms=track['duration_ms'],
                    artist_name=", ".join(artist['name'] for artist in track['artists']) if track['artists'] else artist_name,
                    exact_search_match=exact_match
                ) for track in tracks_raw]
                
            # Cache the result
            self.cache[cache_key] = tracks
            return tracks

        except Exception as e:
            print_log(f"Error searching for track '{track_name}' by '{artist_name}': {e}")
            # Cache negative result to avoid retrying
            self.cache[cache_key] = None
            raise e # raise to propagate error
