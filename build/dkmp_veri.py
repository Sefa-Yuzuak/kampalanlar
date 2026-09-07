# -*- coding: utf-8 -*-
"""DKMP Korunan Alan İstatistikleri (2025) Excel dosyalarını tek biçime çevirir.

Kaynak: Tarım ve Orman Bakanlığı, Doğa Koruma ve Milli Parklar Genel Müdürlüğü
  https://www.tarimorman.gov.tr/DKMP/Menu/18/Korunan-Alan-Istatistikleri

Girdi (data/ham/):  Tabiat_Parkı_2025.xlsx · Milli_Park_2025.xlsx · TabiatiKoruma_2025.xlsx
Çıktı:              data/korunan_alanlar.json

Kaynak dosyalardaki DOĞRULANMIŞ hatalar ve burada uygulanan onarımlar:
  1. Milli Park dosyasında Enlem/Boylam sütunları TERS (31 satır ters, 5 düz).
     -> Her satırda iki sıralama Türkiye sınır kutusuna karşı denenir; içeride kalan alınır.
        İkisi de içerideyse dosyanın çoğunluk yönü uygulanır.
  2. 12 kayıtta ondalık ayraç yok (41126699 -> 41.126699).
     -> 7-8 haneli tam sayı görülürse ilk iki haneden sonra ondalık eklenir.
  3. İl bilgisi ayrı satırlarda NUTS-3 koduyla grup başlığı olarak geliyor (TR100, TR211…).
     -> İleri doldurma + NUTS-3 -> il adı tablosu.
  4. Alan adlarında fazla boşluk ve tür kısaltması (TP/MP/TKA) var. -> temizlenir, tür alana yazılır.

Kural: kaynakta olmayan hiçbir alan tahminle doldurulmaz.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
HAM = KOK / "data" / "ham"
CIKTI = KOK / "data" / "korunan_alanlar.json"

KAYNAK_URL = "https://www.tarimorman.gov.tr/DKMP/Menu/18/Korunan-Alan-Istatistikleri"
KAYNAK_AD = "Tarım ve Orman Bakanlığı DKMP, Korunan Alan İstatistikleri 2025"

# Türkiye sınır kutusu (küçük pay bırakılmış)
EN_MIN, EN_MAX, BOY_MIN, BOY_MAX = 35.8, 42.2, 25.6, 44.9

DOSYALAR = [
    ("Tabiat_Parkı_2025.xlsx", "tabiat_parki", "Tabiat Parkı", "TP"),
    ("Milli_Park_2025.xlsx", "milli_park", "Milli Park", "MP"),
    ("TabiatiKoruma_2025.xlsx", "tabiati_koruma", "Tabiatı Koruma Alanı", "TKA"),
]

NUTS3 = {
    "TR100": "İstanbul", "TR211": "Tekirdağ", "TR212": "Edirne", "TR213": "Kırklareli",
    "TR221": "Balıkesir", "TR222": "Çanakkale", "TR310": "İzmir", "TR321": "Aydın",
    "TR322": "Denizli", "TR323": "Muğla", "TR331": "Manisa", "TR332": "Afyonkarahisar",
    "TR333": "Kütahya", "TR334": "Uşak", "TR411": "Bursa", "TR412": "Eskişehir",
    "TR413": "Bilecik", "TR421": "Kocaeli", "TR422": "Sakarya", "TR423": "Düzce",
    "TR424": "Bolu", "TR425": "Yalova", "TR510": "Ankara", "TR521": "Konya",
    "TR522": "Karaman", "TR611": "Antalya", "TR612": "Isparta", "TR613": "Burdur",
    "TR621": "Adana", "TR622": "Mersin", "TR631": "Hatay", "TR632": "Kahramanmaraş",
    "TR633": "Osmaniye", "TR711": "Kırıkkale", "TR712": "Aksaray", "TR713": "Niğde",
    "TR714": "Nevşehir", "TR715": "Kırşehir", "TR721": "Kayseri", "TR722": "Sivas",
    "TR723": "Yozgat", "TR811": "Zonguldak", "TR812": "Karabük", "TR813": "Bartın",
    "TR821": "Kastamonu", "TR822": "Çankırı", "TR823": "Sinop", "TR831": "Samsun",
    "TR832": "Tokat", "TR833": "Çorum", "TR834": "Amasya", "TR901": "Trabzon",
    "TR902": "Ordu", "TR903": "Giresun", "TR904": "Rize", "TR905": "Artvin",
    "TR906": "Gümüşhane", "TRA11": "Erzurum", "TRA12": "Erzincan", "TRA13": "Bayburt",
    "TRA21": "Ağrı", "TRA22": "Kars", "TRA23": "Iğdır", "TRA24": "Ardahan",
    "TRB11": "Malatya", "TRB12": "Elazığ", "TRB13": "Bingöl", "TRB14": "Tunceli",
    "TRB21": "Van", "TRB22": "Muş", "TRB23": "Bitlis", "TRB24": "Hakkari",
    "TRC11": "Gaziantep", "TRC12": "Adıyaman", "TRC13": "Kilis", "TRC21": "Şanlıurfa",
    "TRC22": "Diyarbakır", "TRC31": "Mardin", "TRC32": "Batman", "TRC33": "Şırnak",
    "TRC34": "Siirt",
}

# Rekreasyon Değeri sütununda kamp izni anlamına gelen ifadeler
KAMP_KALIPLARI = re.compile(r"çadır|kamp|karavan", re.IGNORECASE)

# Tablonun altındaki açıklama/dipnot satırları (uyarı basmaya değmez)
DIPNOT = re.compile(r"^(NOT:|Kaynak:|\(\d+\)|\d+\s*[-.)])", re.IGNORECASE)


def _metin(v) -> str:
    return " ".join(str(v).split()) if v is not None else ""


def _sayi(v) -> float | None:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(" ", "")
    if not s:
        return None
    # "2.931,32" (TR) ve "2931.32" (EN) biçimlerinin ikisi de gelebiliyor
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _koordinat_onar(v) -> float | None:
    """41126699 -> 41.126699 ; '37394757' -> 37.394757 ; 41.11294 -> 41.11294"""
    s = _metin(v).replace(",", ".")
    if not s:
        return None
    if re.fullmatch(r"\d{7,9}", s):
        return float(s[:2] + "." + s[2:])
    try:
        return float(s)
    except ValueError:
        return None


def _tarih(v) -> str:
    if isinstance(v, (datetime, date)):
        return v.strftime("%Y-%m-%d")
    s = _metin(v)
    m = re.match(r"(\d{1,2})[./](\d{1,2})[./](\d{4})", s)
    if m:
        return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    if re.fullmatch(r"\d{5}", s):                       # Excel seri numarası
        return (date(1899, 12, 30) + __import__("datetime").timedelta(days=int(s))).isoformat()
    return s[:10] if s else ""


def _icinde(en: float, boy: float) -> bool:
    return EN_MIN <= en <= EN_MAX and BOY_MIN <= boy <= BOY_MAX


def _basliklar(satirlar: list, bi: int) -> dict[str, int]:
    """Üç başlık satırını birleştirip anahtar -> sütun indeksi haritası üretir."""
    birlesik = []
    for j in range(len(satirlar[bi])):
        parcalar = []
        for k in range(bi, min(bi + 3, len(satirlar))):
            if j < len(satirlar[k]) and satirlar[k][j]:
                parcalar.append(str(satirlar[k][j]).split("\n")[0].strip())
        birlesik.append(" | ".join(dict.fromkeys(parcalar)).lower())
    h: dict[str, int] = {}
    for j, b in enumerate(birlesik):
        if "alan adı" in b: h["ad"] = j
        elif "bölge müdürlüğü" in b: h["bolge"] = j
        elif "alan (hektar)" in b or "alan  (hektar)" in b: h["hektar"] = j
        elif "ilantarihi" in b or "ilan tarihi" in b: h["ilan"] = j
        elif "enlem" in b: h["enlem"] = j
        elif b.strip() == "boylam": h["boylam"] = j
        elif "yükseklik" in b: h["rakim"] = j
        elif "rekreasyon" in b: h["rekreasyon"] = j
        elif "gelişme plan" in b: h["plan"] = j
        elif "ulusal sınıflama" in b: h["kod"] = j
    # Boylam, "enlem" sütununun hemen sağında; başlık boşsa oradan al
    if "enlem" in h and "boylam" not in h:
        h["boylam"] = h["enlem"] + 1
    # Kaynak/tabii değerler: enlem-rakım-rekreasyon dışındaki metin sütunları
    h["deger_sutunlari"] = [j for j, b in enumerate(birlesik)
                            if ("değer" in b or "kaynak" in b) and "rekreasyon" not in b]
    return h


def dosya_oku(dosya: Path, tur: str, tur_ad: str, kisaltma: str) -> list[dict]:
    import openpyxl

    ws = openpyxl.load_workbook(dosya, read_only=True, data_only=True).active
    satirlar = [list(s) for s in ws.iter_rows(values_only=True)]
    bi = next(i for i, s in enumerate(satirlar) if s and any("Alan Adı" in str(c) for c in s if c))
    h = _basliklar(satirlar, bi)
    for z in ("ad", "hektar", "enlem", "boylam"):
        if z not in h:
            sys.exit(f"{dosya.name}: '{z}' sütunu bulunamadı — başlık yapısı değişmiş olabilir.")

    # 1. geçiş: ham satırlar + il ileri doldurma
    ham: list[dict] = []
    il = ""
    for s in satirlar[bi + 3:]:
        if not s:
            continue
        kod = _metin(s[0])
        if kod:
            # Birden çok ile yayılan alanlar "TR332+TR322" ya da "TR521+522" biçiminde geliyor.
            # Bunları atlamak, alanın bir önceki ilde görünmesine yol açıyordu.
            parcalar = [p.strip() for p in kod.split("+") if p.strip()]
            adlar, cozuldu = [], bool(parcalar)
            for i, p in enumerate(parcalar):
                if p not in NUTS3 and parcalar and re.fullmatch(r"\d{3}", p):
                    p = parcalar[0][:2] + p          # "522" -> "TR522"
                if p in NUTS3:
                    adlar.append(NUTS3[p])
                else:
                    cozuldu = False
            if cozuldu and adlar:
                yeni_il = " / ".join(dict.fromkeys(adlar))
                # Kaynak dosyada satır kayması var: Milli Park listesinde "Aladağlar MP"
                # adı bir satır aşağı kaymış ve sonraki il başlığı satırıyla çakışmış.
                # Böyle bir satırda ad ÖNCEKİ ile aittir; kod ise sonraki satırlar için geçerlidir.
                kayik_ad = _metin(s[h["ad"]]) if h["ad"] < len(s) else ""
                if kayik_ad:
                    ham.append({"il": il, "satir": s})
                il = yeni_il
                continue
            if kod != "TR" and not DIPNOT.match(kod):
                print(f"  UYARI {dosya.name}: çözülemeyen il kodu {kod!r}")
        ad = _metin(s[h["ad"]]) if h["ad"] < len(s) else ""
        if not ad:
            continue
        ham.append({"il": il, "satir": s})

    # 2. geçiş: dosyanın çoğunluk koordinat yönünü belirle
    duz = ters = 0
    for k in ham:
        s = k["satir"]
        a, b = _koordinat_onar(s[h["enlem"]]), _koordinat_onar(s[h["boylam"]])
        if a is None or b is None:
            continue
        d, t = _icinde(a, b), _icinde(b, a)
        if d and not t: duz += 1
        elif t and not d: ters += 1
    dosya_ters = ters > duz
    if dosya_ters:
        print(f"  NOT {dosya.name}: Enlem/Boylam sütunları ters (ters={ters}, düz={duz}); düzeltiliyor.")

    # 3. geçiş: kayıtları üret
    cikti = []
    for k in ham:
        s = k["satir"]
        ad_ham = _metin(s[h["ad"]])
        # Kaynakta ada dipnot işareti yapışmış olabiliyor: "Gökpınar Gölü TP (2)".
        # Önce dipnotu, sonra tür kısaltmasını at.
        ad = re.sub(r"\s*\(\d+\)\s*$", "", ad_ham)
        ad = re.sub(rf"\s+{kisaltma}\.?$", "", ad).strip()
        a, b = _koordinat_onar(s[h["enlem"]]), _koordinat_onar(s[h["boylam"]])
        en = boy = None
        if a is not None and b is not None:
            d, t = _icinde(a, b), _icinde(b, a)
            if d and not t:      en, boy = a, b
            elif t and not d:    en, boy = b, a
            elif d and t:        en, boy = (b, a) if dosya_ters else (a, b)
        rek = _metin(s[h["rekreasyon"]]) if "rekreasyon" in h and h["rekreasyon"] < len(s) else ""
        degerler = [_metin(s[j]) for j in h["deger_sutunlari"] if j < len(s) and _metin(s[j])]
        cikti.append({
            "ad": ad,
            "tur": tur,
            "tur_ad": tur_ad,
            "il": k["il"],
            "bolge_mudurlugu": _metin(s[h["bolge"]]) if "bolge" in h else "",
            "hektar": _sayi(s[h["hektar"]]),
            "ilan_tarihi": _tarih(s[h["ilan"]]) if "ilan" in h else "",
            "plan_tarihi": _tarih(s[h["plan"]]) if "plan" in h and h["plan"] < len(s) else "",
            "lat": round(en, 6) if en is not None else None,
            "lng": round(boy, 6) if boy is not None else None,
            "rakim_m": _sayi(s[h["rakim"]]) if "rakim" in h and h["rakim"] < len(s) else None,
            "kaynak_degeri": degerler,
            "rekreasyon": rek,
            "kamp_izni_resmi": bool(KAMP_KALIPLARI.search(rek)),
            "dkmp_kodu": _metin(s[h["kod"]]) if "kod" in h else "",
            "kaynak": {"ad": KAYNAK_AD, "url": KAYNAK_URL, "dosya": dosya.name},
        })
    return cikti


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    kayitlar: list[dict] = []
    for dosya, tur, tur_ad, kis in DOSYALAR:
        yol = HAM / dosya
        if not yol.exists():
            print(f"  {dosya:<26} YOK, atlandı"); continue
        k = dosya_oku(yol, tur, tur_ad, kis)
        kayitlar += k
        print(f"  {dosya:<26} {len(k):>4} kayıt")

    kayitlar.sort(key=lambda k: (k["il"], k["tur"], k["ad"]))
    CIKTI.write_text(json.dumps(kayitlar, ensure_ascii=False, indent=1), encoding="utf-8")

    from collections import Counter
    koord = [k for k in kayitlar if k["lat"] is not None]
    disari = [k for k in koord if not _icinde(k["lat"], k["lng"])]
    ilsiz = [k for k in kayitlar if not k["il"]]
    print(f"\n{len(kayitlar)} kayıt -> {CIKTI.relative_to(KOK)}")
    print("tür      :", dict(Counter(k["tur"] for k in kayitlar)))
    print("il sayısı:", len({k['il'] for k in kayitlar if k['il']}), "| il bilgisi eksik:", len(ilsiz))
    print(f"koordinat: {len(koord)}/{len(kayitlar)} | sınır dışı: {len(disari)}")
    print("resmî kamp izni (rekreasyon değerinde çadır/kamp/karavan):",
          sum(1 for k in kayitlar if k["kamp_izni_resmi"]))
    for k in disari[:5]:
        print("   SINIR DIŞI:", k["ad"], k["lat"], k["lng"])


if __name__ == "__main__":
    main()
