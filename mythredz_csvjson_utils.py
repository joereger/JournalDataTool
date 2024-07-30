import csv
import json
import re
from datetime import datetime

def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def clean_description(desc):
    if desc is None:
        desc = ''
    desc = re.sub(r'[^\x00-\x7F]+', '', str(desc))
    return desc.replace("\r\n", " ").replace("\n", " ")

def save_entries_to_csv(entries, file_path):
    fieldnames = ['date', 'category', 'title', 'body', 'datablogging.eventid', 'datablogging.logid', 'images', 'source', 'thred.thredid', 'thred.name', 'post.postid']
    with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for entry in entries:
            writer.writerow(entry)

def save_entries_to_json(entries, file_path):
    with open(file_path, 'w', encoding='utf-8') as jsonfile:
        json.dump(entries, jsonfile, indent=4, ensure_ascii=False)

def process_mythredz_posts(posts, threds):
    processed_posts = []
    
    for post in posts:
        thred = next((t for t in threds if t['thredid'] == post['thredid'] and t['userid'] == 1), None)
        if not thred:
            continue

        cleaned_contents = clean_description(post['contents'])
        post_data = {
            'date': post['date'],
            'category': thred['name'],
            'title': f"{thred['name']}: {cleaned_contents}",
            'body': cleaned_contents,
            'datablogging.eventid': '',
            'datablogging.logid': '',
            'images': '',
            'source': 'mythredz',
            'thred.thredid': thred['thredid'],
            'thred.name': thred['name'],
            'post.postid': post['postid']
        }
        
        processed_posts.append(post_data)
    
    return processed_posts

def combine_and_sort_entries(entries):
    entries.sort(key=lambda x: datetime.fromisoformat(x['date']))
    return entries