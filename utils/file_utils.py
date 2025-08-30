
import json
import os
from typing import List, Optional

from utils.simple_logger import print_log


def export_to_json(data: List[object], input_filename: str, suffix="processed") -> Optional[str]:
    """
    Export filtered data to a JSON file with optional suffix
    """
    if not data or len(data) == 0:
        print_log(f"No data available for export: {input_filename} + '{suffix}'. Not writing anything.")
        return None

    # Create output filename
    filename = os.path.split(input_filename)[-1]
    base_name = os.path.splitext(filename)[0]
    extension = os.path.splitext(filename)[1]
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{os.path.basename(base_name)}-{suffix}{extension}")
    
    try:
        # Convert objects to dictionaries for JSON serialization
        json_data = [track.to_dict() for track in data]
        
        # Write filtered entries to output file
        with open(output_file, 'w', encoding='utf-8') as output:
            json.dump(json_data, output, indent=2, ensure_ascii=False)
        
        print_log(f"Data written to: {output_file}")
        return output_file
    
    except Exception as e:
        print_log(f"Error writing to {output_file}: {e}")
        return None

def export_to_csv(data: List[str], headerRow: str, input_filename: str, suffix="processed") -> Optional[str]:
    """
    Export filtered data to a CSV file with optional suffix
    """
    # Create output filename
    filename = os.path.split(input_filename)[-1]
    base_name = os.path.splitext(filename)[0]
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{os.path.basename(base_name)}-{suffix}.csv")

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