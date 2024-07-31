import os
import json
from datetime import datetime
from mediaarchive_csvjson_utils import (
    save_entries_to_json,
    infer_date_from_path,
    infer_date_from_filename,
    find_available_day,
    process_media_files
)

def process_media_archive(root_dir):
    entries = []
    
    for year_dir in sorted(os.listdir(root_dir)):
        year_path = os.path.join(root_dir, year_dir)
        if not os.path.isdir(year_path) or not year_dir.isdigit():
            continue

        for subdir, _, files in os.walk(year_path):
            if not files:
                continue

            folder_date = infer_date_from_path(subdir, root_dir)
            folder_name = os.path.basename(subdir)
            
            # Group files by date
            date_groups = {}
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mov', '.avi')):
                    file_date = infer_date_from_filename(file, folder_date)
                    if file_date not in date_groups:
                        date_groups[file_date] = []
                    date_groups[file_date].append(os.path.join(subdir, file))

            # Process each date group
            for date, media_files in date_groups.items():
                title = folder_name if folder_name != year_dir else "Media"
                entries = process_media_files(entries, date, title, media_files)

    # Sort entries by date
    entries.sort(key=lambda x: x['date'])

    return entries

def main():
    root_dir = "source_data/mediaarchive"
    
    if not os.path.exists(root_dir):
        print(f"Error: The directory '{root_dir}' does not exist.")
        return

    entries = process_media_archive(root_dir)

    # Generate output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"exported_data/mediaarchive_output_{timestamp}.json"

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Save entries to JSON file
    save_entries_to_json(entries, output_file)

    print(f"Processed {len(entries)} entries.")
    print(f"Output saved to: {output_file}")

    # Print the first few entries to console for verification
    print("\nSample entries:")
    print(json.dumps(entries[:5], indent=2))

if __name__ == "__main__":
    main()