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
## Caveats / Troubleshooting

1. It does not process data watched on the YouTube site itself, because the Google Takeout data for listening history does not contain video type, therefore music videos cannot be identified.
