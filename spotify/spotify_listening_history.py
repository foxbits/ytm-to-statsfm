from objects.process_metadata import ProcessingStatus, SpotifyProcessingMetadata
from objects.ytm_processed_track import YTMProcessedTrack
from spotify.constants import SPOTIFY_URI_PREFIX


class SpotifyAdditionalYTMData:
    def __init__(self, ms_played: int = 0, conn_country: str = "", platform: str = "", ip_addr: str = ""):
        self.ms_played = ms_played
        self.conn_country = conn_country
        self.platform = platform
        self.ip_addr = ip_addr

    def to_dict(self):
        return {
            "ms_played": self.ms_played,
            "conn_country": self.conn_country,
            "platform": self.platform,
            "ip_addr": self.ip_addr
        }

class SpotifyStreamingEntry:
    def __init__(self, ts: str = "",
                 master_metadata_track_name: str = "", master_metadata_album_artist_name: str = "", 
                 additional_data: SpotifyAdditionalYTMData = None):
        
        additional_data = additional_data or SpotifyAdditionalYTMData()

        # data that actually exists in YTM history
        self.ts = ts
        self.master_metadata_track_name = master_metadata_track_name
        self.master_metadata_album_artist_name = master_metadata_album_artist_name

        # data that can be 'calculated' (static, not great)
        self.ms_played = additional_data.ms_played

        # data that can be 'calculated' (environment)
        self.platform = additional_data.platform
        self.conn_country = additional_data.conn_country
        self.ip_addr = additional_data.ip_addr

        # unsure if needed
        self.spotify_track_uri = "" # "spotify:track:<track-id>" well this is needed fuck
        self.master_metadata_album_album_name = ""

        # default fields
        self.reason_start = "playbtn"
        self.reason_end = "trackdone"
        self.skipped = False
        self.offline = False
        self.offline_timestamp = None
        self.incognito_mode = False

        # Episode metadata
        self.episode_name = None
        self.episode_show_name = None
        self.spotify_episode_uri = None
        self.audiobook_title = None
        self.audiobook_uri = None
        self.audiobook_chapter_uri = None
        self.audiobook_chapter_title = None
        self.shuffle = None

        # Processing metadata
        self.metadata = SpotifyProcessingMetadata()

    def has_basic_info(self):
        return bool(self.master_metadata_track_name and self.master_metadata_album_artist_name)

    def has_spotify_data(self):
        return bool(self.spotify_track_uri) and self.spotify_track_uri.startswith(SPOTIFY_URI_PREFIX)
    
    def set_info_from_track(self, track_index: int):
        if not self.metadata or not self.metadata.tracks or track_index < 0 or track_index >= len(self.metadata.tracks):
            raise ValueError("Invalid track index or metadata not available")

        # save new track details
        self.spotify_track_uri = self.metadata.tracks[track_index].uri
        self.ms_played = self.metadata.tracks[track_index].duration_ms

        # replace track details with new data
        self.master_metadata_track_name = self.metadata.tracks[track_index].name
        self.master_metadata_album_artist_name = self.metadata.tracks[track_index].artist_name
        self.master_metadata_album_album_name = self.metadata.tracks[track_index].album_name
    
    def set_status_as_matched(self, status: ProcessingStatus = ProcessingStatus.OK, track_index: int = 0):
        self.metadata.status = status
        self.metadata.status_message = f"Trusted match with score {self.metadata.match_score:.2f}"
        
        if self.metadata.tracks[track_index].exact_search_match:
            self.metadata.status_message += " (exact API search match, not calculated)"
    
    def set_status_as_unmatched(self, status: ProcessingStatus = ProcessingStatus.NO_MATCH):
        self.metadata.status = status
        self.metadata.status_message = f"All matches are wrong, cannot match"

    @classmethod
    def from_ytm_track(cls, ytm_track: YTMProcessedTrack, additional_data: SpotifyAdditionalYTMData = None):
        additional_data = additional_data or SpotifyAdditionalYTMData()
        return cls(
            ts=ytm_track.timestamp_iso,
            master_metadata_track_name=ytm_track.title,
            master_metadata_album_artist_name=ytm_track.artist,
            additional_data=additional_data
        )

    def to_dict(self):
        return {
            "ts": self.ts,
            "platform": self.platform,
            "ms_played": self.ms_played,
            "conn_country": self.conn_country,
            "ip_addr": self.ip_addr,
            "master_metadata_track_name": self.master_metadata_track_name,
            "master_metadata_album_artist_name": self.master_metadata_album_artist_name,
            "master_metadata_album_album_name": self.master_metadata_album_album_name,
            "spotify_track_uri": self.spotify_track_uri,
            "episode_name": self.episode_name,
            "episode_show_name": self.episode_show_name,
            "spotify_episode_uri": self.spotify_episode_uri,
            "audiobook_title": self.audiobook_title,
            "audiobook_uri": self.audiobook_uri,
            "audiobook_chapter_uri": self.audiobook_chapter_uri,
            "audiobook_chapter_title": self.audiobook_chapter_title,
            "reason_start": self.reason_start,
            "reason_end": self.reason_end,
            "shuffle": self.shuffle,
            "skipped": self.skipped,
            "offline": self.offline,
            "offline_timestamp": self.offline_timestamp,
            "incognito_mode": self.incognito_mode,
            "metadata": self.metadata.to_dict()
        }

    @classmethod
    def from_dict(cls, data: dict):
        entry = cls()
        entry.ts=data.get("ts", "")
        entry.master_metadata_track_name=data.get("master_metadata_track_name", "")
        entry.master_metadata_album_artist_name=data.get("master_metadata_album_artist_name", "")
        entry.conn_country=data.get("conn_country", "")
        entry.platform=data.get("platform", "")
        entry.ip_addr=data.get("ip_addr", "")
        entry.ms_played=data.get("ms_played", 0)
        entry.master_metadata_album_album_name = data.get("master_metadata_album_album_name", "")
        entry.spotify_track_uri = data.get("spotify_track_uri", "")
        entry.episode_name = data.get("episode_name")
        entry.episode_show_name = data.get("episode_show_name")
        entry.spotify_episode_uri = data.get("spotify_episode_uri")
        entry.audiobook_title = data.get("audiobook_title")
        entry.audiobook_uri = data.get("audiobook_uri")
        entry.audiobook_chapter_uri = data.get("audiobook_chapter_uri")
        entry.audiobook_chapter_title = data.get("audiobook_chapter_title")
        entry.reason_start = data.get("reason_start", "playbtn")
        entry.reason_end = data.get("reason_end", "trackdone")
        entry.shuffle = data.get("shuffle")
        entry.skipped = data.get("skipped", False)
        entry.offline = data.get("offline", False)
        entry.offline_timestamp = data.get("offline_timestamp")
        entry.incognito_mode = data.get("incognito_mode", False)
        entry.metadata = SpotifyProcessingMetadata.from_dict(data.get("metadata", {}))
        return entry
    