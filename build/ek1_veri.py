# -*- coding: utf-8 -*-
"""DKMP 2026 ücret tarifesi EK-1'i (coğrafi grup ve kategoriye göre korunan alan listesi)
resmî PDF'ten çıkarır: python build/ek1_veri.py

Kaynak: Tarım ve Orman Bakanlığı DKMP, Korunan Alanlar Ücret Tarifesi 2026, EK-1
  https://www.tarimorman.gov.tr/DKMP/Menu/39/Korunan-Alanlar-Ucret-Tarifesi

PDF'te her satır bir il; sütunlar ana bölge, alt bölge (grup), il, I./II./III. kategori.
Kategori hücresinde alanlar satır sonuyla ayrılmış; boş hücre "-".

GRUP ETİKETİ TUZAĞI (ölçüldü): grup hücresi birleşik ve sayfa sonunu aşıyor; etiket metni
birleşik hücrenin ortasındaki satıra düşüyor. "Marmara - 2" etiketi 3. sayfada Bursa
satırında, ama grubun ilk ili Balıkesir 2. sayfanın sonunda etiketsiz. İleri doldurma
Balıkesir'i Marmara-1'e, Artvin/Kastamonu'yu Karadeniz-1'e, Çankırı/Aksaray'ı
İç Anadolu-2'ye yanlış bağlıyordu. Bu yüzden grup, ilini açıkça listeleyen EK-4'ten
(data/tarife_2026.json) alınır; EK-1'deki her AÇIK etiket EK-4 ile karşılaştırılır ve
biri bile çelişirse betik durur.

Çıktı: data/kategori_2026.json — her kayıt (il, grup, kategori, ad). EK-4'teki ücret
tabloyla birleştirme derle.py'de yapılır.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
PDF = KOK / "data" / "ham" / "ek1_kategori_listesi_2026.pdf"
TARIFE = KOK / "data" / "tarife_2026.json"
CIKTI = KOK / "data" / "kategori_2026.json"

KAYNAK = {
    "ad": "Tarım ve Orman Bakanlığı DKMP, Korunan Alanlar Ücret Tarifesi 2026 (EK-1 Coğrafi Grup "
          "ve Kategorilere Göre Korunan Alanlar Listesi)",
    "url": "https://www.tarimorman.gov.tr/DKMP/Menu/39/Korunan-Alanlar-Ucret-Tarifesi",
}
GRUP_KALIP = re.compile(r"^(Akdeniz|Ege|Marmara|İç Anadolu|Karadeniz|Doğu Anadolu|Güneydoğu)\s*-\s*(\d)$")


def grup_adi(metin: str) -> str | None:
    """'Akdeniz - 2' -> 'AKDENİZ-2' (EK-4 tablosundaki yazım). Türkçe i -> İ."""
    m = GRUP_KALIP.match(" ".join(metin.split()))
    if not m:
        return None
    return m.group(1).replace("i", "İ").upper() + "-" + m.group(2)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    import pymupdf
    if not PDF.exists():
        sys.exit(f"PDF yok: {PDF}")
    tarife = json.loads(TARIFE.read_text(encoding="utf-8"))
    tarife_il_grup = {il: g["grup"] for g in tarife["gruplar"] for il in g["iller"]}
    tarife_gruplar = {g["grup"] for g in tarife["gruplar"]}

    kayitlar: list[dict] = []
    acik_etiket: list[tuple[str, str]] = []                      # (il, EK-1'deki açık etiket)
    il = None
    for sayfa in pymupdf.open(PDF):
        for tablo in sayfa.find_tables().tables:
            for satir in tablo.extract():
                hucre = [(c or "").strip() for c in satir]
                if len(hucre) != 6:
                    continue
                if hucre[2] and not hucre[2].isupper():          # başlık satırları büyük harf
                    il = " ".join(hucre[2].split())
                if not il:
                    continue
                if il not in tarife_il_grup:
                    sys.exit(f"EK-4'te grubu olmayan il: {il}")
                g = grup_adi(hucre[1])
                if g:
                    acik_etiket.append((il, g))
                for kategori, metin in zip((1, 2, 3), hucre[3:6]):
                    for ad in metin.split("\n"):
                        ad = " ".join(ad.split())
                        if ad and ad != "-":
                            kayitlar.append({"il": il, "grup": tarife_il_grup[il],
                                             "kategori": kategori, "ad": ad})

    if not kayitlar:
        sys.exit("EK-1'den kayıt çıkmadı — PDF biçimi değişmiş olabilir.")
    bilinmeyen = {g for _, g in acik_etiket} - tarife_gruplar
    if bilinmeyen:
        sys.exit(f"EK-4'te olmayan grup: {bilinmeyen}")
    uyumsuz = [(il, g, tarife_il_grup[il]) for il, g in acik_etiket if tarife_il_grup[il] != g]
    if uyumsuz:
        sys.exit(f"EK-1'deki açık grup etiketi EK-4 ile çelişiyor: {uyumsuz}")
    print(f"EK-1'deki {len(acik_etiket)} açık grup etiketinin hepsi EK-4 ile uyumlu")

    KAYNAK["erisim"] = date.today().isoformat()
    CIKTI.write_text(json.dumps({"yil": 2026, "kaynak": KAYNAK, "kayitlar": kayitlar},
                                ensure_ascii=False, indent=1), encoding="utf-8")
    iller = {k["il"] for k in kayitlar}
    print(f"{len(kayitlar)} kayıt, {len(iller)} il, {len({k['grup'] for k in kayitlar})} grup "
          f"-> {CIKTI.relative_to(KOK)}")
    for kat in (1, 2, 3):
        print(f"  {kat}. kategori: {sum(1 for k in kayitlar if k['kategori'] == kat)}")


if __name__ == "__main__":
    main()
