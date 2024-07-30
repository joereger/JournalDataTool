import requests
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from ratelimit import limits, sleep_and_retry
from queue import Queue, Empty
from threading import Thread
import re

# Trello rate limits
TRELLO_RATE_LIMIT = 100  # number of requests
TRELLO_RATE_LIMIT_PERIOD = 10  # seconds

# Function to create a requests session with retry strategy
def create_session_with_retries():
    session = requests.Session()
    retries = Retry(total=5,  # Number of retries
                    backoff_factor=1,  # Wait time between retries (exponential backoff)
                    status_forcelist=[500, 502, 503, 504],  # Retry on these HTTP status codes
                    allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT"])  # Retry on these methods
    session.mount('https://', HTTPAdapter(max_retries=retries))
    session.mount('http://', HTTPAdapter(max_retries=retries))
    return session

# Create a session with retries
session = create_session_with_retries()

# Rate limiting decorator
@sleep_and_retry
@limits(calls=TRELLO_RATE_LIMIT, period=TRELLO_RATE_LIMIT_PERIOD)
def make_request(method, url, **kwargs):
    if method.upper() in ['POST', 'PUT']:
        data = kwargs.pop('data', None)
        #print(f"Making {method} request to {url} with data: {data}")
        response = session.request(method, url, data=data, **kwargs)
    else:
        #print(f"Making {method} request to {url} with params: {kwargs.get('params')}")
        response = session.request(method, url, **kwargs)
    #print(f"Response status code: {response.status_code}, Response content: {response.content}")
    response.raise_for_status()
    return response

# Worker function for processing requests from the queue
def worker(queue):
    while True:
        try:
            method, url, kwargs, callback = queue.get(timeout=1)
            try:
                response = make_request(method, url, **kwargs)
                if callback:
                    callback(response)
            except requests.RequestException as e:
                print(f"Request failed: {e}")
            finally:
                queue.task_done()
        except Empty:
            break

# Function to process requests in order using a queue
def process_requests_in_order(requests_queue):
    queue = Queue()
    for req in requests_queue:
        queue.put(req)

    # Start worker threads
    for _ in range(1):
        thread = Thread(target=worker, args=(queue,))
        thread.daemon = True
        thread.start()

    queue.join()

# Function to load API keys and tokens from a text file
def load_api_keys(file_path):
    api_keys = {}
    with open(file_path, 'r') as file:
        for line in file:
            key, value = line.strip().split('=')
            api_keys[key] = value
    return api_keys

# Function to get the board ID by name
def get_board_id(board_name, api_key, token):
    url = f"https://api.trello.com/1/members/me/boards"
    query = {
        'key': api_key,
        'token': token,
        'fields': 'name'
    }
    response = make_request('GET', url, params=query)
    boards = response.json()
    for board in boards:
        if board['name'] == board_name:
            return board['id']
    return None

# Function to create a board
def create_board(board_name, api_key, token):
    url = f"https://api.trello.com/1/boards/"
    query = {
        'key': api_key,
        'token': token,
        'name': board_name,
        'defaultLists': 'false',  # Do not create default lists
        'prefs_permissionLevel': 'private'  # Set board visibility to private
    }
    response = make_request('POST', url, params=query)
    return response.json()

# Function to create a list on a board with a given position
def create_list(board_id, list_name, pos, api_key, token):
    url = f"https://api.trello.com/1/lists"
    query = {
        'key': api_key,
        'token': token,
        'name': list_name,
        'idBoard': board_id,
        'pos': pos
    }
    response = make_request('POST', url, params=query)
    return response.json()['id'], ('POST', url, {'params': query}, None)

# Function to get all lists on a board
def get_board_lists(board_id, api_key, token):
    url = f"https://api.trello.com/1/boards/{board_id}/lists"
    query = {
        'key': api_key,
        'token': token,
        'fields': 'name,pos'
    }
    response = make_request('GET', url, params=query)
    return response.json()

# Function to create or update a list on a board with a given position
def create_or_update_list(board_id, list_name, pos, api_key, token):
    existing_lists = get_board_lists(board_id, api_key, token)
    for lst in existing_lists:
        if lst['name'] == list_name:
            # Update the position of the existing list
            url = f"https://api.trello.com/1/lists/{lst['id']}"
            query = {
                'key': api_key,
                'token': token,
                'pos': pos
            }
            response = make_request('PUT', url, params=query)
            return lst['id'], ('PUT', url, {'params': query}, None)

    # Create a new list if it doesn't exist
    return create_list(board_id, list_name, pos, api_key, token)

# Function to get all cards in a list
def get_list_cards(list_id, api_key, token):
    url = f"https://api.trello.com/1/lists/{list_id}/cards"
    query = {
        'key': api_key,
        'token': token,
        'fields': 'name'
    }
    response = make_request('GET', url, params=query)
    return response.json()

# Function to clean description
def clean_description(desc):
    # Remove any unsupported characters
    return re.sub(r'[^\x00-\x7F]+', '', desc)

# Function to create or update a card in a list
def create_or_update_card(list_id, name, desc, api_key, token):
    max_desc_length = 13000  # Trello's maximum allowed length for card descriptions

    # Clean and truncate the description if it exceeds the maximum length
    desc = clean_description(desc)
    if len(desc) > max_desc_length:
        desc = desc[:max_desc_length]

    existing_cards = get_list_cards(list_id, api_key, token)
    for card in existing_cards:
        if card['name'] == name:
            # Update the card description if it exists
            url = f"https://api.trello.com/1/cards/{card['id']}"
            data = {
                'key': api_key,
                'token': token,
                'desc': desc
            }
            response = make_request('PUT', url, data=data)
            return card['id'], ('PUT', url, {'data': data}, None)

    # Create a new card if it doesn't exist
    url = f"https://api.trello.com/1/cards"
    data = {
        'key': api_key,
        'token': token,
        'idList': list_id,
        'name': name,
        'desc': desc
    }
    response = make_request('POST', url, data=data)
    return response.json()['id'], ('POST', url, {'data': data}, None)

# Function to upload an attachment to a card
def upload_attachment(card_id, file_path, api_key, token):
    url = f"https://api.trello.com/1/cards/{card_id}/attachments"
    query = {
        'key': api_key,
        'token': token
    }
    with open(file_path, 'rb') as file:
        response = make_request('POST', url, params=query, files={'file': file})
    return response.json()['id'], ('POST', url, {'params': query, 'files': {'file': file}}, None)

# Function to add a comment to a card
def add_comment(card_id, comment_text, api_key, token):
    url = f"https://api.trello.com/1/cards/{card_id}/actions/comments"
    query = {
        'key': api_key,
        'token': token,
        'text': comment_text
    }
    response = make_request('POST', url, params=query)
    return response.json()['id'], ('POST', url, {'params': query}, None)

# Function to check for existing attachments
def check_existing_attachments(card_id, file_name, file_size, api_key, token):
    url = f"https://api.trello.com/1/cards/{card_id}/attachments"
    query = {
        'key': api_key,
        'token': token
    }
    response = make_request('GET', url, params=query)
    attachments = response.json()
    
    # Extract the base name of the file (remove directories)
    target_file_name = os.path.basename(file_name.replace('\\', '/'))
    
    print(f"Checking existing attachments for card '{card_id}'")
    print(f"Target file name: {target_file_name}, Target file size: {file_size}")
    
    for attachment in attachments:
        print(f"Existing attachment: {attachment['name']}, Size: {attachment['bytes']}")
        if attachment['name'] == target_file_name and attachment['bytes'] == file_size:
            print("Attachment already exists.")
            return True
    print("Attachment does not exist.")
    return False
