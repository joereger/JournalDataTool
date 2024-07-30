import json
import re
from datetime import datetime
import blog_csvjson_utils

# Set the start date for processing events
start_date = datetime(2001, 10, 22, 0, 0)

# Load event, megalog, and image data
events = blog_csvjson_utils.load_json('mysql_data_exported/event.json')
megalogs = blog_csvjson_utils.load_json('mysql_data_exported/megalog.json')
images = blog_csvjson_utils.load_json('mysql_data_exported/image.json')

# Sort events by date (oldest to newest)
events.sort(key=lambda x: datetime.fromisoformat(x['date']))

# Process events to prepare data for CSV and JSON
processed_events = blog_csvjson_utils.process_events(events, megalogs, images)

# Add a datestamp to the filenames
datestamp = datetime.now().strftime('%Y%m%d%H%M%S')
csv_filename = f'exported_data/JoeregercomBlog_{datestamp}.csv'
json_filename = f'exported_data/JoeregercomBlog_{datestamp}.json'

# Save processed events to CSV and JSON
blog_csvjson_utils.save_events_to_csv(processed_events, csv_filename)
blog_csvjson_utils.save_events_to_json(processed_events, json_filename)

print(f"Finished processing and saving events to {csv_filename} and {json_filename}")
