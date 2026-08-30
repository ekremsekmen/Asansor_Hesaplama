#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ŞABLON DENETLEYİCİ  —  komut satırından hızlı kontrol

    python3 araclar/sablon_denetle.py

templates/ klasöründeki iki Excel'in programın beklediği dosyalar olup
olmadığını saniyeler içinde söyler:  sayfalar, girdi hücreleri ve şablonun
içindeki tablo değerleri motordaki tablolarla karşılaştırılır.

Ne zaman koşulur:
  · Excel dosyalarını elle düzenledikten sonra,
  · templates/ klasörüne yeni bir dosya kopyaladıktan sonra,
  · "acaba doğru şablon mu duruyor" diye şüphelenildiğinde.

Tam doğrulama için  python3 testler/calistir.py  ( Test 1 ) vardır; o
LibreOffice ile şablonu YENİDEN HESAPLATIR ve 5.000'den fazla hücreyi
karşılaştırır ama dakikalar sürer.  Bu betik ise yapısal bir ön kontroldür.

Çıkış kodu:  0 = iki şablon da uygun,  1 = sorun var.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from exports import sablon_denetim as D          # noqa: E402
from exports import xlsx_export as XE            # noqa: E402

KALIN, SIFIRLA = "\033[1m", "\033[0m"
YESIL, KIRMIZI = "\033[92m", "\033[91m"


def main():
    print()
    print("═" * 68)
    print(f"  {KALIN}ŞABLON DENETİMİ{SIFIRLA}   templates/ klasörü")
    print("═" * 68)
    tumu_uygun = True
    for tur, yol, baslik in (("trafik", XE.TRAFIK_SABLON, "TRAFİK HESABI"),
                             ("avan", XE.AVAN_SABLON, "AVAN HESAPLARI")):
        s = D.denetle(yol, tur, onbellek=False)
        tumu_uygun = tumu_uygun and s["uygun"]
        isaret = f"{YESIL}✔{SIFIRLA}" if s["uygun"] else f"{KIRMIZI}✘{SIFIRLA}"
        print(f"\n{isaret} {KALIN}{baslik}{SIFIRLA}   {s['dosya']}")
        print(f"    sayfa : {s['sayfa_sayisi']}")
        print(f"    md5   : {s['md5']}")
        if s["uygun"]:
            print("    durum : programın beklediği şablon — girdi hücreleri ve "
                  "tablo değerleri uyuşuyor")
        else:
            print(f"    durum : {KIRMIZI}UYUŞMUYOR — {len(s['hatalar'])} sorun{SIFIRLA}")
            for h in s["hatalar"][:25]:
                print(f"        · {h}")
            if len(s["hatalar"]) > 25:
                print(f"        … ve {len(s['hatalar']) - 25} sorun daha")

    print()
    print("─" * 68)
    if tumu_uygun:
        print(f"  {YESIL}İki şablon da uygun.{SIFIRLA}  XLSX çıktısı güvenle alınabilir.")
    else:
        print(f"  {KIRMIZI}Şablon uyuşmuyor.{SIFIRLA}  Program bu dosyalarla XLSX ÜRETMEZ; "
              "doğru\n  şablonu templates/ klasörüne koyun. Hesap ve PDF çıktısı "
              "etkilenmez —\n  motor Excel'den bağımsızdır.")
    print("─" * 68)
    print()
    return 0 if tumu_uygun else 1


if __name__ == "__main__":
    sys.exit(main())
