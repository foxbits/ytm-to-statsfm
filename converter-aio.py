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
    parser.add_argument("--ignore-videos", action="store_true", help="Specify in order to ignore videos watched on YouTube Music and process only songs")
    parser.add_argument("--ignore-songs", action="store_true", help="Specify in order to ignore songs and process only videos (starting from conversion step)")
    parser.add_argument("--use-pause", action="store_true", help="Specify in order to pause between each step")

    parser.add_argument("--skip-sanitize", action="store_true", help="Skip sanitization step (if already done)")
    parser.add_argument("--skip-convert", action="store_true", help="Skip conversion steps (if already done)")
    parser.add_argument("--skip-enrich", action="store_true", help="Skip enrichment steps (if already done)")
    parser.add_argument("--skip-report", action="store_true", help="Skip matched track analysis (import+export) (if already done)")
    
    parser.add_argument("--skip-sanitize-export", action="store_true", help="Skip sanitization - videos CSV generation step (if you already exported it)")
    parser.add_argument("--skip-report-export", action="store_true", help="Skip matched track analysis export (CSV report generation) for songs/videos (if you already exported it)")
    
    
    args = parser.parse_args()
    
    input_file = args.file
    base_name = Path(input_file).stem  # e.g., "watch-history"

    print_title("YouTube Music to Spotify Converter - All-in-One Pipeline")
    print_log(f"Input file: {input_file}")
    
    # Store generated error files    
    error_files = []

    # Store OKed files
    ok_files = []

    # Define output files as input file by default
    songs_file_base = base_name
    videos_file_base = base_name
    songs_file = input_file
    videos_file = input_file
    

    # Step 1.1: Sanitize and split input
    if args.skip_sanitize:
        print_log("Skipping step 1.1 - sanitization...")
    else:
        print_title("STEP 1.1: Sanitize and split input")
        cmd = f"python sanitizer.py --file {input_file}" + (args.ignore_videos and " --ignore-videos" or "")
        run_command(cmd, "Sanitizing and splitting input data")

        songs_file_base = f"{songs_file_base}.songs"
        songs_file = f"output\\{songs_file_base}.json"
        videos_file_base = f"{videos_file_base}.videos"
        videos_file = f"output\\{videos_file_base}.json"

        # Print error files if created
        sanitized_errors = f"output\\errors\\{base_name}.errors.json"
        if check_file_exists(sanitized_errors):
            error_files.append(sanitized_errors)

    if args.use_pause:
        input("Press Enter to continue to the next step...")
    

    # Step 1.2: Manual Review of Videos File
    if args.skip_sanitize or args.ignore_videos:
        print_log("Skipping step 1.2 - sanitization video review step...")
    else:
        has_videos = check_file_exists(videos_file)
        if has_videos:
            print_title("STEP 1.2: Manual Review of Videos File")
            cmd = f"python reporter-videos.py --file {videos_file} --import"
            if not args.skip_sanitize_export:
                cmd += " --export"
            
            run_command(cmd, "Reviewing and validating videos file")
            
            videos_file_base = f"{videos_file_base}.reviewed"
            videos_file = f"output\\{videos_file_base}.json"

    if args.use_pause:
        input("Press Enter to continue to the next step...")


    # Step 2.1 and 2.2: Conversion    
    if args.skip_convert:
        print_log("Skipping conversion step...")
    else:
        # Step 2.1: Convert the songs
        if not args.ignore_songs:
            has_songs = check_file_exists(songs_file)
            if has_songs:
                print_title("STEP 2.1: Convert songs to Spotify format")
                cmd = f"python converter.py --file {songs_file}"
                run_command(cmd, "Converting songs to Spotify format")
                
                songs_file_base = f"{songs_file_base}.spotify"
                songs_file = f"output\\{songs_file_base}.json"
            else:
                print_log("Skipping step 2.1 (songs conversion)")
        
        # Enrich videos
        if not args.ignore_videos:
            has_videos = check_file_exists(videos_file)
            if has_videos:
                # Step 3 - Videos processing
                print_title("STEP 2.2: Convert music videos to Spotify format")
                cmd = f"python converter.py --file {videos_file}"
                run_command(cmd, "Converting music videos to Spotify format")
                
                videos_file_base = f"{videos_file_base}.spotify"
                videos_file = f"output\\{videos_file_base}.json"
            else:
                print_log("Skipping step 2.2 (videos conversion)")

    if args.use_pause:
        input("Press Enter to continue to the next step...")


    # Step 3: Enrich with Spotify API track data
    if args.skip_enrich:
        print_log("Skipping enrichment step...")
    else:
        print_title("STEP 3: Enrich with Spotify track data")

        # Enrich songs
        if not args.ignore_songs:
            has_songs = check_file_exists(songs_file)
            if has_songs:
                cmd = f"python enricher.py --file {songs_file}"
                run_command(cmd, "Enriching songs with Spotify data")

                enriched_songs_ok = f"output\\ok\\{songs_file_base}.rich.ok.json"
                enriched_songs_errors = f"output\\errors\\{songs_file_base}.rich.errors.json"

                if check_file_exists(enriched_songs_ok):
                    ok_files.append(enriched_songs_ok)
                
                if check_file_exists(enriched_songs_errors):
                    error_files.append(enriched_songs_errors)
                
                songs_file_base = f"{songs_file_base}.rich.doubt"
                songs_file = f"output\\{songs_file_base}.json"

        # Enrich videos
        if not args.ignore_videos:
            has_videos = check_file_exists(videos_file)
            if has_videos:
                cmd = f"python enricher.py --file {videos_file}"
                run_command(cmd, "Enriching videos with Spotify data")

                enriched_videos_ok = f"output\\ok\\{videos_file_base}.rich.ok.json"
                enriched_videos_errors = f"output\\errors\\{videos_file_base}.rich.errors.json"

                if check_file_exists(enriched_videos_ok):
                    ok_files.append(enriched_videos_ok)

                if check_file_exists(enriched_videos_errors):
                    error_files.append(enriched_videos_errors)
                
                videos_file_base = f"{videos_file_base}.rich.doubt"
                videos_file = f"output\\{videos_file_base}.json"

    if args.use_pause:
        input("Press Enter to continue to the next step...")


    # Step 4: Generate CSV reports for doubt cases
    if args.skip_report:
        print_log("Skipping CSV analysis / reporting step...")
    else:
        print_title("STEP 4: Generate CSV reports for manual review")

        # Report for songs
        if not args.ignore_songs:
            has_songs = check_file_exists(songs_file)
            if has_songs:
                cmd = f"python reporter.py --file {songs_file} --import"
                if not args.skip_report_export:
                    cmd += " --export"
                
                run_command(cmd, "Generating CSV analysis / reporting for songs doubt cases")
                
                validated_songs = f"output\\ok\\{songs_file_base}.validated.json"
                invalid_songs = f"output\\errors\\{songs_file_base}.invalid.json"

                if check_file_exists(validated_songs):
                    ok_files.append(validated_songs)

                if check_file_exists(invalid_songs):
                    error_files.append(invalid_songs)

        # Report for videos
        if not args.ignore_videos:
            has_videos = check_file_exists(videos_file)
            if has_videos:
                cmd = f"python reporter.py --file {videos_file} --import"
                if not args.skip_report_export:
                    cmd += " --export"
                
                run_command(cmd, "Generating CSV analysis / reporting for videos doubt cases")

                validated_videos = f"output\\ok\\{videos_file_base}.validated.json"
                invalid_videos = f"output\\errors\\{videos_file_base}.invalid.json"

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