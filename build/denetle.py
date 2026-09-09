"""Üretilen sitenin baştan sona denetimi: python build/denetle.py

NEDEN VAR: denetim betiği olmayan site sessizce bozulur. ankaradacocuk'ta
mekân başlığı kalıbı yapısal olarak bozuktu (sabit kısmı tek başına 59
karakter) ve aylarca fark edilmedi. Aynı ölçümler kamp alanları dizini için de yapılır.

Bulgu varsa çıkış kodu 1 döner; CI'da derlemeden sonra çağrılabilir.
"""

from __future__ import annotations

import html as H
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import unquote

KOK = Path(__file__).resolve().parent.parent
DIST = KOK / "dist"
ALAN = "https://kampalanlar.com"

BASLIK_EN = 62      # SERP'te kırpılma sınırı
ACIKLAMA_EN = 160

bulgular: list[tuple[str, str, str]] = []


def bul(agirlik: str, sayfa: str, mesaj: str) -> None:
    bulgular.append((agirlik, sayfa, mesaj))


def yol_of(p: Path) -> str:
    r = p.relative_to(DIST).as_posix()
    return "/" + (r[: -len("index.html")] if r.endswith("index.html") else r)


def hedef_var(hedef: str) -> bool:
    h = unquote(hedef.split("#")[0].split("?")[0])
    if not h.startswith("/"):
        return True
    p = DIST / h.lstrip("/")
    if h.endswith("/") or "." not in p.name:
        return (p / "index.html").exists() or p.exists()
    return p.exists()


def oznitelik(h: str, ad: str, tur: str = "name") -> str:
    """content özniteliğini AÇILIŞ TIRNAĞINI yakalayarak alır.

    `content=["\\'](.*?)["\\']` kalıbı, içinde kesme işareti geçen bir metni
    ilk kesme işaretinde kesiyor ("Ankara'da çocuklu..." 6 karakter görünür).
    Ayrıca HTML varlıkları çözülmeden uzunluk ölçülürse `&#39;` beş karakter
    sayılır. İkisi de yaşandı.
    """
    m = re.search(rf'<meta[^>]+{tur}="{ad}"[^>]+content=(["\'])(.*?)\1', h, re.S | re.I)
    if not m:
        m = re.search(rf'<meta[^>]+content=(["\'])(.*?)\1[^>]+{tur}="{ad}"', h, re.S | re.I)
    return H.unescape(m.group(2)).strip() if m else ""


def main() -> int:
    if not DIST.exists():
        print("dist/ yok — önce python build/derle.py")
        return 1

    sayfalar = sorted(DIST.rglob("*.html"))
    basliklar: Counter = Counter()
    aciklamalar: Counter = Counter()
    ic_baglanti: defaultdict[str, int] = defaultdict(int)
    kanonikler: Counter = Counter()
    tum_yollar = set()

    for p in sayfalar:
        yol = yol_of(p)
        tum_yollar.add(yol)
        h = p.read_text(encoding="utf-8", errors="replace")

        # --- başlık / açıklama
        m = re.search(r"<title>(.*?)</title>", h, re.S)
        baslik = H.unescape(m.group(1)).strip() if m else ""
        if not baslik:
            bul("YUKSEK", yol, "title yok")
        else:
            basliklar[baslik] += 1
            if len(baslik) > BASLIK_EN:
                bul("DUSUK", yol, f"başlık {len(baslik)} karakter (sınır {BASLIK_EN})")

        aciklama = oznitelik(h, "description")
        if not aciklama:
            bul("YUKSEK", yol, "meta description yok")
        else:
            aciklamalar[aciklama] += 1
            if len(aciklama) > ACIKLAMA_EN:
                bul("ORTA", yol, f"açıklama {len(aciklama)} karakter (sınır {ACIKLAMA_EN})")

        # --- temel etiketler
        if not re.search(r'<html[^>]+lang="tr"', h):
            bul("ORTA", yol, "lang=\"tr\" yok")
        if not re.search(r'name="viewport"', h):
            bul("ORTA", yol, "viewport yok")
        # noindex sayfa yinelenen icerik uretemez; canonical denetiminden muaf.
        noindex = bool(re.search(r'name="robots"[^>]*content="[^"]*noindex', h, re.I))
        kan = re.search(r'<link[^>]+rel="canonical"[^>]+href="([^"]+)"', h)
        if not kan:
            if not noindex:
                bul("YUKSEK", yol, "canonical yok")
        else:
            u = kan.group(1)
            if not noindex:
                kanonikler[u] += 1
            if not u.startswith(ALAN):
                bul("YUKSEK", yol, f"canonical yabancı alan adı: {u}")
            elif u != ALAN + yol and not noindex:
                bul("ORTA", yol, f"canonical kendini göstermiyor: {u}")

        h1 = re.findall(r"<h1\b[^>]*>(.*?)</h1>", h, re.S)
        if len(h1) == 0:
            bul("ORTA", yol, "h1 yok")
        elif len(h1) > 1:
            bul("DUSUK", yol, f"{len(h1)} adet h1")

        # tek robots etiketi olmalı; iki farklı robots satırı çelişir
        robots = re.findall(r'<meta[^>]+name="robots"[^>]*>', h, re.I)
        if len(robots) > 1:
            bul("YUKSEK", yol, f"{len(robots)} adet robots etiketi (çelişebilir)")

        # --- JSON-LD gerçekten ayrışıyor mu
        for blok in re.findall(
                r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', h, re.S):
            try:
                json.loads(blok)
            except json.JSONDecodeError as ex:
                bul("YUKSEK", yol, f"JSON-LD bozuk: {ex}")

        # --- görsel alt metni
        for etiket in re.findall(r"<img\b[^>]*>", h):
            if not re.search(r'\balt=', etiket):
                bul("ORTA", yol, "alt metni olmayan <img>")
                break

        # --- iç bağlantılar
        for hedef in re.findall(r'<a\b[^>]*href="([^"]+)"', h):
            if hedef.startswith("/"):
                ic_baglanti[unquote(hedef.split("#")[0].split("?")[0])] += 1
                if not hedef_var(hedef):
                    bul("YUKSEK", yol, f"kırık bağlantı: {hedef}")
        for hedef in (re.findall(r'<link\b[^>]*href="(/[^"]+)"', h)
                      + re.findall(r'<(?:img|script)\b[^>]*src="(/[^"]+)"', h)):
            if not hedef_var(hedef):
                bul("YUKSEK", yol, f"eksik dosya: {hedef}")

    # --- tekrar eden başlık / açıklama
    for b, n in basliklar.items():
        if n > 1:
            bul("ORTA", "(genel)", f"{n} sayfada aynı title: {b[:70]}")
    for a, n in aciklamalar.items():
        if n > 1:
            bul("DUSUK", "(genel)", f"{n} sayfada aynı açıklama: {a[:60]}")
    for u, n in kanonikler.items():
        if n > 1:
            bul("YUKSEK", "(genel)", f"{n} sayfa aynı canonical'ı gösteriyor: {u}")

    # --- öksüz sayfa
    for yol in sorted(tum_yollar):
        if yol in ("/", "/404.html"):
            continue
        if ic_baglanti.get(yol, 0) == 0 and ic_baglanti.get(yol.rstrip("/"), 0) == 0:
            bul("ORTA", yol, "hiçbir sayfadan bağlantı verilmemiş (öksüz)")

    # --- sitemap ile karşılaştır
    sm = DIST / "sitemap.xml"
    if not sm.exists():
        bul("YUKSEK", "(genel)", "sitemap.xml yok")
    else:
        icerik = sm.read_text(encoding="utf-8")
        listelenen = {u.replace(ALAN, "") for u in re.findall(r"<loc>(.*?)</loc>", icerik)}
        for u in listelenen:
            if u not in tum_yollar and u.rstrip("/") + "/" not in tum_yollar:
                bul("YUKSEK", "(sitemap)", f"sitemap'te olup diske yazılmayan: {u}")
        yayimlanabilir = {y for y in tum_yollar
                          if not y.endswith(".html") or y == "/404.html"}
        eksik = {y for y in yayimlanabilir if y != "/404.html"} - listelenen
        if len(eksik) > 3:
            bul("ORTA", "(sitemap)", f"{len(eksik)} sayfa sitemap'te yok, ilki: {sorted(eksik)[0]}")

    # --- rapor
    agirlik_sirasi = {"YUKSEK": 0, "ORTA": 1, "DUSUK": 2}
    bulgular.sort(key=lambda b: (agirlik_sirasi[b[0]], b[1]))
    sayim = Counter(b[0] for b in bulgular)
    print(f"\n{len(sayfalar)} sayfa denetlendi")
    print(f"YUKSEK {sayim['YUKSEK']} · ORTA {sayim['ORTA']} · DUSUK {sayim['DUSUK']}")
    for agirlik in ("YUKSEK", "ORTA", "DUSUK"):
        grup = [b for b in bulgular if b[0] == agirlik]
        if not grup:
            continue
        print(f"\n--- {agirlik} ({len(grup)}) ---")
        toplu: Counter = Counter()
        for _, sayfa, mesaj in grup:
            toplu[mesaj] += 1
        for mesaj, n in toplu.most_common(20):
            ilk = next(s for a, s, m in grup if m == mesaj)
            print(f"  {n:4}x {ilk[:44]:46s} {mesaj[:90]}")
        if len(toplu) > 20:
            print(f"  ... {len(toplu) - 20} çeşit daha")
    return 1 if sayim["YUKSEK"] else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
