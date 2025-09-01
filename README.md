This repo contains a set of python scripts that allow you to convert the YouTube Music listening history format (songs only) into Spotify listening history format (with some details using default values), making it importable into [stats.fm](http://stats.fm) and other applications that use this format. At the end of this page there is an example for the same song in the two different formats.

It is based on a multi-step process:
1. data sanitization (automatic)
2. data conversion to the Spotify listening history format (automatic)
3. data enrichment using the official Spotify Search API (to find to actual spotify track ids, which are mandatory) (automatic)
4. track score analysis in case of multiple track matches in a single search (semi-automatic)
  - nobody wants to import in their listening history unwanted tracks, and since YTM provides only artist & track name, the match with Spotify is, most of the times, non-deterministic (you might have encountered this with playlist converters)
  - if track API search result (from Spotify) is exact OR if artist & track name text fuzzy match score is higher than a defined threshold => the track considered a match (automatic)
  - otherwise, a report is generated which requires manual review to select the right track from a list of returned results (manual)
  - in this case, the process is able to import a manually reviewed file and then process it normally (automatic)

Each step of the process is available as a standalone script, in order to allow you to run / re-do each step manually, or as part of an automated end-to-end script.

- [1. Pre-requisites](#1-pre-requisites)
  - [1.1. Exporting your YouTube Music Data](#11-exporting-your-youtube-music-data)
  - [1.2. Installing software](#12-installing-software)
  - [1.3 Setting the environment variables](#13-setting-the-environment-variables)
- [2. Processing the History](#2-processing-the-history)
  - [2.1. Data Sanitization](#21-data-sanitization)
  - [2.2 Data Conversion to Spotify listening history format](#22-data-conversion-to-spotify-listening-history-format)
  - [2.3 Data enrichment using the official Spotify Search API](#23-data-enrichment-using-the-official-spotify-search-api)
  - [Example of full flow](#example-of-full-flow)
- [Caveats / Troubleshooting](#caveats--troubleshooting)
- [Example of the same song in the 2 different formats](#example-of-the-same-song-in-the-2-different-formats)
  - [YouTube (Music) listening history](#youtube-music-listening-history)
  - [Spotify listening history](#spotify-listening-history)


## 1. Pre-requisites

### 1.1. Exporting your YouTube Music Data

1. Go to Google Takeout at [takeout.google.com](https://takeout.google.com).
2. Sign in with your Google account that is linked to the YouTube Music history you want to export
3. Deselect all
4. Select "YouTube and YouTube Music" - All YouTube data included
5. Deselect all except the history option
6. Select JSON as format
7. Wait for the download link in the email

### 1.2. Installing software

1. Install [python](https://www.python.org) (3.*)
2. Clone this repo
3. Run `pip install -r requirements.txt` to install dependencies

### 1.3 Setting the environment variables

Create a `.env` file and fill in the environment variables as identified in [`.env.example`](.env.example), according to your needs and as described below.

These env vars are used to connect to the Spotify API:
1. Make sure you have a Spotify Developer account and an application to use for this part
   1. Go to https://developer.spotify.com/dashboard, login and create an app
   2. Put in a name and description (like ytm-history-converter)
   3. For callbacks add something random (but valid) like `https://localhost:3000/callback`. This will, anyway, not be used, since we won't be connecting with an user account (using only metadata API)
   4. Check only the Web API in the Which APIs/SDKs are you planning to use
2. Copy your client id and client secret and put them in the `.env` file
   1. `SPOTIFY_CLIENT_ID` - client id
   2. `SPOTIFY_CLIENT_SECRET` - client secret
3. Set the following settings for communicating with Spotify (can use defaults from example):
   1. `SPOTIFY_SEARCH_RESULTS_LIMIT` -> the number of tracks to search for matching in Spotify; this is exported in the enriched data for determining the best match; the number should not be very big (1 for exact matching => risky)
   2. `SPOTIFY_MAX_RETRIES` -> number of retries to do on rate limiting api errors
4. The API search will use the `CONN_COUNTRY` value for the market to search for (in order to display results from where you actually use Spotify, not default). Set it o your country code (A-2 from [here](https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes))


These env vars are used for track score matching:
1. `SCORE_TRACKS_BY` - choose how the track name and title weight in deciding higher scores. The available options are:
   1. `track_score` - only use the track title score
   2. `artist_score` - only use artist name score
   3. `equal_weight` - 50% track title, 50% artist name (RECOMMENDED)
   4. `track_heavy` - 70% track title, 30% artist name
   5. `artist_heavy` - 30% track title, 70% artist name
   6. `min_score` - the minimum score between the two (pesimistic)
   7. `max_score` - the maximum score between the two (optimistic)
2. `MINIMUM_MATCH_DECISION_SCORE` - the minimum match percentage (0-1) to consider a track fully compatible / matched; if a track scores higher or equal to this, there's no doubt - it's considered fully matching! it will not be outputed in the doubts list. Choose a high number, `0.9` should fit well enough


These env vars are used to populate some default fields that are required in Spotify but not available in YTM
1. `MS_PLAYED` - the milliseconds played (number). YT Music listening history does not have a duration of the time played, therefore a default is needed. I recommend the usual song average of 3 minutes, which is 180s therefore `180000` (ms). This will be replaced if a match is found at next step, but is used as default
2. `CONN_COUNTRY` - your country code (A-2 from [here](https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes))
3. `PLATFORM` - Put your own platform (needs to be supported by spotify), or use `ios`.
4. `IP_ADDR` - your ip address - use some random one or add your actual ip address (https://www.whatsmyip.org)

## 2. Processing the History

**Note**: all the scripts will output informational logs to both screen and to the file `output/logs.txt`.

### 2.1. Data Sanitization

1. Copy your `watch-history.json` into the same folder as these scripts
2. Run `python sanitizer.py`
   1. This script uses by default as input file a `watch-history.json` available in the same folder; you can use a different file if you want, by specifying `--file your-file.json`
3. The script will run (time depends on your history size). It will then output info regarding its status.
4. The script exports 3 files in the `output` folder, based on the original file name:
   1. `.sanitized.songs.json` - the list of songs detected on YT Music listening history. These are 100% accurate ✅
   2. `.sanitized.videos.json` - the list of music videos detected on your YT Music listening history; These can be or cannot be accurate when converted to tracks 🤔
      - if you run the program with `--ignore-videos` flag, then the music videos are not processed and are put in a `.sanitized.skipped.json` list
      - Since music videos naming can follow or not follow deterministic naming standards, it is recommended to do a double check and edit / correct the entries in this file before importing; otherwise, you will have to review the matchings anyways in the final step
      - For more details see #2 from [Caveats / Troubleshooting](#caveats--troubleshooting)
   3. `.sanitized.errors.json` - the list of entries in the history that cannot be processed ❌
      - The file contains entries in the original YT Music listening history format, therefore, if you think you can fix any of the entries, have a quick look, fix them and then use the corrected file as input for the `sanitizer script` (e.g. restart the process but with the corrected file);
      - Most of the cases the error is due to missing artist name / track name in the YTM export, and you have to put them manually
5. At the end of this process you will have 1/2/3 json files that you can use for the next step


### 2.2 Data Conversion to Spotify listening history format

For more insights into the Spotify Data format, see:
- [understanding my data](https://support.spotify.com/article/understanding-my-data/)
- [`ReadMeFirst_ExtendedStreamingHistory.pdf`](docs/ReadMeFirst_ExtendedStreamingHistory.pdf)
- the comments inside [`spotify/spotify_listening_history.py`](spotify/spotify_listening_history.py)
- the exaple at the end at [Example of the same song in the 2 different formats](#example-of-the-same-song-in-the-2-different-formats)

Do the following steps:

1. Run `python converter.py --file output\\watch-history.sanitized.*.json`
   1. Run it with the `songs` and/or `videos` files 
   2. Alternatively you can run it with any file that follows the YTM format defined in [`objects/ytm_processed_track.py`](objects/ytm_processed_track.py) if you use custom files
2. You will obtain a new json file named `<your-file>.spotify.format.json` in the `output` directory
3. This full file follows the exact Spotify listening history format, but is populated only with the data available in YTM history (artist name, track name, timestamp) and with the default parameters (some from env vars). You most likely cannot import this file in many places. The full data is populated in next step (the enrichment).

### 2.3 Data enrichment using the official Spotify Search API

Since YTM does provide only the artist name, track title and timestamp when played, a lot of the specific Spotify data is missing, most importantly the Spotify Track ID, the Album Name and the actual duration of the track.

This extra data (the most important being the spotify track id) is identified through searching the Spotify Metadata API by artist & track name. This result will sometimes return multiple entries.

1. Run `python enricher.py --file output\\watch-history.sanitized.*.spotify.format.json`
   1. Run it with the `songs` and/or `videos` files
   2. Alternatively you can run it with any file that follows the Spotify format defined in [`spotify/spotify_listening_history.py`](spotify/spotify_listening_history.py) if you use custom files
2. Wait for it to run. If your file data is big, you will encounter Spotify Rate limiting (180 searches / minute) so it might take a while.
3. You will obtain a new set of json files:
   1. `<your-file>.enriched.matched.json` ✅
      - contains all the successfully matched tracks with metadata; a track is matched if:
         - has a matching score with the top result above `SCORE_TRACKS_WEIGHT`; 
         - spotify returns them as exact matches (results for exact track name and artist)
         - you can see the score in the `metadata.match_score`
      - `tracks` array populated with top spotify results
      - this file can be directly used as final ✅
   2. `<your-file>.enriched.doubt.json` 🤔
      - contains the tracks that cannot be safely matched with a result automatically
      - they need manual validation
      - this file is used in next step
   3. `<your-file>.enriched.errors.json` ❌
      - contains all the tracks that ended in error either when communicating with the Spotify API (e.g. rate limiting retries ending, unknown errors) or in not being able to identify any tracks
      - you can inspect these errors and eventually do some edits on it and re-process (restart this flow)



### Example of full flow

```
#1 - sanitize and split input
python sanitizer.py --file watch-history-small.json
=> output\\watch-history-small.sanitized.songs.json,
=> output\\watch-history-small.sanitized.videos.json
=> output\\watch-history-small.sanitized.errors.json

#2 - convert the songs
python converter.py --file output\\watch-history-small.sanitized.songs.json 
=> output\\watch-history-small.sanitized.songs.spotify.format.json

#3 - manually double check the videos json output\\watch-history-small.sanitized.videos.json

#4 - convert the music videos
python converter.py --file output\\watch-history-small.sanitized.videos.json
=> output\\watch-history-small.sanitized.videos.spotify.format.json

#5 - enrich the songs and/or videos with spotify track data
python enricher.py --file output\\watch-history-small.sanitized.songs.spotify.format.json
=> output\\watch-history-small.sanitized.songs.spotify.format.enricher.matched.json
=> output\\watch-history-small.sanitized.songs.spotify.format.enricher.doubt.json
=> output\\watch-history-small.sanitized.songs.spotify.format.enricher.errors.json

python enricher.py --file output\\watch-history-small.sanitized.videos.spotify.format.json
=> output\\watch-history-small.sanitized.videos.spotify.format.enricher.matched.json
=> output\\watch-history-small.sanitized.videos.spotify.format.enricher.doubt.json
=> output\\watch-history-small.sanitized.videos.spotify.format.enricher.errors.json

#6 - manually validate entries with doubts

#7 - use the successfully created files
- output\\watch-history-small.sanitized.videos.spotify.format.enricher.matched.json
- the processed doubt files
- any errored files that you re-process

```

- test if one fails
- test with video

## Caveats / Troubleshooting

1. This does not process data watched on the YouTube site itself, only on YouTube Music, because the Google Takeout data for listening history does not contain video type, therefore music videos cannot be identified.
2. I recommend you to test first with a small portion of your data (just pick a few entries from the array and create a `watch-history-small.json`); if everything is ok, go with the full data
3. The script runs by default without the `--ignore-videos` flag. 
   As you know, on YT Music you can both listen to songs and watch videos (which are basically YouTube videos). 
   These videos often do not have standard track artist / title naming format and usually put everything in the title (since they are YT videos) - e.g. "Artist - Song | Official Audio" and other variations. This means that the script has to do some non-deterministic guessing as in what's the artist and the song title in such videos, which often fails if you want a lot of music videos with non-standard formatting. Therefore, you can choose to ignore such videos watched on YT Music (note: videos watched on YouTube itself are automatically ignored). If you choose not to ignore them, the script tries to sanitize them as best as it can, following the format <artist-name><split-chars><song-title> and stripping any Official* (with/without paranthesis) from the song
4. In case of rapidfuzz related errors, get the latest build version from [here](https://www.piwheels.org/project/rapidfuzz/) and install it with `pip install rapidfuzz==<version> --force-reinstall --no-deps`


## Example of the same song in the 2 different formats

### YouTube (Music) listening history

```
{
   "header": "YouTube Music",
   "title": "Watched Nothing Breaks Like a Heart",
   "titleUrl": "https://music.youtube.com/watch?v\u003dKBDRUN6ovvk",
   "subtitles": [
      {
            "name": "Mark Ronson - Topic",
            "url": "https://www.youtube.com/channel/UCm9XijVCOsRrxdx0giD_1fQ"
      }
   ],
   "time": "2025-07-16T20:40:31.824Z",
   "products": [
      "YouTube"
   ],
   "activityControls": [
      "YouTube watch history"
   ]
}
```

### Spotify listening history

```

```