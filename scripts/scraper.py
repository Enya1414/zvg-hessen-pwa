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
    "M1401": "Alsfeld",
    "M1305": "Bad Hersfeld",
    "M1202": "Bad Homburg v. d. Hoehe",
    "M1905": "Bad Schwalbach",
    "M1102": "Bensheim",
    "M1801": "Biedenkopf",
    "M1402": "Buedingen",
    "M1103": "Darmstadt",
    "M1104": "Dieburg",
    "M1702": "Dillenburg",
    "M1705": "Dillenburg Zweigstelle Herborn",
    "M1602": "Eschwege",
    "M1803": "Frankenberg (Eder)",
    "M1201": "Frankfurt am Main",
    "M1405": "Friedberg (Hessen)",
    "M1603": "Fritzlar",
    "M1105": "Fuerth",
    "M1301": "Fulda",
    "M1501": "Gelnhausen",
    "M1406": "Giessen",
    "M1106": "Gross-Gerau",
    "M1502": "Hanau",
    "M1307": "Huenfeld",
    "M1903": "Idstein",
    "M1607": "Kassel",
    "M1605": "Kassel Zweigstelle Hofgeismar",
    "M1807": "Kirchhain",
    "M1203": "Koenigstein im Taunus",
    "M1608": "Korbach",
    "M1111": "Lampertheim",
    "M1112": "Langen",
    "M1706": "Limburg a. d. Lahn",
    "M1809": "Marburg",
    "M1609": "Melsungen",
    "M1113": "Offenbach am Main",
    "M1114": "Ruesselsheim",
    "M1904": "Rheingau",
    "M1107": "Darmstadt-Dieburg",
    "M1812": "Schwalmstadt",
    "M1117": "Wiesbaden",
    "M1709": "Wetzlar",
    "M1710": "Weilburg",
    "M1906": "Wiesbaden-Land",
}

BASE_URL = "https://www.zvg-portal.de"


def parse_auctions(html, gericht_code, gericht_name):
    soup = BeautifulSoup(html, "html.parser")
    results = []

    links = soup.find_all("a", href=re.compile(r"showZvg"))
    print("[" + gericht_name + "] Bulunan ilan linki: " + str(len(links)))

    for link in links:
        table = link.find_parent("table")
        if not table:
            continue

        aktenzeichen = link.get_text(strip=True).replace("(Detailansicht)", "").strip()

        href = link.get("href", "")
        m_id = re.search(r"zvg_id=(\d+)", href)
        zvg_id = m_id.group(1) if m_id else ""

        objekt = ""
        verkehrswert_raw = ""
        termin_raw = ""

        rows = table.find_all("tr")
        for row in rows:
            tds = row.find_all("td")
            if len(tds) < 2:
                continue
            label = tds[0].get_text(strip=True).lower()
            value = tds[1].get_text(" ", strip=True)

            if "objekt" in label or "lage" in label:
                objekt = value
            elif "verkehrswert" in label:
                verkehrswert_raw = value
            elif "termin" in label and "letzte" not in label:
                termin_raw = value

        vw = 0
        vw_clean = re.sub(r"[^\d]", "", verkehrswert_raw.split(",")[0])
        if vw_clean:
            try:
                vw = int(vw_clean)
            except ValueError:
                vw = 0

        termin = ""
        m_date = re.search(r"(\d{2})\.\s*(\w+)\s*(\d{4})", termin_raw)
        if m_date:
            monat_map = {
                "januar": "01", "februar": "02", "maerz": "03", "april": "04",
                "mai": "05", "juni": "06", "juli": "07", "august": "08",
                "september": "09", "oktober": "10", "november": "11", "dezember": "12",
            }
            monat = monat_map.get(m_date.group(2).lower(), "00")
            termin = m_date.group(3) + "-" + monat + "-" + m_date.group(1)
        else:
            m_date2 = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", termin_raw)
            if m_date2:
                termin = m_date2.group(3) + "-" + m_date2.group(2) + "-" + m_date2.group(1)

        obj_lower = objekt.lower()
        if "wohnung" in obj_lower or "eigentumswohnung" in obj_lower:
            typ = "Wohnung"
        elif "grundstuck" in obj_lower or "grundst" in obj_lower or "baugrund" in obj_lower:
            typ = "Grundstueck"
        else:
            typ = "Haus"

        if not aktenzeichen:
            continue

        results.append({
            "id": gericht_code + "-" + zvg_id,
            "title": objekt[:120],
            "city": gericht_name,
            "type": typ,
            "verkehrswert": vw,
            "date": termin,
            "ag": "AG " + gericht_name,
            "aktenzeichen": aktenzeichen,
            "termin_raw": termin_raw,
            "zvg_id": zvg_id,
        })

    return results


def fetch_auctions(gericht_code, gericht_name):
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "de,en-US;q=0.7,en;q=0.3",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Referer": BASE_URL + "/",
    })

    try:
        r0 = session.get(BASE_URL + "/index.php?button=Termine%20suchen", timeout=30)
        if r0.status_code != 200:
            print("[" + gericht_name + "] GET hatasi: " + str(r0.status_code))
            return []
    except Exception as e:
        print("[" + gericht_name + "] GET hatasi: " + str(e))
        return []

    time.sleep(1)

    form_data = {
        "land_abk": "he",
        "ger_id": gericht_code,
        "ger_name": gericht_name,
        "button": "Suchen",
        "order_by": "2",
        "az1": "", "az2": "", "az3": "", "az4": "",
        "str": "", "hnr": "", "plz": "", "ort": "", "ortsteil": "",
        "vtermin": "", "btermin": "",
        "art": "ALL", "obj": "ALL", "etype": "N",
    }

    try:
        r = session.post(
            BASE_URL + "/index.php?button=Suchen",
            data=form_data,
            timeout=30,
        )
        r.raise_for_status()
        print("[" + gericht_name + "] POST: " + str(r.status_code) + ", boyut: " + str(len(r.text)))
    except Exception as e:
        print("[" + gericht_name + "] POST hatasi: " + str(e))
        return []

    if len(r.text) < 8000:
        print("[" + gericht_name + "] Sonuc yok.")
        return []

    results = parse_auctions(r.text, gericht_code, gericht_name)
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
