import json
from datetime import datetime
import mythredz_trello_utils
import time

start_date = datetime(2008, 6, 14, 0, 0)

def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

api_keys = mythredz_trello_utils.load_api_keys('api_keys_and_tokens.txt')
api_key = api_keys['trello_api_key']
token = api_keys['trello_token']

threds = load_json('mysql_data_exported/mythredz/thred.json')
posts = load_json('mysql_data_exported/mythredz/post.json')

threds_dict = {thred['thredid']: thred for thred in threds if thred['userid'] == 1}
filtered_posts = [post for post in posts if post['thredid'] in threds_dict]
filtered_posts.sort(key=lambda x: datetime.fromisoformat(x['date']))

def calculate_pos(event_date, base_date, total_units):
    days_since_start = (event_date - base_date).days
    return (1 - (days_since_start / total_units)) * 1000

for post in filtered_posts[:50000]:
    post_date = datetime.fromisoformat(post['date'])
    if post_date < start_date:
        continue

    if post_date.year < 2000:
        if post_date.year < 1980:
            board_name = "Out with the Old 1970s Edition"
            base_date = datetime(1970, 1, 1)
        elif post_date.year < 1990:
            board_name = "Out with the Old 1980s Edition"
            base_date = datetime(1980, 1, 1)
        else:
            board_name = "Out with the Old 1990s Edition"
            base_date = datetime(1990, 1, 1)
        total_units = (datetime(base_date.year + 10, 1, 1) - base_date).days
    else:
        board_name = f"Out with the Old {post_date.year} Edition"
        base_date = datetime(post_date.year, 1, 1)
        total_units = (datetime(post_date.year + 1, 1, 1) - base_date).days

    print(f"Processing post for board: {board_name}")

    board_id = mythredz_trello_utils.get_board_id(board_name, api_key, token)
    if board_id is None:
        board = mythredz_trello_utils.create_board(board_name, api_key, token)
        board_id = board['id']
        print(f"Created new board: {board_name} (ID: {board_id})")
    else:
        print(f"Using existing board: {board_name} (ID: {board_id})")

    list_name = post_date.strftime('%a %b').upper() + f" {post_date.day}"
    pos = calculate_pos(post_date, base_date, total_units)

    list_id, _ = mythredz_trello_utils.create_or_get_list(board_id, list_name, pos, api_key, token)
    print(f"Using list: {list_name} (ID: {list_id})")

    thred_name = threds_dict[post['thredid']]['name']
    card_title = f"{thred_name}: {post['contents']}"
    card_description = f"Date: {post['date']}\nSource: mythredz app\nThred ID: {post['thredid']}\nPost ID: {post['postid']}"

    print(f"Attempting to create or update card: {card_title}")

    existing_cards = mythredz_trello_utils.get_list_cards(list_id, api_key, token)
    
    if card_title in existing_cards:
        existing_card = existing_cards[card_title]
        if existing_card['desc'] != card_description:
            card_id = mythredz_trello_utils.update_card(existing_card['id'], card_description, api_key, token)
            print(f"Updated existing card: {card_title} (ID: {card_id})")
        else:
            print(f"Card already exists and is up to date: {card_title} (ID: {existing_card['id']})")
    else:
        card_id = mythredz_trello_utils.create_card(list_id, card_title, card_description, api_key, token)
        print(f"Created new card: {card_title} (ID: {card_id})")

    time.sleep(1)  # Wait for 1 second
    existing_cards = mythredz_trello_utils.get_list_cards(list_id, api_key, token)  # Refresh the list of cards

    print(f"Board: {board_name}")
    print(f"List: {list_name}")
    print(f"List Position: {pos}")
    print(f"Card Title: {card_title}")
    print(f"Card Description:")
    print(card_description)
    print("=" * 40)

print("Finished processing posts")