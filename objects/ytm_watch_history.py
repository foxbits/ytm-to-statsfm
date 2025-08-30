from typing import List, Optional

from objects.constants import YT_MUSIC_HEADER

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
                 subtitles: Optional[List[YTMWatchHistorySubtitleEntry]] = None):
        self.header = header
        self.title = title
        self.titleUrl = titleUrl
        self.time = time
        self.products = products or []
        self.activityControls = activityControls or []
        self.subtitles = subtitles or []
    
    def to_dict(self):
        return {
            "header": self.header,
            "title": self.title,
            "titleUrl": self.titleUrl,
            "time": self.time,
            "products": self.products,
            "activityControls": self.activityControls,
            "subtitles": self.subtitles
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
            subtitles=[YTMWatchHistorySubtitleEntry.from_dict(item) for item in data.get("subtitles", [])]
        )
    
    def is_youtube_music_entry(self) -> bool:
        """Check if this entry is a YouTube Music entry"""
        return self.header == YT_MUSIC_HEADER
