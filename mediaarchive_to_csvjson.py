import os
import json
import re
from datetime import datetime
from mediaarchive_csvjson_utils import (
    save_entries_to_json,
    infer_date_from_path,
    infer_date_from_filename,
    find_available_day,
    process_media_files
)

def clean_title(title, date):
    # Remove date from the beginning of the title if it matches the entry date
    date_pattern = r'^\d{4}-\d{2}-\d{2}-'
    if re.match(date_pattern, title):
        title = re.sub(date_pattern, '', title).strip()
    
    # Remove "(Part X of Y)" if Y is 1 or if X equals Y
    title = re.sub(r'\s*\(Part (\d+) of (\d+)\)\s*', lambda m: "" if m.group(2) == "1" or m.group(1) == m.group(2) else f" (Part {m.group(1)} of {m.group(2)})", title)
    
    # If title is empty or just a number, use the date
    if not title.strip() or title.strip().isdigit():
        title = date
    
    return title.strip()

def process_media_archive(root_dir):
    entries = []
    
    for year_dir in sorted(os.listdir(root_dir)):
        year_path = os.path.join(root_dir, year_dir)
        if not os.path.isdir(year_path) or not year_dir.isdigit():
            continue

        for subdir, _, files in os.walk(year_path):
            # Skip .thumbnails folders
            if os.path.basename(subdir) == ".thumbnails":
                continue

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
                title = clean_title(title, date)
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

    # Generate output filename with timestamp in the format YYYY-MM-DD-HHMMam/pm
    timestamp = datetime.now().strftime("%Y-%m-%d-%I%M%p").lower()
    output_file = f"exported_data/MediaArchive_output_{timestamp}.json"

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