# -*- coding: utf-8 -*-
"""81 il merkezinin koordinatını tek seferlik çeker: python build/il_merkezleri.py

Kaynak: Wikidata. Her il (P31 = Q48336 "Türkiye ili") için idari merkez (P36) ve
merkezin koordinatı (P625, yalnız en iyi sıralı ifade). Merkez koordinatı yoksa
ilin kendi koordinatı kullanılır ve kayıt "il" olarak işaretlenir.

Alan sayfalarındaki "il merkezine kuş uçuşu N km" satırı bu tablodan hesaplanır.
Çıktı: data/il_merkezleri.json (git'e girer; derleme ağ istemez).
"""
from __future__ import annotations

import csv
import io
import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
CIKTI = KOK / "data" / "il_merkezleri.json"

SORGU = """
SELECT ?ilLabel ?merkezLabel ?koord ?ilkoord WHERE {
  ?il wdt:P31 wd:Q48336 .
  OPTIONAL { ?il wdt:P36 ?merkez . ?merkez p:P625 ?st . ?st a wikibase:BestRank . ?st ps:P625 ?koord . }
  OPTIONAL { ?il p:P625 ?st2 . ?st2 a wikibase:BestRank . ?st2 ps:P625 ?ilkoord . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "tr". }
} ORDER BY ?ilLabel ?koord
"""
NOKTA = re.compile(r"Point\(([-\d.]+) ([-\d.]+)\)")


def nokta(metin: str):
    m = NOKTA.match(metin or "")
    return (round(float(m.group(2)), 5), round(float(m.group(1)), 5)) if m else None


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": SORGU})
    istek = urllib.request.Request(url, headers={
        "Accept": "text/csv", "User-Agent": "kampalanlar-build/1.0 (https://kampalanlar.com)"})
    with urllib.request.urlopen(istek, timeout=60) as y:
        satirlar = list(csv.DictReader(io.StringIO(y.read().decode("utf-8"))))

    iller: dict[str, dict] = {}
    coklu: list[str] = []
    for s in satirlar:
        ad = s["ilLabel"]
        k = nokta(s["koord"])
        if ad in iller:
            if k and iller[ad]["kaynak"] == "merkez":
                coklu.append(ad)          # aynı merkez için ikinci koordinat ifadesi; ilki kalır
            continue
        if k:
            iller[ad] = {"lat": k[0], "lng": k[1], "merkez": s["merkezLabel"], "kaynak": "merkez"}
        elif nokta(s["ilkoord"]):
            ik = nokta(s["ilkoord"])
            iller[ad] = {"lat": ik[0], "lng": ik[1], "merkez": ad, "kaynak": "il"}
    if len(iller) != 81:
        sys.exit(f"81 il bekleniyordu, {len(iller)} geldi — sorgu ya da Wikidata değişmiş.")

    sonuc = {
        "kaynak": {
            "ad": "Wikidata — Türkiye illeri (P31=Q48336), idari merkez (P36), koordinat (P625)",
            "url": "https://query.wikidata.org/",
            "erisim": date.today().isoformat(),
        },
        "not": ("İl merkezi koordinatı, Wikidata'da ilin idari merkezi olarak kayıtlı yerleşimin "
                "koordinatıdır. 'kaynak: il' olan kayıtlarda merkez koordinatı bulunmadığından ilin "
                "kendi koordinatı kullanıldı. Birden çok koordinat ifadesi olan merkezlerde ilk ifade "
                "alındı: " + ", ".join(sorted(set(coklu)))),
        "iller": dict(sorted(iller.items())),
    }
    CIKTI.write_text(json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8")
    ilden = [a for a, v in iller.items() if v["kaynak"] == "il"]
    print(f"{len(iller)} il -> {CIKTI.relative_to(KOK)} | ilin kendi koordinatı: {ilden or '-'} | "
          f"çoklu ifade: {sorted(set(coklu))}")


if __name__ == "__main__":
    main()
