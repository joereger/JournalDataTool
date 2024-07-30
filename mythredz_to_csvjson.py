import json
from datetime import datetime
import mythredz_csvjson_utils

# Load mythredz data
threds = mythredz_csvjson_utils.load_json('mysql_data_exported/mythredz/thred.json')
posts = mythredz_csvjson_utils.load_json('mysql_data_exported/mythredz/post.json')

# Load existing combined data
existing_combined_data = mythredz_csvjson_utils.load_json('exported_data/joeregerposts_20240721105155.json')

# Process mythredz posts
processed_mythredz_posts = mythredz_csvjson_utils.process_mythredz_posts(posts, threds)

# Combine and sort all entries
all_entries = existing_combined_data + processed_mythredz_posts
all_entries = mythredz_csvjson_utils.combine_and_sort_entries(all_entries)

# Sort mythredz entries
sorted_mythredz_posts = mythredz_csvjson_utils.combine_and_sort_entries(processed_mythredz_posts)

# Add a datestamp to the filenames
datestamp = datetime.now().strftime('%Y%m%d%H%M%S')

# Combined files
combined_csv_filename = f'exported_data/Combined_JoeregercomBlog-and-Mythredz_{datestamp}.csv'
combined_json_filename = f'exported_data/Combined_JoeregercomBlog-and-Mythredz_{datestamp}.json'

# Mythredz-only files
mythredz_csv_filename = f'exported_data/Mythredz_{datestamp}.csv'
mythredz_json_filename = f'exported_data/Mythredz_{datestamp}.json'

# Save combined entries to CSV and JSON
mythredz_csvjson_utils.save_entries_to_csv(all_entries, combined_csv_filename)
mythredz_csvjson_utils.save_entries_to_json(all_entries, combined_json_filename)

# Save mythredz-only entries to CSV and JSON
mythredz_csvjson_utils.save_entries_to_csv(sorted_mythredz_posts, mythredz_csv_filename)
mythredz_csvjson_utils.save_entries_to_json(sorted_mythredz_posts, mythredz_json_filename)

print(f"Finished processing and saving combined entries to {combined_csv_filename} and {combined_json_filename}")
print(f"Finished processing and saving mythredz-only entries to {mythredz_csv_filename} and {mythredz_json_filename}")