This repo contains a set of python scripts that allow you to convert the YouTube Music listening history (songs only) into Spotify listening history (with some details using default values), making it importable into [stats.fm](http://stats.fm) and other applications that use this format.

## Pre-requisites

1. [python](https://www.python.org) installed and available in path

## How to use

### 1. Exporting your YouTube Music Data

1. Go to Google Takeout at [takeout.google.com](https://takeout.google.com).
2. Sign in with your Google account that is linked to the YouTube Music history you want to export
3. Deselect all
4. Select "YouTube and YouTube Music" - All YouTube data included
5. Deselect all except the history option
6. Select JSON as format
7. Wait for the download link in the email

### 2. Getting the scripts

1. Clone this repo
2. Run `pip install -r requirements.txt` to install dependencies

**Note**: all the scripts will output informational logs to both screen and to the file `output/logs.txt`.

### 3. Listening history sanitization

1. Copy your `watch-history.json` into the same folder as these scripts
2. Run `python sanitizer.py`
   1. This script uses by default as input file a `watch-history.json` available in the same folder; you can use a different file if you want, by specifying `--file your-file.json`
3. The script will run (time depends on your history size). It will then output info regarding it's status.
4. The script exports 3 files in the `output` folder, based on the original file name:
   1. `-songs.json` - the list of songs detected on YT Music listening history. These are 100% accurate ✅
   2. `-videos.json` - the list of videos detected on your YT Music listening history; These can be or cannot be accurate* 🤔
      1. Since music videos naming can follow or not follow deterministic naming standards, it is recommended to do a double check and edit / correct the entries in this file before importing. 
      2. For more details see Caveats / #2
   3. `-errors.json` - the list of entries in the history that cannot be processed** ❌
      1. The file contains entries in the original YT Music listening history format, therefore, if you think you can fix any of the entries, have a quick look, fix them and then use the corrected file as input for the `sanitizer script` (e.g. restart the process but with the corrected file)
5. At the end of this process you will have 1/2/3 json files that you can use for the next step


### 4. Converting to Spotify format

For more insights into the Spotify Data format, see [understanding my data](https://support.spotify.com/article/understanding-my-data/), [`ReadMeFirst_ExtendedStreamingHistory.pdf`](docs/ReadMeFirst_ExtendedStreamingHistory.pdf) and the comments inside [`types/spotify_listening_history.py`](types/spotify_listening_history.py).

1. Create a `.env` file and fill in the environment variables as identified in [`.env.example`](.env.example), according to your needs. These env vars are used to populate some default fields that are required in Spotify but not available in YTM
   1. `MS_PLAYED` - the milliseconds played (number). YT Music listening history does not have a duration of the time played, therefore a default is needed. I recommend the usual song average of 3 minutes, which is 180s therefore `180000` (ms). This will be replaced if a match is found at next step, but is used as default
   2. `CONN_COUNTRY` - your country code (A-2 from [here](https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes))
   3. `PLATFORM` - Put your own platform (needs to be supported by spotify), or use `ios`.
   4. `IP_ADDR` - your ip address - use some random one or add your actual ip address (https://www.whatsmyip.org)

2. Run `python converter.py --file output\\watch-history-sanitized-songs.json` (and `python converter.py --file output\\watch-history-sanitized-videos.json` if you have checked and want to process the watched YTM videos as well).. or with your preffered file that follows the YTM format defined in [`types/ytm_processed_track.py`](types/ytm_processed_track.py) if you used other names
3. You will obtain a new json file named `<your-file>-spotify-format.json` in the `output` directory (e.g. `output\\watch-history-sanitized-songs-spotify-format.json`).
4. You can use this file as you would use a normal spotify listening history file, except that it does not have such significant data except the artist name, track name and timestamp played. The full data is populated in next steps.

### 5. Using the Spotify API to enrich the data

Since YTM does provide only the artist name, track title and time played, a lot of the specific Spotify data is missing, most importantly the Spotify Track ID, the Album Name and the actual time played.

This extra data (the most important being the spotify track id) is identified through searching the Spotify Metadata API by artist & track name. This result will sometimes return multiple entries, so this is a multi-step process

#### 5.1 Configure the Spotify Client

1. Make sure you have a Spotify Developer account and an application to use for this part
   1. Go to https://developer.spotify.com/dashboard, login and create an app
   2. Put in a name and description (like ytm-history-converter)
   3. For callbacks add something random (but valid) like `https://localhost:3000/callback`. This will, anyway, not be used, since we won't be connecting with an user account (using only metadata API)
   4. Check only the Web API in the Which APIs/SDKs are you planning to use
2. Copy your client id and client secret and put them in the .env file
   1. `SPOTIFY_CLIENT_ID` - client id
   2. `SPOTIFY_CLIENT_SECRET` - client secret
3. Set the following settings for communicating with Spotify (can use defaults from example):
   1. `SPOTIFY_SEARCH_RESULTS_LIMIT` -> the number of tracks to search for matching in Spotify; this is exported in the enriched data for determining the best match; the number should not be very big (1 for exact matching => risky)
   2. `SPOTIFY_MAX_RETRIES` -> number of retries to do on rate limiting api errors
4. The API search will use the `CONN_COUNTRY` value for the market to search for (in order to display results from where you actually use Spotify, not default - Global/US). This should be set already from the previous steps

#### 5.2 Enrich the data

1. Run `python enricher.py --file output\\watch-history-sanitized-songs-spotify-format.json` (and `python converter.py --file output\\watch-history-sanitized-videos.json-spotify-format` if you have checked and want to process the watched YTM videos as well)
2. You will obtain a new set of json files:
   1. `<your-file>-enriched-ok.json` -> contains all the successfully processed tracks with metadata -> tracks array populated with top spotify results
   2. `<your-file>-enriched-errors.json` -> contains all the tracks that ended in error either when communicating with the Spotify API or in not being able to identify any tracks. You can inspect these errors and eventually do some edits on it and re-process



### Example of full flow

```
#1 - sanitize and split input
python sanitizer.py --file watch-history-small.json
=> output\\watch-history-small-sanitized-songs.json,
=> output\\watch-history-small-sanitized-videos.json
=> output\\watch-history-small-sanitized-errors.json

#2 - convert the songs
python converter.py --file output\\watch-history-small-sanitized-songs.json
=> output\\watch-history-small-sanitized-songs-spotify-format.json

#3 - manually double check the videos json output\\watch-history-small-sanitized-videos.json

#4 - convert the music videos
python converter.py --file output\\watch-history-small-sanitized-videos.json
=> output\\watch-history-small-sanitized-videos-spotify-format.json

#5 - enrich the songs and/or videos with spotify track data (top X configurable)
python enricher.py --file output\\watch-history-small-sanitized-songs-spotify-format.json
=> output\\watch-history-small-sanitized-songs-spotify-format-enriched-ok.json
=> output\\watch-history-small-sanitized-songs-spotify-format-enriched-errors.json

python enricher.py --file output\\watch-history-small-sanitized-videos-spotify-format.json
=> output\\watch-history-small-sanitized-videos-spotify-format-enriched-ok.json
=> output\\watch-history-small-sanitized-videos-spotify-format-enriched-errors.json

#6 - manually check the errors file(s) to see if anything can be fixed / retried (e.g. in case of rate limiting)


```

- test if one fails
- test with video

## Caveats / Troubleshooting

1. It does not process data watched on the YouTube site itself, because the Google Takeout data for listening history does not contain video type, therefore music videos cannot be identified.
2. I recommend you to test first with a small portion of your data (just pick a few entries from the array); if everything is ok, go with the full data
3. The script runs by default without the `--ignore-videos` flag. 
   As you know, on YT Music you can both listen to songs and watch videos (which are basically YouTube videos). 
   These videos often do not have standard track artist / title naming format and usually put everything in the title (since they are YT videos) - e.g. "Artist - Song | Official Audio" and other variations. This means that the script has to do some non-deterministic guessing as in what's the artist and the song title in such videos, which often fails if you want a lot of music videos with non-standard formatting. Therefore, you can choose to ignore such videos watched on YT Music (note: videos watched on YouTube itself are automatically ignored). If you choose not to ignore them, the script tries to sanitize them as best as it can, following the format <artist-name><split-chars><song-title> and stripping any Official* (with/without paranthesis) from the song
4. In case of rapidfuzz related errors, get the latest build version from [here](https://www.piwheels.org/project/rapidfuzz/) and install it with `pip install rapidfuzz==<version> --force-reinstall --no-deps`
