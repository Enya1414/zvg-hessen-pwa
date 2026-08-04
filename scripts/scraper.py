#!/usr/bin/env python3
import json
import re
import sys
import time
from datetime import datetime

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("requests ve beautifulsoup4 gerekli")
    sys.exit(1)

HESSEN_GERICHTE = {
    "3402": "Frankfurt am Main",
    "3403": "Wiesbaden",
}

BASE_URL = "https://www.zvg-portal.de"


def fetch_auctions(gericht_code, gericht_name):
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })

    try:
        r0 = session.get(f"{BASE_URL}/", timeout=30)
        print(f"[{gericht_name}] Ana sayfa: {r0.status_code}")
    except Exception as e:
        print(f"[{gericht_name}] Ana sayfa hatası: {e}")
        return []

    time.sleep(1)

    url = f"{BASE_URL}/index.php?button=Termine%20suchen"
    form_data = {
        'land_abk': 'he',
        'ger_id': gericht_code,
        'button': 'Termine suchen'
    }

    try:
        r = session.post(url, data=form_data, timeout=30)
        r.raise_for_status()
        print(f"[{gericht_name}] POST: {r.status_code}, boyut: {len(r.text)}")
    except Exception as e:
        print(f"[{gericht_name}] POST hatası: {e}")
        return []

    if gericht_code == "3402":
        print("--- HTML SNIPPET ---")
        print(r.text[:5000])
        print("--- HTML SNIPPET SONU ---")

    soup = BeautifulSoup(r.text, "html.parser")
    all_rows = soup.find_all("tr")
    print(f"[{gericht_name}] Toplam TR: {len(all_rows)}")

    classes = set()
    for row in all_rows:
        if row.get('class'):
            classes.add(str(row.get('class')))
    if classes:
        print(f"[{gericht_name}] TR class'ları: {classes}")

    rows = soup.find_all("tr", class_=re.compile(r"treffer[12]"))
    print(f"[{gericht_name}] {len(rows)} ilan bulundu.")
    return []


def main():
    for code, name in HESSEN_GERICHTE.items():
        fetch_auctions(code, name)
        time.sleep(2)

    output = {
        "last_updated": datetime.now().isoformat(),
        "count": 0,
        "auctions": [],
    }

    with open("data/auctions.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
