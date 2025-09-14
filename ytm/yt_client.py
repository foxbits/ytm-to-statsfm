import re
from ytmusicapi import YTMusic

from utils.simple_logger import print_log
from ytm.ytm_watch_history import YTMWatchHistoryEntry

class YouTubeClient:
    def __init__(self):
        self.ytmusic = YTMusic()

    def extract_video_id(self, url: str) -> str:
        """Extract YouTube video ID from a URL containing 'watch?v=<id>'"""
        match = re.search(r"watch\?v=([\w-]+)", url)
        return match.group(1) if match else ""
    
    def extract_song_details(self, yt_url: str) -> dict:
        """Extract song details from a YouTube URL"""
        video_id = self.extract_video_id(yt_url)
        if not video_id:
            print_log(f"No valid video ID found in URL {yt_url}")
            return {}
        
        try:
            song = self.ytmusic.get_song(video_id)
            return song
        except Exception as e:
            print_log(f"Error fetching song for video ID {video_id}: {e}")
            return {}