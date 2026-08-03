#!/usr/bin/env python3
import json
import re
import sys
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
    "3404": "Kassel",
    "3405": "Darmstadt",
    "3406": "Offenbach",
    "3407": "Hanau",
    "3408": "Fulda",
    "3409": "Gießen",
    "3410": "Marburg",
    "3411": "Wetzlar",
    "3412": "Limburg",
    "3413": "Bad Homburg",
    "3414": "Bad Hersfeld",
    "3415": "Friedberg",
    "3416": "Hofgeismar",
    "3417": "Homberg (Efze)",
    "3418": "Königstein",
    "3419": "Korbach",
    "3420": "Lauterbach",
    "3421": "Melsungen",
    "3422": "Rüsselsheim",
    "3423": "Schlüchtern",
}

BASE_URL = "https://www.zvg-portal.de"


def fetch_auctions(gericht_code, gericht_name):
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })

    # Önce ana sayfaya git (cookie/session al)
    session.get(f"{BASE_URL}/", timeout=30)

    # Form submit - POST ile
    url = f"{BASE_URL}/index.php?button=Termine%20suchen"
    form_data = {
        'land_abk': 'he',
        'ger_id': gericht_code,
        'button': 'Termine suchen'
    }

    try:
        r = session.post(url, data=form_data, timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f"[{gericht_name}] Hata: {e}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    rows = soup.find_all("tr", class_=re.compile(r"treffer[12]"))
    results = []

    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 4:
            continue

        aktenzeichen = cells[0].get_text(strip=True)
        termin_text = cells[1].get_text(strip=True)
        art_ort = cells[2].get_text(strip=True)
        verkehrswert_text = cells[3].get_text(strip=True)

        vw = 0
        m = re.search(r"[\d.]+", verkehrswert_text.replace(".", "").replace(",", ""))
        if m:
            try:
                vw = int(m.group().replace(".", "").replace(",", ""))
            except ValueError:
                vw = 0

        art_lower = art_ort.lower()
        if "wohnung" in art_lower or "eigentumswohnung" in art_lower:
            typ = "Wohnung"
        elif "grundstück" in art_lower or "baugrund" in art_lower:
            typ = "Grundstück"
        else:
            typ = "Haus"

        termin = ""
        m_date = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", termin_text)
        if m_date:
            termin = f"{m_date.group(3)}-{m_date.group(2)}-{m_date.group(1)}"

        results.append({
            "id": f"{gericht_code}-{aktenzeichen}",
            "title": art_ort,
            "city": gericht_name,
            "type": typ,
            "verkehrswert": vw,
            "date": termin,
            "ag": f"AG {gericht_name}",
            "aktenzeichen": aktenzeichen,
            "termin_raw": termin_text,
        })

    print(f"[{gericht_name}] {len(results)} ilan bulundu.")
    return results


def main():
    all_auctions = []
    for code, name in HESSEN_GERICHTE.items():
        auctions = fetch_auctions(code, name)
        all_auctions.extend(auctions)

    output = {
        "last_updated": datetime.now().isoformat(),
        "count": len(all_auctions),
        "auctions": all_auctions,
    }

    with open("data/auctions.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Toplam {len(all_auctions)} ilan kaydedildi.")


if __name__ == "__main__":
    main()
