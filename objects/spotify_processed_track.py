from typing import List
from spotify.spotify_listening_history import SpotifyStreamingEntry


class SpotifyProcessedTracks:
    def __init__(self, processed: List[SpotifyStreamingEntry], doubt: List[SpotifyStreamingEntry], errors: List[SpotifyStreamingEntry]):
        self.processed = processed
        self.doubt = doubt
        self.errors = errors

    def to_dict(self) -> dict:
        return {
            "processed": [entry.to_dict() for entry in self.processed],
            "doubt": [entry.to_dict() for entry in self.doubt],
            "errors": [entry.to_dict() for entry in self.errors]
        }