import csv
import json
import re

# Function to load JSON data from a file
def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

# Function to clean description and comments
def clean_description(desc):
    # Ensure desc is a string and remove any unsupported characters
    if desc is None:
        desc = ''
    desc = re.sub(r'[^\x00-\x7F]+', '', str(desc))
    # Replace newline characters with a space
    return desc.replace("\r\n", " ").replace("\n", " ")

# Function to save events to CSV
def save_events_to_csv(events, file_path):
    fieldnames = ['date', 'category', 'title', 'body', 'datablogging.eventid', 'datablogging.logid', 'images']
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for event in events:
            writer.writerow(event)

# Function to save events to JSON
def save_events_to_json(events, file_path):
    with open(file_path, 'w') as jsonfile:
        json.dump(events, jsonfile, indent=4)

# Function to process events and prepare data for CSV and JSON
def process_events(events, megalogs, images):
    processed_events = []
    
    for event in events:
        if event['accountid'] != 50:
            continue
        
        # Find the megalog name
        megalog_name = next((megalog['name'] for megalog in megalogs if megalog['logid'] == event['logid']), None)
        if not megalog_name:
            continue

        # Clean the comments for the event body
        event_body = clean_description(event['comments'])

        # Add simplified image data
        event_images = [
            {
                'imageid': image['imageid'],
                'filename': image['filename'],
                'description': clean_description(image.get('description', ''))
            }
            for image in images if image['eventid'] == event['eventid']
        ]

        event_data = {
            'date': event['date'],
            'category': megalog_name,
            'title': clean_description(event['title']),
            'body': event_body,
            'datablogging.eventid': event['eventid'],
            'datablogging.logid': event['logid'],
            'images': json.dumps(event_images) if event_images else ''
        }
        
        processed_events.append(event_data)
        
        # Log status for each processed event (commented out)
        # print(f"Processed event: {event['date']} - {event['title']}")
    
    return processed_events
