# -*- coding: utf-8 -*-
"""
ŞABLON BİÇİM DÜZELTMELERİ  —  v1.3

sablon_guncelle.py hesabı doğru kurdu ama dosyalar Excel'de AÇILDIĞINDA
görünen birkaç sorun kaldı.  Bu betik onları giderir:

  ·  Birleştirilmiş hücrelerdeki uzun notlar kırpılıyordu (satır kaydırma
     kapalı) — kaydırma açılıp satır yüksekliği veriliyor.
  ·  v1.3 ile geçersiz kalan üç açıklama metni güncelleniyor:
       ÇOKLU!A81  · ÇOKLU!A84  · avan GİRİŞ!A50
  ·  ÇOKLU sayfasında 85-98. satırlar (gizli yardımcı alan) gizleniyor;
     böylece notlar ile yeni girdi bloğu arasındaki boş aralık kapanıyor.

Çalıştırma:  python3 araclar/sablon_bicim_duzelt.py
"""
import os
import sys
from copy import copy

import openpyxl

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAFIK = os.path.join(KOK, "templates", "ASANSOR_TRAFIK_HESABI_v2_1.xlsx")
AVAN = os.path.join(KOK, "templates", "ASANSOR_AVAN_HESAPLARI.xlsx")


def kaydir(ws, adres, yukseklik=None, dikey="top"):
    """Hücrede satır kaydırmayı açar, gerekiyorsa satır yüksekliği verir."""
    h = ws[adres]
    a = copy(h.alignment)
    a.wrap_text = True
    if dikey:
        a.vertical = dikey
    h.alignment = a
    if yukseklik:
        ws.row_dimensions[h.row].height = yukseklik


def main():
    # ============================================================ TRAFİK
    wb = openpyxl.load_workbook(TRAFIK)

    ws = wb["HESAPLAMA"]
    kaydir(ws, "E14", 92)          # kapı genişliği kapsam notu
    kaydir(ws, "B19", 48)          # bodrum açıklaması (B19:E19 birleşik)
    print("  · HESAPLAMA →  E14 ve B19 notları kaydırmalı")

    ws = wb["ÇOKLU ASANSÖR"]
    ws["A13"] = "⑪ Bodrum durak adedi (ortak, ana giriş altı)"
    ws["C13"] = ("Asansör bazında farklıysa 100. satırdan girin.  "
                 "Bodrum H ve S'yi değiştirmez; yalnız Tablo-2 hız seçimine "
                 "ve seyahat mesafesine girer.")
    kaydir(ws, "C13", 40)
    kaydir(ws, "A21", 30)
    kaydir(ws, "A106", 52)
    #  v1.3 ile geçersiz kalan iki not
    ws["A81"] = ("Kural: Durak sayısı 2 ile ortak durak sayısı (B9+1) arasında tam sayı "
                 "olmalıdır; boş bırakılan kolon ortak durak sayısını kullanır. Ortak kat "
                 "sayısı B9, grubun en yüksek asansörüne göre girilir — nüfus (b, B), k ve "
                 "Izul bina genelinde ortaktır, yalnız H, S ve Tablo-2 minimum hızı asansör "
                 "bazında ayrışır. Bodrum durağı (13. ve 100. satır) H ve S'yi DEĞİŞTİRMEZ; "
                 "yalnız Tablo-2 durak adedine ve seyahat mesafesine girer.")
    ws["A84"] = ("Kapı genişliği kapsamı: listedeki yedi genişliğin (700 – 1300 mm) tamamı "
                 "hesaplanır. MMO Tablo-4'te 1000 ve 1200 mm, ISO 8100-32 Tablo 6'da 700 mm "
                 "BASILI DEĞİLDİR; bu değerler komşu satırlardan enterpolasyon / dış "
                 "değerleme ile türetilir ve paftada kaynağı 'ara değer' olarak yazılır. "
                 "'Kabin İçi Oto. Kat K.Ç.' kapı tipi 1200 ve 1300 mm'de tabloda hiç yoktur — "
                 "bu durumda 102-103. satıra imalatçı ta/tk değerini girin. Asansör bazında "
                 "manuel süre girişi 102-105. satırdadır.")
    kaydir(ws, "A81", 64)
    kaydir(ws, "A84", 76)
    #  gizli yardımcı alan — notlar ile yeni blok arasındaki boşluğu kapat
    for r in range(85, 99):
        ws.row_dimensions[r].hidden = True
    print("  · ÇOKLU     →  C13/A81/A84 notları güncel + kaydırmalı, 85-98 gizlendi")

    ws = wb["TABLO-4"]
    kaydir(ws, "A11", 104)
    print("  · TABLO-4   →  kaynak notu kaydırmalı")

    ws = wb["TABLO-8"]
    ws["A5"] = ('Kaynak: ISO 8100-32:2020 "Planning and selection of passenger lifts…", '
                "Tablo 6 — 900 mm: 1,1 s | 1000 mm: 1,0 s | 1100 mm: 1,0 s | 1200 mm: 0,9 s.")
    kaydir(ws, "A5", 30)
    kaydir(ws, "A3", 30)
    print("  · TABLO-8   →  kaynak notları kaydırmalı")

    wb.calculation.fullCalcOnLoad = True
    wb.save(TRAFIK)

    # ============================================================== AVAN
    wb = openpyxl.load_workbook(AVAN)
    ws = wb["GİRİŞ"]
    ws["A50"] = ("Q₀ kapasiteden Tablo-7 ile bulunur.  Q satırını yalnız Tablo-7 dışı bir "
                 "kapasite kullanıyorsanız doldurun; boşsa Q₀ geçerlidir.   Boş kabin kütlesi "
                 "Gk de anma yükünden Tablo-11 ile gelir; imalatçı verisi varsa 'elle' "
                 "satırına yazın.   Palanga (i) ve denge faktörü (q) ASANSÖR BAZINDA "
                 "girilebilir (aşağıdaki 3. bölüm); boş bırakılırsa SABİTLER B kullanılır. "
                 "Ray sayısı, flexbil, montör, armatür ve priz değerleri tüm asansörlerde "
                 "ortaktır → SABİTLER sayfası, B bölümü.")
    kaydir(ws, "A50", 44)
    kaydir(ws, "A55", 32)
    print("  · GİRİŞ     →  A50 notu güncel + kaydırmalı")

    ws = wb["SABİTLER"]
    kaydir(ws, "A40", 44)
    kaydir(ws, "E22", 30)
    kaydir(ws, "E23", 30)
    print("  · SABİTLER  →  notlar kaydırmalı")

    wb.calculation.fullCalcOnLoad = True
    wb.save(AVAN)
    print("\nTamam.")


if __name__ == "__main__":
    sys.exit(main())
