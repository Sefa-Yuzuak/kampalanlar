# -*- coding: utf-8 -*-
"""DKMP 2026 çadır ücret tarifesini (EK-4) resmî PDF'ten çıkarır.

Kaynak: Tarım ve Orman Bakanlığı DKMP, Korunan Alanlar Ücret Tarifesi 2026, EK-4
  https://www.tarimorman.gov.tr/DKMP/Menu/39/Korunan-Alanlar-Ucret-Tarifesi

PDF'te tablo DEVRİK: bölge grupları sütun, kategoriler satır (21 grup x 3 kategori).
Hücreler tablo çizgilerinden okunur (find_tables); konuma göre en yakın sütunu seçmek
illeri yanlış gruplara dağıtıyordu (Doğu Anadolu illeri Karadeniz'e düşüyordu).

Sayfada eğik bir filigran var; hücre metinlerine tek başına duran rakamlar karışıyor,
bunlar temizlenir.

Çıktı: data/tarife_2026.json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
PDF = KOK / "data" / "ham" / "ek4_cadir_tarifesi_2026.pdf"
CIKTI = KOK / "data" / "tarife_2026.json"

KAYNAK = {
    "ad": "Tarım ve Orman Bakanlığı DKMP, Korunan Alanlar Ücret Tarifesi 2026 (EK-4 Çadır)",
    "url": "https://www.tarimorman.gov.tr/DKMP/Menu/39/Korunan-Alanlar-Ucret-Tarifesi",
}

IL_ADLARI = {
    "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Aksaray", "Amasya", "Ankara", "Antalya",
    "Ardahan", "Artvin", "Aydın", "Balıkesir", "Bartın", "Batman", "Bayburt", "Bilecik",
    "Bingöl", "Bitlis", "Bolu", "Burdur", "Bursa", "Çanakkale", "Çankırı", "Çorum", "Denizli",
    "Diyarbakır", "Düzce", "Edirne", "Elazığ", "Erzincan", "Erzurum", "Eskişehir", "Gaziantep",
    "Giresun", "Gümüşhane", "Hakkari", "Hatay", "Iğdır", "Isparta", "İstanbul", "İzmir",
    "Kahramanmaraş", "Karabük", "Karaman", "Kars", "Kastamonu", "Kayseri", "Kilis", "Kırıkkale",
    "Kırklareli", "Kırşehir", "Kocaeli", "Konya", "Kütahya", "Malatya", "Manisa", "Mardin",
    "Mersin", "Muğla", "Muş", "Nevşehir", "Niğde", "Ordu", "Osmaniye", "Rize", "Sakarya",
    "Samsun", "Siirt", "Sinop", "Sivas", "Şanlıurfa", "Şırnak", "Tekirdağ", "Tokat", "Trabzon",
    "Tunceli", "Uşak", "Van", "Yalova", "Yozgat", "Zonguldak",
}
DUZELTME = {"Snop": "Sinop"}                      # PDF'te dizgi hatası
GRUP_KALIP = re.compile(r"^(AKDENİZ|EGE|MARMARA|İÇ ANADOLU|KARADENİZ|DOĞU ANADOLU|GÜNEYDOĞU)-\d$")


def temizle(hucre) -> str:
    """Filigrandan gelen tek başına rakamları ve fazla boşluğu atar."""
    if not hucre:
        return ""
    parcalar = [p for p in str(hucre).replace("\n", " ").split()
                if not re.fullmatch(r"[\d\-–]+", p)]
    return " ".join(parcalar).strip()


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        import pymupdf
    except ImportError:
        sys.exit("PyMuPDF gerekli: pip install pymupdf")
    if not PDF.exists():
        sys.exit(f"PDF yok: {PDF}")

    tablolar = pymupdf.open(PDF)[0].find_tables()
    if not tablolar.tables:
        sys.exit("PDF'te tablo bulunamadı — kaynak biçimi değişmiş olabilir.")
    izgara = tablolar.tables[0].extract()

    # Satırları rolüne göre bul
    grup_satiri = il_satiri = None
    kategori_satirlari: list[tuple[str, list]] = []
    for satir in izgara:
        temiz = [temizle(c) for c in satir]
        if grup_satiri is None and sum(1 for c in temiz if GRUP_KALIP.match(c)) >= 3:
            grup_satiri = temiz
            continue
        if grup_satiri is not None and il_satiri is None and any(
                any(p.strip(",.") in IL_ADLARI for p in c.replace(",", " , ").split())
                for c in temiz):
            il_satiri = temiz
            continue
        etiket = temiz[0] if temiz else ""
        if re.match(r"^\d\.\s*Kategori", etiket, re.IGNORECASE):
            kategori_satirlari.append((etiket, temiz))

    if not grup_satiri or not il_satiri:
        sys.exit("Grup ya da il satırı bulunamadı — PDF yapısı değişmiş.")
    if len(kategori_satirlari) != 3:
        sys.exit(f"3 kategori satırı bekleniyordu, {len(kategori_satirlari)} bulundu.")

    def tutar(m: str):
        s = re.sub(r"[^\d,]", "", m).split(",")[0]
        return int(s) if s else None

    gruplar = []
    for j, g in enumerate(grup_satiri):
        if not GRUP_KALIP.match(g):
            continue
        iller = []
        for parca in (il_satiri[j] if j < len(il_satiri) else "").replace(",", " , ").split():
            ad = DUZELTME.get(parca.strip(",."), parca.strip(",."))
            if ad in IL_ADLARI and ad not in iller:
                iller.append(ad)
        ucret = {}
        for etiket, satir in kategori_satirlari:
            no = re.match(r"^(\d)", etiket).group(1)
            t = tutar(satir[j]) if j < len(satir) else None
            if t:
                ucret[f"{no}. kategori"] = t
        gruplar.append({"grup": g, "iller": sorted(iller), "ucret": ucret})

    # Tek illik grupların (Antalya, Ankara, Edirne, Bolu…) ili, komşu grubun hücresine
    # satır kaymasıyla da düşebiliyor. Tek illik grup asıldır, diğerinden düşülür.
    tekil = {g["iller"][0] for g in gruplar if len(g["iller"]) == 1}
    for g in gruplar:
        if len(g["iller"]) > 1:
            g["iller"] = [i for i in g["iller"] if i not in tekil]

    sonuc = {
        "yil": 2026,
        "birim": "4 kişilik çadır, günlük, TL",
        "kaynak": KAYNAK,
        "notlar": [
            "Tutarlar 4 kişilik çadır için günlük yer kullanım bedelidir.",
            "Ortak kullanım bedeli (su, duş, çamaşırhane, bulaşıkhane, katı/sıvı atık) ayrıca "
            "alınabilir; çadır/karavan ünite başı günlük tarifeyi geçemez ve ilgili Bölge "
            "Müdürlüğünce çıkarılacak Olur ile belirlenir.",
            "Elektrik tüketimi ve ısınma giderleri ortak kullanım bedeline dahil değildir.",
            "Kategori, alanın DKMP tarafından belirlenen sınıfıdır; aynı ilde farklı kategoride "
            "alan bulunabilir. Alanın kategorisi için EK-1 listesine bakın.",
        ],
        "gruplar": gruplar,
    }
    CIKTI.write_text(json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8")

    kapsanan = {i for g in gruplar for i in g["iller"]}
    tum = [v for g in gruplar for v in g["ucret"].values()]
    print(f"{len(gruplar)} bölge grubu -> {CIKTI.relative_to(KOK)}")
    print(f"il eşleşmesi: {len(kapsanan)}/81 | ücret aralığı: {min(tum)} – {max(tum)} TL")
    cift = [i for i in kapsanan if sum(1 for g in gruplar if i in g["iller"]) > 1]
    if cift:
        print("  UYARI birden çok grupta görünen il:", ", ".join(sorted(cift)))
    eksik = sorted(IL_ADLARI - kapsanan)
    if eksik:
        print("  UYARI eşleşmeyen il:", ", ".join(eksik))
    for g in gruplar:
        u = g["ucret"]
        print(f"  {g['grup']:<15} {u.get('1. kategori','?'):>4}/{u.get('2. kategori','?'):>4}/"
              f"{u.get('3. kategori','?'):>4} TL  {', '.join(g['iller'])[:58]}")


if __name__ == "__main__":
    main()
