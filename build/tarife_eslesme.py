# -*- coding: utf-8 -*-
"""Korunan alanı DKMP'nin resmî tarifesiyle eşleştirir: python build/tarife_eslesme.py

EK-1 (data/kategori_2026.json) her alanın ilini ve kategorisini (1/2/3) verir;
EK-4 (data/tarife_2026.json) 21 bölge grubu × 3 kategori için 4 kişilik çadırın
günlük yer kullanım bedelini verir. İkisini birleştirince her alanın kendi ücreti
çıkıyor; eskiden kullanıcı "kategorini resmî PDF'ten bul" diye yollanıyordu.

Eşleşme kuralları (hepsi ölçümle konuldu, 15.09.2026):
  - Ad sonundaki tür eki atılır. Bizim kayıtta "Milli Park", EK-1'de "Milli Parkı"
    yazıyor; bu tek harf yüzünden 50 alanın 6'sı eşleşmiyordu.
  - Türkçe harfler lower()'dan ÖNCE çevrilir (İ.lower() i + U+0307 üretir).
  - Çok illi alanların ("Adana / Niğde / Kayseri") illeri tek tek denenir.
  - Aynı çekirdek ad iki farklı kategoriye düşüyorsa eşleşme YAPILMAZ. Tahmin yok.
  - EK-1 kaydının ili, EK-4'teki grubun il listesinde yoksa eşleşme yapılmaz.

Sonuç: 358 alanın 277'si eşleşti, belirsiz 0. Eşleşmeyen 81'in 32'si Tabiatı
Koruma Alanı: bunlar tarifede hiç yok, çünkü kamu kullanımına kapalı. Tür etiketi
tutmayan 4 eşleşme kabul edildi (Abant Gölü ve Akdağ tabiat parkından milli parka
geçti, Mut Yerköprü ve Harmankaya şelaleleri EK-1'de tabiat anıtı): yer aynı,
yalnızca tescil türü farklı yazılmış.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent

TR = str.maketrans("İIıŞşĞğÇçÖöÜüÂâÎîÛû", "iiisSgGcCoOuUaaiiuu")
# Uzun ekler önce: "tarihi milli parki" atılmadan "milli parki" atılırsa "tarihi" kalır.
EKLER = (
    "tarihi milli parki", "tarihi milli park", "milli parki", "milli park", "tmp",
    "tabiat parki", "tabiat park", "tabiati koruma alani", "tabiat koruma alani",
    "tabiat aniti", "sulak alani", "yasam alani",
)


def sade(metin: str) -> str:
    m = metin.translate(TR).lower()
    return " ".join("".join(c if c.isalnum() else " " for c in m).split())


def cekirdek(metin: str) -> str:
    """Tür eki atılmış ad: 'Abant Gölü Milli Park' -> 'abant golu'."""
    a = sade(metin)
    degisti = True
    while degisti:
        degisti = False
        for ek in EKLER:
            if a == ek:
                return ""
            if a.endswith(" " + ek):
                a = a[: -len(ek)].strip()
                degisti = True
                break
    return a


def eslestir(alanlar: list[dict], kategori: dict | None, tarife: dict | None) -> int:
    """Eşleşen her alana a["tarife"] yazar, eşleşen sayısını döndürür."""
    for a in alanlar:
        a["tarife"] = None
    if not kategori or not tarife:
        return 0

    grup_ucret = {sade(g["grup"]): g for g in tarife["gruplar"]}
    dizin: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for k in kategori["kayitlar"]:
        dizin[sade(k["il"])][cekirdek(k["ad"])].append(k)

    n = 0
    for a in alanlar:
        cek = cekirdek(f"{a['ad']} {a['tur_bilgi']['ad']}")
        if not cek:
            continue
        adaylar: list[dict] = []
        for il in a["iller"]:
            adaylar += dizin[sade(il)].get(cek, [])
        if not adaylar or len({x["kategori"] for x in adaylar}) != 1:
            continue
        k = adaylar[0]
        g = grup_ucret.get(sade(k["grup"]))
        if not g or sade(k["il"]) not in {sade(i) for i in g["iller"]}:
            continue
        ucret = g["ucret"].get(f"{k['kategori']}. kategori")
        if not ucret:
            continue
        a["tarife"] = {
            "kategori": k["kategori"],
            "grup": g["grup"],
            "ucret": ucret,
            "ek1_ad": k["ad"],
            "birim": tarife["birim"],
            "kaynak": tarife["kaynak"],
        }
        n += 1
    return n


def _dene() -> None:
    """Betik doğrudan çalıştırılınca eşleşme sayılarını basar (yayın etkisi yok)."""
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import derle

    site = derle.yukle("site.json")
    alanlar = derle.hazirla(derle.yukle("korunan_alanlar.json"), site)
    n = eslestir(alanlar, derle.yukle("kategori_2026.json", None),
                 derle.yukle("tarife_2026.json", None))
    kamp = [a for a in alanlar if a["kamp_izni_resmi"]]
    print(f"eşleşen {n}/{len(alanlar)} alan")
    print(f"kamp izinli {sum(1 for a in kamp if a['tarife'])}/{len(kamp)}")
    for a in alanlar[:3]:
        if a["tarife"]:
            print(" ", a["ad"], "->", json.dumps(a["tarife"], ensure_ascii=False))


if __name__ == "__main__":
    _dene()
