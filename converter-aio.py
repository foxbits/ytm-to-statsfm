#!/usr/bin/env python3
"""
Converter All-in-One (AIO) - Automated pipeline for processing YouTube Music history to Spotify format
Executes the full workflow: sanitize -> convert -> enrich -> report
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path
from utils.simple_logger import print_log


def run_command(command: str, description: str, is_fatal: bool = True) -> bool:
    """
    Run a shell command and return success status
    """
    print_log(f"Running: {description}")
    print_log(f"Command: {command}")
    
    try:
        subprocess.run(
            command, 
            shell=True, 
            check=True
        )
        print_log(f"✓ Success: {description}")
        return True
    except subprocess.CalledProcessError as e:
        print_log(f"✗ Failed: {description}")
        print_log(f"Error: {e}")
        if is_fatal:
            print_log("Fatal error occurred. Exiting...")
            sys.exit(1)
        return False


def check_file_exists(filepath: str) -> bool:
    """
    Check if a file exists and log the result
    """
    if os.path.exists(filepath):
        print_log(f"✓ File EXISTS: {filepath}")
        return True
    else:
        print_log(f"✗ File DOES NOT EXIST: {filepath}")
        return False

def print_title(text):
    print_log("\n\n")
    print_log("=" * 80)
    print_log(text)
    print_log("=" * 80)

def main():
    parser = argparse.ArgumentParser(description="All-in-one YouTube Music to Spotify converter pipeline")
    parser.add_argument("--file", required=True, help="Input JSON file with YouTube Music watch history")
    parser.add_argument("--skip-sanitize", action="store_true", help="Skip sanitization step (if already done)")
    parser.add_argument("--skip-convert", action="store_true", help="Skip conversion steps (if already done)")
    parser.add_argument("--skip-enrich", action="store_true", help="Skip enrichment steps (if already done)")
    parser.add_argument("--skip-report", action="store_true", help="Skip report generation (if already done)")
    parser.add_argument("--ignore-videos", action="store_true", help="Specify in order to ignore videos watched on YouTube Music and process only songs")
    parser.add_argument("--use-pause", action="store_true", help="Specify in order to pause between each step")
    
    args = parser.parse_args()
    
    input_file = args.file
    base_name = Path(input_file).stem  # e.g., "watch-history"

    print_title("YouTube Music to Spotify Converter - All-in-One Pipeline")
    print_log(f"Input file: {input_file}")
    
    # Check if input file exists
    if not check_file_exists(input_file):
        print_log("Input file not found. Exiting.")
        sys.exit(1)

    # Store generated error files    
    error_files = []

    # Store OKed files
    ok_files = []

    # Step 1: Sanitize and split input

    # Define sanitizer output files
    sanitized_songs = f"output\\{base_name}.songs.json"
    sanitized_videos = f"output\\{base_name}.videos.json"
    sanitized_validated_videos = f"output\\{base_name}.videos.reviewed.json"
    sanitized_errors = f"output\\errors\\{base_name}.errors.json"
    

    if args.skip_sanitize:
        print_log("Skipping sanitization step...")
    else:
        print_title("STEP 1: Sanitize and split input")
        cmd = f"python sanitizer.py --file {input_file}" + (args.ignore_videos and " --ignore-videos" or "")
        run_command(cmd, "Sanitizing and splitting input data")

        # Print error files if created
        if check_file_exists(sanitized_errors):
            error_files.append(sanitized_errors)

    if args.use_pause:
        input("Press Enter to continue to the next step...")

    # Step 2 + 3 + 4: Conversion

    # Define converter output files
    spotified_songs = f"output\\{base_name}.songs.spotify.json"
    # Define expected output files
    spotified_videos = f"output\\{base_name}.videos.reviewed.spotify.json"
    
    if args.skip_convert:
        print_log("Skipping conversion step...")
    else:
        # Step 2: Convert the songs
        has_songs = check_file_exists(sanitized_songs)
        if has_songs:
            print_title("STEP 2: Convert songs to Spotify format")
            cmd = f"python converter.py --file {sanitized_songs}"
            run_command(cmd, "Converting songs to Spotify format")
        
        has_videos = check_file_exists(sanitized_videos)
        if has_videos:
            # Step 3: Manual Review of Videos File
            print_title("STEP 3: Manual Review of Videos File")
            cmd = f"python reporter-videos.py --file {sanitized_videos} --export --import"
            run_command(cmd, "Reviewing and validating videos file")
        
        has_videos = check_file_exists(sanitized_validated_videos)
        if has_videos:
            # Step 4 - Videos processing
            print_title("STEP 4: Convert music videos to Spotify format")
            cmd = f"python converter.py --file {sanitized_validated_videos}"
            run_command(cmd, "Converting music videos to Spotify format")
        else:
            print_log("Skipping steps 3 and 4 (videos) since either --ignore-videos is enabled or no videos have been found")

    if args.use_pause:
        input("Press Enter to continue to the next step...")

    # Step 5: Enrich with Spotify API track data

    # Define enricher output files
    enriched_songs_ok = f"output\\ok\\{base_name}.songs.spotify.rich.ok.json"
    enriched_songs_doubt = f"output\\{base_name}.songs.spotify.rich.doubt.json"
    enriched_songs_errors = f"output\\errors\\{base_name}.songs.spotify.rich.errors.json"
    enriched_videos_ok = f"output\\ok\\{base_name}.videos.reviewed.spotify.rich.ok.json"
    enriched_videos_doubt = f"output\\{base_name}.videos.reviewed.spotify.rich.doubt.json"
    enriched_videos_errors = f"output\\errors\\{base_name}.videos.reviewed.spotify.rich.errors.json"

    if args.skip_enrich:
        print_log("Skipping enrichment step...")
    else:
        print_title("STEP 5: Enrich with Spotify track data")

        # Enrich songs
        has_songs = check_file_exists(spotified_songs)
        if has_songs:
            cmd = f"python enricher.py --file {spotified_songs}"
            run_command(cmd, "Enriching songs with Spotify data")

            if check_file_exists(enriched_songs_ok):
                ok_files.append(enriched_songs_ok)
            
            if check_file_exists(enriched_songs_errors):
                error_files.append(enriched_songs_errors)

        # Enrich videos
        has_videos = check_file_exists(spotified_videos)
        if has_videos:
            cmd = f"python enricher.py --file {spotified_videos}"
            run_command(cmd, "Enriching videos with Spotify data")

            if check_file_exists(enriched_videos_ok):
                ok_files.append(enriched_videos_ok)

            if check_file_exists(enriched_videos_errors):
                error_files.append(enriched_videos_errors)

    if args.use_pause:
        input("Press Enter to continue to the next step...")

    # Step 6: Generate CSV reports for doubt cases

    # Define output files
    validated_songs = f"output\\ok\\{base_name}.songs.spotify.rich.doubt.validated.json"
    validated_videos = f"output\\ok\\{base_name}.videos.reviewed.spotify.rich.doubt.validated.json"
    invalid_songs = f"output\\errors\\{base_name}.songs.spotify.rich.doubt.invalid.json"
    invalid_videos = f"output\\errors\\{base_name}.videos.reviewed.spotify.rich.doubt.invalid.json"

    if args.skip_report:
        print_log("Skipping CSV analysis / reporting step...")
    else:
        print_title("STEP 6: Generate CSV reports for manual review")

        # Report for songs
        has_songs = check_file_exists(enriched_songs_doubt)
        if has_songs:
            cmd = f"python reporter.py --file {enriched_songs_doubt} --export --import"
            run_command(cmd, "Generating CSV analysis / reporting for songs doubt cases")

            if check_file_exists(validated_songs):
                ok_files.append(validated_songs)

            if check_file_exists(invalid_songs):
                error_files.append(invalid_songs)

        # Report for videos
        has_videos = check_file_exists(enriched_videos_doubt)
        if has_videos:
            cmd = f"python reporter.py --file {enriched_videos_doubt} --export --import"
            run_command(cmd, "Generating CSV analysis / reporting for videos doubt cases")

            if check_file_exists(validated_videos):
                ok_files.append(validated_videos)

            if check_file_exists(invalid_videos):
                error_files.append(invalid_videos)

    print_title("Pipeline execution complete!")

    # Print the success files:
    if len(ok_files) > 0:
        print_log("You can use the following successfully converted files:")
        for f in ok_files:
            print_log(f" ✓ {f}")
    else:
        print_log("No successfully converted files found.")
    
    # Print the error files:
    if len(error_files) > 0:
        print_log("The following error files were generated:")
        for f in error_files:
            print_log(f" ✗ {f}")
        print_log("Please review and address the issues in these files and then re-run the process on them individually. See the README for details.")
    else:
        print_log("No error files found.")


if __name__ == "__main__":
    main()