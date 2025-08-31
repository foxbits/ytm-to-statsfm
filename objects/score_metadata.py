class MatchScore:
    def __init__(self, track_score: float = 0.0, artist_score: float = 0.0, equal_weight: float = 0.0, track_heavy: float = 0.0, artist_heavy: float = 0.0, min_score: float = 0.0, max_score: float = 0.0):
        self.track_score = track_score
        self.artist_score = artist_score
        self.equal_weight = equal_weight
        self.track_heavy = track_heavy
        self.artist_heavy = artist_heavy
        self.min_score = min_score
        self.max_score = max_score

    def to_dict(self):
        return {
            "track_score": self.track_score,
            "artist_score": self.artist_score,
            "equal_weight": self.equal_weight,
            "track_heavy": self.track_heavy,
            "artist_heavy": self.artist_heavy,
            "min_score": self.min_score,
            "max_score": self.max_score
        }
    
    @classmethod
    def max_score(cls):
        return cls(100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            track_score=data.get("track_score", 0.0),
            artist_score=data.get("artist_score", 0.0),
            equal_weight=data.get("equal_weight", 0.0),
            track_heavy=data.get("track_heavy", 0.0),
            artist_heavy=data.get("artist_heavy", 0.0),
            min_score=data.get("min_score", 0.0),
            max_score=data.get("max_score", 0.0)
        )