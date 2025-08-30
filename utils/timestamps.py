
from datetime import datetime


def convert_to_unix_timestamp(iso_timestamp):
    if iso_timestamp:
        dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        return int(dt.timestamp())
    return None