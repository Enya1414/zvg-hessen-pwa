#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
    "HE1100": "Frankfurt am Main",
    "HE1200": "Wiesbaden",
}

BASE_URL = "https://www.zvg-portal.de"


def fetch_auctions(gericht_code, gericht_name):
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "de,en-US;q=0.7,en;q=0.3",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    })

    try:
        r0 = session.get(BASE_URL + "/", timeout=30)
        print("[" + gericht_name + "] Ana sayfa: " + str(r0.status_code))
        if r0.status_code != 200:
            return []
    except Exception as e:
        print("[" + gericht_name + "] Ana sayfa hatasi: " + str(e))
        return []

    time.sleep(1)

    url = BASE_URL + "/index.php?button=Termine%20suchen"
    form_data = {
        "land_abk": "he",
        "ger_id": gericht_code,
        "button": "Termine suchen",
    }

    try:
        r = session.post(url, data=form_data, timeout=30)
        r.raise_for_status()
        print("[" + gericht_name + "] POST: " + str(r.status_code) + ", boyut: " + str(len(r.text)))
    except Exception as e:
        print("[" + gericht_name + "] POST hatasi: " + str(e))
        return []

    print("[DEBUG] HTML FULL:")
    print(r.text)

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

    print("Debug tamamlandi.")


if __name__ == "__main__":
    main()
