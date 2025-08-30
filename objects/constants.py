# Header that identifies YouTube Music entries in the YT History
YT_MUSIC_HEADER = 'YouTube Music'

# Characters that are used as artist-song splitters (only for videos watched on YTM)
SPLIT_CHARACTERS = [r"-", r"💕"]

# Regex patterns that match the split characters
RG_SPLIT_CHARS = r"[" + "".join(SPLIT_CHARACTERS) + r"]"

# Strings that are removed from the final artist / track name (only for videos watched on YTM)
FORBIDDEN_STRINGS = [" - ", " 💕 ", r" \| ", " ✖️ ", " ALBUM", "ALBUM "]