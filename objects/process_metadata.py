from enum import Enum
from typing import List

from spotify.spotify_responses import TrackInfo


class ProcessingStatus(Enum):
    OK = "OK"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"

class YTMProcessingMetadata:
    def __init__(self, status: ProcessingStatus = ProcessingStatus.OK, status_message: str = "", is_video: bool = False,
            ytm_url: str = "", original_channel: str = "", original_title: str = ""):
        self.status = status
        self.status_message = status_message or status.value
        self.is_video = is_video
        self.ytm_url = ytm_url
        self.original_channel = original_channel
        self.original_title = original_title
    
    def to_dict(self):
        return {
            "status": self.status.value,
            "status_message": self.status_message,
            "is_video": self.is_video,
            "ytm_url": self.ytm_url,
            "original_channel": self.original_channel,
            "original_title": self.original_title
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            status=ProcessingStatus(data.get("status", ProcessingStatus.OK.value)),
            status_message=data.get("status_message", ""),
            is_video=data.get("is_video", False),
            ytm_url=data.get("ytm_url", ""),
            original_channel=data.get("original_channel", ""),
            original_title=data.get("original_title", "")
        )

class SpotifyProcessingMetadata:
    def __init__(self, status: ProcessingStatus = ProcessingStatus.OK, status_message: str = "", tracks: List[TrackInfo] = None):
        self.status = status
        self.status_message = status_message
        self.tracks = tracks or []

    def to_dict(self):
        return {
            "status": self.status.value,
            "status_message": self.status_message,
            "tracks": [track.to_dict() for track in self.tracks]
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        status = ProcessingStatus(data.get("status", ProcessingStatus.OK.value))
        status_message = data.get("status_message", "")
        tracks_data = data.get("tracks", [])
        tracks = [TrackInfo.from_dict(track) for track in tracks_data]

        return cls(
            status=status,
            status_message=status_message,
            tracks=tracks
        )
