from typing import List
from spotify.spotify_listening_history import SpotifyStreamingEntry


class SpotifyProcessedTracks:
    def __init__(self, processed: List[SpotifyStreamingEntry], errors: List[SpotifyStreamingEntry]):
        self.processed = processed
        self.errors = errors

    def to_dict(self) -> dict:
        return {
            "processed": [entry.to_dict() for entry in self.processed],
            "errors": [entry.to_dict() for entry in self.errors]
        }