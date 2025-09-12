
import json
import os
import platform
import subprocess
from typing import List, Optional

from utils.simple_logger import print_log

def generate_output_filename(input_filename: str, suffix="processed", separator=".", new_extension = None, parent_directory = "output") -> str:
    """
    Append a suffix to the input filename before the file extension.
    """
    filename = os.path.split(input_filename)[-1]
    base_name = os.path.splitext(filename)[0]
    extension = os.path.splitext(filename)[1]
    output_dir = parent_directory
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{os.path.basename(base_name)}{separator}{suffix}{new_extension or extension}")
    return output_file

def export_to_json(data: List[object], input_filename: str, suffix="processed", separator=".", parent_directory = "output") -> Optional[str]:
    """
    Export filtered data to a JSON file with optional suffix
    """
    if not data or len(data) == 0:
        print_log(f"No data available for export: {input_filename} + '{suffix}'. Not writing anything.")
        return None

    # Create output filename
    output_file = generate_output_filename(input_filename, suffix, separator, parent_directory=parent_directory)

    try:
        # Convert objects to dictionaries for JSON serialization
        json_data = [(track if isinstance(track, dict) else track.to_dict()) for track in data]
        
        # Write filtered entries to output file
        with open(output_file, 'w', encoding='utf-8') as output:
            json.dump(json_data, output, indent=2, ensure_ascii=False)
        
        print_log(f"Data written to: {output_file}")
        return output_file
    
    except Exception as e:
        print_log(f"Error writing to {output_file}: {e}")
        return None

def export_to_csv(data: List[str], headerRow: str, input_filename: str, suffix="processed", separator=".") -> Optional[str]:
    """
    Export filtered data to a CSV file with optional suffix
    """
    if not data or len(data) == 0:
        print_log(f"No data available for export: {input_filename} + '{suffix}'. Not writing anything.")
        return None

    # Create output filename
    output_file = generate_output_filename(input_filename, suffix, separator)

    try:
        # Write filtered entries to output file
        with open(output_file, 'w', encoding='utf-8') as output:
            output.write(headerRow + "\n")
            output.write("\n".join(data))

        print_log(f"Data written to: {output_file}")
        return output_file

    except Exception as e:
        print_log(f"Error writing to {output_file}: {e}")
        return None

def export_to_csv(contents: str, input_filename: str, suffix="processed", separator=".") -> Optional[str]:
    """
    Export filtered data to a CSV file with optional suffix
    """
    if not contents or len(contents) == 0:
        print_log(f"No data available for export: {input_filename} + '{suffix}'. Not writing anything.")
        return None
    
    # Create output filename
    output_file = generate_output_filename(input_filename, suffix, separator, new_extension=".csv")

    try:
        # Write filtered entries to output file
        with open(output_file, 'w', encoding='utf-8') as output:
            output.write(contents)

        print_log(f"Data written to: {output_file}")
        return output_file

    except Exception as e:
        print_log(f"Error writing to {output_file}: {e}")
        return None

def open_file(file_path: str):
    """
    Open a file using the default application based on the operating system
    """
    try:
        if platform.system() == 'Windows':
            os.startfile(file_path)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.run(['open', file_path])
        else:  # Linux and other OS
            subprocess.run(['xdg-open', file_path])
    except Exception as e:
        print_log(f"Error opening file {file_path}: {e}")