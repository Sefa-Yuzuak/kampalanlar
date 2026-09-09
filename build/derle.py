# -*- coding: utf-8 -*-
"""kampalanlar.com — statik site üreteci.

Girdi : data/site.json, data/korunan_alanlar.json, data/rehberler.json, data/sayfalar.json
Çıktı : dist/

Sitenin ayrışma noktası, rakiplerin hiçbirinde bulunmayan üç şey:
  1. Her kayıtta ham GPS koordinatı ve DKMP kaynak bağlantısı
  2. "Bu alanda resmen kamp izinli mi" durumu (DKMP Rekreasyon Değeri sütunundan)
  3. Görünür son doğrulama tarihi

Puan/ücret/izin gibi hiçbir alan tahminle doldurulmaz; kaynakta yoksa boş kalır.
"""
from __future__ import annotations

import json
import math
import re
import shutil
import statistics
import sys
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

KOK = Path(__file__).resolve().parent.parent
DATA = KOK / "data"
DIST = KOK / "dist"
STATIC = KOK / "static"
TEMPLATES = KOK / "templates"

TURLER = {
    "milli_park": {"ad": "Milli Park", "cogul": "Milli Parklar", "slug": "milli-park",
                   "ikon": "🏔", "schema": "Park",
                   "aciklama": "2873 sayılı Milli Parklar Kanunu ile korunan, ulusal ve "
                               "uluslararası ölçekte değer taşıyan doğa parçaları."},
    "tabiat_parki": {"ad": "Tabiat Parkı", "cogul": "Tabiat Parkları", "slug": "tabiat-parki",
                     "ikon": "🌲", "schema": "Park",
                     "aciklama": "Bitki örtüsü ve yaban hayatı özelliğiyle dinlenme ve "
                                 "eğlenmeye uygun, korunan tabiat parçaları."},
    "tabiati_koruma": {"ad": "Tabiatı Koruma Alanı", "cogul": "Tabiatı Koruma Alanları",
                       "slug": "tabiati-koruma-alani", "ikon": "🛡", "schema": "Park",
                       "aciklama": "Bilim ve eğitim bakımından önem taşıyan, ender "
                                   "ekosistemleri barındıran sıkı korunan alanlar."},
}

# Koordinat denetimi: aynı ildeki kayıtların ortancasından bu kadar uzaktaki nokta
# şüpheli sayılır. Türkiye'nin illeri büyük (Konya tek başına ~350 km), bu yüzden eşik
# geniş tutuldu; 150 km'de Gökpınar Gölü TP gibi doğru kayıtlar yanlış alarm veriyordu.
SAPMA_ESIGI_KM = 200
EN_AZ_KAYIT = 3


def slugify(metin: str) -> str:
    d = {"ı": "i", "İ": "i", "ş": "s", "Ş": "s", "ğ": "g", "Ğ": "g",
         "ü": "u", "Ü": "u", "ö": "o", "Ö": "o", "ç": "c", "Ç": "c"}
    metin = "".join(d.get(k, k) for k in metin)
    metin = unicodedata.normalize("NFKD", metin).encode("ascii", "ignore").decode()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", metin.lower())).strip("-")


def yukle(ad: str, varsayilan=None):
    yol = DATA / ad
    if not yol.exists():
        if varsayilan is None:
            sys.exit(f"Eksik veri dosyası: {yol}")
        return varsayilan
    return json.loads(yol.read_text(encoding="utf-8"))


def km(a_lat, a_lng, b_lat, b_lng) -> float:
    """Haversine — iki nokta arası kuş uçuşu kilometre."""
    R = 6371.0
    p1, p2 = math.radians(a_lat), math.radians(b_lat)
    dp, dl = p2 - p1, math.radians(b_lng - a_lng)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def kisalt(metin: str, en: int = 158) -> str:
    metin = " ".join((metin or "").split())
    if len(metin) <= en:
        return metin
    kesik = metin[:en]
    bosluk = kesik.rfind(" ")
    return (kesik[:bosluk] if bosluk > en * 0.6 else kesik).rstrip(" ,.;:") + "…"


def koordinat_denetle(alanlar: list[dict]) -> None:
    """Aynı ildeki kayıtların ortancasına göre aykırı koordinatları işaretler.

    Kaynak (DKMP) verisi DEĞİŞTİRİLMEZ. Amaç, Kaçkar Dağları MP gibi kaynakta
    şüpheli görünen kayıtları kullanıcıdan gizlemek değil, açıkça belirtmek.
    """
    iller: dict[str, list[dict]] = {}
    for a in alanlar:
        if a["lat"] is not None:
            iller.setdefault(a["il"], []).append(a)

    for a in alanlar:
        if a["lat"] is None:
            a["koordinat_durum"] = "yok"
            continue
        grup = iller.get(a["il"], [])
        if len(grup) < EN_AZ_KAYIT:
            a["koordinat_durum"] = "tekil"          # karşılaştıracak komşu yok
            continue
        orta_lat = statistics.median(g["lat"] for g in grup)
        orta_lng = statistics.median(g["lng"] for g in grup)
        sapma = km(a["lat"], a["lng"], orta_lat, orta_lng)
        if sapma <= SAPMA_ESIGI_KM:
            a["sapma_km"] = round(sapma)
            a["koordinat_durum"] = "tamam"
            continue
        # Tek tek ters girilmiş kayıtlar var (Divriği TKA: 38.12,39.37 -> 39.37,38.12).
        # Dosya geneli düz olduğu için ayrıştırıcının çoğunluk kuralı bunları yakalayamıyor.
        # Yer değiştirme sapmayı eşiğin altına indiriyorsa hata kanıtlanmış demektir.
        ters = km(a["lng"], a["lat"], orta_lat, orta_lng)
        if ters <= SAPMA_ESIGI_KM and ters < sapma / 2:
            a["lat"], a["lng"] = a["lng"], a["lat"]
            a["sapma_km"] = round(ters)
            a["koordinat_durum"] = "duzeltildi_ters"
            continue
        a["sapma_km"] = round(sapma)
        a["koordinat_durum"] = "supheli"


def hazirla(alanlar: list[dict], site: dict) -> list[dict]:
    # Denetim önce çalışır: aykırı kayıtlarda enlem/boylam yer değiştirebiliyor,
    # maps_url ve koordinat yazısı düzeltilmiş değerden üretilmeli.
    koordinat_denetle(alanlar)
    goruldu: set[str] = set()
    for a in alanlar:
        if a["tur"] not in TURLER:
            sys.exit(f"Bilinmeyen tür: {a['tur']} ({a['ad']})")
        temel = slugify(f"{a['ad']}-{TURLER[a['tur']]['slug']}")
        slug = temel
        # Aynı adda birden çok alan var (iki ayrı "Kartaltepe Tabiat Parkı" gibi);
        # ili ekleyerek hem adres hem sayfa başlığı ayrışsın, çift başlık oluşmasın.
        a["ad_ayirt"] = a["ad"]
        if slug in goruldu:
            a["ad_ayirt"] = f"{a['ad']} ({a['il'].split(' / ')[0]})"
            slug = slugify(f"{temel}-{a['il'].split(' / ')[0]}")
        n = 2
        while slug in goruldu:
            slug, n = f"{temel}-{n}", n + 1
        goruldu.add(slug)
        a["slug"] = slug
        a["url"] = f"/alan/{slug}/"
        a["tur_bilgi"] = TURLER[a["tur"]]
        a["iller"] = [i.strip() for i in a["il"].split("/") if i.strip()]
        a["il_sluglari"] = [slugify(i) for i in a["iller"]]
        a["hektar_yazi"] = (f"{a['hektar']:,.0f}".replace(",", ".") if a.get("hektar") else "")
        a["rekreasyon_liste"] = [p.strip(" .") for p in re.split(r"[,;]", a.get("rekreasyon") or "") if p.strip(" .")]
        a["kaynak_liste"] = [k for k in (a.get("kaynak_degeri") or []) if k]
        if a.get("lat") is not None:
            a["maps_url"] = f"https://www.google.com/maps/search/?api=1&query={a['lat']},{a['lng']}"
            a["koordinat_yazi"] = f"{a['lat']:.6f}, {a['lng']:.6f}"
        else:
            a["maps_url"] = ("https://www.google.com/maps/search/?api=1&query="
                             + re.sub(r"\s+", "+", f"{a['ad']} {a['tur_bilgi']['ad']}"))
            a["koordinat_yazi"] = ""
        a["ilan_yili"] = (a.get("ilan_tarihi") or "")[:4]
        a["dogrulama"] = site["veri_tarihi"]
    alanlar.sort(key=lambda a: (not a["kamp_izni_resmi"], -(a.get("hektar") or 0), a["ad"]))
    return alanlar


# --------------------------------------------------------------------------- şema
def kirintilar(site, *parcalar):
    ogeler = [{"@type": "ListItem", "position": 1, "name": "Ana sayfa", "item": site["url"] + "/"}]
    for i, (ad, yol) in enumerate(parcalar, start=2):
        ogeler.append({"@type": "ListItem", "position": i, "name": ad, "item": site["url"] + yol})
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": ogeler}


def alan_schema(a: dict, site: dict) -> dict:
    s = {
        "@context": "https://schema.org",
        "@type": ["Park", "TouristAttraction"],
        "name": f"{a['ad']} {a['tur_bilgi']['ad']}",
        "url": site["url"] + a["url"],
        "dateModified": site["veri_tarihi"],
        "description": ozet(a),
        "address": {"@type": "PostalAddress", "addressRegion": a["il"], "addressCountry": "TR"},
        "isAccessibleForFree": False,
        "publicAccess": True,
    }
    if a.get("lat") is not None and a["koordinat_durum"] != "supheli":
        s["geo"] = {"@type": "GeoCoordinates", "latitude": a["lat"], "longitude": a["lng"]}
    if a.get("hektar"):
        s["additionalProperty"] = [{"@type": "PropertyValue", "name": "Alan", "value": a["hektar"], "unitCode": "HAR"}]
    return s


def liste_schema(site, ad, yol, alanlar):
    return {"@context": "https://schema.org", "@type": "ItemList", "name": ad,
            "url": site["url"] + yol, "numberOfItems": len(alanlar),
            "itemListElement": [{"@type": "ListItem", "position": i,
                                 "name": f"{a['ad']} {a['tur_bilgi']['ad']}",
                                 "url": site["url"] + a["url"]}
                                for i, a in enumerate(alanlar[:60], start=1)]}


def sss_schema(sorular):
    return {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": s["s"],
                            "acceptedAnswer": {"@type": "Answer", "text": s["c"]}} for s in sorular]}


def ozet(a: dict) -> str:
    parcalar = [f"{a['ad']} {a['tur_bilgi']['ad']}, {a['il']} sınırlarında"]
    if a["hektar_yazi"]:
        parcalar.append(f"{a['hektar_yazi']} hektar")
    if a["ilan_yili"]:
        parcalar.append(f"{a['ilan_yili']} yılında ilan edildi")
    metin = ", ".join(parcalar) + ". "
    metin += ("DKMP kayıtlarında bu alan için çadırlı kamp/karavan kullanımı belirtiliyor."
              if a["kamp_izni_resmi"] else
              "DKMP kayıtlarında bu alan için çadırlı kamp belirtilmiyor.")
    return metin


def alan_sss(a: dict) -> list[dict]:
    s = []
    if a["kamp_izni_resmi"]:
        s.append({"s": f"{a['ad']} {a['tur_bilgi']['ad']}'nda kamp yapılabilir mi?",
                  "c": f"DKMP'nin 2025 korunan alan istatistiklerinde bu alanın rekreasyon "
                       f"değeri arasında çadırlı kamp/karavan kullanımı sayılıyor. Kamp yalnızca "
                       f"idarece belirlenen alanlarda ve ücret tarifesine göre yapılabilir; "
                       f"gitmeden önce alan müdürlüğünü arayın."})
    else:
        s.append({"s": f"{a['ad']} {a['tur_bilgi']['ad']}'nda kamp yapılabilir mi?",
                  "c": f"DKMP'nin 2025 kayıtlarında bu alan için çadırlı kamp belirtilmiyor. "
                       f"6831 sayılı Orman Kanunu'nun 76/a maddesi, idarece belirlenen konak "
                       f"yerleri dışında gecelemeyi yasaklıyor. İzin durumunu alan müdürlüğünden "
                       f"teyit etmeden çadır kurmayın."})
    if a["hektar_yazi"]:
        s.append({"s": f"{a['ad']} kaç hektar?",
                  "c": f"DKMP 2025 istatistiklerine göre {a['hektar_yazi']} hektar."})
    if a["koordinat_yazi"] and a["koordinat_durum"] != "supheli":
        s.append({"s": f"{a['ad']} nerede?",
                  "c": f"{a['il']} sınırlarında. DKMP kayıtlarındaki koordinat: {a['koordinat_yazi']}."})
    return s


# --------------------------------------------------------------------------- yazma
def yaz(yol: str, icerik: str) -> None:
    hedef = DIST / yol.strip("/") / "index.html" if yol != "/" else DIST / "index.html"
    hedef.parent.mkdir(parents=True, exist_ok=True)
    hedef.write_text(icerik, encoding="utf-8")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    site = yukle("site.json")
    site["yil"] = date.today().year
    site["derleme_zamani"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    alanlar = hazirla(yukle("korunan_alanlar.json"), site)
    rehberler = yukle("rehberler.json", [])
    sayfalar = yukle("sayfalar.json", [])

    for r in rehberler:
        r["url"] = f"/rehber/{r['slug']}/"

    env = Environment(loader=FileSystemLoader(TEMPLATES),
                      autoescape=select_autoescape(["html"]), trim_blocks=True, lstrip_blocks=True)
    env.filters["json"] = lambda v: json.dumps(v, ensure_ascii=False)

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    shutil.copytree(STATIC, DIST / "static")
    for ad in ("favicon.svg",):
        if (STATIC / ad).exists():
            shutil.copy(STATIC / ad, DIST / ad)

    kamp_izinli = [a for a in alanlar if a["kamp_izni_resmi"]]
    il_grup: dict[str, list[dict]] = {}
    for a in alanlar:
        for il in a["iller"]:
            il_grup.setdefault(il, []).append(a)
    iller = sorted(({"ad": il, "slug": slugify(il), "url": f"/il/{slugify(il)}/",
                     "alanlar": sorted(g, key=lambda x: (not x["kamp_izni_resmi"], x["ad"])),
                     "kamp": sum(1 for x in g if x["kamp_izni_resmi"])}
                    for il, g in il_grup.items()), key=lambda x: x["ad"])
    turler = [dict(t, slug_url=f"/tur/{t['slug']}/",
                   alanlar=[a for a in alanlar if a["tur"] == anahtar])
              for anahtar, t in TURLER.items()]

    ortak = {"site": site, "iller": iller, "turler": turler, "rehberler": rehberler,
             "toplam": len(alanlar), "kamp_sayisi": len(kamp_izinli)}
    yollar: list[tuple[str, str, str]] = []      # (url, lastmod, öncelik)

    def tam_baslik(b: str) -> str:
        """Site adı yalnızca 60 karaktere sığıyorsa eklenir; yer adları kısaltılmaz."""
        ekli = f"{b} | {site['ad']}"
        return ekli if len(ekli) <= 60 else b

    def sayfa(yol, sablon, baslik, aciklama, schema, oncelik="0.6", **kw):
        yaz(yol, env.get_template(sablon).render(
            baslik=baslik, tam_baslik=tam_baslik(baslik), meta_desc=kisalt(aciklama),
            canonical=yol, schema=schema, **ortak, **kw))
        yollar.append((yol, site["veri_tarihi"], oncelik))

    # ana sayfa
    sayfa("/", "home.html",
          f"Türkiye Kamp Alanları {site['yil']}: {len(kamp_izinli)} Resmî İzinli Alan",
          f"Türkiye'deki {len(alanlar)} milli park, tabiat parkı ve tabiatı koruma alanı; "
          f"hangisinde resmen kamp izinli olduğu, GPS koordinatı ve resmî kaynağıyla.",
          [{"@context": "https://schema.org", "@type": "WebSite", "name": site["ad"],
            "url": site["url"] + "/", "inLanguage": "tr-TR"},
           {"@context": "https://schema.org", "@type": "Organization", "name": site["ad"],
            "url": site["url"] + "/"},
           liste_schema(site, "Resmî kamp izinli alanlar", "/kamp-izinli/", kamp_izinli)],
          oncelik="1.0", kamp_izinli=kamp_izinli[:24], one_cikan=alanlar[:12])

    # resmî kamp izinli alanlar — sitenin en değerli sayfası
    sayfa("/kamp-izinli/", "liste.html",
          f"Resmî Kamp İzinli {len(kamp_izinli)} Korunan Alan ({site['yil']})",
          f"DKMP kayıtlarında çadırlı kamp veya karavan kullanımı belirtilen "
          f"{len(kamp_izinli)} korunan alan; il, koordinat ve resmî kaynağıyla.",
          [liste_schema(site, "Resmî kamp izinli alanlar", "/kamp-izinli/", kamp_izinli),
           kirintilar(site, ("Kamp izinli alanlar", "/kamp-izinli/"))],
          oncelik="0.9", liste=kamp_izinli, liste_basligi="Resmî kamp izinli alanlar",
          giris=("Aşağıdaki alanlar, Tarım ve Orman Bakanlığı DKMP'nin 2025 korunan alan "
                 "istatistiklerinde rekreasyon değeri olarak çadırlı kamp, kamp ya da karavan "
                 "kullanımı belirtilen alanlardır. Liste resmî kayıttan üretilmiştir; "
                 "kamp yalnızca idarece belirlenen alanlarda ve ücret tarifesine göre yapılabilir."),
          kirinti=[("Kamp izinli alanlar", "/kamp-izinli/")])

    # il dizini + il sayfaları
    sayfa("/il/", "il_dizini.html", f"İllere Göre Kamp Alanları ve Korunan Alanlar",
          f"81 ilde {len(alanlar)} korunan alan; hangi ilde kaç tanesinde resmen kamp izinli.",
          [kirintilar(site, ("İller", "/il/"))], oncelik="0.8",
          kirinti=[("İller", "/il/")])
    for il in iller:
        kamp = [a for a in il["alanlar"] if a["kamp_izni_resmi"]]
        sayfa(il["url"], "liste.html",
              f"{il['ad']} Kamp Alanları: {len(il['alanlar'])} Korunan Alan",
              f"{il['ad']} sınırlarındaki {len(il['alanlar'])} milli park, tabiat parkı ve "
              f"koruma alanı; {len(kamp)} tanesinde DKMP kayıtlarında kamp belirtiliyor.",
              [liste_schema(site, f"{il['ad']} korunan alanları", il["url"], il["alanlar"]),
               kirintilar(site, ("İller", "/il/"), (il["ad"], il["url"]))],
              liste=il["alanlar"], liste_basligi=f"{il['ad']} korunan alanları",
              giris=(f"{il['ad']} sınırlarında DKMP kaydı bulunan {len(il['alanlar'])} korunan alan var; "
                     f"bunların {len(kamp)} tanesinin rekreasyon değerinde kamp geçiyor."),
              kirinti=[("İller", "/il/"), (il["ad"], il["url"])])

    # tür sayfaları
    for t in turler:
        sayfa(t["slug_url"], "liste.html", f"Türkiye'deki {len(t['alanlar'])} {t['cogul']}",
              f"{t['aciklama']} Türkiye'de {len(t['alanlar'])} adet {t['ad'].lower()} bulunuyor.",
              [liste_schema(site, t["cogul"], t["slug_url"], t["alanlar"]),
               kirintilar(site, (t["cogul"], t["slug_url"]))],
              oncelik="0.8", liste=t["alanlar"], liste_basligi=t["cogul"],
              giris=t["aciklama"], kirinti=[(t["cogul"], t["slug_url"])])

    # tekil alan sayfaları
    for a in alanlar:
        sss = alan_sss(a)
        sayfa(a["url"], "alan.html",
              f"{a['ad_ayirt']} {a['tur_bilgi']['ad']}: Kamp İzni ve Konum",
              ozet(a),
              [alan_schema(a, site), sss_schema(sss),
               kirintilar(site, ("İller", "/il/"), (a["iller"][0], f"/il/{a['il_sluglari'][0]}/"),
                          (a["ad"], a["url"]))],
              oncelik="0.7", a=a, sss=sss,
              benzer=[b for b in il_grup.get(a["iller"][0], []) if b["slug"] != a["slug"]][:6],
              kirinti=[("İller", "/il/"), (a["iller"][0], f"/il/{a['il_sluglari'][0]}/"), (a["ad"], a["url"])])

    # harita
    sayfa("/harita/", "harita.html", "Kamp Alanları Haritası",
          "Türkiye'deki korunan alanların haritası; resmî kamp izinli olanlar ayrı işaretli.",
          [kirintilar(site, ("Harita", "/harita/"))], oncelik="0.7",
          noktalar=[a for a in alanlar if a["lat"] is not None and a["koordinat_durum"] != "supheli"],
          kirinti=[("Harita", "/harita/")])

    # 2026 resmî ücret tarifesi — "milli park kamp ücreti 2026" sorgusunda
    # bugün ilk sıradaki sonuç bir PDF; HTML muadili rakipsiz.
    tarife = yukle("tarife_2026.json", None)
    if tarife:
        tum = [v for g in tarife["gruplar"] for v in g["ucret"].values()]
        sss_tarife = [
            {"s": f"{tarife['yil']} milli park kamp ücreti ne kadar?",
             "c": f"DKMP'nin {tarife['yil']} tarifesine göre 4 kişilik çadır için günlük yer "
                  f"kullanım bedeli, bölge grubuna ve alanın kategorisine göre "
                  f"{min(tum)} TL ile {max(tum)} TL arasında değişiyor."},
            {"s": "Ücrete neler dahil?",
             "c": "Tutar yer kullanım bedelidir. Su, duş, çamaşırhane, bulaşıkhane ve atık "
                  "hizmetlerini kapsayan ortak kullanım bedeli ayrıca alınabilir; elektrik "
                  "tüketimi ve ısınma giderleri bu bedele dahil değildir."},
            {"s": "Kategoriyi nereden öğrenirim?",
             "c": "Kategori, alanın DKMP tarafından belirlenen sınıfıdır ve aynı ilde farklı "
                  "kategoride alan bulunabilir. Alanın kategorisi için DKMP'nin ücret tarifesi "
                  "sayfasındaki EK-1 listesine bakın."},
        ]
        sayfa("/kamp-ucretleri-2026/", "tarife.html",
              f"Kamp Ücretleri {tarife['yil']}: Resmî DKMP Tarifesi",
              f"DKMP'nin {tarife['yil']} resmî çadır tarifesi: 21 bölge grubu ve 3 kategori için "
              f"günlük ücretler, {min(tum)}–{max(tum)} TL. Doğrudan resmî PDF'ten çıkarıldı.",
              [sss_schema(sss_tarife), kirintilar(site, ("Kamp ücretleri", "/kamp-ucretleri-2026/"))],
              oncelik="0.9", tarife=tarife, en_az=min(tum), en_cok=max(tum), sss=sss_tarife,
              kirinti=[("Kamp ücretleri", "/kamp-ucretleri-2026/")])

    # rehberler
    if rehberler:
        sayfa("/rehber/", "rehber_dizini.html", "Kamp Rehberleri: İzin, Ceza ve Mevzuat",
              "Türkiye'de nereye kamp kurulabilir, izin nasıl alınır, ceza ne kadar.",
              [kirintilar(site, ("Rehberler", "/rehber/"))], oncelik="0.8",
              kirinti=[("Rehberler", "/rehber/")])
    for r in rehberler:
        sayfa(r["url"], "rehber.html", f"{r['baslik']}", r["ozet"],
              [sss_schema(r.get("sss", [])),
               {"@context": "https://schema.org", "@type": "Article", "headline": r["baslik"],
                "description": r["ozet"], "dateModified": r.get("guncelleme", site["veri_tarihi"]),
                "url": site["url"] + r["url"]},
               kirintilar(site, ("Rehberler", "/rehber/"), (r["baslik"], r["url"]))],
              oncelik="0.8", r=r, kirinti=[("Rehberler", "/rehber/"), (r["baslik"], r["url"])])

    # düz sayfalar (hakkında, kaynaklar, gizlilik)
    for p in sayfalar:
        sayfa(p["url"], "sayfa.html", p["baslik"], p["meta"],
              [kirintilar(site, (p["baslik"], p["url"]))], oncelik="0.4", p=p,
              kirinti=[(p["baslik"], p["url"])])

    # 404
    (DIST / "404.html").write_text(env.get_template("404.html").render(
        baslik="Sayfa bulunamadı", meta_desc="Aradığınız sayfa bulunamadı.",
        canonical="/404.html", schema=[], tam_baslik=tam_baslik("Sayfa bulunamadı"), **ortak), encoding="utf-8")

    # açık veri
    (DIST / "veri").mkdir(exist_ok=True)
    (DIST / "veri" / "korunan-alanlar.json").write_text(json.dumps(
        [{k: v for k, v in a.items() if k not in ("tur_bilgi",)} for a in alanlar],
        ensure_ascii=False, indent=1), encoding="utf-8")

    # sitemap / robots / llms / ads
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for yol, lastmod, onc in yollar:
        sm.append(f"  <url><loc>{site['url']}{yol}</loc><lastmod>{lastmod}</lastmod>"
                  f"<priority>{onc}</priority></url>")
    sm.append("</urlset>")
    (DIST / "sitemap.xml").write_text("\n".join(sm), encoding="utf-8")

    (DIST / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\n"
        "# Yapay zekâ tarayıcıları (GEO): içeriğin alıntılanmasına izin veriyoruz\n"
        + "".join(f"User-agent: {b}\nAllow: /\n" for b in
                  ("GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot",
                   "PerplexityBot", "Google-Extended", "Applebot-Extended", "CCBot"))
        + f"\nSitemap: {site['url']}/sitemap.xml\n", encoding="utf-8")

    if site.get("adsense"):
        (DIST / "ads.txt").write_text(
            f"google.com, {site['adsense'].removeprefix('ca-')}, DIRECT, f08c47fec0942fa0\n",
            encoding="utf-8")

    llms = [f"# {site['ad']}", "", f"> {site['aciklama']}", "",
            f"Veri kaynağı: Tarım ve Orman Bakanlığı DKMP, Korunan Alan İstatistikleri 2025. "
            f"Son veri güncellemesi: {site['veri_tarihi']}.", "",
            f"## Resmî kamp izinli alanlar ({len(kamp_izinli)})", ""]
    for a in kamp_izinli:
        llms.append(f"- [{a['ad']} {a['tur_bilgi']['ad']}]({site['url']}{a['url']}): "
                    f"{a['il']}, {a['hektar_yazi']} ha. {a['rekreasyon']}")
    llms += ["", "## Rehberler", ""]
    for r in rehberler:
        llms.append(f"- [{r['baslik']}]({site['url']}{r['url']}): {r['ozet']}")
    (DIST / "llms.txt").write_text("\n".join(llms), encoding="utf-8")

    supheli = sum(1 for a in alanlar if a["koordinat_durum"] == "supheli")
    print(f"✓ {len(yollar)} sayfa | {len(alanlar)} alan | {len(kamp_izinli)} kamp izinli | "
          f"{len(iller)} il | {len(rehberler)} rehber -> {DIST}")
    if supheli:
        print(f"  koordinatı şüpheli işaretlenen kayıt: {supheli} "
              f"(il ortancasından >{SAPMA_ESIGI_KM} km)")


if __name__ == "__main__":
    main()
