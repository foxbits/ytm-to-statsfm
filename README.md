This repo contains a set of python scripts that allow you to convert the YouTube Music listening history format (songs only) into Spotify listening history format (with some details using default values), making it importable into [stats.fm](http://stats.fm) and other applications that use this format. At the end of this page there is an example for the same song in the two different formats.

It is based on a multi-step process:
1. data sanitization (automatic)
2. data conversion to the Spotify listening history format (automatic)
3. data enrichment using the official Spotify Search API (to find to actual spotify track ids, which are mandatory) (automatic)
4. matched track score analysis in case of multiple track matches in a single search (semi-automatic)
     - nobody wants to import in their listening history unwanted tracks, and since YTM provides only artist & track name, the match with Spotify is, most of the times, non-deterministic (you might have encountered this with playlist converters)
     - if track API search result (from Spotify) is exact OR if artist & track name text fuzzy match score is higher than a defined threshold => the track considered a match (automatic)
     - otherwise, a report is generated which requires manual review to select the right track from a list of returned results (manual)
     - in this case, the process is able to import a manually reviewed file and then process it normally (automatic)

Each step of the process is available as a standalone script, in order to allow you to run / re-do each step manually (see [2. Processing the History](#2-processing-the-history)), or as part of an automated all-in-one end-to-end script.

- [1. Pre-requisites](#1-pre-requisites)
  - [1.1. Exporting your YouTube Music Data](#11-exporting-your-youtube-music-data)
  - [1.2. Installing software](#12-installing-software)
  - [1.3 Setting the environment variables](#13-setting-the-environment-variables)
- [2. Processing the History (Individual Scripts)](#2-processing-the-history-individual-scripts)
  - [2.1. Data Sanitization](#21-data-sanitization)
  - [2.2 Data Conversion to Spotify listening history format](#22-data-conversion-to-spotify-listening-history-format)
  - [2.3 Data enrichment using the official Spotify Search API](#23-data-enrichment-using-the-official-spotify-search-api)
  - [2.4 Matched track score analysis](#24-matched-track-score-analysis)
  - [2.5 Example of full flow](#25-example-of-full-flow)
- [3. Processing the History (All In One)](#3-processing-the-history-all-in-one)
- [4. Caveats / Troubleshooting](#4-caveats--troubleshooting)
- [5. Example of the same song in the 2 different formats](#5-example-of-the-same-song-in-the-2-different-formats)
  - [5.1 YouTube (Music) listening history (INPUT)](#51-youtube-music-listening-history-input)
  - [5.2 Spotify listening history (OUTPUT)](#52-spotify-listening-history-output)


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

## 2. Processing the History (Individual Scripts)

**Note**: all the scripts will output informational logs to both screen and to the file `output/logs.txt`.

### 2.1. Data Sanitization

1. Copy your `watch-history.json` into the same folder as these scripts
2. Run `python sanitizer.py`
   1. This script uses by default as input file a `watch-history.json` available in the same folder; you can use a different file if you want, by specifying `--file your-file.json`
3. The script will run (time depends on your history size). It will then output info regarding its status.
4. The script exports 3 files in the `output` folder, based on the original file name:
   1. `.songs.json` - the list of songs detected on YT Music listening history. These are 100% accurate ✅
   2. `.videos.json` - the list of music videos detected on your YT Music listening history; These can be or cannot be accurate when converted to tracks 🤔
      - if you run the program with `--ignore-videos` flag, then the music videos are not processed and are put in a `.skipped.json` list
      - Since music videos naming can follow or not follow deterministic naming standards, it is recommended to do a double check and edit / correct the entries in this file before importing; otherwise, you will have to review the matchings anyways in the final step
      - For more details see #2 from [Caveats / Troubleshooting]((#4-caveats--troubleshooting))
   3. `.errors.json` - the list of entries in the history that cannot be processed ❌
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

1. Run `python converter.py --file output\\watch-history.*.json`
   1. Run it with the `songs` and/or `videos` files 
   2. Alternatively you can run it with any file that follows the YTM format defined in [`objects/ytm_processed_track.py`](objects/ytm_processed_track.py) if you use custom files
2. You will obtain a new json file named `<your-file>.spotify.json` in the `output` directory
3. This full file follows the exact Spotify listening history format, but is populated only with the data available in YTM history (artist name, track name, timestamp) and with the default parameters (some from env vars). You most likely cannot import this file in many places. The full data is populated in next step (the enrichment).

### 2.3 Data enrichment using the official Spotify Search API

Since YTM does provide only the artist name, track title and timestamp when played, a lot of the specific Spotify data is missing, most importantly the Spotify Track ID, the Album Name and the actual duration of the track.

This extra data (the most important being the spotify track id) is identified through searching the Spotify Metadata API by artist & track name. This result will sometimes return multiple entries.

1. Run `python enricher.py --file output\\watch-history.*.spotify.json`
   1. Run it with the `songs` and/or `videos` files
   2. Alternatively you can run it with any file that follows the Spotify format defined in [`spotify/spotify_listening_history.py`](spotify/spotify_listening_history.py) if you use custom files
2. Wait for it to run. If your file data is big, you will encounter Spotify Rate limiting (180 searches / minute) so it might take a while.
3. You will obtain a new set of json files:
   1. `<your-file>.rich.ok.json` ✅
      - contains all the successfully matched tracks with metadata; a track is matched if:
         - has a matching score with the top result above `SCORE_TRACKS_WEIGHT`; 
         - spotify returns them as exact matches (results for exact track name and artist)
         - you can see the score in the `metadata.match_score`
      - `tracks` array populated with top spotify results
      - this file can be directly used as final ✅
   2. `<your-file>.rich.doubt.json` 🤔
      - contains the tracks that cannot be safely matched with a result automatically
      - they need manual validation
      - this file is used in next step
   3. `<your-file>.rich.errors.json` ❌
      - contains all the tracks that ended in error either when communicating with the Spotify API (e.g. rate limiting retries ending, unknown errors) or in not being able to identify any tracks
      - you can inspect these errors and eventually do some edits on it and re-process (restart this flow)


### 2.4 Matched track score analysis

In the previous step, there is a `.doubt.json` file generated which contains tracks, in the Spotify listening history format (but with incomplete data), that have search results that have been returned by Spotify but could not be considered as safe matches, according to the  `MINIMUM_MATCH_DECISION_SCORE` setting.

This step facilitates two functions: 
- exporting a **CSV report** which contains, as rows, all the entries from the listening history that could not be safely matched, as well as a column with all the potential matches (numbered list) and their details (score, artist, track):
  - **id**: incremental number, id of each row (corresponding to the id of the ordered tracks from the json in order of appeareance)
  - **original_track**: the original track name as found in the YouTube Music listening history
  - **original_artist**: the original artist name as found in the YouTube Music listening history
  - **your_choice**: 
    - a number from the `choices` column representing the track number from the possible matches list that you consider a correct match
    - `1` <= `number of possible matches` <= `SPOTIFY_SEARCH_RESULTS_LIMIT`
    - use `-1` if you consider that none of the matches are correct and the song should not be used in the listening history; if no result from the list seems correct, it might mean that the song does not exist in Spotify
  - **choices**: a list of songs, one per row, that have been returned by Spotify as potential matches for the current track in the format `<id>. (<score>)<artist> - <track>`
- importing the same **CSV report** with the `your_choice` column correctly populated for all rows 


How to use it:

1. Run `python reporter.py --file output\\<your-file>.rich.doubt.json --export --import`
   - `--file` flag allows specifying the json file to process; this should be the `.doubt.json` file generated at previous step
   - `--export` flag specifies to the script to execute the export step
   - `--import` flag specifies to the script to execute the import step (if both are specified, first the export is done, then the script waits for user input, then the import is done);
2. The script will generate a CSV file (`output\\<your-file>.rich.doubt.validator.csv`) in the format described above and then it will wait for user input (RETURN key, do not press it!)
3. The user (you) must open the CSV file and fill in, for all rows, the `your_choice` column with a valid number
4. The user (you) must press the RETURN key in the script window; the script now will read back the CSV and validate the user's (your) choices
   - make sure you have filled in the CSV correctly, otherwise there will be errors
   - make sure that the json file and the csv file are in the same directory (if running the script manually or on custom files / directories)
   - do not change the order of rows from the CSV; do not change the order of rows from the JSON; do not change the order of tracks from the JSON
5.  The script will generate:
    - a new file `output\\<your-file>.rich.doubt.validated.json`, this file can be directly used as final ✅
    - a new file `output\\<your-file>.rich.doubt.invalid.json`, containing items marked as not matched in the CSV - this file cannot be used as final ❌



### 2.5 Example of full flow

```
#1 - sanitize and split input
python sanitizer.py --file watch-history-small.json
=> output\\watch-history-small.songs.json,
=> output\\watch-history-small.videos.json
=> output\\watch-history-small.errors.json

#2 - convert the songs
python converter.py --file output\\watch-history-small.songs.json 
=> output\\watch-history-small.songs.spotify.json

#3 - manually double check the videos json output\\watch-history-small.videos.json

#4 - convert the music videos
python converter.py --file output\\watch-history-small.videos.json
=> output\\watch-history-small.videos.spotify.json

#5 - enrich the songs and/or videos with spotify track data
python enricher.py --file output\\watch-history-small.songs.spotify.json
=> output\\watch-history-small.songs.spotify.rich.ok.json
=> output\\watch-history-small.songs.spotify.rich.doubt.json
=> output\\watch-history-small.songs.spotify.rich.errors.json

python enricher.py --file output\\watch-history-small.videos.spotify.json
=> output\\watch-history-small.videos.spotify.rich.ok.json
=> output\\watch-history-small.videos.spotify.rich.doubt.json
=> output\\watch-history-small.videos.spotify.rich.errors.json

#6 - generate the CSV report for the songs and/or videos in doubt, fill it in, then import it back
python reporter.py --file output\\watch-history-small.songs.spotify.rich.doubt.json --import --export
=> output\\watch-history-small.songs.spotify.rich.doubt.validator.csv
=> output\\watch-history-small.songs.spotify.rich.doubt.validated.json

python reporter.py --file output\\watch-history-small.videos.spotify.rich.doubt.json --import --export
=> output\\watch-history-small.videos.spotify.rich.doubt.validator.csv
=> output\\watch-history-small.videos.spotify.rich.doubt.validated.json
=> output\\watch-history-small.videos.spotify.rich.doubt.invalid.json

#7 - use the successfully created files
- output\\watch-history-small.songs.spotify.rich.ok.json
- output\\watch-history-small.videos.spotify.rich.ok.json
- output\\watch-history-small.songs.spotify.rich.doubt.validated.json
- output\\watch-history-small.videos.spotify.rich.doubt.validated.json
- any errored files that you re-process manually later

```


## 3. Processing the History (All In One)

This is a wrapper around the previous steps, intended to be used as an all-in-one script (easier to use). 

**Note**: It is important to know that this script does not process the songs that end up with errors when interpreting / transforming the listening history. It will generate the detailed `.error` files as described in the previous chapters, inform about them during the process and at the end and will log them to `output\\logs.txt`. To reprocess the error files (it requires manual intervention in editing the JSONs most of the times), the steps from the previous chapter must be used individually.

How to use:
1. Run `python converter-aio.py --file watch-history.json`
   1. You can use `--ignore-videos` if you want to ignore the music videos found in the YouTube Music history (as specified in the individual steps and in [Caveats / Troubleshooting]((#4-caveats--troubleshooting))), as YouTube videos are ignored by default
   2. You can use `--skip-**` instructions to skip certain steps of the process (simulate individual steps or only run from a certain step forward):
      1. `--skip-sanitize` - skip first step (history sanitization)
      2. `--skip-convert` - skip second step (conversion of history to spotify file format)
      3. `--skip-enrich` - skip third step (data enrichment from Spotify API)
      4. `--skip-report` - skips the final step (manual score matching - export & import)
2. Follow the instruction on screen
   1. any errors will stop the process and it needs to be started again
   2. at some points there will be instructions on screen which require manual intervention
3. At the end, a small report will be printed to the screen (the full log trail can be also found inside `output\\logs.txt`), the main points are:
   1. the *successfully converted files* - these can be used ✅
   2. the *error files* - these are errors and need to be verified, manually edited and re-processed from the failed step:
      1. `<your-file>.errors.json` => failed at **sanitize** step
      2. `<your-file>.[songs|videos].spotify.rich.errors.json` => failed at **enrich** step
      2. `<your-file>.[songs|videos].spotify.rich.doubt.invalid.json` => marked as not matched at **score analysis** step



## 4. Caveats / Troubleshooting

1. This does not process data watched on the YouTube site itself, only on YouTube Music, because the Google Takeout data for listening history does not contain video type, therefore music videos cannot be identified.
2. I recommend you to test first with a small portion of your data (just pick a few entries from the array and create a `watch-history-small.json`); if everything is ok, go with the full data
3. The script runs by default without the `--ignore-videos` flag. 
   As you know, on YT Music you can both listen to songs and watch videos (which are basically YouTube videos). 
   These videos often do not have standard track artist / title naming format and usually put everything in the title (since they are YT videos) - e.g. "Artist - Song | Official Audio" and other variations. This means that the script has to do some non-deterministic guessing as in what's the artist and the song title in such videos, which often fails if you want a lot of music videos with non-standard formatting. Therefore, you can choose to ignore such videos watched on YT Music (note: videos watched on YouTube itself are automatically ignored). If you choose not to ignore them, the script tries to sanitize them as best as it can, following the format <artist-name><split-chars><song-title> and stripping any Official* (with/without paranthesis) from the song
4. In case of rapidfuzz related errors, get the latest build version from [here](https://www.piwheels.org/project/rapidfuzz/) and install it with `pip install rapidfuzz==<version> --force-reinstall --no-deps`
5. For files that end-up with errors (listed in previous steps), they cannot be retried if you don't edit anything in the process:
      1. `<your-file>.errors.json` => failed at **sanitize** step
         1. if you want to retry this, you have to manually edit this file to make sure it has valid artist (`subtitles[0].name`) and track name (`title`)
         2. after fixing the file, restart it from step 1, using the file as input file
      2. `<your-file>.[songs|videos].spotify.rich.errors.json` => failed at **enrich** step
         1. it's usually due to spotify errors (e.g. unavailable, rate limiting, random errors);
         2. technically they can be retried without changing the file, since it's usually Spotify's fault
         3. but certain errors might be due to weird entries in history and might require track name (`master_metadata_track_name`) / artist (`master_metadata_album_artist_name`) edit
      3. `<your-file>.[songs|videos].spotify.rich.doubt.invalid.json` => marked as not matched at **score analysis** step
         1. most likely this file cannot be retried
         2. it means Spotify returned some tracks as possible matches that you marked as incorrect (you didn't find any of the results correct)
         3. if the input track name (`master_metadata_track_name`) and artist (`master_metadata_album_artist_name`) are correct, then it means Spotify really doesn't have the track
         4. if the input track name and artist are incorrect, then edit them end retry the file from the **enrich** step
         5. what you can also try is to increase the `SPOTIFY_SEARCH_RESULTS_LIMIT` to make Spotify return more results


## 5. Example of the same song in the 2 different formats

### 5.1 YouTube (Music) listening history (INPUT)

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

### 5.2 Spotify listening history (OUTPUT)

```
{
    "ts": "2025-07-16T20:40:31.824Z",
    "platform": "ios",
    "ms_played": 217466,
    "conn_country": "US",
    "ip_addr": "127.0.0.1",
    "master_metadata_track_name": "Nothing Breaks Like a Heart (feat. Miley Cyrus)",
    "master_metadata_album_artist_name": "Mark Ronson, Miley Cyrus",
    "master_metadata_album_album_name": "Nothing Breaks Like a Heart (feat. Miley Cyrus)",
    "spotify_track_uri": "spotify:track:27rdGxbavYJeBphck5MZAF",
    "episode_name": null,
    "episode_show_name": null,
    "spotify_episode_uri": null,
    "audiobook_title": null,
    "audiobook_uri": null,
    "audiobook_chapter_uri": null,
    "audiobook_chapter_title": null,
    "reason_start": "playbtn",
    "reason_end": "trackdone",
    "shuffle": null,
    "skipped": false,
    "offline": false,
    "offline_timestamp": null,
    "incognito_mode": false
  }
```