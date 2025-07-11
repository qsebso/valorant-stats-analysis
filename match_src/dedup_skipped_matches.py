import os

LOG_PATH = os.path.join(os.path.dirname(__file__), '..', 'skipped_matches.log')

def dedup_log():
    seen = set()
    unique_lines = []
    with open(LOG_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            url = line.strip()
            if url and url not in seen:
                seen.add(url)
                unique_lines.append(url)
    with open(LOG_PATH, 'w', encoding='utf-8') as f:
        for url in unique_lines:
            f.write(url + '\n')
    print(f"Deduplicated {len(unique_lines)} unique URLs written to skipped_matches.log.")

if __name__ == '__main__':
    dedup_log() 