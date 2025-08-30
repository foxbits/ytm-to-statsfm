from typing import List, Optional

from objects.constants import YT_MUSIC_TRACK_IDENTIFIER
from objects.process_metadata import YTMProcessingMetadata
from ytm.ytm_watch_history import YTMWatchHistoryEntry

class YTMProcessedTrack:
    def __init__(self, timestamp_iso: str = "", timestamp_unix: Optional[int] = None, title: str = "", artist: str = "", metadata: YTMProcessingMetadata = None):
        self.timestamp_iso = timestamp_iso
        self.timestamp_unix = timestamp_unix
        self.title = title
        self.artist = artist
        self.metadata = metadata or YTMProcessingMetadata()

    def to_dict(self):
        return {
            "timestamp_iso": self.timestamp_iso,
            "timestamp_unix": self.timestamp_unix,
            "title": self.title,
            "artist": self.artist,
            "metadata": self.metadata.to_dict()
        }

    def is_valid(self):
        return bool(self.title and self.artist)
    
    def is_track(self):
        return YT_MUSIC_TRACK_IDENTIFIER in self.artist

    def is_music_video(self):
        return YT_MUSIC_TRACK_IDENTIFIER not in self.artist

    @classmethod
    def from_dict(cls, data: dict):
        metadata_data = data.get("metadata", {})
        metadata = YTMProcessingMetadata.from_dict(metadata_data)

        return cls(
            timestamp_iso=data.get("timestamp_iso", ""),
            timestamp_unix=data.get("timestamp_unix"),
            title=data.get("title", ""),
            artist=data.get("artist", ""),
            metadata=metadata
        )

class YTMProcessedResults: 
    def __init__(self, songs: List[YTMProcessedTrack], music_videos: List[YTMProcessedTrack], errors: List[YTMWatchHistoryEntry], skipped: List[YTMWatchHistoryEntry]):
        self.songs = songs
        self.music_videos = music_videos
        self.errors = errors
        self.skipped = skipped

    def to_dict(self):
        return {
            "songs": [track.to_dict() for track in self.songs],
            "music_videos": [track.to_dict() for track in self.music_videos],
            "errors": [track.to_dict() for track in self.errors],
            "skipped": [track.to_dict() for track in self.skipped]
        }
