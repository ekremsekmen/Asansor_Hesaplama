# -*- coding: utf-8 -*-
"""
ALTIN ÇIKTI ÜRETİCİ  —  refactor kalkanı

Trafik motorunun TAM çıktısını ( her adım, her uyarı, her not, her pafta
satırı ) çok sayıda senaryo için dondurur.  test_altin.py bunu her koşuda
yeniden üretip karşılaştırır.

NİÇİN:  mevcut testler BELİRLİ DEĞERLERİ ( TR, adet, Izul ) kontrol eder.
Refactor'da asıl risk onlar değil — uyarıların SIRASI, bir notun düşmesi,
bir adım satırının kaybolması gibi kimsenin assert etmediği şeylerdir.
Altın çıktı bunların hepsini kilitler:  bir karakter değişirse test söyler.

    python3 testler/altin_uret.py        → dosyayı YENİDEN ÜRETİR

Yeniden üretmek DAVRANIŞI DEĞİŞTİRME İZNİDİR.  Refactor sırasında ASLA
çalıştırılmaz;  yalnız kasıtlı bir davranış değişikliğinden sonra, diff
gözle incelenip onaylandığında çalıştırılır.
"""
import gzip
import itertools
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import tables as T                              # noqa: E402
from engine import traffic as TR                            # noqa: E402

DOSYA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "altin_trafik.json.gz")


def senaryolar():
    """Tek ve çoklu yolu, tablo sınırlarını ve manuel ezmeleri tarayan girdiler."""
    kapilar = [(700, "Teleskopik Otomatik"), (900, "Merkezden Açılan Oto."),
               (1000, "Teleskopik Otomatik"), (1200, "Merkezden Açılan Oto."),
               (1300, "Kabin İçi Oto. Kat K.Ç.")]
    # 1) bina tipi × kat × kapasite  ( tek asansör )
    for bt in T.BINA_TIPLERI:
        for N in (1, 5, 11, 20, 30):
            for P in (6, 10, 16, 30):
                kg, kt = kapilar[(N + P) % len(kapilar)]
                yield {"bina_tipi": bt, "bina_yuksekligi": 39.98, "yapi_yuksekligi": 43,
                       "N": N, "h": 3, "hizli1": 44, "hizli2": 3, "manuel_k": 0.1,
                       "asansorler": [{"P": P, "kapi_genisligi": kg, "kapi_tipi": kt}]}
    # 2) yükseklik / bodrum / hız ezmeleri
    for by, yy in ((10, 12), (21.5, 30.5), (22, 31), (60, 70)):
        for bod in (None, 0, 2, 10):
            for V in (None, 0.63, 1.6, 3.5):
                yield {"bina_tipi": "Konut", "bina_yuksekligi": by, "yapi_yuksekligi": yy,
                       "N": 12, "h": 3.2, "hizli1": 60, "hizli2": 2, "bodrum": bod,
                       "manuel_V": V,
                       "asansorler": [{"P": 13, "kapi_genisligi": 1100,
                                       "kapi_tipi": "Teleskopik Otomatik"}]}
    # 3) manuel süre ezmeleri  ( uyarı metinlerini tetikler )
    for mta, mtk, mtg, mtp in itertools.product((None, 2.4), (None, 3.1),
                                                (None, 5.9), (None, 1.15)):
        yield {"bina_tipi": "Otel (4* ve üzeri)", "bina_yuksekligi": 30,
               "yapi_yuksekligi": 33, "N": 9, "h": 3, "hizli1": 120,
               "asansorler": [{"P": 16, "kapi_genisligi": 1000,
                               "kapi_tipi": "Teleskopik Otomatik",
                               "manuel_ta": mta, "manuel_tk": mtk,
                               "manuel_tg": mtg, "manuel_tp": mtp}]}
    # 4) çoklu yol  —  farklı tipler, asansör bazında durak / h / bodrum
    for n in (2, 3, 4):
        for fark in ("P", "kapi", "V", "durak", "h", "bodrum"):
            liste = []
            for i in range(n):
                a = {"P": 10, "kapi_genisligi": 900, "kapi_tipi": "Teleskopik Otomatik"}
                if fark == "P":      a["P"] = (10, 16, 20, 25)[i]
                if fark == "kapi":   a["kapi_genisligi"] = (900, 1100, 1300, 800)[i]
                if fark == "V":      a["V"] = (1.6, 2, 2.5, 1)[i]
                if fark == "durak":  a["durak"] = (12, 9, 7, 5)[i]
                if fark == "h":      a["h"] = (3, 3.2, 2.9, 3.5)[i]
                if fark == "bodrum": a["bodrum"] = (0, 1, 2, 3)[i]
                liste.append(a)
            yield {"bina_tipi": "Konut", "bina_yuksekligi": 39.98, "yapi_yuksekligi": 43,
                   "N": 11, "h": 3, "hizli1": 44, "hizli2": 3, "asansorler": liste}
    # 5) özdeş çoklu  ( tek yola düşer )  +  ek nüfus  +  hata yolları
    for n in (2, 3, 4):
        yield {"bina_tipi": "İş Merkezi (Çok Firmalı)", "bina_yuksekligi": 45,
               "yapi_yuksekligi": 50, "N": 14, "h": 3.6, "hizli1": 4800,
               "asansorler": [{"P": 20, "kapi_genisligi": 1100,
                               "kapi_tipi": "Teleskopik Otomatik"}] * n}
    for ek in ([], [{"aciklama": "Zemin dükkân", "miktar": 30, "kalem": "DOĞRUDAN KİŞİ — Tablo-1 dışı"}],
               [{"aciklama": "Otopark", "miktar": 40, "kalem": "OTOPARK — Özel araç"},
                {"aciklama": "Ofis katı", "miktar": 600, "kalem": "İŞ MERKEZİ — Çalışma alanı"}]):
        yield {"bina_tipi": "Konut", "bina_yuksekligi": 39.98, "yapi_yuksekligi": 43,
               "N": 11, "h": 3, "hizli1": 44, "hizli2": 3, "ek_nufus": ek,
               "asansorler": [{"P": 13, "kapi_genisligi": 900,
                               "kapi_tipi": "Teleskopik Otomatik"}]}
    for bozuk in ({"N": 31}, {"N": 0}, {"h": -3}, {"h": 0}, {"bina_yuksekligi": None},
                  {"hizli1": None}, {"manuel_k": 0.2}, {"bodrum": 11},
                  {"asansorler": [{"P": 7, "kapi_genisligi": 900, "kapi_tipi": "Teleskopik Otomatik"}]},
                  {"asansorler": [{"P": 10, "kapi_genisligi": 900,
                                   "kapi_tipi": "Teleskopik Otomatik", "durak": 5}]},
                  {"asansorler": []}):
        temel = {"bina_tipi": "Konut", "bina_yuksekligi": 39.98, "yapi_yuksekligi": 43,
                 "N": 11, "h": 3, "hizli1": 44, "hizli2": 3,
                 "asansorler": [{"P": 10, "kapi_genisligi": 900,
                                 "kapi_tipi": "Teleskopik Otomatik"}]}
        temel.update(bozuk)
        yield temel


def uret():
    kayit = []
    for i, g in enumerate(senaryolar()):
        kayit.append({"no": i, "girdi": g, "cikti": TR.hesapla(json.loads(json.dumps(g)))})
    return kayit


def yaz():
    kayit = uret()
    ham = json.dumps(kayit, ensure_ascii=False, sort_keys=True, default=str, indent=1)
    with gzip.open(DOSYA, "wt", encoding="utf-8") as f:
        f.write(ham)
    print(f"  {len(kayit)} senaryo  ·  {len(ham)/1024:.0f} KB ham  ·  "
          f"{os.path.getsize(DOSYA)/1024:.0f} KB sıkıştırılmış")
    print(f"  → {DOSYA}")


if __name__ == "__main__":
    yaz()
