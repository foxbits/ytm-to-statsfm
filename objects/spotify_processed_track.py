from typing import List
from spotify.spotify_listening_history import SpotifyStreamingEntry


class SpotifyProcessedTracks:
    def __init__(self, processed: List[SpotifyStreamingEntry], skipped: List[SpotifyStreamingEntry], errors: List[SpotifyStreamingEntry], logs: List[str]):
        self.processed = processed
        self.skipped = skipped
        self.errors = errors
        self.logs = logs

    def to_dict(self) -> dict:
        return {
            "processed": [entry.to_dict() for entry in self.processed],
            "skipped": [entry.to_dict() for entry in self.skipped],
            "errors": [entry.to_dict() for entry in self.errors],
            "logs": self.logs
        }