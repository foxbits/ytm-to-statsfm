from typing import List, Optional

from ytm.ytm_watch_history import YTMWatchHistoryEntry

class YTMProcessedTrackMetadata:
    def __init__(self, original_channel: str = "", original_title: str = "", ytm_url: str = ""):
        self.original_channel = original_channel
        self.original_title = original_title
        self.ytm_url = ytm_url

    def to_dict(self):
        return {
            "original_channel": self.original_channel,
            "original_title": self.original_title,
            "ytm_url": self.ytm_url
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            original_channel=data.get("original_channel", ""),
            original_title=data.get("original_title", ""),
            ytm_url=data.get("ytm_url", "")
        )

class YTMProcessedTrack:
    def __init__(self, timestamp_iso: str = "", timestamp_unix: Optional[int] = None, title: str = "", artist: str = "", metadata: YTMProcessedTrackMetadata = None):
        self.timestamp_iso = timestamp_iso
        self.timestamp_unix = timestamp_unix
        self.title = title
        self.artist = artist
        self.metadata = metadata or YTMProcessedTrackMetadata()

    def to_dict(self):
        return {
            "timestamp_iso": self.timestamp_iso,
            "timestamp_unix": self.timestamp_unix,
            "title": self.title,
            "artist": self.artist,
            "metadata": self.metadata.to_dict()
        }

    @classmethod
    def from_dict(cls, data: dict):
        metadata_data = data.get("metadata", {})
        metadata = YTMProcessedTrackMetadata.from_dict(metadata_data)
        
        return cls(
            timestamp_iso=data.get("timestamp_iso", ""),
            timestamp_unix=data.get("timestamp_unix"),
            title=data.get("title", ""),
            artist=data.get("artist", ""),
            metadata=metadata
        )

class YTMProcessedResults: 
    def __init__(self, songs: List[YTMProcessedTrack], music_videos: List[YTMProcessedTrack], errors: List[YTMWatchHistoryEntry]):
        self.songs = songs
        self.music_videos = music_videos
        self.errors = errors

    def to_dict(self):
        return {
            "songs": [track.to_dict() for track in self.songs],
            "music_videos": [track.to_dict() for track in self.music_videos],
            "errors": [track.to_dict() for track in self.errors]
        }
