# -*- coding: utf-8 -*-
"""Paylaşım kartı görselini (og:image, 1200x630) üretir: python build/og_gorsel.py

Site renkleri ve site adıyla tek bir varsayılan görsel; static/og.png olarak git'e girer.
Yazı tipi olarak sistemdeki Arial kullanılır (Türkçe harfler tam). Derleme sunucusunda
yazı tipi bulunmadığı için görsel derlemede değil, burada, tek seferlik üretilir.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

KOK = Path(__file__).resolve().parent.parent
CIKTI = KOK / "static" / "og.png"
YAZI_TIPLERI = [
    Path("C:/Windows/Fonts/arialbd.ttf"), Path("C:/Windows/Fonts/arial.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
]
YESIL, YESIL_AC, ACIK, BEYAZ = "#1b5e3f", "#2e7d5b", "#8fd6a8", "#ffffff"


def yazi_tipi(boyut: int, kalin: bool) -> ImageFont.FreeTypeFont:
    for y in YAZI_TIPLERI:
        if y.exists() and (("bd" in y.name.lower() or "Bold" in y.name) == kalin):
            return ImageFont.truetype(str(y), boyut)
    sys.exit("Türkçe destekli yazı tipi bulunamadı.")


def main() -> None:
    site = json.loads((KOK / "data" / "site.json").read_text(encoding="utf-8"))
    g = Image.new("RGB", (1200, 630), YESIL)
    c = ImageDraw.Draw(g)
    # sağda logo ağacı (favicon ile aynı biçim), büyük ve soluk
    ox, oy, s = 900, 130, 11
    c.polygon([(ox + 16 * s, oy + 3 * s), (ox + 4 * s, oy + 27 * s), (ox + 28 * s, oy + 27 * s)], fill=YESIL_AC)
    c.polygon([(ox + 16 * s, oy + 11 * s), (ox + 9.5 * s, oy + 24 * s), (ox + 22.5 * s, oy + 24 * s)], fill=ACIK)
    c.ellipse([ox + 14 * s, oy + 22.5 * s, ox + 18 * s, oy + 26.5 * s], fill=YESIL)
    # metin
    c.text((80, 170), site["ad"], font=yazi_tipi(96, True), fill=BEYAZ)
    c.text((84, 300), site["slogan"], font=yazi_tipi(40, False), fill=ACIK)
    c.text((84, 360), "Milli park, tabiat parkı ve koruma alanları", font=yazi_tipi(34, False), fill=BEYAZ)
    c.text((84, 408), "Resmî kamp izni · GPS koordinatı · DKMP kaynağı", font=yazi_tipi(34, False), fill=BEYAZ)
    c.rectangle([80, 520, 1120, 523], fill=YESIL_AC)
    c.text((84, 545), site["url"].replace("https://", ""), font=yazi_tipi(32, True), fill=ACIK)
    g.save(CIKTI, optimize=True)
    print(f"{CIKTI.relative_to(KOK)} {CIKTI.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
