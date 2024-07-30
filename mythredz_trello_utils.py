import requests
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from ratelimit import limits, sleep_and_retry

TRELLO_RATE_LIMIT = 100
TRELLO_RATE_LIMIT_PERIOD = 10

def create_session_with_retries():
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504], allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT"])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    session.mount('http://', HTTPAdapter(max_retries=retries))
    return session

session = create_session_with_retries()

@sleep_and_retry
@limits(calls=TRELLO_RATE_LIMIT, period=TRELLO_RATE_LIMIT_PERIOD)
def make_request(method, url, **kwargs):
    response = session.request(method, url, **kwargs)
    response.raise_for_status()
    return response

def load_api_keys(file_path):
    api_keys = {}
    with open(file_path, 'r') as file:
        for line in file:
            key, value = line.strip().split('=')
            api_keys[key] = value
    return api_keys

def get_board_id(board_name, api_key, token):
    url = f"https://api.trello.com/1/members/me/boards"
    query = {'key': api_key, 'token': token, 'fields': 'name,id'}
    response = make_request('GET', url, params=query)
    boards = response.json()
    return next((board['id'] for board in boards if board['name'] == board_name), None)

def create_board(board_name, api_key, token):
    url = f"https://api.trello.com/1/boards/"
    query = {'key': api_key, 'token': token, 'name': board_name, 'defaultLists': 'false', 'prefs_permissionLevel': 'private'}
    response = make_request('POST', url, params=query)
    return response.json()

def get_board_lists(board_id, api_key, token):
    url = f"https://api.trello.com/1/boards/{board_id}/lists"
    query = {'key': api_key, 'token': token, 'fields': 'name,id'}
    response = make_request('GET', url, params=query)
    return {lst['name']: lst['id'] for lst in response.json()}

def create_or_get_list(board_id, list_name, pos, api_key, token):
    existing_lists = get_board_lists(board_id, api_key, token)
    if list_name in existing_lists:
        return existing_lists[list_name], None
    url = f"https://api.trello.com/1/lists"
    query = {'key': api_key, 'token': token, 'name': list_name, 'idBoard': board_id, 'pos': pos}
    response = make_request('POST', url, params=query)
    return response.json()['id'], ('POST', url, {'params': query}, None)

def get_list_cards(list_id, api_key, token):
    url = f"https://api.trello.com/1/lists/{list_id}/cards"
    query = {'key': api_key, 'token': token, 'fields': 'name,desc,id', 'limit': 1000}
    response = make_request('GET', url, params=query)
    cards = response.json()
    while len(cards) % 1000 == 0 and len(cards) > 0:
        query['before'] = cards[-1]['id']
        response = make_request('GET', url, params=query)
        new_cards = response.json()
        if not new_cards:
            break
        cards.extend(new_cards)
    return {card['name']: card for card in cards}

def update_card(card_id, desc, api_key, token):
    url = f"https://api.trello.com/1/cards/{card_id}"
    data = {'key': api_key, 'token': token, 'desc': desc}
    make_request('PUT', url, data=data)
    return card_id

def create_card(list_id, name, desc, api_key, token):
    url = f"https://api.trello.com/1/cards"
    data = {'key': api_key, 'token': token, 'idList': list_id, 'name': name, 'desc': desc}
    response = make_request('POST', url, data=data)
    return response.json()['id']