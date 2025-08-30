from objects.ytm_processed_track import YTMProcessedTrack


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
    def __init__(self, timestamp_iso: str = "",
                 track_name: str = "", artist: str = "", timestamp_unix: int = 0, 
                 additional_data: SpotifyAdditionalYTMData = SpotifyAdditionalYTMData()):
        
        # data that actually exists in YTM history
        self.ts = timestamp_iso
        self.master_metadata_track_name = track_name
        self.master_metadata_album_artist_name = artist

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
    
    @classmethod
    def from_ytm_track(cls, ytm_track: YTMProcessedTrack, additional_data: SpotifyAdditionalYTMData = SpotifyAdditionalYTMData()):
        return cls(
            timestamp_iso=ytm_track.timestamp_iso,
            track_name=ytm_track.title,
            artist=ytm_track.artist,
            timestamp_unix=ytm_track.timestamp_unix,
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
            "incognito_mode": self.incognito_mode
        }