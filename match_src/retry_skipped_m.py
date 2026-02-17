import time
from scrape_matches_m import scrape_match_details

SKIPPED_LOG = 'skipped_matches.log'
RETRY_LOG = 'skipped_matches_retry.log'

def main():
    with open(SKIPPED_LOG, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]
    print(f"Retrying {len(urls)} skipped matches...")
    failed = []
    for url in urls:
        before = count_skipped(RETRY_LOG)
        scrape_match_details(url)
        time.sleep(2)  # Polite delay
        after = count_skipped(RETRY_LOG)
        if after > before:
            failed.append(url)
    print(f"Done. {len(failed)} matches still failed. See {RETRY_LOG}.")

def count_skipped(logfile):
    try:
        with open(logfile, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f)
    except FileNotFoundError:
        return 0

if __name__ == '__main__':
    main() 