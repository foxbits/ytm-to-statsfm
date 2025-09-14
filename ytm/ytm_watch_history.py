from typing import List, Optional

from objects.constants import YT_MUSIC_HEADER, YT_MUSIC_TRACK_IDENTIFIER, YT_MUSIC_TRACK_TITLE_PREFIX
from objects.process_metadata import ProcessingStatus, YTMProcessingMetadata

class YTMWatchHistorySubtitleEntry:
    def __init__(self, name: str = "", url: str = ""):
        self.name = name
        self.url = url
    
    def to_dict(self):
        return {
            "name": self.name,
            "url": self.url
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            name=data.get("name", ""),
            url=data.get("url", "")
        )

class YTMWatchHistoryEntry:
    def __init__(self, 
                 header: str = "",
                 title: str = "",
                 titleUrl: str = "",
                 time: str = "",
                 products: Optional[List[str]] = None,
                 activityControls: Optional[List[str]] = None,
                 subtitles: Optional[List[YTMWatchHistorySubtitleEntry]] = None,
                 metadata: YTMProcessingMetadata = None):
        self.header = header
        self.title = title
        self.titleUrl = titleUrl
        self.time = time
        self.products = products or []
        self.activityControls = activityControls or []
        self.subtitles = subtitles or []
        self.metadata = metadata or YTMProcessingMetadata()
    
    def is_youtube_music_entry(self) -> bool:
        """Check if this entry is a YouTube Music entry"""
        return self.header == YT_MUSIC_HEADER
    
    def set_metadata_error(self, error_message: str):
        self.metadata.status = ProcessingStatus.ERROR
        self.metadata.status_message = error_message
    
    def set_track_data(self, title: str, artist: str):

        # Make sure the subtitles list exists
        if not self.subtitles or len(self.subtitles) == 0:
            self.subtitles = [YTMWatchHistorySubtitleEntry()]
        
        # Save original data for reference
        self.metadata.original_title = self.title
        self.metadata.original_channel = self.subtitles[0].name

        # Set title as "Watched <track-name>"
        if not title.startswith(YT_MUSIC_TRACK_TITLE_PREFIX):
            title = YT_MUSIC_TRACK_TITLE_PREFIX + title

        # Set artist as "<artist-name> - Topic"
        if not artist.endswith(YT_MUSIC_TRACK_IDENTIFIER):
            artist += f" {YT_MUSIC_TRACK_IDENTIFIER}"

        self.title = title
        self.subtitles[0].name = artist
        self.metadata.status = ProcessingStatus.OK
    
    def to_dict(self):
        return {
            "header": self.header,
            "title": self.title,
            "titleUrl": self.titleUrl,
            "time": self.time,
            "products": self.products,
            "activityControls": self.activityControls,
            "subtitles": [s.to_dict() for s in self.subtitles],
            "metadata": self.metadata.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            header=data.get("header", ""),
            title=data.get("title", ""),
            titleUrl=data.get("titleUrl", ""),
            time=data.get("time", ""),
            products=data.get("products", []),
            activityControls=data.get("activityControls", []),
            subtitles=[YTMWatchHistorySubtitleEntry.from_dict(item) for item in data.get("subtitles", [])],
            metadata=YTMProcessingMetadata.from_dict(data.get("metadata", {}))
        )
