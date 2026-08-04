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
    "HE1300": "Kassel",
    "HE1400": "Darmstadt",
    "HE1500": "Offenbach",
    "HE1600": "Hanau",
    "HE1700": "Fulda",
    "HE1800": "Giessen",
    "HE1900": "Marburg",
    "HE2000": "Wetzlar",
    "HE2100": "Limburg",
    "HE2200": "Bad Homburg",
    "HE2300": "Bad Hersfeld",
    "HE2400": "Friedberg",
    "HE2500": "Hofgeismar",
    "HE2600": "Homberg Efze",
    "HE2700": "Koenigstein",
    "HE2800": "Korbach",
    "HE2900": "Lauterbach",
    "HE3000": "Melsungen",
    "HE3100": "Ruesselsheim",
    "HE3200": "Schluechtern",
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

    if gericht_code == "HE1100":
        print("[DEBUG] HTML (ilk 3000):")
        print(r.text[:3000])

    soup = BeautifulSoup(r.text, "html.parser")
    rows = soup.find_all("tr", class_=re.compile(r"treffer[12]"))

    if not rows:
        all_trs = soup.find_all("tr")
        rows = []
        for tr in all_trs:
            tds = tr.find_all("td")
            if len(tds) >= 4:
                text = tr.get_text(strip=True).lower()
                if "aktenzeichen" in text or "termin" in text:
                    continue
                rows.append(tr)
        if rows:
            print("[" + gericht_name + "] fallback ile " + str(len(rows)) + " satir bulundu")

    results = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 4:
            continue

        aktenzeichen = cells[0].get_text(strip=True)
        termin_text = cells[1].get_text(strip=True)
        art_ort = cells[2].get_text(strip=True)
        verkehrswert_text = cells[3].get_text(strip=True)

        if not aktenzeichen or len(aktenzeichen) < 3:
            continue

        vw = 0
        vw_clean = re.sub(r"[^\d]", "", verkehrswert_text)
        if vw_clean:
            try:
                vw = int(vw_clean)
            except ValueError:
                vw = 0

        art_lower = art_ort.lower()
        if "wohnung" in art_lower or "eigentumswohnung" in art_lower:
            typ = "Wohnung"
        elif "grundstuck" in art_lower or "baugrund" in art_lower:
            typ = "Grundstueck"
        else:
            typ = "Haus"

        termin = ""
        m_date = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", termin_text)
        if m_date:
            termin = m_date.group(3) + "-" + m_date.group(2) + "-" + m_date.group(1)

        results.append({
            "id": gericht_code + "-" + aktenzeichen,
            "title": art_ort,
            "city": gericht_name,
            "type": typ,
            "verkehrswert": vw,
            "date": termin,
            "ag": "AG " + gericht_name,
            "aktenzeichen": aktenzeichen,
            "termin_raw": termin_text,
        })

    print("[" + gericht_name + "] " + str(len(results)) + " ilan bulundu.")
    return results


def main():
    all_auctions = []
    for code, name in HESSEN_GERICHTE.items():
        auctions = fetch_auctions(code, name)
        all_auctions.extend(auctions)
        time.sleep(2)

    output = {
        "last_updated": datetime.now().isoformat(),
        "count": len(all_auctions),
        "auctions": all_auctions,
    }

    with open("data/auctions.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("Toplam " + str(len(all_auctions)) + " ilan kaydedildi.")


if __name__ == "__main__":
    main()
