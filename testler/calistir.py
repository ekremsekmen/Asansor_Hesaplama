# -*- coding: utf-8 -*-
"""
TÜM TESTLERİ ÇALIŞTIR

    python3 testler/calistir.py            → hepsi
    python3 testler/calistir.py hizli      → Excel taraması hariç (saniyeler)
    python3 testler/calistir.py 2 3        → yalnız 2. ve 3. testler

Arayüz ve HTTP testleri için program açık olmalıdır (baslat.command).
Excel uyum testi için LibreOffice kurulu olmalıdır.
Eksik olan bileşenlerin testi atlanır, diğerleri yine çalışır.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from testler.ortak import GRI, KIRMIZI, SIFIR, YESIL      # noqa: E402

TESTLER = [
    ("1", "Excel uyumu", "testler.test_excel_uyumu", True),
    ("2", "Kenar durumlar", "testler.test_kenar_durum", False),
    ("3", "Girdi dayanıklılığı", "testler.test_dayaniklilik", False),
    ("4", "Çıktı bütünlüğü", "testler.test_ciktilar", False),
    ("5", "Arayüz", "testler.test_arayuz", False),
    ("6", "Geri yükleme", "testler.test_geri_yukleme", False),
]


def main(argv):
    secim = [a for a in argv if a.isdigit()]
    hizli = "hizli" in argv or "hızlı" in argv
    print("\n" + "═" * 68)
    print("  ASANSÖR AVAN HESAPLAMA PROGRAMI  —  DOĞRULAMA PAKETİ")
    print("═" * 68)

    baslangic = time.time()
    sonuclar = []
    for no, ad, modul_adi, yavas in TESTLER:
        if secim and no not in secim:
            continue
        if hizli and yavas:
            print(f"\n{GRI}TEST {no} — {ad}: hızlı kipte atlandı{SIFIR}")
            continue
        modul = __import__(modul_adi, fromlist=["calistir"])
        t0 = time.time()
        try:
            rapor = modul.calistir()
        except Exception as e:                                   # noqa: BLE001
            import traceback
            print(f"   {KIRMIZI}✘ test çalıştırılamadı: {e}{SIFIR}")
            traceback.print_exc()
            sonuclar.append((no, ad, False, 0, 0, 0, time.time() - t0))
            continue
        tamam = rapor.yazdir()
        sonuclar.append((no, ad, tamam, rapor.gecti, rapor.kaldi, rapor.atlandi,
                         time.time() - t0))

    print("\n" + "═" * 68)
    print("  ÖZET")
    print("═" * 68)
    tg = tk = ta = 0
    for no, ad, tamam, gecti, kaldi, atlandi, sure in sonuclar:
        tg += gecti; tk += kaldi; ta += atlandi
        isaret = f"{YESIL}✔{SIFIR}" if tamam else f"{KIRMIZI}✘{SIFIR}"
        ek = f"  {GRI}({atlandi} atlandı){SIFIR}" if atlandi else ""
        print(f"  {isaret}  TEST {no}  {ad:<26} {gecti:>5} geçti  "
              f"{kaldi:>3} kaldı  {GRI}{sure:5.1f} sn{SIFIR}{ek}")
    print("─" * 68)
    renk = YESIL if tk == 0 else KIRMIZI
    print(f"  {renk}TOPLAM : {tg} kontrol geçti, {tk} başarısız{SIFIR}"
          f"{f'  ({ta} bölüm atlandı)' if ta else ''}"
          f"   {GRI}· {time.time()-baslangic:.1f} sn{SIFIR}")
    print("═" * 68 + "\n")
    return 0 if tk == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
