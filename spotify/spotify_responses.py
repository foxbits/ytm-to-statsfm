from spotify.constants import SPOTIFY_URI_PREFIX


class TrackInfo:
    def __init__(self, id: str, name: str, album_name: str, duration_ms: int, artist_name: str):
        self.id = id
        self.name = name
        self.album_name = album_name
        self.duration_ms = duration_ms
        self.artist_name = artist_name
        self.uri = f"{SPOTIFY_URI_PREFIX}{id}"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "album_name": self.album_name,
            "duration_ms": self.duration_ms,
            "artist_name": self.artist_name,
            "uri": self.uri
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            album_name=data.get("album_name", ""),
            duration_ms=data.get("duration_ms", 0),
            artist_name=data.get("artist_name", ""),
            uri=data.get("uri", "")
        )