import csv
import yaml
import re
import sqlite3
import os

csv_path = 'test/vlr_chronicle_matches.csv'
yaml_path = 'config/events.yaml'
db_path = os.path.join('data', 'valorant_stats_clean.db')

def clean_text(s):
    # Remove punctuation: , . - ; :
    return re.sub(r'[.,;:\-]', '', s)

def first_n_words(s, n=3):
    s = clean_text(s)
    return ' '.join(s.split()[:n]).lower()

def get_yaml_event_names(yaml_path):
    with open(yaml_path, encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return set(first_n_words(e['event_name']) for e in data['events'] if 'event_name' in e)

def match_id_exists(match_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM map_stats WHERE match_id = ? LIMIT 1", (match_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def extract_match_id(link):
    # Extract the first number after the first slash
    m = re.search(r'/([0-9]+)', link)
    return m.group(1) if m else None

def main():
    yaml_events = get_yaml_event_names(yaml_path)
    
    print("Event (first 3 words) | Match Link (ID) | In DB?")
    print("----------------------|------------------|--------")
    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            event = row.get('event', '').strip()
            link = row.get('link', '').strip()
            key = first_n_words(event)
            if event and key not in yaml_events:
                match_id = extract_match_id(link)
                in_db = match_id_exists(match_id) if match_id else False
                if not in_db:
                    print(f"{key:22} | {link:16} | NO")

if __name__ == '__main__':
    main() 