import json
import csv
import sys
from operator import itemgetter

SEEN_FILE = 'seen_listings.json'
OUTPUT_CSV = 'output/seen_ranked.csv'
OUTPUT_MD = 'output/top_seen_opportunities.md'

# Filtros configuráveis
FILTER_STATUS = 'needs_review'  # Pode ser 'approved', 'rejected', etc. Ou None para todos

# Lê o histórico
def load_seen(path):
    try:
        with open(path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
    except UnicodeDecodeError:
        with open(path, 'r', encoding='latin-1') as f:
            data = json.load(f)
    # Normaliza para lista
    listings = []
    for url, info in data.items():
        entry = dict(info)
        entry['url'] = url
        listings.append(entry)
    return listings

def main():
    listings = load_seen(SEEN_FILE)
    # Filtro por status
    if FILTER_STATUS:
        listings = [l for l in listings if l.get('status') == FILTER_STATUS]
    # Só mantém os que têm score
    listings = [l for l in listings if 'score' in l and isinstance(l['score'], (int, float))]
    # Ranking por score decrescente
    listings.sort(key=itemgetter('score'), reverse=True)
    # Exporta para CSV
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['url', 'score', 'status', 'title', 'date_processed'])
        writer.writeheader()
        for l in listings:
            writer.writerow({
                'url': l.get('url'),
                'score': l.get('score'),
                'status': l.get('status'),
                'title': l.get('title', ''),
                'date_processed': l.get('date_processed', '')
            })
    # Exporta para markdown bonito
    with open(OUTPUT_MD, 'w', encoding='utf-8') as f:
        f.write(f"# TOP Opportunities (Histórico - {FILTER_STATUS})\n\n")
        f.write(f"Total: {len(listings)}\n\n")
        f.write("| # | Score | Status | Título | Link | Data |\n")
        f.write("|---|-------|--------|--------|------|------|\n")
        for idx, l in enumerate(listings, 1):
            title = l.get('title', '').replace('|', ' ')
            url = l.get('url', '')
            score = l.get('score', '')
            status = l.get('status', '')
            date = l.get('date_processed', '')
            link_md = f"[link]({url})" if url else ''
            f.write(f"| {idx} | {score} | {status} | {title[:40]} | {link_md} | {date} |\n")
    print(f"Exportado {len(listings)} imóveis para {OUTPUT_CSV} e {OUTPUT_MD}")

if __name__ == '__main__':
    main()
