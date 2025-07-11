import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import os
import sys
import re

# Allow import from src/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from parser import parse_vlr_match # type: ignore

DB_PATH = os.path.join('data', 'valorant_stats_matchcentric.db')
BASE_URL = 'https://www.vlr.gg/matches/results/?page={}'
MATCH_BASE = 'https://www.vlr.gg{}'

# --- DB Setup ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS map_stats (
            event_id            TEXT,
            event_name          TEXT,
            bracket_stage       TEXT,
            match_id            TEXT,
            match_datetime      DATETIME,
            patch               TEXT,
            map_name            TEXT,
            map_index           INTEGER,
            team1_name          TEXT,
            team1_score         INTEGER,
            team2_name          TEXT,
            team2_score         INTEGER,
            team1_attacker_rounds INTEGER,
            team1_defender_rounds INTEGER,
            team2_attacker_rounds INTEGER,
            team2_defender_rounds INTEGER,
            map_duration        TEXT,
            winner              TEXT,
            rounds_played       INTEGER,
            player_name         TEXT,
            player_team         TEXT,
            player_country      TEXT,
            agent_played        TEXT,
            rating_2_0          REAL,
            ACS                 REAL,
            KDRatio             REAL,
            KDARatio            REAL,
            KAST_pct            REAL,
            ADR                 REAL,
            KPR                 REAL,
            APR                 REAL,
            FKPR                REAL,
            FDPR                REAL,
            HS_pct              REAL,
            total_kills         INTEGER,
            total_deaths        INTEGER,
            total_assists       INTEGER,
            total_first_kills   INTEGER,
            total_first_deaths  INTEGER,
            PRIMARY KEY (match_id, map_name, player_name)
        )
    ''')
    conn.commit()
    conn.close()

# --- Scraper Logic ---
def get_match_links(page):
    url = BASE_URL.format(page)
    resp = requests.get(url)
    if resp.status_code != 200:
        return []
    soup = BeautifulSoup(resp.text, 'html.parser')
    links = []
    for a in soup.select('a[href^="/"][class*="match-item"]'):
        href = a.get('href')
        if href and href.startswith('/'):
            if href.count('/') == 2 and href[1:].split('/')[0].isdigit():
                links.append(href)
    return list(set(links))

def save_map_stats(row):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    columns = ', '.join(row.keys())
    placeholders = ', '.join('?' for _ in row)
    sql = f'INSERT OR REPLACE INTO map_stats ({columns}) VALUES ({placeholders})'
    c.execute(sql, tuple(row.values()))
    conn.commit()
    conn.close()

def calculate_per_round_stats(row):
    rounds = row.get('rounds_played')
    if not rounds or rounds <= 0:
        return {
            'KPR': None,
            'APR': None,
            'FKPR': None,
            'FDPR': None,
            'KDRatio': None,
            'KDARatio': None
        }
    try:
        kills = int(row.get('total_kills', 0) or 0)
        assists = int(row.get('total_assists', 0) or 0)
        deaths = int(row.get('total_deaths', 0) or 0)
        first_kills = int(row.get('total_first_kills', 0) or 0)
        first_deaths = int(row.get('total_first_deaths', 0) or 0)
    except (ValueError, TypeError):
        return {
            'KPR': None,
            'APR': None,
            'FKPR': None,
            'FDPR': None,
            'KDRatio': None,
            'KDARatio': None
        }
    kpr = round(kills / rounds, 3)
    apr = round(assists / rounds, 3)
    fkpr = round(first_kills / rounds, 3)
    fdpr = round(first_deaths / rounds, 3)
    if deaths > 0:
        kdr = round(kills / deaths, 3)
        kdar = round((kills + assists) / deaths, 3)
    else:
        kdr = None
        kdar = None
    return {
        'KPR': kpr,
        'APR': apr,
        'FKPR': fkpr,
        'FDPR': fdpr,
        'KDRatio': kdr,
        'KDARatio': kdar
    }

MAP_STATS_COLUMNS = [
    'event_id', 'event_name', 'bracket_stage', 'match_id', 'match_datetime', 'patch',
    'map_name', 'map_index', 'team1_name', 'team1_score', 'team2_name', 'team2_score',
    'winner',
    'rounds_played',
    'player_name', 'player_team', 'player_country', 'agent_played',
    'rating_2_0', 'ACS', 'KDRatio', 'KDARatio', 'KAST_pct',
    'ADR', 'KPR', 'APR', 'FKPR', 'FDPR', 'HS_pct',
    'total_kills', 'total_deaths', 'total_assists',
    'total_first_kills', 'total_first_deaths',
    'team1_attacker_rounds', 'team1_defender_rounds',
    'team2_attacker_rounds', 'team2_defender_rounds',
    'map_duration'
]

def scrape_match_details(match_url):
    print(f"Scraping details for: {match_url}")
    import random
    max_retries = 5
    for attempt in range(max_retries):
        try:
            resp = requests.get(match_url, timeout=15)
            if resp.status_code == 200:
                break
            else:
                print(f"Failed to fetch {match_url} (status {resp.status_code})")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {match_url} (attempt {attempt+1}/{max_retries}): {e}")
        time.sleep(2 + random.uniform(0, 3))  # Polite randomized delay
    else:
        print(f"Giving up on {match_url} after {max_retries} attempts.")
        with open('skipped_matches.log', 'a', encoding='utf-8') as logf:
            logf.write(match_url + '\n')
        return
    html = resp.text
    try:
        match_result = parse_vlr_match(html)
    except Exception as e:
        print(f"Failed to parse match: {match_url} | Error: {e}")
        with open('skipped_matches.log', 'a', encoding='utf-8') as logf:
            logf.write(match_url + '\n')
        return
    # Extract match_id from URL if not present
    match_id = match_result.get('match_id')
    if not match_id:
        m = re.search(r'/([0-9]+)/', match_url)
        match_id = m.group(1) if m else None
    event_id = match_result.get('event_id')
    event_name = match_result.get('event_name')
    for map_info in match_result.get('maps', []):
        for player_data in map_info.get('players', []):
            row = {
                'event_id': event_id,
                'event_name': event_name,
                'bracket_stage': match_result.get('bracket_stage'),
                'match_id': match_id,
                'match_datetime': match_result.get('date'),
                'patch': match_result.get('patch'),
                'map_name': map_info.get('map_name'),
                'map_index': map_info.get('map_index'),
                'team1_name': map_info.get('team1_name'),
                'team1_score': map_info.get('team1_score'),
                'team2_name': map_info.get('team2_name'),
                'team2_score': map_info.get('team2_score'),
                'team1_attacker_rounds': map_info.get('team1_attacker_rounds'),
                'team1_defender_rounds': map_info.get('team1_defender_rounds'),
                'team2_attacker_rounds': map_info.get('team2_attacker_rounds'),
                'team2_defender_rounds': map_info.get('team2_defender_rounds'),
                'map_duration': map_info.get('map_duration'),
                'winner': map_info.get('winner'),
                'player_name': player_data.get('Player') or player_data.get('player_name'),
                'player_team': player_data.get('Team') or player_data.get('player_team'),
                'player_country': player_data.get('Country') or player_data.get('player_country'),
                'agent_played': player_data.get('Agent') or player_data.get('agent_played'),
                'rating_2_0': player_data.get('Rating 2.0') or player_data.get('rating_2_0'),
                'ACS': player_data.get('ACS') or player_data.get('Average Combat Score'),
                'ADR': player_data.get('ADR') or player_data.get('Average Damage per Round'),
                'KDRatio': player_data.get('K/D') or player_data.get('K/D Ratio'),
                'KDARatio': player_data.get('KDA'),
                'KAST_pct': player_data.get('KAST'),
                'KPR': None, 'APR': None, 'FKPR': None, 'FDPR': None,  # Will calculate below
                'HS_pct': player_data.get('HS%') or player_data.get('Headshot %'),
                'total_kills': player_data.get('Kills'),
                'total_deaths': player_data.get('Deaths'),
                'total_assists': player_data.get('Assists'),
                'total_first_kills': player_data.get('FK') or player_data.get('First Kills'),
                'total_first_deaths': player_data.get('FD') or player_data.get('First Deaths'),
            }
            # Calculate rounds_played from team scores
            try:
                team1_score = int(row.get('team1_score', 0) or 0)
                team2_score = int(row.get('team2_score', 0) or 0)
                row['rounds_played'] = team1_score + team2_score
            except (ValueError, TypeError):
                row['rounds_played'] = None
            # Calculate per-round stats
            row.update(calculate_per_round_stats(row))
            # Ensure all required columns are present
            for col in MAP_STATS_COLUMNS:
                if col not in row:
                    row[col] = None
            # Remove any extra keys
            row = {k: row[k] for k in MAP_STATS_COLUMNS}
            save_map_stats(row)

def scrape_all_matches():
    print('Initializing DB...')
    init_db()
    page = 1
    seen = set()
    while True:
        print(f'Scraping page {page}...')
        url = BASE_URL.format(page)
        resp = requests.get(url)
        if resp.status_code != 200:
            print('No more pages or error. Stopping.')
            break
        soup = BeautifulSoup(resp.text, 'html.parser')
        match_cards = soup.select('a[href^="/"][class*="match-item"]')
        if not match_cards:
            print('No matches found on this page. Stopping.')
            break
        for card in match_cards:
            href = card.get('href')
            match_id = href.split('/')[1]
            if match_id in seen:
                continue
            seen.add(match_id)
            full_url = MATCH_BASE.format(href)
            scrape_match_details(full_url)
        page += 1
        time.sleep(1)  # Be polite to the server

if __name__ == '__main__':
    scrape_all_matches() 