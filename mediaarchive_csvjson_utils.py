import json
import csv
from datetime import datetime
import os

def save_entries_to_json(entries, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

def save_entries_to_csv(entries, file_path):
    fieldnames = ['id', 'date', 'title', 'body', 'images', 'videos']
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for entry in entries:
            row = {
                'id': entry['id'],
                'date': entry['date'],
                'title': entry['title'],
                'body': entry['body'],
                'images': '|'.join(entry['images']),
                'videos': '|'.join(entry['videos'])
            }
            writer.writerow(row)

def infer_date_from_path(file_path, root_dir):
    parts = file_path.split(os.sep)
    root_parts = root_dir.split(os.sep)
    year_index = len(root_parts)
    
    if year_index >= len(parts):
        return datetime.now().strftime("%Y-%m-%d")
    
    year = parts[year_index]
    month = '01'
    day = '01'

    # Check if the next part is a valid month
    if len(parts) > year_index + 1:
        possible_month = parts[year_index + 1]
        if possible_month.isdigit() and 1 <= int(possible_month) <= 12:
            month = possible_month.zfill(2)

    # Look for date in folder name
    for part in parts[year_index:]:
        if part.startswith(year):
            date_parts = part.split('-')
            if len(date_parts) >= 3:
                year, month, day = date_parts[:3]
                break

    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

def infer_date_from_filename(filename, folder_date):
    # Try to find a date in the filename
    date_formats = [
        "%Y-%m-%d",
        "%Y%m%d",
        "%Y-%m-%d %H.%M.%S",
    ]
    
    for date_format in date_formats:
        try:
            file_date = datetime.strptime(filename[:10], date_format).date()
            if file_date.year == int(folder_date[:4]):
                return file_date.strftime("%Y-%m-%d")
        except ValueError:
            pass
    
    # If no date found in filename, use the folder date
    return folder_date

def find_available_day(entries, year, month):
    days_in_month = (datetime(int(year), int(month) % 12 + 1, 1) - datetime(int(year), int(month), 1)).days
    day_counts = {str(day).zfill(2): 0 for day in range(1, days_in_month + 1)}
    
    for entry in entries:
        entry_date = datetime.strptime(entry['date'], "%Y-%m-%d")
        if entry_date.year == int(year) and entry_date.month == int(month):
            day_counts[str(entry_date.day).zfill(2)] += 1
    
    # Find the day with the least entries
    return min(day_counts, key=day_counts.get)

def create_entry(date, title, images, videos, part=None, total_parts=None):
    entry = {
        'id': f"{date}-{title.replace(' ', '_')}",
        'date': date,
        'title': title,
        'body': '',
        'images': images,
        'videos': videos
    }
    
    if part is not None and total_parts is not None:
        entry['id'] += f"_part{part}"
        entry['title'] += f" (Part {part} of {total_parts})"
        entry['body'] += f"\n\nThis is part {part} of {total_parts} for this date and folder."
    
    return entry

def process_media_files(entries, date, title, media_files):
    MAX_FILES_PER_POST = 100
    total_parts = (len(media_files) - 1) // MAX_FILES_PER_POST + 1
    
    for part in range(1, total_parts + 1):
        start_idx = (part - 1) * MAX_FILES_PER_POST
        end_idx = min(part * MAX_FILES_PER_POST, len(media_files))
        
        images = [file for file in media_files[start_idx:end_idx] if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
        videos = [file for file in media_files[start_idx:end_idx] if file.lower().endswith(('.mp4', '.mov', '.avi'))]
        
        entry = create_entry(date, title, images, videos, part, total_parts)
        entries.append(entry)
    
    return entries