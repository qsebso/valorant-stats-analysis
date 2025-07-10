import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import time
import re
import difflib
from dateutil import parser as dateparser

# VLR Chronicle match history base URL
BASE_URL = "https://www.vlr.gg/player/matches/458/chronicle/?page={}"  # Pages 1-5

# Output paths
DB_CSV = os.path.join(os.path.dirname(__file__), 'chronicle_unique_matches.csv')
VLR_CSV = os.path.join(os.path.dirname(__file__), 'vlr_chronicle_matches.csv')

# Helper to scrape a single page
def scrape_vlr_page(page_num):
    url = BASE_URL.format(page_num)
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    matches = []
    for row in soup.select('a.wf-card.fc-flex.m-item'):
        link = row['href'] if row.has_attr('href') else ''
        event = row.select_one('.m-item-event.text-of').text.strip() if row.select_one('.m-item-event.text-of') else ''
        teams = row.select('.m-item-team.text-of')
        team1 = teams[0].text.strip() if len(teams) > 0 else ''
        team2 = teams[1].text.strip() if len(teams) > 1 else ''
        date = row.select_one('.m-item-date').text.strip() if row.select_one('.m-item-date') else ''
        score = row.select_one('.m-item-result').text.strip() if row.select_one('.m-item-result') else ''
        stage = row.select_one('.m-item-extra').text.strip() if row.select_one('.m-item-extra') else ''
        matches.append({
            'date': date,
            'event': event,
            'team1': team1,
            'team2': team2,
            'score': score,
            'stage': stage,
            'link': link
        })
    return matches

def scrape_all_vlr_matches():
    all_matches = []
    for page in range(1, 6):  # Pages 1-5
        print(f"Scraping VLR page {page}...")
        matches = scrape_vlr_page(page)
        all_matches.extend(matches)
        time.sleep(1)  # Be polite to the server
    df = pd.DataFrame(all_matches)
    df.to_csv(VLR_CSV, index=False)
    print(f"Saved {len(df)} VLR matches to {VLR_CSV}")
    return df

def clean_text(s):
    if not isinstance(s, str):
        return ''
    # Remove team tags (e.g., #AFP), extra whitespace, tabs, newlines, and lowercase
    s = re.sub(r'#\w+', '', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip().lower()

def clean_date(s):
    if not isinstance(s, str):
        return ''
    # Remove ordinal suffixes (st, nd, rd, th)
    s = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', s)
    s = s.replace(',', '').replace('pdt', '').replace('pst', '').replace('am', '').replace('pm', '')
    s = re.sub(r'\s+', ' ', s)
    return s.strip().lower()

def parse_date_fuzzy(s):
    try:
        return dateparser.parse(s, fuzzy=True).date()
    except Exception:
        return None

def teams_match(t1a, t2a, t1b, t2b):
    # True if teams match in any order
    return (t1a == t1b and t2a == t2b) or (t1a == t2b and t2a == t1b)

def event_similarity(e1, e2):
    return difflib.SequenceMatcher(None, e1, e2).ratio()

def load_db_matches():
    df = pd.read_csv(DB_CSV)
    # Normalize for comparison
    df['event_name'] = df['event_name'].apply(clean_text)
    df['team1_name'] = df['team1_name'].apply(clean_text)
    df['team2_name'] = df['team2_name'].apply(clean_text)
    df['match_datetime'] = df['match_datetime'].apply(clean_date)
    return df

def load_vlr_matches():
    df = pd.read_csv(VLR_CSV)
    df['event'] = df['event'].apply(clean_text)
    df['team1'] = df['team1'].apply(clean_text)
    df['team2'] = df['team2'].apply(clean_text)
    df['date'] = df['date'].apply(clean_date)
    return df

def compare_matches(vlr_df, db_df):
    print('\nSample VLR rows:')
    print(vlr_df[['event', 'team1', 'team2', 'date']].head(5))
    print('\nSample DB rows:')
    print(db_df[['event_name', 'team1_name', 'team2_name', 'match_datetime']].head(5))
    # Build DB match list for fast lookup
    db_matches = []
    for _, row in db_df.iterrows():
        db_matches.append({
            'event': row['event_name'],
            'team1': row['team1_name'],
            'team2': row['team2_name'],
            'date': row['match_datetime'],
            'orig': row
        })
    matched = 0
    fuzzy_matched = 0
    for _, vrow in vlr_df.iterrows():
        vevent, vteam1, vteam2, vdate = vrow['event'], vrow['team1'], vrow['team2'], vrow['date']
        vdate_parsed = parse_date_fuzzy(vdate)
        found = False
        best_score = 0
        best_db = None
        for dbrow in db_matches:
            devent, dteam1, dteam2, ddate = dbrow['event'], dbrow['team1'], dbrow['team2'], dbrow['date']
            ddate_parsed = parse_date_fuzzy(ddate)
            # Event similarity
            es = event_similarity(vevent, devent)
            # Team match
            tm = teams_match(vteam1, vteam2, dteam1, dteam2)
            # Date match (within 1 day)
            date_ok = False
            if vdate_parsed and ddate_parsed:
                delta = abs((vdate_parsed - ddate_parsed).days)
                date_ok = delta <= 1
            # Strong match
            if es > 0.8 and tm and date_ok:
                found = True
                matched += 1
                break
            # Track best fuzzy match
            score = es + (1 if tm else 0) + (1 if date_ok else 0)
            if score > best_score:
                best_score = score
                best_db = dbrow
        if not found:
            # Print best fuzzy match for manual inspection
            fuzzy_matched += 1 if best_score > 1.5 else 0
            print(f"\nNo exact match for VLR: {vevent} | {vteam1} vs {vteam2} | {vdate}")
            if best_db:
                print(f"  Closest DB: {best_db['event']} | {best_db['team1']} vs {best_db['team2']} | {best_db['date']} (score={best_score:.2f})")
    print(f"\nTotal exact/fuzzy matches: {matched} / {fuzzy_matched} (out of {len(vlr_df)})")
    # Optionally, do the reverse: DB->VLR

def main():
    vlr_df = load_vlr_matches() if os.path.exists(VLR_CSV) else scrape_all_vlr_matches()
    db_df = load_db_matches()
    compare_matches(vlr_df, db_df)

if __name__ == "__main__":
    main() 