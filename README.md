This repo contains a set of python scripts that allow you to convert the YouTube Music listening history (songs only) into Spotify listening history (with some details using default values), making it importable into [stats.fm](http://stats.fm) and other applications that use this format.

## Pre-requisites

1. [python](https://www.python.org) installed and available in path

## How to use

### Exporting your YouTube Music Data

1. Go to Google Takeout at [takeout.google.com](https://takeout.google.com).
2. Sign in with your Google account that is linked to the YouTube Music history you want to export
3. Deselect all
4. Select "YouTube and YouTube Music" - All YouTube data included
5. Deselect all except the history option
6. Select JSON as format
7. Wait for the download link in the email

### Getting the scripts

1. Clone this repo
2. Run `pip install -r requirements.txt` to install dependencies

### Listening history sanitization

1. Copy your `watch-history.json` into the same folder as these scripts
2. Run `python sanitizer.py`
   1. This script uses by default as input file a `watch-history.json` available in the same folder; you can use a different file if you want, by specifying `--file your-file.json`
3. The script will run (time depends on your history size). It will then output info regarding it's status.
4. The script exports 3 files in the `output` folder, based on the original file name:
   1. `-songs.json` - the list of songs detected on YT Music listening history. These are 100% accurate ✅
   2. `-videos.json` - the list of videos detected on your YT Music listening history; These can be or cannot be accurate 🤔
   Since music videos naming can follow or not follow deterministic naming standards, it is recommended to do a double check and edit / correct the entries in this file before importing. For more details see Cafeats / #2
   3. `-errors.json` - the list of entries in the history that cannot be processed ❌ 
   The file contains entries in the original YT Music listening history format, therefore, if you think you can fix any of the entries, have a quick look, fix them and then use the corrected file as input for the `sanitizer script`
5. At the end of this process you will have 1/2 json files that you can use for the next step

### Converting to Spotify format

For more insights into the Spotify Data format, see [understanding my data](https://support.spotify.com/article/understanding-my-data/), [`ReadMeFirst_ExtendedStreamingHistory.pdf`](docs/ReadMeFirst_ExtendedStreamingHistory.pdf) and the comments inside [`types/spotify_listening_history.py`](types/spotify_listening_history.py).

1. Create a `.env` file and fill in the environment variables as identified in [`.env.example`](.env.example), according to your needs. These env vars are used to populate some default fields that are required in Spotify but not available in YTM
   1. `MS_PLAYED` - the milliseconds played (number). YT Music listening history does not have a duration of the time played, therefore a default is needed. I recommend the usual song average of 3 minutes, which is 180s therefore `180000` (ms)
   2. `CONN_COUNTRY` - your country code (A-2 from [here](https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes))
   3. `PLATFORM` - Put your own platform (needs to be supported by spotify), or use `ios`.
   4. `IP_ADDR` - your ip address - use some random one or add your actual ip address (https://www.whatsmyip.org)

2. Run `python converter.py --file watch-history-sanitized-songs.json` or `python converter.py --file watch-history-sanitized-videos.json` or with your preffered file that follows the YTM format defined in [`types/ytm_processed_track.py`](types/ytm_processed_track.py)
3. You will obtain a new json file named `your-file-spotify-format.json` (e.g. `watch-history-sanitized-songs-spotify-format.json`) in the `output` directory.
4. You can use this file as you would use a normal spotify listening history file

## Caveats / Troubleshooting

1. It does not process data watched on the YouTube site itself, because the Google Takeout data for listening history does not contain video type, therefore music videos cannot be identified.
2. The script runs by default without the `--ignore-videos` flag. 
   As you know, on YT Music you can both listen to songs and watch videos (which are basically YouTube videos). 
   These videos often do not have standard track artist / title naming format and usually put everything in the title (since they are YT videos) - e.g. "Artist - Song | Official Audio" and other variations. This means that the script has to do some non-deterministic guessing as in what's the artist and the song title in such videos, which often fails if you want a lot of music videos with non-standard formatting. Therefore, you can choose to ignore such videos watched on YT Music (note: videos watched on YouTube itself are automatically ignored). If you choose not to ignore them, the script tries to sanitize them as best as it can, following the format <artist-name><split-chars><song-title> and stripping any Official* (with/without paranthesis) from the song
