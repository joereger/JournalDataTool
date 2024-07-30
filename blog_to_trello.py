import json
import os
import re
from datetime import datetime, timedelta
from html import unescape
from termcolor import colored
import blog_trello_utils

# Set the start date for processing events
start_date = datetime(2014, 6, 16, 0, 0)

# Function to clean and format the card title
def format_card_title(megalog_name, title, logid):
    # Allow standard characters including dashes and apostrophes
    clean_title = re.sub(r'[^a-zA-Z0-9\s\-\']', '', title)  # Allow dashes and apostrophes
    clean_title = re.sub(r'<.*?>', '', clean_title).strip()
    clean_title = unescape(clean_title)
    if logid == 1:  # If the logid is 1, do not prepend the megalog name
        return clean_title
    else:
        return f"{megalog_name}: {clean_title}"

# Function to remove special formatting from comments
def clean_comments(comments):
    comments = comments.replace("\r\n", " ").replace("\n", " ").strip()
    return comments

# Function to remove HTML tags from a string
def remove_html_tags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

# Function to clean image descriptions
def clean_image_description(description):
    if description is None:
        return ''
    return description.replace("\r\n", " ").replace("\n", " ").strip()

# Function to load JSON data from a file
def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

# Load event, megalog, and image data
events = load_json('mysql_data_exported/event.json')
megalogs = load_json('mysql_data_exported/megalog.json')
images = load_json('mysql_data_exported/image.json')

# Sort events by date (oldest to newest)
events.sort(key=lambda x: datetime.fromisoformat(x['date']))

# Function to find the megalog name by logid
def find_megalog_name(logid):
    for megalog in megalogs:
        if megalog['logid'] == logid:
            return megalog['name']
    return None

# Function to calculate a deterministic position based on the event date
def calculate_pos(event_date, base_date, total_units):
    days_since_start = (event_date - base_date).days
    return (1 - (days_since_start / total_units)) * 1000  # Inverse and normalize to Trello pos range

# Load API keys and tokens
api_keys = blog_trello_utils.load_api_keys('api_keys_and_tokens.txt')
api_key = api_keys['trello_api_key']
token = api_keys['trello_token']

# Initialize requests queue
requests_queue = []

# Process the sorted event objects
for event in events:  # Removed limiting to 10 for general processing
    # Convert event date string to datetime object
    event_date = datetime.fromisoformat(event['date'])

    # Skip events before the start date
    if event_date < start_date:
        continue

    # Determine the board name and base date for position calculation
    if event_date.year < 2000:
        if event_date.year < 1980:
            board_name = "Out with the Old 1970s Edition"
            base_date = datetime(1970, 1, 1)
        elif event_date.year < 1990:
            board_name = "Out with the Old 1980s Edition"
            base_date = datetime(1980, 1, 1)
        else:
            board_name = "Out with the Old 1990s Edition"
            base_date = datetime(1990, 1, 1)
        total_units = (datetime(base_date.year + 10, 1, 1) - base_date).days
    else:
        board_name = f"Out with the Old {event_date.year} Edition"
        base_date = datetime(event_date.year, 1, 1)
        total_units = (datetime(event_date.year + 1, 1, 1) - base_date).days

    # Override the board name to always post to "TEST"
    # board_name = "TEST"

    # Get the board ID, create the board if it does not exist
    board_id = blog_trello_utils.get_board_id(board_name, api_key, token)
    if board_id is None:
        board = blog_trello_utils.create_board(board_name, api_key, token)
        board_id = board['id']

    # Determine the list name (without zero-padding the day)
    list_name = event_date.strftime('%a %b').upper() + f" {event_date.day}"
    if event_date.year < 2000:
        list_name += f" {event_date.year}"

    # Calculate the position of the list
    pos = calculate_pos(event_date, base_date, total_units)

    # Find the megalog name
    megalog_name = find_megalog_name(event['logid'])
    if not megalog_name:
        print(colored(f"Error: Could not find megalog name for logid {event['logid']}", 'red', 'on_white'))
        continue

    # Format the card title
    card_title = format_card_title(megalog_name, event['title'], event['logid'])

    # Clean the comments for the card description
    card_description = clean_comments(event['comments'])

    # Identify image tags and clean the description
    image_tag_pattern = re.compile(r'<\$image id=', re.IGNORECASE)
    attachments = []
    comments_parts = image_tag_pattern.split(card_description)
    card_description = comments_parts[0]
    for part in comments_parts[1:]:
        try:
            image_id = part.split("$>")[0].replace('"', '').strip()
            image_found = False
            for image in images:
                if image['imageid'] == int(image_id):
                    attachments.append(image)
                    card_description += part.split("$>")[1]
                    image_found = True
                    break
        except Exception as e:
            continue

    # After identifying all image tags, remove HTML tags from the description
    card_description = remove_html_tags(card_description)

    # Add source and event details
    card_description += f"\n\nEvent Date: {event['date']}\nSource: joereger.com blog\nEvent ID: {event['eventid']}\nLog ID: {event['logid']}"

    # Add any additional attachments based on eventid and sort by imageorder
    event_attachments = [image for image in images if image['eventid'] == event['eventid']]
    event_attachments.sort(key=lambda x: x['imageorder'])
    for image in event_attachments:
        if image not in attachments:
            attachments.append(image)

    # Split description if it exceeds the maximum length
    max_desc_length = 13000
    description_chunks = [card_description[i:i+max_desc_length] for i in range(0, len(card_description), max_desc_length)]

    # Create or update the list
    list_id, list_request = blog_trello_utils.create_or_update_list(board_id, list_name, pos, api_key, token)
    requests_queue.append(list_request)

    # Create cards for each description chunk
    for i, chunk in enumerate(description_chunks):
        if i == 0:
            title = card_title
        else:
            title = f"{card_title} ...CONTINUED"
        
        card_id, card_request = blog_trello_utils.create_or_update_card(list_id, title, chunk, api_key, token)
        requests_queue.append(card_request)

        # Log the actions
        print(f"Event Date: {event['date']} | Event ID: {event['eventid']}")
        print(f"Board: {board_name} | List: {list_name} | Card Title: {title}")

        # Upload attachments and add comments only to the first card
        if i == 0:
            for attachment in attachments:
                print(f"Attachment: {attachment['filename']}")
                print(f"Attachment Comment: {clean_image_description(attachment['description'])}")
            print("="*40)

            for attachment in attachments:
                # Check if filename is not None
                if attachment['filename']:
                    attachment_path = os.path.join('source_data/joeregercomlivedata/uploadimages/files/50', attachment['filename'].replace('\\', os.path.sep))
                    if not os.path.exists(attachment_path):
                        print(colored(f"Error: File not found - {attachment_path}", 'red', 'on_white'))
                        continue
                    if not blog_trello_utils.check_existing_attachments(card_id, attachment['filename'], os.path.getsize(attachment_path), api_key, token):
                        attachment_id, attachment_request = blog_trello_utils.upload_attachment(card_id, attachment_path, api_key, token)
                        requests_queue.append(attachment_request)
                        cleaned_description = clean_image_description(attachment['description'])
                        if cleaned_description:
                            comment_id, comment_request = blog_trello_utils.add_comment(card_id, cleaned_description, api_key, token)
                            requests_queue.append(comment_request)

# Process all requests in order
print("Processing all requests in order")
blog_trello_utils.process_requests_in_order(requests_queue)
print("Finished processing requests")
